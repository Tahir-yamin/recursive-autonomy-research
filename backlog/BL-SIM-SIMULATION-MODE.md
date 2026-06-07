# BL-SIM — Master Blocker: Simulation Mode Produces All Reported Results

**Priority:** 🔴 P0 — Must resolve before any submission
**Status:** OPEN
**Found by:** All 15 personas independently (convergent finding)
**Audit date:** 2026-06-07

---

## What the Problem Is

`run_pilot_experiment.py` lines 39–91 (`call_llm`) and
`run_deep_learning_harness.py` lines 134–166 (`train_and_evaluate`) and
lines 284–318 (`evaluate_test_vault`) contain a hard-coded
**"SRE Fast Simulation Mode"** that activates silently whenever no
API key is present in the environment.

In this mode:
- `call_llm` returns a hard-coded JSON config from a lookup table
  (`base_seq`, `rar_seq`, `rag_seq`) — no real LLM is called.
- `train_and_evaluate` returns `score = 0.380 + f(config) + noise`
  — no PyTorch model is built, no data is loaded, no forward pass occurs.
- `evaluate_test_vault` returns `0.370 + f(config)` with 5-run averaging
  of the same formula — again, no real training.

## Evidence in pilot_results.json

- `stateless_baseline.test_accuracies` == `vector_rag.test_accuracies`
  — bit-for-bit identical across all 10 seeds. Physically impossible in
  real runs with different context conditions.
- ALL `net_tokens` values: exactly `[18974, 18974, ..., 18974]` across
  10 seeds for baseline — zero variance. Hard-coded constant.
- ALL `prompt_densities`: exactly `0.42435` for all 10 seeds — zero
  variance. Hard-coded constant.
- Wilcoxon p=0.0010 = 1/1024 = the trivial minimum for N=10 when ALL
  differences are positive. Guaranteed by simulation design, not
  discovered empirically.

## What the Paper Claims vs. Reality

Paper (main.tex:358–360):
> "The campaign is executed using **physical LLM inference** via OpenRouter,
> routing to the `nvidia/nemotron-nano-9b-v2:free` model."
> "physical autonomous hyperparameter optimization campaign"

Reality: simulation stub produces all numbers. No disclosure anywhere
in the manuscript.

## Required Fix

### Option A (Preferred): Run Real Experiments
1. Obtain valid OpenRouter API key (set `OPENROUTER_API_KEY` env var).
2. Re-run `run_pilot_experiment.py` with the live key — ensure all
   three conditions run through real `call_llm` (check `"mode":"LLM"`
   in every trial entry in the output JSON).
3. Verify that `stateless_baseline` and `vector_rag` no longer share
   identical arrays.
4. Replace `pilot_results.json` with the real-run output.
5. Update all Table 1 numbers to match the new JSON.
6. Re-run Wilcoxon test on real per-seed deltas.

### Option B: Reframe as Simulation Study
1. Rename "SRE Fast Simulation Mode" to "Calibrated Simulation Study."
2. Add a clearly labeled Section 5.0 disclosing that results are from
   a simulation with stated assumptions (fixed score formulas).
3. Remove ALL "physical LLM inference" language from abstract, intro,
   and results.
4. Change all statistical claims to simulation-validated claims.
5. Note: this changes the paper's contribution significantly.

### In Both Cases
- Add a prominent `logging.warning` at simulation-mode entry so future
  runs cannot be silently simulated:
  ```python
  log.warning("SIMULATION MODE ACTIVE — no real LLM or PyTorch training. "
              "Set OPENROUTER_API_KEY to run physical experiments.")
  ```

## Acceptance Criteria
- [ ] `pilot_results.json` shows non-zero variance in `net_tokens`
      and `prompt_densities` across seeds
- [ ] `stateless_baseline.test_accuracies` ≠ `vector_rag.test_accuracies`
- [ ] Every trial entry in JSON has `"mode": "LLM"` (not `"heuristic"`)
- [ ] Wilcoxon p-value is computed on real per-seed deltas
- [ ] Abstract says either "physical" (Option A) or "simulation"
      (Option B) — never ambiguously both
