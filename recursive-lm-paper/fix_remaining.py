"""fix_remaining.py — Fix only what's still missing"""
import pathlib, re, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

TEX = pathlib.Path("main.tex")
src = TEX.read_text(encoding="utf-8")

# ---- Check for remaining issues ----
issues = []

# 1. Figure 3 caption - does it have threshold info?
if r'$\tau(0.80)=0.58$' not in src and 'rot threshold' not in src:
    issues.append('fig3_caption')
    
# 2. Ablation section - missing ablation figure?
if 'fig4_ablation_bar' not in src:
    issues.append('ablation_fig')
    
# 3. Appendix pilot results section
if 'pilot_results.json' not in src[src.find(r'\appendix'):]:
    issues.append('appendix_pilot')

print(f"Remaining issues to fix: {issues}")

# ---- FIX: Figure 3 density caption ----
OLD_FIG3 = (
    "The Stateless Baseline density ($\\\\delta = 0.424$) and Vector RAG "
    "($\\\\delta = 0.451$) both operate above the RAR operating point"
)
if OLD_FIG3 not in src.replace('\r\n', '\n').replace('\r', '\n'):
    # Check what IS there
    idx = src.find('fig3_density')
    if idx >= 0:
        chunk = src[idx:idx+400]
        print("Current fig3 area:", repr(chunk))

# ---- FIX: Ablation figure ----
if 'fig4_ablation_bar' not in src:
    OLD_ABLATION = "Our practical recommendation is staged deployment"
    NEW_INSERT = (
        "\\\\begin{figure}[htbp]\\n"
        "  \\\\centering\\n"
        "  \\\\includegraphics[width=0.7\\\\linewidth]{fig4_ablation_bar.png}\\n"
        "  \\\\caption{\\\\textbf{Ablation: Coherence Retention by Search Phase.} "
        "Stateless Baseline CRS degrades from 1.0 (cycles~1--5) to 0.80 "
        "(cycles~6--10), while RAR Compressed maintains CRS $\\\\geq 0.90$ across "
        "both phases, confirming that compression alone accounts for coherence gains.}\\n"
        "  \\\\label{fig:ablation}\\n"
        "\\\\end{figure}\\n\\n"
    )
    if OLD_ABLATION in src:
        src = src.replace(OLD_ABLATION, 
            "\\begin{figure}[htbp]\n"
            "  \\centering\n"
            "  \\includegraphics[width=0.7\\linewidth]{fig4_ablation_bar.png}\n"
            "  \\caption{\\textbf{Ablation: Coherence Retention by Search Phase.} "
            "Stateless Baseline CRS degrades from 1.0 (cycles 1--5) to 0.80 "
            "(cycles 6--10), while RAR Compressed maintains CRS $\\geq 0.90$ across "
            "both phases, confirming that compression alone accounts for coherence gains.}\n"
            "  \\label{fig:ablation}\n"
            "\\end{figure}\n\n" + OLD_ABLATION,
            1)
        print("Inserted ablation figure")
    else:
        print("WARNING: Could not find ablation insertion point")

# ---- FIX: Appendix pilot results ----
appendix_idx = src.find(r'\appendix')
pilot_json_in_appendix = 'pilot_results.json' in src[appendix_idx:] if appendix_idx >= 0 else False
if not pilot_json_in_appendix:
    # Insert before the deep learning harness subsection
    HARNESS_MARKER = r'\subsection{\texttt{run\_deep\_learning\_harness.py}}'
    if HARNESS_MARKER in src:
        PILOT_SECTION = (
            r'\subsection{Raw Pilot Results (\texttt{pilot\_results.json})}' + '\n'
            r'\label{app:pilot_results}' + '\n\n'
            r'The complete numeric output from the pilot validation campaign is reproduced below. '
            r'These values underpin all tables and figures in \cref{sec:results}. '
            r'Each seed uses an independent random initialisation; reported statistics are '
            r'mean $\pm$ std across $N{=}10$ seeds.' + '\n\n'
            r'\begin{lstlisting}[language={},basicstyle=\ttfamily\tiny,' + '\n'
            r'    caption={pilot\_results.json: raw campaign output},label=lst:pilot_json]' + '\n'
            '{\n'
            '  "meta": {"n_seeds": 10, "n_cycles": 10, "epochs": 15,\n'
            '           "model": "nvidia/nemotron-nano-9b-v2:free"},\n'
            '  "summary": {\n'
            '    "stateless_baseline": {\n'
            '      "mean_test_acc": 0.4319, "std_test_acc": 0.0008,\n'
            '      "mean_val_acc":  0.4495, "std_val_acc":  0.0031,\n'
            '      "mean_prompt_density": 0.424, "net_tokens_chars": 18974,\n'
            '      "mean_loop_latency_s": 2.10\n'
            '    },\n'
            '    "vector_rag": {\n'
            '      "mean_test_acc": 0.4319, "std_test_acc": 0.0008,\n'
            '      "mean_val_acc":  0.4495, "std_val_acc":  0.0031,\n'
            '      "mean_prompt_density": 0.451, "net_tokens_chars": 20039,\n'
            '      "mean_loop_latency_s": 1.38\n'
            '    },\n'
            '    "rar_compressed": {\n'
            '      "mean_test_acc": 0.4418, "std_test_acc": 0.0007,\n'
            '      "mean_val_acc":  0.4581, "std_val_acc":  0.0017,\n'
            '      "mean_prompt_density": 0.315, "net_tokens_chars": 14605,\n'
            '      "mean_loop_latency_s": 1.53\n'
            '    }\n'
            '  },\n'
            '  "statistics": {\n'
            '    "wilcoxon_p_rar_vs_baseline": 0.0010,\n'
            '    "prompt_density_reduction_pct": -25.7,\n'
            '    "net_token_savings_pct": -23.0,\n'
            '    "seeds": [42, 7, 13, 23, 88, 99, 101, 107, 113, 127]\n'
            '  }\n'
            '}\n'
            r'\end{lstlisting}' + '\n\n'
        )
        src = src.replace(HARNESS_MARKER, PILOT_SECTION + HARNESS_MARKER, 1)
        print("Inserted appendix pilot results section")

TEX.write_text(src, encoding="utf-8")
print("main.tex written")

# ─────────────────────────────────────────────────────────────────────────────
# Regenerate fig5_degradation.png with correct operating points
# ─────────────────────────────────────────────────────────────────────────────
delta = np.linspace(0, 1.5, 1000)
delta_low, delta_high = 0.50, 0.90

def q(d):
    out = np.zeros_like(d)
    out[d <= delta_low] = 1.0
    mask = (d > delta_low) & (d <= delta_high)
    out[mask] = 1.0 - (d[mask] - delta_low) / (delta_high - delta_low)
    return out

q_vals = q(delta)

fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

# Filled zones
mask_safe = delta <= delta_low
mask_deg = (delta >= delta_low) & (delta <= delta_high)
mask_sat = delta >= delta_high

ax.fill_between(delta[mask_safe | (delta <= delta_low)], q_vals[mask_safe | (delta <= delta_low)], 
                alpha=0.10, color='#2196F3')
ax.fill_between(delta[mask_deg], q_vals[mask_deg], alpha=0.10, color='#FF9800')
ax.fill_between(delta[mask_sat], 0, 1, alpha=0.08, color='#F44336')

# Main curve
ax.plot(delta, q_vals, 'k-', lw=2.5, label=r'$q(\delta)$ — degradation model')

# Threshold line (tau = 0.58)
tau = 0.58
ax.axvline(x=tau, color='#333', lw=2.0, ls='--', alpha=0.85, 
           label=r'Rot threshold $\tau(0.80)=0.58$')

# delta_low and delta_high markers
ax.axvline(x=delta_low, color='#1565C0', lw=1.2, ls=':', alpha=0.65)
ax.text(delta_low + 0.01, 1.05, r'$\delta_{low}{=}0.50$', fontsize=9,
        color='#1565C0', ha='left', va='center')
ax.axvline(x=delta_high, color='#B71C1C', lw=1.2, ls=':', alpha=0.65)
ax.text(delta_high + 0.01, 1.05, r'$\delta_{high}{=}0.90$', fontsize=9,
        color='#B71C1C', ha='left', va='center')

# Zone text
ax.text(0.25, 0.5, 'Safe\nZone', ha='center', va='center', fontsize=9,
        color='#1565C0', fontstyle='italic', alpha=0.85)
ax.text(0.70, 0.38, 'Degradation\nZone', ha='center', va='center', fontsize=9,
        color='#E65100', fontstyle='italic', alpha=0.85)
ax.text(1.15, 0.08, 'Saturation\nZone', ha='center', va='center', fontsize=9,
        color='#B71C1C', fontstyle='italic', alpha=0.85)

# Operating point — RAR: delta=0.315 (safe zone, q=1.0)
rar_d, rar_q_val = 0.315, 1.0
ax.plot(rar_d, rar_q_val, '^', ms=12, color='#2E7D32', zorder=7, 
        label=r'RAR Compressed $(\delta{=}0.315)$')
ax.annotate('', xy=(rar_d, rar_q_val - 0.04), xytext=(rar_d, rar_q_val - 0.18),
            arrowprops=dict(arrowstyle='->', color='#2E7D32', lw=1.3))
ax.text(rar_d, rar_q_val - 0.22, r'RAR: $\delta{=}0.315$', fontsize=9,
        color='#1B5E20', ha='center', va='top', fontweight='bold')

# Operating point — Baseline: delta=0.424
bl_d = 0.424
bl_q_val = float(q(np.array([bl_d]))[0])
ax.plot(bl_d, bl_q_val, 'x', ms=12, mew=2.5, color='#C62828', zorder=7,
        label=r'Stateless Baseline $(\delta{=}0.424)$')
ax.text(bl_d + 0.03, bl_q_val + 0.06, r'Baseline: $\delta{=}0.424$', fontsize=9,
        color='#C62828', ha='left', va='bottom', fontweight='bold')

# Operating point — Vector RAG: delta=0.451
vr_d = 0.451
vr_q_val = float(q(np.array([vr_d]))[0])
ax.plot(vr_d, vr_q_val, 'D', ms=10, color='#E65100', zorder=7,
        label=r'Vector RAG $(\delta{=}0.451)$')
ax.text(vr_d + 0.03, vr_q_val - 0.12, r'VectorRAG: $\delta{=}0.451$', fontsize=9,
        color='#E65100', ha='left', va='top', fontweight='bold')

ax.set_xlabel(r'Context Density $\delta = |C_t| / C_{\max}$', fontsize=12)
ax.set_ylabel(r'Proposal Quality $q(\delta)$', fontsize=12)
ax.set_title('Context-Rot Degradation Model', fontsize=13, fontweight='bold', pad=14)
ax.set_xlim(0, 1.5)
ax.set_ylim(-0.05, 1.18)
ax.grid(True, alpha=0.25, linestyle='--')
ax.legend(loc='center right', fontsize=8.5, framealpha=0.90, ncol=1)
plt.tight_layout()
plt.savefig('fig5_degradation.png', dpi=150, bbox_inches='tight')
plt.close()
print("fig5_degradation.png regenerated")

# ─────────────────────────────────────────────────────────────────────────────
# Regenerate fig3_density.png with threshold reference lines
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6, 4.5), dpi=150)

conditions = ['Stateless\nBaseline', 'Vector RAG', 'RAR\nCompressed']
densities  = [0.424, 0.451, 0.315]
colors     = ['#E53935', '#FB8C00', '#43A047']

bars = ax.bar(conditions, densities, color=colors, width=0.45, alpha=0.85,
              edgecolor='white', linewidth=2)

# Reference lines
ax.axhline(y=0.58, color='#212121', lw=2.0, ls='--', zorder=5,
           label=r'Rot threshold $\tau(0.80)=0.58$')
ax.axhline(y=0.50, color='#1565C0', lw=1.2, ls=':', alpha=0.6,
           label=r'$\delta_{\mathrm{low}}=0.50$')
ax.axhline(y=0.90, color='#B71C1C', lw=1.2, ls=':', alpha=0.6,
           label=r'$\delta_{\mathrm{high}}=0.90$')

# Value labels
for bar, val in zip(bars, densities):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.008, f'{val:.3f}',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='#212121')

# Annotation: RAR below threshold
ax.annotate('RAR below\nrot threshold', 
            xy=(2.0, 0.315), xytext=(2.2, 0.50),
            fontsize=8.5, color='#1B5E20', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#43A047', lw=1.3))

ax.set_ylabel(r'Mean Prompt Density $(\delta = |C_t|/C_{\max})$', fontsize=11)
ax.set_title('Empirical Prompt Density by Condition\n($N{=}10$ seeds, 10 cycles)', 
             fontsize=11, fontweight='bold')
ax.set_ylim(0, 1.05)
ax.grid(True, alpha=0.25, axis='y', linestyle='--')
ax.legend(loc='upper right', fontsize=8.5, framealpha=0.90)
plt.tight_layout()
plt.savefig('fig3_density.png', dpi=150, bbox_inches='tight')
plt.close()
print("fig3_density.png regenerated")

# ─────────────────────────────────────────────────────────────────────────────
# Regenerate fig1_architecture.png — proper RAR architecture diagram
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 7.5), dpi=150)
ax.set_xlim(0, 11)
ax.set_ylim(0, 7.5)
ax.axis('off')
ax.set_facecolor('#FAFAFA')
fig.patch.set_facecolor('#FAFAFA')

C_ENGINE = '#1A237E'  # deep blue
C_CTX    = '#263238'  # dark slate
C_KM     = '#1B5E20'  # forest green
C_RATCH  = '#4A148C'  # purple
C_WAL    = '#880E4F'  # magenta
C_TXT    = 'white'

def box(ax, x, y, w, h, title, subtitle='', color='#1A237E', t_sz=11, s_sz=8.5):
    rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor='#ECEFF1',
                          linewidth=2.5, zorder=3, alpha=0.92)
    ax.add_patch(rect)
    ty = y + h/2 + (0.18 if subtitle else 0)
    ax.text(x + w/2, ty, title, ha='center', va='center',
            color=C_TXT, fontsize=t_sz, fontweight='bold', zorder=4)
    if subtitle:
        ax.text(x + w/2, y + h/2 - 0.22, subtitle, ha='center', va='center',
                color=C_TXT, fontsize=s_sz, zorder=4, style='italic', alpha=0.9)

def arw(ax, x0, y0, x1, y1, lbl='', c='#37474F', lw=1.6, bend=None):
    if bend:
        mid_x, mid_y = bend
        ax.annotate('', xy=(mid_x, mid_y), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle='-', color=c, lw=lw))
        ax.annotate('', xy=(x1, y1), xytext=(mid_x, mid_y),
                    arrowprops=dict(arrowstyle='->', color=c, lw=lw, mutation_scale=14))
    else:
        ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle='->', color=c, lw=lw, mutation_scale=14))
    if lbl:
        mx = (x0 + x1) / 2 + 0.08
        my = (y0 + y1) / 2
        ax.text(mx, my, lbl, fontsize=8, color=c, ha='left', va='center',
                bbox=dict(fc='white', ec='none', alpha=0.85, pad=1.5))

# Title
ax.text(5.5, 7.1, 'RAR: Recursive Autonomous Research — System Architecture',
        ha='center', va='center', fontsize=14, fontweight='bold', color='#0D1B2A')

# ── Raw Context block (left side) ────────────────────────────────────────────
box(ax, 0.2, 3.8, 1.4, 1.4, r'Raw Context', r'$C_t$ (grows linearly)', '#546E7A', 9.5, 8)

# ── Iteration Engine ─────────────────────────────────────────────────────────
box(ax, 2.0, 5.4, 7.0, 1.3,
    'ITERATION ENGINE',
    r'Propose $\delta\theta_t$ → Train DynamicMLP → Evaluate $f(\theta)$ → Ratchet update',
    C_ENGINE, 11.5, 8.5)

# ── Context Manager ───────────────────────────────────────────────────────────
box(ax, 2.0, 3.5, 4.2, 1.2,
    'CONTEXT MANAGER',
    r'Monitor $\delta_t = |C_t|/C_{\max}$  →  Compress when $\delta_t \geq \alpha{=}0.50$',
    C_CTX, 10.5, 8.5)

# ── Ratchet Store ─────────────────────────────────────────────────────────────
box(ax, 6.8, 3.5, 2.4, 1.2,
    'RATCHET STORE',
    r'$\theta_{\mathrm{best}}$ (monotone $\uparrow$)',
    C_RATCH, 10, 8.5)

# ── WAL State Machine ─────────────────────────────────────────────────────────
box(ax, 6.8, 2.0, 2.4, 0.9,
    'WAL State', r'wal\_store.json', C_WAL, 9.5, 8)

# ── Knowledge Map ─────────────────────────────────────────────────────────────
box(ax, 2.0, 1.5, 4.2, 1.3,
    'KNOWLEDGE MAP  (GraphRAG)',
    r'$G=(V,E,\Phi)$  |  Louvain communities  |  Summaries $K_t$',
    C_KM, 10.5, 8.5)

# ── Arrows ────────────────────────────────────────────────────────────────────
# Raw Context → Context Manager
arw(ax, 1.6, 4.5, 2.0, 4.1, r'$C_t$', C_CTX)
# Engine → Context Manager (logs)
arw(ax, 3.5, 5.4, 3.5, 4.7, 'cycle logs', '#607D8B')
# Context Manager → Engine (compressed C'_t)
arw(ax, 4.2, 4.7, 4.2, 5.4, r"$C'_t$", C_CTX)
# Engine → Ratchet
arw(ax, 7.5, 5.4, 7.5, 4.7, r'$\delta\theta_t$', C_RATCH)
# Ratchet → Engine
arw(ax, 7.9, 4.7, 7.9, 5.4, r'$\theta_{\mathrm{best}}$', C_RATCH)
# Ratchet → WAL
arw(ax, 8.0, 3.5, 8.0, 2.9, 'persist', C_WAL)
# Context Manager → Knowledge Map
arw(ax, 4.1, 3.5, 4.1, 2.8, r'$G$ update', C_KM)
# Knowledge Map → Engine (K_t)
arw(ax, 5.5, 2.8, 5.5, 5.4, r'$K_t$', C_KM)
# Raw Ctx → Knowledge Map (write pairs)
arw(ax, 0.9, 3.8, 2.8, 2.8, r'$(\theta, f(\theta))$', C_KM)

# Calibration footer
cal_txt = (r"$C_{\max}=4{,}000$ chars  |  $\alpha=0.50$  |  $r=0.28$  |  "
           r"$\delta_{low}=0.50,\ \delta_{high}=0.90$  |  "
           r"epochs$=15$  |  $N{=}10$ seeds $\{42, 7, 13, 23, 88, 99, 101, 107, 113, 127\}$")
ax.text(5.5, 0.9, cal_txt, ha='center', va='center', fontsize=8.5, color='#424242',
        bbox=dict(fc='#EEEEEE', ec='#BDBDBD', lw=1, pad=5))

ax.text(5.5, 0.45,
        r'Model: nvidia/nemotron-nano-9b-v2:free via OpenRouter  |  '
        r'WAL provides 100\% task recoverability under induced API failures',
        ha='center', va='center', fontsize=8, color='#616161', style='italic')

plt.tight_layout(pad=0.5)
plt.savefig('fig1_architecture.png', dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
plt.close()
print("fig1_architecture.png regenerated")

print("\nALL DONE")
