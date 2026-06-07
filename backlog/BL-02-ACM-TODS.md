# BL-02 — ACM TODS Reviewer Critiques

**Priority:** 🔴 P0
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** Reject

---

## Issue 2.1 — Multigraph Schema Formally Incomplete
**File:** main.tex:263–276
**Evidence:** G=(V,E,Φ) declared as multigraph but Φ is defined as
an edge **weight** function (Φ: E → R⁺), not the **incidence**
function (Φ: E → V×V) required to formally distinguish a multigraph
from a simple graph. Additionally, the edge weight w_ij is written
as a function of vertex indices, not edge identity — ambiguous for
parallel edges.

**Fix:**
- Either: define G as a weighted directed graph (not multigraph) and
  remove the multigraph claim — simpler and honest.
- Or: properly define the incidence function ψ: E → V×V as the
  multigraph's third component, then define weight separately as
  w: E → R⁺, giving G=(V,E,ψ,w).
- Add primary-key semantics for vertices (what uniquely identifies a
  trial vertex — trial_id? configuration hash?).
- Add edge cardinality constraints (can (θ_i, θ_j, λ) appear twice?).

**Acceptance criteria:**
- [ ] Third component of multigraph triple is an incidence function
      (if multigraph claim is kept), OR paper switches to "weighted
      directed graph" terminology
- [ ] Vertex primary key is explicitly defined
- [ ] w_ij formula is indexed by edge identity, not vertex pair

---

## Issue 2.2 — O(n²) Graph Rebuild Not Bounded
**File:** run_pilot_experiment.py:415–467
**Evidence:** `_cpu_louvain_partition` creates `G = nx.Graph()` and
recomputes full `cosine_similarity(vectors)` (O(n²·d)) on every
consolidation call. The `deque(maxlen=50)` caps the trials list but
`raw_history_buffer` (passed to the function at line 494) is unbounded.
The O(n²) claim of elimination is false.

**Fix:**
- Pass `list(trials)` (the bounded deque) to `_cpu_louvain_partition`,
  NOT `list(raw_history_buffer)`.
- Confirm `all_trials` parameter at call site is always the bounded
  deque, not the unbounded raw buffer.
- Update manuscript complexity claim to accurately reflect the
  bounded-input behavior.

**Acceptance criteria:**
- [ ] `_cpu_louvain_partition` receives only the bounded deque
- [ ] `raw_history_buffer` is either bounded or not passed to graph builder
- [ ] Complexity claim updated to "bounded by MAX_TRIAL_MEMORY=50"

---

## Issue 2.3 — `load_wal`/`clear_wal` Synchronous on Event Loop
**File:** run_pilot_experiment.py:682, 708, 856
**Evidence:** `load_wal(wal_path)` and `clear_wal(wal_path)` called
directly in async coroutine body — blocking file I/O on event loop.

**Fix:**
```python
# Replace:
state = load_wal(wal_path)
# With:
state = await asyncio.to_thread(load_wal, wal_path)
```
Same pattern for `clear_wal`.

**Acceptance criteria:**
- [ ] All `load_wal` and `clear_wal` calls wrapped in `asyncio.to_thread`
