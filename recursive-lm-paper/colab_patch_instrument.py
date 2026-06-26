# ============================================================================
# COLAB PATCH CELL -- run this RIGHT AFTER the git-clone cell (cell 3) and
# BEFORE the seed-run cells (13-22). It instruments the cloned
# run_pilot_experiment.py to persist per-cycle trajectories, so the campaign
# produces the data needed for a REAL Coherence-Retention-Score trajectory.
# Idempotent: safe to run more than once. Touches only the cloned file.
# ============================================================================
import os, io

PATH = "/content/recursive-autonomy-research/run_pilot_experiment.py"
src = io.open(PATH, encoding="utf-8").read()

if "per_cycle_trajectories" in src:
    print("Already instrumented -- nothing to do.")
else:
    # 1) Add the per-seed trajectory list to each condition's result dict.
    src = src.replace(
        '            "generalization_gaps": []\n        }',
        '            "generalization_gaps": [],\n'
        '            "per_cycle_trajectories": []\n        }')

    # 2) Initialise a fresh per-cycle buffer at the start of each condition run.
    src = src.replace(
        "                start_time = time.time()\n"
        "                consolidator = AsyncMemoryConsolidator()",
        "                start_time = time.time()\n"
        "                consolidator = AsyncMemoryConsolidator()\n"
        "                cycle_trace = []  # per-cycle records for the rot trajectory")

    # 3) Append one record per cycle (density, accuracy, running-best, redundancy).
    src = src.replace(
        "                        densities.append(len(prompt) / 4000.0)\n"
        '                        print(f"  Proposed: {config} -> Val Acc: {acc:.4f} (Redundant: {is_redundant})")',
        "                        densities.append(len(prompt) / 4000.0)\n"
        "                        cycle_trace.append({\n"
        '                            "cycle": cycle,\n'
        '                            "density": len(prompt) / 4000.0,\n'
        '                            "val_acc": acc,\n'
        '                            "running_best": max(t["acc"] for t in trials),\n'
        '                            "redundant": int(is_redundant),\n'
        '                            "mode": mode,\n'
        "                        })\n"
        '                        print(f"  Proposed: {config} -> Val Acc: {acc:.4f} (Redundant: {is_redundant})")')

    # 4) Persist the trajectory alongside the per-seed scalars.
    src = src.replace(
        '                campaign_results["conditions"][cond]["generalization_gaps"].append(abs(max(val_accs) - test_acc))',
        '                campaign_results["conditions"][cond]["generalization_gaps"].append(abs(max(val_accs) - test_acc))\n'
        '                campaign_results["conditions"][cond]["per_cycle_trajectories"].append(cycle_trace)')

    # A fully-applied patch adds: 2x "per_cycle_trajectories" (dict-init + store),
    # 1x "cycle_trace = []" (init), and 1x "cycle_trace.append(" (per-cycle record).
    ok = (src.count("per_cycle_trajectories") == 2
          and "cycle_trace = []" in src
          and "cycle_trace.append(" in src)
    assert ok, "patch did not fully apply -- the cloned file's text did not match all anchors"
    io.open(PATH, "w", encoding="utf-8").write(src)
    print("Instrumented OK (all 4 edits applied). Re-run the seed cells to capture per-cycle data.")
