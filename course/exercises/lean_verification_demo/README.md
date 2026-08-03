# Demo breve: Lean como verificador matemático

Este material acompaña un módulo de 20 minutos para personas sin experiencia
previa. **Lean** es un lenguaje de programación y un verificador de teoremas:
permite escribir una afirmación con precisión y su pequeño núcleo comprueba si
el objeto presentado cuenta como prueba. **Mathlib** es la biblioteca
comunitaria de matemáticas formalizadas para Lean; aporta, entre otras cosas,
números reales, sumas finitas, probabilidad y tácticas de prueba.

Para una primera prueba, abra [Lean Web con
Mathlib](https://live.lean-lang.org/?from=mathlib) y pegue `PrimerPaso.lean`.
La meta no es dominar el lenguaje: es aprender a leer un contrato formal y
observar después cómo otra afirmación se rechaza, se refuta con un
contraejemplo y se repara haciendo explícito un supuesto.

## Cinco palabras antes de empezar

- **Teorema:** un contrato: si se cumplen los supuestos, debe seguir la
  conclusión.
- **Prueba:** una cadena de pasos que satisface ese contrato.
- **Núcleo:** la parte pequeña de Lean que comprueba la prueba final.
- **Táctica:** un procedimiento que intenta construir una prueba; por ejemplo,
  `linarith` para aritmética lineal.
- **Formalizar:** traducir una afirmación a objetos, supuestos y conclusión sin
  depender de lo que “se entiende” por contexto.

## Ruta de 20 minutos

| Minutos | Acción |
|---:|---|
| 0–2:30 | Entender por qué “suena bien” no equivale a “se sigue”, y leer un teorema como contrato. |
| 2:30–4:30 | Distinguir Lean, su núcleo y Mathlib. |
| 4:30–7:00 | Leer y ejecutar `PrimerPaso.lean`; separar táctica de verificación. |
| 7:00–10:00 | Repartir responsabilidades entre persona, agente, Mathlib y Lean; elegir una forma de ejecución. |
| 10:00–12:00 | Formular el caso de incidencia como objetos, supuestos y conclusión. |
| 12:00–15:00 | Leer el rechazo y comprobar el contraejemplo 2/100 frente a 1/10. |
| 15:00–16:30 | Comprobar el teorema reparado y nombrar el supuesto añadido. |
| 16:30–18:00 | Verificar que un promedio ponderado queda entre sus extremos. |
| 18:00–19:30 | Conectar el ejemplo con `expected_mix` de *Disentangling*. |
| 19:30–20:00 | Delimitar qué no verificó Lean y formular un paso propio. |

El archivo debe estar pegado y procesado antes de empezar la clase. La primera
carga de Mathlib puede tomar decenas de segundos. No descargue dependencias en
vivo.

## Guion exacto del demo

1. **Empiece con un caso verde.** Ejecute `PrimerPaso.lean`, lea el teorema en
   castellano y distinga la táctica `linarith` del núcleo que comprueba la
   prueba producida.
2. **Ubique las piezas.** Lean verifica; Mathlib aporta resultados reutilizables;
   el agente edita y ejecuta; la persona elige y audita el enunciado.
3. **La sala se compromete.** Pregunte si la conclusión se sigue antes de abrir
   el editor.
4. **Lean rechaza el paso.** Ejecute `IncidenciaRojo.lean`, o quite los
   delimitadores de comentario `/-` y `-/` del primer teorema de
   `Incidencia.lean`. Una desigualdad entre conteos no tiene el tipo de una
   desigualdad entre tasas.
5. **Lean acepta la refutación.** Vuelva a comentar el primer bloque. El teorema
   `incidencia_mayor_es_falsa` certifica el contraejemplo 2/100 frente a 1/10.
6. **La reparación cambia el enunciado.** `incidencia_comparable` usa el mismo
   denominador. El resultado no fue una prueba más ingeniosa: fue hacer visible
   un supuesto de comparabilidad.
7. **Construya el puente.** `MezclaEntreExtremos.lean` muestra por qué un peso
   debe estar entre cero y uno. `PuenteDisentangling.lean` verifica después que
   el valor esperado de una mezcla es la mezcla de los valores esperados.
8. **La IA queda subordinada al verificador.** Puede pedir a un agente que
   redacte y corrija código; no acepte el resultado hasta que Lean lo compruebe
   y usted pueda explicar el enunciado.

Frase recomendada para narrar el flujo:

> Yo escribí la afirmación en castellano; un modelo ayudó a traducirla a Lean;
> Lean la rechazó. Todavía me corresponde comprobar que la traducción expresa lo
> que quise decir y que los supuestos describen el mundo.

## Qué puede hacer el participante después

### Elegir una forma de trabajo

- **Lean Web:** útil para pegar un ejemplo corto sin instalar nada.
- **VS Code + Lean 4:** muestra metas y errores mientras se escribe; es la ruta
  recomendada para aprender y explorar.
- **Repositorio con Lake:** fija las versiones de Lean y Mathlib y permite
  repetir todas las comprobaciones con `./verificar.sh`.

### Trabajar con Codex o Claude Code

Un agente de código reduce dos costos iniciales: recordar la sintaxis y buscar
los nombres de resultados existentes en Mathlib. Como puede editar archivos,
ejecutar comandos y leer errores, puede repetir el ciclo
**formalizar → ejecutar Lean → corregir**. Lean, no el agente, conserva la
decisión de aceptación; la persona conserva la responsabilidad de revisar la
traducción y los supuestos.

Prompt reproducible para usar dentro de esta carpeta:

> Trabaja en este repositorio. Lee este README y los ejemplos antes de editar.
> Traduce mi afirmación a Lean 4 con Mathlib, separando objetos, supuestos y
> conclusión. No uses `sorry`, `axiom` ni añadas supuestos sin señalarlos.
> Ejecuta `./verificar.sh` después de cada cambio. Al terminar, explica en
> castellano qué verificó Lean, qué cambió respecto de mi frase y qué quedó
> fuera de la formalización.

### Formular una afirmación propia

Antes de pedir código para una afirmación propia, complete esta ficha:

1. **Objetos:** ¿cuáles son los números, funciones o relaciones?
2. **Supuestos:** ¿qué debe suponerse explícitamente?
3. **Conclusión:** ¿qué debe seguir exactamente, sin fortalecerla en prosa?
4. **Prueba adversarial:** ¿qué supuesto quitaría primero para buscar un
   contraejemplo?
5. **Límite externo:** ¿qué parte depende de evidencia, medición o interpretación
   y por tanto no queda validada por Lean?

Prompt corto para una exploración inicial:

> Traduce esta afirmación a Lean 4 con Mathlib. Separa objetos, supuestos y
> conclusión. No añadas axiomas ni cambies la afirmación. Propón una prueba y un
> contraejemplo para la versión sin el supuesto más fuerte. Luego explica en
> castellano qué verificó Lean y qué quedó fuera.

`ExtensionInyectividad.lean` ofrece una segunda práctica sin Mathlib: si `g ∘ f`
es inyectiva, entonces `f` lo es. Cambiar la conclusión a que `g` es inyectiva
produce una afirmación falsa; el archivo incluye un contraejemplo pequeño.

`MezclaEntreExtremos.lean` es la práctica recomendada después del demo: quite
primero `ha1 : a ≤ 1`, pida al agente un contraejemplo y compruebe que un peso
fuera del intervalo convierte la mezcla en extrapolación.

## Segundo ejemplo: puente al proyecto Disentangling

`PuenteDisentangling.lean` aísla el núcleo algebraico de un lema de la
formalización real: el valor esperado de una mezcla de loterías es la mezcla de
sus valores esperados. La versión del proyecto representa loterías en un simplex
finito y explicita las condiciones que hacen válida la mezcla; aquí se conserva
una versión legible para el primer contacto.

El contraste es importante: Lean comprueba la identidad algebraica, pero `p` y
`q` solo representan probabilidades si también codificamos no negatividad y suma
uno. Lo que no se formaliza no se verifica.

## Opción local

La instalación recomendada usa VS Code y la extensión oficial de Lean 4:
<https://lean-lang.org/install/>. Desde esta carpeta:

```bash
lake exe cache get
./verificar.sh
```

La primera preparación descarga Lean y Mathlib; hágala antes de la clase. El
editor web procesa código en un servidor, por lo que no se debe usar para teoría
inédita, datos ni texto confidencial.

`IncidenciaRojo.lean` existe solo para la prueba automática: debe fallar con el
mismo error de tipo que se produce al descomentar el primer bloque del demo.

## Fuentes y siguientes pasos

- [Lean Language Reference](https://lean-lang.org/doc/reference/latest/): qué
  es Lean y cómo funciona su núcleo verificador.
- [Documentación de Mathlib 4](https://leanprover-community.github.io/mathlib4_docs/Mathlib):
  definiciones, teoremas y tácticas disponibles.
- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
  y [Mathematics in Lean](https://leanprover-community.github.io/mathematics_in_lean/):
  rutas de aprendizaje interactivas.
- [Buenas prácticas de Codex](https://learn.chatgpt.com/guides/best-practices.md)
  y [CLI de Claude Code](https://docs.anthropic.com/en/docs/claude-code/cli-usage):
  contexto de repositorio, edición, ejecución y validación.
