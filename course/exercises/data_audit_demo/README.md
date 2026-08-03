# Demo: pérdida silenciosa de observaciones

Mini-repositorio para enseñar auditoría de un análisis de datos con Jupyter en VS Code y Codex.

## Pregunta pedagógica

> ¿Qué patrones descriptivos muestran estos datos sobre asistencia escolar entre estudiantes de hogares que participan y no participan en Juntos?

Los datos son **sintéticos**. No representan estimaciones oficiales, no reproducen ENAHO y no permiten inferencia causal sobre Juntos.

## El problema intencional

`notebooks/01_demo_inicial.ipynb` une la base de estudiantes con una tabla auxiliar de hogares mediante un `inner merge`. La tabla auxiliar tiene cobertura incompleta y desigual. El código corre, pero desaparecen observaciones y cambia la composición de la muestra.

`notebooks/02_demo_resuelto.ipynb` muestra el flujo de auditoría:

1. contar antes y después;
2. usar un indicador de merge;
3. identificar quién desaparece;
4. revisar una corrección mínima;
5. añadir aserciones;
6. separar corrección técnica de interpretación causal.

## Estructura

```text
data_audit_demo/
├── data/
│   ├── estudiantes.csv
│   └── caracteristicas_hogar.csv
├── notebooks/
│   ├── 01_demo_inicial.ipynb
│   └── 02_demo_resuelto.ipynb
├── expected/
│   ├── metadata.json
│   └── resultados_esperados.md
├── scripts/
│   ├── generate_demo.py
│   └── validate_demo.py
├── requirements.txt
└── README.md
```

## Preparación rápida

Desde esta carpeta:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/validate_demo.py
code .
```

En VS Code:

1. selecciona `.venv` mediante **Python: Select Interpreter**;
2. abre el notebook inicial;
3. selecciona `.venv` mediante **Select Kernel**;
4. abre Codex en modo local;
5. reinicia el kernel y ejecuta el notebook desde arriba.

## Primer prompt recomendado

```text
Lee este notebook sin modificar archivos. Resume la pregunta empírica,
la población analítica y cada transformación que pueda cambiar el número
o la composición de las observaciones. Señala incertidumbres.
```

No abras primero el notebook resuelto durante el demo. Se conserva como fallback y como clave del facilitador.

## Regeneración

Los CSV, notebooks y resultados esperados se generan de forma determinista:

```bash
python scripts/generate_demo.py
python scripts/validate_demo.py
```
