"""Stage 5 gate -- cold start and resident memory, measured.

    python scripts/measure_api.py

Render's free tier gives 512MB and spins the instance down after inactivity,
so the first request after a quiet period pays the full startup cost. A
60-second blank screen in front of a recruiter is the failure this guards
against.

GATE: cold start under 10s, resident memory under 400MB, warm request under
500ms. Exits non-zero on failure so it can gate a deploy.

Measured on a real /analyze call with a real resume, not on an empty request
-- an empty request would skip the extraction path entirely and report a
number that means nothing.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
MAX_COLD_START_S = 10.0
MAX_RSS_MB = 400.0
MAX_WARM_MS = 500.0


def rss_mb() -> float:
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    except ImportError:
        # Windows fallback without psutil
        import ctypes
        import ctypes.wintypes as w

        class PMC(ctypes.Structure):
            _fields_ = [("cb", w.DWORD), ("PageFaultCount", w.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]
        c = PMC()
        c.cb = ctypes.sizeof(c)
        ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb)
        return c.WorkingSetSize / 1024 / 1024


def main() -> int:
    baseline = rss_mb()

    t0 = time.perf_counter()
    from fastapi.testclient import TestClient

    from api.main import app
    import_s = time.perf_counter() - t0

    resume_path = ROOT / "resumes" / "me.txt"
    resume = (resume_path.read_text(encoding="utf-8")
              if resume_path.exists()
              else "TECHNICAL SKILLS\nPython, Java, SQL, MySQL, Git\n" * 3)

    t0 = time.perf_counter()
    with TestClient(app) as client:
        startup_s = time.perf_counter() - t0

        t0 = time.perf_counter()
        first = client.post("/analyze", json={
            "resume_text": resume, "role_id": "sde1-backend"})
        first_ms = (time.perf_counter() - t0) * 1000
        first.raise_for_status()

        warm = []
        for _ in range(20):
            t0 = time.perf_counter()
            client.post("/analyze", json={
                "resume_text": resume, "role_id": "sde1-backend"})
            warm.append((time.perf_counter() - t0) * 1000)

        loaded = rss_mb()

    warm.sort()
    cold_total = import_s + startup_s + first_ms / 1000

    print(f"{'':<26}{'measured':>12}{'budget':>10}")
    print("-" * 50)
    rows = [
        ("import api.main", f"{import_s:.2f}s", ""),
        ("app startup (lifespan)", f"{startup_s:.2f}s", ""),
        ("first /analyze", f"{first_ms:.0f}ms", ""),
        ("COLD START TOTAL", f"{cold_total:.2f}s", f"{MAX_COLD_START_S:.0f}s"),
        ("warm /analyze (median)", f"{warm[len(warm)//2]:.0f}ms", f"{MAX_WARM_MS:.0f}ms"),
        ("warm /analyze (p95)", f"{warm[int(len(warm)*0.95)]:.0f}ms", ""),
        ("resident memory", f"{loaded:.0f}MB", f"{MAX_RSS_MB:.0f}MB"),
        ("  of which baseline", f"{baseline:.0f}MB", ""),
    ]
    for label, value, budget in rows:
        print(f"{label:<26}{value:>12}{budget:>10}")

    failures = []
    if loaded <= 1.0:
        failures.append(
            "memory measurement returned 0MB, which cannot be right -- a "
            "broken measurement must fail rather than silently pass")
    if cold_total > MAX_COLD_START_S:
        failures.append(f"cold start {cold_total:.1f}s > {MAX_COLD_START_S}s")
    if loaded > MAX_RSS_MB:
        failures.append(f"memory {loaded:.0f}MB > {MAX_RSS_MB}MB")
    if warm[len(warm) // 2] > MAX_WARM_MS:
        failures.append(f"warm request {warm[len(warm)//2]:.0f}ms > {MAX_WARM_MS}ms")

    print()
    if failures:
        print("GATE FAILED: " + "; ".join(failures))
        return 1
    print("GATE PASSED  cold start, memory and warm latency all within budget")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
