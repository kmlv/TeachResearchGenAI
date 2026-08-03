# Solicitudes listas para copiar

## 0. Diagnosticar sin editar

```text
Lee AGENTS.md, question.md y protocol.md. No edites todavía. Resume el estado
del flujo, enumera los archivos que contienen decisiones humanas pendientes y
propón una sola acción siguiente. Distingue hechos del corpus, decisiones del
protocolo y trabajo todavía no verificado.
```

## 1. Proponer cribado

```text
Lee question.md, protocol.md y candidates.csv. Para las filas con
ai_proposal=pending, propón include, exclude, uncertain o editorial_flag y una
razón breve basada solo en los metadatos disponibles. No cambies
human_decision, human_reason ni human_checked. No inventes información que no
aparece en la tabla. Si el título no basta, usa uncertain. Muéstrame el plan y
espera mi aprobación antes de editar candidates.csv.
```

## 2. Extraer evidencia

```text
Lee protocol.md y los textos autorizados en papers/. Para cada estudio que yo
indique, propón una fila de evidence.csv con diseño, población, intervención,
comparador, resultado, un fragmento exacto de máximo 25 palabras y un
localizador verificable. Si algo falta, escribe NO ENCONTRADO. No cambies
human_correction ni human_verified. Espera mi aprobación antes de editar.
```

## 3. Auditar una fila

```text
Compara esta fila de evidence.csv con la fuente y el localizador indicados.
Separa: (a) texto que sí aparece, (b) interpretación razonable y (c) afirmación
que excede la fuente o el diseño. No declares la fila verificada; devuelve una
lista de comprobaciones para que yo decida.
```

## 4. Sintetizar solo lo verificado

```text
Lee question.md, protocol.md y evidence.csv. Usa únicamente filas con
human_verified=yes. Redacta tres apartados para synthesis.md: qué permite decir
la evidencia, qué no permite afirmar y qué vacíos quedan. Conserva DOI o
record_id junto a cada afirmación. Si ninguna fila está verificada, detente y
explica qué falta. No busques ni agregues fuentes externas.
```

## 5. Cerrar con una auditoría

```text
Ejecuta python3 validate_workspace.py. Después enumera: archivos cambiados,
decisiones todavía pendientes, filas usadas en la síntesis y límites que una
persona debe revisar. No publiques ni envíes nada.
```
