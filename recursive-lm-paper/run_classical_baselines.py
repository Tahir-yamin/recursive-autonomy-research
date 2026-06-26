"""Classical HPO baselines (Random Search + Bayesian Optimization) on the SAME
search space and training harness as the LLM conditions.

These are non-LLM references: they answer the question every HPO reviewer asks --
"does the LLM-driven agent beat plain random search / Bayesian optimization?"
They consume ZERO language-model tokens; their only cost is the same PyTorch
training the LLM conditions also pay.

Usage (per dataset; honors RAR_DATASET / RAR_CYCLES like the main campaign):
    RAR_DATASET=digits python run_classical_baselines.py
Writes per-seed files pilot_seed_<seed>_<dataset>_classical.json and a merged
pilot_results_<dataset>_classical.json with conditions {random_search, bayesian_opt}.
"""
import os, sys, json, time, glob
import numpy as np

# Real training required: refuse to run under simulation, same guard philosophy
# as the rest of the codebase (set a real key to run; RAR_SIM=1 for offline sim).
import run_pilot_experiment as rpe           # SEARCH_SPACE, get_random_config
import run_deep_learning_harness as h        # train_and_evaluate, evaluate_test_vault

DATASET = os.environ.get("RAR_DATASET", "manifold")
CYCLES = int(os.environ.get("RAR_CYCLES", "60"))
SEEDS = [int(x) for x in os.environ.get(
    "RAR_SEEDS", "42,7,13,23,88,99,101,107,113,127").split(",")]
SEARCH = rpe.SEARCH_SPACE
EPOCHS = int(os.environ.get("RAR_EPOCHS", "15"))


def _empty_cond():
    return {m: [] for m in ("val_accuracies", "test_accuracies", "redundancies",
                            "prompt_densities", "wall_clock_latencies",
                            "net_tokens", "generalization_gaps")}


def random_search(seed):
    np.random.seed(seed)
    best_cfg, best_val, seen, redundant = None, -1.0, set(), 0
    for _ in range(CYCLES):
        cfg = rpe.get_random_config()
        key = json.dumps(cfg, sort_keys=True)
        if key in seen:
            redundant += 1
        seen.add(key)
        val = h.train_and_evaluate(cfg, dataset_seed=seed, epochs=EPOCHS)
        if val > best_val:
            best_val, best_cfg = val, cfg
    test = h.evaluate_test_vault(best_cfg, dataset_seed=seed, epochs=EPOCHS)
    return best_val, test, redundant


def bayesian_opt(seed):
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial):
        cfg = {k: trial.suggest_categorical(k, SEARCH[k]) for k in SEARCH}
        return h.train_and_evaluate(cfg, dataset_seed=seed, epochs=EPOCHS)

    study = optuna.create_study(
        direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=CYCLES, show_progress_bar=False)
    best_cfg = {k: study.best_params[k] for k in SEARCH}
    test = h.evaluate_test_vault(best_cfg, dataset_seed=seed, epochs=EPOCHS)
    # TPE re-proposes near-optima; count exact-duplicate trials as redundancy
    keys = [json.dumps({k: t.params.get(k) for k in SEARCH}, sort_keys=True)
            for t in study.trials]
    redundant = len(keys) - len(set(keys))
    return study.best_value, test, redundant


def run_seed(seed):
    out = f"pilot_seed_{seed}_{DATASET}_classical.json"
    if os.path.exists(out):
        print(f"seed {seed} [{DATASET}/classical]: exists, skip")
        return
    rec = {"seed": seed, "dataset": DATASET, "CYCLES": CYCLES,
           "conditions": {"random_search": _empty_cond(),
                          "bayesian_opt": _empty_cond()}}
    for name, fn in (("random_search", random_search), ("bayesian_opt", bayesian_opt)):
        t0 = time.time()
        val, test, red = fn(seed)
        dt = time.time() - t0
        c = rec["conditions"][name]
        c["val_accuracies"].append(round(float(val), 4))
        c["test_accuracies"].append(round(float(test), 4))
        c["redundancies"].append(int(red))
        c["prompt_densities"].append(0.0)         # no prompt: not an LLM method
        c["net_tokens"].append(0)                 # no language-model tokens
        c["wall_clock_latencies"].append(round(dt, 2))
        c["generalization_gaps"].append(round(float(val - test), 4))
        print(f"seed {seed} {name:14s} val={val:.4f} test={test:.4f} "
              f"redundant={red} {dt:.1f}s")
    with open(out, "w") as f:
        json.dump(rec, f, indent=2)
    print(f"  wrote {out}")


def merge():
    files = sorted(glob.glob(f"pilot_seed_*_{DATASET}_classical.json"),
                   key=lambda p: int(p.split("_")[2]))
    if not files:
        print("no per-seed classical files to merge"); return
    conds = ("random_search", "bayesian_opt")
    metrics = list(_empty_cond().keys())
    merged = {c: {m: [] for m in metrics} for c in conds}
    seeds = []
    for fp in files:
        r = json.load(open(fp)); seeds.append(r["seed"])
        for c in conds:
            for m in metrics:
                merged[c][m] += r["conditions"][c][m]
    out = {"meta": f"Classical HPO baselines on {DATASET}",
           "dataset_tag": DATASET, "SEEDS": seeds, "CYCLES": CYCLES,
           "data": {"dataset": DATASET, "SEEDS": seeds,
                    "CYCLES": CYCLES, "conditions": merged}}
    name = f"pilot_results_{DATASET}_classical.json"
    json.dump(out, open(name, "w"), indent=2)
    print(f"\nMerged {len(seeds)} seeds -> {name}")
    for c in conds:
        ta = merged[c]["test_accuracies"]
        print(f"  {c:14s} mean test_acc={np.mean(ta):.4f}")


if __name__ == "__main__":
    print(f"Classical baselines | dataset={DATASET} cycles={CYCLES} seeds={SEEDS}")
    for s in SEEDS:
        run_seed(s)
    merge()
