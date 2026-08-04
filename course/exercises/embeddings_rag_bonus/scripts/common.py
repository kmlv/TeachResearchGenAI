from __future__ import annotations

import difflib
import re
from collections.abc import Iterable, Mapping, Sequence

import numpy as np


WORD_RE = re.compile(r"\w+", flags=re.UNICODE)
SAFE_ID_RE = re.compile(r"[^a-z0-9-]+")

TEXT_POLICIES = ("digital", "auto", "ocr")

# Below this a fragment is a caption or a stray line, not a passage worth
# embedding. It is the floor for a whole chunk, not for a page: a 30-word page
# that used to disappear now contributes its words to the chunk around it.
MIN_CHUNK_WORDS = 40

# Version of the on-disk index layout. 2 added `author`, `year` and the
# `page_start`/`page_end` range of every chunk; an index built before it lacks
# those keys and has to be rebuilt rather than read.
INDEX_SCHEMA = 2

# Where the text of an indexed page came from.
PAGE_SOURCES = ("pdf", "ocr")

# A page of a digital textbook carries well over a thousand characters; a scanned
# page usually yields a handful of stray glyphs. The middle band is reported as
# "sparse" so a human decides instead of the script guessing.
DIGITAL_MIN_CHARS = 180.0
SCANNED_MAX_CHARS = 25.0

# Characters alone are not enough. A page can carry thousands of them and still
# be unreadable: Holt 2019 extracts as `Chapter12asbeingrelevant…`, so 2,248
# characters collapse into three "words". Counting characters called that page
# digital, the preflight called the book mixed at 1,904 chars/page, and the build
# then produced fifteen chunks for 683 pages of text before anyone noticed.
#
# Two signals together, never one alone: too few words for a page of prose, and
# characters per word far outside what prose produces. Measured over the
# 2026-08-04 corpus of eighteen works, the seventeen sound books sit at 5.2-6.7
# characters per word and 339-833 words per page; Holt sits at 779 and 6. The
# thresholds are an order of magnitude away from both sides of that gap.
GLUED_MAX_WORDS_PER_PAGE = 40.0
GLUED_MIN_CHARS_PER_WORD = 25.0

# Document labels that mean "not one sampled page had a usable text layer".
# `glued` is one of them: the glyphs are there, the words are not, and only OCR
# recovers them.
FULL_SCAN_LAYERS = frozenset({"scanned", "sparse", "glued"})

# Every label a sampled page can take, worst-first for the tie-break in
# `combine_text_layers`.
PAGE_LAYERS = ("digital", "scanned", "glued", "sparse")


def normalize_text(text: str) -> str:
    """Collapse PDF whitespace without destroying words or punctuation."""
    text = text.replace("\x00", " ")
    text = re.sub(r"(?<=\w)-\s+(?=\w)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def chunk_word_spans(
    words: Sequence[str], size: int = 320, overlap: int = 45
) -> list[tuple[int, int]]:
    """Half-open `[start, end)` word ranges covering a document.

    Returning ranges instead of strings is what lets the caller remember where
    each word came from: the same spans that produce the text also produce the
    page range printed under the citation.
    """
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Require size > overlap >= 0")
    total = len(words)
    if total < MIN_CHUNK_WORDS:
        return []
    spans: list[tuple[int, int]] = []
    step = size - overlap
    for start in range(0, total, step):
        end = min(start + size, total)
        if end - start < MIN_CHUNK_WORDS:
            break
        spans.append((start, end))
        if start + size >= total:
            break
    return spans


def chunk_words(text: str, size: int = 320, overlap: int = 45) -> list[str]:
    """Chunks of one block of text. Unchanged behaviour; now a thin wrapper."""
    words = text.split()
    return [" ".join(words[start:end]) for start, end in chunk_word_spans(words, size, overlap)]


def document_chunks(
    page_texts: Mapping[int, str], size: int = 320, overlap: int = 45
) -> list[dict]:
    """Chunks for one document, cut over its pages joined in reading order.

    Chunking page by page splits every paragraph that crosses a page break into
    two halves, and neither half retrieves well because neither states the whole
    idea. Over seventy pilot pages that is an annoyance; over a 900-page book it
    happens at nearly every break. Joining the pages first and remembering which
    page each word came from keeps the paragraph intact and still cites a page
    range instead of a vague "somewhere in this book".

    Known limitation, and the reason `full-books-runbook.md` §9 asks for a human
    look before this is trusted: a running head or a page number sitting at a
    page edge used to land at the edge of a chunk, where it was harmless. Joined
    text can leave it in the middle of a sentence.
    """
    words: list[str] = []
    pages: list[int] = []
    for page in sorted(page_texts):
        page_words = page_texts[page].split()
        words.extend(page_words)
        pages.extend([page] * len(page_words))
    return [
        {
            "text": " ".join(words[start:end]),
            "words": end - start,
            "page_start": pages[start],
            "page_end": pages[end - 1],
        }
        for start, end in chunk_word_spans(words, size, overlap)
    ]


def page_ledger_rows(
    document_id: str, page_texts: Mapping[int, str], origins: Mapping[int, str]
) -> list[dict]:
    """One row per indexed page: which page, where its text came from, how much.

    Two concrete uses. A citation that reads strangely in class can be checked
    against `source`: OCR of a scanned page invents plausible words, an embedded
    text layer does not. And after an OCR batch the ledger says how many pages it
    actually added, instead of the count of pages it was asked to try.

    Counts only, never text, so the file stays a metadata artefact.
    """
    rows: list[dict] = []
    for page in sorted(page_texts):
        source = origins.get(page)
        if source is None:
            raise ValueError(f"{document_id}: page {page} has text but no recorded source")
        if source not in PAGE_SOURCES:
            raise ValueError(f"{document_id}: page {page} has unknown source {source!r}")
        text = page_texts[page]
        rows.append(
            {
                "document_id": document_id,
                "page": page,
                "source": source,
                "characters": len(text),
                "words": len(text.split()),
            }
        )
    return rows


def index_schema_error(config: Mapping) -> str | None:
    """Message asking for a rebuild, or None when the index matches this code.

    Without this the mismatch surfaces as a `KeyError: 'page_start'` from inside
    a result loop, which is a bad thing to read in front of a room.
    """
    found = config.get("schema", 1)
    if found == INDEX_SCHEMA:
        return None
    return (
        f"El índice en disco declara esquema {found} y este código espera el "
        f"{INDEX_SCHEMA} (author, year y rango de páginas por fragmento). "
        "Reconstruilo con scripts/build_index.py: tarda minutos y no vuelve a "
        "pedir OCR, porque reutiliza lo que ya está en ocr_cache/."
    )


def format_page_range(page_start: int, page_end: int) -> str:
    """`p. 84` for a chunk inside one page, `pp. 84–85` for one that crosses."""
    if page_end < page_start:
        raise ValueError("page_end cannot precede page_start")
    if page_end == page_start:
        return f"p. {page_start}"
    return f"pp. {page_start}–{page_end}"


def format_citation(author: str, year: str, title: str) -> str:
    """What the class reads under a result.

    The manifest declares `author` and `year` for the whole-book corpus and not
    for the pilot, so both shapes have to render without looking broken.
    """
    author = (author or "").strip()
    year = str(year or "").strip()
    if author and year:
        return f"{author} ({year}), {title}"
    if author:
        return f"{author}, {title}"
    return title


def unit_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(norms, 1e-12)


def query_terms(query: str) -> str:
    """Create a safe, broad SQLite FTS5 OR query."""
    tokens = [t.lower() for t in WORD_RE.findall(query) if len(t) > 2]
    return " OR ".join(f'"{t}"' for t in dict.fromkeys(tokens))


def reciprocal_rank_fusion(
    rankings: Iterable[list[int]], k: int = 60
) -> dict[int, float]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return scores


def page_window(
    total_pages: int,
    start_page: int,
    max_pages: int | None = None,
    end_page: int | None = None,
) -> list[int]:
    """Return the 1-indexed pages to read, skipping front matter.

    `start_page` lets the manifest jump over covers, prefaces and tables of
    contents, which otherwise dominate the top-k with front matter noise.
    `end_page` cuts the back matter: an analytical index is a bag of keywords
    that lexical search loves and that answers nothing. `max_pages=None` means
    "read to the end", which is what a whole-book row declares.
    """
    if total_pages < 0:
        raise ValueError("total_pages cannot be negative")
    if start_page < 1:
        raise ValueError("start_page is 1-indexed and must be >= 1")
    if max_pages is not None and max_pages <= 0:
        raise ValueError("max_pages must be positive")
    if end_page is not None and end_page < start_page:
        raise ValueError("end_page cannot precede start_page")
    if start_page > total_pages:
        return []
    last = total_pages
    if end_page is not None:
        last = min(last, end_page)
    if max_pages is not None:
        last = min(last, start_page + max_pages - 1)
    return list(range(start_page, last + 1))


def sample_positions(pages: Sequence[int], sample: int) -> list[int]:
    """Evenly spaced pages from a window, always including both ends."""
    if not pages or sample < 1:
        return []
    if len(pages) <= sample:
        return list(pages)
    step = (len(pages) - 1) / (sample - 1)
    picked = {pages[round(index * step)] for index in range(sample)}
    return sorted(picked)


def is_glued_text(characters: float, words: float) -> bool:
    """True when extracted text has the characters of prose but not its words.

    Only ever consulted for text that is long enough to look digital; below that
    the character count already says "scanned" or "sparse" and this adds nothing.
    """
    if min(characters, words) < 0:
        raise ValueError("character and word counts cannot be negative")
    if characters < DIGITAL_MIN_CHARS or words >= GLUED_MAX_WORDS_PER_PAGE:
        return False
    if words == 0:
        return True
    return characters / words > GLUED_MIN_CHARS_PER_WORD


def classify_text_layer(chars_per_page: float, words_per_page: float | None = None) -> str:
    """Label a PDF as digital, glued, scanned or sparse from its extracted text.

    `words_per_page` is optional so that a caller with only a character count
    keeps the old three-way answer; a caller that passes both gets the defective
    layer named instead of read as digital.
    """
    if chars_per_page < 0:
        raise ValueError("chars_per_page cannot be negative")
    if words_per_page is not None and is_glued_text(chars_per_page, words_per_page):
        return "glued"
    if chars_per_page >= DIGITAL_MIN_CHARS:
        return "digital"
    if chars_per_page <= SCANNED_MAX_CHARS:
        return "scanned"
    return "sparse"


def combine_text_layers(labels: Sequence[str]) -> str:
    """One label for a document from the labels of its sampled pages.

    A whole book is not uniform: a volume can carry a clean text layer for three
    hundred pages and then a scanned plate section in the middle. Averaging
    characters per page hides exactly that case, so the mixed books are named
    instead of being rounded into "digital" and discovered mid-class.

    When no page is digital the majority label wins, so a book that is glued
    from cover to cover is reported as glued even if one sampled page happened
    to come back empty. Ties keep the older order, scanned before sparse.
    """
    unique = set(labels)
    if not unique:
        raise ValueError("no page labels to combine")
    unknown = unique - set(PAGE_LAYERS)
    if unknown:
        raise ValueError(f"unknown text layer labels: {sorted(unknown)}")
    if unique == {"digital"}:
        return "digital"
    if "digital" in unique:
        return "mixed"
    ranked = [label for label in PAGE_LAYERS if label != "digital"]
    return max(
        ranked, key=lambda label: (labels.count(label), -ranked.index(label))
    )


def ocr_scope(text_layer: str | None, missing_pages: int) -> str:
    """How firm the OCR bill of one document is.

    Two books can report the same number of window pages absent from the OCR
    cache and mean entirely different things by it:

    - ``full-scan``: no sampled page carried a usable text layer — none at all,
      or one glued into unreadable strings — so every page the sidecar does not
      cover really has to be recognised. The number is firm.
    - ``mixed-gaps``: some sampled pages carried text and some did not. The
      pages without a sidecar are an upper bound, and usually a wildly
      pessimistic one: a blank, a plate or an end page reads as "no text" and
      gains nothing from OCR. Those pages get looked at, not recognised.
    - ``none``: nothing pending.

    Adding the two together is what made the first whole-book preflight quote
    an OCR batch three times larger than the one actually pending.
    """
    if missing_pages < 0:
        raise ValueError("missing_pages cannot be negative")
    if missing_pages == 0 or text_layer is None or text_layer == "digital":
        return "none"
    if text_layer in FULL_SCAN_LAYERS:
        return "full-scan"
    if text_layer == "mixed":
        return "mixed-gaps"
    raise ValueError(f"unknown text layer: {text_layer!r}")


def sampled_gap_estimate(
    window_pages: int, sampled_pages: int, pages_without_text: int
) -> int:
    """Scale "sampled pages without text" up to the whole window.

    An estimate, and labelled as one everywhere it is printed: the sample says
    what share of the window looks textless, not which pages those are.
    """
    if min(window_pages, sampled_pages, pages_without_text) < 0:
        raise ValueError("page counts cannot be negative")
    if pages_without_text > sampled_pages:
        raise ValueError("more pages without text than pages sampled")
    if not window_pages or not sampled_pages:
        return 0
    return min(window_pages, round(window_pages * pages_without_text / sampled_pages))


def summarize_ocr_debt(reports: Sequence[dict]) -> dict:
    """Split the pending OCR into the part that is measured and the part bounded.

    Takes the per-document rows of the preflight report; returns the totals the
    facilitator needs before authorising a batch. The two page counts are never
    added into one headline number, because only the first one is a bill.
    """
    full_scan = [r for r in reports if r.get("ocr_scope") == "full-scan"]
    mixed = [r for r in reports if r.get("ocr_scope") == "mixed-gaps"]
    return {
        "ocr_pages_full_scan": sum(r["ocr_missing_pages"] for r in full_scan),
        "ocr_pages_mixed_upper_bound": sum(r["ocr_missing_pages"] for r in mixed),
        "ocr_pages_mixed_estimate": sum(r["ocr_pages_estimate"] for r in mixed),
        "full_scan_documents": [r["document_id"] for r in full_scan],
        "mixed_gap_documents": [r["document_id"] for r in mixed],
    }


def match_key(path_or_title: str) -> str:
    """Lowercase alphanumeric signature used to match manifest rows to files."""
    stem = path_or_title.rsplit("/", 1)[-1]
    stem = re.sub(r"\.pdf$", "", stem, flags=re.IGNORECASE)
    return " ".join(WORD_RE.findall(stem.lower()))


def rank_path_candidates(
    declared_path: str, candidates: Sequence[str], limit: int = 3
) -> list[tuple[str, float]]:
    """Best-guess replacements for a manifest path that does not exist on disk.

    Returns `(candidate, ratio)` pairs sorted by descending similarity so the
    preflight report can propose a fix instead of failing with a bare
    FileNotFoundError.
    """
    target = match_key(declared_path)
    scored = [
        (candidate, difflib.SequenceMatcher(None, target, match_key(candidate)).ratio())
        for candidate in candidates
    ]
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return scored[:limit]


def safe_cache_name(document_id: str, sha256: str) -> str:
    """Filename for an OCR sidecar that cannot escape the cache directory."""
    slug = SAFE_ID_RE.sub("-", document_id.lower()).strip("-")
    if not slug:
        raise ValueError("document_id has no usable characters")
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("sha256 must be a 64-character hex digest")
    return f"{slug}.{sha256[:12]}.jsonl"


def diversify(
    ordered_ids: Iterable[int], metadata: list[dict], limit: int, per_document: int = 2
) -> list[int]:
    selected: list[int] = []
    seen: dict[str, int] = {}
    for chunk_id in ordered_ids:
        doc_id = metadata[chunk_id]["document_id"]
        if seen.get(doc_id, 0) >= per_document:
            continue
        selected.append(chunk_id)
        seen[doc_id] = seen.get(doc_id, 0) + 1
        if len(selected) == limit:
            break
    return selected


# --------------------------------------------------------------------------
# Answer layer.
#
# Everything below serves `answer.py` and `serve.py`. It lives here, next to
# the retrieval helpers, because it is all pure: no model, no index, no
# network. That is what lets `test_core.py` check the abstention rule and the
# citation contract without a virtualenv.
# --------------------------------------------------------------------------

# A citation marker in a generated answer: `[1]`, `[12]`. Nothing else counts,
# so a model that writes "(Camerer 2003)" fails the check instead of passing it
# by looking like a citation.
CITATION_RE = re.compile(r"\[(\d+)\]")

# Sentence boundary for the extractive answer. Deliberately blunt: the corpus is
# academic prose with abbreviations ("e.g.", "Fig. 3") that a regex will split
# wrongly now and then. A slightly short quote is a cosmetic problem; the page
# range under it is what the class verifies, and that stays correct.
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡\"“«])")

# What `answer-calibration.json` has to declare before `answer.py` will run.
CALIBRATION_KEYS = ("mode", "model", "min_top_score", "answerable", "unanswerable")

# The sentence a synthesising model is required to be able to produce, and the
# one the extractive path prints when the evidence is too weak. Fixed text so
# the browser, the terminal and the tests all recognise the same abstention.
ABSTAIN_SENTENCE = (
    "La evidencia recuperada no alcanza para responder esta pregunta con este corpus."
)

# A quoted sentence is cut here. Two reasons, both hard rules of this exercise.
# The demo transcript is committed, and the books are not ours to redistribute:
# a citation is a pointer to a page, not a reproduction of it. And a quote long
# enough to stand alone invites reading the answer instead of the source, which
# is the habit this lab exists to break.
MAX_QUOTE_WORDS = 40

# What the class sees before a single word of any book leaves the laptop. Shown
# by the terminal and the browser, and repeated in the payload disclosure, so
# nobody discovers after the fact that the "local" demo made a network call.
CONSENT_WARNING = (
    "AVISO: el modo claude_cli envía los fragmentos seleccionados a la API de "
    "Anthropic. Los excerptos salen de esta laptop. El resto del corpus, los "
    "PDFs y el índice no se envían. Sin consentimiento explícito el demo "
    "responde en modo extractivo, que es totalmente local."
)


def split_sentences(text: str) -> list[str]:
    """Sentences of a retrieved passage, in order, without empties."""
    return [piece.strip() for piece in SENTENCE_SPLIT_RE.split(text.strip()) if piece.strip()]


def citation_markers(text: str) -> list[int]:
    """Every `[n]` in an answer, in order of appearance, duplicates included."""
    return [int(match.group(1)) for match in CITATION_RE.finditer(text)]


def citation_problems(answer: str, source_count: int, require_citation: bool = True) -> list[str]:
    """Why an answer fails the deck's citation contract, or an empty list.

    The three conditions stated on the "Cuándo empieza RAG" slide, checked
    mechanically:

    1. every answer carries citations (unless it abstains, hence the flag);
    2. every `[n]` points at a passage that was actually put on the table —
       this is the one that catches a model citing a source it invented;
    3. the sources are numbered from 1, so `[0]` is a bug, not a citation.

    What it cannot check is whether the cited passage supports the sentence. No
    program checks that. A person opens the PDF at the page range printed under
    the answer.
    """
    if source_count < 0:
        raise ValueError("source_count cannot be negative")
    markers = citation_markers(answer)
    problems: list[str] = []
    if require_citation and not markers:
        problems.append("La respuesta no cita ninguna fuente.")
    out_of_range = sorted({n for n in markers if n < 1 or n > source_count})
    if out_of_range:
        problems.append(
            "La respuesta cita fuentes que no se le entregaron: "
            + ", ".join(f"[{n}]" for n in out_of_range)
            + f" (se entregaron {source_count})."
        )
    return problems


def abstention_statistic(results: Sequence[Mapping]) -> float:
    """The number the abstention rule compares against its threshold.

    The best dense similarity among the retrieved passages, not the fused score.
    Two reasons. Cosine similarity is comparable across queries, which is what a
    fixed threshold needs; the RRF score is not, since it only encodes agreement
    between two rankings and lands in the same narrow band whether the corpus
    answered the question or not. And it is the one number `calibrate_answer.py`
    measures, so the threshold and the statistic are the same quantity by
    construction rather than by hope.
    """
    return max((float(result["dense_score"]) for result in results), default=0.0)


def abstention_verdict(statistic: float, calibration: Mapping) -> dict:
    """Whether to answer, with the measurement that decided it.

    Returns the threshold and the margin as well as the verdict, because the
    demo shows them: a rule the class cannot see the inputs of is exactly the
    unexplained constant this exercise argues against.
    """
    threshold = float(calibration["min_top_score"])
    return {
        "answer": statistic >= threshold,
        "statistic": round(statistic, 4),
        "threshold": round(threshold, 4),
        "margin": round(statistic - threshold, 4),
        "separable": bool(calibration.get("separable", True)),
    }


def calibration_error(calibration: Mapping, mode: str, model: str) -> str | None:
    """Message explaining how to produce a usable calibration, or None.

    `answer.py` refuses to guess a threshold. A missing or mismatched
    calibration is an instruction to run one command, not a crash.
    """
    missing = [key for key in CALIBRATION_KEYS if key not in calibration]
    if missing:
        return (
            f"answer-calibration.json no declara {', '.join(missing)}. "
            "Regeneralo con scripts/calibrate_answer.py --write."
        )
    if calibration["mode"] != mode:
        return (
            f"La calibración se midió en modo {calibration['mode']!r} y se está "
            f"respondiendo en modo {mode!r}. El umbral solo es válido para el modo "
            "en que se midió: volvé a correr calibrate_answer.py --mode "
            f"{mode} --write."
        )
    if calibration["model"] != model:
        return (
            f"La calibración se midió con {calibration['model']} y el índice usa "
            f"{model}. Otro modelo, otra escala de similitud: volvé a correr "
            "calibrate_answer.py --write."
        )
    return None


def calibrated_threshold(answerable_min: float, unanswerable_max: float) -> dict:
    """Turn two measured distributions into the abstention threshold.

    When the worst question with audited evidence scores above the best question
    about something the corpus does not discuss, there is a gap and the
    threshold goes in the middle of it. When the two overlap there is no
    threshold that separates them, and the honest move is to say so rather than
    to pick a number that looks decisive: the fallback sits at the answerable
    minimum, which abstains on part of the overlap, and `separable` is false so
    every surface can print the caveat.
    """
    gap = answerable_min - unanswerable_max
    if gap > 0:
        return {
            "min_top_score": round((answerable_min + unanswerable_max) / 2, 4),
            "gap": round(gap, 4),
            "separable": True,
        }
    return {
        "min_top_score": round(answerable_min, 4),
        "gap": round(gap, 4),
        "separable": False,
    }


# A quote shorter than this is a heading, a running head or half a formula. It
# can score well — short strings match short queries — and it supports nothing.
MIN_QUOTE_WORDS = 8


def is_evidence_sentence(sentence: str) -> bool:
    """Whether a sentence can serve as evidence, as opposed to merely matching.

    Embedding similarity rewards sentences that look like the question, and the
    sentence that looks most like a question is a question. Asked about System
    1 and System 2, the top-scoring sentence in Kahneman was "Why call them
    System 1 and System 2 …?" — a perfect lexical mirror of the query that
    answers none of it. Interrogatives and fragments are set aside while any
    declarative sentence remains; if a passage is nothing but those, the best
    of them is still quoted rather than dropping the source silently.
    """
    text = sentence.strip()
    if len(text.split()) < MIN_QUOTE_WORDS:
        return False
    return not text.endswith("?")


def clip_quote(sentence: str, max_words: int = MAX_QUOTE_WORDS) -> str:
    """A quotable fragment: whitespace collapsed, cut at `max_words`.

    The ellipsis is part of the contract, not decoration. It tells the reader
    that what they have is a pointer into a page, and that the sentence
    continues in the book.
    """
    if max_words < 1:
        raise ValueError("max_words must be positive")
    words = sentence.split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]) + " …"


def quote_is_grounded(quote: str, chunk_text: str) -> bool:
    """True when `quote` is a verbatim fragment of the passage it cites.

    The extractive path builds its quotes by cutting a retrieved passage, so
    this should always hold; it is checked anyway because "should always hold"
    is how ungrounded text reaches a slide. Comparison ignores whitespace only:
    a paraphrase, a translation or an invented sentence all fail.
    """
    needle = " ".join(quote.replace("…", " ").split())
    haystack = " ".join(chunk_text.split())
    return bool(needle) and needle in haystack


def format_source_line(number: int, result: Mapping) -> str:
    """`[n] Autor (año), Título — pp. 84–85 — ruta/relativa.pdf`.

    The path is there so the verification step is mechanical: the reader does
    not search for the book, they open that file at that page.
    """
    if number < 1:
        raise ValueError("sources are numbered from 1")
    return (
        f"[{number}] {result['citation']} — {result['pages']} — "
        f"{result['relative_path']}"
    )


def extractive_answer(picks: Sequence[Mapping]) -> str:
    """Compose the offline answer from passages already chosen and clipped.

    Spanish scaffolding around literal quotes. The scaffolding is what makes
    the answer readable; the quotes are what makes it checkable. Nothing here
    rewrites, translates or summarises a book — the corpus is in English and
    this mode says so rather than inventing a Spanish sentence no source
    supports.
    """
    if not picks:
        raise ValueError("an extractive answer needs at least one passage")
    body = "\n\n".join(
        f"«{pick['quote']}» [{pick['number']}]" for pick in picks
    )
    return (
        "Respuesta extractiva (sin modelo generativo, todo local). Los pasajes "
        "recuperados dicen, literalmente:\n\n"
        f"{body}\n\n"
        "Las citas son literales y están en el idioma del libro; este modo no "
        "traduce ni redacta. Verificá cada [n] abriendo el PDF en las páginas "
        "indicadas."
    )


def excerpt_disclosure(picks: Sequence[Mapping]) -> str:
    """Exactly what would leave the laptop, counted before it leaves.

    Consent to "send the excerpts" means nothing if the person consenting
    cannot see how much text that is and where it came from. This is the line
    printed next to the warning, and it is computed from the payload itself so
    it cannot drift from what is actually sent.
    """
    if not picks:
        return "No hay fragmentos seleccionados: no se enviaría nada."
    words = sum(len(pick["quote"].split()) for pick in picks)
    books = sorted({pick["citation"] for pick in picks})
    listed = "; ".join(books)
    return (
        f"Se enviarían {len(picks)} fragmentos ({words} palabras en total) "
        f"de {len(books)} obra(s): {listed}."
    )


def synthesis_prompt(question: str, picks: Sequence[Mapping]) -> str:
    """The whole payload sent to the model, built from the clipped quotes only.

    Two properties this function exists to guarantee, both covered by tests:
    the model receives the numbered passages and nothing else from the corpus,
    and it is told in the prompt that abstaining is a valid answer. A model
    that cannot say "no sé" will always find something to say.
    """
    if not picks:
        raise ValueError("a synthesis prompt needs at least one passage")
    passages = "\n\n".join(
        f"[{pick['number']}] {pick['citation']} — {pick['pages']}\n{pick['quote']}"
        for pick in picks
    )
    return (
        "Sos un asistente de investigación. Respondé en español, en un párrafo "
        "breve, usando ÚNICAMENTE los pasajes numerados que siguen.\n\n"
        "Reglas estrictas:\n"
        "1. Cada afirmación lleva su marcador [n] del pasaje que la sostiene.\n"
        "2. No cites números de pasaje que no aparezcan abajo.\n"
        "3. No agregues datos, autores, cifras ni ejemplos que no estén en los "
        "pasajes.\n"
        f"4. Si los pasajes no alcanzan, respondé exactamente: {ABSTAIN_SENTENCE}\n\n"
        f"Pregunta: {question}\n\n"
        f"Pasajes:\n{passages}\n"
    )


def synthesis_problems(answer: str, picks: Sequence[Mapping]) -> list[str]:
    """Why a synthesised answer cannot be shown, or an empty list.

    The generated path is the only one where text arrives that no one on this
    laptop wrote, so it is the only one that needs a gate. An answer that
    abstains is allowed to carry no citations; anything else has to cite, and
    every marker has to point at a passage that was actually in the prompt.
    Failing this is not an error to report — `answer.py` falls back to the
    extractive answer, which is grounded by construction.
    """
    text = (answer or "").strip()
    if not text:
        return ["El modelo no devolvió texto."]
    if ABSTAIN_SENTENCE in text:
        return []
    return citation_problems(text, len(picks), require_citation=True)
