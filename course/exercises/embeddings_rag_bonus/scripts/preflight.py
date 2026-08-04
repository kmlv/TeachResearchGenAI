"""Check every manifest row before paying for a build.

Answers four questions per document: does the file exist, can it be opened, does
the page window carry a *usable* embedded text layer — characters and word
breaks, not just characters — and is an OCR sidecar already cached. A row that is
missing only because the filename was typed from memory gets a suggested
replacement instead of a stack trace.

The pending OCR is reported as two numbers that are never added together: the
pages of the fully scanned works, which is a bill, and the upper bound of the
mixed works, which is not.

    python scripts/preflight.py --books-root "/path/to/99 - Books"
    python scripts/preflight.py --books-root "..." --fix-paths
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import DependencyError, PyPdfError

from common import (
    classify_text_layer,
    combine_text_layers,
    normalize_text,
    ocr_scope,
    page_window,
    rank_path_candidates,
    sample_positions,
    sampled_gap_estimate,
    summarize_ocr_debt,
)
from manifest import list_books, load_manifest, sha256, write_manifest
from ocr import cache_file, load_sidecar


SAMPLE_PAGES = 8
FIX_MIN_RATIO = 0.72
FIX_MIN_MARGIN = 0.05

BLOCKING = {"missing", "damaged", "encrypted", "empty-window"}


def inspect(entry: dict, cache_root: Path, sample: int) -> dict:
    report = {
        "document_id": entry["document_id"],
        "title": entry["title"],
        "category": entry["category"],
        "relative_path": entry["relative_path"],
        "start_page": entry["start_page"],
        "end_page": entry.get("end_page"),
        "max_pages": entry["max_pages"],
        "text_policy": entry["text_policy"],
        "status": "ok",
        "total_pages": None,
        "window_pages": 0,
        "sampled_pages": [],
        "chars_per_page": 0.0,
        "words_per_page": 0.0,
        "chars_per_word": 0.0,
        "text_layer": None,
        "sampled_without_text": 0,
        "sampled_glued": 0,
        "ocr_cached": False,
        "ocr_cached_pages": 0,
        "ocr_missing_pages": 0,
        "ocr_scope": "none",
        "ocr_pages_estimate": 0,
        "sha256": None,
        "detail": "",
        "suggestions": [],
    }
    if not entry["exists"]:
        report["status"] = "missing"
        report["detail"] = "file not found under the books root"
        return report

    try:
        reader = PdfReader(entry["pdf_path"])
        if reader.is_encrypted:
            # An empty user password is common in library copies; a real password
            # is a blocker, not something to guess at.
            if reader.decrypt("") == 0:
                report["status"] = "encrypted"
                report["detail"] = "PDF needs a password"
                return report
        total_pages = len(reader.pages)
    except (PyPdfError, DependencyError, ValueError, OSError) as exc:
        report["status"] = "damaged"
        report["detail"] = f"{type(exc).__name__}: {exc}"
        return report

    report["total_pages"] = total_pages
    report["sha256"] = sha256(entry["pdf_path"])
    report["ocr_cached"] = cache_file(
        cache_root, entry["document_id"], report["sha256"]
    ).is_file()

    pages = page_window(
        total_pages,
        entry["start_page"],
        entry["max_pages"],
        entry.get("end_page"),
    )
    report["window_pages"] = len(pages)
    if not pages:
        report["status"] = "empty-window"
        report["detail"] = (
            f'start_page {entry["start_page"]} is past the last page ({total_pages})'
        )
        return report

    sampled = sample_positions(pages, sample)
    report["sampled_pages"] = sampled
    total_chars = 0
    total_words = 0
    labels: list[str] = []
    for page in sampled:
        try:
            text = normalize_text(reader.pages[page - 1].extract_text() or "")
        except (PyPdfError, DependencyError, ValueError, KeyError) as exc:
            report["status"] = "damaged"
            report["detail"] = f"page {page}: {type(exc).__name__}: {exc}"
            return report
        total_chars += len(text)
        words = len(text.split())
        total_words += words
        # Both counts, not just the characters: a page of glued glyphs has the
        # character count of prose and none of its words.
        labels.append(classify_text_layer(len(text), words))
    report["chars_per_page"] = round(total_chars / len(sampled), 1)
    report["words_per_page"] = round(total_words / len(sampled), 1)
    report["chars_per_word"] = round(total_chars / total_words, 1) if total_words else 0.0
    # Per-page labels, not the average: a book that is digital for three hundred
    # pages and scanned in the middle averages out to "digital" and then fails
    # in class. `combine_text_layers` names that book "mixed" instead.
    report["text_layer"] = combine_text_layers(labels)
    report["sampled_without_text"] = sum(1 for label in labels if label != "digital")
    report["sampled_glued"] = sum(1 for label in labels if label == "glued")

    cached = (
        load_sidecar(cache_root, entry["document_id"], report["sha256"])
        if report["ocr_cached"]
        else {}
    )
    report["ocr_cached_pages"] = len(cached)
    if report["text_layer"] != "digital":
        # Pages of the window that no sidecar covers. On a fully scanned book
        # that is the bill; on a mixed one it is only an upper bound, and
        # `ocr_scope` is what keeps the two from being added together.
        report["ocr_missing_pages"] = sum(1 for page in pages if page not in cached)
    report["ocr_scope"] = ocr_scope(report["text_layer"], report["ocr_missing_pages"])
    if report["ocr_scope"] == "full-scan":
        report["ocr_pages_estimate"] = report["ocr_missing_pages"]
    elif report["ocr_scope"] == "mixed-gaps":
        report["ocr_pages_estimate"] = min(
            report["ocr_missing_pages"],
            sampled_gap_estimate(
                len(pages), len(sampled), report["sampled_without_text"]
            ),
        )

    if report["text_layer"] == "digital":
        report["status"] = "ok"
    elif report["ocr_cached"] and report["ocr_missing_pages"] == 0:
        report["status"] = "ok"
        report["detail"] = (
            f'{report["text_layer"]} text layer, but the OCR sidecar covers all '
            f"{len(pages)} pages of the window"
        )
    else:
        report["status"] = "needs-ocr"
        cached_note = (
            f'; sidecar covers {report["ocr_cached_pages"]} of {len(pages)} '
            f'window pages, {report["ocr_missing_pages"]} still missing'
            if report["ocr_cached"]
            else ""
        )
        scope_note = (
            f'; upper bound {report["ocr_missing_pages"]} window pages, '
            f'sample points to ~{report["ocr_pages_estimate"]} — inspect before OCR'
            if report["ocr_scope"] == "mixed-gaps"
            else ""
        )
        glued_note = (
            f'; {report["sampled_glued"]} sampled page(s) carry characters but no '
            f'word breaks ({report["chars_per_word"]} chars per word) — those '
            "pages index to nothing and only OCR recovers them"
            if report["sampled_glued"]
            else ""
        )
        report["detail"] = (
            f'{report["text_layer"]} text layer: '
            f'{report["sampled_without_text"]} of {len(sampled)} sampled pages '
            f'without usable text, {report["chars_per_page"]} chars/page and '
            f'{report["words_per_page"]} words/page on average'
            f"{cached_note}{scope_note}{glued_note}"
        )
    return report


def suggest_paths(reports: list[dict], books_root: Path) -> None:
    """Attach candidate replacements to every row whose file is missing."""
    if not any(report["status"] == "missing" for report in reports):
        return
    catalogue = list_books(books_root)
    if not catalogue:
        return
    for report in reports:
        if report["status"] != "missing":
            continue
        report["suggestions"] = [
            {"relative_path": path, "ratio": round(ratio, 3)}
            for path, ratio in rank_path_candidates(report["relative_path"], catalogue)
        ]


def apply_path_fixes(entries: list[dict], reports: list[dict]) -> list[dict]:
    """Adopt a suggestion only when it is both strong and unambiguous."""
    by_id = {entry["document_id"]: entry for entry in entries}
    applied: list[dict] = []
    for report in reports:
        candidates = report.get("suggestions") or []
        if report["status"] != "missing" or not candidates:
            continue
        best = candidates[0]
        runner_up = candidates[1]["ratio"] if len(candidates) > 1 else 0.0
        if best["ratio"] < FIX_MIN_RATIO or best["ratio"] - runner_up < FIX_MIN_MARGIN:
            continue
        entry = by_id[report["document_id"]]
        applied.append(
            {
                "document_id": report["document_id"],
                "from": entry["relative_path"],
                "to": best["relative_path"],
                "ratio": best["ratio"],
            }
        )
        entry["relative_path"] = best["relative_path"]
    return applied


def print_table(reports: list[dict]) -> None:
    header = (
        f'{"document_id":<28} {"status":<11} {"layer":<8} {"pages":>6} '
        f'{"chars/pg":>9} {"words/pg":>9}'
    )
    print(header)
    print("-" * len(header))
    for report in reports:
        print(
            f'{report["document_id"]:<28} {report["status"]:<11} '
            f'{report["text_layer"] or "-":<8} {report["window_pages"]:>6} '
            f'{report["chars_per_page"]:>9.1f} {report["words_per_page"]:>9.1f}'
        )
        if report["detail"]:
            print(f'    {report["detail"]}')
        for suggestion in report["suggestions"]:
            print(f'    candidate {suggestion["ratio"]:.3f}: {suggestion["relative_path"]}')


def parse_args() -> argparse.Namespace:
    root = Path(__file__).parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--books-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=root / "manifest.csv")
    parser.add_argument("--cache-root", type=Path, default=root)
    parser.add_argument("--report", type=Path, default=root / "preflight-report.json")
    parser.add_argument("--sample-pages", type=int, default=SAMPLE_PAGES)
    parser.add_argument(
        "--fix-paths",
        action="store_true",
        help="rewrite the manifest when a missing path has one clear match",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="also fail when a document still needs OCR",
    )
    parser.add_argument(
        "--strict-scope",
        choices=("any", "full-scan"),
        default="any",
        help="with --strict, which OCR debt fails the run: any pending page "
        "(default), or only the fully scanned works, whose count is firm. A "
        "mixed book keeps a handful of textless pages forever, so 'any' never "
        "goes green once the batch is done.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries = load_manifest(args.manifest, args.books_root, require_files=False)
    reports = [inspect(entry, args.cache_root, args.sample_pages) for entry in entries]
    suggest_paths(reports, args.books_root)

    if args.fix_paths:
        applied = apply_path_fixes(entries, reports)
        if applied:
            write_manifest(args.manifest, entries)
            print(f"Rewrote {len(applied)} path(s) in {args.manifest.name}:")
            for fix in applied:
                print(f'  {fix["document_id"]}: {fix["to"]} (ratio {fix["ratio"]:.3f})')
            print("Re-run preflight without --fix-paths to inspect the new paths.\n")
        else:
            print("No path was unambiguous enough to fix automatically.\n")

    print_table(reports)

    counts: dict[str, int] = {}
    for report in reports:
        counts[report["status"]] = counts.get(report["status"], 0) + 1
    summary = {
        "documents": len(reports),
        "status_counts": counts,
        "window_pages_total": sum(report["window_pages"] for report in reports),
        "total_pages_total": sum(report["total_pages"] or 0 for report in reports),
        # Kept for readers of the older report, but it adds a measurement to a
        # bound. `ocr_pages_full_scan` is the number to budget against.
        "ocr_pages_pending": sum(report["ocr_missing_pages"] for report in reports),
        **summarize_ocr_debt(reports),
        "mixed_text_layer": [
            report["document_id"] for report in reports if report["text_layer"] == "mixed"
        ],
        "glued_text_layer": [
            report["document_id"] for report in reports if report["text_layer"] == "glued"
        ],
        # Any work with even one glued sampled page, including the mixed ones:
        # this is the list a human has to open, because a character count alone
        # would have called those pages digital.
        "glued_pages_sampled": {
            report["document_id"]: report["sampled_glued"]
            for report in reports
            if report["sampled_glued"]
        },
        "needs_ocr": [
            report["document_id"] for report in reports if report["status"] == "needs-ocr"
        ],
        "blocking": [
            report["document_id"] for report in reports if report["status"] in BLOCKING
        ],
    }
    args.report.write_text(
        json.dumps({"summary": summary, "documents": reports}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"\n{summary['documents']} documents, "
        f"{summary['total_pages_total']} pages on disk, "
        f"{summary['window_pages_total']} pages in window"
    )
    if summary["ocr_pages_full_scan"]:
        print(
            f'OCR to run: {summary["ocr_pages_full_scan"]} pages in '
            f'{len(summary["full_scan_documents"])} fully scanned work(s) — '
            f'{", ".join(summary["full_scan_documents"])}'
        )
    if summary["mixed_gap_documents"]:
        print(
            f'Mixed text layer, {len(summary["mixed_gap_documents"])} work(s): '
            f'{summary["ocr_pages_mixed_upper_bound"]} window pages carry no sidecar, '
            f'but the sample points to about {summary["ocr_pages_mixed_estimate"]}. '
            "Look at those pages before OCRing a mixed work; a blank or a plate "
            "reads as textless and gains nothing from OCR."
        )
        print(f'  {", ".join(summary["mixed_gap_documents"])}')
    if summary["glued_pages_sampled"]:
        print(
            "Defective text layer (characters without word breaks) in "
            f'{len(summary["glued_pages_sampled"])} work(s). Those pages extract '
            "as unreadable strings, produce almost no chunks, and need OCR even "
            "though they are not blank:"
        )
        for document_id, pages in summary["glued_pages_sampled"].items():
            print(f"  {document_id}: {pages} of the sampled pages")
    print(f"Report written to {args.report}")

    if summary["blocking"]:
        print(f'Blocking rows: {", ".join(summary["blocking"])}')
        return 1
    if args.strict:
        offenders = (
            summary["full_scan_documents"]
            if args.strict_scope == "full-scan"
            else summary["needs_ocr"]
        )
        if offenders:
            print(f'Still need OCR: {", ".join(offenders)}')
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
