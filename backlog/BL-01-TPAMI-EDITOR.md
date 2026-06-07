# BL-01 — IEEE TPAMI Editor Critiques

**Priority:** 🔴 P0
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** F | Verdict: Reject

---

## Issue 1.1 — Wrong Document Class (DESK-REJECT)
**File:** main.tex:1
**Evidence:** `\documentclass[11pt,a4paper]{article}` with custom
`\titleformat`, `\fancyhdr`, decorative `\noindent\rule` separators.
TPAMI requires `IEEEtran` two-column format.

**Fix:**
- Replace `\documentclass{article}` with `\documentclass[journal]{IEEEtran}`
- Remove `titlesec`, `fancyhdr`, `parskip` packages (IEEEtran handles these)
- Remove all `\noindent\rule`, `\vspace{4pt}`, custom heading colors
- Use IEEEtran's `\IEEEauthorblockN` and `\IEEEauthorblockA`

**Acceptance criteria:**
- [ ] Document class is IEEEtran
- [ ] No `\noindent\rule` or manual `\vspace{Npt}` overrides
- [ ] Compiles with zero IEEEtran warnings

---

## Issue 1.2 — `\boldsymbol` in Text-Mode Table Cells
**File:** main.tex:380–381
**Evidence:** Table 1 uses `\boldsymbol{-25.7\%}` and
`\boldsymbol{14{,}605}` in table body (text mode, not math mode).
`\boldsymbol` is a math-mode command — wrong rendering.

**Fix:** Replace `\boldsymbol{...}` with `\textbf{...}` in all
table body cells.

**Acceptance criteria:**
- [ ] Zero `\boldsymbol` occurrences outside math environments

---

## Issue 1.3 — Wilcoxon p=0.0010 is Trivially Guaranteed
**Evidence:** With N=10 and all differences positive (guaranteed by
simulation design), T=0 and p = 1/1024 = 0.000977. This is the
minimum achievable p for N=10 — it is not an empirical discovery.

**Fix:** This is resolved by BL-SIM (running real experiments).
Once real data exists, re-run `scipy.stats.wilcoxon` on actual
per-seed deltas. If some differences are negative, p will be larger
and more meaningful. Do NOT report p=0.0010 if derived from a
simulation where all diffs are guaranteed positive.

**Acceptance criteria:**
- [ ] p-value computed from real experiment data
- [ ] If p=0.0010 survives real data, show the actual T statistic
      and N in the table caption

---

## Issue 1.4 — Benchmark Triviality (Not Desk-Reject but Reviewer Concern)
**Evidence:** 3-class Gaussian quantile + polynomial warp, best
accuracy ~44% (barely above 33% chance). For TPAMI this signals
the task is too easy or the model is poorly suited — either way,
it looks like a toy problem.

**Fix:** Either (a) increase to a harder benchmark (more classes,
higher dimensions, more complex architecture) or (b) add a clear
justification section explaining why this scale is appropriate for
validating the *memory/context* mechanism rather than raw accuracy.
TPAMI reviewers will accept the latter if argued clearly.

**Acceptance criteria:**
- [ ] Either harder benchmark OR explicit benchmark-choice justification
      section in manuscript
