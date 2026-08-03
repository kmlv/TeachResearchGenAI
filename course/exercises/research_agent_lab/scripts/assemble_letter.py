#!/usr/bin/env python3
"""Build the response letter deterministically from the approved ledger."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_case.py"
spec = importlib.util.spec_from_file_location("validate_case", VALIDATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

with (ROOT / "official_ledger.csv").open(encoding="utf-8", newline="") as handle:
    ledger = list(csv.DictReader(handle))

expected = set(module.expected_points())
final = {"approve", "no_change"}
if {row["point_id"] for row in ledger} != expected or any(
    row["decision"] not in final for row in ledger
):
    raise SystemExit("Letter blocked: every referee point needs a final human decision")

failures = [failure for failure in module.validate() if not failure.startswith("assembly:")]
if failures:
    raise SystemExit("Letter blocked:\n- " + "\n- ".join(failures))

target = ROOT / "letter" / "response.md"
target.write_text(module.rendered_letter(ledger), encoding="utf-8")
print(f"Wrote {target.relative_to(ROOT)} from {len(ledger)} approved ledger rows")
