# Workspace reproducible para una mini-revisión

Esta carpeta convierte una revisión asistida por IA en archivos que otra
persona puede inspeccionar. No necesita una API. Puede usarse manualmente, en
un proyecto de ChatGPT o Claude, o como carpeta local con Codex o Claude Code.

El ejemplo trata sobre persuasión mediada por modelos de lenguaje. Sustituya
la pregunta y el protocolo para reutilizarlo en otro tema.

## Qué contiene

| Archivo | Función | Quién decide |
|---|---|---|
| `question.md` | Pregunta y alcance | Equipo investigador |
| `protocol.md` | Criterios y reglas de parada | Equipo investigador |
| `search_log.csv` | Plataforma, consulta, fecha y resultado | Persona que busca |
| `candidates.csv` | Propuesta de cribado y decisión humana | Humano |
| `evidence.csv` | Extracción con pasaje y localizador | Humano verifica |
| `synthesis.md` | Síntesis final desde filas verificadas | Equipo investigador |
| `AGENTS.md` | Reglas compartidas para Codex | Equipo investigador |
| `CLAUDE.md` | Hace que Claude Code lea las mismas reglas | Equipo investigador |
| `PROJECT-INSTRUCTIONS.md` | Reglas para pegar en proyectos de chat | Equipo investigador |
| `PROMPTS.md` | Solicitudes listas para copiar | — |

## Ruta A — ChatGPT o Claude como aplicación

1. Cree un proyecto nuevo.
2. Pegue `PROJECT-INSTRUCTIONS.md` en las instrucciones del proyecto.
3. Suba `question.md`, `protocol.md`, `search_log.csv`, `candidates.csv`,
   `evidence.csv`, `synthesis.md` y los textos que haya obtenido legalmente.
4. Copie una solicitud de `PROMPTS.md`.
5. Pida una propuesta, descargue el archivo y compare los cambios.
6. Marque una decisión o evidencia como verificada solo después de abrir la
   fuente.

La aplicación no conoce automáticamente la carpeta local. Si modifica un
archivo, descargue la nueva versión y conserve la anterior.

## Ruta B — Codex

En la aplicación de escritorio, cree o abra un proyecto local y añada esta
carpeta. En VS Code, abra la carpeta y comience un chat de Codex. También puede
iniciar el CLI desde la carpeta:

Use el inicio de sesión o plan que ya tenga; no cree ni pegue una clave API.

```bash
cd starter_workspace
codex
```

Solicitud inicial:

```text
Lee AGENTS.md, question.md y protocol.md. No edites todavía. Resume el estado
del flujo, enumera los archivos que faltan y propón una sola acción siguiente.
```

Antes de aceptar cambios, revise el diff y ejecute:

```bash
python3 validate_workspace.py
```

## Ruta C — Claude Code

Claude Code lee `CLAUDE.md`, que importa las mismas reglas de `AGENTS.md`:

Use el inicio de sesión o plan que ya tenga; no cree ni pegue una clave API.

```bash
cd starter_workspace
claude
```

Pegue la misma solicitud inicial. Use `/memory` para comprobar que
`CLAUDE.md` fue cargado. Revise los cambios antes de aceptarlos y ejecute el
mismo validador.

## Orden recomendado

1. Escribir pregunta y protocolo.
2. Buscar en una interfaz académica y registrar la consulta.
3. Importar o copiar metadatos a `candidates.csv`.
4. Pedir una propuesta de cribado; decidir cada fila humanamente.
5. Añadir solo textos obtenidos legalmente a `papers/`.
6. Extraer pasajes y localizadores a `evidence.csv`.
7. Verificar las filas utilizadas.
8. Redactar `synthesis.md` únicamente desde esas filas.

## Límite

Este paquete enseña trazabilidad. No convierte una consulta ni un corpus
pequeño en una revisión sistemática. Una revisión publicable necesita además
bases justificadas, deduplicación, cribado conforme al protocolo, evaluación
de calidad o riesgo de sesgo y reporte metodológico apropiado.

La carpeta `papers/` se entrega deliberadamente sin artículos completos. Para
probar la extracción, añada textos autorizados o use primero el corpus de cuatro
pasajes Juntos enlazado desde la guía pública.
