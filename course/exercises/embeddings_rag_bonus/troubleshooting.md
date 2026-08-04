# Troubleshooting

Ordenado por el momento en que aparece el problema. Cada síntoma trae la causa
probable y el comando que la resuelve. Todos los comandos se corren desde
`course/exercises/embeddings_rag_bonus` con el entorno activado.

## Preflight

**`FileNotFoundError` al cargar el manifest**
El manifest declara una ruta y el disco tiene otra. No se edita a ciegas:

```bash
BOOKS_ROOT="/path/to/books"
python scripts/preflight.py --books-root "$BOOKS_ROOT"
```

La fila sale como `missing` con hasta tres candidatos y su puntaje. Si el primero es
claramente el correcto y le saca distancia al segundo, `--fix-paths` lo aplica; si
no, se copia la ruta a mano. El caso típico que **no** se autocorrige es un libro que
convive con su manual de soluciones: ahí decide una persona.

**`Manifest is missing columns: [...]`**
El manifest quedó en el formato viejo de cuatro columnas. El formato actual es
`document_id,title,category,relative_path,start_page,max_pages,text_policy`.

**`Manifest path escapes books root`**
Una ruta con `../`. Es una defensa deliberada: el laboratorio solo lee dentro del
directorio indicado por `BOOKS_ROOT`.

**Estado `empty-window`**
`start_page` quedó más allá de la última página, casi siempre por copiar el
`start_page` de un libro a un capítulo suelto. Los capítulos y papers usan
`start_page=1`.

**Estado `encrypted`**
El PDF pide contraseña real. No se adivina: se reemplaza por otra copia o se saca del
manifest y se dice en clase que el corpus quedó en 19.

**Estado `damaged`**
El archivo está truncado o mal escrito. Verificar abriéndolo en el visor; si tampoco
abre ahí, el problema es la copia, no el script.

**Estado `needs-ocr` en muchas obras a la vez**
Sospechar de `start_page`: si apunta a láminas o a páginas en blanco, la muestra sale
sin texto aunque el libro sí lo tenga. Revisar `sampled_pages` en
`preflight-report.json` antes de correr OCR.

## OCR

**`Missing external tools: pdftoppm, tesseract`**

```bash
brew install poppler tesseract tesseract-lang
```

**El OCR tarda muchísimo**
Es lo esperado: son 300 dpi por página, renderizado más reconocimiento. Bajar el
costo con `--dpi 200`, reducir `max_pages` para esa fila, o correr solo una obra con
`--only document-id`. Primero conviene un `--dry-run` para ver cuántas páginas son.

**El OCR corrió pero el build no lo usa**
El caché está indexado por hash del PDF: si el archivo cambió, el sidecar ya no
aplica. Confirmar que la fila tiene `text_policy=ocr` o `auto` y volver a correr OCR.
Con `text_policy=digital` el sidecar se ignora por definición.

**El texto reconocido sale con basura**
Normal en tablas, fórmulas y escaneos torcidos. Es material de clase, no un defecto a
esconder: se muestra que OCR agrega su propio error a la cadena.

## Build

**`No chunks were extracted`**
Ninguna obra produjo texto. Casi siempre el `--books-root` está mal escrito. Revisar
`preflight-report.json`.

**El build termina pero avisa `Not indexed: ...`**
Comportamiento correcto: una obra falló y las demás entraron. El motivo exacto está
en `build-log.md`. Se decide si se reemplaza la obra o si la clase corre con menos.

**La descarga del modelo falla**
El primer build necesita red para bajar ~0.22 GB. Sin red, el índice lexical se puede
construir igual y la demo densa se reemplaza por los resultados congelados.

**El build consume demasiada memoria**
Bajar `--batch-size` a 16 o 32, o recortar `max_pages` en el manifest.

**Las páginas citadas no coinciden con el libro impreso**
No es un error: la página reportada es la del PDF, que casi nunca coincide con la
numeración impresa cuando hay prefacio en romanos. Se verifica abriendo el PDF, no la
edición en papel.

## Búsqueda

**La búsqueda lexical devuelve cero resultados**
Es el punto de la demo: la consulta está en español y los libros están en inglés.

**Todos los resultados vienen del mismo libro**
Subir `--per-document` es lo contrario de lo que se quiere. El valor 1 por defecto
fuerza diversidad; con 2 o 3 se muestra en vivo cómo un solo libro captura el top-k.

**`FileNotFoundError: local_index/index.json`**
No hay índice todavía. Correr `build_index.py` o dictar el bloque con
`demo-results.md`.

**Los puntajes cambiaron respecto a `demo-results.md`**
El corpus cambió (una obra distinta, otro `start_page`, OCR nuevo). Se vuelven a
congelar los resultados; no se muestran números que ya no salen de una corrida real.

## Pruebas

```bash
python scripts/test_core.py
```

Corren sin PDF y sin entorno virtual. Si fallan después de tocar `common.py`, el
problema está en el laboratorio, no en el corpus.
