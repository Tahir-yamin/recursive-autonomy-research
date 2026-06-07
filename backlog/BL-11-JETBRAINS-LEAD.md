# BL-11 — JetBrains Lead Critiques

**Priority:** 🟡 P2
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** Fail

---

## Issue 11.1 — 33 print() Calls; Module Logger Never Used
**Files:** run_pilot_experiment.py (30 calls), run_deep_learning_harness.py (3 calls)
**Evidence:** `log = logging.getLogger("rar_orchestrator")` exists at
run_pilot_experiment.py:23 but is never called. ALL diagnostic output
uses `print()`. run_deep_learning_harness.py has zero logging infrastructure.

**Fix (bulk replacement):**
```python
# run_deep_learning_harness.py — add at top:
import logging
log = logging.getLogger(__name__)

# Replace ALL print() calls with appropriate log level:
# print(f"Rate limited...") → log.warning(...)
# print(f"API Error...") → log.error(...)
# print(f"Starting campaign...") → log.info(...)
# print(f"SRE WAL Error...") → log.error(...)
# print(f"CUDA OOM...") → log.error(...)
```
Priority order: fix error/warning paths first (WAL failures, API
errors, OOM handlers) — these are the ones that cause data integrity
issues when invisible.

**Acceptance criteria:**
- [ ] Zero `print()` calls on error/warning paths in both files
- [ ] `run_deep_learning_harness.py` imports and uses logging
- [ ] `log.error(exc_info=True)` used at all exception sites to
      capture stack traces

---

## Issue 11.2 — Critical: `except Exception:` at Line 866 Silences Broken Wilcoxon
**File:** run_pilot_experiment.py:866
**Evidence:**
```python
except Exception:
    p_val_str = "n.s. (insufficient variance)"
```
A scipy.stats.wilcoxon failure (e.g., all-identical arrays — which
happens in simulation mode!) silently replaces the p-value with a
human-readable string that gets serialized to JSON and reported
as a result. No logging, no exc_info.

**Fix:**
```python
except Exception as e:
    log.error(f"Wilcoxon test failed: {e}", exc_info=True)
    p_val_str = "STAT_ERROR"  # not a publishable result string
    # Do NOT write "n.s." — that looks like a legitimate statistical outcome
```

**Acceptance criteria:**
- [ ] Failed Wilcoxon is logged with exc_info=True
- [ ] Result string is clearly marked as an error, not "n.s."

---

## Issue 11.3 — Bare `except:` at Line 299 Swallows KeyboardInterrupt
**File:** run_pilot_experiment.py:299
**Evidence:**
```python
except:
    pass
```
Swallows ALL exceptions including KeyboardInterrupt and SystemExit.

**Fix:**
```python
except OSError:
    pass  # tmp file already gone — acceptable
```

**Acceptance criteria:**
- [ ] Zero bare `except:` clauses in the codebase

---

## Issue 11.4 — LaTeX Listing at Line 2101 Uses `language=C` on JSON Data
**File:** main.tex:2101
**Evidence:** A listing block containing JSON data is labeled
`[language=C, caption=Snippet of pilot_results.json...]`.
C syntax highlighting miscolors JSON braces and strings.

**Fix:** Change to `[language={}, caption=...]` or `[language=json]`
(if listings JSON language definition is loaded).

**Acceptance criteria:**
- [ ] JSON data listings use `language={}` or `language=json`
