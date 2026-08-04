from __future__ import annotations

import contextlib
import io
import json
import sqlite3
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from common import (
    ABSTAIN_SENTENCE,
    CONSENT_WARNING,
    INDEX_SCHEMA,
    MAX_QUOTE_WORDS,
    MIN_CHUNK_WORDS,
    abstention_statistic,
    abstention_verdict,
    calibrated_threshold,
    calibration_error,
    chunk_word_spans,
    chunk_words,
    citation_markers,
    citation_problems,
    classify_text_layer,
    clip_quote,
    combine_text_layers,
    diversify,
    document_chunks,
    excerpt_disclosure,
    extractive_answer,
    format_citation,
    format_page_range,
    format_source_line,
    index_schema_error,
    is_evidence_sentence,
    is_glued_text,
    ocr_scope,
    page_ledger_rows,
    page_window,
    query_terms,
    quote_is_grounded,
    rank_path_candidates,
    reciprocal_rank_fusion,
    safe_cache_name,
    sample_positions,
    sampled_gap_estimate,
    split_sentences,
    summarize_ocr_debt,
    synthesis_problems,
    synthesis_prompt,
    unit_rows,
)
from manifest import load_manifest, resolve_inside, sha256, write_manifest
from ocr import write_sidecar


def install_heavy_dependency_stubs() -> None:
    """Let `build_index` be imported without fastembed or pypdf installed.

    Everything under test here is extraction and bookkeeping; the embedding
    model and the PDF parser are only touched by the real build. Stubbing them
    keeps the suite runnable on any interpreter, which is what makes it useful
    to a facilitator debugging on a laptop with no virtualenv activated.
    """
    if "fastembed" not in sys.modules:
        fastembed = types.ModuleType("fastembed")
        fastembed.TextEmbedding = object
        sys.modules["fastembed"] = fastembed
    if "pypdf" not in sys.modules:
        pypdf = types.ModuleType("pypdf")
        pypdf.PdfReader = object
        errors = types.ModuleType("pypdf.errors")

        class PyPdfError(Exception):
            pass

        class DependencyError(PyPdfError):
            pass

        errors.PyPdfError = PyPdfError
        errors.DependencyError = DependencyError
        pypdf.errors = errors
        sys.modules["pypdf"] = pypdf
        sys.modules["pypdf.errors"] = errors


install_heavy_dependency_stubs()

import answer  # noqa: E402
import build_index  # noqa: E402  (needs the stubs above)
import evaluate  # noqa: E402
import preflight  # noqa: E402
import search  # noqa: E402
import serve  # noqa: E402


class FakePage:
    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self) -> str:
        return self.text


class FakeReader:
    """A PdfReader that returns the pages the test declared."""

    def __init__(self, texts: list[str]) -> None:
        self.pages = [FakePage(text) for text in texts]
        self.is_encrypted = False


DIGEST = "a" * 64

PILOT_ROW = (
    "document_id,title,category,relative_path,start_page,max_pages,text_policy\n"
    "kahneman-2011,\"Thinking, Fast and Slow\",behavioral,"
    "Behavioral Economics/Kahneman.pdf,20,70,auto\n"
)

FULL_BOOK_ROW = (
    "document_id,title,author,year,category,relative_path,start_page,end_page,"
    "max_pages,text_policy\n"
    "mas-colell-1995,Microeconomic Theory,\"Mas-Colell, Whinston, Green\",1995,"
    "game-theory,\"Game Theory/Mas-Colell.pdf\",25,940,,ocr\n"
)


class CoreTests(unittest.TestCase):
    def test_chunking_preserves_overlap(self) -> None:
        words = [f"w{i}" for i in range(120)]
        chunks = chunk_words(" ".join(words), size=60, overlap=10)
        self.assertEqual(chunks[0].split()[-10:], chunks[1].split()[:10])

    def test_invalid_chunk_settings_fail(self) -> None:
        with self.assertRaises(ValueError):
            chunk_words("enough words " * 50, size=20, overlap=20)

    def test_unit_rows(self) -> None:
        matrix = unit_rows(np.array([[3.0, 4.0], [0.0, 2.0]]))
        np.testing.assert_allclose(np.linalg.norm(matrix, axis=1), [1.0, 1.0])

    def test_fts_query_is_bounded(self) -> None:
        self.assertEqual(query_terms('empleo "formal" Perú'), '"empleo" OR "formal" OR "perú"')

    def test_rrf_rewards_agreement(self) -> None:
        scores = reciprocal_rank_fusion([[1, 2, 3], [3, 1, 4]])
        self.assertGreater(scores[1], scores[2])
        self.assertGreater(scores[3], scores[4])

    def test_diversity_cap(self) -> None:
        metadata = [
            {"document_id": "a"},
            {"document_id": "a"},
            {"document_id": "a"},
            {"document_id": "b"},
        ]
        self.assertEqual(diversify([0, 1, 2, 3], metadata, 4, 2), [0, 1, 3])

    def test_manifest_cannot_escape_root(self) -> None:
        with self.assertRaises(ValueError):
            resolve_inside(Path("/tmp/books"), "../secret.pdf")


class PageWindowTests(unittest.TestCase):
    def test_window_skips_front_matter(self) -> None:
        self.assertEqual(page_window(100, 21, 5), [21, 22, 23, 24, 25])

    def test_window_is_clipped_to_the_document(self) -> None:
        self.assertEqual(page_window(23, 21, 10), [21, 22, 23])

    def test_window_is_empty_past_the_last_page(self) -> None:
        self.assertEqual(page_window(12, 40, 70), [])

    def test_zero_indexed_start_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            page_window(100, 0, 70)

    def test_whole_book_reads_to_the_last_page(self) -> None:
        self.assertEqual(page_window(6, 3), [3, 4, 5, 6])
        self.assertEqual(page_window(6, 3, None), [3, 4, 5, 6])

    def test_end_page_trims_the_back_matter(self) -> None:
        self.assertEqual(page_window(1001, 25, None, 28), [25, 26, 27, 28])

    def test_end_page_past_the_document_is_clipped(self) -> None:
        self.assertEqual(page_window(27, 25, None, 900), [25, 26, 27])

    def test_max_pages_and_end_page_take_the_tighter_bound(self) -> None:
        self.assertEqual(page_window(1001, 25, 2, 900), [25, 26])
        self.assertEqual(page_window(1001, 25, 900, 26), [25, 26])

    def test_end_page_before_start_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            page_window(100, 30, None, 29)


class TextLayerTests(unittest.TestCase):
    def test_digital_scanned_and_sparse(self) -> None:
        self.assertEqual(classify_text_layer(2400.0), "digital")
        self.assertEqual(classify_text_layer(3.0), "scanned")
        self.assertEqual(classify_text_layer(90.0), "sparse")

    def test_sampling_covers_both_ends_of_the_window(self) -> None:
        pages = list(range(21, 91))
        sampled = sample_positions(pages, 8)
        self.assertEqual(sampled[0], 21)
        self.assertEqual(sampled[-1], 90)
        self.assertEqual(len(sampled), 8)

    def test_sampling_a_short_window_returns_every_page(self) -> None:
        self.assertEqual(sample_positions([4, 5, 6], 8), [4, 5, 6])

    def test_a_uniform_book_keeps_its_label(self) -> None:
        self.assertEqual(combine_text_layers(["digital"] * 24), "digital")
        self.assertEqual(combine_text_layers(["scanned"] * 24), "scanned")
        self.assertEqual(combine_text_layers(["sparse", "sparse"]), "sparse")

    def test_one_scanned_signature_makes_the_book_mixed(self) -> None:
        labels = ["digital"] * 23 + ["scanned"]
        self.assertEqual(combine_text_layers(labels), "mixed")

    def test_a_scanned_book_with_sparse_pages_is_scanned(self) -> None:
        self.assertEqual(combine_text_layers(["scanned", "sparse"]), "scanned")

    def test_combining_nothing_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            combine_text_layers([])


class GluedTextLayerTests(unittest.TestCase):
    """Characters are not text. Holt 2019 is why this class exists.

    Its pages extract as `Chapter12asbeingrelevant…`: 1,838-3,285 characters and
    one to ten "words" each. A character count called every one of them digital,
    the preflight called the book mixed at 1,904 chars/page, and the build then
    turned 683 pages into fifteen chunks before anyone looked.
    """

    # Measured on the diagnostic build of 2026-08-04: Holt against the soundest
    # and the sparsest of the other seventeen works.
    HOLT_PAGE = (2248.0, 3.0)
    KAGEL_PAGE = (2671.4, 503.0)
    KOCKESEN_PAGE = (1854.8, 363.5)

    def test_the_holt_page_is_named_and_the_sound_ones_are_not(self) -> None:
        self.assertTrue(is_glued_text(*self.HOLT_PAGE))
        self.assertFalse(is_glued_text(*self.KAGEL_PAGE))
        self.assertFalse(is_glued_text(*self.KOCKESEN_PAGE))

    def test_a_page_of_characters_and_no_words_at_all(self) -> None:
        self.assertTrue(is_glued_text(2248.0, 0.0))

    def test_a_short_page_is_scanned_or_sparse_and_this_adds_nothing(self) -> None:
        # Below DIGITAL_MIN_CHARS the character count already answers the
        # question, and a page number alone would otherwise read as glued.
        self.assertFalse(is_glued_text(12.0, 1.0))
        self.assertFalse(is_glued_text(179.0, 0.0))

    def test_both_signals_are_required_never_one_alone(self) -> None:
        # Enough words for prose, however long they run: not glued.
        self.assertFalse(is_glued_text(4000.0, 40.0))
        self.assertTrue(is_glued_text(4000.0, 39.0))
        # Exactly at the characters-per-word threshold, not past it.
        self.assertFalse(is_glued_text(250.0, 10.0))
        self.assertTrue(is_glued_text(260.0, 10.0))

    def test_a_negative_count_is_a_bug_not_a_label(self) -> None:
        with self.assertRaises(ValueError):
            is_glued_text(-1.0, 3.0)
        with self.assertRaises(ValueError):
            is_glued_text(2248.0, -3.0)

    def test_the_character_count_alone_still_says_digital(self) -> None:
        """The old two-argument reading, kept so the failure stays legible."""
        self.assertEqual(classify_text_layer(1904.0), "digital")
        self.assertEqual(classify_text_layer(1904.0, 6.0), "glued")
        self.assertEqual(classify_text_layer(2671.4, 503.0), "digital")

    def test_an_empty_page_is_still_scanned_not_glued(self) -> None:
        self.assertEqual(classify_text_layer(0.0, 0.0), "scanned")
        self.assertEqual(classify_text_layer(90.0, 4.0), "sparse")

    def test_a_book_glued_from_cover_to_cover_is_reported_as_such(self) -> None:
        self.assertEqual(combine_text_layers(["glued"] * 24), "glued")

    def test_one_blank_page_does_not_rename_a_glued_book(self) -> None:
        # Holt's sample: 23 unreadable pages and one that came back empty.
        self.assertEqual(combine_text_layers(["glued"] * 23 + ["scanned"]), "glued")

    def test_a_glued_page_in_a_readable_book_makes_it_mixed(self) -> None:
        self.assertEqual(combine_text_layers(["digital"] * 23 + ["glued"]), "mixed")

    def test_a_tie_keeps_the_older_order(self) -> None:
        self.assertEqual(combine_text_layers(["glued", "scanned"]), "scanned")

    def test_an_invented_label_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            combine_text_layers(["digital", "pegado"])


class OcrDebtTests(unittest.TestCase):
    """A scanned book owes pages; a mixed book owes an inspection."""

    def test_a_fully_scanned_book_owes_every_missing_page(self) -> None:
        self.assertEqual(ocr_scope("scanned", 907), "full-scan")
        self.assertEqual(ocr_scope("sparse", 12), "full-scan")

    def test_a_mixed_book_only_owes_an_upper_bound(self) -> None:
        self.assertEqual(ocr_scope("mixed", 695), "mixed-gaps")

    def test_a_glued_book_owes_every_page_like_a_scan(self) -> None:
        """Holt: 695 window pages, all of them unreadable, none of them blank.

        A glued book looks the opposite of a scan — it reports characters on
        every page — and owes exactly the same bill, because none of those
        characters survive as words.
        """
        self.assertEqual(ocr_scope("glued", 695), "full-scan")

    def test_nothing_missing_is_nothing_owed(self) -> None:
        self.assertEqual(ocr_scope("scanned", 0), "none")
        self.assertEqual(ocr_scope("digital", 0), "none")
        self.assertEqual(ocr_scope(None, 0), "none")

    def test_an_unknown_layer_is_not_silently_bucketed(self) -> None:
        with self.assertRaises(ValueError):
            ocr_scope("scaneado", 10)

    def test_the_sample_scales_up_to_the_window(self) -> None:
        # Kahneman: 2 of 24 sampled pages textless over a 364-page window.
        self.assertEqual(sampled_gap_estimate(364, 24, 2), 30)
        self.assertEqual(sampled_gap_estimate(240, 24, 24), 240)
        self.assertEqual(sampled_gap_estimate(240, 24, 0), 0)

    def test_an_impossible_sample_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            sampled_gap_estimate(364, 8, 9)

    def test_the_two_bills_are_never_added_together(self) -> None:
        reports = [
            {"document_id": "camerer", "ocr_scope": "full-scan",
             "ocr_missing_pages": 154, "ocr_pages_estimate": 154},
            {"document_id": "mas-colell", "ocr_scope": "full-scan",
             "ocr_missing_pages": 907, "ocr_pages_estimate": 907},
            {"document_id": "kahneman", "ocr_scope": "mixed-gaps",
             "ocr_missing_pages": 364, "ocr_pages_estimate": 30},
            {"document_id": "osborne", "ocr_scope": "none",
             "ocr_missing_pages": 0, "ocr_pages_estimate": 0},
        ]
        debt = summarize_ocr_debt(reports)
        self.assertEqual(debt["ocr_pages_full_scan"], 1061)
        self.assertEqual(debt["ocr_pages_mixed_upper_bound"], 364)
        self.assertEqual(debt["ocr_pages_mixed_estimate"], 30)
        self.assertEqual(debt["full_scan_documents"], ["camerer", "mas-colell"])
        self.assertEqual(debt["mixed_gap_documents"], ["kahneman"])

    def test_a_glued_work_is_billed_with_the_scans_not_with_the_gaps(self) -> None:
        """Where the fourth work lands once the detector names it.

        Before the words/page column Holt sat in the mixed bucket, where its 695
        pages were an upper bound nobody planned to pay. It belongs in the bill.
        """
        reports = [
            {"document_id": "camerer", "ocr_scope": "full-scan",
             "ocr_missing_pages": 154, "ocr_pages_estimate": 154},
            {"document_id": "holt-2019", "ocr_scope": "full-scan",
             "ocr_missing_pages": 695, "ocr_pages_estimate": 695},
            {"document_id": "kahneman", "ocr_scope": "mixed-gaps",
             "ocr_missing_pages": 364, "ocr_pages_estimate": 30},
        ]
        debt = summarize_ocr_debt(reports)
        self.assertEqual(debt["ocr_pages_full_scan"], 849)
        self.assertEqual(debt["full_scan_documents"], ["camerer", "holt-2019"])
        self.assertEqual(debt["ocr_pages_mixed_upper_bound"], 364)


class PathRepairTests(unittest.TestCase):
    def test_best_candidate_beats_a_similar_but_wrong_file(self) -> None:
        catalogue = [
            "Game Theory/Osborne - An Introduction to Game Theory (2003).pdf",
            "Game Theory/An Introduction to Game Theory - Solutions Manual.pdf",
            "Behavioral Economics/Kahneman - Thinking, Fast and Slow (2011).pdf",
        ]
        ranked = rank_path_candidates(
            "Game Theory/Osborne - Introduction to Game Theory 2003.pdf", catalogue
        )
        self.assertEqual(ranked[0][0], catalogue[0])
        self.assertGreater(ranked[0][1], ranked[1][1])


class CacheNameTests(unittest.TestCase):
    def test_cache_name_is_flat_and_hashed(self) -> None:
        self.assertEqual(safe_cache_name("kahneman-2011", DIGEST), f"kahneman-2011.{'a' * 12}.jsonl")

    def test_cache_name_cannot_escape_the_cache_directory(self) -> None:
        name = safe_cache_name("../../etc/passwd", DIGEST)
        self.assertEqual(name, f"etc-passwd.{'a' * 12}.jsonl")
        self.assertNotIn("/", name)

    def test_cache_name_requires_a_real_digest(self) -> None:
        with self.assertRaises(ValueError):
            safe_cache_name("kahneman-2011", "not-a-digest")


class ManifestSchemaTests(unittest.TestCase):
    """The whole-book manifest must load without breaking the pilot manifest."""

    def load(self, text: str) -> tuple[list[dict], Path]:
        root = Path(tempfile.mkdtemp())
        path = root / "manifest.csv"
        path.write_text(text, encoding="utf-8")
        return load_manifest(path, root / "books", require_files=False), path

    def test_pilot_row_still_loads(self) -> None:
        entries, _ = self.load(PILOT_ROW)
        self.assertEqual(entries[0]["max_pages"], 70)
        self.assertNotIn("end_page", entries[0])

    def test_whole_book_row_has_no_page_budget(self) -> None:
        entries, _ = self.load(FULL_BOOK_ROW)
        self.assertIsNone(entries[0]["max_pages"])
        self.assertEqual(entries[0]["end_page"], 940)
        self.assertEqual(entries[0]["year"], "1995")

    def test_end_page_before_start_page_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.load(FULL_BOOK_ROW.replace(",25,940,,ocr", ",25,24,,ocr"))

    def test_a_non_numeric_page_budget_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.load(PILOT_ROW.replace(",20,70,auto", ",20,muchas,auto"))

    def test_rewriting_keeps_author_year_and_end_page(self) -> None:
        entries, path = self.load(FULL_BOOK_ROW)
        write_manifest(path, entries)
        header = path.read_text(encoding="utf-8").splitlines()[0]
        self.assertIn("author", header)
        self.assertIn("year", header)
        self.assertIn("end_page", header)
        reloaded, _ = self.load(path.read_text(encoding="utf-8"))
        self.assertEqual(reloaded[0]["end_page"], 940)
        self.assertIsNone(reloaded[0]["max_pages"])

    def test_rewriting_a_pilot_manifest_adds_no_columns(self) -> None:
        entries, path = self.load(PILOT_ROW)
        write_manifest(path, entries)
        self.assertEqual(path.read_text(encoding="utf-8"), PILOT_ROW)


class FullBooksManifestTests(unittest.TestCase):
    """The shipped whole-book manifest, checked without opening a single PDF."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).parents[1]
        cls.entries = load_manifest(
            root / "manifest-full-books.csv",
            Path("/nonexistent-books-root"),
            require_files=False,
        )

    def test_eighteen_whole_works(self) -> None:
        self.assertEqual(len(self.entries), 18)

    def test_categories_match_the_agreed_split(self) -> None:
        counts: dict[str, int] = {}
        for entry in self.entries:
            counts[entry["category"]] = counts.get(entry["category"], 0) + 1
        self.assertEqual(counts, {"behavioral": 3, "experimental": 10, "game-theory": 5})

    def test_no_row_caps_the_pages(self) -> None:
        for entry in self.entries:
            self.assertIsNone(entry["max_pages"], entry["document_id"])

    def test_every_row_carries_a_citable_author(self) -> None:
        for entry in self.entries:
            self.assertTrue(entry["author"].strip(), entry["document_id"])

    def test_only_the_measured_full_scans_are_marked_for_ocr(self) -> None:
        """Four works, not three: three scans and one defective text layer.

        The preflight of 2026-08-04 found three works whose pages carried no
        characters at all. `holt-2019` is the fourth, and it was found the
        expensive way: its pages carry characters and no word breaks, so the
        build extracted 683 pages of text out of it and produced fifteen
        chunks. These four are what `scripts/ocr.py` picks up by default.
        Marking one more costs an unnecessary hour of batch; marking one fewer
        ships a book that indexes to almost nothing.
        """
        marked = sorted(
            entry["document_id"]
            for entry in self.entries
            if entry["text_policy"] == "ocr"
        )
        self.assertEqual(
            marked, ["camerer-2003", "holt-2019", "list-2026", "mas-colell-1995"]
        )

    def test_no_chapter_or_paper_slipped_in(self) -> None:
        paths = [entry["relative_path"].lower() for entry in self.entries]
        self.assertFalse([p for p in paths if "/chapters/" in p])


# A paragraph cut in half by a page break. Neither half states the whole idea,
# which is exactly why page-by-page chunking retrieved neither of them well.
PAGE_ONE = (
    "El efecto de dotación aparece cuando la disposición a aceptar de un sujeto "
    "supera de manera sistemática su disposición a pagar por exactamente el mismo "
    "bien, lo que"
)
PAGE_TWO = (
    "contradice la predicción estándar de que ambas medidas coinciden en ausencia "
    "de efectos ingreso y de costos de transacción apreciables en el mercado."
)


class ChunkSpanTests(unittest.TestCase):
    """9.1: the spans, checked before anything is joined to a page."""

    def test_spans_cover_the_document_with_the_declared_overlap(self) -> None:
        words = [f"w{i}" for i in range(120)]
        self.assertEqual(chunk_word_spans(words, size=60, overlap=10), [(0, 60), (50, 110)])

    def test_chunk_words_is_unchanged_by_the_rewrite(self) -> None:
        words = [f"w{i}" for i in range(120)]
        chunks = chunk_words(" ".join(words), size=60, overlap=10)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].split()[-10:], chunks[1].split()[:10])

    def test_a_tail_shorter_than_the_floor_is_not_its_own_chunk(self) -> None:
        # The last 10 words belong to the previous chunk's overlap, not to a
        # 10-word fragment that would outrank real passages on a short query.
        words = [f"w{i}" for i in range(MIN_CHUNK_WORDS + 5)]
        self.assertEqual(chunk_word_spans(words, size=60, overlap=10), [(0, 45)])

    def test_a_document_below_the_floor_produces_nothing(self) -> None:
        self.assertEqual(chunk_word_spans([f"w{i}" for i in range(20)]), [])

    def test_invalid_settings_still_fail(self) -> None:
        with self.assertRaises(ValueError):
            chunk_word_spans(["a"] * 100, size=20, overlap=20)


class CrossPageChunkTests(unittest.TestCase):
    """9.1: the reason the rewrite exists — paragraphs that cross a break."""

    def test_a_paragraph_split_by_a_page_break_is_retrieved_whole(self) -> None:
        chunks = document_chunks({20: PAGE_ONE, 21: PAGE_TWO})
        self.assertEqual(len(chunks), 1)
        self.assertIn("por exactamente el mismo bien, lo que contradice", chunks[0]["text"])
        self.assertEqual((chunks[0]["page_start"], chunks[0]["page_end"]), (20, 21))

    def test_the_old_behaviour_lost_that_paragraph_entirely(self) -> None:
        # Not a regression guard: the record of what this change bought. Each
        # half is under the 40-word floor, so page-by-page chunking indexed
        # neither of them.
        self.assertEqual(chunk_words(PAGE_ONE), [])
        self.assertEqual(chunk_words(PAGE_TWO), [])

    def test_a_chunk_that_spans_three_pages_declares_both_ends(self) -> None:
        pages = {5: "alfa " * 20, 6: "beta " * 20, 7: "gama " * 20}
        chunks = document_chunks(pages, size=320, overlap=45)
        self.assertEqual(len(chunks), 1)
        self.assertEqual((chunks[0]["page_start"], chunks[0]["page_end"]), (5, 7))
        self.assertEqual(chunks[0]["words"], 60)

    def test_a_chunk_inside_one_page_still_cites_one_page(self) -> None:
        chunks = document_chunks({84: "palabra " * 100})
        self.assertEqual((chunks[0]["page_start"], chunks[0]["page_end"]), (84, 84))

    def test_page_start_is_where_the_chunk_begins(self) -> None:
        # The second chunk starts at word 40, still on page 1, and ends on
        # page 2. Citing page 2 because most of its words are there would put
        # the reader on the wrong page.
        pages = {1: "uno " * 45, 2: "dos " * 45}
        chunks = document_chunks(pages, size=50, overlap=10)
        self.assertEqual(len(chunks), 2)
        self.assertEqual((chunks[1]["page_start"], chunks[1]["page_end"]), (1, 2))

    def test_pages_are_joined_in_page_order_not_in_insertion_order(self) -> None:
        pages = {}
        pages[12] = "tarde " * 30
        pages[3] = "temprano " * 30
        chunks = document_chunks(pages)
        self.assertEqual(chunks[0]["page_start"], 3)
        self.assertTrue(chunks[0]["text"].startswith("temprano"))

    def test_a_gap_in_the_page_numbers_is_reported_as_it_is(self) -> None:
        # Page 6 produced no text (a plate, or an OCR failure). The chunk really
        # does span 5 to 7 and says so; inventing page 6 would be worse.
        chunks = document_chunks({5: "alfa " * 25, 7: "gama " * 25})
        self.assertEqual((chunks[0]["page_start"], chunks[0]["page_end"]), (5, 7))

    def test_an_empty_document_produces_nothing(self) -> None:
        self.assertEqual(document_chunks({}), [])


class PageLedgerTests(unittest.TestCase):
    """9.3: one row per indexed page, and not one word of the book."""

    TEXTS = {12: "hola mundo", 7: "una página escaneada", 9: "otra"}
    ORIGINS = {12: "pdf", 7: "ocr", 9: "pdf"}

    def test_one_row_per_page_with_text_in_page_order(self) -> None:
        rows = page_ledger_rows("camerer-2003", self.TEXTS, self.ORIGINS)
        self.assertEqual([row["page"] for row in rows], [7, 9, 12])
        self.assertEqual(len(rows), len(self.TEXTS))

    def test_the_ledger_says_which_pages_came_from_ocr(self) -> None:
        rows = page_ledger_rows("camerer-2003", self.TEXTS, self.ORIGINS)
        from_ocr = [row["page"] for row in rows if row["source"] == "ocr"]
        self.assertEqual(from_ocr, [7])

    def test_the_ledger_carries_counts_and_never_text(self) -> None:
        rows = page_ledger_rows("camerer-2003", self.TEXTS, self.ORIGINS)
        for row in rows:
            self.assertNotIn("text", row)
            self.assertEqual(set(row), {"document_id", "page", "source", "characters", "words"})
        self.assertEqual(rows[-1]["characters"], len("hola mundo"))
        self.assertEqual(rows[-1]["words"], 2)

    def test_a_page_with_text_and_no_recorded_source_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            page_ledger_rows("camerer-2003", {4: "algo"}, {})

    def test_an_unknown_source_is_not_written_to_the_ledger(self) -> None:
        with self.assertRaises(ValueError):
            page_ledger_rows("camerer-2003", {4: "algo"}, {4: "adivinado"})


class IndexSchemaTests(unittest.TestCase):
    """9.2: an index built before this change has to say so, not crash."""

    def test_a_current_index_passes(self) -> None:
        self.assertIsNone(index_schema_error({"schema": INDEX_SCHEMA}))

    def test_an_index_without_a_schema_key_is_the_old_one(self) -> None:
        message = index_schema_error({"model": "x", "chunks": 2614})
        self.assertIsNotNone(message)
        self.assertIn("build_index.py", message)
        self.assertIn("esquema 1", message)

    def test_the_message_names_both_versions(self) -> None:
        message = index_schema_error({"schema": 1})
        self.assertIn("esquema 1", message)
        self.assertIn(str(INDEX_SCHEMA), message)

    def test_a_newer_index_is_not_read_silently(self) -> None:
        self.assertIsNotNone(index_schema_error({"schema": INDEX_SCHEMA + 1}))

    def test_search_refuses_an_old_index_before_loading_anything(self) -> None:
        # The guard has to fire on index.json alone: a stale index still has a
        # 5 MB chunks.jsonl next to it, and loading it only to fail later is
        # both slow and a worse message.
        index = Path(tempfile.mkdtemp())
        (index / "index.json").write_text('{"model": "m", "chunks": 2614}', encoding="utf-8")
        with self.assertRaises(SystemExit) as raised:
            search.run_search("efecto de dotación", index, "lexical", 5)
        self.assertIn("build_index.py", str(raised.exception))


class CitationTests(unittest.TestCase):
    """What the room reads under a result, for both manifests."""

    def test_the_whole_book_manifest_cites_author_and_year(self) -> None:
        self.assertEqual(
            format_citation("Mas-Colell, Whinston, Green", "1995", "Microeconomic Theory"),
            "Mas-Colell, Whinston, Green (1995), Microeconomic Theory",
        )

    def test_the_pilot_manifest_has_neither_and_still_reads_well(self) -> None:
        self.assertEqual(format_citation("", "", "Thinking, Fast and Slow"), "Thinking, Fast and Slow")
        self.assertEqual(format_citation("Kahneman", "", "Thinking, Fast and Slow"), "Kahneman, Thinking, Fast and Slow")

    def test_a_year_read_as_a_number_still_renders(self) -> None:
        self.assertEqual(format_citation("Camerer", 2003, "Behavioral Game Theory"), "Camerer (2003), Behavioral Game Theory")

    def test_page_range_collapses_when_the_chunk_stays_on_one_page(self) -> None:
        self.assertEqual(format_page_range(84, 84), "p. 84")
        self.assertEqual(format_page_range(84, 86), "pp. 84–86")

    def test_a_reversed_range_is_a_bug_not_a_display(self) -> None:
        with self.assertRaises(ValueError):
            format_page_range(86, 84)


class ExtractDocumentTests(unittest.TestCase):
    """The build path end to end, with the PDF parser stubbed out."""

    PILOT_ENTRY = {
        "document_id": "kahneman-2011",
        "title": "Thinking, Fast and Slow",
        "category": "behavioral",
        "relative_path": "Behavioral Economics/Kahneman.pdf",
        "text_policy": "digital",
        "start_page": 2,
        "max_pages": 70,
    }

    def extract(self, page_texts: list[str], entry: dict, policy_root: Path | None = None):
        root = policy_root or Path(tempfile.mkdtemp())
        pdf = root / "book.pdf"
        if not pdf.exists():
            pdf.write_bytes(b"%PDF-1.4 not a real PDF; PdfReader is stubbed")
        full = {**entry, "pdf_path": pdf, "exists": True}
        with patch.object(build_index, "PdfReader", lambda path: FakeReader(page_texts)):
            return build_index.extract_document(full, root, 320, 45, 0) + (root,)

    def test_the_pilot_entry_builds_under_the_new_schema(self) -> None:
        chunks, record, ledger, _ = self.extract(
            ["portada", PAGE_ONE, PAGE_TWO], self.PILOT_ENTRY
        )
        self.assertEqual(record["status"], "ok")
        self.assertEqual(record["pages_with_text"], 2)
        self.assertEqual(record["pages_from_ocr"], 0)
        self.assertEqual(len(chunks), 1)
        # No author and no year in the pilot manifest: empty, never missing.
        self.assertEqual(chunks[0]["author"], "")
        self.assertEqual(chunks[0]["year"], "")
        self.assertEqual(chunks[0]["page"], chunks[0]["page_start"])
        self.assertEqual((chunks[0]["page_start"], chunks[0]["page_end"]), (2, 3))
        self.assertEqual(record["chunks_crossing_pages"], 1)
        self.assertEqual([row["page"] for row in ledger], [2, 3])

    def test_author_and_year_reach_every_chunk(self) -> None:
        entry = {
            **self.PILOT_ENTRY,
            "document_id": "mas-colell-1995",
            "title": "Microeconomic Theory",
            "author": "Mas-Colell, Whinston, Green",
            "year": "1995",
            "start_page": 1,
            "max_pages": None,
            "end_page": 2,
        }
        chunks, record, _, _ = self.extract([PAGE_ONE, PAGE_TWO, "descartada"], entry)
        self.assertEqual(record["author"], "Mas-Colell, Whinston, Green")
        self.assertTrue(chunks)
        for chunk in chunks:
            self.assertEqual(chunk["author"], "Mas-Colell, Whinston, Green")
            self.assertEqual(chunk["year"], "1995")
            self.assertLessEqual(chunk["page_end"], 2)

    def test_a_page_recovered_by_ocr_is_marked_as_such_in_the_ledger(self) -> None:
        root = Path(tempfile.mkdtemp())
        pdf = root / "book.pdf"
        pdf.write_bytes(b"%PDF-1.4 not a real PDF; PdfReader is stubbed")
        entry = {
            **self.PILOT_ENTRY,
            "document_id": "camerer-2003",
            "text_policy": "auto",
            "start_page": 1,
            "max_pages": 2,
        }
        write_sidecar(root, "camerer-2003", sha256(pdf), {2: PAGE_TWO * 3})
        chunks, record, ledger, _ = self.extract([PAGE_ONE, "  "], entry, root)
        sources = {row["page"]: row["source"] for row in ledger}
        self.assertEqual(sources, {1: "pdf", 2: "ocr"})
        self.assertEqual(record["pages_from_ocr"], 1)
        self.assertEqual(record["pages_from_pdf"], 1)
        self.assertTrue(chunks)

    def test_a_document_with_no_usable_text_is_skipped_and_leaves_no_ledger(self) -> None:
        chunks, record, ledger, _ = self.extract(["", "  ", ""], self.PILOT_ENTRY)
        self.assertEqual(record["status"], "skipped")
        self.assertEqual(chunks, [])
        self.assertEqual(ledger, [])

    def test_a_start_page_past_the_end_fails_that_document_only(self) -> None:
        entry = {**self.PILOT_ENTRY, "start_page": 40}
        chunks, record, ledger, _ = self.extract(["una", "dos"], entry)
        self.assertEqual(record["status"], "failed")
        self.assertIn("past the last page", record["error"])
        self.assertEqual((chunks, ledger), ([], []))

    def test_a_missing_file_still_produces_a_complete_log_row(self) -> None:
        record = build_index.blank_record(self.PILOT_ENTRY, "missing", "file not found")
        self.assertEqual(record["status"], "missing")
        self.assertEqual(record["chunks_crossing_pages"], 0)
        self.assertEqual(record["author"], "")


class PreflightGluedLayerTests(unittest.TestCase):
    """The preflight has to catch this before the build pays for it.

    The build is the expensive place to discover a defective text layer: it
    extracted Holt's 683 pages, embedded fifteen chunks and reported `ok`. The
    preflight reads twenty-four pages and costs nothing.
    """

    # No spaces, the way the real extraction returns them.
    GLUED_PAGE = "Chapter12asbeingrelevanttothedecision" * 60
    PROSE_PAGE = "el equilibrio walrasiano existe bajo continuidad y convexidad " * 40

    def inspect(self, page_texts: list[str]) -> dict:
        root = Path(tempfile.mkdtemp())
        pdf = root / "book.pdf"
        pdf.write_bytes(b"%PDF-1.4 not a real PDF; PdfReader is stubbed")
        entry = {
            "document_id": "holt-2019",
            "title": "Markets, Games, and Strategic Behavior (2nd ed.)",
            "category": "experimental",
            "relative_path": "Experimental Economics/Holt 2019.pdf",
            "start_page": 1,
            "end_page": None,
            "max_pages": None,
            "text_policy": "ocr",
            "exists": True,
            "pdf_path": pdf,
        }
        with patch.object(preflight, "PdfReader", lambda path: FakeReader(page_texts)):
            return preflight.inspect(entry, root / "ocr_cache", 8)

    def test_a_glued_book_is_not_reported_as_digital_or_as_mixed(self) -> None:
        report = self.inspect([self.GLUED_PAGE] * 8)
        self.assertEqual(report["text_layer"], "glued")
        self.assertEqual(report["status"], "needs-ocr")
        self.assertEqual(report["sampled_glued"], 8)
        self.assertEqual(report["sampled_without_text"], 8)

    def test_the_bill_is_firm_and_covers_the_whole_window(self) -> None:
        report = self.inspect([self.GLUED_PAGE] * 8)
        self.assertEqual(report["ocr_scope"], "full-scan")
        self.assertEqual(report["ocr_pages_estimate"], report["window_pages"])

    def test_the_detail_line_says_why_a_page_full_of_characters_needs_ocr(self) -> None:
        report = self.inspect([self.GLUED_PAGE] * 8)
        # A reader who only saw chars/page would think the row was mislabelled.
        self.assertGreater(report["chars_per_page"], 1000)
        self.assertLess(report["words_per_page"], 40)
        self.assertGreater(report["chars_per_word"], 25)
        self.assertIn("word breaks", report["detail"])
        self.assertIn("chars per word", report["detail"])

    def test_a_readable_book_is_untouched_by_the_new_column(self) -> None:
        report = self.inspect([self.PROSE_PAGE] * 8)
        self.assertEqual(report["text_layer"], "digital")
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["sampled_glued"], 0)
        self.assertEqual(report["ocr_scope"], "none")

    def test_one_glued_page_among_readable_ones_is_counted_and_named(self) -> None:
        report = self.inspect([self.PROSE_PAGE] * 7 + [self.GLUED_PAGE])
        self.assertEqual(report["text_layer"], "mixed")
        self.assertEqual(report["sampled_glued"], 1)
        # Mixed stays an upper bound; what changes is that the page is visible.
        self.assertEqual(report["ocr_scope"], "mixed-gaps")
        self.assertIn("word breaks", report["detail"])


class SqliteSchemaTests(unittest.TestCase):
    """SQLite has to carry the citation, not just the text."""

    CHUNK = {
        "chunk_id": 0,
        "document_id": "mas-colell-1995",
        "title": "Microeconomic Theory",
        "author": "Mas-Colell, Whinston, Green",
        "year": "1995",
        "category": "game-theory",
        "page": 84,
        "page_start": 84,
        "page_end": 85,
        "relative_path": "Game Theory/Mas-Colell.pdf",
        "sha256": DIGEST,
        "text": "el equilibrio walrasiano existe bajo continuidad y convexidad",
    }

    def test_metadata_carries_author_year_and_the_page_range(self) -> None:
        path = Path(tempfile.mkdtemp()) / "search.sqlite"
        build_index.write_sqlite(path, [self.CHUNK])
        connection = sqlite3.connect(path)
        try:
            row = connection.execute(
                "SELECT author, year, page, page_start, page_end FROM metadata"
            ).fetchone()
            found = connection.execute(
                "SELECT chunk_id FROM chunks_fts WHERE chunks_fts MATCH ?", ('"walrasiano"',)
            ).fetchall()
        finally:
            connection.close()
        self.assertEqual(row, ("Mas-Colell, Whinston, Green", "1995", 84, 84, 85))
        self.assertEqual(found, [(0,)])

    def test_rebuilding_over_an_old_database_replaces_it(self) -> None:
        path = Path(tempfile.mkdtemp()) / "search.sqlite"
        build_index.write_sqlite(path, [self.CHUNK])
        build_index.write_sqlite(path, [self.CHUNK])
        connection = sqlite3.connect(path)
        try:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM metadata").fetchone(), (1,)
            )
        finally:
            connection.close()


class EvaluationHarnessTests(unittest.TestCase):
    QRELS = [
        {
            "document_id": "kahneman-2011",
            "page_start": 20,
            "page_end": 22,
            "relevance": 1,
        },
        {
            "document_id": "camerer-2003",
            "page_start": 50,
            "page_end": 50,
            "relevance": 1,
        },
    ]

    def test_relevance_requires_document_and_overlapping_page_range(self) -> None:
        self.assertTrue(
            evaluate.result_is_relevant(
                {"document_id": "kahneman-2011", "page_start": 21, "page_end": 23},
                self.QRELS,
            )
        )
        self.assertFalse(
            evaluate.result_is_relevant(
                {"document_id": "kahneman-2011", "page_start": 23, "page_end": 24},
                self.QRELS,
            )
        )
        self.assertFalse(
            evaluate.result_is_relevant(
                {"document_id": "other", "page_start": 20, "page_end": 22},
                self.QRELS,
            )
        )

    def test_metrics_use_first_relevant_rank_and_binary_dcg(self) -> None:
        results = [
            {"document_id": "other", "page_start": 1, "page_end": 1},
            {"document_id": "kahneman-2011", "page_start": 20, "page_end": 20},
            {"document_id": "other-2", "page_start": 1, "page_end": 1},
            {"document_id": "camerer-2003", "page_start": 50, "page_end": 50},
        ]
        metrics = evaluate.query_metrics(results, self.QRELS)
        self.assertEqual(metrics["hit_at_3"], 1.0)
        self.assertEqual(metrics["reciprocal_rank"], 0.5)
        expected_dcg = 1 / np.log2(3) + 1 / np.log2(5)
        ideal = 1 + 1 / np.log2(3)
        self.assertAlmostEqual(metrics["ndcg_at_5"], expected_dcg / ideal)

    def test_overlapping_chunks_do_not_count_the_same_qrel_twice(self) -> None:
        one_qrel = [self.QRELS[0]]
        results = [
            {"document_id": "kahneman-2011", "page_start": 20, "page_end": 21},
            {"document_id": "kahneman-2011", "page_start": 21, "page_end": 22},
        ]
        metrics = evaluate.query_metrics(results, one_qrel)
        self.assertEqual(metrics["ndcg_at_5"], 1.0)

    def test_mean_metrics_names_mrr_in_the_summary(self) -> None:
        summary = evaluate.mean_metrics(
            [
                {"hit_at_3": 1.0, "reciprocal_rank": 1.0, "ndcg_at_5": 0.5},
                {"hit_at_3": 0.0, "reciprocal_rank": 0.0, "ndcg_at_5": 0.0},
            ]
        )
        self.assertEqual(summary, {"hit_at_3": 0.5, "mrr": 0.5, "ndcg_at_5": 0.25})

    def test_positive_qrel_requires_a_named_and_dated_human_verification(self) -> None:
        root = Path(tempfile.mkdtemp())
        path = root / "qrels.csv"
        path.write_text(
            ",".join(evaluate.QREL_FIELDS)
            + "\nB01,kahneman-2011,20,22,1,,,\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "verified_by"):
            evaluate.load_qrels(path, {"B01"})

    def test_pool_judgment_distinguishes_positive_negative_and_unjudged(self) -> None:
        qrels = [
            {"document_id": "book-a", "page_start": 10, "page_end": 12, "relevance": 1},
            {"document_id": "book-b", "page_start": 20, "page_end": 21, "relevance": 0},
        ]
        self.assertEqual(
            evaluate.result_judgment(
                {"document_id": "book-a", "page_start": 12, "page_end": 13}, qrels
            ),
            "positive",
        )
        self.assertEqual(
            evaluate.result_judgment(
                {"document_id": "book-b", "page_start": 19, "page_end": 20}, qrels
            ),
            "explicit-negative",
        )
        self.assertEqual(
            evaluate.result_judgment(
                {"document_id": "book-c", "page_start": 1, "page_end": 2}, qrels
            ),
            "unjudged",
        )

    def test_pool_deduplicates_modes_and_keeps_best_rank(self) -> None:
        candidate = {
            "document_id": "book-a",
            "page_start": 10,
            "page_end": 11,
        }
        row = {
            "query_id": "B01",
            "modes": {
                "lexical": {"results": [{**candidate, "rank": 3}]},
                "dense": {"results": [{**candidate, "rank": 1}]},
                "hybrid": {"results": [{**candidate, "rank": 2}]},
            },
        }
        pool = evaluate.build_pool([row], {"B01": self.QRELS})
        self.assertEqual(len(pool), 1)
        self.assertEqual(pool[0]["seen_in_modes"], "lexical|dense|hybrid")
        self.assertEqual(pool[0]["best_rank"], 1)
        self.assertEqual(pool[0]["judgment"], "unjudged")


# --------------------------------------------------------------------------
# Answer layer: abstention, citations, consent.
# --------------------------------------------------------------------------

CALIBRATION = {
    "mode": "dense",
    "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "min_top_score": 0.5636,
    "answerable": {"min": 0.6634, "median": 0.7144, "max": 0.8073},
    "unanswerable": {"min": 0.3504, "median": 0.4029, "max": 0.4638},
    "separable": True,
    "gap": 0.1996,
}

KAHNEMAN_CHUNK = (
    "Why call them System 1 and System 2 rather than the more descriptive "
    "automatic system and effortful system? System 1 operates automatically "
    "and quickly, with little or no effort and no sense of voluntary control. "
    "System 2 allocates attention to the effortful mental activities that "
    "demand it, including complex computations."
)

OSBORNE_CHUNK = (
    "Player function P of the empty history is the set containing 1 and 2. "
    "A strategy of player 1 in an extensive game specifies an action for every "
    "history after which it is her turn to move."
)


def fake_vector(text: str) -> np.ndarray:
    """A deterministic bag-of-words vector, so tests exercise the real path.

    `select_evidence` scores sentences with `embed_passages @ embed_query` and
    takes the argmax. Substituting word overlap for the transformer keeps that
    arithmetic intact and makes the outcome predictable, which is what lets a
    test assert *which* sentence gets quoted.
    """
    import re
    import zlib

    vector = np.zeros(64, dtype=np.float32)
    for word in re.findall(r"\w+", text.lower()):
        vector[zlib.crc32(word.encode("utf-8")) % 64] += 1.0
    return vector / max(float(np.linalg.norm(vector)), 1e-12)


class FakeIndex:
    """A `SearchIndex` with the model and the ranking replaced by fixtures."""

    def __init__(self, chunks: list[dict], results: list[dict]) -> None:
        self.chunks = chunks
        self._results = results
        self.config = {"model": CALIBRATION["model"], "dimensions": 64}
        self.queries: list[str] = []

    def search(self, query: str, mode: str = "dense", limit: int = 5,
               per_document: int = 2) -> list[dict]:
        self.queries.append(query)
        return self._results[:limit]

    def embed_query(self, query: str) -> np.ndarray:
        return fake_vector(query)

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        return np.vstack([fake_vector(text) for text in texts])


def quiet():
    """Swallow the consent warning a test deliberately triggers.

    The warning belongs on a facilitator's screen, not in the middle of a test
    report; the tests that care about it assert on the string instead.
    """
    return contextlib.redirect_stderr(io.StringIO())


def fake_result(chunk_id: int, dense: float, citation: str, pages: str) -> dict:
    return {
        "rank": chunk_id + 1,
        "chunk_id": chunk_id,
        "score": 0.03,
        "dense_score": dense,
        "lexical_score": 0.0,
        "document_id": f"doc-{chunk_id}",
        "citation": citation,
        "pages": pages,
        "page_start": 23,
        "page_end": 24,
        "relative_path": f"Books/{chunk_id}.pdf",
    }


def answering_index() -> FakeIndex:
    return FakeIndex(
        [{"text": KAHNEMAN_CHUNK}, {"text": OSBORNE_CHUNK}],
        [
            fake_result(0, 0.6826, "Daniel Kahneman (2011), Thinking, Fast and Slow", "pp. 23–24"),
            fake_result(1, 0.5901, "Martin J. Osborne (2003), An Introduction to Game Theory", "p. 525"),
        ],
    )


class AbstentionRuleTests(unittest.TestCase):
    """The rule that decides whether the corpus has an answer at all."""

    def test_statistic_is_the_best_similarity_not_the_first_rank(self) -> None:
        # Hybrid fusion can rank a slightly less similar passage first; the
        # threshold was measured against the best similarity, so that is what
        # has to be compared against it.
        results = [{"dense_score": 0.41}, {"dense_score": 0.77}, {"dense_score": 0.52}]
        self.assertEqual(abstention_statistic(results), 0.77)

    def test_no_results_at_all_scores_zero_rather_than_raising(self) -> None:
        self.assertEqual(abstention_statistic([]), 0.0)

    def test_verdict_answers_above_the_threshold_and_reports_the_margin(self) -> None:
        verdict = abstention_verdict(0.6826, CALIBRATION)
        self.assertTrue(verdict["answer"])
        self.assertEqual(verdict["threshold"], 0.5636)
        self.assertEqual(verdict["margin"], 0.119)

    def test_verdict_abstains_below_the_threshold(self) -> None:
        verdict = abstention_verdict(0.3504, CALIBRATION)
        self.assertFalse(verdict["answer"])
        self.assertLess(verdict["margin"], 0)

    def test_threshold_sits_in_the_middle_of_a_measured_gap(self) -> None:
        calibrated = calibrated_threshold(0.6634, 0.4638)
        self.assertTrue(calibrated["separable"])
        self.assertEqual(calibrated["min_top_score"], 0.5636)
        self.assertEqual(calibrated["gap"], 0.1996)

    def test_overlapping_distributions_are_reported_not_papered_over(self) -> None:
        calibrated = calibrated_threshold(0.42, 0.55)
        self.assertFalse(calibrated["separable"])
        self.assertEqual(calibrated["min_top_score"], 0.42)
        self.assertLess(calibrated["gap"], 0)

    def test_calibration_must_match_the_mode_and_the_model_in_use(self) -> None:
        self.assertIsNone(calibration_error(CALIBRATION, "dense", CALIBRATION["model"]))
        self.assertIn("modo", calibration_error(CALIBRATION, "hybrid", CALIBRATION["model"]))
        self.assertIn("otra escala", calibration_error(CALIBRATION, "dense", "other-model"))

    def test_an_incomplete_calibration_names_the_command_that_fixes_it(self) -> None:
        problem = calibration_error({"mode": "dense"}, "dense", "m")
        self.assertIn("calibrate_answer.py", problem)
        self.assertIn("min_top_score", problem)

    def test_answer_py_refuses_to_run_without_a_measured_threshold(self) -> None:
        missing = Path(tempfile.mkdtemp()) / "answer-calibration.json"
        with self.assertRaises(SystemExit) as raised:
            answer.load_calibration(missing, "dense", "m")
        self.assertIn("calibrate_answer.py", str(raised.exception))


class CitationContractTests(unittest.TestCase):
    """`[n]` has to point at a passage somebody actually retrieved."""

    def test_markers_are_read_in_order_including_repeats(self) -> None:
        self.assertEqual(citation_markers("uno [1] dos [2] otra vez [1]"), [1, 2, 1])

    def test_an_answer_without_citations_fails(self) -> None:
        problems = citation_problems("Los libros dicen que sí.", 3)
        self.assertEqual(len(problems), 1)
        self.assertIn("no cita", problems[0])

    def test_a_marker_nobody_handed_the_writer_is_named(self) -> None:
        problems = citation_problems("Afirmación [1] y otra [9].", 3)
        self.assertIn("[9]", problems[0])
        self.assertIn("se entregaron 3", problems[0])

    def test_zero_is_not_a_citation(self) -> None:
        self.assertTrue(citation_problems("Algo [0].", 3))

    def test_a_well_formed_answer_passes(self) -> None:
        self.assertEqual(citation_problems("Uno [1] y dos [2].", 2), [])

    def test_an_abstention_is_allowed_to_cite_nothing(self) -> None:
        self.assertEqual(citation_problems(ABSTAIN_SENTENCE, 0, require_citation=False), [])


class QuoteGroundingTests(unittest.TestCase):
    """A quote is a pointer into a page, and a short one."""

    def test_a_long_sentence_is_cut_and_says_so(self) -> None:
        sentence = " ".join(f"palabra{n}" for n in range(80))
        clipped = clip_quote(sentence)
        self.assertEqual(len(clipped.split()), MAX_QUOTE_WORDS + 1)
        self.assertTrue(clipped.endswith("…"))

    def test_a_short_sentence_is_left_alone(self) -> None:
        self.assertEqual(clip_quote("System 1 operates  automatically."), "System 1 operates automatically.")

    def test_a_clipped_quote_is_still_grounded_in_its_passage(self) -> None:
        quote = clip_quote(split_sentences(KAHNEMAN_CHUNK)[1], max_words=6)
        self.assertTrue(quote_is_grounded(quote, KAHNEMAN_CHUNK))

    def test_a_translation_or_a_paraphrase_is_not_grounded(self) -> None:
        self.assertFalse(quote_is_grounded("El Sistema 1 opera automáticamente.", KAHNEMAN_CHUNK))
        self.assertFalse(quote_is_grounded("System 1 is fast and System 2 is slow.", KAHNEMAN_CHUNK))

    def test_whitespace_differences_do_not_break_grounding(self) -> None:
        self.assertTrue(quote_is_grounded("System 2   allocates\nattention", KAHNEMAN_CHUNK))

    def test_a_question_mirrors_the_query_and_is_not_evidence(self) -> None:
        # The measured failure: asked about System 1 and System 2, the best
        # scoring sentence in Kahneman was the chapter's own rhetorical
        # question, which answers nothing.
        self.assertFalse(is_evidence_sentence(split_sentences(KAHNEMAN_CHUNK)[0]))
        self.assertTrue(is_evidence_sentence(split_sentences(KAHNEMAN_CHUNK)[1]))

    def test_a_fragment_is_not_evidence_either(self) -> None:
        self.assertFalse(is_evidence_sentence("Chapter 12."))

    def test_sentences_split_on_terminators_and_drop_empties(self) -> None:
        self.assertEqual(len(split_sentences(KAHNEMAN_CHUNK)), 3)


class ExtractiveAnswerTests(unittest.TestCase):
    """The offline answer: Spanish scaffolding, literal quotes, real markers."""

    PICKS = [
        {"number": 1, "quote": "System 1 operates automatically and quickly.",
         "citation": "Daniel Kahneman (2011), Thinking, Fast and Slow", "pages": "pp. 23–24"},
        {"number": 2, "quote": "System 2 allocates attention to effortful activities.",
         "citation": "Daniel Kahneman (2011), Thinking, Fast and Slow", "pages": "p. 25"},
    ]

    def test_the_composed_answer_satisfies_the_citation_contract(self) -> None:
        text = extractive_answer(self.PICKS)
        self.assertEqual(citation_markers(text), [1, 2])
        self.assertEqual(citation_problems(text, len(self.PICKS)), [])

    def test_it_says_it_neither_translates_nor_redacts(self) -> None:
        self.assertIn("no traduce", extractive_answer(self.PICKS))

    def test_an_answer_with_no_passages_is_a_bug_not_an_empty_string(self) -> None:
        with self.assertRaises(ValueError):
            extractive_answer([])

    def test_source_lines_carry_the_path_a_reader_has_to_open(self) -> None:
        line = format_source_line(1, {
            "citation": "Daniel Kahneman (2011), Thinking, Fast and Slow",
            "pages": "pp. 23–24",
            "relative_path": "Behavioral Economics/Kahneman.pdf",
        })
        self.assertTrue(line.startswith("[1] Daniel Kahneman (2011)"))
        self.assertIn("Behavioral Economics/Kahneman.pdf", line)

    def test_sources_are_numbered_from_one(self) -> None:
        with self.assertRaises(ValueError):
            format_source_line(0, {"citation": "x", "pages": "p. 1", "relative_path": "x.pdf"})


class ConsentDisclosureTests(unittest.TestCase):
    """What the person consenting is told before anything is sent."""

    PICKS = ExtractiveAnswerTests.PICKS

    def test_the_disclosure_counts_the_words_that_would_leave(self) -> None:
        disclosure = excerpt_disclosure(self.PICKS)
        self.assertIn("2 fragmentos", disclosure)
        self.assertIn("13 palabras", disclosure)
        self.assertIn("1 obra(s)", disclosure)

    def test_the_warning_says_the_excerpts_leave_the_laptop(self) -> None:
        self.assertIn("salen de esta laptop", CONSENT_WARNING)
        self.assertIn("Anthropic", CONSENT_WARNING)

    def test_the_prompt_carries_the_quotes_and_nothing_else_of_the_corpus(self) -> None:
        prompt = synthesis_prompt("¿Sistema 1 y Sistema 2?", self.PICKS)
        self.assertIn("System 1 operates automatically and quickly.", prompt)
        # The passage the quote was cut from never appears in the payload.
        self.assertNotIn("no sense of voluntary control", prompt)

    def test_the_prompt_authorises_the_model_to_abstain(self) -> None:
        self.assertIn(ABSTAIN_SENTENCE, synthesis_prompt("¿Y?", self.PICKS))

    def test_a_synthesised_abstention_needs_no_citations(self) -> None:
        self.assertEqual(synthesis_problems(ABSTAIN_SENTENCE, self.PICKS), [])

    def test_a_synthesised_answer_citing_an_invented_source_is_rejected(self) -> None:
        self.assertTrue(synthesis_problems("Según [7], sí.", self.PICKS))

    def test_an_empty_completion_is_rejected(self) -> None:
        self.assertTrue(synthesis_problems("   ", self.PICKS))


class SelectEvidenceTests(unittest.TestCase):
    """Choosing what to quote out of a 320-word passage."""

    def test_it_quotes_the_declarative_sentence_not_the_mirrored_question(self) -> None:
        index = answering_index()
        picks = answer.select_evidence(
            index, "System 1 and System 2 differences", index.search(""), 2
        )
        self.assertEqual(len(picks), 2)
        self.assertFalse(picks[0]["quote"].endswith("?"))
        self.assertNotIn("Why call them", picks[0]["quote"])

    def test_every_quote_is_verbatim_from_the_passage_it_cites(self) -> None:
        index = answering_index()
        picks = answer.select_evidence(index, "System 1 automatic", index.search(""), 2)
        for pick in picks:
            self.assertTrue(
                quote_is_grounded(pick["quote"], index.chunks[pick["chunk_id"]]["text"])
            )

    def test_sources_are_numbered_contiguously_from_one(self) -> None:
        index = answering_index()
        picks = answer.select_evidence(index, "System 2 attention", index.search(""), 2)
        self.assertEqual([pick["number"] for pick in picks], [1, 2])

    def test_a_passage_with_no_sentences_is_skipped_not_fatal(self) -> None:
        index = FakeIndex([{"text": "   "}], [fake_result(0, 0.9, "X (2020), Y", "p. 1")])
        self.assertEqual(answer.select_evidence(index, "algo", index.search(""), 1), [])


class BuildAnswerTests(unittest.TestCase):
    """The whole decision, from retrieval to the citation check."""

    QUESTION = "¿Cuáles son las diferencias entre el Sistema 1 y el Sistema 2?"

    def test_weak_evidence_abstains_with_the_numbers_that_decided_it(self) -> None:
        index = FakeIndex(
            [{"text": KAHNEMAN_CHUNK}],
            [fake_result(0, 0.3504, "Daniel Kahneman (2011), Thinking, Fast and Slow", "p. 23")],
        )
        payload = answer.build_answer(index, "¿Receta del ceviche?", CALIBRATION)
        self.assertFalse(payload["answered"])
        self.assertEqual(payload["answer"], ABSTAIN_SENTENCE)
        self.assertEqual(payload["sources"], [])
        self.assertEqual(payload["generator"], "abstained")
        self.assertIn("0.3504", " ".join(payload["notes"]))

    def test_strong_evidence_answers_with_verified_citations(self) -> None:
        payload = answer.build_answer(answering_index(), self.QUESTION, CALIBRATION)
        self.assertTrue(payload["answered"])
        self.assertEqual(payload["generator"], "extractive")
        self.assertTrue(payload["citation_check"]["ok"])
        self.assertEqual(len(payload["sources"]), 2)
        self.assertEqual(citation_markers(payload["answer"]), [1, 2])

    def test_the_payload_carries_pages_and_paths_but_not_whole_passages(self) -> None:
        payload = answer.build_answer(answering_index(), self.QUESTION, CALIBRATION)
        source = payload["sources"][0]
        self.assertIn("pages", source)
        self.assertIn("relative_path", source)
        self.assertLessEqual(len(source["quote"].split()), MAX_QUOTE_WORDS + 1)
        self.assertNotIn(KAHNEMAN_CHUNK, json.dumps(payload, ensure_ascii=False))

    def test_an_unseparable_calibration_is_flagged_on_every_answer(self) -> None:
        calibration = {**CALIBRATION, "separable": False}
        payload = answer.build_answer(answering_index(), self.QUESTION, calibration)
        self.assertIn("no separa", " ".join(payload["notes"]))

    def test_the_cloud_generator_does_nothing_without_consent(self) -> None:
        with quiet(), patch.object(answer, "synthesize_with_claude") as never:
            payload = answer.build_answer(
                answering_index(), self.QUESTION, CALIBRATION,
                generator="claude_cli", send_excerpts=False, interactive=False,
            )
        never.assert_not_called()
        self.assertEqual(payload["generator"], "extractive")
        self.assertIn("no se envió nada", " ".join(payload["notes"]))

    def test_with_consent_a_valid_synthesis_is_shown_and_labelled(self) -> None:
        with patch.object(
            answer, "synthesize_with_claude",
            return_value=("El Sistema 1 es automático [1]; el 2 es deliberado [2].", "ok"),
        ):
            payload = answer.build_answer(
                answering_index(), self.QUESTION, CALIBRATION,
                generator="claude_cli", send_excerpts=True,
            )
        self.assertEqual(payload["generator"], "claude_cli")
        self.assertTrue(payload["citation_check"]["ok"])
        self.assertIn("palabras en total", " ".join(payload["notes"]))

    def test_a_cloud_abstention_is_a_valid_final_decision(self) -> None:
        with patch.object(
            answer, "synthesize_with_claude",
            return_value=(ABSTAIN_SENTENCE, "ok"),
        ):
            payload = answer.build_answer(
                answering_index(), self.QUESTION, CALIBRATION,
                generator="claude_cli", send_excerpts=True,
            )
        self.assertFalse(payload["answered"])
        self.assertEqual(payload["generator"], "claude_cli")
        self.assertEqual(payload["answer"], ABSTAIN_SENTENCE)
        self.assertTrue(payload["verdict"]["answer"])
        self.assertTrue(payload["citation_check"]["ok"])
        self.assertIn("Opus concluyó", " ".join(payload["notes"]))

    def test_a_synthesis_citing_an_invented_source_falls_back_to_the_quotes(self) -> None:
        with patch.object(
            answer, "synthesize_with_claude",
            return_value=("Según Camerer [9], el Sistema 1 decide.", "ok"),
        ):
            payload = answer.build_answer(
                answering_index(), self.QUESTION, CALIBRATION,
                generator="claude_cli", send_excerpts=True,
            )
        self.assertEqual(payload["generator"], "extractive")
        self.assertTrue(payload["citation_check"]["ok"])
        self.assertIn("falló el control de citas", " ".join(payload["notes"]))

    def test_a_failed_call_falls_back_and_says_why(self) -> None:
        with patch.object(
            answer, "synthesize_with_claude",
            return_value=("", "El CLI `claude` no respondió en 90 s."),
        ):
            payload = answer.build_answer(
                answering_index(), self.QUESTION, CALIBRATION,
                generator="claude_cli", send_excerpts=True,
            )
        self.assertEqual(payload["generator"], "extractive")
        self.assertIn("no respondió", " ".join(payload["notes"]))
        self.assertTrue(payload["citation_check"]["ok"])


class ClaudeCliTests(unittest.TestCase):
    """Every way an external process fails is a note, never a traceback."""

    def test_a_timeout_returns_no_answer_and_an_explanation(self) -> None:
        with patch.object(answer.shutil, "which", return_value="/usr/bin/claude"), patch.object(
            answer.subprocess, "run",
            side_effect=answer.subprocess.TimeoutExpired(cmd="claude", timeout=90),
        ):
            text, note = answer.synthesize_with_claude("prompt", timeout=90)
        self.assertEqual(text, "")
        self.assertIn("90 s", note)

    def test_a_missing_cli_is_reported_without_calling_anything(self) -> None:
        with patch.object(answer.shutil, "which", return_value=None):
            text, note = answer.synthesize_with_claude("prompt")
        self.assertEqual(text, "")
        self.assertIn("PATH", note)

    def test_a_non_zero_exit_carries_the_last_line_of_stderr(self) -> None:
        completed = types.SimpleNamespace(returncode=2, stdout="", stderr="credit balance too low")
        with patch.object(answer.shutil, "which", return_value="/usr/bin/claude"), patch.object(
            answer.subprocess, "run", return_value=completed
        ):
            text, note = answer.synthesize_with_claude("prompt")
        self.assertEqual(text, "")
        self.assertIn("credit balance too low", note)

    def test_an_empty_completion_is_treated_as_a_failure(self) -> None:
        completed = types.SimpleNamespace(returncode=0, stdout="  \n", stderr="")
        with patch.object(answer.shutil, "which", return_value="/usr/bin/claude"), patch.object(
            answer.subprocess, "run", return_value=completed
        ):
            text, note = answer.synthesize_with_claude("prompt")
        self.assertEqual(text, "")
        self.assertIn("vacía", note)

    def test_the_prompt_is_passed_as_an_argument_and_stdin_is_closed(self) -> None:
        completed = types.SimpleNamespace(returncode=0, stdout="Respuesta [1].", stderr="")
        with patch.object(answer.shutil, "which", return_value="/usr/bin/claude"), patch.object(
            answer.subprocess, "run", return_value=completed
        ) as run:
            text, _ = answer.synthesize_with_claude("PROMPT")
        self.assertEqual(text, "Respuesta [1].")
        command = run.call_args.args[0]
        self.assertEqual(command[:3], ["/usr/bin/claude", "-p", "PROMPT"])
        self.assertEqual(command[3:], ["--model", answer.CLAUDE_MODEL])
        self.assertEqual(run.call_args.kwargs["stdin"], answer.subprocess.DEVNULL)


class ConsentGateTests(unittest.TestCase):
    """`--send-excerpts`, a typed answer, or nothing leaves the machine."""

    PICKS = ExtractiveAnswerTests.PICKS

    def test_the_flag_is_consent_given_in_advance(self) -> None:
        self.assertTrue(answer.consent_granted(self.PICKS, True, interactive=False))

    def test_a_pipe_cannot_consent_on_a_persons_behalf(self) -> None:
        with quiet():
            self.assertFalse(answer.consent_granted(self.PICKS, False, interactive=False))

    def test_the_warning_is_printed_before_the_question_is_asked(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stderr(stream), patch("builtins.input", return_value="n"):
            answer.consent_granted(self.PICKS, False, interactive=True)
        self.assertIn("salen de esta laptop", stream.getvalue())
        self.assertIn("13 palabras", stream.getvalue())

    def test_a_typed_yes_is_consent_and_anything_else_is_not(self) -> None:
        with quiet(), patch("builtins.input", return_value="s"):
            self.assertTrue(answer.consent_granted(self.PICKS, False, interactive=True))
        with quiet(), patch("builtins.input", return_value=""):
            self.assertFalse(answer.consent_granted(self.PICKS, False, interactive=True))
        with quiet(), patch("builtins.input", return_value="no"):
            self.assertFalse(answer.consent_granted(self.PICKS, False, interactive=True))


class LocalhostServerTests(unittest.TestCase):
    """The browser demo may not become a file server for a copyrighted library."""

    def setUp(self) -> None:
        self.state = {
            "index": answering_index(),
            "calibration": CALIBRATION,
            "mode": "dense",
            "timeout": 5,
            "lock": threading.Lock(),
        }

    def test_binding_outside_loopback_is_refused_with_a_reason(self) -> None:
        args = types.SimpleNamespace(host="0.0.0.0", port=8000)
        with patch.object(serve, "parse_args", return_value=args):
            with self.assertRaises(SystemExit) as raised:
                serve.main()
        self.assertIn("0.0.0.0", str(raised.exception))
        self.assertIn("derechos de autor", str(raised.exception))

    def test_loopback_host_headers_are_accepted_with_or_without_a_port(self) -> None:
        for header in ("127.0.0.1:8000", "localhost:8000", "localhost", "[::1]:8000"):
            self.assertTrue(serve.host_is_loopback(header), header)

    def test_a_rebinding_hostname_is_rejected(self) -> None:
        for header in ("evil.example.com", "evil.example.com:8000", "192.168.1.20:8000", "", None):
            self.assertFalse(serve.host_is_loopback(header), header)

    def test_an_empty_or_oversized_question_is_a_client_error(self) -> None:
        with self.assertRaises(ValueError):
            serve.answer_request(self.state, {"question": "   "})
        with self.assertRaises(ValueError):
            serve.answer_request(self.state, {"question": "x" * 501})

    def test_an_unknown_generator_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            serve.answer_request(self.state, {"question": "¿Sistema 1?", "generator": "gpt"})

    def test_the_server_re_decides_consent_instead_of_trusting_the_browser(self) -> None:
        with quiet(), patch.object(answer, "synthesize_with_claude") as never:
            payload = serve.answer_request(
                self.state,
                {"question": "¿Sistema 1 y 2?", "generator": "claude_cli", "consent": False},
            )
        never.assert_not_called()
        self.assertEqual(payload["generator"], "extractive")
        self.assertIn("no se envió nada", " ".join(payload["notes"]))

    def test_a_ticked_box_reaches_the_generator_as_consent(self) -> None:
        with patch.object(
            answer, "synthesize_with_claude", return_value=("Sí [1].", "ok")
        ) as called:
            payload = serve.answer_request(
                self.state,
                {"question": "¿Sistema 1 y 2?", "generator": "claude_cli", "consent": True},
            )
        called.assert_called_once()
        self.assertEqual(payload["generator"], "claude_cli")

    def test_an_absurd_limit_is_clamped_rather_than_honoured(self) -> None:
        payload = serve.answer_request(
            self.state, {"question": "¿Sistema 1 y 2?", "limit": 900}
        )
        self.assertLessEqual(len(payload["sources"]), 8)
        payload = serve.answer_request(
            self.state, {"question": "¿Sistema 1 y 2?", "limit": "muchos"}
        )
        self.assertTrue(payload["answered"])

    def test_the_page_carries_the_warning_and_loads_nothing_from_the_network(self) -> None:
        page = serve.render_page().decode("utf-8")
        self.assertIn("salen de esta laptop", page)
        self.assertNotIn("CONSENT_WARNING_TEXT", page)
        self.assertNotIn("http://", page)
        self.assertNotIn("https://", page)


if __name__ == "__main__":
    unittest.main()
