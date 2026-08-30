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
| Cypress | posting 8 (Backend Developer) | named outright; end-to-end testing tool |
| Splunk | posting 6 | logging/observability tool |
| Crystal Reports | posting 13 | the entire subject of the role; BI reporting tool |
| OpenGL | posting 15 | graphics library |
| Apache NiFi | posting 17 | the entire subject of the role |
| Groovy, Jolt, Hashicorp Vault | posting 17 | named in nice-to-haves |
| CakePHP, Smarty | posting 18 | PHP ecosystem |
| Webflow | posting 29 | no-code website builder |
| Business Objects | posting 15 | SAP BI reporting tool |
| Visual Studio | posting 6 | an editor, not a skill — correctly absent |
| GIS / ESRI / ERDAS / remote sensing | posting 3 | whole adjacent profession; out of scope, not a gap to fill |

## The single systematic curation error: category word -> specific product

Four confirmed instances, all mine, all the same shape. A generic category
term is listed as an alias of one specific product, so any posting
mentioning the category acquires a product it never named.

| alias | maps to | should be |
|---|---|---|
| `analytical` | Problem Solving | a trait, not a skill claim |
| `erp` | SAP | ERP is a category; SAP is one vendor |
| `cms` | WordPress | posting 29 names Webflow, not WordPress |
| `cloud` | Cloud Fundamentals | double-counts when AWS/GCP is also named |
| `http` | Computer Networks | sometimes right, often incidental |

This is the dominant source of false positives, and it is one mistake
repeated rather than five separate ones. Worth stating that way: the fix is
a rule ("a category term is not an alias of a product"), not five patches.

## Taxonomy entries that are too vague to be skills

**`apache`** is the clearest case. The entry is named "Apache" with alias
`nginx`, so it means the web server — but "Apache" is a foundation, not a
product. Posting 17 is an Apache NiFi role, and its `apache` tag will make
the extractor assert web-server Apache for a data-integration job.

The same shape as the over-greedy aliases, one level up: the entry itself
names a category rather than a skill. Rename to "Apache HTTP Server" and
drop the bare `apache` surface form.

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

## Role-matching problems (continued)

| posting | filed as | actually |
|---|---|---|
| 5 — Staff Software Engineer | sde1-backend, entry-level | Senior role. Body text says "7+ years of experience in backend development", while Naukri's own `experience` field says `2-5 Yrs`. The exclude list catches "senior", "lead" and "architect" but not "staff". |

This is a second, distinct failure mode from posting 3. Posting 3 was the
wrong *profession*; this is the wrong *seniority*, and it slipped through
because the structured experience field disagrees with the description.
The structured field is the one we filter on, and it is not always right.

Candidate fixes, after scoring:
- add "staff", "principal", "sr", "iii", "iv" to the role exclude list
- cross-check the description for "N+ years" and prefer it over the
  structured field when they disagree

## Error patterns from the first 4 labelled postings

Two distinct failure modes, both visible before the set is even a tenth done.

**Recall losses are prose, not names.** System Design, Database Design, SQL
and NoSQL were all missed on posting 5, where the posting says "relational
and non-relational databases" and "Architect, design, build". The taxonomy
knows the token `nosql`, not the phrase that means it. A human reads
meaning; the matcher reads strings.

**Precision losses come from trusting employer tags.** Posting 4 is an
Android role whose Naukri tags include `sap`, `sas` and `social networking`.
The extractor takes tags at confidence 1.0, so it asserted SAP and SAS for
an Android job. The labeller correctly did not.

That is the more interesting of the two, because tags were chosen as the
high-confidence signal replacing required-vs-preferred. The evidence so far
says they are noisier than assumed, and the weighting may need to invert:
a tag corroborated by the description is strong, a tag appearing nowhere in
the body text is weak.

Candidate fixes, after scoring:
- phrase aliases for the prose forms ("non-relational database" -> nosql)
- down-weight a tag that never appears in the description, or require
  corroboration for tags outside the posting's own role category

## Misfiled postings, running count

Postings whose title matched a role pattern but whose actual work is
something else. Counted properly once labelling is complete.

| posting | title | actually |
|---|---|---|
| 3 | Junior Software Developer | GIS specialist |
| 5 | Staff Software Engineer | senior, 7+ years |
| 6 | Software Engineer III | senior, 5+ years |
| 9 | Software Engineer - Power | hardware/firmware, power management ICs |
| 15 | Software Engineer iPhone | iOS mobile development |
| 18 | Web Developer/Software Engineer | PHP/CakePHP/Drupal/WordPress agency work — the exact segment the exclude list was meant to keep out |

Six of the first eighteen — a third of the sample so far. Three distinct
causes:

**Exclusions are title-only.** Posting 18 is precisely the PHP/CMS agency
work the exclude list exists to filter out, but its title is "Web
Developer/Software Engineer" and every PHP mention is in the description.
The filter never reads the description, so the exclusion cannot fire. This
is a design flaw rather than a missing pattern — adding more words to the
list would not have caught it.

Two further causes: `software engineer` and `software developer` are so generic they
match any adjacent discipline, and seniority words like "staff" and "III"
are not excluded. Both are cheap to fix; the value is knowing the rate.

## Seniority leakage is looking systematic, not incidental

| posting | title | body says | Naukri field |
|---|---|---|---|
| 5 | Staff Software Engineer | 7+ years | 2-5 Yrs |
| 6 | Software Engineer III | 5+ years | 2-5 Yrs |
| 25 | Frontend Engineer | 6+ years, React 4+ years | 1-4 Yrs |

Three by posting 25, and the third is in the frontend block -- so this is
not a backend-only artefact. If the rate holds across the sample it is a headline
limitation, not a footnote: a meaningful share of the "entry-level" demand
profile is built from senior postings, which would inflate demand for
skills a fresher is not expected to have.

Worth counting exactly once labelling is complete, and reporting the figure.

Also seen here but out of taxonomy scope: Splunk (logging), Visual Studio
(an editor, not a skill).

## Scored at 10 postings: micro P 0.757 / R 0.889 / F1 0.818

63 true skill mentions, backend role only. Up from P 0.700 / R 0.840 at
four postings. Gate is R >= 0.70.

The spurious list has stopped being noise and become three named causes,
all of them over-greedy aliases in my own curation rather than faults in
the matcher:

| asserted | times | why |
|---|---|---|
| Problem Solving | 3 | `analytical` is an alias of problem-solving, and Naukri tags almost everything `analytical` |
| Cloud Fundamentals | 3 | "AWS Cloud" matches both AWS and the generic cloud entry, so we claim two skills where the labeller sees one |
| Computer Networks | 2 | `http` is an alias of networking; any posting tagged http acquires it |
| SAP | expected | `erp` is an alias of SAP, so posting 13's "Prior exposure to ERP products" will assert SAP although SAP is never named |

Recall losses split two ways:

- **Git (2)** — hides behind "GitHub", "version control", "code versioning
  tools". Some spellings are covered, not all.
- **SQL, NoSQL, Database Design, System Design, JavaScript (1 each)** —
  prose rather than names: "relational and non-relational databases",
  "Architect, design, build", Node.js implying JavaScript.

Candidate fixes, after the full 40:
- drop `analytical` from problem-solving; it is a trait, not a claim
- make Cloud Fundamentals fire only when no specific cloud is present
- drop `http` from networking
- add the missing Git spellings
- decide whether framework-implies-language should be an extraction rule or
  stay purely in the Stage 4 prerequisite graph

## Scored at 20 postings (backend block complete): P 0.810 / R 0.878 / F1 0.842

131 true skill mentions. Precision up from 0.757 at ten postings, recall
flat. Macro moved more (P 0.584 -> 0.738) as the later postings carried
fuller labels.

**JavaScript fails in both directions at once**, which is the sharpest
finding so far:

- missed 3x — the labeller ticks it because Node.js or React.js implies
  JavaScript; the extractor makes no such inference
- invented 2x — a `javascript` tag on postings whose descriptions
  contradict it (the Goldman Sachs systems role, the Python/Django role)

Too literal on the description, too trusting of the tags. One skill, two
opposite failures, needing two different fixes. Averaging them into "recall
is 0.88" would hide that entirely.

The three predicted over-greedy aliases are now confirmed with counts:
Problem Solving 4, Cloud Fundamentals 4, SAP 2.

Remaining backend recall losses are the prose problem again: System Design
2, Database Design 2, SQL, NoSQL — all phrases rather than names.
