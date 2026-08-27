# Stage 1 — data audit

Measured, not assumed. Every number below came from the raw CSVs; the code
that produced them is in the commit history for this file.

## The two candidates

| | LinkedIn (arshkon) | Naukri (muhammetakkurt) |
|---|---|---|
| postings | 123,849 | 96,659 unique |
| median description | **3,435 chars** | **330 chars** |
| has "required"-type marker | 91.1% | 34.8% |
| has "preferred"-type marker | 63.0% | 27.9% |
| **has both** | **59.9%** | **14.9%** |
| pre-extracted skills | `job_skills.csv` + id mapping | `tagsAndSkills` (comma-separated) |
| experience field | `formatted_experience_level` (bucketed) | `experience` ("0-5 Yrs") |
| market | largely US | India |

## The finding that changed the plan

We chose LinkedIn expecting richer text, and its text *is* ~10x richer.
But it is a **general** job board dump, not a tech one. Counting postings
per target role:

| role | LinkedIn (all) | LinkedIn (entry) | Naukri (all) | Naukri (entry) |
|---|---|---|---|---|
| SDE-1 Backend | 57 | **4** | 1,166 | **259** |
| Data Analyst | 413 | 158 | 766 | 251 |
| Frontend Engineer | 114 | **10** | 1,109 | 229 |

Only 20,114 of LinkedIn's 123,849 postings are tech-ish at all, and that
figure is inflated by electrical, mechanical, manufacturing and financial
roles. The most common genuinely-software title appears 181 times across
*all* experience levels.

**LinkedIn cannot clear the 250-posting gate for these roles. Naukri can.**

The queries were widened before concluding this — the first pass used
narrow patterns that missed a plain "software engineer", and re-running with
broader matching did not change the verdict.

## Consequence for the design

The required-vs-preferred split was meant to be what made Stage 4 feel
intelligent. On Naukri it exists in only 14.9% of postings, so it cannot
carry that weight.

The substitute is better suited to the data anyway: Naukri ships
`tagsAndSkills`, an explicit per-posting skill list. So

    tagsAndSkills mention   -> high weight  (the employer named it)
    description-only match  -> lower weight (contextual)

replaces required/preferred as the confidence axis. Same idea — some
mentions are stronger evidence of demand than others — expressed in the
signal this dataset actually has.

## Decision

- **Naukri is the primary source.** It has the roles, and it is the Indian
  market, which is the market the user is actually hiring into.
- The entry-level filter is `experience` starting at 0 or 1 year, which is a
  sharper instrument than LinkedIn's bucketed level field.
- LinkedIn is retained only for a possible global-vs-India comparison on
  Data Analyst, the one role where it has enough volume (413). It does not
  feed any headline number.

## Limitations this creates

- Short descriptions mean less context per skill mention, so the "evidence"
  string shown in the UI will often be a fragment rather than a sentence.
- `tagsAndSkills` is Naukri's own extraction, with its own biases. Storing it
  separately from our extraction keeps the comparison honest and gives
  Stage 3 a free baseline.
- Single-market data. The tool should say so on screen rather than implying
  its percentages are universal.
