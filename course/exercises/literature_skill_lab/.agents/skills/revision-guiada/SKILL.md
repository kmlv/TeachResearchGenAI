---
name: revision-guiada
description: Guía conversacionalmente una revisión de literatura didáctica desde la búsqueda hasta un brief trazable. Úsala cuando una persona quiera buscar, inspeccionar una o dos fuentes, verificar pasajes, registrar decisiones humanas y generar un brief sin manejar la terminal.
---

# Revisión guiada

Conducir el trabajo como una conversación de cinco fases. Avanzar solo una fase
por respuesta y mantener `PROGRESO.md` como fuente de estado.

## Formato visible en cada respuesta

Comenzar con `FASE n/5 · NOMBRE`. Después mostrar:

1. **Encontré**: resultado concreto o estado actual.
2. **Mira esto**: texto, pasaje o diferencia que la persona debe inspeccionar.
3. **Necesito de ti**: una sola decisión o dato.
4. **Después haré**: la siguiente acción, sin ejecutarla todavía si depende de
   la decisión.

Evitar párrafos largos. Preferir tablas pequeñas, citas en bloque y opciones
tecleables.

## Fase 1 · Encuadrar

Leer `PROGRESO.md`. Si está en `INICIO`, preguntar únicamente:

- la pregunta o tema de búsqueda;
- el nombre que quedará junto a las decisiones.

Registrar ambos. Proponer una consulta breve y pedir confirmación antes de
buscar.

## Fase 2 · Buscar

Tras la confirmación, ejecutar por cuenta propia:

```bash
python3 scripts/flujo.py buscar --consulta "CONSULTA"
```

Mostrar los resultados como una tabla de tres filas con ID, título y razón de
posible relevancia. Aclarar que son candidatos, no evidencia. Pedir que la
persona seleccione una o dos entradas. Registrar la consulta y los IDs en
`PROGRESO.md`.

## Fase 3 · Inspeccionar

Para cada entrada seleccionada, ejecutar:

```bash
python3 scripts/flujo.py mostrar --id ID
```

Mostrar una tarjeta en el chat con este orden:

- título, diseño y población;
- **TEXTO EXACTO**, en cita de bloque;
- localizador;
- una afirmación candidata;
- **TENSIÓN**: la objeción metodológica más fuerte.

No ocultar el pasaje detrás de una paráfrasis. No inspeccionar la segunda
entrada hasta resolver la primera.

## Fase 4 · Decidir y firmar

Ofrecer exactamente estas formas:

```text
APROBAR S1: [razón] — [nombre]
REESCRIBIR S2: [afirmación permitida] — [nombre]
EXCLUIR S3: [razón] — [nombre]
```

No interpretar “sí”, “ok” o “continúa” como firma. Tras recibir una forma
completa, copiar literalmente la decisión, razón y nombre a la fila correcta
de `PROGRESO.md`. Ejecutar `python3 scripts/flujo.py validar` y mostrar la salida
sin suavizarla.

La firma es pedagógica: registra autoría, pero no es una firma digital.

## Fase 5 · Cerrar

Cuando el comprobador responda `LISTO`, ejecutar:

```bash
python3 scripts/flujo.py brief
```

Abrir `BRIEF.md` y mostrar en el chat:

- la pregunta;
- una afirmación por fuente aceptada;
- debajo, pasaje exacto y localizador;
- la decisión y el nombre de quien la firmó;
- exclusiones y razones.

Terminar explicando qué verificó el script y qué dependió del juicio humano.

## Detenerse

Detenerse y formular una sola pregunta cuando:

- la persona seleccione más de dos entradas;
- la afirmación exceda lo que el pasaje o diseño permiten;
- falten razón o nombre;
- una entrada observacional use lenguaje causal;
- el comprobador responda `BLOQUEADO`.

Nunca generar el brief desde el chat ni decidir por la persona.
