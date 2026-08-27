"""Database schema and connection -- the single source of truth.

Defined with SQLAlchemy Core rather than raw DDL so the same definitions run
on SQLite locally and Postgres in production. Stage 7 changes DATABASE_URL
and nothing else.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_URL = f"sqlite:///{ROOT / 'data' / 'skillgap.db'}"

metadata = MetaData()

sources = Table(
    "sources", metadata,
    Column("id", String(32), primary_key=True),          # 'naukri', 'linkedin'
    Column("name", String(128), nullable=False),
    Column("market", String(32), nullable=False),        # 'india', 'global'
    Column("collected_on", Date),
    Column("has_section_split", Integer, nullable=False, default=0),
    Column("notes", Text),
)

postings = Table(
    "postings", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_id", String(32), ForeignKey("sources.id"), nullable=False),
    Column("external_id", String(64)),
    Column("role_id", String(64), nullable=False, index=True),
    Column("title", Text, nullable=False),
    Column("company", Text),
    Column("location", Text),
    Column("experience", String(32)),
    Column("description", Text, nullable=False),
    Column("posted_on", Date),
    Column("dedupe_key", String(32), nullable=False),
    # Dedupe within a source, not across it. The same role genuinely
    # appearing on two boards is two pieces of evidence; the same posting
    # repeated ten times on one board is one.
    UniqueConstraint("source_id", "dedupe_key", name="uq_posting_source_dedupe"),
)

# Skills the employer named outright (Naukri's tagsAndSkills). Strong signal:
# this is the axis that replaces required-vs-preferred, which does not
# survive on short Naukri descriptions. See docs/stage1-data-audit.md.
provided_skills = Table(
    "provided_skills", metadata,
    Column("posting_id", Integer, ForeignKey("postings.id", ondelete="CASCADE"),
           primary_key=True),
    Column("raw_skill", String(128), primary_key=True),
)

# Skills OUR extractor found. Kept separate from provided_skills so the
# comparison between the two stays honest -- it is a free Stage 3 baseline.
posting_skills = Table(
    "posting_skills", metadata,
    Column("posting_id", Integer, ForeignKey("postings.id", ondelete="CASCADE"),
           primary_key=True),
    Column("skill_id", String(64), primary_key=True, index=True),
    Column("origin", String(16), primary_key=True),   # 'tagged' | 'description'
    Column("method", String(16), nullable=False),     # 'alias'|'fuzzy'|'embedding'
    Column("confidence", Float, nullable=False),
    Column("evidence", Text),
)


def get_engine(url: str | None = None):
    return create_engine(url or os.environ.get("DATABASE_URL") or DEFAULT_URL,
                         future=True)


def create_all(engine) -> None:
    metadata.create_all(engine)
