# Registro del build

Generado por `scripts/build_index.py`. Solo metadatos: no contiene texto
de los libros.

- Modelo: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Manifest: `manifest.csv`
- Documentos en el manifest: 20
- Documentos indexados: 20
- Páginas con texto: 1262
- Páginas recuperadas por OCR: 140
- Fragmentos: 2210
- Fragmentos que cruzan un salto de página: 1354
- Dimensiones: 384
- Esquema del índice: 2
- Fragmentación: 320 palabras, 45 de solapamiento
- Extracción: 24.4 s; embeddings: 53.61 s; total: 78.17 s

| document_id | estado | páginas | OCR | fragmentos | cruzan salto | s | sha256 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| behavioral-guide-2016 | ok | 70 | 0 | 96 | 72 | 1.61 | `40e3b8108217` |
| camerer-2003 | ok | 70 | 70 | 204 | 78 | 0.09 | `3daedf7ce619` |
| kahneman-2011 | ok | 70 | 0 | 140 | 70 | 0.85 | `0aae84e267b9` |
| charness-pingle-2021 | ok | 66 | 0 | 103 | 70 | 1.18 | `f83c58f0be9a` |
| friedman-cassar-2004 | ok | 69 | 0 | 84 | 63 | 0.27 | `cc47a130092b` |
| frechette-schotter | ok | 67 | 0 | 107 | 70 | 0.65 | `4b8be5f7b0b5` |
| gerber-green-2012 | ok | 70 | 0 | 213 | 83 | 3.59 | `5a07d206773f` |
| holt-2019 | ok | 69 | 0 | 103 | 75 | 2.25 | `fe5c350f465c` |
| imbens-rubin-2015 | ok | 69 | 0 | 120 | 75 | 0.74 | `ec6b652d783f` |
| jacquemet-lharidon-2018 | ok | 68 | 0 | 114 | 70 | 1.1 | `cbdd8128008a` |
| kagel-roth-vol1 | ok | 66 | 0 | 118 | 71 | 6.2 | `b99ff6e22242` |
| kagel-roth-vol2 | ok | 68 | 0 | 135 | 75 | 0.81 | `641f593f1506` |
| list-2026-internal-validity | ok | 34 | 0 | 51 | 37 | 0.3 | `2b916847c1b4` |
| list-2026-generalizability | ok | 40 | 0 | 66 | 46 | 0.38 | `74ee41b85128` |
| list-sadoff-wagner-2011 | ok | 19 | 0 | 35 | 21 | 0.25 | `bc2cb8fa2096` |
| kockesen-ok-2007 | ok | 70 | 0 | 93 | 71 | 1.48 | `0d16d87b8e9d` |
| mas-colell-1995 | ok | 70 | 70 | 116 | 76 | 0.13 | `9c77c6301d22` |
| myerson-1997 | ok | 70 | 0 | 93 | 75 | 0.5 | `a19d63135617` |
| osborne-2003 | ok | 70 | 0 | 125 | 79 | 1.14 | `e7a2584df427` |
| osborne-rubinstein-1994 | ok | 67 | 0 | 94 | 77 | 0.9 | `70733e532ffb` |

Sin fallos: las 20 obras del manifest entraron al índice.
