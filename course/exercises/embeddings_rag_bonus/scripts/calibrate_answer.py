"""Measure the similarity distribution the abstention rule depends on.

The demo has to decide, without a human in the loop, whether the corpus
contains an answer at all. That decision is a number compared against a
threshold, and a threshold invented at the desk is exactly the kind of
unexplained constant this course argues against. This script measures both
sides of the decision on the real index:

- the twelve evaluated questions, whose evidence was audited page by page;
- a control set of questions about things eighteen economics books do not
  discuss (a capital city, a drug dose, pruning an olive tree).

It prints the two distributions and the gap between them. `answer.py` states
its thresholds as constants with this measurement cited next to them; rerun
this script if the corpus or the embedding model changes.

Metadata only: it prints scores and document ids, never book text.
"""

from __future__ import annotations

import argparse
import csv
import json
import warnings
from datetime import date
from pathlib import Path

from common import abstention_statistic, calibrated_threshold
from search import SearchIndex

warnings.filterwarnings("ignore")

# Questions no economics library answers. Deliberately ordinary: a student
# types these by accident, and the demo has to say "not here" instead of
# returning the five least-bad paragraphs in the corpus with a straight face.
CONTROL_QUESTIONS = (
    "¿Cuál es la capital de Perú y cuántos habitantes tiene?",
    "¿Cómo se calibra un espectrómetro de masas de tiempo de vuelo?",
    "¿Qué dosis de amoxicilina se receta a un niño de veinte kilos?",
    "¿Quién ganó la final del mundial de fútbol de 2022?",
    "¿Cómo se poda un olivo joven en primavera?",
    "¿Qué dice el artículo 27 de la constitución mexicana sobre la tierra?",
    "¿Cuál es la receta tradicional del ceviche peruano?",
    "¿Cómo se trata una fractura de escafoides en la muñeca?",
)


def measure(
    index: SearchIndex, questions: list[str], limit: int, mode: str = "dense"
) -> list[dict]:
    """Score every question with the statistic the abstention rule uses.

    `abstention_statistic` rather than the score of rank 1: in hybrid mode the
    fused ordering can put a slightly less similar passage first, and a
    threshold is only meaningful when it is compared against the same quantity
    that `answer.py` will compute.
    """
    rows = []
    for question in questions:
        results = index.search(question, mode=mode, limit=limit, per_document=1)
        rows.append(
            {
                "query": question,
                "top_score": round(abstention_statistic(results), 4),
                "last_score": round(results[-1]["dense_score"], 4) if results else 0.0,
                "top_document": results[0]["document_id"] if results else "",
            }
        )
    return rows


def summarize(rows: list[dict]) -> dict:
    scores = sorted(row["top_score"] for row in rows)
    return {
        "count": len(scores),
        "min": round(scores[0], 4),
        "median": round(scores[len(scores) // 2], 4),
        "max": round(scores[-1], 4),
    }


def parse_args() -> argparse.Namespace:
    root = Path(__file__).parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=root / "local_index_full")
    parser.add_argument("--questions", type=Path, default=root / "evaluation-questions.csv")
    parser.add_argument("--mode", choices=["dense", "hybrid"], default="dense")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--write",
        action="store_true",
        help="escribir answer-calibration.json, que answer.py exige para responder",
    )
    parser.add_argument(
        "--calibration", type=Path, default=root / "answer-calibration.json"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.questions.open(encoding="utf-8") as stream:
        evaluated = [row["query"] for row in csv.DictReader(stream)]
    index = SearchIndex.load(args.index)
    answerable = measure(index, evaluated, args.limit, args.mode)
    unanswerable = measure(index, list(CONTROL_QUESTIONS), args.limit, args.mode)
    answerable_summary = summarize(answerable)
    unanswerable_summary = summarize(unanswerable)
    threshold = calibrated_threshold(
        answerable_summary["min"], unanswerable_summary["max"]
    )
    report = {
        "index": str(args.index),
        "mode": args.mode,
        "model": index.config["model"],
        "answerable": answerable_summary,
        "unanswerable": unanswerable_summary,
        **threshold,
    }
    if args.write:
        # Metadata only: the questions are ours, the scores are numbers, and no
        # book text is involved at any point of the measurement.
        args.calibration.write_text(
            json.dumps(
                {**report, "measured_on": date.today().isoformat(),
                 "questions": len(evaluated), "controls": len(CONTROL_QUESTIONS)},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    if args.json:
        print(json.dumps({"summary": report, "answerable": answerable,
                          "unanswerable": unanswerable}, ensure_ascii=False, indent=2))
        return
    print("Preguntas evaluadas (con evidencia auditada en el corpus)")
    for row in answerable:
        print(f"  {row['top_score']:.4f}  {row['top_document']:<24} {row['query'][:58]}")
    print("\nPreguntas de control (fuera del corpus)")
    for row in unanswerable:
        print(f"  {row['top_score']:.4f}  {row['top_document']:<24} {row['query'][:58]}")
    print(
        f"\nCon evidencia: min {report['answerable']['min']}, "
        f"mediana {report['answerable']['median']}, max {report['answerable']['max']}"
    )
    print(
        f"Sin evidencia: min {report['unanswerable']['min']}, "
        f"mediana {report['unanswerable']['median']}, max {report['unanswerable']['max']}"
    )
    print(f"Separación entre la peor con evidencia y la mejor sin evidencia: {report['gap']}")
    print(f"Umbral de abstención (modo {args.mode}): {report['min_top_score']}")
    if not report["separable"]:
        print(
            "Las dos distribuciones se solapan: ningún umbral las separa. El "
            "valor elegido abstiene sobre parte del solapamiento y answer.py "
            "imprime la advertencia."
        )
    if args.write:
        print(f"Calibración escrita en {args.calibration}")


if __name__ == "__main__":
    main()
