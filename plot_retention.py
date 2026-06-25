"""Figure for Proposition 2: best-trial retention vs horizon.
Stateless theory min(1, w/t) overlaid with the measured late-cycle retention (~29%);
RAR's horizon-independent retention (1-rho). No data download; pure model + one measured point.
"""
import os, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.abspath(__file__))
w = 20          # retention window: C_max(4000) / ~192 chars per verbose trial entry
rho = 0.05      # summary infidelity rate -> RAR retains >= 1-rho
t = np.arange(1, 251)
stateless = np.minimum(1.0, w / t)

fig, ax = plt.subplots(figsize=(7, 4.3))
ax.plot(t, stateless, color="#888888", lw=2.2, ls="--",
        label=r"Stateless: $\min(1,\,w/t)$  ($w=20$)")
ax.axhline(1 - rho, color="#d62728", lw=2.2,
           label=r"RAR (summary): $\geq 1-\rho$")
# measured point: stateless late-cycle best-retention ~29% at the 60-cycle campaign
ax.scatter([60], [0.29], s=90, color="#1f1f1f", zorder=5,
           label="Measured (stateless, 60-cyc): 0.29")
# annotation in the open upper-centre area, arrow down to the measured point
ax.annotate("theory $20/60 = 0.33$\nmeasured $0.29$", xy=(60, 0.29), xytext=(108, 0.54),
            fontsize=11, ha="left", va="center",
            arrowprops=dict(arrowstyle="->", color="#555"))
ax.axvspan(1, w, color="#cfe8cf", alpha=0.5)
ax.text(w + 4, 0.62, r"$t\leq w$ (parity)", ha="left", fontsize=10, color="#2a6")
ax.text(235, 0.045, r"$t\gg w$ (gap widens)", ha="right", fontsize=10, color="#a33")
ax.set_xlabel("Cycle horizon $t$")
ax.set_ylabel(r"$\Pr[\text{best-so-far} \in \text{context}]$")
ax.set_ylim(0, 1.10); ax.set_xlim(1, 250)
ax.set_title("Best-trial retention decays as $1/t$; summary memory does not", fontsize=12)
ax.grid(True, ls=":", alpha=0.6)
ax.legend(loc="upper right", fontsize=10, framealpha=0.95)
fig.tight_layout()
out = os.path.join(ROOT, "fig_retention.png")
fig.savefig(out, dpi=160)
print("saved", out)
