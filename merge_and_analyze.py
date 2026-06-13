"""Merge Task A + Task B results (from any combination of full JSON, partial JSON, or
log-salvaged seeds) and run the pre-registered analysis:
 - per-task one-sided Wilcoxon (RAR > stateless) on test accuracy
 - Holm correction across the two tasks
Robust to Task B being incomplete (reports the actual n and flags pre-registration status).

Inputs it will use if present (in repo root):
  pilot_results_taskA.json                 (Task A, N=10)
  taskB_6seeds_from_log.json               (6 salvaged Task B seeds: test acc per condition)
  pilot_results_taskB.json / partial_results.json  (new Task B seeds from Colab/Kaggle)
"""
import json, os, glob, numpy as np
from scipy.stats import wilcoxon

ROOT = os.path.dirname(os.path.abspath(__file__))
CONDS = ["stateless_baseline", "vector_rag", "rar_compressed"]


def load_json(name):
    p = os.path.join(ROOT, name)
    return json.load(open(p)) if os.path.exists(p) else None


def taskB_seed_map():
    """Return {seed: {cond: test_acc}} merging all available Task B sources."""
    seeds = {}
    # 1) salvaged 6 seeds (schema: {cond: {seed: acc}})
    s6 = load_json("taskB_6seeds_from_log.json")
    if s6:
        for cond, d in s6.items():
            for seed, acc in d.items():
                seeds.setdefault(int(seed), {})[cond] = float(acc)
    # 2) any full/partial results JSON with per-seed test_accuracies aligned to SEEDS
    for fn in ["pilot_results_taskB.json", "partial_results_taskB.json", "partial_results.json"]:
        d = load_json(fn)
        if not d:
            continue
        sl = d.get("SEEDS") or d.get("data", {}).get("SEEDS")
        conds = d.get("data", {}).get("conditions") or d.get("conditions")
        if not conds:
            continue
        for cond in CONDS:
            accs = conds.get(cond, {}).get("test_accuracies", [])
            for i, acc in enumerate(accs):
                if sl and i < len(sl):
                    seeds.setdefault(int(sl[i]), {})[cond] = float(acc)
    # keep only seeds with all three conditions
    return {s: v for s, v in seeds.items() if all(c in v for c in CONDS)}


def wilcox(rar, base):
    rar, base = np.array(rar), np.array(base)
    if len(rar) < 5:
        return None, len(rar)
    try:
        _, p = wilcoxon(rar, base, alternative="greater")
        return float(p), len(rar)
    except Exception:
        return None, len(rar)


def report_task(name, base, vec, rar, seeds=None):
    base, vec, rar = np.array(base)*100, np.array(vec)*100, np.array(rar)*100
    print(f"\n=== {name} (n={len(rar)}{' seeds '+str(sorted(seeds)) if seeds else ''}) ===")
    print(f"  stateless : {base.mean():.2f} ± {base.std():.2f}%")
    print(f"  vector_rag: {vec.mean():.2f} ± {vec.std():.2f}%")
    print(f"  RAR       : {rar.mean():.2f} ± {rar.std():.2f}%   (RAR-base {rar.mean()-base.mean():+.2f}pp, wins {int((rar>base).sum())}/{len(rar)})")
    p, n = wilcox(rar/100, base/100)
    print(f"  Wilcoxon one-sided p (RAR>base): {p if p is None else round(p,4)}")
    return p


def main():
    pvals = {}
    # Task A
    A = load_json("pilot_results_taskA.json")
    if A:
        c = A["data"]["conditions"]
        pvals["Task A"] = report_task("TASK A (synthetic, N=%d)" % len(A["SEEDS"]),
                                      c["stateless_baseline"]["test_accuracies"],
                                      c["vector_rag"]["test_accuracies"],
                                      c["rar_compressed"]["test_accuracies"])
    # Task B (merged)
    bmap = taskB_seed_map()
    if bmap:
        seeds = sorted(bmap)
        base = [bmap[s]["stateless_baseline"] for s in seeds]
        vec = [bmap[s]["vector_rag"] for s in seeds]
        rar = [bmap[s]["rar_compressed"] for s in seeds]
        pvals["Task B"] = report_task("TASK B (CIFAR)", base, vec, rar, seeds)
        if len(seeds) < 10:
            print(f"  NOTE: Task B has {len(seeds)}/10 seeds — pre-registration requires N=10; "
                  f"missing {sorted(set([42,7,13,23,88,99,101,107,113,127])-set(seeds))}.")

    # Holm correction across tasks (only valid pvals)
    valid = {k: v for k, v in pvals.items() if v is not None}
    if len(valid) >= 2:
        order = sorted(valid, key=lambda k: valid[k])
        m = len(valid)
        print("\n=== Holm-corrected (across tasks) ===")
        for i, k in enumerate(order):
            adj = min(1.0, valid[k] * (m - i))
            print(f"  {k}: raw p={valid[k]:.4f} -> Holm p={adj:.4f}  {'SIGNIFICANT' if adj<0.05 else 'n.s.'}")
    print("\n(Decision rule: see PREREGISTRATION.md)")


if __name__ == "__main__":
    main()
