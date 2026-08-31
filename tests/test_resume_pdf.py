"""PDF resume parsing, tested against real PDFs rather than fake bytes.

Feeding `parse_pdf` a hand-written byte string would not exercise pypdf at
all, so every fixture here is a genuine PDF built at test time -- including
the awkward shapes that break extraction in practice.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from analyzer.extract import extract
from analyzer.resume import MAX_PAGES, ResumeParseError, parse_pdf
from analyzer.taxonomy import Taxonomy
from api.main import app
from tests.pdf_fixtures import image_only, many_pages, single_column

RESUME = """TECHNICAL SKILLS
Programming Languages: Python, Java, C, SQL
Databases: MySQL
Tools and Platforms: Git, GitHub, JDBC
Web Technologies: HTML, CSS
PROJECTS
Built an NLP job recommender in Python with Scikit-learn.
Built a hospital management system in Java with MySQL and JDBC.
"""


@pytest.fixture(scope="module")
def tax():
    return Taxonomy.load()


def test_a_normal_pdf_round_trips():
    parsed = parse_pdf(single_column(RESUME))
    assert parsed.pages == 1
    assert "Python" in parsed.text
    assert "MySQL" in parsed.text
    assert not parsed.warnings


def test_the_same_skills_survive_the_pdf_round_trip(tax):
    """The point of the feature: a PDF must not lose skills a paste would find."""
    from_text = {m.skill_id for m in extract(RESUME, tax)}
    from_pdf = {m.skill_id for m in extract(parse_pdf(single_column(RESUME)).text, tax)}
    assert from_text == from_pdf, (
        f"lost {sorted(from_text - from_pdf)}, "
        f"invented {sorted(from_pdf - from_text)}"
    )


def test_a_scanned_pdf_is_refused_with_an_explanation():
    """An image-only PDF has no text layer. Returning empty text would give
    the user a confident 0% instead of telling them what went wrong."""
    with pytest.raises(ResumeParseError, match="scan or an image"):
        parse_pdf(image_only())


def test_a_non_pdf_is_refused_before_parsing():
    with pytest.raises(ResumeParseError, match="does not look like a PDF"):
        parse_pdf(b"PK\x03\x04 this is a docx", "cv.docx")


def test_an_empty_file_is_refused():
    with pytest.raises(ResumeParseError, match="empty"):
        parse_pdf(b"")


def test_an_oversized_file_is_refused_by_size_not_by_parsing():
    huge = b"%PDF-1.4" + b"\x00" * (6 * 1024 * 1024)
    with pytest.raises(ResumeParseError, match="limit"):
        parse_pdf(huge)


def test_long_documents_are_truncated_and_say_so():
    parsed = parse_pdf(many_pages(RESUME, MAX_PAGES + 3))
    assert parsed.pages == MAX_PAGES
    assert any("first" in w for w in parsed.warnings)


def test_error_messages_are_ascii_safe():
    """These strings reach a terminal as well as a browser, and a non-ASCII
    arrow crashes a cp1252 Windows console mid-message."""
    try:
        parse_pdf(b"not a pdf", "cv.docx")
    except ResumeParseError as exc:
        str(exc).encode("ascii")


# ------------------------------------------------------------------ endpoint


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_upload_endpoint_returns_text_not_an_analysis(client):
    """/parse-resume must NOT analyse. The text goes back for review first,
    because a scrambled parse would otherwise become a confident wrong gap."""
    r = client.post("/parse-resume", files={
        "file": ("resume.pdf", single_column(RESUME), "application/pdf")})
    assert r.status_code == 200
    body = r.json()
    assert "Python" in body["text"]
    assert body["pages"] == 1
    assert "coverage" not in body and "gaps" not in body


def test_upload_endpoint_reports_a_bad_file_as_400(client):
    r = client.post("/parse-resume", files={
        "file": ("scan.pdf", image_only(), "application/pdf")})
    assert r.status_code == 400
    assert "scan" in r.json()["detail"]


def test_uploaded_text_then_analyses_normally(client):
    """The two endpoints must compose: upload, review, analyse."""
    text = client.post("/parse-resume", files={
        "file": ("resume.pdf", single_column(RESUME), "application/pdf")
    }).json()["text"]
    r = client.post("/analyze", json={"resume_text": text,
                                      "role_id": "sde1-backend"})
    assert r.status_code == 200
    assert "python" in r.json()["have"]


def test_the_repo_ships_no_stray_pdfs():
    """Fixtures are built in memory. A committed PDF would likely be someone's
    actual resume."""
    assert not list((Path(__file__).resolve().parent.parent).glob("**/*.pdf"))
