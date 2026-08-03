# Literatura: de una afirmación a una mini-síntesis verificable

Paquete completo para el bloque autónomo de literatura (35 minutos). No requiere
cuenta nueva ni clave API. Combina un mapa breve de herramientas, un clip de
descubrimiento, un workspace reutilizable para ChatGPT/Claude/Codex/Claude Code
y una práctica de extracción, auditoría y síntesis sobre un corpus congelado.

## Producto y límite pedagógico

La pregunta es: **¿qué permite concluir este corpus pequeño sobre Juntos y
resultados educativos, y qué no permite concluir?** No es una revisión
sistemática ni una evaluación nueva. Es una práctica de extracción,
verificación y síntesis sobre un corpus congelado.

Cada pareja audita una afirmación. La sala reúne después las tres filas y cada
persona redacta tres oraciones desde la matriz verificada. El producto no debe
decir que una asociación observada en otra fuente identifica el efecto causal
de Juntos.

## Abrir en este orden

1. Slideshow: [`../../slides/literature-review-35min.qmd`](../../slides/literature-review-35min.qmd).
2. Guía de flujo: [`workflow-guide.qmd`](workflow-guide.qmd), con rutas para
   aplicaciones de chat y agentes sobre carpeta local.
3. Workspace descargable: `starter_workspace.zip`; la carpeta fuente está en
   [`starter_workspace/`](starter_workspace/README.md).
4. Participantes: [`participant-packet.qmd`](participant-packet.qmd), renderizado
   como `participant-packet.html` en el sitio; reúne corpus, hoja y prompt.
   `worksheet.md` queda como versión Markdown.
5. Clip del facilitador: [`discovery-screening-clip.html`](discovery-screening-clip.html).
   Empieza en pausa; espacio reproduce, flechas avanzan y `R` reinicia.
6. Facilitación: [`facilitator-runbook.md`](facilitator-runbook.md).
7. Respaldo: [`fallback-matrix.md`](fallback-matrix.md).
8. Corrección: [`answer-key.md`](answer-key.md), solo para facilitación.
9. Controles: `python3 validate_packet.py --check-links`,
   `node validate_clip.js` y
   `python3 starter_workspace/validate_workspace.py`.

## Fuentes y derechos

Los pasajes son extractos textuales mínimos (cada uno de 25 palabras o menos)
de las cuatro fuentes que luego usa el auditor, con enlaces estables. Todo el
resto del paquete parafrasea.
No distribuir artículos completos ni pedir a participantes que suban PDFs.

## Rol de los dos casos del bloque

- **IA, persuasión y comunicación** pertenece al clip pregrabado de descubrimiento
  y cribado; no se mezcla con este ejercicio.
- **Juntos** es exclusivamente el corpus pequeño para extracción y auditoría.

El `starter_workspace` usa el caso de IA y persuasión para unir descubrimiento,
cribado, extracción y síntesis en archivos. La práctica Juntos conserva un
corpus distinto para que la auditoría no dependa de recordar el clip.

## Convención del agente auditor

El ejercicio usa cuatro etiquetas fijas en español. El archivo de respuestas
mapea cada una al enum en inglés que debe usar el `evidence_auditor`:
`supported`, `contradicted`, `partially_supported`, `insufficient`.

## Procedencia del clip

La consulta congelada devolvió 452 resultados en Semantic Scholar el
2026-08-02. Los ocho candidatos son una muestra didáctica curada —no los ocho
primeros resultados— y sus títulos, autoría, año, publicación y DOI se
comprobaron contra registros editoriales/Crossref. El registro de Costello et
al. se separa por la *Editorial Expression of Concern* de Science,
doi `10.1126/science.aej2383` (2026-06-11).

El clip muestra el **estado final congelado**: cinco incluidos, dos excluidos y
una bandera editorial, todos con motivo. `starter_workspace/candidates.csv`
reabre deliberadamente cinco filas como `pending` y conserva tres decisiones
de ejemplo; así la práctica local enseña a proponer cribado sin fingir que los
ocho registros siguen sin revisar.
