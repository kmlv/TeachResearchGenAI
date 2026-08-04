# Salida

Esta carpeta está vacía a propósito.

`review_brief.md` **no se escribe a mano y no viene incluido**. Aparece solo
cuando `scripts/assemble_brief.py` lo genera a partir de
`official/evidence_ledger.csv`, y solo si `scripts/validate_review.py` pasa
antes. Si alguien crea el archivo por otra vía, el validador lo detecta y
bloquea.

Esa es la prueba pedagógica: el brief es una consecuencia del ledger aprobado,
no un documento independiente que se pueda mejorar por fuera.
