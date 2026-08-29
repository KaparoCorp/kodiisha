#!/usr/bin/env python3
"""Generate the PROPATIA calculation audit PDF from Markdown source."""

from __future__ import annotations

import html
import re
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "propatia_calculation_audit.md"
OUTPUT = ROOT / "propatia_calculation_audit.pdf"


def read_source() -> str:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing source document: {SOURCE}")
    return SOURCE.read_text(encoding="utf-8")


def try_reportlab(markdown_text: str) -> bool:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
    except ImportError:
        return False

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=42,
        title="PROPATIA Calculation Audit",
    )
    story = []

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if line == "<!-- pagebreak -->":
            story.append(PageBreak())
            continue
        if not line:
            story.append(Spacer(1, 6))
            continue

        style_name = "BodyText"
        if line.startswith("# "):
            style_name = "Title"
            line = line[2:]
        elif line.startswith("## "):
            style_name = "Heading1"
            line = line[3:]
        elif line.startswith("### "):
            style_name = "Heading2"
            line = line[4:]
        elif line.startswith("- "):
            line = "&bull; " + line[2:]

        line = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", html.escape(line))
        line = line.replace("&lt;font name=&#x27;Courier&#x27;&gt;", "<font name='Courier'>")
        line = line.replace("&lt;/font&gt;", "</font>")
        story.append(Paragraph(line, styles[style_name]))

    doc.build(story)
    return True


def markdown_to_pdf_lines(markdown_text: str) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    for raw_line in markdown_text.splitlines():
        stripped = raw_line.strip()
        if stripped == "<!-- pagebreak -->":
            lines.append(("", "pagebreak"))
        elif not stripped:
            lines.append(("", "blank"))
        elif stripped.startswith("# "):
            lines.append((stripped[2:], "title"))
        elif stripped.startswith("## "):
            lines.append((stripped[3:], "section"))
        elif stripped.startswith("### "):
            lines.append((stripped[4:], "subsection"))
        elif stripped.startswith("- "):
            lines.append(("  - " + stripped[2:], "bullet"))
        else:
            lines.append((stripped, "body"))
    return lines


def wrap_line(text: str, kind: str) -> list[str]:
    widths = {
        "title": 54,
        "section": 62,
        "subsection": 76,
        "bullet": 92,
        "body": 96,
    }
    if kind == "blank":
        return [""]
    if kind == "bullet":
        return textwrap.wrap(text, width=widths[kind], subsequent_indent="    ") or [text]
    return textwrap.wrap(text, width=widths.get(kind, 96)) or [text]


def paginate(lines: list[tuple[str, str]]) -> list[list[tuple[str, str]]]:
    pages: list[list[tuple[str, str]]] = [[]]
    usable_height = 692
    used = 0

    def line_height(kind: str) -> int:
        if kind == "title":
            return 22
        if kind == "section":
            return 20
        if kind == "subsection":
            return 16
        if kind == "blank":
            return 8
        return 12

    for text, kind in lines:
        if kind == "pagebreak":
            if pages[-1]:
                pages.append([])
                used = 0
            continue

        wrapped = wrap_line(text, kind)
        block_height = sum(line_height(kind) for _ in wrapped)
        if pages[-1] and used + block_height > usable_height:
            pages.append([])
            used = 0

        for wrapped_line in wrapped:
            pages[-1].append((wrapped_line, kind))
            used += line_height(kind)

    return [page for page in pages if page]


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def render_page(page: list[tuple[str, str]], page_number: int, total_pages: int) -> bytes:
    y = 742
    chunks = []
    for text, kind in page:
        if kind == "blank":
            y -= 8
            continue
        font = "F1"
        size = 9
        leading = 12
        if kind == "title":
            font = "F2"
            size = 16
            leading = 22
        elif kind == "section":
            font = "F2"
            size = 14
            leading = 20
        elif kind == "subsection":
            font = "F2"
            size = 10
            leading = 16

        chunks.append(f"BT /{font} {size} Tf 54 {y} Td ({pdf_escape(text)}) Tj ET")
        y -= leading

    footer = f"Page {page_number} of {total_pages}"
    chunks.append(f"BT /F1 8 Tf 54 30 Td ({footer}) Tj ET")
    return "\n".join(chunks).encode("latin-1", errors="replace")


def write_minimal_pdf(markdown_text: str) -> None:
    lines = markdown_to_pdf_lines(markdown_text)
    pages = paginate(lines)
    page_count = len(pages)

    font1_id = 2 * page_count + 3
    font2_id = 2 * page_count + 4
    objects: dict[int, bytes] = {}

    page_ids = [3 + (idx * 2) for idx in range(page_count)]
    objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>".encode("ascii")

    for idx, page in enumerate(pages):
        page_id = 3 + (idx * 2)
        content_id = page_id + 1
        content = render_page(page, idx + 1, page_count)
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font1_id} 0 R /F2 {font2_id} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        ).encode("ascii")
        objects[content_id] = b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream"

    objects[font1_id] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objects[font2_id] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {0: 0}
    max_obj_id = max(objects)
    for obj_id in range(1, max_obj_id + 1):
        offsets[obj_id] = len(pdf)
        pdf.extend(f"{obj_id} 0 obj\n".encode("ascii"))
        pdf.extend(objects[obj_id])
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {max_obj_id + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for obj_id in range(1, max_obj_id + 1):
        pdf.extend(f"{offsets[obj_id]:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {max_obj_id + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )

    OUTPUT.write_bytes(pdf)


def main() -> int:
    markdown_text = read_source()
    if not try_reportlab(markdown_text):
        write_minimal_pdf(markdown_text)

    if not OUTPUT.exists() or OUTPUT.stat().st_size == 0:
        print(f"Failed to generate {OUTPUT}", file=sys.stderr)
        return 1

    print(f"Generated {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
