/* The results view. Separate from the landing page on purpose: once someone
   has a report, the marketing copy is noise and the screen should be about
   their answer. */

import { useCountUp } from "./motion.js";

export default function Results({
  report, roles, roleId, onRole, busy, onEdit, onReset,
}) {
  const pct = Math.round((report?.coverage ?? 0) * 100);
  // Hooks run before the early return below, so this cannot be conditional.
  const shown = useCountUp(pct);
  if (!report) return null;

  return (
    <main className="wrap results">
      <p className="eyebrow">Step 3 of 3 · your result</p>

      <div className="scoreline">
        <div className="dial" style={{ "--pct": shown }}>
          <span>{shown}%</span>
        </div>
        <div>
          <h1>{report.role_name}</h1>
          <p>
            You have <strong>{report.core_have}</strong> of the{" "}
            <strong>{report.core_total}</strong> most-demanded skills for this
            role, measured across{" "}
            {report.total_postings.toLocaleString()} postings in the{" "}
            {report.market} market.
          </p>
        </div>
      </div>

      <div className="controls">
        <div>
          <label htmlFor="role2">Compare against a different role</label>
          <select
            id="role2"
            value={roleId}
            onChange={(e) => onRole(e.target.value)}
            disabled={busy}
          >
            {roles.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
        </div>
        <button className="ghost" onClick={onEdit}>Edit my resume text</button>
        <button className="plain" onClick={onReset}>Start over</button>
      </div>

      {/* Showing what WAS found matters as much as the gaps: it lets a wrong
          extraction be spotted instead of hiding inside a confident score. */}
      <section className="res-section" data-reveal>
        <h2>What we found on your resume</h2>
        <p className="hint">
          If something here is wrong, the score is wrong too — go back and
          correct the text.
        </p>
        <ul className="chips">
          {report.have_names.map((s) => (
            <li key={s} className="chip">{s}</li>
          ))}
        </ul>
        {report.unused.length > 0 && (
          <details>
            <summary>
              {report.unused.length} skills on your resume this role does not
              ask for
            </summary>
            <ul className="chips">
              {report.unused.map((s) => (
                <li key={s} className="chip muted">{s}</li>
              ))}
            </ul>
          </details>
        )}
      </section>

      <section className="res-section" data-reveal>
        <h2>Learn these, in this order</h2>
        <p className="hint">
          Prerequisites come first, so you can start at the top. Steps marked
          as prerequisites were not the highest-impact skills — they are things
          the next step needs.
        </p>
        <ol className="roadmap">
          {report.roadmap.map((step) => (
            <li key={step.skill_id}>
              <div className="step-head">
                <span className="step-name">{step.skill_name}</span>
                {step.is_prerequisite && <span className="tag">prerequisite</span>}
              </div>
              <p className="reason">{step.reason}</p>
              {step.resources.map((r) => (
                <a
                  key={r.url}
                  className="resource"
                  href={r.url}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  {r.title}
                  <span className="meta">
                    {r.kind}{r.hours ? ` · ~${r.hours}h` : ""}
                  </span>
                </a>
              ))}
            </li>
          ))}
        </ol>
      </section>

      <section className="res-section" data-reveal>
        <h2>The evidence behind each gap</h2>
        <p className="hint">
          Coverage added is what learning that skill next would gain you, given
          everything above it.
        </p>
        <div className="scroller">
          <table className="gaps">
            <thead>
              <tr>
                <th>Skill</th>
                <th>Coverage added</th>
                <th className="ev">Measured demand</th>
              </tr>
            </thead>
            <tbody>
              {report.gaps.map((g) => (
                <tr key={g.skill_id}>
                  <td className="skill">{g.skill_name}</td>
                  <td className="num">+{(g.marginal_gain * 100).toFixed(1)}%</td>
                  <td className="ev">{g.evidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
