# Task B — Hard / Q1-Grade Second Benchmark (for you to verify)

## Why this exists
The original Task B (`digits`) was **too easy**: strong 98% / weak 96% (2pp gap) — no
dynamic range, so it could not test the hypothesis (the same flaw as the old 3-class task).

**Key correction (from your notebook-3 cell 112):** the honest difficulty metric is the
**spread of accuracy across the whole search space**, NOT a single hand-picked weak config.
Covtype, for example, looked weak on one hand-picked config (8pp) but its *search* spans
~42–86% — plenty of range. `verify_tasks.py` measures this spread directly.

## The options (pick by verified spread; CIFAR is the Q1-hardest)

| TASK | Dataset | Why | Expected spread | Q1 strength |
|------|---------|-----|-----------------|-------------|
| **A** | Synthetic 10-class manifold | Phase-0 validated (primary) | ~56→91% (**35pp**) | primary task |
| **B** | **CIFAR-10 → PCA-64** | **Hardest:** MLPs can't use spatial structure → wide spread; a genuinely hard *real* task reviewers respect | expect ~25→52% (**~25pp**) | **strongest generality claim** |
| **C** | Fashion-MNIST → PCA-64 | Real images, moderate difficulty | expect ~65→86% (**~20pp**) | good real fallback |
| **D** | Forest CoverType (54→64) | Real tabular; your cell 112 showed ~42→86% | ~44pp spread | solid real tabular |

**My recommendation for Q1:** **Task A (synthetic, primary) + Task B (CIFAR-10, hardest real).**
CIFAR-via-MLP is a recognised hard setting — it makes the generality claim strong, and the
wide accuracy spread means a memory/search effect (if real) will be visible.

## Files in this change (everything you need)
- `rar_tasks.py` — Task A (unchanged) + **B = CIFAR-10→PCA-64**, **C = Fashion-MNIST→PCA-64**,
  **D = covtype**. Real tasks use a **leak-free** pipeline (Scaler+PCA fit on TRAIN only).
- `verify_tasks.py` — standalone difficulty checker (CPU, **no LLM, no tokens**). Trains a
  strong/weak reference pair AND samples K random configs to report the search-space spread.

## How to verify (run locally or in Colab — nothing is sent anywhere)
```bash
pip install scikit-learn torch          # already present in Colab
# Task A (sanity, fast):
TASK=A python verify_tasks.py
# Task B (CIFAR — downloads ~170MB via OpenML first time, then cached):
TASK=B VERIFY_K=8 VERIFY_EPOCHS=25 python verify_tasks.py
# Task C / D similarly:
TASK=C python verify_tasks.py
TASK=D python verify_tasks.py
```
Each run prints, e.g.:
```
Hand-picked:  STRONG=48.0%  WEAK=27.0%  gap=21.0pp
--- SEARCH-SPACE SPREAD (the meaningful metric) ---
min=24.0% max=51.0% mean=38.0% RANGE=27.0pp
VERDICT: PASS (search spread >= 20pp -> hypothesis testable)
```

## Decision rule
Pick the Task B whose **RANGE >= 20pp** and that is hardest/most credible. If CIFAR (B)
passes (very likely), use it. If its download/runtime is inconvenient, Fashion-MNIST (C)
or covtype (D) are fine fallbacks. Tell me which passed and I will lock it as the official
Task B and wire it into the campaign + manuscript.

## Notes
- `get_dataset()` dispatches on the `TASK` env var (A/B/C/D); the campaign harness already
  calls it, so no harness change is needed to switch tasks.
- Real tasks need internet on first run (OpenML download), then cache locally.
- Nothing here was executed on my side — these are for your local/Colab verification.
