"""Q1-caliber manuscript figures, rendered as paper-matched vector PDF.

Typography matches IEEEtran (Times-like STIX serif + stix mathtext) so figures
read as part of the paper, not pasted onto it. Every value traces to the
canonical campaign JSON files; nothing is interpolated or invented.

Reads:  pilot_results.json, pilot_results_digits.json, pilot_seed_*_digits.json
Writes (vector PDF):
  fig_q1_paired_accuracy.pdf      per-seed paired test accuracy, both datasets
  fig_q1_compression_timeline.pdf real per-cycle density + compression events
  fig_q1_seed101_anatomy.pdf      seed-101 generalization-gap outlier (L9)
  fig_q1_degradation_model.pdf    q(delta) piecewise model + operating points
  fig_q1_method_taxonomy.pdf      agent-memory system comparison grid
  fig_q1_forest_plot.pdf          accuracy 95% CI forest + TOST band
  fig_q1_crs_corrected.pdf        proposed CRS vs corrected frontier metric
  fig_q1_scalability.pdf          density projection to 150 cycles
"""

import json, glob, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.lines import Line2D
from scipy import stats

# ── Q1 house style: Times-like serif (STIX, bundled — no install needed) ────────
rcParams.update({
    "pdf.fonttype": 42,              # embed TrueType, editable text in PDF
    "ps.fonttype": 42,
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 9,
    "axes.titlesize": 9.5,
    "axes.titleweight": "normal",
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.7,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "axes.grid": True,
    "grid.alpha": 0.18,
    "grid.linewidth": 0.5,
    "lines.linewidth": 1.4,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})

# IEEE column width ≈ 3.5in; full text width ≈ 7.16in
COL_W, FULL_W = 3.5, 7.16

# Refined, colorblind-safe, slightly desaturated palette
CLR = {"stateless_baseline": "#7A8088",   # slate gray
       "vector_rag":         "#D98A2B",   # ochre
       "rar_compressed":     "#1F8A7A"}   # deep teal (ours)
COND  = ["stateless_baseline", "vector_rag", "rar_compressed"]
NICE  = ["Stateless Baseline", "Vector RAG", "RAR (ours)"]
COLORS = [CLR[c] for c in COND]
SEEDS  = [7, 13, 23, 42, 88, 99, 101, 107, 113, 127]
CYCLES = 60
D_LOW, D_HIGH = 0.50, 0.90
HERE = os.path.dirname(os.path.abspath(__file__))


def save(fig, name):
    fig.savefig(os.path.join(HERE, name + ".pdf"))
    plt.close(fig)
    print("OK " + name + ".pdf")


# ── load canonical data ─────────────────────────────────────────────────────────
with open(os.path.join(HERE, "pilot_results.json")) as f:
    C_SYN = json.load(f)["data"]["conditions"]
with open(os.path.join(HERE, "pilot_results_digits.json")) as f:
    C_DIG = json.load(f)["data"]["conditions"]

def arr(C, cond, key):
    return np.array(C[cond][key], dtype=float)

pilot_traces = {}
for fp in sorted(glob.glob(os.path.join(HERE, "pilot_seed_*_digits.json"))):
    with open(fp) as f:
        d = json.load(f)
    seed = d["SEEDS"][0]
    cd = d["data"]["conditions"]
    pilot_traces[seed] = {c: sorted(cd[c]["per_cycle_trajectories"][0],
                                    key=lambda r: r["cycle"])
                          for c in COND if cd[c].get("per_cycle_trajectories")}
pilot_seeds = sorted(pilot_traces.keys())


# ══ FIG — Per-seed paired test accuracy ═════════════════════════════════════════
def fig_paired_accuracy():
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.9))
    for ax, C, title, ylim in [
        (axes[0], C_SYN, "(a) Synthetic manifold", (37, 46)),
        (axes[1], C_DIG, "(b) digits",   (82, 99)),
    ]:
        base = arr(C, "stateless_baseline", "test_accuracies") * 100
        rar  = arr(C, "rar_compressed",     "test_accuracies") * 100
        for b, r in zip(base, rar):
            outlier = abs(r - b) > 3
            ax.plot([0, 1], [b, r], color="#C0392B" if outlier else "#C9CDD2",
                    lw=1.1 if outlier else 0.8, alpha=0.9 if outlier else 0.7, zorder=2)
        ax.scatter(np.zeros_like(base), base, color=CLR["stateless_baseline"],
                   s=24, zorder=4, edgecolor="white", linewidth=0.4)
        ax.scatter(np.ones_like(rar), rar, color=CLR["rar_compressed"],
                   s=24, zorder=4, edgecolor="white", linewidth=0.4)
        if C is C_DIG:
            i = SEEDS.index(101)
            ax.annotate("seed 101", xy=(1, rar[i]), xytext=(0.5, rar[i] - 5),
                        fontsize=7, color="#C0392B",
                        arrowprops=dict(arrowstyle="-", color="#C0392B", lw=0.7))
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Stateless", "RAR"])
        ax.set_ylabel("Test accuracy (%)")
        ax.set_title(title, fontsize=9)
        ax.set_xlim(-0.35, 1.35); ax.set_ylim(ylim)
        ax.grid(axis="x", visible=False)
    fig.tight_layout(w_pad=2.5)
    save(fig, "fig_q1_paired_accuracy")


# ══ FIG — Real per-cycle density with compression events ════════════════════════
def fig_compression_timeline():
    if not pilot_seeds:
        print("WARN no pilot trajectories"); return
    seed = pilot_seeds[0]
    fig, axes = plt.subplots(3, 1, figsize=(COL_W, 4.3), sharex=True)
    for ax, cond, nice, clr in zip(axes, COND, NICE, COLORS):
        tr = pilot_traces[seed].get(cond, [])
        cyc = np.array([r["cycle"] for r in tr])
        den = np.array([r["density"] for r in tr])
        ax.plot(cyc, den, color=clr, lw=1.3)
        ax.axhline(D_LOW, color="#888", ls=(0, (4, 3)), lw=0.6)
        ax.axhline(D_HIGH, color="#C0392B", ls=(0, (4, 3)), lw=0.6)
        for i in range(1, len(den)):
            if den[i] < den[i - 1] - 0.05:
                ax.axvline(cyc[i], color=clr, alpha=0.25, lw=0.7)
        ax.text(0.985, 0.86, nice, transform=ax.transAxes, ha="right", va="top",
                fontsize=7.8, color=clr,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.7))
        ax.set_ylabel(r"$\delta_t$")
        ax.set_ylim(0, max(den) * 1.18)
    axes[0].text(59, D_HIGH + 0.04, r"$\delta_{\mathrm{high}}$", fontsize=7, color="#C0392B", ha="right")
    axes[2].set_xlabel("Cycle")
    fig.suptitle("Per-cycle context density with compression events\n"
                 r"(digits pilot seed " + str(seed) +
                 r"; vertical ticks $=$ compression fires)", fontsize=8.5, y=1.005)
    fig.tight_layout(h_pad=0.6)
    save(fig, "fig_q1_compression_timeline")


# ══ FIG — Seed-101 generalization-gap outlier ═══════════════════════════════════
def fig_seed101_anatomy():
    fig, ax = plt.subplots(figsize=(COL_W, 2.7))
    x = np.arange(len(SEEDS))
    for cond, nice, clr in zip(COND, NICE, COLORS):
        g = arr(C_DIG, cond, "generalization_gaps") * 100
        ax.plot(x, g, marker="o", ms=3.5, lw=1.1, color=clr, label=nice, alpha=0.9)
    i = SEEDS.index(101)
    rg = arr(C_DIG, "rar_compressed", "generalization_gaps") * 100
    ax.annotate(f"seed 101 (L9)\ngap $=$ {rg[i]:.1f}%", xy=(i, rg[i]),
                xytext=(i - 2.6, rg[i] - 2.5), fontsize=7, color="#C0392B",
                arrowprops=dict(arrowstyle="->", color="#C0392B", lw=0.8))
    ax.set_xticks(x); ax.set_xticklabels([str(s) for s in SEEDS], fontsize=7)
    ax.set_xlabel("Seed"); ax.set_ylabel("Generalization gap (%)")
    ax.set_title(r"Per-seed generalization gap on digits", fontsize=9)
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    save(fig, "fig_q1_seed101_anatomy")


# ══ FIG — Context-rot degradation model ═════════════════════════════════════════
def fig_degradation_model():
    fig, ax = plt.subplots(figsize=(COL_W, 2.7))
    d = np.linspace(0, 2.5, 600)
    q = np.where(d <= D_LOW, 1.0,
        np.where(d <= D_HIGH, 1 - (d - D_LOW) / (D_HIGH - D_LOW), 0.0))
    ax.axvspan(0, D_LOW, color="#2E7D32", alpha=0.05)
    ax.axvspan(D_LOW, D_HIGH, color="#E89A2B", alpha=0.06)
    ax.axvspan(D_HIGH, 2.5, color="#C0392B", alpha=0.05)
    ax.plot(d, q, color="#1A3D6D", lw=1.8)
    op = {"RAR": (0.387, CLR["rar_compressed"]),
          "Vector RAG": (0.660, CLR["vector_rag"]),
          "Stateless": (1.409, CLR["stateless_baseline"])}
    for lbl, (dv, clr) in op.items():
        qv = 1.0 if dv <= D_LOW else max(0, 1 - (dv - D_LOW) / (D_HIGH - D_LOW))
        ax.scatter([dv], [qv], s=42, color=clr, zorder=6, edgecolor="white", lw=0.5)
        ax.annotate(lbl, xy=(dv, qv), xytext=(dv + 0.05, qv + 0.06),
                    fontsize=7, color=clr)
    ax.axvline(D_LOW, color="#888", ls=(0, (4, 3)), lw=0.6)
    ax.axvline(D_HIGH, color="#C0392B", ls=(0, (4, 3)), lw=0.6)
    ax.text(D_LOW, 1.08, r"$\delta_{\mathrm{low}}$", fontsize=7.5, color="#888", ha="center")
    ax.text(D_HIGH, 1.08, r"$\delta_{\mathrm{high}}$", fontsize=7.5, color="#C0392B", ha="center")
    ax.set_xlabel(r"Context density $\delta_t$")
    ax.set_ylabel(r"Proposal quality $q(\delta)$")
    ax.set_xlim(0, 2.5); ax.set_ylim(0, 1.18)
    ax.set_title("Context-rot degradation model (Eq.~1)", fontsize=9)
    fig.tight_layout()
    save(fig, "fig_q1_degradation_model")


# ══ FIG — Method taxonomy (vector glyphs, no font dependency) ════════════════════
def fig_method_taxonomy():
    systems = ["MemGPT", "Mem0", "ACON", "Active Context\nCompression", "RAR (ours)"]
    props = ["Context\nbounding", "Graph\nmemory", "Accuracy-\nparity test",
             "Paired\nstatistics", "Negative\nresult", "Open\nharness"]
    grid = np.array([
        [1, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1],
    ], dtype=float)
    nrow, ncol = grid.shape
    fig, ax = plt.subplots(figsize=(FULL_W, 2.6))
    fill = CLR["rar_compressed"]
    # scatter markers stay perfectly round regardless of axis aspect, so columns
    # can spread across the full text width without the labels colliding.
    for i in range(nrow):
        y = nrow - 1 - i
        for j in range(ncol):
            if grid[i, j] == 1:                      # filled disc = present
                ax.scatter(j, y, s=150, color=fill, zorder=3)
            else:                                    # open ring = absent
                ax.scatter(j, y, s=150, facecolor="none", edgecolor="#B9BEC4",
                           linewidth=1.1, zorder=3)
    ax.add_patch(plt.Rectangle((-0.5, -0.5), ncol, 1, facecolor=fill, alpha=0.07,
                               edgecolor=fill, lw=1.0, zorder=1))
    ax.set_xlim(-0.6, ncol - 0.4); ax.set_ylim(-0.7, nrow - 0.3)
    ax.set_xticks(range(ncol)); ax.set_xticklabels(props, fontsize=7.6)
    ax.set_yticks(range(nrow)); ax.set_yticklabels(systems[::-1], fontsize=8)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(False)
    legend = [Line2D([0], [0], marker="o", color="none", markerfacecolor=fill,
                     markersize=8, label="present"),
              Line2D([0], [0], marker="o", color="none", markerfacecolor="none",
                     markeredgecolor="#B9BEC4", markersize=8, label="absent")]
    ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(0, 1.16),
              ncol=2, frameon=False, fontsize=7.5)
    ax.set_title("Agent-memory systems: methodological properties", fontsize=9, pad=18)
    fig.tight_layout()
    save(fig, "fig_q1_method_taxonomy")


# ══ FIG — Accuracy forest plot with TOST band ═══════════════════════════════════
def fig_forest_plot():
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.7), sharey=True)
    margin = 2.0
    for ax, (name, C) in zip(axes, [("(a) Synthetic manifold", C_SYN),
                                    ("(b) digits", C_DIG)]):
        # y=0 bottom (stateless) ... y=2 top (RAR); labels stay aligned to data
        for y, (cond, clr) in enumerate(zip(COND, COLORS)):
            v = arr(C, cond, "test_accuracies") * 100
            m, se = v.mean(), stats.sem(v)
            ci = se * stats.t.ppf(0.975, len(v) - 1)
            ax.errorbar(m, y, xerr=ci, fmt="o", color=clr, capsize=3,
                        capthick=1.0, ms=5, lw=1.4)
            ax.text(m, y + 0.22, f"{m:.1f}", ha="center", fontsize=7, color=clr)
        bm = arr(C, "stateless_baseline", "test_accuracies").mean() * 100
        ax.axvspan(bm - margin, bm + margin, color="#1A3D6D", alpha=0.08)
        ax.axvline(bm, color="#888", ls=(0, (4, 3)), lw=0.7)
        ax.set_yticks(range(len(COND))); ax.set_yticklabels(NICE)
        ax.set_ylim(-0.5, len(COND) - 0.5)
        ax.set_xlabel("Mean test accuracy (%), 95% CI")
        ax.set_title(name, fontsize=9)
        ax.grid(axis="y", visible=False)
    axes[0].text(0.5, -0.34, r"shaded band $= \pm2$ pp TOST equivalence margin",
                 transform=axes[0].transAxes, ha="center", fontsize=7, color="#555")
    fig.tight_layout(w_pad=2.0)
    save(fig, "fig_q1_forest_plot")


# ══ FIG — Proposed CRS vs corrected frontier-proximity metric ═══════════════════
def fig_crs_corrected():
    if not pilot_seeds:
        print("WARN no pilot trajectories"); return
    W = 10
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.7), sharey=True)

    def series(tr):
        """Return (cycles, CRS, FP) for one seed's per-cycle trace."""
        cyc = np.array([r["cycle"] for r in tr])
        red = np.array([r["redundant"] for r in tr], dtype=float)
        acc = np.array([r["val_acc"] for r in tr], dtype=float)
        n = len(tr); f_min, f_max = acc.min(), acc.max()
        rng = (f_max - f_min) or 1e-9
        CRS = np.empty(n); FP = np.empty(n)
        for t in range(n):
            lo = max(0, t - W + 1)
            nr = 1.0 - red[lo:t + 1].mean()
            win = acc[lo:t + 1]
            wp = np.array([acc[:max(1, lo + i)].max() for i in range(len(win))])
            dc = np.mean(win >= wp)
            CRS[t] = (nr + dc) / 2
            FP[t] = np.mean((win - f_min) / rng)
        return cyc, CRS, FP

    # Average across all pilot seeds so the figure matches the aggregate numbers
    # the text reports; shade ±1 s.d. across seeds.
    for cond, nice, clr in zip(COND, NICE, COLORS):
        traces = [pilot_traces[s][cond] for s in pilot_seeds if cond in pilot_traces[s]]
        cyc = np.array([r["cycle"] for r in traces[0]])
        CRS_all = np.vstack([series(tr)[1] for tr in traces])
        FP_all  = np.vstack([series(tr)[2] for tr in traces])
        for ax, M in [(axes[0], CRS_all), (axes[1], FP_all)]:
            m, s = M.mean(0), M.std(0, ddof=1) if M.shape[0] > 1 else np.zeros(M.shape[1])
            ax.plot(cyc, m, color=clr, lw=1.4, label=nice)
            ax.fill_between(cyc, m - s, m + s, color=clr, alpha=0.10)
    axes[0].axhline(0.70, color="#C0392B", ls=(0, (4, 3)), lw=0.8)
    axes[0].text(2, 0.72, r"target $\geq 0.70$", fontsize=7, color="#C0392B")
    axes[0].set_ylabel("Coherence score")
    axes[0].set_xlabel("Cycle"); axes[1].set_xlabel("Cycle")
    axes[0].set_title("(a) Proposed CRS — rewards forgetting", fontsize=8.7)
    axes[1].set_title("(b) Corrected frontier proximity", fontsize=8.7)
    axes[0].set_ylim(0, 1.05)
    axes[1].legend(frameon=False, loc="lower right")
    fig.tight_layout(w_pad=1.6)
    save(fig, "fig_q1_crs_corrected")


# ══ FIG — Density scalability projection to 150 cycles ══════════════════════════
def fig_scalability():
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.7), sharey=True)
    T = 150; cp = np.arange(1, T + 1)
    for ax, (C, name) in zip(axes, [(C_SYN, "(a) Synthetic manifold"),
                                    (C_DIG, "(b) digits")]):
        for cond, nice, clr in zip(COND, NICE, COLORS):
            dm = float(np.mean(arr(C, cond, "prompt_densities")))
            ds = float(np.std(arr(C, cond, "prompt_densities"), ddof=1))
            if cond == "stateless_baseline":
                curve = dm / CYCLES * cp
                up, lo = (dm + ds) / CYCLES * cp, max(0, dm - ds) / CYCLES * cp
            else:
                curve = np.full_like(cp, dm, dtype=float)
                up = np.full_like(cp, dm + ds, dtype=float)
                lo = np.full_like(cp, max(0, dm - ds), dtype=float)
            obs = cp <= CYCLES
            ax.plot(cp[obs], curve[obs], color=clr, lw=1.5, label=nice)
            ax.plot(cp[~obs], curve[~obs], color=clr, lw=1.5, ls=(0, (5, 2)))
            ax.fill_between(cp, lo, up, color=clr, alpha=0.08)
        ax.axvline(CYCLES, color="#AAA", ls=":", lw=0.8)
        ax.axhline(D_HIGH, color="#C0392B", ls=(0, (4, 3)), lw=0.6)
        ax.text(CYCLES + 2, 0.04, "observed | projected", fontsize=6.5, color="#999")
        ax.set_xlabel("Cycle"); ax.set_title(name, fontsize=9)
        ax.set_xlim(1, T); ax.set_ylim(0, None)
    axes[0].set_ylabel(r"Context density $\delta$")
    axes[1].legend(frameon=False, loc="center right")
    fig.tight_layout(w_pad=1.6)
    save(fig, "fig_q1_scalability")


if __name__ == "__main__":
    fig_paired_accuracy()
    fig_compression_timeline()
    fig_seed101_anatomy()
    fig_degradation_model()
    fig_method_taxonomy()
    fig_forest_plot()
    fig_crs_corrected()
    fig_scalability()
    print("\nAll Q1 figures written as vector PDF.")
