# data/

| file | stage | committed? |
|---|---|---|
| `roles.json` | 1 | yes |
| `skills.json` | 1 | yes — the taxonomy, backbone of everything |
| `prereqs.json` | 4 | yes — hand-curated skill DAG |
| `resources.json` | 4 | yes — hand-curated free resources |
| `postings.csv` | 1 | **gitignored while large** — the frozen dataset snapshot |
| `profiles/` | 4 | **committed** — 52KB, and the API loads it at startup |

`postings.csv` is a **frozen snapshot**, not a live scrape. No scraper in the
request path: a demo that depends on a scraper is a demo that breaks during an
interview. If you write a scraper, run it once, commit the output, and describe
it as a data-collection step.

If the snapshot is small enough (< 50MB), drop it from `.gitignore` and commit
it — a repo that clones and runs is worth more than a tidy one.


## What a fresh clone can and cannot do

**Can, immediately:** run the API and the CLI. `data/profiles/` is committed
(52KB) and is all the analysis needs at request time.

**Cannot, without fetching data:** rebuild the profiles from scratch. That
needs the raw Kaggle CSVs in `data/raw/` — 682MB, deliberately excluded.

```
kaggle datasets download -d muhammetakkurt/naukri-jobs-dataset -p data/raw --unzip
python scripts/load_db.py
python scripts/extract_skills.py
python scripts/build_profiles.py
```

The rule: **rebuildable and large stays out; small and precomputed goes in.**
`data/profiles/` was gitignored at first, which meant a clone returned an
empty `/roles` and 404'd every `/analyze` — a portfolio repo that did not
work for whoever opened it. `tests/test_fresh_clone.py` now enforces both
halves of the rule.
