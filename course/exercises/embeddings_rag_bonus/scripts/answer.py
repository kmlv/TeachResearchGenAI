"""Answer a question from the local corpus, with citations or with silence.

This is where the exercise stops being retrieval and becomes RAG, and the
difference is not that a model writes prose. It is that three things are
enforced instead of hoped for:

1. **The corpus may not contain the answer.** The rule that decides is a
   measurement, not a mood: `calibrate_answer.py` scores twelve audited
   questions and eight questions no economics library answers, and the
   threshold sits in the gap between the two distributions. Below it this
   script abstains and says with what numbers it decided.
2. **Every claim points at a page.** `[n]` markers are checked mechanically
   against the passages that were actually retrieved. A marker nobody handed
   the writer is a bug, and it is caught here rather than in front of a class.
3. **Text leaves the laptop only with permission.** The default generator is
   extractive: it quotes the retrieved passages and never calls anything. The
   `claude_cli` generator is opt-in, prints what it would send before sending
   it, and falls back to the extractive answer on timeout, on error, or when
   the synthesised answer fails the citation check.

What no program in this file can check is whether a cited passage supports the
sentence it is attached to. A person opens the PDF at the printed page range.
That is the whole point of printing it.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np

from common import (
    ABSTAIN_SENTENCE,
    CONSENT_WARNING,
    abstention_statistic,
    abstention_verdict,
    calibration_error,
    citation_problems,
    clip_quote,
    excerpt_disclosure,
    extractive_answer,
    format_source_line,
    is_evidence_sentence,
    quote_is_grounded,
    split_sentences,
    synthesis_problems,
    synthesis_prompt,
)
from search import SearchIndex

warnings.filterwarnings(
    "ignore", message=r"The model .* now uses mean pooling instead of CLS embedding.*"
)

GENERATORS = ("extractive", "claude_cli")

# Long enough for Opus to answer a paragraph over five short passages, short
# enough that a stalled call does not hold a classroom hostage. On expiry the
# extractive answer is printed instead, so the cost of being wrong here is a
# less fluent answer, never a dead demo.
CLAUDE_TIMEOUT_SECONDS = 90

# Kristian explicitly requested Opus 5 for this demo. Keep the canonical model
# name visible so a classroom run cannot silently resolve to another alias.
CLAUDE_MODEL = "claude-opus-5"


def load_calibration(path: Path, mode: str, model: str) -> dict:
    """The measured threshold, or an exit that says which command produces it.

    Refusing to run without a calibration is deliberate. A default threshold
    compiled into this file would be exactly the unexplained constant the rest
    of the lab argues against, and it would silently be wrong for any other
    corpus or embedding model.
    """
    if not path.exists():
        raise SystemExit(
            f"Falta {path.name}: answer.py no inventa un umbral de abstención.\n"
            "Medilo primero:\n"
            f"  python scripts/calibrate_answer.py --mode {mode} --write"
        )
    calibration = json.loads(path.read_text(encoding="utf-8"))
    problem = calibration_error(calibration, mode, model)
    if problem:
        raise SystemExit(problem)
    return calibration


def select_evidence(
    index: SearchIndex, question: str, results: list[dict], max_sources: int
) -> list[dict]:
    """One short, verbatim, grounded quote per retrieved passage.

    A 320-word chunk is the right unit to retrieve and the wrong unit to quote,
    so each passage is split into sentences and scored against the question
    with the same embedding model that retrieved it. The sentence that survives
    is checked back against the chunk it came from: a quote that is not a
    verbatim fragment of its own source is dropped rather than shown.
    """
    query_vector = index.embed_query(question)
    picks: list[dict] = []
    for result in results[:max_sources]:
        chunk_text = index.chunks[result["chunk_id"]]["text"]
        sentences = split_sentences(chunk_text)
        # Declarative sentences first; a passage made only of headings and
        # questions still gets to speak, with its best line.
        usable = [s for s in sentences if is_evidence_sentence(s)] or sentences
        if not usable:
            continue
        scores = index.embed_passages(usable) @ query_vector
        best = int(np.argmax(scores))
        quote = clip_quote(usable[best])
        if not quote_is_grounded(quote, chunk_text):
            continue
        picks.append(
            {
                "number": len(picks) + 1,
                "chunk_id": result["chunk_id"],
                "quote": quote,
                "sentence_similarity": round(float(scores[best]), 4),
                "citation": result["citation"],
                "pages": result["pages"],
                "document_id": result["document_id"],
                "page_start": result["page_start"],
                "page_end": result["page_end"],
                "relative_path": result["relative_path"],
                "dense_score": result["dense_score"],
                "score": result["score"],
            }
        )
    return picks


def consent_granted(picks: list[dict], granted: bool, interactive: bool) -> bool:
    """Whether excerpts may be sent, after the warning has actually been shown.

    `--send-excerpts` is consent given in advance and is honoured. Without it
    the warning and the exact payload size are printed and the answer is asked
    for out loud; a non-interactive run (a pipe, a Makefile, a slide build)
    cannot consent on a person's behalf, so it declines.
    """
    if granted:
        return True
    print(f"\n{CONSENT_WARNING}\n{excerpt_disclosure(picks)}", file=sys.stderr)
    if not interactive:
        print(
            "Sin TTY no hay consentimiento posible: se responde en modo "
            "extractivo. Usá --send-excerpts si querés autorizarlo explícito.",
            file=sys.stderr,
        )
        return False
    reply = input("¿Enviar estos fragmentos a la API de Anthropic? [s/N] ").strip().lower()
    return reply in {"s", "si", "sí", "y", "yes"}


def synthesize_with_claude(
    prompt: str, timeout: int = CLAUDE_TIMEOUT_SECONDS, model: str = CLAUDE_MODEL
) -> tuple[str, str]:
    """`(answer, note)`; an empty answer means the caller falls back.

    Every failure mode of an external process is a note, never a traceback: no
    CLI installed, non-zero exit, a call that never returns. The demo degrades
    to the local answer and says why on screen.
    """
    binary = shutil.which("claude")
    if not binary:
        return "", "No se encontró el CLI `claude` en el PATH."
    try:
        completed = subprocess.run(
            [binary, "-p", prompt, "--model", model],
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "", f"El CLI `claude` no respondió en {timeout} s."
    except OSError as error:  # pragma: no cover - depends on the local install
        return "", f"No se pudo ejecutar el CLI `claude`: {error}."
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip().splitlines()
        return "", f"El CLI `claude` salió con código {completed.returncode}: " + (
            detail[-1] if detail else "sin detalle"
        )
    text = (completed.stdout or "").strip()
    if not text:
        return "", "El CLI `claude` devolvió una respuesta vacía."
    return text, f"Respuesta sintetizada con el CLI `claude` (modelo {model})."


def build_answer(
    index: SearchIndex,
    question: str,
    calibration: dict,
    mode: str = "dense",
    limit: int = 5,
    per_document: int = 2,
    generator: str = "extractive",
    send_excerpts: bool = False,
    interactive: bool = False,
    timeout: int = CLAUDE_TIMEOUT_SECONDS,
) -> dict:
    """Retrieve, decide whether to answer at all, then answer or abstain."""
    results = index.search(question, mode=mode, limit=limit, per_document=per_document)
    verdict = abstention_verdict(abstention_statistic(results), calibration)
    notes: list[str] = []
    if not verdict["separable"]:
        notes.append(
            "La calibración no separa las preguntas con y sin evidencia: el "
            "umbral es conservador y esta decisión es más débil de lo que parece."
        )

    if not verdict["answer"] or not results:
        return {
            "question": question,
            "mode": mode,
            "generator": "abstained",
            "answered": False,
            "verdict": verdict,
            "answer": ABSTAIN_SENTENCE,
            "sources": [],
            "citation_check": {"ok": True, "problems": []},
            "notes": notes
            + [
                f"Similitud máxima {verdict['statistic']} < umbral "
                f"{verdict['threshold']} (margen {verdict['margin']})."
            ],
        }

    picks = select_evidence(index, question, results, limit)
    if not picks:
        return {
            "question": question,
            "mode": mode,
            "generator": "abstained",
            "answered": False,
            "verdict": verdict,
            "answer": ABSTAIN_SENTENCE,
            "sources": [],
            "citation_check": {"ok": True, "problems": []},
            "notes": notes
            + ["Ningún pasaje recuperado produjo una cita literal verificable."],
        }

    answer = extractive_answer(picks)
    used = "extractive"
    generator_abstained = False
    if generator == "claude_cli":
        if not consent_granted(picks, send_excerpts, interactive):
            notes.append(
                "Sin consentimiento explícito: no se envió nada, respuesta local."
            )
        else:
            notes.append(excerpt_disclosure(picks))
            synthesised, note = synthesize_with_claude(
                synthesis_prompt(question, picks), timeout=timeout
            )
            notes.append(note)
            problems = synthesis_problems(synthesised, picks) if synthesised else []
            if synthesised and not problems:
                answer = synthesised
                used = "claude_cli"
                generator_abstained = ABSTAIN_SENTENCE in synthesised
            elif synthesised:
                notes.append(
                    "La respuesta sintetizada falló el control de citas ("
                    + " ".join(problems)
                    + ") y se descartó."
                )
            if used == "extractive":
                notes.append("Se muestra la respuesta extractiva local.")
            elif generator_abstained:
                notes.append(
                    "El recuperador superó el umbral, pero Opus concluyó que los "
                    "fragmentos no bastaban para redactar una respuesta."
                )
            else:
                notes.append("Cada [n] fue verificado contra los pasajes recuperados.")

    problems = citation_problems(
        answer, len(picks), require_citation=not generator_abstained
    )
    return {
        "question": question,
        "mode": mode,
        "generator": used,
        "answered": not generator_abstained,
        "verdict": verdict,
        "answer": answer,
        "sources": [
            {key: pick[key] for key in pick if key != "chunk_id"} for pick in picks
        ],
        "citation_check": {"ok": not problems, "problems": problems},
        "notes": notes,
    }


def render(payload: dict) -> str:
    """The terminal view: the answer, its sources, and the numbers behind it."""
    verdict = payload["verdict"]
    lines = [f"Pregunta: {payload['question']}", "", payload["answer"], ""]
    if payload["sources"]:
        lines.append("Fuentes")
        lines += [
            format_source_line(source["number"], source)
            for source in payload["sources"]
        ]
        lines.append("")
    retrieval_decision = "pasa" if verdict["answer"] else "se abstiene"
    lines.append(
        f"Regla de recuperación: {retrieval_decision} porque la similitud máxima "
        f"{verdict['statistic']} {'≥' if verdict['answer'] else '<'} umbral "
        f"{verdict['threshold']} (margen {verdict['margin']})."
    )
    if verdict["answer"] and not payload["answered"]:
        lines.append(
            "Decisión final: Opus se abstuvo después de leer los fragmentos recuperados."
        )
    lines.append(
        f"Generador: {payload['generator']}. Citas verificadas: "
        f"{'sí' if payload['citation_check']['ok'] else 'NO'}."
    )
    lines += [f"Nota: {note}" for note in payload["notes"]]
    lines += [f"Problema de citas: {problem}" for problem in payload["citation_check"]["problems"]]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    root = Path(__file__).parents[1]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("question")
    parser.add_argument("--index", type=Path, default=root / "local_index_full")
    parser.add_argument(
        "--calibration", type=Path, default=root / "answer-calibration.json"
    )
    parser.add_argument("--mode", choices=["lexical", "dense", "hybrid"], default="dense")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--per-document", type=int, default=2)
    parser.add_argument("--generator", choices=GENERATORS, default="extractive")
    parser.add_argument(
        "--send-excerpts",
        action="store_true",
        help="consentimiento explícito para enviar los fragmentos citados a la API",
    )
    parser.add_argument("--timeout", type=int, default=CLAUDE_TIMEOUT_SECONDS)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    index = SearchIndex.load(args.index)
    calibration = load_calibration(args.calibration, args.mode, index.config["model"])
    payload = build_answer(
        index,
        args.question,
        calibration,
        mode=args.mode,
        limit=args.limit,
        per_document=args.per_document,
        generator=args.generator,
        send_excerpts=args.send_excerpts,
        interactive=sys.stdin.isatty(),
        timeout=args.timeout,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render(payload))
    return 0 if payload["citation_check"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
