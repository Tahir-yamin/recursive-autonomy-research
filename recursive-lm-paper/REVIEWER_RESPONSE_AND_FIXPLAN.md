# Reviewer Response & Fix Plan — recursive-lm-paper

Response to the 15-persona Q1 audit (`PEER_REVIEW_Q1_AUDIT.md`). Each item lists
the reviewer's blocker, the action taken in this honesty pass, and status:
**DONE** (fixed now), **REMAINING** (genuine future engineering, now stated
honestly in the paper instead of overclaimed).

Guiding principle: every claim must be backed by the code and the data. Where a
capability is not implemented, the paper now says so explicitly rather than
implying it exists.

---

## #1 TPAMI — benchmark / stats / format
- **Parity overclaim → equivalence.** Added a paired TOST: equivalence within
  ±2 points (p=0.003; 95% CI [-0.65,+1.40]); superiority test still reported as
  non-significant. Abstract, Results, Table 1 caption updated. **DONE.**
- **Embedded red-team log** removed entirely. **DONE.**
- **Near-chance benchmark** acknowledged as a proof-of-concept limit (L5). **DONE (disclosed); REMAINING** to run a harder benchmark.
- **Journal vs conference class:** currently `[conference]`. Switch to
  `[journal]{IEEEtran}` if targeting TPAMI specifically. **REMAINING (venue choice).**

## #2 ACM TODS — formal schema / amortized cost
- Cost claim reframed (Prop. 1) to a real **bounded-window** statement
  ($M{=}50$): token cost $O(T\,\alpha\Cmax)$, consolidation $O(T M^2 d)$ linear in
  $T$ — provable from the code. **DONE.**
- deque bound + `asyncio.to_thread` confirmed accurate. **DONE.**
- Fully formal multigraph schema with incidence function Φ. **REMAINING.**

## #3 NVIDIA — hardware honesty
- Removed the `set_num_threads(1)`-per-seed overclaim; §7 now lists thread
  offload as implemented and is silent on affinity it does not do. **DONE.**
- Architecture figure is logical, not hardware-boundary; acceptable for scope,
  not reintroduced as a hardware claim. **DONE.**

## #4 Cohere — safety / injection
- Injection claim **scoped to what `is_valid_config` does** (validates the
  proposer's *output* against the schema) and explicitly states it does *not*
  sanitize summarizer *input*. **DONE.**
- Leaked-looking `sk-or-v1-...` string removed with the red-team section. **DONE.**

## #5 Scale AI — data rigor
- "Swiss Roll" comment removed; "dynamic" softened to "procedurally generated,
  fixed warp re-sampled per seed." **DONE.**
- Near-chance benchmark disclosed (L5). **DONE.**
- Dataset version/hash stamp in `pilot_results.json`; explicit one-shot
  Test-Vault lock. **REMAINING.**

## #6 MSR — hygiene
- No duplicate packages / Windows abs paths (verified). **PASS.**
- WAL final-failure currently logs and continues (data-loss risk) — should
  `raise`. **REMAINING (code).**

## #7 JMLR — numbers trace to JSON
- All Table 1 numbers re-derived and confirmed exact vs `pilot_results.json`. **PASS.**
- δ thresholds (0.50/0.90) are nominal modeling parameters, not fitted — should
  be stated as illustrative or empirically calibrated. **REMAINING (one sentence + or a calibration study).**

## #8 Hugging Face — cost honesty
- Added explicit cost caveat (L7): LLM-orchestration is **not** cost-competitive
  with classical HPO at this scale; efficiency is reported relative to other LLM
  agents. **DONE.**

## #9 ETH HPC — threading / scaling on hot path
- "Incremental" claim corrected; Prop. 1 now reflects from-scratch consolidation
  bounded by the fixed window. **DONE.**
- True per-seed affinity on the orchestrator hot path. **REMAINING (code).**

## #10 SANS — security claims / standards grounding
- **OWASP fixed:** removed the false "API9 = Injection" mapping; note that
  Injection was removed from the 2023 API Top 10; kept correct API4 mapping. **DONE.**
- SOC 2 name-drop removed; WAL SHA-256 is written **and verified** (accurate). **DONE.**
- `\bibitem{owasp2023api}` present and resolves. **PASS.**

## #11 JetBrains — code craft
- Misleading "structured logger replaces print()" comment corrected to admit
  print() remains on hot paths. **DONE (honest).**
- Migrate error/warning sites to the logger; narrow bare/broad `except`. **REMAINING (code).**

## #12 Oxford — proofs / complexity
- "Proof sketch" replaced with a **valid bounded-window proof** that makes no
  unbounded claim and does not depend on unimplemented incremental Louvain. **DONE.**
- Explicit Louvain-vs-grid justification (or lean on the negative ablation). **REMAINING.**

## #13 AWS — cloud realism
- Cloud section rewritten as **explicit design intent / future work**, clearly
  marked not-implemented, with a **Redlock safety caveat** and Kleppmann
  citation; recommends fencing tokens / DynamoDB conditional writes instead. **DONE.**

## #14 LangChain — schema-driven
- Corrected: paper now states `config_to_vector` **hardcodes** normalization for
  the present 7-parameter space and is **not** schema-agnostic today
  (`is_valid_config` is). **DONE.**

## #15 Neo4j — graph modeling / incremental
- Incremental-Louvain claim corrected to honest from-scratch + bounded window;
  real incremental detection named as future work (Neo4j GDS). **DONE.**
- Named relationship labels (SUCCEEDS/COSINE_SIM) in a real schema. **REMAINING.**

---

## Summary
- **Resolved now (honesty/claims):** #1 stats+log, #3, #4, #8, #9 claims, #10,
  #12, #13, #14, #15 claims, plus #2/#5 wording. The paper no longer claims any
  capability the code does not implement.
- **Remaining = real engineering or a venue decision**, now disclosed in
  Limitations rather than hidden: harder benchmark (#1/#5), dataset versioning
  (#5), WAL `raise` on final failure (#6), threshold derivation (#7), logger
  migration + exception narrowing (#11), true incremental Louvain (#9/#15),
  schema-general vectorizer (#14), formal graph schema (#2/#15), journal class (#1).

The honest paper is now an **efficiency result at demonstrated accuracy-equivalence**
on a controlled synthetic task, with an explicit, accurate boundary between what
is implemented and what is future work.
