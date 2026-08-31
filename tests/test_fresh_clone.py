"""Everything a fresh clone needs to RUN must be tracked in git.

The failure this guards against: `data/profiles/` was gitignored while being
exactly what the API loads at startup. A clone got a project where /roles
returned an empty list and /analyze 404'd on every role -- a portfolio repo
that does not work for whoever opens it.

The distinction is between artefacts that can be REBUILT (the 16MB SQLite
database, the 682MB of raw Kaggle CSVs) and artefacts that must be SHIPPED
(52KB of precomputed role profiles). Rebuildable things stay out; the small
precomputed output that makes the repo runnable goes in.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def tracked(path: str) -> list[str]:
    out = subprocess.run(["git", "ls-files", path], cwd=ROOT,
                         capture_output=True, text=True, check=False).stdout
    return [line for line in out.splitlines() if line.strip()]


REQUIRED_AT_RUNTIME = [
    "data/skills.json",
    "data/stoplist.json",
    "data/roles.json",
    "data/prereqs.json",
    "data/resources.json",
    "data/implies.json",
    "data/sources.json",
]


@pytest.mark.parametrize("path", REQUIRED_AT_RUNTIME)
def test_runtime_data_files_are_tracked(path):
    assert tracked(path), f"{path} is needed at runtime but is not in git"


def test_role_profiles_are_tracked():
    """The API loads these at startup. Without them a clone serves nothing."""
    files = tracked("data/profiles")
    assert files, (
        "data/profiles/ is not tracked. The API reads it at startup, so a "
        "fresh clone would return an empty /roles and 404 every /analyze."
    )
    assert any(f.endswith(".json") for f in files)


def test_tracked_profiles_are_valid_and_populated():
    for rel in tracked("data/profiles"):
        raw = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        assert raw["total_postings"] >= 250, f"{rel} below the Stage 1 gate"
        assert raw["demands"], f"{rel} has no demand data"


def test_large_rebuildable_artefacts_stay_out_of_git():
    """The other half of the rule: anything big and rebuildable is excluded."""
    for path in ["data/raw", "data/skillgap.db"]:
        assert not tracked(path), (
            f"{path} is tracked. It is large and rebuildable, so it belongs "
            "outside git -- see data/README.md."
        )


def test_personal_resume_is_never_committed():
    for rel in tracked("resumes"):
        assert not rel.endswith("me.txt"), "a personal resume must stay local"


def test_readme_route_count_matches_the_api():
    """The count drifted the moment a route was added -- pin it.

    Lives here rather than with the other README checks because it needs no
    corpus, and a stale route count is exactly what a fresh clone shows off.
    """
    import re

    from api.main import app

    paths = [r.path for r in app.routes if getattr(r, "include_in_schema", False)]
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    m = re.search(r"FastAPI, (\d+) routes", text)
    assert m, "README no longer states a route count"
    assert int(m.group(1)) == len(paths), (
        f"README says {m.group(1)} routes, API has {len(paths)}: {paths}"
    )


def test_readme_install_steps_only_use_declared_dependencies():
    """The README told people to run `spacy download`; spacy is not installed.

    Anyone following the instructions hit a failure on step four.
    """
    reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    declared = {ln.split("[")[0].split(">")[0].split("=")[0].strip().lower()
                for ln in reqs.splitlines()
                if ln.strip() and not ln.strip().startswith("#")}
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for line in readme.splitlines():
        s = line.strip()
        if s.startswith("#") or not s.startswith("python -m "):
            continue
        module = s.split()[2]
        # First-party modules ship in the repo; stdlib ones always resolve.
        if (ROOT / module.split(".")[0]).is_dir():
            continue
        assert module in declared or module in {"venv", "http.server"}, (
            f"README install step runs {module!r}, which is not in "
            f"requirements.txt: {s!r}"
        )
