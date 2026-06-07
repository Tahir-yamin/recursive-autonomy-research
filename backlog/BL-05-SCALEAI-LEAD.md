# BL-05 — Scale AI Lead Critiques

**Priority:** 🔴 P0
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** D | Verdict: Reject

---

## Issue 5.1 — "Swiss Roll" Survives in Live Code Comment
**File:** run_deep_learning_harness.py:39
**Evidence:** Comment reads: "# Apply complex multi-dimensional
non-linear polynomial and trigonometric warp (Swiss Roll-like curvature)"
The appendix listing was sanitized but the real production code was not.

**Fix:**
```python
# Replace comment at line 39 with:
# Apply non-linear polynomial + trigonometric warp to generate
# a dynamically warped Gaussian quantile manifold
```

**Acceptance criteria:**
- [ ] `grep -ri "swiss roll" *.py` returns zero hits

---

## Issue 5.2 — "Dynamically Warped" Claim is Cosmetically True, Substantively False
**File:** run_deep_learning_harness.py:35–40, main.tex:148
**Evidence:** Warp coefficients are hardcoded: `X + 0.2*(X**2) -
0.1*(X**3) + 0.5*np.sin(X*np.pi)`. The word "dynamic" appears to
mean "generated at runtime," not "structurally varied across seeds."
`make_gaussian_quantiles` has no warp parameters — the manifold
topology is identical across all seeds. Only the point sample varies.

**Fix (two options):**
Option A — Make warp genuinely dynamic:
```python
# Vary warp coefficients by seed
rng = np.random.default_rng(seed)
a, b, c = rng.uniform(0.1, 0.4), rng.uniform(-0.2, -0.05), rng.uniform(0.3, 0.7)
X = X + a*(X**2) + b*(X**3) + c*np.sin(X*np.pi)
```
Then the manifold topology genuinely varies by seed.

Option B — Fix the description:
Change "dynamically warped" to "statically warped at runtime" or
"polynomial-warped Gaussian quantile manifold" — accurate and still
defensible as non-linear.

**Acceptance criteria:**
- [ ] Warp coefficients either vary by seed (Option A) OR description
      uses accurate language (Option B)

---

## Issue 5.3 — "Exactly Once" Test Vault Claim Has No Enforcement
**File:** run_pilot_experiment.py:844, main.tex:317
**Evidence:** `evaluate_test_vault` is called 30 times total (10 seeds
× 3 conditions). There is no flag, lockfile, or assertion preventing
re-evaluation on WAL resume. The "exactly once" claim is prose only.

**Fix:**
```python
# In execute_campaign(), track evaluation:
TEST_VAULT_EVALUATED = set()  # persistent across WAL resume

# Before evaluate_test_vault call:
vault_key = f"{cond}_{seed}"
if vault_key in TEST_VAULT_EVALUATED:
    raise RuntimeError(f"Test vault already evaluated for {vault_key}!")
test_acc = await asyncio.to_thread(evaluate_test_vault, best_config, seed, 15)
TEST_VAULT_EVALUATED.add(vault_key)
```
Or save `TEST_VAULT_EVALUATED` in the WAL so it persists across restarts.

**Acceptance criteria:**
- [ ] A guard prevents double-evaluation of test vault per condition/seed
- [ ] WAL resume path respects the guard
