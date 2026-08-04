# Runbook del facilitador — bonus de embeddings, recuperación y RAG

Duración: 34 minutos, fuera del tronco principal; 40 minutos si se incluyen las
dos láminas opcionales de libros enteros y evaluación. Requiere una laptop con el
índice ya construido y un PDF abierto en el visor. Si el índice no está listo,
este bloque se dicta con `demo-results.md` y no se improvisa.

## El día anterior (10–15 minutos en la corrida verificada)

```bash
cd course/exercises/embeddings_rag_bonus
source .venv/bin/activate
BOOKS_ROOT="/path/to/books"

# 1. ¿Se puede leer todo lo que declara el manifest?
python scripts/preflight.py --books-root "$BOOKS_ROOT"

# 2. Solo si preflight reportó needs-ocr: marcar esas filas como text_policy=ocr
python scripts/ocr.py --books-root "$BOOKS_ROOT"

# 3. Construir
python scripts/build_index.py --books-root "$BOOKS_ROOT"

# 4. Guardar los resultados que se van a mostrar
python scripts/test_core.py
```

Lista de verificación antes de cerrar la laptop:

- [ ] `preflight-report.json` sin filas `missing`, `damaged`, `encrypted` ni
      `empty-window`.
- [ ] `build-log.md` existe y dice cuántas de las 20 obras entraron.
- [ ] Las cuatro consultas de la sesión corren en menos de cinco segundos cada una.
- [ ] Los resultados observados están copiados en `demo-results.md`.
- [ ] Un PDF de la lista abierto en la página que se va a citar en vivo.
- [ ] Wi-Fi apagado una vez: la búsqueda debe seguir funcionando sin red.

Si alguna obra quedó fuera, no se oculta: el número real de obras indexadas está en
`build-log.md` y es lo que se dice en clase.

Tiempo observado: 8 min 58 s de OCR para 140 páginas y 78.17 s para construir el
índice. La instalación o la primera descarga del modelo pueden añadir tiempo, por
eso se hacen fuera de clase.

La extensión de libros enteros se prepara, no se reconstruye en vivo: 18/18
libros, 8,669 páginas, 14,726 fragmentos y build final de 407.16 s. La evaluación
usa 12 preguntas y un pool de 123 candidatos; dense alcanza Hit@3 de 0.917 y
hybrid 0.833. Kristian aprobó G2/G4: 6 candidatos permanecen sin juicio como
incompletitud aceptada y 38 de las 57 qrels positivas se descubrieron desde los
propios recuperadores comparados.

## Minuto a minuto

| min | bloque | qué se hace |
| ---: | --- | --- |
| 0–3 | La pregunta | «Tengo 185 PDF en el disco y quiero encontrar ideas, no palabras.» Mostrar el directorio, no el código. |
| 3–7 | Antes del vector | Correr `preflight.py` en vivo. Es el punto pedagógico: inventario, derechos, páginas legibles y escaneados **antes** de vectorizar. |
| 7–10 | Qué es un embedding | Coordenada semántica. Cercanía no es verdad, ni causalidad, ni consenso. |
| 10–14 | Demo 1 — lexical | Consulta en español, `--mode lexical`. Falla o devuelve poco: los libros están en inglés. |
| 14–19 | Demo 2 — densa | Misma consulta, `--mode dense`. Abrir el PDF en la página devuelta y verificar en vivo. |
| 19–23 | Demo 3 — híbrida | `--mode hybrid`. Explicar RRF y la regla de un fragmento por obra. |
| 23–26 | El falso positivo | Correr la consulta de incentivos y motivación intrínseca. Mostrar un resultado malo y decir por qué el modelo lo trajo. |
| 26–30 | Cuándo empieza RAG | `--json`. El paquete de evidencia es la entrada del LLM; la cita con página es la condición de aceptación. |
| 30–34 | Transferencia y cierre | Clasificar tres preguntas: híbrida/RAG, base estructurada, o relaciones explícitas. |

Si hay seis minutos adicionales, insertar después de «Lo que hay en el estante»
la escala de 18 libros completos y después de «La búsqueda híbrida» la tabla de
evaluación. No recortar la verificación del PDF para hacerles espacio.

## Las cuatro consultas de la sesión

```bash
python scripts/search.py "¿Cómo distinguir validez interna de validez externa?" --mode lexical
python scripts/search.py "¿Cómo distinguir validez interna de validez externa?" --mode dense
python scripts/search.py "¿Qué cambia entre interacción repetida y juego de una sola vez?" --mode hybrid
python scripts/search.py "¿Por qué los incentivos monetarios pueden desplazar motivación intrínseca?" --mode hybrid
python scripts/search.py "¿Qué cambia entre interacción repetida y juego de una sola vez?" --mode hybrid --json
```

Correrlas una vez antes de clase: el primer uso del modelo carga pesos y tarda más
que los siguientes.

## Qué decir en los tres momentos difíciles

**«¿El puntaje 0.78 significa que es 78% correcto?»**
No. Es similitud coseno entre dos vectores. No es probabilidad, no es exactitud y no
compara entre consultas distintas. Lo único que autoriza es abrir la página.

**«¿Entonces el modelo leyó los libros?»**
No. El modelo convirtió fragmentos en coordenadas. Quien decide relevancia es la
persona que abre el PDF en la página citada. Si nadie abre el PDF, no hay evidencia.

**«¿Por qué salió ese resultado que no tiene nada que ver?»**
Porque la cercanía semántica es contexto, no verdad ni pertinencia. Ese falso
positivo es parte de la clase: la métrica de éxito es cita verificable, no
«suena bien».

## Ejercicio de transferencia (últimos 4 minutos)

La sala clasifica tres preguntas:

1. «¿Qué textos discuten spillovers entre unidades?» → búsqueda híbrida/RAG.
2. «¿Cuál fue el desempleo de Lima en 2024?» → base estructurada, no embeddings.
3. «¿Qué autores usaron ENAHO y diferencias en diferencias para estudiar empleo
   femenino?» → filtros + grafo ligero, o extracción estructurada equivalente.

Lo evaluable no es memorizar herramientas: es escoger el tipo de recuperación que
corresponde a la pregunta.

## Fallback si algo falla en vivo

1. **El modelo no carga o no hay red:** correr solo `--mode lexical` y usar esa
   carencia para explicar qué añaden los embeddings. Es una demo válida.
2. **El índice no está:** leer los resultados congelados de `demo-results.md` y
   decir explícitamente que son de una corrida anterior.
3. **Una consulta tarda demasiado:** pasar a la siguiente y volver al final.
4. **Un resultado esperado no aparece:** mostrarlo como lo que es. Un recuperador
   que falla frente a la clase enseña más que uno que siempre acierta.

Nunca se muestran puntajes ni páginas que no salieron de una corrida real.
