"""Stage 4 regression tests -- coverage, ranking and roadmap ordering."""

from __future__ import annotations

import pytest

from analyzer.gap import analyze, coverage_of, rank_by_marginal_coverage
from analyzer.profiles import RoleProfile
from analyzer.roadmap import _detect_cycle, load_prereqs, load_resources
from analyzer.taxonomy import Taxonomy


@pytest.fixture(scope="module")
def tax() -> Taxonomy:
    return Taxonomy.load()


@pytest.fixture(scope="module")
def profile() -> RoleProfile:
    return RoleProfile.load("sde1-backend")


def test_prereq_graph_is_acyclic():
    """A cycle would make the roadmap loop forever or silently truncate."""
    cycle = _detect_cycle(load_prereqs())
    assert cycle is None, f"cycle: {' -> '.join(cycle)}"


def test_every_prereq_is_a_real_skill(tax):
    for skill, deps in load_prereqs().items():
        assert skill in tax.skills, f"prereq key {skill!r} is not a skill"
        for dep in deps:
            assert dep in tax.skills, f"{skill} depends on unknown {dep!r}"


def test_every_resource_targets_a_real_skill(tax):
    for skill in load_resources():
        assert skill in tax.skills, f"resource for unknown skill {skill!r}"


def test_coverage_bounds(profile):
    assert coverage_of(set(), profile) == 0.0
    everything = {d.skill_id for d in profile.demands}
    assert coverage_of(everything, profile) == pytest.approx(1.0)


def test_coverage_uses_top_n_not_the_long_tail(profile):
    """Regression: coverage across all ~130 demanded skills gave a
    well-matched CV 24%, because rare skills dominated the denominator."""
    top = {d.skill_id for d in profile.demands[:30]}
    assert coverage_of(top, profile) == pytest.approx(1.0)


def test_ranking_never_recommends_a_non_actionable_skill(tax, profile):
    """Regression: 'learn Data Analysis' was the top suggestion for the
    Data Analyst role -- real demand, useless as a next step."""
    gaps = rank_by_marginal_coverage(set(), profile, tax, top_n=15)
    for g in gaps:
        assert tax.skills[g.skill_id].actionable, f"{g.skill_id} is not actionable"


def test_ranking_gains_are_descending(tax, profile):
    gaps = rank_by_marginal_coverage(set(), profile, tax, top_n=8)
    gains = [g.marginal_gain for g in gaps]
    assert gains == sorted(gains, reverse=True)
    assert all(g > 0 for g in gains)


def test_already_held_skills_are_never_recommended(tax, profile):
    have = {d.skill_id for d in profile.demands[:5]}
    gaps = rank_by_marginal_coverage(have, profile, tax, top_n=10)
    assert not ({g.skill_id for g in gaps} & have)


def test_roadmap_puts_prerequisites_before_dependents(tax):
    resume = "TECHNICAL SKILLS\nPython, SQL, Git\n"
    report = analyze(resume, "sde1-backend", tax, top_n=8)
    position = {s.skill_id: s.order for s in report.roadmap}
    prereqs = load_prereqs()
    for skill_id, order in position.items():
        for dep in prereqs.get(skill_id, []):
            if dep in position:
                assert position[dep] < order, f"{dep} must precede {skill_id}"


def test_report_is_coherent_on_a_real_resume(tax):
    resume = "TECHNICAL SKILLS\nJava, Spring Boot, MySQL, Git, Docker\n"
    report = analyze(resume, "sde1-backend", tax)
    assert 0.0 <= report.coverage <= 1.0
    assert "java" in report.have
    assert report.core_total == 30
    assert not ({g.skill_id for g in report.gaps} & set(report.have))
