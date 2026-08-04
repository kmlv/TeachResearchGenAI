#!/usr/bin/env python3
"""Única herramienta determinista del laboratorio de revisión guiada."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "PROGRESO.md"
BRIEF = ROOT / "BRIEF.md"

SOURCES = {
    "S1": {
        "title": "Mensajes generados por IA y credibilidad",
        "design": "experimento aleatorizado",
        "population": "240 personas adultas",
        "outcome": "credibilidad declarada en una escala de 1 a 7",
        "locator": "Resultados, párrafo 2",
        "excerpt": "Los participantes asignados al mensaje generado por IA calificaron su credibilidad 0,4 puntos más alta que el grupo control.",
        "match": "Compara mensajes y mide una respuesta declarada en personas adultas.",
    },
    "S2": {
        "title": "Uso de asistentes y disposición a compartir",
        "design": "estudio observacional transversal",
        "population": "510 personas adultas usuarias de redes sociales",
        "outcome": "disposición declarada a compartir mensajes políticos",
        "locator": "Resultados, párrafo 4",
        "excerpt": "El uso frecuente de asistentes de escritura se asoció con mayor disposición declarada a compartir mensajes políticos.",
        "match": "Relaciona uso de asistentes con una intención declarada en personas.",
    },
    "S3": {
        "title": "Evaluación automática de argumentos",
        "design": "evaluación computacional",
        "population": "respuestas producidas por modelos de lenguaje; no participaron personas",
        "outcome": "puntuación automática de coherencia",
        "locator": "Tabla 1",
        "excerpt": "El clasificador asignó puntuaciones mayores a los argumentos producidos por el modelo ajustado.",
        "match": "Comparte vocabulario, pero no estudia personas ni respuestas humanas.",
    },
}

CAUSAL_WORDS = ("caus", "efecto", "aumentó", "redujo", "provoc", "generó")


def field(text: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}:[ \t]*(.*)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def decisions(text: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        if not re.match(r"^\| S[123] \|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 5:
            rows[cells[0]] = {
                "decision": cells[1].lower(),
                "claim": cells[2],
                "reason": cells[3],
                "signature": cells[4],
            }
    return rows


def selected_ids(text: str) -> list[str]:
    raw = field(text, "Seleccionados")
    return [item.strip().upper() for item in raw.split(",") if item.strip()]


def validation_errors(text: str) -> list[str]:
    errors: list[str] = []
    researcher = field(text, "Investigador")
    question = field(text, "Pregunta")
    query = field(text, "Consulta")
    selected = selected_ids(text)
    rows = decisions(text)

    if not researcher:
        errors.append("falta el nombre del investigador")
    if not question:
        errors.append("falta la pregunta")
    if not query:
        errors.append("falta la consulta aprobada")
    if not 1 <= len(selected) <= 2:
        errors.append("seleccione una o dos entradas")
    for source_id in selected:
        if source_id not in SOURCES:
            errors.append(f"identificador desconocido: {source_id}")
            continue
        row = rows.get(source_id)
        if not row:
            errors.append(f"falta la fila de decisión para {source_id}")
            continue
        if row["decision"] not in {"aprobar", "reescribir", "excluir"}:
            errors.append(f"{source_id}: decisión pendiente o inválida")
        if not row["reason"]:
            errors.append(f"{source_id}: falta una razón")
        if not row["signature"]:
            errors.append(f"{source_id}: falta la firma")
        if row["decision"] in {"aprobar", "reescribir"} and not row["claim"]:
            errors.append(f"{source_id}: falta la afirmación aprobada")
        if source_id == "S2" and row["decision"] in {"aprobar", "reescribir"}:
            lowered = row["claim"].lower()
            if any(word in lowered for word in CAUSAL_WORDS):
                errors.append("S2: el diseño observacional no admite lenguaje causal")
    return errors


def cmd_search(query: str) -> int:
    print(f"BÚSQUEDA DIDÁCTICA · {query}")
    print("CANDIDATOS · todavía no son evidencia")
    for source_id, source in SOURCES.items():
        print(f"{source_id} | {source['title']} | {source['match']}")
    return 0


def cmd_show(source_id: str) -> int:
    source = SOURCES.get(source_id.upper())
    if not source:
        print(f"ERROR · identificador desconocido: {source_id}")
        return 2
    print(f"ENTRADA {source_id.upper()} · {source['title']}")
    print(f"DISEÑO · {source['design']}")
    print(f"POBLACIÓN · {source['population']}")
    print(f"RESULTADO · {source['outcome']}")
    print(f"LOCALIZADOR · {source['locator']}")
    print(f"TEXTO EXACTO · “{source['excerpt']}”")
    return 0


def cmd_validate() -> int:
    text = PROGRESS.read_text(encoding="utf-8")
    errors = validation_errors(text)
    if errors:
        print("BLOQUEADO")
        for error in errors:
            print(f"- {error}")
        return 1
    print("LISTO · decisiones completas; el brief puede generarse")
    return 0


def cmd_brief() -> int:
    text = PROGRESS.read_text(encoding="utf-8")
    errors = validation_errors(text)
    if errors:
        print("BLOQUEADO · el brief no fue generado")
        for error in errors:
            print(f"- {error}")
        return 1

    rows = decisions(text)
    selected = selected_ids(text)
    accepted = [sid for sid in selected if rows[sid]["decision"] != "excluir"]
    if not accepted:
        print("BLOQUEADO · ninguna entrada fue aprobada")
        return 1

    lines = [
        "# Brief de evidencia",
        "",
        f"**Pregunta:** {field(text, 'Pregunta')}",
        "",
        f"**Consulta registrada:** {field(text, 'Consulta')}",
        "",
        "> Este brief se generó desde decisiones humanas registradas. Las fuentes son sintéticas y didácticas.",
        "",
        "## Evidencia aprobada",
        "",
    ]
    for source_id in accepted:
        source = SOURCES[source_id]
        row = rows[source_id]
        lines.extend(
            [
                f"### {source_id} · {source['title']}",
                "",
                f"**Afirmación aprobada:** {row['claim']}",
                "",
                f"> “{source['excerpt']}”",
                "",
                f"**Localizador:** {source['locator']}  ",
                f"**Diseño:** {source['design']}  ",
                f"**Decisión:** {row['decision']} — {row['reason']}  ",
                f"**Firmó:** {row['signature']}",
                "",
            ]
        )

    excluded = [sid for sid in selected if rows[sid]["decision"] == "excluir"]
    if excluded:
        lines.extend(["## Exclusiones", ""])
        for source_id in excluded:
            row = rows[source_id]
            lines.append(f"- **{source_id}:** {row['reason']} — {row['signature']}")
        lines.append("")

    lines.extend(
        [
            "## Qué fue comprobado",
            "",
            "El programa comprobó que había una pregunta, una consulta, una o dos entradas seleccionadas y una decisión con razón y firma para cada una. También impidió lenguaje causal para la entrada observacional S2.",
            "",
            "La persona decidió si el pasaje sostenía la afirmación y si la fuente era pertinente. Esa parte no fue automatizada.",
            "",
        ]
    )
    BRIEF.write_text("\n".join(lines), encoding="utf-8")
    print("GENERADO · BRIEF.md")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    search = subparsers.add_parser("buscar")
    search.add_argument("--consulta", required=True)
    show = subparsers.add_parser("mostrar")
    show.add_argument("--id", required=True)
    subparsers.add_parser("validar")
    subparsers.add_parser("brief")
    args = parser.parse_args()

    if args.command == "buscar":
        return cmd_search(args.consulta)
    if args.command == "mostrar":
        return cmd_show(args.id)
    if args.command == "validar":
        return cmd_validate()
    return cmd_brief()


if __name__ == "__main__":
    raise SystemExit(main())
