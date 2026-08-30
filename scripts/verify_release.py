"""One command that answers: would this work for somebody else?

    python scripts/verify_release.py

Three separate bugs shipped undetected because every check ran on the
development machine, which had accumulated a database, generated profiles
and packages installed as side-effects. Everything passed locally and the
repository was broken for anyone who cloned it.

This runs the checks that only fail for a stranger. Exit code is non-zero if
any of them do, so it can gate a deploy.

    --deep   also clone from GitHub into a temp directory, build a fresh
             virtual environment from requirements.txt alone, and run the
             suite there. Slower (a few minutes) and the only way to catch a
             missing dependency.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/AnshulJJW/skill-gap-analyzer.git"

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
results: list[tuple[str, str, str]] = []


def check(name: str, ok: bool, detail: str = "", warn_only: bool = False) -> bool:
    status = PASS if ok else (WARN if warn_only else FAIL)
    results.append((status, name, detail))
    return ok


def run(cmd: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          check=False)


def git(*args: str, cwd: Path = ROOT) -> str:
    return run(["git", *args], cwd=cwd).stdout.strip()


# --------------------------------------------------------------- repository


def check_repo() -> None:
    dirty = git("status", "--porcelain")
    check("working tree is clean", not dirty,
          f"{len(dirty.splitlines())} uncommitted files" if dirty else "")

    ahead = git("status", "-sb").splitlines()[0]
    check("in sync with the remote", "ahead" not in ahead and "behind" not in ahead,
          ahead)

    history = git("log", "--format=%B")
    ai = sum(history.lower().count(w) for w in ("claude", "anthropic", "co-authored-by"))
    check("no AI attribution in history", ai == 0, f"{ai} mentions found")

    authors = set(git("log", "--format=%an <%ae>").splitlines())
    check("single consistent author", len(authors) == 1, ", ".join(sorted(authors)))


# ------------------------------------------------------- privacy and secrets


def check_nothing_private_is_committed() -> None:
    tracked = git("ls-files").splitlines()

    resumes = [f for f in tracked if f.startswith("resumes/")
               and not f.endswith((".gitkeep", "example.txt"))]
    check("no personal resume committed", not resumes, ", ".join(resumes))

    secrets = [f for f in tracked
               if Path(f).name in {".env", "kaggle.json", "access_token"}]
    check("no credential files committed", not secrets, ", ".join(secrets))

    # a token pasted into a tracked file would be far worse than in history
    hits = run(["git", "grep", "-lI", "-E", "KGAT_[A-Za-z0-9]{20,}", "--", "."])
    check("no API token in tracked files", not hits.stdout.strip(),
          hits.stdout.strip())


# ----------------------------------------------------------- runnable clone


def check_clone_can_run() -> None:
    """Everything the app reads at startup must be tracked."""
    needed = ["data/skills.json", "data/stoplist.json", "data/roles.json",
              "data/prereqs.json", "data/resources.json", "data/implies.json"]
    missing = [f for f in needed if not git("ls-files", f)]
    check("runtime data files are tracked", not missing, ", ".join(missing))

    profiles = git("ls-files", "data/profiles").splitlines()
    check("role profiles are tracked", bool(profiles),
          f"{len(profiles)} profiles" if profiles else
          "the API loads these at startup -- a clone would serve nothing")

    for rel in profiles:
        raw = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        if not check(f"  {Path(rel).stem} has usable demand data",
                     raw.get("total_postings", 0) >= 250 and raw.get("demands")):
            break

    big = [f for f in ["data/raw", "data/skillgap.db"] if git("ls-files", f)]
    check("large rebuildable artefacts stay out of git", not big, ", ".join(big))


# ------------------------------------------------------------ code and docs


def check_code() -> None:
    py = sys.executable
    t = run([py, "-m", "pytest", "-q"])
    last = t.stdout.strip().splitlines()[-1] if t.stdout.strip() else "no output"
    check("test suite passes", t.returncode == 0, last)

    lint = run([py, "-m", "ruff", "check", "."])
    check("lint is clean", lint.returncode == 0,
          lint.stdout.strip().splitlines()[-1] if lint.stdout.strip() else "")

    stubs = run(["git", "grep", "-c", "raise NotImplementedError", "--",
                 "analyzer", "api", "eval"])
    check("no stubs left in shipped packages", not stubs.stdout.strip(),
          stubs.stdout.strip(), warn_only=True)


def check_docs_match_reality() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    check("README documents the install steps",
          "pip install -r requirements.txt" in readme)
    check("README states the measured results", "recall" in readme.lower())
    check("limitations section is written",
          "## Limitations" in readme and "<!--" not in
          readme.split("## Limitations")[1][:200])


# ------------------------------------------------------------- deep (clone)


def check_deep() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="sga-verify-"))
    try:
        c = run(["git", "clone", "--quiet", REPO_URL, str(tmp / "repo")], cwd=tmp)
        if not check("clone from GitHub", c.returncode == 0, c.stderr.strip()):
            return
        repo = tmp / "repo"

        v = run([sys.executable, "-m", "venv", str(repo / ".venv")], cwd=repo)
        if not check("create a fresh virtual environment", v.returncode == 0):
            return
        py = repo / ".venv" / "Scripts" / "python.exe"
        if not py.exists():
            py = repo / ".venv" / "bin" / "python"

        i = run([str(py), "-m", "pip", "install", "--quiet",
                 "-r", "requirements.txt"], cwd=repo)
        if not check("install from requirements.txt alone", i.returncode == 0,
                     i.stderr.strip()[-200:]):
            return

        t = run([str(py), "-m", "pytest", "-q"], cwd=repo)
        last = t.stdout.strip().splitlines()[-1] if t.stdout.strip() else ""
        check("tests pass in the clean environment", t.returncode == 0, last)

        smoke = (
            "import sys; sys.path.insert(0,'.')\n"
            "from fastapi.testclient import TestClient\n"
            "from api.main import app\n"
            "c = TestClient(app)\n"
            "c.__enter__()\n"
            "roles = c.get('/roles').json()\n"
            "assert roles, 'no roles'\n"
            # The schema enforces a 50-character minimum on resume_text. The
            # first version of this fixture was 45 characters, so the API
            # correctly returned 422 and the check reported a failure that
            # was the verifier's fault rather than the app's.
            "cv = ('TECHNICAL SKILLS'+chr(10)"
            "+'Languages: Python, Java, SQL'+chr(10)"
            "+'Databases: MySQL'+chr(10)+'Tools: Git'+chr(10)"
            "+'PROJECTS'+chr(10)+'Built a web application.'+chr(10))\n"
            "assert len(cv) >= 50, 'fixture is shorter than the schema allows'\n"
            "r = c.post('/analyze', json={'resume_text':cv,"
            "'role_id':roles[0]['id']})\n"
            "assert r.status_code == 200, r.status_code\n"
            "print(len(roles), round(r.json()['coverage'],3))\n"
        )
        s = run([str(py), "-c", smoke], cwd=repo)
        check("API answers in the clean environment", s.returncode == 0,
              s.stdout.strip() or s.stderr.strip()[-200:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deep", action="store_true",
                    help="clone from GitHub and build a fresh venv (slow)")
    args = ap.parse_args()

    check_repo()
    check_nothing_private_is_committed()
    check_clone_can_run()
    check_code()
    check_docs_match_reality()
    if args.deep:
        print("running deep checks (clone + fresh venv), this takes a few minutes...\n")
        check_deep()

    width = max(len(n) for _, n, _ in results) + 2
    for status, name, detail in results:
        mark = {PASS: "ok  ", FAIL: "FAIL", WARN: "warn"}[status]
        print(f"  {mark}  {name:<{width}}{detail}")

    failed = [n for s, n, _ in results if s == FAIL]
    print()
    if failed:
        print(f"{len(failed)} CHECK(S) FAILED: {', '.join(failed)}")
        return 1
    warned = sum(1 for s, _, _ in results if s == WARN)
    print(f"ALL {len(results)} CHECKS PASSED"
          + (f" ({warned} warning)" if warned else ""))
    if not args.deep:
        print("Run with --deep before a release to also test a clean install.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
