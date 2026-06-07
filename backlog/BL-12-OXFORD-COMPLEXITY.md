# BL-12 — Oxford Complexity Professor Critiques

**Priority:** 🔴 P0
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** Reject outright

---

## Issue 12.1 — Proposition 1 Proof Has 3 Independent Logical Failures

**File:** main.tex:306–313

### Gap 1: Context Manager activation count is dimensionally wrong
**Claim in proof:** "The Context Manager activates O(T/C_max) times"
**Reality:** Activation triggers when |C_t| ≥ α·C_max. If each cycle
adds ~220 chars and α·C_max = 2000 chars, compression fires every
~9 cycles → O(T) activations, NOT O(T/C_max).
The claimed O(T/C_max) would require each cycle's log entry to be O(1)
characters — physically impossible.

**Fix:** Correct the activation count derivation:
"The Context Manager activates Θ(T · chars_per_cycle / (α·C_max))
times. For fixed chars_per_cycle (determined by the trial log format),
this is Θ(T) activations."
Then rederive the total compression cost from this corrected premise.

### Gap 2: The algebra uses the wrong activation count
**Claim:** k recurse() calls × C_max/k cost × T/C_max activations = O(T)
**Reality:** Using the correct Θ(T) activation count:
T × k × (C_max/k) = T × C_max = O(T·C_max)
The compression cost is the same order as the Iteration Engine,
not a lower-order term as claimed.

### Gap 3: "Incremental Louvain" costs O(T log T) — both parts false
**Claim:** "Incremental Louvain on |V|=O(T) vertices costs O(T log T)"
**Reality from code:**
- The Louvain is NOT incremental (G = nx.Graph() new every call)
- The cosine_similarity(vectors) is O(n²·d) per call, NOT O(n log n)
- Across T/consolidation_interval calls with growing n:
  Total cost = O(T³·d) across the campaign

**Fix for all three gaps:**
Option A (honest): Rewrite Proposition 1 to reflect actual code behavior:
"The total campaign cost is dominated by the Iteration Engine at
O(T·C_max) and the graph consolidator at O(T³·d/interval) for
from-scratch Louvain over the history buffer. For the reported scale
(T=10, d=10, interval=3) this is computationally negligible."

Option B (fix the code first): Implement real incremental Louvain
(see BL-15) then the O(T log T) claim becomes achievable.

### Gap 4: Numeric example ≠ proof
The line "for C_max=4000 and T=1000, T·C_max = 4×10⁶ ≫ T log T ≈ 10,000"
is one data point, not a mathematical proof. Replace with a proper
asymptotic argument.

**Acceptance criteria:**
- [ ] Proof derives activation count correctly (not O(T/C_max))
- [ ] Total cost formula is consistent with the actual code's behavior
- [ ] No ∎ symbol without a complete, logically valid derivation

---

## Issue 12.2 — No Louvain vs. Grid Justification
**Evidence:** The manuscript never names rectangular grid partitioning
as an alternative, never computes its cost, and never argues why
Louvain's modularity maximization is preferred.

**Fix:** Add a paragraph in Section 3.3 or 3.4:
"Compared to rectangular grid partitioning (O(n log n) sorting per
dimension) which groups configurations into fixed hypercube cells,
Louvain community detection identifies non-rectangular groupings
that capture cross-parameter covariance interactions (e.g., the
interaction between learning rate and optimizer type). This is
essential when hyperparameter effects are not axis-aligned — a
known property of deep learning training dynamics [cite relevant HPO
paper, e.g. Bergstra & Bengio 2012]."

**Acceptance criteria:**
- [ ] Grid partitioning named and compared to Louvain in manuscript
- [ ] Non-rectangular covariance argument is explicit, not implicit
