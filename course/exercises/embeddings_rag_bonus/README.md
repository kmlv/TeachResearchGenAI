# Bonus mediano: embeddings, recuperación y RAG

Este laboratorio convierte una biblioteca local en un buscador verificable. La
consulta puede estar en español aunque los libros estén en inglés. No usa claves
de API, no sube los libros a ningún servicio y no copia al repositorio PDFs,
texto, OCR ni vectores.

Hay dos escalas separadas:

| escala | propósito | manifest | índice local |
| --- | --- | --- | --- |
| piloto | demo rápida en clase | `manifest.csv` (20 ventanas) | `local_index/` |
| libros enteros | corpus mediano evaluado | `manifest-full-books.csv` (18 obras únicas) | `local_index_full/` |

El piloto usa ventanas de hasta 70 páginas y conserva capítulos o papers útiles
para la demostración. El corpus final evita contar dos ediciones o capítulos del
mismo libro como evidencia independiente.

## Qué produce

- preflight que separa PDF digitales, escaneados, mixtos y capas defectuosas;
- OCR incremental y explícito para las obras que lo requieren;
- fragmentos de 320 palabras con 45 de solapamiento que pueden cruzar páginas;
- embeddings multilingües de 384 dimensiones;
- índice lexical SQLite FTS5 y búsqueda densa;
- búsqueda híbrida con Reciprocal Rank Fusion y diversidad por documento;
- citas con autor, año y rango de páginas;
- `page_ledger.jsonl` para auditar si cada página vino del PDF o del OCR;
- evaluación lexical/dense/hybrid con Hit@3, MRR y nDCG@5;
- registros reproducibles que contienen metadatos, nunca texto de los libros.

Sobre esa recuperación se apoya la capa de respuesta (`scripts/answer.py` y
`scripts/serve.py`), que es donde el ejercicio se vuelve RAG:

- regla de abstención **medida**, no elegida: si el corpus no contiene la
  respuesta, el sistema se calla y muestra con qué números lo decidió;
- respuesta con marcadores `[n]` verificados contra los pasajes que realmente se
  recuperaron;
- modo extractivo por defecto, totalmente local: cita literal, sin redacción;
- redacción opcional con Opus vía CLI, solo con consentimiento explícito y aviso
  de que los excerptos salen de la laptop;
- interfaz de navegador atada a localhost.

## Resultado medido

### Piloto de clase

- 20/20 documentos, 1,262 páginas con texto;
- 2,210 fragmentos; 1,354 cruzan un salto de página;
- 140 páginas recuperadas por OCR;
- build de esquema 2: 78.17 s.

### Corpus de libros enteros

- 18/18 obras, 8,669 páginas con texto;
- 14,726 fragmentos; 9,611 cruzan un salto de página;
- 2,746 páginas leídas desde OCR;
- build: 407.16 s (125.6 s extracción; 280.51 s embeddings);
- 12 preguntas, 57 qrels positivas y 58 negativas explícitas;
- pool top-5: 123 candidatos; 6 siguen sin juzgar;
- Hit@3: lexical 0.333, dense 0.917, hybrid 0.833.

Kristian aprobó G2 y G4 el 4 de agosto de 2026. Los seis candidatos sin juicio
quedan aceptados como incompletitud documentada y se tratan como no relevantes
solo para calcular las métricas. Los
detalles están en [`full-books-runbook.md`](full-books-runbook.md),
[`build-log-full-books.md`](build-log-full-books.md) y
[`evaluation-report-full-books.md`](evaluation-report-full-books.md).
El flujo completo y sus entregables están resumidos en
[`pipeline-map.md`](pipeline-map.md).
El registro de las dos firmas y su evidencia está en
[`approval-checklist.md`](approval-checklist.md).

## Requisitos

- Python 3.11 o superior;
- `uv` recomendado;
- acceso local a un directorio con los PDF del corpus;
- red solo para la primera descarga del modelo (aprox. 0.22 GB);
- para OCR: `brew install poppler tesseract tesseract-lang`.

```bash
cd course/exercises/embeddings_rag_bonus
uv venv
uv pip install -r requirements.txt
source .venv/bin/activate
BOOKS_ROOT="/path/to/books"
```

## Piloto: construir y buscar

```bash
python scripts/preflight.py \
  --books-root "$BOOKS_ROOT"

python scripts/build_index.py \
  --books-root "$BOOKS_ROOT"

python scripts/search.py \
  "¿Cómo distinguir validez interna de validez externa?" \
  --mode lexical

python scripts/search.py \
  "¿Cómo distinguir validez interna de validez externa?" \
  --mode dense

python scripts/search.py \
  "¿Qué cambia entre interacción repetida y juego de una sola vez?" \
  --mode hybrid --json
```

Las salidas reales para facilitar la clase están congeladas en
[`demo-results.md`](demo-results.md).

## Libros enteros: pipeline reproducible

### 1. Preflight estricto

```bash
python scripts/preflight.py \
  --books-root "$BOOKS_ROOT" \
  --manifest manifest-full-books.csv \
  --report preflight-report-full-books.json \
  --sample-pages 24 --strict --strict-scope full-scan
```

El detector no se limita a contar caracteres. También identifica capas pegadas:
Holt parecía tener texto, pero producía solo 3 palabras por página. Esa señal lo
clasificó como `glued` y activó OCR correctivo.

### 2. OCR incremental

```bash
python scripts/ocr.py \
  --books-root "$BOOKS_ROOT" \
  --manifest manifest-full-books.csv --dry-run

python scripts/ocr.py \
  --books-root "$BOOKS_ROOT" \
  --manifest manifest-full-books.csv
```

La caché usa `document_id` y el hash del PDF. Si cambia el archivo, el sidecar
viejo deja de aplicar. El lote final sometió 2,637 páginas nuevas a OCR sin
fallos; 2,606 produjeron texto y, con 140 páginas útiles del piloto, el índice
lee 2,746 páginas desde OCR.

### 3. Build completo

```bash
python scripts/build_index.py \
  --books-root "$BOOKS_ROOT" \
  --manifest manifest-full-books.csv \
  --output local_index_full \
  --build-log build-log-full-books.md
```

### 4. Evaluar los tres recuperadores

```bash
python scripts/evaluate.py \
  --index local_index_full \
  --questions evaluation-questions.csv \
  --qrels evaluation-qrels.csv \
  --report-md evaluation-report-full-books.md \
  --report-json evaluation-report-full-books.json
```

Las preguntas pedagógicas y los juicios de relevancia viven en archivos
distintos. `expected_documents` orienta la curaduría, pero nunca se transforma
automáticamente en ground truth. Cada qrel positiva declara quién abrió la página
y cuándo.

## Responder con citas: `answer.py` y `serve.py`

### 5. Calibrar la regla de abstención

Un umbral inventado en el escritorio es exactamente la constante sin explicar
que este curso critica. Se mide sobre el índice real, contra las 12 preguntas
con evidencia auditada y 8 preguntas de control que estos libros no responden:

```bash
python scripts/calibrate_answer.py --index local_index_full --mode dense --write
```

Medición del 4 de agosto de 2026: con evidencia 0.6634–0.8073, sin evidencia
0.3504–0.4638, separación 0.1996, umbral **0.5636**. Queda escrito en
`answer-calibration.json`; `answer.py` se niega a responder sin ese archivo y
lo rechaza si cambia el modo o el modelo del índice.

### 6. Responder

```bash
python scripts/answer.py \
  "¿Cuáles son las diferencias entre el Sistema 1 y el Sistema 2?" --limit 2

python scripts/answer.py \
  "¿Cuál es la receta tradicional del ceviche peruano?" --limit 3
```

La primera responde con dos citas verificadas; la segunda se abstiene y muestra
`0.3504 < 0.5636`. La transcripción real está en
[`demo-respuesta-citada.md`](demo-respuesta-citada.md).

El modo por defecto es **extractivo**: cita literalmente los pasajes y no llama
a nada. Los libros están en inglés y la respuesta no los traduce, porque lo que
se promete es verificabilidad, no fluidez.

### 7. Redacción con Opus (opcional, con consentimiento)

```bash
python scripts/answer.py "…" --generator claude_cli               # pregunta antes de enviar
python scripts/answer.py "…" --generator claude_cli --send-excerpts  # consentimiento previo
```

Antes de enviar nada imprime el aviso y el recuento exacto de lo que saldría
(cuántos fragmentos, cuántas palabras, de qué obras). Sin TTY y sin
`--send-excerpts` no envía: responde local. Si el CLI falta, falla, tarda más de
90 s o devuelve una respuesta que cita fuentes que no se le entregaron, la
respuesta extractiva se muestra igual y la nota dice por qué.

Requiere el CLI `claude` en el PATH y usa explícitamente `claude-opus-5`. Es lo
único de este laboratorio que usa la red además de la descarga inicial del
modelo. La ejecución real documentada sintetiza «¿Qué es un resultado
potencial?» con dos citas válidas después de enviar 58 palabras seleccionadas;
el corpus, los PDFs y el índice permanecieron locales.

### 8. Interfaz de navegador

```bash
python scripts/serve.py --port 8000
```

Solo biblioteca estándar y solo loopback: `--host 0.0.0.0` es un error con
explicación y una petición con `Host:` que no sea localhost recibe 403. El
checkbox de Opus es un pedido, no una autorización; el servidor vuelve a
decidir. La página no carga nada de la red.

## Secuencia sugerida en clase

1. Mostrar el preflight: antes de vectorizar hay que saber qué se puede leer.
2. Ejecutar lexical en español y observar la pérdida por vocabulario.
3. Ejecutar dense y abrir el PDF en la página devuelta.
4. Combinar señales con hybrid y discutir aciertos y falsos positivos.
5. Mostrar la evaluación: lexical pierde el cruce de idiomas; dense e hybrid
   recuperan más, pero fallan en dos trampas difíciles.
6. Explicar que RAG agrega redacción, no verificación.
7. Justificar un knowledge graph solo cuando la relación sea la respuesta.

## Validación

```bash
python scripts/test_core.py
```

La suite tiene 174 pruebas: ventanas y rutas seguras, OCR, detección de texto
pegado, fragmentación entre páginas, esquema del índice, ledger, búsqueda,
diversidad, métricas y separación estricta entre preguntas y qrels; y para la
capa de respuesta, la regla de abstención, el contrato de citas, que cada cita
sea literal del pasaje que declara, el consentimiento antes de enviar excerptos,
los tres modos de falla del CLI y el cierre del servidor a localhost.

La suite no toca el modelo, el índice ni la red: `fastembed` y `pypdf` están
stubbeados y el recuperador se reemplaza por un contador de palabras. Con numpy
disponible corre con el intérprete del sistema, sin activar el virtualenv.

## Límites y derechos

- Similitud no es probabilidad, verdad, consenso ni causalidad.
- Todo top-k se verifica abriendo el documento en la página citada.
- El OCR puede inventar palabras plausibles; `page_ledger.jsonl` permite saber
  cuándo una cita viene de OCR.
- Los libros son de uso local. `.gitignore` y `_quarto.yml` excluyen PDFs, OCR,
  texto, vectores e índices de los artefactos publicados.
- Un knowledge graph es opcional: primero debe existir una pregunta relacional
  que justifique extraer y auditar entidades y aristas.
- Microdatos como ENAHO se consultan con SQL/DuckDB/Parquet; se indexan sus
  diccionarios y metodologías, no millones de filas como embeddings.
