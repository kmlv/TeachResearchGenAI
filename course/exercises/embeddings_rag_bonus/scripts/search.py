from __future__ import annotations

import argparse
import json
import sqlite3
import warnings
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding

from common import (
    diversify,
    format_citation,
    format_page_range,
    index_schema_error,
    query_terms,
    reciprocal_rank_fusion,
    unit_rows,
)

warnings.filterwarnings(
    "ignore", message=r"The model .* now uses mean pooling instead of CLS embedding.*"
)


def load_chunks(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def dense_ranking(
    query: str, model: TextEmbedding, vectors: np.ndarray
) -> tuple[list[int], dict[int, float]]:
    query_vector = np.asarray(list(model.query_embed([query])), dtype=np.float32)
    query_vector = unit_rows(query_vector)[0]
    scores = vectors @ query_vector
    ranking = np.argsort(-scores).tolist()
    return ranking, {int(i): float(scores[i]) for i in ranking}


def lexical_ranking(query: str, database: Path) -> tuple[list[int], dict[int, float]]:
    match = query_terms(query)
    if not match:
        return [], {}
    connection = sqlite3.connect(database)
    try:
        rows = connection.execute(
            "SELECT chunk_id, bm25(chunks_fts) AS score FROM chunks_fts "
            "WHERE chunks_fts MATCH ? ORDER BY score LIMIT 100",
            (match,),
        ).fetchall()
    finally:
        connection.close()
    ranking = [int(row[0]) for row in rows]
    return ranking, {int(row[0]): float(-row[1]) for row in rows}


class SearchIndex:
    """An index held open across queries.

    `run_search` reloads the chunks, the vectors and the embedding model on
    every call, which is invisible from the command line and unusable from a
    server: the model alone costs seconds. This class is the same pipeline with
    the loading done once. `run_search` now delegates to it, so there is one
    ranking implementation and the demo retrieves exactly what the evaluation
    measured.
    """

    def __init__(self, path: Path, config: dict, chunks: list[dict]) -> None:
        self.path = path
        self.config = config
        self.chunks = chunks
        self._vectors: np.ndarray | None = None
        self._model: TextEmbedding | None = None

    @classmethod
    def load(cls, path: Path) -> "SearchIndex":
        config = json.loads((path / "index.json").read_text(encoding="utf-8"))
        stale = index_schema_error(config)
        if stale:
            raise SystemExit(stale)
        return cls(path, config, load_chunks(path / "chunks.jsonl"))

    @property
    def vectors(self) -> np.ndarray:
        if self._vectors is None:
            self._vectors = np.load(self.path / "embeddings.npy")
        return self._vectors

    @property
    def model(self) -> TextEmbedding:
        if self._model is None:
            self._model = TextEmbedding(model_name=self.config["model"])
        return self._model

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        """Unit vectors for arbitrary text, in the passage role.

        Used by the answer layer to score individual sentences of a retrieved
        passage against the question with the same model that retrieved it.
        """
        if not texts:
            return np.zeros((0, int(self.config["dimensions"])), dtype=np.float32)
        return unit_rows(np.asarray(list(self.model.embed(texts)), dtype=np.float32))

    def embed_query(self, query: str) -> np.ndarray:
        return unit_rows(
            np.asarray(list(self.model.query_embed([query])), dtype=np.float32)
        )[0]

    def search(
        self, query: str, mode: str = "hybrid", limit: int = 5, per_document: int = 1
    ) -> list[dict]:
        return _rank(query, self, mode, limit, per_document)


def run_search(
    query: str, index: Path, mode: str, limit: int, per_document: int = 1
) -> list[dict]:
    return _rank(query, SearchIndex.load(index), mode, limit, per_document)


def _rank(
    query: str, index: "SearchIndex", mode: str, limit: int, per_document: int
) -> list[dict]:
    chunks = index.chunks
    dense_ids: list[int] = []
    dense_scores: dict[int, float] = {}
    lexical_ids: list[int] = []
    lexical_scores: dict[int, float] = {}
    if mode != "lexical":
        dense_ids, dense_scores = dense_ranking(query, index.model, index.vectors)
    if mode != "dense":
        lexical_ids, lexical_scores = lexical_ranking(query, index.path / "search.sqlite")
    if mode == "dense":
        ordered = dense_ids
        final_scores = dense_scores
    elif mode == "lexical":
        ordered = lexical_ids
        final_scores = lexical_scores
    else:
        final_scores = reciprocal_rank_fusion([dense_ids[:100], lexical_ids[:100]])
        ordered = sorted(final_scores, key=final_scores.get, reverse=True)

    selected = diversify(ordered, chunks, limit=limit, per_document=per_document)
    results: list[dict] = []
    for rank, chunk_id in enumerate(selected, start=1):
        chunk = chunks[chunk_id]
        results.append(
            {
                "rank": rank,
                "mode": mode,
                # Metadata, never text: the answer layer looks the passage up
                # by id instead of carrying it through files that are committed.
                "chunk_id": chunk_id,
                "score": round(final_scores[chunk_id], 6),
                "dense_score": round(dense_scores.get(chunk_id, 0.0), 6),
                "lexical_score": round(lexical_scores.get(chunk_id, 0.0), 6),
                "document_id": chunk["document_id"],
                "title": chunk["title"],
                "author": chunk.get("author", ""),
                "year": chunk.get("year", ""),
                "category": chunk.get("category", ""),
                "page": chunk["page"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "citation": format_citation(
                    chunk.get("author", ""), chunk.get("year", ""), chunk["title"]
                ),
                "pages": format_page_range(chunk["page_start"], chunk["page_end"]),
                "relative_path": chunk["relative_path"],
                "preview": " ".join(chunk["text"].split()[:24]) + " …",
            }
        )
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument(
        "--index", type=Path, default=Path(__file__).parents[1] / "local_index"
    )
    parser.add_argument("--mode", choices=["lexical", "dense", "hybrid"], default="hybrid")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--per-document", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_search(
        args.query, args.index, args.mode, args.limit, args.per_document
    )
    if args.json:
        print(json.dumps({"query": args.query, "results": results}, ensure_ascii=False, indent=2))
        return
    print(f"Query: {args.query}\nMode: {args.mode}\n")
    for result in results:
        print(
            f'{result["rank"]}. {result["citation"]} — {result["pages"]} '
            f'(score {result["score"]:.4f})'
        )
        print(f'   {result["preview"]}')
        print(f'   {result["relative_path"]}\n')


if __name__ == "__main__":
    main()
