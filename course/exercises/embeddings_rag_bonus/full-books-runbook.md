# Corpus de libros enteros — runbook

El piloto indexa una ventana de 70 páginas por obra: sirve para mostrar cómo
funciona la búsqueda por significado, pero es una maqueta. Este runbook describe
el corpus de **18 obras completas** que la reemplaza, con los comandos exactos,
las mediciones finales y el registro de las decisiones humanas ya tomadas.

El piloto no se toca. `manifest.csv`, `local_index/` y `build-log.md` siguen
siendo el ejercicio que ya está en clase; todo lo de libros enteros vive en
archivos y directorios aparte.

| | piloto | libros enteros |
| --- | --- | --- |
| manifest | `manifest.csv` | `manifest-full-books.csv` |
| índice | `local_index/` | `local_index_full/` |
| reporte de preflight | `local_index/preflight.json` | `preflight-report-full-books.json` |
| registro del build | `build-log.md` | `build-log-full-books.md` |
| caché de OCR | `ocr_cache/` | `ocr_cache/` (compartido, ver abajo) |

La caché de OCR es la única cosa compartida a propósito. Está indexada por
`document_id` y por el sha256 del PDF, así que las páginas que el piloto ya
reconoció siguen valiendo: el build de libro entero no las vuelve a pagar.

## 1. La selección: 18 obras, no 20

Tres de economía del comportamiento, diez de experimental e inferencia causal,
cinco de teoría de juegos y microeconomía.

| categoría | obras |
| --- | --- |
| behavioral | Behavioral Economics Guide 2016; Camerer 2003; Kahneman 2011 |
| experimental | Charness y Pingle 2021; Friedman y Cassar 2004; Fréchette y Schotter; Gerber y Green 2012; Holt 2019; Imbens y Rubin 2015; Jacquemet y L'Haridon 2018; Kagel y Roth vol. 1; Kagel y Roth vol. 2; List 2026 |
| game-theory | Koçkesen y Ok 2007; Mas-Colell, Whinston y Green 1995; Myerson 1997; Osborne 2003; Osborne y Rubinstein 1994 |

Son 18 y no 20 a propósito. Llegar a 20 obligaba a incluir dos ediciones
repetidas de obras que ya estaban en la lista, y una obra repetida no agrega
evidencia: agrega la apariencia de que dos fuentes distintas coinciden cuando en
realidad es la misma fuente contada dos veces. Además rompería la regla de
diversidad del recuperador, que permite como máximo dos fragmentos por obra en
el top-k.

Quedan fuera, y conviene dejarlo escrito:

- **Holt 2007, 1.ª edición.** Misma obra que Holt 2019 en el corpus.
- **List 2026 por capítulos** (`chapters/Ch03…`, `chapters/Ch16…`) y
  **List, Sadoff y Wagner 2011.** Los dos capítulos sueltos del piloto quedan
  subsumidos por el libro completo de List; el paper de 19 páginas no es una obra
  completa y por eso no cuenta para las 18.
- **`Experimental_Economics_List_ORIGINAL-DO NOT USE.pdf`** y la versión
  `GrayScale`. El manifest apunta a la versión `PROCESSED TO USE`, que es la que
  el propio directorio marca como utilizable.

Lo excluido, documentado, también es resultado.

## 2. Lo que el manifest declara

`manifest-full-books.csv` agrega tres columnas a las siete del piloto. El
cargador las trata como opcionales, así que `manifest.csv` sigue funcionando sin
cambios.

| columna | qué hace |
| --- | --- |
| `author`, `year` | la cita que ve la clase se arma con estas dos, no con el título |
| `end_page` | corta el índice analítico y la bibliografía |
| `max_pages` vacío | lee el libro entero; el piloto sigue usando `70` |

`text_policy=ocr` en cuatro filas. Tres —`camerer-2003`, `list-2026` y
`mas-colell-1995`— son las obras que el preflight encontró escaneadas de punta a
punta, sin un solo carácter (§5). La cuarta, `holt-2019`, se marcó el 4 de agosto
de 2026 y por el camino caro: sus páginas **sí** traen caracteres, pero sin
espacios, así que el build extrajo 683 páginas de texto y produjo quince
fragmentos (§5.1). Es la lista que `scripts/ocr.py` toma por defecto: marcar una
obra de más cuesta una hora de lote inútil; marcar una de menos manda al índice un
libro que produce cero páginas —o quince fragmentos, que es peor, porque parece
que funcionó—. Una prueba
(`test_only_the_measured_full_scans_are_marked_for_ocr`) ata esas cuatro filas a
la medición, para que nadie las cambie sin volver a medir.

Las 18 filas ya declaran autor y año. Los tres `year` que estaban vacíos
—`frechette-schotter`, `kagel-roth-vol1`, `kagel-roth-vol2`— se completaron el 4
de agosto de 2026 contrastando las páginas de créditos con las fichas editoriales,
no de memoria ni del nombre del archivo: Fréchette y Schotter 2015 (OUP), Kagel y
Roth vol. 1 1995 (Princeton) y Kagel y Roth vol. 2 **2016** (Princeton). En este
último, la página legal declara copyright 2015, mientras el catálogo oficial de
Princeton fecha la publicación en 2016; el manifest usa el año de publicación,
que es el que corresponde a la cita bibliográfica.

Kristian **aprobó G2 el 4 de agosto de 2026** con estas dos decisiones de
curaduría:

1. `end_page` queda vacío en las 18 filas: la ventana continúa hasta el final del
   PDF e incluye bibliografía, índice y páginas finales. Las páginas sin texto no
   generan fragmentos.
2. `start_page` vale 1 en `holt-2019` y `list-2026`, que son las dos obras que no
   venían del piloto. El preflight confirma que ese 1 es válido —ninguna de las
   dos filas cae fuera del documento— pero no que sea el mejor corte: con
   `start_page=1` entran portada, prefacio e índice. Las otras dieciséis
   conservan el valor que ya funcionó. La inspección de los 36 extremos está en
   `approval-checklist.md`; G2 aceptó estos límites sin reconstrucción.

## 3. Las cinco puertas humanas

Ninguna de estas la puede firmar un script.

- **G1 — Corpus.** Resuelta: las 18 rutas existen y las exclusiones
  están documentadas. Holt es la segunda edición de Princeton de 2019; la portada
  de List confirma *Experimental Economics: Theory and Practice*, John A. List,
  y el PDF tiene 881 páginas. Kagel y Roth vol. 2 usa 2016, año de publicación
  del catálogo de Princeton, no el copyright 2015. El alcance aprobado es uso
  local y académico sin redistribución.
- **G2 — Preflight y calidad. Aprobada por Kristian.** Se inspeccionaron los 36
  extremos y cuatro páginas OCR difíciles; `start_page` y `end_page` quedan como
  declara el manifest. Evidencia en `approval-checklist.md`.
- **G3 — Lote de OCR. Completada.** El
  primero —1,942 páginas nuevas en las tres obras escaneadas— ya corrió y está en
  la caché (§5). El segundo fue correctivo: 695 páginas de Holt, completadas en
  1,871.3 s (§5.1 y §6).
- **G4 — Gold set. Aprobada por Kristian.** Las 12 preguntas y páginas se
  aprobaron después de doble revisión. Se conservan seis candidatos `unjudged`
  como incompletitud explícita. Un examen escrito por el mismo sistema que se
  evalúa no mide nada; por eso la aprobación quedó separada de la ejecución.
- **G5 — Prompt de síntesis. No activada.** Este paquete mide recuperación; si
  luego se activa RAG, exige cita de obra/página y abstención cuando la evidencia
  no alcanza.

## 4. Comandos

Los tres pasos se corren por separado, nunca encadenados. El OCR es el único
caro y va en su propio momento, de noche y fuera de clase.

```bash
cd course/exercises/embeddings_rag_bonus
source .venv/bin/activate
BOOKS_ROOT="/path/to/books"
```

**Preflight** (minutos, sin costo). Con 24 muestras por obra en vez de 8: a
escala de libro entero, ocho páginas ya no describen la obra.

```bash
python scripts/preflight.py \
  --books-root "$BOOKS_ROOT" \
  --manifest manifest-full-books.csv \
  --report preflight-report-full-books.json \
  --sample-pages 24
```

La salida trae dos cifras de OCR que **nunca se suman**, y esa separación es el
punto:

- `OCR to run` — páginas de las obras escaneadas de punta a punta. Es una
  factura: cada una de esas páginas hay que reconocerla.
- `Mixed text layer` — obras con capa de texto en unas páginas y no en otras. La
  cota superior cuenta toda la ventana sin sidecar, pero la muestra apunta a una
  fracción mínima: son páginas en blanco, láminas o finales de capítulo, y
  reconocerlas no agrega nada. Se miran; no se meten al lote.

Sumar las dos es lo que hizo que el primer preflight de libros enteros anunciara
5,909 páginas de OCR cuando las pendientes de verdad eran 1,942.

El resumen JSON trae `ocr_pages_full_scan`, `ocr_pages_mixed_upper_bound` y
`ocr_pages_mixed_estimate` por separado. `ocr_pages_pending` sigue existiendo
—suma las dos— solo para no romper a quien ya lea el reporte viejo; no es la
cifra contra la cual presupuestar.

**OCR** (con G3 aprobada). Por defecto toma solo las filas con `text_policy=ocr`,
que en la primera corrida eran tres obras y 1,942 páginas nuevas por reconocer.
Después del diagnóstico de Holt fueron cuatro filas. Conviene probar con un tope
antes de soltar cualquier lote nuevo:

```bash
# ensayo: 20 páginas por obra, para ver que tesseract está bien instalado
python scripts/ocr.py --books-root "$BOOKS_ROOT" \
  --manifest manifest-full-books.csv --limit-pages 20

# lote completo, desatendido
python scripts/ocr.py --books-root "$BOOKS_ROOT" \
  --manifest manifest-full-books.csv
```

El script es incremental: reconoce solo las páginas que la caché todavía no
tiene y las fusiona con las que ya estaban. Un ensayo con `--limit-pages` no se
desperdicia, y las 140 páginas que el piloto ya reconoció de Camerer y Mas-Colell
no se vuelven a pagar. Para paralelizar sin tocar el código, tres terminales con
`--only` sobre `document_id` distintos escriben en archivos de caché distintos:

```bash
python scripts/ocr.py --books-root "$BOOKS_ROOT" \
  --manifest manifest-full-books.csv --only camerer-2003
python scripts/ocr.py --books-root "$BOOKS_ROOT" \
  --manifest manifest-full-books.csv --only list-2026
python scripts/ocr.py --books-root "$BOOKS_ROOT" \
  --manifest manifest-full-books.csv --only mas-colell-1995
```

El paralelismo es por obra. En la primera corrida hubo tres obras; Holt se añadió
después como corrección independiente. El reloj de pared no baja de lo que tarde
la obra más larga.

Terminado el lote, el mismo preflight sirve de puerta:

```bash
python scripts/preflight.py --books-root "$BOOKS_ROOT" \
  --manifest manifest-full-books.csv \
  --report preflight-report-full-books.json \
  --sample-pages 24 --strict --strict-scope full-scan
```

`--strict-scope full-scan` existe porque `--strict` a secas nunca va a dar verde:
una obra mixta conserva para siempre un puñado de páginas en blanco sin capa de
texto, y eso no es una deuda pendiente.

**Build** (minutos, después del OCR).

```bash
python scripts/build_index.py \
  --books-root "$BOOKS_ROOT" \
  --manifest manifest-full-books.csv \
  --output local_index_full \
  --build-log build-log-full-books.md
```

Las cuatro banderas van juntas o no va ninguna: sin `--output` y `--build-log`
el build sobrescribe el índice y el registro del piloto. `build-log-full-books.md`
declara de qué manifest salió, justamente para que una confusión se vea.

**Búsqueda** sobre el corpus nuevo:

```bash
python scripts/search.py "¿qué es un experimento de campo?" \
  --index local_index_full --mode hybrid
```

## 5. Lo que el preflight ya midió (4 de agosto de 2026)

El preflight corrió sobre las 18 filas con 24 muestras por obra. Todo lo de esta
sección sale de `preflight-report-full-books.json`; nada está proyectado.

- **18 obras, ninguna fila bloqueante**: ni `missing`, ni `damaged`, ni
  `encrypted`, ni `empty-window`. Las 18 rutas del manifest existen en el disco.
- **9,079 páginas en disco**, **8,780 dentro de las ventanas declaradas**.
- **Siete obras digitales** (2,731 páginas de ventana) no necesitan nada:
  Behavioral Guide, Friedman y Cassar, Gerber y Green, Imbens y Rubin, Jacquemet
  y L'Haridon, Osborne, Osborne y Rubinstein.

**Tres obras escaneadas de punta a punta en el primer lote.** Las 24 páginas
muestreadas de cada una devolvieron cero caracteres:

| obra | ventana | ya en caché | por reconocer |
| --- | ---: | ---: | ---: |
| `camerer-2003` | 224 | 70 | 154 |
| `list-2026` | 881 | 0 | 881 |
| `mas-colell-1995` | 977 | 70 | 907 |
| **total inicial** | **2,082** | **140** | **1,942** |

Las 140 páginas en caché son las que el piloto ya pagó, y la caché compartida las
conserva.

**Siete obras mixtas después de corregir Holt.** Kahneman, Charness y Pingle,
Fréchette y Schotter, los dos Kagel y Roth, Koçkesen y Ok, y Myerson suman 3,272
páginas de ventana sin sidecar. La muestra apunta a unas **219** páginas sin
texto; la inspección encontró esto:

| obra | páginas sin texto en la muestra |
| --- | --- |
| Kahneman | p. 383 en cero; p. 257 con 10 caracteres |
| Charness y Pingle | p. 29 y p. 269 en cero |
| Fréchette y Schotter | p. 163 y p. 491 en cero |
| Kagel y Roth vol. 1 | p. 20 en cero, el resto con texto |
| Kagel y Roth vol. 2 | p. 20 y p. 770 en cero |
| Koçkesen y Ok | p. 84 con 17 caracteres, páginas vecinas con texto |
| Myerson | solo p. 587 en cero |

Portadas, blancos, láminas y finales de capítulo. **Ninguna de estas siete obras
mixtas va al OCR masivo.** Si una consulta cae en un hueco, se reconocen páginas
sueltas; no se vuelve a procesar el libro entero.

### 5.1 Holt: el defecto que el conteo de caracteres no veía

Holt parecía digital porque tenía una mediana de 2,248 caracteres por página,
pero solo **3 palabras por página**: la capa venía pegada (`Chapter12asbeing...`).
El primer build indexó 683 páginas y produjo apenas **15 fragmentos**. Ese
resultado imposible motivó `is_glued_text`, que combina palabras/página y
caracteres/palabra y clasifica la capa como `glued`.

El OCR correctivo procesó **695/695 páginas**, sin fallos, produjo 1,734,034
caracteres en **1,871.3 s** y dejó 683 páginas con texto utilizables. En el build
final Holt aporta **1,035 fragmentos**; su densidad volvió a un rango normal:
mediana 439 palabras/página, media 416.5 y solo 4 páginas bajo 40 palabras.

### Verificación de las dos incorporaciones (G1)

El conteo resolvió la duda que quedaba sobre las dos filas que no venían del
piloto: `Holt 2019.pdf` tiene **695 páginas**, así que no es otra vez la Parte 1
de 160, y `List … PROCESSED TO USE.pdf` tiene **881**. Juntas aportan 1,576
páginas, exactamente lo que había que ver para llegar a 9,079.

La de Holt se abrió: portada de Princeton, © 2019, coherente con la 2.ª edición
que declara el manifest. La portada de List se abrió visualmente después del OCR
y confirma *Experimental Economics: Theory and Practice* y John A. List. Los
tres `year` vacíos ya se completaron desde la página de créditos y los catálogos
editoriales (§2).

## 6. Tiempos y escala medidos

Ya no son proyecciones. El lote inicial produjo 1,942 páginas nuevas de OCR:
Camerer 154 en 715.7 s, List 881 en 3,029.4 s y Mas-Colell 907 en 2,660.3 s.
Holt añadió 695 páginas correctivas en 1,871.3 s. En total se reconocieron
**2,637 páginas nuevas**, sin fallos. De ellas, 2,606 produjeron texto útil; al
sumar las 140 ya disponibles del piloto, el índice utiliza **2,746 páginas OCR**.
Las 31 restantes son páginas procesadas pero vacías o no utilizables.

El build final sobre las 18 obras tardó **407.16 s**: 125.6 s de extracción y
280.51 s de embeddings. Produjo 8,669 páginas con texto, 14,726 fragmentos y
9,611 fragmentos que cruzan al menos un salto de página. Todo el índice y el
caché siguen ignorados por Git.

## 7. Criterios de completitud

1. Ninguna fila bloqueante en el preflight —ni `missing`, ni `damaged`, ni
   `encrypted`, ni `empty-window`— y `--strict --strict-scope full-scan` en cero
   después del lote. Cumplido: 18 filas, cero bloqueos; las siete obras mixtas
   restantes son páginas blancas o ilustraciones, no deuda masiva.
2. `build-log-full-books.md` cierra sin fallos inexplicados; los explicados
   quedan escritos.
3. Cada obra declara autor y año, porque la cita que ve la clase se arma con
   ellos. Cumplido: las 18 filas los traen desde el 4 de agosto de 2026 (§2).
4. El reporte de evaluación compara los tres recuperadores sobre el mismo gold
   set. Cumplido técnicamente: 12 preguntas, 57 qrels positivas, 58 negativas
   explícitas, un pool exportado de 123 candidatos y tres modos;
   queda la aprobación normativa de Kristian en G4.
5. Las consultas de demostración y evaluación corren localmente y sus salidas
   reales quedan guardadas sin texto de los libros en los reportes rastreados.
6. Cada número del deck coincide con `build-log-full-books.md` y con
   `evaluation-report-full-books.md`.

## 8. Derechos y alcance

Uso local y académico. Ni los PDFs, ni el texto de los libros, ni los vectores
entran al repositorio: `.gitignore` excluye `local_index_full/`, `ocr_cache/` y
el reporte de preflight. En clase se muestra la pantalla; no se reparte el
corpus. El deck no debe sugerir que los participantes repliquen esto con libros
que no poseen.

El OCR introduce error propio: una página reconocida puede recuperarse bien y
citarse mal. Por eso la regla que sostiene todo el ejercicio es poder abrir el
PDF en la página citada y encontrar la frase con los ojos. Si eso no se puede
hacer, no hay una fuente: hay una sugerencia.

## 9. Esquema 2 del índice: qué cambió y qué falta

9.1–9.4 están implementados, probados y **verificados sobre índices reales**. El
piloto se reconstruyó con el esquema 2 y la costura se inspeccionó a ojo (§9.5);
el corpus completo tiene su arnés de evaluación reproducible (§9.4).

**9.1 Fragmentación que cruza saltos de página.** Antes se fragmentaba dentro de
cada página: un párrafo partido por un salto quedaba en dos mitades y ninguna
recuperaba bien, porque ninguna enunciaba la idea completa. En un libro entero
eso pasa en casi cada salto.

- `common.chunk_word_spans(words, size, overlap)` devuelve rangos `[inicio, fin)`
  de índices de palabra. `chunk_words` quedó como envoltura sobre ella: el
  comportamiento del piloto es idéntico, y hay una prueba que lo fija.
- `common.document_chunks(page_texts, size, overlap)` une las páginas en orden de
  página, recuerda de qué página vino cada palabra y traduce cada rango a
  `page_start` y `page_end`.
- `build_index.py` conserva `page`, igual a `page_start`, para no romper nada que
  ya citaba por `page`, y agrega `ordinal` (posición del fragmento dentro del
  documento) en lugar de `within_page`, que dejó de significar algo.
- Efecto lateral que conviene saber: una página de menos de 40 palabras antes no
  producía ningún fragmento y desaparecía del índice. Ahora sus palabras se suman
  a las de la página vecina. En el piloto eran 22 páginas de 1,262.

**9.2 `author` y `year` dentro del índice.** El manifest ya los declaraba y el
build no los copiaba, así que la cita se armaba con el título. Ahora viajan al
fragmento, a `chunks.jsonl` y a la tabla `metadata` de SQLite, junto con
`page_start` y `page_end`. `index.json` declara `"schema": 2` y `search.py`
verifica ese número antes de leer nada: contra un índice viejo sale con
"reconstruí el índice" en vez de un `KeyError` a media clase. La cita impresa es
`Autor (año), Título — pp. 84–85`; sin autor ni año —el caso del piloto— imprime
el título solo, exactamente como antes.

**9.3 `page_ledger.jsonl`.** Una fila por página indexada, escrita en el
directorio del índice (ignorado por Git): `document_id`, `page`, `source` (`pdf`
u `ocr`), `characters` y `words`. Sin una palabra del libro. `page_texts` ahora
devuelve el origen por página y no solo los conteos, que es el cambio que lo
habilita. Sirve para dos cosas concretas: saber si una cita dudosa viene de OCR
—que inventa palabras plausibles— y medir cuánto agregó de verdad el lote.

`build-log.md` agrega una columna "cruzan salto" y una línea de esquema, para que
9.1 sea auditable y no una afirmación.

**9.4 Arnés de evaluación.** `evaluation-questions.csv` contiene 12 preguntas
balanceadas: cuatro behavioral, cuatro experimental y cuatro de teoría de
juegos; incluye consultas bilingües, anclas exactas y trampas con premisas
falsas. `evaluation-qrels.csv` mantiene 57 juicios positivos y 58 negativos
explícitos separados de las expectativas documentales: el script nunca convierte
una expectativa en verdad. `evaluation-pool-full-books.csv` exporta los 123
candidatos únicos del top 5 sin texto de los libros: 57 caen en rangos positivos,
60 en rangos negativos explícitos y 6 siguen sin juzgar.

`scripts/evaluate.py` ejecuta lexical, dense e hybrid sobre el mismo índice y
calcula Hit@3, MRR y nDCG@5. Falla si alguna pregunta no tiene al menos una qrel
positiva con responsable y fecha, consume una misma qrel una sola vez aunque dos
fragmentos se solapen, y escribe reportes Markdown/JSON sin texto de los libros.
La corrida final aprobada en G4 dio:

| modo | Hit@3 | MRR | nDCG@5 |
| --- | ---: | ---: | ---: |
| lexical | 0.333 | 0.354 | 0.310 |
| dense | 0.917 | 0.792 | 0.584 |
| hybrid | 0.833 | 0.799 | 0.587 |

Las páginas o sus imágenes renderizadas fueron inspeccionadas localmente y
Kristian **aprobó G4 el 4 de agosto de 2026**. Los seis candidatos sin juicio
quedan aceptados como incompletitud documentada y se tratan como no relevantes
solo para las métricas. De las 57 positivas,
38 se descubrieron desde los resultados de los recuperadores y 19 se sembraron
independientemente. Este pooling es útil pero puede volver optimistas las cifras
absolutas; además, la comparación no es plenamente independiente. La trampa G04
queda sin acierto en los tres modos: ningún recuperador halló la página que refuta
su premisa falsa, un fallo que se conserva como diagnóstico. Dense cubre once de
doce preguntas; hybrid cubre diez, pero queda apenas arriba en MRR y nDCG. No hay
un ganador único para todas las métricas.

### 9.5 La reconstrucción del piloto, medida (4 de agosto de 2026)

El cambio de esquema no fue gratis, y el piloto se reconstruyó para pagarlo antes
de tocar el corpus grande. Lo que se predijo y lo que salió:

1. **El índice del piloto quedaba inservible hasta reconstruirlo.** Ya está
   reconstruido: **20/20 documentos, 1,262 páginas, 2,210 fragmentos, 78.17 s**,
   sin fallos y sin volver a pedir OCR —`ocr_cache/` se reutilizó—. De esos 2,210
   fragmentos, **1,354 cruzan un salto de página**, que es 9.1 funcionando y no
   una afirmación.
2. **Las cifras del piloto cambiaron, y la proyección se sostuvo.** La estimación
   escrita antes de construir era «2,614 → ~2,207, cota inferior». El build dio
   **2,210**: tres por encima de la cota, exactamente la dirección anunciada
   (las 22 páginas cortas que antes no producían nada ahora sí aportan). Las
   páginas con texto —1,262— no se movieron, como estaba previsto.
   `build-log.md`, `demo-results.md` y el deck se reconciliaron con **2,210** y
   las cuatro consultas se volvieron a correr sobre el esquema 2.

Y la verificación que ningún test reemplaza, la misma que estaba escrita como
riesgo antes de implementar: **al unir páginas, un encabezado corrido o un número
de página que antes quedaba al borde del fragmento ahora puede quedar en medio de
una oración.** Hay que leer diez fragmentos que crucen un salto, con el índice ya
construido:

    python3 - <<'PY'
    import json, collections
    byd = collections.defaultdict(list)
    with open("local_index/chunks.jsonl", encoding="utf-8") as src:
        for c in map(json.loads, src):
            if c["page_end"] > c["page_start"]:
                byd[c["document_id"]].append(c)
    for doc in list(byd)[:10]:
        cs = byd[doc]
        c = cs[len(cs) // 2]
        print(f'--- {doc} pp. {c["page_start"]}-{c["page_end"]}')
        print(c["text"][:600])
    PY

Dos decisiones de muestreo que no son adorno. **Uno por documento**, porque los
diez primeros del archivo salen casi todos de la misma obra y miden una sola
maquetación. Y **la costura del medio de cada obra**, no la primera: la primera
cae siempre en el frontmatter, que es la parte menos representativa de un libro
y la que más basura de imprenta tiene. Muestrear la primera infla el problema y
además lo atribuye al lugar equivocado.

Se busca una sola cosa: si en la costura aparece basura de encabezado. Si aparece
en más de dos de diez, hay que limpiarla antes del build grande; si no, se anota
que se miró y se sigue. Anotar el resultado acá, con fecha, porque es evidencia.

**Resultado, 4 de agosto de 2026.** Se leyeron **dos muestras independientes** de
diez costuras cada una, en diez documentos distintos, y las dos dan lo mismo.

- *Primera muestra (costura inicial de cada obra).* Dos de diez con ruido claro
  de encabezado o pie dentro del fragmento: el OCR de Camerer y el frontmatter de
  CUP en Jacquemet y L'Haridon. Las otras ocho, continuidad semántica utilizable.
- *Segunda muestra (costura del medio de cada obra, el corte que de verdad va a
  ver la clase).* También **dos de diez**, pero en obras distintas y con el caso
  de manual a la vista. En Imbens y Rubin pp. 56-57, el número de página y el
  encabezado corrido quedaron **en medio de una oración**. Jacquemet y L'Haridon
  pp. 54-55 repite el patrón: un encabezado de capítulo interrumpe el pasaje. Las
  otras ocho se leen enteras a través del salto.

El umbral escrito de antemano era «limpiar si >2/10»; **2/10 en las dos muestras,
así que no se activa** y el build grande queda habilitado sin paso de limpieza.

Dos matices que conviene no confundir. Gerber y Holt muestran ruido de OCR
general —Holt pp. 57-58 es ilegible a ojo—, presente también dentro de una
página: no lo introdujo el salto y 9.1 no puede arreglarlo. El caso de Imbens y
Rubin, en cambio, **sí** lo introdujo el salto, y es exactamente el riesgo que se
había escrito antes de implementar. A escala de libro entero ese 20% se aplica a
14,726 fragmentos en vez de a 1,354. Si en el corpus grande la clase llega a ver
un encabezado en medio de una cita, la reparación no es rehacer 9.1: es filtrar
las líneas que se repiten en muchas páginas de la misma obra, que es la firma de
un encabezado corrido. Se mide con `page_ledger.jsonl` y no se toca antes de
tener el corpus.

La suite completa tiene **108 pruebas** en `scripts/test_core.py`. Además de
9.1–9.3 cubre el detector de texto pegado, el contrato de las cuatro obras OCR,
la separación preguntas/qrels y las métricas de evaluación. Entre los casos: un
párrafo partido entre dos páginas se recupera entero y las dos mitades sueltas no
producían nada; un fragmento que cruza tres páginas declara bien los dos
extremos; `page_start` es donde el fragmento empieza y no donde tiene más
palabras; el ledger tiene exactamente una fila por página con texto, dice cuáles
vinieron de OCR y no contiene texto; un índice sin `schema` se reporta como el
viejo; y el manifest del piloto sigue construyendo, sin autor ni año, bajo el
esquema nuevo.
