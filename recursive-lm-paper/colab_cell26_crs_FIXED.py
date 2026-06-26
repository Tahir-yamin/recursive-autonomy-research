# ============================================================================
# CORRECTED Cell 26 -- REAL Context-Rot (CRS) trajectory.
# Replaces the broken version that plotted per-SEED redundancy counts as if
# they were cycles. This reads the genuine per-cycle trajectories that the
# INSTRUMENTED run_pilot_experiment.py now logs under
# conditions[*]["per_cycle_trajectories"]. If that field is absent (i.e. the
# campaign was run with the OLD orchestrator), it refuses and tells you to
# re-run -- it does NOT fabricate a trajectory.
#
# Requires: your repo's run_pilot_experiment.py must be the instrumented
# version (it persists per_cycle_trajectories). Re-run the seed cells (13-22)
# AFTER updating the repo, then run this cell.
# ============================================================================
import json, os, glob
import numpy as np
import matplotlib.pyplot as plt

W = 10  # trailing window
COLORS = {"stateless_baseline": "#b41e1e", "vector_rag": "#1c4f8a", "rar_compressed": "#2ca02c"}
LABELS = {"stateless_baseline": "Stateless", "vector_rag": "Vector RAG", "rar_compressed": "RAR (ours)"}

# Prefer per-seed files (each has one trajectory); fall back to merged file.
DATASET = os.environ.get("RAR_DATASET", "digits")
per_seed = sorted(glob.glob(f"pilot_seed_*_{DATASET}.json"))
conds = {}
if per_seed:
    for f in per_seed:
        c = json.load(open(f)).get("data", {}).get("conditions", {})
        for k, v in c.items():
            conds.setdefault(k, {"per_cycle_trajectories": []})
            conds[k]["per_cycle_trajectories"] += v.get("per_cycle_trajectories", [])
else:
    merged = f"pilot_results_{DATASET}.json"
    if os.path.exists(merged):
        conds = json.load(open(merged)).get("data", {}).get("conditions", {})

have = any(conds.get(c, {}).get("per_cycle_trajectories") for c in conds)
if not have:
    raise SystemExit(
        "No per_cycle_trajectories found. Your campaign was run with the OLD "
        "orchestrator (per-seed means only). Update run_pilot_experiment.py to "
        "the instrumented version, re-run the seed cells, then run this cell. "
        "No trajectory will be fabricated.")


def crs_series(trace):
    trace = sorted(trace, key=lambda r: r["cycle"])
    red = np.array([r["redundant"] for r in trace], float)
    acc = np.array([r["val_acc"] for r in trace], float)
    n = len(trace); NR = np.empty(n); DC = np.empty(n)
    for t in range(n):
        lo = max(0, t - W + 1)
        NR[t] = 1.0 - red[lo:t + 1].mean()
        win = acc[lo:t + 1]
        prior = np.array([acc[:max(1, lo + i)].max() for i in range(len(win))])
        DC[t] = np.mean(win >= prior)
    return (NR + DC) / 2.0, np.array([r["density"] for r in trace])


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))
for c in ["stateless_baseline", "vector_rag", "rar_compressed"]:
    trs = [t for t in conds.get(c, {}).get("per_cycle_trajectories", []) if t and len(t) > 1]
    if not trs:
        continue
    L = min(len(t) for t in trs)
    crs = np.array([crs_series(t)[0][:L] for t in trs])
    den = np.array([crs_series(t)[1][:L] for t in trs])
    x = np.arange(1, L + 1)
    ax1.plot(x, crs.mean(0), color=COLORS[c], lw=2, label=LABELS[c])
    ax1.fill_between(x, crs.mean(0) - crs.std(0), crs.mean(0) + crs.std(0), color=COLORS[c], alpha=0.15)
    ax2.plot(x, den.mean(0), color=COLORS[c], lw=2, label=LABELS[c])
ax1.axhline(0.70, color="black", ls=":", lw=1, label="success (0.70)")
ax1.set_xlabel("Cycle"); ax1.set_ylabel("CRS"); ax1.set_title("Coherence Retention Score trajectory"); ax1.legend(fontsize=8); ax1.grid(alpha=0.4)
ax2.set_xlabel("Cycle"); ax2.set_ylabel(r"Context density $\delta$"); ax2.set_title("Context density trajectory"); ax2.legend(fontsize=8); ax2.grid(alpha=0.4)
plt.tight_layout(); plt.savefig("fig_rot_trajectory.png", dpi=300, bbox_inches="tight"); plt.show()
print("Saved REAL fig_rot_trajectory.png  (download this + pilot_results_digits.json and send back).")
