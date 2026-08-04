# Laboratorio: literatura y agentes, una sola cadena

Este laboratorio acompaña la sesión **Revisión de literatura con agentes**
(75 minutos). Un solo caso recorre todo el módulo: **persuasión mediada por
modelos de lenguaje**.

El producto no es una respuesta. Es una cadena de evidencia que otra persona
puede revisar sin haber estado en la sesión.

> **AVISO SOBRE LAS FUENTES.** Los ocho registros `r1`–`r8` de
> `case/candidates.csv` son **reales** y verificables por DOI: sobre ellos se
> practica el cribado con metadatos. Las cuatro fuentes `T1`–`T4` de
> `case/source_packet.md` son **sintéticas**, escritas para este ejercicio:
> sobre ellas se practica la extracción con pasaje y localizador. **Ninguna
> cita de `T1`–`T4` pertenece a ninguno de los ocho registros reales ni a
> ningún artículo publicado.** Las dos capas nunca se mezclan.

## Requisitos

Python 3.9 o superior. Nada más: solo biblioteca estándar, sin red y sin
instalar dependencias.

## Paso previo: de la estrategia a los candidatos

La carpeta [`discovery/`](discovery/README.md) enseña el eslabón anterior al
cribado: escribir una estrategia, consultar OpenAlex, conservar la respuesta,
normalizar metadatos y documentar duplicados. Funciona igual desde Codex
Desktop o desde la terminal integrada de VS Code.

```bash
cd discovery
python3 scripts/test_discovery.py
python3 scripts/search_openalex.py --offline  # reproducible, sin red
python3 scripts/search_openalex.py            # intenta OpenAlex; fallback visible
```

Ese paso produce candidatos, no decisiones. Nunca modifica `case/`, y
`case/candidates.csv` permanece congelado para que el demo central siga siendo
idéntico y comprobable en todas las aulas.

## La carpeta separa cinco cosas

```text
literature_agent_lab/
├── case/          fuentes congeladas · solo lectura, con hash
├── work/          lo que el agente propone
├── human/         lo que una persona decidió · escrito solo por el gate
├── official/      el ledger · llega solo desde una decisión humana
└── output/        el brief · se genera, no se escribe
```

Esa separación es el punto pedagógico completo. Un chat mezcla las cinco cosas
en un solo hilo de texto; aquí cada una tiene su archivo, su dueño y su regla
de escritura.

## Qué hay dentro

| Ruta | Qué es |
| --- | --- |
| `AGENTS.md` · `CLAUDE.md` | contrato del agente: objetivo, autoridad, presupuesto, terminado |
| `.agents/skills/literature-evidence/SKILL.md` | el método reutilizable, separado del caso |
| `PROMPTS.md` | los cinco encargos y los comandos que solo ejecuta una persona |
| `case/question.md` · `case/protocol.md` | pregunta y criterios, congelados con hash |
| `case/candidates.csv` | doce registros a cribar |
| `case/source_packet.md` | cuatro fuentes con diseño, población, resultado, localizador y pasaje |
| `case/search_log.csv` | plataforma, consulta y fecha |
| `case/FREEZE.lock` | hashes de la pregunta, el protocolo y el paquete |
| `work/*.csv` | propuestas del agente |
| `human/*.csv` · `human/decisions.lock` | decisiones humanas y su tripwire |
| `official/evidence_ledger.csv` | evidencia oficial |
| `output/` | vacío hasta que el ensamblador escriba el brief |
| `STATE.json` · `TRACE.csv` | estado y traza para poder interrumpir y reanudar |
| `fixtures/` | cuatro estados de arranque para clase o pruebas |
| `scripts/` | validador, compuerta humana, ensamblador, tests y relock |

## Cómo se usa

```bash
cd course/exercises/literature_agent_lab

python3 scripts/validate_review.py   # en una copia recién clonada: BLOQUEADO, y dice por qué
python3 scripts/test_lab.py          # 33 comprobaciones, sin red y sin modelo
```

Después abra la carpeta con Codex o Claude Code y siga `PROMPTS.md`. Quien
prefiera chat puede subir la carpeta a un proyecto de ChatGPT o Claude y pegar
`AGENTS.md` como instrucciones: los archivos y las barreras son los mismos.

## Los cuatro estados de arranque

`fixtures/` permite empezar la clase en el punto que convenga sin esperar a que
el agente trabaje en vivo:

| Fixture | Para qué sirve |
| --- | --- |
| `unstarted` | igual al estado que se distribuye; el validador enumera lo que falta |
| `waiting_gate` | cribado terminado y tres filas de evidencia esperando decisión — **es el punto de arranque de la demo** |
| `rejected` | después de rechazar una fila; el validador muestra el hueco que dejó |
| `ready` | todo verificado; sirve para demostrar el ensamblaje en un minuto |

Para usar uno, copie sus archivos sobre la raíz:

```bash
cp -R fixtures/waiting_gate/. .
python3 scripts/validate_review.py
```

## Qué comprueba el validador

Nada de esto llama a un modelo, y nada de esto entiende de metodología:

1. La pregunta, el protocolo y el paquete siguen siendo los que se congelaron.
2. `human/` no cambió fuera de la compuerta.
3. Cada registro aparece exactamente una vez; ningún identificador inventado.
4. Cada decisión de cribado tiene un estado del protocolo y una razón escrita.
5. Cada pasaje y cada localizador coinciden **carácter por carácter** con la ficha.
6. Ningún pasaje supera veinticinco palabras.
7. Diseño, población y resultado son los que la ficha declara.
8. Ningún verbo causal aparece junto a un diseño que no lo admite.
9. Ninguna fila llega al ledger sin verificación humana.
10. Ninguna fuente excluida, incierta o marcada llega al ledger.
11. El brief no existe antes de tiempo y coincide exactamente con el ledger.

### Lo que el validador NO hace

- **No entiende causalidad.** La comprobación 8 es léxica: busca verbos en una
  lista y mira qué diseño declara la ficha. Una frase causal escrita con
  cuidado puede pasar. Por eso la compuerta humana no es opcional.
- **No es seguridad.** Los hashes de `FREEZE.lock` y `decisions.lock` son
  tripwires pedagógicos: hacen visible una edición silenciosa. Quien pueda
  editar los archivos también puede recalcularlos con `scripts/relock.py`.
- **No juzga si la pregunta vale la pena.** Eso nunca fue delegable.

## Los dos errores que vienen sembrados

`fixtures/waiting_gate` incluye a propósito dos fallas distintas:

- **`EV-T3`** interpreta un estudio observacional con un verbo causal. La
  detecta el validador. Es la fila de la microauditoría de cinco minutos.
- **`EV-T4`** apunta a un localizador equivocado *y* convierte una intención
  declarada en conducta. El localizador lo detecta el validador; el salto de
  intención a conducta **solo lo detecta una persona**.

Ese contraste es el argumento del módulo: los validadores atrapan lo mecánico y
liberan atención humana para lo que no lo es.

## Relación con el resto del taller

Este laboratorio es autocontenido. No reemplaza
`course/exercises/literature_review/` (flujo manual y en chat) ni
`course/exercises/research_agent_lab/` (respuesta a referees): usa el mismo
vocabulario y las mismas barreras sobre un caso distinto.
