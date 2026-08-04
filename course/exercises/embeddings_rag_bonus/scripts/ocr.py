"""Opt-in OCR for scanned PDFs, cached outside Git.

Nothing here runs during a normal build. Preflight decides which documents have
no text layer; this script renders only those pages and stores the recognised
text in `ocr_cache/`, which `.gitignore` excludes. Book text never reaches the
repository.

Requires two external binaries, installed by the facilitator:

    brew install poppler tesseract tesseract-lang
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from common import page_window, safe_cache_name
from manifest import load_manifest, sha256


CACHE_DIRNAME = "ocr_cache"
DEFAULT_DPI = 300
DEFAULT_LANG = "eng"

# A whole scanned book is an hour-long batch; silence for an hour is not a
# progress report.
PROGRESS_EVERY = 25


def cache_dir(root: Path) -> Path:
    return root / CACHE_DIRNAME


def cache_file(root: Path, document_id: str, digest: str) -> Path:
    return cache_dir(root) / safe_cache_name(document_id, digest)


def load_sidecar(root: Path, document_id: str, digest: str) -> dict[int, str]:
    """Recognised text for one document, keyed by 1-indexed page number."""
    path = cache_file(root, document_id, digest)
    if not path.is_file():
        return {}
    pages: dict[int, str] = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            pages[int(record["page"])] = record["text"]
    return pages


def write_sidecar(root: Path, document_id: str, digest: str, pages: dict[int, str]) -> Path:
    path = cache_file(root, document_id, digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for page in sorted(pages):
            stream.write(
                json.dumps({"page": page, "text": pages[page]}, ensure_ascii=False) + "\n"
            )
    return path


def missing_binaries() -> list[str]:
    return [name for name in ("pdftoppm", "tesseract") if shutil.which(name) is None]


def ocr_page(pdf_path: Path, page: int, dpi: int, lang: str) -> str:
    """Render one page to an image in a temp directory and recognise it."""
    with tempfile.TemporaryDirectory(prefix="ocr-bonus-") as workdir:
        prefix = Path(workdir) / "page"
        subprocess.run(
            [
                "pdftoppm", "-f", str(page), "-l", str(page),
                "-r", str(dpi), "-png", "-singlefile",
                str(pdf_path), str(prefix),
            ],
            check=True,
            capture_output=True,
        )
        image = prefix.with_suffix(".png")
        if not image.is_file():
            raise RuntimeError(f"pdftoppm produced no image for page {page}")
        completed = subprocess.run(
            ["tesseract", str(image), "stdout", "-l", lang],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout


def parse_args() -> argparse.Namespace:
    root = Path(__file__).parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--books-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=root / "manifest.csv")
    parser.add_argument("--cache-root", type=Path, default=root)
    parser.add_argument(
        "--only",
        default="",
        help="comma-separated document_id list; default is every row with text_policy=ocr",
    )
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    parser.add_argument("--lang", default=DEFAULT_LANG)
    parser.add_argument("--force", action="store_true", help="re-OCR even if cached")
    parser.add_argument(
        "--limit-pages",
        type=int,
        default=0,
        help="stop after this many pages per document; 0 means no limit. A capped "
        "run leaves a partial sidecar that a later run completes.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries = load_manifest(args.manifest, args.books_root)
    wanted = {item.strip() for item in args.only.split(",") if item.strip()}
    if wanted:
        unknown = wanted - {entry["document_id"] for entry in entries}
        if unknown:
            raise SystemExit(f"Unknown document_id values: {sorted(unknown)}")
        selected = [entry for entry in entries if entry["document_id"] in wanted]
    else:
        selected = [entry for entry in entries if entry["text_policy"] == "ocr"]

    if not selected:
        print("Nothing to OCR: no row has text_policy=ocr and --only was empty.")
        return 0

    missing = missing_binaries()
    if missing and not args.dry_run:
        raise SystemExit(
            f"Missing external tools: {', '.join(missing)}. "
            "Install them with: brew install poppler tesseract tesseract-lang"
        )

    from pypdf import PdfReader

    for entry in selected:
        digest = sha256(entry["pdf_path"])
        reader = PdfReader(entry["pdf_path"])
        pages = page_window(
            len(reader.pages),
            entry["start_page"],
            entry["max_pages"],
            entry.get("end_page"),
        )
        if not pages:
            print(
                f'{entry["document_id"]}: start_page {entry["start_page"]} is past '
                f"the last page ({len(reader.pages)}), skipping"
            )
            continue
        # The cache is keyed by document and file hash, not by page range, so a
        # sidecar written for a 70-page pilot window would otherwise be reused
        # as if it covered the whole book. Recognise the gap and fill it: the
        # pages already paid for stay paid for.
        cached = {} if args.force else load_sidecar(
            args.cache_root, entry["document_id"], digest
        )
        todo = [page for page in pages if page not in cached]
        if args.limit_pages > 0:
            todo = todo[: args.limit_pages]
        if not todo:
            print(
                f'{entry["document_id"]}: sidecar already covers all {len(pages)} '
                "pages of the window, skipping"
            )
            continue
        print(
            f'{entry["document_id"]}: {len(todo)} pages to recognise of '
            f'{len(pages)} in the window (p. {pages[0]}–{pages[-1]}), '
            f"{len(cached)} already cached, {args.dpi} dpi"
        )
        if args.dry_run:
            continue
        started = time.perf_counter()
        recognised: dict[int, str] = dict(cached)
        failures = 0
        for done, page in enumerate(todo, start=1):
            try:
                recognised[page] = ocr_page(entry["pdf_path"], page, args.dpi, args.lang)
            except (subprocess.CalledProcessError, RuntimeError) as exc:
                failures += 1
                print(f'  page {page} failed: {type(exc).__name__}')
            if done % PROGRESS_EVERY == 0 and done < len(todo):
                elapsed = time.perf_counter() - started
                remaining = (len(todo) - done) * elapsed / done
                print(
                    f"  {done}/{len(todo)} pages, {elapsed / 60:.1f} min elapsed, "
                    f"~{remaining / 60:.1f} min left"
                )
        if not recognised:
            print(f'  {entry["document_id"]}: no page could be recognised')
            continue
        path = write_sidecar(
            args.cache_root, entry["document_id"], digest, recognised
        )
        elapsed = time.perf_counter() - started
        chars = sum(len(text) for text in recognised.values())
        print(
            f"  wrote {path.name}: {len(recognised)} pages cached in total "
            f"({len(todo) - failures} new, {failures} failed), {chars} chars, "
            f"{elapsed:.1f}s"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
