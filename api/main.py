"""Stage 5 -- a thin wrapper. Four routes, no business logic.

If this file grows past ~120 lines, logic is leaking out of analyzer/ and
into the routes. Push it back.

Free-tier reality check (Render: 512MB, cold start after inactivity):
  - the taxonomy and every role profile load ONCE at startup, not per request
  - profiles are read from precomputed JSON, never recomputed from postings
  - only the resume is processed live, and that is pure string matching
  - nothing imports torch or a transformer, so there is no model to warm

Stage 5's gate is cold start under 10s and resident memory under 400MB.
Measure it with scripts/measure_api.py rather than assuming.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from analyzer.gap import analyze
from analyzer.profiles import RoleProfile
from analyzer.resume import MAX_BYTES, ResumeParseError, parse_pdf
from analyzer.roadmap import load_resources
from analyzer.taxonomy import Taxonomy
from api.schemas import (
    AnalyzeIn,
    AnalyzeOut,
    HealthOut,
    ParsedResumeOut,
    ResourceOut,
    RoleOut,
)

STATE: dict = {}

# Vite's dev server, plus whatever Stage 7 deploys to.
ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",") if o.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load everything once. Anything added here lands on the cold start."""
    STATE["taxonomy"] = Taxonomy.load()
    STATE["resources"] = load_resources()
    STATE["profiles"] = {}
    for key in RoleProfile.available():
        role_id, _, source_id = key.partition("__")
        if source_id:
            STATE["profiles"][role_id] = RoleProfile.load(role_id, source_id)
    yield
    STATE.clear()


app = FastAPI(
    title="Skill-Gap Analyzer",
    version="0.1.0",
    description=(
        "Compares a resume against real job-posting demand for a role and "
        "returns a ranked, prerequisite-ordered learning path."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(
        status="ok",
        roles_loaded=len(STATE.get("profiles", {})),
        skills_loaded=len(STATE.get("taxonomy", {}) or {}),
    )


@app.get("/roles", response_model=list[RoleOut])
def list_roles() -> list[RoleOut]:
    return [
        RoleOut(id=p.role_id, name=p.role_name, market=p.market,
                total_postings=p.total_postings)
        for p in sorted(STATE["profiles"].values(),
                        key=lambda p: -p.total_postings)
    ]


@app.get("/resources/{skill_id}", response_model=list[ResourceOut])
def resources(skill_id: str) -> list[ResourceOut]:
    if skill_id not in STATE["taxonomy"].skills:
        raise HTTPException(404, f"unknown skill {skill_id!r}")
    return [ResourceOut(**vars(r))
            for r in STATE["resources"].get(skill_id, [])]


@app.post("/parse-resume", response_model=ParsedResumeOut)
async def parse_resume(file: UploadFile = File(...)) -> ParsedResumeOut:
    """PDF in, text out. Deliberately does NOT analyse.

    The text goes back to the browser for the user to read and correct
    first. PDF extraction fails in ways nothing can reliably detect -- see
    analyzer/resume.py -- and analysing a bad parse straight away would
    produce a confident, wrong answer.
    """
    data = await file.read(MAX_BYTES + 1)
    try:
        parsed = parse_pdf(data, file.filename or "resume.pdf")
    except ResumeParseError as exc:
        raise HTTPException(400, str(exc)) from exc
    return ParsedResumeOut(**vars(parsed))


@app.post("/analyze", response_model=AnalyzeOut)
def analyze_resume(payload: AnalyzeIn) -> AnalyzeOut:
    if payload.role_id not in STATE["profiles"]:
        raise HTTPException(
            404,
            f"unknown role {payload.role_id!r}. "
            f"Available: {sorted(STATE['profiles'])}",
        )
    report = analyze(payload.resume_text, payload.role_id,
                     STATE["taxonomy"], top_n=payload.top_n)
    return AnalyzeOut.model_validate(report, from_attributes=True)
