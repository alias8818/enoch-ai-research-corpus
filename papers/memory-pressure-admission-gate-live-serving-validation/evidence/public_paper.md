# Memory Pressure Admission Gate: Live Serving Validation on a Local LLM Endpoint

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We evaluate a memory-pressure admission gate for OpenAI-compatible LLM serving endpoints. The gate compresses or defers low-value, context-heavy prompts when estimated prompt-pressure exceeds the available slot KV budget. In a live benchmark against a local llama.cpp server running Phi-4-mini-instruct (Q4_K_M GGUF) on an NVIDIA GB10 host, the gate reduced p95 request latency by 69.0% and energy proxy by 71.0% with zero completion loss relative to a throughput-only baseline. However, peak server RSS increased by 6.4%, indicating the gate does not reduce process-level memory and may slightly increase it due to compression overhead. Evidence strength is moderate: results come from a single server stack, a single quantized model, and a compact 16-request deterministic workload. Generalization to production serving stacks, larger models, and diverse workloads remains unvalidated.

## 1. Introduction

Autoregressive LLM serving under memory pressure faces a fundamental tension: long prompts consume disproportionate KV-cache capacity per slot, crowding out shorter but potentially higher-value requests. When all available context slots are occupied by long, low-value prompts, both tail latency and throughput degrade.

A memory-pressure admission gate addresses this by estimating per-request prompt pressure at admission time and selectively compressing or deferring requests that would disproportionately consume slot budget. Prior work in this project lineage evaluated this mechanism in a deterministic simulator and found positive results. The present study extends validation to a live OpenAI-compatible endpoint, measuring real request latencies, GPU power draw, and process-level memory under controlled paired workloads.

The central question is whether admission-time compression of low-value long prompts measurably improves serving efficiency on a real endpoint, and whether any such improvement comes at the cost of completion rate, response quality, or process-level memory.

## 2. Method

### 2.1 Admission Gate Design

The memory-pressure admission gate operates as a request-time proxy layer in front of an OpenAI-compatible endpoint. For each incoming request, the gate:

1. **Estimates prompt pressure** by computing the token-length footprint of the prompt relative to the per-slot context budget.
2. **Classifies request value** as high, medium, or low based on prompt metadata (length and content category).
3. **Applies compression** to low-value long prompts by truncating or summarizing the prompt to a shorter representation before forwarding it to the backend.
4. **Defers admission** when the aggregate estimated prompt pressure across active slots exceeds the available slot budget, queuing the request until pressure subsides.

The baseline condition (`throughput_only`) forwards all requests to the endpoint without modification, applying no compression or deferral.

### 2.2 Benchmark Harness

The benchmark harness (`src/live_memory_gate_bench.py`) is a stdlib-first Python script that:

- Constructs a deterministic 16-request mixed workload containing: (a) repeated-prefix prompts that benefit from cache reuse, (b) high-value medium-length prompts, and (c) low-value long prompts designed to pressure the KV budget.
- Executes the workload under both conditions (`throughput_only` and `memory_gate`) against the same endpoint in sequence.
- Records per-request latency (request latency and arrival-to-finish latency), completion status, response content, server RSS via `/proc` sampling, GPU power via `nvidia-smi` polling, and an energy proxy (mean GPU power × makespan).

### 2.3 Endpoint Configuration

The live endpoint was a llama.cpp `llama-server` instance with the following configuration:

| Parameter | Value |
|---|---|
| Model | Phi-4-mini-instruct Q4_K_M GGUF |
| Context window | 8192 tokens |
| Parallel slots | 4 |
| Per-slot context | 2048 tokens (`n_ctx_seq`) |
| CUDA KV buffer per slot | 544 MiB |
| Cache reuse threshold | 256 |
| Endpoint | `http://127.0.0.1:8011` |

The host was `gx10-efe8` with an NVIDIA GB10 GPU. The llama-server was started specifically for this benchmark and stopped afterward; no persistent serving infrastructure was used.

## 3. Results

### 3.1 Primary Metrics

| Metric | throughput_only | memory_gate | Delta |
|---|---:|---:|---|
| Completed / total | 16 / 16 | 16 / 16 | no completion loss |
| p95 request latency | 2.3336 s | 0.7230 s | −69.0% |
| p95 arrival-to-finish latency | 2.9933 s | 0.9024 s | −69.9% |
| Mean latency | 1.9947 s | 0.6143 s | −69.2% |
| Makespan | 5.1677 s | 2.9305 s | −43.3% |
| Energy proxy | 319.07 J | 92.70 J | −71.0% |
| Mean GPU power | 64.82 W | 34.32 W | −47.1% |
| Peak server RSS | 1257.30 MiB | 1337.33 MiB | +6.4% |
| Compressed requests | 0 | 8 | gate action |

All 16 requests completed under both conditions. The gate compressed 8 of 16 requests (the low-value long prompts), which is the expected gate behavior given the workload composition.

### 3.2 Latency and Energy

The gate produced substantial improvements in latency and energy metrics. The 69% reduction in p95 request latency and 71% reduction in energy proxy both exceed the pre-specified 10% improvement threshold for the branch kill condition. Mean GPU power dropped by 47%, consistent with fewer long-prompt tokens requiring KV allocation and attention computation.

### 3.3 Process-Level Memory

Peak server RSS increased by 6.4% under the gate condition. This is a negative result. The likely explanation is that process-level RSS captures the full server memory footprint—including model weights, runtime overhead, and prompt cache allocations—rather than isolating per-request KV pressure. The gate's compression step introduces additional intermediate prompt representations that may briefly increase allocation before the shorter prompts are dispatched. The core mechanism validated here is admission-time compression of low-value long prompts to reduce per-slot KV budget consumption, not reduction of the static model memory footprint.

## 4. Limitations

1. **Single model and quantization.** All results are from Phi-4-mini-instruct at Q4_K_M quantization. Larger models, different architectures, and full-precision serving may exhibit different KV pressure dynamics and compression trade-offs.

2. **Single serving stack.** Only llama.cpp was tested. vLLM, SGLang, TensorRT-LLM, and other production serving frameworks have different KV cache management strategies (e.g., PagedAttention) that may change the gate's cost-benefit profile.

3. **Compact deterministic workload.** The 16-request workload is small and deterministic. It was designed to exercise the gate's compression path but does not represent the distribution of request lengths, inter-arrival times, or content diversity seen in production traffic.

4. **No response quality evaluation.** Completion rate was preserved (16/16), but no automated quality metric (e.g., semantic similarity, task accuracy) was applied to the compressed-request responses. Compression may degrade output quality for some tasks, and this trade-off is not quantified here.

5. **Process-level RSS is a coarse memory metric.** The 6.4% RSS increase does not directly measure per-slot KV consumption. A finer-grained metric (e.g., per-slot KV utilization from llama.cpp's `--slots` metrics) would better isolate the gate's effect on memory pressure.

6. **No statistical replication.** Each condition was run once. Variance in latency, power, and RSS under repeated runs is not characterized.

7. **Local endpoint only.** The benchmark ran against a local llama-server on a single GPU. Network latency, multi-GPU serving, and distributed serving topologies are not represented.

8. **Compression strategy is simple.** The gate's compression was truncation-based. More sophisticated compression (e.g., prompt summarization via a smaller model, semantic compression) may yield different quality–efficiency trade-offs.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Model identifier and source | Phi-4-mini-instruct Q4_K_M GGUF, lmstudio-community distribution, local cache at `[redacted-local-model-cache]/` |
| Server binary and version | llama.cpp `llama-server`, build at `llama-server` |
| Server launch command | `llama-server -c 8192 -np 4 --metrics --slots --cache-reuse 256` |
| Benchmark harness | `src/live_memory_gate_bench.py`, stdlib-first, no external dependencies beyond `openai` client |
| Benchmark command | `python3 src/live_memory_gate_bench.py --base-url http://127.0.0.1:8011 --port 8011 --outdir results/live_llama_cpp_ctx8192` |
| Hardware | Host `gx10-efe8`, NVIDIA GB10 GPU |
| Workload | Deterministic 16-request mixed workload (repeated-prefix, high-value medium, low-value long) |
| Result artifacts | `results/live_llama_cpp_ctx8192/summary.json`, `results/live_llama_cpp_ctx8192/throughput_only_responses.json`, `results/live_llama_cpp_ctx8192/memory_gate_responses.json` |
| Log artifacts | `logs/live_bench_ctx8192_20260417_101546.log` |
| Random seeds | Workload is deterministic; no stochastic sampling in the benchmark harness |
| Number of runs per condition | 1 (no replication) |

## 6. Conclusion

A memory-pressure admission gate that compresses low-value long prompts before they occupy scarce KV-cache slots produced substantial latency and energy improvements on a local llama.cpp endpoint serving Phi-4-mini-instruct. The p95 request latency improved by 69% and the energy proxy by 71%, with no completion loss. However, peak server RSS increased by 6.4%, indicating that the gate does not reduce process-level memory and may slightly increase it. The validated mechanism is admission-time prompt compression to reduce per-slot KV budget consumption, not static memory footprint reduction.

These results are from a single model, a single serving stack, and a compact deterministic workload. The evidence supports the hypothesis that memory-pressure admission gating can improve serving efficiency in the tested setting, but the evidence strength is moderate and generalization to production deployments is not established. The project decision recommends using these validation artifacts to decide whether to productize an OpenAI-compatible memory-gate proxy, with the caveat that this follow-up is not guaranteed to succeed.

## Referenced Artifacts

### Result files
- `results/live_llama_cpp_ctx8192/summary.json`
- `results/live_llama_cpp_ctx8192/memory_gate_responses.json`
- `results/live_llama_cpp_ctx8192/throughput_only_responses.json`
- `results/live_llama_cpp/summary.json`
- `results/live_llama_cpp/memory_gate_responses.json`
- `results/live_llama_cpp/throughput_only_responses.json`

### Source and log files
- `src/live_memory_gate_bench.py`
- `logs/live_bench_ctx8192_20260417_101546.log`
- `logs/live_bench_20260417_101458.log`

### Project metadata and decision files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`
- `run_notes.md`
- `prompts/initial.md`
- `prompts/resume.md`

### Paper audit files
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
