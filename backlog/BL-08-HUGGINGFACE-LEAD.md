# BL-08 — Hugging Face Production Lead Critiques

**Priority:** 🟠 P1
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** 3/10 | Verdict: Reject

---

## Issue 8.1 — HPO Cost Analysis Section Missing Despite Claimed Resolution
**File:** main.tex — resolution claims it was added but it does not exist
**Evidence:** The internal red-team resolution log says "Added a
detailed section on HPO computational budgets and token efficiency
tradeoffs." Grep of main.tex finds no such section or table.

**Fix:** Add a real Section 5.x (or subsection within Results) with:
- LLM orchestration cost: N_cycles × avg_tokens_per_prompt × $/token
- Direct random HPO baseline: N_trials × training_time × compute_cost
- Cost ratio table comparing the two
- Conclusion: at what scale (N_cycles, N_params) does LLM orchestration
  become cost-competitive vs. Optuna/random search?

Live pricing reference (June 2026) — NOTE the authoritative campaign now uses
`openai/gpt-oss-20b:free` (free tier, $0.00/M, the real run was at zero direct
cost); confirm current paid-tier rates for gpt-oss-20b when computing the cost
ratio. (Legacy: nemotron-nano-9b-v2 paid was $0.04/M input, $0.16/M output.)

**Acceptance criteria:**
- [ ] A table or paragraph with actual computed cost numbers exists
      in the manuscript
- [ ] Cost ratio (LLM-HPO vs. random HPO) is stated explicitly

---

## Issue 8.2 — "Swiss Roll" Survives in Active Harness Code
(Same as BL-05 Issue 5.1 — tracked here for HF persona record)
**File:** run_deep_learning_harness.py:39

**Fix:** See BL-05-SCALEAI-LEAD.md Issue 5.1

---

## Issue 8.3 — Central Premise Not Economically Justified
**Evidence:** The paper uses a 9B-parameter LLM orchestrator to tune
a ~5K-parameter MLP. No cost-benefit argument justifying this ratio
exists. The ablation (Section 5.1) implicitly admits Louvain adds
no measurable benefit at tested scale.

**Fix:** Add a "Scalability and Cost Justification" paragraph:
"The LLM orchestration overhead is justified when the search space
has non-trivial covariance structure [cite multi-fidelity HPO lit]
and when N_cycles > threshold_T. For the present-scale validation
(60 cycles, 9 dimensions), we acknowledge the ratio is suboptimal
and position this paper as a proof-of-concept for the architectural
pattern, validated at the smallest practical scale."
Honest framing avoids the reviewer complaint while keeping the paper.

**Acceptance criteria:**
- [ ] Paper acknowledges and addresses the overkill ratio explicitly
- [ ] Either a cost-competitive claim is made with evidence, OR the
      proof-of-concept framing is used clearly
