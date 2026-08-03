"""Corpus local con paráfrasis docentes, no citas textuales."""

from .models import Passage, Source

_VERIFIED = "2026-08-02"
SOURCES = (
    Source(
        id="perova-vakis-2010",
        title="El impacto y potencial del Programa Juntos en Perú: evidencia de una evaluación no-experimental",
        authors="Elizabeta Perova y Renos Vakis",
        year=2010,
        country="Perú",
        url="https://repositorio.minedu.gob.pe/handle/20.500.12799/3974",
        verified_on=_VERIFIED,
    ),
    Source(
        id="sanchez-rodriguez-2016",
        title="Balance del impacto de JUNTOS, programa de transferencias condicionadas del Perú",
        authors="Alan Sánchez y María Gracia Rodríguez",
        year=2016,
        country="Perú",
        url="https://repositorio.minedu.gob.pe/handle/20.500.12799/4650",
        verified_on=_VERIFIED,
    ),
    Source(
        id="inei-enaho",
        title="Fichas técnicas de los indicadores generados a partir de la ENAHO",
        authors="INEI",
        year=2022,
        country="Perú",
        url="https://proyectos.inei.gob.pe/iinei/srienaho/Descarga/FichaTecnica/854-1788-Ficha.pdf",
        verified_on=_VERIFIED,
    ),
    Source(
        id="gibbons-rossi-2015-panama",
        title="Evaluación de impacto de un programa de inclusión social y prevención de violencia estudiantil",
        authors="Gibbons y Rossi",
        year=2015,
        country="Panamá",
        url="https://repositorio.minedu.gob.pe/handle/20.500.12799/4125",
        verified_on=_VERIFIED,
    ),
)
_URL = {s.id: s.url for s in SOURCES}
PASSAGES = (
    Passage(
        id="pv-01",
        source_id="perova-vakis-2010",
        summary="El resumen reporta resultados cuantitativos tempranos para Juntos y advierte que la evaluación es no experimental.",
        locator="Resumen/abstract, descripción del diseño",
        study_design="evaluación no experimental",
        causal_strength="suggestive",
        verified_on=_VERIFIED,
        source_url=_URL["perova-vakis-2010"],
        keywords=("juntos", "perú", "evaluación"),
    ),
    Passage(
        id="pv-02",
        source_id="perova-vakis-2010",
        summary="El resumen ubica matrícula y asistencia entre los resultados educativos, especialmente en transiciones, sin presentar aquí una estimación numérica.",
        locator="Resumen/abstract, oración sobre matrícula y asistencia",
        study_design="evaluación no experimental",
        causal_strength="suggestive",
        verified_on=_VERIFIED,
        source_url=_URL["perova-vakis-2010"],
        keywords=("juntos", "asistencia", "escolar", "perú"),
    ),
    Passage(
        id="sr-01",
        source_id="sanchez-rodriguez-2016",
        summary="El boletín sintetiza evaluaciones de impacto de Juntos sobre salud, educación y trabajo infantil.",
        locator="Resumen/abstract, objetivos y alcance",
        study_design="síntesis de literatura",
        causal_strength="suggestive",
        verified_on=_VERIFIED,
        source_url=_URL["sanchez-rodriguez-2016"],
        keywords=("juntos", "educación", "perú", "impacto"),
    ),
    Passage(
        id="sr-02",
        source_id="sanchez-rodriguez-2016",
        summary="La síntesis señala que la asistencia por sí sola no equivale a mejora de aprendizajes.",
        locator="Resumen/abstract, sección sobre educación",
        study_design="síntesis de literatura",
        causal_strength="suggestive",
        verified_on=_VERIFIED,
        source_url=_URL["sanchez-rodriguez-2016"],
        keywords=("juntos", "asistencia", "aprendizajes", "perú"),
    ),
    Passage(
        id="enaho-01",
        source_id="inei-enaho",
        summary="La ficha define la tasa neta de inasistencia escolar para población de 3 a 16 años.",
        locator="p. 3 (numeración impresa), indicador 7",
        study_design="ficha técnica de indicador",
        causal_strength="descriptive",
        verified_on=_VERIFIED,
        source_url=_URL["inei-enaho"],
        keywords=("enaho", "asistencia", "escolar", "perú"),
    ),
    Passage(
        id="enaho-02",
        source_id="inei-enaho",
        summary="La ficha advierte que el indicador no mide calidad ni necesariamente asistencia regular a clases.",
        locator="p. 3 (numeración impresa), limitaciones",
        study_design="ficha técnica de indicador",
        causal_strength="descriptive",
        verified_on=_VERIFIED,
        source_url=_URL["inei-enaho"],
        keywords=("enaho", "limitaciones", "asistencia", "perú"),
    ),
    Passage(
        id="enaho-03",
        source_id="inei-enaho",
        summary="El nivel de inferencia indicado incluye total nacional, área urbana y rural y departamentos.",
        locator="p. 3 (numeración impresa), nivel de inferencia",
        study_design="ficha técnica de indicador",
        causal_strength="descriptive",
        verified_on=_VERIFIED,
        source_url=_URL["inei-enaho"],
        keywords=("enaho", "indicador", "perú"),
    ),
    Passage(
        id="gr-01",
        source_id="gibbons-rossi-2015-panama",
        summary="Este registro se conserva como distractor de Panamá: no es evidencia sobre Juntos Perú.",
        locator="Registro del repositorio",
        study_design="no aplicable al reclamo peruano",
        causal_strength="none",
        verified_on=_VERIFIED,
        source_url=_URL["gibbons-rossi-2015-panama"],
        keywords=("juntos", "panamá", "programa"),
    ),
)
_SOURCES = {s.id: s for s in SOURCES}
_PASSAGES = {p.id: p for p in PASSAGES}


class Corpus:
    def search(self, query: str) -> list[Passage]:
        terms = {word.strip(".,;:¿?¡!").lower() for word in query.split() if len(word) > 2}
        peru = "perú" in terms or "peru" in terms
        content_terms = terms - {"perú", "peru", "panamá", "panama"}
        return [
            p
            for p in PASSAGES
            if (not peru or _SOURCES[p.source_id].country == "Perú")
            and (not content_terms or content_terms.intersection(p.keywords))
        ]

    def open(self, passage_id: str) -> Passage | None:
        return _PASSAGES.get(passage_id)

    def source_for(self, passage_id: str) -> Source | None:
        passage = self.open(passage_id)
        return _SOURCES.get(passage.source_id) if passage else None
