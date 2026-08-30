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
