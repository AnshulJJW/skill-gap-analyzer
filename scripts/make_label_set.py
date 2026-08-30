"""Stage 3 -- build the hand-labelling set and its tool.

    python scripts/make_label_set.py

Samples 40 postings, stratified by role, and writes a self-contained HTML
page you open in a browser to label them. Progress saves in the browser as
you go, so it can be done in several sittings.

On bias: the tool shows the FULL taxonomy as checkboxes, never a pre-filled
guess from our own extractor. Pre-selecting the extractor's answers would
make the labeller agree with it and inflate recall -- the measurement would
then be of nothing at all.

The honest limitation this leaves: a skill absent from the taxonomy cannot be
labelled, so we measure how well the extractor finds skills it knows about,
not how complete the taxonomy is. Taxonomy coverage is a separate question,
and it is recorded in the results rather than hidden.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer.db import get_engine, postings, provided_skills
from analyzer.taxonomy import Taxonomy

ROOT = Path(__file__).resolve().parent.parent
OUT_HTML = ROOT / "eval" / "label.html"
OUT_SAMPLE = ROOT / "eval" / "sample.json"

SEED = 42
QUOTA = {"sde1-backend": 20, "frontend": 12, "data-analyst": 8}

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Label 40 postings</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#15181f;--mid:#5a6070;--soft:#8b91a3;
--line:#e0e3ea;--acc:#1f5d8c;--accw:#e3eef6;--ok:#1c7a4a;--warn:#9a5b12}
@media(prefers-color-scheme:dark){:root{--bg:#101319;--card:#181c24;--ink:#e8eaf0;
--mid:#a4abbb;--soft:#7c8398;--line:#282d38;--acc:#7fb4dd;--accw:#152634;
--ok:#5fc38e;--warn:#d9a24e}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.6 "Segoe UI",system-ui,sans-serif}
header{position:sticky;top:0;z-index:9;background:var(--card);
border-bottom:1px solid var(--line);padding:.7rem 1rem;
display:flex;gap:1rem;align-items:center;flex-wrap:wrap}
header b{font-size:1rem}
.bar{flex:1;height:7px;background:var(--line);border-radius:4px;
overflow:hidden;min-width:120px}
.bar i{display:block;height:100%;background:var(--acc);width:0}
button{font:inherit;padding:.4rem .85rem;border-radius:5px;
border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
button.p{background:var(--acc);color:#fff;border-color:var(--acc);font-weight:600}
button:disabled{opacity:.4;cursor:not-allowed}
main{display:grid;grid-template-columns:1fr;gap:1rem;padding:1rem;
max-width:1400px;margin:0 auto}
@media(min-width:1000px){main{grid-template-columns:1fr 1fr}}
.card{background:var(--card);border:1px solid var(--line);
border-radius:8px;padding:1rem}
.meta{font-size:.8rem;color:var(--soft);margin-bottom:.5rem}
h2{margin:.1rem 0 .6rem;font-size:1.05rem}
pre.jd{white-space:pre-wrap;font:inherit;color:var(--mid);
max-height:46vh;overflow:auto;margin:0;
border-top:1px solid var(--line);padding-top:.7rem}
.tags{margin-top:.7rem;font-size:.78rem;color:var(--soft);
border-top:1px dashed var(--line);padding-top:.5rem}
input[type=search]{width:100%;padding:.5rem .7rem;border-radius:5px;
border:1px solid var(--line);background:var(--bg);color:var(--ink);
font:inherit;margin-bottom:.7rem}
.cat{font-size:.68rem;text-transform:uppercase;letter-spacing:.09em;
color:var(--soft);margin:.8rem 0 .35rem;font-weight:700}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.15rem}
label.s{display:flex;gap:.4rem;align-items:center;padding:.25rem .35rem;
border-radius:4px;cursor:pointer;font-size:.87rem}
label.s:hover{background:var(--accw)}
label.s.on{background:var(--accw);color:var(--acc);font-weight:600}
.picked{min-height:1.6rem;display:flex;flex-wrap:wrap;gap:.3rem;margin-bottom:.6rem}
.chip{background:var(--accw);color:var(--acc);border-radius:99px;
padding:.1rem .55rem;font-size:.78rem;font-weight:600}
.done{color:var(--ok);font-weight:600}
#out{width:100%;height:130px;font:12px monospace;margin-top:.6rem;
border:1px solid var(--line);border-radius:5px;background:var(--bg);
color:var(--ink);padding:.5rem;display:none}
.hint{font-size:.82rem;color:var(--soft);margin:.4rem 0 0}
</style></head><body>
<header>
  <b id="pos">1 / 40</b>
  <div class="bar"><i id="prog"></i></div>
  <span id="cnt" class="meta"></span>
  <button id="prev">&larr; Prev</button>
  <button id="next" class="p">Next &rarr;</button>
  <button id="save">Save file</button>
</header>
<main>
  <div class="card">
    <div class="meta" id="meta"></div>
    <h2 id="title"></h2>
    <pre class="jd" id="jd"></pre>
    <div class="tags" id="tags"></div>
  </div>
  <div class="card">
    <div class="picked" id="picked"></div>
    <input type="search" id="find" placeholder="Filter skills...">
    <div id="skills"></div>
    <p class="hint">Tick every skill this posting genuinely asks for. Ignore
    job titles and vague words. If unsure, leave it off &mdash; a wrong tick
    hurts the measurement more than a missed one.</p>
    <textarea id="out" readonly></textarea>
  </div>
</main>
<script>
const POSTINGS = __POSTINGS__, SKILLS = __SKILLS__;
const KEY = "sga_labels_v1";
let i = 0, labels = JSON.parse(localStorage.getItem(KEY) || "{}");

const byCat = {};
SKILLS.forEach(s => (byCat[s.category] ||= []).push(s));

function save(){ try{ localStorage.setItem(KEY, JSON.stringify(labels)); }catch(e){} }

function renderSkills(){
  const q = document.getElementById("find").value.toLowerCase();
  const cur = new Set(labels[POSTINGS[i].id] || []);
  let h = "";
  for(const cat of Object.keys(byCat).sort()){
    const list = byCat[cat].filter(s => !q || s.name.toLowerCase().includes(q) || s.id.includes(q));
    if(!list.length) continue;
    h += `<div class="cat">${cat}</div><div class="grid">`;
    for(const s of list){
      const on = cur.has(s.id);
      h += `<label class="s${on?" on":""}"><input type="checkbox" data-id="${s.id}"${on?" checked":""}>${s.name}</label>`;
    }
    h += `</div>`;
  }
  document.getElementById("skills").innerHTML = h;
  document.getElementById("picked").innerHTML =
    [...cur].map(id => `<span class="chip">${(SKILLS.find(s=>s.id===id)||{}).name||id}</span>`).join("")
    || `<span class="meta">nothing ticked yet</span>`;
}

function render(){
  const p = POSTINGS[i];
  document.getElementById("pos").textContent = `${i+1} / ${POSTINGS.length}`;
  document.getElementById("meta").textContent =
    `${p.role}  ·  ${p.company||"—"}  ·  ${p.location||"—"}  ·  ${p.experience||"—"}`;
  document.getElementById("title").textContent = p.title;
  document.getElementById("jd").textContent = p.description;
  document.getElementById("tags").textContent = "employer tags: " + (p.tags || "none");
  document.getElementById("prog").style.width =
    (100*Object.keys(labels).length/POSTINGS.length) + "%";
  const n = Object.keys(labels).length;
  const c = document.getElementById("cnt");
  c.textContent = `${n} of ${POSTINGS.length} labelled`;
  c.className = n >= POSTINGS.length ? "done" : "meta";
  document.getElementById("prev").disabled = i === 0;
  document.getElementById("next").disabled = i === POSTINGS.length - 1;
  renderSkills();
}

document.getElementById("skills").addEventListener("change", e => {
  const id = e.target.dataset.id; if(!id) return;
  const pid = POSTINGS[i].id;
  const set = new Set(labels[pid] || []);
  e.target.checked ? set.add(id) : set.delete(id);
  labels[pid] = [...set];
  save(); render();
});
document.getElementById("find").addEventListener("input", renderSkills);
document.getElementById("prev").onclick = () => { if(i>0){ i--; render(); } };
document.getElementById("next").onclick = () => { if(i<POSTINGS.length-1){ i++; render(); } };
document.addEventListener("keydown", e => {
  if(e.target.tagName === "INPUT") return;
  if(e.key === "ArrowRight") document.getElementById("next").click();
  if(e.key === "ArrowLeft") document.getElementById("prev").click();
});

document.getElementById("save").onclick = () => {
  const payload = {
    _note: "Stage 3 hand labels. Ground truth for precision/recall.",
    labelled: Object.keys(labels).length,
    total: POSTINGS.length,
    cases: POSTINGS.map(p => ({ id: p.id, role: p.role, skills: (labels[p.id]||[]).sort() }))
  };
  const text = JSON.stringify(payload, null, 2);
  const blob = new Blob([text], {type:"application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "labels.json";
  document.body.appendChild(a); a.click(); a.remove();
  const out = document.getElementById("out");
  out.style.display = "block"; out.value = text; out.select();
};
render();
</script></body></html>
"""


def main() -> int:
    random.seed(SEED)
    tax = Taxonomy.load()
    engine = get_engine()

    with engine.connect() as conn:
        chosen = []
        for role, quota in QUOTA.items():
            rows = conn.execute(
                select(postings.c.id, postings.c.title, postings.c.company,
                       postings.c.location, postings.c.experience,
                       postings.c.description, postings.c.role_id)
                .where(postings.c.role_id == role)
            ).all()
            # Long enough to actually contain skills; the tiniest postings
            # would make the measurement look artificially easy.
            rows = [r for r in rows if len(r.description) >= 200]
            chosen += random.sample(rows, min(quota, len(rows)))

        tags: dict[int, list[str]] = {}
        for pid, tag in conn.execute(
            select(provided_skills.c.posting_id, provided_skills.c.raw_skill)
            .where(provided_skills.c.posting_id.in_([r.id for r in chosen]))
        ):
            tags.setdefault(pid, []).append(tag)

    sample = [{
        "id": r.id, "role": r.role_id, "title": r.title,
        "company": r.company, "location": r.location,
        "experience": r.experience, "description": r.description,
        "tags": ", ".join(sorted(tags.get(r.id, []))),
    } for r in chosen]

    skills = sorted(
        ({"id": s.id, "name": s.name, "category": s.category}
         for s in tax.skills.values()),
        key=lambda s: (s["category"], s["name"].lower()),
    )

    OUT_SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    OUT_SAMPLE.write_text(json.dumps(sample, indent=2), encoding="utf-8")

    html = (PAGE
            .replace("__POSTINGS__", json.dumps(sample))
            .replace("__SKILLS__", json.dumps(skills)))
    OUT_HTML.write_text(html, encoding="utf-8")

    print(f"sampled {len(sample)} postings (seed {SEED})")
    for role, quota in QUOTA.items():
        got = sum(1 for s in sample if s["role"] == role)
        print(f"  {role:<16} {got:>3} / {quota}")
    print(f"\nlabelling tool : {OUT_HTML}")
    print(f"sample record  : {OUT_SAMPLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
