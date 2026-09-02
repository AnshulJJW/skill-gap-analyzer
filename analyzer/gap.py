"""Stage 4 -- the actual product.

Compares a resume against a role profile and produces:
  - a coverage score (the headline number)
  - ranked gaps with EVIDENCE (the thing that makes it credible)

The ranking is by marginal coverage, not raw frequency: which single skill,
learned next, unlocks the most postings you currently fail? That is greedy
set cover, and it is a better answer than "sorted by frequency" because the
most common missing skill is often one you already half-have through its
neighbours, while a slightly rarer one opens a whole segment of the market.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

from analyzer.extract import (
    Origin,
    Section,
    extract,
    resolve_implications,
    suppress_generic_cloud,
)
from analyzer.profiles import RoleProfile, SkillDemand
from analyzer.roadmap import RoadmapStep, build_roadmap
from analyzer.taxonomy import Taxonomy

# How many of the role's top skills the headline number is measured against.
#
# Coverage across ALL demanded skills is mathematically defensible and
# communicatively useless: a CV with Python, pandas, NumPy, scikit-learn,
# SQL and ML scored 24% for Data Analyst, a role it genuinely suits, because
# the long tail of 83 rarely-demanded skills dominates the denominator.
#
# Measuring against the top N answers the question a user is actually
# asking -- "am I close?" -- rather than "do I know everything anyone ever
# asked for?". 30 is a judgement call, recorded so it can be argued with.
TOP_N_FOR_COVERAGE = 30


# Sections where naming a skill is a claim about what you can do: an explicit
# skills list, or a project you built. A mention under EDUCATION is usually a
# course title, and OTHER is unheaded text we could not place -- both are
# weaker evidence that you actually hold the skill.
#
# extract() already scores these; the gap report used to throw the score away
# and treat "coursework included Java" as equal to listing Java outright.
_CLAIMED_SECTIONS = {Section.SKILLS, Section.EXPERIENCE}


@dataclass
class HeldSkill:
    """A skill the resume shows, and how well it shows it."""

    skill_id: str
    skill_name: str
    confirmed: bool     # named in a skills list or shown in a project
    section: str        # where it was found, so the call can be argued with


@dataclass
class Gap:
    skill_id: str
    skill_name: str
    category: str
    share: float               # share of postings for this role asking for it
    postings: int              # absolute count, shown as evidence
    marginal_gain: float       # coverage points added by learning it next
    unlocks: int               # postings you would newly satisfy
    evidence: str


@dataclass
class GapReport:
    role_id: str
    role_name: str
    market: str
    total_postings: int
    coverage: float
    core_have: int = 0            # of the top-N demanded skills
    core_total: int = 0
    have: list[str] = field(default_factory=list)
    have_names: list[str] = field(default_factory=list)
    held: list[HeldSkill] = field(default_factory=list)   # with evidence level
    unused: list[str] = field(default_factory=list)   # on the CV, not demanded
    gaps: list[Gap] = field(default_factory=list)
    roadmap: list[RoadmapStep] = field(default_factory=list)
    skills_detected: int = 0
    # Set when the resume yielded nothing we recognise. Without it a
    # scrambled PDF or a pasted cover letter returns a confident 0% with a
    # full learning plan attached, and nothing says the input was the
    # problem.
    empty_note: str = ""


def core_demands(profile: RoleProfile, top_n: int = TOP_N_FOR_COVERAGE):
    """The N most-demanded skills -- the ones a candidate is judged on."""
    return profile.demands[:top_n]


def coverage_of(have: set[str], profile: RoleProfile,
                top_n: int = TOP_N_FOR_COVERAGE) -> float:
    """Share of the role's core weighted demand the candidate already meets."""
    core = core_demands(profile, top_n)
    total = sum(d.weight for d in core)
    if not total:
        return 0.0
    return sum(d.weight for d in core if d.skill_id in have) / total


def _evidence(demand: SkillDemand, profile: RoleProfile) -> str:
    tagged = (f", named outright by the employer in {demand.tagged}"
              if demand.tagged else "")
    return (f"appears in {demand.share:.0%} of {profile.total_postings:,} "
            f"{profile.role_name} postings{tagged}")


def rank_by_marginal_coverage(
    have: set[str], profile: RoleProfile, tax: Taxonomy,
    top_n: int = 10, include_soft: bool = False,
) -> list[Gap]:
    """Greedy set cover over the demand this candidate does not yet meet.

    Each round picks the skill adding the most coverage, adds it to the
    'have' set, and repeats. Because coverage is weighted by how often a
    skill is demanded AND how strongly, the second pick is chosen given the
    first -- which is what makes this a path rather than a list.
    """
    acquired = set(have)
    missing = {
        d.skill_id: d for d in profile.demands
        if d.skill_id not in acquired and d.postings > 0
    }
    if not include_soft:
        missing = {
            sid: d for sid, d in missing.items()
            if sid in tax.skills and tax.skills[sid].actionable
        }

    out: list[Gap] = []
    base = coverage_of(acquired, profile)

    for _ in range(min(top_n, len(missing))):
        best_id, best_gain = None, -1.0
        for sid in missing:
            gain = coverage_of(acquired | {sid}, profile) - base
            if gain > best_gain:
                best_id, best_gain = sid, gain
        if best_id is None or best_gain <= 0:
            break

        demand = missing.pop(best_id)
        acquired.add(best_id)
        base += best_gain
        out.append(Gap(
            skill_id=best_id,
            skill_name=tax.name_of(best_id),
            category=tax.skills[best_id].category if best_id in tax.skills else "",
            share=demand.share,
            postings=demand.postings,
            marginal_gain=best_gain,
            unlocks=demand.postings,
            evidence=_evidence(demand, profile),
        ))
    return out


def analyze(resume_text: str, role_id: str, taxonomy: Taxonomy,
            source_id: str = "naukri", top_n: int = 10) -> GapReport:
    profile = RoleProfile.load(role_id, source_id)

    # with_evidence=False: the quoted source line costs a scan of the whole
    # document per mention and nothing below reads it.
    mentions = extract(resume_text, taxonomy, origin=Origin.RESUME,
                       with_evidence=False)
    section_of = {m.skill_id: m.section for m in mentions}

    have = {m.skill_id for m in mentions}
    # Both fixes below also run when postings are processed offline
    # (scripts/extract_skills.py). Applying them to only one side would make
    # the resume and the profile disagree about what a skill set even is.
    have |= resolve_implications(have)
    have = suppress_generic_cloud(have)

    demanded = set(profile.by_id)
    core = {d.skill_id for d in core_demands(profile)}
    matched = have & demanded

    # Evidence level per held skill. Implied languages (React -> JavaScript)
    # have no section of their own; they inherit "confirmed" because the
    # framework that asserted them was itself a claim.
    held = sorted(
        (
            HeldSkill(
                skill_id=sid,
                skill_name=taxonomy.name_of(sid),
                confirmed=section_of.get(sid, Section.SKILLS) in _CLAIMED_SECTIONS,
                section=section_of.get(sid, Section.SKILLS).value,
            )
            for sid in matched
        ),
        key=lambda h: (h.confirmed is False, h.skill_name.lower()),
    )

    note = ""
    if not have:
        note = (
            "No skills we recognise were found in that text. If you pasted a "
            "resume, check it came through as words rather than scrambled "
            "characters — the score below is measured on what is above, so "
            "an empty read gives an empty score."
        )

    gaps = rank_by_marginal_coverage(have, profile, taxonomy, top_n)
    return GapReport(
        core_have=len(have & core),
        core_total=len(core),
        role_id=profile.role_id,
        role_name=profile.role_name,
        market=profile.market,
        total_postings=profile.total_postings,
        coverage=coverage_of(have, profile),
        have=sorted(matched),
        have_names=sorted(taxonomy.name_of(s) for s in matched),
        held=held,
        unused=sorted(taxonomy.name_of(s) for s in have - demanded),
        gaps=gaps,
        roadmap=build_roadmap(gaps, have, taxonomy),
        skills_detected=len(have),
        empty_note=note,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Report a skill gap for one resume.")
    parser.add_argument("--resume", required=True, type=Path)
    parser.add_argument("--role", required=True, help="e.g. sde1-backend")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    tax = Taxonomy.load()
    report = analyze(args.resume.read_text(encoding="utf-8"), args.role, tax,
                     top_n=args.top)

    print(f"\n{report.role_name}  ({report.market} market, "
          f"{report.total_postings:,} postings)")
    print("=" * 78)
    print(f"COVERAGE  {report.coverage:.0%}\n")

    print(f"You already have ({len(report.have_names)} of the skills this role wants):")
    print("  " + ", ".join(report.have_names) + "\n")

    if report.unused:
        print("On your CV but not asked for in this role:")
        print("  " + ", ".join(report.unused) + "\n")

    print("BIGGEST GAPS  (ranked by coverage each one adds)")
    print("-" * 78)
    for i, g in enumerate(report.gaps, 1):
        print(f"{i:>2}. {g.skill_name:<26} +{g.marginal_gain:>5.1%}   {g.evidence}")

    print("\nLEARNING ORDER  (prerequisites first -- start at the top)")
    print("-" * 78)
    total_hours = 0
    for step in report.roadmap:
        tag = "  [prerequisite]" if step.is_prerequisite else ""
        print(f"{step.order:>2}. {step.skill_name}{tag}")
        print(f"    {step.reason}")
        for res in step.resources[:2]:
            hrs = f"~{res.hours}h" if res.hours else ""
            total_hours += res.hours or 0
            print(f"      - {res.title}  ({res.kind}, {hrs})")
            print(f"        {res.url}")
        if not step.resources:
            print("      - no curated resource yet")
    if total_hours:
        print(f"\n    roughly {total_hours} hours of listed material")
    print()


if __name__ == "__main__":
    main()
