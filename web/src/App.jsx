import { useEffect, useRef, useState } from "react";
import { analyze, analyzeJD, getRoles, parseResume } from "./api.js";
import JDResults from "./JDResults.jsx";
import { useReveal } from "./motion.js";
import Results from "./Results.jsx";
import { Button, Callout, Flow, Icon } from "./ui.jsx";

const MIN_RESUME_CHARS = 50;
const MIN_JD_CHARS = 80;

/* Four screens driven by one state value rather than a router.
   The flow is linear and short, nothing is deep-linkable, and a router
   would add a dependency to manage three transitions.

   Landing takes the resume. Check is the safety step: PDF extraction
   scrambles two-column layouts and nothing reliably detects when it has, so
   the text is always shown before anything is measured. Results drops the
   marketing and shows only the answer. */
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

  useEffect(() => { window.scrollTo(0, 0); }, [view]);

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
      <Topbar onHome={reset} inFlow={view !== "landing"} />

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
          resume={resume} setResume={setResume}
          uploaded={uploaded}
          roles={roles} roleId={roleId} setRoleId={setRoleId}
          busy={busy} error={error}
          mode={mode} setMode={setMode}
          jd={jd} setJd={setJd}
          onRun={runAnalysis} onBack={reset}
        />
      )}

      {view === "jdresults" && (
        <JDResults report={jdReport} onEdit={() => setView("review")} onReset={reset} />
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
          error={error}
          onEdit={() => setView("review")}
          onReset={reset}
        />
      )}

      <SiteFooter />
    </>
  );
}

function Topbar({ onHome, inFlow }) {
  return (
    <header className="topbar">
      <div className="wrap inner">
        <button className="brand" onClick={onHome}>
          <span className="mark">SG</span>
          Skill-Gap Analyzer
        </button>
        <nav>
          {inFlow ? (
            <Button variant="quiet" onClick={onHome}>Start over</Button>
          ) : (
            <>
              <a href="#what">What you get</a>
              <a href="#how">How it works</a>
              <a href="#method">Accuracy</a>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

/* ------------------------------------------------------------------ landing */

function Landing({ roles, busy, error, fileInput, onFile, onPaste }) {
  const [dragging, setDragging] = useState(false);
  const postings = roles.reduce((n, r) => n + r.total_postings, 0);

  return (
    <main>
      <div className="wrap hero">
        <h1>Find the skills you need for the job you want.</h1>
        <p className="sub">
          Upload your resume. We compare it with real job postings and show
          you what to learn next.
        </p>

        <div className="facts">
          <div className="fact">
            <div className="v">{postings ? postings.toLocaleString() : "—"}</div>
            <div className="k">job postings</div>
          </div>
          <div className="fact">
            <div className="v">{roles.length || "—"}</div>
            <div className="k">roles</div>
          </div>
          <div className="fact">
            <div className="v">Free</div>
            <div className="k">no sign-up</div>
          </div>
        </div>

        <div
          className={`dropzone${dragging ? " over" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
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
          <div className="ico"><Icon.upload width={22} height={22} /></div>
          <h2>Drop your resume here</h2>
          <p>PDF only. Your file is not saved.</p>
          <Button size="lg" onClick={() => fileInput.current?.click()} disabled={busy}>
            {busy && <span className="spinner" />}
            {busy ? "Reading your PDF" : "Choose a file"}
          </Button>
          <div className="alt">
            or <button className="btn link" onClick={onPaste}>paste the text instead</button>
          </div>
        </div>

        {error && (
          <div style={{ marginTop: "1.25rem" }}>
            <Callout tone="danger">{error}</Callout>
          </div>
        )}
      </div>

      <section className="band" id="what" data-reveal>
        <div className="wrap">
          <div className="section-head">
            <h2>What you get</h2>
            <p>Every number comes from job postings you can check.</p>
          </div>
          <div className="grid-3">
            {WHAT.map((c) => {
              const Ico = Icon[c.icon];
              return (
                <div className="feature" key={c.title}>
                  <span className="ico"><Ico width={18} height={18} /></span>
                  <h3>{c.title}</h3>
                  <p>{c.body}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="band" id="how" data-reveal>
        <div className="wrap">
          <div className="section-head">
            <h2>How it works</h2>
            <p>Three steps. Nothing is stored.</p>
          </div>
          <div className="grid-3">
            {HOW.map((s, i) => (
              <div className="step" key={s.title}>
                <span className="n">{i + 1}</span>
                <div>
                  <h3>{s.title}</h3>
                  <p>{s.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="band" id="method" data-reveal>
        <div className="wrap">
          <div className="section-head">
            <h2>How accurate is it?</h2>
            <p>We measured it instead of asking you to trust it.</p>
          </div>
          <div className="grid-2">
            <div>
              <p className="muted" style={{ fontSize: ".9rem" }}>
                Someone read 40 job postings by hand and marked every skill in
                them — 255 in total — without seeing what the tool had found.
                We then scored the tool against those marks.
              </p>
              <div className="facts" style={{ marginTop: "1.25rem" }}>
                <div className="fact">
                  <div className="v">0.86</div>
                  <div className="k">precision</div>
                </div>
                <div className="fact">
                  <div className="v">0.90</div>
                  <div className="k">recall</div>
                </div>
              </div>
            </div>
            <div>
              <p className="muted" style={{ fontSize: ".9rem" }}>
                That check also caught about one posting in six filed under the
                wrong job title. Those are now removed rather than quietly
                counted.
              </p>
              <p className="muted" style={{ fontSize: ".9rem", marginTop: ".8rem" }}>
                Postings come from a fixed Naukri snapshot, so the numbers
                describe entry-level hiring in India.{" "}
                <a href={REPO} target="_blank" rel="noreferrer noopener">
                  Full method and limits
                </a>
                .
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

const REPO = "https://github.com/AnshulJJW/skill-gap-analyzer";

const WHAT = [
  {
    icon: "target",
    title: "Your score",
    body: "How many of the skills this role asks for most are already on your resume.",
  },
  {
    icon: "list",
    title: "What we found",
    body: "Every skill we read from your resume, so you can spot anything we got wrong.",
  },
  {
    icon: "trend",
    title: "What to learn first",
    body: "The skill that opens the most jobs you currently miss out on — not just the most common one.",
  },
  {
    icon: "route",
    title: "In a sensible order",
    body: "Basics before advanced. It will not tell you to learn Kubernetes before Docker.",
  },
  {
    icon: "book",
    title: "Free links",
    body: "One free resource per skill, with a rough time to finish.",
  },
  {
    icon: "info",
    title: "The evidence",
    body: "Each result shows how many postings it came from, so you can judge it yourself.",
  },
];

const HOW = [
  { title: "Add your resume", body: "Upload a PDF or paste the text." },
  { title: "Check the text", body: "PDFs often come out scrambled. Fix anything wrong before we measure." },
  { title: "See your gap", body: "Your score, what to learn, and where to learn it." },
];

/* ------------------------------------------------------------------- check */

function Review({
  resume, setResume, uploaded, roles, roleId, setRoleId,
  busy, error, mode, setMode, jd, setJd, onRun, onBack,
}) {
  const tooShort = resume.trim().length < MIN_RESUME_CHARS;
  const jdTooShort = mode === "jd" && jd.trim().length < MIN_JD_CHARS;
  const role = roles.find((r) => r.id === roleId);

  return (
    <main className="wrap sm view">
      <Flow step={2} />

      <div className="section-head">
        <h2>Check the text</h2>
        <p>Fix anything that looks wrong. We measure exactly what is here.</p>
      </div>

      <div className="stack-lg">
        {uploaded && (
          <Callout icon="file">
            <strong>{uploaded.name}</strong> — {uploaded.pages} page
            {uploaded.pages === 1 ? "" : "s"}, {uploaded.chars} characters.
            <div style={{ marginTop: ".3rem" }}>
              PDFs with two columns or tables often come out jumbled, and there
              is no reliable way to detect it.
            </div>
            {uploaded.warnings.map((w) => (
              <div key={w} style={{ marginTop: ".5rem", color: "var(--warn)" }}>{w}</div>
            ))}
          </Callout>
        )}

        <div>
          <label htmlFor="resume">Your resume text</label>
          <textarea
            id="resume"
            value={resume}
            onChange={(e) => setResume(e.target.value)}
            spellCheck={false}
            placeholder={"TECHNICAL SKILLS\nLanguages: Python, Java, SQL\nDatabases: MySQL\nTools: Git\n\nPROJECTS\nBuilt a web app with Django and MySQL."}
          />
          <div className="field-foot">
            <span>{tooShort && resume.length > 0 ? `Need at least ${MIN_RESUME_CHARS} characters` : ""}</span>
            <span className="mono">{resume.trim().length}</span>
          </div>
        </div>

        <div>
          <label>Compare against</label>
          <div className="segmented" role="group">
            <button
              type="button"
              className={mode === "role" ? "on" : ""}
              onClick={() => setMode("role")}
            >
              A role
            </button>
            <button
              type="button"
              className={mode === "jd" ? "on" : ""}
              onClick={() => setMode("jd")}
            >
              One job posting
            </button>
          </div>
          <p className="small muted" style={{ marginTop: ".55rem" }}>
            {mode === "role"
              ? "Measures you against thousands of postings for this role."
              : "Measures you against one posting, and shows which of its asks the wider market shares."}
          </p>
        </div>

        {mode === "jd" && (
          <div>
            <label htmlFor="jd">Paste the job posting</label>
            <textarea
              id="jd"
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              spellCheck={false}
              style={{ minHeight: "10rem" }}
              placeholder={"We are hiring a Backend Engineer.\n\nRequirements:\n- Strong Python and Django\n- PostgreSQL and Redis\n- Docker\n- REST APIs"}
            />
            <div className="field-foot">
              <span>{jdTooShort && jd.length > 0 ? `Need at least ${MIN_JD_CHARS} characters` : ""}</span>
              <span className="mono">{jd.trim().length}</span>
            </div>
          </div>
        )}

        <div>
          <label htmlFor="role">
            {mode === "role" ? "Target role" : "Role, for market context"}
          </label>
          <select id="role" value={roleId} onChange={(e) => setRoleId(e.target.value)}>
            {roles.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
          {role && mode === "role" && (
            <p className="small muted" style={{ marginTop: ".45rem" }}>
              {role.total_postings.toLocaleString()} postings, {role.market} market.
            </p>
          )}
        </div>

        {error && <Callout tone="danger">{error}</Callout>}

        <div className="actions">
          <Button onClick={onRun} disabled={busy || tooShort || jdTooShort || !roleId}>
            {busy && <span className="spinner" />}
            {busy ? "Analysing" : "See my results"}
          </Button>
          <span className="spacer" />
          <Button variant="quiet" onClick={onBack}>Start over</Button>
        </div>
      </div>
    </main>
  );
}

function SiteFooter() {
  return (
    <footer className="site">
      <div className="wrap">
        Job postings from a fixed Naukri snapshot, December 2024. Accuracy is
        measured by hand and the limits are written down —{" "}
        <a href={REPO} target="_blank" rel="noreferrer noopener">see the repository</a>.
      </div>
    </footer>
  );
}
