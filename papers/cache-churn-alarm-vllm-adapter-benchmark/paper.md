# Cache Churn Alarm: Reducing KV-Cache Preemption and Energy Cost via Latency-Triggered Request Gating in vLLM

> **AI Provenance Notice.** This draft was generated entirely by AI from automated research artifacts (run notes, evidence bundles, claim ledgers, benchmark results, and decision JSON). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate a client-side cache-churn-alarm policy that monitors request latency and, upon detecting a threshold crossing, suppresses optional speculative request branches to reduce KV-cache pressure on a serving endpoint. We evaluate this policy against a memory-blind baseline using a custom OpenAI-compatible benchmark harness across three experimental phases: a deterministic mock-endpoint smoke test, a real vLLM endpoint pilot under moderate load, and a pressure-specific vLLM pilot designed to saturate KV-cache capacity. Under pressure conditions with Qwen2.5-1.5B-Instruct served by vLLM 0.15.0rc2.dev51 (GPU memory utilization constrained to 0.045), the alarm policy eliminated all 12 optional speculative branches after a single alarm transition, reducing vLLM-reported preemptions from 2 to 0 (a 100% reduction in the observed churn signal) and improving estimated joules per correct request by 42.63%, while preserving required-request quality at 16/16. However, p95 latency showed no improvement and was marginally worse (−0.30%). Under non-pressure conditions, the alarm produced negligible benefits and an 8.40% throughput reduction. These results support the hypothesis that latency-triggered request gating can reduce KV-cache churn and energy cost under memory pressure, but they do not support a latency-improvement claim. All findings are limited to a single model, a single hardware configuration, and isolated A/B runs with imperfectly controlled initial KV state.

## 1. Introduction

Autoregressive language model serving systems such as vLLM manage a finite KV cache divided into blocks. When concurrent requests exceed available KV capacity, the scheduler preempts lower-priority requests, evicting their cached KV blocks and forcing recomputation upon resumption. This churn degrades throughput, increases latency variance, and wastes energy on redundant computation.

Server-side scheduling policies (e.g., vLLM's preemptive recomputation and swapping strategies) address this problem internally, but they operate after the admission decision has already been made. A complementary approach is client-side request gating: a client-side policy that monitors observable signals—such as request latency—and suppresses optional or speculative request branches when those signals indicate cache pressure. This approach requires no server modification and can be deployed against any OpenAI-compatible endpoint.

We define a **cache-churn-alarm** policy that:
1. Monitors p95 latency over a sliding window of recent requests.
2. Triggers an alarm state when observed latency exceeds a configured threshold.
3. While in alarm state, suppresses optional (speculative) request branches while allowing required requests to proceed.
4. Uses hysteresis to avoid rapid alarm toggling.

We evaluate this policy against a memory-blind baseline that issues all requests (required and optional) without gating. The evaluation proceeds through three phases of increasing fidelity: a mock-endpoint smoke test validating harness mechanics, a real vLLM endpoint pilot under moderate load, and a pressure-specific pilot designed to saturate KV capacity.

The central question is whether client-side latency-triggered gating can measurably reduce KV-cache churn, energy cost, or latency when serving against a real vLLM endpoint—without degrading the quality of required requests.

## 2. Method

### 2.1 Policy Definitions

**Memory-blind baseline.** All requests—both required and optional speculative branches—are issued without any gating or latency monitoring. This represents a client that does not adapt its behavior to server-side cache pressure.

**Cache-churn-alarm policy.** The client maintains a sliding window of recent request latencies. When the p95 latency within this window exceeds a configured threshold, the policy enters an alarm state. While in alarm state, optional speculative request branches are suppressed; only required requests proceed. A hysteresis mechanism prevents rapid state transitions. The policy exits alarm state when latency falls below the threshold minus a hysteresis margin.

### 2.2 Benchmark Harness

We implemented `benchmark_cache_churn_adapter.py`, a dependency-free Python benchmark harness targeting any OpenAI-compatible endpoint. The harness:

- Discovers the endpoint via `/v1/models`.
- Issues requests to `/v1/chat/completions` with configurable concurrency and repeat counts.
- Optionally scrapes Prometheus `/metrics` (with label-aware parsing for vLLM's labeled metric format) to capture server-side signals including `num_preemptions` as a churn proxy.
- Supports multiple workload types: standard (prefix-sharing, tool-pause, offload-pressure, speculation-like phases) and pressure (long-context prompts designed to saturate KV capacity).
- Records per-request latency, token counts, success/failure, and policy state.
- Captures system-level metrics: CPU load, process RSS/PSS where available, UMA memory (`MemAvailable + SwapFree`), and GPU utilization snapshots.
- Estimates joules per correct request from wall-clock time and GPU utilization.

Each policy is run against a freshly launched vLLM server instance to ensure independent KV-cache state.

### 2.3 Workload Design

The workload consists of two categories of requests:

- **Required requests**: Must succeed for the workload to be considered correct. These are never suppressed by either policy.
- **Optional speculative branches**: Additional requests that explore speculative paths (e.g., alternative prompt completions, tool-call probes). These are the targets of suppression under the alarm policy.

The **pressure workload** extends this design with long-unique context prompts calibrated to fill approximately 99.63% of the server's KV-cache token capacity (1,627 peak active prompt blocks at 16 tokens per block, totaling ~26,032 active prompt tokens against a server capacity of 26,128 KV tokens).

### 2.4 Acceptance Criteria

The branch-level success condition required at least one of the following without quality loss on required requests:

- ≥10% p95 latency reduction
- ≥10% joules-per-correct-request reduction
- ≥25% endpoint-observed cache-churn/eviction reduction

Quality loss is defined as any required request failing or producing an incorrect response.

## 3. Results

### 3.1 Phase 1: Mock-Endpoint Smoke Test

A deterministic mock OpenAI-compatible server (`mock_openai_cache_server.py`) was used to validate harness mechanics without a real serving backend. This phase confirms that the benchmark harness correctly implements both policies, records metrics, and suppresses optional requests when the alarm triggers. It does not constitute evidence about real server behavior.

| Metric | Memory-blind | Cache-churn-alarm |
|---|---|---|
| Required requests succeeded | 84/84 | 84/84 |
| Optional speculative requests sent | 21 | 0 (suppressed) |
| Quality (required) | 1.0 | 1.0 |
| p95 improvement | — | +0.36% |
| Joules/correct improvement | — | +6.19% |
| Cache eviction metric improvement | — | +0.04% |
| Alarm transitions | — | 1 |

The mock test confirmed functional correctness of the harness and policy logic. The small metric differences reflect the mock server's deterministic behavior and are not interpretable as real-server evidence.

### 3.2 Phase 2: Real vLLM Endpoint Pilot (Non-Pressure)

A real vLLM server (v0.15.0rc2.dev51, CUDA PyTorch cu130) served Qwen2.5-1.5B-Instruct with default memory settings. The workload used standard (non-pressure) phases.

| Metric | Memory-blind | Cache-churn-alarm |
|---|---|---|
| Required requests succeeded | 84/84 | 84/84 |
| Total requests sent | 105 | 96 |
| Optional branches suppressed | 0 | 9 |
| Quality (required) | 1.0 | 1.0 |
| p95 improvement | — | +0.21% |
| Joules/correct improvement | — | +0.67% |
| Tokens/sec change | — | −8.40% |
| vLLM preemptions observed | 0 | 0 |

Under non-pressure conditions, the alarm policy provided negligible benefit on latency and energy, while reducing throughput by 8.40% due to suppressed speculative branches that would have contributed to token output. The vLLM server reported zero preemptions under both policies, indicating that KV-cache pressure was not the binding constraint. This result does not meet any branch success criterion.

A notable confound: vLLM reported 26,080 KV tokens at memory-blind server startup and 15,888 KV tokens at alarm-policy server startup, reflecting imperfect control over initial KV state between isolated runs. This limits the strength of A/B comparison even for this non-pressure phase.

### 3.3 Phase 3: Pressure-Specific vLLM Pilot

To drive actual KV-cache pressure, the vLLM server was configured with constrained GPU memory:

- Model: Qwen/Qwen2.5-1.5B-Instruct
- `--gpu-memory-utilization 0.045`
- `--max-model-len 8192`
- `--max-num-seqs 16`
- `--max-num-batched-tokens 16384`

The pressure workload used long-unique context prompts calibrated to reach 1,627 peak active prompt blocks (~26,032 active prompt tokens), approximately 99.63% of the server's 26,128-token KV capacity. Each policy was run against a freshly launched vLLM instance.

| Metric | Memory-blind | Cache-churn-alarm |
|---|---|---|
| Required requests succeeded | 16/16 | 16/16 |
| Optional speculative branches sent | 12 | 0 (all suppressed) |
| Quality (required) | 1.0 | 1.0 |
| vLLM preemptions | 2 | 0 |
| Joules/correct improvement | — | +42.63% |
| Preemption/churn reduction | — | 100% |
| p95 latency change | — | −0.30% (slightly worse) |
| GPU utilization | 96% | 94% |
| Harness CPU load | <0.03% | <0.03% |

The alarm policy triggered once and suppressed all 12 optional speculative branches. Under memory-blind policy, vLLM reported 2 preemptions; under alarm policy, 0 preemptions were observed. Estimated joules per correct request improved by 42.63%, meeting the ≥10% threshold. The preemption signal reduction of 100% meets the ≥25% threshold. Required-request quality was preserved at 16/16 for both policies.

However, p95 latency did not improve and was marginally worse (−0.30%), failing to meet the ≥10% latency reduction criterion. GPU utilization decreased from 96% to 94%, consistent with reduced concurrent load from suppressed speculative branches.

### 3.4 Summary of Criteria

| Criterion | Threshold | Observed | Met? |
|---|---|---|---|
| p95 latency reduction | ≥10% | −0.30% (worse) | No |
| Joules/correct reduction | ≥10% | +42.63% | Yes |
| Preemption/churn reduction | ≥25% | +100% | Yes |
| Quality preserved | No loss | 16/16 both | Yes |

Two of three quantitative criteria were met without quality loss. The branch success condition (at least one criterion met) is therefore satisfied, though the absence of a latency improvement is a negative result that must be reported.

## 4. Limitations

1. **Single model and hardware configuration.** All real-endpoint results use Qwen2.5-1.5B-Instruct on a single GPU with constrained memory utilization. Generalization to larger models, multi-GPU configurations, or different architectures is not established.

2. **Imperfect A/B control.** The memory-blind and alarm-policy runs used separate vLLM server launches. The initial KV-cache state differed between runs (26,080 vs. 15,888 KV tokens at startup in the non-pressure pilot), introducing a confound. While the pressure pilot used isolated launches with consistent configuration, perfect state control was not achieved.

3. **No direct online KV-usage sampling.** The alarm policy relies on observed latency as a proxy for cache pressure. Direct measurement of KV-cache utilization (e.g., via vLLM internal metrics on active vs. total KV blocks) was not captured in real time. The relationship between latency spikes and KV pressure may be model- and workload-dependent.

4. **Small sample sizes.** The pressure pilot involved 16 required requests and 12 optional branches per policy. Statistical power to detect small effect sizes is limited.

5. **No multi-seed replication.** Each configuration was run once. Variance across random seeds, request ordering, and scheduling jitter has not been characterized.

6. **Throughput trade-off under non-pressure conditions.** The alarm policy reduced tokens/sec by 8.40% in the non-pressure pilot by suppressing speculative branches that would have contributed throughput. The policy's cost–benefit ratio depends on the proportion of optional requests and the baseline KV pressure.

7. **Energy estimation is indirect.** Joules per correct request is estimated from wall-clock time and GPU utilization snapshots, not from direct power measurement. This approximation may not capture dynamic voltage/frequency scaling or idle power accurately.

8. **Alarm threshold tuning.** The latency threshold and hysteresis parameters were set for this specific workload and server configuration. Sensitivity of the policy to these parameters has not been systematically explored.

9. **Preemption count as churn proxy.** vLLM's `num_preemptions` counter captures one aspect of cache churn. Other churn-related costs (e.g., recomputation overhead, cache block fragmentation) are not directly measured.

## 5. Reproducibility Checklist

- **Benchmark harness source**: `scripts/benchmark_cache_churn_adapter.py` (dependency-free Python, validated via `py_compile`)
- **Mock server source**: `scripts/mock_openai_cache_server.py`
- **vLLM version**: 0.15.0rc2.dev51 (CUDA PyTorch cu130)
- **Model**: Qwen/Qwen2.5-1.5B-Instruct (Hugging Face cache)
- **vLLM server configuration (pressure pilot)**: `--gpu-memory-utilization 0.045`, `--max-model-len 8192`, `--max-num-seqs 16`, `--max-num-batched-tokens 16384`
- **Server launch directory**: `/tmp/cache_churn_alarm_services`
- **Isolated A/B protocol**: Each policy run uses a fresh vLLM server launch; server is stopped and verified down between runs
- **Per-request results**: CSV files in `results/pressure_endpoint_pilot/final_ab_isolated/{memory_blind,cache_churn_alarm}/request_results.csv`
- **Server-side metrics**: Prometheus-format metric files (`memory_blind_final_metrics.prom`, `cache_churn_alarm_final_metrics.prom`)
- **Server logs**: `server_memory_blind.log`, `server_cache_churn_alarm.log`
- **Combined summary**: `results/pressure_endpoint_pilot/final_ab_isolated/combined_summary.json`
- **Server cleanup verification**: `server_stopped_check_memory_blind.txt`, `server_stopped_check_cache_churn_alarm.txt` (both confirm `server_down=True`)
- **Hardware**: Single GPU (model not specified in artifacts); UMA memory environment
- **Random seeds**: Not explicitly controlled in artifacts

## 6. Conclusion

We presented a client-side cache-churn-alarm policy that gates optional speculative requests when observed latency indicates KV-cache pressure on a vLLM serving endpoint. In a pressure-specific pilot with constrained GPU memory (utilization 0.045) and a workload designed to fill ~99.6% of KV capacity, the alarm policy eliminated vLLM preemptions (2 → 0), reduced estimated joules per correct request by 42.63%, and preserved required-request quality. These results meet two of three pre-registered acceptance criteria.

However, p95 latency did not improve and was marginally worse (−0.30%), and under non-pressure conditions the policy provided negligible benefit while reducing throughput by 8.40%. The alarm policy is therefore conditionally useful: it can reduce cache churn and energy cost when KV pressure is present, but it does not improve latency and imposes a throughput cost when pressure is absent.

These findings are limited to a single model, hardware configuration, and workload design, with imperfectly controlled initial KV state between A/B runs. Replication across additional models, hardware configurations, random seeds, and direct KV-usage sampling would strengthen the evidence. The current artifacts support the finding in the tested setting but do not establish universal applicability.

---

## Referenced Artifacts

### Project-local source files
- `scripts/benchmark_cache_churn_adapter.py`
- `scripts/mock_openai_cache_server.py`
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Result files (pressure pilot, final isolated A/B)
- `results/report.md`
- `results/pressure_endpoint_pilot/final_ab_isolated/combined_summary.json`
- `results/pressure_endpoint_pilot/final_ab_isolated/summary.md`
- `results/pressure_endpoint_pilot/final_ab_isolated/memory_blind/request_results.csv`
- `results/pressure_endpoint_pilot/final_ab_isolated/memory_blind/summary.json`
- `results/pressure_endpoint_pilot/final_ab_isolated/cache_churn_alarm/request_results.csv`
- `results/pressure_endpoint_pilot/final_ab_isolated/cache_churn_alarm/summary.json`
- `results/pressure_endpoint_pilot/final_ab_isolated/memory_blind_final_metrics.prom`
- `results/pressure_endpoint_pilot/final_ab_isolated/cache_churn_alarm_final_metrics.prom`
- `results/pressure_endpoint_pilot/final_ab_isolated/server_memory_blind.log`
- `results/pressure_endpoint_pilot/final_ab_isolated/server_cache_churn_alarm.log`
- `results/pressure_endpoint_pilot/final_ab_isolated/server_stopped_check_memory_blind.txt`
- `results/pressure_endpoint_pilot/final_ab_isolated/server_stopped_check_cache_churn_alarm.txt`
- `results/pressure_endpoint_pilot/final_ab_isolated/memory_blind_stdout.json`
- `results/pressure_endpoint_pilot/final_ab_isolated/cache_churn_alarm_stdout.json`
- `results/pressure_endpoint_pilot/final_ab_isolated/memory_blind_time.txt`
- `results/pressure_endpoint_pilot/final_ab_isolated/cache_churn_alarm_time.txt`
- `results/pressure_endpoint_pilot/final_ab_isolated/server_cache_churn_alarm.pid`
- `results/pressure_endpoint_pilot/final_ab_isolated/memory_blind/latest_summary.txt`
- `results/pressure_endpoint_pilot/final_ab_isolated/cache_churn_alarm/latest_summary.txt`

### Result files (non-pressure real endpoint pilot)
- `results/real_endpoint_pilot/` (probes, per-policy request CSVs, final Prometheus metrics, `combined_summary.json`, `summary.md`, `server_stopped_check.txt`)

### Result files (mock smoke test)
- `results/mock_pressure_reset_final/`

### Paper and audit artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/README.md`
