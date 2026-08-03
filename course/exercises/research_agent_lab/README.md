# Laboratorio: responder a referees con evidencia

Este caso sintético construye un agente útil en Codex o Claude Code. El agente
no «escribe una carta»: convierte seis observaciones en propuestas trazables,
un diff por cambio, una decisión humana por punto y, solo al final, una carta
ensamblada desde el ledger aprobado.

## Qué demuestra

- La diferencia entre prompt, workflow, loop, tool, skill y agente.
- Estado persistente: se puede cerrar la sesión y continuar desde `STATE.json`.
- Autoridad limitada: el agente escribe `pending.csv` y `changes/`; nunca decide
  en `approvals.csv`.
- Verificación determinista: cobertura, anclajes, cambios, gate y ensamblaje.

## Recorrido sugerido

1. Desde esta carpeta, pida a Codex o Claude Code que lea `AGENTS.md`,
   `PROMPTS.md` y el contenido de `case/` sin editar.
2. Use los encargos 1–3 de `PROMPTS.md` para crear propuestas.
3. Ejecute `python3 scripts/validate_case.py`: debe bloquear la carta mientras
   falten puntos, anclajes, diffs o decisiones.
4. La persona registra cada decisión con
   `python3 scripts/review_proposals.py --point R1-01 --decision approve --by NOMBRE`.
   El comando exige una terminal interactiva y volver a escribir el ID.
5. Reanude en una conversación nueva con el encargo 4. Ensamble la carta solo
   cuando el validador esté verde, usando `python3 scripts/assemble_letter.py`.

Un rechazo no cierra el caso: el agente vuelve a proponer el mismo ID y la
persona registra una segunda decisión, que reemplaza la anterior.

El manuscrito y los informes son deliberadamente sintéticos: enseñan el
proceso, no aportan evidencia empírica a la clase.

## Pruebas

```bash
python3 scripts/test_lab.py
```

El hash de `approvals.csv` es un *tripwire* didáctico contra ediciones
accidentales del agente; no es una frontera de seguridad frente a alguien con
control total del sistema de archivos.
