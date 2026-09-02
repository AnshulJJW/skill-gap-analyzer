import { encouragement } from "./encouragement.js";
import { useCountUp } from "./motion.js";
import { Button, Callout, Empty, Flow, Icon, Loading, SkillRow } from "./ui.jsx";

/* The results screen, ordered by the questions someone actually arrives with:

     1. How close am I?          -> the score panel
     2. What should I learn?     -> the ranked list, first
     3. What am I missing, and
        what do I already have?  -> the skill comparison
     4. Where do these numbers
        come from?               -> the evidence table, last and collapsed

   The old version led with a chip cloud of found skills, which answered a
   question nobody opens the page to ask. */
export default function Results({
  report, roles, roleId, onRole, busy, error, onEdit, onReset,
}) {
  const pct = Math.round((report?.coverage ?? 0) * 100);
  // Hooks cannot sit behind the early return below.
  const shown = useCountUp(pct);
  if (!report) return null;

  const gaps = report.gaps ?? [];
  const note = encouragement(report.coverage, gaps.length);

  // Skills on the resume that this role actually asks for. Shown as the
  // second half of the comparison, after the gaps -- gaps are the part you
  // can act on, so they lead.
  const have = report.have_names ?? [];

  return (
    <main className="wrap md view">
      <Flow step={3} />

      <div className="result-head">
        <div>
          <h1>{report.role_name}</h1>
          <p className="sub">
            {report.total_postings.toLocaleString()} postings · {report.market} market
          </p>
        </div>
        <div style={{ display: "flex", gap: ".5rem", alignItems: "center" }}>
          <label htmlFor="role2" className="small muted" style={{ margin: 0 }}>Role</label>
          <select
            id="role2"
            value={roleId}
            onChange={(e) => onRole(e.target.value)}
            disabled={busy}
            style={{ width: "auto", minWidth: "11rem" }}
          >
            {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
          </select>
        </div>
      </div>

      <section className="score">
        <div className="dial" style={{ "--pct": shown }} role="img"
             aria-label={`Coverage ${pct} percent`}>
          <div className="face">
            <div>
              <div className="v">{shown}%</div>
              <div className="l">covered</div>
            </div>
          </div>
        </div>
        <div>
          <div className="headline">
            You have {report.core_have} of the {report.core_total} skills this
            role asks for most.
          </div>
          <div className="detail">
            Weighted by how often each skill appears, that covers {pct}% of
            what employers ask for.
          </div>
          <div className="encourage">
            <span className="ico"><Icon.trend /></span>
            <span>{note}</span>
          </div>
        </div>
      </section>

      {error && <div style={{ marginTop: "1rem" }}><Callout tone="danger">{error}</Callout></div>}

      {busy ? <Loading label="Recalculating for this role" /> : (
        <>
          <section className="res-block" data-reveal>
            <div className="section-head">
              <h2>What to learn next</h2>
              <p>In order. Anything marked <em>needed first</em> is there because a step below it depends on it.</p>
            </div>
            {report.roadmap.length === 0 ? (
              <Empty icon="route">Nothing to add for this role.</Empty>
            ) : (
              <ol className="roadmap">
                {report.roadmap.map((step, i) => (
                  <li key={step.skill_id}>
                    <div className="head">
                      <span className="n">{i + 1}</span>
                      <span className="name">{step.skill_name}</span>
                      {step.is_prerequisite && <span className="tag">needed first</span>}
                    </div>
                    {step.reason && <p className="why">{step.reason}</p>}
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
              <h2>Your skills against this role</h2>
              <p>
                Gaps first, because that is what you can act on. The bar is
                how many postings ask for that skill — the order is by how
                much each would raise your score, which is not the same
                thing.
              </p>
            </div>

            {have.length === 0 && gaps.length === 0 ? (
              <Empty>Nothing matched. Check the resume text and try again.</Empty>
            ) : (
              <>
                {gaps.length > 0 && (
                  <>
                    <h3 className="group">Missing <span>{gaps.length}</span></h3>
                    <ul className="skill-list">
                      {gaps.map((g) => (
                        <SkillRow key={g.skill_id} name={g.skill_name} have={false} share={g.share} />
                      ))}
                    </ul>
                  </>
                )}
                {have.length > 0 && (
                  <>
                    {/* Chips rather than rows: these carry no demand figure to
                        show, and a column of empty dashes reads as broken. */}
                    <h3 className="group">Already on your resume <span>{have.length}</span></h3>
                    <ul className="chips">
                      {have.map((name) => <li key={name} className="chip">{name}</li>)}
                    </ul>
                  </>
                )}
              </>
            )}

            {report.unused.length > 0 && (
              <details className="more">
                <summary>
                  <Icon.chevron className="chev" width={12} height={12} />
                  {report.unused.length} other skills on your resume this role does not ask for
                </summary>
                <ul className="chips">
                  {report.unused.map((s) => <li key={s} className="chip muted">{s}</li>)}
                </ul>
              </details>
            )}
          </section>

          <section className="res-block" data-reveal>
            <details className="more">
              <summary>
                <Icon.chevron className="chev" width={12} height={12} />
                Where these numbers come from
              </summary>
              <p className="small muted">
                Coverage added is how much your score would rise by learning
                that skill next, given the ones above it.
              </p>
              <div className="scroller">
                <table className="data">
                  <thead>
                    <tr>
                      <th>Skill</th>
                      <th>Coverage added</th>
                      <th className="ev">Found in</th>
                    </tr>
                  </thead>
                  <tbody>
                    {gaps.map((g) => (
                      <tr key={g.skill_id}>
                        <td className="skill">{g.skill_name}</td>
                        <td className="n">+{(g.marginal_gain * 100).toFixed(1)}%</td>
                        <td className="ev">{g.evidence}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          </section>
        </>
      )}

      <div className="actions res-block">
        <Button variant="secondary" onClick={onEdit}>Edit my resume text</Button>
        <span className="spacer" />
        <Button variant="quiet" onClick={onReset}>Start over</Button>
      </div>
    </main>
  );
}
