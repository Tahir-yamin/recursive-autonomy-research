# BL-01 — IEEE TPAMI Editor Critiques

**Priority:** 🔴 P0
**Status:** Issue 1.3 RESOLVED (2026-06-14, real p=0.2461); LaTeX/benchmark items remain open
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

**Fix:** Resolved by BL-SIM (real experiments now run). The real
$N=10$, 60-cycle campaign (`openai/gpt-oss-20b:free`) was re-run through
`scipy.stats.wilcoxon` on actual per-seed deltas.

**✅ RESOLVED (2026-06-14):** The fraud-derived p=0.0010 did **not** survive
real data. Real one-sided Wilcoxon RAR>baseline gives **p = 0.2461 (not
significant)**. The paper now reports accuracy parity and an efficiency
contribution (70.0% token reduction, 72.5% density reduction) instead of any
significance claim.

**Acceptance criteria:**
- [x] p-value computed from real experiment data (p = 0.2461)
- [x] Accuracy-superiority claim withdrawn; efficiency framing adopted across
      manuscript, Table 1 caption, and abstract

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
