# Clave de respuestas — solo facilitación

## Etiquetas congeladas y enum del agente

| Etiqueta visible | Enum `evidence_auditor` | Regla |
|---|---|---|
| respaldada | `supported` | El pasaje y el alcance coinciden con la afirmación. |
| contradicha | `contradicted` | El corpus dice lo contrario de un componente central. |
| parcialmente respaldada | `partially_supported` | Una parte central coincide; otra excede el pasaje/diseño. |
| evidencia insuficiente | `insufficient` | El corpus no permite decidir, o falta el pasaje necesario. |

No sustituir estas etiquetas por “verdadera/falsa”. El enum es para el agente;
la etiqueta en español es para la conversación en clase.

## Matriz correcta

| ID | Veredicto | Fuente/localizador | Justificación | Qué permite / no permite |
|---|---|---|---|---|
| A1 | **respaldada** (`supported`) | S1; resumen, oración sobre educación | El pasaje nombra Juntos, matrícula, asistencia y años de transición. | Permite atribuir esa descripción al resumen. No cuantifica el efecto ni revalida la evaluación no experimental. |
| A2 | **contradicha** (`contradicted`) | S2; resumen, educación; S3, p. 3, limitaciones | S2 dice que la sola asistencia es insuficiente para mejorar aprendizajes; S3 dice que el indicador no considera calidad. | Permite distinguir acceso/participación de aprendizaje. No prueba un efecto causal de Juntos sobre aprendizaje. |
| A3 | **contradicha** (`contradicted`) | S4; resumen, primera oración | El título parecido oculta otro programa: “Juntos para Una Comunidad sin Violencia”, en Panamá. | Puede ilustrar un error de recuperación, no aportar evidencia sobre el programa peruano. |

**Discusión legítima en A1.** Si una pareja marca `partially_supported` porque
«principalmente» interpreta «se encuentran más», acepte la fila si explicita esa
reserva. La clave cierra en `supported` porque la afirmación atribuye una
descripción al resumen —no una magnitud ni una conclusión causal— y el pasaje sí
ubica matrícula y asistencia con mayor presencia en los años de transición.

## Errores que deben aparecer en el debrief

1. **A1:** es una atribución fiel al resumen, no una reauditoría causal. El
   diseño se declara no experimental y el pasaje no contiene una magnitud.
2. **A2:** el salto tiene dos partes: convierte asistencia en aprendizaje y una
   descripción/síntesis en prueba causal. S2 y S3 permiten detectar ambas.
3. **A3:** la cita y el título son auténticos. Precisamente por eso el distractor
   funciona: “Juntos” nombra otro programa y el país es Panamá.

## Mini-síntesis esperada

Una respuesta suficiente dice que el corpus ubica efectos de Juntos sobre
matrícula y asistencia en transiciones escolares; no permite equiparar
asistencia con aprendizaje ni establecer desde estos pasajes un efecto causal;
y el estudio panameño no evalúa el programa peruano. Debe señalar que el corpus
es pequeño y no equivale a una revisión exhaustiva.
