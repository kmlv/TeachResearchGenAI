#!/usr/bin/env python3
"""The only door into human/ and official/.

Two decisions live here: screening a candidate and verifying an evidence row.
Both require an interactive terminal and retyping the identifier, so a chat
message can never stand in for a decision. The agent contract forbids running
this script.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREENING_STATES = ("include", "exclude", "uncertain", "editorial_flag")
EVIDENCE_VERDICTS = ("verified", "rejected")

LEDGER_FIELDS = [
    "evidence_id",
    "source_id",
    "claim_id",
    "study_design",
    "population",
    "outcome",
    "verbatim_excerpt",
    "locator",
    "final_interpretation",
    "reviewer",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fieldnames(path: Path) -> list[str]:
    with path.open(encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle))


def write_rows(path: Path, columns: list[str], values: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(values)


def refresh_lock() -> None:
    lines = []
    for name in ("screening_decisions.csv", "evidence_verifications.csv"):
        digest = hashlib.sha256((ROOT / "human" / name).read_bytes()).hexdigest()
        lines.append(f"{name} {digest}")
    (ROOT / "human" / "decisions.lock").write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_trace(stage: str, item: str, event: str, artifact: str, result: str) -> None:
    path = ROOT / "TRACE.csv"
    with path.open("a", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerow(
            [datetime.now(timezone.utc).isoformat(), stage, item, event, artifact, result]
        )


def confirm(identifier: str, decision: str) -> None:
    if not sys.stdin.isatty():
        raise SystemExit("Human gate requires an interactive terminal")
    typed = input(f"Retype {identifier} to record '{decision}': ").strip()
    if typed != identifier:
        raise SystemExit("Decision cancelled: identifier did not match")


def screen(args: argparse.Namespace) -> None:
    pending_path = ROOT / "work" / "screening_pending.csv"
    pending = read_rows(pending_path)
    matches = [row for row in pending if row["record_id"] == args.id]
    if len(matches) != 1:
        raise SystemExit(
            f"Expected exactly one pending proposal for {args.id}; found {len(matches)}"
        )
    if not args.reason.strip():
        raise SystemExit("A screening decision needs a written reason")

    confirm(args.id, args.decision)

    decisions_path = ROOT / "human" / "screening_decisions.csv"
    decisions = [row for row in read_rows(decisions_path) if row["record_id"] != args.id]
    decisions.append(
        {
            "record_id": args.id,
            "human_decision": args.decision,
            "human_reason": args.reason,
            "reviewer": args.reviewer,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    decisions.sort(key=lambda row: row["record_id"])
    write_rows(decisions_path, fieldnames(decisions_path), decisions)

    write_rows(
        pending_path,
        fieldnames(pending_path),
        [row for row in pending if row["record_id"] != args.id],
    )
    refresh_lock()
    append_trace("screening", args.id, "human_decision", "human/screening_decisions.csv", args.decision)
    print(f"Recorded screening '{args.decision}' for {args.id} by {args.reviewer}")


def verify(args: argparse.Namespace) -> None:
    pending_path = ROOT / "work" / "evidence_pending.csv"
    pending = read_rows(pending_path)
    matches = [row for row in pending if row["evidence_id"] == args.id]
    if len(matches) != 1:
        raise SystemExit(
            f"Expected exactly one pending evidence row for {args.id}; found {len(matches)}"
        )
    proposal = matches[0]

    screening = {
        row["record_id"]: row
        for row in read_rows(ROOT / "human" / "screening_decisions.csv")
    }.get(proposal["source_id"])
    if args.decision == "verified":
        if screening is None:
            raise SystemExit(
                f"Cannot verify {args.id}: {proposal['source_id']} has no screening decision yet"
            )
        if screening["human_decision"] != "include":
            raise SystemExit(
                f"Cannot verify {args.id}: {proposal['source_id']} was screened as "
                f"'{screening['human_decision']}' and does not advance"
            )

    confirm(args.id, args.decision)

    verifications_path = ROOT / "human" / "evidence_verifications.csv"
    verifications = [
        row for row in read_rows(verifications_path) if row["evidence_id"] != args.id
    ]
    verifications.append(
        {
            "evidence_id": args.id,
            "source_id": proposal["source_id"],
            "verdict": args.decision,
            "human_correction": args.correction,
            "reviewer": args.reviewer,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    verifications.sort(key=lambda row: row["evidence_id"])
    write_rows(verifications_path, fieldnames(verifications_path), verifications)

    ledger_path = ROOT / "official" / "evidence_ledger.csv"
    ledger = [row for row in read_rows(ledger_path) if row["evidence_id"] != args.id]
    if args.decision == "verified":
        # The human correction, when present, is what becomes official. The
        # agent's own wording never reaches the ledger unedited by default.
        final = args.correction.strip() or proposal["ai_interpretation"]
        ledger.append(
            {
                "evidence_id": args.id,
                "source_id": proposal["source_id"],
                "claim_id": proposal["claim_id"],
                "study_design": proposal["study_design"],
                "population": proposal["population"],
                "outcome": proposal["outcome"],
                "verbatim_excerpt": proposal["verbatim_excerpt"],
                "locator": proposal["locator"],
                "final_interpretation": final,
                "reviewer": args.reviewer,
            }
        )
    ledger.sort(key=lambda row: row["evidence_id"])
    write_rows(ledger_path, LEDGER_FIELDS, ledger)

    # Either way the row leaves the queue. A rejected row can be proposed again
    # under the same evidence_id; the second decision replaces the first.
    write_rows(
        pending_path,
        fieldnames(pending_path),
        [row for row in pending if row["evidence_id"] != args.id],
    )
    refresh_lock()
    append_trace("evidence", args.id, "human_verification", "official/evidence_ledger.csv", args.decision)
    print(f"Recorded evidence '{args.decision}' for {args.id} by {args.reviewer}")


parser = argparse.ArgumentParser(description="Human review gate")
parser.add_argument("--kind", required=True, choices=("screening", "evidence"))
parser.add_argument("--id", required=True)
parser.add_argument("--decision", required=True)
parser.add_argument("--by", required=True, dest="reviewer")
parser.add_argument("--reason", default="", help="required for a screening decision")
parser.add_argument("--correction", default="", help="optional rewrite for an evidence row")
args = parser.parse_args()

if args.kind == "screening":
    if args.decision not in SCREENING_STATES:
        raise SystemExit(f"--decision must be one of {', '.join(SCREENING_STATES)}")
    screen(args)
else:
    if args.decision not in EVIDENCE_VERDICTS:
        raise SystemExit(f"--decision must be one of {', '.join(EVIDENCE_VERDICTS)}")
    verify(args)
