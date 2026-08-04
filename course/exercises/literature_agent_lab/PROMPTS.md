# Cinco encargos

Funcionan igual en Codex y en Claude Code sobre esta carpeta. En un proyecto de
ChatGPT o Claude, suba la carpeta y pegue `AGENTS.md` como instrucciones antes
del primer encargo.

Cada encargo pide **un artefacto acotado**. Ninguno pide «hazme una revisión».

---

## 1 · Comprender sin editar

```text
Lee AGENTS.md, case/question.md, case/protocol.md y case/source_packet.md.

No edites nada todavía.

Devuelve:
- qué decide esta carpeta y qué no
- qué archivos puedes escribir y cuáles no
- qué te impide marcar una fila como verificada
- una sola acción siguiente propuesta
```

---

## 2 · Inventariar y cribar, sin decidir

```text
Aplica case/protocol.md a los doce registros de case/candidates.csv.

Para cada uno, escribe una fila en work/screening_pending.csv con
ai_proposal y ai_reason. Usa solo los metadatos disponibles.
Si el título no basta, propón uncertain.

No escribas en human/ ni en official/.
Actualiza STATE.json y TRACE.csv, y ejecuta el validador.
```

---

## 3 · Extraer con anclaje exacto

```text
Para cada fuente de case/source_packet.md cuyo registro quedó en include,
abre una fila en work/evidence_pending.csv.

Copia verbatim_excerpt y locator EXACTOS de la ficha.
Transcribe study_design, population y outcome tal como los declara.
Escribe ai_interpretation con el verbo que el diseño permite.

Si el pasaje no sostiene la afirmación, escribe NO ENCONTRADO.
Ejecuta el validador y muéstrame qué bloquea.
```

---

## 4 · Detenerse en la compuerta

```text
Ejecuta python3 scripts/validate_review.py.

Para cada error, dime:
- qué fila lo produce
- qué dice la ficha congelada
- qué tendría que cambiar para que pase
- si el cambio te corresponde a ti o a mí

No ejecutes scripts/review_gate.py. No edites human/ ni official/.
```

---

## 5 · Reanudar sin el chat anterior

```text
Lee STATE.json, las últimas filas de TRACE.csv, work/ y human/.

Resume: último ítem completo, qué decisiones humanas ya existen,
qué filas siguen abiertas y cuál es la próxima acción permitida.

No edites. Espera confirmación.
```

---

## Los dos comandos que solo ejecuta una persona

```bash
python3 scripts/review_gate.py --kind screening --id T1 \
  --decision include --reason "Adultos, mensaje LLM, resultado posterior" --by "Su nombre"

python3 scripts/review_gate.py --kind evidence --id EV-T3 \
  --decision rejected --correction "Diseño observacional: no admite verbo causal" --by "Su nombre"
```

Ambos exigen terminal interactiva y que retecleé el identificador. Esa
fricción es deliberada: hace que aprobar sea un acto, no un descuido.

## El comando que cierra el trabajo

```bash
python3 scripts/assemble_brief.py
```

Se niega a correr mientras quede una fila abierta o un validador en rojo.
