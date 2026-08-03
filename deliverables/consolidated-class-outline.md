# Propuesta consolidada actualizada

## IA generativa para la investigación económica y social — taller de cuatro horas

Esta versión integra la conversación original, la revisión independiente de
Fable 5, la revisión crítica de Codex y las decisiones confirmadas por Kristian
el 2 de agosto de 2026.

## Recomendación central

La clase debe dejar de parecer una lista de herramientas y convertirse en la
historia completa de una sola investigación. Cada bloque debe hacer avanzar el
mismo caso y terminar con una acción que el participante pueda repetir en su
propio proyecto.

La promesa recomendada es:

> Al terminar, podrás usar un asistente generalista de manera responsable en
> literatura, razonamiento y código; sabrás verificar sus resultados y
> construirás un agente individual, acotado y verificable; además entenderás
> cómo ese flujo puede escalar responsablemente a varios agentes.

## Condiciones confirmadas

- Grupo pequeño: entre 10 y 20 investigadores de economía, antropología,
  psicología, sociología, geografía y otras ciencias sociales.
- Cuatro horas completas de docencia; los descansos ocurren fuera de esas
  cuatro horas.
- Cada participante tendrá laptop, internet confiable y, en la mayoría de los
  casos, una cuenta de Claude o ChatGPT.
- Python será el lenguaje común del bloque de código. Stata y R se presentarán
  como lenguajes desde los cuales el mismo patrón puede transferirse.
- Juntos y ENAHO quedan aceptados como caso conductor, usando archivos pequeños
  preparados previamente y evitando descargas, merges o estimaciones pesadas en
  vivo.
- Idioma de trabajo: español, conservando términos técnicos en inglés cuando
  resulten naturales.

## Decisiones sugeridas

| Acción | Decisión |
|---|---|
| **Mantener** | Organizar por etapas del proceso de investigación, no por aplicaciones. |
| **Mantener** | Claude Code y Codex como stack principal; otras herramientas solo cuando cumplen una función especializada. |
| **Mantener** | Demos breves y reproducibles en vivo, más una demostración avanzada pregrabada. |
| **Agregar** | Un caso conductor único y aproximadamente 60 minutos de práctica distribuida. |
| **Agregar** | Un correo/encuesta previa, un paquete de ejercicios y una hoja de trabajo que el participante se lleva. |
| **Mover** | Las cuatro reglas de uso responsable al inicio y reforzarlas en todos los bloques. |
| **Combinar** | Hipótesis, explicaciones alternativas, robustez y referee en un patrón único: “colaborador adversarial”. |
| **Combinar** | Verificación de evidencia, construcción de un agente individual y orquestación en un bloque final: “de una tarea manual a un sistema verificable”. |
| **Reducir** | Enseñar una sola herramienta/patrón de búsqueda bibliográfica; dejar Consensus, Scite y Elicit como alternativas en una slide. |
| **Reducir** | Enseñar el flujo en Python; usar Stata y R solo para demostrar transferencia, no como tres rutas paralelas. |
| **Reducir** | Mecánica de embeddings, arquitectura RAG y configuración MCP. La construcción se limita a un agente individual con dos herramientas y límites explícitos. |
| **Eliminar** | Orquestación multiagente en vivo y demos que dependan de tiempos largos de inferencia. |
| **Eliminar** | Un bloque independiente de prompt engineering; los patrones de prompt se enseñan dentro de tareas reales. |

## Resultados de aprendizaje

Al terminar, cada participante podrá:

1. Mapear una pregunta de investigación a sus etapas y marcar en cuáles la IA
   propone, verifica o no debe decidir.
2. Obtener una síntesis de literatura y comprobar si una fuente primaria
   realmente respalda una afirmación y una cita.
3. Usar el patrón de colaborador adversarial para producir una explicación
   alternativa o un robustness check accionable.
4. Pedir a un asistente que explique, depure y pruebe código Python, y verificar
   el resultado mediante ejecución y sanity checks.
5. Aplicar cuatro reglas: verificar fuentes; conservar el juicio científico;
   proteger datos; documentar y transparentar el uso material conforme a las
   reglas de la revista, institución o financiador.
6. Construir y evaluar un agente individual con objetivo, herramientas, bucle,
   condición de parada y revisión humana; explicar después cómo puede escalar a
   varios agentes sin confundir acuerdo entre modelos con evidencia.

## Caso conductor confirmado

**Pregunta recomendada:**

> ¿Qué permiten concluir la literatura existente y los datos públicos sobre
> Juntos y la asistencia escolar, y qué diseño sería necesario para atribuirle
> un efecto causal?

La formulación importa. Un extracto pequeño de ENAHO puede servir para
descriptivos, depuración,
visualización y para mostrar problemas de selección; no debe presentarse como
si identificara por sí sola el efecto causal del programa. Para la parte causal
se utilizarían estudios publicados y, si existe un paquete de replicación
adecuado, un extracto preparado previamente.

Ventajas: relevancia regional, datos públicos, literatura real, problemas de
identificación reconocibles y continuidad entre literatura, hipótesis, código
y revisión adversarial. También permite preguntas de implementación,
heterogeneidad espacial, comportamiento, experiencia de los hogares y contexto
institucional que resultan pertinentes para distintas ciencias sociales.

Para mantenerlo liviano, la clase utilizará un CSV curado con pocas variables y
observaciones, más un paquete corto de literatura. Nada dependerá de descargar o
procesar la ENAHO completa durante la sesión.

## Cronograma: 240 minutos docentes más descansos

| Tiempo transcurrido | Min. docentes | Bloque | Producto del participante |
|---|---:|---|---|
| 0:00–0:15 | 15 | Apertura, promesa, caso y cuatro reglas | Mapa inicial: IA propone / IA verifica / humano decide |
| 0:15–0:40 | 25 | Cómo cambia el flujo de investigación | Crítica breve a un plan de investigación generado |
| 0:40–1:25 | 45 | Literatura: buscar, mapear y verificar | Hoja de afirmaciones verificadas/refutadas |
| 1:25–2:00 | 35 | El colaborador adversarial | Una amenaza o robustness check escrito como prosa científica |
| 2:00–2:10 | — | Descanso de 10 minutos | — |
| 2:10–3:10 | 60 | Código y análisis de datos en Python | Script corregido, sanity check y prompt documentado |
| 3:10–3:40 | 30 | Construcción de un agente auditor | Agente individual ejecutado, traza inspeccionada y límite humano definido |
| 3:40–3:45 | — | Microdescanso de 5 minutos | — |
| 3:45–4:05 | 20 | Síntesis, escritura y transparencia | Plan personal de uso para el día siguiente |
| 4:05–4:15 | 10 | Preguntas y cierre | Compromiso final / dudas pendientes |
| **Total docente** | **240** | **Duración transcurrida: 255 minutos** | **15 minutos adicionales de descanso** |

## Desarrollo de cada bloque

### 0. Apertura, caso y reglas — 15 min

- Promesa de la clase (3 min).
- Cuatro reglas en una sola slide (5 min).
- Presentación del caso conductor (5 min).
- Encuesta rápida: ¿qué partes del flujo ya delegan a una IA? (2 min).

Las cuatro reglas se vuelven etiquetas recurrentes en las slides y demos, no
una advertencia separada al final.

### 1. Cómo cambia el flujo — 25 min

- Pipeline completo, desde pregunta hasta comunicación (8 min).
- Matriz “IA propone / IA comprueba / humano decide” (5 min).
- Demo D1: convertir la pregunta del caso en plan de investigación (máximo 3
  min).
- Crítica colectiva: contenido útil, boilerplate, decisiones que faltan y
  elementos que un referee eliminaría (7 min).
- Transición hacia la literatura (2 min).

### 2. Literatura: buscar, mapear, verificar — 45 min

- Patrón transferible: buscar → mapear → comparar → verificar (5 min).
- Demo D2: mapa tabular de literatura con una sola plataforma (3 min) y
  debrief (4 min).
- Presentación del paquete D3 de tres afirmaciones con citas (3 min). Una cita
  o interpretación está deliberadamente equivocada.
- Ejercicio en parejas usando abstracts/PDFs proporcionados (18 min).
- Debrief: qué cuenta como verificación y qué no (8 min).
- Reproducibilidad: guardar consulta, prompt, versión, fecha y fuentes (4 min).

La afirmación problemática debe estar curada de antemano; no conviene pedir al
modelo en vivo que fabrique errores hasta obtener uno.

### 3. El colaborador adversarial — 35 min

- Patrón: hipótesis rivales → amenazas → pruebas de robustez → referee (5 min).
- Demo D4: crítica del mecanismo y la estrategia del caso (3 min) + debrief
  sobre objeciones reales frente a texto genérico (5 min).
- Ejercicio: aplicar el prompt-referee al proyecto propio o al caso conductor
  (15 min).
- Escribir el hallazgo como una oración de limitaciones o plan de robustez y
  compartir dos ejemplos (5 min).
- Transición hacia evidencia computacional (2 min).

### 4. Código y análisis en Python — 60 min

- Marco: entender, generar, depurar, probar y documentar; nunca pegar a ciegas
  (5 min).
- Demo D5: explicar un script Python desconocido y señalar una operación riesgosa
  (3 min) + debrief (3 min).
- Demo D6: diagnosticar una caída inesperada de observaciones, corregirla,
  agregar una aserción y ejecutar la prueba (4 min) + debrief (4 min).
- Ejercicio por niveles (27 min):
  - **A:** cualquier chat y un notebook de Python ya preparado; explicar el
    script, proponer la corrección y diseñar el sanity check con resultados
    esperados proporcionados.
  - **B:** Claude Code o Codex en un mini-repo; ejecutar prueba que falla,
    corregir y ejecutar prueba que pasa.
- Debrief: “corre” no equivale a “es correcto” (8 min).
- Transferencia: mostrar durante 4 minutos cómo el mismo patrón se expresa en
  Stata o R, sin abrir rutas paralelas de enseñanza.
- Transición (2 min).

### 5. Construcción de un agente auditor de evidencia — 30 min

El agente recibe una afirmación sobre Juntos y asistencia escolar, consulta el
mismo corpus curado que los participantes ya verificaron manualmente y devuelve
un veredicto estructurado: respaldada, contradicha, parcialmente respaldada o
evidencia insuficiente. Debe incluir fuente, página, fragmento, incertidumbre y
próximo paso.

- Diferencia observable entre prompt, workflow y agente (3 min).
- Construcción D7 en Python: instrucciones, estado y dos herramientas,
  `buscar_corpus()` y `abrir_fuente()` (7 min).
- Ejecución de dos afirmaciones: una respaldada y otra que exagera una
  conclusión causal (6 min).
- Inspección de la traza: consultas, resultados descartados, reformulación y
  errores (5 min).
- Límites y revisión humana: máximo seis llamadas, máximo dos reformulaciones,
  nunca inventar referencias y aprobación antes de usar la afirmación (3 min).
- Video D8: fragmento del sistema multiagente de Kristian con desacuerdo real
  y arbitraje (4 min).
- Debrief: verificación manual → agente individual → orquestación avanzada
  (2 min).

La lógica científica y las herramientas se mantienen como funciones Python
independientes de la plataforma. La demostración live utiliza un solo SDK; no
se enseñan dos implementaciones paralelas. Quien no tenga acceso API puede
seguir el código y analizar la traza de respaldo sin recibir una clave
compartida.

**Regla explícita:** dos modelos que coinciden no han verificado un hecho. Las
afirmaciones empíricas y las citas todavía se comprueban contra fuentes
primarias o datos autoritativos.

### 6. Síntesis, escritura y transparencia — 20 min

- Recorrer la hoja de trabajo completa (7 min).
- Ejemplo breve de documentación/divulgación de uso de IA, sujeto a políticas
  del venue (4 min).
- Cada participante completa: “mañana usaré ___ para ___ y comprobaré el
  resultado mediante ___” (5 min).
- Dos ejemplos y cierre (4 min).

### 7. Preguntas y cierre — 10 min

Este bloque sirve también como buffer. No se debe sacrificar el ejercicio de
compromiso para ampliar preguntas.

## Arquitectura mínima de demos

| Demo | Función | Formato | Duración máxima | Respaldo preparado |
|---|---|---|---:|---|
| D1 | Descomponer la pregunta en plan | Claude o ChatGPT estándar, live | 3 min | Capturas de una ejecución ensayada |
| D2 | Crear mapa de literatura | Una plataforma con web/citas, live | 3 min | Tabla exportada |
| D3 | Verificar afirmaciones y citas | Paquete curado, no generación live | 3 min de introducción | El propio paquete garantiza el ejercicio |
| D4 | Referee adversarial | Plataforma generalista distinta de D1, live | 3 min | Transcripción guardada |
| D5 | Explicar código Python | Claude Code o Codex, live | 3 min | Video corto |
| D6 | Encontrar bug Python y agregar prueba | Claude Code o Codex, live | 4 min | Video + versión inicial/final del repo |
| D7 | Construir y ejecutar un agente auditor de evidencia | Python, un solo SDK, live | 13 min entre construcción y ejecución | Mini-repo, traza esperada y video corto |
| D8 | Flujo multiagente con desacuerdo y arbitraje | Video pregrabado | 4 min | Es el formato principal, no un fallback |

Cada demo live debe tener un cronómetro, una salida esperada y una slide de
respaldo ya insertada. Si excede su tiempo, se corta y se pasa al respaldo.

## Preparación previa y materiales

### Una semana antes

- Encuesta de cinco minutos: disciplina, lenguaje de programación, nivel,
  cuentas disponibles, laptop y proyecto propio.
- Correo de preparación con acceso mínimo a un asistente y opciones A/B.
- Caso de una página y PDFs de verificación.
- Notebook Python listo para abrir y mini-repo opcional para quienes usarán
  Claude Code o Codex; Colab sirve como fallback sin instalación.

### Paquete de clase

- Slides centradas en decisiones y patrones.
- Hoja de trabajo/cheat sheet del flujo completo.
- Paquete de citas y fuentes para verificación.
- Script Python con bug, CSV pequeño, datos públicos y resultados esperados.
- Mini-repo del agente auditor con corpus curado, dos herramientas, afirmaciones
  de prueba, límites, tests y una traza esperada.
- Capturas/transcripciones de todas las demos live.
- Video multiagente de cuatro minutos.
- Audio explainers como repaso posterior, no sustituto del trabajo práctico.

## Versión exacta de 180 minutos

| Tiempo | Min. | Bloque |
|---|---:|---|
| 0:00–0:10 | 10 | Apertura y reglas |
| 0:10–0:25 | 15 | Flujo y demo D1 |
| 0:25–0:55 | 30 | Literatura y verificación |
| 0:55–1:20 | 25 | Colaborador adversarial |
| 1:20–1:25 | 5 | Descanso |
| 1:25–2:10 | 45 | Código y análisis |
| 2:10–2:25 | 15 | Agente auditor y video multiagente |
| 2:25–2:45 | 20 | Síntesis y compromiso |
| 2:45–3:00 | 15 | Preguntas/buffer |
| **Total** | **180** |  |

Se eliminan primero la escalera de madurez, comparaciones entre lenguajes y
exposición teórica. Se conservan los ejercicios de verificación, crítica y
código. El agente auditor se presenta desde un mini-repo ya preparado: se
ejecuta una afirmación y se inspecciona la traza, sin programarlo completo en
vivo.

## Módulo breve adicional: Lean como verificador matemático — 20 min

Este módulo vive en un slideshow de Quarto separado para poder dictarse o
reutilizarse de manera autónoma. Pertenece a razonamiento y crítica: por una
vez, la máquina revisa un paso escrito por la persona. No sustituye la
validación empírica ni metodológica.

| Min. | Lámina / acción | Resultado |
|---:|---|---|
| 2.5 | Del salto verbal al contrato | Entender por qué “suena bien” no equivale a “se sigue” y separar supuestos de conclusión. |
| 2 | Lean, núcleo y Mathlib | Distinguir lenguaje, verificador y biblioteca matemática. |
| 2.5 | Primer teorema verde | Leer objetos, supuesto, conclusión y táctica en `PrimerPaso.lean`. |
| 3 | Persona, agente, Mathlib y Lean | Separar responsabilidades y elegir Lean Web, VS Code o repositorio. |
| 2 | Incidencia como contrato | Formular el caso antes de mostrar código. |
| 3 | Rechazo y contraejemplo | Distinguir prueba fallida de refutación verificada. |
| 1.5 | Reparar cambia el enunciado | Ver que el supuesto común, no la elocuencia, hace el trabajo. |
| 1.5 | Mezcla entre extremos | Entender por qué un peso debe permanecer en $[0,1]$. |
| 1.5 | Valor esperado en *Disentangling* | Conectar el puente didáctico con el lema real `expected_mix`. |
| 0.5 | Límites y transferencia | Formular una afirmación propia como contrato revisable. |

El slideshow independiente vive en
`course/slides/lean-verificacion-matematica.qmd`. El primer archivo es
`course/exercises/lean_verification_demo/PrimerPaso.lean`; después se ejecutan
`IncidenciaRojo.lean`, `Incidencia.lean`, `MezclaEntreExtremos.lean` y
`PuenteDisentangling.lean`. Deben estar precargados; no se descargan
dependencias en la sala. El paquete contiene además una práctica de
inyectividad.

La frase de cierre del módulo es: **Lean verifica el paso, no el mundo.** Quedan
fuera cuatro juicios: que los supuestos sean ciertos, que la traducción formal
diga lo que quisimos decir, que los datos respalden el modelo y que la pregunta
valga la pena.

## Decisiones ya resueltas

Las preguntas sobre público, duración, equipos, lenguaje de código y caso
conductor ya fueron respondidas e incorporadas. Quedan dos decisiones de
producción antes de cerrar los materiales: elegir la plataforma live del bloque
de literatura según licencias y acceso real, y confirmar el SDK único de D7.
OpenAI Agents SDK es el candidato provisional por su traza incorporada; la
lógica del agente y sus dos herramientas deben permanecer independientes para
no atar el ejercicio a un proveedor.

## Orden de validación recomendado

El público, el caso y Python ya están congelados. El siguiente orden recomendado
es: hoja de trabajo → ejercicios y fallbacks → decisión de plataforma de
literatura → mini-repo y traza D7 → video D8 → slides → audio explainers
complementarios.
