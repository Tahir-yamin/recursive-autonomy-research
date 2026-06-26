# Proof of Resolution: Critique 19 (Anchor Bias & Fallback Standardization)

## Original Critique
Anchor Bias: RAG strictly retrieves neighbors to `rag_trials[-1]["config"]`, trapping the search in a localized random walk.
Rigged Fallbacks: RAR defaults to an explicitly programmed Guided Hill-Climbing Algorithm, while baselines collapse to random guessing.

## Proof of Resolution
1. Anchor Bias Elimination: Shifted the similarity anchor search point from the last trial config `[-1]` to the *optimum peak centroid* (highest accuracy configuration currently achieved). This directs retrieval toward global extrema rather than localized walks.
2. Standardized Fallback System: Unified heuristic fallback procedures across all baseline and experimental branches. If model calls fail, every group is routed to a shared `propose_heuristic_config` function running the exact same robust Guided Hill-Climbing logic.

### Code Snippet (`run_pilot_experiment.py`)
```python
# Vector RAG centroid anchor resolution
best_known = max(trials, key=lambda x: x["acc"])
candidate_dummy = best_known["config"]
history_str = retrieve_vector_rag_context(list(trials), candidate_dummy, budget_limit=2000)

# Unified Fallback Strategy
def propose_heuristic_config(condition, trials):
    # ...
    best_trial = max(trials, key=lambda t: t["acc"])
    best_cfg = best_trial["config"]
    for _ in range(100):
        cfg = perturb_config_guided(best_cfg, best_trial["acc"])
        if cfg not in evaluated_configs:
            return cfg
    return get_random_config()
```
This guarantees complete comparative fairness across all conditions.
