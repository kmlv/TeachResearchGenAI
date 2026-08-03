#!/usr/bin/env python3
"""Validate the generated data and the intended pedagogical failure."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    students = read_csv(ROOT / "data" / "estudiantes.csv")
    households = read_csv(ROOT / "data" / "caracteristicas_hogar.csv")
    metadata = json.loads((ROOT / "expected" / "metadata.json").read_text(encoding="utf-8"))
    covered = {row["hogar_id"] for row in households}
    selected = [row for row in students if row["hogar_id"] in covered]

    assert len(students) == metadata["student_rows_full"]
    assert len(selected) == metadata["student_rows_inner_merge"]
    assert len(students) - len(selected) == metadata["student_rows_lost"]
    assert len({row["estudiante_id"] for row in students}) == len(students)
    assert len({row["hogar_id"] for row in households}) == len(households)
    assert 0.70 <= len(selected) / len(students) <= 0.85

    zone_totals = Counter(row["zona"] for row in students)
    zone_matched = Counter(row["zona"] for row in selected)
    urban_rate = zone_matched["urbana"] / zone_totals["urbana"]
    rural_rate = zone_matched["rural"] / zone_totals["rural"]
    assert urban_rate - rural_rate >= 0.15, "La pérdida ya no es suficientemente desigual"

    for notebook in ("01_demo_inicial.ipynb", "02_demo_resuelto.ipynb"):
        payload = json.loads((ROOT / "notebooks" / notebook).read_text(encoding="utf-8"))
        assert payload["nbformat"] == 4
        assert payload["cells"]

    print("Demo validado")
    print(f"Estudiantes: {len(students)}")
    print(f"Inner merge: {len(selected)}")
    print(f"Pérdida: {len(students)-len(selected)} ({1-len(selected)/len(students):.1%})")
    print(f"Correspondencia urbana: {urban_rate:.1%}")
    print(f"Correspondencia rural: {rural_rate:.1%}")


if __name__ == "__main__":
    main()
