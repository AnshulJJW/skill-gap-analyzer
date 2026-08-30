"""Stage 2 -- run the extractor over every loaded posting.

    python scripts/extract_skills.py

Fills posting_skills, the table of skills OUR extractor found. Naukri's own
tags stay in provided_skills, untouched, so Stage 3 can measure one against
the other.

Re-runnable: it clears its own output first, so changing the taxonomy and
re-running always gives a clean result.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import delete, insert, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer.db import get_engine, posting_skills, postings, provided_skills
from analyzer.extract import Origin, extract, extract_from_tags
from analyzer.taxonomy import Taxonomy, audit_aliases

BATCH = 2000


def main() -> int:
    tax = Taxonomy.load()
    print(f"taxonomy: {len(tax)} skills, {len(tax.surfaces)} surface forms")

    lost = sorted(set(audit_aliases(tax)))
    if lost:
        print(f"note: {len(lost)} compound aliases imply a second skill "
              "(handled by the Stage 4 prerequisite graph, not here)")

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(delete(posting_skills))

        rows = conn.execute(
            select(postings.c.id, postings.c.description)
        ).all()
        tags_by_posting: dict[int, list[str]] = {}
        for pid, tag in conn.execute(
            select(provided_skills.c.posting_id, provided_skills.c.raw_skill)
        ):
            tags_by_posting.setdefault(pid, []).append(tag)

    print(f"postings: {len(rows):,}")

    out: list[dict] = []
    per_posting = Counter()
    from_tags = from_desc = 0

    for pid, description in rows:
        seen: dict[str, dict] = {}

        for m in extract_from_tags(tags_by_posting.get(pid, []), tax):
            seen[m.skill_id] = {
                "posting_id": pid, "skill_id": m.skill_id,
                "origin": Origin.TAGGED.value, "method": m.method.value,
                "confidence": m.confidence, "evidence": m.evidence[:200],
            }
            from_tags += 1

        for m in extract(description, tax, origin=Origin.DESCRIPTION,
                         sectioned=False):
            if m.skill_id in seen:
                continue
            seen[m.skill_id] = {
                "posting_id": pid, "skill_id": m.skill_id,
                "origin": Origin.DESCRIPTION.value, "method": m.method.value,
                "confidence": round(m.confidence * 0.8, 3),
                "evidence": m.evidence[:200],
            }
            from_desc += 1

        per_posting[len(seen)] += 1
        out.extend(seen.values())

    with engine.begin() as conn:
        for i in range(0, len(out), BATCH):
            conn.execute(insert(posting_skills), out[i:i + BATCH])

    total = sum(per_posting.values())
    empty = per_posting[0]
    mean = sum(k * v for k, v in per_posting.items()) / max(total, 1)
    print()
    print(f"skill mentions written {len(out):>9,}")
    print(f"  from employer tags   {from_tags:>9,}")
    print(f"  from description     {from_desc:>9,}")
    print(f"mean skills / posting  {mean:>9.1f}")
    print(f"postings with none     {empty:>9,}  ({empty / total:.1%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
