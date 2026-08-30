"""Stage 1 -- frozen Naukri snapshot -> database.

Run:  python scripts/load_db.py

Cleaning happens here rather than by hand so it is reproducible: when Stage 3
says the data was the problem, you can change one rule and re-run.

The 250-posting gate is enforced in code and exits non-zero. A role backed by
40 postings produces confident-looking percentages that mean nothing, and
enforcing it here stops you talking yourself past it at 1am.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import delete, func, insert, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer.db import (
    create_all,
    get_engine,
    posting_skills,
    postings,
    provided_skills,
    sources,
)

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MIN_POSTINGS = 250

NAUKRI_FILES = ["naukri_software_engineer.csv", "naukri_data_scientist.csv"]
USECOLS = ["jobId", "title", "companyName", "location", "experience",
           "jobDescription", "tagsAndSkills", "createdDate"]


def clean_html(raw: str) -> str:
    """Naukri descriptions are HTML fragments; <br> carries the line breaks."""
    s = html.unescape(str(raw))
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</?(p|div|li|ul|ol|tr|td)[^>]*>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def dedupe_key(title: str, company: str, desc: str) -> str:
    """Same posting reposted under a new id is one piece of evidence, not ten.

    Duplicates silently inflate every frequency in Stage 4 and the output
    still looks entirely plausible -- the failure most likely to survive
    undetected all the way to a demo.
    """
    blob = f"{title.lower().strip()}|{company.lower().strip()}|{desc[:500].lower()}"
    return hashlib.md5(blob.encode("utf-8")).hexdigest()


# Reading a minimum experience requirement out of prose.
#
# The first version of this matched any number followed by "year", which read
# "2-5 years" as five and discarded genuinely entry-level postings. Three of
# the forty labelled postings were removed that way. A range states a
# MINIMUM of its lower bound; only "N+" and "at least N" state a floor.
_RANGE = re.compile(r"(\d{1,2}(?:\.\d)?)\s*(?:-|–|to)\s*\d{1,2}(?:\.\d)?\s*\+?\s*y(?:ea)?rs?", re.IGNORECASE)
_PLUS = re.compile(r"(\d{1,2}(?:\.\d)?)\s*\+\s*y(?:ea)?rs?", re.IGNORECASE)
_ATLEAST = re.compile(r"(?:at least|minimum(?:\s+of)?|min\.?)\s+(\d{1,2}(?:\.\d)?)\s*\+?\s*y(?:ea)?rs?", re.IGNORECASE)


def min_years_required(text: str) -> float | None:
    """Lowest years-of-experience floor the text states, or None.

    Ranges contribute their lower bound: "2-5 years" asks for two, not five.
    Taking the smallest floor found is deliberate -- a posting saying both
    "2-5 years overall" and "5+ years in React" is still open to someone with
    two years, and over-filtering costs real data.
    """
    floors = [float(m.group(1)) for m in _RANGE.finditer(text)]
    floors += [float(m.group(1)) for m in _PLUS.finditer(text)]
    floors += [float(m.group(1)) for m in _ATLEAST.finditer(text)]
    return min(floors) if floors else None


def assign_role(title: str, description: str, cfg: dict) -> str | None:
    """Match a posting to a role, then apply three disqualifying checks.

    Stage 3 hand-labelling found 7 of 40 postings (17.5%) misfiled -- GIS,
    firmware and iOS roles filed as backend, three senior roles filed as
    entry-level, a business analyst filed as a data analyst. Three distinct
    causes, so three distinct checks.
    """
    t = title.lower()
    d = description.lower()
    desc_ex = cfg.get("exclude_description", {})
    max_years = cfg.get("min_years_from_description", {}).get("max_years", 99)

    for role in cfg["roles"]:
        if any(x in t for x in role["exclude"]):
            continue
        if not any(i in t for i in role["include"]):
            continue

        # 1. disqualifying signal in the description, not the title
        if any(x in d for x in desc_ex.get(role["id"], [])):
            return None

        # 2. body text states a higher floor than the structured field claims
        floor = min_years_required(description)
        if floor is not None and floor > max_years:
            return None

        return role["id"]
    return None


def load_naukri(cfg: dict) -> pd.DataFrame:
    frames = [pd.read_csv(RAW / f, usecols=USECOLS, low_memory=False)
              for f in NAUKRI_FILES]
    df = pd.concat(frames, ignore_index=True)
    print(f"  read            {len(df):>7,}")

    df = df.drop_duplicates("jobId")
    print(f"  unique jobId    {len(df):>7,}")

    years = df.experience.fillna("").str.extract(r"^(\d+)")[0].astype(float)
    df = df[years <= cfg["entry_level_max_years"]]
    print(f"  entry-level     {len(df):>7,}  (0-{cfg['entry_level_max_years']} yrs)")

    df["description_raw"] = df.jobDescription.fillna("").map(clean_html)
    df["role_id"] = [
        assign_role(str(t), d, cfg)
        for t, d in zip(df.title.fillna(""), df.description_raw)
    ]
    df = df[df.role_id.notna()]
    print(f"  role-matched    {len(df):>7,}")

    df["description"] = df.description_raw
    df = df[df.description.str.len() >= 60]
    print(f"  desc >= 60ch    {len(df):>7,}")

    df["dedupe_key"] = [
        dedupe_key(str(t), str(c), d)
        for t, c, d in zip(df.title, df.companyName.fillna(""), df.description)
    ]
    df = df.drop_duplicates("dedupe_key")
    print(f"  content-deduped {len(df):>7,}")
    return df


def main() -> int:
    cfg = json.loads((ROOT / "data" / "roles.json").read_text(encoding="utf-8"))
    engine = get_engine()
    create_all(engine)

    print("naukri:")
    df = load_naukri(cfg)

    with engine.begin() as conn:
        # Clear children first, explicitly. SQLite does not enforce
        # ON DELETE CASCADE unless foreign keys are switched on per
        # connection, so deleting postings alone leaves orphaned rows --
        # and because primary keys restart from 1, the next load collides
        # with them on the unique constraint.
        conn.execute(delete(posting_skills))
        conn.execute(delete(provided_skills))
        conn.execute(delete(postings).where(postings.c.source_id == "naukri"))
        conn.execute(delete(sources).where(sources.c.id == "naukri"))
        conn.execute(insert(sources), {
            "id": "naukri", "name": "Naukri.com (Dec 2024 snapshot)",
            "market": "india", "has_section_split": 0,
            "notes": "Short descriptions; tagsAndSkills replaces required/preferred.",
        })

        rows = [{
            "source_id": "naukri",
            "external_id": str(r.jobId),
            "role_id": r.role_id,
            "title": str(r.title),
            "company": None if pd.isna(r.companyName) else str(r.companyName),
            "location": None if pd.isna(r.location) else str(r.location),
            "experience": None if pd.isna(r.experience) else str(r.experience),
            "description": r.description,
            "dedupe_key": r.dedupe_key,
        } for r in df.itertuples()]
        conn.execute(insert(postings), rows)

        # map external_id -> db id so provided skills attach correctly
        idmap = dict(conn.execute(
            select(postings.c.external_id, postings.c.id)
            .where(postings.c.source_id == "naukri")
        ).all())

        tag_rows, seen = [], set()
        for r in df.itertuples():
            pid = idmap.get(str(r.jobId))
            if pid is None or pd.isna(r.tagsAndSkills):
                continue
            for tag in str(r.tagsAndSkills).split(","):
                tag = tag.strip().lower()
                if tag and (pid, tag) not in seen:
                    seen.add((pid, tag))
                    tag_rows.append({"posting_id": pid, "raw_skill": tag})
        if tag_rows:
            conn.execute(insert(provided_skills), tag_rows)

    print(f"\nloaded {len(rows):,} postings, {len(tag_rows):,} provided-skill tags\n")

    print(f"{'role':<20} {'postings':>9}   gate({MIN_POSTINGS})")
    print("-" * 45)
    failed = []
    with engine.connect() as conn:
        counts = dict(conn.execute(
            select(postings.c.role_id, func.count())
            .where(postings.c.source_id == "naukri")
            .group_by(postings.c.role_id)
        ).all())
    for role in cfg["roles"]:
        n = counts.get(role["id"], 0)
        ok = n >= MIN_POSTINGS
        print(f"{role['name']:<20} {n:>9,}   {'PASS' if ok else 'FAIL'}")
        if not ok:
            failed.append(role["name"])

    if failed:
        print(f"\nGATE FAILED for: {', '.join(failed)}")
        print("Widen the role patterns or drop the role. Do not proceed.")
        return 1
    print("\nStage 1 gate PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
