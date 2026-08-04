#!/usr/bin/env python3
"""Recompute the tripwire hashes for a lab root or a fixture.

Use this only when a change to the frozen case or to a fixture is deliberate.
Running it to silence a validator error is exactly the move the tripwire exists
to make visible, which is also why the tripwire is not security: whoever can
edit the files can also run this.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
CASE_FILES = ("question.md", "protocol.md", "source_packet.md")
HUMAN_FILES = ("screening_decisions.csv", "evidence_verifications.csv")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_lock(target: Path, names: tuple[str, ...], directory: Path) -> None:
    lines = [f"{name} {digest(directory / name)}" for name in names]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


parser = argparse.ArgumentParser(description="Recompute FREEZE.lock and decisions.lock")
parser.add_argument("--root", default=str(DEFAULT_ROOT))
parser.add_argument(
    "--human-only",
    action="store_true",
    help="fixtures carry only human/ files; skip the frozen case",
)
args = parser.parse_args()
root = Path(args.root).resolve()

if not args.human_only:
    write_lock(root / "case" / "FREEZE.lock", CASE_FILES, root / "case")
    print(f"wrote {root / 'case' / 'FREEZE.lock'}")

write_lock(root / "human" / "decisions.lock", HUMAN_FILES, root / "human")
print(f"wrote {root / 'human' / 'decisions.lock'}")
