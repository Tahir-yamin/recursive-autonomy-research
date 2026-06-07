# BL-07 — JMLR Editor Critiques

**Priority:** 🔴 P0
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** Fail | Verdict: Reject

---

## Issue 7.1 — δ_low and δ_high Justified Only by Assertion
**File:** main.tex:232, 351
**Evidence:** "Calibrated to δ_low=0.50 and δ_high=0.90" is stated
with no empirical derivation, no ablation, and no theoretical bound.
"Calibrated" = "we chose these values" in the current text.

**Fix (two options):**
Option A — Empirical calibration:
Run sensitivity ablation over δ_low ∈ {0.3, 0.4, 0.5, 0.6} and
δ_high ∈ {0.7, 0.8, 0.9} and report which pair maximizes the
generalization gap improvement. Present as a small table. Cite the
winning pair as "empirically calibrated via grid search."

Option B — Engineering justification:
Provide a mechanical argument: "δ_low=0.50 triggers compression when
the context is half full (conservative), giving the LLM sufficient
remaining budget; δ_high=0.90 prevents operation above 90% fill
where LLM coherence degrades empirically [cite relevant LLM context
length paper]." The second part requires an actual citation.

**Acceptance criteria:**
- [ ] Definition 1 includes a justification paragraph beyond
      "calibrated values"
- [ ] Either ablation table OR engineering argument with citation

---

## Issue 7.2 — Table 1 Numbers Must Match Pilot Results JSON Exactly
**Evidence (current audit):** Table 1 arithmetic currently matches
the simulation JSON correctly. BUT — after BL-SIM is resolved and
real experiments run — Table 1 must be regenerated from the new JSON.
Risk: the table is updated manually and drifts from the JSON.

**Fix:** Automate table generation:
```python
# inject_results.py should read pilot_results.json and
# overwrite the Table 1 rows programmatically — never
# hand-edit the .tex table values.
```
Add a CI/pre-commit check: run `inject_results.py` and verify that
`git diff main.tex` shows zero changes to table numeric values.

**Acceptance criteria:**
- [ ] Table 1 values are generated programmatically from pilot_results.json
- [ ] No manual hand-editing of table numeric values in .tex

---

## Issue 7.3 — Appendix JSON Listing Doesn't Match pilot_results.json
**File:** main.tex lines ~828–860
**Evidence:** Appendix reproduces a "raw pilot_results.json" with
different structure and slightly different rounded values vs. the
actual file on disk.

**Fix:** Replace appendix JSON listing with the actual file content
(auto-generated via `inject_results.py` or a similar script).

**Acceptance criteria:**
- [ ] Appendix JSON listing is identical to pilot_results.json
