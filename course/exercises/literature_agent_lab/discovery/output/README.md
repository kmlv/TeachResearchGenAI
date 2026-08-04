# Esta carpeta se genera

Está vacía a propósito en una copia recién clonada. La llena
`scripts/search_openalex.py`:

| Archivo | Qué es |
| --- | --- |
| `raw/Q1.json` … | la respuesta tal cual, sin tocar (o `fixture-response.json` si no hubo red) |
| `candidates.csv` | los candidatos normalizados y sin duplicados |
| `dedup_report.csv` | qué se descartó, contra qué y por qué campo |
| `search_log.json` | modo, consultas, cuentas, tope aplicado y si hubo caída a la fixture |

Nada de esto se versiona: sale de `search_strategy.json` más la fuente. Si
necesita conservar una corrida concreta, cópiela fuera de aquí con una fecha en
el nombre.

**Ninguna fila de `candidates.csv` ha sido leída por nadie.** No es un cribado,
no es evidencia, y no entra sola a `case/`.
