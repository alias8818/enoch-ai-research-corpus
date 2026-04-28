# CPU-Offload Stress Harness Real-Server Scaleup: Multi-Backend Latency and KV-Placement Evidence

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We present evidence from a multi-backend, real-server scale-up study of a CPU-offload stress replay harness across llama.cpp, vLLM, and SGLang serving backends. The study investigates two questions: (1) whether explicit KV-cache placement (GPU vs. CPU) produces measurable latency and throughput separation under calibrated replay, and (2) whether request stress metadata correlates with per-request latency more strongly than semantic similarity metadata. Across llama.cpp Qwen3-0.6B runs, GPU-KV offload yielded 2.26× throughput and 0.44× mean latency relative to CPU-KV no-offload, confirming that KV placement is a strong, reproducible server behavior separator. The stress-vs-similarity latency predictor signal was directionally positive in all completed backends but weak and inconsistent across sample sizes: a Phi-4-mini-instruct pilot at n=16 showed max stress-latency correlation of 0.821 vs. similarity-latency correlation of 0.711, but at n=48 the margin collapsed to 0.281 vs. 0.255. SGLang execution on the GB10 platform failed at both the Triton/ptxas compilation layer and the custom kernel layer, producing durable platform-incompatibility evidence rather than serving results. We report these mixed findings as-is and identify tokenizer-aware prompt fitting as a necessary precondition for reliable long-context replay.

---

## 1. Introduction

Inference serving backends for large language models expose a variety of configuration knobs that affect latency, throughput, and resource utilization. Among these, KV-cache placement—whether the key-value cache resides in GPU memory or is offloaded to CPU memory—represents a first-order control point with direct implications for serving capacity and request latency. Simultaneously, the question of whether per-request metadata (such as estimated computational stress or semantic similarity to a reference set) can predict observed latency has practical implications for request routing and admission control.

This study reports results from a real-server scale-up of a CPU-offload stress replay harness. The harness replays a fixed dataset of prompt examples against live inference endpoints under multiple request-ordering policies, recording per-request latency, throughput, token counts, and resource utilization. The work was conducted across three serving backends (llama.cpp, vLLM, SGLang) on a GB10 unified-memory platform, with explicit KV-placement comparisons on llama.cpp and a tokenizer-aware prompt-fitting mechanism to avoid context-overflow failures observed in early runs.

The project concluded with a `finalize_positive` decision and `mixed` hypothesis status: the KV-placement signal is strong and reproducible, while the stress-vs-similarity ranking-stability signal is directionally positive but too weak and inconsistent to support a decisive claim at the tested sample sizes.

---

## 2. Method

### 2.1 Stress Replay Harness

The replay harness (`src/cpu_offload_endpoint_replay.py`, `src/cpu_offload_stress_harness.py`) sends a fixed set of prompt examples from `data/cpu_offload_stress_examples.jsonl` to a live OpenAI-compatible inference endpoint. Each example is dispatched under multiple request-ordering policies (e.g., `stress_desc`, `similarity_desc`, and additional variants). The harness records per-request latency, completion token counts, reported prompt token counts, and server-reported metrics where available.

### 2.2 Tokenizer-Aware Prompt Fitting

Early runs using approximate (word-count-based) token estimation produced context-overflow failures when materialized prompts exceeded the server's token slot limit. A capacity probe with `--max-prompt-tokens 6144` on llama.cpp Qwen3-0.6B at 8192-token slots confirmed that only 2/32 requests per policy succeeded, because materialized Qwen chat prompts reached 10k–21k llama tokens.

To address this, the harness was extended with a `--token-budget-mode` parameter supporting three strategies:

- **`approx`**: Original word-count heuristic (preserved for backward compatibility).
- **`endpoint`**: Probes the server's `/tokenize` or `/v1/tokenize` endpoint with common payload shapes to obtain exact token counts, then applies binary-search prompt truncation to fit within the configured budget.
- **`hf`**: Uses an installed `transformers` tokenizer when available.

The endpoint-based fitting path was validated against a local fake OpenAI-compatible server (3/3 requests succeeded; reported prompt tokens tracked materialized counts). All subsequent scale-up runs used `endpoint` mode.

### 2.3 Resource Sampling

Resource snapshots (`resource_before.txt`, `resource_during.txt`, `resource_after.txt`) were captured for each run, including `/proc/meminfo` UMA memory, server process RSS/VSZ, elapsed time, CPU utilization, and GPU utilization/power/temperature where `nvidia-smi` returned data. Per GB10 policy, nvidia memory values are not used as capacity evidence.

### 2.4 Kill Condition

The branch defined an explicit kill condition: downgrade or terminate the stress harness if a calibrated replay across real servers showed (a) no stable stress-vs-similarity latency advantage and (b) no meaningful offload/KV configuration separation after completing at least one llama.cpp CPU-KV vs. GPU-KV comparison, one vLLM replay, and either a successful SGLang replay or a concrete SGLang platform failure.

---

## 3. Results

### 3.1 llama.cpp Qwen3-0.6B: KV-Placement Comparison

Two calibrated replay runs were performed with llama.cpp serving Qwen3-0.6B (f16 KV, flash attention enabled, `--ctx-size 16384 --parallel 2`, 8192-token slots, 48 examples × 4 policies):

| Configuration | Throughput (rps) | Total tok/s | Mean Latency (s) | p95 Latency (s) | Success Rate |
|---|---|---|---|---|---|
| CPU-KV (`--no-kv-offload`) | 0.624 | 4087.7 | 3.203 | 3.457 | 48/48 |
| GPU-KV (`--kv-offload --metrics`) | 1.410 | 9237.4 | 1.418 | 1.544 | 48/48 |

GPU-KV offload produced 2.26× throughput, 2.26× total tokens per second, and 0.44× mean latency relative to CPU-KV no-offload on the same calibrated replay. This confirms that explicit KV placement produces a strong, reproducible separation in server behavior at this context size and model scale.

### 3.2 llama.cpp Qwen3-0.6B: Capacity Probe

A separate run with `--max-prompt-tokens 6144` and approximate token estimation (n=32) resulted in only 2/32 requests per policy succeeding. Materialized Qwen chat prompts reached 10k–21k llama tokens, exceeding the 8192-token slot context. This failure motivated the tokenizer-aware fitting implementation.

### 3.3 vLLM Qwen3-4B

vLLM 0.19.1rc1 served Qwen3-4B from local HuggingFace cache with `--max-model-len 4096 --attention-backend flash_attn --gpu-memory-utilization 0.78 --max-num-batched-tokens 4096`, 24 examples × 4 policies, concurrency 4:

| Metric | Value |
|---|---|
| Throughput | 1.858 rps |
| Total tok/s | 5732.8 |
| Mean Latency | 2.142 s |
| p95 Latency | 2.227 s |
| Success Rate | 24/24 |
| Prefill KV tokens/policy | ~72,900 |

All requests succeeded. vLLM reported approximately 72.9k prefill KV computed tokens per policy.

### 3.4 SGLang Qwen3-4B: Platform Failure

**Initial attempt (SGLang 0.5.6.post2, default compilation):** The server started and `/v1/models` responded, but the first replay request killed the scheduler with a Triton/ptxas compilation failure:

```
ptxas fatal: Value 'sm_121a' is not defined for option 'gpu-name'
```

This is a concrete platform/toolchain incompatibility on the GB10 GPU architecture.

**Recovery attempt (non-Inductor/non-Triton fallback):** A second attempt disabled all Triton and Inductor paths (`TORCHDYNAMO_DISABLE=1`, `TORCHINDUCTOR_DISABLE=1`, `--attention-backend torch_native`, `--sampling-backend pytorch`, `--grammar-backend none`, `--disable-cuda-graph`, `--disable-piecewise-cuda-graph`, `--disable-overlap-schedule`, `--skip-server-warmup`). Server startup succeeded; `/v1/models` and `/tokenize` both responded. However, the first generation still killed the scheduler, now failing at the custom kernel layer:

```
RuntimeError: RMSNorm failed with error code no kernel image is available for execution on the device
```

This constitutes durable evidence that the installed SGLang custom kernel stack (sgl_kernel) lacks a GB10-compatible kernel image, even when all Triton/Inductor graph compilation is disabled. The SGLang backend is therefore excluded from the latency comparison on this platform.

### 3.5 llama.cpp Phi-4-mini-instruct Q4_K_M: Tokenizer-Aware Scale-Up

**Pilot (n=16):** Phi-4-mini-instruct (~2.49GB / 3.84B params), `--ctx-size 12288 --parallel 2` (6144-token slots), `--kv-offload`, endpoint tokenizer fitting, 16 examples × 3 policies, concurrency 2:

| Metric | Value |
|---|---|
| Throughput | 1.044 rps |
| Total tok/s | 3094.7 |
| Mean Latency | 1.913 s |
| p95 Latency | 2.945 s |
| Mean reported prompt tokens | 2941.3 |
| Mean target prompt tokens | 2981.8 |
| Token fit ratio | 0.986× |
| Max stress-latency correlation | 0.821 |
| Max similarity-latency correlation | 0.711 |

All 16/16 requests per policy succeeded. Endpoint tokenizer fitting avoided the earlier slot overflow.

**Full run (n=48):** Same configuration, 48 examples × 3 policies, concurrency 2, max completion 64:

| Metric | Value |
|---|---|
| Throughput | 0.391 rps |
| Total tok/s | 2355.5 |
| Mean Latency | 5.111 s |
| p95 Latency | 5.191 s |
| Mean reported prompt tokens | 5957.3 |
| Mean target prompt tokens | 5987.0 |
| Token fit ratio | 0.995× |
| Max stress-latency correlation | 0.281 |
| Max similarity-latency correlation | 0.255 |

All 48/48 requests per policy succeeded. Tokenizer fitting remained accurate near the 6144-token slot limit. Sampled GPU utilization during the run frequently reached ~90–96%, indicating the server was substantially loaded rather than underutilized.

### 3.6 Stress-vs-Similarity Signal Summary

Across all completed backends, the stress-vs-similarity latency correlation was directionally positive (stress correlation exceeded similarity correlation in at least one policy per backend), but the magnitude and consistency of this advantage varied substantially:

| Backend / Run | Max Stress-Latency ρ | Max Similarity-Latency ρ | Margin |
|---|---|---|---|
| llama.cpp CPU-KV (n=48) | 0.325 | 0.277 | +0.048 |
| llama.cpp GPU-KV (n=48) | 0.269 | 0.154 | +0.115 |
| vLLM (n=24) | 0.365 | 0.202 | +0.163 |
| Phi-4-mini pilot (n=16) | 0.821 | 0.711 | +0.110 |
| Phi-4-mini full (n=48) | 0.281 | 0.255 | +0.026 |

The n=16 pilot on Phi-4-mini showed the largest absolute correlations and a meaningful margin, but the n=48 replication on the same model showed substantially reduced correlations and a near-zero margin. Cluster latency separation became weak once prompts were clipped to fit context. The stress-vs-similarity ranking-stability hypothesis remains directionally supported but is not decisively confirmed at these sample sizes.

---

## 4. Limitations

1. **Sample size.** The largest completed replay was n=48. Correlation differences at this scale are fragile; the collapse from ρ=0.821 (n=16) to ρ=0.281 (n=48) on the same model and configuration illustrates the instability. No power analysis was performed to determine the sample size required for a decisive test.

2. **Single hardware platform.** All runs were conducted on a single GB10 unified-memory system. The SGLang failure is specific to this platform's GPU architecture (`sm_121a`). Results may not generalize to discrete-GPU systems or other architectures.

3. **Limited model diversity.** The study covered Qwen3-0.6B (f16), Qwen3-4B (vLLM, BF16), and Phi-4-mini-instruct (Q4_K_M GGUF). No large-scale model (≥7B active parameters) was tested due to wall-clock and memory constraints.

4. **Context clipping as a confound.** Tokenizer-aware fitting truncates prompts to fit within server context slots. This changes the input distribution relative to the original dataset, potentially weakening stress-metadata signals that depend on long-context effects. The capacity probe failure (2/32 success without fitting) shows that unclipped replay is infeasible at these context sizes, but clipping may attenuate the very signal under study.

5. **No SGLang latency data.** SGLang produced only platform-failure evidence on GB10. The stress-vs-similarity comparison is therefore limited to llama.cpp and vLLM backends.

6. **Correlation without significance testing.** Reported correlations are descriptive maxima across policies. No multiple-comparison correction or formal hypothesis test was applied. The directional consistency across backends is suggestive but not statistically rigorous.

7. **Automated artifact provenance.** This draft and all reported results were generated by an automated research pipeline. No independent human verification of the raw data, analysis code, or numerical results has been performed.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Source code available | `src/cpu_offload_endpoint_replay.py`, `src/cpu_offload_stress_harness.py` (compiled successfully via `py_compile`) |
| Dataset specified | `data/cpu_offload_stress_examples.jsonl` |
| Server configurations documented | All llama.cpp, vLLM, and SGLang launch commands recorded in run notes |
| Hardware specified | GB10 unified-memory system; GPU architecture `sm_121a` |
| Software versions recorded | llama.cpp (local build), vLLM 0.19.1rc1, SGLang 0.5.6.post2, torch 2.9.1+cu129, triton 3.5.1 |
| Per-request data captured | `endpoint_requests.csv` and `endpoint_summary.csv` in each result directory |
| Resource snapshots captured | `resource_before.txt`, `resource_during.txt`, `resource_after.txt` where applicable |
| Server logs retained | All server logs in `logs/` directory |
| Aggregate summaries available | `results/scaleup_summary.json`, `results/scaleup_summary.md` |
| Random seeds | Not controlled; dataset-order replay was used |
| External dependencies | Local HuggingFace model cache; local llama.cpp build; platform-specific CUDA/Triton stack |

---

## 6. Conclusion

This study provides two primary findings from real-server scale-up of a CPU-offload stress replay harness:

**Finding 1 (strong):** Explicit KV-cache placement produces a large, reproducible separation in serving behavior. On llama.cpp Qwen3-0.6B at 16k context, GPU-KV offload yielded 2.26× throughput and 0.44× mean latency relative to CPU-KV no-offload. This signal is robust across the tested configurations and constitutes the strongest positive result of the study.

**Finding 2 (mixed/weak):** Request stress metadata shows a directionally positive but inconsistent correlation advantage over semantic similarity metadata for predicting per-request latency. The advantage was present in all completed backends but collapsed from a meaningful margin at n=16 to a near-zero margin at n=48 on the same model. The hypothesis that stress metadata provides stable ranking information for latency prediction is not rejected but is not confirmed at the tested sample sizes.

**Platform finding:** SGLang 0.5.6.post2 is incompatible with the GB10 `sm_121a` GPU architecture at both the Triton/ptxas compilation layer and the custom kernel (sgl_kernel) layer, even with all Inductor/Triton graph compilation disabled. This is documented as a durable platform constraint rather than a setup deficiency.

**Methodological contribution:** Tokenizer-aware prompt fitting via endpoint `/tokenize` probing with binary-search truncation is a necessary precondition for reliable long-context replay. Without it, approximate token estimation produced context-overflow failure rates of 94% (2/32 success). With it, fit ratios of 0.986×–0.995× were achieved at slot-proximal prompt sizes.

The project decision is `finalize_positive` with `mixed` hypothesis status and `medium` confidence. The recommended next action is to evaluate separately whether (a) GB10 SGLang kernel compatibility and (b) larger multi-model statistical validation of the stress-vs-similarity hypothesis warrant dedicated follow-up projects.

---

## Referenced Artifacts

### Run notes and decisions
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Source code
- `src/cpu_offload_endpoint_replay.py`
- `src/cpu_offload_stress_harness.py`

### Dataset
- `data/cpu_offload_stress_examples.jsonl`

### Result directories
- `results/llama_cpp_qwen06b_ctx16k_cpu_kv_n48_fit8k/`
- `results/llama_cpp_qwen06b_ctx16k_gpu_kv_n48_fit8k/`
- `results/llama_cpp_qwen06b_ctx16k_cpu_kv_n32/`
- `results/vllm_qwen3_4b_len4096_n24/`
- `results/sglang_qwen3_4b_len4096_n24/`
- `results/sglang_qwen3_4b_len4096_noinductor_attempt/`
- `results/tokenizer_smoke/`
- `results/llama_cpp_phi4mini_q4_ctx12k_gpu_kv_n16_tokfit/`
- `results/llama_cpp_phi4mini_q4_ctx12k_gpu_kv_n48_tokfit/`

### Aggregate summaries
- `results/scaleup_summary.json`
- `results/scaleup_summary.md`

### Server logs
- `logs/llama_cpp_qwen06b_ctx16k_cpu_kv_server.log`
- `logs/llama_cpp_qwen06b_ctx16k_gpu_kv_server.log`
- `logs/vllm_qwen3_4b_port8122.log`
- `logs/sglang_qwen3_4b_port30011.log`
- `logs/sglang_qwen3_4b_port30012_noinductor.log`
- `logs/llama_cpp_phi4mini_q4_ctx12k_gpu_kv_port8024.log`
- `logs/llama_cpp_phi4mini_q4_ctx12k_gpu_kv_port8025.log`

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
