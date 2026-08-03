# Auditor de evidencia: Juntos y ENAHO

Mini-repo para una demostración de 30 minutos. El agente solo busca y abre
paráfrasis locales; el validador de la aplicación reconstruye citas canónicas y
deja toda conclusión en `human_review.status: pending`.

## Comandos exactos

Requiere Python 3.11+ y `uv`.

```bash
uv sync
uv run evidence-auditor list
uv run evidence-auditor offline "Juntos Perú asistencia escolar"
uv run evidence-auditor replay
uv run pytest -q
```

`replay` ejecuta dos trazas grabadas, siempre con `mode: recorded_replay`; no
necesita red ni una clave. Cada caso preparado declara fuera del modelo si el
reclamo es causal, de modo que la exageración causal activa la alarma incluso
sin banderas. `offline` solo muestra resultados de búsqueda. El
modo opcional `live` requiere una clave y pasa siempre su borrador Pydantic por
validación e hidratación antes de imprimirlo:

```bash
OPENAI_API_KEY=... uv run evidence-auditor live --causal "Juntos mejoró la asistencia escolar"
```

En modo `live`, `--causal` es una decisión explícita de la aplicación: activa una alarma que
rechaza una conclusión favorable si los pasajes abiertos no tienen fuerza causal.
El modelo no decide esa clasificación.

## Guion (30 min)

1. **0–5:** `list`; comparar los metadatos de Perú con el distractor de Panamá.
2. **5–12:** `offline`; explicar que un ID encontrado aún no es un ID abierto.
3. **12–18:** mostrar los presupuestos: seis operaciones, tres búsquedas; llamadas inválidas también consumen presupuesto.
4. **18–25:** contrastar la ficha ENAHO (descriptiva) con evaluaciones/síntesis prudentes de Juntos.
5. **25–30:** `replay`; observar dos trayectorias distintas e inspeccionar `run_summary`, citas canónicas y revisión humana pendiente.

## Fuentes estables del corpus

Todas las entradas del corpus son **paráfrasis pedagógicas**, con localizador y
fecha de verificación (`2026-08-02`). No son citas textuales y no sustituyen la
lectura de las fuentes ni una evaluación de calidad metodológica.

- [Perova y Vakis (2010)](https://repositorio.minedu.gob.pe/handle/20.500.12799/3974)
- [Sánchez y Rodríguez (2016)](https://repositorio.minedu.gob.pe/handle/20.500.12799/4650)
- [INEI, ficha técnica ENAHO, p. 3](https://proyectos.inei.gob.pe/iinei/srienaho/Descarga/FichaTecnica/854-1788-Ficha.pdf)
- [Gibbons y Rossi (2015), Panamá — distractor](https://repositorio.minedu.gob.pe/handle/20.500.12799/4125)

## Diseño y trazabilidad

Hay exactamente dos herramientas SDK (`buscar_corpus`, `abrir_fuente`). Las
herramientas se habilitan dinámicamente, se ejecutan en serie
(`max_function_tool_concurrency=1` y `parallel_tool_calls=False`) y `MAX_TURNS`
vale 7. La configuración del run desactiva datos sensibles en tracing y usa el
workflow `evidence-auditor`.

La referencia de implementación está en la documentación oficial de
[agentes](https://developers.openai.com/api/docs/guides/agents), el
[inicio rápido del Agents SDK](https://developers.openai.com/api/docs/guides/agents/quickstart),
las [herramientas](https://developers.openai.com/api/docs/guides/tools) y la
[observabilidad](https://developers.openai.com/api/docs/guides/agents/integrations-observability).
