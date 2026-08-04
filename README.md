# TeachResearchGenAI

Material del taller **IA generativa para la investigación económica y social**
(cuatro horas docentes, grupo pequeño de investigadores sociales).

Sitio público: <https://kmlv.github.io/TeachResearchGenAI>

El punto de entrada para quienes participan en la clase es la portada del
sitio. Es una sola página con dos bloques, presentaciones y materiales, desde
la que se llega a las cinco secciones, a los laboratorios y a la guía técnica
sin compartir carpetas.

## Estructura

| Ruta | Qué contiene | Se versiona | Se publica |
|---|---|---|---|
| `index.qmd` | Portada del sitio y única página normal que se publica. | Sí | Sí |
| `materiales.qmd`, `pages/` | Páginas anteriores del sitio. Fuera de la lista de render mientras la portada las reemplaza. | Sí | No |
| `course/slides/` | Fuente Quarto de las presentaciones y componentes del reproductor. | Sí | Las cinco secciones vigentes |
| `course/exercises/` | Laboratorios y demos reproducibles. | Sí | Mediante enlaces al repositorio |
| `materials/` | Archivos pequeños y documentación pública. | Sí | Sí |
| `examples/` | Ejemplos reproducibles de la clase. | Sí | Mediante enlaces al repositorio |
| `deliverables/` | Documentos de trabajo y artefactos de audio. | Solo los dos documentos que el sitio incluye | Solo dentro de una página |
| Material de preparación local | Fuentes originales y notas internas. | No | No |
| `_site/` | Salida del render. | No | Es el sitio |

## Render local

Requiere [Quarto](https://quarto.org) 1.9.37 (la misma versión que fija CI).
El sitio no ejecuta código, así que no hace falta Python ni R.

```bash
quarto preview        # servidor local con recarga automática
quarto render         # genera _site/
```

## Publicación

`.github/workflows/publish.yml` renderiza el sitio en cada push a `main` (y a
demanda con *Run workflow*) y lo despliega en GitHub Pages como artefacto de
build. El árbol renderizado nunca se commitea.

El repositorio usa **GitHub Actions** como fuente de Pages. Esa configuración
se realiza una sola vez al crear el sitio.

Para subir la versión de Quarto, cambiar `version:` en el workflow y usar la
misma localmente.

## Qué se publica y qué no

Publicar es una decisión explícita, no un efecto secundario. `_quarto.yml`
declara una lista blanca de render: solo se publica lo que está nombrado ahí.

El sitio publica únicamente los seis archivos nombrados en la lista `render:`:

- `index.qmd`
- `course/slides/ia-generativa-investigacion-ciencias-sociales.qmd`
- `course/slides/literatura-agentes-integrados.qmd`
- `course/slides/analisis-datos-codex-jupyter.qmd`
- `course/slides/lean-verificacion-matematica.qmd`
- `course/slides/bonus-embeddings-rag.qmd`

`materiales.qmd`, `pages/propuesta.qmd` y `pages/herramientas.qmd` siguen en el
repositorio pero salieron de la lista: la portada las reemplaza. Quedan fuera,
deliberadamente: las revisiones internas, las fuentes originales, los archivos
temporales, los entornos locales, los índices y cachés de los laboratorios y los
audios de trabajo. Los activos grandes aprobados para participantes se publican
en una versión de GitHub, no en el historial del repositorio.

Para publicar una página nueva hay que añadirla a la lista `render:` de
`_quarto.yml`. Si no está en la lista, no se publica.

### Dos barreras distintas

La lista blanca de `_quarto.yml` decide qué entra en el sitio. No decide qué
entra en el repositorio, y el repositorio que publica un sitio en GitHub Pages
también es público. Esa segunda barrera es `.gitignore`, que deja fuera del
control de versiones el material local de preparación y todos los artefactos
de trabajo salvo los dos documentos que el sitio incluye.

Antes del primer `push`, conviene revisar la lista real de archivos candidatos:

```bash
git ls-files --others --exclude-standard   # lo que un `git add -A` subiría
```

## Cómo se produjo este material

El taller se preparó con asistencia de varios modelos de lenguaje, coordinados
mediante notas internas que se quedan fuera del repositorio. Cada documento
publicado dice en su encabezado qué modelo lo redactó y quién lo revisó, que es
la misma regla de documentación que propone el taller.

## Licencia

Todavía no se ha elegido una licencia. Mientras no exista un archivo
`LICENSE`, el contenido conserva todos los derechos por defecto. Publicar el
sitio permite consultarlo y descargarlo, pero no concede permisos adicionales
de reutilización.
