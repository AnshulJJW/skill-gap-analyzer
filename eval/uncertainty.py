"""How much should we trust the Stage 3 numbers?

    python -m eval.uncertainty

The headline micro-average is dominated by whichever role has the most
labelled mentions. With a 20/12/8 posting split that is backend, at 51% of
all mentions -- so "P 0.852" is largely a backend figure wearing a general
label.

Two things are computed here:

1. **Bootstrap confidence intervals per role.** Resamples postings (not
   individual mentions) with replacement, because mentions within one
   posting are correlated -- a posting either gets extracted well or badly,
   and treating its twelve mentions as twelve independent trials would make
   the intervals look far tighter than they are.

2. **A corpus-weighted estimate.** The sample deliberately over-represents
   the smaller roles: the corpus is 73/22/6 backend/frontend/analyst, the
   sample is 50/30/20. Good for measuring each role, but it means the micro
   average does not describe the corpus either. Re-weighting per-role rates
   by true corpus share gives the figure that actually applies to the 7,593
   postings the tool runs on.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

from sqlalchemy import func, select

from analyzer.db import get_engine, postings
from eval.score import load_predictions, prf

HERE = Path(__file__).resolve().parent
BOOTSTRAP = 5000
SEED = 42


def role_corpus_shares() -> dict[str, float]:
    with get_engine().connect() as conn:
        rows = dict(conn.execute(
            select(postings.c.role_id, func.count()).group_by(postings.c.role_id)
        ).all())
    total = sum(rows.values())
    return {r: n / total for r, n in rows.items()}, rows


def counts_for(cases, predicted) -> tuple[int, int, int]:
    tp = fp = fn = 0
    for case in cases:
        truth = set(case["skills"])
        pred = predicted.get(case["id"], set())
        tp += len(truth & pred)
        fp += len(pred - truth)
        fn += len(truth - pred)
    return tp, fp, fn


def bootstrap(cases, predicted, n=BOOTSTRAP) -> dict[str, tuple[float, float]]:
    """Resample POSTINGS with replacement, not mentions.

    Mentions inside one posting are correlated: the extractor either handles
    that posting well or badly. Resampling mentions independently would
    understate the true spread considerably.
    """
    rng = random.Random(SEED)
    ps, rs = [], []
    for _ in range(n):
        draw = [rng.choice(cases) for _ in cases]
        tp, fp, fn = counts_for(draw, predicted)
        p, r, _ = prf(tp, fp, fn)
        ps.append(p)
        rs.append(r)
    ps.sort()
    rs.sort()
    lo, hi = int(0.025 * n), int(0.975 * n) - 1
    return {"precision": (ps[lo], ps[hi]), "recall": (rs[lo], rs[hi])}


def main() -> None:
    data = json.loads((HERE / "labels.json").read_text(encoding="utf-8"))
    cases = data["cases"]
    predicted = load_predictions([c["id"] for c in cases])

    by_role = defaultdict(list)
    for case in cases:
        by_role[case["role"]].append(case)

    shares, corpus_counts = role_corpus_shares()

    print(f"bootstrap: {BOOTSTRAP:,} resamples of postings, seed {SEED}\n")
    print(f"{'role':<15}{'postings':>9}{'mentions':>10}"
          f"{'precision (95% CI)':>26}{'recall (95% CI)':>26}")
    print("-" * 86)

    per_role = {}
    for role in sorted(by_role, key=lambda r: -len(by_role[r])):
        rc = by_role[role]
        tp, fp, fn = counts_for(rc, predicted)
        p, r, _ = prf(tp, fp, fn)
        ci = bootstrap(rc, predicted)
        per_role[role] = (p, r)
        print(f"{role:<15}{len(rc):>9}{tp + fn:>10}"
              f"{p:>13.3f} [{ci['precision'][0]:.2f}-{ci['precision'][1]:.2f}]"
              f"{r:>13.3f} [{ci['recall'][0]:.2f}-{ci['recall'][1]:.2f}]")

    tp, fp, fn = counts_for(cases, predicted)
    p, r, _ = prf(tp, fp, fn)
    ci = bootstrap(cases, predicted)
    print("-" * 86)
    print(f"{'ALL (micro)':<15}{len(cases):>9}{tp + fn:>10}"
          f"{p:>13.3f} [{ci['precision'][0]:.2f}-{ci['precision'][1]:.2f}]"
          f"{r:>13.3f} [{ci['recall'][0]:.2f}-{ci['recall'][1]:.2f}]")

    print("\n\nSAMPLE vs CORPUS COMPOSITION")
    print(f"{'role':<15}{'corpus':>10}{'corpus %':>10}"
          f"{'sample':>9}{'sample %':>10}{'mentions %':>12}")
    print("-" * 66)
    total_mentions = tp + fn
    for role in sorted(by_role, key=lambda r: -corpus_counts.get(r, 0)):
        rc = by_role[role]
        rtp, _, rfn = counts_for(rc, predicted)
        print(f"{role:<15}{corpus_counts.get(role, 0):>10,}"
              f"{shares.get(role, 0):>9.1%}"
              f"{len(rc):>9}{len(rc) / len(cases):>10.1%}"
              f"{(rtp + rfn) / total_mentions:>12.1%}")

    wp = sum(shares.get(role, 0) * pr[0] for role, pr in per_role.items())
    wr = sum(shares.get(role, 0) * pr[1] for role, pr in per_role.items())
    print("\n\nESTIMATE FOR THE ACTUAL CORPUS")
    print("Per-role rates re-weighted by true corpus share, rather than by")
    print("how many postings happened to be sampled.\n")
    print(f"  micro (sample-weighted)   precision {p:.3f}   recall {r:.3f}")
    print(f"  corpus-weighted           precision {wp:.3f}   recall {wr:.3f}")
    print(f"\n  difference                {wp - p:+.3f}          {wr - r:+.3f}")


if __name__ == "__main__":
    main()
