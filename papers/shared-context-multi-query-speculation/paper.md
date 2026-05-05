# Shared-Context Multi-Query Speculation: Adaptive Draft-Depth Control from Online Acceptance Signals Across Related Queries

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, simulator output, and environment logs). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact.

---

## Abstract

Speculative decoding accelerates autoregressive inference by drafting candidate tokens and verifying them against a target model. We investigate whether sharing online acceptance-rate signals across clusters of related queries can improve speculative decoding efficiency beyond fixed-depth batched verification. We implement a self-contained simulator that models exact speculative decoding—output quality is preserved by construction—and compare four policies across four scenarios varying in shared-context strength and acceptance-rate dynamics. The shared-context adaptive policy reduces wasted draft compute by 19–23% relative to the strongest batched baseline across all scenarios and improves modeled accepted-token throughput by 4–37% depending on scenario. However, it does not improve accepted tokens per verifier call versus fixed-depth batched verification; gains arise from spending fewer verifier-token positions and less draft work, not from increasing per-call acceptance. These results are simulator-only and do not account for GPU kernel behavior, KV-cache implementation, or real model acceptance distributions. Final scientific closure requires validation with a real target/draft model pair.

## Introduction

Speculative decoding accelerates autoregressive language model inference by having a small draft model propose candidate continuations that the target model verifies in a single forward pass, accepting tokens that match the target distribution exactly. The efficiency of this process depends on the acceptance rate: higher acceptance yields more tokens per target-model invocation and less wasted draft computation.

Recent work has explored dynamic adaptation of the speculative process. Medusa verifies multiple candidate continuations per target-model step using tree attention. EAGLE-2 argues that acceptance is context-dependent and uses context-aware dynamic draft trees. An ACL 2025 contribution reports that on-the-fly adaptation of draft window and model selection can improve standard speculative decoding without offline benchmarking. A 2026 reinforcement-learning approach frames draft-tree hyperparameters as real-time context-aware decisions. These results support the principle of dynamic, context-aware speculative policies.

A natural extension arises in multi-query serving settings. When multiple queries share a common context prefix—batch chat over the same document, FAQ-style queries, or code completion in the same repository—their acceptance rates may be correlated. If one query in a cluster exhibits high acceptance, related queries may too. Sharing online acceptance signals across a cluster could allow the system to adapt draft depth more efficiently than independent per-query adaptation.

This paper asks: **Can a shared-context, multi-query speculative decoding policy beat uniform verifier checks by adapting draft depth and verification effort from online acceptance signals across related queries?**

We report results from a self-contained simulator that models exact speculative decoding. We do not claim these results generalize to real hardware without validation.

## Method

### Simulator Design

We implemented a Python simulator (`scripts/shared_context_spec_sim.py`) that models exact speculative decoding. Drafted tokens are accepted only when the verifier would accept them under the standard speculative decoding acceptance criterion, so output quality is preserved by construction (`quality_delta = 0.0`). Policies affect only verifier call count, draft depth, batching strategy, and wasted draft compute—not the output distribution.

This is a toy simulation: it abstracts GPU kernel behavior, KV-cache implementation, real model acceptance distributions, and memory hierarchy effects. It serves as a first-pass feasibility probe, not as a substitute for real-model measurement.

### Policies

We compare four policies:

1. **`uniform_per_query`** — Fixed draft length, one verifier call per query. No batching, no adaptation. This is the weakest baseline.

2. **`uniform_batched_by_cluster`** — Fixed draft length, verifier calls batched by shared-context cluster. This is the strongest local baseline because batching amortizes verifier overhead across related queries.

3. **`independent_adaptive_buckets`** — Per-query online draft-depth adaptation based on each query's own acceptance history, with verifier calls batched by chosen depth.

4. **`shared_context_adaptive`** — Cluster-level online acceptance estimate chooses draft depth for all queries in the cluster, with a shared-prefix verifier overhead discount. This is the proposed policy.

### Scenarios

Four scenarios test different shared-context assumptions and acceptance-rate dynamics:

- **`faq_related`** — Related FAQ/batch-chat prompts over common context. Strong shared-context assumption, high acceptance rates.

- **`mixed_general`** — Weaker shared-context assumption. Queries are loosely related with moderate acceptance rates.

- **`bursty_structured`** — Code/JSON-like generation with high-confidence runs punctuated by low-confidence cliffs. Acceptance rates are bursty.

- **`adversarial_interference`** — Queries appear to share context but have misleading or divergent continuations. Tests robustness when the shared-context assumption is violated.

### Experimental Protocol

We ran 50 trials per scenario. Each trial samples acceptance rates from scenario-specific distributions and applies all four policies. Metrics are averaged across trials.

The simulator was validated with two smoke tests (2 trials each) before the main 50-trial run. Memory was monitored before and after the main run; no anomalies were observed (available memory changed from 122,614,896 kB to 122,626,684 kB; swap was intentionally disabled at 0 kB).

### Metrics

- **Accepted/call** — Mean accepted tokens per verifier invocation.
- **Tokens/time** — Modeled accepted-token throughput (higher is better).
- **Wasted draft ratio** — Fraction of drafted tokens that are rejected (lower is better).
- **Relative tokens/time vs. uniform batched** — Percentage change in throughput relative to the strongest baseline.
- **Relative waste reduction** — Percentage reduction in wasted draft ratio relative to the strongest baseline.

The baseline for all relative comparisons is `uniform_batched_by_cluster`, as it represents the strongest fixed-depth policy that also exploits shared context.

## Results

### Main Results

Table 1 presents results from 50 trials per scenario. All relative metrics use `uniform_batched_by_cluster` as baseline.

**Table 1.** Simulator results across four scenarios and four policies (50 trials each). Relative columns use `uniform_batched_by_cluster` as baseline.

| Scenario | Policy | Accepted/call | Tokens/time | Wasted draft | Rel tok/s vs batched | Rel waste reduction |
|---|---|---|---|---|---|---|
| adversarial_interference | independent_adaptive_buckets | 1.702 | 0.939 | 0.720 | +19.2% | +14.2% |
| adversarial_interference | shared_context_adaptive | 1.526 | 0.990 | 0.648 | +25.7% | +22.8% |
| adversarial_interference | uniform_batched_by_cluster | 1.857 | 0.788 | 0.840 | baseline | baseline |
| bursty_structured | independent_adaptive_buckets | 1.638 | 0.923 | 0.717 | +11.9% | +15.3% |
| bursty_structured | shared_context_adaptive | 1.526 | 1.131 | 0.685 | +37.0% | +19.1% |
| bursty_structured | uniform_batched_by_cluster | 1.719 | 0.825 | 0.846 | baseline | baseline |
| faq_related | independent_adaptive_buckets | 7.109 | 2.846 | 0.494 | −35.1% | +6.3% |
| faq_related | shared_context_adaptive | 9.322 | 4.560 | 0.403 | +4.0% | +23.5% |
| faq_related | uniform_batched_by_cluster | 12.285 | 4.384 | 0.527 | baseline | baseline |
| mixed_general | independent_adaptive_buckets | 4.016 | 1.844 | 0.622 | +27.1% | +13.5% |
| mixed_general | shared_context_adaptive | 2.641 | 1.600 | 0.580 | +10.3% | +19.3% |
| mixed_general | uniform_batched_by_cluster | 3.223 | 1.451 | 0.719 | baseline | baseline |

### Positive Signals

The shared-context adaptive policy shows consistent improvements in wasted draft reduction across all four scenarios (19.1–23.5% reduction vs. the batched baseline). Throughput improvements are scenario-dependent:

- **`bursty_structured`**: +37.0% tokens/time. This is the strongest result, consistent with the intuition that bursty acceptance patterns benefit most from adaptive depth control.
- **`adversarial_interference`**: +25.7% tokens/time and +22.8% waste reduction. The policy remains beneficial even when the shared-context assumption is partially violated.
- **`mixed_general`**: +10.3% tokens/time and +19.3% waste reduction.
- **`faq_related`**: Only +4.0% tokens/time, though +23.5% waste reduction. The high baseline acceptance rate in this scenario leaves less room for throughput improvement.

The independent adaptive policy (`independent_adaptive_buckets`) also improves throughput in three of four scenarios but performs poorly in `faq_related` (−35.1% tokens/time), likely because independent adaptation cannot exploit the cluster-level acceptance correlation that the `faq_related` scenario exhibits.

### Negative Signals

The shared-context adaptive policy **does not improve accepted tokens per verifier call** versus the batched fixed-depth baseline. In every scenario, `uniform_batched_by_cluster` achieves higher accepted/call than `shared_context_adaptive`. The throughput gains arise from spending fewer verifier-token positions and less draft work, not from increasing per-call acceptance.

Accepted/call deltas for `shared_context_adaptive` vs. `uniform_batched_by_cluster` are negative in all scenarios:

- `faq_related`: −0.241 (from 12.285 to 9.322)
- `mixed_general`: −0.181 (from 3.223 to 2.641)
- `bursty_structured`: −0.112 (from 1.719 to 1.526)
- `adversarial_interference`: −0.178 (from 1.857 to 1.526)

If the goal is strictly "more accepted tokens per verifier call," this simulator gives a negative result versus batched fixed-depth verification.

### Success Criteria Assessment

Against pre-registered success criteria:

- **≥15% accepted tokens per second**: Met in `bursty_structured` (+37.0%) and `adversarial_interference` (+25.7%); not met in `faq_related` (+4.0%) or `mixed_general` (+10.3%).
- **≥20% less wasted draft compute**: Met in `faq_related` (+23.5%) and `adversarial_interference` (+22.8%); near miss in `mixed_general` (+19.3%) and `bursty_structured` (+19.1%).
- **Equal output quality**: Met by construction (exact speculative verification, `quality_delta = 0.0`).
- **Improved accepted tokens per verifier call**: Not met versus `uniform_batched_by_cluster` in any scenario.

## Limitations

1. **Simulator-only results.** The simulator abstracts GPU kernel behavior, KV-cache implementation details, real model acceptance distributions, and memory hierarchy effects. Whether the throughput and waste-reduction gains survive on real hardware with real models is unknown. This is a toy simulation, not a llama.cpp hook-prototype, CUDA copy calibration, or production validation.

2. **Modeled acceptance distributions.** The simulator draws acceptance rates from scenario-specific distributions. Real model acceptance rates depend on draft/target model quality gaps, prompt structure, and decoding temperature in ways not captured here.

3. **Verifier overhead model.** The shared-prefix verifier overhead discount is a modeling assumption. Real shared-prefix KV-cache reuse and verifier batching overhead depend on framework implementation (e.g., vLLM, llama.cpp) and hardware architecture (e.g., UMA vs. discrete GPU).

4. **No real latency measurements.** "Tokens/time" is a modeled metric, not a wall-clock measurement. Real latency includes kernel launch overhead, memory transfer, and scheduling jitter that the simulator does not capture.

5. **Cluster assignment is assumed.** The simulator assumes queries are correctly assigned to shared-context clusters. The `adversarial_interference` scenario tests robustness to partial misassignment, but real cluster assignment may be noisier.

6. **Fixed trial count.** Fifty trials per scenario provides moderate statistical power but may not capture rare failure modes or long-tail acceptance distributions.

7. **No multi-turn interaction.** The simulator models single-turn speculative decoding. Multi-turn conversations with evolving shared context may exhibit different dynamics.

8. **Random seed handling.** Seeds were not logged in the run notes; this is a reproducibility gap. Future runs should record and expose random seeds.

9. **No variance reporting.** The summary table reports means across 50 trials but not standard deviations or confidence intervals, making it difficult to assess the statistical significance of the observed differences.

## Reproducibility Checklist

- **Code available**: `scripts/shared_context_spec_sim.py` (self-contained Python simulator, no ML framework dependency).
- **Environment recorded**: `logs/environment.txt`, `logs/accelerator_probe.txt`. Host: Linux `gx10-efe8`, `aarch64`, NVIDIA GB10, CUDA 13.0, driver 580.x. PyTorch was not preinstalled; the simulator uses pure Python.
- **Smoke tests**: Two smoke runs with 2 trials each logged in `logs/smoke_sim.log` and `logs/smoke_sim_v2.log`.
- **Main run logged**: `logs/main_sim.log` with timestamps and memory snapshots before and after.
- **Raw data**: `results/shared_context_spec/raw.csv`.
- **Summary data**: `results/shared_context_spec/summary.json`, `results/shared_context_spec/summary_table.md`.
- **Random seed handling**: Not specified in run notes; this is a gap.
- **Memory monitoring**: `/proc/meminfo` recorded before and after main run; no anomalies observed.
- **Swap**: Intentionally disabled (`SwapTotal: 0 kB`) to expose out-of-memory conditions.
- **Claim ledger**: `papers/.../claim_ledger.json` exists but contains no structured claims; audit status is `blocked_empty_claims`.

## Conclusion

We investigated whether sharing online acceptance-rate signals across clusters of related queries can improve speculative decoding efficiency. In a self-contained simulator modeling exact speculative decoding across four scenarios and 50 trials each, the shared-context adaptive policy consistently reduced wasted draft compute (19–23% reduction) and improved modeled throughput in scenarios with bursty or adversarial acceptance dynamics (+25–37%). However, the policy does not improve accepted tokens per verifier call versus a fixed-depth batched baseline; gains arise from reduced verifier work and draft waste, not from higher per-call acceptance.

These results are preliminary. The simulator abstracts critical implementation details—GPU kernel behavior, KV-cache sharing, real acceptance distributions, and scheduling overhead—that determine whether the modeled gains transfer to real hardware. We recommend a follow-up experiment using a real speculative decoding backend (e.g., llama.cpp or vLLM) with 16–64 related prompts, measuring actual accepted tokens/sec, verifier invocations, target and draft forward times, and energy utilization against three baselines: autoregressive, fixed-depth speculative batched by shared prefix, and independent adaptive batching. The shared-context adaptive policy should be promoted only if real target runs preserve the simulator's throughput or waste-reduction advantages under equal output-quality checks.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Simulator script | `scripts/shared_context_spec_sim.py` |
| Environment log | `logs/environment.txt` |
| Accelerator probe | `logs/accelerator_probe.txt` |
| Smoke test log 1 | `logs/smoke_sim.log` |
| Smoke test log 2 | `logs/smoke_sim_v2.log` |
| Main run log | `logs/main_sim.log` |
| Raw metrics (CSV) | `results/shared_context_spec/raw.csv` |
| Summary metrics (JSON) | `results/shared_context_spec/summary.json` |
| Summary table (Markdown) | `results/shared_context_spec/summary_table.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Claim ledger | `papers/.../claim_ledger.json` |
| Evidence bundle | `papers/.../evidence_bundle.json` |
| Paper manifest | `papers/.../paper_manifest.json` |
