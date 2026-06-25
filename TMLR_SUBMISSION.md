# TMLR Submission Package — Recursive Autonomous Research

Target venue: **Transactions on Machine Learning Research (TMLR)**, via OpenReview.
TMLR accepts on two criteria only: **(1)** are the claims supported by accurate,
convincing, and complete evidence, and **(2)** would some individuals in TMLR's audience
be interested. It explicitly does *not* gate on significance, novelty, or SOTA. This paper
is written to that bar: an honest, reproducible study with a robust efficiency result and a
transparently-reported, non-significant accuracy trend.

---

## 1. Claims and the evidence for each

| # | Claim (as stated in the paper) | Evidence | Strength |
|---|--------------------------------|----------|----------|
| **C1** | RAR's recursive context compression reduces net token cost by ~68–70% and prompt density by 72.5% versus a stateless baseline, at accuracy parity. | Table 1 efficiency row; `pilot_results*.json`; reproducible via `inject_results.py`. | **Strong / supported.** |
| **C2** | Any accuracy benefit of agent memory is small and scales with task difficulty; it is not uniform. | Table 1: RAR top condition on both hard tasks (8/10, 7/10 seeds), neutral on the easy control. | **Supported as a trend**, explicitly *not* claimed significant. |
| **C3** | The accuracy advantage on hard tasks is directional but not statistically significant after multiple-comparison correction. | Wilcoxon p=0.116 (synthetic), 0.064 (CIFAR); Holm-adjusted 0.116 / 0.129. Stated as such. | **Supported (a null/borderline result, honestly reported).** |
| **C4** | The compression protocol is asymptotically cost-equivalent to a stateless baseline for bounded memory. | Proposition 1 + proof; bounded `deque(maxlen=50)` in code. Scope limited to bounded M (stated). | **Supported within stated scope.** |
| **C5** | Local Write-Ahead Logging gives 100% task recoverability under induced API failures. | WAL with SHA-256 checksum + atomic `os.replace`; recoverability column in Table 1. | **Supported.** |

No claim of accuracy *superiority* or SOTA is made. The headline contribution is **C1
(efficiency)**; **C2/C3** are reported as a difficulty-dependent trend, not a win.

## 2. Why TMLR's audience would be interested

- Long-horizon LLM agents are a fast-growing area; **context rot** is a real and
  under-measured failure mode. A pre-registered, leak-free measurement of whether structured
  memory *actually* helps (and by how much) is useful even when the accuracy answer is "not
  significantly, but it trends with difficulty."
- The **efficiency result is immediately actionable**: ~68% token reduction at parity is
  relevant to anyone running agentic search loops at scale.
- The **honest negative/borderline accuracy finding** is exactly the kind of result that
  rarely gets published but should: it tells the field where *not* to expect easy gains.

## 3. Reproducibility statement

- **Pre-registration:** `PREREGISTRATION.md` (committed before the campaigns; git history is
  the timestamp). Hypotheses, tasks, seeds, cycles, and decision rule fixed in advance.
- **Code:** full orchestrator (`run_pilot_experiment.py`), harness
  (`run_deep_learning_harness.py`), tasks (`rar_tasks.py`), analysis (`merge_and_analyze.py`).
- **Data:** per-task results (`pilot_results_taskA.json`, `taskB_cifar_N10.json`, digits
  output) and the headline summary (`RESULTS_FINAL.md`); tables regenerated programmatically.
- **Seeds:** fixed set {42,7,13,23,88,99,101,107,113,127}, N=10 per task.
- **Anti-fabrication guard:** `call_llm` refuses to run without a real API key unless
  `RAR_SIM=1` is explicitly set, so a lost environment variable cannot silently simulate
  results.

## 4. Limitations disclosed in the paper (TMLR values candor)

1. Accuracy effect small and non-significant after Holm (N=10 underpowered for sub-point
   effects; CIFAR borderline at raw p=0.064).
2. **Mixed proposing model on CIFAR** (6 gemma2 + 4 OpenRouter seeds) — documented exception,
   deferred to future work. A uniform re-run was attempted but the free OpenRouter tier
   rate-limited it to ~1 seed / 12h (non-viable for N=10); the paired within-seed design
   cancels any per-seed orchestrator offset, so the within-task statistics remain valid.
3. Classification-only task families; max 60 cycles; bounded-memory theory only.
4. Several systems features (distributed locking, incremental community detection) are design
   intent, not implemented — flagged explicitly, not claimed as results.

## 5. Suggested OpenReview cover note (paste-ready)

> We submit a pre-registered, three-benchmark study of context-rot mitigation in long-horizon
> LLM optimization agents. Our central, well-supported claim is an **efficiency** result:
> recursive context compression cuts net token cost by ~68% at accuracy parity. We
> additionally report, with full transparency, a **small difficulty-dependent positive
> accuracy trend that does not reach significance after correction** — RAR is the top
> condition on both hard benchmarks (winning 8/10 and 7/10 seeds) but neutral on an easy
> control. We pre-registered hypotheses, seeds, and the decision rule, and we report the
> outcome as found. We believe the efficiency result is directly useful to practitioners and
> the honest accuracy finding is informative for the agent-memory literature. All code, data,
> and the pre-registration are released.

## 6. Pre-submission checklist

- [x] Manuscript compiles clean (23 pp, 0 undefined refs)
- [x] Every number machine-generated from released JSON (no hand-entry)
- [x] Pre-registration committed before runs
- [x] Limitations section complete and candid
- [x] No leaked credentials; anti-fabrication guard in place
- [x] Code migrated to structured logging; buzzwords trimmed
- [x] Mixed-orchestrator CIFAR framed as a documented exception deferred to future work (uniform re-run rate-limited on free tier)
- [ ] Anonymize author/repo identifiers for double-blind (currently anonymous title block; scrub repo URL on submission)
- [ ] Generate camera-ready figures from the three-task data (`plot_best_found.py` + Table via `inject_results.py`)
