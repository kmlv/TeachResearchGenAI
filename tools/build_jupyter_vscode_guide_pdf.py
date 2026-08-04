#!/usr/bin/env python3
"""Build the Jupyter/VS Code/Codex guide PDF from its Markdown source."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
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
SOURCE = ROOT / "deliverables" / "guia-demo-jupyter-vscode-codex.md"
OUTPUT = ROOT / "output" / "pdf" / "guia-demo-jupyter-vscode-codex.pdf"

NAVY = colors.HexColor("#17233B")
TEAL = colors.HexColor("#007F7B")
PALE_TEAL = colors.HexColor("#E8F4F3")
PALE_BLUE = colors.HexColor("#EDF2F8")
INK = colors.HexColor("#243041")
MUTED = colors.HexColor("#667085")
RULE = colors.HexColor("#D7DEE8")
CODE_BG = colors.HexColor("#F5F7FA")


def register_fonts() -> None:
    base = Path("/System/Library/Fonts/Supplemental")
    pdfmetrics.registerFont(TTFont("GuideSans", str(base / "Arial.ttf")))
    pdfmetrics.registerFont(TTFont("GuideSans-Bold", str(base / "Arial Bold.ttf")))
    pdfmetrics.registerFont(TTFont("GuideSans-Italic", str(base / "Arial Italic.ttf")))
    pdfmetrics.registerFont(TTFont("GuideMono", "/System/Library/Fonts/Menlo.ttc", subfontIndex=0))


class GuideDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=19 * mm,
            bottomMargin=18 * mm,
            title="Guía personal: Jupyter Notebooks en VS Code con Codex",
            author="Kristian López Vargas",
            subject="Runbook detallado para el demo de análisis de datos",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
        )
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
        canvas.drawString(doc.leftMargin, height - 8.5 * mm, "Jupyter en VS Code con Codex")
    canvas.setFont("GuideSans", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 9 * mm, "TeachResearchGenAI · guía personal")
    canvas.drawRightString(width - doc.rightMargin, 9 * mm, f"{doc.page}")
    canvas.restoreState()


def styles():
    sheet = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=sheet["BodyText"],
        fontName="GuideSans",
        fontSize=9.2,
        leading=13.1,
        textColor=INK,
        spaceAfter=5.5,
        allowWidows=0,
        allowOrphans=0,
    )
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=body,
            fontName="GuideSans-Bold",
            fontSize=27,
            leading=31,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=7,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=body,
            fontName="GuideSans",
            fontSize=16,
            leading=20,
            textColor=TEAL,
            spaceAfter=22,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=body,
            fontSize=9,
            leading=13,
            textColor=MUTED,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=body,
            fontName="GuideSans-Bold",
            fontSize=18,
            leading=22,
            textColor=NAVY,
            spaceBefore=12,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=body,
            fontName="GuideSans-Bold",
            fontSize=14.5,
            leading=18,
            textColor=NAVY,
            spaceBefore=11,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=body,
            fontName="GuideSans-Bold",
            fontSize=11.2,
            leading=14,
            textColor=TEAL,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": body,
        "list": ParagraphStyle(
            "List",
            parent=body,
            leftIndent=1,
            firstLineIndent=0,
            spaceAfter=2.5,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=body,
            fontName="GuideMono",
            fontSize=7.6,
            leading=10.2,
            textColor=colors.HexColor("#263444"),
            leftIndent=0,
            rightIndent=0,
            spaceAfter=0,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=body,
            fontName="GuideSans-Bold",
            fontSize=10.5,
            leading=15,
            textColor=NAVY,
            leftIndent=0,
            rightIndent=0,
            alignment=TA_LEFT,
        ),
        "source": ParagraphStyle(
            "Source",
            parent=body,
            fontSize=7.6,
            leading=10.5,
            textColor=MUTED,
        ),
    }


URL_RE = re.compile(r"(https?://[^\s<]+)")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = BOLD_RE.sub(r"<b>\1</b>", escaped)
    escaped = CODE_RE.sub(r'<font name="GuideMono" size="8">\1</font>', escaped)
    escaped = URL_RE.sub(r'<link href="\1" color="#007F7B">\1</link>', escaped)
    return escaped


def code_box(code: str, st) -> Table:
    pre = Preformatted(code.rstrip(), st["code"], maxLineLength=92)
    table = Table([[pre]], colWidths=[166 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, RULE),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def quote_box(text: str, st) -> Table:
    table = Table([[Paragraph(inline(text), st["quote"])]], colWidths=[166 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_TEAL),
                ("LINEBEFORE", (0, 0), (0, -1), 3, TEAL),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def flush_paragraph(buffer: list[str], story: list, st) -> None:
    if not buffer:
        return
    text = " ".join(part.strip() for part in buffer).strip()
    if text:
        story.append(Paragraph(inline(text), st["body"]))
    buffer.clear()


def flush_list(items: list[str], ordered: bool, story: list, st) -> None:
    if not items:
        return
    all_checkboxes = all(item.startswith("[ ] ") for item in items)
    if all_checkboxes:
        checkbox_style = ParagraphStyle(
            "CheckboxList",
            parent=st["list"],
            leftIndent=8,
            spaceAfter=4,
        )
        for item in items:
            story.append(Paragraph(inline("☐ " + item[4:]), checkbox_style))
        story.append(Spacer(1, 2))
        items.clear()
        return
    flow_items = []
    for item in items:
        flow_items.append(ListItem(Paragraph(inline(item), st["list"]), leftIndent=11))
    list_kwargs = {
        "bulletType": "1" if ordered else "bullet",
        "leftIndent": 16,
        "bulletFontName": "GuideSans",
        "bulletFontSize": 8.5,
        "bulletColor": TEAL,
        "spaceAfter": 5,
    }
    if ordered:
        list_kwargs["start"] = "1"
    else:
        list_kwargs["bulletChar"] = "•"
    story.append(ListFlowable(flow_items, **list_kwargs))
    items.clear()


def build_story(markdown: str):
    st = styles()
    lines = markdown.splitlines()
    story = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_ordered = False
    in_code = False
    code_lines: list[str] = []
    seen_main_title = False

    def flush_all():
        nonlocal list_ordered
        flush_paragraph(paragraph, story, st)
        flush_list(list_items, list_ordered, story, st)
        list_ordered = False

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            flush_all()
            if in_code:
                story.append(code_box("\n".join(code_lines), st))
                story.append(Spacer(1, 6))
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            flush_all()
            continue
        if line == "<!-- pagebreak -->":
            flush_all()
            story.append(PageBreak())
            continue
        if line == "---":
            flush_all()
            story.append(HRFlowable(width="100%", thickness=0.8, color=RULE, spaceBefore=5, spaceAfter=8))
            continue
        if line.startswith("# "):
            flush_all()
            title = line[2:].strip()
            if not seen_main_title:
                story.extend(
                    [
                        Spacer(1, 28 * mm),
                        Paragraph(inline(title), st["cover_title"]),
                    ]
                )
                seen_main_title = True
            else:
                story.append(Paragraph(inline(title), st["h1"]))
            continue
        if line.startswith("## "):
            flush_all()
            text = line[3:].strip()
            if len(story) < 4:
                story.append(Paragraph(inline(text), st["cover_subtitle"]))
            else:
                if text == "Fuentes oficiales":
                    story.append(PageBreak())
                story.append(Paragraph(inline(text), st["h2"]))
            continue
        if line.startswith("### "):
            flush_all()
            story.append(Paragraph(inline(line[4:].strip()), st["h3"]))
            continue
        if line.startswith("> "):
            flush_all()
            story.append(quote_box(line[2:].strip(), st))
            story.append(Spacer(1, 5))
            continue
        m_ordered = re.match(r"^\d+\.\s+(.*)", line)
        if m_ordered:
            flush_paragraph(paragraph, story, st)
            if list_items and not list_ordered:
                flush_list(list_items, False, story, st)
            list_ordered = True
            list_items.append(m_ordered.group(1))
            continue
        if line.startswith("- "):
            flush_paragraph(paragraph, story, st)
            if list_items and list_ordered:
                flush_list(list_items, True, story, st)
            list_ordered = False
            list_items.append(line[2:].strip())
            continue
        if line.startswith("**") and line.endswith("**") and len(story) < 10:
            flush_all()
            story.append(Paragraph(inline(line), st["meta"]))
            continue
        paragraph.append(line)

    flush_all()
    if in_code and code_lines:
        story.append(code_box("\n".join(code_lines), st))

    # Force the substantive guide to start cleanly after the cover metadata.
    for index, flowable in enumerate(story):
        if isinstance(flowable, HRFlowable):
            story[index] = PageBreak()
            break
    return story


def main() -> None:
    register_fonts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    markdown = SOURCE.read_text(encoding="utf-8")
    doc = GuideDocTemplate(str(OUTPUT))
    doc.build(build_story(markdown))
    print(OUTPUT)


if __name__ == "__main__":
    main()
