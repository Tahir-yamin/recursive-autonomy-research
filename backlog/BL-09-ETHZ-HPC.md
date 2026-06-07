# BL-09 — ETH Zurich HPC Chair Critiques

**Priority:** 🟠 P1
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** Fail

---

## Issue 9.1 — "Per Seed Process" Architecture Claim is False
(Also tracked in BL-03 Issue 3.3)
**File:** main.tex:360
**Evidence:** All 10 seeds run in ONE asyncio process sequentially.
No subprocess forks. `asyncio.to_thread` creates threads, not processes.
`torch.set_num_threads` is process-global, called once at import time.

**Fix:** See BL-03 Issue 3.3.

---

## Issue 9.2 — quadratic cosine_similarity Always Materialised
**File:** run_pilot_experiment.py:422
**Evidence:** `cosine_similarity(vectors)` builds full N×N matrix
before sparse k-NN selection at line 426–433. "Sparse construction"
is a misleading description — it is dense construction with sparse
edge retention.

**Fix (proper sparse construction):**
```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Instead of full N×N matrix, use approximate NN for large N:
# For N <= 100 (current scale), full matrix is fine but claim
# must be accurate.

# Update manuscript claim from "sparse k-NN graph construction"
# to "k-NN edge selection from full pairwise similarity matrix"
# OR switch to sklearn NearestNeighbors for O(N log N) actual sparse:
from sklearn.neighbors import NearestNeighbors
nbrs = NearestNeighbors(n_neighbors=k+1, metric='cosine').fit(vectors)
distances, indices = nbrs.kneighbors(vectors)
```
At current scale (N≤50) this is cosmetic. For the paper's claim of
"bounded sparse construction" it is a terminology fix.

**Acceptance criteria:**
- [ ] Manuscript accurately describes the construction as
      "k-NN edge selection from full pairwise similarity" OR
      switches to a genuinely sparse construction

---

## Issue 9.3 — raw_history_buffer is Unbounded
**File:** run_pilot_experiment.py:690
**Evidence:** `raw_history_buffer = []` with no `maxlen`. Grows
without bound. The consolidator receives `list(raw_history_buffer)`
at line 494 — an ever-growing list passed to the O(n²) function.
Contradicts the "bounded memory" architectural claim.

**Fix:**
```python
# Replace:
raw_history_buffer = []
# With:
raw_history_buffer = collections.deque(maxlen=MAX_TRIAL_MEMORY * 2)
```
Or cap by slicing before passing to consolidator:
```python
all_trials = list(raw_history_buffer)[-MAX_TRIAL_MEMORY:]
```

**Acceptance criteria:**
- [ ] raw_history_buffer is bounded OR capped before graph construction
