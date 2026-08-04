# Contrato del agente de evidencia

## Objetivo

Producir un brief de evidencia trazable sobre la pregunta congelada en
`case/question.md`: cada afirmación del brief debe descansar en una fila del
ledger oficial que una persona verificó, con pasaje textual y localizador.

## Autoridad

**Puede** leer `case/`; escribir `work/screening_pending.csv`,
`work/evidence_pending.csv`, `STATE.json` y `TRACE.csv`; y ejecutar
`python3 scripts/validate_review.py`.

**No puede** escribir ni un carácter en `human/` ni en `official/`. **No puede**
ejecutar `scripts/review_gate.py` ni `scripts/relock.py`. **No puede** editar
`case/question.md`, `case/protocol.md` ni `case/source_packet.md`. Solo puede
crear `output/review_brief.md` mediante `scripts/assemble_brief.py`.

Estas prohibiciones son instrucciones, no permisos del sistema operativo. Por
eso existen además los hashes y los validadores: hacen visible el
incumplimiento en lugar de confiar en que no ocurra.

## Presupuesto

Doce registros de cribado, cuatro fuentes de extracción, una ronda de revisión
por fila rechazada. Si algo excede este presupuesto, deténgase y pregunte.

## Reglas

1. Procese un ítem a la vez y conserve su identificador.
2. En cribado, use únicamente los metadatos de `case/candidates.csv` y el
   protocolo. Si el título no alcanza, proponga `uncertain`; no rellene.
3. En extracción, copie el pasaje **exacto** y el localizador **exacto** de
   `case/source_packet.md`. Un pasaje aproximado es un error, no una
   aproximación aceptable.
4. Transcriba diseño, población y resultado tal como los declara la ficha. No
   los mejore ni los normalice.
5. Escriba la interpretación con el verbo que el diseño permite. Un diseño
   observacional no admite lenguaje causal.
6. Si falta evidencia, escriba `NO ENCONTRADO`. No complete el campo con algo
   plausible.
7. Nunca describa una fila como verificada, aprobada o oficial. Esa palabra
   solo la escribe `scripts/review_gate.py`.
8. Después de cada ítem, actualice `STATE.json`, agregue una fila a `TRACE.csv`
   y ejecute el validador.
9. Ante una decisión humana faltante, deténgase y presente ítem, pasaje,
   localizador y la tensión concreta que la persona debe resolver.
10. Un rechazo devuelve la fila a la cola: proponga una revisión bajo el mismo
    `evidence_id` y espere una segunda decisión.

## Terminado cuando

Los doce registros tienen decisión humana de cribado; cada fuente incluida
tiene exactamente una fila en el ledger oficial con verificación humana;
`scripts/validate_review.py` pasa; y `output/review_brief.md` existe únicamente
porque `scripts/assemble_brief.py` lo generó desde ese ledger.
