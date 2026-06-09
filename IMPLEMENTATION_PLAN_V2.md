# RAR v2 — Implementation Plan (Q1-Decisive Experiment)

**Status:** Awaiting approval to start Phase 0
**Created:** 2026-06-08
**Owner:** Tahir Yamin
**Goal:** Make the RAR context-rot hypothesis genuinely testable, so either outcome
(positive *or* conclusive negative) is Q1-grade.

---

## The one problem we are fixing
Models train to only ~40% on a 3-class task (chance = 33%). Every condition is pinned
near random, so accuracy cannot reveal search quality, so memory cannot show any effect.
**Root cause:** undertraining (15 epochs, a *searched* LR with no schedule) collapses good
and bad configs to the same score. **Fix training first, then test the hypothesis on a
harder, instrumented benchmark.**

---

## Phase 0 — Learnability gate (BEFORE any campaign) ✅ COMPLETE
- [x] Add warmup (2 epochs) + cosine annealing LR schedule (`phase0_learnability_gate.py`)
- [x] Raise budget to 40 epochs with early stopping on validation (patience=8)
- [x] Hand-train one *strong* config and one *weak* config on Task A
- [x] **GATE PASSED:** strong >= 75% AND (strong - weak) gap >= 20 points, stable over 3 seeds:
  - seed 42: strong 82.5% / weak 55.8% / **gap 26.7pp**
  - seed 7:  strong 82.7% / weak 55.5% / **gap 27.2pp**
  - seed 13: strong 82.5% / weak 57.6% / **gap 24.9pp**

**Locked Task A definition** (10-class, learnable + discriminating):
`make_classification(n_samples=12000, n_features=64, n_informative=55, n_redundant=0,
n_classes=10, n_clusters_per_class=2, class_sep=1.3, flip_y=0.02)` + warp
`X + 0.4*tanh(0.7X) + 0.3*sin(Xpi)`. Training: AdamW + warmup(2) + cosine, 40 epochs,
early stopping patience=8.

## Phase 1 — Build the two benchmarks
- [ ] **Task A (primary):** harder synthetic manifold (10 classes, 64 features, lower
      class separation). Agent searches **architecture + regularization** (depth, width,
      dropout, weight-decay, label-smoothing). **LR schedule fixed** (clean accuracy signal).
- [ ] **Task B (generality):** real small dataset (sklearn `digits` or UCI). Agent search
      **includes LR** (realistic HPO).
- [ ] Verbose per-cycle logs (~700 chars) so the stateless baseline genuinely overflows
      `C_max` and truncates.
- [ ] Add `TASK` env switch to select task family.

## Phase 2 — Instrumentation (Q1 credibility)
- [ ] Log per cycle to JSON: **best-found accuracy so far**
- [ ] Log per cycle: whether the **global-best trial is still in the baseline's context**
      (direct evidence of rot)
- [ ] Keep redundancy / density / tokens / latency tracking (already real)
- [ ] New plot script: **best-found accuracy vs cycle** (the central figure)

## Phase 3 — Pre-registration (commit BEFORE running)
- [ ] Write `PREREGISTRATION.md`:
  - **H1 (primary):** RAR best-found test accuracy > stateless (one-sided Wilcoxon, alpha=0.05)
  - **H2 (mechanism):** baseline best-found plateaus after context saturates; RAR's does not
  - **Decision rule:** report whatever happens — positive OR conclusive negative

## Phase 4 — Run (automated on Kaggle)
- [ ] Conditions: Stateless / Vector-RAG / RAR; **N=10 seeds, 60 cycles**, gemma2:9b local
- [ ] **One kernel per task** (fits 12 h limit; per-seed checkpointing in place)
- [ ] Push via Kaggle API -> poll -> pull logs + JSON for Task A
- [ ] Repeat for Task B

## Phase 5 — Analyze & write
- [ ] Regenerate tables + best-found-vs-cycle figure from real JSON (no hand-entry)
- [ ] Wilcoxon per task + Holm correction across tasks; effect sizes + 95% CIs
- [ ] Update the paper to whatever the data shows

---

## Outcome map (both publishable, honestly)
| Result | Interpretation |
|---|---|
| RAR wins on accuracy under proven saturation | Genuine positive Q1 claim |
| RAR ties despite proven saturation + dynamic range | Conclusive negative (efficiency, not accuracy) — also Q1-grade because instrumented + general |
| Saturation still not achieved | Inconclusive -> iterate on task difficulty before claiming anything |

## Honesty guardrails
- [ ] Pre-register H1/H2 before running
- [ ] Every number machine-generated from real logs (no hand-entry)
- [ ] Report the result that occurs, positive or negative

## Effort estimate
- Phase 0-3 (build + gate): ~1-2 h
- Phase 4 (run): ~6-10 h Kaggle, automated
- Phase 5 (analyze + write): ~1 h

---

## Decisions locked (no longer open questions)
- Both task families: **yes** (A primary, B generality)
- LR: **warmup + cosine annealing, 40 epochs + early stopping**
- Search target: **Task A = architecture+regularization (fixed LR); Task B = includes LR**
- N=10 seeds, 60 cycles, gemma2:9b on Kaggle GPU

---

## Progress log
- 2026-06-08: Plan created, awaiting "go" to start Phase 0.
- 2026-06-08: **Phase 0 COMPLETE.** Built warmup+cosine / 40-epoch / early-stopping training
  and a 10-class Task A. Tuned difficulty across 4 iterations until learnable AND
  discriminating (too-easy 2.9pp gap -> too-hard 57% ceiling -> locked at strong 82.5% /
  weak 56% / 26.7pp gap, stable over seeds 42/7/13). Gate PASSED.
- 2026-06-08: **Phase 0 EXTENDED (Colab).** Owner ran deep characterisation on GPU:
  architecture sweep (strong ceiling 82.2% -> 91.1% refined; 91.3% at 7x768 = manifold
  ceiling), LR sweep (1e-2 optimal), efficiency analysis, confusion-matrix + t-SNE error
  analysis (Class 3<->9 geometric overlap, proximity 1.12x). Full record + 15 figures in
  `phase0/PHASE0_RECORD.md`. Search-space bounds for Phase 1 now set (depth<=7, width<=512,
  LR<=1e-2). Ready for Phase 1.
