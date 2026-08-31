/* Results for a single job description.
   Deliberately a different shape from the role report: with one posting
   there are no frequencies to rank by, so the interesting column is how
   typical each requirement is across the wider market. That is what turns
   "you are missing ten things" into "two of these are worth your month". */

export default function JDResults({ report, onEdit, onReset }) {
  if (!report) return null;
  const pct = Math.round(report.coverage * 100);
  const total = report.matched.length + report.missing.length;

  return (
    <main className="wrap results">
      <p className="eyebrow">Your result · one job description</p>

      <div className="scoreline">
        <div className="dial" style={{ "--pct": pct }}>
          <span>{pct}%</span>
        </div>
        <div>
          <h1>This posting</h1>
          <p>
            You meet <strong>{report.matched.length}</strong> of the{" "}
            <strong>{total}</strong> skills this job description names.
            {report.role_name && (
              <>
                {" "}
                Market context comes from{" "}
                {report.market_postings.toLocaleString()} {report.role_name}{" "}
                postings.
              </>
            )}
          </p>
        </div>
      </div>

      <div className="controls">
        <button className="ghost" onClick={onEdit}>Edit and try again</button>
        <button className="plain" onClick={onReset}>Start over</button>
      </div>

      {report.unmatched_note && (
        <div className="notice">{report.unmatched_note}</div>
      )}

      <section className="res-section">
        <h2>What this posting wants that you are missing</h2>
        <p className="hint">
          Ordered by how much the wider market wants each one — so you can see
          which gaps are worth closing generally, and which matter only here.
        </p>
        <ul className="jd-list">
          {report.missing.map((s) => (
            <li key={s.skill_id}>
              <span className="name">{s.skill_name}</span>
              <span className={`note ${noteClass(s.market_share)}`}>
                {s.market_note}
              </span>
            </li>
          ))}
        </ul>
        {report.missing.length === 0 && (
          <p>Nothing missing — this posting asks for nothing you lack.</p>
        )}
      </section>

      {report.roadmap.length > 0 && (
        <section className="res-section">
          <h2>Where to start</h2>
          <p className="hint">
            Prerequisites first. Skills nobody can hand you a course for —
            communication, problem solving — are left out on purpose.
          </p>
          <ol className="roadmap">
            {report.roadmap.map((step) => (
              <li key={step.skill_id}>
                <div className="step-head">
                  <span className="step-name">{step.skill_name}</span>
                  {step.is_prerequisite && (
                    <span className="tag">prerequisite</span>
                  )}
                </div>
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
      )}

      <section className="res-section">
        <h2>What you already match</h2>
        <ul className="jd-list">
          {report.matched.map((s) => (
            <li key={s.skill_id}>
              <span className="name">{s.skill_name}</span>
              <span className={`note ${noteClass(s.market_share)}`}>
                {s.market_note}
              </span>
            </li>
          ))}
        </ul>
        {report.matched.length === 0 && (
          <p>
            Nothing matched. If that seems wrong, go back and check the resume
            text was read correctly.
          </p>
        )}
      </section>
    </main>
  );
}

function noteClass(share) {
  if (share === null || share === undefined) return "narrow";
  if (share >= 0.25) return "broad";
  if (share < 0.08) return "narrow";
  return "";
}
