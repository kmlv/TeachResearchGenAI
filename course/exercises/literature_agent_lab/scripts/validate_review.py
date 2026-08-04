#!/usr/bin/env python3
"""Deterministic gates for the integrated literature + agent teaching case.

Every check here is mechanical. None of them calls a model, and none of them
understands what a study means. They exist so that a plausible sentence cannot
become an official evidence row without a human decision behind it.

The hashes in `case/FREEZE.lock` and `human/decisions.lock` are pedagogical
tripwires that make silent edits visible. They are not operating-system
security: anyone with write access can recompute them.
"""

from __future__ import annotations

import csv
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREENING_STATES = {"include", "exclude", "uncertain", "editorial_flag"}
ADVANCING_STATES = {"include"}
PROTOCOL_POPULATION = "adultos"
CAUSAL_DESIGNS = {"experimento aleatorizado", "experimento de campo aleatorizado"}
EXCERPT_WORD_LIMIT = 25

# Lexical tripwire only. The validator cannot tell whether a claim is causal;
# it can tell whether a causal-sounding verb was written next to a design the
# frozen protocol does not accept for causal language. A careful sentence can
# still slip through, which is exactly why the human gate exists.
CAUSAL_VERBS = (
    "causa",
    "causó",
    "provoca",
    "provocó",
    "produce",
    "produjo",
    "el efecto de",
    "efecto causal",
    "reduce",
    "redujo",
    "hace que",
    "lleva a",
    "impacta",
    "impactó",
    "gracias a",
    "debido al asistente",
)


def rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_lock(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2:
            entries[parts[0]] = parts[1]
    return entries


def source_packet() -> dict[str, dict[str, str]]:
    """Parse the frozen packet into source_id -> declared fields plus excerpt."""
    text = (ROOT / "case" / "source_packet.md").read_text(encoding="utf-8")
    sources: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for line in text.splitlines():
        heading = re.match(r"^## (T\d+)\b", line)
        if heading:
            current = {"source_id": heading.group(1)}
            sources[heading.group(1)] = current
            continue
        if current is None:
            continue
        field = re.match(r"^- `([a-z_]+)`: (.+)$", line)
        if field:
            current[field.group(1)] = field.group(2).strip()
            continue
        if line.startswith("> ") and "excerpt" not in current:
            current["excerpt"] = line[2:].strip()
    return sources


def word_count(text: str) -> int:
    return len([token for token in re.split(r"\s+", text.strip()) if token])


def causal_verb_in(text: str) -> str | None:
    """Whole-word match only, so 'afirmación causal' does not trip on 'causa'."""
    lowered = text.lower()
    for verb in CAUSAL_VERBS:
        if re.search(rf"\b{re.escape(verb)}\b", lowered):
            return verb
    return None


def rendered_brief(ledger: list[dict[str, str]]) -> str:
    ordered = sorted(ledger, key=lambda row: (row["claim_id"], row["evidence_id"]))
    parts = [
        "# Brief de evidencia",
        "",
        "Ensamblado por `scripts/assemble_brief.py` desde `official/evidence_ledger.csv`.",
        "Cada afirmación proviene de una fila que una persona verificó con",
        "`scripts/review_gate.py`. No se puede agregar prosa por fuera: el validador",
        "compara este archivo carácter por carácter contra el ledger.",
        "",
        "AVISO · las fuentes T1-T4 son sintéticas y didácticas. No son citas de",
        "ningún artículo real.",
        "",
    ]
    for row in ordered:
        parts.extend(
            [
                f"## {row['claim_id']} · {row['evidence_id']}",
                "",
                row["final_interpretation"],
                "",
                f"- Fuente · {row['source_id']} ({row['study_design']}, {row['population']})",
                f"- Resultado medido · {row['outcome']}",
                f"- Pasaje · «{row['verbatim_excerpt']}»",
                f"- Localizador · {row['locator']}",
                f"- Verificado por · {row['reviewer']}",
                "",
            ]
        )
    return "\n".join(parts).rstrip() + "\n"


def validate() -> list[str]:
    errors: list[str] = []

    # 1. The frozen question and protocol must still be the ones that were screened.
    freeze = read_lock(ROOT / "case" / "FREEZE.lock")
    for name in ("question.md", "protocol.md", "source_packet.md"):
        expected = freeze.get(name)
        actual = sha256(ROOT / "case" / name)
        if expected is None:
            errors.append(f"freeze: FREEZE.lock has no entry for {name}")
        elif expected != actual:
            errors.append(f"freeze: case/{name} changed after the corpus was frozen")

    # 2. The human files must still be the ones the gate wrote.
    human_lock = read_lock(ROOT / "human" / "decisions.lock")
    for name in ("screening_decisions.csv", "evidence_verifications.csv"):
        expected = human_lock.get(name)
        actual = sha256(ROOT / "human" / name)
        if expected is None:
            errors.append(f"gate: decisions.lock has no entry for {name}")
        elif expected != actual:
            errors.append(f"gate: human/{name} changed outside scripts/review_gate.py")

    candidates = [row["record_id"] for row in rows("case/candidates.csv")]
    candidate_ids = set(candidates)
    packet = source_packet()

    screening_pending = rows("work/screening_pending.csv")
    screening_decided = rows("human/screening_decisions.csv")
    evidence_pending = rows("work/evidence_pending.csv")
    verifications = rows("human/evidence_verifications.csv")
    ledger = rows("official/evidence_ledger.csv")

    pending_map = {row["record_id"]: row for row in screening_pending}
    decided_map = {row["record_id"]: row for row in screening_decided}

    # 3. Screening: every candidate exactly once, no invented identifiers.
    unknown = sorted((set(pending_map) | set(decided_map)) - candidate_ids)
    if unknown:
        errors.append("screening: unknown record_id " + ", ".join(unknown))

    duplicated = {
        record_id
        for source in (screening_pending, screening_decided)
        for record_id, count in Counter(row["record_id"] for row in source).items()
        if count > 1
    }
    if duplicated:
        errors.append("screening: duplicated record_id " + ", ".join(sorted(duplicated)))

    overlap = sorted(set(pending_map) & set(decided_map))
    if overlap:
        errors.append("screening: still pending after a human decision " + ", ".join(overlap))

    covered = set(pending_map) | set(decided_map)
    missing = [record_id for record_id in candidates if record_id not in covered]
    if missing:
        errors.append("screening: missing " + ", ".join(missing))

    for record_id in sorted(decided_map):
        row = decided_map[record_id]
        decision = row.get("human_decision", "")
        if decision not in SCREENING_STATES:
            errors.append(f"screening: {record_id} has state '{decision}' outside the protocol")
        if not row.get("human_reason", "").strip():
            errors.append(f"screening: {record_id} has a decision without a written reason")

    if pending_map:
        errors.append("gate: screening decision pending for " + ", ".join(sorted(pending_map)))

    # 4. Evidence rows must anchor to the frozen packet, exactly.
    verification_map = {row["evidence_id"]: row for row in verifications}
    ledger_map = {row["evidence_id"]: row for row in ledger}
    proposal_map = {row["evidence_id"]: row for row in evidence_pending}

    duplicated_evidence = {
        evidence_id
        for source in (evidence_pending, ledger)
        for evidence_id, count in Counter(row["evidence_id"] for row in source).items()
        if count > 1
    }
    if duplicated_evidence:
        errors.append("evidence: duplicated evidence_id " + ", ".join(sorted(duplicated_evidence)))

    active_evidence = dict(ledger_map)
    active_evidence.update(proposal_map)

    for evidence_id in sorted(active_evidence):
        row = active_evidence[evidence_id]
        source_id = row.get("source_id", "")
        source = packet.get(source_id)
        if source is None:
            errors.append(
                f"anchor: {evidence_id} cites {source_id or '[blank]'}, "
                "which is not in the frozen packet"
            )
            continue
        if row.get("verbatim_excerpt", "") != source.get("excerpt", ""):
            errors.append(f"anchor: {evidence_id} excerpt does not match {source_id} exactly")
        if row.get("locator", "") != source.get("locator", ""):
            errors.append(f"anchor: {evidence_id} locator does not match {source_id}")
        if word_count(row.get("verbatim_excerpt", "")) > EXCERPT_WORD_LIMIT:
            errors.append(f"anchor: {evidence_id} excerpt exceeds {EXCERPT_WORD_LIMIT} words")
        if row.get("study_design", "") != source.get("design", ""):
            errors.append(f"design: {evidence_id} reports a design {source_id} does not declare")
        if row.get("population", "") != source.get("population", ""):
            errors.append(
                f"population: {evidence_id} reports a population {source_id} does not declare"
            )
        if row.get("outcome", "") != source.get("outcome", ""):
            errors.append(f"outcome: {evidence_id} reports an outcome {source_id} does not declare")

        interpretation = row.get("final_interpretation") or row.get("ai_interpretation", "")
        verb = causal_verb_in(interpretation)
        if verb and source.get("design", "") not in CAUSAL_DESIGNS:
            errors.append(
                f"causal-language: {evidence_id} uses '{verb}' but {source_id} declares "
                f"'{source.get('design', '')}'"
            )

    # 5. Only records screened as include may produce official evidence.
    required_sources = sorted(
        source_id
        for source_id in packet
        if decided_map.get(source_id, {}).get("human_decision") in ADVANCING_STATES
    )
    claimed_sources = {row.get("source_id", "") for row in active_evidence.values()}
    unclaimed = [source_id for source_id in required_sources if source_id not in claimed_sources]
    if unclaimed:
        errors.append("evidence: no row yet for " + ", ".join(unclaimed))

    # 6. Only a human decision moves a row into the official ledger.
    for evidence_id in sorted(ledger_map):
        row = ledger_map[evidence_id]
        verification = verification_map.get(evidence_id)
        if verification is None:
            errors.append(f"ledger: {evidence_id} is official without a human verification")
        elif verification.get("verdict") != "verified":
            errors.append(
                f"ledger: {evidence_id} is official but the human verdict is "
                f"'{verification.get('verdict', '')}'"
            )
        screening = decided_map.get(row.get("source_id", ""))
        if screening is None:
            errors.append(f"ledger: {evidence_id} descends from a record with no screening decision")
        elif screening.get("human_decision") not in ADVANCING_STATES:
            errors.append(
                f"ledger: {evidence_id} descends from a record screened as "
                f"'{screening.get('human_decision')}'"
            )
        if row.get("population", "") != PROTOCOL_POPULATION:
            errors.append(
                f"ledger: {evidence_id} has population '{row.get('population', '')}', "
                "which the protocol does not admit"
            )

    for evidence_id in sorted(set(verification_map) - set(ledger_map) - set(proposal_map)):
        if verification_map[evidence_id].get("verdict") == "verified":
            errors.append(f"ledger: {evidence_id} was verified but never reached the ledger")

    if proposal_map:
        errors.append("gate: human verification pending for " + ", ".join(sorted(proposal_map)))

    # 7. The brief is a consequence of the ledger, never an independent document.
    brief = ROOT / "output" / "review_brief.md"
    ready = (
        bool(ledger)
        and not proposal_map
        and not pending_map
        and all(source_id in claimed_sources for source_id in required_sources)
    )
    if brief.exists() and not ready:
        errors.append("assembly: review_brief.md exists before the ledger is complete")
    elif brief.exists() and brief.read_text(encoding="utf-8") != rendered_brief(ledger):
        errors.append("assembly: review_brief.md was not generated exactly from the ledger")

    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("BLOCKED")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)
    print("VALID: all deterministic gates pass")
