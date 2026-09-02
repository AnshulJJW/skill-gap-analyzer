import { encouragement } from "./encouragement.js";
import { useCountUp, useMounted } from "./motion.js";
import {
  Button, Callout, Empty, Flow, GapCard, Icon, Loading, Ring, Tile,
} from "./ui.jsx";

/* The results screen, ordered by the questions someone actually arrives with:

     1. How close am I?          -> the score panel, above the fold
     2. What should I learn?     -> the ranked path
     3. Where are my gaps, and
        what have I already got? -> gap cards, then strengths
     4. Where do the numbers
        come from?               -> the evidence table, last and collapsed

   An earlier version led with a chip cloud of skills found, which answers a
   question nobody opens the page to ask. */
export default function Results({
  report, roles, roleId, onRole, busy, error, onEdit, onReset,
}) {
  const pct = Math.round((report?.coverage ?? 0) * 100);
  // Hooks cannot sit behind the early return below.
  const shown = useCountUp(pct);
  const mounted = useMounted();
  if (!report) return null;

  const gaps = report.gaps ?? [];
  // Skills on the resume that this role actually asks for. Shown after the
  // gaps: gaps are the part you can act on, so they lead.
  const have = report.have_names ?? [];
  const held = report.held ?? [];
  const confirmed = held.filter((h) => h.confirmed);
  // Found only under a heading like EDUCATION -- a course title rather than
  // a claim. Worth showing separately: it is the one thing on the page the
  // reader can fix in five minutes, by moving it onto a project.
  const weak = held.filter((h) => !h.confirmed);
  const note = encouragement(report.coverage, gaps.length);

  return (
    <main className="wrap md view">
      <Flow step={3} />

      <div className="result-head">
        <div>
          <h1>{report.role_name}</h1>
          <p className="sub">
            Measured against {report.total_postings.toLocaleString()} postings
            in the {report.market} market
          </p>
        </div>
        <div className="role-pick">
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
        <Ring value={shown} label="covered" />
        <div>
          <div className="headline">
            You have {report.core_have} of the {report.core_total} skills this
            role asks for most.
          </div>
          <div className="detail">
            Weighted by how often each skill appears, that covers {pct}% of
            what employers ask for.
          </div>

          <div className="tiles">
            <Tile tone="ok" value={have.length} label="skills you have" />
            <Tile tone="warn" value={gaps.length} label="gaps to close" />
            <Tile value={report.roadmap.length} label="steps to take" />
          </div>

          <div className="encourage">
            <span className="ico"><Icon.trend /></span>
            <span>{note}</span>
          </div>
        </div>
      </section>

      {report.empty_note && (
        <div className="res-block">
          <Callout tone="warn"><strong>Nothing was recognised.</strong> {report.empty_note}</Callout>
        </div>
      )}

      {error && <div className="res-block"><Callout tone="danger">{error}</Callout></div>}

      {busy ? <Loading label="Recalculating for this role" /> : (
        <>
          <section className="res-block" data-reveal>
            <div className="section-head">
              <h2>What to learn next</h2>
              <p>
                In order. Anything marked <em>needed first</em> is there
                because a step below it depends on it.
              </p>
            </div>
            {report.roadmap.length === 0 ? (
              <Empty icon="route">Nothing to add for this role.</Empty>
            ) : (
              <ol className="roadmap">
                {report.roadmap.map((step, i) => (
                  <li key={step.skill_id} data-stagger>
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
              <h2>Your skills, side by side</h2>
              <p>
                Gaps first, because that is what you can act on. The bar is
                how many postings ask for that skill — the order is by how
                much each would raise your score, which is not the same
                thing.
              </p>
            </div>

            {held.length === 0 && gaps.length === 0 ? (
              <Empty>Nothing matched. Check the resume text and try again.</Empty>
            ) : (
              <>
                {gaps.length > 0 && (
                  <>
                    <h3 className="group">
                      Skills to improve <span className="count warn">{gaps.length}</span>
                    </h3>
                    <ul className="gap-grid" style={{ listStyle: "none", padding: 0, margin: 0 }}>
                      {gaps.map((g, i) => (
                        <GapCard
                          key={g.skill_id}
                          rank={i}
                          name={g.skill_name}
                          category={g.category}
                          share={g.share}
                          gain={g.marginal_gain}
                          mounted={mounted}
                        />
                      ))}
                    </ul>
                  </>
                )}

                {confirmed.length > 0 && (
                  <>
                    <h3 className="group">
                      Skills you already have <span className="count ok">{confirmed.length}</span>
                    </h3>
                    {/* Compact tiles rather than metered rows: these carry no
                        demand figure, and a column of empty dashes reads as
                        broken. */}
                    <div className="have-grid">
                      {confirmed.map((h) => (
                        <div className="have-item" key={h.skill_id} title={`Found under ${h.section}`}>
                          <span className="ico"><Icon.check width={14} height={14} /></span>
                          {h.skill_name}
                        </div>
                      ))}
                    </div>
                  </>
                )}

                {weak.length > 0 && (
                  <>
                    <h3 className="group">
                      Only mentioned in passing <span className="count">{weak.length}</span>
                    </h3>
                    <p className="small muted" style={{ marginTop: "-.35rem", marginBottom: ".7rem" }}>
                      These appear under a heading like Education rather than in
                      your skills list or a project. They still count toward your
                      score — but a recruiter reading quickly may not credit them.
                    </p>
                    <div className="have-grid">
                      {weak.map((h) => (
                        <div className="have-item weak" key={h.skill_id} title={`Found under ${h.section}`}>
                          <span className="ico"><Icon.alert width={14} height={14} /></span>
                          {h.skill_name}
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </>
            )}

            {report.unused.length > 0 && (
              <details className="more">
                <summary>
                  <Icon.chevron className="chev" width={12} height={12} />
                  {report.unused.length} other skill{report.unused.length === 1 ? "" : "s"} on your resume this role does not ask for
                </summary>
                <ul className="chips">
                  {report.unused.map((s) => <li key={s} className="chip">{s}</li>)}
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
