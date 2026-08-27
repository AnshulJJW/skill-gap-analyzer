"""Stage 3 -- the go/no-go gate.

Hand-label 40 postings in labeled.json, then run this. The numbers go
straight into the README's Results section -- almost no student project has
one, and it is ten minutes of interview material.

GATE: recall >= 0.70 on hard technical skills. Below that, go back to
Stage 2. Every downstream number inherits these errors, so a polished
frontend on bad extraction only hides the problem.

Keep labeled.json in the repo forever -- it is your regression test.
"""

from __future__ import annotations

import json
from pathlib import Path

from analyzer.extract import extract
from analyzer.taxonomy import Taxonomy

LABELED = Path(__file__).resolve().parent / "labeled.json"


def score(predicted: set[str], truth: set[str]) -> tuple[float, float]:
    if not predicted:
        return 0.0, 0.0
    tp = len(predicted & truth)
    precision = tp / len(predicted)
    recall = tp / len(truth) if truth else 0.0
    return precision, recall


def main() -> None:
    taxonomy = Taxonomy.load()
    cases = json.loads(LABELED.read_text(encoding="utf-8"))["cases"]
    if not cases:
        raise SystemExit("labeled.json is empty -- label 40 postings first (Stage 3).")

    precisions, recalls = [], []
    for case in cases:
        predicted = {m.skill_id for m in extract(case["text"], taxonomy)}
        truth = set(case["skills"])
        p, r = score(predicted, truth)
        precisions.append(p)
        recalls.append(r)

        # the useful part: read these one by one, they tell you what to fix
        if missed := truth - predicted:
            print(f"[{case['id']}] MISSED: {sorted(missed)}")
        if spurious := predicted - truth:
            print(f"[{case['id']}] FALSE:  {sorted(spurious)}")

    mp = sum(precisions) / len(precisions)
    mr = sum(recalls) / len(recalls)
    print(f"\nn={len(cases)}  precision={mp:.3f}  recall={mr:.3f}")
    print("GATE PASSED" if mr >= 0.70 else "GATE FAILED -- return to Stage 2")


if __name__ == "__main__":
    main()
