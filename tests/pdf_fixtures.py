"""Build real PDFs in memory so the parser is tested against actual files.

A test that feeds `parse_pdf` a hand-written byte string proves nothing --
it would not exercise pypdf at all. These produce genuine PDFs, including
the awkward shapes that break extraction in practice.
"""

from __future__ import annotations

import textwrap

from fpdf import FPDF

WRAP = 95


def _lines(text: str) -> list[str]:
    """fpdf raises if a line has no break point inside the page width."""
    out: list[str] = []
    for raw in text.splitlines():
        safe = raw.encode("latin-1", "replace").decode("latin-1")
        out.extend(textwrap.wrap(safe, WRAP) or [""])
    return out


def single_column(text: str) -> bytes:
    pdf = FPDF()
    pdf.set_margins(12, 12, 12)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    for line in _lines(text):
        if line.strip():
            # explicit width: w=0 measures from the current x, which after a
            # wrapped cell can leave no room and makes fpdf raise
            pdf.multi_cell(pdf.epw, 5, line, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.ln(5)
    return bytes(pdf.output())


def two_column(left: str, right: str) -> bytes:
    """The layout PDF extraction handles worst -- text interleaves."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=9)
    lefts, rights = _lines(left), _lines(right)
    for i in range(max(len(lefts), len(rights))):
        pdf.set_xy(10, 10 + i * 5)
        pdf.cell(85, 5, lefts[i][:60] if i < len(lefts) else "")
        pdf.set_xy(105, 10 + i * 5)
        pdf.cell(85, 5, rights[i][:60] if i < len(rights) else "")
    return bytes(pdf.output())


def image_only() -> bytes:
    """A scan: a page with no text layer at all."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(200, 200, 200)
    pdf.rect(20, 20, 170, 200, style="F")
    return bytes(pdf.output())


def many_pages(text: str, pages: int) -> bytes:
    pdf = FPDF()
    pdf.set_font("Helvetica", size=10)
    for n in range(pages):
        pdf.add_page()
        pdf.multi_cell(pdf.epw, 5, f"Page {n + 1}", new_x="LMARGIN", new_y="NEXT")
        for line in _lines(text)[:20]:
            if line.strip():
                pdf.multi_cell(pdf.epw, 5, line, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
