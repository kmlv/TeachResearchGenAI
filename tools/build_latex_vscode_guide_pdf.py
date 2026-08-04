#!/usr/bin/env python3
"""Build the LaTeX/VS Code workflow guide as a styled, linked PDF."""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables" / "guia-flujo-latex-vscode.md"
OUTPUT = ROOT / "output" / "pdf" / "guia-flujo-latex-vscode.pdf"
MATERIALS = ROOT / "materials" / "guides" / "guia-flujo-latex-vscode.pdf"

NAVY = colors.HexColor("#17233B")
TEAL = colors.HexColor("#007F7B")
PALE_TEAL = colors.HexColor("#E8F4F3")
INK = colors.HexColor("#243041")
MUTED = colors.HexColor("#667085")
RULE = colors.HexColor("#D7DEE8")
CODE_BG = colors.HexColor("#F5F7FA")
WHITE = colors.white


def register_fonts() -> None:
    mac = Path("/System/Library/Fonts/Supplemental")
    if (mac / "Arial.ttf").exists():
        sans = mac / "Arial.ttf"
        bold = mac / "Arial Bold.ttf"
        italic = mac / "Arial Italic.ttf"
        mono = Path("/System/Library/Fonts/Menlo.ttc")
        mono_kwargs = {"subfontIndex": 0}
    else:
        sans = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
        italic = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf")
        mono = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
        mono_kwargs = {}
    pdfmetrics.registerFont(TTFont("GuideSans", str(sans)))
    pdfmetrics.registerFont(TTFont("GuideSans-Bold", str(bold)))
    pdfmetrics.registerFont(TTFont("GuideSans-Italic", str(italic)))
    pdfmetrics.registerFont(TTFont("GuideMono", str(mono), **mono_kwargs))


class GuideDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=19 * mm,
            bottomMargin=18 * mm,
            title="Flujo de trabajo para LaTeX en VS Code",
            author="Kristian López Vargas",
            subject="Guía práctica de edición, SyncTeX y colaboración con Overleaf",
        )
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal")
        self.addPageTemplates(PageTemplate(id="guide", frames=frame, onPage=draw_page))


def draw_page(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    if doc.page == 1:
        canvas.setFillColor(NAVY)
        canvas.rect(0, height - 8 * mm, width, 8 * mm, stroke=0, fill=1)
    else:
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, height - 11 * mm, width - doc.rightMargin, height - 11 * mm)
        canvas.setFont("GuideSans", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(doc.leftMargin, height - 8.5 * mm, "LaTeX en VS Code")
    canvas.setFont("GuideSans", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 9 * mm, "TeachResearchGenAI · guía práctica")
    canvas.drawRightString(width - doc.rightMargin, 9 * mm, str(doc.page))
    canvas.restoreState()


def make_styles() -> dict[str, ParagraphStyle]:
    sheet = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=sheet["BodyText"],
        fontName="GuideSans",
        fontSize=9.15,
        leading=12.8,
        textColor=INK,
        spaceAfter=5.2,
        allowWidows=0,
        allowOrphans=0,
    )
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle", parent=body, fontName="GuideSans-Bold", fontSize=27,
            leading=31, textColor=NAVY, alignment=TA_LEFT, spaceAfter=8,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle", parent=body, fontSize=15.5, leading=20,
            textColor=TEAL, spaceAfter=22,
        ),
        "meta": ParagraphStyle("Meta", parent=body, fontSize=9, leading=13, textColor=MUTED),
        "h1": ParagraphStyle(
            "H1", parent=body, fontName="GuideSans-Bold", fontSize=17.5,
            leading=21, textColor=NAVY, spaceBefore=8, spaceAfter=8, keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2", parent=body, fontName="GuideSans-Bold", fontSize=14.2,
            leading=17, textColor=NAVY, spaceBefore=8, spaceAfter=6, keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3", parent=body, fontName="GuideSans-Bold", fontSize=10.9,
            leading=14, textColor=TEAL, spaceBefore=7, spaceAfter=4, keepWithNext=True,
        ),
        "body": body,
        "list": ParagraphStyle("List", parent=body, spaceAfter=2.2),
        "code": ParagraphStyle(
            "Code", parent=body, fontName="GuideMono", fontSize=7.25,
            leading=9.6, textColor=colors.HexColor("#263444"), spaceAfter=0,
        ),
        "quote": ParagraphStyle(
            "Quote", parent=body, fontName="GuideSans-Bold", fontSize=9.8,
            leading=14, textColor=NAVY,
        ),
        "table_header": ParagraphStyle(
            "TableHeader", parent=body, fontName="GuideSans-Bold", fontSize=7.5,
            leading=9.4, textColor=WHITE, spaceAfter=0,
        ),
        "table_body": ParagraphStyle(
            "TableBody", parent=body, fontSize=7.45, leading=9.4,
            textColor=INK, spaceAfter=0,
        ),
        "source": ParagraphStyle(
            "Source", parent=body, fontSize=7.2, leading=9.7, textColor=MUTED,
        ),
    }


URL_RE = re.compile(r"(https?://[^\s<]+)")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = BOLD_RE.sub(r"<b>\1</b>", escaped)
    escaped = ITALIC_RE.sub(r"<i>\1</i>", escaped)
    escaped = CODE_RE.sub(r'<font name="GuideMono" size="7.5">\1</font>', escaped)
    escaped = URL_RE.sub(r'<link href="\1" color="#007F7B">\1</link>', escaped)
    return escaped


def code_box(code: str, st: dict[str, ParagraphStyle]) -> Table:
    pre = Preformatted(code.rstrip(), st["code"], maxLineLength=94)
    table = Table([[pre]], colWidths=[166 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def quote_box(text: str, st: dict[str, ParagraphStyle]) -> Table:
    table = Table([[Paragraph(inline(text), st["quote"])]], colWidths=[166 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE_TEAL),
        ("LINEBEFORE", (0, 0), (0, -1), 3, TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def markdown_table(rows: list[list[str]], st: dict[str, ParagraphStyle]) -> Table:
    columns = len(rows[0])
    widths_by_count = {
        2: [52 * mm, 114 * mm],
        3: [39 * mm, 58 * mm, 69 * mm],
        4: [33 * mm, 41 * mm, 44 * mm, 48 * mm],
    }
    widths = widths_by_count.get(columns, [166 * mm / columns] * columns)
    data = []
    for row_index, row in enumerate(rows):
        style = st["table_header"] if row_index == 0 else st["table_body"]
        data.append([Paragraph(inline(cell.strip()), style) for cell in row])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FB")]),
        ("GRID", (0, 0), (-1, -1), 0.35, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def parse_table(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    index = start
    while index < len(lines) and lines[index].strip().startswith("|"):
        cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
        if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            rows.append(cells)
        index += 1
    return rows, index


def build_story(markdown: str) -> list:
    st = make_styles()
    lines = markdown.splitlines()
    story: list = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_ordered = False
    in_code = False
    code_lines: list[str] = []
    seen_title = False
    source_section = False

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph).strip()
            if text:
                style = st["source"] if source_section else st["body"]
                story.append(Paragraph(inline(text), style))
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_ordered
        if not list_items:
            return
        flow_items = [
            ListItem(Paragraph(inline(item), st["list"]), leftIndent=11)
            for item in list_items
        ]
        kwargs = {
            "bulletType": "1" if list_ordered else "bullet",
            "leftIndent": 16,
            "bulletFontName": "GuideSans",
            "bulletFontSize": 8.3,
            "bulletColor": TEAL,
            "spaceAfter": 5,
        }
        if list_ordered:
            kwargs["start"] = "1"
        else:
            kwargs["bulletChar"] = "•"
        story.append(ListFlowable(flow_items, **kwargs))
        list_items.clear()
        list_ordered = False

    def flush_all() -> None:
        flush_paragraph()
        flush_list()

    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        if line.startswith("```"):
            flush_all()
            if in_code:
                story.append(code_box("\n".join(code_lines), st))
                story.append(Spacer(1, 5))
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            index += 1
            continue
        if in_code:
            code_lines.append(line)
            index += 1
            continue
        if line.strip().startswith("|") and index + 1 < len(lines) and "---" in lines[index + 1]:
            flush_all()
            rows, index = parse_table(lines, index)
            story.append(markdown_table(rows, st))
            story.append(Spacer(1, 6))
            continue
        if not line.strip():
            flush_all()
            index += 1
            continue
        if line == "<!-- pagebreak -->":
            flush_all()
            story.append(PageBreak())
            index += 1
            continue
        if line == "---":
            flush_all()
            story.append(HRFlowable(width="100%", thickness=0.8, color=RULE, spaceBefore=5, spaceAfter=8))
            index += 1
            continue
        if line.startswith("# "):
            flush_all()
            title = line[2:].strip()
            if not seen_title:
                story.extend([Spacer(1, 28 * mm), Paragraph(inline(title), st["cover_title"])])
                seen_title = True
            else:
                story.append(Paragraph(inline(title), st["h1"]))
            index += 1
            continue
        if line.startswith("## "):
            flush_all()
            title = line[3:].strip()
            source_section = title == "Fuentes oficiales"
            if len(story) < 4:
                story.append(Paragraph(inline(title), st["cover_subtitle"]))
            else:
                story.append(Paragraph(inline(title), st["h2"]))
            index += 1
            continue
        if line.startswith("### "):
            flush_all()
            story.append(Paragraph(inline(line[4:].strip()), st["h3"]))
            index += 1
            continue
        if line.startswith("> "):
            flush_all()
            story.append(quote_box(line[2:].strip(), st))
            story.append(Spacer(1, 5))
            index += 1
            continue
        ordered = re.match(r"^\d+\.\s+(.*)", line)
        if ordered:
            flush_paragraph()
            if list_items and not list_ordered:
                flush_list()
            list_ordered = True
            list_items.append(ordered.group(1))
            index += 1
            continue
        if line.startswith("- "):
            flush_paragraph()
            if list_items and list_ordered:
                flush_list()
            list_ordered = False
            list_items.append(line[2:].strip())
            index += 1
            continue
        if line.startswith("**") and line.rstrip().endswith("  ") and len(story) < 12:
            flush_all()
            story.append(Paragraph(inline(line.strip()), st["meta"]))
            index += 1
            continue
        paragraph.append(line)
        index += 1

    flush_all()
    if in_code and code_lines:
        story.append(code_box("\n".join(code_lines), st))

    for idx, flowable in enumerate(story):
        if isinstance(flowable, HRFlowable):
            story[idx] = PageBreak()
            break
    return story


def main() -> None:
    register_fonts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    MATERIALS.parent.mkdir(parents=True, exist_ok=True)
    document = GuideDocTemplate(str(OUTPUT))
    document.build(build_story(SOURCE.read_text(encoding="utf-8")))
    shutil.copyfile(OUTPUT, MATERIALS)
    print(MATERIALS)


if __name__ == "__main__":
    main()
