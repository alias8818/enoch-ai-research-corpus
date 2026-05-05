# Retrieval-Landmark KV Pins: Protecting Answer-Critical KV-Cache Spans Under Tight Resident Budgets

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, benchmark outputs, claim ledger, evidence bundle). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

We investigate a KV-cache residency policy that pins cache spans around retrieval landmarks—retrieved passages, citations, and explicit references—to preserve answer-critical key-value state under tight memory budgets. In a deterministic trace-level simulation over synthetic single-hop and two-fact multi-hop retrieval contexts (32,768 tokens, 256 queries, 10 seeds), the retrieval-landmark pinning policy achieves modeled exact-match quality within 2 percentage points of full-KV residency at a 512-token budget (98.4% footprint reduction) when retriever recall is 0.99. However, quality degrades sharply as retrieval recall falls: at 0.80 recall, two-fact multi-hop exact match drops to 66.6%, and at 0.60 recall it falls to 40.0%. Recency-only eviction, by contrast, achieves only 5.6% single-hop and 0.4% multi-hop exact match at a 2,048-token budget. These results are trace-level only: they model whether answer-critical token spans remain resident, not whether a transformer actually attends to them correctly. We conclude that retrieval-landmark KV pinning is a conditionally viable admission policy whose quality ceiling is set by retriever recall and citation localization precision, and that real-model integration is required before drawing stronger conclusions.

## 1. Introduction

Autoregressive language models with long contexts face a growing tension between context length and KV-cache memory. A Llama-class model with 32 layers, 8 KV heads, head dimension 128, and fp16 key/value storage requires approximately 128 KiB per token; a full 32,768-token context occupies roughly 4,096 MiB of KV-cache memory. Serving systems must therefore evict or offload KV entries, and the eviction policy directly affects generation quality.

Prior work has explored several approaches. StreamingLLM demonstrates that retaining a small set of initial "attention-sink" tokens plus a recent window can maintain generation stability for streaming contexts, but mid-context factual retrieval degrades once the window passes beyond relevant spans. SnapKV proposes training-free KV compression by selecting important positions from prompt attention features, reporting generation speedups and memory efficiency gains. FIER argues that page-level KV retrieval can miss sparse important tokens and achieves full-KV-matching performance at 11% cache budget via fine-grained token retrieval. The RULER benchmark cautions that vanilla needle-in-haystack evaluations are superficial and advocates multi-hop and aggregation tasks. Active systems demand for pluggable KV eviction with protected token positions has also been documented in serving frameworks.

A common observation in retrieval-augmented generation (RAG) settings is that answer-critical tokens are not uniformly distributed: they cluster around retrieved passages, citations, and explicit references—what we term *retrieval landmarks*. If the serving system already knows which context spans were retrieved (because it performed the retrieval), this information can inform KV-cache residency decisions without additional model inference.

We propose and evaluate a simple policy: pin KV-cache spans around retrieval landmark centers, retain a small sink-token prefix for attention stability, and allocate the remaining budget to recent tokens. We test this policy in a deterministic trace-level simulation that models whether answer-critical spans remain resident under bounded KV budgets, without running a real language model. This is a necessary but insufficient validation step.

## 2. Method

### 2.1 Policy Design

The **retrieval-landmark pin** (RL-pin) policy divides the resident KV-cache budget into three segments:

1. **Sink prefix.** The first 16 tokens are always pinned, following the attention-sink observation from StreamingLLM.
2. **Landmark windows.** For each retrieval landmark center $c_i$, a symmetric window of tokens $[c_i - w, c_i + w]$ is pinned. The window half-width $w$ is set so that the total landmark budget fits within the allocation.
3. **Recent remainder.** Any remaining budget after sink and landmark allocations is used for the most recent tokens.

We compare five policies:

| Policy | Description |
|---|---|
| `full_kv` | All context tokens resident (quality upper bound) |
| `recency_only` | Last $B$ tokens only |
| `sink_recency` | First 16 sink tokens plus last $B - 16$ recent tokens |
| `retrieval_landmark_pins` | Sink + landmark windows + recent remainder |
| `oracle_landmark_pins` | Upper bound using true answer-fact positions instead of retriever-identified landmarks |

### 2.2 Trace-Level Simulation Harness

We implemented `scripts/kv_pin_sim.py`, a deterministic trace-level benchmark. The harness does **not** execute a language model; it tests whether answer-critical token spans would remain resident under each policy at a given budget.

**Context and query generation.** Synthetic contexts of 32,768 tokens are generated with embedded fact spans. Queries target either a single fact (single-hop) or two facts (two-fact multi-hop). Each configuration uses 256 queries and 10 random seeds.

**Retriever model.** Rather than running a real retriever, the simulation parameterizes retriever recall directly. At recall $r$, each ground-truth fact span is included in the retrieved set with independent probability $r$, and the landmark center is placed at the retrieved span's position. This isolates the effect of retrieval quality on the pinning policy.

**Quality metric.** The primary metric is *modeled exact match* (EM): the fraction of queries for which all answer-critical token spans are fully resident in the KV-cache under the given policy. This is a necessary condition for correct generation but not a sufficient one.

**Memory model.** We use a Llama-class proxy: 32 layers, 8 KV heads, head dimension 128, fp16 key/value storage, yielding 128 KiB/token. At 32,768 tokens, full KV occupies approximately 4,096 MiB. A 2,048-token budget corresponds to approximately 256 MiB (93.75% footprint reduction); a 512-token budget corresponds to approximately 64 MiB (98.4% footprint reduction).

### 2.3 Experimental Configuration

| Parameter | Value |
|---|---|
| Context length | 32,768 tokens |
| Query count | 256 per seed |
| Seeds | 10 |
| Retriever recall values | 0.60, 0.80, 0.95, 0.99 |
| Resident budgets tested | 512, 1,024, 2,048, 4,096 tokens |
| Facts per query | 1 (single-hop), 2 (multi-hop) |

## 3. Results

### 3.1 Single-Hop Retrieval at 2,048-Token Budget

At a 2,048-token resident budget (256 MiB, 93.75% footprint reduction):

| Retriever Recall | RL-pin EM | Recency-only EM | Loss vs Full KV | Gain vs Recency |
|---:|---:|---:|---:|---:|
| 0.60 | 62.0% | 5.6% | 38.0 pp | 56.3 pp |
| 0.80 | 82.0% | 5.6% | 18.0 pp | 76.3 pp |
| 0.95 | 95.4% | 5.6% | 4.6 pp | 89.8 pp |
| 0.99 | 99.1% | 5.6% | 0.9 pp | 93.4 pp |

Recency-only eviction performs poorly for mid-context facts, as expected: at a 2,048-token window in a 32,768-token context, most answer-critical spans have already been evicted. RL-pin substantially improves over recency-only at all recall levels, but the absolute quality depends critically on retriever recall.

### 3.2 Two-Fact Multi-Hop Retrieval at 2,048-Token Budget

| Retriever Recall | RL-pin EM | Recency-only EM | Loss vs Full KV | Gain vs Recency |
|---:|---:|---:|---:|---:|
| 0.60 | 40.0% | 0.4% | 60.0 pp | 39.7 pp |
| 0.80 | 66.6% | 0.4% | 33.4 pp | 66.2 pp |
| 0.95 | 90.7% | 0.4% | 9.3 pp | 90.4 pp |
| 0.99 | 98.2% | 0.4% | 1.8 pp | 97.8 pp |

Multi-hop retrieval is more sensitive to recall degradation because both facts must be successfully retrieved and pinned. At 0.80 recall, the probability that both facts in a two-fact query are retrieved is approximately $0.80^2 = 0.64$, which aligns closely with the observed 66.6% EM. At 0.95 recall, the joint probability is approximately $0.95^2 \approx 0.9025$, again consistent with the observed 90.7%. This near-multiplicative compounding suggests that the independent-failure retriever model used in the simulation is a reasonable approximation for this regime, though real retrievers with correlated failures may deviate.

### 3.3 Best-Case Results at 512-Token Budget

At the tightest budget tested (512 tokens, 64 MiB, 98.4% footprint reduction) with 0.99 retriever recall:

| Setting | RL-pin EM | Recency EM | Loss vs Full KV | Footprint Reduction |
|---|---:|---:|---:|---:|
| Single-hop | 99.0% | 1.1% | 0.98 pp | 98.4% |
| Two-hop | 98.1% | 0.0% | 1.91 pp | 98.4% |

Under near-perfect retrieval, the RL-pin policy achieves modeled quality within 2 percentage points of full KV at less than 2% of the resident footprint. These figures represent the best-case outcome under the trace model and should not be extrapolated to real-model performance.

### 3.4 Restore Churn

At 2,048 tokens and 0.99 recall, mean restored tokens per query were 247.8 (single-hop) and 304.2 (multi-hop). At 512 tokens and 0.99 recall, mean restored tokens per query were 252.5 (single-hop) and 312.1 (multi-hop). This indicates that landmark windows are not always resident between queries and must be restored from offloaded storage. A production implementation would require hysteresis, TTL, or admission control to prevent restore thrashing that could erase latency benefits. The simulation does not model the temporal pattern of restores (burst vs. steady), their interaction with batch scheduling, or the cost of cache-line invalidation.

### 3.5 Negative and Mixed Results

Several findings temper the positive signal:

1. **Quality is upper-bounded by retriever recall.** Below 0.95 recall, multi-hop EM falls below 91%, and below 0.80 it falls below 67%. The pinning policy cannot protect spans that the retriever fails to identify. This is the dominant failure mode.

2. **False-positive pins compete with recent context.** When the retriever returns irrelevant passages, their pinned windows consume budget that would otherwise serve recent tokens, potentially harming coherence on subsequent generation steps. The simulation does not quantify this effect.

3. **Recency-only is a weak baseline for this task.** The large gains over recency-only partly reflect the unsuitability of recency-only eviction for mid-context retrieval, not solely the strength of RL-pin. A more informative comparison would be against attention-based compression methods (e.g., SnapKV, FIER), which were not simulated.

4. **Trace-level EM does not measure generation quality.** A span being resident is necessary but not sufficient for correct model output. Attention patterns, F1, perplexity, and actual generation quality remain unmeasured. The gap between span residency and correct generation is unknown and may be substantial.

5. **Restore churn is nonzero even at high recall.** At 0.99 recall and 512 tokens, approximately 250–312 tokens must be restored per query on average. Without hysteresis or TTL mechanisms, this churn could negate the latency benefits of reduced resident KV.

## 4. Limitations

1. **No real model validation.** The entire evaluation is trace-level simulation. No transformer was executed; no actual attention scores, generation outputs, F1 scores, or perplexity measurements were collected. The relationship between span residency and generation quality is assumed but not demonstrated. This is the most significant limitation.

2. **Synthetic contexts only.** Contexts are procedurally generated with known fact positions. Real documents have more complex structure, ambiguous fact boundaries, and distractor passages that may confuse both the retriever and the model.

3. **Retriever is parameterized, not real.** Recall is set exogenously rather than measured from an actual retrieval system. Real retrievers may have correlated failures (e.g., systematic misses on certain query types) that the independent-failure model does not capture. The near-multiplicative compounding observed in multi-hop results is an artifact of this independence assumption.

4. **No latency or traffic measurement.** The simulation counts restored tokens but does not model the actual cost of KV-cache offload/restore in terms of CPU-UMA traffic, PCIe transfers, or decode latency impact. The restore-churn numbers are indicative but not directly translatable to wall-clock performance.

5. **Single model-class proxy.** The 128 KiB/token memory model reflects Llama-class architectures. Other architectures with different KV shapes (e.g., grouped-query attention with fewer KV heads, multi-query attention) may yield different trade-offs and different optimal budget allocations.

6. **No comparison to learned compression.** Methods such as SnapKV or FIER that select important KV positions based on attention features were not simulated. The `oracle_landmark_pins` policy provides an upper bound on position-aware pinning, but a direct comparison to attention-based compression under equivalent budgets would be more informative.

7. **Churn dynamics are not fully modeled.** The mean restore counts are reported, but the temporal pattern of restores (burst vs. steady), their interaction with batch scheduling, and the cost of cache-line invalidation are not captured.

8. **Claim audit is incomplete.** The claim ledger for this artifact contains no structured claims and its audit status is blocked. The findings presented here have not passed a formal claim-evidence audit.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Source code available | Yes: `scripts/kv_pin_sim.py` (deterministic, no GPU required) |
| Random seeds documented | Yes: 10 seeds per configuration; seeds control fact placement and query generation |
| Raw outputs archived | Yes: `results/full_singlehop/raw_metrics.csv`, `results/full_multihop/raw_metrics.csv` |
| Summary outputs archived | Yes: `results/full_singlehop/summary.json`, `results/full_singlehop/comparisons.json`, `results/full_multihop/summary.json`, `results/full_multihop/comparisons.json` |
| Run logs archived | Yes: `logs/smoke_singlehop_v2.log`, `logs/full_singlehop.log`, `logs/full_multihop.log` |
| System telemetry archived | Yes: `logs/gb10_telemetry_before.txt`, `logs/gb10_telemetry_after.txt` |
| Verification commands | `python3 -m py_compile scripts/kv_pin_sim.py`; `python3 -m json.tool .omx/project_decision.json`; JSON validation on comparison files |
| Execution environment | CPU-only trace simulation; swap disabled; ~117 GiB RAM available; GPU utilization 0% (no GPU used) |
| Determinism | Fully deterministic given same seeds and parameters; no stochastic model inference involved |
| External dependencies | None beyond Python standard library and `json.tool` |

## 6. Conclusion

Retrieval-landmark KV pinning is a conditionally viable KV-cache residency policy. In trace-level simulation, it achieves modeled exact-match quality within 2 percentage points of full-KV residency at 98.4% footprint reduction when retriever recall is 0.99. However, quality degrades sharply as retrieval recall decreases, particularly for multi-hop queries where joint recall compounds the failure probability. The policy is best understood as an admission/protection layer whose quality ceiling is set by the retriever, not as a standalone replacement for KV compression or retrieval methods.

These results are trace-level only and do not constitute scientific closure. The critical next steps are: (1) integration with a real KV-cache backend (e.g., vLLM BlockEvictionPolicy or HF DynamicCache) to measure actual generation quality, decode latency, and memory traffic; (2) evaluation on RULER and LongBench-style benchmarks with exact-match and F1 metrics; (3) comparison against attention-based compression methods (SnapKV, FIER) under equivalent budget constraints; and (4) addition of pin TTL/hysteresis mechanisms to evaluate whether restore churn can be reduced without quality loss. Until such integration is performed, the present findings should be treated as promising but preliminary evidence that retrieval landmarks can inform effective KV-cache residency decisions.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Simulation script | `scripts/kv_pin_sim.py` |
| Smoke test log | `logs/smoke_singlehop_v2.log` |
| Single-hop run log | `logs/full_singlehop.log` |
| Multi-hop run log | `logs/full_multihop.log` |
| Telemetry (before) | `logs/gb10_telemetry_before.txt` |
| Telemetry (after) | `logs/gb10_telemetry_after.txt` |
| Single-hop raw metrics | `results/full_singlehop/raw_metrics.csv` |
| Single-hop summary | `results/full_singlehop/summary.json` |
| Single-hop comparisons | `results/full_singlehop/comparisons.json` |
| Multi-hop raw metrics | `results/full_multihop/raw_metrics.csv` |
| Multi-hop summary | `results/full_multihop/summary.json` |
| Multi-hop comparisons | `results/full_multihop/comparisons.json` |
| Project decision JSON | `.omx/project_decision.json` |
| Project metrics JSON | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260428T232028476221+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260428T232028476221+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260428T232028476221+0000/paper_manifest.json` |
