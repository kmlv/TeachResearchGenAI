# Resultados congelados para el facilitador

Regla: aquí solo entran números de corridas reales. El texto de los fragmentos
no se guarda en este archivo; durante la clase se abre el PDF local.

## A. Piloto de clase — esquema 2

Corrida del 4 de agosto de 2026 con `manifest.csv` y `local_index/`:

- 20/20 documentos;
- 1,262 páginas con texto, 140 desde OCR;
- 2,210 fragmentos, 1,354 cruzan un salto de página;
- 384 dimensiones;
- fragmentación 320 palabras, solapamiento 45;
- extracción 24.4 s; embeddings 53.61 s; total 78.17 s;
- cero fallos.

### A.1 Lexical: español frente a libros en inglés

Consulta: **¿Cómo distinguir validez interna de validez externa?**

Resultado lexical: **cero resultados**. La consulta equivalente en inglés,
`internal validity external validity generalizability`, devolvió:

1. *Generalizability and Scaling*, p. 34 — 23.3183.
2. *Economics Lab*, p. 44 — 16.2832.
3. *Internal Validity and Identification*, pp. 20–21 — 11.9332.
4. *Handbook of Experimental Economic Methodology*, p. 21 — 10.8514.
5. *Handbook of Experimental Economics*, vol. 2, p. 33 — 7.5458.

Los puntajes son BM25: sirven para ordenar dentro de esta lista, no son
probabilidades.

### A.2 Dense: la misma pregunta en español

1. *Generalizability and Scaling*, pp. 1–2 — 0.6746.
2. *Economics Lab*, pp. 34–35 — 0.5583.
3. *Internal Validity and Identification*, pp. 1–2 — 0.5386.
4. *Experimental Economics: Method and Applications*, p. 83 — 0.5334.
5. *Thinking, Fast and Slow*, p. 61 — 0.4935.

Los puntajes son similitud coseno. El primer pasaje explicita que la validez
interna es requisito para la externa; debe abrirse en vivo para verificarlo.

### A.3 Hybrid: interacción repetida

Consulta: **¿Qué cambia entre interacción repetida y juego de una sola vez?**

1. *Game Theory: Analysis of Conflict*, pp. 69–70 — 0.0164.
2. *Behavioral Game Theory*, pp. 56–57 — 0.0164.
3. *An Introduction to Game Theory* (Osborne), p. 24 — 0.0159.
4. *An Introduction to Game Theory* (Koçkesen y Ok), p. 42 — 0.0156.
5. *Handbook of Experimental Economics*, vol. 1, pp. 35–36 — 0.0154.

Los puntajes híbridos son RRF. La demostración debe abrir al menos un acierto y
discutir si los otros cuatro realmente responden.

### A.4 Hybrid: falsos positivos visibles

Consulta: **¿Por qué los incentivos monetarios pueden desplazar motivación
intrínseca?**

1. *Behavioral Game Theory*, p. 58 — 0.0269; OCR ruidoso, falso positivo.
2. *Handbook of Experimental Economics*, vol. 1, p. 41 — 0.0164.
3. *Experimental Economics: Method and Applications*, p. 61 — 0.0161.
4. *Behavioral Economics Guide 2016*, p. 19 — 0.0159.
5. *The Art of Experimental Economics*, pp. 47–48 — 0.0152; pertinente.

La primera posición se conserva porque enseña una limitación real: un puntaje
alto no certifica pertinencia.

## B. Corpus de 18 libros enteros

Build final del 4 de agosto de 2026 con `manifest-full-books.csv`:

- 18/18 obras;
- 8,669 páginas con texto;
- 2,746 páginas leídas desde OCR;
- 14,726 fragmentos, 9,611 entre páginas;
- 384 dimensiones;
- extracción 125.6 s; embeddings 280.51 s; total 407.16 s;
- cero fallos.

El OCR procesó 2,637 páginas nuevas: Camerer 154, List 881, Mas-Colell 907 y
Holt 695. De ellas, 2,606 aportaron texto al índice; sumadas a 140 páginas útiles
del piloto explican las 2,746 páginas OCR finales. Holt es el caso diagnóstico
importante: una capa con miles de
caracteres pero casi sin espacios produjo 15 fragmentos; tras OCR produjo 1,035.

### B.1 Evaluación aprobada

Doce preguntas balanceadas (4 behavioral, 4 experimental, 4 game theory), 57
qrels positivas y 58 negativas explícitas. El pool top-5 contiene 123 candidatos:
57 positivos, 60 negativos explícitos y 6 todavía sin juzgar. Treinta y ocho de
las 57 positivas se descubrieron desde ese mismo pool y 19 se sembraron de forma
independiente, de modo que las cifras pueden ser optimistas aunque G4 esté aprobado:

| modo | Hit@3 | MRR | nDCG@5 |
| --- | ---: | ---: | ---: |
| lexical | 0.333 | 0.354 | 0.310 |
| dense | 0.917 | 0.792 | 0.584 |
| hybrid | 0.833 | 0.799 | 0.587 |

Interpretación docente: dense recupera una página relevante en el top 3 para
once de doce preguntas; hybrid para diez y lexical para cuatro. Hybrid queda
apenas arriba en MRR y nDCG, mientras dense gana en cobertura. Ningún modo domina
todas las métricas. G04 falla en los tres modos y se conserva como caso de
diagnóstico: los recuperadores no hallaron la página que refuta su premisa falsa.
Kristian **aprobó G4** el 4 de agosto de 2026, aceptando los 6 candidatos sin
juicio como incompletitud documentada. Para las métricas se tratan como no
relevantes; el archivo del pool conserva su estado explícito.
