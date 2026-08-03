"""Agente mínimo y validación independiente del modelo."""

from agents import Agent, ModelSettings, RunConfig, ToolExecutionConfig, function_tool

from .models import AuditDraft, AuditResult, CanonicalCitation, RunSummary
from .session import MAX_OPERATIONS, MAX_SEARCHES, AuditSession

DEFAULT_MODEL = "gpt-5.6-terra"
MAX_TURNS = 7
RUN_CONFIG = RunConfig(
    trace_include_sensitive_data=False,
    workflow_name="evidence-auditor",
    tool_execution=ToolExecutionConfig(max_function_tool_concurrency=1),
)


def build_agent(session: AuditSession, model: str = DEFAULT_MODEL) -> Agent:
    @function_tool(
        is_enabled=lambda _ctx, _agent: (
            session.operations < MAX_OPERATIONS and session.searches < MAX_SEARCHES
        )
    )
    def buscar_corpus(consulta: str) -> str:
        """Busca paráfrasis locales y devuelve IDs; no abre fuentes."""
        result = session.search(consulta)
        return (
            result if isinstance(result, str) else "\n".join(f"{p.id}: {p.summary}" for p in result)
        )

    @function_tool(
        is_enabled=lambda _ctx, _agent: (
            bool(session.found_ids) and session.operations < MAX_OPERATIONS
        )
    )
    def abrir_fuente(passage_id: str) -> str:
        """Abre únicamente un ID devuelto por buscar_corpus."""
        result = session.open(passage_id)
        if isinstance(result, str):
            return result
        source = session.corpus.source_for(result.id)
        return result.model_dump_json(
            include={
                "id",
                "summary",
                "locator",
                "study_design",
                "causal_strength",
                "content_kind",
            }
        ) + (f'\nPaís: {source.country}' if source else "")

    return Agent(
        name="Auditor de evidencia",
        model=model,
        instructions="""Audita solo con el corpus local. Tú decides qué buscar, qué resultado abrir,
si reformular y cuándo detenerte. Busca antes de abrir y no confundas Perú con Panamá. Usa solo IDs
abiertos en evidence_refs. Un veredicto supported necesita evidencia supports; contradicted necesita
contradicts; partially_supported necesita supports y además context o contradicts. Si no basta,
devuelve insufficient. Describe incertidumbre, limitaciones y el siguiente paso. La aplicación,
no tú, determina si el reclamo requiere evidencia causal.""",
        tools=[buscar_corpus, abrir_fuente],
        output_type=AuditDraft,
        model_settings=ModelSettings(parallel_tool_calls=False),
    )


def validate_draft(
    claim: str, draft: AuditDraft, session: AuditSession, *, causal: bool, mode: str = "live"
) -> AuditResult:
    ids = [ref.passage_id for ref in draft.evidence_refs]
    errors: list[str] = []
    unopened = sorted(set(ids) - session.opened_ids)
    if unopened:
        errors.append(f"IDs no abiertos: {', '.join(unopened)}")
    relations = {ref.relation for ref in draft.evidence_refs}
    if draft.verdict == "supported" and "supports" not in relations:
        errors.append("Veredicto supported sin una referencia supports.")
    if draft.verdict == "contradicted" and "contradicts" not in relations:
        errors.append("Veredicto contradicted sin una referencia contradicts.")
    if draft.verdict == "partially_supported" and not {
        "supports",
        "context",
    }.issubset(relations) and not {"supports", "contradicts"}.issubset(relations):
        errors.append(
            "Veredicto partially_supported sin supports y una referencia context/contradicts."
        )
    if causal and draft.verdict in {"supported", "partially_supported"}:
        strengths = [
            session.corpus.open(ref.passage_id).causal_strength
            for ref in draft.evidence_refs
            if ref.relation == "supports"
            and ref.passage_id in session.opened_ids
            and session.corpus.open(ref.passage_id)
        ]
        if "causal" not in strengths:
            errors.append(
                "Alarma causal: la aplicación exige evidencia con fuerza causal, no solo descriptiva o sugestiva."
            )
    citations = []
    for passage_id in dict.fromkeys(ids):
        if passage_id not in session.opened_ids:
            continue
        passage, source = session.corpus.open(passage_id), session.corpus.source_for(passage_id)
        if passage and source:
            citations.append(
                CanonicalCitation(
                    passage_id=passage.id,
                    source=source.authors,
                    title=source.title,
                    url=source.url,
                    locator=passage.locator,
                    summary=passage.summary,
                )
            )
    if errors:
        draft = draft.model_copy(update={"verdict": "insufficient"})
    return AuditResult(
        mode=mode,
        claim=claim,
        draft=draft,
        citations=citations,
        validation_errors=errors,
        run_summary=RunSummary(
            operations=session.operations,
            searches=session.searches,
            opened_passages=sorted(session.opened_ids),
        ),
    )
