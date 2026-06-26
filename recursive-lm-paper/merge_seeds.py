"""Stitch all pilot_seed_<seed>.json files into one pilot_results.json.

Each per-seed file (written by run_single_seed.py) holds one seed's results for
all three conditions. This script:
  1. Globs pilot_seed_*.json in the workspace.
  2. Concatenates each condition's metric arrays IN A CONSISTENT SEED ORDER
     (sorted by seed) so the paired Wilcoxon compares like-for-like rows.
  3. Runs the Wilcoxon signed-rank test (RAR test-acc > baseline test-acc).
  4. Writes the combined pilot_results.json.

Run after every seed has produced its file:
    python merge_seeds.py
"""
import os
import re
import glob
import json
from scipy.stats import wilcoxon

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

CONDITIONS = ["stateless_baseline", "vector_rag", "rar_compressed"]
# Every per-condition metric list we expect to concatenate across seeds.
METRICS = [
    "val_accuracies", "test_accuracies", "redundancies", "prompt_densities",
    "wall_clock_latencies", "net_tokens", "generalization_gaps",
]


def seed_of(path):
    m = re.search(r"pilot_seed_(\d+)(?:_[A-Za-z0-9]+)?\.json$", os.path.basename(path))
    return int(m.group(1)) if m else None


def main():
    # Optional dataset tag: `python merge_seeds.py digits` merges
    # pilot_seed_<seed>_digits.json -> pilot_results_digits.json.
    import sys
    tag = sys.argv[1] if len(sys.argv) > 1 else None
    if tag:
        pattern = os.path.join(OUTPUT_DIR, f"pilot_seed_*_{tag}.json")
        out_name = f"pilot_results_{tag}.json"
    else:
        pattern = os.path.join(OUTPUT_DIR, "pilot_seed_*.json")
        out_name = "pilot_results.json"
    files = sorted(
        [f for f in glob.glob(pattern) if seed_of(f) is not None],
        key=lambda p: seed_of(p),
    )
    if not files:
        print(f"No files matching {os.path.basename(pattern)} found. Run the seed loop first.")
        return

    seeds_in_order = []
    merged = {c: {m: [] for m in METRICS} for c in CONDITIONS}
    cycles = None

    for path in files:
        seed = seed_of(path)
        with open(path, "r") as f:
            payload = json.load(f)
        data = payload["data"]
        cycles = payload.get("CYCLES", cycles)

        # A per-seed file should hold exactly one seed; guard against stale files.
        file_seeds = data.get("SEEDS", [])
        if len(file_seeds) != 1:
            print(f"WARNING: {os.path.basename(path)} holds {len(file_seeds)} "
                  f"seeds, expected 1. Skipping to avoid contamination.")
            continue

        seeds_in_order.append(seed)
        for cond in CONDITIONS:
            cdata = data["conditions"][cond]
            for metric in METRICS:
                vals = cdata.get(metric, [])
                if vals:
                    merged[cond][metric].append(vals[0])

        print(f"Merged seed {seed} from {os.path.basename(path)}")

    n = len(seeds_in_order)
    print(f"\nMerged {n} seeds: {seeds_in_order}")

    # Paired Wilcoxon: RAR test accuracy greater than stateless baseline.
    rar = merged["rar_compressed"]["test_accuracies"]
    base = merged["stateless_baseline"]["test_accuracies"]
    if n >= 2 and len(rar) == len(base) == n:
        try:
            _, p_val = wilcoxon(rar, base, alternative="greater")
            p_val_str = f"{p_val:.4f}"
        except Exception as e:
            p_val_str = f"n.s. ({e})"
    else:
        p_val_str = "n/a (need >=2 paired seeds)"

    # Quick honest summary so you see the real picture immediately.
    def mean(xs):
        return sum(xs) / len(xs) if xs else float("nan")

    print("\n--- REAL AGGREGATE (merged) ---")
    for cond in CONDITIONS:
        print(f"{cond:18s} test_acc={mean(merged[cond]['test_accuracies']):.4f}  "
              f"net_tokens={mean(merged[cond]['net_tokens']):.0f}")
    print(f"Wilcoxon RAR>Baseline p = {p_val_str}")

    results_to_save = {
        "meta": f"Merged per-seed campaign (PyTorch Residual MLP); dataset tag={tag or 'manifold'}",
        "dataset_tag": tag or "manifold",
        "SEEDS": seeds_in_order,
        "CYCLES": cycles,
        "wilcoxon_p_value_RAR_vs_Baseline": p_val_str,
        "data": {
            "dataset": tag or "manifold",
            "SEEDS": seeds_in_order,
            "CYCLES": cycles,
            "conditions": merged,
        },
    }

    out = os.path.join(OUTPUT_DIR, out_name)
    with open(out, "w") as f:
        json.dump(results_to_save, f, indent=2)
    print(f"\nWrote merged results -> {out_name}")


if __name__ == "__main__":
    main()
