#!/usr/bin/env python3
"""Bounded, reproducible discovery against the OpenAlex works endpoint.

This script turns a human-written search strategy into four artifacts: the raw
responses, a normalized candidate table, a deduplication report, and a run log.
It does not screen, it does not judge relevance, and it does not decide what
counts as evidence. Every record it emits is unread.

Two rules shape the code more than anything else:

1. No book or abstract text ever reaches an output file. OpenAlex ships an
   inverted index of the abstract; the normalizer records only whether one was
   present. Discovery moves metadata.
2. A secret must not be able to leak through an artifact. `OPENALEX_API_KEY` is
   read from the environment, attached to the live request only, and every URL
   written to disk is the redacted one.

Runs offline against a recorded fixture when the network is unavailable, so the
lab works in a classroom with bad wifi. The fallback is always visible in
`search_log.json` -- it is never silent.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_STRATEGY = ROOT / "search_strategy.json"
DEFAULT_FIXTURE = ROOT / "fixture" / "openalex_response.json"
DEFAULT_OUTPUT = ROOT / "output"

API_KEY_ENV = "OPENALEX_API_KEY"
MAILTO_ENV = "OPENALEX_MAILTO"
REDACTED = "***"

CANDIDATE_FIELDS = (
    "candidate_id",
    "query_id",
    "title",
    "year",
    "doi",
    "openalex_id",
    "venue",
    "type",
    "first_author",
    "n_authors",
    "has_abstract",
)

DEDUP_FIELDS = (
    "dropped_position",
    "dropped_query_id",
    "dropped_openalex_id",
    "dropped_doi",
    "match_field",
    "match_value",
    "kept_candidate_id",
    "kept_openalex_id",
    "kept_in_candidates",
)

DOI_PREFIXES = (
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
    "doi:",
)

OPENALEX_ID_PREFIXES = (
    "https://openalex.org/",
    "http://openalex.org/",
)


class DiscoveryError(Exception):
    """A stop with an actionable message. Never a bare traceback."""


# --------------------------------------------------------------------------
# normalization
# --------------------------------------------------------------------------


def collapse_whitespace(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def normalize_doi(raw: object) -> str:
    """Return a bare, lowercase DOI. Empty string when there is none.

    OpenAlex returns `https://doi.org/10.xxxx/yyy`, but the same DOI travels
    through the world as a bare string, with `doi:`, with `dx.`, and in any
    case. All of those are the same work.
    """
    value = collapse_whitespace(raw).lower()
    if not value:
        return ""
    for prefix in DOI_PREFIXES:
        if value.startswith(prefix):
            value = value[len(prefix) :]
            break
    return value.lstrip("/")


def normalize_openalex_id(raw: object) -> str:
    value = collapse_whitespace(raw)
    for prefix in OPENALEX_ID_PREFIXES:
        if value.startswith(prefix):
            return value[len(prefix) :]
    return value


def venue_of(work: dict) -> str:
    """Journal or venue name, tolerating the shapes OpenAlex has used."""
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    name = collapse_whitespace(source.get("display_name"))
    if name:
        return name
    host = work.get("host_venue") or {}
    return collapse_whitespace(host.get("display_name"))


def normalize_work(work: dict, query_id: str) -> dict:
    """One OpenAlex work -> one flat record.

    Deliberately lossy. `abstract_inverted_index` is reduced to a boolean: the
    presence of an abstract is useful for deciding what to retrieve next, and
    the abstract itself is not ours to redistribute.
    """
    authorships = work.get("authorships") or []
    first_author = ""
    if authorships:
        author = authorships[0].get("author") or {}
        first_author = collapse_whitespace(author.get("display_name"))

    year = work.get("publication_year")
    year_text = str(year) if isinstance(year, int) else collapse_whitespace(year)

    title = collapse_whitespace(work.get("display_name") or work.get("title"))

    return {
        "query_id": query_id,
        "title": title,
        "year": year_text,
        "doi": normalize_doi(work.get("doi")),
        "openalex_id": normalize_openalex_id(work.get("id")),
        "venue": venue_of(work),
        "type": collapse_whitespace(work.get("type")),
        "first_author": first_author,
        "n_authors": str(len(authorships)),
        "has_abstract": "true" if work.get("abstract_inverted_index") else "false",
    }


def title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def record_keys(record: dict) -> list:
    """Every identifier a record can be matched on, most trustworthy first.

    A record carries more than one identity: the same work can come back with
    a DOI from one query and without it from another. Matching on a single
    key would let that pair through, so every available identifier is checked
    and every available identifier is remembered.

    The normalized title is a last resort, used only when neither identifier
    exists. Two records with the same title but different DOIs are usually a
    preprint and its published version -- different rows, and not this
    script's business to merge.
    """
    keys = []
    if record["doi"]:
        keys.append(("doi", record["doi"]))
    if record["openalex_id"]:
        keys.append(("openalex_id", record["openalex_id"].lower()))
    if keys:
        return keys
    slug = title_key(record["title"])
    return [("title", slug)] if slug else []


def dedup(records: list) -> tuple:
    """First occurrence wins. Returns (kept, report_rows).

    Order in equals order out: the caller feeds records in strategy order, so
    two runs of the same strategy produce the same table. A record with no
    identifier at all cannot be matched to anything, so it is kept.
    """
    kept: list = []
    seen: dict = {}
    report: list = []

    for position, record in enumerate(records, start=1):
        keys = record_keys(record)
        match = next((key for key in keys if key in seen), None)

        if match is not None:
            first = seen[match]
            field, value = match
            report.append(
                {
                    "dropped_position": str(position),
                    "dropped_query_id": record["query_id"],
                    "dropped_openalex_id": record["openalex_id"],
                    "dropped_doi": record["doi"],
                    "match_field": field,
                    "match_value": value,
                    "kept_candidate_id": "",
                    "kept_openalex_id": first["openalex_id"],
                }
            )
            continue

        for key in keys:
            seen[key] = record
        kept.append(record)

    return kept, report


def assign_candidate_ids(records: list) -> None:
    for index, record in enumerate(records, start=1):
        record["candidate_id"] = "D%02d" % index


def backfill_kept_ids(kept: list, included: list, report: list) -> None:
    """Point every duplicate to its canonical row and say whether the cap kept it."""
    by_openalex = {r["openalex_id"]: r.get("candidate_id", "") for r in kept}
    included_ids = {r.get("candidate_id", "") for r in included}
    for row in report:
        row["kept_candidate_id"] = by_openalex.get(row["kept_openalex_id"], "")
        row["kept_in_candidates"] = (
            "true" if row["kept_candidate_id"] in included_ids else "false"
        )


# --------------------------------------------------------------------------
# requests
# --------------------------------------------------------------------------


def build_url(endpoint: str, query: dict, per_page: int, mailto: str, api_key: str) -> tuple:
    """Return (real_url, redacted_url).

    The redacted URL is the only one that may be written to a file or printed.
    """
    params = [("search", query.get("search", ""))]

    filters = query.get("filter") or {}
    if filters:
        joined = ",".join("%s:%s" % (k, filters[k]) for k in sorted(filters))
        params.append(("filter", joined))

    params.append(("per_page", str(per_page)))
    params.append(("page", "1"))

    if mailto:
        params.append(("mailto", mailto))

    safe = urllib.parse.urlencode(params)
    real = safe
    if api_key:
        real = safe + "&" + urllib.parse.urlencode([("api_key", api_key)])
        safe = safe + "&" + urllib.parse.urlencode([("api_key", REDACTED)])

    return endpoint + "?" + real, endpoint + "?" + safe


def fetch(url: str, timeout: int) -> tuple:
    """GET and parse JSON. Returns (payload, http_status)."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "literature-agent-lab-discovery/1.0 (teaching exercise)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", None) or response.getcode()
        body = response.read().decode("utf-8")
    return json.loads(body), status


def results_of(payload: dict) -> list:
    results = payload.get("results")
    if not isinstance(results, list):
        raise DiscoveryError(
            "La respuesta no trae una lista `results`. Si viene de la API, puede ser un "
            "error de OpenAlex devuelto con forma de JSON; revise output/raw/."
        )
    return [item for item in results if isinstance(item, dict)]


# --------------------------------------------------------------------------
# strategy and fixture
# --------------------------------------------------------------------------


def load_strategy(path: Path) -> dict:
    if not path.is_file():
        raise DiscoveryError(
            "No existe la estrategia %s.\n"
            "La estrategia se escribe antes de buscar. Restaure el archivo del "
            "repositorio o pase --strategy con la ruta correcta." % path
        )
    try:
        strategy = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise DiscoveryError("La estrategia %s no es JSON válido: %s" % (path, error))

    queries = strategy.get("consultas")
    if not isinstance(queries, list) or not queries:
        raise DiscoveryError(
            "La estrategia %s no declara ninguna consulta en `consultas`." % path
        )
    for query in queries:
        if not query.get("query_id") or not query.get("search"):
            raise DiscoveryError(
                "Cada consulta necesita `query_id` y `search`. Falta en: %s"
                % json.dumps(query, ensure_ascii=False)
            )
    return strategy


def load_fixture(path: Path) -> dict:
    if not path.is_file():
        raise DiscoveryError(
            "No hay red utilizable y tampoco existe la fixture %s.\n"
            "Sin una de las dos no hay nada que normalizar. Restaure el archivo "
            "del repositorio, o ejecute con red y sin --offline." % path
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise DiscoveryError("La fixture %s no es JSON válido: %s" % (path, error))


def fixture_response(bundle: dict, query_id: str) -> dict:
    """Return the recorded response for one query.

    Current fixtures contain one response per query. The legacy single-response
    shape remains readable so an older teaching copy fails neither silently nor
    mysteriously, but newly saved fixtures always use the explicit mapping.
    """
    responses = bundle.get("responses")
    if responses is None:
        return bundle
    payload = responses.get(query_id)
    if not isinstance(payload, dict):
        raise DiscoveryError(
            "La fixture no contiene una respuesta para %s. Vuelva a capturarla "
            "con --live-only --save-fixture o use una estrategia compatible."
            % query_id
        )
    return payload


def fixture_safe_work(work: dict) -> dict:
    """Keep redistribution-safe metadata while dropping abstract/source text."""
    authorships = []
    for authorship in work.get("authorships") or []:
        author = authorship.get("author") or {}
        authorships.append({"author": {"display_name": author.get("display_name", "")}})
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    return {
        "id": work.get("id"),
        "doi": work.get("doi"),
        "display_name": work.get("display_name") or work.get("title"),
        "publication_year": work.get("publication_year"),
        "type": work.get("type"),
        "authorships": authorships,
        "primary_location": {"source": {"display_name": source.get("display_name", "")}},
        # The normalizer needs presence, not the abstract itself.
        "abstract_inverted_index": {"_present": [0]}
        if work.get("abstract_inverted_index")
        else None,
    }


def fixture_bundle(raw_dir: Path, query_log: list, strategy_id: str) -> dict:
    """Build a small per-query fallback from the live raw responses."""
    responses = {}
    for entry in query_log:
        if entry.get("served_from") != "live":
            continue
        query_id = entry["query_id"]
        payload = json.loads((raw_dir / ("%s.json" % query_id)).read_text(encoding="utf-8"))
        responses[query_id] = {
            "meta": payload.get("meta") or {},
            "results": [fixture_safe_work(work) for work in results_of(payload)],
        }
    return {
        "_fixture_provenance": {
            "aviso": "CAPTURA REAL MINIMIZADA; NO ES LA RESPUESTA CRUDA",
            "captured_utc": utc_now(),
            "strategy_id": strategy_id,
            "source": "https://api.openalex.org/works",
            "transformacion": (
                "Una respuesta por query_id. Se conservaron solo metadatos; el texto "
                "del abstract se redujo a presencia/ausencia. Las respuestas crudas "
                "solo viven en output/raw/ y no se versionan."
            ),
        },
        "responses": responses,
    }


def limits_of(strategy: dict, timeout_override: int) -> dict:
    raw = strategy.get("limites") or {}
    return {
        "per_page": int(raw.get("per_page", 25)),
        "max_records_total": int(raw.get("max_registros_total", 25)),
        "timeout_seconds": int(timeout_override or raw.get("timeout_segundos", 20)),
    }


# --------------------------------------------------------------------------
# writing
# --------------------------------------------------------------------------


def write_csv(path: Path, fieldnames: tuple, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------


def run(
    strategy_path: Path,
    fixture_path: Path,
    output_dir: Path,
    mode: str,
    timeout_override: int = 0,
    endpoint_override: str = "",
    save_fixture: Path = None,
) -> dict:
    """Execute the strategy and write the four artifacts. Returns the log."""
    strategy = load_strategy(strategy_path)
    limits = limits_of(strategy, timeout_override)
    source = strategy.get("fuente") or {}
    endpoint = endpoint_override or source.get(
        "endpoint", "https://api.openalex.org/works"
    )

    api_key = os.environ.get(API_KEY_ENV, "").strip()
    mailto = os.environ.get(MAILTO_ENV, "").strip()

    started = utc_now()
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    query_log: list = []
    fixture_payload = None
    fallback_reason = ""
    used_live = False

    for query in strategy["consultas"]:
        query_id = query["query_id"]
        real_url, safe_url = build_url(
            endpoint, query, limits["per_page"], mailto, api_key
        )

        entry = {
            "query_id": query_id,
            "search": query.get("search", ""),
            "filter": query.get("filter") or {},
            "per_page": limits["per_page"],
            "request_url_redacted": safe_url if mode != "offline" else None,
            "http_status": None,
            "served_from": None,
            "results_returned": 0,
            "error": None,
        }

        payload = None
        if mode != "offline":
            try:
                payload, status = fetch(real_url, limits["timeout_seconds"])
                entry["http_status"] = status
                entry["served_from"] = "live"
                used_live = True
                (raw_dir / ("%s.json" % query_id)).write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            except (urllib.error.URLError, OSError, ValueError) as error:
                message = redact(str(error), api_key)
                entry["error"] = message
                if mode == "live-only":
                    entry["served_from"] = "none"
                    query_log.append(entry)
                    write_json(
                        output_dir / "search_log.json",
                        failed_log(strategy, started, entry, query_log, api_key, mailto),
                    )
                    raise DiscoveryError(
                        "--live-only y la consulta %s no llegó a %s.\n"
                        "Detalle: %s\n"
                        "No se escribió candidates.csv: sin respuesta real no hay nada que "
                        "normalizar. Quite --live-only para usar la fixture, o revise la red."
                        % (query_id, endpoint, message)
                    )
                if not fallback_reason:
                    fallback_reason = "La consulta %s no llegó a la API (%s). Esa consulta se sirvió desde la fixture." % (
                        query_id,
                        message,
                    )

        if payload is None:
            if fixture_payload is None:
                fixture_payload = load_fixture(fixture_path)
            payload = fixture_response(fixture_payload, query_id)
            (raw_dir / ("%s.json" % query_id)).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            entry["served_from"] = "fixture"
            if mode == "offline" and not fallback_reason:
                fallback_reason = "Modo --offline: no se intentó ninguna petición de red."

        entry["results_returned"] = len(results_of(payload))
        query_log.append(entry)

    # Normalize in strategy order so the output is stable across runs.
    records: list = []
    for entry, query in zip(query_log, strategy["consultas"]):
        payload = None
        if entry["served_from"] == "live":
            payload = json.loads(
                (raw_dir / ("%s.json" % entry["query_id"])).read_text(encoding="utf-8")
            )
        else:
            payload = fixture_response(fixture_payload, entry["query_id"])
        for work in results_of(payload):
            records.append(normalize_work(work, query["query_id"]))

    kept, report = dedup(records)
    deduped_count = len(kept)
    assign_candidate_ids(kept)

    cap = limits["max_records_total"]
    dropped_by_cap = max(0, len(kept) - cap)
    included = kept[:cap]
    backfill_kept_ids(kept, included, report)

    write_csv(output_dir / "candidates.csv", CANDIDATE_FIELDS, included)
    write_csv(output_dir / "dedup_report.csv", DEDUP_FIELDS, report)

    if save_fixture and used_live:
        bundle = fixture_bundle(raw_dir, query_log, strategy.get("strategy_id", ""))
        if len(bundle["responses"]) != len(strategy["consultas"]):
            raise DiscoveryError(
                "No se guardó la fixture: no todas las consultas tuvieron respuesta "
                "en vivo. Ejecute otra vez con --live-only."
            )
        write_json(save_fixture, bundle)

    log = {
        "run": {
            "script": "search_openalex.py",
            "strategy_id": strategy.get("strategy_id", ""),
            "strategy_file": str(strategy_path.name),
            "mode_requested": mode,
            "endpoint": endpoint,
            "started_utc": started,
            "finished_utc": utc_now(),
        },
        "auth": {
            "api_key_provided": bool(api_key),
            "api_key_source": "env:%s" % API_KEY_ENV,
            "api_key_in_artifacts": False,
            "mailto_provided": bool(mailto),
        },
        "fallback": {
            "used_fixture": any(e["served_from"] == "fixture" for e in query_log),
            "reason": fallback_reason,
            "fixture_file": str(fixture_path.name),
        },
        "queries": query_log,
        "normalization": {
            "records_seen": len(records),
            "records_after_dedup": deduped_count,
            "duplicates_dropped": len(report),
        },
        "cap": {
            "max_records_total": cap,
            "records_written": len(included),
            "dropped_by_cap": dropped_by_cap,
        },
        "outputs": {
            "candidates_csv": "candidates.csv",
            "dedup_report_csv": "dedup_report.csv",
            "raw_dir": "raw/",
        },
        "esto_no_es": (
            "Un registro de descubrimiento. Ninguna fila de candidates.csv ha sido "
            "leída, cribada ni verificada por nadie. No es evidencia y no entra sola "
            "a case/, que está congelado."
        ),
    }
    write_json(output_dir / "search_log.json", log)
    return log


def failed_log(
    strategy: dict, started: str, entry: dict, query_log: list, api_key: str, mailto: str
) -> dict:
    """A log for the --live-only failure path, so the run is still auditable."""
    return {
        "run": {
            "script": "search_openalex.py",
            "strategy_id": strategy.get("strategy_id", ""),
            "mode_requested": "live-only",
            "started_utc": started,
            "finished_utc": utc_now(),
            "outcome": "failed",
        },
        "auth": {
            "api_key_provided": bool(api_key),
            "api_key_source": "env:%s" % API_KEY_ENV,
            "api_key_in_artifacts": False,
            "mailto_provided": bool(mailto),
        },
        "queries": query_log,
        "error": entry["error"],
    }


def redact(text: str, api_key: str) -> str:
    if api_key and api_key in text:
        return text.replace(api_key, REDACTED)
    return text


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------


def parse_args(argv: list) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ejecuta search_strategy.json contra OpenAlex y escribe candidatos "
            "normalizados, un reporte de duplicados y un registro de la corrida. "
            "Descubrir no es cribar."
        )
    )
    parser.add_argument("--strategy", default=str(DEFAULT_STRATEGY))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT))
    parser.add_argument(
        "--offline",
        action="store_true",
        help="No intentar ninguna petición de red; usar la fixture.",
    )
    parser.add_argument(
        "--live-only",
        action="store_true",
        help="Fallar si la API no responde, en vez de caer a la fixture.",
    )
    parser.add_argument("--timeout", type=int, default=0)
    parser.add_argument("--endpoint", default="")
    parser.add_argument(
        "--save-fixture",
        default="",
        help="Guardar la primera respuesta real en esta ruta (solo con red).",
    )
    return parser.parse_args(argv)


def main(argv: list) -> int:
    args = parse_args(argv)
    if args.offline and args.live_only:
        print("--offline y --live-only se contradicen. Elija uno.", file=sys.stderr)
        return 1

    mode = "offline" if args.offline else ("live-only" if args.live_only else "auto")

    try:
        log = run(
            strategy_path=Path(args.strategy).resolve(),
            fixture_path=Path(args.fixture).resolve(),
            output_dir=Path(args.out).resolve(),
            mode=mode,
            timeout_override=args.timeout,
            endpoint_override=args.endpoint,
            save_fixture=Path(args.save_fixture).resolve() if args.save_fixture else None,
        )
    except DiscoveryError as error:
        print("BLOQUEADO\n%s" % error, file=sys.stderr)
        return 2

    served = "en vivo" if not log["fallback"]["used_fixture"] else "desde la fixture"
    print("Descubrimiento %s: %d registros vistos, %d duplicados, %d candidatos." % (
        served,
        log["normalization"]["records_seen"],
        log["normalization"]["duplicates_dropped"],
        log["cap"]["records_written"],
    ))
    if log["cap"]["dropped_by_cap"]:
        print(
            "Tope aplicado: %d candidatos quedaron fuera por max_registros_total=%d."
            % (log["cap"]["dropped_by_cap"], log["cap"]["max_records_total"])
        )
    if log["fallback"]["reason"]:
        print(log["fallback"]["reason"])
    print("Ninguno de estos registros ha sido cribado. Descubrir no es cribar.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
