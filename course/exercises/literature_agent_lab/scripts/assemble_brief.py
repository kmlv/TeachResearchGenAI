#!/usr/bin/env python3
"""Build the evidence brief deterministically from the approved ledger."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_review.py"

spec = importlib.util.spec_from_file_location("validate_review", VALIDATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

with (ROOT / "official" / "evidence_ledger.csv").open(encoding="utf-8", newline="") as handle:
    ledger = list(csv.DictReader(handle))

if not ledger:
    raise SystemExit("Brief blocked: the official ledger is empty")

failures = [failure for failure in module.validate() if not failure.startswith("assembly:")]
if failures:
    raise SystemExit("Brief blocked:\n- " + "\n- ".join(failures))

target = ROOT / "output" / "review_brief.md"
target.write_text(module.rendered_brief(ledger), encoding="utf-8")
print(f"Wrote {target.relative_to(ROOT)} from {len(ledger)} verified ledger rows")
