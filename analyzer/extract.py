"""Stage 2 -- text in, normalized skill ids out.

Order of operations, and it matters:
  1. taxonomy alias matching        <- does most of the work
  2. spaCy for sentence/section splitting and noun-phrase candidates
  3. embedding similarity          <- fallback only, for what 1 misses

Note what spaCy is NOT used for: off-the-shelf NER will not tag Kafka or
gRPC as skills, because it is trained on people, places and organisations.
Using it that way is the mistake this module exists to avoid.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from analyzer.taxonomy import Taxonomy


class Section(str, Enum):
    """Where in the document a mention was found."""
    REQUIRED = "required"      # posting: hard requirements
    PREFERRED = "preferred"    # posting: nice-to-haves
    SKILLS = "skills"          # resume: explicit skills section
    EXPERIENCE = "experience"  # resume: demonstrated in work/projects
    OTHER = "other"


class MatchMethod(str, Enum):
    ALIAS = "alias"            # exact taxonomy hit -- high confidence
    FUZZY = "fuzzy"            # rapidfuzz near-miss
    EMBEDDING = "embedding"    # semantic fallback -- log and review these


@dataclass
class Mention:
    skill_id: str
    surface: str               # the literal text that matched
    section: Section
    method: MatchMethod
    confidence: float
    evidence: str              # the sentence it came from, for the UI


def split_sections(text: str) -> list[tuple[Section, str]]:
    """Split raw text into (section, chunk) pairs.

    For postings this is the required/preferred split -- that distinction is
    what makes the Stage 4 output feel intelligent rather than mechanical.
    For resumes it separates demonstrated experience from a keyword dump.
    """
    # TODO Stage 2: heading regexes for both document types.
    raise NotImplementedError


def extract(text: str, taxonomy: Taxonomy) -> list[Mention]:
    """Full pipeline: raw text -> deduped, normalized mentions."""
    # TODO Stage 2:
    #   - split_sections
    #   - alias pass over each chunk (rapidfuzz, score_cutoff ~90)
    #   - embedding pass over leftover noun phrases
    #   - dedupe by skill_id, keeping the highest-confidence mention
    raise NotImplementedError


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract skills from a text file.")
    parser.add_argument("--file", required=True, type=Path)
    args = parser.parse_args()

    taxonomy = Taxonomy.load()
    mentions = extract(args.file.read_text(encoding="utf-8"), taxonomy)
    for m in sorted(mentions, key=lambda x: -x.confidence):
        print(f"{m.skill_id:<24} {m.method.value:<10} {m.confidence:.2f}  {m.section.value}")


if __name__ == "__main__":
    main()
