# Descubrimiento: buscar en OpenAlex sin confundirlo con cribar

Este subdirectorio añade **un paso anterior** al laboratorio, y solo uno: cómo
se arma una búsqueda automatizada que otra persona pueda repetir.

> **Descubrir no es cribar, y un candidato no es evidencia.**
> Nada de lo que produce esta carpeta ha sido leído por nadie. `candidates.csv`
> es una lista de cosas que existen, no una lista de cosas que sirven. El
> cribado sigue ocurriendo en el laboratorio padre, con el protocolo congelado
> y la compuerta humana; el ledger oficial sigue exigiendo una decisión de una
> persona.

El laboratorio padre no cambia. `case/` sigue congelado, `case/candidates.csv`
sigue siendo el corpus didáctico de doce registros, y **nada de aquí entra allí
automáticamente**.

## Requisitos

Python 3.9 o superior. Solo biblioteca estándar: sin `pip install`, sin
dependencias y —si hace falta— sin internet.

## Los cuatro archivos que importan

```text
discovery/
├── search_strategy.json    lo que un humano decidió buscar, antes de buscar
├── scripts/
│   ├── search_openalex.py  ejecuta la estrategia y normaliza
│   └── test_discovery.py   25 pruebas, sin red y sin modelo
├── fixture/
│   └── openalex_response.json   una respuesta grabada, para dar clase sin wifi
└── output/                 se genera; no se versiona
```

La estrategia se escribe **primero** y se versiona. Ese es el punto pedagógico
completo: en un chat, la consulta se improvisa, se pierde en el hilo y nadie
puede repetirla; aquí es un archivo que se lee, se critica y se corrige.

### Por qué tres consultas y no una

No es por falta de sintaxis. El parámetro `search` de OpenAlex **sí admite
booleanos**: `AND`, `OR` y `NOT` en mayúsculas, frases entre comillas y
paréntesis; el límite documentado es de longitud, no de expresividad. Tres
consultas son una decisión.

Una sola cadena larga devuelve un montón indistinguible: si un trabajo aparece,
nadie puede decir después **qué parte de la consulta lo trajo**. Con tres
familias, `candidates.csv` guarda en `query_id` cuál lo encontró primero y
`dedup_report.csv` muestra cuáles lo repitieron. Un candidato que solo aparece
en `Q3` es información sobre su estrategia; en una cadena única, esa
información no existe.

El costo es tener que deduplicar. Por eso el reporte de duplicados es un
producto de primera clase aquí, y no un detalle interno del script.

## Cómo se usa

```bash
cd course/exercises/literature_agent_lab/discovery

python3 scripts/test_discovery.py          # 25 pruebas, sin red
python3 scripts/search_openalex.py --offline   # corre con la fixture grabada
python3 scripts/search_openalex.py             # intenta la API; si falla, cae a la fixture
python3 scripts/search_openalex.py --live-only # falla si no hay API; no inventa nada
```

Las tres corridas escriben lo mismo en `output/`: la respuesta cruda,
`candidates.csv`, `dedup_report.csv` y `search_log.json`.

### Los modos, y por qué son tres

| Modo | Qué hace | Cuándo |
| --- | --- | --- |
| _(sin bandera)_ | intenta la API; si no responde, usa la fixture **y lo escribe en el registro** | clase normal |
| `--offline` | no toca la red | wifi de conferencia |
| `--live-only` | se niega a producir resultados si la API no responde | cuando el resultado va a usarse de verdad |

La caída a la fixture **nunca es silenciosa**: queda en
`search_log.json → fallback.reason` y se imprime en pantalla. Un resultado que
parece de la API y salió de un archivo local es la peor forma de equivocarse.

## Qué produce, exactamente

| Archivo | Contenido |
| --- | --- |
| `output/raw/*.json` | la respuesta sin tocar, para poder discutir qué devolvió la fuente |
| `output/candidates.csv` | `candidate_id, query_id, title, year, doi, openalex_id, venue, type, first_author, n_authors, has_abstract` |
| `output/dedup_report.csv` | cada descarte, contra qué candidato, por qué campo coincidió y si el tope conservó la fila canónica |
| `output/search_log.json` | modo, consultas, cuentas, tope aplicado, y si hubo clave de API (no cuál) |

### Dos decisiones del normalizador que conviene explicar en clase

**No se guarda el resumen.** OpenAlex devuelve el abstract como índice
invertido. El normalizador solo anota `has_abstract: true|false`. Saber que hay
resumen sirve para decidir qué recuperar después; el texto del resumen no es
nuestro para redistribuirlo. Es la misma regla del laboratorio padre: aquí
circulan metadatos.

**Los duplicados se resuelven por identificador, no por título.** Un DOI
significa lo mismo fuera de esta carpeta; un título, no. El script compara DOI y
`openalex_id`, y usa el título normalizado **solo** cuando faltan los dos. Dos
registros con el mismo título y DOIs distintos suelen ser el preprint y la
versión publicada: son filas distintas y no le toca a un script fusionarlas.

## La clave de API

OpenAlex **no exige clave**. Si usted tiene una:

```bash
export OPENALEX_API_KEY="su-clave"      # solo en el entorno, nunca en un archivo
export OPENALEX_MAILTO="usted@ejemplo.org"   # opcional: grupo de peticiones cortés
python3 scripts/search_openalex.py --live-only
```

El script lee ambas del entorno y de ningún otro sitio. La clave viaja en la
petición y **en ningún artefacto**: la URL que se escribe en `search_log.json`
lleva `api_key=***`. El registro anota `api_key_provided: true`, no el valor. El
correo tampoco se guarda: solo `mailto_provided: true`. Hay una prueba que corre
el script con una clave centinela en el entorno y revisa **todos** los archivos
de salida buscándola.

## Sobre la fixture

`fixture/openalex_response.json` contiene **una respuesta por consulta**, tomada
de una corrida real y minimizada para el repositorio. Su bloque
`_fixture_provenance` registra fecha, estrategia, endpoint y transformación.

- Los títulos, DOI, OpenAlex ID, año, tipo, autoría y venue provienen de la API.
- El texto de los resúmenes no se versiona. Solo queda un marcador booleano de
  presencia, que el normalizador convierte en `has_abstract`.
- La fixture no pretende ser la respuesta cruda. Las respuestas completas se
  guardan durante una corrida en `output/raw/`, que está ignorado por Git.
- Mantener una respuesta separada para Q1, Q2 y Q3 evita fingir que una misma
  página fue devuelta por tres consultas distintas.

Para reemplazarla por una real, con red:

```bash
python3 scripts/search_openalex.py --live-only \
  --save-fixture fixture/openalex_response.json
```

Eso actualiza las tres respuestas de la fixture y su bloque de procedencia. La
captura se minimiza automáticamente: conserva metadatos, no texto de abstracts.

## Flujo exacto en Codex Desktop

1. Abra Codex y apunte el espacio de trabajo a
   `course/exercises/literature_agent_lab/` (la carpeta **padre**, para que el
   agente pueda leer `case/question.md`).
2. Primer encargo, sin permitir ediciones:

   ```text
   Lee discovery/search_strategy.json y case/question.md.

   No edites nada.

   Dime:
   - qué recupera cada consulta que la otra no
   - qué hueco de `huecos_conocidos` te parece el más costoso para esta pregunta
   - una consulta que añadirías, y qué esperas que aparezca que hoy no aparece
   ```

3. Segundo encargo, ya ejecutando:

   ```text
   Ejecuta:
     cd discovery && python3 scripts/search_openalex.py --offline

   Luego abre output/dedup_report.csv y explícame, fila por fila,
   por qué campo coincidió cada descarte.

   No edites case/ ni human/ ni official/.
   ```

4. Cuando Codex pida aprobar la ejecución de comandos, apruebe. Ese diálogo es
   el análogo, en la herramienta, de la compuerta humana del laboratorio.

## Flujo exacto en VS Code

1. `File → Open Folder…` y elija
   `course/exercises/literature_agent_lab/`.
2. Abra la terminal integrada con `Terminal → New Terminal`:

   ```bash
   cd discovery
   python3 --version          # debe decir 3.9 o superior
   python3 scripts/test_discovery.py
   python3 scripts/search_openalex.py --offline
   ```

3. Abra `output/candidates.csv`. Para verlo como tabla y no como texto separado
   por comas, instale la extensión **Rainbow CSV** y use
   `CSV: Align columns`.
4. Con la extensión de Codex o de Claude Code instalada, los dos encargos de
   arriba funcionan igual desde el panel lateral.
5. Si edita `search_strategy.json`, vuelva a correr el script y **compare los
   dos `search_log.json`**. Eso —y no la memoria de nadie— es lo que hace que
   una búsqueda sea reproducible.

## Qué NO hace este script

- **No decide relevancia.** No lee títulos con criterio ni aplica
  `case/protocol.md`. Ordena y quita repetidos; nada más.
- **No es exhaustivo, y lo dice.** Una base, un tipo de documento, términos solo
  en inglés, una página por consulta. Todo eso está escrito en
  `huecos_conocidos`, no escondido.
- **No trunca en silencio.** Si el tope deja candidatos fuera, aparece en
  `search_log.json → cap.dropped_by_cap` y en pantalla.
- **No escribe en `case/`, `work/`, `human/` ni `official/`.** El corpus
  congelado del laboratorio no se toca desde aquí.

## Cómo enlaza con el resto del laboratorio

Descubrir produce candidatos. Cribar los reduce con un protocolo escrito antes.
Extraer los ancla a un pasaje exacto. Verificar es una persona escribiendo una
decisión. El ledger es lo que sobrevive a las cuatro cosas.

Esta carpeta es la primera, y es la única de las cinco donde equivocarse es
barato: un candidato de más cuesta un minuto de cribado. Por eso es también la
única donde conviene ser generoso.
