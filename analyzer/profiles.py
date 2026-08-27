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
    role_id: str            # "sde1-backend"
    role_name: str          # "SDE-1 Backend"
    total_postings: int
    demands: list[SkillDemand]

    def save(self) -> Path:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        path = PROFILE_DIR / f"{self.role_id}.json"
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, role_id: str) -> "RoleProfile":
        raw = json.loads((PROFILE_DIR / f"{role_id}.json").read_text(encoding="utf-8"))
        raw["demands"] = [SkillDemand(**d) for d in raw["demands"]]
        return cls(**raw)


def build(role_id: str, postings: list[dict]) -> RoleProfile:
    """Aggregate extracted mentions across postings into one profile.

    Guard rail: if len(postings) < 250, raise. A role backed by 40 postings
    produces confident-looking percentages that mean nothing, and that is
    worse than not shipping the role at all. See Stage 1's gate.
    """
    # TODO Stage 4
    raise NotImplementedError
