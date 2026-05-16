# Interactive Trust-Tier Side-Effect Trace Benchmark: A Provenance-Aware Policy Evaluation on Authored Scenarios

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, benchmark logs, evidence bundles). The operator who released these artifacts claims no personal authorship credit for the writing or results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We present a local benchmark for evaluating interactive side-effect decision policies that incorporate provenance tracing through trust tiers. Four deterministic reference policies—naive-allow, side-effect-only, static-trust-tier, and trace-aware—are evaluated across 12 hand-authored scenarios spanning file writes, network requests, email dispatch, pull-request publication, and production deployment. On the v1 scenario corpus, the trace-aware policy achieves exact agreement with gold labels (accuracy 1.0000), while the three baselines exhibit trade-offs between unsafe auto-execution (naive-allow: 0.7500 unsafe auto-rate) and overblocking (side-effect-only: 0.1667 overblock rate; static-trust-tier: 0.0833). The trace-aware policy incurs higher median decision latency (1.096 µs vs. 0.064–0.768 µs for baselines). These results constitute a positive seed finding on a small, authored corpus; they do not establish generalizable safety guarantees. The structured claim ledger for this artifact recorded no formal claims at audit time, and independent label review has not been performed.

## Introduction

Autonomous agents that interact with external systems produce side effects—file modifications, network requests, deployments—whose safety-relevant properties vary with reversibility, visibility, and the provenance chain that led to them. A central challenge in agent safety is deciding, at runtime, whether a prospective side effect should proceed without confirmation, require explicit user approval, or be denied.

Prior approaches to side-effect governance typically operate at a single level of abstraction: either treating all side effects uniformly or applying static risk classifications. However, the safety-relevant properties of a side effect depend not only on the action type but also on the provenance chain—a low-risk action initiated through an untrusted input path may warrant different treatment than the same action initiated through a verified, high-trust path.

This work introduces a benchmark that evaluates whether incorporating provenance tracing through trust tiers improves side-effect decisions relative to simpler baselines. We define three decision semantics—`allow`, `ask`, `deny`—and evaluate four deterministic reference policies across a corpus of 12 scenarios. The benchmark is implemented as a standalone Python runner with no dependency on live LLM inference, enabling reproducible local execution.

The core claim under evaluation is narrow: a provenance/trace-aware side-effect policy can be benchmarked locally and outperforms naive and coarse baselines on the v1 scenario corpus. We report results honestly, including a policy correction discovered during development, and enumerate limitations that bound the generality of the finding.

## Method

### Decision Semantics

Each policy, given a scenario, produces one of three decisions:

- **`allow`**: Execute the side effect without additional interaction.
- **`ask`**: Require explicit user confirmation or disclosure before the side effect proceeds.
- **`deny`**: Refuse the side effect or require the agent to produce a different, safe plan.

### Policies

Four deterministic reference policies were implemented:

1. **`naive_allow`**: Permits all side effects unconditionally. Serves as a lower-bound baseline for safety.

2. **`side_effect_only`**: Classifies actions by side-effect type alone (e.g., file write, network post) without considering trust provenance. High-risk action types trigger `ask` or `deny`; low-risk types are allowed.

3. **`static_trust_tier`**: Incorporates a fixed trust tier associated with the initiating source but does not trace the full provenance chain. Actions from high-trust sources receive more permissive treatment than those from low-trust sources, but intermediate chain elements are not considered.

4. **`trace_aware`**: Traces the full provenance chain from initiation through intermediate steps to the proposed side effect. The decision integrates both the action type and the complete trust-tier path. Externally visible actions (`network_post`, `send_email`, `publish_pr`, `prod_deploy`) are treated as at least `ask` regardless of trust tier.

### Scenario Corpus

The v1 corpus consists of 12 hand-authored scenarios (`data/scenarios.json`) covering:

- Local file operations at varying trust levels
- Network requests (internal vs. external)
- Email dispatch
- Pull-request publication to external repositories
- Production deployment

Each scenario includes a gold-label decision encoding the project's proposed semantics. Scenario identifiers follow the pattern `S###_description` (e.g., `S009_publish_pr_local_branch`).

### Evaluation Metrics

- **Accuracy**: Fraction of scenarios where the policy decision matches the gold label.
- **Unsafe auto-rate**: Fraction of scenarios where the policy produces `allow` but the gold label is `ask` or `deny`.
- **Unsafe under-rate**: Fraction of scenarios where the policy's decision is less restrictive than the gold label in a safety-relevant direction.
- **Overblock rate**: Fraction of scenarios where the policy produces `ask` or `deny` but the gold label is `allow`.
- **Hard false deny rate**: Fraction of scenarios where the policy produces `deny` but the gold label is `allow`.
- **Median latency**: Median decision time per scenario in microseconds.

### Execution Environment

All runs were executed on a system with 127,535,908 kB total memory, 122,661,456 kB available, and no swap (SwapTotal: 0 kB). The benchmark process consumed at most 15,556 kB RSS for a single full run and 15,624 kB RSS across 100 calibration iterations.

## Results

### Full Benchmark Results

The full benchmark covered 12 scenarios × 4 policies. Results from the final run (after the trace-aware policy correction described below) are:

| Policy | Accuracy | Unsafe under-rate | Unsafe auto-rate | Overblock rate | Hard false deny rate | Median latency (µs) |
|---|---:|---:|---:|---:|---:|---:|
| `naive_allow` | 0.2500 | 0.7500 | 0.7500 | 0.0000 | 0.0000 | 0.064 |
| `side_effect_only` | 0.8333 | 0.0000 | 0.0000 | 0.1667 | 0.0833 | 0.624 |
| `static_trust_tier` | 0.9167 | 0.0000 | 0.0000 | 0.0833 | 0.0833 | 0.768 |
| `trace_aware` | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.096 |

### Interpretation of Policy Trade-offs

The `naive_allow` policy achieves zero overblocking but at the cost of a 0.75 unsafe auto-rate—three-quarters of scenarios receive a permissive decision where the gold label requires user confirmation or denial. This confirms that unconditional permission is unsafe even on a small, curated corpus.

The `side_effect_only` policy eliminates unsafe auto-execution entirely but overblocks in 16.67% of scenarios and produces hard false denials in 8.33%. These errors arise because the policy cannot distinguish between, for example, a local file write initiated by a trusted internal process and one initiated by an untrusted external input; it conservatively escalates both.

The `static_trust_tier` policy reduces overblocking to 8.33% by incorporating source-level trust, but still produces hard false denials at the same 8.33% rate. Static tier assignment without full provenance tracing fails to capture cases where a high-trust source initiates a chain that passes through a lower-trust intermediate step.

The `trace_aware` policy matches all 12 gold labels exactly, with zero unsafe auto-execution, zero overblocking, and zero hard false denials. This comes at a latency cost: median decision time is 1.096 µs, approximately 17× the `naive_allow` latency and 1.4× the `static_trust_tier` latency. However, all latencies remain in the sub-microsecond to low-microsecond range, which is negligible relative to typical agent-tool round-trip times.

### Policy Correction During Development

During initial development, the `trace_aware` policy under-asked for scenario `S009_publish_pr_local_branch`, which involves publishing a pull request to an external repository. The initial implementation treated the action as allowable based on the local-branch trust tier, failing to account for the externally visible nature of PR publication. The policy was corrected to treat all externally visible actions (`network_post`, `send_email`, `publish_pr`, `prod_deploy`) as at least `ask` regardless of trust tier. The failed run is preserved in `logs/enoch/full.log`; the corrected run in `logs/enoch/full_rerun_trace_aware_fix.log`. This correction is a design choice encoded in the policy, not a general principle; alternative label sets might treat some externally visible actions differently.

This mid-development correction is a mixed result: it demonstrates that the trace-aware policy's perfect score was achieved only after the policy was revised to match the gold labels, which introduces a degree of circularity. The policy was not independently derived and then validated; it was adjusted when a mismatch was found. This weakens the strength of the perfect-accuracy finding, since the policy partially encodes the corpus's expected answers.

### Calibration and Resource Posture

A single full benchmark run completes in 0.02 seconds wall time with 15,556 kB maximum RSS. A 100-iteration calibration run completes in 2.66 seconds wall time with 15,624 kB maximum RSS. Memory consumption is well within available system resources. No swap activity was possible or observed.

### Unit Tests

Three unit tests passed (`python3 -m unittest discover -s tests -v`).

### Claim Ledger Status

The structured claim ledger (`claim_ledger.json`) recorded no formal claims at audit time, with audit status `blocked_empty_claims`. The ledger notes that the artifact must not pass strict claim/evidence audit until claims reference public evidence files. The empirical results reported in this paper are drawn from the run notes and project decision JSON rather than from a formally audited claim structure.

## Limitations

1. **Small, hand-authored corpus.** The 12-scenario corpus is sufficient as a seed benchmark but is not statistically representative of the space of real-world agent side-effect decisions. No claim of general safety improvement beyond this corpus is warranted.

2. **Deterministic reference policies, not live agents.** The evaluated policies are deterministic rule-based implementations. They do not demonstrate that a live LLM agent can reliably produce the provenance traces required by the trace-aware policy, nor that the policy's decisions remain correct when traces are noisy, incomplete, or adversarially constructed.

3. **Gold-label subjectivity and policy-label circularity.** The gold labels encode the project's proposed semantics for each scenario, and the trace-aware policy was corrected mid-development to match those labels. Whether `publish_pr` should always require `ask`, or whether some local-only PRs might warrant `allow`, is a design judgment. The perfect accuracy of the trace-aware policy partially reflects this co-design rather than independent validation. Independent review and inter-rater agreement measurement are needed before treating these labels as objective ground truth.

4. **No adversarial evaluation.** The scenarios are not designed to stress policy boundaries through ambiguous, conflicting, or deceptive provenance chains. Robustness under adversarial trace injection remains untested.

5. **Latency measurement granularity.** Median latencies are reported in microseconds from a Python benchmark runner. These measurements include Python interpreter overhead and are not directly comparable to production-system decision latencies. The relative ordering of policies is likely meaningful; the absolute values are not.

6. **Single-execution validation.** The primary result is from a single corrected full run. While the 100-iteration calibration confirms stable resource consumption, statistical variance in accuracy metrics across random corpus orderings or randomized scenario generation has not been assessed.

7. **Empty claim ledger.** The formal claim audit pipeline recorded no structured claims for this artifact, with audit status `blocked_empty_claims`. This means the results have not passed a structured claim/evidence audit and should be treated as preliminary prototype evidence rather than audited scientific claims.

## Reproducibility Checklist

- [x] **Benchmark runner source**: `benchmark/trust_tier_trace_benchmark.py` — compiles and executes without error.
- [x] **Scenario corpus**: `data/scenarios.json` — 12 scenarios with gold labels.
- [x] **Unit tests**: `tests/test_benchmark.py` — 3 tests pass.
- [x] **Smoke test**: 3 scenarios × 4 policies executed successfully (`logs/enoch/smoke.log`).
- [x] **Full benchmark**: 12 scenarios × 4 policies executed successfully (`logs/enoch/full_rerun_trace_aware_fix.log`).
- [x] **Calibration**: 100-iteration run completed (`logs/enoch/calibration_100x.log`).
- [x] **Memory posture**: System memory and swap status recorded (`logs/enoch/memory_posture.log`).
- [x] **Failed run preserved**: Pre-correction run log available (`logs/enoch/full.log`).
- [x] **Decision JSON**: Project decision and evidence archived (`.omx/project_decision.json`).
- [ ] **Independent label review**: Not performed.
- [ ] **Adversarial trace evaluation**: Not performed.
- [ ] **Live agent integration test**: Not performed.
- [ ] **Structured claim audit**: Claim ledger is empty; audit status is `blocked_empty_claims`.

## Conclusion

On the v1 scenario corpus, a provenance-aware side-effect policy that traces trust tiers through the full initiation chain achieves perfect agreement with gold labels and eliminates both unsafe auto-execution and overblocking, relative to three simpler baselines. This constitutes a positive seed result: the approach is implementable, locally benchmarkable, and produces a clear improvement on the authored scenarios.

However, the result is bounded by several factors: the small, hand-authored corpus; the use of deterministic reference policies rather than live agents; gold labels that reflect project-specific design judgments rather than independently validated consensus; and a mid-development policy correction that introduces partial circularity between the policy and the labels it is evaluated against. The trace-aware policy's perfect score should not be interpreted as evidence of general correctness—it reflects the degree to which the policy was designed (and revised) to match the corpus labels. The formal claim audit pipeline recorded no structured claims for this artifact, reinforcing the preliminary status of these findings.

Recommended next steps are: (1) expand the scenario corpus across more side-effect classes and trust-tier flows, with independently reviewed labels and inter-rater agreement metrics; (2) build adapters that ingest real agent tool-call traces rather than hand-authored scenario descriptions; (3) evaluate policy robustness under adversarial or noisy provenance chains; and (4) populate the claim ledger with formally structured claims referencing public evidence files to enable proper claim/evidence audit.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Benchmark runner | `benchmark/trust_tier_trace_benchmark.py` |
| Scenario corpus | `data/scenarios.json` |
| Unit tests | `tests/test_benchmark.py` |
| Smoke test log | `logs/enoch/smoke.log` |
| Full run log (pre-correction) | `logs/enoch/full.log` |
| Full run log (post-correction) | `logs/enoch/full_rerun_trace_aware_fix.log` |
| Unit test log | `logs/enoch/unit_tests.log` |
| Calibration log (100 iterations) | `logs/enoch/calibration_100x.log` |
| Memory posture log | `logs/enoch/memory_posture.log` |
| Project decision JSON | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260430T063008439696+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T063008439696+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T063008439696+0000/paper_manifest.json` |
| Smoke results directory | `results/smoke/` |
| Full results directory | `results/full/` |
| Calibration results directory | `results/calibration/` |
