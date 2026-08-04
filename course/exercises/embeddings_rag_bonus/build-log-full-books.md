# Registro del build

Generado por `scripts/build_index.py`. Solo metadatos: no contiene texto
de los libros.

- Modelo: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Manifest: `manifest-full-books.csv`
- Documentos en el manifest: 18
- Documentos indexados: 18
- Páginas con texto: 8669
- Páginas recuperadas por OCR: 2746
- Fragmentos: 14726
- Fragmentos que cruzan un salto de página: 9611
- Dimensiones: 384
- Esquema del índice: 2
- Fragmentación: 320 palabras, 45 de solapamiento
- Extracción: 125.6 s; embeddings: 280.51 s; total: 407.16 s

| document_id | estado | páginas | OCR | fragmentos | cruzan salto | s | sha256 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| behavioral-guide-2016 | ok | 173 | 0 | 230 | 174 | 3.03 | `40e3b8108217` |
| camerer-2003 | ok | 224 | 224 | 630 | 252 | 0.13 | `3daedf7ce619` |
| kahneman-2011 | ok | 361 | 0 | 665 | 367 | 3.69 | `0aae84e267b9` |
| charness-pingle-2021 | ok | 246 | 0 | 390 | 269 | 3.89 | `f83c58f0be9a` |
| friedman-cassar-2004 | ok | 225 | 0 | 295 | 234 | 0.82 | `cc47a130092b` |
| frechette-schotter | ok | 466 | 0 | 756 | 508 | 4.18 | `4b8be5f7b0b5` |
| gerber-green-2012 | ok | 232 | 0 | 703 | 267 | 11.69 | `5a07d206773f` |
| holt-2019 | ok | 683 | 683 | 1035 | 753 | 1.92 | `e7a71c809883` |
| imbens-rubin-2015 | ok | 613 | 0 | 988 | 673 | 5.65 | `ec6b652d783f` |
| jacquemet-lharidon-2018 | ok | 450 | 0 | 771 | 504 | 6.22 | `cbdd8128008a` |
| kagel-roth-vol1 | ok | 718 | 0 | 1260 | 808 | 60.99 | `b99ff6e22242` |
| kagel-roth-vol2 | ok | 747 | 0 | 1529 | 860 | 6.85 | `641f593f1506` |
| list-2026 | ok | 867 | 867 | 1272 | 964 | 0.39 | `237f72cf7964` |
| kockesen-ok-2007 | ok | 132 | 0 | 163 | 132 | 1.71 | `0d16d87b8e9d` |
| mas-colell-1995 | ok | 972 | 972 | 1741 | 1107 | 0.29 | `9c77c6301d22` |
| myerson-1997 | ok | 565 | 0 | 757 | 630 | 2.13 | `a19d63135617` |
| osborne-2003 | ok | 654 | 0 | 1069 | 726 | 8.34 | `e7a2584df427` |
| osborne-rubinstein-1994 | ok | 341 | 0 | 472 | 383 | 3.69 | `70733e532ffb` |

Sin fallos: las 18 obras del manifest entraron al índice.
