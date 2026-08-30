"""The README's headline numbers must match what the code produces.

Stage 4 rebuilt the corpus and shrank the evaluation set from 40 postings to
34, but the README kept quoting the old figures while telling the reader to
reproduce them with `python -m eval.score`. Anyone cloning the repo and
running that command would have got different numbers from the ones claimed
-- which reads as fabrication even when it is an oversight.

Documentation that states a measurement is making a claim, and a claim that
nothing checks will eventually drift. These tests fail when it does.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from sqlalchemy import inspect

from analyzer.db import get_engine
from eval.score import load_predictions, prf

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def _corpus_available() -> bool:
    """These checks recompute the score, which needs the postings database.

    It is 16MB and rebuildable, so it is deliberately not in git -- see
    data/README.md. On a fresh clone these tests SKIP with a reason rather
    than erroring, because a test that cannot run has not failed.
    """
    try:
        return "posting_skills" in inspect(get_engine()).get_table_names()
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _corpus_available(),
    reason=(
        "needs the postings database (16MB, not in git). Rebuild with: "
        "kaggle datasets download -d muhammetakkurt/naukri-jobs-dataset "
        "-p data/raw --unzip && python scripts/load_db.py && "
        "python scripts/extract_skills.py"
    ),
)


def _current_scores():
    labels = json.loads((ROOT / "eval" / "labels.json").read_text(encoding="utf-8"))
    cases = labels["cases"]
    predicted = load_predictions([c["id"] for c in cases])
    tp = fp = fn = 0
    for case in cases:
        truth = set(case["skills"])
        pred = predicted.get(case["id"], set())
        tp += len(truth & pred)
        fp += len(pred - truth)
        fn += len(truth - pred)
    p, r, f1 = prf(tp, fp, fn)
    return {"postings": len(cases), "mentions": tp + fn,
            "precision": p, "recall": r, "f1": f1}


def _readme_current_block() -> str:
    """The 'Current -- reproducible from this tree' table only."""
    start = README.index("### Current")
    end = README.index("### The history")
    return README[start:end]


@pytest.fixture(scope="module")
def actual():
    return _current_scores()


def test_readme_quotes_the_right_posting_count(actual):
    block = _readme_current_block()
    m = re.search(r"labelled postings scored \|\s*(\d+)", block)
    assert m, "README no longer states a posting count"
    assert int(m.group(1)) == actual["postings"]


def test_readme_quotes_the_right_mention_count(actual):
    block = _readme_current_block()
    m = re.search(r"true skill mentions \|\s*([\d,]+)", block)
    assert m, "README no longer states a mention count"
    assert int(m.group(1).replace(",", "")) == actual["mentions"]


@pytest.mark.parametrize("label,key", [
    ("precision", "precision"), ("recall", "recall"), ("F1", "f1"),
])
def test_readme_headline_metrics_match_the_code(actual, label, key):
    block = _readme_current_block()
    m = re.search(rf"\*\*{label}\*\*[^|]*\|\s*\*\*([\d.]+)\*\*", block)
    assert m, f"README no longer states {label}"
    claimed = float(m.group(1))
    assert claimed == pytest.approx(actual[key], abs=0.001), (
        f"README claims {label} {claimed}, code produces "
        f"{actual[key]:.3f}. Re-run `python -m eval.score` and update the "
        "Current table -- or explain why they differ."
    )


def test_historical_figures_are_marked_unreproducible():
    """The pre-filter numbers are real history but cannot be re-derived from
    this tree. They must never be presented as reproducible claims."""
    assert "cannot be\nreproduced from this tree" in README or \
           "cannot be reproduced from this tree" in README, \
        "the history table must state that those figures do not reproduce"


def test_filtered_out_labels_are_kept_as_evidence():
    path = ROOT / "eval" / "labels_filtered_out.json"
    assert path.exists(), "removed labels must be retained, not deleted"
    dropped = json.loads(path.read_text(encoding="utf-8"))["cases"]
    total = _current_scores()["postings"] + len(dropped)
    assert total == 40, f"labels should still account for all 40, found {total}"
