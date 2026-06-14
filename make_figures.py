"""Regenerate all manuscript figures from the real pilot_results.json.

Every figure is derived from the canonical merged campaign file so the paper's
visuals can never drift from the reported numbers again. Run:

    python make_figures.py

Produces (300 dpi PNGs in the working directory):
    fig2_crs_trajectory.png  - test-accuracy distribution + net-token cost
    fig3_density.png          - context density vs rot thresholds
    fig4_ablation_bar.png     - late-cycle exploration redundancy
    fig5_degradation.png      - context-rot model q(delta) with operating points
    fig6_pareto.png           - accuracy vs token cost Pareto view (bonus)
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# ---- house style ----------------------------------------------------------
rcParams.update({
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "medium",
    "axes.labelsize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.6,
    "savefig.bbox": "tight",
})

COND = ["stateless_baseline", "vector_rag", "rar_compressed"]
NICE = ["Stateless\nbaseline", "Vector RAG", "RAR compressed\n(ours)"]
CLR = {"stateless_baseline": "#9AA0A6",   # neutral gray
       "vector_rag": "#E8943A",           # amber
       "rar_compressed": "#2FA89B"}       # teal (ours)
COLORS = [CLR[c] for c in COND]

with open("pilot_results.json") as f:
    R = json.load(f)
C = R["data"]["conditions"]
P = R.get("wilcoxon_p_value_RAR_vs_Baseline", "n/a")


def arr(cond, metric):
    return np.array(C[cond][metric], dtype=float)


def mean(cond, metric):
    return float(np.mean(arr(cond, metric)))


def sd(cond, metric):
    return float(np.std(arr(cond, metric), ddof=1))


# ---- fig2: test accuracy distribution + net-token cost --------------------
def fig2():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.2))
    acc = [arr(c, "test_accuracies") * 100 for c in COND]
    bp = ax1.boxplot(acc, widths=0.55, patch_artist=True, showfliers=False,
                     medianprops=dict(color="#333", lw=1.3))
    for patch, c in zip(bp["boxes"], COLORS):
        patch.set_facecolor(c); patch.set_alpha(0.35); patch.set_edgecolor(c)
    rng = np.random.default_rng(0)
    for i, (a, c) in enumerate(zip(acc, COLORS), start=1):
        x = rng.normal(i, 0.06, size=len(a))
        ax1.scatter(x, a, s=26, color=c, edgecolor="white", linewidth=0.6, zorder=3)
    ax1.set_xticks([1, 2, 3]); ax1.set_xticklabels(NICE)
    ax1.set_ylabel("Test accuracy (%)")
    ax1.set_title("Test accuracy across 10 seeds")
    ax1.annotate(f"RAR vs baseline: Wilcoxon $p$ = {P} (n.s.)",
                 xy=(0.5, 0.03), xycoords="axes fraction", ha="center", fontsize=9.5,
                 bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#bbb", alpha=0.9))

    toks = [mean(c, "net_tokens") for c in COND]
    bars = ax2.bar(NICE, toks, color=COLORS, alpha=0.9, width=0.6, edgecolor="white")
    ax2.set_ylabel("Net tokens (campaign total)")
    ax2.set_title("Token cost at equal accuracy")
    base = toks[0]
    for b, t, c in zip(bars, toks, COND):
        pct = (t - base) / base * 100
        lbl = f"{t/1000:.0f}k" + ("" if c == "stateless_baseline" else f"\n({pct:+.0f}%)")
        ax2.text(b.get_x() + b.get_width()/2, t + base*0.012, lbl, ha="center",
                 va="bottom", fontsize=9.5)
    ax2.set_ylim(0, base * 1.18)
    fig.tight_layout()
    fig.savefig("fig2_crs_trajectory.png"); plt.close(fig)


# ---- fig3: context density vs rot thresholds ------------------------------
def fig3():
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    dens = [mean(c, "prompt_densities") for c in COND]
    err = [sd(c, "prompt_densities") for c in COND]
    bars = ax.bar(NICE, dens, yerr=err, capsize=4, color=COLORS, alpha=0.9,
                  width=0.6, edgecolor="white")
    ax.axhline(0.58, ls="--", lw=1.1, color="#C0392B")
    ax.axhline(0.90, ls=":", lw=1.1, color="#7A5AF0")
    ax.text(2.46, 0.58, r" rot threshold $\tau=0.58$", color="#C0392B", va="bottom", fontsize=9)
    ax.text(2.46, 0.90, r" high-pressure $\delta=0.90$", color="#7A5AF0", va="bottom", fontsize=9)
    for b, d in zip(bars, dens):
        ax.text(b.get_x()+b.get_width()/2, d+0.03, f"{d:.3f}", ha="center", fontsize=10)
    ax.set_ylabel(r"Mean prompt density $\delta$")
    ax.set_title("Context density: only RAR stays below the rot threshold")
    ax.set_ylim(0, 1.55)
    fig.tight_layout()
    fig.savefig("fig3_density.png"); plt.close(fig)


# ---- fig4: late-cycle exploration redundancy ------------------------------
def fig4():
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    red = [mean(c, "redundancies") for c in COND]
    err = [sd(c, "redundancies") for c in COND]
    bars = ax.bar(NICE, red, yerr=err, capsize=4, color=COLORS, alpha=0.9,
                  width=0.6, edgecolor="white")
    for b, v in zip(bars, red):
        ax.text(b.get_x()+b.get_width()/2, v+0.6, f"{v:.1f}", ha="center", fontsize=10)
    ax.set_ylabel("Mean late-cycle redundant proposals")
    ax.set_title("Vector RAG re-explores; RAR stays lean")
    ax.set_ylim(0, max(red)*1.25)
    fig.tight_layout()
    fig.savefig("fig4_ablation_bar.png"); plt.close(fig)


# ---- fig5: context-rot degradation model with operating points ------------
def fig5():
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    d = np.linspace(0, 1.55, 400)
    dlow, dhigh = 0.50, 0.90
    q = np.clip((dhigh - d) / (dhigh - dlow), 0, 1)
    ax.plot(d, q, color="#333", lw=1.8, label=r"proposal quality $q(\delta)$")
    ax.axvline(0.58, ls="--", lw=1.0, color="#C0392B")
    ax.text(0.6, 0.05, r"$\tau=0.58$", color="#C0392B", fontsize=9)
    pts = {"rar_compressed": "RAR", "vector_rag": "Vector RAG", "stateless_baseline": "Baseline"}
    for c, name in pts.items():
        dv = mean(c, "prompt_densities")
        qv = float(np.clip((dhigh - dv) / (dhigh - dlow), 0, 1))
        ax.scatter([dv], [qv], s=130, color=CLR[c], edgecolor="black", zorder=5)
        ax.annotate(f"{name}\n$\\delta$={dv:.3f}", (dv, qv),
                    textcoords="offset points", xytext=(6, 10), fontsize=9)
    ax.set_xlabel(r"Context density $\delta$ (ratio to $C_{\max}$)")
    ax.set_ylabel(r"Modeled proposal quality $q$")
    ax.set_title("Where each condition operates on the context-rot curve")
    ax.set_xlim(0, 1.55); ax.set_ylim(-0.05, 1.1)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig("fig5_degradation.png"); plt.close(fig)


# ---- fig6: Pareto (bonus) -------------------------------------------------
def fig6():
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    for c, name in zip(COND, ["Stateless baseline", "Vector RAG", "RAR compressed"]):
        tk = arr(c, "net_tokens"); ac = arr(c, "test_accuracies") * 100
        ax.scatter(tk, ac, s=28, color=CLR[c], alpha=0.35)
        ax.scatter([tk.mean()], [ac.mean()], s=220, color=CLR[c],
                   edgecolor="black", zorder=5, label=name)
    ax.annotate("cheapest at\nequal accuracy",
                xy=(mean('rar_compressed','net_tokens'), mean('rar_compressed','test_accuracies')*100),
                xytext=(165000, 39.0),
                arrowprops=dict(arrowstyle="->", color="#333"), fontsize=9.5, ha="center")
    ax.set_xlabel("Net tokens (lower = cheaper)")
    ax.set_ylabel("Test accuracy (%)")
    ax.set_title("Accuracy-cost Pareto view")
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    fig.tight_layout()
    fig.savefig("fig6_pareto.png"); plt.close(fig)


if __name__ == "__main__":
    fig2(); fig3(); fig4(); fig5(); fig6()
    print("Wrote: fig2_crs_trajectory.png fig3_density.png fig4_ablation_bar.png "
          "fig5_degradation.png fig6_pareto.png")
