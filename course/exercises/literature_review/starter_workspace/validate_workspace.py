#!/usr/bin/env python3
"""Valida estructura y separación entre propuestas de IA y decisiones humanas."""

from __future__ import annotations

import csv
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent

REQUIRED = {
    "question.md",
    "protocol.md",
    "search_log.csv",
    "candidates.csv",
    "evidence.csv",
    "synthesis.md",
    "AGENTS.md",
    "CLAUDE.md",
    "PROJECT-INSTRUCTIONS.md",
    "PROMPTS.md",
}

CANDIDATE_COLUMNS = {
    "record_id",
    "title",
    "year",
    "doi",
    "source",
    "ai_proposal",
    "ai_reason",
    "human_decision",
    "human_reason",
    "human_checked",
}

EVIDENCE_COLUMNS = {
    "record_id",
    "claim_id",
    "study_design",
    "population",
    "intervention",
    "comparator",
    "outcome",
    "verbatim_excerpt",
    "locator",
    "ai_interpretation",
    "human_correction",
    "human_verified",
}

ALLOWED_DECISIONS = {"", "include", "exclude", "uncertain", "editorial_flag", "pending"}
ALLOWED_CHECKS = {"", "yes", "no"}


def substantive_synthesis_lines(text: str) -> list[str]:
    """Return authored content while ignoring the shipped empty template."""
    placeholders = {"pendiente.", "pendiente", "-"}
    content: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.lower() in placeholders:
            continue
        if line.startswith("-") and line.endswith(":"):
            continue
        if line.startswith("**Estado:**"):
            continue
        content.append(line)
    return content


def read_rows(name: str) -> tuple[list[str], list[dict[str, str]]]:
    with (ROOT / name).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def main() -> int:
    errors: list[str] = []
    missing = sorted(name for name in REQUIRED if not (ROOT / name).exists())
    if missing:
        errors.append("Faltan archivos: " + ", ".join(missing))

    candidate_fields, candidates = read_rows("candidates.csv")
    if set(candidate_fields) != CANDIDATE_COLUMNS:
        errors.append("Columnas inesperadas en candidates.csv")

    seen: set[str] = set()
    for row_number, row in enumerate(candidates, start=2):
        record_id = row.get("record_id", "")
        if not record_id or record_id in seen:
            errors.append(f"Fila {row_number}: record_id vacío o duplicado")
        seen.add(record_id)
        for field in ("ai_proposal", "human_decision"):
            if row.get(field, "") not in ALLOWED_DECISIONS:
                errors.append(f"Fila {row_number}: {field} no permitido")
        if row.get("human_checked", "") not in ALLOWED_CHECKS:
            errors.append(f"Fila {row_number}: human_checked debe ser yes/no")
        if row.get("human_checked") == "yes" and not row.get("human_decision"):
            errors.append(f"Fila {row_number}: decisión humana verificada pero vacía")

    evidence_fields, evidence = read_rows("evidence.csv")
    if set(evidence_fields) != EVIDENCE_COLUMNS:
        errors.append("Columnas inesperadas en evidence.csv")

    verified_record_ids: set[str] = set()
    for row_number, row in enumerate(evidence, start=2):
        if row.get("human_verified", "") not in ALLOWED_CHECKS:
            errors.append(f"Evidencia {row_number}: human_verified debe ser yes/no")
        excerpt = row.get("verbatim_excerpt", "").strip()
        if excerpt and excerpt != "NO ENCONTRADO" and len(excerpt.split()) > 25:
            errors.append(f"Evidencia {row_number}: fragmento supera 25 palabras")
        if row.get("human_verified") == "yes" and not row.get("locator", "").strip():
            errors.append(f"Evidencia {row_number}: verificada sin localizador")
        if row.get("human_verified") == "yes":
            record_id = row.get("record_id", "").strip()
            if record_id not in seen:
                errors.append(f"Evidencia {row_number}: record_id no existe en candidates.csv")
            verified_record_ids.add(record_id)

    synthesis_text = (ROOT / "synthesis.md").read_text(encoding="utf-8")
    synthesis_body = synthesis_text.split("## Procedencia", maxsplit=1)[0]
    synthesis_content = substantive_synthesis_lines(synthesis_body)
    if synthesis_content and not verified_record_ids:
        errors.append("synthesis.md contiene contenido pero no hay evidencia verificada")
    if synthesis_content:
        candidate_dois = {
            row.get("record_id", "").strip(): row.get("doi", "").strip().lower()
            for row in candidates
        }
        verified_dois = {
            candidate_dois[record_id]
            for record_id in verified_record_ids
            if candidate_dois.get(record_id)
        }
        cited_ids = {match.lower() for match in re.findall(r"\br\d+\b", synthesis_body, re.I)}
        cited_dois = {
            match.rstrip(".,;)").lower()
            for match in re.findall(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", synthesis_body, re.I)
        }
        if not cited_ids and not cited_dois:
            errors.append("synthesis.md contiene contenido sin record_id o DOI")
        invalid_ids = sorted(cited_ids - {item.lower() for item in verified_record_ids})
        invalid_dois = sorted(cited_dois - verified_dois)
        if invalid_ids:
            errors.append("synthesis.md cita record_id no verificados: " + ", ".join(invalid_ids))
        if invalid_dois:
            errors.append("synthesis.md cita DOI no verificados: " + ", ".join(invalid_dois))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        "OK: workspace válido; "
        f"{len(candidates)} candidatos y {len(evidence)} filas de evidencia."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
