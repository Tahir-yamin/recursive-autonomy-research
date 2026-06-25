"""Efficiency figure from the REAL Task A campaign (the synthetic study in the paper).
Four panels: net tokens, prompt density, late-cycle redundancy, loop latency, per condition.
"""
import os, json, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size":13,"axes.titlesize":13,"axes.labelsize":12,"xtick.labelsize":11,"ytick.labelsize":11})

ROOT = os.path.dirname(os.path.abspath(__file__))
c = json.load(open(os.path.join(ROOT, "pilot_results_taskA.json")))["data"]["conditions"]
CONDS = ["stateless_baseline", "vector_rag", "rar_compressed"]
LAB = ["Stateless", "Vector RAG", "RAR (ours)"]
COL = ["#bbbbbb", "#7fb3d5", "#d62728"]


def agg(field, per_cycle=False):
    out = []
    for k in CONDS:
        v = c[k][field]
        out.append(np.mean([np.mean(x) for x in v]) if per_cycle and isinstance(v[0], list)
                   else np.mean(v))
    return out


metrics = [
    ("Net tokens (K)", [t / 1000 for t in agg("net_tokens")], "{:.0f}"),
    ("Prompt density $\\delta$", agg("prompt_densities"), "{:.2f}"),
    ("Late redundancy", agg("redundancies"), "{:.1f}"),
    ("Loop latency (s)", agg("wall_clock_latencies"), "{:.0f}"),
]

fig, axes = plt.subplots(1, 4, figsize=(13, 3.6))
for ax, (title, vals, fmt) in zip(axes, metrics):
    bars = ax.bar(LAB, vals, color=COL, alpha=0.8)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, fmt.format(v), ha="center", va="bottom", fontsize=9)
    ax.set_title(title, fontsize=11)
    ax.set_xticklabels(LAB, rotation=20, ha="right", fontsize=8.5)
    ax.set_ylim(0, max(vals) * 1.18)
    ax.grid(True, axis="y", ls=":", alpha=0.5)

tok = agg("net_tokens"); dens = agg("prompt_densities")
fig.suptitle(f"Efficiency on the synthetic campaign ($N{{=}}10$, 60 cycles): "
             f"RAR cuts tokens {100*(1-tok[2]/tok[0]):.0f}% and density {100*(1-dens[2]/dens[0]):.0f}% vs baseline, at parity accuracy",
             fontsize=11)
fig.tight_layout(rect=[0, 0.02, 1, 0.92])
out = os.path.join(ROOT, "fig_efficiency.png")
fig.savefig(out, dpi=160)
print("saved", out, "| tokens -%.1f%% | density -%.1f%%" % (100*(1-tok[2]/tok[0]), 100*(1-dens[2]/dens[0])))
