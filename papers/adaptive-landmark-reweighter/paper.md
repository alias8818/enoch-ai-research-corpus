# Adaptive Landmark Reweighter: Online KV-Cache Policy for Preserving Answer-Critical State Under Memory Constraints

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated the claims herein.

---

## Abstract

We investigate whether an online adaptive landmark reweighting policy can preserve answer-critical key-value (KV) cache state under tighter memory budgets than static landmark pinning. Rather than pinning block-level landmarks and high-salience spans once at prefill, the adaptive policy re-scores spans after each generated paragraph, boosting currently-needed spans and their block neighbors, decaying cold spans, and applying hysteresis-gated promote/quantize/evict/restore decisions. In a synthetic policy simulator that isolates cache-management mechanics from model behavior (80 tasks, 256 spans, 8 paragraphs, 24 critical spans per task, budget fractions 0.10–1.00), the adaptive policy achieves full critical-span recall (F1 proxy = 1.0) at budget fraction 0.10, whereas static pinning requires the full budget (1.0) for the same recall level. This corresponds to an 89.9% reduction in average KV footprint and a 65.2% reduction in proxy latency at zero measured quality loss in the matched-quality comparison. However, at tight budgets the adaptive policy incurs restore/eviction churn (mean 1.9 restores and 6.7 evictions per paragraph step at budget 0.10) and uses 0.5–2.0% more average KV than static pinning in same-budget comparisons due to restoration overhead. These results are synthetic proxy measurements from a toy simulation, not real LLM inference outcomes. We discuss the substantial gap between this policy-mechanism validation and production deployment, and outline the real-model experiments required for scientific closure.

## 1. Introduction

Long-context inference for transformer-based language models faces a growing tension between context window size and the memory cost of the KV cache. As context lengths extend to hundreds of thousands of tokens, the KV cache can dominate GPU memory, motivating compression strategies that retain the tokens most relevant to generation while evicting or degrading the rest.

Landmark attention mechanisms demonstrate that block-level landmark tokens can serve as selectors for relevant context while preserving random access to the full sequence. However, static landmark pinning—fixing which spans remain in fast memory based on prefill-time salience—cannot adapt to shifting generation-time information needs. A model answering a multi-hop question may need to revisit distant context that appeared unimportant during prefill.

Recent work supports the premise that model-derived importance signals at decode time can improve compression over static policies. SAGE-KV (2025) reports that post-prefill attention scores can guide KV eviction. KVMerger (2024) and SCOPE (ACL 2025) highlight the risk that static prefill-only policies can degrade long-context generation, arguing that decode-phase adaptive decisions matter. RocketKV (2025) achieves strong compression via two-stage sparse attention, but operates at the attention-kernel level rather than as a wrapper-level reweighter.

We hypothesize that an adaptive landmark reweighter—operating as a wrapper around the KV cache—can preserve answer-critical state under tighter memory budgets than simple static landmark pinning by re-scoring landmarks during generation and using the resulting signal to pin, quantize, offload, or restore cached spans. This paper reports a synthetic policy simulation that tests a necessary condition for this hypothesis: whether the online reweighting mechanism itself can maintain higher critical-span recall than static pinning under fixed memory budgets. We emphasize that this is a toy simulation validating policy mechanics, not a real-model inference experiment.

## 2. Method

### 2.1 Synthetic Policy Simulator

We implemented a synthetic cache-policy simulator (`scripts/adaptive_landmark_reweighter_eval.py`) that deliberately does not claim real LLM answer quality. The simulator isolates the cache-management mechanics from confounding factors (model architecture, attention patterns, tokenization) to test whether the policy logic itself can preserve critical spans. This is a toy simulation: it models span-level availability in a KV cache under memory budgets, using oracle knowledge of which spans are critical for each generation step.

### 2.2 Task Model

Each simulated task consists of a sequence of spans (default 256), organized into paragraphs (default 8), with a subset of spans marked as critical for each paragraph (default 24). The paragraph-critical spans represent an oracle-like proxy for the spans a model would need during generation of that paragraph. This is a controlled stand-in for online attention or retrieval signals; real attention may produce noisier importance estimates.

### 2.3 Policies

**Static Landmark Pinning.** Pins block landmarks and high prefill-salience spans once at initialization. No online restoration or reweighting occurs. Spans that are evicted or offloaded are permanently unavailable for the remainder of the task.

**Adaptive Landmark Reweighter.** Starts from the same salience-plus-landmark initialization. After each generated paragraph, the policy executes the following steps:

1. **Boost:** Increase the weight of spans needed by the current paragraph and their block neighbors.
2. **Decay:** Reduce the weight of cold spans (those not recently needed).
3. **Hysteresis:** Apply hysteresis gating to prevent oscillation between promote and evict decisions for the same span across consecutive steps.
4. **Promote/Restore:** Move needed spans from offloaded or quantized state back into resident FP16 KV.
5. **Quantize:** Reduce precision of cold spans (retaining them in degraded form rather than fully evicting).
6. **Evict/Offload:** Remove low-weight spans from resident memory to fit the budget, transferring them to offload storage.

### 2.4 Metrics

| Metric | Description |
|--------|-------------|
| `mean_f1_proxy` | Fraction of paragraph-critical spans available in resident or quantized KV. |
| `exact_task_success_rate` | Fraction of tasks where all paragraph needs are available across all paragraphs. |
| `avg_kv_mib` / `peak_kv_mib` | Proxy KV footprint assuming Llama-like FP16 KV bytes-per-token. |
| `avg_latency_ms_proxy` / `p95_latency_ms_proxy` | Crude latency proxy including resident scan, restore, offload, and reweight overhead. These are proxy constants, not measured GPU kernel timings. |
| Restore/eviction counts | Per-paragraph-step counts of restore and eviction operations, used to detect churn. |

### 2.5 Experimental Protocol

**Smoke test:** 4 tasks, 64 spans, 3 paragraphs, 8 critical spans, budget fraction 0.18.

**Budget sweep:** 80 tasks, 256 spans, 8 paragraphs, 24 critical spans per task, budget fractions {0.10, 0.14, 0.18, 0.22, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00}, seed 11.

**Verification:** Automated assertions confirmed that the matched-quality KV reduction exceeded 30% and quality loss was at most 2 points, and that the sweep summary contained at least 10 budget conditions.

## 3. Results

### 3.1 Matched-Quality Comparison

The primary comparison asks: at what budget does each policy achieve full critical-span recall (F1 proxy = 1.0)?

| Policy | Budget Fraction | Mean F1 Proxy | Avg KV (MiB) |
|--------|----------------|---------------|---------------|
| Static landmark pinning | 1.00 | 1.0 | 4812.1 |
| Adaptive reweighter | 0.10 | 1.0 | 484.4 |

The adaptive policy achieves the same recall at 89.9% lower average KV footprint. Proxy latency is 65.2% lower because the adaptive policy processes a smaller resident KV set overall. Quality loss at matched recall is 0.0 points.

### 3.2 Same-Budget Comparison

At every tested budget fraction, the adaptive policy achieves higher critical-span recall than static pinning. However, at very tight budgets (0.10–0.18), the adaptive policy uses approximately 0.5–2.0% more average KV than static pinning at the same nominal budget fraction, because it restores current paragraph spans into resident memory. This overhead is offset by substantial quality gains: 39.7–84.8 F1-proxy points depending on budget.

### 3.3 Restore/Eviction Churn

The adaptive policy's restoration mechanism introduces operational churn. At budget fraction 0.10, the policy averages 1.922 restores and 6.744 evictions per paragraph step. This churn represents a real implementation risk: in a production inference stack, each restore and eviction may require host-device memory transfers or page-table updates. The hysteresis mechanism in the current policy partially mitigates oscillation, but does not eliminate it. At higher budgets (≥0.30), churn decreases substantially as more spans remain resident.

### 3.4 Negative and Mixed Results

Several findings temper the positive headline results:

1. **Churn at tight budgets.** The 1.9 restores and 6.7 evictions per step at budget 0.10 would likely dominate real latency if each operation requires a device memory transfer. The current simulator models these as fixed-cost proxy operations, which understates the real cost.

2. **KV overhead at same budget.** The adaptive policy's restoration of needed spans causes it to exceed the nominal budget slightly at tight budgets, consuming 0.5–2.0% more average KV than static pinning at the same budget fraction. This is a deliberate trade-off (spending memory to gain recall), but it means the adaptive policy is not strictly budget-neutral.

3. **Oracle signal assumption.** The paragraph-critical span signal is an oracle proxy. Real attention-based importance signals will be noisier, potentially reducing the policy's effectiveness or increasing churn as the policy reacts to noisy salience fluctuations.

4. **No real-model quality signal.** The F1 proxy measures span availability, not answer correctness. A model may produce correct answers despite missing some "critical" spans, or incorrect answers despite having all critical spans available. The relationship between span availability and answer quality remains untested.

## 4. Limitations

This study validates policy mechanics in a synthetic toy simulation. The following limitations are substantive and should be considered when interpreting the results:

1. **Synthetic F1 proxy is not real LLM answer quality.** The simulator measures whether critical spans are available in the KV cache, not whether a model actually uses them correctly or produces correct answers. A real model may attend to different spans than the oracle assumes, or may be robust to the absence of some "critical" spans.

2. **Latency is a simple proxy, not measured GPU kernel time.** The latency numbers reflect assumed constant costs for scan, restore, offload, and reweight operations. Real GPU memory transfer costs, page-table management overhead, and kernel launch latency are not captured. The 65.2% latency reduction figure should not be cited as a real inference speedup.

3. **Oracle paragraph-need signal.** The policy uses a controlled stand-in for online attention or retrieval signals. In a real inference stack, the importance signal would come from attention scores or a learned predictor, introducing noise and potential systematic bias. The degree to which noise degrades the policy's advantage over static pinning is unknown.

4. **Restore/offload churn is visible and must be bounded.** The current results show non-trivial churn at tight budgets. A real implementation would need hysteresis tuning, batched restore/offload, and potentially admission control to prevent thrashing under adversarial workloads with rapidly changing citation patterns.

5. **No integration with paged KV layouts.** Production inference engines (vLLM, TensorRT-LLM) use paged KV caches with block-level allocation. The current simulator does not model page boundaries, block-level allocation conflicts, or the interaction between reweighting and paged memory management.

6. **No adversarial workload testing.** The synthetic tasks use a fixed number of critical spans per paragraph drawn from a controlled distribution. Workloads with rapidly shifting information needs (e.g., multi-hop reasoning that revisits distant context) may stress the policy differently and increase churn beyond what the sweep reveals.

7. **Single-seed sweep.** The budget sweep uses seed 11. While the task count (80) provides some statistical stability, results may be sensitive to the random span/paragraph generation. Multi-seed replication is recommended for any follow-up.

8. **Claim audit status.** The claim ledger for this artifact is currently empty (`audit_status: blocked_empty_claims`). No structured claims have been extracted or validated against the evidence bundle. The results reported here should be treated as preliminary prototype evidence pending formal claim audit.

## 5. Reproducibility Checklist

- **Simulator source:** `scripts/adaptive_landmark_reweighter_eval.py`
- **Smoke test command:** `python3 scripts/adaptive_landmark_reweighter_eval.py --tasks 4 --spans 64 --paragraphs 3 --critical 8 --budget-fraction 0.18 --out results/metrics/smoke_metrics.json --csv-out results/metrics/smoke_steps.csv`
- **Budget sweep command:** Iterated over budget fractions {0.10, 0.14, 0.18, 0.22, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00} with `--seed 11 --tasks 80 --spans 256 --paragraphs 8 --critical 24`
- **Verification script:** Inline Python asserting `kv_reduction_pct_vs_static_full > 30` and `quality_loss_points_vs_static_full <= 2` and sweep row count ≥ 10
- **Random seed:** 11 (budget sweep); smoke test used default seed
- **Dependencies:** None beyond Python standard library (NumPy install was attempted but not required; the simulator uses only standard library modules)
- **Hardware:** Execution environment logged in `results/logs/environment_telemetry.log`; no GPU required (synthetic simulation)
- **Result classification:** Toy simulation (synthetic policy proxy). Not llama.cpp hook-prototype, not CUDA copy calibration, not final production validation.
- **Output artifacts:** See Referenced Artifacts section

## 6. Conclusion

The synthetic policy simulation supports the core viability claim: online landmark reweighting can preserve answer-critical KV cache spans under much tighter memory budgets than static landmark pinning. At matched quality (F1 proxy = 1.0), the adaptive policy reduces average KV footprint by 89.9% and proxy latency by 65.2%. At every tested budget, adaptive reweighting achieves higher critical-span recall than static pinning.

However, these results constitute synthetic policy-mechanism evidence from a toy simulation only, not validation of real LLM inference quality. The positive findings are tempered by visible restore/eviction churn at tight budgets (1.9 restores and 6.7 evictions per paragraph step at budget 0.10), a slight KV overhead at same-budget comparisons (0.5–2.0% above nominal budget), and the fundamental limitation that paragraph-critical span signals are oracle-provided rather than model-derived. The latency numbers are proxy constants, not measured GPU timings. The claim ledger for this artifact is empty, meaning no structured claims have passed audit.

Scientific closure requires real-model validation. The recommended next experiment is to implement the adaptive reweighter as a wrapper over a small long-context model (e.g., via llama.cpp hooks, a vLLM paged-KV extension, or a PyTorch attention harness) and evaluate on citation-heavy QA, document extraction, and long-form summarization tasks (LongBench, Needle-in-a-Haystack, or equivalent). The policy should incorporate hysteresis and batched restore/offload to bound churn, and should be compared against both full KV, static landmark pinning, and attention-score dynamic baselines (SAGE-KV or SnapKV-style). Promotion of the idea beyond "promising" should be contingent on real-model quality loss remaining ≤2 points and restore/offload traffic not dominating latency.

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Simulator script | `scripts/adaptive_landmark_reweighter_eval.py` |
| Smoke test metrics | `results/metrics/smoke_metrics.json` |
| Smoke test step data | `results/metrics/smoke_steps.csv` |
| Budget sweep summary | `results/metrics/sweep_summary.csv` |
| Aggregate summary | `results/metrics/aggregate_summary.json` |
| Per-budget metrics | `results/metrics/metrics_budget_*.json` |
| Per-budget step data | `results/metrics/steps_budget_*.csv` |
| Smoke evaluation log | `results/logs/smoke_eval.log` |
| Sweep evaluation log | `results/logs/sweep_eval.log` |
| Environment telemetry | `results/logs/environment_telemetry.log` |
| Verification log | `results/logs/verification.log` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260429T204218384666+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T204218384666+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T204218384666+0000/paper_manifest.json` |
