# BL-15 — Neo4j Graph Scientist Critiques

**Priority:** 🟠 P1
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** Reject

---

## Issue 15.1 — Named Relationship Labels Missing from Schema
**File:** main.tex:263–278
**Evidence:** Λ = {lr, arch, reg, optim, other} are edge-attribute
category labels, not named relationship types. No `SUCCEEDS`,
`COSINE_SIM`, `SIMILAR_TO`, or `BELONGS_TO_COMMUNITY` labels defined.

**Fix:** Add explicit relationship type definitions to Section 3.2:
```
Relationship types in G:
  SUCCEEDS(v_i, v_j): trial j was proposed immediately after trial i
                       in the agent's recommendation sequence
  SIMILAR_TO(v_i, v_j, weight=w): cosine similarity w > 0.3 between
                       config vectors; edge label λ ∈ Λ records
                       which parameter dimension changed most
  BELONGS_TO(v, c):   trial v is a member of Louvain community c
```
These map directly to Neo4j property graph model.

**Acceptance criteria:**
- [ ] At least 2 named relationship types defined with semantics in §3.2
- [ ] Relationship types are referenced in the formal schema notation

---

## Issue 15.2 — §7.4 Has No Cypher, No GDS Reference
**File:** main.tex:496
**Evidence:** §7.4 is one paragraph of "this could map to Neo4j."
No Cypher pattern, no GDS API call, no node label definition.

**Fix:** Add a code-like appendix listing or at minimum inline
Cypher sketches:
```cypher
// Node creation
CREATE (:Trial {id: $trial_id, config: $config_json, accuracy: $acc,
                community: $louvain_community_id})

// Succession edge
MATCH (a:Trial {id: $prev_id}), (b:Trial {id: $curr_id})
CREATE (a)-[:SUCCEEDS]->(b)

// Similarity edge
MATCH (a:Trial {id: $id_i}), (b:Trial {id: $id_j})
WHERE a.id <> b.id
CREATE (a)-[:SIMILAR_TO {weight: $cosine_sim, param_delta: $lambda}]->(b)

// Louvain (Neo4j GDS)
CALL gds.louvain.stream('trialGraph', {seedProperty: 'community'})
YIELD nodeId, communityId
```

**Acceptance criteria:**
- [ ] At least one Cypher CREATE/MATCH pattern in §7.4 or appendix
- [ ] `seedProperty` usage (incremental warm-start) mentioned

---

## Issue 15.3 — `_cpu_louvain_partition` is From-Scratch, Not Incremental
**File:** run_pilot_experiment.py:415–467
**Evidence:** `G = nx.Graph()` at line 415 (new object every call).
No `previous_partition` variable. No `initial_partition` parameter
passed to `louvain_communities`. Full O(n²) cosine matrix every call.
Paper §7.4 claims "caches the partition states from cycle t-1."
This is false.

**Fix (real incremental Louvain):**
```python
# Module-level partition cache
_partition_cache: Dict[int, int] = {}  # trial_index → community_id

def _cpu_louvain_partition(all_trials: list,
                            use_cache: bool = True) -> str:
    G = nx.Graph()
    for i, t in enumerate(all_trials):
        G.add_node(i, config=t["config"], acc=t["acc"],
                   # Seed from previous partition if available
                   community=_partition_cache.get(i, i))
    # ... build edges as before ...

    # Pass previous partition as seed (NetworkX 3.x supports this)
    initial_partition = None
    if use_cache and _partition_cache:
        # Build partition sets from cache
        from collections import defaultdict
        comm_map = defaultdict(set)
        for node_id, comm_id in _partition_cache.items():
            if G.has_node(node_id):
                comm_map[comm_id].add(node_id)
        if comm_map:
            initial_partition = list(comm_map.values())

    communities = list(louvain_communities(
        G, weight='weight', seed=42,
        # Note: NetworkX louvain_communities does NOT support
        # initial_partition natively in v3.x — use python-louvain
        # (community library) which does support partition seeding.
    ))

    # Update cache with new assignments
    for comm_id, comm_set in enumerate(communities):
        for node_id in comm_set:
            _partition_cache[node_id] = comm_id

    # ... rest of function ...
```
Note: NetworkX's `louvain_communities` does not support seeded
initialization. Use `python-louvain` (community package) instead:
```python
import community as community_louvain
partition_dict = community_louvain.best_partition(
    G, weight='weight', random_state=42,
    partition=prev_partition_dict  # warm start
)
```

**Acceptance criteria:**
- [ ] Partition state is stored between consolidation calls
- [ ] New Louvain run is seeded/warm-started from prior partition
- [ ] `G = nx.Graph()` replaced with incremental node/edge delta logic
      OR clear documentation that full rebuild is used with bounded n
- [ ] If full rebuild is kept (acceptable for n≤50): manuscript claims
      corrected from "incremental" to "bounded-window from-scratch"
