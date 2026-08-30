"""Stage 2 -- the skill taxonomy: canonical names, aliases, categories.

This is the backbone of the whole system. Every downstream stage refers to
skills by canonical id, never by raw surface string.

Curated from the 403 tags appearing 20+ times across the loaded corpus, so
the vocabulary reflects what employers actually write. See
docs/stage1-data-audit.md for how that vocabulary was measured.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from rapidfuzz import process as fuzz_process

DATA = Path(__file__).resolve().parent.parent / "data"

# Surface forms that must survive normalisation as distinct tokens. Stripping
# punctuation blindly would collapse "c++" and "c#" into "c", which then
# matches the C language and inflates it enormously -- c/c++/c# are three of
# the most common tags in this corpus, so this is not a hypothetical.
_PROTECTED = {
    "c++": "cplusplus",
    "c#": "csharp",
    "f#": "fsharp",
    ".net": "dotnet",
    "ci/cd": "cicd",
    "node.js": "nodejs",
    "react.js": "reactjs",
    "vue.js": "vuejs",
    "asp.net": "aspdotnet",
    "ado.net": "adodotnet",
    "vb.net": "vbdotnet",
}

_JS_SUFFIX = re.compile(r"(?:\.js|js)$")


def normalize(text: str) -> str:
    """Fold a surface form to its comparison key.

    'Node.js', 'NodeJS' and 'node js' must all fold to the same key. Getting
    this wrong is the single largest source of false negatives -- when Stage 3
    recall comes back low, look here first.
    """
    s = str(text).strip().lower()
    if not s:
        return ""

    for literal, token in _PROTECTED.items():
        s = s.replace(literal, f" {token} ")

    s = re.sub(r"[^a-z0-9+#./\s-]", " ", s)
    s = re.sub(r"[-_/.]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    # 'nodejs' / 'node js' -> 'node js'; keeps the two spellings together
    # without merging unrelated words that merely end in s.
    parts = []
    for word in s.split():
        if word not in {"js"} and _JS_SUFFIX.search(word) and len(word) > 4:
            word = _JS_SUFFIX.sub(" js", word).strip()
        parts.append(word)
    return " ".join(parts).strip()


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    category: str
    aliases: tuple[str, ...] = ()


@dataclass
class Taxonomy:
    skills: dict[str, Skill] = field(default_factory=dict)
    _alias_index: dict[str, str] = field(default_factory=dict)
    _stop: set[str] = field(default_factory=set)

    @classmethod
    def load(cls, path: Path | None = None,
             stop_path: Path | None = None) -> Taxonomy:
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

        stop_path = stop_path or DATA / "stoplist.json"
        if stop_path.exists():
            groups = json.loads(stop_path.read_text(encoding="utf-8"))["stoplist"]
            for terms in groups.values():
                tax._stop.update(normalize(t) for t in terms)
            # Taxonomy wins over the stoplist: an explicit alias is a
            # deliberate mapping, the stoplist is a catch-all.
            tax._stop -= set(tax._alias_index)
        return tax

    def _build_alias_index(self) -> None:
        self._alias_index = {}
        for skill in self.skills.values():
            for surface in (skill.id, skill.name, *skill.aliases):
                key = normalize(surface)
                if key:
                    self._alias_index[key] = skill.id

    def resolve(self, surface: str) -> str | None:
        """Exact-match a surface string to a canonical skill id."""
        return self._alias_index.get(normalize(surface))

    def is_noise(self, surface: str) -> bool:
        """True when this is a known non-skill (job title, trait, degree)."""
        return normalize(surface) in self._stop

    def fuzzy_resolve(self, surface: str, cutoff: int = 92) -> tuple[str | None, float]:
        """Catch near-misses the alias index does not cover.

        Deliberately strict. At a lower cutoff 'data mining' starts matching
        'data modeling', which are different skills, and a wrong skill in a
        learning roadmap is worse than a missing one.
        """
        key = normalize(surface)
        if not key or len(key) < 3:
            return None, 0.0
        hit = fuzz_process.extractOne(key, self._alias_index.keys(),
                                      score_cutoff=cutoff)
        if hit is None:
            return None, 0.0
        matched, score, _ = hit
        return self._alias_index[matched], score / 100.0

    @property
    def surfaces(self) -> list[str]:
        """All known surface forms -- the search space for the matcher."""
        return list(self._alias_index)

    def name_of(self, skill_id: str) -> str:
        skill = self.skills.get(skill_id)
        return skill.name if skill else skill_id

    def __len__(self) -> int:
        return len(self.skills)


def audit_aliases(tax: Taxonomy) -> list[tuple[str, str, str]]:
    """Find aliases that are really a LIST of skills rather than one skill.

    Longest-match-wins is correct when the compound is more specific than its
    parts -- "spring boot" should beat "spring", "react native" should beat
    "react". It is a bug when the alias enumerates two skills: "html/css"
    normalises to "html css", resolves to HTML, consumes both tokens, and CSS
    is never recorded.

    The two cases are distinguished precisely: it is a list when one part
    resolves to the alias's own owner AND another part resolves to a
    different skill. Then the second skill is silently lost.

    Invisible in the output -- you only notice a skill you expected is absent
    -- which is why it gets a check rather than a comment.
    """
    problems: list[tuple[str, str, str]] = []
    for surface, owner in tax._alias_index.items():
        words = surface.split()
        if len(words) < 2:
            continue
        owners = [tax._alias_index.get(w) for w in words]
        if owner not in owners:
            continue  # more specific than its parts -- correct behaviour
        for word, other in zip(words, owners):
            if other and other != owner:
                problems.append((surface, owner, other))
    return problems
