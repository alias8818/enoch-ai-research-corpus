# Attention-Sink Rescue Pool: Preserving Sparse Mid-Context Bridge Tokens in Bounded KV-Cache Retention

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, benchmark logs, decision records, telemetry). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Bounded KV-cache retention for large-language-model inference commonly preserves initial attention-sink tokens and a recent-token window, following the StreamingLLM pattern. This fixed policy discards sparse mid-context tokens that retrieval-oriented attention heads may require for bridging or multi-hop reasoning. We investigate adding a small, bounded **rescue pool** to the sink-plus-recent pattern, selectively promoting tokens identified by an online scoring signal. In a model-free synthetic simulator at KV budget 64 (sink size 4, rescue pool size 8), the rescue-pool policy achieves 0.812 accuracy over 1,000 deterministic probes, compared to 0.400 for sink-plus-recent and 0.200 for pure sliding window. The rescue pool preserves accuracy on prefix-sink, tail-recency, single-bridge, and multi-hop probe families but degrades to 0.060 under adversarial candidate-overflow conditions where rescue candidates exceed pool capacity. Increasing the rescue pool to size 16 recovered full accuracy on the overflow family. These results are confined to model-free synthetic simulation; no real transformer KV-cache instrumentation was performed. The findings are preliminary and do not constitute production-level validation.

## Introduction

Efficient KV-cache management is a practical constraint on long-context language model inference. The StreamingLLM framework demonstrated that retaining a small set of initial attention-sink tokens alongside a sliding window of recent tokens suffices for stable streaming generation, reporting up to 22.2× speedup over sliding-window recomputation baselines (Xiao et al., 2023, arXiv:2309.17453). DuoAttention (Liu et al., 2024, arXiv:2410.10819) subsequently separated retrieval-oriented attention heads from streaming heads, observing that streaming heads primarily need recent tokens and sinks while retrieval heads require broader context access. Empirical studies of attention sinks across models (Zhang et al., 2024, arXiv:2410.10781) confirm that sink behavior is widespread but incompletely understood.

A gap persists between these two regimes. The fixed sink-plus-recent policy drops mid-context tokens that may be critical for sparse retrieval or bridging operations, while granting retrieval heads full context access is expensive. This work investigates whether a small, selectively populated **rescue pool** can recover the specific failure mode of fixed retention—loss of sparse mid-context bridge tokens—without incurring the full cost of wider KV retention.

We pose the following research question: *Can a bounded rescue pool added to the standard attention-sink plus recent-window KV-cache pattern preserve sparse mid-context bridge tokens that fixed StreamingLLM-style retention drops?*

To isolate the information-retention properties of this policy from confounds of any particular model architecture, we implement a model-free synthetic simulator and evaluate across five probe families designed to stress different retention requirements. We report both positive and negative findings.

## Method

### Simulator Design

A model-free simulator was implemented to evaluate KV-cache retention policies under controlled synthetic conditions. The simulator does not execute a real transformer; it models token retention and retrieval as a budget-constrained selection problem. Each probe defines a context of tokens and a correct answer that depends on specific token positions. A probe is scored as correct if and only if all tokens required to produce the answer are retained under the given policy.

### Retention Policies

Five policies were compared:

1. **full_context** — Oracle upper bound; no KV eviction. All tokens are retained.
2. **sliding_window** — Retain only the most recent $w$ tokens; no sink preservation.
3. **sink_recent** — Retain the first $k_{\text{sink}}$ tokens (attention sinks) plus the most recent $w - k_{\text{sink}}$ tokens. This approximates the StreamingLLM retention pattern.
4. **rescue_pool** — Retain the first $k_{\text{sink}}$ sink tokens, a bounded pool of up to $k_{\text{rescue}}$ tokens selected by an observable promotion signal, plus the remaining budget allocated to recent tokens.
5. **random_budget** — Randomly retain tokens within the budget; serves as a lower-bound baseline.

### Probe Families

Five synthetic probe families were designed to isolate distinct failure modes:

- **prefix_sink_only**: The correct answer depends only on the first (sink) tokens.
- **late_tail_lookup**: The correct answer is in the recent tail window.
- **mid_rescue_bridge**: The correct answer requires a single sparse mid-context bridge token that falls outside both the sink and recent windows under fixed retention.
- **multi_hop_rescue**: The correct answer requires the sink token plus two mid-context bridge tokens.
- **rescue_overflow**: Adversarial family with more rescue candidates than the rescue pool can hold, stressing the scoring and eviction policy.

### Rescue Promotion Signal

In the simulator, rescue-eligible tokens are marked with observable metadata tags. These tags stand in for real signals such as attention magnitude, routing tags, or retrieval-head scores. This is a deliberate simplification: the simulator assumes the promotion signal is available and reliable. In a real transformer, this signal would need to be derived from online attention statistics or head-level routing decisions, which remains an open engineering problem.

### Experimental Configuration

| Parameter | Value |
|---|---|
| Number of probes | 1,000 |
| Random seed | 344 |
| KV budget (tokens) | 64 |
| Sink size ($k_{\text{sink}}$) | 4 |
| Rescue pool size ($k_{\text{rescue}}$) | 8 |
| Bootstrap trials | 80 |

An additional sweep with $k_{\text{rescue}} = 16$ was performed on the `rescue_overflow` family.

### Hardware and Environment

The benchmark ran on a host with 116 GiB available memory (swap disabled, posture GB10). GPU utilization was 0% for this model-free run. No GPU computation was involved; the simulator is CPU-only.

## Results

### Overall Accuracy

At KV budget 64, $k_{\text{sink}} = 4$, $k_{\text{rescue}} = 8$, over 1,000 deterministic probes:

| Policy | Accuracy |
|---|---:|
| full_context | 1.000 |
| rescue_pool | 0.812 |
| sink_recent | 0.400 |
| sliding_window | 0.200 |
| random_budget | 0.087 |

The rescue-pool policy more than doubles the accuracy of the standard sink-plus-recent baseline under these synthetic conditions. However, the aggregate number is dominated by the probe-family composition and should not be generalized beyond the specific mix used here.

### Per-Family Accuracy

| Probe Family | full_context | rescue_pool | sink_recent | sliding_window | random_budget |
|---|---:|---:|---:|---:|---:|
| prefix_sink_only | 1.000 | 1.000 | 1.000 | 0.000 | ~0.063 |
| late_tail_lookup | 1.000 | 1.000 | 1.000 | 1.000 | ~0.063 |
| mid_rescue_bridge | 1.000 | 1.000 | 0.000 | 0.000 | ~0.063 |
| multi_hop_rescue | 1.000 | 1.000 | 0.000 | 0.000 | ~0.063 |
| rescue_overflow | 1.000 | 0.060 | 0.000 | 0.000 | ~0.063 |

The rescue pool preserves accuracy on the four non-adversarial families, recovering the exact failure mode of sink-plus-recent on mid-context bridge and multi-hop probes. Under the adversarial `rescue_overflow` condition where rescue candidates exceed pool capacity ($k_{\text{rescue}} = 8$), accuracy collapses to 0.060—only marginally above the random baseline. This is the central negative finding: the rescue pool fails on the exact cases it is designed to address when the pool is undersized relative to candidate volume.

Increasing $k_{\text{rescue}}$ to 16 in a follow-up sweep recovered 1.000 accuracy for the overflow probe generator, confirming that the overflow failure is a capacity constraint rather than a fundamental policy defect. However, this also demonstrates that pool sizing is a critical and workload-dependent design parameter.

### Bootstrap Stability

Over 80 bootstrap resampling trials, the accuracy delta (rescue_pool minus sink_recent) showed:

| Statistic | Value |
|---|---|
| Mean delta | 0.412 |
| Minimum delta | 0.357 |
| Maximum delta | 0.483 |

The improvement is stable across resamples, though the range (0.357–0.483) indicates meaningful variance depending on probe composition. The lower bound of 0.357 confirms that the improvement is unlikely to be an artifact of a single probe mix, but the magnitude of the effect is sensitive to the distribution of probe families.

## Limitations

1. **Model-free simulation only.** No real transformer attention or KV-cache instrumentation was performed. The simulator abstracts away all model-specific dynamics—attention head behavior, token embedding interactions, layer-wise differences, and positional encoding effects. Results demonstrate information-retention properties of the policy under synthetic assumptions, not end-to-end model performance. This is a toy simulation, not a llama.cpp hook-prototype, CUDA calibration, or production validation.

2. **Synthetic promotion signal.** The rescue pool depends on a reliable online signal to identify and promote rescue candidates. The simulator uses explicit metadata tags as a stand-in for attention statistics, routing tags, or retrieval-head scores. Whether such signals can be extracted cheaply and accurately from a running model remains unvalidated. If the promotion signal is noisy or delayed, the rescue pool may promote the wrong tokens or fail to promote critical ones.

3. **Pool sizing sensitivity and adversarial failure.** The severe degradation on `rescue_overflow` probes at $k_{\text{rescue}} = 8$ reveals that undersized pools or weak scoring can cause the rescue pool to fail on the exact cases it is designed to address. Pool sizing and candidate scoring must be calibrated to the target workload; no general sizing rule is established here.

4. **Probe design bias.** The synthetic probe families are constructed to isolate specific failure modes. Real-world long-context workloads may exhibit different distributions of bridge-token density, multi-hop chain length, and candidate overflow rates. The 0.812 aggregate accuracy is specific to the probe mix used and should not be generalized.

5. **No throughput or memory regression measured.** Because no real model was run, the memory and latency overhead of maintaining a rescue pool—index structures, promotion logic, attention mask modifications—is unquantified. The configured rescue-token budget specifies a token-count ceiling but not its realized cost in FLOPs or wall-clock time.

6. **Single budget point.** Results are reported at a single KV budget of 64 tokens. Sensitivity to budget size, sink size, and rescue-pool size ratio has not been systematically explored beyond the $k_{\text{rescue}} = 16$ overflow sweep.

7. **Claim audit status.** The structured claim ledger for this artifact was flagged as `blocked_empty_claims` at the time of draft generation, meaning no formal claims passed evidence audit. The numerical results reported here are drawn directly from the benchmark logs and decision record but have not undergone independent claim-level verification.

## Reproducibility Checklist

- [x] **Code available**: Simulator source at `src/rescue_pool_sim.py`; tests at `tests/test_rescue_pool_sim.py`; benchmark runner at `scripts/run_rescue_pool_benchmark.py`.
- [x] **Deterministic seed**: Seed 344 specified for all probe generation and benchmark execution.
- [x] **Full parameter specification**: KV budget 64, $k_{\text{sink}} = 4$, $k_{\text{rescue}} = 8$, 1,000 probes, 80 bootstrap trials.
- [x] **Raw output preserved**: Benchmark JSON (`results/rescue_pool_eval.json`), summary (`results/rescue_pool_summary.md`), probe data (`data/rescue_pool_probes.jsonl`), unit test log (`logs/unit_tests.log`), benchmark log (`logs/rescue_pool_benchmark.log`), telemetry (`logs/telemetry_smoke.log`).
- [x] **Unit tests passed**: 4 tests passed (see `logs/unit_tests.log`).
- [x] **Environment recorded**: Host posture GB10, swap disabled, `MemAvailable=116Gi`, GPU utilization 0%.
- [ ] **Real-model validation**: Not performed. This is a model-free synthetic study.
- [ ] **Attention signal extraction validated**: Not performed; promotion signal is synthetic metadata.
- [ ] **Claim audit passed**: Claim ledger is in `blocked_empty_claims` status; no structured claims have been verified against evidence.

## Conclusion

A bounded rescue pool added to the standard attention-sink plus recent-window KV-cache retention policy improved synthetic information-retention accuracy from 0.400 to 0.812 at KV budget 64 in a model-free simulator, with a bootstrap mean improvement delta of 0.412 (range 0.357–0.483). The rescue pool correctly preserved prefix-sink and tail-recency cases while recovering mid-context bridge and multi-hop probe accuracy—precisely the failure mode of fixed sink-plus-recent retention.

However, the rescue pool failed severely under adversarial candidate-overflow conditions (0.060 accuracy at $k_{\text{rescue}} = 8$), demonstrating that pool sizing and candidate scoring are critical design risks. Increasing pool capacity to 16 resolved the overflow in this generator, but the general sizing problem remains open and workload-dependent.

These findings are preliminary and confined to model-free synthetic evidence. They do not constitute proof that a rescue pool improves real transformer inference. The central unresolved question is whether a cheap, reliable online promotion signal can be extracted from a running model's attention patterns or head-level routing statistics. The recommended next step is to instrument a real llama.cpp or vLLM KV-cache retention path to promote tokens into a rescue pool based on such signals, then evaluate against long-context QA probes. A meaningful success criterion for that stage would be: the rescue pool recovers at least 50% of the sink-plus-recent misses on bridge/retrieval probes without material throughput or memory regression beyond the configured rescue-token budget.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Simulator source | `src/rescue_pool_sim.py` |
| Unit tests | `tests/test_rescue_pool_sim.py` |
| Benchmark runner | `scripts/run_rescue_pool_benchmark.py` |
| Benchmark results (JSON) | `results/rescue_pool_eval.json` |
| Benchmark summary | `results/rescue_pool_summary.md` |
| Probe data | `data/rescue_pool_probes.jsonl` |
| Unit test log | `logs/unit_tests.log` |
| Benchmark log | `logs/rescue_pool_benchmark.log` |
| Telemetry log | `logs/telemetry_smoke.log` |
| Project decision record | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260429T160518429119+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T160518429119+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T160518429119+0000/paper_manifest.json` |
