#!/usr/bin/env python3
"""Regression tests for the gates, the reject/resume path, and exact assembly.

Every test builds a throwaway copy of the lab, so running this never disturbs
the shipped state. No test needs a model or a network connection.
"""

from __future__ import annotations

import csv
import os
import pty
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_FILES = (
    "STATE.json",
    "work/screening_pending.csv",
    "work/evidence_pending.csv",
    "human/screening_decisions.csv",
    "human/evidence_verifications.csv",
    "human/decisions.lock",
    "official/evidence_ledger.csv",
)

passed: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise AssertionError(f"{label} failed. {detail}".strip())
    passed.append(label)


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=root, text=True, capture_output=True, check=False)


def validator(root: Path) -> subprocess.CompletedProcess[str]:
    return run(root, "python3", "scripts/validate_review.py")


@contextmanager
def lab(fixture: str | None = None):
    """A disposable copy of the lab, optionally overlaid with a fixture."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "lab"
        shutil.copytree(ROOT, root)
        if fixture is not None:
            for name in FIXTURE_FILES:
                source = ROOT / "fixtures" / fixture / name
                if source.is_file():
                    shutil.copyfile(source, root / name)
        yield root


def read(root: Path, relative: str) -> list[dict[str, str]]:
    with (root / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write(root: Path, relative: str, columns: list[str], rows: list[dict[str, str]]) -> None:
    with (root / relative).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def gate(root: Path, *args: str) -> tuple[int, str]:
    """Drive the human gate through a pseudo-terminal and confirm the ID."""
    identifier = args[args.index("--id") + 1]
    master, slave = pty.openpty()
    process = subprocess.Popen(
        ["python3", "scripts/review_gate.py", *args],
        cwd=root,
        stdin=slave,
        stdout=slave,
        stderr=slave,
    )
    os.close(slave)
    os.write(master, f"{identifier}\n".encode())
    code = process.wait(timeout=15)
    os.close(master)
    return code, identifier


# 1. A fresh clone is honestly incomplete, not silently valid.
result = validator(ROOT)
check(
    "fresh clone reports the work that is missing",
    result.returncode == 1 and "screening: missing" in result.stdout,
    result.stdout,
)

# 2. The frozen question cannot drift under a finished screening.
with lab("waiting_gate") as root:
    question = root / "case" / "question.md"
    question.write_text(question.read_text(encoding="utf-8") + "\nY tambien conducta.\n", encoding="utf-8")
    check(
        "editing the frozen question is caught",
        "freeze: case/question.md changed" in validator(root).stdout,
        validator(root).stdout,
    )

# 3. Human files edited outside the gate are caught.
with lab("waiting_gate") as root:
    decisions = root / "human" / "screening_decisions.csv"
    decisions.write_text(
        decisions.read_text(encoding="utf-8").replace("T2,exclude", "T2,include"), encoding="utf-8"
    )
    check(
        "tampering with human decisions is caught",
        "gate: human/screening_decisions.csv changed outside" in validator(root).stdout,
        validator(root).stdout,
    )

# 4. An invented record identifier cannot enter screening.
with lab("waiting_gate") as root:
    rows = read(root, "work/screening_pending.csv")
    rows.append(
        {
            "record_id": "r99",
            "ai_proposal": "include",
            "ai_reason": "Titulo plausible",
            "proposed_at": "2026-08-03T12:00:00+00:00",
        }
    )
    write(root, "work/screening_pending.csv", ["record_id", "ai_proposal", "ai_reason", "proposed_at"], rows)
    check(
        "unknown record_id is rejected",
        "screening: unknown record_id r99" in validator(root).stdout,
        validator(root).stdout,
    )

# 5. An invented source identifier cannot anchor evidence.
with lab("waiting_gate") as root:
    rows = read(root, "work/evidence_pending.csv")
    rows[0]["source_id"] = "T9"
    write(root, "work/evidence_pending.csv", list(rows[0]), rows)
    check(
        "unknown source_id is rejected",
        "cites T9, which is not in the frozen packet" in validator(root).stdout,
        validator(root).stdout,
    )

# 6. A near-miss excerpt is not an excerpt.
with lab("waiting_gate") as root:
    rows = read(root, "work/evidence_pending.csv")
    rows[0]["verbatim_excerpt"] = rows[0]["verbatim_excerpt"].replace("3.4", "4.3")
    write(root, "work/evidence_pending.csv", list(rows[0]), rows)
    check(
        "an altered excerpt is caught",
        "EV-T1 excerpt does not match T1 exactly" in validator(root).stdout,
        validator(root).stdout,
    )

# 7. The shipped waiting_gate state already contains the two teaching errors.
with lab("waiting_gate") as root:
    output = validator(root).stdout
    check(
        "causal verb over an observational design is caught",
        "causal-language: EV-T3 uses 'redujo'" in output,
        output,
    )
    check(
        "a wrong locator is caught",
        "anchor: EV-T4 locator does not match T4" in output,
        output,
    )
    check(
        "unverified rows are reported as pending at the gate",
        "gate: human verification pending for EV-T1, EV-T3, EV-T4" in output,
        output,
    )

# 8. A wrong-population proposal cannot become official evidence.
with lab("waiting_gate") as root:
    packet_row = {
        "evidence_id": "EV-T2",
        "source_id": "T2",
        "claim_id": "C4",
        "study_design": "evaluación automatizada entre modelos",
        "population": "modelos de lenguaje",
        "intervention": "argumentos generados por distintos modelos",
        "comparator": "argumentos escritos por personas",
        "outcome": "calificación de calidad argumental otorgada por jueces",
        "verbatim_excerpt": (
            "Los argumentos del modelo recibieron mejores calificaciones de calidad "
            "que los argumentos humanos; las personas calificaron textos y no cambiaron su postura."
        ),
        "locator": "resumen, segunda oración",
        "ai_interpretation": "Los mensajes del modelo persuadieron mejor que los humanos.",
        "proposed_at": "2026-08-03T12:08:00+00:00",
    }
    rows = read(root, "work/evidence_pending.csv") + [packet_row]
    write(root, "work/evidence_pending.csv", list(rows[0]), rows)
    code, _ = gate(root, "--kind", "evidence", "--id", "EV-T2", "--decision", "verified", "--by", "Test")
    check("the gate refuses to verify an excluded record", code != 0)
    check(
        "the excluded record never reaches the ledger",
        not any(row["evidence_id"] == "EV-T2" for row in read(root, "official/evidence_ledger.csv")),
    )

# 9. The gate needs a terminal; a script cannot approve on its own.
with lab("waiting_gate") as root:
    denied = run(
        root, "python3", "scripts/review_gate.py",
        "--kind", "evidence", "--id", "EV-T1", "--decision", "verified", "--by", "Agent",
    )
    check(
        "the gate refuses to run without a terminal",
        denied.returncode == 1 and "interactive terminal" in denied.stderr,
        denied.stderr,
    )

# 10. A screening decision without a written reason is refused.
with lab("unstarted") as root:
    rows = [
        {
            "record_id": "T1",
            "ai_proposal": "include",
            "ai_reason": "Cumple los cuatro criterios",
            "proposed_at": "2026-08-03T12:00:00+00:00",
        }
    ]
    write(root, "work/screening_pending.csv", list(rows[0]), rows)
    denied = run(
        root, "python3", "scripts/review_gate.py",
        "--kind", "screening", "--id", "T1", "--decision", "include", "--by", "Test",
    )
    check(
        "a screening decision requires a reason",
        denied.returncode == 1 and "needs a written reason" in denied.stderr,
        denied.stderr,
    )

# 11. Reject, resume from state, re-propose, and verify the corrected row.
with lab("rejected") as root:
    output = validator(root).stdout
    check(
        "a rejected row leaves a visible hole",
        "evidence: no row yet for T3" in output,
        output,
    )
    revised = {
        "evidence_id": "EV-T3",
        "source_id": "T3",
        "claim_id": "C2",
        "study_design": "estudio observacional",
        "population": "adultos",
        "intervention": "uso voluntario de un asistente conversacional",
        "comparator": "personas que usaron el asistente con menor frecuencia",
        "outcome": "postura declarada en una segunda encuesta",
        "verbatim_excerpt": (
            "Quienes conversaron más veces con el asistente declararon posturas más "
            "moderadas en la segunda encuesta que quienes conversaron menos."
        ),
        "locator": "sección de resultados, primer párrafo",
        "ai_interpretation": (
            "Quienes conversaron más veces declararon posturas más moderadas; "
            "el diseño observacional no permite atribuir ese cambio al asistente."
        ),
        "proposed_at": "2026-08-03T12:29:00+00:00",
    }
    rows = read(root, "work/evidence_pending.csv") + [revised]
    write(root, "work/evidence_pending.csv", list(rows[0]), rows)
    check(
        "the re-proposed row is not treated as a duplicate",
        "duplicated" not in validator(root).stdout,
        validator(root).stdout,
    )
    code, _ = gate(root, "--kind", "evidence", "--id", "EV-T3", "--decision", "verified", "--by", "Facilitador")
    check("the corrected row can be verified on a second pass", code == 0)
    verification = {row["evidence_id"]: row for row in read(root, "human/evidence_verifications.csv")}
    check(
        "the second decision replaces the rejection",
        verification["EV-T3"]["verdict"] == "verified",
        verification["EV-T3"]["verdict"],
    )

# 12. The narrated demo path reaches a brief from waiting_gate, including EV-T4.
with lab("waiting_gate") as root:
    proposals = {
        row["evidence_id"]: row for row in read(root, "work/evidence_pending.csv")
    }
    for evidence_id, decision, correction in (
        ("EV-T1", "verified", ""),
        ("EV-T3", "rejected", "Diseño observacional: use lenguaje asociativo"),
        ("EV-T4", "rejected", "La fuente mide intención declarada, no conducta"),
    ):
        args = [
            "--kind", "evidence", "--id", evidence_id,
            "--decision", decision, "--by", "Facilitador",
        ]
        if correction:
            args.extend(("--correction", correction))
        code, _ = gate(root, *args)
        check(f"demo gate records {decision} for {evidence_id}", code == 0)

    revised_t3 = dict(proposals["EV-T3"])
    revised_t3["ai_interpretation"] = (
        "Quienes conversaron más veces declararon posturas más moderadas; "
        "el diseño observacional no permite atribuir ese cambio al asistente."
    )
    revised_t4 = dict(proposals["EV-T4"])
    revised_t4["locator"] = "sección de resultados, medidas secundarias"
    revised_t4["ai_interpretation"] = (
        "El mensaje aumentó la intención declarada de compartir; el estudio no "
        "midió conducta, así que el brief no puede afirmar comportamiento."
    )
    write(
        root,
        "work/evidence_pending.csv",
        list(revised_t3),
        [revised_t3, revised_t4],
    )
    for evidence_id in ("EV-T3", "EV-T4"):
        code, _ = gate(
            root,
            "--kind", "evidence", "--id", evidence_id,
            "--decision", "verified", "--by", "Facilitador",
        )
        check(f"demo verifies the corrected {evidence_id}", code == 0)

    check(
        "the full waiting_gate demo reaches a valid ledger",
        validator(root).returncode == 0,
        validator(root).stdout,
    )
    assembled = run(root, "python3", "scripts/assemble_brief.py")
    check(
        "the full waiting_gate demo assembles three verified rows",
        assembled.returncode == 0 and "from 3 verified ledger rows" in assembled.stdout,
        assembled.stdout + assembled.stderr,
    )

# 13. The brief assembles only from the ledger, exactly, and cannot be edited after.
with lab("ready") as root:
    check("the ready fixture passes every gate", validator(root).returncode == 0, validator(root).stdout)

    blocked_early = run(root, "python3", "scripts/assemble_brief.py")
    check("assembling from a complete ledger succeeds", blocked_early.returncode == 0, blocked_early.stderr)

    brief = root / "output" / "review_brief.md"
    check("the brief lists every verified row", brief.read_text(encoding="utf-8").count("## C") == 3)
    check(
        "the brief carries the synthetic-source warning",
        "sintéticas" in brief.read_text(encoding="utf-8"),
    )
    check("the assembled brief validates", validator(root).returncode == 0, validator(root).stdout)

    brief.write_text(
        brief.read_text(encoding="utf-8") + "\nLa evidencia demuestra causalidad.\n", encoding="utf-8"
    )
    check(
        "an edited brief is caught",
        "assembly: review_brief.md was not generated exactly from the ledger" in validator(root).stdout,
        validator(root).stdout,
    )

# 14. A brief cannot appear before the ledger is complete.
with lab("rejected") as root:
    (root / "output" / "review_brief.md").write_text("# Brief de evidencia\n", encoding="utf-8")
    check(
        "a premature brief is caught",
        "assembly: review_brief.md exists before the ledger is complete" in validator(root).stdout,
        validator(root).stdout,
    )
    blocked = run(root, "python3", "scripts/assemble_brief.py")
    check("assembly refuses to run while rows are open", blocked.returncode != 0, blocked.stdout)

# 15. An unverified row cannot be smuggled into the ledger by hand.
with lab("ready") as root:
    ledger = read(root, "official/evidence_ledger.csv")
    smuggled = dict(ledger[0])
    smuggled["evidence_id"] = "EV-T2"
    smuggled["source_id"] = "T2"
    write(root, "official/evidence_ledger.csv", list(ledger[0]), ledger + [smuggled])
    output = validator(root).stdout
    check(
        "a hand-written ledger row without a human verification is caught",
        "ledger: EV-T2 is official without a human verification" in output,
        output,
    )

print(f"PASS: {len(passed)} checks")
for label in passed:
    print(f"- {label}")
