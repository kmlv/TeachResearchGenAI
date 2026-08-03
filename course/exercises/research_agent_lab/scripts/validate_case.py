#!/usr/bin/env python3
"""Deterministic gates for the referee-response teaching case."""

from __future__ import annotations

import csv
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def expected_points() -> list[str]:
    text = "\n".join(
        (ROOT / "case" / name).read_text(encoding="utf-8")
        for name in ("REFEREE_1.md", "REFEREE_2.md")
    )
    return re.findall(r"^(R\d+-\d+)\s*\|", text, flags=re.MULTILINE)


def manuscript_lines() -> dict[str, str]:
    result: dict[str, str] = {}
    for line in (ROOT / "case" / "MANUSCRIPT.md").read_text(encoding="utf-8").splitlines():
        match = re.match(r"^(M\d+)\s*\|\s*(.*)$", line)
        if match:
            result[match.group(1)] = match.group(2)
    return result


def rendered_letter(ledger: list[dict[str, str]]) -> str:
    ordered = sorted(ledger, key=lambda row: row["point_id"])
    parts = ["# Response to referees", "", "Thank you for the careful reports.", ""]
    for row in ordered:
        parts.extend(
            [
                f"## {row['point_id']}",
                "",
                row["response_text"],
                "",
                f"Evidence anchor: {row['evidence_line']}",
                f"Decision: {row['decision']}",
                f"Change artifact: {row['change_file'] or 'no change proposed'}",
                "",
            ]
        )
    return "\n".join(parts).rstrip() + "\n"


def validate() -> list[str]:
    errors: list[str] = []
    expected = expected_points()
    pending = rows("pending.csv")
    ledger = rows("official_ledger.csv")
    approvals = rows("approvals.csv")

    pending_counts = Counter(row["point_id"] for row in pending)
    ledger_counts = Counter(row["point_id"] for row in ledger)
    pending_map = {row["point_id"]: row for row in pending}
    ledger_map = {row["point_id"]: row for row in ledger}
    active = dict(ledger_map)
    for point, row in pending_map.items():
        prior = ledger_map.get(point)
        if prior is None or prior.get("decision") == "reject":
            active[point] = row
    counts = Counter(active)
    missing = [point for point in expected if point not in counts]
    duplicates = [
        point
        for point in set(pending_counts) | set(ledger_counts)
        if pending_counts[point] > 1
        or ledger_counts[point] > 1
        or (
            pending_counts[point]
            and ledger_counts[point]
            and ledger_map[point].get("decision") != "reject"
        )
    ]
    unknown = [point for point in counts if point not in expected]
    if missing:
        errors.append("coverage: missing " + ", ".join(missing))
    if duplicates:
        errors.append("coverage: duplicated across pending/ledger " + ", ".join(duplicates))
    if unknown:
        errors.append("coverage: unknown " + ", ".join(unknown))

    manuscript = manuscript_lines()
    for point, row in active.items():
        anchor = row.get("evidence_line", "")
        quote = row.get("evidence_quote", "")
        if anchor not in manuscript:
            errors.append(f"anchor: {point} references missing {anchor or '[blank]'}")
        elif quote != manuscript[anchor]:
            errors.append(f"anchor: {point} quote does not match {anchor}")

        if row.get("response_type", "change") == "change":
            rel = row.get("change_file", "")
            path = (ROOT / rel).resolve()
            if not rel or ROOT.resolve() not in path.parents or not path.is_file():
                errors.append(f"change: {point} has no diff")
            else:
                lines = path.read_text(encoding="utf-8").splitlines()
                removed = [
                    line[1:]
                    for line in lines
                    if line.startswith("-") and not line.startswith("---")
                ]
                added = [
                    line[1:]
                    for line in lines
                    if line.startswith("+") and not line.startswith("+++")
                ]
                anchored_text = manuscript.get(anchor, "")
                if anchored_text not in removed:
                    errors.append(f"change: {point} diff does not remove its anchored manuscript line")
                if not any(text and text not in removed for text in added):
                    errors.append(f"change: {point} diff lacks a distinct added line")

    approval_bytes = (ROOT / "approvals.csv").read_bytes()
    actual_hash = hashlib.sha256(approval_bytes).hexdigest()
    locked_hash = (ROOT / "approvals.lock").read_text(encoding="utf-8").strip()
    if actual_hash != locked_hash:
        errors.append("gate: approvals.csv changed outside the human review command")

    approval_map = {row["point_id"]: row for row in approvals}
    for point, approval in approval_map.items():
        if point not in active:
            errors.append(f"gate: {point} approved without a proposal")
        if point not in ledger_map:
            errors.append(f"ledger: {point} has a decision but no official row")
        elif ledger_map[point].get("decision") != approval.get("decision"):
            errors.append(f"ledger: {point} decision disagrees with approvals.csv")

    awaiting = [
        point
        for point in active
        if point not in ledger_map
        or ledger_map[point].get("decision") not in {"approve", "no_change"}
        or point in pending_map
    ]
    if awaiting:
        errors.append("gate: human decision pending for " + ", ".join(sorted(awaiting)))

    letter = ROOT / "letter" / "response.md"
    final_decisions = {"approve", "no_change"}
    ready = (
        set(ledger_map) == set(expected)
        and all(row.get("decision") in final_decisions for row in ledger)
    )
    if letter.exists() and not ready:
        errors.append("assembly: response letter exists before all points are approved")
    elif letter.exists():
        actual = letter.read_text(encoding="utf-8")
        expected_letter = rendered_letter(ledger)
        if actual != expected_letter:
            errors.append("assembly: response letter was not generated exactly from the approved ledger")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("BLOCKED")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)
    print("VALID: all deterministic gates pass")
