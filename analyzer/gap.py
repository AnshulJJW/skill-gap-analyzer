"""Stage 4 -- the actual product.

Compares a resume's skills against a role profile and produces:
  - a coverage score (the headline number)
  - ranked gaps with EVIDENCE (the thing that makes it credible)

The ranking is by marginal coverage, not raw frequency: which single skill,
learned next, unlocks the most postings you currently fail? That is greedy
set cover, it is about ten lines, and it is a far better interview answer
than "I sorted by frequency".
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from analyzer.profiles import RoleProfile
from analyzer.taxonomy import Taxonomy


@dataclass
class Gap:
    skill_id: str
    skill_name: str
    required_pct: float
    postings_blocked: int      # postings you fail ONLY because of this skill
    marginal_gain: float       # coverage delta if you learned it next
    evidence: str              # "appears in 68% of 340 SDE-1 Backend postings"


@dataclass
class GapReport:
    role_name: str
    total_postings: int
    coverage: float            # 0.0 - 1.0
    have: list[str]            # skills found in the resume -- show these too;
                               # it builds trust and surfaces extraction errors
    gaps: list[Gap]            # ranked by marginal_gain, descending


def analyze(resume_text: str, role_id: str, taxonomy: Taxonomy) -> GapReport:
    # TODO Stage 4:
    #   1. extract(resume_text) -> set of skill_ids the candidate has
    #   2. RoleProfile.load(role_id)
    #   3. coverage = sum(weight of matched demands) / sum(all weights)
    #   4. rank_by_marginal_coverage over the unmatched demands
    raise NotImplementedError


def rank_by_marginal_coverage(
    have: set[str], profile: RoleProfile, top_n: int = 10
) -> list[Gap]:
    """Greedy set cover over the postings this candidate currently fails.

    Each round: pick the skill that unblocks the most still-failing postings,
    add it to the 'have' set, repeat. This is why the output says "learn Kafka
    next" rather than "here are the 40 most common skills you lack".
    """
    # TODO Stage 4
    raise NotImplementedError


def main() -> None:
    parser = argparse.ArgumentParser(description="Report a skill gap for one resume.")
    parser.add_argument("--resume", required=True, type=Path)
    parser.add_argument("--role", required=True, help="e.g. sde1-backend")
    args = parser.parse_args()

    report = analyze(
        args.resume.read_text(encoding="utf-8"), args.role, Taxonomy.load()
    )
    print(f"Coverage: {report.coverage:.0%}  (of {report.total_postings} {report.role_name} postings)")
    for i, gap in enumerate(report.gaps, 1):
        print(f"{i:>2}. {gap.skill_name:<20} {gap.evidence}, blocks {gap.postings_blocked}")


if __name__ == "__main__":
    main()
