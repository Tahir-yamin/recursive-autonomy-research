# Q1 Hard-Liner Peer-Review Audit — recursive-lm-paper

Re-derived from the actual files (main.tex, appendix_codebase.tex,
run_pilot_experiment.py, run_deep_learning_harness.py, pilot_results.json),
with live-source verification. No sugar-coating. Date: 2026-06-14.

Scope note: data-integrity is now SOUND — the fabricated p=0.0010 is gone and
every Table 1 number traces to `pilot_results.json` (verified by recomputation).
The remaining failures are about **prose claiming things the code does not do**,
a **near-chance toy benchmark**, and an **embedded red-team log that does not
belong in a manuscript**.

---

## #1 IEEE TPAMI Editor — Grade D — Reject (resubmit)
- Typesetting clean (no `\noindent\rule`/`\vspace` hacks; `\mathbf` only in math mode). PASS.
- Stats now honest: recomputed Wilcoxon one-sided p=0.2461 (matches paper). PASS on integrity.
- **FAIL: "accuracy parity" claimed from a *non-significant* difference test.** Absence of evidence ≠ equivalence; needs a TOST equivalence test with a stated margin.
- **FAIL: near-chance benchmark.** Best test acc 40.5% vs 33.3% chance = 7.2 pts above chance on a 3-class synthetic manifold (run_deep_learning_harness.py:32-40). Toy for TPAMI.
- Blockers: wrong class (`[conference]` for a journal venue) + embedded red-team §(main.tex:2152+).
- **Biggest blocker:** benchmark realism (near-chance synthetic).

## #2 ACM TODS Reviewer — Grade C− — Major revision
- Graph schema §3.2: vertex tuple `T(v)=(θ,f(θ),x,r)` (main.tex:255), cosine edge weight (261). Semi-formal — **no explicit incidence/labeling function Φ, no named edge types.** PARTIAL.
- `collections.deque(maxlen=MAX_TRIAL_MEMORY=50)` used (run_pilot_experiment.py:693, 236). Bounded. PASS.
- `asyncio.to_thread` wraps Louvain (run_pilot_experiment.py:513). PASS for that call. BUT `save_wal` does synchronous `open/fsync/os.replace` (268-303) — blocking I/O on the loop path. PARTIAL.
- MAX_TRIAL_MEMORY=50 < 60-cycle campaign ⇒ "persistent GraphRAG memory" is actually a last-50 sliding window. Honesty gap.
- **Biggest blocker:** the O(n²)→amortized claim is asserted, not achieved — Louvain is recomputed from scratch (see #15).

## #3 NVIDIA Architect — Grade D+ — Major revision
- `ProcessPoolExecutor(max_workers=1)` removed. PASS.
- **FAIL: `torch.set_num_threads` only in the harness at module level, set to `max(1,min(8,cpu//2))` (main.tex:907 / appendix:65) — NOT `(1)`, NOT per-seed, NOT in the orchestrator** (`run_pilot_experiment.py` has no such call). The "thread-affinity per seed" hardening is not on the hot path that produced the numbers.
- Architecture figure is now vector TikZ but depicts **logical layers, not CPU/GPU/storage boundaries** — the hardware-honesty item the persona demands is absent.
- GPU "available but unused"; runs are CPU (≈400-700 s/seed). Acceptable but the GPU framing is decorative.
- **Biggest blocker:** thread-affinity claim contradicts the code.

## #4 Cohere Safety Lead — Grade C — Major revision
- No hardcoded `sk-` key in active `.py` — keys via `os.environ.get` (run_pilot_experiment.py:30,34-36). PASS.
- **BUT the manuscript body still prints the string `sk-or-v1-...` inside the embedded red-team section** (main.tex:2251; appendix:1409). Placeholder, not a live key — but unprofessional; delete the whole section.
- `is_valid_config` does real membership/type/range checks against SEARCH_SPACE (run_pilot_experiment.py:200-215). PASS as a guard.
- **FAIL (overclaim): §7.1 says this "prevents a malicious training log from hijacking the system prompt."** `is_valid_config` only validates the *final* config dict; it does not sanitize what enters the compression summarizer — the actual indirect-injection surface. Claim exceeds mechanism.
- **Biggest blocker:** injection-defense claim overstated relative to code.

## #5 Scale AI Lead — Grade C− — Major revision
- **"Swiss Roll" NOT fully purged** — survives as a code comment "Swiss Roll-like curvature" (run_deep_learning_harness.py:39) and therefore in the appendix listing.
- **"dynamic/warped manifold" oversold.** `generate_synthetic_manifold` is `make_gaussian_quantiles` + a **fixed deterministic** elementwise warp `X + 0.2X² − 0.1X³ + 0.5·sin(Xπ)` (run_deep_learning_harness.py:32-40). Only the RNG seed varies across seeds; the manifold *structure* is static. "Dynamic" = re-sampled, not dynamically-structured.
- Train/Val/Test split exists (harness:333) and Test Vault is evaluated once at end, but there is **no lock/flag preventing re-touch** and **no dataset version/hash** recorded in `pilot_results.json` (only SEEDS). PARTIAL/leak-risk.
- **Biggest blocker:** near-chance toy benchmark + "dynamic" overstatement + no dataset versioning.

## #6 MSR Research Engineer — Grade B− — Minor→major
- No duplicate `\usepackage`; no Windows absolute paths in code. PASS.
- LaTeX listings styled (`lstset`, language, basicstyle, breaklines). PASS.
- WAL `os.replace` retry: exponential backoff `0.1*2**attempt`, catches `PermissionError/OSError`, 5 attempts (run_pilot_experiment.py:293-301). Good pattern. **BUT on final failure it only `print()`s and continues — the WAL update is silently lost (no raise, no surfaced error).** PARTIAL (data-loss risk).
- **Biggest blocker:** final-failure WAL path loses state with only a print.

## #7 JMLR Editor — Grade B− — Minor→major (data integrity now PASSES)
- Cross-checked every Table 1 number against `pilot_results.json` by recomputation: test acc 40.12/40.19/40.50; tokens 350,249/170,502/105,055; density 1.409/0.660/0.387; token −70.0% and density −72.5% reductions; Wilcoxon p=0.2461. **All trace exactly.** This persona caught the old fraud — it is now resolved.
- **FAIL: δ_low=0.50, δ_high=0.90 are asserted "calibrated," not derived.** No empirical/physical justification — assertion by restatement.
- **Biggest blocker:** threshold values lack derivation (everything else now traces).

## #8 Hugging Face Production Lead — Grade C — Major revision
- "closed-loop ratchet" purged from main.tex. "Swiss Roll" remains in code comment. PARTIAL.
- **FAIL: no quantified cost-benefit.** The paper reports token counts but never compares the cost of running an LLM orchestrator against plain random/Bayesian HPO on a ~5K-param MLP. My estimate: 60 random-search trainings of a sub-5K MLP ≈ seconds-to-minutes of CPU ≈ \$0; the LLM-in-the-loop is strictly *more* expensive for this toy. The premise (big LLM tunes tiny model) is economically unjustified at this scale and the paper doesn't confront it with numbers.
- **Biggest blocker:** the central premise is not cost-justified.

## #9 ETH Zurich HPC Chair — Grade D+ — Major revision
- Sparse k-NN graph (k=3, gated >0.3) implemented (run_pilot_experiment.py:434-443). PASS — bounds edges.
- **FAIL: affinity not on hot path** — `set_num_threads` only in harness module (#3); the multi-seed loop in `run_pilot_experiment.py` never calls it.
- **FAIL: `cosine_similarity(vectors)` over all trials is recomputed every consolidation (run_pilot_experiment.py:430-431) — O(n²·d) from scratch.** Bounded only because the deque caps n at 50; the §7.4 "incremental, caches t−1" claim is not implemented.
- **Biggest blocker:** "incremental/bounded" is achieved by a hard cap, not by the claimed incremental algorithm.

## #10 SANS Security Auditor — Grade C — Major revision
- `\bibitem{owasp2023api}` exists (main.tex:832) and `\citep` resolves (main.aux). The `main.blg` "no database entry" line is a stale artifact (paper uses manual `thebibliography`, not bibtex). **Not a broken reference.** PASS.
- WAL SHA-256 is **written (284) AND verified on load (322-325)** — real integrity check, not theater. PASS.
- **FAIL: OWASP standard mischaracterized.** Paper labels indirect prompt injection as "API9:2023 — Improper Inventory Management / Injection" (main.tex:503). Per OWASP, API9:2023 is *Improper Inventory Management* only, and **Injection was removed from the 2023 API Top 10** ([OWASP API9:2023](https://owasp.org/API-Security/editions/2023/en/0xa9-improper-inventory-management/), [Nordic APIs](https://nordicapis.com/a-look-at-the-owasp-api-security-top-10-2023/)). (API4:2023 = Unrestricted Resource Consumption is used correctly.)
- SOC 2 name-dropped (main.tex:507) with no citation/mechanism beyond env-var keys. PARTIAL.
- **Biggest blocker:** misrepresents the content of a cited security standard.

## #11 JetBrains Lead — Grade C − Major revision
- `perturb_config` has full type hints + docstring (run_pilot_experiment.py:559). PASS.
- **FAIL: logging claim is false.** Line 17 comment says a structured logger "replaces bare print() for error/warning paths," yet error/exception sites use `print()` throughout: 159,162,165,196,197,231,301,303,320,325,329,338,499,544,549.
- **FAIL: bare `except:` (run_pilot_experiment.py:308) and broad `except Exception` at 164,196,230,302,328,337,457,548** — several swallow silently (308 `pass`, 457 fallback).
- **Biggest blocker:** "structured logging" is configured but unused; broad/bare exception handling persists.

## #12 Oxford Complexity Professor — Grade D — Reject (major)
- §3.2 schema is semi-formal prose-with-symbols, not rigorously typed. PARTIAL.
- **FAIL: Proposition 1 is a "Proof sketch" (main.tex:299-301) resting on "Incremental Louvain ... O(T log T)" — which the code does not implement (it recomputes from scratch, #15) and which is mis-cited to Blondel 2008 (standard Louvain has no proven near-linear worst-case bound; the cited paper reports *empirical* speed).** The dominant-term argument is plausible but the load-bearing complexity term is unproven and unimplemented.
- **FAIL: no justification for Louvain over cheaper grid partitioning** — and the ablation shows the Knowledge Map adds no benefit, undercutting the choice entirely.
- **Biggest blocker:** a labeled "proof" that is an order-of-magnitude sketch leaning on an unimplemented claim.

## #13 AWS Architect — Grade D − Reject (for this persona)
- §7.2 (main.tex:509-515): Redis Redlock, S3/DynamoDB, SQS/Kafka/Lambda. **Claimed in prose: yes | implemented in code: NO.** No `BaseStateStore`, `BaseDistributedLock`, adapters, or queue clients exist (grep negative).
- **FAIL: Redlock recommended for correctness-critical locking without caveat** — Redlock is contested for exactly this (no fencing tokens, timing assumptions; [Kleppmann](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)).
- Paper does acknowledge Lambda container freezing (514) — partial awareness — but the whole section is aspirational.
- **Biggest blocker:** the critique asked for interface classes in code; the response added words.

## #14 LangChain Founding Engineer — Grade C− — Major revision
- `is_valid_config` is schema-driven (reads SEARCH_SPACE, run_pilot_experiment.py:209-215). PASS.
- **FAIL: `config_to_vector` is hardcoded** (run_pilot_experiment.py:360-389): literal constants `(x−1.0)/2.0`, `(x−16.0)/48.0`, `/0.5`, `log10(0.0001)…log10(0.05)`, and fixed one-hots for exactly {ReLU,ELU,LeakyReLU} and {AdamW,SGD}.
- **Internal inconsistency:** §7.3 claims "schema-driven … without manual codebase modifications," but **adding one entry to SEARCH_SPACE (e.g., a 4th activation) silently produces wrong/truncated vectors** — `config_to_vector` would not adapt. The "schema-driven" claim is half-true at best.
- **Biggest blocker:** "schema-driven" is false for the vectorization path.

## #15 Neo4j Graph Scientist — Grade D − Reject (for this persona)
- **FAIL: no named relationship labels** (SUCCEEDS / COSINE_SIM or equivalent) in §3.2 — only abstract cosine-weighted edges.
- **FAIL: §7.4 "Neo4j mapping" is prose only** — no Cypher, no node/edge label correspondence.
- **FAIL (the big one): `_cpu_louvain_partition` (run_pilot_experiment.py:424-458) builds the graph fresh, computes `cosine_similarity` over all trials, and runs full `louvain_communities` every call. There is NO `previous_partition` cache and NO local refinement.** §7.4's "caches the partition states from cycle t−1 and performs local refinement updates" is **not implemented** — it is the from-scratch algorithm described as incremental.
- Real incremental/streaming Louvain caches community assignments and only re-evaluates affected neighborhoods (Neo4j GDS; incremental-modularity literature). This code does none of that.
- **Biggest blocker:** the headline "incremental Louvain" claim directly contradicts the code.

---

## Cross-cutting blockers (multiple reviewers)
1. **Prose ≠ code.** "Incremental Louvain" (#9,#12,#15), "schema-driven" (#14), "cloud-native" (#13), "thread-affinity per seed" (#3,#9), "injection defense" (#4) all overstate what the code does. This is the dominant theme.
2. **Embedded red-team audit section** (main.tex:2152-2292) — not manuscript content; delete before any submission (#1,#4).
3. **Near-chance toy benchmark** — 40.5% vs 33.3% chance (#1,#5,#8).
4. **Statistical framing** — "parity" needs a TOST equivalence test, not a null difference test (#1).

## What is genuinely SOLID now
- Data integrity: every number traces to `pilot_results.json` (#7). The fabrication is gone.
- WAL SHA-256 written and verified (#10). deque bound + k-NN sparsification + Louvain offloaded to a thread (#2,#9). No hardcoded credentials in code (#4).

## Net editorial recommendation
Across a Q1 panel this is a **Reject-and-resubmit**: the experiments are now honest but the contribution is an efficiency result on a near-chance toy, and the systems/architecture sections (§7, complexity, graph) repeatedly claim capabilities the code does not implement. Two paths: (a) **scope down** to an honest short paper — "context compression buys equal accuracy at 70% fewer tokens on a synthetic HPO task" — deleting §7's unimplemented cloud/schema/incremental claims and the red-team log; or (b) **build the missing pieces** (real incremental Louvain, schema-driven vectorization, a real benchmark, a TOST) to support the current claims.
