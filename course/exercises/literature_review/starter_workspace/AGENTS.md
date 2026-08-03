# Reglas del workspace de literatura

## Objetivo

Ayudar a construir una mini-revisión trazable sin sustituir decisiones
metodológicas ni verificación humana.

## Reglas obligatorias

- Lea `question.md` y `protocol.md` antes de proponer cambios.
- No cambie la pregunta, los criterios o la regla de parada sin autorización
  explícita.
- No invente títulos, autores, DOI, citas, páginas, tamaños muestrales ni
  resultados.
- Si falta evidencia, escriba `NO ENCONTRADO`.
- Separe siempre `ai_proposal` de `human_decision`.
- Nunca cambie `human_checked` o `human_verified` a `yes`; solo una persona
  puede hacerlo después de abrir la fuente.
- Para cribado use únicamente los campos disponibles en `candidates.csv` y
  explique el criterio aplicado.
- Para extracción use únicamente archivos presentes en `papers/` o pasajes
  suministrados explícitamente. Incluya localizador verificable.
- No redacte una síntesis final con filas cuyo `human_verified` no sea `yes`.
- No use búsquedas externas salvo autorización explícita. Si se autoriza una,
  registre plataforma, consulta, filtros, fecha y número de resultados en
  `search_log.csv`.
- Antes de terminar, ejecute `python3 validate_workspace.py` y reporte el
  resultado.

## Forma de trabajar

1. Diagnostique antes de editar.
2. Proponga el cambio y nombre los archivos afectados.
3. Haga cambios pequeños y revisables.
4. Muestre qué proviene de una fuente y qué es interpretación.
5. Deténgase si una decisión requiere juicio del equipo.
