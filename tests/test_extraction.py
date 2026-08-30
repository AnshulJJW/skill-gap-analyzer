"""Stage 2 regression tests.

These lock in the bugs already found, so they cannot come back quietly. The
CSS case in particular was invisible in the output -- the only symptom was a
skill you expected being absent.

    python -m pytest -q
"""

from __future__ import annotations

import pytest

from analyzer.extract import Section, extract, find_skills, split_sections
from analyzer.taxonomy import Taxonomy, audit_aliases, normalize


@pytest.fixture(scope="module")
def tax() -> Taxonomy:
    return Taxonomy.load()


@pytest.mark.parametrize("variants", [
    ("Node.js", "nodejs", "node js", "NodeJS"),
    ("react.js", "reactjs", "React JS"),
    ("PostgreSQL", "postgres", "Postgres"),
    ("core java", "Core Java", "J2EE"),
    ("version control", "GitHub", "git"),
])
def test_spellings_collapse_to_one_skill(tax, variants):
    resolved = {tax.resolve(v) for v in variants}
    assert len(resolved) == 1, f"{variants} resolved to {resolved}"
    assert None not in resolved


def test_c_family_stays_distinct(tax):
    """Blind punctuation stripping collapses c++ and c# into c, which then
    inflates the C language enormously. All three are common tags here."""
    assert tax.resolve("C") == "c"
    assert tax.resolve("C++") == "cpp"
    assert tax.resolve("C#") == "csharp"
    assert normalize("c++") != normalize("c")


def test_junk_tags_are_rejected(tax):
    for junk in ["backend", "development", "coding", "software",
                 "computer science", "software development", "front end"]:
        assert tax.resolve(junk) is None, f"{junk!r} should not be a skill"
        assert tax.is_noise(junk), f"{junk!r} should be on the stoplist"


def test_real_skills_are_not_rejected(tax):
    for skill in ["python", "docker", "kubernetes", "mysql", "react", "git"]:
        assert tax.resolve(skill) is not None
        assert not tax.is_noise(skill)


def test_adjacent_skills_both_survive(tax):
    """Regression: the alias 'html/css' normalised to 'html css', matched as
    a single HTML mention, consumed both tokens, and CSS was lost."""
    found = {sid for sid, _ in find_skills("Web Technologies: HTML, CSS", tax)}
    assert found == {"html", "css"}


def test_no_alias_is_a_list_of_two_skills(tax):
    """Guards the same bug class across the whole taxonomy, not just HTML."""
    problems = sorted(set(audit_aliases(tax)))
    listy = [p for p in problems if p[0] in {"html css", "html javascript"}]
    assert not listy, f"list-style aliases lose a skill: {listy}"


def test_longest_match_wins(tax):
    """'spring boot' must not also register a bare 'spring'."""
    found = dict(find_skills("Experience with Spring Boot required", tax))
    assert "spring-boot" in found
    assert "spring" not in found


def test_sections_are_detected():
    text = (
        "ANSHUL\nBengaluru\n"
        "TECHNICAL SKILLS\nProgramming Languages: Python, Java\n"
        "PROJECTS\nBuilt a thing with Django\n"
        "EDUCATION\nB.E. in AI and ML\n"
    )
    sections = dict(split_sections(text))
    assert Section.SKILLS in sections
    assert Section.EXPERIENCE in sections
    assert Section.EDUCATION in sections
    assert "Python" in sections[Section.SKILLS]


def test_skills_section_outranks_education(tax):
    """A skill claimed under TECHNICAL SKILLS is a claim; the same word under
    EDUCATION is usually a course name."""
    text = (
        "TECHNICAL SKILLS\nPython, SQL\n"
        "EDUCATION\nCoursework included Java and Python\n"
    )
    by_id = {m.skill_id: m for m in extract(text, tax)}
    assert by_id["python"].section is Section.SKILLS
    assert by_id["python"].confidence > by_id["java"].confidence


def test_empty_input_is_safe(tax):
    assert extract("", tax) == []
    assert find_skills("", tax) == []
    assert normalize("") == ""
