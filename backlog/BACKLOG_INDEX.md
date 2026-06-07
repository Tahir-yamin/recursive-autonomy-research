# RAR Q1 — Critique Backlog Index

Generated: 2026-06-07
Source: 15-Persona Hard-Liner Peer Review (full sub-agent audit with live web verification)

## ⚠️ MASTER BLOCKER: Simulation Mode
Before any other fix: ALL reported results in `pilot_results.json` were produced by the
hardcoded "SRE Fast Simulation Mode" (`run_pilot_experiment.py:39-91`,
`run_deep_learning_harness.py:134-166, 284-318`), not real LLM experiments.
**Status: OPEN — must be resolved before re-submission.**

---

## Backlog Files (one file = one persona critique)

| File | Persona | Priority | Status |
|------|---------|----------|--------|
| `BL-01-TPAMI-EDITOR.md` | IEEE TPAMI Editor | 🔴 P0 | OPEN |
| `BL-02-ACM-TODS.md` | ACM TODS Reviewer | 🔴 P0 | OPEN |
| `BL-03-NVIDIA-ARCHITECT.md` | NVIDIA Architect | 🟠 P1 | OPEN |
| `BL-04-COHERE-SAFETY.md` | Cohere Safety Lead | 🔴 P0 | OPEN |
| `BL-05-SCALEAI-LEAD.md` | Scale AI Lead | 🔴 P0 | OPEN |
| `BL-06-MSR-ENGINEER.md` | MSR Research Engineer | 🟠 P1 | OPEN |
| `BL-07-JMLR-EDITOR.md` | JMLR Editor | 🔴 P0 | OPEN |
| `BL-08-HUGGINGFACE-LEAD.md` | Hugging Face Production Lead | 🟠 P1 | OPEN |
| `BL-09-ETHZ-HPC.md` | ETH Zurich HPC Chair | 🟠 P1 | OPEN |
| `BL-10-SANS-AUDITOR.md` | SANS Security Auditor | 🔴 P0 | OPEN |
| `BL-11-JETBRAINS-LEAD.md` | JetBrains Lead | 🟡 P2 | OPEN |
| `BL-12-OXFORD-COMPLEXITY.md` | Oxford Complexity Professor | 🔴 P0 | OPEN |
| `BL-13-AWS-ARCHITECT.md` | AWS Architect | 🟠 P1 | OPEN |
| `BL-14-LANGCHAIN-ENGINEER.md` | LangChain Founding Engineer | 🟠 P1 | OPEN |
| `BL-15-NEO4J-SCIENTIST.md` | Neo4j Graph Scientist | 🟠 P1 | OPEN |

## Priority Legend
- 🔴 P0 — Desk-reject / scientific integrity blocker. Submit nothing until fixed.
- 🟠 P1 — Major revision required. Will cause rejection at Q1 venue.
- 🟡 P2 — Minor revision. Will cause reviewer complaints but not outright rejection.

## Implementation Order (recommended)
1. BL-SIM (Simulation Mode) — master blocker
2. BL-04 (credential leak — 5 min fix)
3. BL-10 (SOC 2 missing bibitem — 5 min fix)
4. BL-01 (document class switch IEEEtran)
5. BL-07 (re-run real experiments, replace pilot_results.json)
6. BL-12 (rewrite Proposition 1)
7. BL-15 (implement real incremental Louvain)
8. BL-02 (fix graph schema formalism)
9. BL-14 (fix config_to_vector to be schema-driven)
10. BL-13 (implement BaseStateStore/BaseDistributedLock stubs)
11. BL-05 (fix Swiss Roll in live code, fix manifold warp claim)
12. BL-03 (sync appendix code with disk)
13. BL-06 (fix absolute paths, WAL silent-failure)
14. BL-08 (add HPO cost analysis section)
15. BL-09 (fix set_num_threads placement claim)
16. BL-11 (replace print() with logging, fix exception handlers)
