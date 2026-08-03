---
name: referee-response
description: Convierte informes de referee en propuestas, diffs y una carta trazable con aprobación humana.
---

# Respuesta trazable a referees

Use esta skill cuando exista un manuscrito y uno o más informes estructurados
por ID.

1. Inventarie todos los puntos antes de redactar.
2. Para cada punto, ubique una línea estable del manuscrito y copie la cita.
3. Distinga `change` de `no_change`; no prometa una modificación sin diff.
4. Escriba propuestas solo en `pending.csv` y `changes/`.
5. Ejecute el validador y deténgase ante el gate humano.
6. Tras la decisión humana, lea el ledger que actualizó la interfaz humana; no
   lo edite.
7. Ensamble la carta únicamente con `scripts/assemble_letter.py`, nunca desde
   memoria del chat.

Ante ambigüedad sustantiva, registre `blocked` y formule la pregunta mínima que
la persona debe decidir.
