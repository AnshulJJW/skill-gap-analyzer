"""Stage 5 -- the wire contract.

These models are the boundary between analyzer/ and web/. They double as the
API documentation, generated automatically at /docs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RoleOut(BaseModel):
    id: str
    name: str
    market: str
    total_postings: int


class ResourceOut(BaseModel):
    title: str
    url: str
    kind: str
    hours: int | None = None


class GapOut(BaseModel):
    skill_id: str
    skill_name: str
    category: str
    share: float
    postings: int
    marginal_gain: float
    evidence: str


class RoadmapStepOut(BaseModel):
    order: int
    skill_id: str
    skill_name: str
    reason: str
    is_prerequisite: bool
    resources: list[ResourceOut] = []


class AnalyzeIn(BaseModel):
    resume_text: str = Field(min_length=50, max_length=40_000)
    role_id: str
    top_n: int = Field(default=10, ge=1, le=25)


class AnalyzeOut(BaseModel):
    role_id: str
    role_name: str
    market: str
    total_postings: int
    coverage: float
    core_have: int
    core_total: int
    have: list[str]
    unused: list[str]
    gaps: list[GapOut]
    roadmap: list[RoadmapStepOut]


class HealthOut(BaseModel):
    status: str
    roles_loaded: int
    skills_loaded: int
