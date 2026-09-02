"""Stage 2 -- text in, normalized skill ids out.

Same function runs over job postings and over resumes. That symmetry is what
makes the Stage 4 comparison meaningful: both sides are measured with the
same instrument, so a gap is a real gap rather than an artifact of two
different extractors disagreeing.

Matching is n-gram lookup against the taxonomy rather than one large regex.
Longest match wins and consumes its tokens, so "spring boot" does not also
register a separate "spring", and "data structures" does not register "data".

On NLP libraries: this module deliberately uses none. spaCy was installed
and then not used -- its off-the-shelf NER is trained on people, places and
organisations and will not tag Kafka or gRPC as a skill, and its sentence
segmentation buys nothing on Naukri descriptions, which are short and already
line-broken. A curated taxonomy plus fuzzy matching does the job at a
fraction of the cost and, unlike a model, can explain every decision it
makes. Measured against a labelled set in Stage 3, not assumed.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from analyzer.taxonomy import DATA, Taxonomy, normalize

MAX_NGRAM = 3

# Specific cloud providers. When one of these is present, the generic
# "Cloud Fundamentals" entry is suppressed: a posting saying "AWS Cloud"
# names one skill, not two. Six false positives in Stage 3 came from this.
_SPECIFIC_CLOUDS = {"aws", "azure", "gcp"}
_GENERIC_CLOUD = "cloud"


def _load_implications() -> dict[str, str]:
    """framework skill id -> language skill id it asserts."""
    raw = json.loads((DATA / "implies.json").read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for language, frameworks in raw.items():
        if language.startswith("_"):
            continue
        for fw in frameworks:
            out[fw] = language
    return out


IMPLIES = _load_implications()


def resolve_implications(skill_ids: set[str]) -> set[str]:
    """Add languages asserted by the frameworks present.

    A posting saying "React" asserts JavaScript without writing it. This was
    the largest single recall loss in Stage 3 (JavaScript missed 6 times).
    Kept deliberately narrow -- see data/implies.json for what is excluded
    and why.
    """
    return {IMPLIES[s] for s in skill_ids if s in IMPLIES} - skill_ids


def suppress_generic_cloud(skill_ids: set[str]) -> set[str]:
    """Drop the generic cloud entry when a specific provider is named."""
    if skill_ids & _SPECIFIC_CLOUDS:
        return skill_ids - {_GENERIC_CLOUD}
    return skill_ids


class Section(str, Enum):
    """Where in the document a mention was found."""

    SKILLS = "skills"          # resume: an explicit skills list
    EXPERIENCE = "experience"  # resume: demonstrated in work or projects
    EDUCATION = "education"    # resume: degrees, coursework
    OTHER = "other"


class Origin(str, Enum):
    """How strong the evidence is.

    This replaces the required/preferred split, which does not survive on
    Naukri's short descriptions -- only 14.9% carry both markers. See
    docs/stage1-data-audit.md.
    """

    TAGGED = "tagged"            # employer named it outright in tagsAndSkills
    DESCRIPTION = "description"  # found in the body text
    RESUME = "resume"


class Method(str, Enum):
    ALIAS = "alias"    # exact taxonomy hit
    FUZZY = "fuzzy"    # near-miss caught by rapidfuzz


@dataclass
class Mention:
    skill_id: str
    surface: str
    section: Section
    origin: Origin
    method: Method
    confidence: float
    evidence: str


# Resume section headers. Real resumes shout them, which is convenient.
_HEADINGS = [
    (Section.SKILLS, r"(technical\s+skills?|skills?\s*(&|and)?\s*\w*|technologies|tech\s+stack)"),
    (Section.EXPERIENCE, r"(experience|projects?|work\s+history|employment|internships?)"),
    (Section.EDUCATION, r"(education|academics?|qualifications?|certifications?|achievements?|awards?)"),
]
_HEADING_RE = re.compile(
    r"^\s*(" + "|".join(p for _, p in _HEADINGS) + r")\s*:?\s*$",
    re.IGNORECASE,
)


def split_sections(text: str) -> list[tuple[Section, str]]:
    """Split a resume into (section, chunk) pairs.

    A skill claimed under TECHNICAL SKILLS is a claim; the same word under
    EDUCATION is usually a course name. Weighting them identically is how you
    end up crediting someone with Java because their degree mentioned it.
    """
    lines = text.splitlines()
    chunks: list[tuple[Section, list[str]]] = [(Section.OTHER, [])]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        matched = None
        # A heading is short and, in practice, capitalised.
        if len(stripped) <= 40:
            for section, pattern in _HEADINGS:
                if re.fullmatch(r"\s*" + pattern + r"\s*:?\s*", stripped,
                                re.IGNORECASE):
                    matched = section
                    break
        if matched is not None:
            chunks.append((matched, []))
        else:
            chunks[-1][1].append(stripped)

    return [(sec, "\n".join(body)) for sec, body in chunks if body]


def _tokens(text: str) -> list[str]:
    return [t for t in normalize(text).split() if t]


def find_skills(text: str, taxonomy: Taxonomy) -> list[tuple[str, str]]:
    """Return (skill_id, matched_surface) pairs found in the text.

    Longest-first so multi-word skills win over their own fragments.
    """
    toks = _tokens(text)
    used = [False] * len(toks)
    found: list[tuple[str, str]] = []

    for n in range(MAX_NGRAM, 0, -1):
        for i in range(len(toks) - n + 1):
            if any(used[i:i + n]):
                continue
            gram = " ".join(toks[i:i + n])
            skill_id = taxonomy.resolve(gram)
            if skill_id:
                found.append((skill_id, gram))
                for j in range(i, i + n):
                    used[j] = True
    return found


def _evidence_for(surface: str, text: str, width: int = 90) -> str:
    """The line the match came from, trimmed. Shown to the user as proof."""
    head = surface.split()[0]
    for line in text.splitlines():
        if head in line.lower():
            line = line.strip()
            return line if len(line) <= width else line[:width].rstrip() + "..."
    return ""


def extract(text: str, taxonomy: Taxonomy,
            origin: Origin = Origin.RESUME,
            sectioned: bool = True,
            with_evidence: bool = True) -> list[Mention]:
    """Full pipeline: raw text -> deduped, normalized mentions.

    Keeps the highest-confidence mention per skill. Section confidence is a
    judgement call, recorded here so it can be defended: an explicit skills
    list is a direct claim, project text is demonstrated use, and a mention
    under education is usually incidental.

    with_evidence=False skips building the quoted source line. That scan
    walks every line of the document once per mention, and callers that only
    want the skill ids -- the gap report is one -- were paying for a string
    they immediately discarded.
    """
    weights = {
        Section.SKILLS: 1.0,
        Section.EXPERIENCE: 0.9,
        Section.OTHER: 0.7,
        Section.EDUCATION: 0.5,
    }

    pieces = split_sections(text) if sectioned else [(Section.OTHER, text)]
    best: dict[str, Mention] = {}

    for section, chunk in pieces:
        for skill_id, surface in find_skills(chunk, taxonomy):
            confidence = weights[section]
            existing = best.get(skill_id)
            if existing and existing.confidence >= confidence:
                continue
            best[skill_id] = Mention(
                skill_id=skill_id,
                surface=surface,
                section=section,
                origin=origin,
                method=Method.ALIAS,
                confidence=confidence,
                evidence=_evidence_for(surface, chunk) if with_evidence else "",
            )
    return list(best.values())


def extract_from_tags(tags: list[str], taxonomy: Taxonomy) -> list[Mention]:
    """Employer-named tags. Higher confidence, and fuzzy matching is safe here
    because each tag is already a short skill-shaped string rather than prose.
    """
    best: dict[str, Mention] = {}
    for tag in tags:
        skill_id = taxonomy.resolve(tag)
        method, confidence = Method.ALIAS, 1.0
        if not skill_id:
            if taxonomy.is_noise(tag):
                continue
            skill_id, score = taxonomy.fuzzy_resolve(tag)
            if not skill_id:
                continue
            method, confidence = Method.FUZZY, score
        if skill_id in best and best[skill_id].confidence >= confidence:
            continue
        best[skill_id] = Mention(
            skill_id=skill_id, surface=tag, section=Section.OTHER,
            origin=Origin.TAGGED, method=method,
            confidence=confidence, evidence=tag,
        )
    return list(best.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract skills from a text file.")
    parser.add_argument("--file", required=True, type=Path)
    args = parser.parse_args()

    taxonomy = Taxonomy.load()
    mentions = extract(args.file.read_text(encoding="utf-8"), taxonomy)

    print(f"{len(mentions)} skills found in {args.file.name}\n")
    print(f"{'skill':<32} {'section':<12} {'conf':>5}  evidence")
    print("-" * 96)
    for m in sorted(mentions, key=lambda x: (-x.confidence, x.skill_id)):
        print(f"{taxonomy.name_of(m.skill_id):<32} {m.section.value:<12} "
              f"{m.confidence:>5.2f}  {m.evidence[:44]}")


if __name__ == "__main__":
    main()
