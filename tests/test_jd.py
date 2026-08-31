"""Regression tests for single-job-description mode.

The point of this mode is not "which words match" -- any grep does that. It
is the market-share annotation that separates a gap worth closing from one
that matters only to this employer. These tests pin that behaviour down.
"""

from __future__ import annotations

import pytest

from analyzer.jd import MIN_JD_CHARS, _market_note, analyze_jd
from analyzer.taxonomy import Taxonomy

RESUME = """TECHNICAL SKILLS
Programming Languages: Python, Java, SQL
Databases: MySQL
Tools: Git, GitHub
"""

JD = """We are hiring a Backend Engineer. You will build and maintain REST APIs
using Java and Spring Boot. Requirements: strong knowledge of Java, SQL and
MySQL. Experience with Docker, Kubernetes and AWS is required. Familiarity
with Redis caching and Kafka. Good communication skills and Git.
"""


@pytest.fixture(scope="module")
def tax() -> Taxonomy:
    return Taxonomy.load()


def test_matched_and_missing_partition_what_the_jd_asks_for(tax):
    """Every wanted skill lands in exactly one bucket, or coverage lies."""
    r = analyze_jd(RESUME, JD, tax, role_id="sde1-backend")
    matched = {s.skill_id for s in r.matched}
    missing = {s.skill_id for s in r.missing}
    assert matched & missing == set()
    assert matched, "resume shares Java/SQL/Git with the JD"
    assert r.coverage == pytest.approx(len(matched) / (len(matched) + len(missing)))


def test_resume_skills_the_jd_never_mentions_are_not_reported(tax):
    """Unlike role mode there is no 'unused' list -- one posting is not a market."""
    r = analyze_jd(RESUME, JD, tax, role_id="sde1-backend")
    reported = {s.skill_id for s in r.matched} | {s.skill_id for s in r.missing}
    assert "python" not in reported


def test_market_share_annotates_every_skill_when_a_role_is_given(tax):
    r = analyze_jd(RESUME, JD, tax, role_id="sde1-backend")
    for s in r.matched + r.missing:
        assert s.market_note, f"{s.skill_id} carries no market note"


def test_without_a_role_there_is_no_market_claim(tax):
    """Better to say nothing than to invent a share out of one posting."""
    r = analyze_jd(RESUME, JD, tax, role_id=None)
    assert r.role_name is None
    assert r.market_postings == 0
    assert all(s.market_share is None for s in r.matched + r.missing)


def test_missing_is_ordered_by_market_share(tax):
    """The ordering IS the advice: broadly-wanted gaps first."""
    r = analyze_jd(RESUME, JD, tax, role_id="sde1-backend")
    shares = [s.market_share or 0.0 for s in r.missing]
    assert shares == sorted(shares, reverse=True)


def test_market_note_wording_matches_the_share_bands():
    assert "broadly valuable" in _market_note(0.40)
    assert "specific to this employer" in _market_note(0.02)
    assert "not commonly asked for" in _market_note(None)
    # Boundaries, because off-by-one here mislabels advice.
    assert "broadly valuable" in _market_note(0.25)
    assert "specific to this employer" not in _market_note(0.08)


def test_roadmap_excludes_non_actionable_skills(tax):
    """Nobody can hand you a course for 'Communication'."""
    r = analyze_jd(RESUME, JD, tax, role_id="sde1-backend")
    assert any(s.skill_id == "communication" for s in r.missing), \
        "the JD does ask for communication"
    assert all(step.skill_id != "communication" for step in r.roadmap)


def test_short_job_description_is_refused(tax):
    with pytest.raises(ValueError, match="too short"):
        analyze_jd(RESUME, "Java developer needed.", tax)


def test_min_chars_boundary_is_inclusive(tax):
    """One character under must fail; the threshold itself must pass."""
    filler = "We need a backend engineer with Java and SQL experience. " * 4
    assert len(filler) > MIN_JD_CHARS
    with pytest.raises(ValueError):
        analyze_jd(RESUME, filler[: MIN_JD_CHARS - 1], tax)
    analyze_jd(RESUME, filler[:MIN_JD_CHARS], tax)


def test_jd_with_no_known_skills_says_so_rather_than_scoring_zero(tax):
    prose = ("We are looking for a passionate self-starter who thrives in a "
             "fast-paced environment and enjoys collaborating with "
             "stakeholders to deliver outcomes that delight our customers. " * 2)
    r = analyze_jd(RESUME, prose, tax)
    if not r.matched and not r.missing:
        assert r.unmatched_note, "a zero score with no explanation is misleading"
