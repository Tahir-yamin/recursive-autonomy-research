"""Camera-ready three-task accuracy figure from the real released data.
One panel per benchmark (different y-scales), box = 10 seeds per condition, RAR highlighted,
annotated with seeds-won and one-sided Wilcoxon p. Replaces the stale fig2_crs_trajectory.
"""
import os, json, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon

ROOT = os.path.dirname(os.path.abspath(__file__))
CONDS = ["stateless_baseline", "vector_rag", "rar_compressed"]
LABELS = ["Stateless", "Vector RAG", "RAR (ours)"]
COLORS = ["#bbbbbb", "#7fb3d5", "#d62728"]


def task_accs(name):
    if name == "A":
        c = json.load(open(os.path.join(ROOT, "pilot_results_taskA.json")))["data"]["conditions"]
        return [np.array(c[k]["test_accuracies"]) * 100 for k in CONDS]
    if name == "CIFAR":
        d = json.load(open(os.path.join(ROOT, "taskB_cifar_N10.json")))
        s = sorted(d["rar_compressed"], key=int)
        return [np.array([d[k][i] for i in s]) * 100 for k in CONDS]
    if name == "digits":
        c = json.load(open(os.path.join(ROOT, "pilot_results_digits.json")))["data"]["conditions"]
        return [np.array(c[k]["test_accuracies"]) * 100 for k in CONDS]


panels = [("Synthetic manifold (hard)", "A"),
          ("CIFAR-10→PCA-64 (hard)", "CIFAR"),
          ("Digits (easy control)", "digits")]

fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
for ax, (title, key) in zip(axes, panels):
    b, v, r = task_accs(key)
    bp = ax.boxplot([b, v, r], widths=0.6, patch_artist=True, showmeans=True,
                    meanprops=dict(marker="D", markerfacecolor="black", markersize=4))
    for patch, col in zip(bp["boxes"], COLORS):
        patch.set_facecolor(col); patch.set_alpha(0.65)
    for i, arr in enumerate([b, v, r]):
        ax.scatter(np.full(len(arr), i + 1) + np.random.uniform(-0.08, 0.08, len(arr)),
                   arr, s=12, color="black", alpha=0.5, zorder=3)
    _, p = wilcoxon(r, b, alternative="greater")
    won = int((r > b).sum())
    ax.set_title(f"{title}\nRAR {won}/10, Wilcoxon $p$={p:.3f}", fontsize=10)
    ax.set_xticks([1, 2, 3]); ax.set_xticklabels(LABELS, fontsize=8, rotation=12)
    ax.grid(True, axis="y", ls=":", alpha=0.5)
    ax.set_ylabel("Test accuracy (%)") if key == "A" else None

fig.suptitle("Test-vault accuracy across three benchmarks ($N{=}10$ seeds, 60 cycles): "
             "RAR edges the baseline on hard tasks, neutral on the easy control",
             fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.95])
out = os.path.join(ROOT, "fig_threetask.png")
fig.savefig(out, dpi=160)
print("saved", out)
