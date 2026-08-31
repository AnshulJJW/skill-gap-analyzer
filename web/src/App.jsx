import { useEffect, useRef, useState } from "react";
import { analyze, analyzeJD, getRoles, parseResume } from "./api.js";
import JDResults from "./JDResults.jsx";
import { useReveal } from "./motion.js";
import Results from "./Results.jsx";

const MIN_RESUME_CHARS = 50;
const MIN_JD_CHARS = 80;

/* Three views rather than one long page.
   Landing sells and takes the upload. Review is the safety step -- PDF
   extraction scrambles two-column layouts and nothing reliably detects
   when it has, so the text is always shown before anything is analysed.
   Results is a focused screen with the marketing gone. */
export default function App() {
  const [view, setView] = useState("landing");
  const [roles, setRoles] = useState([]);
  const [roleId, setRoleId] = useState("");
  const [resume, setResume] = useState("");
  const [uploaded, setUploaded] = useState(null);
  const [report, setReport] = useState(null);
  const [jdReport, setJdReport] = useState(null);
  const [mode, setMode] = useState("role");   // "role" | "jd"
  const [jd, setJd] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const fileInput = useRef(null);

  // Keyed on the view: each one mounts nodes the previous observer never saw.
  useReveal(view);

  useEffect(() => {
    getRoles()
      .then((r) => {
        setRoles(r);
        if (r.length) setRoleId(r[0].id);
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [view]);

  async function handleFile(file) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const parsed = await parseResume(file);
      setResume(parsed.text);
      setUploaded({ name: file.name, ...parsed });
      setView("review");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function runAnalysis() {
    setBusy(true);
    setError(null);
    try {
      if (mode === "jd") {
        setJdReport(await analyzeJD(resume, jd, roleId));
        setReport(null);
        setView("jdresults");
      } else {
        setReport(await analyze(resume, roleId));
        setJdReport(null);
        setView("results");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setReport(null);
    setJdReport(null);
    setResume("");
    setJd("");
    setUploaded(null);
    setError(null);
    setView("landing");
  }

  return (
    <>
      <Topbar onHome={reset} showBack={view !== "landing"} />
      {view === "landing" && (
        <Landing
          roles={roles}
          busy={busy}
          error={error}
          fileInput={fileInput}
          onFile={handleFile}
          onPaste={() => setView("review")}
        />
      )}
      {view === "review" && (
        <Review
          resume={resume}
          setResume={setResume}
          uploaded={uploaded}
          roles={roles}
          roleId={roleId}
          setRoleId={setRoleId}
          busy={busy}
          error={error}
          mode={mode}
          setMode={setMode}
          jd={jd}
          setJd={setJd}
          onRun={runAnalysis}
          onBack={reset}
        />
      )}
      {view === "jdresults" && (
        <JDResults
          report={jdReport}
          onEdit={() => setView("review")}
          onReset={reset}
        />
      )}
      {view === "results" && (
        <Results
          report={report}
          roles={roles}
          roleId={roleId}
          onRole={async (id) => {
            setRoleId(id);
            setBusy(true);
            try {
              setReport(await analyze(resume, id));
            } catch (e) {
              setError(e.message);
            } finally {
              setBusy(false);
            }
          }}
          busy={busy}
          onEdit={() => setView("review")}
          onReset={reset}
        />
      )}
      <SiteFooter />
    </>
  );
}

function Topbar({ onHome, showBack }) {
  return (
    <header className="topbar">
      <div className="wrap">
        <div className="brand">
          <span className="mark">SG</span> Skill-Gap Analyzer
        </div>
        <nav>
          {showBack ? (
            <button className="plain" onClick={onHome}>
              Start over
            </button>
          ) : (
            <>
              <a href="#what">What you get</a>
              <a href="#how">How it works</a>
              <a href="#method">Method</a>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

function Landing({ roles, busy, error, fileInput, onFile, onPaste }) {
  const [dragging, setDragging] = useState(false);
  const total = roles.reduce((n, r) => n + r.total_postings, 0);

  return (
    <main>
      <div className="wrap hero">
        <p className="eyebrow">Measured, not guessed</p>
        <h1>
          Find out which skills are actually <em>costing you interviews</em>.
        </h1>
        <p className="sub">
          Upload your resume and see it compared against thousands of real job
          postings — with the evidence for every recommendation, and an honest
          account of what the numbers cannot tell you.
        </p>

        <div className="trust">
          <span>
            <b>{total ? total.toLocaleString() : "—"}</b> real postings analysed
          </span>
          <span>
            <b>{roles.length || "—"}</b> roles covered
          </span>
          <span>
            <b>Free</b> · no account needed
          </span>
        </div>

        <div
          className={`dropzone${dragging ? " over" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            onFile(e.dataTransfer.files?.[0]);
          }}
        >
          <input
            ref={fileInput}
            type="file"
            accept="application/pdf,.pdf"
            onChange={(e) => onFile(e.target.files?.[0])}
            hidden
          />
          <span className="arrow">↑</span>
          <h2>Drop your resume here</h2>
          <p>PDF · stays on your machine · nothing is stored</p>
          <button onClick={() => fileInput.current?.click()} disabled={busy}>
            {busy ? "Reading your PDF…" : "Choose a PDF"}
          </button>
          <div className="assure">
            <span>No sign-up</span>
            <span>No file kept after analysis</span>
            <span>
              <button className="plain" onClick={onPaste}>
                or paste the text instead
              </button>
            </span>
          </div>
        </div>

        {error && <div className="error">{error}</div>}
      </div>

      <section className="band" id="what" data-reveal>
        <div className="wrap">
          <div className="section-head">
            <h2>What you get</h2>
            <p>
              Six things, each traceable back to a number you can check.
            </p>
          </div>
          <div className="cards">
            {WHAT.map((c, i) => (
              <article key={c.title}>
                <div className="n">0{i + 1}</div>
                <h3>{c.title}</h3>
                <p>{c.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="band" id="how" data-reveal>
        <div className="wrap">
          <div className="section-head">
            <h2>How it works</h2>
            <p>Three steps. No sign-up, no card, nothing stored.</p>
          </div>
          <div className="steps">
            {HOW.map((s, i) => (
              <div className="step" key={s.title} data-n={i + 1}>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="band" id="method" data-reveal>
        <div className="wrap">
          <div className="section-head">
            <h2>How the numbers were checked</h2>
            <p>
              Most tools in this space ask you to take their accuracy on
              trust. This one was measured, and the measurement is published.
            </p>
          </div>
          <div className="prose">
            <p>
              Forty job postings were read and labelled by hand — 255 skill
              mentions — by a person who could not see what the extractor had
              produced. The extractor was then scored against those labels:{" "}
              <strong>precision 0.86, recall 0.90</strong>.
            </p>
            <p>
              That process also found a problem the code could not: roughly one
              posting in six had been filed under the wrong role — GIS and
              firmware jobs sitting in a backend bucket, senior roles labelled
              entry-level. Those are now filtered out, and the rate is
              published rather than hidden.
            </p>
            <p>
              Demand comes from a frozen snapshot of Naukri postings, so the
              percentages describe the Indian entry-level market specifically.
              The full method, the numbers and the limitations are in the{" "}
              <a
                href="https://github.com/AnshulJJW/skill-gap-analyzer"
                target="_blank"
                rel="noreferrer noopener"
              >
                repository
              </a>
              .
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

const WHAT = [
  {
    title: "Coverage score",
    body: "How much of what this role actually demands you already meet, measured against its thirty most-requested skills rather than a long tail nobody has.",
  },
  {
    title: "The skills it found",
    body: "Everything read off your resume, shown openly — so when the parser gets something wrong you can see it, instead of it hiding inside a confident number.",
  },
  {
    title: "Ranked gaps",
    body: "Not the most common missing skill, but the one that unlocks the most postings you currently fail. Each pick is chosen given the ones before it.",
  },
  {
    title: "A learning order",
    body: "Prerequisites first. It will never tell you to learn Kubernetes before Docker, or a framework before its language.",
  },
  {
    title: "Free resources",
    body: "A curated free resource for each step, with a rough time cost. Hand-picked, not generated — and the README says so plainly.",
  },
  {
    title: "The evidence",
    body: "Every recommendation carries its count: appears in 42% of 4,837 postings. A percentage without a denominator is an assertion, not a measurement.",
  },
];

const HOW = [
  {
    title: "Upload your resume",
    body: "Drop in a PDF, or paste the text. Nothing is uploaded anywhere permanent and nothing is stored after the analysis runs.",
  },
  {
    title: "Check what was read",
    body: "The extracted text is shown to you first. PDF layouts scramble in ways nothing can reliably detect, so you get to correct it before anything is measured.",
  },
  {
    title: "Read the gap",
    body: "Pick a role and get your coverage, your ranked gaps with evidence, and a prerequisite-ordered path with resources attached.",
  },
];

function Review({
  resume, setResume, uploaded, roles, roleId, setRoleId,
  busy, error, mode, setMode, jd, setJd, onRun, onBack,
}) {
  const tooShort = resume.trim().length < MIN_RESUME_CHARS;
  const jdTooShort = mode === "jd" && jd.trim().length < MIN_JD_CHARS;
  const role = roles.find((r) => r.id === roleId);

  return (
    <main className="wrap narrow review">
      <p className="eyebrow">Step 2 of 3</p>
      <div className="section-head">
        <h2>Check what we read</h2>
        <p>
          Edit anything that looks wrong before analysing — this is the whole
          reason the step exists.
        </p>
      </div>

      {uploaded && (
        <div className="notice">
          <strong>Read {uploaded.name}</strong> — {uploaded.pages} page
          {uploaded.pages === 1 ? "" : "s"}, {uploaded.chars} characters.
          <br />
          PDF extraction can interleave two-column layouts and scramble text
          inside tables, and there is no reliable way to detect when it has.
          {uploaded.warnings.map((w) => (
            <div key={w} className="warn">{w}</div>
          ))}
        </div>
      )}

      <label htmlFor="resume">Your resume text</label>
      <textarea
        id="resume"
        value={resume}
        onChange={(e) => setResume(e.target.value)}
        spellCheck={false}
        placeholder={
          "TECHNICAL SKILLS\nProgramming Languages: Python, Java, SQL\n" +
          "Databases: MySQL\nTools: Git, GitHub\n\nPROJECTS\n" +
          "Built a web application using Django and MySQL."
        }
      />
      <p className="hint">
        {resume.trim().length} characters
        {tooShort && resume.length > 0 && ` — need at least ${MIN_RESUME_CHARS}`}
      </p>

      <div className="modes">
        <button
          type="button"
          className={mode === "role" ? "on" : ""}
          onClick={() => setMode("role")}
        >
          Compare against a role
        </button>
        <button
          type="button"
          className={mode === "jd" ? "on" : ""}
          onClick={() => setMode("jd")}
        >
          Compare against one job description
        </button>
      </div>
      <p className="hint" style={{ marginTop: "-.6rem", marginBottom: "1rem" }}>
        {mode === "role"
          ? "Measures you against what thousands of postings for this role demand."
          : "Measures you against one specific posting — and tells you which of its requirements the wider market wants too."}
      </p>

      {mode === "jd" && (
        <div className="jd-box">
          <label htmlFor="jd">Paste the job description</label>
          <textarea
            id="jd"
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            spellCheck={false}
            placeholder={
              "We are hiring a Backend Engineer.\n\nRequirements:\n" +
              "- Strong Python and Django experience\n" +
              "- PostgreSQL and Redis\n- Docker for deployment\n" +
              "- Experience building REST APIs"
            }
          />
          <p className="hint">
            {jd.trim().length} characters
            {jdTooShort && jd.length > 0 && ` — need at least ${MIN_JD_CHARS}`}
          </p>
        </div>
      )}

      <div className="controls">
        <div>
          <label htmlFor="role">
            {mode === "role" ? "Target role" : "Role, for market context"}
          </label>
          <select
            id="role"
            value={roleId}
            onChange={(e) => setRoleId(e.target.value)}
          >
            {roles.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
        </div>
        <button onClick={onRun} disabled={busy || tooShort || jdTooShort || !roleId}>
          {busy ? "Analysing…" : "Analyse my gap"}
        </button>
        <button className="plain" onClick={onBack}>Start over</button>
      </div>

      {role && mode === "role" && (
        <p className="hint">
          Compared against {role.total_postings.toLocaleString()} real{" "}
          {role.name} postings from the {role.market} market.
        </p>
      )}

      {error && <div className="error">{error}</div>}
    </main>
  );
}

function SiteFooter() {
  return (
    <footer className="site">
      <div className="wrap">
        Demand measured from a frozen snapshot of Naukri postings, December
        2024. Extraction accuracy is hand-measured and the limitations are
        published —{" "}
        <a
          href="https://github.com/AnshulJJW/skill-gap-analyzer"
          target="_blank"
          rel="noreferrer noopener"
        >
          see the repository
        </a>
        .
      </div>
    </footer>
  );
}
