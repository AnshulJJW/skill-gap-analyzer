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

Hand-labelled evaluation. 40 postings were labelled by a human who could not
see the extractor's output, following the rules in
[eval/LABELLING_GUIDE.md](eval/LABELLING_GUIDE.md).

### Current — reproducible from this tree

```
python -m eval.score
```

| metric | value |
|---|---|
| labelled postings scored | 34 |
| true skill mentions | 220 |
| **precision** (micro) | **0.857** |
| **recall** (micro) | **0.900** |
| **F1** (micro) | **0.878** |
| precision / recall (macro) | 0.855 / 0.859 |

| role | precision | recall | mentions |
|---|---|---|---|
| Frontend Engineer | 0.952 | 0.898 | 88 |
| SDE-1 Backend | 0.817 | 0.927 | 96 |
| Data Analyst | 0.769 | 0.833 | 36 |

**Why 34 and not 40.** Stage 4 applied role filters that removed 6 of the
labelled postings from the corpus entirely — a GIS role, a firmware role, an
iOS role and three senior roles, all of which had been misfiled as
entry-level backend. Their labels are kept in
`eval/labels_filtered_out.json` as evidence the filters removed the right
things.

**These figures are tuned on this set.** The taxonomy was corrected using
gaps this set exposed, so they are optimistic. A clean measurement needs a
fresh sample.

### The history, and why it is not reproducible

| stage | postings | precision | recall | F1 |
|---|---|---|---|---|
| pre-fix baseline — **the honest untuned number** | 40 | 0.852 | 0.855 | 0.853 |
| after taxonomy and extraction fixes | 40 | 0.850 | 0.890 | 0.870 |
| after fixes, like-for-like | 40 | 0.904 | 0.890 | 0.897 |
| after role filters — **current** | 34 | 0.857 | 0.900 | 0.878 |

The first three rows were measured against a corpus of 7,593 postings that
no longer exists — the Stage 4 filters reduced it to 6,898. **They cannot be
reproduced from this tree, and are recorded as history rather than as
claims.** Only the current row reproduces.

The pre-fix row is the one to trust as an unbiased estimate: every gap found
while labelling was written down and deliberately left unfixed until after
that number was recorded.

### How much to trust the numbers

`python -m eval.uncertainty` bootstraps 5,000 resamples of postings (not of
individual mentions — mentions inside one posting are correlated, and
resampling them independently would make the intervals look far tighter than
they are).

On the 40-posting set the overall figure was reliable to about ±0.05, while
data-analyst recall spanned 0.63–0.96 on 36 mentions. **Per-role figures
should always be quoted with their interval, never as point estimates.**

The sample also over-samples the smaller roles (50/30/20 against a corpus of
73/22/6) so each role gets measured at all. Re-weighting by true corpus share
moved the headline by about one point, because the three roles score
similarly.

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
