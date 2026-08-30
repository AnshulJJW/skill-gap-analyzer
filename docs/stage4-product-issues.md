# Stage 4 — the pipeline works, and running it exposed two product flaws

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

Fix: mark skills as `actionable: true|false` in the taxonomy rather than
inferring it from category, and exclude the non-actionable ones from
recommendations while still counting them toward coverage.

## 2. The coverage number is discouraging rather than informative

A CV with Python, pandas, NumPy, scikit-learn, SQL, MySQL, ML and NLP scores
**24% for Data Analyst** — a role it is genuinely well suited to.

The cause is the denominator: coverage is weighted demand across *all* 83
skills the role mentions, so the long tail of rare skills dominates. Nobody
can score high, which makes the number useless for comparing roles or
tracking progress.

Three candidate fixes, none obviously right:

- coverage over the **top N** demanded skills rather than all of them
- weight by share **squared**, so common skills dominate the denominator
- report **"you have 20 of the 30 most-demanded skills"**, which is a count
  people can actually reason about

Worth deciding deliberately rather than defaulting. The current number is
mathematically defensible and communicatively bad, which is the worst
combination.

## 3. Market accuracy versus useful advice

For SDE-1 Backend the ranking puts **.NET (+1.8%)** and **C++ (+1.8%)**
above Docker or Spring Boot. That is a correct reading of the Indian
entry-level market — there are many .NET and C++ service-company roles.

But it is questionable advice for a Python/Java student. The tool currently
optimises for "unlocks the most postings", which is not the same as "is a
good next step for this person".

Not a bug, and not obviously fixable — but worth stating in the README
rather than pretending the ranking is career guidance.
