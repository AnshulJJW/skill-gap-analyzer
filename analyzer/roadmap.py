"""Stage 4 -- turning a ranked gap list into a sane learning order.

Two ingredients, both hand-curated, and be honest about that in the README:
a curated map beats a bad recommender, and interviewers respect the
distinction between "I learned this" and "I encoded domain knowledge".

  - prereqs.json   : skill dependency edges (Docker before Kubernetes)
  - resources.json : free resources per skill
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


@dataclass
class Resource:
    title: str
    url: str
    kind: str          # "course" | "docs" | "book" | "video" | "practice"
    hours: int | None  # rough time cost, for the "fastest path" framing


@dataclass
class RoadmapStep:
    order: int
    skill_id: str
    skill_name: str
    unlocked_by: list[str]   # prerequisites already satisfied
    resources: list[Resource]


def load_prereqs(path: Path | None = None) -> dict[str, list[str]]:
    """skill_id -> list of skill_ids that should be learned first."""
    path = path or DATA / "prereqs.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_resources(path: Path | None = None) -> dict[str, list[Resource]]:
    path = path or DATA / "resources.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {sid: [Resource(**r) for r in items] for sid, items in raw.items()}


def build_roadmap(gap_skill_ids: list[str], have: set[str]) -> list[RoadmapStep]:
    """Topologically sort the gaps so prerequisites come first.

    Ranking gives the order by impact; this reorders it by what is actually
    learnable next. If a high-impact skill has an unmet prerequisite, the
    prerequisite is promoted above it.
    """
    # TODO Stage 4: topological sort over the prereq DAG, restricted to
    #               gap_skill_ids plus any missing prerequisites they pull in.
    #               Detect cycles and fail loudly -- a cycle means bad data.
    raise NotImplementedError
