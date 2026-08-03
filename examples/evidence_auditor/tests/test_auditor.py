import pytest

from evidence_auditor.agent import DEFAULT_MODEL, MAX_TURNS, RUN_CONFIG, build_agent, validate_draft
from evidence_auditor.cli import _replay, main
from evidence_auditor.corpus import PASSAGES, SOURCES, Corpus
from evidence_auditor.models import AuditDraft, EvidenceRef
from evidence_auditor.session import AuditSession


def draft(ids, verdict="supported"):
    return AuditDraft(
        verdict=verdict,
        evidence_refs=[EvidenceRef(passage_id=i, relation="supports", use="prueba") for i in ids],
        uncertainty="incertidumbre",
        limitations=["límite"],
        next_step="leer",
    )


def test_four_exact_sources_unique_ids_and_passage_metadata():
    assert [s.url for s in SOURCES] == [
        "https://repositorio.minedu.gob.pe/handle/20.500.12799/3974",
        "https://repositorio.minedu.gob.pe/handle/20.500.12799/4650",
        "https://proyectos.inei.gob.pe/iinei/srienaho/Descarga/FichaTecnica/854-1788-Ficha.pdf",
        "https://repositorio.minedu.gob.pe/handle/20.500.12799/4125",
    ]
    assert len({s.id for s in SOURCES}) == len(SOURCES) == 4
    assert len({p.id for p in PASSAGES}) == len(PASSAGES)
    assert all(
        p.locator
        and p.study_design
        and p.causal_strength
        and p.verified_on
        and p.source_url
        and p.content_kind == "pedagogical_paraphrase"
        for p in PASSAGES
    )


def test_search_excludes_panama_distractor_for_peru():
    results = Corpus().search("Juntos Perú asistencia escolar")
    assert {p.id for p in results} >= {"pv-02", "enaho-01"}
    assert "gr-01" not in {p.id for p in results}


def test_budgets_and_invalid_open_are_counted():
    session = AuditSession()
    assert "Solo se puede" in session.open("pv-02")
    for _ in range(3):
        assert not isinstance(session.search("Juntos Perú"), str)
    assert "3 búsquedas" in session.search("Juntos Perú")
    session = AuditSession()
    session.search("Juntos Perú asistencia")
    for _ in range(5):
        session.open("pv-02")
    assert session.operations == 6
    assert "6 operaciones" in session.open("pv-02")


def test_exact_search_and_operation_boundaries():
    searches = AuditSession()
    for _ in range(3):
        assert not isinstance(searches.search("Juntos Perú"), str)
    assert searches.searches == 3
    assert "3 búsquedas" in searches.search("Juntos Perú")
    operations = AuditSession()
    operations.search("Juntos Perú")
    for _ in range(5):
        assert not isinstance(operations.open("pv-02"), str)
    assert operations.operations == 6
    assert "6 operaciones" in operations.open("pv-02")


def test_open_requires_a_previously_found_id_even_if_it_exists():
    session = AuditSession()
    session.search("ENAHO Perú")
    assert "Solo se puede" in session.open("pv-02")
    assert session.operations == 2


def test_unopened_ids_rejected_and_causality_is_app_controlled():
    session = AuditSession()
    session.search("Juntos Perú asistencia")
    session.open("pv-02")
    bad = validate_draft("x", draft(["pv-02", "enaho-01"]), session, causal=False)
    assert bad.draft.verdict == "insufficient" and "IDs no abiertos" in bad.validation_errors[0]
    causal = validate_draft("x", draft(["pv-02"]), session, causal=True)
    assert "Alarma causal" in causal.validation_errors[0]
    assert causal.citations[0].passage_id == "pv-02"


@pytest.mark.parametrize(
    ("verdict", "relation", "error"),
    [
        ("supported", "context", "supported sin"),
        ("contradicted", "supports", "contradicted sin"),
        ("partially_supported", "supports", "partially_supported sin"),
    ],
)
def test_verdict_relation_invariants(verdict, relation, error):
    session = AuditSession()
    session.search("Juntos Perú asistencia")
    session.open("pv-02")
    candidate = draft(["pv-02"], verdict)
    candidate.evidence_refs[0].relation = relation
    result = validate_draft("x", candidate, session, causal=False)
    assert result.draft.verdict == "insufficient"
    assert any(error in message for message in result.validation_errors)


def test_hydration_and_pending_review():
    session = AuditSession()
    session.search("Juntos Perú asistencia")
    session.open("pv-02")
    result = validate_draft("x", draft(["pv-02"], "partially_supported"), session, causal=False)
    assert result.citations[0].model_dump().keys() == {
        "passage_id",
        "source",
        "title",
        "url",
        "locator",
        "summary",
        "content_kind",
    }
    assert result.citations[0].content_kind == "pedagogical_paraphrase"
    assert result.human_review.status == "pending"


def test_replays_have_labels_budgets_and_pending():
    result = _replay("recorded_replay.json")
    assert result["mode"] == "recorded_replay" and result["human_review"]["status"] == "pending"
    assert result["draft"]["verdict"] == "partially_supported"
    assert result["run_summary"] == {
        "operations": 3,
        "searches": 1,
        "opened_passages": ["pv-02", "sr-02"],
    }
    second = _replay("recorded_replay_insufficient.json")
    assert second["draft"]["verdict"] == "insufficient"
    assert "Alarma causal" in second["validation_errors"][0]
    assert second["citations"][0]["passage_id"] == "enaho-01"
    assert second["run_summary"] == {
        "operations": 2,
        "searches": 1,
        "opened_passages": ["enaho-01"],
    }


def test_sdk_config_and_pydantic_output():
    agent = build_agent(AuditSession())
    assert agent.model == DEFAULT_MODEL and MAX_TURNS == 7 and agent.output_type is AuditDraft
    assert {tool.name for tool in agent.tools} == {"buscar_corpus", "abrir_fuente"}
    assert agent.model_settings.parallel_tool_calls is False
    assert RUN_CONFIG.tool_execution.max_function_tool_concurrency == 1
    assert (
        RUN_CONFIG.trace_include_sensitive_data is False
        and RUN_CONFIG.workflow_name == "evidence-auditor"
    )


def test_cli_replay_offline_and_missing_key(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["evidence-auditor", "replay"])
    main()
    assert '"mode": "recorded_replay"' in capsys.readouterr().out
    monkeypatch.setattr("sys.argv", ["evidence-auditor", "offline", "Juntos Perú asistencia"])
    main()
    assert "pv-02" in capsys.readouterr().out
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("sys.argv", ["evidence-auditor", "live"])
    with pytest.raises(SystemExit):
        main()
    assert "requiere OPENAI_API_KEY" in capsys.readouterr().err


def test_cli_live_always_validates_and_hydrates_without_calling_api(monkeypatch, capsys):
    class FakeRun:
        def final_output_as(self, _output_type):
            return draft(["pv-02"])

    def fake_build_agent(session):
        session.search("Juntos Perú asistencia")
        session.open("pv-02")
        return object()

    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-used")
    monkeypatch.setattr("evidence_auditor.cli.build_agent", fake_build_agent)
    monkeypatch.setattr(
        "evidence_auditor.cli.Runner.run_sync", lambda *_args, **_kwargs: FakeRun()
    )
    monkeypatch.setattr("sys.argv", ["evidence-auditor", "live", "reclamo"])
    main()
    result = capsys.readouterr().out
    assert '"mode": "live"' in result
    assert '"passage_id": "pv-02"' in result
    assert '"status": "pending"' in result
