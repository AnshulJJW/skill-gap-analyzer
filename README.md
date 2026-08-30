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

Measured against `eval/labels.json` — 40 postings hand-labelled by a human
who did not see the extractor's output, using the rules in
[eval/LABELLING_GUIDE.md](eval/LABELLING_GUIDE.md). Reproduce with
`python -m eval.score`.

| metric | value |
|---|---|
| labelled postings | 40 |
| true skill mentions | 255 |
| **precision** (micro) | **0.852** |
| **recall** (micro) | **0.855** |
| **F1** (micro) | **0.853** |
| precision / recall (macro) | 0.800 / 0.787 |

Per role:

| role | precision | recall | mentions |
|---|---|---|---|
| Frontend Engineer | 0.936 | 0.830 | 88 |
| Data Analyst | 0.833 | 0.833 | 36 |
| SDE-1 Backend | 0.810 | 0.878 | 131 |

**Frontend precision is 12 points above backend, and the reason is
linguistic rather than technical: frontend postings *name* their skills
("React", "jQuery"), backend postings *describe* them ("relational and
non-relational databases", "architect scalable systems"). A taxonomy
matches nouns, not prose.**

### How much to trust these numbers

`python -m eval.uncertainty` bootstraps 5,000 resamples of postings (not of
individual mentions -- mentions inside one posting are correlated, and
resampling them independently would make the intervals look far tighter than
they are).

| role | precision (95% CI) | recall (95% CI) | mentions |
|---|---|---|---|
| sde1-backend | 0.810 [0.75–0.88] | 0.878 [0.82–0.93] | 131 |
| frontend | 0.936 [0.87–1.00] | 0.830 [0.70–0.93] | 88 |
| data-analyst | 0.833 [0.73–0.92] | 0.833 [0.63–0.96] | 36 |
| **all (micro)** | **0.852 [0.80–0.90]** | **0.855 [0.80–0.90]** | 255 |

The overall figure is reliable to about ±0.05. **The per-role figures are
not equally trustworthy**: data-analyst rests on 36 mentions and its recall
interval spans 0.63–0.96, so it should always be quoted with the interval
rather than as a point estimate.

The sample is also not proportional to the corpus — it deliberately
over-samples the smaller roles (sample 50/30/20 against a corpus of
73/22/6) so each role gets measured at all. Re-weighting the per-role rates
by true corpus share gives **precision 0.839, recall 0.865** — about one
point from the micro figures, because the three roles score similarly. Had
they diverged, the weighting would have mattered a great deal.

### Before and after the fixes

Every problem found during labelling was recorded in
[eval/FINDINGS.md](eval/FINDINGS.md) and deliberately **not** fixed until
after the score above was locked in. Patching a taxonomy because an
evaluation posting exposed a gap, then scoring against that posting,
measures nothing.

| | precision | recall | F1 |
|---|---|---|---|
| **pre-fix** — untuned, the honest baseline | 0.852 | 0.855 | 0.853 |
| post-fix, counting newly-added skills as errors | 0.850 | 0.890 | 0.870 |
| post-fix, like-for-like against the labels | **0.904** | **0.890** | **0.897** |

**The post-fix figures are tuned on this set and are therefore optimistic.**
A clean measurement would need a fresh sample.

The middle row needs explaining, because it looks like precision stalled.
Sixteen of its "false positives" are skills added *after* labelling — R,
Kotlin, Cypress, OpenGL, Webflow, Crystal Reports, PySpark, BigQuery,
Redshift, NiFi and others. Every one was identified during labelling as
named in the posting but having no checkbox. The extractor now finds them
correctly and is scored wrong for it, because the ground truth predates
them. The bottom row removes that artefact.

What the targeted fixes did:

| false positive | before | after | | miss | before | after |
|---|---|---|---|---|---|---|
| Problem Solving | 7 | **0** | | JavaScript | 6 | **0** |
| Cloud Fundamentals | 6 | **0** | | Responsive Design | 6 | 3 |
| Computer Networks | 2 | **0** | | | | |

All the false-positive fixes were one curation error repeated: a category
term listed as an alias of a specific product (`analytical` → Problem
Solving, `cloud` → Cloud Fundamentals, `http` → Computer Networks, `erp` →
SAP, `cms` → WordPress). The JavaScript recall fix was the opposite
problem — frameworks assert their language even when the language is never
written.

## What it said about my own resume

<!-- Stage 8. What it got right, what it got wrong, and why. -->

## Limitations

Named here deliberately, and measured where possible.

**About one in six postings is filed under the wrong role.** Found by hand
across 40 postings (17.5%) and independently corroborated by an automated
filter across the whole corpus (16.0%). The filters now remove 6 of the 8
cases found; the two survivors are a senior role rescued by a junior
sub-requirement, and a business analyst with no disqualifying signal at all.

**The ranking optimises for market coverage, not personal fit.** It answers
"which skill unlocks the most postings", which is not the same as "which
skill is the sensible next step for *this* person". For a Python/Java
student it correctly places .NET and C++ in the top six, because the Indian
entry-level market really does want them — but that is arguably poor advice.

**Single market, single snapshot.** Naukri, December 2024. Core skills move
slowly, but anything fast-moving will drift. The pipeline is source-agnostic,
so refreshing is a data task rather than a code change.

**The taxonomy inherited its corpus's bias.** It was built from tags
appearing 20+ times in a corpus that is 73% backend, so data-analysis
coverage was thinner — R, one of the two principal languages of that
profession, was missing entirely until hand-labelling exposed it. A
frequency-thresholded vocabulary is only as broad as what you counted.

**Resource recommendations are hand-curated, not learned.** 55 skills have
free resources attached because someone chose them. That is a deliberate
choice — a good curated map beats a bad recommender — but it is not machine
learning and is not described as such.

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
