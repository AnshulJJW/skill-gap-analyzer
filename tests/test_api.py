"""Stage 5 -- API contract tests.

The API is a thin wrapper, so these check the wiring and the error paths
rather than the analysis itself, which is covered by test_gap.py.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app

RESUME = (
    "TECHNICAL SKILLS\n"
    "Programming Languages: Python, Java, SQL\n"
    "Databases: MySQL\n"
    "Tools: Git\n"
    "PROJECTS\n"
    "Built a thing with Django and MySQL.\n"
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_reports_what_was_loaded(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["roles_loaded"] >= 1
    assert body["skills_loaded"] > 100


def test_roles_are_listed_largest_first(client):
    roles = client.get("/roles").json()
    assert roles
    counts = [r["total_postings"] for r in roles]
    assert counts == sorted(counts, reverse=True)
    assert all(r["market"] for r in roles)


def test_analyze_returns_a_usable_report(client):
    r = client.post("/analyze", json={
        "resume_text": RESUME, "role_id": "sde1-backend", "top_n": 5})
    assert r.status_code == 200
    body = r.json()
    assert 0.0 <= body["coverage"] <= 1.0
    assert body["core_total"] == 30
    assert "python" in body["have"]
    assert len(body["gaps"]) <= 5
    assert body["roadmap"], "a report with gaps must carry a roadmap"


def test_roadmap_steps_carry_their_reason(client):
    body = client.post("/analyze", json={
        "resume_text": RESUME, "role_id": "sde1-backend"}).json()
    for step in body["roadmap"]:
        assert step["reason"], f"step {step['skill_id']} has no reason"
        assert step["order"] >= 1


def test_recommendations_never_repeat_what_the_cv_has(client):
    body = client.post("/analyze", json={
        "resume_text": RESUME, "role_id": "sde1-backend"}).json()
    assert not ({g["skill_id"] for g in body["gaps"]} & set(body["have"]))


def test_unknown_role_is_a_404_naming_the_valid_ones(client):
    r = client.post("/analyze", json={
        "resume_text": RESUME, "role_id": "astronaut"})
    assert r.status_code == 404
    assert "sde1-backend" in r.json()["detail"]


def test_short_resume_is_rejected_by_validation(client):
    r = client.post("/analyze", json={
        "resume_text": "hi", "role_id": "sde1-backend"})
    assert r.status_code == 422


def test_resources_endpoint(client):
    assert client.get("/resources/docker").json()
    assert client.get("/resources/not-a-skill").status_code == 404


def test_no_heavy_ml_import_reaches_the_api():
    """The Stage 5 memory budget depends on this. torch or a transformer
    landing in the import graph would blow a 512MB free tier."""
    import sys
    forbidden = {"torch", "sentence_transformers", "transformers", "spacy"}
    assert not (forbidden & set(sys.modules)), (
        f"heavy import leaked in: {forbidden & set(sys.modules)}")


JD = (
    "We are hiring a Backend Engineer. You will build and maintain REST APIs "
    "using Java and Spring Boot. Requirements: strong knowledge of Java, SQL "
    "and MySQL. Experience with Docker, Kubernetes and AWS is required. "
    "Familiarity with Redis caching and Kafka. Good communication and Git."
)


def test_analyze_jd_returns_a_usable_report(client):
    r = client.post("/analyze-jd", json={
        "resume_text": RESUME,
        "job_description": JD,
        "role_id": "sde1-backend",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert 0.0 <= body["coverage"] <= 1.0
    assert body["matched"] and body["missing"]
    assert body["role_name"] and body["market_postings"] > 0
    assert all(s["market_note"] for s in body["missing"])


def test_analyze_jd_works_without_a_role(client):
    """Market context is optional; the comparison must still run."""
    r = client.post("/analyze-jd", json={
        "resume_text": RESUME, "job_description": JD,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role_name"] is None
    assert body["market_postings"] == 0


def test_analyze_jd_rejects_an_unknown_role(client):
    r = client.post("/analyze-jd", json={
        "resume_text": RESUME, "job_description": JD, "role_id": "no-such-role",
    })
    assert r.status_code == 404


def test_analyze_jd_rejects_a_job_description_too_short_to_read(client):
    r = client.post("/analyze-jd", json={
        "resume_text": RESUME, "job_description": "Java dev needed.",
    })
    assert r.status_code == 422
