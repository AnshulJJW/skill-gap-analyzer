import { useEffect, useState } from "react";
import { analyze, getRoles } from "./api.js";

const MIN_RESUME_CHARS = 50;

export default function App() {
  const [roles, setRoles] = useState([]);
  const [roleId, setRoleId] = useState("");
  const [resume, setResume] = useState("");
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getRoles()
      .then((r) => {
        setRoles(r);
        if (r.length) setRoleId(r[0].id);
      })
      .catch((e) => setError(e.message));
  }, []);

  const tooShort = resume.trim().length < MIN_RESUME_CHARS;

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setReport(null);
    try {
      setReport(await analyze(resume, roleId));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const role = roles.find((r) => r.id === roleId);

  return (
    <div className="page">
      <header>
        <h1>Skill-Gap Analyzer</h1>
        <p className="lede">
          Paste your resume, pick a role, and see which skills the market
          actually asks for — measured across real job postings, not guessed.
        </p>
      </header>

      <form onSubmit={onSubmit}>
        <label htmlFor="resume">Your resume, as plain text</label>
        <textarea
          id="resume"
          value={resume}
          onChange={(e) => setResume(e.target.value)}
          placeholder={
            "TECHNICAL SKILLS\n" +
            "Programming Languages: Python, Java, SQL\n" +
            "Databases: MySQL\n" +
            "Tools: Git, GitHub\n\n" +
            "PROJECTS\n" +
            "Built a web application using Django and MySQL."
          }
          rows={12}
          spellCheck={false}
        />
        <p className="hint">
          {resume.trim().length} characters
          {tooShort && resume.length > 0 && ` — need at least ${MIN_RESUME_CHARS}`}
        </p>

        <div className="row">
          <div>
            <label htmlFor="role">Target role</label>
            <select
              id="role"
              value={roleId}
              onChange={(e) => setRoleId(e.target.value)}
              disabled={!roles.length}
            >
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>
          <button type="submit" disabled={busy || tooShort || !roleId}>
            {busy ? "Analysing…" : "Analyse"}
          </button>
        </div>

        {role && (
          <p className="hint">
            Compared against {role.total_postings.toLocaleString()} real{" "}
            {role.name} postings ({role.market} market).
          </p>
        )}
      </form>

      {busy && (
        <p className="status">
          Reading your resume and comparing it against the demand profile…
        </p>
      )}

      {error && (
        <div className="error" role="alert">
          <strong>Something went wrong.</strong> {error}
        </div>
      )}

      {report && <Report report={report} />}

      <footer>
        Demand measured from a frozen snapshot of Naukri postings. Extraction
        accuracy is hand-measured — see the README for precision, recall and
        the limitations.
      </footer>
    </div>
  );
}

function Report({ report }) {
  const pct = Math.round(report.coverage * 100);
  return (
    <section className="report">
      <div className="score">
        <div className="dial" style={{ "--pct": pct }}>
          <span>{pct}%</span>
        </div>
        <div>
          <h2>{report.role_name}</h2>
          <p>
            You have <strong>{report.core_have}</strong> of the{" "}
            <strong>{report.core_total}</strong> most-demanded skills for this
            role, across {report.total_postings.toLocaleString()} postings.
          </p>
        </div>
      </div>

      {/* Showing what WAS found matters as much as what is missing: it lets
          the user see when extraction got something wrong, instead of hiding
          it behind a confident-looking score. */}
      <details open>
        <summary>Skills found on your resume ({report.have.length})</summary>
        <ul className="chips">
          {report.have.map((s) => (
            <li key={s} className="chip have">
              {s}
            </li>
          ))}
        </ul>
        {report.unused.length > 0 && (
          <>
            <p className="hint">On your resume, but not asked for in this role:</p>
            <ul className="chips">
              {report.unused.map((s) => (
                <li key={s} className="chip muted">
                  {s}
                </li>
              ))}
            </ul>
          </>
        )}
      </details>

      <h3>Learn next</h3>
      <p className="hint">
        Ordered so prerequisites come first — start at the top.
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
            <p className="reason">{step.reason}</p>
            {step.resources.map((r) => (
              <a
                key={r.url}
                href={r.url}
                target="_blank"
                rel="noreferrer noopener"
                className="resource"
              >
                {r.title}
                <span className="meta">
                  {r.kind}
                  {r.hours ? ` · ~${r.hours}h` : ""}
                </span>
              </a>
            ))}
          </li>
        ))}
      </ol>

      <h3>Biggest gaps, with the evidence</h3>
      <table className="gaps">
        <thead>
          <tr>
            <th>Skill</th>
            <th>Coverage added</th>
            <th>Why</th>
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
    </section>
  );
}
