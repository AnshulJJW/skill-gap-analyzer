"""Stage 4 -- precomputed role profiles.

A role profile answers: "across every posting for this role, how often is
each skill asked for, and is it a hard requirement or a nice-to-have?"

This runs OFFLINE, as a build step (scripts/build_profiles.py). The API
reads the stored result. It must never scan the postings table at request
time -- that is the difference between a 200ms response and a timeout on a
512MB free-tier instance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
PROFILE_DIR = DATA / "profiles"


@dataclass
class SkillDemand:
    skill_id: str
    required_pct: float     # share of postings listing it as a requirement
    preferred_pct: float    # share listing it as preferred
    posting_count: int      # absolute count -- shown as evidence in the UI

    @property
    def weight(self) -> float:
        """How much this skill matters for the role.

        Required mentions count fully; preferred mentions count for less.
        The 0.4 is a judgement call -- write down why you chose it, because
        an interviewer will ask.
        """
        return self.required_pct + 0.4 * self.preferred_pct


@dataclass
class RoleProfile:
    """Demand for one role, within ONE source.

    Profiles are per (role, source) on purpose. LinkedIn and Naukri describe
    different labour markets; averaging them yields a percentage that
    reflects which dataset was larger rather than either market. Comparing
    the two profiles is far more interesting than blending them, and it is
    the honest thing to put in front of a user deciding what to learn.
    """

    role_id: str            # "sde1-backend"
    role_name: str          # "SDE-1 Backend"
    source_id: str          # "linkedin" | "naukri"
    market: str             # "global" | "india"
    total_postings: int
    demands: list[SkillDemand]

    @property
    def key(self) -> str:
        return f"{self.role_id}__{self.source_id}"

    def save(self) -> Path:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        path = PROFILE_DIR / f"{self.key}.json"
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, role_id: str, source_id: str) -> "RoleProfile":
        path = PROFILE_DIR / f"{role_id}__{source_id}.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw["demands"] = [SkillDemand(**d) for d in raw["demands"]]
        return cls(**raw)


MIN_POSTINGS = 250


def build(role_id: str, source_id: str, postings: list[dict]) -> RoleProfile:
    """Aggregate extracted mentions across one source's postings.

    Guard rail: fewer than MIN_POSTINGS raises. A role backed by 40 postings
    produces confident-looking percentages that mean nothing, and that is
    worse than not shipping the role at all. Enforcing the Stage 1 gate in
    code stops you talking yourself past it at 1am.
    """
    # TODO Stage 4
    raise NotImplementedError
