"""Comparing a resume against ONE job description.

The role mode answers "what does this market want?". This answers "what does
this specific employer want?" -- a different question, and the honest output
shape is different too.

With a single posting there are no frequencies: every skill it names appears
exactly once, so ranking by demand is meaningless and marginal coverage
degenerates to "whatever is missing".

What this adds instead, and what a plain JD matcher cannot do: for each
skill the posting asks for, how often the wider market asks for it too.
That separates a gap worth closing from a gap that matters only here --
Docker in 18% of similar roles is worth your month; Struts in 2% is not.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.extract import (
    Origin,
    extract,
    resolve_implications,
    suppress_generic_cloud,
)
from analyzer.profiles import RoleProfile
from analyzer.roadmap import RoadmapStep, build_roadmap
from analyzer.taxonomy import Taxonomy

MIN_JD_CHARS = 80


@dataclass
class JDSkill:
    skill_id: str
    skill_name: str
    category: str
    have: bool
    market_share: float | None   # how often the wider market asks for it
    market_note: str


@dataclass
class JDReport:
    role_id: str | None
    role_name: str | None
    market_postings: int
    coverage: float
    matched: list[JDSkill] = field(default_factory=list)
    missing: list[JDSkill] = field(default_factory=list)
    unmatched_note: str = ""
    roadmap: list[RoadmapStep] = field(default_factory=list)


def _market_note(share: float | None) -> str:
    if share is None:
        return "not commonly asked for in this market"
    if share >= 0.25:
        return f"also wanted by {share:.0%} of similar postings - broadly valuable"
    if share >= 0.08:
        return f"wanted by {share:.0%} of similar postings"
    return f"only {share:.0%} of similar postings ask for this - specific to this employer"


def analyze_jd(resume_text: str, jd_text: str, taxonomy: Taxonomy,
               role_id: str | None = None,
               source_id: str = "naukri") -> JDReport:
    """Compare a resume against one job description.

    role_id is optional and used only for market context. Without it the
    comparison still works; it just cannot say how typical each requirement
    is, which is the interesting half.
    """
    if len(jd_text.strip()) < MIN_JD_CHARS:
        raise ValueError(
            f"That job description is too short to read ({len(jd_text.strip())} "
            f"characters). Paste at least {MIN_JD_CHARS}."
        )

    have = {m.skill_id for m in extract(resume_text, taxonomy,
                                        origin=Origin.RESUME,
                                        with_evidence=False)}
    have |= resolve_implications(have)
    have = suppress_generic_cloud(have)

    # The JD is prose, not a resume, so no section weighting applies.
    wanted = {m.skill_id for m in
              extract(jd_text, taxonomy, origin=Origin.DESCRIPTION,
                      sectioned=False, with_evidence=False)}
    wanted |= resolve_implications(wanted)
    # Both sides get the same treatment. A posting naming AWS means one
    # skill, not AWS plus a generic cloud entry -- and if only one side were
    # suppressed the two would disagree about what they are comparing.
    wanted = suppress_generic_cloud(wanted)

    profile = None
    if role_id:
        try:
            profile = RoleProfile.load(role_id, source_id)
        except FileNotFoundError:
            profile = None
    demand = profile.by_id if profile else {}

    def make(skill_id: str) -> JDSkill:
        d = demand.get(skill_id)
        share = d.share if d else None
        return JDSkill(
            skill_id=skill_id,
            skill_name=taxonomy.name_of(skill_id),
            category=(taxonomy.skills[skill_id].category
                      if skill_id in taxonomy.skills else ""),
            have=skill_id in have,
            market_share=share,
            market_note=_market_note(share),
        )

    matched = sorted((make(s) for s in wanted & have),
                     key=lambda s: -(s.market_share or 0))
    missing = sorted((make(s) for s in wanted - have),
                     key=lambda s: -(s.market_share or 0))

    coverage = len(matched) / len(wanted) if wanted else 0.0

    # Order the missing skills by prerequisite, reusing the same graph as the
    # role roadmap. Gaps here carry no marginal_gain -- there is nothing to
    # maximise over a single posting -- so a light shim keeps the shape.
    class _G:
        def __init__(self, s: JDSkill):
            self.skill_id = s.skill_id
            self.marginal_gain = s.market_share or 0.0

    actionable = [s for s in missing
                  if s.skill_id in taxonomy.skills
                  and taxonomy.skills[s.skill_id].actionable]
    roadmap = build_roadmap([_G(s) for s in actionable], have, taxonomy)

    note = ""
    if not wanted:
        note = ("No known skills were found in that job description. It may be "
                "mostly prose, or use terms outside this taxonomy.")

    return JDReport(
        role_id=role_id,
        role_name=profile.role_name if profile else None,
        market_postings=profile.total_postings if profile else 0,
        coverage=coverage,
        matched=matched,
        missing=missing,
        unmatched_note=note,
        roadmap=roadmap,
    )
