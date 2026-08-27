# Skill-Gap Analyzer & Career Path Recommender

Paste your resume, pick a target role, and find out which skills you are
missing — ranked by how many real job postings each one unlocks, ordered so
prerequisites come first, with a free resource attached to each.

It does not score your resume against one job description. It builds a demand
profile from hundreds of postings for a role, compares your skills against
that profile, and answers a different question: **what do I learn next, and
why that?**

Built because I needed it for my own placement prep, and pointed at my own
resume first.

> **Status: Stage 0 — scaffold.** Structure and contracts are in place; the
> pipeline is not implemented yet. Progress tracked against
> [docs/build-plan.html](docs/build-plan.html).

---

## How it works

```
 postings dataset            resume text
   (frozen snapshot)              │
        │                         │
        ▼                         ▼
  ┌───────────────────────────────────────┐
  │  analyzer/  — no web framework here   │
  │                                       │
  │  taxonomy.py   canonical skills       │
  │  extract.py    text → skill ids       │
  │  profiles.py   role demand (offline)  │
  │  gap.py        coverage + ranking     │
  │  roadmap.py    prereq DAG + resources │
  └───────────────────────────────────────┘
        │                         │
        ▼                         ▼
   data/profiles/*.json      GapReport
   (precomputed)                  │
        └──────────┬──────────────┘
                   ▼
            api/  FastAPI, 3 routes
                   ▼
            web/  React + Vite, one page
```

**Extraction is a hybrid, on purpose.** A curated skill taxonomy does most of
the work; spaCy handles tokenizing and section splitting; embeddings
(`all-MiniLM-L6-v2`) resolve only the variants the dictionary misses.
Off-the-shelf NER is *not* used to find skills — it is trained on people,
places and organisations, and will not tag `Kafka` or `gRPC`.

**Ranking is by marginal coverage, not frequency.** Greedy set cover over the
postings you currently fail: which single skill, learned next, unlocks the
most of them? That is why the output says *"learn Kafka next"* rather than
listing the forty most common skills you lack.

**Role profiles are precomputed offline.** The API reads them; it never scans
the postings table at request time.

## Results

<!-- Stage 3 fills this in. Do not ship without it. -->

| metric | value |
|---|---|
| labeled postings | — |
| precision (hard skills) | — |
| recall (hard skills) | — |

Measured against `eval/labeled.json`, 40 hand-labeled postings, via
`python -m eval.score`. The gate for proceeding past Stage 3 is **recall ≥ 0.70**.

## What it said about my own resume

<!-- Stage 8. What it got right, what it got wrong, and why. -->

## Limitations

<!-- Stage 8. Name these yourself, first. -->

---

## Stack

| layer | choice | why |
|---|---|---|
| Backend | FastAPI | serving an ML pipeline; Django's ORM and admin buy nothing here |
| Database | Postgres (Supabase) | the data is deeply relational; `pgvector` is there if needed |
| Frontend | React + Vite | one page, no router, no state library |
| Skills | curated taxonomy + embeddings | dictionary first, embeddings as fallback |
| Job data | frozen snapshot | no scraper in the request path |

## Running it locally

Requires **Python 3.12+** and **Node LTS** (Node not needed until Stage 6).

Verified on Python 3.14.7. Dependencies use lower bounds rather than exact
pins -- older pinned versions have no wheels for recent Python and fall back
to compiling from source, which needs a C++ toolchain you probably do not
have.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
# requirements-ml.txt (PyTorch, ~2.5GB) is Stage 2 only -- skip for now
cp .env.example .env
```

Then, once the stages are built:

```bash
python scripts/load_db.py                                   # stage 1
python -m analyzer.extract --file resumes/me.txt            # stage 2
python -m eval.score                                        # stage 3
python scripts/build_profiles.py                            # stage 4
python -m analyzer.gap --resume resumes/me.txt --role sde1-backend
uvicorn api.main:app --reload                               # stage 5
```

## Layout

```
analyzer/   the ML core — importable and testable with no server running
api/        FastAPI wrapper, three routes, no business logic
web/        Vite + React, one page (stage 6)
data/       taxonomy, prereqs, resources, frozen postings snapshot
eval/       hand-labeled set + precision/recall — the stage 3 gate
scripts/    load_db, build_profiles, seed_prod
docs/       the build plan
resumes/    your own resume, gitignored
```
