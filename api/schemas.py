"""Stage 5 -- the wire contract.

These models are the boundary between analyzer/ and web/. Define them before
writing either side; they double as your API docs for free via /docs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RoleOut(BaseModel):
    id: str
    name: str
    total_postings: int


class ResourceOut(BaseModel):
    title: str
    url: str
    kind: str
    hours: int | None = None


class GapOut(BaseModel):
    skill_id: str
    skill_name: str
    required_pct: float
    postings_blocked: int
    evidence: str
    resources: list[ResourceOut] = []


class AnalyzeIn(BaseModel):
    resume_text: str = Field(min_length=50, max_length=40_000)
    role_id: str


class AnalyzeOut(BaseModel):
    role_name: str
    total_postings: int
    coverage: float
    have: list[str]
    gaps: list[GapOut]
