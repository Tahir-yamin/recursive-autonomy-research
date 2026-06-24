# Final Pre-Registered Results (N=10 per task)

| Task | Baseline | Vector-RAG | RAR | RAR-base | RAR wins | Wilcoxon p | Holm p |
|------|----------|-----------|-----|----------|----------|-----------|--------|
| A synthetic (hard) | 86.00 | 85.69 | 86.70 | +0.70pp | 8/10 | 0.116 | 0.116 |
| B CIFAR-PCA64 (hard) | 44.28 | 44.26 | 44.62 | +0.35pp | 7/10 | 0.064 | 0.129 |
| digits (easy, extra) | 96.08 | 95.71 | 95.11 | -0.97pp | 5/10 | 0.473 | - |

**H1 (RAR test accuracy > stateless):** NOT confirmed at alpha=0.05 after Holm
(both Holm p ~0.12-0.13). RAR is the top condition on both hard tasks and wins the
majority of seeds; CIFAR is borderline (raw p=0.064). On the easy digits task RAR is
neutral. **H3 efficiency** replicates (~-68% tokens, reported separately).

**Pre-registered conclusion:** efficiency win at accuracy parity, with a small,
consistent, difficulty-dependent positive accuracy trend that is not statistically
significant. Reported as found (PREREGISTRATION.md decision rule).

## Provenance / caveats (honest)
- Task A: gemma2:9b orchestrator on Kaggle GPU, 60 cycles.
- CIFAR N=10 = 6 seeds (gemma2/Ollama, original run) + 4 seeds (OpenRouter, rar-cifar-n10).
  Mixed orchestrator across seeds; same task, same test-vault metric. Documented, not hidden.
- digits: OpenRouter, 60 cycles (easy task, included as a difficulty contrast).
- All test accuracies are real test-vault numbers; no simulation.
