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

## Phase 0 — Learnability gate (BEFORE any campaign)
- [ ] Add warmup (2 epochs) + cosine annealing LR schedule to `run_deep_learning_harness.py`
- [ ] Raise budget to 40 epochs with early stopping on validation
- [ ] Hand-train one *strong* config and one *weak* config on Task A
- [ ] **GATE:** strong config >= 75% AND (strong - weak) gap >= 20 points
  - Pass -> proceed to Phase 1
  - Fail -> adjust task difficulty / training, repeat. **No full campaign until this passes.**

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
