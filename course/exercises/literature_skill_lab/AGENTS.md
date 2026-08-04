# Contrato del agente

## Objetivo

Guiar a una persona desde una búsqueda didáctica hasta un brief trazable usando
el skill `.agents/skills/revision-guiada/SKILL.md`.

## Autoridad

- Puede leer todos los archivos de esta carpeta.
- Durante el flujo normal solo puede editar `PROGRESO.md` y generar `BRIEF.md`.
- Puede ejecutar `python3 scripts/flujo.py` con sus subcomandos.
- No puede decidir por la persona, inventar una firma ni cambiar `FUENTES.md`.
- Solo puede editar el skill si la persona pide explícitamente aprender a
  modificarlo.

## Regla de interacción

Avance una fase a la vez. Muestre en el chat qué encontró, qué significa y qué
decisión falta. No esconda el pasaje detrás de un resumen ni pida un ambiguo
“¿continúo?”.

## Terminado

El trabajo termina cuando cada entrada seleccionada tiene una decisión, razón y
firma en `PROGRESO.md`, el comprobador responde `LISTO`, y `BRIEF.md` fue
generado desde esas decisiones.
