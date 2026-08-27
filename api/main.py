"""Stage 5 -- a thin wrapper. Three routes, no business logic.

If this file grows past ~120 lines, logic is leaking out of analyzer/ and
into your routes. Push it back.

Free-tier reality check (Render, 512MB, cold starts after inactivity):
  - role profiles are READ from disk/db, never recomputed per request
  - only the resume is processed live
  - if dictionary matching alone handles the resume path, do not load the
    transformer at runtime at all -- see LOAD_EMBEDDINGS_AT_RUNTIME
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import AnalyzeIn, AnalyzeOut, ResourceOut, RoleOut

STATE: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO Stage 5: load taxonomy + role profiles ONCE here, not per request.
    #               Measure cold start after adding anything to this block.
    yield
    STATE.clear()


app = FastAPI(title="Skill-Gap Analyzer", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # TODO Stage 7: add the Vercel origin
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/roles", response_model=list[RoleOut])
def list_roles():
    raise HTTPException(501, "Stage 5")


@app.post("/analyze", response_model=AnalyzeOut)
def analyze(payload: AnalyzeIn):
    raise HTTPException(501, "Stage 5")


@app.get("/resources/{skill_id}", response_model=list[ResourceOut])
def resources(skill_id: str):
    raise HTTPException(501, "Stage 5")
