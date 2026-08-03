#!/usr/bin/env python3
"""Generate deterministic synthetic data and notebooks for the data-audit demo."""

from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
NOTEBOOK_DIR = ROOT / "notebooks"
EXPECTED_DIR = ROOT / "expected"
SEED = 20260802


DISTRICTS = [
    ("Distrito_A", "urbana", 0.96),
    ("Distrito_B", "urbana", 0.90),
    ("Distrito_C", "rural", 0.73),
    ("Distrito_D", "rural", 0.58),
    ("Distrito_E", "rural", 0.66),
]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def generate_rows() -> tuple[list[dict], list[dict]]:
    rng = random.Random(SEED)
    students: list[dict] = []
    households: list[dict] = []
    student_number = 1

    for household_number in range(1, 361):
        household_id = f"H{household_number:04d}"
        district, area, coverage = rng.choice(DISTRICTS)
        rural = area == "rural"
        juntos_probability = 0.58 if rural else 0.20
        juntos = int(rng.random() < juntos_probability)
        household_size = rng.randint(3, 7)
        expenditure = round(rng.uniform(180, 620) - 70 * rural - 35 * juntos, 2)

        # The auxiliary household module is intentionally incomplete. Coverage
        # is lower in rural districts, especially Distrito_D.
        if rng.random() < coverage:
            households.append(
                {
                    "hogar_id": household_id,
                    "miembros_hogar": household_size,
                    "gasto_per_capita": max(60.0, expenditure),
                }
            )

        for _ in range(rng.randint(1, 3)):
            age = rng.randint(6, 17)
            sex = rng.choice(["mujer", "hombre"])
            attendance_probability = (
                0.84
                + 0.045 * juntos
                - 0.075 * rural
                - 0.018 * max(age - 14, 0)
                + (0.018 if sex == "mujer" else 0)
            )
            attendance_probability = clamp(attendance_probability, 0.55, 0.97)
            students.append(
                {
                    "estudiante_id": f"E{student_number:05d}",
                    "hogar_id": household_id,
                    "edad": age,
                    "sexo": sex,
                    "zona": area,
                    "distrito": district,
                    "juntos": juntos,
                    "asiste_regularmente": int(rng.random() < attendance_probability),
                }
            )
            student_number += 1

    return students, households


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(students: list[dict], households: list[dict]) -> dict:
    covered = {row["hogar_id"] for row in households}
    selected = [row for row in students if row["hogar_id"] in covered]

    def attendance(rows: list[dict], group: int) -> float:
        values = [int(row["asiste_regularmente"]) for row in rows if int(row["juntos"]) == group]
        return sum(values) / len(values)

    full_rate = {str(group): attendance(students, group) for group in (0, 1)}
    selected_rate = {str(group): attendance(selected, group) for group in (0, 1)}
    by_zone = defaultdict(lambda: [0, 0])
    by_district = defaultdict(lambda: [0, 0])
    for row in students:
        matched = int(row["hogar_id"] in covered)
        for key, store in ((row["zona"], by_zone), (row["distrito"], by_district)):
            store[key][0] += matched
            store[key][1] += 1

    return {
        "seed": SEED,
        "student_rows_full": len(students),
        "student_rows_inner_merge": len(selected),
        "student_rows_lost": len(students) - len(selected),
        "overall_match_rate": len(selected) / len(students),
        "households_expected": len({row["hogar_id"] for row in students}),
        "households_auxiliary": len(households),
        "attendance_full": full_rate,
        "attendance_inner_merge": selected_rate,
        "descriptive_gap_full": full_rate["1"] - full_rate["0"],
        "descriptive_gap_inner_merge": selected_rate["1"] - selected_rate["0"],
        "match_rate_by_zone": {
            key: matched / total for key, (matched, total) in sorted(by_zone.items())
        },
        "match_rate_by_district": {
            key: matched / total for key, (matched, total) in sorted(by_district.items())
        },
        "students_by_zone": dict(Counter(row["zona"] for row in students)),
    }


def markdown_cell(source: str, cell_id: str) -> dict:
    return {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": source.splitlines(True)}


def code_cell(source: str, cell_id: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cell_id,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(True),
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def initial_notebook() -> dict:
    return notebook(
        [
            markdown_cell(
                "# Demo inicial: Juntos y asistencia escolar\n\n"
                "**Datos sintéticos.** Pregunta descriptiva: ¿qué patrones muestran estos datos sobre "
                "asistencia escolar entre estudiantes de hogares que participan y no participan en Juntos?\n\n"
                "> Este ejercicio no identifica efectos causales.",
                "intro",
            ),
            code_cell(
                "from pathlib import Path\nimport pandas as pd\n\n"
                "CANDIDATES = [\n"
                "    Path.cwd(),\n"
                "    Path.cwd() / 'course/exercises/data_audit_demo',\n"
                "    Path.cwd().parent,\n"
                "]\n"
                "ROOT = next(\n"
                "    (p for p in CANDIDATES if (p / 'data/estudiantes.csv').exists()),\n"
                "    None,\n"
                ")\n"
                "if ROOT is None:\n"
                "    raise FileNotFoundError('Abre la carpeta data_audit_demo o la raíz del repositorio')\n"
                "DATA = ROOT / 'data'\n"
                "print('Raíz del demo:', ROOT.resolve())",
                "setup",
            ),
            code_cell(
                "estudiantes = pd.read_csv(DATA / 'estudiantes.csv')\n"
                "hogares = pd.read_csv(DATA / 'caracteristicas_hogar.csv')\n\n"
                "estudiantes.head()",
                "load",
            ),
            markdown_cell("## Construcción de la base analítica", "merge-title"),
            code_cell(
                "analisis = estudiantes.merge(\n"
                "    hogares,\n"
                "    on='hogar_id',\n"
                "    how='inner',\n"
                ")\n\n"
                "print(f'Base analítica: {len(analisis):,} estudiantes')",
                "inner-merge",
            ),
            code_cell(
                "tabla_inicial = (\n"
                "    analisis.groupby('juntos', as_index=False)\n"
                "    .agg(\n"
                "        estudiantes=('estudiante_id', 'size'),\n"
                "        asistencia_media=('asiste_regularmente', 'mean'),\n"
                "    )\n"
                ")\n"
                "tabla_inicial['asistencia_media'] = tabla_inicial['asistencia_media'].round(3)\n"
                "tabla_inicial",
                "initial-table",
            ),
            markdown_cell(
                "## Antes de interpretar\n\n"
                "Pide a Codex que explique el análisis e identifique operaciones capaces de cambiar el "
                "número o la composición de las observaciones. No le pidas todavía que corrija el código.",
                "prompt-cue",
            ),
        ]
    )


def resolved_notebook() -> dict:
    return notebook(
        [
            markdown_cell(
                "# Demo resuelto: auditar antes de interpretar\n\n"
                "**Clave del facilitador.** Los datos son sintéticos y el objetivo es hacer visible una "
                "pérdida no aleatoria de observaciones.",
                "intro",
            ),
            code_cell(
                "from pathlib import Path\nimport pandas as pd\n\n"
                "CANDIDATES = [\n"
                "    Path.cwd(),\n"
                "    Path.cwd() / 'course/exercises/data_audit_demo',\n"
                "    Path.cwd().parent,\n"
                "]\n"
                "ROOT = next(\n"
                "    (p for p in CANDIDATES if (p / 'data/estudiantes.csv').exists()),\n"
                "    None,\n"
                ")\n"
                "if ROOT is None:\n"
                "    raise FileNotFoundError('Abre la carpeta data_audit_demo o la raíz del repositorio')\n"
                "DATA = ROOT / 'data'",
                "setup",
            ),
            code_cell(
                "estudiantes = pd.read_csv(DATA / 'estudiantes.csv')\n"
                "hogares = pd.read_csv(DATA / 'caracteristicas_hogar.csv')\n\n"
                "print(f'Estudiantes antes del merge: {len(estudiantes):,}')\n"
                "print(f'Hogares en tabla auxiliar: {len(hogares):,}')",
                "load-count",
            ),
            markdown_cell("## 1. Conservar todas las observaciones durante la auditoría", "audit-title"),
            code_cell(
                "auditoria = estudiantes.merge(\n"
                "    hogares,\n"
                "    on='hogar_id',\n"
                "    how='left',\n"
                "    indicator=True,\n"
                "    validate='many_to_one',\n"
                ")\n\n"
                "conteo_merge = auditoria['_merge'].value_counts(dropna=False)\n"
                "conteo_merge",
                "left-merge",
            ),
            code_cell(
                "auditoria['en_tabla_auxiliar'] = auditoria['_merge'].eq('both')\n\n"
                "tasas_zona = (\n"
                "    auditoria.groupby('zona')['en_tabla_auxiliar']\n"
                "    .agg(['count', 'mean'])\n"
                "    .rename(columns={'count': 'estudiantes', 'mean': 'tasa_correspondencia'})\n"
                ")\n"
                "tasas_zona['tasa_correspondencia'] = tasas_zona['tasa_correspondencia'].round(3)\n"
                "tasas_zona",
                "rates-zone",
            ),
            code_cell(
                "tasas_distrito = (\n"
                "    auditoria.groupby('distrito')['en_tabla_auxiliar']\n"
                "    .agg(['count', 'mean'])\n"
                "    .rename(columns={'count': 'estudiantes', 'mean': 'tasa_correspondencia'})\n"
                "    .sort_values('tasa_correspondencia')\n"
                ")\n"
                "tasas_distrito['tasa_correspondencia'] = tasas_distrito['tasa_correspondencia'].round(3)\n"
                "tasas_distrito",
                "rates-district",
            ),
            markdown_cell("## 2. Convertir el diagnóstico en comprobaciones", "checks-title"),
            code_cell(
                "assert len(auditoria) == len(estudiantes), 'El merge cambió el número de estudiantes'\n"
                "assert auditoria['estudiante_id'].is_unique, 'Se duplicaron estudiantes'\n"
                "assert auditoria['en_tabla_auxiliar'].mean() >= 0.70, 'Cobertura auxiliar demasiado baja'\n\n"
                "print('Comprobaciones superadas')",
                "assertions",
            ),
            markdown_cell(
                "## 3. Responder la pregunta con la población adecuada\n\n"
                "La característica auxiliar no es necesaria para calcular el descriptivo principal. Por "
                "eso usamos la base completa de estudiantes y reportamos la cobertura auxiliar por separado.",
                "analysis-title",
            ),
            code_cell(
                "tabla_auditada = (\n"
                "    estudiantes.groupby('juntos', as_index=False)\n"
                "    .agg(\n"
                "        estudiantes=('estudiante_id', 'size'),\n"
                "        asistencia_media=('asiste_regularmente', 'mean'),\n"
                "    )\n"
                ")\n"
                "tabla_auditada['asistencia_media'] = tabla_auditada['asistencia_media'].round(3)\n"
                "tabla_auditada",
                "audited-table",
            ),
            code_cell(
                "muestra_completa = estudiantes[['estudiante_id', 'juntos', 'asiste_regularmente']]\n"
                "muestra_reducida = auditoria.loc[auditoria['en_tabla_auxiliar']]\n\n"
                "comparacion = pd.DataFrame({\n"
                "    'muestra': ['completa', 'inner merge'],\n"
                "    'n': [len(muestra_completa), len(muestra_reducida)],\n"
                "    'brecha_descriptiva': [\n"
                "        muestra_completa.groupby('juntos')['asiste_regularmente'].mean().diff().iloc[-1],\n"
                "        muestra_reducida.groupby('juntos')['asiste_regularmente'].mean().diff().iloc[-1],\n"
                "    ],\n"
                "})\n"
                "comparacion['brecha_descriptiva'] = comparacion['brecha_descriptiva'].round(3)\n"
                "comparacion",
                "sensitivity",
            ),
            markdown_cell(
                "## 4. Interpretación\n\n"
                "La tabla auditada describe diferencias en estos datos sintéticos. No demuestra que "
                "Juntos cause cambios en asistencia: participación y asistencia pueden estar relacionadas "
                "con ruralidad, selección, territorio y otras características no observadas.",
                "interpretation",
            ),
        ]
    )


def write_notebook(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def write_expected(metadata: dict) -> None:
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    (EXPECTED_DIR / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Resultados esperados",
        "",
        "Datos sintéticos; no son resultados oficiales sobre Juntos.",
        "",
        f"- Estudiantes antes del merge: **{metadata['student_rows_full']}**.",
        f"- Estudiantes después del inner merge: **{metadata['student_rows_inner_merge']}**.",
        f"- Observaciones perdidas: **{metadata['student_rows_lost']}**.",
        f"- Tasa global de correspondencia: **{metadata['overall_match_rate']:.1%}**.",
        f"- Brecha descriptiva, muestra completa: **{metadata['descriptive_gap_full']:.3f}**.",
        f"- Brecha descriptiva, inner merge: **{metadata['descriptive_gap_inner_merge']:.3f}**.",
        "",
        "## Tasa de correspondencia por zona",
        "",
    ]
    for zone, rate in metadata["match_rate_by_zone"].items():
        lines.append(f"- {zone}: **{rate:.1%}**")
    lines.extend(["", "## Tasa por distrito", ""])
    for district, rate in metadata["match_rate_by_district"].items():
        lines.append(f"- {district}: **{rate:.1%}**")
    lines.extend(
        [
            "",
            "## Resultado pedagógico",
            "",
            "El `inner merge` produce una muestra menor y con composición distinta. La corrección técnica "
            "no autoriza una interpretación causal.",
            "",
        ]
    )
    (EXPECTED_DIR / "resultados_esperados.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    students, households = generate_rows()
    write_csv(DATA_DIR / "estudiantes.csv", students)
    write_csv(DATA_DIR / "caracteristicas_hogar.csv", households)
    metadata = summarize(students, households)
    write_expected(metadata)
    write_notebook(NOTEBOOK_DIR / "01_demo_inicial.ipynb", initial_notebook())
    write_notebook(NOTEBOOK_DIR / "02_demo_resuelto.ipynb", resolved_notebook())
    print(f"Generated {len(students)} students and {len(households)} auxiliary households")
    print(f"Silent loss: {metadata['student_rows_lost']} rows ({1-metadata['overall_match_rate']:.1%})")


if __name__ == "__main__":
    main()
