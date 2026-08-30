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

from analyzer.extract import Origin, extract, resolve_implications
from analyzer.profiles import RoleProfile, SkillDemand
from analyzer.taxonomy import Taxonomy

# Skills nobody can hand you a course for. They are real demand and they
# count toward coverage, but a learning roadmap that says "acquire
# communication" is useless, so they are excluded from recommendations.
UNTEACHABLE = {"soft"}


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
    have: list[str] = field(default_factory=list)
    have_names: list[str] = field(default_factory=list)
    unused: list[str] = field(default_factory=list)   # on the CV, not demanded
    gaps: list[Gap] = field(default_factory=list)


def coverage_of(have: set[str], profile: RoleProfile) -> float:
    """Fraction of the role's weighted demand the candidate already meets."""
    total = profile.total_weight
    if not total:
        return 0.0
    return sum(d.weight for d in profile.demands if d.skill_id in have) / total


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
            if (tax.skills[sid].category if sid in tax.skills else "") not in UNTEACHABLE
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

    mentions = extract(resume_text, taxonomy, origin=Origin.RESUME)
    have = {m.skill_id for m in mentions}
    # A framework on the CV asserts its language, exactly as in extraction.
    have |= resolve_implications(have)

    demanded = set(profile.by_id)
    return GapReport(
        role_id=profile.role_id,
        role_name=profile.role_name,
        market=profile.market,
        total_postings=profile.total_postings,
        coverage=coverage_of(have, profile),
        have=sorted(have & demanded),
        have_names=sorted(taxonomy.name_of(s) for s in have & demanded),
        unused=sorted(taxonomy.name_of(s) for s in have - demanded),
        gaps=rank_by_marginal_coverage(have, profile, taxonomy, top_n),
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

    print("LEARN NEXT  (ranked by how much coverage each one adds)")
    print("-" * 78)
    for i, g in enumerate(report.gaps, 1):
        print(f"{i:>2}. {g.skill_name:<26} +{g.marginal_gain:>5.1%} coverage")
        print(f"    {g.evidence}")
    print()


if __name__ == "__main__":
    main()
