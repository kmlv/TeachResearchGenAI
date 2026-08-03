#!/usr/bin/env python3
"""Explicit human gate: record one review decision and refresh its tripwire."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], values: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(values)


parser = argparse.ArgumentParser(description="Human review gate")
parser.add_argument("--point", required=True)
parser.add_argument("--decision", required=True, choices=("approve", "reject", "no_change"))
parser.add_argument("--by", required=True, dest="reviewer")
args = parser.parse_args()

if not sys.stdin.isatty():
    raise SystemExit("Human gate requires an interactive terminal")
confirmation = input(f"Retype {args.point} to record {args.decision}: ").strip()
if confirmation != args.point:
    raise SystemExit("Decision cancelled: point ID did not match")

pending_path = ROOT / "pending.csv"
pending = read_rows(pending_path)
matches = [row for row in pending if row["point_id"] == args.point]
if len(matches) != 1:
    raise SystemExit(f"Expected exactly one pending proposal for {args.point}; found {len(matches)}")
proposal = matches[0]
if args.decision == "no_change" and proposal["response_type"] != "no_change":
    raise SystemExit("no_change requires a proposal whose response_type is no_change")

now = datetime.now(timezone.utc).isoformat()
approval_path = ROOT / "approvals.csv"
approvals = [row for row in read_rows(approval_path) if row["point_id"] != args.point]
approvals.append({"point_id": args.point, "decision": args.decision, "reviewer": args.reviewer, "timestamp": now})
write_rows(approval_path, ["point_id", "decision", "reviewer", "timestamp"], approvals)
(ROOT / "approvals.lock").write_text(
    hashlib.sha256(approval_path.read_bytes()).hexdigest() + "\n", encoding="utf-8"
)

ledger_path = ROOT / "official_ledger.csv"
ledger = [row for row in read_rows(ledger_path) if row["point_id"] != args.point]
ledger.append(
    {
        "point_id": args.point,
        "decision": args.decision,
        "response_type": proposal["response_type"],
        "response_text": proposal["response_text"],
        "evidence_line": proposal["evidence_line"],
        "evidence_quote": proposal["evidence_quote"],
        "change_file": proposal["change_file"],
    }
)
write_rows(
    ledger_path,
    ["point_id", "decision", "response_type", "response_text", "evidence_line", "evidence_quote", "change_file"],
    ledger,
)

# A reviewed proposal moves from the pending queue into the official ledger.
write_rows(pending_path, list(proposal), [row for row in pending if row["point_id"] != args.point])
print(f"Recorded {args.decision} for {args.point} by {args.reviewer}")
