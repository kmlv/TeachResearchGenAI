@AGENTS.md

## Claude Code

- Use modo de planificación antes de una edición que toque más de un archivo.
- Use además `.agents/skills/literature-evidence/SKILL.md`.
- No solicite permisos amplios ni instale dependencias: el laboratorio corre
  con la biblioteca estándar de Python 3.
- Ninguna frase del chat cuenta como aprobación. Solo cuentan las filas que
  `scripts/review_gate.py` escribió en `human/` y `official/`.
- Al cerrar, muestre el diff y la salida de `python3 scripts/validate_review.py`.
