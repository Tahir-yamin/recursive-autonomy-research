# BL-06 — MSR Research Engineer Critiques

**Priority:** 🟠 P1
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** D | Verdict: Fail

---

## Issue 6.1 — 14 Tooling Scripts Have Hardcoded Windows Absolute Paths
**Files:** patch_and_update.py, fix_appendix.py, append_logs.py,
inject_results.py, clean_unicode_comments.py, add_appendix.py,
search_text.py, update_all_paper_assets.py, update_appendix.py,
update_full_appendix.py, update_listings.py, update_manuscript.py,
update_manuscript_clean.py, update_plan.py
**Evidence:** All contain `r"C:\Users\Administrator\..."` or similar.

**Fix:** In each script, replace the hardcoded root with:
```python
import os
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
```
Then reference all paths relative to `PROJECT_ROOT`.

**Acceptance criteria:**
- [ ] `grep -r "C:\\\\Users" *.py` returns zero hits
- [ ] `grep -r "D:\\\\.*Administrator" *.py` returns zero hits

---

## Issue 6.2 — WAL Retry-Backoff Silently Swallows Final Failure (DATA LOSS)
**File:** run_pilot_experiment.py:284–299
**Evidence:** After 5 failed `os.replace` attempts, the code prints
an error then the `finally` block deletes `tmp_file` and returns
normally. The WAL write is silently lost with no exception raised.
Paper claims "100% task recoverability."

**Fix:**
```python
for attempt in range(5):
    try:
        os.replace(tmp_file, wal_file)
        return  # success
    except (PermissionError, OSError) as e:
        if attempt < 4:
            delay = 0.1 * (2 ** attempt) + random.uniform(0, 0.05)
            log.warning(f"WAL replace attempt {attempt+1} failed: {e}. "
                       f"Retrying in {delay:.2f}s...")
            time.sleep(delay)
        else:
            log.error(f"WAL WRITE FAILED after 5 attempts: {e}. "
                     f"State for cycle {cycle} may be lost.")
            raise  # do NOT silently swallow
```
Add jitter to prevent thundering herd under concurrent writes.

**Acceptance criteria:**
- [ ] Final failure raises exception (not swallowed)
- [ ] All retry attempts use `log.warning`/`log.error`, not `print()`
- [ ] Jitter added to backoff delays

---

## Issue 6.3 — Stray `\begin{document}` in listings_config.tex
**File:** listings_config.tex:25
**Evidence:** Spurious `\begin{document}` that would cause a fatal
compile error if this file were ever `\input`-ted.

**Fix:** Delete the `\begin{document}` line from listings_config.tex.

**Acceptance criteria:**
- [ ] listings_config.tex contains no `\begin{document}`

---

## Issue 6.4 — Simulation Mode Activates Silently (No Log Warning)
**Files:** run_pilot_experiment.py:39, run_deep_learning_harness.py:134, 284
**Evidence:** Simulation mode fires with no print/log at entry.
A user without API keys gets silently fabricated results.

**Fix:** At the entry of each simulation branch:
```python
log.warning("=" * 60)
log.warning("SIMULATION MODE: No API key detected.")
log.warning("Results are SYNTHETIC — not real LLM/PyTorch output.")
log.warning("Set OPENROUTER_API_KEY to run physical experiments.")
log.warning("=" * 60)
```

**Acceptance criteria:**
- [ ] WARNING banner logged whenever simulation mode activates
- [ ] Output JSON contains `"mode": "simulation"` for simulation runs
