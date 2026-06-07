# BL-14 — LangChain Founding Engineer Critiques

**Priority:** 🟠 P1
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** Fail

---

## Issue 14.1 — `config_to_vector` Fully Hardcoded (Schema-Driven Claim is False)
**File:** run_pilot_experiment.py:345–382
**Evidence:** All normalization constants are literals:
- `(x - 1.0) / 2.0` for num_conv_layers (line 351)
- `(x - 16.0) / 48.0` for filters_2 (line 352)
- `x / 0.5` for dropout_rate (line 353)
- `(log10(x) - log10(0.0001)) / (log10(0.05) - log10(0.0001))` for lr (line 357)
- `(x - 16.0) / 48.0` for batch_size (line 359)
- 3 hardcoded strings for activation one-hot (lines 362–366)
- 2 hardcoded strings for optimizer one-hot (lines 369–372)

**Test:** Adding `filters_2=128` to SEARCH_SPACE silently produces
vectors > 1.0. Adding `optimizer="RMSprop"` silently maps to [0,0].
Section 7.3 claims "automatically adapt without manual modifications"
— this is false.

**Fix:**
```python
def config_to_vector(config: Dict[str, Any]) -> np.ndarray:
    """Schema-driven vectorizer: reads bounds from SEARCH_SPACE at runtime."""
    vec = []
    for key, domain in SEARCH_SPACE.items():
        val = config.get(key)
        if all(isinstance(v, (int, float)) for v in domain):
            # Numeric: min-max normalize from SEARCH_SPACE bounds
            lo, hi = min(domain), max(domain)
            norm = (float(val) - lo) / (hi - lo) if hi != lo else 0.0
            vec.append(norm)
        else:
            # Categorical: one-hot from SEARCH_SPACE list order
            vec.extend([1.0 if val == v else 0.0 for v in domain])
    return np.array(vec, dtype=np.float32)
```
This version NEVER needs manual updates when SEARCH_SPACE changes.

**Acceptance criteria:**
- [ ] `config_to_vector` reads bounds/categories from SEARCH_SPACE
- [ ] Adding a new entry to SEARCH_SPACE requires ZERO changes to
      `config_to_vector`
- [ ] All previous hardcoded constants removed

---

## Issue 14.2 — `is_valid_config` Key List is Hardcoded
**File:** run_pilot_experiment.py:195
**Evidence:**
```python
required_keys = ["num_conv_layers", "filters_2", "activation",
                  "dropout_rate", "optimizer", "lr", "batch_size"]
```
Not derived from `SEARCH_SPACE.keys()`.

**Fix:**
```python
def is_valid_config(config: Dict[str, Any]) -> bool:
    if not isinstance(config, dict):
        return False
    for key, domain in SEARCH_SPACE.items():
        if key not in config:
            return False
        try:
            # Type coerce and check membership
            if all(isinstance(v, int) for v in domain):
                if int(config[key]) not in domain: return False
            elif all(isinstance(v, float) for v in domain):
                if float(config[key]) not in domain: return False
            else:
                if str(config[key]) not in domain: return False
        except (ValueError, TypeError):
            return False
    return True
```

**Acceptance criteria:**
- [ ] `required_keys` derived from `SEARCH_SPACE.keys()`, not hardcoded
- [ ] Adding a new key to SEARCH_SPACE auto-enforces it in validation

---

## Issue 14.3 — §7.3 "Schema-Driven" Claim Must Be Corrected
**File:** main.tex:493
**Evidence:** "The search boundaries, validation rules, and
vectorization spaces are governed by a dynamic JSON schema...
automatically adapt to arbitrary hyperparameter dimensions
without manual codebase modifications."
This is false for the current code but will be true after Issues
14.1 and 14.2 are fixed.

**Fix:** Implement Issues 14.1 and 14.2 first, then the §7.3 text
becomes accurate. No text change needed if code is fixed.

**Acceptance criteria:**
- [ ] BL-14 Issues 14.1 and 14.2 implemented
- [ ] Integration test: add `"weight_decay": [0.0, 1e-4, 1e-3]` to
      SEARCH_SPACE, run a campaign cycle, confirm no crashes and
      correct vector dimension
