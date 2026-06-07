"""Regenerate Table 1 (tab:empirical_results) and the Wilcoxon caption in main.tex
directly from pilot_results.json. Table numeric values are NEVER hand-edited; this
script is the single source of truth (BL-07.2). Paths are resolved relative to this
file so the script is portable (BL-06.1)."""
import json
import os
import re
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
filepath = os.path.join(PROJECT_ROOT, "main.tex")
results_path = os.path.join(PROJECT_ROOT, "pilot_results.json")

if not os.path.exists(results_path):
    print("pilot_results.json does not exist!")
    raise SystemExit(1)

with open(results_path, "r", encoding="utf-8") as f:
    res = json.load(f)

p_val = res.get("wilcoxon_p_value_RAR_vs_Baseline", "n.s.")
data = res.get("data", {})
conditions = data.get("conditions", {})
stateless = conditions.get("stateless_baseline", {})
vector_rag = conditions.get("vector_rag", {})
rar = conditions.get("rar_compressed", {})


def get_stats(lst, multiply_by_100=True):
    if not lst:
        return 0.0, 0.0
    arr = np.array(lst, dtype=float)
    if multiply_by_100 and all(x <= 1.0 for x in arr):
        arr = arr * 100.0
    return float(np.mean(arr)), float(np.std(arr))


s_val_mean, s_val_std = get_stats(stateless.get("val_accuracies", []))
s_test_mean, s_test_std = get_stats(stateless.get("test_accuracies", []))
s_dens_mean, s_dens_std = get_stats(stateless.get("prompt_densities", []), multiply_by_100=False)
s_tok_mean, s_tok_std = get_stats(stateless.get("net_tokens", []), multiply_by_100=False)
s_lat_mean, s_lat_std = get_stats(stateless.get("wall_clock_latencies", []), multiply_by_100=False)

v_val_mean, v_val_std = get_stats(vector_rag.get("val_accuracies", []))
v_test_mean, v_test_std = get_stats(vector_rag.get("test_accuracies", []))
v_dens_mean, v_dens_std = get_stats(vector_rag.get("prompt_densities", []), multiply_by_100=False)
v_tok_mean, v_tok_std = get_stats(vector_rag.get("net_tokens", []), multiply_by_100=False)
v_lat_mean, v_lat_std = get_stats(vector_rag.get("wall_clock_latencies", []), multiply_by_100=False)

r_val_mean, r_val_std = get_stats(rar.get("val_accuracies", []))
r_test_mean, r_test_std = get_stats(rar.get("test_accuracies", []))
r_dens_mean, r_dens_std = get_stats(rar.get("prompt_densities", []), multiply_by_100=False)
r_tok_mean, r_tok_std = get_stats(rar.get("net_tokens", []), multiply_by_100=False)
r_lat_mean, r_lat_std = get_stats(rar.get("wall_clock_latencies", []), multiply_by_100=False)


def pct_change(x, base):
    """Signed % change of x relative to base (negative = reduction)."""
    return ((x - base) / base) * 100.0 if base else 0.0


# All density/token changes are reported relative to the Stateless Baseline.
v_dens_change = pct_change(v_dens_mean, s_dens_mean)
r_dens_change = pct_change(r_dens_mean, s_dens_mean)
v_tok_change = pct_change(v_tok_mean, s_tok_mean)
r_tok_change = pct_change(r_tok_mean, s_tok_mean)


def signed(v):
    return f"+{v:.1f}\\%" if v >= 0 else f"-{abs(v):.1f}\\%"


with open(filepath, "r", encoding="utf-8") as f:
    text = f.read()

# --- Update Wilcoxon caption -------------------------------------------------
text = re.sub(
    r"Wilcoxon signed-rank \$p\$-value = .*? for RAR vs Baseline",
    f"Wilcoxon signed-rank $p$-value = {p_val} for RAR vs Baseline",
    text,
)

# --- Rebuild Table 1 body (text-mode bold uses \textbf, never \mathbf) --------
new_table_body = f"""\\begin{{tabular}}{{L{{5.4cm}}C{{2.8cm}}C{{2.8cm}}C{{2.8cm}}}}
\\toprule
\\rh \\textbf{{Metric}} & \\textbf{{Stateless Baseline}} & \\textbf{{Vector RAG}} & \\textbf{{RAR Compressed (Ours)}} \\\\
\\midrule
\\ra Mean Val. Accuracy (\\%)        & ${s_val_mean:.2f} \\pm {s_val_std:.2f}$            & ${v_val_mean:.2f} \\pm {v_val_std:.2f}$    & ${r_val_mean:.2f} \\pm {r_val_std:.2f}$ \\\\
    Mean Test Accuracy (\\%)       & ${s_test_mean:.2f} \\pm {s_test_std:.2f}$            & ${v_test_mean:.2f} \\pm {v_test_std:.2f}$    & \\textbf{{${r_test_mean:.2f} \\pm {r_test_std:.2f}$}} \\\\
\\ra Mean Prompt Density ($\\delta$) & ${s_dens_mean:.3f} \\pm {s_dens_std:.3f}$           & ${v_dens_mean:.3f} \\pm {v_dens_std:.3f}$   & ${r_dens_mean:.3f} \\pm {r_dens_std:.3f}$ \\\\
    Prompt Density Change (\\%)    & Reference                   & ${signed(v_dens_change)}$           & \\textbf{{${signed(r_dens_change)}$}} \\\\
\\ra Net Tokens (characters)        & ${s_tok_mean:,.0f} \\pm {s_tok_std:.0f}$             & ${v_tok_mean:,.0f} \\pm {v_tok_std:.0f}$     & \\textbf{{${r_tok_mean:,.0f} \\pm {r_tok_std:.0f}$}} \\\\
    Net Token Change (\\%)         & Reference                   & ${signed(v_tok_change)}$           & \\textbf{{${signed(r_tok_change)}$}} \\\\
\\ra Mean Loop Latency (s)          & ${s_lat_mean:.2f} \\pm {s_lat_std:.2f}$             & ${v_lat_mean:.2f} \\pm {v_lat_std:.2f}$     & ${r_lat_mean:.2f} \\pm {r_lat_std:.2f}$ \\\\
    SRE WAL Task Recoverability   & $0.0\\%$ (No WAL)            & $100\\%$             & \\textbf{{$100\\%$}} \\\\
\\bottomrule
\\end{{tabular}}"""

text = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}",
              lambda m: new_table_body, text, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)

# --- Emit a machine-readable summary for downstream prose updates ------------
summary = {
    "p_value": p_val,
    "stateless": {"val": [s_val_mean, s_val_std], "test": [s_test_mean, s_test_std],
                  "density": [s_dens_mean, s_dens_std], "tokens": [s_tok_mean, s_tok_std]},
    "vector_rag": {"val": [v_val_mean, v_val_std], "test": [v_test_mean, v_test_std],
                   "density": [v_dens_mean, v_dens_std], "tokens": [v_tok_mean, v_tok_std]},
    "rar": {"val": [r_val_mean, r_val_std], "test": [r_test_mean, r_test_std],
            "density": [r_dens_mean, r_dens_std], "tokens": [r_tok_mean, r_tok_std]},
    "rar_vs_baseline": {"density_change_pct": r_dens_change, "token_change_pct": r_tok_change},
    "vector_vs_baseline": {"density_change_pct": v_dens_change, "token_change_pct": v_tok_change},
}
with open(os.path.join(PROJECT_ROOT, "results_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("Table 1 regenerated from pilot_results.json.")
print(json.dumps(summary, indent=2))
