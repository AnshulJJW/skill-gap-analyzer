"""Stage 4 -- offline build step: postings -> data/profiles/<role>__<source>.json

    python scripts/build_profiles.py

Run this whenever the taxonomy or the dataset changes. The API only ever
reads the output. Keeping this offline is what keeps the API inside the
512MB / 10s cold-start budget in Stage 5's gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer.db import get_engine, posting_skills, postings, sources
from analyzer.profiles import build
from analyzer.taxonomy import Taxonomy

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    cfg = json.loads((ROOT / "data" / "roles.json").read_text(encoding="utf-8"))
    tax = Taxonomy.load()
    engine = get_engine()

    with engine.connect() as conn:
        markets = dict(conn.execute(select(sources.c.id, sources.c.market)).all())
        rows = conn.execute(
            select(postings.c.role_id, postings.c.source_id, postings.c.id,
                   posting_skills.c.skill_id, posting_skills.c.origin)
            .select_from(postings.join(
                posting_skills, postings.c.id == posting_skills.c.posting_id))
        ).all()

    grouped: dict[tuple[str, str], list] = {}
    for role_id, source_id, pid, skill_id, origin in rows:
        grouped.setdefault((role_id, source_id), []).append((pid, skill_id, origin))

    names = {r["id"]: r["name"] for r in cfg["roles"]}
    print(f"{'role':<18}{'source':<10}{'postings':>9}{'skills':>8}   top demand")
    print("-" * 78)

    written = 0
    for (role_id, source_id), triples in sorted(grouped.items()):
        try:
            profile = build(role_id, names.get(role_id, role_id), source_id,
                            markets.get(source_id, "unknown"), triples)
        except ValueError as exc:
            print(f"SKIPPED {exc}")
            continue
        profile.save()
        written += 1
        top = ", ".join(f"{tax.name_of(d.skill_id)} {d.share:.0%}"
                        for d in profile.demands[:4])
        print(f"{role_id:<18}{source_id:<10}{profile.total_postings:>9,}"
              f"{len(profile.demands):>8}   {top}")

    print(f"\n{written} profiles written to data/profiles/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
