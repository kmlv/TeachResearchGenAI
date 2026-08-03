"""CLI reproducible; live es el único modo que puede usar API."""

import argparse
import json
import os
from pathlib import Path

from agents import Runner

from .agent import MAX_TURNS, RUN_CONFIG, build_agent, validate_draft
from .corpus import SOURCES, Corpus
from .models import AuditDraft
from .session import AuditSession

FIXTURES = Path(__file__).parents[2] / "tests" / "fixtures"


def _replay(name: str, causal_override: bool | None = None) -> dict:
    fixture = json.loads((FIXTURES / name).read_text())
    session = AuditSession()
    for call in fixture["tool_calls"]:
        (
            session.search(call["input"])
            if call["tool"] == "buscar_corpus"
            else session.open(call["input"])
        )
    return validate_draft(
        fixture["claim"],
        AuditDraft.model_validate(fixture["draft"]),
        session,
        causal=fixture["causal"] if causal_override is None else causal_override,
        mode="recorded_replay",
    ).model_dump()


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditor de evidencia offline")
    parser.add_argument("mode", choices=("list", "offline", "replay", "live"))
    parser.add_argument("claim", nargs="?", default="Juntos mejoró la asistencia escolar.")
    parser.add_argument(
        "--causal", action="store_true", help="Activa la alarma causal de la aplicación."
    )
    args = parser.parse_args()
    if args.mode == "list":
        for source in SOURCES:
            print(f"{source.id}: {source.title} — {source.url}")
    elif args.mode == "offline":
        for passage in Corpus().search(args.claim):
            print(f"{passage.id}: {passage.summary} [{passage.locator}]")
    elif args.mode == "replay":
        for filename in ("recorded_replay.json", "recorded_replay_insufficient.json"):
            override = True if args.causal else None
            print(json.dumps(_replay(filename, override), ensure_ascii=False))
    else:
        if not os.environ.get("OPENAI_API_KEY"):
            parser.error("live requiere OPENAI_API_KEY; use 'offline' o 'replay' sin API.")
        session = AuditSession()
        output = Runner.run_sync(
            build_agent(session), args.claim, max_turns=MAX_TURNS, run_config=RUN_CONFIG
        )
        result = validate_draft(
            args.claim, output.final_output_as(AuditDraft), session, causal=args.causal
        )
        print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
