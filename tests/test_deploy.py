"""Deployment invariants.

The API is deployed from requirements-api.txt, not requirements.txt. That
split is easy to break by adding an import to analyzer/ without noticing it
pulls a package the server does not install -- which would fail at startup on
the instance, not here.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_REQS = ROOT / "requirements-api.txt"

STDLIB_OK = {
    "__future__", "os", "io", "re", "json", "enum", "argparse", "pathlib",
    "dataclasses", "contextlib", "typing", "collections", "itertools",
    "functools", "math", "datetime", "hashlib", "textwrap", "sys", "time",
}

# Distribution name -> the module it provides, where they differ.
PROVIDES = {
    "uvicorn": {"uvicorn"},
    "python-multipart": {"multipart"},   # imported by fastapi, not by us
    "fastapi": {"fastapi", "starlette"},
    "pydantic": {"pydantic"},
    "rapidfuzz": {"rapidfuzz"},
    "pypdf": {"pypdf"},
}


def _declared() -> set[str]:
    names = set()
    for line in API_REQS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        dist = line.split(">=")[0].split("==")[0].split("[")[0].strip().lower()
        names |= PROVIDES.get(dist, {dist})
    return names


def _imports_reachable_from(entry: str) -> set[str]:
    """Every third-party top-level module the API can reach by import."""
    seen: set[str] = set()
    found: set[str] = set()
    stack = [entry]
    while stack:
        rel = stack.pop()
        if rel in seen:
            continue
        seen.add(rel)
        path = ROOT / rel
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                mods = [node.module]
            for mod in mods:
                top = mod.split(".")[0]
                if top in ("analyzer", "api", "eval", "scripts"):
                    stack.append(mod.replace(".", "/") + ".py")
                else:
                    found.add(top)
    return found


def test_the_api_only_imports_what_the_server_installs():
    """A new import in analyzer/ that is not in requirements-api.txt would
    crash the deployed instance at startup while every local test passed."""
    used = _imports_reachable_from("api/main.py") - STDLIB_OK
    missing = sorted(used - _declared())
    assert not missing, (
        f"api/main.py reaches {missing}, which requirements-api.txt does not "
        "install. Add them there, or keep them out of the request path."
    )


def test_the_heavy_pipeline_packages_stay_out_of_the_runtime_install():
    """pandas, SQLAlchemy and psycopg are the bulk of the full install and
    the server imports none of them: profiles are precomputed to JSON, so
    nothing touches a database at request time."""
    declared = _declared()
    for heavy in ("pandas", "sqlalchemy", "psycopg", "numpy", "torch"):
        assert heavy not in declared, f"{heavy} is not needed to serve requests"


def test_every_file_the_api_reads_at_startup_is_committed():
    """The instance builds from a git clone. A data file that is gitignored
    works locally and 404s every request in production -- which has happened
    on this project before, with data/profiles/."""
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", "data"], cwd=ROOT, capture_output=True, text=True,
        check=True,
    ).stdout.split()
    for needed in ("data/skills.json", "data/stoplist.json", "data/implies.json",
                   "data/prereqs.json", "data/resources.json"):
        assert needed in tracked, f"{needed} is not committed"

    profiles = [t for t in tracked if t.startswith("data/profiles/")]
    assert profiles, "no role profiles are committed; /roles would return []"
    for path in profiles:
        raw = json.loads((ROOT / path).read_text(encoding="utf-8"))
        assert raw["demands"], f"{path} carries no demand data"


def test_render_blueprint_matches_the_runtime_install():
    """The blueprint must install the slim file, or the free instance builds
    pandas for nothing."""
    blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "requirements-api.txt" in blueprint
    assert "api.main:app" in blueprint
    assert "$PORT" in blueprint, "the instance port is assigned, not fixed"
    assert "healthCheckPath: /health" in blueprint


def test_the_root_vercel_config_builds_the_frontend_not_the_backend():
    """Vercel guesses the framework from the repository root, and this root
    is a Python project -- requirements.txt and a pyproject.toml holding only
    ruff settings. It guessed FastAPI twice and tried to `uv lock` against a
    pyproject.toml with no [project] table.

    Naming the commands explicitly removes the guess. framework:null is the
    part that actually disables detection; the commands alone are not enough.
    """
    cfg = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert cfg["framework"] is None, "detection must be off, or FastAPI wins again"
    assert cfg["outputDirectory"] == "web/dist"
    assert "web" in cfg["buildCommand"] and "web" in cfg["installCommand"]


def test_pyproject_is_lint_config_only():
    """If a [project] table is ever added here, the root becomes a real
    Python package and Vercel's detection would be right to build it --
    at which point vercel.json above is the only thing stopping it."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[project]" not in text, (
        "a [project] table changes what this repository root claims to be; "
        "check vercel.json still points at the frontend"
    )
