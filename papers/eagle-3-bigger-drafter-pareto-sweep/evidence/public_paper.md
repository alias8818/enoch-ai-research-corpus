# EAGLE-3 Speculative Decoding Draft-Depth Sweep on NVIDIA GB10 with Qwen3-8B

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, benchmark results, decision records). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We report a calibrated sweep of EAGLE-3 speculative decoding draft depths (K = 2, 4, 8 speculative tokens) on an NVIDIA GB10 system running Qwen3-8B with the public RedHatAI EAGLE-3 speculator via vLLM. In a single-batch, short-decode latency benchmark (prompt length 128, output length 64, batch size 1, 3 iterations per case), K = 8 produced the lowest average latency of 3.481 s (18.39 output tokens/s), a 1.30× speedup over the non-speculative baseline of 4.528 s (14.13 output tokens/s). K = 2 achieved 1.20× speedup. K = 4 achieved only 1.10× speedup, underperforming K = 2 despite higher draft depth, consistent with near-zero per-position acceptance rates at deeper draft positions. The result is positive but narrow: only one prompt length, one output length, batch size 1, and three measured iterations were tested, using synthetic benchmark prompts rather than application traces. The non-monotonic speedup across K values and the low acceptance rates at positions beyond the first two drafted tokens indicate that the optimal draft depth is workload-dependent and cannot be determined from this sweep alone.

---

## Introduction

Speculative decoding accelerates autoregressive language model inference by using a lightweight draft model to propose multiple candidate tokens, which the target model then verifies in a single forward pass. EAGLE-3 is a speculative decoding algorithm that employs a trained speculator head to propose K tokens (the draft depth), with the target model accepting or rejecting each position. The choice of K involves a trade-off: larger K offers greater potential speedup if acceptance rates are high, but incurs additional draft computation and wasted verification work when later positions are rejected.

The NVIDIA DGX Spark (GB10) platform documentation recommends experimenting with draft depth values while monitoring acceptance rates and throughput. The vLLM inference engine supports EAGLE-3 via pretrained speculator models, including `RedHatAI/Qwen3-8B-speculator.eagle3` for the `Qwen/Qwen3-8B` target model.

This study asks: does increasing the EAGLE-3 draft depth K improve the latency/throughput Pareto point on GB10 for Qwen3-8B? We conduct a small, calibrated sweep at K = 2, 4, and 8, measuring latency, throughput, and per-position acceptance rates under controlled conditions.

---

## Method

### System Configuration

All experiments ran on an NVIDIA GB10 system (aarch64) with driver version 580.159.03 and CUDA 13.0, inside the Docker image `nvcr.io/nvidia/vllm:26.03-py3` (vLLM 0.17.1+a03ca76a.nv26.03.46967107). The GPU had 121 GiB total memory with approximately 117 GiB initially available. System swap was intentionally disabled (SwapTotal: 0 kB), and earlyoom was active with a 4% memory threshold.

A Docker GPU access issue (missing `/usr/local/bin/nvidia-smi`) was resolved by creating a symlink to `/usr/bin/nvidia-smi` prior to benchmarking.

### Models

The target model `Qwen/Qwen3-8B` (16.40 GB) and the EAGLE-3 speculator `RedHatAI/Qwen3-8B-speculator.eagle3` (2.04 GB) were downloaded to local storage using a curl-based range-resume downloader. This approach was chosen after implicit Hugging Face downloads inside vLLM stalled and created root-owned cache locks.

### Benchmark Harness

Latency measurements used `vllm bench latency` with the following fixed parameters:

| Parameter | Value |
|---|---|
| dtype | bfloat16 |
| max model length | 1024 |
| GPU memory utilization | 0.80 |
| batch size | 1 |
| prompt length | 128 tokens |
| output length | 64 tokens |
| iterations | 3 |
| warmup iterations | 0 |

Memory and GPU telemetry (MemAvailable, GPU utilization, temperature, power) were recorded during each run via a shell-based telemetry script (`scripts/mem_telemetry.sh`).

### Experimental Cases

Four cases were measured:

1. **Baseline** (`sweep_base_o64`): No speculative decoding (K = 0).
2. **K = 2** (`sweep_eagle_k2_o64`): EAGLE-3 with `num_speculative_tokens = 2`.
3. **K = 4** (`sweep_eagle_k4_o64`): EAGLE-3 with `num_speculative_tokens = 4`.
4. **K = 8** (`sweep_eagle_k8_o64`): EAGLE-3 with `num_speculative_tokens = 8`.

### Smoke Tests

Prior to the sweep, two smoke tests at output length 8 confirmed that both baseline (0.589 s) and EAGLE-3 K = 4 (0.899 s) ran successfully. The EAGLE-3 smoke test was slower than baseline, as expected for very short generations where speculation overhead dominates useful work.

---

## Results

### Latency and Throughput

| Case | Draft tokens K | Avg latency (s) | Output tok/s | Speedup vs baseline | Mean accept length | Avg draft accept % |
|---|---:|---:|---:|---:|---:|---:|
| `sweep_base_o64` | 0 | 4.528 | 14.13 | 1.00× | — | — |
| `sweep_eagle_k2_o64` | 2 | 3.784 | 16.91 | 1.20× | 1.30 | 15.2% |
| `sweep_eagle_k4_o64` | 4 | 4.120 | 15.53 | 1.10× | 1.34 | 8.4% |
| `sweep_eagle_k8_o64` | 8 | 3.481 | 18.39 | 1.30× | 1.85 | 10.7% |

K = 8 achieved the best latency and throughput in this sweep, with a 1.30× speedup over baseline. K = 2 also improved over baseline at 1.20×. K = 4 improved over baseline at 1.10× but underperformed K = 2, yielding a non-monotonic relationship between draft depth and speedup.

### Per-Position Acceptance Rates

The per-position acceptance probabilities extracted from vLLM logs reveal why K = 4 underperformed:

- **K = 2:** Position acceptance rates 0.207, 0.096. Accepted 41 of 270 drafted tokens.
- **K = 4:** Position acceptance rates 0.205, 0.107, 0.016, 0.008. Accepted 41 of 488 drafted tokens.
- **K = 8:** Position acceptance rates 0.451, 0.304, 0.059, 0.020, 0.010, 0.010, 0.000, 0.000. Accepted 87 of 816 drafted tokens.

For K = 4, positions 3 and 4 had near-zero acceptance (0.016 and 0.008), meaning the draft model almost never correctly predicted beyond position 2, yet the overhead of generating and verifying those positions was still incurred. For K = 8, the first two positions showed substantially higher acceptance (0.451 and 0.304) than observed in the K = 2 and K = 4 runs. This discrepancy may reflect inter-run variance given the small sample size (3 iterations) rather than a genuine effect of K on acceptance rates. Positions 5–8 had negligible acceptance.

The mean acceptance length was 1.30 for K = 2, 1.34 for K = 4, and 1.85 for K = 8. The higher mean acceptance length at K = 8, combined with the higher first-position acceptance rate observed in that run, explains its stronger speedup despite the majority of deeper positions being rejected.

### Resource Utilization

GPU utilization reached 96% across all cases. Peak GPU power was 65.65 W (observed during the K = 8 sweep). Minimum host MemAvailable during EAGLE-3 runs was approximately 16.2 GiB, above the earlyoom 4% threshold (~4.8 GiB on a 121 GiB system) but leaving limited headroom for concurrent processes. No OOM or earlyoom events occurred. No swap was available or used.

---

## Limitations

This study has several significant limitations that prevent broad generalization of the results:

1. **Small sample size.** Only 3 measured iterations per case were collected, with 0 warmup iterations. The observed speedup differences, particularly between K = 2 and K = 8, may not be statistically robust. Confidence intervals were not computed.

2. **Narrow workload.** Only batch size 1, prompt length 128, and output length 64 were tested. Speculative decoding benefits vary substantially with output length (longer outputs amortize startup overhead) and batch size (speculation interacts with batching differently).

3. **Synthetic prompts.** The `vllm bench latency` command uses default/synthetic prompts rather than real application traces. Acceptance rates are known to be prompt-dependent.

4. **Non-monotonic speedup.** The K = 4 result underperforming K = 2 highlights that increasing draft depth does not monotonically improve speedup. The optimal K depends on the acceptance rate distribution, which varies by workload. This sweep does not identify the optimal K.

5. **Single hardware configuration.** Results are specific to the GB10 platform, its memory configuration, and the vLLM version tested. Different GPU architectures, memory budgets, or serving frameworks may yield different trade-offs.

6. **No serving throughput measurement.** Only single-request latency was measured. Multi-request serving throughput under speculative decoding was not evaluated.

7. **Inter-run variance in acceptance rates.** The first-position acceptance rate for K = 8 (0.451) was substantially higher than for K = 2 (0.207) and K = 4 (0.205), which may reflect run-to-run variance rather than a genuine effect of K on acceptance. With only 3 iterations, this cannot be distinguished from sampling noise.

8. **Calibration-level evidence only.** These results constitute a calibrated prototype sweep on a single system, not a production-validated deployment measurement. The benchmark configuration (0 warmup iterations, 3 measured iterations) is insufficient for deployment-grade claims.

---

## Reproducibility Checklist

- **Hardware:** NVIDIA GB10 (aarch64), driver 580.159.03, CUDA 13.0, 121 GiB GPU memory.
- **Software:** Docker image `nvcr.io/nvidia/vllm:26.03-py3` (vLLM 0.17.1+a03ca76a.nv26.03.46967107).
- **Models:** `Qwen/Qwen3-8B` (local snapshot at `models/Qwen3-8B/`), `RedHatAI/Qwen3-8B-speculator.eagle3` (local snapshot at `models/Qwen3-8B-speculator.eagle3/`).
- **Benchmark command:** `vllm bench latency` with dtype=bfloat16, max_model_len=1024, gpu_memory_utilization=0.80, batch_size=1, prompt_len=128, output_len=64, num_iters=3, warmup_iters=0.
- **EAGLE-3 parameter:** `num_speculative_tokens` set to 2, 4, or 8 per case.
- **System state:** Swap disabled (SwapTotal: 0 kB), earlyoom active at 4% threshold.
- **Random seeds:** Not explicitly set; vLLM default behavior used.
- **Telemetry:** Memory and GPU metrics recorded via `scripts/mem_telemetry.sh`.
- **Docker GPU fix:** Symlink `/usr/local/bin/nvidia-smi` → `/usr/bin/nvidia-smi` required before benchmarking.

---

## Conclusion

On the tested GB10/vLLM/Qwen3-8B configuration with the public RedHatAI EAGLE-3 speculator, increasing the draft depth to K = 8 produced the best measured latency in a short single-batch sweep: 3.481 s average latency for 64 output tokens, a 1.30× speedup over the 4.528 s non-speculative baseline. K = 2 also improved latency at 1.20× speedup. K = 4 achieved only 1.10× speedup, underperforming K = 2 due to near-zero acceptance at deeper draft positions that still incurred verification overhead.

These results establish that EAGLE-3 speculative decoding is viable on the GB10 platform with Qwen3-8B and that larger draft depths can yield meaningful speedups. However, the non-monotonic behavior at K = 4, the low acceptance rates beyond the first two positions, and the narrow experimental conditions (3 iterations, batch size 1, single prompt/output length, synthetic prompts) mean that the optimal K cannot be determined from this data alone. The results are sufficient to motivate further investigation—particularly sweeps around K = 6–10 with longer output lengths (128–256 tokens), more iterations (≥30 per case for statistical confidence), real application prompt traces, and multi-batch serving throughput—but should not be generalized to other workloads or hardware without additional measurement.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Summary metrics | `results/summary_metrics.json` |
| Environment probe log | `.omx/logs/environment_probe.log` |
| Docker GPU probe log | `.omx/logs/docker_gpu_probe_after_symlink.log` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260504T102518936744+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260504T102518936744+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260504T102518936744+0000/paper_manifest.json` |
| Baseline sweep stdout | `logs/sweep_base_o64.stdout.log` |
| K=2 sweep stdout | `logs/sweep_eagle_k2_o64.stdout.log` |
| K=4 sweep stdout | `logs/sweep_eagle_k4_o64.stdout.log` |
| K=8 sweep stdout | `logs/sweep_eagle_k8_o64.stdout.log` |
| Qwen3-8B model snapshot | `models/Qwen3-8B/` |
| EAGLE-3 speculator snapshot | `models/Qwen3-8B-speculator.eagle3/` |
| Curl snapshot downloader | `scripts/curl_snapshot_download.py` |
| Latency benchmark harness | `scripts/run_latency_case.sh` |
| Memory telemetry script | `scripts/mem_telemetry.sh` |
| Qwen3-8B download log | `logs/curl_download_Qwen3-8B.log` |
| Speculator download log | `logs/curl_download_Qwen3-8B-speculator.log` |
