"""Look inside the database. Read-only -- it cannot break anything.

    python scripts/explore.py                  what is in the database
    python scripts/explore.py roles            posting counts per role
    python scripts/explore.py skills backend   top employer-named skills
    python scripts/explore.py show backend     one full posting, as stored
    python scripts/explore.py find kafka       postings mentioning a word
    python scripts/explore.py sql "SELECT ..." run your own query

The short role names are 'backend', 'frontend', 'analyst'.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import func, select, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer.db import get_engine, postings, provided_skills

ROLE_ALIASES = {
    "backend": "sde1-backend",
    "frontend": "frontend",
    "analyst": "data-analyst",
    "data": "data-analyst",
}


def role_id(name: str) -> str:
    return ROLE_ALIASES.get(name.lower(), name)


def cmd_overview(engine) -> None:
    with engine.connect() as c:
        total = c.execute(select(func.count()).select_from(postings)).scalar()
        tags = c.execute(select(func.count()).select_from(provided_skills)).scalar()
        print(f"postings           {total:>8,}")
        print(f"employer tags      {tags:>8,}")
        print()
        print("tables:")
        for t in ("sources", "postings", "provided_skills", "posting_skills"):
            n = c.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"  {t:<20} {n:>8,} rows")
    print()
    print("try:  python scripts/explore.py roles")


def cmd_roles(engine) -> None:
    with engine.connect() as c:
        rows = c.execute(
            select(postings.c.role_id, func.count())
            .group_by(postings.c.role_id).order_by(func.count().desc())
        ).all()
    print(f"{'role':<20} {'postings':>9}")
    print("-" * 31)
    for rid, n in rows:
        print(f"{rid:<20} {n:>9,}")


def cmd_skills(engine, role: str, limit: int = 20) -> None:
    rid = role_id(role)
    with engine.connect() as c:
        total = c.execute(
            select(func.count()).select_from(postings)
            .where(postings.c.role_id == rid)
        ).scalar()
        if not total:
            print(f"no postings for role '{rid}'")
            return
        rows = c.execute(
            select(provided_skills.c.raw_skill, func.count().label("n"))
            .select_from(provided_skills.join(
                postings, provided_skills.c.posting_id == postings.c.id))
            .where(postings.c.role_id == rid)
            .group_by(provided_skills.c.raw_skill)
            .order_by(func.count().desc()).limit(limit)
        ).all()
    print(f"{rid} -- {total:,} postings\n")
    print(f"{'tag':<30} {'count':>7} {'share':>8}")
    print("-" * 47)
    for skill, n in rows:
        print(f"{skill:<30} {n:>7,} {n / total:>7.1%}")


def cmd_show(engine, role: str) -> None:
    rid = role_id(role)
    with engine.connect() as c:
        row = c.execute(
            select(postings.c.id, postings.c.title, postings.c.company,
                   postings.c.location, postings.c.experience,
                   postings.c.description)
            .where(postings.c.role_id == rid).limit(1)
        ).first()
        if not row:
            print(f"no postings for role '{rid}'")
            return
        tags = c.execute(
            select(provided_skills.c.raw_skill)
            .where(provided_skills.c.posting_id == row[0])
        ).scalars().all()
    print(f"{row[1]}  |  {row[2]}  |  {row[3]}  |  {row[4]}")
    print("=" * 70)
    print(row[5][:1500])
    print("=" * 70)
    print("employer tags:", ", ".join(tags) or "(none)")


def cmd_find(engine, word: str, limit: int = 5) -> None:
    with engine.connect() as c:
        rows = c.execute(
            select(postings.c.title, postings.c.company, postings.c.role_id)
            .where(postings.c.description.ilike(f"%{word}%")).limit(limit)
        ).all()
        n = c.execute(
            select(func.count()).select_from(postings)
            .where(postings.c.description.ilike(f"%{word}%"))
        ).scalar()
        total = c.execute(select(func.count()).select_from(postings)).scalar()
    print(f"'{word}' appears in {n:,} of {total:,} postings ({n / total:.1%})\n")
    for title, company, rid in rows:
        print(f"  {title[:44]:<45} {company[:22]:<23} {rid}")


def cmd_sql(engine, query: str) -> None:
    with engine.connect() as c:
        result = c.execute(text(query))
        cols = list(result.keys())
        rows = result.fetchall()
    print(" | ".join(cols))
    print("-" * 60)
    for r in rows[:40]:
        print(" | ".join(str(v)[:30] for v in r))
    if len(rows) > 40:
        print(f"... and {len(rows) - 40} more rows")


def main() -> None:
    engine = get_engine()
    args = sys.argv[1:]
    if not args:
        cmd_overview(engine)
    elif args[0] == "roles":
        cmd_roles(engine)
    elif args[0] == "skills":
        cmd_skills(engine, args[1] if len(args) > 1 else "backend")
    elif args[0] == "show":
        cmd_show(engine, args[1] if len(args) > 1 else "backend")
    elif args[0] == "find":
        cmd_find(engine, args[1] if len(args) > 1 else "python")
    elif args[0] == "sql":
        cmd_sql(engine, args[1])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
