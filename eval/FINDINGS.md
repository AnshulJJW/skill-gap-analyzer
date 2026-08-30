# Gaps found while labelling — do NOT fix before scoring

Every entry here was noticed while hand-labelling the 40 evaluation
postings. None of them get fixed until the score is recorded.

**Why hold off.** Adding Kotlin to the taxonomy *because* an evaluation
posting mentions it, and then scoring against that same posting, tunes the
system on its own test. The resulting number would be better than the
extractor really is, and every downstream claim would inherit that
flattery. It is the most common way people accidentally lie with a metric.

**The sequence instead:**

1. Finish labelling all 40
2. Run `python -m eval.score` and record the number, whatever it is
3. Fix everything below
4. Re-score, and report **both** figures — the honest one and the improved
   one — saying plainly that the second was tuned on this set
5. If the difference matters, draw a fresh sample and measure clean

---

## Missing from the taxonomy

| term | seen in | note |
|---|---|---|
| Kotlin | posting 4 (Android Support) | named outright; no checkbox exists |
| GIS / ESRI / ERDAS / remote sensing | posting 3 | whole adjacent profession; out of scope, not a gap to fill |

## Normalisation gaps

| written as | taxonomy has | effect |
|---|---|---|
| `unit tests` | `unit testing` | plural form does not match — a stemming gap, likely costing recall wherever plurals appear |

## Role-matching problems

| posting | filed as | actually |
|---|---|---|
| 3 — Junior Software Developer | sde1-backend | GIS specialist. Title contains "software developer", so the pattern matched a different profession entirely. |

Worth quantifying once labelling is done: how many of the 40 are not really
the role they were filed under. That figure belongs in the README, not
hidden — "my title matching pulls in adjacent roles about X% of the time"
is a stronger statement than an unexamined claim of accuracy.

## Data-quality observations

- Posting 4 is filed under the 0–2 year filter with `2-3 Yrs`, because the
  range *starts* at 2. Defensible, but it means the entry-level pool is
  looser than "graduate roles only".
- Boilerplate postings (posting 1) name no technology at all. They still
  count toward the demand denominator while contributing no signal.
