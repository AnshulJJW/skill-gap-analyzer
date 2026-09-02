import { encouragementForJD } from "./encouragement.js";
import { useCountUp } from "./motion.js";
import { Button, Callout, Empty, Flow, Icon, SkillRow } from "./ui.jsx";

/* Results for a single job posting.

   Deliberately a different shape from the role report. With one posting
   there are no frequencies to rank by -- every skill it names appears
   exactly once -- so the interesting column is how typical each requirement
   is across the wider market. That is what turns "you are missing ten
   things" into "two of these are worth your month".

   The layout matches Results.jsx element for element so the two screens read
   as one product. */
export default function JDResults({ report, onEdit, onReset }) {
  const pct = Math.round((report?.coverage ?? 0) * 100);
  // Hooks cannot sit behind the early return below.
  const shown = useCountUp(pct);
  if (!report) return null;

  const total = report.matched.length + report.missing.length;
  const note = encouragementForJD(report.coverage, report.missing.length);

  return (
    <main className="wrap md view">
      <Flow step={3} />

      <div className="result-head">
        <div>
          <h1>This job posting</h1>
          <p className="sub">
            {report.role_name
              ? `Market context from ${report.market_postings.toLocaleString()} ${report.role_name} postings`
              : "No market context — pick a role to compare against"}
          </p>
        </div>
      </div>

      <section className="score">
        <div className="dial" style={{ "--pct": shown }} role="img"
             aria-label={`Match ${pct} percent`}>
          <div className="face">
            <div>
              <div className="v">{shown}%</div>
              <div className="l">match</div>
            </div>
          </div>
        </div>
        <div>
          <div className="headline">
            You have {report.matched.length} of the {total} skills this posting names.
          </div>
          <div className="detail">
            The percentage beside each skill is how many similar postings ask
            for it too.
          </div>
          <div className="encourage">
            <span className="ico"><Icon.trend /></span>
            <span>{note}</span>
          </div>
        </div>
      </section>

      {report.unmatched_note && (
        <div style={{ marginTop: "1rem" }}>
          <Callout tone="warn">{report.unmatched_note}</Callout>
        </div>
      )}

      <section className="res-block" data-reveal>
        <div className="section-head">
          <h2>What to learn next</h2>
          <p>In order, with anything a later step depends on brought forward.</p>
        </div>
        {report.roadmap.length === 0 ? (
          <Empty icon="route">Nothing to add for this posting.</Empty>
        ) : (
          <ol className="roadmap">
            {report.roadmap.map((step, i) => (
              <li key={step.skill_id}>
                <div className="head">
                  <span className="n">{i + 1}</span>
                  <span className="name">{step.skill_name}</span>
                  {step.is_prerequisite && <span className="tag">needed first</span>}
                </div>
                {step.resources.length > 0 && (
                  <div className="resources">
                    {step.resources.map((r) => (
                      <a key={r.url} className="resource" href={r.url}
                         target="_blank" rel="noreferrer noopener">
                        <span>{r.title}</span>
                        <span className="meta">
                          {r.kind}{r.hours ? ` · ${r.hours}h` : ""}
                        </span>
                      </a>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>

      <section className="res-block" data-reveal>
        <div className="section-head">
          <h2>What this posting asks for</h2>
          <p>
            Gaps first. A skill few other postings want is specific to
            this employer, and worth less of your time.
          </p>
        </div>
        {total === 0 ? (
          <Empty>No known skills were found in that posting.</Empty>
        ) : (
          <>
            {report.missing.length > 0 && (
              <>
                <h3 className="group">Missing <span>{report.missing.length}</span></h3>
                <ul className="skill-list">
                  {report.missing.map((s) => (
                    <SkillRow key={s.skill_id} name={s.skill_name} have={false} share={s.market_share} />
                  ))}
                </ul>
              </>
            )}
            {report.matched.length > 0 && (
              <>
                <h3 className="group">You already have <span>{report.matched.length}</span></h3>
                <ul className="skill-list">
                  {report.matched.map((s) => (
                    <SkillRow key={s.skill_id} name={s.skill_name} have share={s.market_share} />
                  ))}
                </ul>
              </>
            )}
          </>
        )}
      </section>

      <div className="actions res-block">
        <Button variant="secondary" onClick={onEdit}>Edit and try again</Button>
        <span className="spacer" />
        <Button variant="quiet" onClick={onReset}>Start over</Button>
      </div>
    </main>
  );
}
