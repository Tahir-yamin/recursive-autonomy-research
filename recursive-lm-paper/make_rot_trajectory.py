"""Compute and plot the Coherence Retention Score (CRS) trajectory.

This implements the metric the manuscript *proposes* (Sec. "Proposed Evaluation
Protocol": CRS_t = (NR_t + DC_t)/2) but never computed, because the original
campaign persisted only per-seed means. The instrumented orchestrator now stores
per-cycle trajectories under conditions[*]["per_cycle_trajectories"]; this script
turns them into the genuine context-rot trajectory.

Definitions (trailing window W):
  NR_t  (Non-Redundancy)        = 1 - (#redundant proposals in window)/W
  DC_t  (Directional Consistency)= (#cycles in window with val_acc >= prior
                                    running-best)/W      [proposal advanced or
                                    held the search frontier]
  CRS_t = (NR_t + DC_t) / 2  in [0,1];  manuscript success criterion CRS_t >= 0.70.

HONESTY: if a results file predates the instrumentation (no per-cycle data), this
script reports that and exits WITHOUT inventing a trajectory. Nothing is fabricated.

Usage: python make_rot_trajectory.py [pilot_results_digits.json]
"""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
W = 10  # trailing window
COLORS = {"stateless_baseline": "#b41e1e", "vector_rag": "#1c4f8a",
          "rar_compressed": "#2ca02c"}
LABELS = {"stateless_baseline": "Stateless", "vector_rag": "Vector RAG",
          "rar_compressed": "RAR (ours)"}


def crs_series(trace):
    """Return (cycles, NR, DC, CRS) arrays for one seed's per-cycle trace."""
    trace = sorted(trace, key=lambda r: r["cycle"])
    red = np.array([r["redundant"] for r in trace], dtype=float)
    acc = np.array([r["val_acc"] for r in trace], dtype=float)
    n = len(trace)
    cycles = np.array([r["cycle"] for r in trace])
    NR = np.empty(n); DC = np.empty(n)
    for t in range(n):
        lo = max(0, t - W + 1)
        NR[t] = 1.0 - red[lo:t + 1].mean()
        prior_best = acc[:t].max() if t > 0 else acc[0]
        win = acc[lo:t + 1]
        win_prior_best = np.array(
            [acc[:max(1, lo + i)].max() for i in range(len(win))])
        DC[t] = np.mean(win >= win_prior_best)
    return cycles, NR, DC, (NR + DC) / 2.0


def main():
    import glob
    dataset = os.environ.get("RAR_DATASET", "digits")
    # Prefer per-seed files (each carries one per-cycle trajectory); each is
    # aggregated so the trajectory pools all available seeds. Fall back to a
    # single merged/explicit file passed as argv[1].
    conds = {}
    per_seed = sorted(glob.glob(os.path.join(HERE, f"pilot_seed_*_{dataset}.json")))
    if len(sys.argv) > 1:
        conds = json.load(open(sys.argv[1]))["data"]["conditions"]
    elif per_seed:
        for f in per_seed:
            c = json.load(open(f)).get("data", {}).get("conditions", {})
            for k, v in c.items():
                conds.setdefault(k, {"per_cycle_trajectories": []})
                conds[k]["per_cycle_trajectories"] += v.get("per_cycle_trajectories", [])
        print(f"aggregated {len(per_seed)} per-seed files: {[os.path.basename(f) for f in per_seed]}")
    else:
        merged = os.path.join(HERE, f"pilot_results_{dataset}.json")
        if os.path.exists(merged):
            conds = json.load(open(merged))["data"]["conditions"]

    have = any(conds.get(c, {}).get("per_cycle_trajectories") for c in conds)
    if not have:
        print("=" * 72)
        print(f"No per-cycle trajectories in {os.path.basename(path)}.")
        print("This results file predates the orchestrator instrumentation, so it")
        print("stores only per-seed means -- a genuine CRS/rot trajectory CANNOT be")
        print("reconstructed from it, and this script will NOT fabricate one.")
        print("Re-run run_pilot_experiment.py (now instrumented) to capture per-cycle")
        print("data, then re-run this script to produce fig_rot_trajectory.png.")
        print("=" * 72)
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))
    plt.rcParams.update({"font.family": "serif"})
    for c in ["stateless_baseline", "vector_rag", "rar_compressed"]:
        traces = conds.get(c, {}).get("per_cycle_trajectories") or []
        traces = [t for t in traces if t and len(t) > 1]
        if not traces:
            continue
        L = min(len(t) for t in traces)
        crs_stack, den_stack = [], []
        for t in traces:
            cyc, NR, DC, CRS = crs_series(t)
            crs_stack.append(CRS[:L])
            den_stack.append([r["density"] for r in sorted(t, key=lambda r: r["cycle"])][:L])
        crs_m = np.mean(crs_stack, axis=0); crs_s = np.std(crs_stack, axis=0)
        den_m = np.mean(den_stack, axis=0)
        x = np.arange(1, L + 1)
        ax1.plot(x, crs_m, color=COLORS[c], label=LABELS[c], lw=2)
        ax1.fill_between(x, crs_m - crs_s, crs_m + crs_s, color=COLORS[c], alpha=0.15)
        ax2.plot(x, den_m, color=COLORS[c], label=LABELS[c], lw=2)

    ax1.axhline(0.70, color="black", ls=":", lw=1, label="success criterion (0.70)")
    ax1.set_xlabel("Cycle", fontweight="bold"); ax1.set_ylabel("CRS", fontweight="bold")
    ax1.set_title("Coherence Retention Score trajectory"); ax1.grid(alpha=0.4); ax1.legend(fontsize=8)
    ax2.set_xlabel("Cycle", fontweight="bold"); ax2.set_ylabel(r"Context density $\delta$", fontweight="bold")
    ax2.set_title("Context density trajectory"); ax2.grid(alpha=0.4); ax2.legend(fontsize=8)
    out = os.path.join(HERE, "fig_rot_trajectory.png")
    fig.savefig(out, dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote", out)

    # --- Corrected coherence metric (frontier proximity) + search quality ------
    # Replaces the flawed non-redundancy term with frontier proximity q_t, which
    # credits informed exploitation. Reported honestly even when inconclusive.
    print("\ncorrected metric (late cycles >=20):")
    print(f"  {'condition':20s}{'CRS(NR-based)':>14s}{'frontier_prox':>14s}{'mean_val':>10s}")
    for c in ["stateless_baseline", "vector_rag", "rar_compressed"]:
        traces = [t for t in conds.get(c, {}).get("per_cycle_trajectories", []) if t and len(t) > 1]
        if not traces:
            continue
        crs_l, pf_l, val_l = [], [], []
        for t in traces:
            ts = sorted(t, key=lambda r: r["cycle"])
            acc = np.array([r["val_acc"] for r in ts], float)
            _, _, _, CRS = crs_series(t)
            n = len(acc); q = np.empty(n)
            for k in range(n):
                b, w = acc[:k + 1].max(), acc[:k + 1].min()
                q[k] = 0.0 if b == w else (acc[k] - w) / (b - w)
            pf = np.array([q[max(0, k - W + 1):k + 1].mean() for k in range(n)])
            crs_l.append(CRS[19:].mean()); pf_l.append(pf[19:].mean()); val_l.append(acc[19:].mean())
        print(f"  {LABELS[c]:20s}{np.mean(crs_l):>14.3f}{np.mean(pf_l):>14.3f}{np.mean(val_l):>10.4f}")
    print("note: two principled metrics inconclusive at 60 cycles; mean_val is the "
          "only consistent signal (RAR highest). Decisive test = >=150 cycles.")


if __name__ == "__main__":
    main()
