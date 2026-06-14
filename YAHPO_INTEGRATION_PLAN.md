# YAHPO Gym integration — plan & status

**Status: staged, not yet implemented.** This file is the honest record of what
a YAHPO Gym benchmark requires, so it is not claimed as done until it runs.

## Why YAHPO
YAHPO Gym (Pfisterer et al., 2022) is a surrogate HPO benchmark: 14 scenarios,
700+ problems, with precomputed/surrogate objective functions. Evaluating RAR on
it (a) costs ~zero compute (no model training — just a surrogate query), and
(b) is the *native* benchmark of the HPO field, so it directly answers the
"is this a real HPO method?" question. Source:
https://proceedings.mlr.press/v188/pfisterer22a.html ·
https://github.com/slds-lmu/yahpo_gym

## What blocks a drop-in (verified locally, 2026-06-14)
1. **Surrogate data is a separate download.** `pip install yahpo_gym` installs the
   library but not the ONNX surrogates; instantiating a benchmark without them
   raises `FileNotFoundError`. The data lives in `slds-lmu/yahpo_data` and must be
   fetched and registered via `local_config.set_data_path(...)`.
2. **Different search space.** YAHPO scenarios (e.g. `lcbench`, `rbv2_*`) define
   their own ConfigSpace (mixed numeric/categorical, different names than our
   7-parameter MLP space). The RAR loop's `SEARCH_SPACE`, `is_valid_config`, and
   `config_to_vector` are currently hardcoded to the MLP space.
3. **`config_to_vector` must become schema-general.** This is the same gap
   Reviewer #14 (LangChain) flagged. Implementing YAHPO support *forces* the
   schema-driven vectorizer, so it resolves two issues at once.

## Implementation steps (next milestone)
1. **Setup (Colab cell):**
   ```bash
   git clone https://github.com/slds-lmu/yahpo_data
   python -c "from yahpo_gym import local_config; local_config.init_config(); \
              local_config.set_data_path('yahpo_data')"
   ```
2. **Backend wrapper** `run_yahpo_objective.py`: given a YAHPO scenario+instance,
   expose `evaluate(config) -> val` and a held-out `test` proxy (a different
   fidelity/instance) mirroring the train/test split discipline.
3. **Schema-general core:** replace hardcoded `SEARCH_SPACE`/`config_to_vector`
   with a `Space` object built from the scenario's ConfigSpace; vectorize numeric
   params by min-max from the declared bounds and categoricals by one-hot from the
   declared choices (no literal constants). `is_valid_config` already reads the
   schema and needs only minor generalization.
4. **Route the orchestrator:** when `RAR_DATASET=yahpo`, the proposer prompt is
   built from the YAHPO space and `train_and_evaluate` is replaced by the surrogate
   query. Classical baselines (`run_classical_baselines.py`) already read
   `SEARCH_SPACE` generically and will work unchanged once it is schema-driven;
   Optuna can also query the surrogate directly as an additional reference.
5. **Report:** add YAHPO as another column in the multi-benchmark table.

## Acceptance criteria (so we don't overclaim again)
- [ ] A YAHPO scenario instantiates and returns a surrogate objective value.
- [ ] RAR proposes valid configs in the YAHPO space (no hardcoded constants).
- [ ] `config_to_vector` produces correct vectors for the YAHPO space (verified by
      a unit check that changing the space does not break it).
- [ ] Results written to `pilot_results_yahpo_<scenario>.json` and merged.
