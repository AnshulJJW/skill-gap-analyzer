"""Turning an uploaded PDF into text the extractor can read.

PDF is a page-description format, not a document format: it stores glyphs at
coordinates, with no notion of paragraphs, columns or reading order. Getting
text back out is reconstruction, and it fails in predictable ways --
two-column layouts interleave, text inside tables scrambles, and a scanned
resume yields nothing at all because it is an image.

**So this never feeds the analyzer directly.** The extracted text is handed
back to the user to check and correct first. A silently bad parse produces a
confident, wrong skill gap, which is worse than refusing to parse.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PyPdfError

MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 10
MIN_USABLE_CHARS = 120


class ResumeParseError(Exception):
    """Raised with a message intended to be shown to the user."""


@dataclass
class ParsedResume:
    text: str
    pages: int
    chars: int
    warnings: list[str]


def _tidy(raw: str) -> str:
    """Undo the artefacts PDF text extraction reliably introduces."""
    s = raw.replace(" ", " ").replace("ﬁ", "fi").replace("ﬂ", "fl")
    s = re.sub(r"[•●▪‣⁃]", " ", s)   # bullet glyphs
    s = re.sub(r"-\n(?=[a-z])", "", s)                        # hyphen line-break
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


# Detecting a two-column layout from extracted text was attempted twice and
# abandoned, which is worth recording so it is not attempted a third time.
#
#   Attempt 1 -- look for SHORT choppy lines, assuming columns fragment the
#   text. Wrong: they do the opposite.
#
#   Attempt 2 -- look for a run of spaces where the column gap was. Also
#   wrong: pypdf collapses the gap to a SINGLE space, so
#
#     "...Machine Learning undergraduate w Hospital Management System"
#
#   is indistinguishable from an ordinary sentence.
#
# There is no reliable signal in the output, so no warning is claimed. The
# safeguard is structural instead: the extracted text is ALWAYS returned for
# the user to read and correct before anything is analysed. A heuristic that
# fires 40% of the time would be worse than none, because it would imply the
# silent cases are fine.

def parse_pdf(data: bytes, filename: str = "resume.pdf") -> ParsedResume:
    """Extract text from a PDF, or raise ResumeParseError with a usable message."""
    if not data:
        raise ResumeParseError("That file is empty.")
    if len(data) > MAX_BYTES:
        raise ResumeParseError(
            f"That file is {len(data) / 1024 / 1024:.1f}MB. "
            f"The limit is {MAX_BYTES // 1024 // 1024}MB — a text resume is "
            "usually well under 1MB."
        )
    if not data.startswith(b"%PDF"):
        raise ResumeParseError(
            f"{filename} does not look like a PDF. If it is a Word document, "
            "open it and use File -> Save as -> PDF, or paste the text directly."
        )

    try:
        reader = PdfReader(io.BytesIO(data))
    except PyPdfError as exc:
        raise ResumeParseError(f"That PDF could not be opened ({exc}).") from exc

    if getattr(reader, "is_encrypted", False):
        try:
            reader.decrypt("")          # many resumes are "encrypted" with no password
        except Exception as exc:
            raise ResumeParseError(
                "That PDF is password protected. Remove the password, or "
                "paste the text directly."
            ) from exc

    pages = reader.pages[:MAX_PAGES]
    warnings: list[str] = []
    if len(reader.pages) > MAX_PAGES:
        warnings.append(
            f"Only the first {MAX_PAGES} pages were read "
            f"(the file has {len(reader.pages)})."
        )

    chunks = []
    for i, page in enumerate(pages, 1):
        try:
            chunks.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001 - one bad page must not lose the rest
            warnings.append(f"Page {i} could not be read and was skipped.")

    raw = "\n".join(chunks)
    text = _tidy(raw)

    if len(text) < MIN_USABLE_CHARS:
        raise ResumeParseError(
            "Almost no text came out of that PDF. It is probably a scan or an "
            "image, which has no text layer to read. Paste your resume text "
            "directly instead."
        )

    return ParsedResume(text=text, pages=len(pages), chars=len(text),
                        warnings=warnings)
