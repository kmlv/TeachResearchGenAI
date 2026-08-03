# Panorama de herramientas para revisión de literatura (2026)

**Autor:** Claude (Opus 5)
**Fecha del documento:** 2026-08-02
**Revisión:** 3 — incorpora la auditoría de fuentes de Codex y la revisión de agy

> **Procedencia de las cifras.** Todos los precios y límites de este documento
> fueron contrastados contra la página oficial del proveedor por **Codex el
> 2026-08-02**, y cada uno enlaza su fuente primaria. Yo redacté el análisis
> funcional sin acceso a red: aporto el juicio sobre qué hace cada herramienta y
> para quién sirve, no la verificación del precio. Esa división es deliberada y
> queda escrita para que cualquier cifra sea rastreable a su enlace y a su
> fecha. Cuando el proveedor no publica un precio público —Undermind, scite
> premium, DistillerSR, Scopus AI, WoS Research Assistant— el documento dice
> **"consultar checkout" o "a medida" y no estima**. Este mercado reprecia
> rápido: verifique en el checkout antes de comprometer presupuesto.

---

## 1. El marco: cuatro etapas, no una sola herramienta

La pregunta "¿cuál es la mejor herramienta de revisión de literatura?" está mal
planteada, porque el proceso tiene cuatro etapas con economías distintas:

1. **Descubrimiento** — encontrar lo que existe. Aquí la IA aporta un margen
   real de *recall*: recupera trabajo relevante que la consulta booleana perdió
   por usar otro vocabulario.
2. **Cribado (screening)** — decidir qué entra. El aprendizaje activo está
   validado metodológicamente y es barato; es la etapa con mejor relación
   evidencia/costo de toda la cadena.
3. **Extracción** — sacar datos estructurados de cada estudio. La IA acelera
   mucho, pero traslada el costo a la verificación: hay que auditar una muestra
   siempre.
4. **Síntesis y redacción** — donde la IA es *menos* confiable y *más*
   tentadora. Es el punto donde aparecen citas inventadas o mal atribuidas.

Evalúo cada herramienta por **etapa** y con seis criterios: **cobertura del
corpus**, **reproducibilidad/auditabilidad** (¿puede otra persona re-ejecutar la
búsqueda?), **exportación y dependencia del proveedor**, **costo real**,
**privacidad** (¿salen del equipo datos no publicados?) y **carga de
verificación** que impone al usuario.

**Lo que dice la evidencia, no el marketing.** Elicit reporta alto *recall* y
exactitud frente a referencias de Cochrane, pero un [estudio independiente de
factibilidad de 2026](https://www.cambridge.org/core/journals/research-synthesis-methods/article/using-elicit-ai-research-assistant-for-data-extraction-in-systematic-reviews-a-feasibility-study-across-environmental-and-life-sciences/C97DAEC70C3173A260F0B12E729E7250)
midió **85,6 % de exactitud global en extracción**, y una [actualización
sistemática de AHRQ de
2025](https://www.ncbi.nlm.nih.gov/sites/books/NBK620201/) encontró *recall* y
precisión medianos **débiles** en herramientas de búsqueda y alrededor de **66
% de extracciones correctas**. La lectura correcta no es "no sirven": es que **ninguna herramienta
por sí sola satisface una revisión sistemática publicable**, y que toda
extracción asistida se reporta como *verificada por humano*. Ese es el supuesto
que atraviesa todas las recomendaciones de abajo.

No hay ganador universal, y desconfiaría de cualquier informe que lo proponga.
Sí hay elecciones claramente mejores *por etapa y por perfil*.

---

## 2. Descubrimiento y síntesis: SaaS de frontera

| Herramienta | Diferenciador real | Precio (verificado 2026-08-02) | Limitación material | Mejor para |
|---|---|---|---|---|
| **[Elicit](https://elicit.com)** | Extracción tabular a escala y flujo dedicado de revisión sistemática: cada celda cita el pasaje de origen | Basic gratis; Plus US$11/usuario/mes anual (US$132/año); Pro US$39/mes anual (US$480/año); Scale US$89/mes anual — [fuente](https://elicit.com/pricing) | La cobertura sigue dependiendo del corpus y del acceso a PDF; sus métricas son principalmente evaluaciones del proveedor y cada decisión requiere auditoría humana. Desde mayo de 2026 el flujo dedicado [declara compatibilidad con PRISMA 2020](https://elicit.com/blog/systematic-review-for-prisma-2020) | **Mejor SaaS integral** para revisiones de alcance y SLR semiautomatizadas |
| **[Consensus](https://consensus.app)** | Lectura a nivel de *afirmación*, no de resumen; medidor de consenso para preguntas sí/no | Gratis: 15 mensajes Pro y 3 *Deep reviews*/mes; Pro US$20/mes o US$144/año; Deep US$65/mes o US$540/año — [fuente](https://help.consensus.app/en/articles/10087865-subscription-plans) | El medidor comprime literatura heterogénea en una barra: útil para orientarse, peligroso como conclusión | Orientación inicial y docencia |
| **[scite](https://scite.ai)** | *Citation statements*: muestra si una cita **apoya, contrasta o solo menciona** el trabajo citado | Prueba gratuita; suscripción Premium requerida para MCP, con precio vigente visible al registrarse — [fuente](https://api.scite.ai/docs) | Depende de la cobertura de texto completo indexado | **Verificar referencias** y detectar citas heredadas sin leer |
| **[ResearchRabbit](https://www.researchrabbit.ai)** | Grafo de citas con *snowballing* hacia atrás y adelante; la línea base gratuita de la categoría | Free US$0; RR+ US$10/mes anual o US$12,50 mensual — [fuente](https://www.researchrabbit.ai/pricing) | No es buscador booleano ni sustituye una base indexada | Complemento gratuito a cualquier buscador |
| **[Litmaps](https://www.litmaps.com)** / Connected Papers / Inciteful | Mapas de citas con alertas de literatura nueva | Litmaps Pro académico US$10/mes anual — [fuente](https://www.litmaps.com/pricing); Inciteful gratis | Mismo límite: descubrimiento por vecindad, no por criterio | Vigilancia de un tema en el tiempo |
| **[Undermind](https://undermind.ai)** | Trata la **saturación de búsqueda** como resultado explícito y reportable, no como acto de fe | A medida / por créditos; consultar checkout | Lento y caro por consulta; rinde mejor en nichos técnicos estrechos | Literatura difícil de hallar en temas técnicos |
| **Scopus AI** (Elsevier) / **WoS Research Assistant** (Clarivate) | Calidad del corpus: curado, desambiguado, con red de citas confiable | Suscripción institucional, a medida | Exportación de salidas de IA restringida; se depende del acuerdo de la biblioteca | Quien ya tiene la suscripción |
| **NotebookLM** (Google) | Razona sobre *tu* corpus subido con anclaje a la fuente y cita al fragmento | Gratis con límites; capacidad ampliada en Google AI Pro/Ultra | **Está anclado a las fuentes, lo que reduce la invención pero no la elimina**; sin búsqueda sistemática; exportación pobre | Leer un corpus ya reunido; enseñar verificación |
| **[Paperguide](https://paperguide.ai)** | Aspirante *all-in-one* emergente: descubrimiento, gestión de referencias, extracción y apoyo a RS en un solo flujo | Gratis: 1.000 créditos, 20 búsquedas/mes, sin SLR; Plus US$17/mes anual (SLR hasta 1.000 artículos); Pro US$39 (5.000); Max US$119 (10.000 y doble cribado PRISMA) — [fuente](https://paperguide.ai/pricing/) | Producto joven; menos validación independiente y trayectoria metodológica que Elicit y las plataformas de §3 | Quien quiere una sola herramienta y acepta el riesgo de un producto nuevo |
| **Agentes de investigación profunda** (ChatGPT, Claude, Gemini, Perplexity) | Informes largos que cruzan web y literatura en minutos | Incluidos en las suscripciones de frontera (~US$20/mes) | Cobertura débil de literatura de pago y **no reproducibles**: dos ejecuciones dan corpus distintos | Contexto y antecedentes; **no sirven como la búsqueda sistemática que se reporta**, aunque sí como apoyo declarado |
| **[Prism](https://openai.com/index/introducing-prism/)** (OpenAI) | Espacio de trabajo **gratuito para escritura** científica | Gratis | **No es un índice de descubrimiento** — no lo trate como buscador | Redactar, no buscar |
| **[Claude Science](https://www.anthropic.com/news/claude-science-ai-workbench)** (beta) | Banco de trabajo científico de Anthropic que integra literatura, datos y análisis | Beta; consultar disponibilidad | Beta: superficie y alcance aún cambian | Seguimiento temprano, no dependencia productiva |

**Dos juicios que conviene explicitar.** Primero, el *snowballing* por grafo de
citas es una práctica **fuertemente recomendada y complementaria** de la
búsqueda booleana, y en muchas revisiones mejora el *recall* de forma material;
no afirmo que sea universalmente obligatorio en toda revisión defendible, y
retiro esa formulación de la versión anterior. Segundo, los agentes de
investigación profunda no están descalificados de todo papel: están
descalificados como **la búsqueda única que se reporta**. Como apoyo declarado
—mapear un campo antes de escribir el protocolo— son legítimos.

---

## 3. Plataformas de flujo para revisiones sistemáticas

Aquí el criterio ya no es inteligencia sino **trazabilidad**: doble cribado,
resolución de conflictos, diagrama PRISMA y registro de auditoría.

| Plataforma | Diferenciador | Precio (verificado 2026-08-02) | Limitación | Mejor para |
|---|---|---|---|---|
| **Covidence** | Estándar de facto tipo Cochrane: cribado por duplicado, discrepancias, riesgo de sesgo, flujo PRISMA | Individual US$339/año (una revisión); tres revisiones US$907/año — [fuente](https://www.covidence.org/pricing/) | Flujo rígido, API prácticamente inexistente | Equipos con respaldo institucional |
| **Rayyan** | La mejor puerta de entrada: cribado rápido con cegado y sugerencias por ML | Free: **3 revisiones activas y 2 revisores**; Essential US$8,33/mes facturado trimestral; Advanced US$13,33/mes trimestral — [fuente](https://www.rayyan.ai/pricing) | La capa gratuita se ha estrechado; parte de la exportación quedó tras el muro de pago | Estudiantes y equipos pequeños |
| **DistillerSR** | Grado regulatorio: rastro de auditoría completo, formularios configurables | A medida | Caro y pesado | ETES/HTA, farmacéutica, trabajo regulado |
| **EPPI-Reviewer** (UCL) | Soporte metodológico profundo, cribado por prioridad, revisiones vivas | A medida / consultar sitio oficial | Curva de aprendizaje | Política pública, ciencias sociales, revisiones vivas |
| **Nested Knowledge** | Mapas de evidencia interactivos y meta-análisis en el mismo flujo | Primer *Nest* gratis; Academic US$19,95/usuario/mes; Academic+ AI US$69,95 — [fuente](https://about.nested-knowledge.com/academic-studentshome/) | Menos estandarizado en entornos Cochrane | Visualización para audiencias no técnicas |
| **SR Accelerator** (IEBH, Bond) | **Gratuito.** *Polyglot Search Translator* traduce la consulta booleana entre PubMed, Embase, Scopus, WoS y otras; incluye *Deduplicator* y *SearchRefinery* | Gratis | Micro-herramientas sueltas, no una plataforma | **Probablemente el mayor ahorro de tiempo por dólar de toda la cadena** |
| **ASReview** (Utrecht, código abierto) | Cribado por aprendizaje activo con metodología publicada y revisada por pares; corre localmente | Gratis | Prioriza el cribado, no reemplaza la plataforma; requiere soltura técnica | Cualquiera con muchos registros y poco presupuesto |
| **CADIMA**, `revtools`, `CiteSource`, `PRISMA2020`, `metafor`, **RobotReviewer** | Ecosistema libre en R: deduplicación con trazabilidad de qué base aportó cada registro, diagramas de flujo, meta-análisis, riesgo de sesgo | Gratis | Requieren código | Perfil metodológico con presupuesto cero |

**Precisión sobre ASReview.** En la versión anterior escribí que es
"completamente reproducible". Es más exacto decir que **es reproducible cuando
se registran las etiquetas, el modelo, la semilla, la regla de parada y la
versión del software**. Sin ese registro, el aprendizaje activo es tan opaco
como cualquier otra caja negra. La propiedad valiosa es que ASReview *permite*
ese registro y los datos no salen del equipo; no que lo garantice solo.

---

## 4. La capa de integración: MCP, skills y APIs abiertas

Esta es la sección con mayor rendimiento por dólar y la que menos aparece en
comparativas comerciales. En 2026 lo relevante ya no es solo *qué* herramienta
se usa, sino **desde dónde se la invoca**: las plataformas de frontera se están
exponiendo como servidores MCP y aplicaciones dentro del asistente.

| Integración | Qué habilita | Requisito / advertencia |
|---|---|---|
| **[Elicit vía MCP](https://support.elicit.com/en/articles/14757404-use-elicit-via-mcp-server)** + [API](https://docs.elicit.com/) | Consultar Elicit y su extracción desde Claude u otro cliente MCP, sin salir del flujo de trabajo | Oficial; disponible en planes **Pro y superiores** |
| **[Consensus en ChatGPT](https://help.consensus.app/en/articles/10059020-consensus-in-chatgpt)** y **[Consensus en Claude vía MCP](https://help.consensus.app/en/articles/13694300-how-to-use-consensus-in-claude-via-mcp)** | Búsqueda a nivel de afirmación dentro del asistente; Consensus además publica *skills* descargables de revisión de literatura | Oficial; funciona desde la capa gratuita (30 búsquedas de ChatGPT o llamadas MCP al mes); cuotas mayores según plan |
| **[scite MCP](https://scite.ai/mcp)** | Verificación de citas dentro del asistente: saber si una referencia realmente apoya lo que se le atribuye | Oficial. Es la integración que más directamente ataca la cita inventada |
| **[Zotero MCP](https://github.com/54yyyu/zotero-mcp)** | Expone *tu* biblioteca (búsqueda, metadatos, texto completo) como corpus de anclaje | **Mantenido por la comunidad, no oficial.** Lo más seguro es ejecutarlo **local y en solo lectura** |
| **arXiv MCP**, **paper-search-mcp**, **PubMed/E-utilities**, **OpenAlex**, **Semantic Scholar** | Envoltorios sobre APIs abiertas: buscar y leer sin depender de la memoria del modelo | Comunitarios; fijar versión y revisar el repositorio |
| **[ChatGPT / Codex](https://learn.chatgpt.com/docs/skills-and-plugins)** | ChatGPT de escritorio, Codex CLI y el IDE **comparten configuración MCP local**, y admiten *skills*/plugins | Sujeto a la superficie y al *workspace*; los [servidores MCP](https://learn.chatgpt.com/docs/extend/mcp) locales se configuran una vez y se comparten entre escritorio, CLI e IDE |
| **[Skills de Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude)** | Instalar o versionar un `SKILL.md` que codifique el protocolo; sirve en Claude, Claude Code y, si el formato es portable, otros agentes | Disponibles según superficie/plan y requieren ejecución de código; una skill puede instalar paquetes o invocar terceros, así que hay que auditarla |
| **VS Code** (Codex IDE, Claude Code o clientes con MCP) | Invocar los mismos MCP y skills junto al repositorio, Quarto, datos y bibliografía | Es la ruta más reproducible para equipos técnicos; las credenciales y permisos del MCP siguen aplicando |
| **[Claude Science](https://www.anthropic.com/news/claude-science-ai-workbench)** | Banco de trabajo científico integrado | Beta |

**Qué es —y qué no es— un *skill*.** Un skill es una **carpeta versionada con
instrucciones, flujo de trabajo y recursos** (`SKILL.md` en `~/.claude/skills/`
o en `.claude/skills/` del repositorio) que el modelo invoca según su
descripción. **No es un corpus académico ni una fuente**: no añade cobertura,
añade *método repetible*. Para revisión de literatura eso es exactamente lo
valioso: codifica tus criterios de inclusión/exclusión, tu esquema de
extracción, tu estilo de cita y tu formato PRISMA, queda en git y se aplica
igual entre personas. Como ejemplos **auditables, no como recomendación**:
existe un [*skill* de revisión de literatura de
**K-Dense**](https://github.com/k-dense-ai/scientific-agent-skills) con licencia MIT
—antes de usarlo conviene revisar sus dependencias y el comportamiento de
figuras que impone por defecto— y un [flujo comunitario de investigación
profunda](https://github.com/lingzhi227/agent-research-skills) con scripts para
búsqueda, PDF y BibTeX. Son ejemplos auditables, no endosos: léalos como se lee
código de terceros, porque eso son.

> **Advertencia de seguridad, no opcional.** Los servidores MCP comunitarios se
> ejecutan con tus credenciales y tu sistema de archivos. Antes de instalar:
> revisar el repositorio, preferir los de mantenimiento activo, **fijar la
> versión**, preferir modo local y de solo lectura, y no dar acceso a
> directorios sensibles. Un servidor MCP es **código ejecutable**, no una
> extensión de navegador.

**APIs y datos abiertos — el argumento de reproducibilidad, con su matiz.**
**OpenAlex**, **Crossref**, **Unpaywall**, **PubMed E-utilities**, **Semantic
Scholar Academic Graph**, **OpenCitations** y **CORE** permiten que la búsqueda
deje de ser una serie de clics irrepetibles y pase a ser **código versionado**
(`pyalex` en Python, `openalexR` en R). Dos precisiones necesarias:

- **OpenAlex ya no es "sin clave".** El conjunto de datos sigue siendo libre y
  CC0, pero el acceso a la API opera bajo un modelo medido con **clave gratuita
  y un crédito diario de US$1** —
  [documentación oficial](https://developers.openalex.org/guides/authentication).
- Las APIs abiertas **mejoran** la reproducibilidad, pero **no garantizan una
  re-ejecución idéntica** salvo que se fije la instantánea o versión de los
  datos. Un corpus vivo cambia bajo los pies del script.

**Zotero como centro de gravedad, y por qué no EndNote ni Mendeley.** Zotero es
gratuito y abierto, con **Better BibTeX** (claves de cita estables para
LaTeX/Quarto), gestión de PDF y conector de navegador. Almacenamiento: **300 MB
gratis; 2 GB US$20/año; 6 GB US$60; ilimitado US$120** —
[fuente](https://www.zotero.org/support/individual_storage)— o sincronización
propia por WebDAV sin costo. EndNote y Mendeley siguen siendo los
predeterminados institucionales y funcionan; los dejo fuera de la recomendación
por tres razones concretas: ecosistema cerrado frente a API abierta y local,
ausencia de una integración MCP equivalente a la de Zotero, y peor encaje con
un flujo de manuscrito en git. Si su institución le impone uno de ellos, la
pérdida real está en la integración, no en la gestión bibliográfica.

**Redacción y bibliometría.** Para la etapa de escritura, **Writefull** y
**Jenni.ai** son populares para reformulación y autocompletado de citas: quedan
al borde de "revisión de literatura" y valen como apoyo de redacción, con la
misma regla de verificación que todo lo demás. **VS Code + Quarto + LaTeX
Workshop + selector de citas de Zotero** da una cadena de manuscrito gratuita y
versionada. Para bibliometría: `bibliometrix`/`biblioshiny`, **VOSviewer**,
**CiteSpace**, `litstudy`.

**Frontera abierta y privada.** [**PaperQA2**
(FutureHouse)](https://github.com/Future-House/paper-qa) hace RAG sobre tus
propios PDF con respuestas ancladas y citadas; [**OpenScholar**
(AI2)](https://github.com/akariasai/openscholar) combina
modelos abiertos con un almacén de decenas de millones de artículos de acceso
abierto. Con **Ollama** y un modelo local, todo el flujo puede correr sin que un
documento no publicado salga del equipo — relevante para datos sensibles,
revisión por pares confidencial o trabajo bajo convenio.

---

## 5. Recomendaciones por perfil, y una pila de bajo costo

- **Clase de pregrado / trabajo de curso.** NotebookLM + Consensus (capa
  gratuita) + Zotero. Todo gratuito, y el anclaje a fuentes de NotebookLM
  permite enseñar verificación en vez de prohibir la herramienta.
- **Tesis, revisión narrativa o de alcance.** Elicit para extracción tabular +
  ResearchRabbit para *snowballing* + scite para verificar las referencias
  citadas + Zotero + Polyglot para traducir la consulta entre bases.
- **Revisión sistemática publicable (PRISMA).** Protocolo registrado
  (PROSPERO/OSF) → consulta booleana en ≥2 bases vía Polyglot → deduplicación
  con CiteSource → cribado por duplicado en Rayyan o Covidence → ASReview para
  priorizar (registrando semilla, modelo y regla de parada) → diagrama con
  PRISMA2020. La IA generativa entra como apoyo **declarado** a la extracción,
  con verificación humana; **no** como la búsqueda que se reporta.
- **Trabajo regulatorio / ETES.** DistillerSR o EPPI-Reviewer: el rastro de
  auditoría es el requisito, no la velocidad.
- **Perfil computacional que prioriza reproducibilidad.** OpenAlex + `pyalex`
  (con clave e instantánea fechada) + PaperQA2 + Zotero MCP local + Claude Code
  o Codex + Quarto, todo en un repositorio.
- **Con respaldo institucional.** Scopus AI o WoS Research Assistant para
  descubrimiento + Covidence para el flujo: se paga por calidad de corpus y
  trazabilidad, que es donde el dinero rinde.

**Pila práctica de bajo costo (US$0–20/mes).** Zotero + Better BibTeX + Zotero
MCP local conectado a su asistente; OpenAlex, Crossref y Unpaywall como fuentes;
Polyglot y Deduplicator del SR Accelerator; ASReview para cribado; capa gratuita
de Rayyan (3 revisiones activas, 2 revisores) si necesita doble revisión;
NotebookLM para leer el corpus; VS Code + Quarto para escribir. **La única línea
pagada es la suscripción a un modelo de frontera (~US$20/mes), que la mayoría ya
tiene.** En reproducibilidad y privacidad esta pila supera a varias
combinaciones que cuestan diez veces más; su costo real es tiempo de
configuración inicial.

---

## 6. Tres advertencias transversales

1. **Los precios de arriba tienen fecha (2026-08-02) y fuente enlazada, no
   garantía.** Las capas gratuitas de este mercado se han estrechado de forma
   sostenida — Rayyan y Consensus son los ejemplos claros. Compruebe los límites
   vigentes en el checkout antes de comprometer un proyecto.
2. **Toda salida asistida se reporta como verificada por humano.** Con ~66 % de
   extracciones correctas en la evidencia agregada y 85,6 % en el mejor estudio
   independiente citado, la muestra de auditoría no es una formalidad: es lo que
   separa una revisión defendible de una rápida.
3. **Ninguna herramienta sustituye la justificación metodológica de la
   búsqueda.** Si no puede explicar por qué el corpus es el que es —qué bases,
   qué fechas, qué criterios, qué versión de los datos— la herramienta no salva
   la revisión.
