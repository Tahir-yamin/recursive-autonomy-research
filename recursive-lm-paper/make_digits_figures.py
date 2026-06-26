"""Publication-quality figures for the digits real-dataset replication (Sec. V-B).

Every figure is computed directly from the per-seed arrays in
pilot_results_digits.json / pilot_results_digits_classical.json -- no synthetic
or smoothed data. The set is deliberately honest: it shows RAR's token frugality
AND the seed-101 compression-collapse failure AND classical Bayesian opt matching
accuracy at zero tokens. Run: python make_digits_figures.py
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "mathtext.fontset": "dejavuserif",
    "axes.grid": True,
    "grid.linestyle": "--",
    "grid.alpha": 0.5,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

C = {  # consistent condition colors
    "stateless_baseline": "#b41e1e",
    "vector_rag": "#1c4f8a",
    "rar_compressed": "#2ca02c",
    "bayesian_opt": "#7b3fa0",
    "random_search": "#7f7f7f",
}
LBL = {
    "stateless_baseline": "Stateless",
    "vector_rag": "Vector RAG",
    "rar_compressed": "RAR (ours)",
    "bayesian_opt": "Bayesian opt",
    "random_search": "Random",
}

llm = json.load(open(os.path.join(HERE, "pilot_results_digits.json")))["data"]["conditions"]
cls = json.load(open(os.path.join(HERE, "pilot_results_digits_classical.json")))["data"]["conditions"]
seeds = json.load(open(os.path.join(HERE, "pilot_results_digits.json")))["SEEDS"]
cond = dict(llm); cond.update(cls)


def arr(c, m):
    return np.asarray(cond[c][m], dtype=float)


def save(fig, name):
    p = os.path.join(HERE, name)
    fig.savefig(p)
    plt.close(fig)
    print("wrote", name)


# --- Fig A: accuracy-vs-token Pareto (classical at zero tokens, honestly) -----
def fig_pareto():
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for c in ["stateless_baseline", "vector_rag", "rar_compressed"]:
        x = arr(c, "net_tokens") / 1000.0
        y = arr(c, "test_accuracies") * 100
        ax.scatter(x, y, s=18, color=C[c], alpha=0.35, edgecolors="none")
        ax.scatter(x.mean(), y.mean(), s=180, color=C[c], edgecolors="black",
                   linewidths=1.2, marker="o", zorder=5, label=LBL[c])
    # classical: zero language-model tokens -> x=0
    for c in ["bayesian_opt", "random_search"]:
        y = arr(c, "test_accuracies") * 100
        ax.scatter(0, y.mean(), s=170, color=C[c], edgecolors="black",
                   linewidths=1.2, marker="D", zorder=5, label=LBL[c] + " (0 tok)")
    ax.set_xlabel("Net language-model tokens per campaign (thousands)", fontweight="bold")
    ax.set_ylabel("Test accuracy (%)", fontweight="bold")
    ax.set_title(r"$\mathbf{Accuracy\!-\!cost\ frontier\ on\ digits}$")
    ax.set_ylim(82, 99)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.95)
    ax.annotate("classical HPO ties\naccuracy at 0 tokens",
                xy=(0, 95.7), xytext=(70, 88), fontsize=8,
                arrowprops=dict(arrowstyle="->", color="black", lw=0.8))
    save(fig, "fig_digits_pareto.png")


# --- Fig B: efficiency reductions vs baseline (Holm-significant) ---------------
def fig_reductions():
    metrics = [("net_tokens", "Net tokens"), ("prompt_densities", "Context density"),
               ("wall_clock_latencies", "Loop latency")]
    base = {m: arr("stateless_baseline", m).mean() for m, _ in metrics}
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    x = np.arange(len(metrics)); w = 0.38
    for i, c in enumerate(["vector_rag", "rar_compressed"]):
        red = [100 * (arr(c, m).mean() - base[m]) / base[m] for m, _ in metrics]
        bars = ax.bar(x + (i - 0.5) * w, red, w, color=C[c], label=LBL[c],
                      edgecolor="black", linewidth=0.6)
        for b, r in zip(bars, red):
            ax.text(b.get_x() + b.get_width() / 2, r - 3, f"{r:.0f}%",
                    ha="center", va="top", fontsize=8, color="white", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels([n for _, n in metrics])
    ax.set_ylabel("Change vs. Stateless Baseline (%)", fontweight="bold")
    ax.set_title(r"$\mathbf{What\ RAR\ cuts\ on\ digits}$"
                 "\n(RAR vs baseline: Holm-corrected $p=0.008$, all three)")
    ax.axhline(0, color="black", lw=0.8)
    ax.legend(loc="lower left", fontsize=8)
    save(fig, "fig_digits_reductions.png")


# --- Fig C: per-seed paired token usage (every seed drops ~70%) ---------------
def fig_token_slope():
    b = arr("stateless_baseline", "net_tokens") / 1000.0
    r = arr("rar_compressed", "net_tokens") / 1000.0
    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    for i in range(len(b)):
        ax.plot([0, 1], [b[i], r[i]], color="#999999", lw=0.9, zorder=1)
    ax.scatter(np.zeros_like(b), b, color=C["stateless_baseline"], s=42, zorder=3)
    ax.scatter(np.ones_like(r), r, color=C["rar_compressed"], s=42, zorder=3)
    ax.scatter(0, b.mean(), color=C["stateless_baseline"], s=150, edgecolors="black", zorder=4)
    ax.scatter(1, r.mean(), color=C["rar_compressed"], s=150, edgecolors="black", zorder=4)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Stateless", "RAR (ours)"], fontweight="bold")
    ax.set_xlim(-0.3, 1.3)
    ax.set_ylabel("Net tokens per campaign (thousands)", fontweight="bold")
    ax.set_title(r"$\mathbf{Per\!-\!seed\ token\ cost\ (paired,\ N\!=\!10)}$")
    ax.annotate(f"mean -69.8%\n(every seed)", xy=(1, r.mean()), xytext=(0.45, 230),
                fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.8))
    save(fig, "fig_digits_token_slope.png")


# --- Fig D: generalization gap per seed, seed-101 failure visible -------------
def fig_gengap():
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    x = np.arange(len(seeds)); w = 0.26
    for i, c in enumerate(["stateless_baseline", "vector_rag", "rar_compressed"]):
        g = arr(c, "generalization_gaps") * 100
        ax.bar(x + (i - 1) * w, g, w, color=C[c], label=LBL[c],
               edgecolor="black", linewidth=0.4)
    j = seeds.index(101)
    ax.annotate("seed 101:\nRAR compression\ncollapse (L9)",
                xy=(x[j] + w, arr("rar_compressed", "generalization_gaps")[j] * 100),
                xytext=(x[j] - 2.2, 11), fontsize=8, color="#7a0000",
                arrowprops=dict(arrowstyle="->", color="#7a0000", lw=1.0))
    ax.set_xticks(x); ax.set_xticklabels(seeds)
    ax.set_xlabel("Seed", fontweight="bold")
    ax.set_ylabel(r"Generalization gap $|Val-Test|$ (%)", fontweight="bold")
    ax.set_title(r"$\mathbf{Per\!-\!seed\ generalization\ gap\ on\ digits}$")
    ax.legend(loc="upper right", fontsize=8, ncol=3)
    save(fig, "fig_digits_gengap.png")


# --- Fig E: accuracy distribution across all five conditions ------------------
def fig_accuracy_box():
    order = ["stateless_baseline", "vector_rag", "rar_compressed", "bayesian_opt", "random_search"]
    data = [arr(c, "test_accuracies") * 100 for c in order]
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    bp = ax.boxplot(data, patch_artist=True, widths=0.6,
                    medianprops=dict(color="black"))
    for patch, c in zip(bp["boxes"], order):
        patch.set_facecolor(C[c]); patch.set_alpha(0.65)
    for i, c in enumerate(order):
        y = data[i]; ax.scatter(np.full_like(y, i + 1), y, s=12,
                                color="black", alpha=0.5, zorder=3)
    ax.set_xticklabels([LBL[c] for c in order], rotation=12)
    ax.set_ylabel("Test accuracy (%)", fontweight="bold")
    ax.set_title(r"$\mathbf{Test\ accuracy\ by\ condition\ (digits,\ N\!=\!10)}$")
    ax.axhspan(94, 97, color="green", alpha=0.05)
    save(fig, "fig_digits_accuracy_box.png")


# --- Fig F: redundancy by condition (honest: baseline lowest) -----------------
def fig_redundancy():
    order = ["stateless_baseline", "vector_rag", "rar_compressed"]
    means = [arr(c, "redundancies").mean() for c in order]
    sds = [arr(c, "redundancies").std(ddof=1) for c in order]
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    bars = ax.bar([LBL[c] for c in order], means, yerr=sds, capsize=5,
                  color=[C[c] for c in order], edgecolor="black", linewidth=0.6, alpha=0.85)
    for b, m in zip(bars, means):
        ax.text(b.get_x() + b.get_width() / 2, m + 0.6, f"{m:.1f}",
                ha="center", fontsize=9, fontweight="bold")
    ax.set_ylabel("Mean late-cycle redundancy", fontweight="bold")
    ax.set_title(r"$\mathbf{Exploration\ redundancy\ (digits)}$")
    save(fig, "fig_digits_redundancy.png")


if __name__ == "__main__":
    fig_pareto(); fig_reductions(); fig_token_slope()
    fig_gengap(); fig_accuracy_box(); fig_redundancy()
    print("All digits figures generated.")
