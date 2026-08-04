"""Manifest loading shared by preflight, OCR and the index build."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from common import TEXT_POLICIES


REQUIRED_COLUMNS = (
    "document_id",
    "title",
    "category",
    "relative_path",
    "start_page",
    "max_pages",
    "text_policy",
)

# Declared by the whole-book manifest, absent from the 70-page pilot manifest.
# `end_page` trims the back matter; `author` and `year` are what the citation
# shown in class is built from.
OPTIONAL_COLUMNS = ("end_page", "author", "year")

# What a manifest writes in `max_pages` to mean "read the whole book".
WHOLE_BOOK_TOKENS = frozenset({"", "-", "0", "all", "todo", "none"})


def parse_page_budget(raw: str, document_id: str) -> int | None:
    """`max_pages` as an int, or None for a whole-book row."""
    value = (raw or "").strip().lower()
    if value in WHOLE_BOOK_TOKENS:
        return None
    try:
        budget = int(value)
    except ValueError as exc:
        raise ValueError(f"{document_id}: max_pages is not a number: {raw!r}") from exc
    if budget < 1:
        raise ValueError(f"{document_id}: max_pages must be positive")
    return budget


def parse_end_page(raw: str, start_page: int, document_id: str) -> int | None:
    """`end_page` as an int, or None for "read to the last page"."""
    value = (raw or "").strip().lower()
    if value in WHOLE_BOOK_TOKENS:
        return None
    try:
        end_page = int(value)
    except ValueError as exc:
        raise ValueError(f"{document_id}: end_page is not a number: {raw!r}") from exc
    if end_page < start_page:
        raise ValueError(f"{document_id}: end_page cannot precede start_page")
    return end_page


def manifest_columns(entries: list[dict]) -> list[str]:
    """Declared columns plus whichever optional ones the file actually used."""
    present = {key for entry in entries for key in entry}
    return list(REQUIRED_COLUMNS) + [c for c in OPTIONAL_COLUMNS if c in present]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_inside(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Manifest path escapes books root: {relative_path}") from exc
    return candidate


def list_books(root: Path) -> list[str]:
    """Every PDF under the books root, as paths relative to that root."""
    return sorted(
        str(path.relative_to(root))
        for path in root.rglob("*.pdf")
        if path.is_file()
    )


def load_manifest(path: Path, books_root: Path, require_files: bool = True) -> list[dict]:
    """Read and validate the manifest.

    `require_files=False` is what preflight uses: it wants to report a missing
    or mistyped path with a suggested replacement, not to crash on the first one.
    """
    entries: list[dict] = []
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        missing_columns = set(REQUIRED_COLUMNS) - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"Manifest is missing columns: {sorted(missing_columns)}")
        has_end_page = "end_page" in (reader.fieldnames or [])
        for row in reader:
            pdf_path = resolve_inside(books_root, row["relative_path"])
            start_page = int(row["start_page"])
            if start_page < 1:
                raise ValueError(f'{row["document_id"]}: start_page is 1-indexed')
            max_pages = parse_page_budget(row["max_pages"], row["document_id"])
            policy = row["text_policy"].strip().lower()
            if policy not in TEXT_POLICIES:
                raise ValueError(
                    f'{row["document_id"]}: text_policy must be one of {TEXT_POLICIES}'
                )
            exists = pdf_path.is_file()
            if require_files and not exists:
                raise FileNotFoundError(pdf_path)
            entry = {
                **row,
                "pdf_path": pdf_path,
                "exists": exists,
                "start_page": start_page,
                "max_pages": max_pages,
                "text_policy": policy,
            }
            if has_end_page:
                entry["end_page"] = parse_end_page(
                    row["end_page"], start_page, row["document_id"]
                )
            entries.append(entry)
    if not entries:
        raise ValueError("Manifest has no rows")
    if len({entry["document_id"] for entry in entries}) != len(entries):
        raise ValueError("document_id values must be unique")
    return entries


def write_manifest(path: Path, entries: list[dict]) -> None:
    """Rewrite the manifest, keeping the declared and optional columns.

    A rewrite must never be a silent downgrade: an author, a year or an
    `end_page` that the file declared has to survive `preflight --fix-paths`.
    """
    columns = manifest_columns(entries)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for entry in entries:
            row = {}
            for key in columns:
                value = entry.get(key)
                row[key] = "" if value is None else value
            writer.writerow(row)
