# Guarded Shared-Prefix Batching for Local LLM Serving: A Single-Node llama.cpp Validation

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or experimental results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We evaluate a guarded shared-prefix batching strategy for local LLM inference serving, where an online guard decides whether incoming requests should wait briefly to co-batch with prefix-overlapping requests or proceed immediately under FIFO dispatch. The strategy is tested against a kill condition requiring at least 10% improvement in p95 latency, throughput, or energy proxy on prefix-heavy or mixed workloads, while correctly disabling shared waiting under low-sharing traffic. In a single-node llama.cpp local-server validation using SmolLM2-135M-Instruct and Qwen2.5-0.5B-Instruct (both Q4_K_M GGUF), prefix-heavy scenarios showed 55–56% p95 latency reduction and 27–44% throughput improvement; mixed scenarios showed 31–44% p95 reduction and 19–30% throughput improvement. The guard disabled shared waiting at request 0 for low-sharing traffic on both models. However, low-sharing Qwen2.5-0.5B exhibited an 8.68% p95 latency regression attributable to a cold-probe cost before the guard activated. Response quality was assessed only via hash and length checks, not semantic evaluation. Confidence in the hypothesis is medium, and evidence strength is moderate, bounded by small model sizes, short generation lengths, and limited request counts.

---

## 1. Introduction

Inference serving for large language models faces a tension between individual request latency and aggregate throughput. When multiple concurrent requests share long common prefixes—as is common in template-driven prompting, few-shot evaluation, or retrieval-augmented generation—the underlying KV cache can be reused across requests if the serving system detects the overlap and batches accordingly. Llama.cpp's `--slot-prompt-similarity` mechanism provides one such reuse path at the slot level.

However, aggressive shared-prefix batching introduces a risk: if the system waits to accumulate prefix-overlapping requests that never arrive, the waiting cost is borne by every request in the queue. A guarded approach—where an online monitor decides whether to enable or disable shared waiting based on observed prefix-sharing rates—offers a compromise. The guard should enable shared waiting when overlap is frequent and disable it promptly when traffic lacks sharing structure.

This paper reports results from a single-node local-server validation of such a guarded shared-prefix batching strategy, implemented as a dispatch layer over llama.cpp's `llama-server`. The validation was conducted against a pre-specified kill condition: the method must deliver at least 10% improvement in p95 latency, throughput, or energy proxy on prefix-heavy or mixed workloads, the guard must correctly disable shared waiting for low-sharing traffic, and response quality must not materially regress.

---

## 2. Method

### 2.1 Guarded Shared-Prefix Dispatch

The dispatch layer operates in two modes:

1. **Baseline FIFO**: Each request is forwarded to the server immediately upon arrival, with no waiting or batching coordination.
2. **Guarded shared-prefix**: An online guard monitors recent request prefix overlap. When the guard estimates that prefix sharing is sufficiently high, incoming requests wait briefly (configured at 35 ms) to co-batch with overlapping requests already in the queue. When the guard estimates low sharing, it disables the wait and falls back to FIFO behavior.

The guard's decision is per-request: it may disable shared waiting at any point during a scenario run. The transition point is recorded as the "guard disabled at" request index.

### 2.2 Server Configuration

The validation harness launches `llama-server` from a local llama.cpp build with the following flags:

- `--metrics`: Enables server-side metrics reporting.
- `--slots`: Enables multi-slot processing.
- `--slot-prompt-similarity 0.55`: Configures the prompt-cache similarity threshold so that overlapping prompts can reuse KV cache entries across slots.

This configuration exercises llama.cpp's real prompt/KV slot reuse path rather than simulating it externally.

### 2.3 Traffic Scenarios

Three deterministic traffic scenarios were generated:

- **prefix_heavy**: Requests share long common prefixes, maximizing KV cache reuse opportunities.
- **mixed**: Requests have partial prefix overlap, creating intermittent sharing opportunities.
- **low_sharing**: Requests have minimal or no prefix overlap, providing a negative control for the guard.

Each scenario consists of 12 requests with `max_tokens=10` per request. The shared-prefix wait parameter is 35 ms.

### 2.4 Metrics Collected

For each request, the harness records:

- End-to-end p50 and p95 latency (from request submission to response completion).
- Tokens per second (throughput).
- Wall time for the scenario.
- Guard state (enabled/disabled) and the request index at which the guard disabled shared waiting.
- Response hash and length (for non-degradation smoke checking).
- Process RSS/PSS from `/proc`.
- System memory availability from `/proc/meminfo` (`MemAvailable`).
- GPU utilization and power draw from `nvidia-smi` (utilization-only sample, not used as memory evidence).

### 2.5 Models

Two quantized GGUF models were used:

- **SmolLM2-135M-Instruct-Q4_K_M** (135M parameters, Q4_K_M quantization).
- **Qwen2.5-0.5B-Instruct-Q4_K_M** (0.5B parameters, Q4_K_M quantization).

Both were loaded from locally cached files via symlinks in the project directory.

---

## 3. Results

### 3.1 SmolLM2-135M-Instruct

| Scenario | p95 Improvement | Throughput Improvement | Wall Time Improvement | Guard Disabled At |
|---|---:|---:|---:|---:|
| prefix_heavy | 56.36% | 26.66% | 21.05% | never |
| mixed | 30.57% | 18.81% | 15.83% | request 1 |
| low_sharing | 4.94% | 2.83% | 2.75% | request 0 |

System memory (`MemAvailable`) moved from 121,702,156 kB to 121,580,032 kB during the run. Server RSS reached approximately 525 MB. GPU utilization was recorded at 19% with 13.85 W power draw (utilization-only sample).

### 3.2 Qwen2.5-0.5B-Instruct

| Scenario | p95 Improvement | Throughput Improvement | Wall Time Improvement | Guard Disabled At |
|---|---:|---:|---:|---:|
| prefix_heavy | 55.99% | 43.53% | 30.33% | never |
| mixed | 44.28% | 29.85% | 22.99% | request 1 |
| low_sharing | −8.68% | 2.68% | 2.61% | request 0 |

System memory (`MemAvailable`) moved from 121,179,360 kB to 121,142,148 kB. Server RSS reached approximately 628 MB.

### 3.3 Guard Behavior

The guard operated as intended in all six scenario–model combinations:

- **prefix_heavy**: The guard never disabled shared waiting, consistent with sustained high prefix overlap.
- **mixed**: The guard disabled shared waiting at request 1 on both models, reflecting the transition from initial overlap to lower-sharing traffic.
- **low_sharing**: The guard disabled shared waiting at request 0 on both models, immediately falling back to FIFO dispatch.

### 3.4 Prompt-Cache Activity

Server logs confirmed that llama.cpp's prompt-cache mechanism was active during the runs. Logged events included entries such as `found better prompt with f_keep = 0.964, sim = 1.000` and prompt evaluations of only 1 token for reused prompts, indicating successful KV cache reuse across overlapping requests.

### 3.5 Response Quality

All requests returned successfully with non-empty responses. Response lengths remained comparable between baseline and guarded runs. However, quality assessment was limited to hash agreement, length comparison, and non-empty checks. No semantic quality benchmark (e.g., accuracy on a downstream task, human evaluation, or automated quality scoring) was conducted.

### 3.6 Negative Result: Low-Sharing Qwen2.5-0.5B p95 Latency

The low-sharing scenario on Qwen2.5-0.5B showed an 8.68% p95 latency regression under the guarded dispatch compared to baseline FIFO. This regression is attributable to the cold-probe cost: the guard's initial shared-wait period was incurred before the guard disabled waiting at request 0. Because the scenario contains only 12 requests, the single cold-probe event weighted heavily on the p95 statistic. Throughput and wall time showed small improvements (2.68% and 2.61%, respectively), suggesting the regression is isolated to the tail latency distribution rather than representing a systematic throughput penalty.

---

## 4. Limitations

1. **Small model sizes.** The two models tested (135M and 0.5B parameters) are substantially smaller than production-scale models. KV cache reuse benefits may scale differently with larger context lengths and model sizes.

2. **Short generation lengths.** All requests used `max_tokens=10`, which limits the generation-phase contribution to total latency. In workloads with longer generations, the relative benefit of prefix reuse on prompt-evaluation time may be diluted.

3. **Limited request counts.** Each scenario consisted of only 12 requests. Statistical confidence in the reported improvements is correspondingly low, and the p95 metric in particular is sensitive to individual outlier requests.

4. **Single-node, single-hardware configuration.** All experiments ran on a single machine. GPU utilization was recorded at 19%, indicating the server was not compute-saturated. Results may differ under higher concurrency or different hardware.

5. **No semantic quality evaluation.** Response quality was checked only via hash, length, and non-empty assertions. It is possible that shared-prefix batching introduces subtle quality regressions (e.g., from KV cache state interactions) that would not be detected by these checks.

6. **Cold-probe latency regression.** The 8.68% p95 regression on low-sharing Qwen2.5-0.5B traffic demonstrates that the guard's initial shared-wait period imposes a latency cost before it can disable waiting. This cost is acceptable under the pre-specified kill condition (which required degradation only on prefix-heavy or mixed workloads), but it indicates that a production guard should default to no-wait mode and enable shared waiting only after accumulating passive evidence of prefix overlap.

7. **No energy measurement.** The kill condition included a joules/request proxy improvement criterion, but `nvidia-smi` power readings were recorded as utilization-only samples and were not integrated into a per-request energy metric. The energy criterion was therefore not directly evaluated.

8. **Calibration and smoke runs.** Additional calibration and smoke-test result directories were produced but are not analyzed in detail in this report. Their primary role was to verify server startup and harness correctness before the formal benchmark runs.

---

## 5. Reproducibility Checklist

| Item | Status | Notes |
|---|---|---|
| Code available | Present in project | `scripts/run_llama_validation.py`; `python3 -m py_compile` passed |
| Model files specified | Yes | SmolLM2-135M-Instruct-Q4_K_M.gguf, Qwen2.5-0.5B-Instruct-Q4_K_M.gguf (symlinks to cached files) |
| Server binary specified | Yes | `llama-server` |
| Server flags documented | Yes | `--metrics`, `--slots`, `--slot-prompt-similarity 0.55` |
| Scenario parameters documented | Yes | 12 requests/scenario, max_tokens=10, wait=35 ms |
| Raw result files preserved | Yes | See Referenced Artifacts |
| Server logs preserved | Yes | `llama_server.log` in each result directory |
| Decision artifact preserved | Yes | `.omx/project_decision.json` |
| Claim ledger preserved | Yes | `claim_ledger.json` |
| Evidence bundle preserved | Yes | `evidence_bundle.json` |
| Hardware fully specified | Partial | GPU model not explicitly recorded; `nvidia-smi` utilization/power captured |
| External replication | Not performed | Results are specific to the single-node configuration tested |

---

## 6. Conclusion

A guarded shared-prefix batching strategy was validated on a single-node llama.cpp server using two small quantized models. On prefix-heavy and mixed traffic, the strategy delivered substantial improvements: 31–56% p95 latency reduction and 19–44% throughput improvement, exceeding the pre-specified 10% bars. The online guard correctly disabled shared waiting for low-sharing traffic on both models. A cold-probe p95 latency regression of 8.68% was observed on low-sharing Qwen2.5-0.5B traffic, indicating that the guard should default to a no-wait cold-start policy in production deployments.

These results support the hypothesis that guarded shared-prefix batching can improve serving efficiency when prefix overlap is present, while protecting against unnecessary waiting costs when it is absent. However, the evidence is bounded by small model sizes, short generation lengths, limited request counts, and the absence of semantic quality evaluation. The project decision recommends integrating a guarded shared-prefix scheduler into a production server path with a no-wait cold-start guard and re-running a larger, quality-scored workload.

---

## Referenced Artifacts

### Run Notes and Decision
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`

### Validation Harness
- `scripts/run_llama_validation.py`

### Model Files
- `models/SmolLM2-135M-Instruct-Q4_K_M.gguf`
- `models/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf`

### Result Directories

**SmolLM2-135M:**
- `results/local_server_20260419/llama_server.log`
- `results/local_server_20260419/summary.csv`
- `results/local_server_20260419/validation_results.json`

**Qwen2.5-0.5B:**
- `results/local_server_qwen05_20260419/llama_server.log`
- `results/local_server_qwen05_20260419/summary.csv`
- `results/local_server_qwen05_20260419/validation_results.json`

**Calibration:**
- `results/local_server_calibration_20260419/llama_server.log`
- `results/local_server_calibration_20260419/summary.csv`
- `results/local_server_calibration_20260419/validation_results.json`

**Smoke Tests:**
- `results/local_server_smoke_20260419/llama_server.log`
- `results/local_server_smoke_20260419/summary.csv`
- `results/local_server_smoke_20260419/validation_results.json`
- `results/local_server_smoke2_20260419/llama_server.log`
- `results/local_server_smoke2_20260419/summary.csv`
- `results/local_server_smoke2_20260419/validation_results.json`

### Paper and Audit Artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`

### Prompt Files
- `prompts/initial.md`
- `prompts/resume.md`
