# Paquete de fuentes congelado

> **AVISO — ESTAS CUATRO FUENTES SON SINTÉTICAS.**
> `T1`–`T4` son reconstrucciones didácticas escritas para este ejercicio. **No
> son citas de ningún artículo real, no tienen DOI y no deben atribuirse a
> ninguna persona autora.** Existen para que la clase practique extracción,
> anclaje y auditoría sobre pasajes estables, sin depender de la red ni de
> derechos de autor.
>
> Los ocho registros de `candidates.csv` sí son reales y verificables por DOI.
> El cribado se practica sobre metadatos reales; la extracción se practica
> sobre este paquete sintético. Las dos capas no se mezclan: ninguna cita de
> aquí pertenece a ninguno de esos ocho registros.

## Cómo leer cada ficha

Cada fuente declara diseño, población, intervención, comparador, resultado y un
localizador. `scripts/validate_review.py` compara carácter por carácter el
pasaje y el localizador que proponga el agente contra lo que dice esta ficha.
Un pasaje aproximado no pasa.

Sustituir una fuente sintética por una real es una edición de datos: basta
reemplazar la ficha completa manteniendo el `source_id`. Los scripts no tienen
pasajes escritos dentro.

---

## T1 — Mensaje generado por modelo frente a mensaje humano

- `source_id`: T1
- `design`: experimento aleatorizado
- `population`: adultos
- `intervention`: mensaje persuasivo generado por un LLM
- `comparator`: mensaje persuasivo escrito por personas
- `outcome`: apoyo declarado a una política, medido inmediatamente después
- `locator`: resumen, oración de resultados principales

> El mensaje generado por el modelo aumentó el apoyo declarado a la política en 3.4 puntos frente al mensaje escrito por personas.

---

## T2 — Comparación de argumentos entre modelos

- `source_id`: T2
- `design`: evaluación automatizada entre modelos
- `population`: modelos de lenguaje
- `intervention`: argumentos generados por distintos modelos
- `comparator`: argumentos escritos por personas
- `outcome`: calificación de calidad argumental otorgada por jueces
- `locator`: resumen, segunda oración

> Los argumentos del modelo recibieron mejores calificaciones de calidad que los argumentos humanos; las personas calificaron textos y no cambiaron su postura.

---

## T3 — Conversaciones registradas con un asistente

- `source_id`: T3
- `design`: estudio observacional
- `population`: adultos
- `intervention`: uso voluntario de un asistente conversacional
- `comparator`: personas que usaron el asistente con menor frecuencia
- `outcome`: postura declarada en una segunda encuesta
- `locator`: sección de resultados, primer párrafo

> Quienes conversaron más veces con el asistente declararon posturas más moderadas en la segunda encuesta que quienes conversaron menos.

---

## T4 — Intención declarada frente a conducta

- `source_id`: T4
- `design`: experimento aleatorizado
- `population`: adultos
- `intervention`: mensaje generado por un LLM sobre una noticia dudosa
- `comparator`: condición de control sin mensaje
- `outcome`: intención declarada de compartir
- `locator`: sección de resultados, medidas secundarias

> La intención declarada de compartir aumentó frente al control; el estudio no registró la conducta de compartir.

---

## Regla de evidencia

Un pasaje sirve para una afirmación solo si coinciden **fuente, población,
resultado y alcance del diseño**. Una cita textualmente correcta puede ser
evidencia equivocada para la afirmación que se le cuelga encima.
