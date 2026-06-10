"""Generate the central Phase-2 figure from pilot_results.json:
left  — mean best-found validation accuracy vs cycle per condition (95% band),
right — fraction of seeds whose global-best trial was still visible in the prompt
        (the direct context-rot signal; stateless should decay, RAR should not).

Usage: python plot_best_found.py  [results.json]  (defaults to pilot_results.json)
Output: fig_best_found_vs_cycle.png (workspace root)
"""
import json
import sys
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJECT_ROOT, "pilot_results.json")
d = json.load(open(path, encoding="utf-8"))
conds = d["data"]["conditions"]

STYLE = {
    "stateless_baseline": ("Stateless Baseline", "#888888", "--"),
    "vector_rag": ("Vector RAG", "#1f77b4", "-."),
    "rar_compressed": ("RAR (Ours)", "#d62728", "-"),
}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

plotted_any = False
for cond, (label, color, ls) in STYLE.items():
    trajs = conds.get(cond, {}).get("best_found_trajectories", [])
    if not trajs:
        continue
    plotted_any = True
    L = min(len(t) for t in trajs)
    M = np.array([t[:L] for t in trajs]) * 100.0
    mean = M.mean(0)
    sem = M.std(0) / max(1, np.sqrt(len(M)))
    x = np.arange(1, L + 1)
    ax1.plot(x, mean, ls, color=color, label=f"{label} (n={len(M)})", linewidth=2)
    ax1.fill_between(x, mean - 1.96 * sem, mean + 1.96 * sem, color=color, alpha=0.15)

    ctx = conds.get(cond, {}).get("best_in_context_trajectories", [])
    if ctx:
        Lc = min(len(t) for t in ctx)
        C = np.array([[1.0 if v else 0.0 for v in t[:Lc]] for t in ctx])
        ax2.plot(np.arange(1, Lc + 1), C.mean(0) * 100, ls, color=color,
                 label=label, linewidth=2)

if not plotted_any:
    raise SystemExit("No best_found_trajectories in this results file (pre-Phase-2 data).")

ax1.set_xlabel("Cycle"); ax1.set_ylabel("Best-found validation accuracy (%)")
ax1.set_title("Best-found accuracy vs cycle")
ax1.grid(True, linestyle=":", alpha=0.6); ax1.legend(loc="lower right")

ax2.set_xlabel("Cycle"); ax2.set_ylabel("Global-best visible in prompt (% of seeds)")
ax2.set_title("Context-rot signal: is the best trial still in context?")
ax2.set_ylim(-5, 105)
ax2.grid(True, linestyle=":", alpha=0.6); ax2.legend(loc="lower left")

fig.suptitle(f"RAR extended evaluation — {len(d.get('SEEDS', []))} seeds, "
             f"{d.get('CYCLES', '?')} cycles, TASK={os.environ.get('TASK', '?')}")
fig.tight_layout()
out = os.path.join(PROJECT_ROOT, "fig_best_found_vs_cycle.png")
fig.savefig(out, dpi=150)
print("Saved", out)
