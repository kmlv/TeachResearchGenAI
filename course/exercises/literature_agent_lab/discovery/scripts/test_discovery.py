#!/usr/bin/env python3
"""Offline tests for the discovery step.

Nothing here touches the network, and nothing here writes into the shipped
`output/`. The one test that exercises the live path points at a closed local
port on purpose, so the fallback is proven rather than assumed.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import search_openalex as oa  # noqa: E402

STRATEGY = ROOT / "search_strategy.json"
FIXTURE = ROOT / "fixture" / "openalex_response.json"
SCRIPT = ROOT / "scripts" / "search_openalex.py"

# Nothing listens on port 9 (the discard port), so a connection there fails
# immediately instead of hanging the suite.
DEAD_ENDPOINT = "http://127.0.0.1:9/works"

passed: list = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise AssertionError(("%s failed. %s" % (label, detail)).strip())
    passed.append(label)


def work(**overrides) -> dict:
    base = {
        "id": "https://openalex.org/W111",
        "doi": "https://doi.org/10.1000/abc",
        "display_name": "A title",
        "publication_year": 2024,
        "type": "article",
        "primary_location": {"source": {"display_name": "A Journal"}},
        "authorships": [],
        "abstract_inverted_index": None,
    }
    base.update(overrides)
    return base


def read_csv(path: Path) -> list:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def run_script(*args, env_extra=None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + list(args),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


# --------------------------------------------------------------------------
# normalization
# --------------------------------------------------------------------------


def test_doi_normalization() -> None:
    check("doi: https prefix", oa.normalize_doi("https://doi.org/10.1/AB") == "10.1/ab")
    check("doi: http prefix", oa.normalize_doi("http://doi.org/10.1/ab") == "10.1/ab")
    check("doi: dx host", oa.normalize_doi("https://dx.doi.org/10.1/ab") == "10.1/ab")
    check("doi: doi: scheme", oa.normalize_doi("doi:10.1/AB") == "10.1/ab")
    check("doi: bare", oa.normalize_doi("10.1/ab") == "10.1/ab")
    check("doi: whitespace", oa.normalize_doi("  10.1/ab  ") == "10.1/ab")
    check("doi: none", oa.normalize_doi(None) == "")
    check("doi: empty", oa.normalize_doi("") == "")


def test_openalex_id_normalization() -> None:
    check("id: prefix stripped", oa.normalize_openalex_id("https://openalex.org/W9") == "W9")
    check("id: bare kept", oa.normalize_openalex_id("W9") == "W9")
    check("id: none", oa.normalize_openalex_id(None) == "")


def test_record_normalization() -> None:
    record = oa.normalize_work(
        work(
            display_name="  Two   spaces  ",
            authorships=[
                {"author": {"display_name": "Ada Lovelace"}},
                {"author": {"display_name": "Alan Turing"}},
            ],
        ),
        "Q1",
    )
    check("record: title collapsed", record["title"] == "Two spaces", record["title"])
    check("record: query id kept", record["query_id"] == "Q1")
    check("record: year as text", record["year"] == "2024")
    check("record: first author", record["first_author"] == "Ada Lovelace")
    check("record: author count", record["n_authors"] == "2")
    check("record: venue", record["venue"] == "A Journal")
    check("record: fields exact", set(record) | {"candidate_id"} == set(oa.CANDIDATE_FIELDS))


def test_missing_fields_do_not_crash() -> None:
    record = oa.normalize_work(
        {"id": None, "doi": None, "display_name": None, "primary_location": None}, "Q1"
    )
    check("missing: title empty", record["title"] == "")
    check("missing: year empty", record["year"] == "")
    check("missing: venue empty", record["venue"] == "")
    check("missing: authors zero", record["n_authors"] == "0")


def test_host_venue_fallback() -> None:
    record = oa.normalize_work(
        work(primary_location=None, host_venue={"display_name": "Old Shape"}), "Q1"
    )
    check("venue: host_venue fallback", record["venue"] == "Old Shape")


def test_abstract_is_never_carried() -> None:
    """The abstract collapses to a boolean. Its words must not survive."""
    inverted = {"telepathic": [0], "marmalade": [1], "quixotic": [2]}
    record = oa.normalize_work(work(abstract_inverted_index=inverted), "Q1")
    check("abstract: flagged present", record["has_abstract"] == "true")
    blob = json.dumps(record).lower()
    for token in inverted:
        check("abstract: %s not stored" % token, token not in blob, blob)
    absent = oa.normalize_work(work(abstract_inverted_index=None), "Q1")
    check("abstract: flagged absent", absent["has_abstract"] == "false")


# --------------------------------------------------------------------------
# dedup
# --------------------------------------------------------------------------


def test_dedup_by_doi() -> None:
    records = [
        oa.normalize_work(work(id="https://openalex.org/W1", doi="https://doi.org/10.1/AB"), "Q1"),
        oa.normalize_work(work(id="https://openalex.org/W2", doi="10.1/ab"), "Q2"),
    ]
    kept, report = oa.dedup(records)
    check("dedup doi: one kept", len(kept) == 1, str(len(kept)))
    check("dedup doi: first wins", kept[0]["openalex_id"] == "W1")
    check("dedup doi: reported", report[0]["match_field"] == "doi", str(report))
    check("dedup doi: kept id recorded", report[0]["kept_openalex_id"] == "W1")


def test_dedup_by_openalex_id_when_doi_missing() -> None:
    records = [
        oa.normalize_work(work(id="https://openalex.org/W5", doi=None), "Q1"),
        oa.normalize_work(work(id="https://openalex.org/W5", doi=None), "Q2"),
    ]
    kept, report = oa.dedup(records)
    check("dedup id: one kept", len(kept) == 1)
    check("dedup id: match field", report[0]["match_field"] == "openalex_id")


def test_dedup_by_title_as_last_resort() -> None:
    records = [
        oa.normalize_work(work(id=None, doi=None, display_name="Same Title!"), "Q1"),
        oa.normalize_work(work(id=None, doi=None, display_name="same   title"), "Q2"),
    ]
    kept, report = oa.dedup(records)
    check("dedup title: one kept", len(kept) == 1)
    check("dedup title: match field", report[0]["match_field"] == "title")


def test_different_works_are_not_merged() -> None:
    records = [
        oa.normalize_work(work(id="https://openalex.org/W1", doi="10.1/a"), "Q1"),
        oa.normalize_work(work(id="https://openalex.org/W2", doi="10.1/b"), "Q1"),
    ]
    kept, report = oa.dedup(records)
    check("dedup: distinct works survive", len(kept) == 2 and not report)


def test_unidentifiable_records_are_kept() -> None:
    records = [
        oa.normalize_work({"display_name": ""}, "Q1"),
        oa.normalize_work({"display_name": ""}, "Q2"),
    ]
    kept, _ = oa.dedup(records)
    check("dedup: nothing to match on is kept", len(kept) == 2)


def test_dedup_is_order_stable() -> None:
    records = [
        oa.normalize_work(work(id="https://openalex.org/W%d" % i, doi="10.1/%d" % (i % 3)), "Q1")
        for i in range(9)
    ]
    first = [r["openalex_id"] for r in oa.dedup(records)[0]]
    second = [r["openalex_id"] for r in oa.dedup(records)[0]]
    check("dedup: deterministic", first == second == ["W0", "W1", "W2"], str(first))


# --------------------------------------------------------------------------
# fixture integrity
# --------------------------------------------------------------------------


def test_shipped_fixture_is_honest() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    provenance = payload.get("_fixture_provenance") or {}
    check("fixture: provenance block", bool(provenance))
    check("fixture: says it is minimized", "MINIMIZADA" in provenance.get("aviso", ""))
    responses = payload.get("responses") or {}
    strategy = oa.load_strategy(STRATEGY)
    query_ids = [query["query_id"] for query in strategy["consultas"]]
    check("fixture: one response per query", sorted(responses) == sorted(query_ids), str(sorted(responses)))
    results = [work for query_id in query_ids for work in responses[query_id]["results"]]
    check("fixture: has results", len(results) >= 8, str(len(results)))
    check(
        "fixture: no abstract text",
        all(
            item.get("abstract_inverted_index") in (None, {"_present": [0]})
            for item in results
        ),
    )
    check(
        "fixture: real OpenAlex ids",
        all((item.get("id") or "").startswith("https://openalex.org/W") for item in results),
    )
    check(
        "fixture: transformation documented",
        "metadatos" in provenance.get("transformacion", ""),
    )


def test_shipped_strategy_declares_its_gaps() -> None:
    strategy = oa.load_strategy(STRATEGY)
    check("strategy: has queries", len(strategy["consultas"]) >= 1)
    check("strategy: declares gaps", len(strategy.get("huecos_conocidos") or []) >= 3)
    check("strategy: has a cap", int(strategy["limites"]["max_registros_total"]) > 0)


def test_broken_strategy_fails_with_a_reason() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "strategy.json"
        bad.write_text(json.dumps({"strategy_id": "X"}), encoding="utf-8")
        try:
            oa.load_strategy(bad)
        except oa.DiscoveryError as error:
            check("strategy: actionable error", "consultas" in str(error), str(error))
        else:
            raise AssertionError("A strategy with no queries should not load.")


# --------------------------------------------------------------------------
# end to end, offline
# --------------------------------------------------------------------------


def test_offline_run_writes_all_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "output"
        result = run_script("--offline", "--out", str(out))
        check("offline: exit 0", result.returncode == 0, result.stderr)
        for name in ("candidates.csv", "dedup_report.csv", "search_log.json"):
            check("offline: wrote %s" % name, (out / name).is_file())
        strategy = oa.load_strategy(STRATEGY)
        for query in strategy["consultas"]:
            check(
                "offline: raw %s kept" % query["query_id"],
                (out / "raw" / (query["query_id"] + ".json")).is_file(),
            )

        log = json.loads((out / "search_log.json").read_text(encoding="utf-8"))
        check("offline: fallback visible", log["fallback"]["used_fixture"] is True)
        check("offline: no request url logged", all(q["request_url_redacted"] is None for q in log["queries"]))
        check("offline: reason written", bool(log["fallback"]["reason"]))

        rows = read_csv(out / "candidates.csv")
        fixture = oa.load_fixture(FIXTURE)
        normalized = []
        for query in strategy["consultas"]:
            payload = oa.fixture_response(fixture, query["query_id"])
            normalized.extend(
                oa.normalize_work(work, query["query_id"])
                for work in oa.results_of(payload)
            )
        kept, expected_report = oa.dedup(normalized)
        expected_rows = min(len(kept), strategy["limites"]["max_registros_total"])
        expected_cap_drop = max(0, len(kept) - expected_rows)
        check("offline: expected unique works", len(rows) == expected_rows, str(len(rows)))
        check("offline: header exact", tuple(rows[0]) == oa.CANDIDATE_FIELDS, str(tuple(rows[0])))
        ids = [row["candidate_id"] for row in rows]
        check("offline: ids sequential", ids == ["D%02d" % i for i in range(1, expected_rows + 1)], str(ids))
        check("offline: dois all normalized", all(not row["doi"].startswith("http") for row in rows))
        nonempty_dois = [row["doi"] for row in rows if row["doi"]]
        check(
            "offline: nonempty dois unique",
            len(set(nonempty_dois)) == len(nonempty_dois),
        )

        report = read_csv(out / "dedup_report.csv")
        check("offline: duplicates reported", len(report) == len(expected_report), str(len(report)))
        check(
            "offline: every drop names its canonical candidate",
            all(row["kept_candidate_id"] for row in report),
        )
        included_ids = {row["candidate_id"] for row in rows}
        check(
            "offline: report says whether the cap kept the canonical row",
            all(row["kept_in_candidates"] in ("true", "false") for row in report),
        )
        check(
            "offline: included canonical ids resolve",
            all(
                row["kept_candidate_id"] in included_ids
                for row in report
                if row["kept_in_candidates"] == "true"
            ),
        )
        check(
            "offline: counts reconcile",
            log["normalization"]["records_seen"]
            == len(rows) + len(report) + log["cap"]["dropped_by_cap"],
        )
        check("offline: cap exact", log["cap"]["dropped_by_cap"] == expected_cap_drop)
        check("offline: says it is not screening", "cribad" in log["esto_no_es"])
        check("offline: stdout repeats the warning", "no es cribar" in result.stdout)


def test_offline_run_is_reproducible() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        first, second = Path(tmp) / "a", Path(tmp) / "b"
        run_script("--offline", "--out", str(first))
        run_script("--offline", "--out", str(second))
        for name in ("candidates.csv", "dedup_report.csv"):
            check(
                "reproducible: %s identical" % name,
                (first / name).read_bytes() == (second / name).read_bytes(),
            )


def test_cap_is_applied_and_announced() -> None:
    """A cap that silently truncates reads as full coverage. It must not."""
    with tempfile.TemporaryDirectory() as tmp:
        strategy = json.loads(STRATEGY.read_text(encoding="utf-8"))
        strategy["limites"]["max_registros_total"] = 3
        path = Path(tmp) / "strategy.json"
        path.write_text(json.dumps(strategy, ensure_ascii=False), encoding="utf-8")

        out = Path(tmp) / "output"
        result = run_script("--offline", "--strategy", str(path), "--out", str(out))
        check("cap: exit 0", result.returncode == 0, result.stderr)
        rows = read_csv(out / "candidates.csv")
        check("cap: rows truncated", len(rows) == 3, str(len(rows)))
        log = json.loads((out / "search_log.json").read_text(encoding="utf-8"))
        fixture = oa.load_fixture(FIXTURE)
        normalized = []
        for query in strategy["consultas"]:
            normalized.extend(
                oa.normalize_work(work, query["query_id"])
                for work in oa.results_of(oa.fixture_response(fixture, query["query_id"]))
            )
        expected_drop = max(0, len(oa.dedup(normalized)[0]) - 3)
        check("cap: exact dropped count", log["cap"]["dropped_by_cap"] == expected_drop, str(log["cap"]))
        check("cap: announced on stdout", "Tope aplicado" in result.stdout, result.stdout)


# --------------------------------------------------------------------------
# fallback and failure
# --------------------------------------------------------------------------


def test_unreachable_api_falls_back_to_the_fixture() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "output"
        result = run_script(
            "--endpoint", DEAD_ENDPOINT, "--timeout", "2", "--out", str(out)
        )
        check("fallback: exit 0", result.returncode == 0, result.stderr)
        log = json.loads((out / "search_log.json").read_text(encoding="utf-8"))
        check("fallback: fixture used", log["fallback"]["used_fixture"] is True)
        check("fallback: reason recorded", "no llegó a la API" in log["fallback"]["reason"], log["fallback"]["reason"])
        check("fallback: error kept per query", bool(log["queries"][0]["error"]))
        check("fallback: candidates still written", (out / "candidates.csv").is_file())


def test_live_only_refuses_to_invent_results() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "output"
        result = run_script(
            "--live-only", "--endpoint", DEAD_ENDPOINT, "--timeout", "2", "--out", str(out)
        )
        check("live-only: nonzero exit", result.returncode != 0, str(result.returncode))
        check("live-only: blocked banner", "BLOQUEADO" in result.stderr, result.stderr)
        check("live-only: explains the fix", "--live-only" in result.stderr)
        check(
            "live-only: no candidates written",
            not (out / "candidates.csv").exists(),
        )
        check("live-only: failure still logged", (out / "search_log.json").is_file())


def test_contradictory_flags_are_refused() -> None:
    result = run_script("--offline", "--live-only")
    check("flags: refused", result.returncode == 1, result.stderr)
    check("flags: says why", "se contradicen" in result.stderr)


def test_missing_fixture_says_what_to_do() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "output"
        result = run_script(
            "--offline", "--fixture", str(Path(tmp) / "nope.json"), "--out", str(out)
        )
        check("missing fixture: exit 2", result.returncode == 2, str(result.returncode))
        check("missing fixture: actionable", "Restaure el archivo" in result.stderr, result.stderr)


# --------------------------------------------------------------------------
# secrets
# --------------------------------------------------------------------------


def test_api_key_is_redacted_in_urls() -> None:
    real, safe = oa.build_url(
        "https://api.openalex.org/works",
        {"search": "x", "filter": {"type": "article"}},
        25,
        "someone@example.org",
        "SUPERSECRET",
    )
    check("key: present in the real url", "SUPERSECRET" in real)
    check("key: absent from the redacted url", "SUPERSECRET" not in safe, safe)
    check("key: redaction marker", "api_key=%2A%2A%2A" in safe or "api_key=***" in safe, safe)


def test_api_key_never_reaches_an_output_file() -> None:
    sentinel = "SENTINEL-KEY-DO-NOT-LEAK"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "output"
        result = run_script(
            "--endpoint",
            DEAD_ENDPOINT,
            "--timeout",
            "2",
            "--out",
            str(out),
            env_extra={oa.API_KEY_ENV: sentinel, oa.MAILTO_ENV: "someone@example.org"},
        )
        check("key: run completed", result.returncode == 0, result.stderr)
        for path in sorted(out.rglob("*")):
            if path.is_file():
                check(
                    "key: absent from %s" % path.name,
                    sentinel not in path.read_text(encoding="utf-8", errors="replace"),
                )
        check("key: absent from stdout", sentinel not in result.stdout)
        check("key: absent from stderr", sentinel not in result.stderr)

        log = json.loads((out / "search_log.json").read_text(encoding="utf-8"))
        check("key: presence recorded", log["auth"]["api_key_provided"] is True)
        check("key: mailto not stored", "someone@example.org" not in json.dumps(log))
        check("key: mailto presence recorded", log["auth"]["mailto_provided"] is True)


def test_no_secret_lives_in_the_tracked_files() -> None:
    """A key committed by accident is the failure this whole design avoids."""
    for path in (SCRIPT, STRATEGY, FIXTURE):
        text = path.read_text(encoding="utf-8")
        check(
            "tracked: %s reads the key from the environment only" % path.name,
            "OPENALEX_API_KEY" not in text or "environ" in text or "entorno" in text,
        )


# --------------------------------------------------------------------------


TESTS = [value for name, value in sorted(globals().items()) if name.startswith("test_")]


def main() -> int:
    for test in TESTS:
        test()
    print("PASS %d comprobaciones en %d pruebas, sin red y sin modelo." % (len(passed), len(TESTS)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as error:
        print("FAIL %s" % error, file=sys.stderr)
        sys.exit(1)
