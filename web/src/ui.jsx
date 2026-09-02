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
  spark: (p) => (
    <svg {...S} {...p}><path d="M8 2.5 9.4 6.6 13.5 8 9.4 9.4 8 13.5 6.6 9.4 2.5 8l4.1-1.4Z" /></svg>
  ),
  layers: (p) => (
    <svg {...S} {...p}><path d="M8 2.5 14 5.5 8 8.5 2 5.5 8 2.5Z" /><path d="m2 8.5 6 3 6-3" /></svg>
  ),
  shield: (p) => (
    <svg {...S} {...p}><path d="M8 2.2 13 4v4c0 3-2.2 5-5 5.8C5.2 13 3 11 3 8V4l5-1.8Z" /></svg>
  ),
};

/* The score ring.

   An SVG arc rather than a conic gradient: stroke-dashoffset animates
   smoothly, takes a round cap, and can carry a gradient along its length.
   `value` is 0-100 and comes from useCountUp, so the arc and the digits in
   the middle advance on the same number. */
export function Ring({ value, label = "covered", size = 118, stroke = 10 }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - Math.min(Math.max(value, 0), 100) / 100);
  const id = `ringGrad-${label.replace(/\W/g, "")}`;

  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} aria-hidden="true">
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--brand-light)" />
            <stop offset="100%" stopColor="var(--brand)" />
          </linearGradient>
        </defs>
        <circle className="track" cx={size / 2} cy={size / 2} r={r}
                fill="none" strokeWidth={stroke} />
        <circle className="fill" cx={size / 2} cy={size / 2} r={r}
                fill="none" strokeWidth={stroke} stroke={`url(#${id})`}
                strokeDasharray={c} strokeDashoffset={offset} />
      </svg>
      <div className="mid">
        <div>
          <div className="v">{value}%</div>
          <div className="l">{label}</div>
        </div>
      </div>
    </div>
  );
}

export function Tile({ tone, value, label }) {
  return (
    <div className={["tile", tone].filter(Boolean).join(" ")}>
      <div className="v">{value}</div>
      <div className="k">{label}</div>
    </div>
  );
}

/* A bar that animates from zero once mounted. `mounted` comes from
   useMounted: rendering the final width on the first paint would just draw
   it there with nothing to transition from. */
export function Bar({ pct, tone, mounted = true }) {
  return (
    <span className={["bar", tone].filter(Boolean).join(" ")} aria-hidden="true">
      <i style={{ width: mounted ? `${Math.max(pct, 2)}%` : 0 }} />
    </span>
  );
}

/* One gap, as a card.

   Priority is the position in the ranked list, which is what the ranking
   already means -- the first few are the ones that unlock the most postings
   you currently fail. It is not a separate judgement invented for display.

   There is deliberately no "your level vs required level": the analyzer
   knows whether a skill is present, not how good you are at it, and drawing
   a proficiency bar would be inventing a measurement. */
export function GapCard({ rank, name, category, share, gain, mounted }) {
  const p = rank === 0 ? "p1" : rank < 3 ? "p2" : "";
  const badge = rank === 0 ? "Start here" : rank < 3 ? "High impact" : null;
  const pct = share == null ? null : Math.round(share * 100);

  return (
    <li className={["gap-card", p].filter(Boolean).join(" ")} data-stagger>
      <div className="gap-top">
        <div>
          <div className="gap-name">{name}</div>
          {category && <div className="gap-cat">{category}</div>}
        </div>
        {badge && <span className={`gap-badge ${p}`}>{badge}</span>}
      </div>
      {pct != null && (
        <div className="gap-meter">
          <div className="lab">
            <span>Asked for in <b>{pct}%</b> of postings</span>
            {gain != null && <span>+{(gain * 100).toFixed(1)}% score</span>}
          </div>
          <Bar pct={pct} tone={rank === 0 ? "warn" : undefined} mounted={mounted} />
        </div>
      )}
    </li>
  );
}

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
      {pct == null ? <span /> : <Bar pct={pct} tone={have ? "ok" : undefined} />}
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
