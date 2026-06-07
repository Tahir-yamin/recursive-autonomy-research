# BL-04 — Cohere Safety Lead Critiques

**Priority:** 🔴 P0 — Fix in <1 hour, must be done before ANY commit to public repo
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** D | Verdict: Reject

---

## Issue 4.1 — Partial API Key in Published LaTeX (CRITICAL)
**Files:**
- main.tex:2168 — `\texttt{sk-or-v1-d881...}`
- appendix_codebase.tex:1351 — same string
- peer_review_report_stage_3.md:39 — same string
**Evidence:** `sk-or-v1-` is the confirmed real OpenRouter API key
prefix format. Even a partial key narrows brute-force surface and
triggers automated secret scanners (GitHub push protection, trufflehog,
detect-secrets). Will appear in published PDF.

**Fix (5 minutes):**
```bash
# In all three files, replace:
sk-or-v1-d881...
# With:
sk-or-v1-[REDACTED]
```
**Also:** Revoke/rotate the original key in OpenRouter dashboard
immediately if not already done.

**Acceptance criteria:**
- [ ] Zero occurrences of `sk-or-v1-d881` in any file (grep confirms)
- [ ] Key revoked in OpenRouter dashboard
- [ ] `[REDACTED]` placeholder in all three locations

---

## Issue 4.2 — Prompt Injection Mitigation Claim is Architecturally Inverted
**File:** main.tex:478, run_pilot_experiment.py:191–209
**Evidence:** Section 7 claims `is_valid_config` prevents "a malicious
training log from hijacking the system prompt." But `is_valid_config`
validates the LLM **output** (the proposed config JSON), not the LLM
**input** (raw trial log content injected into the context prompt at
lines 757–773). The actual injection surface (log content → LLM prompt)
is unguarded.

**Fix (two options):**

Option A — Implement real input sanitization:
```python
def sanitize_log_entry(entry: str) -> str:
    """Strip potential injection patterns from log content before
    it enters the LLM prompt context."""
    # Remove instruction-like patterns
    import re
    entry = re.sub(r'(?i)(ignore|forget|disregard).{0,30}(instruction|above|prior)', '[SANITIZED]', entry)
    # Truncate to max safe length
    return entry[:500]
```
Apply `sanitize_log_entry` to every trial entry before building
`history_str` at line 757.

Option B — Honest disclosure:
Remove the injection-mitigation claim from Section 7. Add a threat
model caveat: "Input-boundary sanitization is future work; the
current `is_valid_config` guard addresses output schema validation
only."

**Acceptance criteria:**
- [ ] Section 7 accurately describes what `is_valid_config` does
      (output validation, not input sanitization)
- [ ] Either input sanitization is implemented OR the claim is removed
