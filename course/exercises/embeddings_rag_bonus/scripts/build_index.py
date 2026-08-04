"""Build the local index over the manifest corpus.

Every document is processed inside a try/except: one damaged PDF degrades the
corpus by one book instead of destroying a twenty-minute build. Failures, page
counts, chunk counts, hashes and timings are written to a build log so the run
can be reported honestly in class.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
import warnings
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding
from pypdf import PdfReader
from pypdf.errors import DependencyError, PyPdfError

from common import (
    INDEX_SCHEMA,
    document_chunks,
    is_glued_text,
    normalize_text,
    page_ledger_rows,
    page_window,
    unit_rows,
)
from manifest import load_manifest, sha256
from ocr import load_sidecar


DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Under `auto`, how much embedded text is enough to skip the OCR sidecar.
EMBEDDED_MIN_CHARS = 200

warnings.filterwarnings(
    "ignore", message=r"The model .* now uses mean pooling instead of CLS embedding.*"
)


def usable_embedded(text: str) -> bool:
    """Whether `auto` should take the PDF's own text instead of the sidecar.

    Length was the whole test until Holt 2019 arrived with 2,248 characters per
    page glued into three words. That comfortably cleared the length bar and
    indexed to nothing, so the word density has to clear a bar too.
    """
    return len(text) >= EMBEDDED_MIN_CHARS and not is_glued_text(
        len(text), len(text.split())
    )


def page_texts(
    entry: dict, reader: PdfReader, pages: list[int], sidecar: dict[int, str]
) -> tuple[dict[int, str], dict[int, str]]:
    """Text per page under the row's text policy, and where each page came from.

    The origin is returned per page rather than as a total because the page
    ledger needs to name the pages that came from OCR, not just count them.
    """
    policy = entry["text_policy"]
    texts: dict[int, str] = {}
    origins: dict[int, str] = {}
    for page in pages:
        embedded = ""
        if policy != "ocr":
            try:
                embedded = normalize_text(reader.pages[page - 1].extract_text() or "")
            except (PyPdfError, ValueError, KeyError):
                embedded = ""
        if policy == "digital" or (policy == "auto" and len(embedded) >= 200):
            chosen, source = embedded, "pdf"
        else:
            recognised = normalize_text(sidecar.get(page, ""))
            if len(recognised) > len(embedded):
                chosen, source = recognised, "ocr"
            else:
                chosen, source = embedded, "pdf"
        if chosen:
            texts[page] = chosen
            origins[page] = source
    return texts, origins


def blank_record(entry: dict, status: str, error: str = "") -> dict:
    """The build-log row for a document, before anything has been read."""
    return {
        "document_id": entry["document_id"],
        "title": entry["title"],
        "author": entry.get("author", ""),
        "year": entry.get("year", ""),
        "category": entry["category"],
        "relative_path": entry["relative_path"],
        "text_policy": entry["text_policy"],
        "start_page": entry["start_page"],
        "end_page": entry.get("end_page"),
        "status": status,
        "total_pages": None,
        "pages_requested": 0,
        "pages_with_text": 0,
        "pages_from_pdf": 0,
        "pages_from_ocr": 0,
        "chunks": 0,
        "chunks_crossing_pages": 0,
        "characters": 0,
        "sha256": None,
        "seconds": 0.0,
        "error": error,
    }


def extract_document(
    entry: dict, cache_root: Path, chunk_size: int, overlap: int, next_chunk_id: int
) -> tuple[list[dict], dict, list[dict]]:
    """Chunks for one document, its build-log record and its page-ledger rows."""
    started = time.perf_counter()
    record = blank_record(entry, "ok")
    chunks: list[dict] = []
    ledger: list[dict] = []
    try:
        digest = sha256(entry["pdf_path"])
        record["sha256"] = digest
        reader = PdfReader(entry["pdf_path"])
        if reader.is_encrypted and reader.decrypt("") == 0:
            raise PyPdfError("PDF needs a password")
        total_pages = len(reader.pages)
        record["total_pages"] = total_pages
        pages = page_window(
            total_pages,
            entry["start_page"],
            entry["max_pages"],
            entry.get("end_page"),
        )
        record["pages_requested"] = len(pages)
        if not pages:
            raise ValueError(
                f'start_page {entry["start_page"]} is past the last page ({total_pages})'
            )
        sidecar = (
            {}
            if entry["text_policy"] == "digital"
            else load_sidecar(cache_root, entry["document_id"], digest)
        )
        texts, origins = page_texts(entry, reader, pages, sidecar)
        record["pages_with_text"] = len(texts)
        record["pages_from_pdf"] = sum(1 for s in origins.values() if s == "pdf")
        record["pages_from_ocr"] = sum(1 for s in origins.values() if s == "ocr")
        ledger = page_ledger_rows(entry["document_id"], texts, origins)
        for ordinal, piece in enumerate(
            document_chunks(texts, size=chunk_size, overlap=overlap), start=1
        ):
            chunks.append(
                {
                    "chunk_id": next_chunk_id + len(chunks),
                    "document_id": entry["document_id"],
                    "title": entry["title"],
                    "author": entry.get("author", ""),
                    "year": entry.get("year", ""),
                    "category": entry["category"],
                    "page": piece["page_start"],
                    "page_start": piece["page_start"],
                    "page_end": piece["page_end"],
                    "ordinal": ordinal,
                    "relative_path": entry["relative_path"],
                    "sha256": digest,
                    "text": piece["text"],
                }
            )
        record["chunks"] = len(chunks)
        record["chunks_crossing_pages"] = sum(
            1 for chunk in chunks if chunk["page_end"] > chunk["page_start"]
        )
        record["characters"] = sum(len(chunk["text"]) for chunk in chunks)
        if not chunks:
            record["status"] = "skipped"
            record["error"] = "no page produced a usable chunk"
            # Nothing of this document reached the index, so nothing of it
            # belongs in a ledger of indexed pages.
            ledger = []
    except (PyPdfError, DependencyError, ValueError, OSError, KeyError) as exc:
        record["status"] = "failed"
        record["error"] = f"{type(exc).__name__}: {exc}"
        chunks = []
        ledger = []
    record["seconds"] = round(time.perf_counter() - started, 2)
    return chunks, record, ledger


METADATA_COLUMNS = (
    "chunk_id",
    "document_id",
    "title",
    "author",
    "year",
    "category",
    "page",
    "page_start",
    "page_end",
    "relative_path",
    "sha256",
)


def write_sqlite(path: Path, chunks: list[dict]) -> None:
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "CREATE TABLE metadata (chunk_id INTEGER PRIMARY KEY, document_id TEXT, "
            "title TEXT, author TEXT, year TEXT, category TEXT, page INTEGER, "
            "page_start INTEGER, page_end INTEGER, relative_path TEXT, sha256 TEXT)"
        )
        connection.execute(
            "CREATE VIRTUAL TABLE chunks_fts USING fts5(text, chunk_id UNINDEXED)"
        )
        connection.executemany(
            f'INSERT INTO metadata ({", ".join(METADATA_COLUMNS)}) VALUES '
            f'({", ".join("?" * len(METADATA_COLUMNS))})',
            [tuple(c[column] for column in METADATA_COLUMNS) for c in chunks],
        )
        connection.executemany(
            "INSERT INTO chunks_fts(text, chunk_id) VALUES (?, ?)",
            [(c["text"], c["chunk_id"]) for c in chunks],
        )
        connection.commit()
    finally:
        connection.close()


def build_log_markdown(config: dict, records: list[dict]) -> str:
    lines = [
        "# Registro del build",
        "",
        "Generado por `scripts/build_index.py`. Solo metadatos: no contiene texto",
        "de los libros.",
        "",
        f'- Modelo: `{config["model"]}`',
        f'- Manifest: `{config["manifest"]}`',
        f'- Documentos en el manifest: {config["documents_requested"]}',
        f'- Documentos indexados: {config["documents_indexed"]}',
        f'- Páginas con texto: {config["pages_with_text"]}',
        f'- Páginas recuperadas por OCR: {config["pages_from_ocr"]}',
        f'- Fragmentos: {config["chunks"]}',
        f'- Fragmentos que cruzan un salto de página: '
        f'{config["chunks_crossing_pages"]}',
        f'- Dimensiones: {config["dimensions"]}',
        f'- Esquema del índice: {config["schema"]}',
        f'- Fragmentación: {config["chunk_words"]} palabras, '
        f'{config["overlap_words"]} de solapamiento',
        f'- Extracción: {config["extract_seconds"]} s; '
        f'embeddings: {config["embed_seconds"]} s; '
        f'total: {config["total_seconds"]} s',
        "",
        "| document_id | estado | páginas | OCR | fragmentos | cruzan salto | s | sha256 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for record in records:
        digest = (record["sha256"] or "")[:12]
        lines.append(
            f'| {record["document_id"]} | {record["status"]} | '
            f'{record["pages_with_text"]} | {record["pages_from_ocr"]} | '
            f'{record["chunks"]} | {record["chunks_crossing_pages"]} | '
            f'{record["seconds"]} | `{digest}` |'
        )
    failures = [r for r in records if r["status"] != "ok"]
    lines.append("")
    if failures:
        lines.append("## Fallos y omisiones")
        lines.append("")
        for record in failures:
            lines.append(f'- `{record["document_id"]}`: {record["status"]} — {record["error"]}')
    else:
        lines.append(
            f'Sin fallos: las {config["documents_indexed"]} obras del manifest '
            "entraron al índice."
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    root = Path(__file__).parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--books-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=root / "manifest.csv")
    parser.add_argument("--output", type=Path, default=root / "local_index")
    parser.add_argument("--cache-root", type=Path, default=root)
    parser.add_argument("--build-log", type=Path, default=root / "build-log.md")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--chunk-words", type=int, default=320)
    parser.add_argument("--overlap-words", type=int, default=45)
    parser.add_argument("--batch-size", type=int, default=64)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.perf_counter()
    args.output.mkdir(parents=True, exist_ok=True)
    entries = load_manifest(args.manifest, args.books_root, require_files=False)

    chunks: list[dict] = []
    records: list[dict] = []
    ledger: list[dict] = []
    for entry in entries:
        if not entry["exists"]:
            records.append(
                blank_record(entry, "missing", "file not found; run scripts/preflight.py")
            )
            print(f'{entry["document_id"]}: missing, skipped')
            continue
        produced, record, pages_indexed = extract_document(
            entry, args.cache_root, args.chunk_words, args.overlap_words, len(chunks)
        )
        chunks.extend(produced)
        ledger.extend(pages_indexed)
        records.append(record)
        print(
            f'{record["document_id"]}: {record["status"]}, '
            f'{record["pages_with_text"]} pages '
            f'({record["pages_from_ocr"]} via OCR), {record["chunks"]} chunks '
            f'({record["chunks_crossing_pages"]} cross a page break), '
            f'{record["seconds"]}s'
        )
    extract_seconds = round(time.perf_counter() - started, 2)
    if not chunks:
        raise SystemExit("No chunks were extracted; check preflight-report.json")

    embed_started = time.perf_counter()
    model = TextEmbedding(model_name=args.model)
    vectors = np.asarray(
        list(model.embed([chunk["text"] for chunk in chunks], batch_size=args.batch_size)),
        dtype=np.float32,
    )
    vectors = unit_rows(vectors).astype(np.float32)
    np.save(args.output / "embeddings.npy", vectors)
    embed_seconds = round(time.perf_counter() - embed_started, 2)

    with (args.output / "chunks.jsonl").open("w", encoding="utf-8") as stream:
        for chunk in chunks:
            stream.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    write_sqlite(args.output / "search.sqlite", chunks)
    with (args.output / "page_ledger.jsonl").open("w", encoding="utf-8") as stream:
        for row in ledger:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")

    indexed = sorted({chunk["document_id"] for chunk in chunks})
    config = {
        "schema": INDEX_SCHEMA,
        "model": args.model,
        "manifest": args.manifest.name,
        "documents_requested": len(entries),
        "documents_indexed": len(indexed),
        "chunks": len(chunks),
        "chunks_crossing_pages": sum(r["chunks_crossing_pages"] for r in records),
        "dimensions": int(vectors.shape[1]),
        "chunk_words": args.chunk_words,
        "overlap_words": args.overlap_words,
        "pages_with_text": sum(r["pages_with_text"] for r in records),
        "pages_from_pdf": sum(r["pages_from_pdf"] for r in records),
        "pages_from_ocr": sum(r["pages_from_ocr"] for r in records),
        "pages_in_ledger": len(ledger),
        "extract_seconds": extract_seconds,
        "embed_seconds": embed_seconds,
        "total_seconds": round(time.perf_counter() - started, 2),
    }
    (args.output / "index.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.output / "build-log.json").write_text(
        json.dumps({"config": config, "documents": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    args.build_log.write_text(build_log_markdown(config, records), encoding="utf-8")

    failed = [r["document_id"] for r in records if r["status"] != "ok"]
    print(
        f'Index ready: {config["documents_indexed"]}/{config["documents_requested"]} '
        f'documents, {config["pages_with_text"]} pages, {config["chunks"]} chunks '
        f'({config["chunks_crossing_pages"]} cross a page break), '
        f'{config["total_seconds"]}s'
    )
    print(f"Build log: {args.build_log}")
    print(f'Page ledger: {args.output / "page_ledger.jsonl"} ({len(ledger)} pages)')
    if failed:
        print(f'Not indexed: {", ".join(failed)}')
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
