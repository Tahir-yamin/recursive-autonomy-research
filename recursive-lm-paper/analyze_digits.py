"""Rigorous statistical analysis of the digits real-dataset RAR campaign.

This is the confirmatory real-data replication of the synthetic Gaussian-quantile
pilot. The synthetic study (main.tex, Table 1) established RAR's contribution as
*efficiency at accuracy-equivalence* on a procedurally generated manifold. This
script runs the same family of paired tests on the sklearn `digits` dataset
(10 seeds x 60 cycles, three LLM conditions + two classical HPO baselines) to
show the efficiency story holds on a real, high-accuracy task.

For every comparison we report, across the N=10 paired seeds:
  * Paired Wilcoxon signed-rank test (two-sided), with Holm-Bonferroni
    correction across the family of efficiency tests.
  * For accuracy: a one-sided Wilcoxon superiority test AND a paired TOST
    equivalence test at a +/-2 percentage-point margin (matching the synthetic
    study's pre-registered margin), so we can claim equivalence rather than a
    mere failure to reject.
  * Effect direction and percentage reduction vs the Stateless Baseline.

Run:  python analyze_digits.py
Writes: digits_analysis.json (machine-readable summary for the manuscript).
"""
import json
import os

import numpy as np
from scipy.stats import wilcoxon, t as student_t

HERE = os.path.dirname(os.path.abspath(__file__))
LLM_FILE = os.path.join(HERE, "pilot_results_digits.json")
CLASSICAL_FILE = os.path.join(HERE, "pilot_results_digits_classical.json")

# Accuracy equivalence margin: +/-2 percentage points, identical to the
# synthetic pilot's pre-stated TOST margin (main.tex, Sec. 5).
TOST_MARGIN = 0.02


def load_conditions():
    with open(LLM_FILE, encoding="utf-8") as fh:
        llm = json.load(fh)["data"]["conditions"]
    with open(CLASSICAL_FILE, encoding="utf-8") as fh:
        classical = json.load(fh)["data"]["conditions"]
    merged = dict(llm)
    merged.update(classical)
    return merged


def summarize(values):
    arr = np.asarray(values, dtype=float)
    # Sample standard deviation (ddof=1) to match the manuscript convention.
    sd = float(arr.std(ddof=1)) if arr.size > 1 else 0.0
    return {"mean": float(arr.mean()), "sd": sd, "min": float(arr.min()),
            "max": float(arr.max()), "n": int(arr.size)}


def paired_wilcoxon(a, b, alternative="two-sided"):
    """Paired Wilcoxon signed-rank test; returns (statistic, p) or (nan, 1.0).

    If every paired difference is zero (no variation) the test is undefined; we
    return p=1.0 in that degenerate case so it propagates harmlessly.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if np.allclose(a, b):
        return float("nan"), 1.0
    stat, p = wilcoxon(a, b, alternative=alternative, zero_method="wilcox")
    return float(stat), float(p)


def tost_equivalence(a, b, margin):
    """Two one-sided t-tests for equivalence of paired means within +/-margin.

    Returns the TOST p-value (max of the two one-sided p-values) and the
    two-sided 90% CI on the mean difference (a-b). Equivalence is established
    when that CI lies entirely inside (-margin, +margin), which is exactly the
    condition TOST p < 0.05 encodes.
    """
    diff = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    n = diff.size
    mean_d = diff.mean()
    se = diff.std(ddof=1) / np.sqrt(n)
    df = n - 1
    # Lower test H0: mean_d <= -margin ; Upper test H0: mean_d >= +margin.
    t_lower = (mean_d - (-margin)) / se
    t_upper = (mean_d - margin) / se
    p_lower = student_t.sf(t_lower, df)   # P(T > t_lower)
    p_upper = student_t.cdf(t_upper, df)  # P(T < t_upper)
    p_tost = max(p_lower, p_upper)
    # 90% CI (1-2*alpha) is the interval TOST evaluates at alpha=0.05.
    crit = student_t.ppf(0.95, df)
    ci = (mean_d - crit * se, mean_d + crit * se)
    return float(p_tost), (float(ci[0]), float(ci[1]))


def holm_bonferroni(pvals):
    """Holm-Bonferroni step-down adjustment. Returns adjusted p-values aligned
    to the input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        adj = (m - rank) * pvals[idx]
        running = max(running, adj)          # enforce monotonicity
        adjusted[idx] = min(running, 1.0)
    return adjusted


def pct_reduction(treatment_mean, baseline_mean):
    if baseline_mean == 0:
        return float("nan")
    return 100.0 * (treatment_mean - baseline_mean) / baseline_mean


def main():
    cond = load_conditions()
    baseline = cond["stateless_baseline"]
    rag = cond["vector_rag"]
    rar = cond["rar_compressed"]

    # ---- Descriptive stats (accuracy in %, the rest in native units) --------
    metrics = ["test_accuracies", "val_accuracies", "prompt_densities",
               "net_tokens", "wall_clock_latencies", "redundancies",
               "generalization_gaps"]
    descriptives = {}
    for name, c in cond.items():
        descriptives[name] = {m: summarize(c[m]) for m in metrics if m in c}

    # ---- Family of efficiency tests: RAR vs baseline -----------------------
    # Lower is better for every efficiency metric, so the directional question
    # is "is RAR < baseline". We run two-sided Wilcoxon and Holm-correct the
    # family {density, tokens, latency, redundancy}.
    efficiency_metrics = ["prompt_densities", "net_tokens",
                          "wall_clock_latencies", "redundancies"]
    raw_p, family = [], []
    for m in efficiency_metrics:
        stat, p = paired_wilcoxon(rar[m], baseline[m])
        raw_p.append(p)
        family.append({
            "metric": m,
            "rar_mean": summarize(rar[m])["mean"],
            "baseline_mean": summarize(baseline[m])["mean"],
            "pct_reduction_vs_baseline": pct_reduction(
                summarize(rar[m])["mean"], summarize(baseline[m])["mean"]),
            "wilcoxon_stat": stat,
            "wilcoxon_p_raw": p,
        })
    holm = holm_bonferroni(raw_p)
    for entry, adj in zip(family, holm):
        entry["wilcoxon_p_holm"] = adj
        entry["significant_holm_0.05"] = adj < 0.05

    # ---- Accuracy: superiority (one-sided) + equivalence (TOST) ------------
    _, p_sup_rar = paired_wilcoxon(rar["test_accuracies"],
                                   baseline["test_accuracies"],
                                   alternative="greater")
    p_tost_rar, ci_rar = tost_equivalence(
        rar["test_accuracies"], baseline["test_accuracies"], TOST_MARGIN)

    # Same accuracy comparison for Vector RAG, for completeness.
    _, p_sup_rag = paired_wilcoxon(rag["test_accuracies"],
                                   baseline["test_accuracies"],
                                   alternative="greater")
    p_tost_rag, ci_rag = tost_equivalence(
        rag["test_accuracies"], baseline["test_accuracies"], TOST_MARGIN)

    accuracy = {
        "margin_points": TOST_MARGIN * 100,
        "rar_vs_baseline": {
            "superiority_wilcoxon_p_one_sided": p_sup_rar,
            "superiority_significant": p_sup_rar < 0.05,
            "tost_equivalence_p": p_tost_rar,
            "tost_equivalent": p_tost_rar < 0.05,
            "ci90_points": [ci_rar[0] * 100, ci_rar[1] * 100],
        },
        "rag_vs_baseline": {
            "superiority_wilcoxon_p_one_sided": p_sup_rag,
            "superiority_significant": p_sup_rag < 0.05,
            "tost_equivalence_p": p_tost_rag,
            "tost_equivalent": p_tost_rag < 0.05,
            "ci90_points": [ci_rag[0] * 100, ci_rag[1] * 100],
        },
    }

    summary = {
        "dataset": "digits",
        "n_seeds": baseline["test_accuracies"].__len__(),
        "cycles": 60,
        "descriptives": descriptives,
        "efficiency_family_rar_vs_baseline": family,
        "accuracy": accuracy,
    }
    out = os.path.join(HERE, "digits_analysis.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    # ---- Console report -----------------------------------------------------
    def pct(x):
        return f"{x:+.1f}%"

    print("=" * 74)
    print("DIGITS REAL-DATASET RAR ANALYSIS  (N=10 seeds, 60 cycles)")
    print("=" * 74)
    print("\nMean test accuracy (%):")
    for n in ["stateless_baseline", "vector_rag", "rar_compressed",
              "bayesian_opt", "random_search"]:
        s = summarize(cond[n]["test_accuracies"])
        print(f"  {n:20s} {s['mean']*100:6.2f} +/- {s['sd']*100:4.2f}"
              f"   (min {s['min']*100:5.2f})")

    print("\nEfficiency family  RAR vs Stateless Baseline"
          "  (Holm-corrected, lower=better):")
    print(f"  {'metric':22s}{'RAR':>12s}{'baseline':>12s}"
          f"{'reduction':>11s}{'p_holm':>10s}  sig")
    for e in family:
        print(f"  {e['metric']:22s}{e['rar_mean']:12.4g}"
              f"{e['baseline_mean']:12.4g}"
              f"{pct(e['pct_reduction_vs_baseline']):>11s}"
              f"{e['wilcoxon_p_holm']:10.4f}"
              f"  {'YES' if e['significant_holm_0.05'] else 'no'}")

    a = accuracy["rar_vs_baseline"]
    print("\nAccuracy  RAR vs Stateless Baseline:")
    print(f"  superiority (one-sided Wilcoxon) p = {a['superiority_wilcoxon_p_one_sided']:.4f}"
          f"  -> {'significant' if a['superiority_significant'] else 'NOT superior'}")
    print(f"  TOST equivalence (+/-2 pts)      p = {a['tost_equivalence_p']:.4f}"
          f"  -> {'EQUIVALENT' if a['tost_equivalent'] else 'not established'}")
    print(f"  90% CI on mean diff (pts)        [{a['ci90_points'][0]:+.2f}, "
          f"{a['ci90_points'][1]:+.2f}]")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
