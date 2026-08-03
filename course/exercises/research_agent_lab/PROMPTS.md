# Cinco encargos para Codex o Claude Code

## 1 · Orientarse

Lee `AGENTS.md`, la skill y todos los archivos de `case/`. Explica objetivo,
límites, artefactos, validadores y decisiones humanas. No edites nada.

## 2 · Inventariar

Extrae los seis IDs de referee. Inicializa `STATE.json` y `TRACE.csv`; informa
qué punto procesarás primero y por qué. No redactes la carta.

## 3 · Proponer

Procesa el próximo punto permitido. Agrega una sola fila a `pending.csv` con
anclaje exacto y crea un diff si propones cambio. Ejecuta el validador, actualiza
estado y detente ante la decisión humana.

## 4 · Reanudar

Lee `STATE.json`, las últimas filas de `TRACE.csv`, `pending.csv` y
`approvals.csv`. Resume último punto completo, pruebas, decisiones pendientes y
próxima acción permitida. No edites. Espera confirmación.

## 5 · Finalizar

Aplica únicamente decisiones humanas ya registradas y ejecuta el validador. Si
los seis puntos tienen decisión final, ejecuta `scripts/assemble_letter.py` y
valida otra vez. No edites el ledger ni la carta a mano; si algo bloquea,
informa la causa exacta.
