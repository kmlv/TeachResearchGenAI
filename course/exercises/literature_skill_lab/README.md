# Laboratorio: una revisión guiada por un skill

Este ejercicio enseña una sola idea: un **skill** puede convertir un método de
trabajo en una conversación guiada. El agente busca, organiza y muestra la
evidencia; la persona decide qué acepta y deja su nombre junto a la decisión.

No es una revisión sistemática ni un sistema para investigación a gran escala.
Usa tres fichas sintéticas y un buscador local reproducible para que toda la
sala vea los mismos resultados.

## Qué harán

1. Abrir esta carpeta en Codex Desktop o en VS Code con Codex o Claude Code.
2. Invocar el skill `revision-guiada`.
3. Dar una pregunta y el nombre de quien tomará las decisiones.
4. Ver una búsqueda breve y escoger una o dos entradas.
5. Leer en el chat el pasaje exacto, el diseño y la tensión de cada entrada.
6. Escribir `APROBAR`, `REESCRIBIR` o `EXCLUIR`, con una razón y un nombre.
7. Dejar que el agente ejecute la comprobación y genere `BRIEF.md`.

La persona no necesita escribir comandos. El agente usa un solo programa,
`scripts/flujo.py`, detrás de la conversación.

## La carpeta completa

```text
literature_skill_lab/
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── FUENTES.md
├── PROGRESO.md
├── BRIEF.md
├── .agents/skills/revision-guiada/SKILL.md
└── scripts/flujo.py
```

`FUENTES.md` contiene el material congelado. `PROGRESO.md` conserva pregunta,
selección y decisiones. `BRIEF.md` se genera desde ese progreso: nunca desde la
memoria del chat.

## Primer mensaje

En Codex, invoque `$revision-guiada`. En Claude Code, escriba:

```text
Usa el skill revision-guiada de esta carpeta. Guíame desde la búsqueda hasta
un brief, una decisión a la vez. No decidas por mí.
```

Después siga las preguntas del agente. Si el agente entrega un brief sin pedir
una decisión firmada por cada entrada seleccionada, deténgalo: no siguió el
skill.

## Qué significa “firma” aquí

La firma es una frase registrada, por ejemplo:

```text
REESCRIBIR S2: describir asociación, no efecto causal — Kristian
```

Hace visible quién tomó la decisión. No es una firma digital ni un control de
seguridad. El ejercicio enseña autoría y trazabilidad, no infraestructura.
