#!/usr/bin/env python3
"""Regression tests for gates, rejection recovery, and exact assembly."""

from __future__ import annotations

import csv
import hashlib
import os
import pty
import subprocess
import tempfile
from pathlib import Path
from shutil import copytree

ROOT = Path(__file__).resolve().parents[1]
POINTS = {
    "R1-01": "M001",
    "R1-02": "M006",
    "R1-03": "M009",
    "R2-01": "M003",
    "R2-02": "M008",
    "R2-03": "M010",
}


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=root, text=True, capture_output=True, check=False)


def validator(root: Path) -> subprocess.CompletedProcess[str]:
    return run(root, "python3", "scripts/validate_case.py")


def manuscript(root: Path) -> dict[str, str]:
    result = {}
    for line in (root / "case" / "MANUSCRIPT.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("M") and "|" in line:
            key, value = line.split("|", 1)
            result[key.strip()] = value.strip()
    return result


def write_proposals(root: Path, points: list[str]) -> None:
    source = manuscript(root)
    records = []
    for point in points:
        anchor = POINTS[point]
        change = f"changes/{point}.diff"
        (root / change).write_text(
            f"-{source[anchor]}\n+Revised wording for {point}.\n", encoding="utf-8"
        )
        records.append(
            {
                "point_id": point,
                "demand": f"Address {point}",
                "response_type": "change",
                "response_text": f"We address {point} with a bounded revision.",
                "evidence_line": anchor,
                "evidence_quote": source[anchor],
                "change_file": change,
            }
        )
    with (root / "pending.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=records[0])
        writer.writeheader()
        writer.writerows(records)


def human_review(root: Path, point: str, decision: str) -> int:
    master, slave = pty.openpty()
    process = subprocess.Popen(
        [
            "python3",
            "scripts/review_proposals.py",
            "--point",
            point,
            "--decision",
            decision,
            "--by",
            "Test Human",
        ],
        cwd=root,
        stdin=slave,
        stdout=slave,
        stderr=slave,
    )
    os.close(slave)
    os.write(master, f"{point}\n".encode())
    code = process.wait(timeout=10)
    os.close(master)
    return code


base = validator(ROOT)
assert base.returncode == 1 and "coverage: missing" in base.stdout

with tempfile.TemporaryDirectory() as tmp:
    lab = Path(tmp) / "lab"
    copytree(ROOT, lab)
    (lab / "approvals.csv").write_text(
        "point_id,decision,reviewer,timestamp\nR1-01,approve,agent,now\n", encoding="utf-8"
    )
    assert "gate: approvals.csv changed outside" in validator(lab).stdout

with tempfile.TemporaryDirectory() as tmp:
    lab = Path(tmp) / "lab"
    copytree(ROOT, lab)
    blocked = (ROOT / "fixtures" / "blocked" / "pending.csv").read_text(encoding="utf-8")
    (lab / "pending.csv").write_text(blocked, encoding="utf-8")
    assert "references missing M999" in validator(lab).stdout

with tempfile.TemporaryDirectory() as tmp:
    lab = Path(tmp) / "lab"
    copytree(ROOT, lab)
    write_proposals(lab, ["R1-01"])
    (lab / "changes" / "R1-01.diff").write_text(
        "-A plausible line that is not in the manuscript.\n+Invented robustness claim.\n",
        encoding="utf-8",
    )
    assert "does not remove its anchored manuscript line" in validator(lab).stdout

with tempfile.TemporaryDirectory() as tmp:
    lab = Path(tmp) / "lab"
    copytree(ROOT, lab)
    write_proposals(lab, list(POINTS))
    denied = run(
        lab,
        "python3",
        "scripts/review_proposals.py",
        "--point",
        "R1-01",
        "--decision",
        "approve",
        "--by",
        "Agent",
    )
    assert denied.returncode == 1 and "interactive terminal" in denied.stderr
    assert human_review(lab, "R2-02", "reject") == 0

    # A rejected point can return to pending without becoming a duplicate.
    remaining = list(POINTS)
    write_proposals(lab, remaining)
    recovery = validator(lab)
    assert "duplicated" not in recovery.stdout
    assert "human decision pending" in recovery.stdout

    for point in POINTS:
        assert human_review(lab, point, "approve") == 0
    digest = hashlib.sha256((lab / "approvals.csv").read_bytes()).hexdigest()
    assert (lab / "approvals.lock").read_text(encoding="utf-8").strip() == digest

    assembled = run(lab, "python3", "scripts/assemble_letter.py")
    assert assembled.returncode == 0, assembled.stderr
    assert validator(lab).returncode == 0
    letter = lab / "letter" / "response.md"
    letter.write_text(letter.read_text(encoding="utf-8") + "Invented claim.\n", encoding="utf-8")
    assert "not generated exactly" in validator(lab).stdout

print("PASS: coverage, anchors, anchored diffs, TTY gate, reject recovery, exact assembly, and tripwire")
