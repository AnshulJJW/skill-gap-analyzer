# How to run and debug this project

Written for someone who has not done this before. Nothing here can break
anything permanently — the database is rebuilt from CSV files by one command.

---

## 1. Open a terminal in the right place

In VS Code press **Ctrl + `** (the backtick key, above Tab, left of 1). A
panel opens at the bottom. It is already pointed at the project folder, which
matters — commands only work from there.

You should see a prompt ending in `skill-gap-analyzer>`.

## 2. Turn on the virtual environment

```
.venv\Scripts\activate
```

Your prompt now starts with `(.venv)`. That means Python will use *this
project's* libraries rather than whatever else is on your laptop.

**Do this every time you open a new terminal.** If a command fails with
`ModuleNotFoundError: No module named 'pandas'`, you forgot this step. That
is the single most common beginner error and it means nothing is wrong.

## 3. Commands that work right now

```
python scripts/explore.py                  what is in the database
python scripts/explore.py roles            posting counts per role
python scripts/explore.py skills backend   top employer-named skills
python scripts/explore.py show backend     one full posting, as stored
python scripts/explore.py find kafka       how many postings mention a word
python scripts/load_db.py                  rebuild the database from scratch
python scripts/build_interview_doc.py      regenerate the interview prep doc
```

`explore.py` is read-only. Run it as much as you like.

`load_db.py` deletes and rebuilds the postings table, which takes about a
minute. Safe to re-run any time — it always reads from the CSV files in
`data/raw/`, so the result is identical.

### Ask the database your own questions

```
python scripts/explore.py sql "SELECT title, company FROM postings LIMIT 5"
```

Useful for practising SQL, and SQL comes up in interviews.

---

## 4. How to read an error

When something breaks Python prints a **traceback**. It looks alarming. It is
not. Two rules:

**Read the LAST line first.** That is the actual error. Everything above it
is just the path the program took to get there.

```
  File "scripts\load_db.py", line 88, in load_naukri
    df = df[years <= cfg["entry_level_max_years"]]
KeyError: 'entry_level_max_years'
```

The last line is the error: a key that does not exist. The line above tells
you where: `load_db.py` line 88. Open that line and look.

**Common ones and what they mean:**

| Error | Means |
|---|---|
| `ModuleNotFoundError` | Virtual environment not activated (step 2) |
| `FileNotFoundError` | A file is missing, or you are in the wrong folder |
| `KeyError: 'x'` | Asked for a column or key that does not exist |
| `TypeError: ... NoneType` | Something was empty when you expected a value |
| `IndentationError` | Spacing is wrong — Python cares about indentation |

---

## 5. How to actually debug

### The simple way: print

Add a line to see what a variable holds:

```python
print("ROWS NOW:", len(df))
print("COLUMNS:", list(df.columns))
```

Unglamorous, and professionals use it constantly. `load_db.py` is built this
way on purpose — it prints the row count at every step, so when a number
looks wrong you can see exactly which step caused it.

### The better way: the VS Code debugger

Lets you pause the program mid-run and inspect everything.

1. Open a file, e.g. `scripts/load_db.py`
2. Click just left of a line number — a **red dot** appears. That is a
   breakpoint.
3. Press **F5**, then choose "Python File" if asked
4. The program runs and freezes at your red dot
5. The **Variables** panel on the left shows every value at that moment
6. **F10** runs the next line, **F5** continues to the end

Put a breakpoint inside `clean_html` and you can watch a messy HTML job
description turn into clean text, one step at a time.

### The exploratory way: the Python shell

```
python
```

Then type Python directly:

```python
>>> from analyzer.db import get_engine
>>> from sqlalchemy import text
>>> e = get_engine()
>>> with e.connect() as c:
...     print(c.execute(text("SELECT COUNT(*) FROM postings")).scalar())
```

`exit()` to leave. Good for trying one thing without editing a file.

---

## 6. If something goes badly wrong

Every change is saved in Git, so nothing is ever really lost.

```
git status                 what you have changed
git diff                   the exact changes, line by line
git checkout -- <file>     throw away your changes to one file
git log --oneline          the history of every saved checkpoint
```

To rebuild the database if it looks wrong:

```
python scripts/load_db.py
```

---

## 7. Running the whole app

Two terminals, both with the virtual environment turned on (section 2).

**Terminal 1 — the backend:**

```
python -m uvicorn api.main:app --reload --port 8000
```

Leave it running. Check it with http://127.0.0.1:8000/docs — that page lists
every route and lets you try each one without the frontend.

**Terminal 2 — the frontend:**

```
cd web
npm install     (first time only)
npm run dev
```

Open http://localhost:5173. The frontend calls the backend, so if the first
terminal is not running you will see "Failed to fetch".

### If the backend seems to ignore your changes

`--reload` restarts the server when a file changes, but if the reloader is
killed without its worker, the old worker keeps the port and keeps serving
the OLD code. Symptom: a route you just added returns 404 while
`/docs` shows the old list. Fix — find what is really holding the port:

```
python -c "import urllib.request,json; print(list(json.load(urllib.request.urlopen('http://127.0.0.1:8000/openapi.json'))['paths']))"
```

If that list is missing your new route, stop every stray Python process and
start the server again. This cost an hour once; it is not your code.

### The two analysis modes

Both start from the same resume text, and both are reachable from the one
page:

- **Compare against a role** — scores you against thousands of postings and
  ranks gaps by marginal coverage.
- **Compare against one job description** — paste a single posting; each of
  its requirements is annotated with how often the wider market asks for it
  too, so you can tell a real gap from this employer's quirk.

## 8. What is NOT built yet

Stages 7 and 8: deployment, and the demo write-up. Everything described
above runs locally today.

## 9. Deploying

Two services, both on free tiers, both fed from this GitHub repository.

```
   GitHub (AnshulJJW/skill-gap-analyzer)
        |                        |
        | root dir: web/         | root dir: repo root
        v                        v
   Vercel  ──── HTTPS ────>  Render
   static bundle            FastAPI + uvicorn
   (dist/)                  reads data/*.json into memory at startup
```

The API is stateless. It loads the taxonomy and the precomputed role profiles
from `data/` at boot and serves everything from memory, so there is no
database to attach and no disk to persist.

### Backend, on Render

`render.yaml` in the repo root describes the service. Render reads it when you
create a Blueprint from the repository, so the build command, start command
and health check do not need typing into a form.

It installs `requirements-api.txt`, not `requirements.txt`. The server imports
neither pandas, SQLAlchemy nor psycopg -- those belong to the data pipeline
that runs offline -- and leaving them out is the difference between a short
build and a slow one on a free instance.

### Frontend, on Vercel

Root directory `web`. `VITE_API_URL` is read at BUILD time, not at runtime, so
changing it requires a redeploy rather than a restart.

### The one ordering constraint

The frontend needs the API's URL, and the API needs the frontend's origin for
CORS. So: deploy the API first, build the frontend against it, then set
`CORS_ORIGINS` on the API to the Vercel URL and let it restart.

### Redeploying

Push to `main`. Both services rebuild automatically. If you change
`VITE_API_URL` or `CORS_ORIGINS`, the service that owns it must redeploy --
for Vercel that means a fresh build, because the value is compiled in.
