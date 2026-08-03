# Contrato del agente de respuesta a referees

## Objetivo

Cubrir exactamente una vez cada punto de `case/REFEREE_1.md` y
`case/REFEREE_2.md` con una respuesta propuesta, un anclaje verificable y, si
se afirma que el manuscrito cambiará, un diff real.

## Autoridad

Puede leer `case/`; escribir `pending.csv`, `changes/`, `STATE.json` y
`TRACE.csv`; y ejecutar `scripts/validate_case.py`. No puede ejecutar
`scripts/review_proposals.py`, editar `approvals.csv`, `approvals.lock`,
`official_ledger.csv` ni el manuscrito base. Solo puede crear
`letter/response.md` mediante `scripts/assemble_letter.py`, después de que el
validador confirme que los seis puntos tienen decisión final.

## Reglas

1. Procese un punto por vez y conserve su ID.
2. Cite un `M###` existente y copie su texto exacto en `evidence_quote`.
3. Si `response_type=change`, cree `changes/<POINT>.diff` con una línea eliminada
   y una agregada. Si `response_type=no_change`, explique por qué.
4. Nunca describa una propuesta como aprobada o aplicada.
5. Después de cada punto, actualice `STATE.json`, agregue una fila a `TRACE.csv`
   y ejecute `python3 scripts/validate_case.py`.
6. Si falta una decisión humana, deténgase y presente punto, anclaje y diff.
7. Un rechazo devuelve el punto a la cola: proponga una revisión y espere una
   segunda decisión sobre el mismo ID.

## Terminado cuando

Los seis puntos aparecen exactamente una vez, todos los anclajes y cambios
validan, cada punto tiene decisión humana, el ledger oficial coincide con esas
decisiones y la carta se puede ensamblar solo desde filas aprobadas o declaradas
sin cambio.
