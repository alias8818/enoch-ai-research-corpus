# Source-Citation KV Reserve: A Trace-Level Evaluation of Citation-Aware Key-Value Cache Residency Policies

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Long-context inference with mandatory source citations requires the key-value (KV) cache to retain both recent generation tokens and distant evidence tokens, but memory budgets often preclude full residency. We propose a *citation-reserve* KV policy that explicitly protects blocks containing answer evidence and citation-locator metadata, filling the remaining budget with recency. We evaluate this policy in a pure-Python trace-level simulator over synthetic 32K-token contexts, comparing it against full-residency, recency-only, and sink+recency baselines across 1,000 trials per configuration. At a resident budget of 1,024 tokens (3.12% of full context), the citation-reserve policy with a 0.99-recall locator and 8 false-positive blocks achieves 0.978 answer-and-citation exact match on single-source tasks and 0.952 on two-source tasks, while recency and sink+recency baselines remain at or below 0.012 and 0.009 respectively. A negative result emerges at 512 tokens (1.56%): two-source reserve exact match drops to 0.664, and even the best oracle-locator configuration reaches only 0.701, indicating a capacity floor near 1,024 tokens for multi-citation tasks in this span-size regime. These results are trace-level residency scores—not live model generation metrics—and do not measure attention quality, latency, or serving behavior. The signal is sufficient to justify implementation in a real KV backend, but scientific closure requires validation with actual transformer attention and generated output fidelity.

## Introduction

Autoregressive transformer inference maintains a key-value (KV) cache of past token representations. For long-context workloads, this cache dominates GPU memory and often exceeds available capacity. Prior work has proposed eviction policies—recency windows, attention-sink retention, importance scoring—to reduce resident KV size while preserving generation quality.

A distinct class of workload—long-context question answering with mandatory source citations—poses a specific challenge: the model must attend to both the recent generation prefix and non-contiguous source spans scattered throughout the input. Pure recency policies evict precisely the distant evidence blocks that cited-answer generation requires. Sink+recency policies retain a fixed prefix but do not adaptively protect evidence at arbitrary positions. Importance-based eviction policies (e.g., H2O, SnapKV) score tokens by observed attention magnitude at prompt-processing time, but their effectiveness for citation tasks—where evidence may receive low attention during prefill but is critical during generation—remains uncharacterized.

We investigate whether a *citation-reserve* policy—one that explicitly protects KV blocks identified as containing answer evidence and citation-locator metadata—can preserve cited-answer exactness at substantially reduced resident budgets. Concretely, we ask: is the task signal strong enough to justify implementing such a policy in a real inference backend?

This paper reports results from a trace-level simulator. We do not claim validation on live model outputs. The distinction between trace-level residency (whether required blocks are present in the cache) and generation-level fidelity (whether a model correctly uses those blocks) is fundamental to interpreting these results.

## Method

### Simulator Design

We implemented a pure-Python trace simulator (`source_citation_kv_reserve_sim.py`) that generates synthetic 32K-token contexts containing:

- **Source headers**: metadata identifying source documents.
- **Citation locators**: spans that reference source locations.
- **Evidence spans**: content required to produce a correct cited answer.

The simulator does not execute a transformer. It evaluates whether a given KV residency policy keeps all *required blocks* (those containing evidence and citation metadata) resident, scoring exact match only when every required block is present. This constitutes an upper bound on real-system performance: a block being resident is necessary but not sufficient for correct generation.

### Policies

Four residency policies are compared:

1. **Full**: All context tokens resident. Upper bound.
2. **Recency**: Only the last $B$ tokens resident, where $B$ is the budget.
3. **Sink+Recency**: First 128 tokens (attention sink) plus the most recent $B - 128$ tokens.
4. **Citation Reserve**: Protect located source/citation/evidence blocks up to a reserve ratio of the budget; fill remaining budget with recency. The locator is parameterized by recall (probability of identifying a required block) and false-positive block count (non-required blocks incorrectly protected).

### Citation Locator Model

The locator is not a real retrieval system. It is parameterized directly:

- **Locator recall**: $\{0.90, 0.95, 0.99, 1.0\}$. Each required block is discovered independently with this probability.
- **False-positive blocks**: $\{0, 8, 32\}$. Non-required blocks are added to the reserve uniformly.

This models an idealized locator with tunable accuracy. The primary reported configuration uses recall 0.99 and 8 false-positive blocks, representing a robust but non-oracle setting. We acknowledge that achieving 0.99 recall on answer-critical source/citation spans in a real system is a non-trivial requirement.

### Reserve Overflow

When protected blocks exceed the budget, the simulator ranks discovered blocks, preferring required blocks over false positives. This constitutes an oracle preference within the discovered set and represents an upper bound on overflow performance. A production system must implement an oracle-free priority score, which may reduce performance below the reported figures.

### Metrics

- **Primary**: `answer_and_citation_em` — exact match requiring all answer-evidence blocks and all citation/source-locator blocks to be resident.
- **Secondary**: answer-only EM, citation-only EM, resident tokens, protected blocks, required-block recall, restore tokens (tokens that would need re-loading from offload to achieve full residency).

### Experimental Configuration

| Parameter | Value |
|---|---|
| Context tokens | 32,768 |
| Trials per configuration | 1,000 |
| Budgets (tokens) | 512, 1024, 2048, 4096 |
| Reserve ratios | 0.25, 0.40, 0.60 |
| Locator recalls | 0.90, 0.95, 0.99, 1.0 |
| False-positive blocks | 0, 8, 32 |
| Facts per task | 1 (single-source), 2 (two-source) |

### Environment

Experiments ran on Linux `gx10-efe8` (kernel 6.17.0-1014-nvidia, aarch64). Swap was intentionally disabled (`SwapTotal: 0 kB`). Available memory remained above 121 GB throughout (before: 121,887,880 kB; after: 121,769,788 kB). Each full run consumed approximately 54 MB max RSS and completed in approximately 35 seconds at ~99% CPU utilization. No swap activity occurred.

## Results

### Main Comparison

Table 1 reports `answer_and_citation_em` for each policy at each budget. The citation-reserve column uses the robust configuration (locator recall 0.99, 8 false-positive blocks). The best reserve column reports the highest EM across all reserve-ratio and locator configurations (including oracle recall 1.0 and zero false positives).

**Table 1.** Answer-and-citation exact match across policies and budgets (1,000 trials per cell).

| Workload | Budget | Resident % | Recency EM | Sink+Rec. EM | Reserve EM (robust) | Restore tok. | Best Reserve EM |
|---|---:|---:|---:|---:|---:|---:|---:|
| Single-source | 512 | 1.56 | 0.002 | 0.000 | 0.976 | 1.34 | 1.000 |
| Single-source | 1024 | 3.12 | 0.012 | 0.009 | 0.978 | 1.15 | 1.000 |
| Single-source | 2048 | 6.25 | 0.048 | 0.042 | 0.981 | 0.88 | 1.000 |
| Single-source | 4096 | 12.50 | 0.106 | 0.103 | 0.984 | 0.72 | 1.000 |
| Two-source | 512 | 1.56 | 0.000 | 0.000 | 0.664 | 11.44 | 0.701 |
| Two-source | 1024 | 3.12 | 0.000 | 0.000 | 0.952 | 2.24 | 1.000 |
| Two-source | 2048 | 6.25 | 0.003 | 0.003 | 0.951 | 2.26 | 1.000 |
| Two-source | 4096 | 12.50 | 0.014 | 0.013 | 0.950 | 2.51 | 1.000 |

### Key Observations

**Citation reserve strongly outperforms recency and sink+recency at every tested budget.** At 1,024 resident tokens (3.12% of full context), the robust reserve policy achieves 0.978 EM (single-source) and 0.952 EM (two-source), while both baselines remain at or below 0.012. This gap is expected given the workload design: required cited evidence is deliberately distributed away from the context tail, so recency-based eviction removes precisely the blocks needed for cited answers.

**Recency and sink+recency are largely ineffective for this workload.** Sink+recency occasionally underperforms pure recency (e.g., single-source at 512 tokens: 0.000 vs. 0.002), likely because the 128-token sink allocation displaces recency slots without covering any required evidence. Both baselines improve with larger budgets but remain far below reserve even at 4,096 tokens (12.50% resident).

**A minimum viable reserve exists near 1,024 tokens.** At 512 tokens, single-source reserve EM remains high (0.976), but two-source EM drops to 0.664. Even the best oracle-locator configuration achieves only 0.701 at this budget, indicating that 512 tokens is below the safe multi-citation reserve floor for the tested span-size distribution. This failure is not a policy defect but a capacity constraint: the combined evidence and citation spans for two independent facts exceed the available protected space.

**Restore tokens are small above the floor.** At 1,024+ tokens, mean restore tokens range from 0.72 to 2.51, suggesting that the reserve policy keeps nearly all required blocks resident with minimal re-loading. At 512 tokens for two-source tasks, restore tokens rise to 11.44, reflecting the capacity shortfall.

**Reserve EM is relatively insensitive to budget above the floor.** From 1,024 to 4,096 tokens, robust reserve EM varies only from 0.978 to 0.984 (single-source) and 0.950 to 0.952 (two-source). The marginal return of additional budget beyond the floor is small in this trace model. This suggests that, for this span-size distribution, the reserve policy saturates quickly once the capacity floor is met.

### Negative Result: Two-Source at 512 Tokens

The 512-token budget is insufficient for two-source tasks. The robust EM of 0.664 and best oracle EM of 0.701 indicate that the reserve cannot reliably protect two independent evidence/citation clusters at this budget. This is a hard capacity constraint: no amount of locator improvement (recall 1.0, zero false positives) can overcome it, as the best oracle EM of 0.701 confirms. The gap between robust EM (0.664) and best oracle EM (0.701) is small, indicating that locator inaccuracy is a minor contributor relative to the budget shortfall at this configuration.

### Mixed Result: Reserve EM Does Not Reach 1.0 Under Robust Conditions

Even at generous budgets (4,096 tokens), the robust reserve configuration does not achieve perfect EM (0.984 single-source, 0.950 two-source). The residual failures stem from the 0.01 locator miss rate: with probability 0.01 per required block, a critical block is not discovered and therefore not protected. This sensitivity to locator recall is a structural property of the policy and motivates the question of whether real locators can achieve and sustain recall at or above 0.99.

## Limitations

1. **Trace-level only.** This simulator evaluates block residency, not transformer attention quality. A block being "resident" in the trace does not guarantee that a real model would attend to it correctly or generate faithful citations. The results are upper bounds on what a real system might achieve. The gap between residency and generation fidelity is unmeasured and could be substantial.

2. **Synthetic contexts.** Contexts are procedurally generated with known required spans. Real documents have more complex structure, ambiguous evidence boundaries, and multi-hop reasoning requirements not modeled here. The span-size distribution is fixed and may not represent natural citation workloads.

3. **Oracle-informed overflow ranking.** When protected blocks exceed the budget, the simulator prefers required blocks over false positives. A production system must implement an oracle-free priority score, which may reduce performance below the reported figures.

4. **Locator is parameterized, not implemented.** Recall and false-positive rates are input parameters. A real citation locator must be built and measured; its actual recall and precision will determine whether the reported EM levels are achievable. The 0.99 recall assumption is demanding and may not hold in practice.

5. **No attention, latency, or serving metrics.** The simulator does not measure attention score degradation, generation latency, offload/restore bandwidth, preemption behavior, or multi-request concurrency. These are critical for serving-system viability and may dominate the engineering trade-offs.

6. **Single span-size regime.** All experiments use 32K-token contexts with a fixed span-size distribution. Performance may differ at other context lengths or evidence distributions. The 1,024-token floor is specific to this regime and should not be generalized without additional experimentation.

7. **Exact match is a strict metric.** The primary metric requires every required block to be resident. Partial credit (e.g., F1 over required blocks) might show different trade-offs, but is not reported here.

8. **Claim audit status.** The claim ledger for this artifact contains no structured claims and its audit status is blocked. The results reported here have not passed a formal claim/evidence audit referencing public evidence files.

## Reproducibility Checklist

- [x] **Code available**: Simulator script at `scripts/source_citation_kv_reserve_sim.py`.
- [x] **Command lines logged**: Full invocation commands recorded in run notes.
- [x] **Trials sufficient**: 1,000 trials per configuration; 64 trials for smoke test.
- [x] **Environment recorded**: Kernel version, architecture, memory state logged before and after runs.
- [x] **Raw results preserved**: Summary JSON files at `results/single_source/summary.json` and `results/two_source/summary.json`; key metrics at `results/key_metrics.csv` and `results/key_metrics.md`.
- [x] **Logs preserved**: `logs/smoke.log`, `logs/full_single_source.log`, `logs/full_two_source.log`.
- [ ] **Explicit random seed setting**: Not confirmed in logged commands. A reader reproducing results should verify whether the script accepts a `--seed` flag or equivalent and set it explicitly.
- [ ] **Real model validation**: Not performed. This is a trace-level study only.
- [ ] **Claim/evidence audit**: The claim ledger audit is blocked with no structured claims extracted. Results should be treated as preliminary.

## Conclusion

A citation-reserve KV policy that protects source-evidence and citation-locator blocks substantially outperforms recency and sink+recency baselines in a trace-level residency benchmark over synthetic 32K-token contexts. At 3.12% resident KV (1,024 of 32,768 tokens), a robust non-oracle locator configuration (0.99 recall, 8 false-positive blocks) achieves 0.978 single-source and 0.952 two-source answer-and-citation exact match, compared to at most 0.012 for baselines. A capacity floor exists near 1,024 tokens: at 512 tokens, two-source EM drops to 0.664, and even the best oracle locator reaches only 0.701.

These results establish that the task signal for citation-aware KV residency is strong at the trace level. However, the gap between trace-level residency and live model generation fidelity remains unmeasured. The residual 1.6–5.0% failure rate under robust conditions is attributable to locator miss rate, and eliminating it would require perfect recall—an unrealistic target for most retrieval systems.

Scientific closure requires implementing the policy in a real KV backend (e.g., a Transformers DynamicCache wrapper or a vLLM/SGLang-style paged KV manager) and evaluating generated answer and citation quality, latency, resident KV bytes, and restore/offload traffic against recency, sink+recency, and importance-based eviction baselines on natural citation-QA workloads. The trace-level results reported here justify that implementation effort but do not constitute evidence that the policy works in practice.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Simulator script | `scripts/source_citation_kv_reserve_sim.py` |
| Key metrics (CSV) | `results/key_metrics.csv` |
| Key metrics (Markdown) | `results/key_metrics.md` |
| Single-source summary | `results/single_source/summary.json` |
| Two-source summary | `results/two_source/summary.json` |
| Smoke test log | `logs/smoke.log` |
| Single-source full log | `logs/full_single_source.log` |
| Two-source full log | `logs/full_two_source.log` |
| Telemetry (before) | `logs/telemetry_before.txt` |
| Telemetry (after) | `logs/telemetry_after.txt` |
| Project decision JSON | `.omx/project_decision.json` |
| Project metrics JSON | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260429T014718342597+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T014718342597+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T014718342597+0000/paper_manifest.json` |

### Prior Work Referenced in Design

- PagedAttention / vLLM: `https://arxiv.org/abs/2309.06180`
- StreamingLLM: `https://arxiv.org/abs/2309.17453`
- H2O: `https://arxiv.org/abs/2306.14048`
- SnapKV: `https://arxiv.org/abs/2404.14469`
- Lost-in-the-Middle: `https://arxiv.org/abs/2307.03172`
