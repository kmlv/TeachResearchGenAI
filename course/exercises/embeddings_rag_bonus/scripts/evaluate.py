"""Evaluate lexical, dense and hybrid retrieval against human-verified pages.

The question catalogue is pedagogical design, not ground truth. Relevance comes
only from ``evaluation-qrels.csv`` after a person has opened the local PDF at
the cited page. Reports contain metadata and scores, never book text.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
from fastembed import TextEmbedding

from common import diversify, index_schema_error, reciprocal_rank_fusion, unit_rows
from search import dense_ranking, lexical_ranking, load_chunks


MODES = ("lexical", "dense", "hybrid")
QUESTION_FIELDS = (
    "query_id",
    "category",
    "query_type",
    "query",
    "expected_documents",
    "relevance_criterion",
    "teaching_purpose",
)
QREL_FIELDS = (
    "query_id",
    "document_id",
    "page_start",
    "page_end",
    "relevance",
    "verified_by",
    "verified_date",
    "verification_note",
)
POOL_FIELDS = (
    "query_id",
    "document_id",
    "page_start",
    "page_end",
    "seen_in_modes",
    "best_rank",
    "judgment",
)


def read_csv(path: Path, required: Sequence[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        missing = set(required) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path.name}: faltan columnas: {', '.join(sorted(missing))}")
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def load_questions(path: Path) -> list[dict[str, str]]:
    rows = read_csv(path, QUESTION_FIELDS)
    ids = [row["query_id"] for row in rows]
    if not rows or any(not value for value in ids):
        raise ValueError(f"{path.name}: cada pregunta necesita query_id")
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path.name}: query_id duplicado")
    return rows


def load_qrels(path: Path, question_ids: set[str]) -> dict[str, list[dict]]:
    rows = read_csv(path, QREL_FIELDS)
    by_query: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row["query_id"] not in question_ids:
            raise ValueError(f"{path.name}: query_id desconocido {row['query_id']!r}")
        try:
            start, end, relevance = (
                int(row["page_start"]),
                int(row["page_end"]),
                int(row["relevance"]),
            )
        except ValueError as exc:
            raise ValueError(f"{path.name}: páginas y relevancia deben ser enteros") from exc
        if start < 1 or end < start or relevance not in (0, 1):
            raise ValueError(f"{path.name}: qrel inválida para {row['query_id']}")
        if relevance and not (row["verified_by"] and row["verified_date"]):
            raise ValueError(
                f"{path.name}: qrel relevante {row['query_id']} debe declarar "
                "verified_by y verified_date"
            )
        by_query[row["query_id"]].append(
            {**row, "page_start": start, "page_end": end, "relevance": relevance}
        )
    return dict(by_query)


def result_is_relevant(result: Mapping, qrels: Sequence[Mapping]) -> bool:
    """True when document and page ranges overlap a positive human judgment."""
    return any(
        qrel["relevance"] == 1
        and result["document_id"] == qrel["document_id"]
        and result["page_start"] <= qrel["page_end"]
        and result["page_end"] >= qrel["page_start"]
        for qrel in qrels
    )


def result_judgment(result: Mapping, qrels: Sequence[Mapping]) -> str:
    """Return positive, explicit-negative or unjudged for a pooled result."""
    overlaps = [
        qrel
        for qrel in qrels
        if result["document_id"] == qrel["document_id"]
        and result["page_start"] <= qrel["page_end"]
        and result["page_end"] >= qrel["page_start"]
    ]
    if any(qrel["relevance"] == 1 for qrel in overlaps):
        return "positive"
    if any(qrel["relevance"] == 0 for qrel in overlaps):
        return "explicit-negative"
    return "unjudged"


def build_pool(results: Sequence[Mapping], qrels: Mapping[str, Sequence[Mapping]]) -> list[dict]:
    """Deduplicate top-k candidates across modes without storing book text."""
    pool: dict[tuple, dict] = {}
    for row in results:
        query_id = row["query_id"]
        for mode in MODES:
            for result in row["modes"][mode]["results"]:
                key = (
                    query_id,
                    result["document_id"],
                    result["page_start"],
                    result["page_end"],
                )
                entry = pool.setdefault(
                    key,
                    {
                        "query_id": query_id,
                        "document_id": result["document_id"],
                        "page_start": result["page_start"],
                        "page_end": result["page_end"],
                        "modes": set(),
                        "best_rank": result["rank"],
                    },
                )
                entry["modes"].add(mode)
                entry["best_rank"] = min(entry["best_rank"], result["rank"])
    rows = []
    for entry in pool.values():
        result = {
            "document_id": entry["document_id"],
            "page_start": entry["page_start"],
            "page_end": entry["page_end"],
        }
        rows.append(
            {
                "query_id": entry["query_id"],
                "document_id": entry["document_id"],
                "page_start": entry["page_start"],
                "page_end": entry["page_end"],
                "seen_in_modes": "|".join(mode for mode in MODES if mode in entry["modes"]),
                "best_rank": entry["best_rank"],
                "judgment": result_judgment(result, qrels.get(entry["query_id"], ())),
            }
        )
    return sorted(rows, key=lambda row: (row["query_id"], row["best_rank"], row["document_id"], row["page_start"]))


def write_pool(path: Path, rows: Sequence[Mapping]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=POOL_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def query_metrics(results: Sequence[Mapping], qrels: Sequence[Mapping]) -> dict[str, float]:
    # Several overlapping chunks can cite the same verified page. They are one
    # relevant item, not several gains: otherwise a single qrel can make nDCG
    # exceed 1 merely because chunk overlap returned it twice.
    positive = [q for q in qrels if q["relevance"] == 1]
    matched: set[int] = set()
    flags: list[bool] = []
    for result in results[:5]:
        match = next(
            (
                index
                for index, qrel in enumerate(positive)
                if index not in matched
                and result["document_id"] == qrel["document_id"]
                and result["page_start"] <= qrel["page_end"]
                and result["page_end"] >= qrel["page_start"]
            ),
            None,
        )
        flags.append(match is not None)
        if match is not None:
            matched.add(match)
    hit3 = float(any(flags[:3]))
    reciprocal_rank = next((1.0 / rank for rank, flag in enumerate(flags, 1) if flag), 0.0)
    dcg = sum((1.0 / math.log2(rank + 1)) for rank, flag in enumerate(flags, 1) if flag)
    relevant_total = len(
        {
            (q["document_id"], q["page_start"], q["page_end"])
            for q in positive
        }
    )
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(relevant_total, 5) + 1))
    return {"hit_at_3": hit3, "reciprocal_rank": reciprocal_rank, "ndcg_at_5": dcg / ideal if ideal else 0.0}


def mean_metrics(rows: Iterable[Mapping[str, float]]) -> dict[str, float]:
    rows = list(rows)
    if not rows:
        return {"hit_at_3": 0.0, "mrr": 0.0, "ndcg_at_5": 0.0}
    return {
        "hit_at_3": sum(row["hit_at_3"] for row in rows) / len(rows),
        "mrr": sum(row["reciprocal_rank"] for row in rows) / len(rows),
        "ndcg_at_5": sum(row["ndcg_at_5"] for row in rows) / len(rows),
    }


class RetrievalRunner:
    """Load vectors/model once, then rank every question in all three modes."""

    def __init__(self, index: Path):
        self.index = index
        self.config = json.loads((index / "index.json").read_text(encoding="utf-8"))
        stale = index_schema_error(self.config)
        if stale:
            raise SystemExit(stale)
        self.chunks = load_chunks(index / "chunks.jsonl")
        self.vectors = np.load(index / "embeddings.npy")
        self.model = TextEmbedding(model_name=self.config["model"])

    def rank(self, query: str, limit: int = 5, per_document: int = 2) -> dict[str, list[dict]]:
        dense_ids, dense_scores = dense_ranking(query, self.model, self.vectors)
        lexical_ids, lexical_scores = lexical_ranking(query, self.index / "search.sqlite")
        fused = reciprocal_rank_fusion([dense_ids[:100], lexical_ids[:100]])
        ordered = {
            "lexical": lexical_ids,
            "dense": dense_ids,
            "hybrid": sorted(fused, key=fused.get, reverse=True),
        }
        scores = {"lexical": lexical_scores, "dense": dense_scores, "hybrid": fused}
        output: dict[str, list[dict]] = {}
        for mode in MODES:
            selected = diversify(ordered[mode], self.chunks, limit, per_document)
            output[mode] = [
                {
                    "rank": rank,
                    "document_id": self.chunks[chunk_id]["document_id"],
                    "page_start": self.chunks[chunk_id]["page_start"],
                    "page_end": self.chunks[chunk_id]["page_end"],
                    "score": round(scores[mode][chunk_id], 6),
                }
                for rank, chunk_id in enumerate(selected, 1)
            ]
        return output


def markdown_report(payload: Mapping) -> str:
    provisional = payload["status"] == "provisional"
    judgment_note = (
        "Las métricas siguen la convención IR de tratar candidatos sin juicio como "
        "no relevantes. Por eso son provisionales: G4 debe revisar el pool, sobre "
        "todo los casos `unjudged`, antes de usarlas como benchmark definitivo. "
        "Como parte del gold set se descubrió desde los recuperadores comparados, "
        "las cifras absolutas pueden ser optimistas y la comparación no es plenamente "
        "independiente."
        if provisional
        else
        "Kristian aprobó G4 aceptando los candidatos `unjudged` como incompletitud "
        "documentada. Para calcular las métricas se tratan como no relevantes, según "
        "la convención IR declarada. Como parte del gold set se descubrió desde los "
        "recuperadores comparados, las cifras absolutas pueden ser optimistas y la "
        "comparación no es plenamente independiente."
    )
    lines = [
        "# Evaluación de recuperación — libros completos",
        "",
        (
            "Estado: **provisional**. Las páginas o sus imágenes renderizadas se "
            "inspeccionaron localmente y quedan "
            "pendientes de aprobación de Kristian en G4."
            if provisional
            else "Estado: **aprobado en G4**."
        ),
        "",
        "Resultados medidos contra páginas auditadas una por una. Los reportes",
        "contienen solo metadatos; no incluyen texto de los libros.",
        "",
        f'- Índice: `{payload["index"]}`',
        f'- Preguntas: {payload["questions"]}',
        f'- Qrels positivas: {payload["positive_qrels"]}',
        f'- Qrels negativas explícitas: {payload["negative_qrels"]}',
        (
            f'- Procedencia de las positivas: {payload["pooled_positive_qrels"]} '
            f'descubiertas en el pool y {payload["seeded_positive_qrels"]} '
            "sembradas independientemente"
        ),
        (
            f'- Pool top-5: {payload["pool_candidates"]} candidatos únicos; '
            f'{payload["pool_positive"]} positivos, {payload["pool_negative"]} '
            f'negativos explícitos y {payload["pool_unjudged"]} sin juzgar'
        ),
        "",
        judgment_note,
        "",
        "| modo | Hit@3 | MRR | nDCG@5 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for mode in MODES:
        metrics = payload["summary"][mode]
        lines.append(
            f'| {mode} | {metrics["hit_at_3"]:.3f} | {metrics["mrr"]:.3f} | '
            f'{metrics["ndcg_at_5"]:.3f} |'
        )
    lines.extend(["", "## Resultado por pregunta", ""])
    for row in payload["results"]:
        lines.append(f'### {row["query_id"]} — {row["query"]}')
        lines.append("")
        for mode in MODES:
            metrics = row["modes"][mode]["metrics"]
            lines.append(
                f'- {mode}: Hit@3 {metrics["hit_at_3"]:.0f}; '
                f'RR {metrics["reciprocal_rank"]:.3f}; nDCG@5 {metrics["ndcg_at_5"]:.3f}'
            )
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    root = Path(__file__).parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=root / "local_index_full")
    parser.add_argument("--questions", type=Path, default=root / "evaluation-questions.csv")
    parser.add_argument("--qrels", type=Path, default=root / "evaluation-qrels.csv")
    parser.add_argument("--report-md", type=Path, default=root / "evaluation-report-full-books.md")
    parser.add_argument("--report-json", type=Path, default=root / "evaluation-report-full-books.json")
    parser.add_argument("--pool", type=Path, default=root / "evaluation-pool-full-books.csv")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--per-document", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    questions = load_questions(args.questions)
    qrels = load_qrels(args.qrels, {row["query_id"] for row in questions})
    incomplete = [
        row["query_id"]
        for row in questions
        if not any(q["relevance"] == 1 for q in qrels.get(row["query_id"], ()))
    ]
    if incomplete:
        raise SystemExit(
            "Faltan qrels positivas verificadas para: " + ", ".join(incomplete)
            + ". Abrí los PDFs en las páginas candidatas y completa evaluation-qrels.csv."
        )
    runner = RetrievalRunner(args.index)
    results = []
    per_mode: dict[str, list[dict]] = defaultdict(list)
    for question in questions:
        ranked = runner.rank(question["query"], args.limit, args.per_document)
        modes = {}
        for mode in MODES:
            metrics = query_metrics(ranked[mode], qrels[question["query_id"]])
            per_mode[mode].append(metrics)
            modes[mode] = {"metrics": metrics, "results": ranked[mode]}
        results.append({"query_id": question["query_id"], "query": question["query"], "modes": modes})
    payload = {
        "index": str(args.index),
        "questions": len(questions),
        "positive_qrels": sum(q["relevance"] == 1 for rows in qrels.values() for q in rows),
        "negative_qrels": sum(q["relevance"] == 0 for rows in qrels.values() for q in rows),
        "pooled_positive_qrels": sum(
            q["relevance"] == 1 and "pooled top-five result" in q["verification_note"]
            for rows in qrels.values()
            for q in rows
        ),
        "seeded_positive_qrels": sum(
            q["relevance"] == 1 and "pooled top-five result" not in q["verification_note"]
            for rows in qrels.values()
            for q in rows
        ),
        "status": (
            "provisional"
            if any(
                "pending Kristian" in q["verification_note"]
                for rows in qrels.values()
                for q in rows
                if q["relevance"] == 1
            )
            else "approved"
        ),
        "summary": {mode: mean_metrics(per_mode[mode]) for mode in MODES},
        "results": results,
    }
    pool = build_pool(results, qrels)
    write_pool(args.pool, pool)
    pool_counts = {label: sum(row["judgment"] == label for row in pool) for label in (
        "positive", "explicit-negative", "unjudged"
    )}
    payload.update(
        {
            "pool_candidates": len(pool),
            "pool_positive": pool_counts["positive"],
            "pool_negative": pool_counts["explicit-negative"],
            "pool_unjudged": pool_counts["unjudged"],
        }
    )
    args.report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    args.report_md.write_text(markdown_report(payload), encoding="utf-8")
    print(markdown_report(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
