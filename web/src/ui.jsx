/* Shared primitives and icons.

   Kept in one file so the three views cannot drift into looking like three
   different products -- a button, a callout or a skill row is defined once
   and used everywhere.

   The icons are hand-drawn inline SVG on a 16-unit grid, stroked in
   currentColor. No icon font and no library: eight glyphs do not justify a
   dependency, and inline SVG inherits colour and size from its context for
   free. They are geometric on purpose -- an outline of the thing the control
   does, nothing illustrative. */

const S = {
  width: 16, height: 16, viewBox: "0 0 16 16", fill: "none",
  stroke: "currentColor", strokeWidth: 1.5,
  strokeLinecap: "round", strokeLinejoin: "round",
  "aria-hidden": true, focusable: false,
};

export const Icon = {
  upload: (p) => (
    <svg {...S} {...p}><path d="M8 10.5V2.5M8 2.5 5 5.5M8 2.5l3 3" /><path d="M2.5 10v2.5a1 1 0 0 0 1 1h9a1 1 0 0 0 1-1V10" /></svg>
  ),
  check: (p) => (
    <svg {...S} {...p}><circle cx="8" cy="8" r="6" /><path d="m5.5 8 1.8 1.8L10.5 6.5" /></svg>
  ),
  dash: (p) => (
    <svg {...S} {...p}><circle cx="8" cy="8" r="6" strokeDasharray="2 2" /></svg>
  ),
  info: (p) => (
    <svg {...S} {...p}><circle cx="8" cy="8" r="6" /><path d="M8 7.5v3M8 5.4v.2" /></svg>
  ),
  alert: (p) => (
    <svg {...S} {...p}><path d="M8 2.8 14 13H2L8 2.8Z" /><path d="M8 6.6v3M8 11.3v.2" /></svg>
  ),
  chevron: (p) => (
    <svg {...S} {...p}><path d="m6 4 4 4-4 4" /></svg>
  ),
  external: (p) => (
    <svg {...S} {...p}><path d="M6.5 3.5H3.2A.7.7 0 0 0 2.5 4.2v8.6a.7.7 0 0 0 .7.7h8.6a.7.7 0 0 0 .7-.7V9.5" /><path d="M9.5 2.5h4v4M13.5 2.5 7.5 8.5" /></svg>
  ),
  // Progress, not celebration -- used beside the supportive note.
  trend: (p) => (
    <svg {...S} {...p}><path d="M2.5 11.5 6 8l2.5 2.5 5-5" /><path d="M10 5.5h3.5V9" /></svg>
  ),
  target: (p) => (
    <svg {...S} {...p}><circle cx="8" cy="8" r="6" /><circle cx="8" cy="8" r="2.6" /></svg>
  ),
  list: (p) => (
    <svg {...S} {...p}><path d="M6 4.5h7.5M6 8h7.5M6 11.5h7.5M2.8 4.5h.2M2.8 8h.2M2.8 11.5h.2" /></svg>
  ),
  route: (p) => (
    <svg {...S} {...p}><circle cx="4" cy="4" r="1.8" /><circle cx="12" cy="12" r="1.8" /><path d="M4 5.8v3.4a2.8 2.8 0 0 0 2.8 2.8h3.4" /></svg>
  ),
  book: (p) => (
    <svg {...S} {...p}><path d="M2.5 3.5h4a2 2 0 0 1 2 2v8a1.6 1.6 0 0 0-1.6-1.6H2.5Z" /><path d="M13.5 3.5h-4a2 2 0 0 0-2 2v8a1.6 1.6 0 0 1 1.6-1.6h4.4Z" /></svg>
  ),
  file: (p) => (
    <svg {...S} {...p}><path d="M9 2.5H4.2a.7.7 0 0 0-.7.7v9.6a.7.7 0 0 0 .7.7h7.6a.7.7 0 0 0 .7-.7V6Z" /><path d="M9 2.5V6h3.5" /></svg>
  ),
};

export function Button({ variant, size, children, ...rest }) {
  const cls = ["btn", variant, size].filter(Boolean).join(" ");
  return <button className={cls} {...rest}>{children}</button>;
}

export function Callout({ tone, icon, children }) {
  const Ico = Icon[icon ?? (tone === "danger" ? "alert" : "info")];
  return (
    <div className={["callout", tone].filter(Boolean).join(" ")} role={tone === "danger" ? "alert" : undefined}>
      <span className="ico"><Ico /></span>
      <div>{children}</div>
    </div>
  );
}

/* Where you are in the flow. Labels are nouns, not instructions, so the rail
   reads the same whether you are looking forward or back. */
export function Flow({ step }) {
  const steps = ["Resume", "Check", "Results"];
  return (
    <div className="flow" aria-label={`Step ${step} of 3`}>
      {steps.map((label, i) => (
        <div key={label} style={{ display: "contents" }}>
          {i > 0 && <span className="bar" />}
          <span className={`dot ${i + 1 === step ? "now" : i + 1 < step ? "done" : ""}`}>
            <span className="pip" />
            {label}
          </span>
        </div>
      ))}
    </div>
  );
}

/* One skill, as a row: do you have it, and how much does the market want it.
   `share` is 0-1 and may be null when there is no market to compare against. */
export function SkillRow({ name, have, share }) {
  const pct = share == null ? null : Math.round(share * 100);
  return (
    <li className={`skill-row ${have ? "has" : "miss"}`}>
      <span className="state" title={have ? "On your resume" : "Not on your resume"}>
        {have ? <Icon.check className="have-ico" /> : <Icon.dash className="miss-ico" />}
      </span>
      <span className="name">{name}</span>
      {pct == null ? <span /> : (
        <span className="bar" aria-hidden="true"><i style={{ width: `${Math.max(pct, 2)}%` }} /></span>
      )}
      <span className="share">{pct == null ? "—" : `${pct}%`}</span>
    </li>
  );
}

export function Empty({ icon = "list", children }) {
  const Ico = Icon[icon];
  return (
    <div className="empty">
      <div className="ico"><Ico width={22} height={22} /></div>
      {children}
    </div>
  );
}

/* Shown while the analysis runs. Bars roughly the shape of the result they
   replace, so the layout does not jump when the real thing arrives. */
export function Loading({ label = "Working…" }) {
  return (
    <div className="busy" role="status" aria-live="polite">
      <span className="small muted">{label}</span>
      <div className="skeleton" style={{ width: "40%" }} />
      <div className="skeleton" style={{ width: "85%" }} />
      <div className="skeleton" style={{ width: "70%" }} />
    </div>
  );
}
