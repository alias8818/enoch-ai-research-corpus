# Reasoning-Aware Quant Router Policy V2: Validator-Gated Quantization Escalation for Small Local Language Models

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, and benchmark results). The operator who released the artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We evaluate a reasoning-aware quantization routing policy (V2) for a locally-served Qwen2.5-3B-Instruct model across three GGUF quantization levels (Q3_K_M, Q4_K_M, Q8_0). The policy routes simple extraction tasks to Q3_K_M, applies a Q4_K_M floor for reasoning, control-policy, arithmetic, and structured-output tasks, and escalates to a Q8_0 retry when a deterministic validator rejects the first attempt on escalation-eligible tasks. On a 40-task deterministic benchmark, the V2 first-attempt policy achieves 30/40 accuracy (0.750) with 43.8% model-byte reduction and 23.6% wall-time reduction versus always-Q8, improving over the prior V1 exact-only router (27/40, 0.675). Adding validator-gated Q8 retry raises accuracy to 32/40 (0.800) and Q8-solvable preservation to 30/31 (0.968), but eliminates wall-time savings (−0.6% vs. always-Q8) while retaining 23.8% model-byte reduction. One Q8-solvable task (`v2_extract_path`) remains unrecovered because path extraction is not escalation-eligible under the current policy. Non-monotonic accuracy across quantization levels invalidates a monotone quality-ladder assumption for this model class. Results are mixed-positive: the reasoning-aware Q4 floor is supported as a genuine improvement, but validator-gated retry trades latency for quality and does not achieve full Q8-solvable preservation.

## 1. Introduction

Quantization reduces the memory and compute cost of local language model inference, but lower-precision representations can degrade output quality, particularly on tasks requiring multi-step reasoning, exact structured output, or control-policy decisions. A quantization router that assigns each prompt to the lowest sufficient precision level could preserve quality while minimizing resource consumption.

A prior experiment (V1) implemented an exact-only router that assigned simple and exact-format tasks to Q3_K_M and escalated structured-output tasks to Q4_K_M, with no retry mechanism. That router achieved 27/40 accuracy on a held-out benchmark but missed five tasks that Q8_0 could solve, including reasoning tasks (`reason_budget`, `reason_timebox`) where Q3_K_M failed but Q4_K_M and Q8_0 passed. This motivated a V2 policy with two changes: (1) a Q4_K_M floor for reasoning, control-policy, arithmetic, and structured-output tasks, and (2) validator-gated Q8_0 retry when a deterministic validator rejects the first attempt on escalation-eligible tasks.

This paper reports the V2 evaluation. We test the claim that a reasoning-aware quant router with a Q4 floor for reasoning/control/structured tasks plus validator-gated Q8 retries can improve over the prior exact-only Q3/Q4 router while reducing Q8 memory/runtime cost. We report both positive and negative evidence.

## 2. Method

### 2.1 Model and Quantization Ladder

The model is Qwen2.5-3B-Instruct, sourced from public Hugging Face safetensors (`Qwen/Qwen2.5-3B-Instruct`), converted locally to F16 GGUF, and quantized to three levels:

| Quantization | Model Size (bytes) | Model Size (GiB) | Median CUDA Self-Allocation |
|---|---:|---:|---:|
| Q3_K_M | 1,590,475,712 | ~1.48 | 1,615 MiB |
| Q4_K_M | 1,929,903,040 | ~1.80 | 1,938 MiB |
| Q8_0 | 3,285,476,288 | ~3.06 | 3,231 MiB |

All three GGUF files were validated and reused from a prior project via symlinks to ensure comparability across V1 and V2 evaluations.

### 2.2 V2 Routing Policy

The pre-registered V2 policy assigns quantization levels as follows:

- **Q3_K_M**: Simple extraction and non-reasoning normal prompts.
- **Q4_K_M floor**: Exact-format, structured-output, arithmetic/time, and control-policy reasoning prompts.
- **Q8_0 retry**: When a deterministic validator rejects the first attempt on an escalation-eligible task, the task is retried at Q8_0. Attempt-cost metrics count both calls (first attempt + retry if triggered).

The policy is deterministic: routing decisions depend only on task feature classification, not on runtime model output. Post-hoc empirical-min/oracle metrics are computed for diagnostic comparison only and were not used for routing decisions.

### 2.3 Benchmark Design

The benchmark consists of 40 deterministic tasks evaluated across all three quantization levels (120 llama.cpp invocations total). The task set includes:

- 24 held-out tasks from the prior V1 evaluation.
- 16 V2 stressor tasks focused on arithmetic/time, control-policy reasoning, exact structured output, path/PID/memory extraction, and routing-policy decisions.

Each invocation records: output text, strict regex pass/fail, wall time, prompt throughput, generation throughput, CPU load, child max RSS, `MemAvailable`, swap status, GPU utilization sample, and llama.cpp CUDA allocator telemetry.

### 2.4 Evaluation Metrics

- **Accuracy**: Strict regex pass count / 40.
- **Q8-solvable preservation**: Among the subset of tasks that Q8_0 passes (31 of 40), the fraction that the policy also passes (counting retries if applicable).
- **Model-byte reduction vs. Q8 attempt cost**: Fractional reduction in cumulative model bytes loaded across all attempts, relative to always-Q8.
- **Wall-time reduction vs. Q8 attempt cost**: Fractional reduction in cumulative wall time across all attempts, relative to always-Q8.

### 2.5 Hardware and Environment

- GPU: NVIDIA GB10
- System memory: ~116 GiB available at benchmark start; swap disabled (0 kB total)
- Inference engine: llama.cpp with CUDA backend
- System memory remained abundant throughout (minimum ~116 GiB available after inference), confirming the benchmark ran without memory pressure.

### 2.6 Baselines

Seven policies are compared:

1. **Always Q3_K_M**: Routes all tasks to Q3_K_M.
2. **Always Q4_K_M**: Routes all tasks to Q4_K_M.
3. **Always Q8_0 (control)**: Routes all tasks to Q8_0.
4. **V1 exact-only router (no retry)**: The prior policy routing simple/exact tasks to Q3_K_M and structured tasks to Q4_K_M.
5. **V2 first attempt**: The V2 reasoning-aware policy without retry.
6. **V2 + validator-gated Q8 retry**: The full V2 policy including retry.
7. **Empirical-min oracle (post-hoc)**: Diagnostic only; selects the lowest-quant pass for each task with hindsight. Not used for routing.

## 3. Results

### 3.1 Per-Quantization Accuracy

| Quantization | Passes | Accuracy | Median Wall Time | P95 Wall Time | Model Bytes | Median CUDA Self |
|---|---:|---:|---:|---:|---:|---:|
| Q3_K_M | 23/40 | 0.575 | 2.244 s | 2.335 s | 1,590,475,712 | 1,615 MiB |
| Q4_K_M | 29/40 | 0.725 | 2.381 s | 13.590 s | 1,929,903,040 | 1,938 MiB |
| Q8_0 | 31/40 | 0.775 | 3.330 s | 17.655 s | 3,285,476,288 | 3,231 MiB |

Q8_0 fails 9/40 tasks (`messy_issue_priority`, `messy_queue_decision`, `reason_two_constraints`, `workflow_error_class`, `v2_wall_clock`, `v2_policy_floor`, `v2_branch_decision`, `v2_quant_order`, `v2_exact_toml`), establishing it as an imperfect quality ceiling for this model and task set.

### 3.2 Policy Comparison

| Policy | Passes | Accuracy | Q8-Solvable Preserved | Model-Byte Reduction vs Q8 | Wall-Time Reduction vs Q8 |
|---|---:|---:|---:|---:|---:|
| Always Q3_K_M | 23/40 | 0.575 | 22/31 (0.710) | 51.6% | 48.7% |
| Always Q4_K_M | 29/40 | 0.725 | 28/31 (0.903) | 41.3% | 22.6% |
| V1 exact-only router | 27/40 | 0.675 | 26/31 (0.839) | 47.5% | 35.9% |
| V2 first attempt | 30/40 | 0.750 | 28/31 (0.903) | 43.8% | 23.6% |
| V2 + validator-gated Q8 retry | 32/40 | 0.800 | 30/31 (0.968) | 23.8% | −0.6% |
| Empirical-min oracle (post-hoc) | 33/40 | 0.825 | 31/31 (1.000) | 38.9% | 18.1% |

### 3.3 V2 First-Attempt Improvement over V1

The V2 reasoning-aware Q4 floor repairs the two motivating V1 failures: `reason_budget` and `reason_timebox`, both of which passed at Q4_K_M and Q8_0 but failed at Q3_K_M. Overall accuracy improves from 27/40 (V1) to 30/40 (V2 first attempt), and Q8-solvable preservation improves from 26/31 (0.839) to 28/31 (0.903), while retaining 43.8% model-byte reduction and 23.6% wall-time reduction versus always-Q8.

However, V2 first attempt still fails three tasks that Q8_0 passes: `workflow_route_model`, `v2_multi_step_fail`, and `v2_extract_path`. The first two are escalation-eligible and addressed by the retry mechanism; the third is not.

### 3.4 Validator-Gated Q8 Retry

The full V2 policy with retry escalates 8 tasks to Q8_0 after validator rejection: `workflow_error_class`, `workflow_route_model`, `v2_multi_step_fail`, `v2_wall_clock`, `v2_policy_floor`, `v2_branch_decision`, `v2_quant_order`, and `v2_exact_toml`. This raises overall accuracy to 32/40 (0.800) and Q8-solvable preservation to 30/31 (0.968). However, the retry overhead eliminates wall-time savings (−0.6% vs. always-Q8), though model-byte attempt cost remains 23.8% below always-Q8.

Notably, the full V2 retry policy achieves 32/40, exceeding the always-Q8 control (31/40). This occurs because some lower-quant passes succeed where Q8_0 fails, a consequence of non-monotonic quantization behavior (Section 3.6).

### 3.5 Remaining Q8-Solvable Failure

The V2 policy (with retry) still misses one Q8-solvable task: `v2_extract_path`. This path extraction task is routed to Q3_K_M because path/identifier extraction is not classified as escalation-eligible under the current policy. Q4_K_M and Q8_0 both pass this task, but Q3_K_M fails, and no retry is triggered because the task is not in the escalation-eligible set.

### 3.6 Non-Monotonic Quantization Behavior

Several tasks exhibit non-monotonic accuracy across quantization levels, violating the assumption that higher precision uniformly improves quality:

- `workflow_route_model`: passes at Q3_K_M and Q8_0, fails at Q4_K_M.
- `messy_queue_decision`: passes at Q3_K_M, fails at Q4_K_M and Q8_0.

This non-monotonicity means that any routing policy assuming a monotone quality ladder will misroute some tasks. The current V2 policy does not account for this phenomenon.

### 3.7 Throughput and Resource Observations

| Quantization | Median Prompt TPS | Median Gen TPS | Min MemAvailable After | Max GPU Util |
|---|---:|---:|---:|---:|
| Q3_K_M | 2,424.2 | 90.6 | ~116.3 GiB | 85% |
| Q4_K_M | 2,350.1 | 81.4 | ~117.1 GiB | 53% |
| Q8_0 | 1,848.3 | 58.6 | ~116.7 GiB | 80% |

System memory remained abundant throughout (minimum ~116 GiB available after inference), and swap remained disabled. These resource figures confirm the benchmark ran without memory pressure; the results reflect quantization quality effects, not resource contention.

## 4. Limitations

1. **Single small model.** All results are for Qwen2.5-3B-Instruct. Whether the V2 policy generalizes to larger models or different architectures is unknown.

2. **Small deterministic task set.** The 40-task benchmark, while expanded with 16 stressors beyond the prior 24, remains a small, deterministic evaluation. Strict regex matching may undercount partially correct outputs and does not capture open-ended generation quality.

3. **Q8 is an imperfect ceiling.** Q8_0 fails 9/40 tasks, so Q8-solvable preservation is a necessary but insufficient quality metric. A stronger model or different task-specific validators would be needed before production deployment claims.

4. **Non-monotonicity.** The observed non-monotonic accuracy across quantization levels means that any policy assuming a monotone quality ladder will misroute some tasks. The current policy does not account for this.

5. **Retry cost.** Validator-gated Q8 retry improves pass count but erases wall-time savings. In latency-sensitive deployments, this trade-off may be unacceptable. The current policy has no retry-cost budget.

6. **Incomplete escalation eligibility.** The `v2_extract_path` failure demonstrates that the current feature classification misses path/identifier extraction as an escalation-eligible category. Broadening eligibility or adding a retry budget could address this, but was not tested.

7. **Deterministic validators only.** The retry mechanism depends on deterministic validators that can reject incorrect outputs. Tasks without suitable validators cannot benefit from retry escalation.

8. **No open-ended generation evaluation.** All tasks use strict regex validation. The policy's behavior on open-ended, non-validatable generation tasks is untested.

9. **Single hardware configuration.** All results are from one NVIDIA GB10 system with abundant RAM. Results may differ under memory pressure or on different GPU architectures.

## 5. Reproducibility Checklist

- **Model provenance**: Public `Qwen/Qwen2.5-3B-Instruct` Hugging Face safetensors, converted locally to F16 GGUF, then quantized to Q3_K_M, Q4_K_M, Q8_0. GGUF files symlinked from prior validated project.
- **Inference engine**: llama.cpp with CUDA backend on NVIDIA GB10.
- **Benchmark script**: `scripts/reasoning_aware_quant_router_v2.py`
- **Smoke test**: Passed (3 tasks, confirming mechanism shape). Log: `logs/001_smoke.log`; results: `artifacts/results/router_v2_smoke_rows.csv`, `artifacts/results/router_v2_smoke_summary.json`.
- **Full benchmark**: 40 tasks × 3 quants = 120 invocations. Log: `logs/002_full_benchmark.log`; results: `artifacts/results/router_v2_full_rows.csv`, `artifacts/results/router_v2_full_summary.json`.
- **Post-hoc analysis**: Log: `logs/003_posthoc_summary.log`.
- **Environment capture**: `logs/000_environment.log`.
- **Routing policy**: Pre-registered in run notes before full benchmark execution. No policy parameters were tuned after observing full-benchmark results.
- **Validators**: Deterministic regex-based; validator logic is embedded in the benchmark script.
- **Randomness control**: Deterministic tasks with fixed prompts; llama.cpp sampling parameters not varied.
- **Data availability**: All result CSVs, summary JSONs, and logs are referenced in the project decision artifact.

## 6. Conclusion

The reasoning-aware Q4 floor in the V2 quantization router is supported as a genuine improvement over the prior V1 exact-only router. It repairs the motivating reasoning-task failures (`reason_budget`, `reason_timebox`), raises overall accuracy from 27/40 to 30/40, and improves Q8-solvable preservation from 26/31 (0.839) to 28/31 (0.903), all while retaining 43.8% model-byte reduction and 23.6% wall-time reduction versus always-Q8.

The validator-gated Q8 retry mechanism presents a mixed result. It further raises accuracy to 32/40 and Q8-solvable preservation to 30/31 (0.968), but the retry overhead eliminates wall-time savings (−0.6% vs. always-Q8), and one Q8-solvable task (`v2_extract_path`) remains unrecovered due to incomplete escalation eligibility. The non-monotonic accuracy behavior across quantization levels means that a simple monotone quality-ladder assumption is invalid for this model class, and routing policies must incorporate task-specific feature classification and validators rather than relying on precision as a proxy for quality.

The V2 policy is viable as a research mechanism but is not production-ready. Future work should: (1) broaden escalation eligibility to include path/identifier extraction tasks, (2) introduce retry-cost budgeting to preserve latency savings, (3) test on stronger local or OpenAI-compatible serving endpoints, and (4) evaluate on larger models and open-ended generation tasks where deterministic validators are unavailable.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Benchmark script | `scripts/reasoning_aware_quant_router_v2.py` |
| Environment log | `logs/000_environment.log` |
| Smoke test log | `logs/001_smoke.log` |
| Smoke test rows | `artifacts/results/router_v2_smoke_rows.csv` |
| Smoke test summary | `artifacts/results/router_v2_smoke_summary.json` |
| Full benchmark log | `logs/002_full_benchmark.log` |
| Full benchmark rows | `artifacts/results/router_v2_full_rows.csv` |
| Full benchmark summary | `artifacts/results/router_v2_full_summary.json` |
| Post-hoc summary log | `logs/003_posthoc_summary.log` |
| Claim ledger | `papers/source-record-redacted-20260501T152818507281+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T152818507281+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T152818507281+0000/paper_manifest.json` |
| Q3_K_M GGUF (symlink) | `artifacts/models/qwen2p5_3b_q3_k_m.gguf` |
| Q4_K_M GGUF (symlink) | `artifacts/models/qwen2p5_3b_q4_k_m.gguf` |
| Q8_0 GGUF (symlink) | `artifacts/models/qwen2p5_3b_q8_0.gguf` |
