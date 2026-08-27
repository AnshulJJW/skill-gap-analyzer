"""Stage 1 -- the skill taxonomy: canonical names, aliases, categories.

This is the backbone of the whole system. Every downstream stage refers to
skills by canonical id, never by raw surface string.

Seed data lives in data/skills.json. Grow it from ESCO or Lightcast Open
Skills rather than by hand once the shape is settled.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


@dataclass(frozen=True)
class Skill:
    id: str                          # canonical id, e.g. "postgresql"
    name: str                        # display name, e.g. "PostgreSQL"
    category: str                    # e.g. "database", "language", "devops"
    aliases: tuple[str, ...] = ()    # e.g. ("postgres", "psql")


@dataclass
class Taxonomy:
    skills: dict[str, Skill] = field(default_factory=dict)
    _alias_index: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> Taxonomy:
        path = path or DATA / "skills.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        tax = cls()
        for entry in raw["skills"]:
            skill = Skill(
                id=entry["id"],
                name=entry["name"],
                category=entry["category"],
                aliases=tuple(entry.get("aliases", [])),
            )
            tax.skills[skill.id] = skill
        tax._build_alias_index()
        return tax

    def _build_alias_index(self) -> None:
        """Map every surface form (name + aliases + id) to its canonical id."""
        self._alias_index = {}
        for skill in self.skills.values():
            for surface in (skill.id, skill.name, *skill.aliases):
                self._alias_index[normalize(surface)] = skill.id

    def resolve(self, surface: str) -> str | None:
        """Exact-match a surface string to a canonical skill id."""
        return self._alias_index.get(normalize(surface))

    @property
    def surfaces(self) -> list[str]:
        """All known surface forms -- the search space for the matcher."""
        return list(self._alias_index)


def normalize(text: str) -> str:
    """Fold a surface form to its comparison key.

    'Node.js' / 'NodeJS' / 'node js' must all fold to the same key. Getting
    this wrong is the single most common source of false negatives -- when
    Stage 3 recall comes back low, look here first.
    """
    # TODO Stage 2: casefold, strip punctuation, collapse whitespace,
    #               handle the .js / -js / js suffix family.
    raise NotImplementedError
