# Stage 4 — two product flaws, found by using it, now fixed

Neither is an accuracy problem. Extraction is at recall 0.900. These are
about what the output *says* to a person, and they only became visible by
running the thing on a real resume.

## 1. Category skills are not actionable advice

Top recommendation for Data Analyst: **"learn Data Analysis" (+17.1%)**,
because it appears in 79% of those postings.

That is circular. Nobody can go and learn "data analysis" — they learn SQL,
or pandas, or a BI tool. The same is true of "Business Intelligence" and
"Data Quality".

It is exactly the soft-skills problem in a different costume. Communication
and Teamwork are already excluded from recommendations (kept in coverage,
dropped from the roadmap) because no course teaches them. Vague category
skills need the same treatment: real demand, useless as a next step.

**FIXED.** Skills now carry `actionable: true|false` in the taxonomy. 13 are
marked false -- traits (Communication, Teamwork, Problem Solving) and
category words (Data Analysis, Business Intelligence, System Design,
Database Design, DevOps, Cloud, Monitoring, Code Review, Debugging,
Data Quality). They still count toward coverage, because the demand is
real, but never appear as a recommendation.

Data Analyst now suggests Data Visualisation, Excel, Statistics and Power BI
-- things a person can actually go and learn.

## 2. The coverage number is discouraging rather than informative

A CV with Python, pandas, NumPy, scikit-learn, SQL, MySQL, ML and NLP scores
**24% for Data Analyst** — a role it is genuinely well suited to.

The cause is the denominator: coverage is weighted demand across *all* 83
skills the role mentions, so the long tail of rare skills dominates. Nobody
can score high, which makes the number useless for comparing roles or
tracking progress.

**FIXED.** Coverage is now measured against the **top 30** demanded skills
rather than all of them, and the report also states the plain count
alongside it.

The same CV went from 24% to 40% on backend. 30 is a judgement call, chosen
because it is roughly where per-skill demand falls below 5% of postings, and
it is a named constant (`TOP_N_FOR_COVERAGE`) so it can be argued with rather
than being buried in a formula.

## 3. Market accuracy versus useful advice

For SDE-1 Backend the ranking puts **.NET (+1.8%)** and **C++ (+1.8%)**
above Docker or Spring Boot. That is a correct reading of the Indian
entry-level market — there are many .NET and C++ service-company roles.

But it is questionable advice for a Python/Java student. The tool currently
optimises for "unlocks the most postings", which is not the same as "is a
good next step for this person".

Not a bug, and not obviously fixable — but worth stating in the README
rather than pretending the ranking is career guidance.
