# BL-10 — SANS Security Auditor Critiques

**Priority:** 🔴 P0
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** 35/100 | Verdict: Reject

---

## Issue 10.1 — SOC 2 Cited with No Bibliography Entry (DESK-REJECT)
**File:** main.tex:482
**Evidence:** "SOC 2 Type II Credential Isolation principles" cited
inline as a noun phrase with no `\cite{}` key and no `\bibitem`.
Additionally "Credential Isolation" is not a real SOC 2 TSC criterion
name — it appears to be invented.

**Fix:**
Option A — Add proper bibliography entry and correct the criterion:
```latex
% In bibliography:
\bibitem[AICPA(2017)]{aicpa2017soc2}
AICPA.
\newblock {Trust Services Criteria for Security, Availability,
Processing Integrity, Confidentiality, and Privacy (SOC 2)}.
\newblock \url{https://www.aicpa-cima.com/resources/download/
2017-trust-services-criteria}, 2017.

% In text, replace "SOC 2 Type II Credential Isolation principles"
% with:
% "SOC 2 Trust Services Criteria CC6.2 (Logical Access Controls)
% \citep{aicpa2017soc2}"
```

Option B — Remove the SOC 2 reference entirely:
Replace with: "consistent with OWASP API Security credential-management
best practices \citep{owasp2023api}."

**Acceptance criteria:**
- [ ] No SOC 2 reference without a corresponding \bibitem
- [ ] Criterion name is either CC6.2/CC6.3 (real TSC names) or
      the reference is removed

---

## Issue 10.2 — OWASP API9:2023 Misattributed to Injection
**File:** main.tex:475–478
**Evidence:** Paper cites "OWASP API9:2023 — Improper Inventory
Management / Injection." API9:2023 covers inventory management only.
Injection was removed from the 2023 list (it was API8:2019).

**Fix:**
For API injection discussion, cite OWASP API8:2019 or the 2023
supplement, or use OWASP Top 10 (web app version which still
includes Injection as A03:2021):
```latex
\citep{owasp2019api}  % API8:2019 — Injection
% Add bibitem for OWASP 2019 API Security list
```

**Acceptance criteria:**
- [ ] No reference to API9:2023 in context of injection
- [ ] Injection discussion cites a real OWASP entry that covers injection

---

## Issue 10.3 — SHA-256 Integrity Check is Write-Only Against Privileged Attacker
**File:** run_pilot_experiment.py:257–320
**Evidence (positive):** Checksum IS written and verified on load —
this is a genuine implementation (not theater). PASS for basic
integrity.
**Evidence (gap):** The check detects accidental corruption only.
A local attacker with filesystem access can replace the WAL file and
recompute a valid checksum. The paper should not claim this prevents
intentional tampering.

**Fix:** Update Section 7 text to accurately scope the protection:
"SHA-256 checksums detect accidental WAL corruption; they do not
provide tamper-resistance against adversaries with local filesystem
access. In adversarial deployments, file-system ACLs or a Hardware
Security Module (HSM) would be required."

**Acceptance criteria:**
- [ ] Threat model for SHA-256 correctly scoped in manuscript
