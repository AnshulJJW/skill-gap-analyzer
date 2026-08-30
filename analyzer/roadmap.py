"""Stage 4 -- turning a ranked gap list into a sane learning order.

Two ingredients, both hand-curated, and the README says so plainly: a
curated map beats a bad recommender, and the distinction between "I learned
this" and "I encoded domain knowledge" is worth being precise about.

  - prereqs.json   : skill dependency edges (Docker before Kubernetes)
  - resources.json : free resources per skill

The ranking from gap.py answers "what adds the most coverage". This answers
"what can you actually start on Monday" -- if the highest-impact skill sits
behind something you don't have, the prerequisite is promoted above it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


@dataclass
class Resource:
    title: str
    url: str
    kind: str          # "course" | "docs" | "book" | "video" | "practice"
    hours: int | None = None


@dataclass
class RoadmapStep:
    order: int
    skill_id: str
    skill_name: str
    reason: str                       # why it is here, in plain words
    marginal_gain: float = 0.0
    is_prerequisite: bool = False     # pulled in, not asked for
    unlocks: list[str] = field(default_factory=list)
    resources: list[Resource] = field(default_factory=list)


def _strip_notes(raw: dict) -> dict:
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def load_prereqs(path: Path | None = None) -> dict[str, list[str]]:
    """skill_id -> skills that should be learned first."""
    path = path or DATA / "prereqs.json"
    return _strip_notes(json.loads(path.read_text(encoding="utf-8")))


def load_resources(path: Path | None = None) -> dict[str, list[Resource]]:
    path = path or DATA / "resources.json"
    raw = _strip_notes(json.loads(path.read_text(encoding="utf-8")))
    return {sid: [Resource(**r) for r in items] for sid, items in raw.items()}


def _detect_cycle(prereqs: dict[str, list[str]]) -> list[str] | None:
    """A cycle means bad data, so fail loudly rather than silently truncating."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[str, int] = {}

    def visit(node: str, path: list[str]) -> list[str] | None:
        colour[node] = GREY
        for dep in prereqs.get(node, []):
            c = colour.get(dep, WHITE)
            if c == GREY:
                return path + [node, dep]
            if c == WHITE:
                found = visit(dep, path + [node])
                if found:
                    return found
        colour[node] = BLACK
        return None

    for node in prereqs:
        if colour.get(node, WHITE) == WHITE:
            found = visit(node, [])
            if found:
                return found
    return None


def build_roadmap(gaps, have: set[str], tax, max_steps: int = 8) -> list[RoadmapStep]:
    """Order the gaps so prerequisites come first.

    Walks the ranked gaps in order. Before emitting one, emits any
    prerequisite the candidate does not already have -- so the list is always
    something you can start at the top of, rather than a wish list.
    """
    prereqs = load_prereqs()
    resources = load_resources()

    cycle = _detect_cycle(prereqs)
    if cycle:
        raise ValueError(f"prereqs.json contains a cycle: {' -> '.join(cycle)}")

    acquired = set(have)
    steps: list[RoadmapStep] = []
    gain_of = {g.skill_id: g.marginal_gain for g in gaps}
    wanted = [g.skill_id for g in gaps]

    def emit(skill_id: str, is_prereq: bool, needed_by: str | None) -> None:
        if skill_id in acquired or len(steps) >= max_steps:
            return
        for dep in prereqs.get(skill_id, []):
            if dep not in acquired:
                emit(dep, True, skill_id)
        if skill_id in acquired or len(steps) >= max_steps:
            return
        acquired.add(skill_id)
        if is_prereq:
            reason = f"needed before {tax.name_of(needed_by)}"
        else:
            reason = f"adds {gain_of.get(skill_id, 0):.0%} coverage on its own"
        steps.append(RoadmapStep(
            order=len(steps) + 1,
            skill_id=skill_id,
            skill_name=tax.name_of(skill_id),
            reason=reason,
            marginal_gain=gain_of.get(skill_id, 0.0),
            is_prerequisite=is_prereq,
            unlocks=[s for s, deps in prereqs.items()
                     if skill_id in deps and s in wanted],
            resources=resources.get(skill_id, []),
        ))

    for skill_id in wanted:
        emit(skill_id, False, None)
        if len(steps) >= max_steps:
            break
    return steps
