"""Stage 3 -- the go/no-go gate.

    python -m eval.score                    # uses eval/labels.json
    python -m eval.score --labels path.json

Compares the extractor against hand labels and reports precision and recall.
The numbers go straight into the README -- almost no student project has one,
and having it is ten minutes of interview material.

GATE: recall >= 0.70 on the labelled set. Below that, go back to Stage 2.
Everything downstream inherits these errors, so a polished frontend built on
bad extraction only hides the problem.

Micro-averaged, not macro: every skill mention counts once, so a posting
asking for twelve skills carries more weight than one asking for two. That
matches how the demand profile is actually built in Stage 4. Both are
reported, because they answer different questions and the gap between them
is itself informative.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from sqlalchemy import select

from analyzer.db import get_engine, posting_skills
from analyzer.taxonomy import Taxonomy

HERE = Path(__file__).resolve().parent
GATE_RECALL = 0.70


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if precision + recall else 0.0)
    return precision, recall, f1


def load_predictions(ids: list[int]) -> dict[int, set[str]]:
    """What our extractor found, from the database."""
    out: dict[int, set[str]] = {i: set() for i in ids}
    with get_engine().connect() as conn:
        for pid, sid in conn.execute(
            select(posting_skills.c.posting_id, posting_skills.c.skill_id)
            .where(posting_skills.c.posting_id.in_(ids))
        ):
            out[pid].add(sid)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", type=Path, default=HERE / "labels.json")
    args = ap.parse_args()

    if not args.labels.exists():
        raise SystemExit(
            f"no labels at {args.labels}\n"
            "Run: python scripts/make_label_set.py, open eval/label.html,\n"
            "label the 40 postings, click 'Save file', and put labels.json in eval/."
        )

    tax = Taxonomy.load()
    data = json.loads(args.labels.read_text(encoding="utf-8"))
    cases = [c for c in data["cases"] if c["skills"]]

    if not cases:
        raise SystemExit("labels.json has no labelled cases yet.")

    predicted = load_predictions([c["id"] for c in cases])

    TP = FP = FN = 0
    per_role: dict[str, list[int]] = {}
    missed, spurious = Counter(), Counter()
    macro_p, macro_r = [], []

    for case in cases:
        truth = set(case["skills"])
        pred = predicted.get(case["id"], set())
        tp, fp, fn = len(truth & pred), len(pred - truth), len(truth - pred)
        TP, FP, FN = TP + tp, FP + fp, FN + fn

        role = per_role.setdefault(case["role"], [0, 0, 0])
        role[0] += tp
        role[1] += fp
        role[2] += fn

        p, r, _ = prf(tp, fp, fn)
        macro_p.append(p)
        macro_r.append(r)
        missed.update(truth - pred)
        spurious.update(pred - truth)

    precision, recall, f1 = prf(TP, FP, FN)

    print(f"labelled postings   {len(cases)} of {data.get('total', '?')}")
    print(f"true skill mentions {TP + FN}\n")
    print(f"{'':<12}{'precision':>11}{'recall':>9}{'F1':>8}")
    print("-" * 40)
    print(f"{'micro':<12}{precision:>11.3f}{recall:>9.3f}{f1:>8.3f}")
    print(f"{'macro':<12}{sum(macro_p) / len(macro_p):>11.3f}"
          f"{sum(macro_r) / len(macro_r):>9.3f}")

    print(f"\n{'role':<16}{'precision':>11}{'recall':>9}{'n':>6}")
    print("-" * 42)
    for role, (tp, fp, fn) in sorted(per_role.items()):
        p, r, _ = prf(tp, fp, fn)
        print(f"{role:<16}{p:>11.3f}{r:>9.3f}{tp + fn:>6}")

    # The useful part: read these one by one, they say what to fix.
    if missed:
        print("\nMOST MISSED  (extractor failed to find; hurts recall)")
        for sid, n in missed.most_common(12):
            print(f"  {tax.name_of(sid):<32} {n:>3}")
    if spurious:
        print("\nMOST SPURIOUS  (extractor invented; hurts precision)")
        for sid, n in spurious.most_common(12):
            print(f"  {tax.name_of(sid):<32} {n:>3}")

    print()
    if recall >= GATE_RECALL:
        print(f"GATE PASSED  recall {recall:.3f} >= {GATE_RECALL}")
        return 0
    print(f"GATE FAILED  recall {recall:.3f} < {GATE_RECALL}")
    print("Fix extraction in Stage 2 before building anything on top of it.")
    print("Start with the MOST MISSED list -- usually missing aliases.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
