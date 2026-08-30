# Labelling guide — Stage 3

The rules used to produce `labels.json`. Written down because consistency
matters more than any individual judgement call: an interviewer can argue
with a rule, but not with a rule applied evenly across all 40 postings.

## What counts as evidence

Both the **description** and the **employer tags**. Both are part of the
posting record and both are visible to the extractor, so excluding either
would penalise the extractor for using data it was designed to use.

The tags are noisy — roughly half are not skills — so they are filtered by
the same test as everything else, not copied wholesale.

**A tag counts only when the description does not contradict it.** Naukri's
tagging is keyword-driven and regularly attaches skills from an unrelated
role: `sap` and `sas` on an Android job (posting 4), `html` and
`javascript` on a Goldman Sachs role about compiled languages, concurrency
and memory management (posting 7).

- tag supported by the description, or simply unmentioned but plausible for
  the role → tick
- tag that clashes with what the posting actually describes → skip

This is a judgement call, and it is the judgement the extractor cannot make
— it takes tags at face value. Where the labeller and the extractor
disagree here, that disagreement is the finding, not an error.

## The test for ticking a skill

> Can I point at words in this posting that name it?

If yes, tick. If no, leave it — **however obvious the skill seems for the
role**. We are measuring whether the extractor finds what the posting says,
not whether it can guess what the job really needs.

Example: a Trainee Software Engineer role obviously needs Git. If the
posting never says Git, Git is not labelled. Otherwise the extractor is
marked wrong for failing to be psychic.

## What is never ticked

| category | examples |
|---|---|
| job titles | backend, frontend, software engineer, developer |
| vague activity | coding, programming, development, software |
| degrees | computer science, MCA, B.Tech |
| traits | analytical, good attitude, strong aptitude |
| a category with no specific technology | "mobile technologies", "web technologies" |

That last one matters. "Should understand mobile technologies" names no
technology — not Android, not iOS, not React Native. Nothing to tick.

## Judgement calls, decided once and applied throughout

- **SDLC** → tick *Agile / Scrum*. The taxonomy groups them.
- **Node.js mentioned** → also tick *JavaScript*. Node is JavaScript.
- **"software testing" / "testing"** → tick *Automated Testing*.
- **"troubleshooting"** → tick *Debugging*.
- **A framework named without its language** (e.g. Django but not Python)
  → tick both. Naming the framework asserts the language.
- **Soft skills** (communication, problem solving) → tick only when the
  posting states them explicitly, which is often.

## When unsure

Leave it off. A false positive damages precision immediately; a miss costs
recall by the same amount, but a wrongly-ticked skill also corrupts the
ground truth itself, which is worse — every future measurement inherits it.

## Postings with almost nothing

Some are pure boilerplate. Posting 1 in this sample names no language, no
framework, no database — only "testing", "debugging" and "troubleshooting".
Two ticks is the correct answer there. Do not pad.

## Known limitation of this method

A skill absent from the taxonomy cannot be labelled, so these figures
measure how well the extractor finds skills it knows about — not how
complete the taxonomy is. Taxonomy coverage is a separate question and is
reported separately rather than folded into precision and recall.
