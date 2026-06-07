# BL-03 — NVIDIA Architect Critiques

**Priority:** 🟠 P1
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** D | Verdict: Reject

---

## Issue 3.1 — Appendix Code Diverges from Disk (REPRODUCIBILITY FAIL)
**Files:** main.tex:880, appendix_codebase.tex:63 vs run_deep_learning_harness.py:13
**Evidence:**
- Appendix shows: `torch.set_num_threads(max(1, min(8, (os.cpu_count() or 4) // 2)))`
- Disk file has: `torch.set_num_threads(1)`
These are materially different. A reader reproducing from the paper
runs N/2 threads; the real code always runs 1.

**Fix:**
- Decide which is correct and apply it consistently.
- Recommendation: `torch.set_num_threads(1)` is the right choice for
  reproducibility in a multi-seeded asyncio context (prevents
  inter-seed thread pool contention).
- Regenerate appendix listing from the actual file (do not hand-edit).

**Acceptance criteria:**
- [ ] Appendix listing byte-matches the disk file for `set_num_threads`
- [ ] A script or Makefile rule regenerates appendix from source

---

## Issue 3.2 — fig1 Has No CPU/GPU/Storage Boundaries
**File:** fig1_architecture.png
**Evidence:** Figure shows 5 colored functional blocks with no hardware
topology. No "CPU" label, no "GPU" label, no "Storage" layer.

**Fix:**
- Add a hardware-boundary layer to fig1 (can be a dashed border around
  the CPU-side blocks, a separate GPU box if/when GPU is used, and a
  storage cylinder for WAL/disk).
- At minimum: add a footnote "All components run on CPU; CUDA path
  available via `torch.device('cuda')` flag" to the figure caption.

**Acceptance criteria:**
- [ ] fig1 caption or figure itself explicitly labels execution tier
      (CPU/GPU/storage)

---

## Issue 3.3 — "Per Seed Process" Architecture Claim is False
**File:** main.tex:360
**Evidence:** Paper says "per seed process" for `set_num_threads`.
Reality: all 10 seeds run sequentially in ONE asyncio process. There
are no subprocesses per seed. The `asyncio.to_thread` dispatch creates
threads in the shared ThreadPoolExecutor, not new processes.

**Fix:**
- Change "per seed process" to "at module initialization in the shared
  orchestrator process" — accurate and still defensible.
- OR: move to true multiprocessing (one `multiprocessing.Process` per
  seed) — then the "per seed process" claim would be accurate, and
  `set_num_threads(1)` in each child process would be meaningful.

**Acceptance criteria:**
- [ ] "Per seed process" language removed or execution model changed
      to match the claim

---

## Issue 3.4 — CUDA Stream Sync Is in `finally` After Return Value Computed
**File:** run_deep_learning_harness.py:267
**Evidence:** `stream.synchronize()` fires in `finally` after
`val_acc = correct/total` is already computed. For the reported
numbers (simulation path) CUDA is never used — making this moot.
For real runs it is technically safe but potentially misleading.

**Fix:** This is low priority — fix after BL-SIM is resolved. Then
verify stream sync placement is correct for the real execution path.

**Acceptance criteria:**
- [ ] (Post BL-SIM) Verify stream.synchronize() placement is
      semantically correct for real PyTorch training path
