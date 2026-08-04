# Demo: una respuesta citada, y una negativa

Salida real de `scripts/answer.py` sobre `local_index_full` (18 obras, 14,726
fragmentos), congelada el 4 de agosto de 2026 para poder facilitar la clase sin
depender de que el índice esté construido en la máquina del momento.

Umbral de abstención vigente: **0.5636**, medido por
`scripts/calibrate_answer.py --mode dense --write` y guardado en
`answer-calibration.json`. No es un número elegido: 12 preguntas con evidencia
auditada puntúan entre 0.6634 y 0.8073; 8 preguntas que estos libros no
responden puntúan entre 0.3504 y 0.4638. El umbral va en el medio de esa
separación de 0.1996.

## 1. Pregunta con evidencia en el corpus

```bash
.venv/bin/python scripts/answer.py \
  "¿Cuáles son las diferencias entre el Sistema 1 y el Sistema 2?" --limit 2
```

```
Pregunta: ¿Cuáles son las diferencias entre el Sistema 1 y el Sistema 2?

Respuesta extractiva (sin modelo generativo, todo local). Los pasajes recuperados dicen, literalmente:

«As a consequence, the thoughts and actions that System 2 believes it has chosen are often guided by the figure at the center of the story, System 1.» [1]

«I should be extra careful.‖ Norms, Surprises, and Causes The central characteristics and functions of System 1 and System 2 have now been introduced, with a more detailed treatment of System 1.» [2]

Las citas son literales y están en el idioma del libro; este modo no traduce ni redacta. Verificá cada [n] abriendo el PDF en las páginas indicadas.

Fuentes
[1] Daniel Kahneman (2011), Thinking, Fast and Slow — pp. 23–24 — Behavioral Economics/Kahneman - Thinking, Fast and Slow (2011).pdf
[2] Daniel Kahneman (2011), Thinking, Fast and Slow — pp. 50–51 — Behavioral Economics/Kahneman - Thinking, Fast and Slow (2011).pdf

Regla de recuperación: pasa porque la similitud máxima 0.6826 ≥ umbral 0.5636 (margen 0.119).
Generador: extractive. Citas verificadas: sí.
```

La pregunta está en español y los libros están en inglés. El modo extractivo no
traduce: cita literalmente y deja la traducción a la persona, que es lo honesto
cuando lo que se promete es verificabilidad.

### Qué significa "Citas verificadas: sí"

Es una comprobación mecánica, y conviene decir en clase exactamente cuál:

- cada `[n]` de la respuesta apunta a un pasaje que se recuperó de verdad;
- la numeración arranca en 1 y no hay marcadores fuera de rango;
- cada frase entrecomillada es un fragmento literal del pasaje que cita
  (se compara contra el texto del fragmento, ignorando espacios).

Lo que **no** comprueba, y ningún programa comprueba: si el pasaje citado
sostiene la afirmación. Eso lo hace una persona abriendo el PDF en `pp. 23–24`.

### Verificación hecha a mano

Con `--json` la misma consulta reporta la evidencia por fuente:

| `[n]` | documento | páginas | similitud del fragmento | similitud de la frase citada |
| --- | --- | --- | --- | --- |
| 1 | kahneman-2011 | pp. 23–24 | 0.6826 | 0.6048 |
| 2 | kahneman-2011 | pp. 50–51 | 0.6349 | 0.7439 |

Las dos citas existen en esas páginas. La cita [2] arrastra un encabezado de
sección (`Norms, Surprises, and Causes`) pegado en medio de la frase: es la
limitación conocida de unir páginas antes de fragmentar, documentada en
`document_chunks` de `scripts/common.py`. No invalida la cita —la frase está en
la página— pero es exactamente el tipo de defecto que aparece al verificar y no
al leer la respuesta.

## 2. Pregunta que el corpus no responde

```bash
.venv/bin/python scripts/answer.py \
  "¿Cuál es la receta tradicional del ceviche peruano?" --limit 3
```

```
Pregunta: ¿Cuál es la receta tradicional del ceviche peruano?

La evidencia recuperada no alcanza para responder esta pregunta con este corpus.

Regla de recuperación: se abstiene porque la similitud máxima 0.3504 < umbral 0.5636 (margen -0.2132).
Generador: abstained. Citas verificadas: sí.
Nota: Similitud máxima 0.3504 < umbral 0.5636 (margen -0.2132).
```

El buscador igual devuelve cinco párrafos de economía: siempre hay un vecino más
cercano. La diferencia entre recuperar y responder es esta regla, y la regla
muestra sus números en pantalla en lugar de pedir confianza.

## 3. Un falso positivo, y por qué el umbral lo habría frenado

Con `--limit 3` entra una tercera fuente:

| `[n]` | fuente | páginas | similitud |
| --- | --- | --- | --- |
| 1 | Daniel Kahneman (2011), Thinking, Fast and Slow | pp. 23–24 | 0.6826 |
| 2 | Daniel Kahneman (2011), Thinking, Fast and Slow | pp. 50–51 | 0.6349 |
| 3 | Martin J. Osborne (2003), An Introduction to Game Theory | p. 525 | 0.4508 |

Osborne aparece porque su página habla de "player 1 and 2" y la pregunta habla
de "Sistema 1 y Sistema 2". El embedding no distingue el numeral del concepto.

El dato para la clase: **0.4508 cae dentro de la banda de las preguntas sin
evidencia** (0.3504–0.4638). Si esa fuera la mejor evidencia disponible, el
sistema se abstendría. Aparece en el top-3 solo porque va acompañada de dos
pasajes fuertes. Un top-k no es un ranking de verdad; es una lista ordenada por
similitud, y la similitud confunde "1 y 2".

## 4. Redacción con Opus: opt-in, con aviso y con salida de emergencia

El modo por defecto es local. `--generator claude_cli` envía los excerptos
seleccionados —no el corpus, no los PDFs, no el índice— a la API de Anthropic, y
solo después de consentimiento explícito:

Salida real de la misma pregunta del punto 1, corrida sin TTY (nada se envió):

```
AVISO: el modo claude_cli envía los fragmentos seleccionados a la API de Anthropic. Los excerptos salen de esta laptop. El resto del corpus, los PDFs y el índice no se envían. Sin consentimiento explícito el demo responde en modo extractivo, que es totalmente local.
Se enviarían 2 fragmentos (60 palabras en total) de 1 obra(s): Daniel Kahneman (2011), Thinking, Fast and Slow.
Sin TTY no hay consentimiento posible: se responde en modo extractivo. Usá --send-excerpts si querés autorizarlo explícito.
```

El recuento se calcula sobre el mismo payload que se enviaría, así que no puede
quedar desactualizado respecto de lo que sale. En una terminal interactiva, en
lugar de la última línea aparece `¿Enviar estos fragmentos a la API de
Anthropic? [s/N]`, y cualquier cosa que no sea sí responde local.
`--send-excerpts` es el consentimiento dado por adelantado.

La canalización se verificó primero con pasajes sintéticos:

- con pasajes que respondían la pregunta, Opus devolvió un párrafo en español
  con `[1]` y `[2]`, y el control de citas pasó;
- con una pregunta sobre una regla inventada, Opus devolvió exactamente la
  frase de abstención que el prompt autoriza;
- una respuesta que citaba `[9]` sobre dos pasajes entregados fue rechazada por
  `synthesis_problems` y el sistema cayó al modo extractivo.

Los tres fallos externos (CLI ausente, código de salida distinto de cero,
timeout de 90 s) devuelven una nota y la respuesta extractiva local. La demo no
se cae por una llamada de red.

Después Kristian autorizó explícitamente terminar el RAG principalmente con
Opus 5. La prueba real envió únicamente **2 fragmentos, 58 palabras en total**,
de List (2026) e Imbens y Rubin (2015). No envió PDFs, índice ni corpus. Comando:

```bash
.venv/bin/python scripts/answer.py \
  "¿Qué es un resultado potencial?" --limit 2 \
  --generator claude_cli --send-excerpts
```

Respuesta real de `claude-opus-5`:

> Un resultado potencial corresponde a lo que habría sido el resultado si el
> estado realizado hubiera sido d [1]; en el marco de inferencia causal, cada
> unidad tiene más de uno de estos resultados —por ejemplo Yi(1) y Yi(0)—, y
> los no observados se tratan como datos faltantes cuya distribución
> condicional puede derivarse dados los datos y los parámetros desconocidos
> [2].

- [1] John A. List (2026), *Experimental Economics: Theory and Practice*,
  pp. 79–80.
- [2] Guido W. Imbens y Donald B. Rubin (2015), *Causal Inference for
  Statistics, Social, and Biomedical Sciences*, p. 203.

El control mecánico de citas pasó. Una pregunta más amplia sobre todas las
diferencias entre Sistema 1 y Sistema 2 hizo que Opus se abstuviera porque los
fragmentos recuperados no bastaban. Esa doble decisión también está probada:
el umbral puede permitir revisar evidencia y el redactor todavía puede decir
«no alcanza» después de leerla.

## 5. Navegador

```bash
.venv/bin/python scripts/serve.py --port 8000
```

Sirve `http://127.0.0.1:8000/` y nada más: `--host 0.0.0.0` es un error con
explicación, y una petición con `Host:` que no sea loopback recibe 403. El
checkbox de Opus es un pedido, no una autorización: el servidor vuelve a decidir
y, sin consentimiento, responde local y lo dice en las notas.

## 6. Qué mostrar en clase, en orden

1. La pregunta con evidencia: hay respuesta y hay páginas.
2. Abrir el PDF en `pp. 23–24` y leer la frase citada. Esto es la clase.
3. La pregunta del ceviche: el sistema se calla, y muestra con qué números.
4. `--limit 3`: el falso positivo de Osborne y su 0.4508.
5. Recién entonces, si hay tiempo, la redacción con Opus y su aviso.

El orden importa: si la redacción va primero, la conversación se vuelve sobre la
fluidez del párrafo. Si va última, se vuelve sobre la evidencia.
