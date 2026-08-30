"""Stage 4 -- precomputed role profiles.

A role profile answers: "across every posting for this role, how often is
each skill asked for, and how strong is the evidence?"

This runs OFFLINE, as a build step (scripts/build_profiles.py). The API
reads the stored result. It must never scan the postings table at request
time -- that is the difference between a 200ms response and a timeout on a
512MB free-tier instance.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
PROFILE_DIR = DATA / "profiles"

MIN_POSTINGS = 250

# Weighting of the two evidence origins. Naukri's short descriptions do not
# carry a required-vs-preferred split (only 14.9% have both markers -- see
# docs/stage1-data-audit.md), so employer-named tags versus description-only
# matches replace it as the confidence axis.
#
# Stage 3 measured tags as noisier than assumed -- an Android posting tagged
# `sap` -- so the gap is smaller than the original design assumed.
W_TAGGED = 1.0
W_DESCRIPTION = 0.75


@dataclass
class SkillDemand:
    skill_id: str
    postings: int          # postings mentioning it at all
    tagged: int            # of those, employer-named
    share: float           # postings / total_postings

    @property
    def weight(self) -> float:
        """How much this skill matters for the role.

        Share of postings, adjusted by how much of that evidence was
        employer-named rather than merely present in the body text.
        """
        if not self.postings:
            return 0.0
        tagged_frac = self.tagged / self.postings
        confidence = W_DESCRIPTION + (W_TAGGED - W_DESCRIPTION) * tagged_frac
        return self.share * confidence


@dataclass
class RoleProfile:
    """Demand for one role, within ONE source.

    Profiles are per (role, source) on purpose. LinkedIn and Naukri describe
    different labour markets; averaging them yields a percentage that
    reflects which dataset was larger rather than either market.
    """

    role_id: str
    role_name: str
    source_id: str
    market: str
    total_postings: int
    demands: list[SkillDemand] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.role_id}__{self.source_id}"

    @property
    def by_id(self) -> dict[str, SkillDemand]:
        return {d.skill_id: d for d in self.demands}

    @property
    def total_weight(self) -> float:
        return sum(d.weight for d in self.demands)

    def save(self) -> Path:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        path = PROFILE_DIR / f"{self.key}.json"
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, role_id: str, source_id: str = "naukri") -> RoleProfile:
        path = PROFILE_DIR / f"{role_id}__{source_id}.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw["demands"] = [SkillDemand(**d) for d in raw["demands"]]
        return cls(**raw)

    @classmethod
    def available(cls) -> list[str]:
        if not PROFILE_DIR.exists():
            return []
        return sorted(p.stem for p in PROFILE_DIR.glob("*.json"))


def build(role_id: str, role_name: str, source_id: str, market: str,
          rows: list[tuple[int, str, str]]) -> RoleProfile:
    """Aggregate (posting_id, skill_id, origin) rows into one profile.

    Guard rail: fewer than MIN_POSTINGS raises. A role backed by 40 postings
    produces confident-looking percentages that mean nothing, and that is
    worse than not shipping the role at all.
    """
    postings_for: dict[str, set[int]] = {}
    tagged_for: dict[str, set[int]] = {}
    all_postings: set[int] = set()

    for posting_id, skill_id, origin in rows:
        all_postings.add(posting_id)
        postings_for.setdefault(skill_id, set()).add(posting_id)
        if origin == "tagged":
            tagged_for.setdefault(skill_id, set()).add(posting_id)

    total = len(all_postings)
    if total < MIN_POSTINGS:
        raise ValueError(
            f"{role_id}: {total} postings is below the {MIN_POSTINGS} minimum. "
            "Widen the role patterns or drop the role -- percentages from a "
            "smaller pool look confident and mean nothing."
        )

    demands = [
        SkillDemand(
            skill_id=sid,
            postings=len(pids),
            tagged=len(tagged_for.get(sid, ())),
            share=len(pids) / total,
        )
        for sid, pids in postings_for.items()
    ]
    demands.sort(key=lambda d: -d.weight)

    return RoleProfile(
        role_id=role_id, role_name=role_name, source_id=source_id,
        market=market, total_postings=total, demands=demands,
    )
