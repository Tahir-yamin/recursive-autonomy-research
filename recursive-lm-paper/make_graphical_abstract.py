"""One-page graphical abstract for sharing with reviewers (vector PDF).

Tells the whole story in one glance: the problem (context rot), the mechanism
(compress + memory map), the validated result (~70% cheaper, same accuracy),
and the honest negative result. Numbers trace to the campaign JSON.
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

rcParams.update({
    "pdf.fonttype": 42, "font.family": "serif",
    "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix", "savefig.bbox": "tight",
})
TEAL, GRAY, OCHRE, INK = "#1F8A7A", "#7A8088", "#D98A2B", "#21303a"
HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "pilot_results.json")) as f:
    C = json.load(f)["data"]["conditions"]
base_tok = np.mean(C["stateless_baseline"]["net_tokens"])
rar_tok  = np.mean(C["rar_compressed"]["net_tokens"])
base_acc = np.mean(C["stateless_baseline"]["test_accuracies"]) * 100
rar_acc  = np.mean(C["rar_compressed"]["test_accuracies"]) * 100

fig = plt.figure(figsize=(8.0, 4.6))
fig.suptitle("Recursive Autonomous Research (RAR): token-bounded agent memory",
             fontsize=13, fontweight="bold", color=INK, y=0.99)
fig.text(0.5, 0.915, "Keep a long-running AI agent affordable by compressing its own history "
         "as it works — same accuracy, a third of the cost.",
         ha="center", fontsize=9.5, color="#48606b")

# ---- left: the problem vs the fix (schematic) -------------------------------
axL = fig.add_axes([0.04, 0.10, 0.40, 0.74]); axL.axis("off")
axL.set_xlim(0, 10); axL.set_ylim(0, 10)
axL.text(5, 9.4, "The problem: “context rot”", ha="center", fontsize=10,
         fontweight="bold", color=INK)
# growing log (baseline)
for i, h in enumerate(np.linspace(0.6, 4.2, 6)):
    axL.add_patch(FancyBboxPatch((0.6, 4.7), 2.6, h/6*4, boxstyle="round,pad=0.02",
                  fc=GRAY, ec="none", alpha=0.25 + i*0.12, zorder=i))
axL.text(1.9, 4.2, "log grows\nevery cycle\n→ cost ↑, reasoning ↓",
         ha="center", va="top", fontsize=8, color=GRAY)
# arrow
axL.add_patch(FancyArrowPatch((3.6, 6.0), (5.2, 6.0), arrowstyle="-|>",
              mutation_scale=14, color=INK, lw=1.4))
axL.text(4.4, 6.45, "RAR", ha="center", fontsize=8.5, color=TEAL, fontweight="bold")
# bounded box (RAR)
axL.add_patch(FancyBboxPatch((5.6, 4.9), 2.6, 1.4, boxstyle="round,pad=0.03",
              fc=TEAL, ec="none", alpha=0.85))
axL.text(6.9, 5.6, "compress +\nmemory map", ha="center", va="center",
         fontsize=8, color="white", fontweight="bold")
axL.text(6.9, 4.4, "bounded, constant-size\nworking memory", ha="center", va="top",
         fontsize=8, color=TEAL)
axL.text(5, 1.6, "An AI research agent normally keeps a running log of everything\n"
         "it has tried. RAR periodically summarises it and stores past results\n"
         "in a small graph — so memory stays small instead of ballooning.",
         ha="center", va="center", fontsize=7.6, color="#48606b")

# ---- right top: cost bar -----------------------------------------------------
axT = fig.add_axes([0.55, 0.50, 0.40, 0.34])
axT.bar([0, 1], [base_tok/1e3, rar_tok/1e3], color=[GRAY, TEAL], width=0.6)
axT.set_xticks([0, 1]); axT.set_xticklabels(["Stateless\nbaseline", "RAR\n(ours)"], fontsize=8)
axT.set_ylabel("Net tokens (×10³)", fontsize=8.5)
red = (base_tok - rar_tok) / base_tok * 100
axT.annotate(f"−{red:.0f}% cost", xy=(1, rar_tok/1e3), xytext=(0.5, base_tok/1e3*0.82),
             fontsize=9, color=TEAL, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=TEAL, lw=1.2))
for s in ["top", "right"]: axT.spines[s].set_visible(False)
axT.set_title("Validated: ~70% cheaper", fontsize=9.5, color=INK, loc="left")

# ---- right bottom: accuracy parity ------------------------------------------
axB = fig.add_axes([0.55, 0.10, 0.40, 0.28])
axB.scatter([base_acc], [0.6], s=70, color=GRAY, zorder=3)
axB.scatter([rar_acc], [0.4], s=70, color=TEAL, zorder=3)
axB.axvspan(base_acc-2, base_acc+2, color="#1A3D6D", alpha=0.10)
axB.axvline(base_acc, color=GRAY, ls="--", lw=1)
axB.text(base_acc, 0.92, "±2 pp equivalence band", ha="center", fontsize=7, color="#48606b")
axB.text(base_acc, 0.6, "  baseline", va="center", fontsize=8, color=GRAY)
axB.text(rar_acc, 0.4, "  RAR", va="center", fontsize=8, color=TEAL)
axB.set_ylim(0.2, 1.05); axB.set_yticks([])
axB.set_xlabel("Mean test accuracy (%)", fontsize=8.5)
for s in ["top", "right", "left"]: axB.spines[s].set_visible(False)
axB.set_title("...at statistically equal accuracy", fontsize=9.5, color=INK, loc="left")

# ---- honesty footer ----------------------------------------------------------
fig.text(0.5, 0.035,
         "Honest scope: efficiency is vs. other LLM agents (not classical optimisation, which uses 0 tokens). "
         "A proposed coherence metric gave a reported NEGATIVE result — diagnosed, not hidden.",
         ha="center", fontsize=7.4, color="#8a5a1a",
         bbox=dict(boxstyle="round,pad=0.4", fc="#fdf6ec", ec="#e8c79a", lw=0.8))

fig.savefig(os.path.join(HERE, "graphical_abstract.pdf"))
fig.savefig(os.path.join(HERE, "graphical_abstract.png"), dpi=200)
print("OK graphical_abstract.pdf / .png")
