# Registro de aprobación — G2 y G4

Kristian aprobó G2 y G4 el 4 de agosto de 2026. Este archivo conserva la evidencia
que informó esa decisión. No contiene texto de los libros, vectores ni imágenes
de página.

## G2 — límites y calidad del corpus

**Decisión aprobada:** conservar los límites actuales como **libros analíticos
completos**. Las 18 ventanas llegan hasta la última página del PDF. Los cortes
iniciales excluyen front matter en 16 obras; Holt y List empiezan en la portada.
Las páginas sin texto al final se conservan en la ventana pero no generan
fragmentos.

| obra | inicio | inspección visual del inicio | última página PDF / última con texto |
| --- | ---: | --- | ---: |
| behavioral-guide-2016 | 12 | sección sustantiva del guide | 184 / 184 |
| camerer-2003 | 25 | cuerpo de capítulo | 248 / 248 |
| kahneman-2011 | 20 | cuerpo de capítulo con figura | 383 / 381 |
| charness-pingle-2021 | 18 | colaboradores antes del cuerpo | 269 / 268 |
| friedman-cassar-2004 | 20 | cuerpo introductorio | 248 / 248 |
| frechette-schotter | 20 | cuerpo de capítulo | 491 / 490 |
| gerber-green-2012 | 25 | cuerpo de capítulo con tabla | 256 / 256 |
| holt-2019 | 1 | portada; OCR correctivo | 695 / 695 |
| imbens-rubin-2015 | 25 | cuerpo de capítulo | 646 / 646 |
| jacquemet-lharidon-2018 | 20 | front matter editorial | 474 / 474 |
| kagel-roth-vol1 | 20 | página blanca; prefacio desde 21 | 752 / 752 |
| kagel-roth-vol2 | 20 | página blanca; portadilla desde 21 | 770 / 769 |
| list-2026 | 1 | portada; OCR | 881 / 880 |
| kockesen-ok-2007 | 10 | cuerpo de capítulo | 141 / 141 |
| mas-colell-1995 | 25 | inicio de capítulo; OCR | 1,001 / 1,001 |
| myerson-1997 | 20 | cuerpo de capítulo | 587 / 586 |
| osborne-2003 | 20 | cuerpo de capítulo | 685 / 685 |
| osborne-rubinstein-1994 | 15 | inicio de capítulo | 368 / 368 |

Se renderizaron y miraron los 36 extremos —inicio y final—. También se revisaron
cuatro páginas OCR deliberadamente difíciles: Camerer p. 191 (tabla), List p. 81
(notación causal), Mas-Colell p. 143 (fórmulas y referencias) y Holt p. 329
(prosa). Las cuatro son legibles en la página original. Que el OCR sea legible no
convierte su texto en autoridad: toda cita sigue requiriendo abrir la página.

Si Kristian prefiere un corpus sin portada ni colaboradores, la alternativa es
subir `start_page` en Holt, List, Charness–Pingle y Jacquemet–L'Haridon y reconstruir
índice y métricas. No se recomienda hacerlo la víspera de clase: el ruido es
pequeño, el corpus actual es reproducible y el objetivo declarado fue trabajar
libros enteros.

## G4 — gold set aprobado

Estado aceptado en la firma:

- 12 preguntas;
- 57 qrels positivas y 58 negativas explícitas;
- pool top-5 de 123 candidatos únicos;
- 57 candidatos cubiertos por rangos positivos, 60 por rangos negativos y 6
  todavía `unjudged`;
- 38 de las 57 positivas se descubrieron desde el pool y 19 se sembraron
  independientemente, por lo que las métricas pueden ser optimistas;
- cero contradicciones entre rangos positivos y negativos.

Dos revisores independientes evaluaron los 14 casos que estaban sin juicio.
Coincidieron en ocho —cinco relevantes y tres no relevantes— y Codex confirmó
visualmente las páginas antes de incorporarlos. Los seis desacuerdos permanecen
`unjudged`; no se forzó consenso. Kristian conserva la aprobación final.

### Los seis desacuerdos para spot-check

| pregunta | candidato físico | revisor A | revisor B | motivo del desacuerdo |
| --- | --- | --- | --- | --- |
| E03 | List pp. 680–681 | relevante | no relevante | supuestos de *surrogacy*, pero no SUTVA ni el marco general |
| E04 | List pp. 40–41 | ambiguo | relevante | la página contiene saliencia/dominance; el chunk recuperado puede empezar después |
| G02 | Myerson pp. 512–513 | no relevante | ambiguo | negociación infinita con descuento, no la solución canónica de ofertas alternadas |
| G03 | Charness–Pingle p. 96 | no relevante | relevante | agentes ingenuos agravan selección adversa, pero el mecanismo de información oculta es indirecto |
| G03 | Fréchette–Schotter pp. 367–368 | no relevante | relevante | *winner's curse* y número de postores, con mecanismo de selección discutible |
| G04 | Osborne pp. 151–152 | no relevante | relevante | refuta equilibrio puro en una subasta *all-pay*, pero no mediante un juego cero-suma/minimax |

Las citas usan páginas físicas del PDF. En List, el folio impreso está 18 páginas
detrás: por ejemplo, PDF 40 corresponde al folio 22. Esta diferencia es estable y
no es un error del índice.

## Aprobación registrada

Kristian respondió **«apruebo»** a la solicitud explícita de aprobar G2 y G4. Los
seis desacuerdos quedan deliberadamente `unjudged`; no se los convierte en
negativos dentro del archivo del pool. La convención de evaluación los trata como
no relevantes únicamente para calcular las métricas publicadas.
