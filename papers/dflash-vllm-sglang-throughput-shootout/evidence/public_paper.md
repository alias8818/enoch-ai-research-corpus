# DFlash Speculative Decoding in vLLM: Throughput and Quality on NVIDIA GB10

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We evaluate DFlash speculative decoding integrated into the vLLM serving framework on an NVIDIA GB10 GPU (SM121). Using Qwen3-4B as the target model and a DFlash-trained draft model (Qwen3-4B-DFlash-b16, 16 speculative tokens), we compare baseline autoregressive serving against DFlash-augmented serving across four prompt sets (chat, GSM8K, MATH-500, MBPP-local) at concurrency 4 with 256-token generation. DFlash achieves throughput speedups of 1.61× (chat), 3.04× (GSM8K), 4.17× (MATH-500), and 3.96× (MBPP-local) with zero measured quality degradation and zero request failures in both modes. A mini-matrix at concurrencies 1/4/8 with 128-token generation confirms the speedup across load levels, though the magnitude decreases with rising concurrency. SGLang evaluation was attempted but could not proceed due to SM121 kernel compatibility failures across three attention backends. Results are bounded to a single GPU, a single model pair, and modest sample sizes; the token acceptance rate observed from Prometheus counters (~21%) suggests headroom for further speedup with improved draft models. We report all negative findings and environmental constraints transparently.

## 1. Introduction

Speculative decoding accelerates autoregressive language model inference by using a smaller draft model to propose candidate token sequences that the target model verifies in parallel. When the draft model's proposals are accepted, multiple tokens are produced per forward pass without modifying the target model's output distribution. DFlash is a recently proposed speculative decoding method that trains draft models specifically for high acceptance rates using a distillation-style objective.

The practical impact of speculative decoding on serving throughput depends on the interaction between acceptance rate, batch composition, and the serving framework's scheduling logic. Published DFlash results focus on per-request latency; the effect on aggregate serving throughput under concurrent load is less well characterized. Additionally, new GPU architectures may expose kernel compatibility gaps that prevent evaluation entirely, as we document for SGLang on the NVIDIA GB10.

This report presents an evidence-grounded evaluation of DFlash speculative decoding in vLLM on the GB10, measuring both throughput and task quality under controlled A/B conditions. We treat SGLang as a documented negative result rather than an unexplored condition.

## 2. Method

### 2.1 Upstream Source

The DFlash implementation was cloned from the upstream repository (`https://github.com/z-lab/dflash`) at commit `6a13dfe956380821bb4e1a4f232b5d765ec17f7c`. Launch commands and model pairs were extracted from the upstream README and encoded into reproducible command artifacts.

### 2.2 Model Configuration

- **Target model**: Qwen/Qwen3-4B
- **Draft model**: z-lab/Qwen3-4B-DFlash-b16 (1.1 GB cached weights)
- **Speculative tokens**: 16
- **DFlash method**: `dflash` (as specified by the upstream `--speculative-config` interface)

Both baseline and DFlash runs use identical target model weights, attention backend (`flash_attn`), and `--max-num-batched-tokens 8192`. The only configuration difference is the addition of `--speculative-config {method:dflash, model:z-lab/Qwen3-4B-DFlash-b16, num_speculative_tokens:16}` for DFlash runs.

### 2.3 Serving Frameworks

- **vLLM**: Nightly build installed in an isolated `.venv-vllm` environment. The `datasets` dependency was upgraded from 2.14.4 to 4.8.4 to resolve a CLI import failure. The nightly CLI exposes `--speculative-config`, `--attention-backend`, and `--max-num-batched-tokens`.
- **SGLang**: Installed in an isolated `.venv-sglang` environment. SGLang's torch 2.9.1+cu129 warned that GB10 compute capability 12.1 exceeds the wheel's supported maximum of 12.0. Three attention backends were attempted; all failed (see Section 5.2).

### 2.4 Benchmark Harness

Two custom scripts were developed:

1. **`scripts/endpoint_benchmark.py`**: Sends requests to OpenAI-compatible endpoints, recording per-sample completion tokens/sec, p50/p95 latency, request failures, GPU utilization samples, and Prometheus metrics excerpts. The harness was hardened to record transport failures (e.g., server crash mid-request) as failed samples rather than aborting.

2. **`scripts/quality_endpoint_eval.py`**: Extends the benchmark harness with task-quality scoring. GSM8K and MATH-500 are scored via exact/numeric answer extraction. MBPP-local uses subprocess unit tests against a local function-test set (the HuggingFace MBPP loader hung in this environment; the local set serves as the durable code-quality gate). Chat prompts are scored on non-empty completion and stability checks.

### 2.5 Experimental Protocol

Servers were launched one at a time from a neutral working directory (`/tmp/dflash-vllm-services`) to avoid GPU memory conflicts. After each run, the server was stopped and GPU memory verified as released before launching the next configuration. No concurrent baseline/DFlash comparison was performed; each mode occupied the GPU exclusively.

**Mini-matrix** (smoke validation): 8 prompts per run, `max_new_tokens=128`, datasets `chat` and `gsm8k_smoke`, concurrencies 1, 4, 8. Both baseline and DFlash completed all 12 cells with 0 failed requests.

**Quality-scored matrix**: `max_new_tokens=256`, concurrency 4, datasets chat (n=32), GSM8K (n=64), MATH-500 (n=40), MBPP-local (n=24). Both baseline and DFlash completed all 4 cells with 0 failed requests.

## 3. Results

### 3.1 Mini-Matrix: Throughput vs. Concurrency

Table 1 reports completion tokens/sec and p95 latency across concurrencies 1, 4, and 8 for the smoke mini-matrix (128-token generation).

**Table 1.** vLLM mini-matrix results (Qwen3-4B, `flash_attn`, `max-num-batched-tokens=8192`, `max_new_tokens=128`, 8 prompts/run).

| Dataset | Concurrency | Baseline tok/s | DFlash tok/s | Speedup | Baseline p95 (s) | DFlash p95 (s) |
|---|---:|---:|---:|---:|---:|---:|
| chat | 1 | 21.55 | 47.39 | 2.20× | 5.91 | 2.86 |
| chat | 4 | 100.71 | 138.52 | 1.38× | 4.83 | 4.10 |
| chat | 8 | 193.79 | 248.49 | 1.28× | 4.99 | 3.90 |
| gsm8k_smoke | 1 | 21.71 | 138.36 | 6.37× | 5.92 | 1.18 |
| gsm8k_smoke | 4 | 87.71 | 369.03 | 4.21× | 5.05 | 1.40 |
| gsm8k_smoke | 8 | 175.77 | 536.61 | 3.05× | 4.99 | 1.61 |

DFlash throughput exceeds baseline in all 12 cells. The speedup magnitude is highest at concurrency 1 and decreases at higher concurrency, consistent with the expected interaction between speculative decoding and batch scheduling: under high batch load, the target model's forward pass is already amortized across more sequences, reducing the marginal benefit of speculative token proposals.

The GSM8K-smoke speedups (6.37× at c1, 3.05× at c8) are substantially larger than the chat speedups (2.20× at c1, 1.28× at c8). This likely reflects the shorter, more deterministic output distributions of math prompts, which increase the draft model's acceptance rate.

### 3.2 Quality-Scored Matrix: Throughput at Equal Quality

Table 2 reports the quality-scored evaluation at concurrency 4 with 256-token generation.

**Table 2.** vLLM quality-scored results (Qwen3-4B, `flash_attn`, `max-num-batched-tokens=8192`, `max_new_tokens=256`, concurrency 4).

| Dataset | n | Baseline quality | DFlash quality | Quality Δ | Baseline tok/s | DFlash tok/s | Speedup | Baseline p95 (s) | DFlash p95 (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| chat | 32 | 1.000 | 1.000 | 0.000 | 101.80 | 163.44 | 1.61× | 9.52 | 6.35 |
| GSM8K | 64 | 0.875 | 0.875 | 0.000 | 103.70 | 315.35 | 3.04× | 9.59 | 2.81 |
| MATH-500 | 40 | 0.250 | 0.250 | 0.000 | 101.03 | 420.90 | 4.17× | 9.68 | 3.54 |
| MBPP-local | 24 | 1.000 | 1.000 | 0.000 | 93.50 | 369.82 | 3.96× | 3.50 | 0.84 |

Quality scores are identical between baseline and DFlash across all four datasets. Both modes recorded zero request failures. The MATH-500 quality score of 0.250 for both modes indicates that Qwen3-4B struggles on this benchmark; the important observation is that DFlash does not degrade the already-low score.

### 3.3 Speculative Decoding Counters

vLLM exposes Prometheus counters for speculative decoding activity. During the quality-scored runs, the final DFlash chat summary recorded cumulative counters:

- `spec_decode_num_drafts_total` = 5,859
- `spec_decode_num_draft_tokens_total` = 93,744
- `spec_decode_num_accepted_tokens_total` = 19,921

The implied token acceptance rate is 19,921 / 93,744 ≈ 21.2%. This is consistent with active speculative decoding but indicates that the majority of draft tokens are rejected, suggesting headroom for improvement with better draft models. The average number of draft tokens per draft request is 93,744 / 5,859 ≈ 16.0, matching the configured `num_speculative_tokens=16`.

During the initial smoke test, the counters were `spec_decode_num_drafts_total=106`, `spec_decode_num_draft_tokens_total=1,696`, `spec_decode_num_accepted_tokens_total=151`, yielding a similar acceptance rate of ~8.9% on the smaller sample.

### 3.4 SGLang: Negative Result

SGLang evaluation was attempted on the same GB10 hardware. Three attention backend configurations were tested; all failed before any benchmark could be run:

| Backend | Error |
|---|---|
| `trtllm_mha` | "TRTLLM MHA backend for prefill is only supported on Blackwell GPUs (SM100)" |
| `fa4` | "RMSNorm failed with error code no kernel image is available for execution on the device" |
| `torch_native` + `--disable-piecewise-cuda-graph` | Server reached `/get_model_info` but crashed on first `/generate` with Triton/ptxas `sm_121a` unsupported |

These failures are attributable to the GB10's SM121 compute capability being newer than the kernel images shipped in the current SGLang/Triton wheel (which supports up to SM120). This is a tooling gap, not a fundamental limitation of DFlash or SGLang, but it prevents any SGLang-side throughput comparison on this hardware.

## 4. Limitations

1. **Single GPU, single model pair.** All results are from one NVIDIA GB10 GPU with one target/draft model pair (Qwen3-4B / Qwen3-4B-DFlash-b16). Generalization to other GPUs, model sizes, or draft-model configurations is not established.

2. **Modest sample sizes.** The quality-scored matrix uses n = 24–64 per dataset. These sizes are sufficient to detect large quality regressions but may not reveal small degradations. The chat quality metric (1.000 for both modes) measures only non-empty completion and stability, not semantic coherence.

3. **MBPP-local is not the full MBPP benchmark.** The HuggingFace MBPP loader hung in this environment, so a local 24-problem function-test set was used instead. Results on this subset may not reflect performance on the full MBPP suite.

4. **MATH-500 floor effect.** Both baseline and DFlash score 0.250 on MATH-500, indicating the model is near floor on this benchmark. Equal quality at floor does not rigorously demonstrate quality preservation; a model that performs well on MATH-500 would provide a more informative test.

5. **SGLang evaluation absent.** The SGLang serving stack could not be evaluated due to SM121 kernel incompatibility. The vLLM results should not be assumed to transfer to SGLang or other serving frameworks.

6. **No multi-GPU or distributed serving.** The evaluation is limited to single-GPU serving. Speculative decoding behavior under tensor or pipeline parallelism may differ.

7. **Token acceptance rate is moderate.** The observed ~21% acceptance rate means most draft tokens are rejected. Throughput gains are real but substantially below the theoretical maximum for a 16-token speculative window with high acceptance.

8. **No answer-correctness evaluation on full benchmarks.** The mini-matrix used smoke prompt sets without quality scoring. Only the quality-scored matrix evaluated correctness, and only on subsets.

9. **Operational fragility.** The first DFlash quality launch failed because a stray Python process from a prior probe retained GPU memory. An initial DFlash restart in the mini-matrix also failed for the same reason. These were resolved by killing orphans, but they indicate that GPU memory management in sequential benchmarking requires careful process hygiene.

10. **HuggingFace Xet download issue.** The initial draft model download via HuggingFace Xet produced a 0-byte `model.safetensors` file. The workaround (`HF_HUB_DISABLE_XET=1`) succeeded, but this is an environmental dependency.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Upstream source commit recorded | Yes: `6a13dfe956380821bb4e1a4f232b5d765ec17f7c` |
| Target and draft model identifiers specified | Yes: `Qwen/Qwen3-4B`, `z-lab/Qwen3-4B-DFlash-b16` |
| Serving framework version identified | Yes: vLLM nightly (isolated `.venv-vllm`); SGLang (isolated `.venv-sglang`, torch 2.9.1+cu129) |
| GPU hardware specified | Yes: NVIDIA GB10, compute capability 12.1 |
| All launch flags documented | Yes: `flash_attn`, `--max-num-batched-tokens 8192`, `--speculative-config` |
| Benchmark harness scripts available | Yes: `scripts/endpoint_benchmark.py`, `scripts/quality_endpoint_eval.py`, `scripts/run_vllm_minimatrix.sh`, `scripts/run_vllm_quality_matrix.sh` |
| Per-sample results recorded | Yes: `.samples.csv` and `.items.json` per run |
| GPU utilization recorded | Yes: `.gpu.csv` per run |
| Server logs captured | Yes: `logs/vllm_*_server_quality_*.log` |
| Prometheus metrics captured | Yes: in per-run `.summary.json` files |
| Failed requests recorded | Yes: 0 for all cells |
| Environment isolation verified | Yes: separate `.venv-vllm` and `.venv-sglang` |
| Random seeds specified | No: vLLM sampling randomness not controlled by fixed seed |
| Multiple random seeds tested | No: single run per cell |
| External replication performed | No |

## 6. Conclusion

DFlash speculative decoding in vLLM produces substantial throughput improvements on the NVIDIA GB10 with the Qwen3-4B / Qwen3-4B-DFlash-b16 model pair, ranging from 1.28× (chat, concurrency 8) to 6.37× (GSM8K-smoke, concurrency 1) in the mini-matrix and from 1.61× (chat) to 4.17× (MATH-500) in the quality-scored matrix at concurrency 4. No quality degradation was measured on any of the four evaluated prompt sets, and zero request failures occurred in both baseline and DFlash modes.

The speedup magnitude decreases with increasing concurrency, consistent with the expected diminishing returns of speculative decoding under batch saturation. The observed token acceptance rate of approximately 21% indicates that the current draft model's proposals are frequently rejected, leaving substantial headroom for improvement.

SGLang evaluation was blocked by SM121 kernel incompatibility across three attention backends. This is a tooling limitation rather than a methodological one, but it means the SGLang serving stack remains unevaluated on this hardware.

These results support the hypothesis that DFlash speculative decoding provides a practical throughput improvement in vLLM serving on the tested configuration. The evidence is bounded to a single GPU, a single model pair, and modest sample sizes; broader validation across hardware, models, and serving frameworks is needed before generalizing.

---

## Referenced Artifacts

### Run Notes and Decision Records
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `BENCHMARK_RUNBOOK.md`

### Benchmark Harness
- `scripts/endpoint_benchmark.py`
- `scripts/quality_endpoint_eval.py`
- `scripts/run_vllm_minimatrix.sh`
- `scripts/run_vllm_quality_matrix.sh`
- `scripts/dflash_server_commands.py`
- `scripts/setup_envs.sh`

### Quality-Scored Result Files
- `results/vllm_qwen3_4b_quality_comparison.json`
- `results/vllm_dflash_qwen3_4b_chat_quality_c4_mt256_n32.summary.json`
- `results/vllm_dflash_qwen3_4b_chat_quality_c4_mt256_n32.samples.csv`
- `results/vllm_dflash_qwen3_4b_chat_quality_c4_mt256_n32.items.json`
- `results/vllm_dflash_qwen3_4b_chat_quality_c4_mt256_n32.gpu.csv`
- `results/vllm_dflash_qwen3_4b_gsm8k_quality_c4_mt256_n64.summary.json`
- `results/vllm_dflash_qwen3_4b_gsm8k_quality_c4_mt256_n64.samples.csv`
- `results/vllm_dflash_qwen3_4b_gsm8k_quality_c4_mt256_n64.items.json`
- `results/vllm_dflash_qwen3_4b_gsm8k_quality_c4_mt256_n64.gpu.csv`
- `results/vllm_dflash_qwen3_4b_math500_quality_c4_mt256_n40.summary.json`
- `results/vllm_dflash_qwen3_4b_math500_quality_c4_mt256_n40.samples.csv`
- `results/vllm_dflash_qwen3_4b_math500_quality_c4_mt256_n40.items.json`
- `results/vllm_dflash_qwen3_4b_math500_quality_c4_mt256_n40.gpu.csv`
- `results/vllm_dflash_qwen3_4b_mbpp_quality_c4_mt256_n24.summary.json`
- `results/vllm_dflash_qwen3_4b_mbpp_quality_c4_mt256_n24.samples.csv`
- `results/vllm_dflash_qwen3_4b_mbpp_quality_c4_mt256_n24.items.json`
- `results/vllm_dflash_qwen3_4b_mbpp_quality_c4_mt256_n24.gpu.csv`

### Command and Model Artifacts
- `artifacts/vllm_dflash_commands_quality_20260413T190529Z.json`
- `artifacts/vllm_dflash_models_quality.json`
- `artifacts/vllm_dflash_models_quality.err`

### Smoke and Mini-Matrix Artifacts
- `results/vllm_baseline_qwen3_4b_smoke_c1.summary.json`
- `results/vllm_dflash_qwen3_4b_smoke_c1.summary.json`
- `results/vllm_qwen3_4b_minimatrix_comparison.json`
- `artifacts/vllm_baseline_models_smoke_20260413T180525Z.json`

### Download and Server Logs
- `logs/hf_download_dflash_qwen3_4b_20260413T181930Z.log`
- `logs/hf_download_dflash_qwen3_4b_noxet_20260413T182944Z.log`
- `logs/sglang_baseline_server_smoke_*.log`
- `logs/vllm_*_server_quality_*.log`

### Claim Ledger and Evidence Bundle
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
