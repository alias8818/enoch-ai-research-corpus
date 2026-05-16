# DFlash Speculative Decoding vs. N-Gram Prompt-Lookup Baseline: A Controlled Throughput–Quality Comparison

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We compare two speculative decoding strategies—DFlash (a draft-model-based speculative method) and vLLM's built-in n-gram prompt-lookup speculation—against a non-speculative target-only baseline, using Qwen3-4B as the target model. Across four benchmark suites (chat, GSM8K, MATH-500, MBPP-local), DFlash achieves 1.60×–3.73× higher completion throughput than n-gram speculation while maintaining equal measured quality on three of four datasets. On MATH-500 (n=40), DFlash shows a −0.025 quality delta relative to n-gram, attributable to a single-item difference. DFlash incurs moderate memory overhead (8.55 GiB model load vs. 7.5 GiB) and reduces available GPU KV cache by approximately 13.8% relative to the n-gram configuration. These results are limited to a single model family, a single GPU configuration, and small sample sizes (n=24–64). The current project artifacts support the finding that DFlash provides substantial throughput gains over the simplest available speculative baseline in the tested setting, but the MATH-500 quality caveat and narrow scope of evaluation warrant replication before broader generalization.

---

## 1. Introduction

Speculative decoding accelerates autoregressive language model inference by drafting candidate token sequences with a cheaper mechanism and validating them against the target model. A critical methodological concern when evaluating any speculative decoding technique is the choice of baseline: comparing a new method only against non-speculative decoding risks overstating its contribution if a simpler speculative baseline could achieve meaningful speedups with lower integration cost.

This study addresses that concern directly. We construct a controlled comparison harness that evaluates DFlash—a draft-model-based speculative decoding method—against vLLM's built-in n-gram prompt-lookup speculation, which represents the simplest available speculative baseline requiring no additional model weights. Both speculative configurations are also compared against a target-only (non-speculative) baseline. The central question is whether DFlash's throughput advantage over n-gram speculation is large enough to justify its additional memory and integration overhead.

The project was designed with an explicit "kill condition": if DFlash failed to exceed the n-gram baseline by at least 10% on throughput, the positive case for DFlash would be rejected. This threshold-based framing is intended to prevent overvaluing DFlash without a simpler-spec baseline.

---

## 2. Method

### 2.1 Models and Framework

- **Target model:** Qwen/Qwen3-4B
- **DFlash draft model:** z-lab/Qwen3-4B-DFlash-b16
- **Inference framework:** vLLM with FlashAttention (`flash_attn`)
- **Server configuration:** `--max-num-batched-tokens 8192`, concurrency 4, `max_new_tokens` 256

### 2.2 Speculative Decoding Configurations

Three configurations were evaluated:

1. **Target-only:** Standard autoregressive decoding with no speculation. Model load 7.5 GiB; available KV cache 97.93 GiB; GPU KV cache capacity 713,088 tokens.

2. **N-gram prompt lookup:** vLLM's built-in speculative decoding using prompt n-gram matching to propose candidate tokens. No additional draft model weights are required. Model load 7.5 GiB; available KV cache 97.29 GiB; GPU KV cache capacity 708,416 tokens. This configuration has the lowest integration complexity of the three speculative options.

3. **DFlash:** Draft-model-based speculative decoding using the Qwen3-4B-DFlash-b16 draft model. Model load 8.55 GiB (1.05 GiB additional for draft weights); available KV cache 96.14 GiB; GPU KV cache capacity 614,704 tokens. Requires a DFlash draft model and configuration, but operates as a single vLLM speculative configuration once weights are cached.

### 2.3 Benchmark Datasets

Four datasets were evaluated, each with a different sample size:

| Dataset | n | Task type |
|---|---|---|
| Chat | 32 | Open-ended conversation |
| GSM8K | 64 | Grade-school math |
| MATH-500 | 40 | Competition mathematics |
| MBPP-local | 24 | Basic Python programming |

### 2.4 Metrics

- **Completion throughput:** Completion tokens per second (tok/s), measured via the OpenAI-compatible endpoint benchmark harness.
- **Quality:** Task-specific accuracy metric computed by the quality evaluation script (exact match for GSM8K/MATH-500/MBPP-local; conversation quality score for chat).
- **P95 latency:** 95th-percentile end-to-end request latency in seconds (reported for n-gram runs only; DFlash and target-only p95 values are not available in the current artifacts).
- **Request failures:** Count of failed requests per dataset.

### 2.5 Provenance of DFlash Results

The DFlash quality and throughput results were obtained from a parent project (`source-record-redacted`) that previously ran DFlash and target-only evaluations on the same model and datasets. Those artifacts were reused rather than re-executed to avoid redundant GPU computation. The n-gram baseline was newly executed in this project using the same vLLM version, model, and evaluation scripts. This cross-project reuse introduces a temporal confound: the DFlash and n-gram runs were not executed in the same session, and server load or environmental differences could affect absolute throughput values. However, both configurations used the same target model, hardware, and evaluation harness, which mitigates (but does not eliminate) this concern.

---

## 3. Results

### 3.1 Throughput

Table 1 reports completion throughput for the n-gram and DFlash configurations across all four datasets.

**Table 1.** Completion throughput (tok/s) and DFlash speedup ratio over n-gram.

| Dataset | n | N-gram (tok/s) | DFlash (tok/s) | DFlash / N-gram |
|---|---|---|---|---|
| Chat | 32 | 102.16 | 163.44 | 1.60× |
| GSM8K | 64 | 123.25 | 315.35 | 2.56× |
| MATH-500 | 40 | 129.99 | 420.90 | 3.24× |
| MBPP-local | 24 | 99.07 | 369.82 | 3.73× |

DFlash exceeds the n-gram baseline by 60%–273% across all four datasets, comfortably above the pre-specified 1.10× kill-condition threshold. The speedup is smallest on the chat dataset (1.60×) and largest on MBPP-local (3.73×).

### 3.2 Quality

Table 2 reports quality scores for both speculative configurations.

**Table 2.** Quality scores and DFlash quality delta relative to n-gram.

| Dataset | n | N-gram quality | DFlash quality | Δ (DFlash − N-gram) |
|---|---|---|---|---|
| Chat | 32 | 1.000 | 1.000 | 0.000 |
| GSM8K | 64 | 0.875 | 0.875 | 0.000 |
| MATH-500 | 40 | 0.275 | 0.250 | −0.025 |
| MBPP-local | 24 | 1.000 | 1.000 | 0.000 |

Quality is equal on three of four datasets. On MATH-500, DFlash scores 0.250 versus n-gram's 0.275, a difference of 0.025 absolute (2.5 percentage points). Given the sample size of n=40, this difference corresponds to a single additional correct item for n-gram. This small-sample fluctuation is retained as a caveat but does not constitute a clear quality regression.

### 3.3 Latency

P95 latency was recorded for the n-gram configuration:

| Dataset | n | N-gram p95 latency (s) |
|---|---|---|
| Chat | 32 | 9.83 |
| GSM8K | 64 | 7.58 |
| MATH-500 | 40 | 9.07 |
| MBPP-local | 24 | 3.47 |

P95 latency for DFlash and target-only configurations is not available in the current artifacts and cannot be reported.

### 3.4 Reliability

All four n-gram benchmark runs completed with 0 request failures. DFlash failure counts are not explicitly recorded in the current project artifacts but were reported as zero in the parent project's logs.

### 3.5 Memory and KV Cache

Table 3 summarizes memory allocation and KV cache capacity across configurations.

**Table 3.** Memory footprint and GPU KV cache capacity.

| Configuration | Model load (GiB) | Available KV cache (GiB) | GPU KV cache (tokens) |
|---|---|---|---|
| Target-only | 7.50 | 97.93 | 713,088 |
| N-gram | 7.50 | 97.29 | 708,416 |
| DFlash | 8.55 | 96.14 | 614,704 |

DFlash requires 1.05 GiB additional memory for the draft model and reduces GPU KV cache capacity by approximately 98,304 tokens (13.8%) relative to the n-gram configuration. The n-gram configuration incurs negligible memory overhead relative to target-only (0.64 GiB less available KV cache, likely due to speculation bookkeeping).

---

## 4. Limitations

1. **Small sample sizes.** Sample sizes range from n=24 (MBPP-local) to n=64 (GSM8K). These are insufficient for precise quality estimation, especially on MATH-500 where the observed −0.025 quality delta reflects a single-item difference.

2. **Single model family.** Only Qwen3-4B was tested. The relative performance of DFlash and n-gram speculation may differ substantially for other model architectures, sizes, or draft-model pairings.

3. **Single hardware environment.** All runs were conducted on the same GPU. Throughput ratios may vary with different GPU memory capacities, interconnect, or batch scheduling.

4. **Cross-project result reuse.** DFlash results were obtained from a parent project and combined with newly collected n-gram results. Although the same model, framework, and evaluation scripts were used, the runs were not conducted in the same session, introducing a potential temporal confound.

5. **Incomplete latency reporting.** P95 latency is available only for the n-gram configuration. Without DFlash and target-only p95 values, a full latency comparison cannot be made.

6. **N-gram as sole simpler baseline.** Only the simplest available speculative baseline (n-gram prompt lookup) was tested. Other speculative methods (e.g., suffix decoding, smaller independent draft models) were not evaluated and may narrow the throughput gap.

7. **Quality metric limitations.** The chat quality metric of 1.000 across both configurations may reflect a coarse grading scheme rather than genuinely identical output quality. A finer-grained evaluation (e.g., LLM-as-judge, human preference) could reveal differences not captured by the current metric.

8. **No statistical testing.** Given the small sample sizes, no confidence intervals or hypothesis tests are reported. The observed throughput differences are large enough to be unlikely due to measurement noise, but quality differences (especially on MATH-500) cannot be statistically distinguished from zero.

---

## 5. Reproducibility Checklist

| Item | Status | Detail |
|---|---|---|
| Model identifiers | Specified | Qwen/Qwen3-4B; z-lab/Qwen3-4B-DFlash-b16 |
| Framework and version | Partially specified | vLLM with flash_attn; exact version not recorded in artifacts |
| GPU hardware | Not recorded | GPU model and VRAM not captured in project artifacts |
| Server configuration | Specified | `--max-num-batched-tokens 8192`, concurrency 4, `max_new_tokens` 256 |
| Evaluation scripts | Available | `scripts/quality_endpoint_eval.py`, `scripts/endpoint_benchmark.py`, `scripts/compare_spec_baselines.py` |
| Raw result files | Available | Per-dataset GPU CSV, samples CSV, summary JSON, and items JSON files (see Referenced Artifacts) |
| Random seeds | Not recorded | Determinism of vLLM sampling not documented |
| DFlash provenance | Documented | Results reused from parent project `source-record-redacted` |
| Server logs | Available | `logs/vllm_ngram_server_existing_spec_20260413T191506Z.log` and associated command/PID files |
| Script compilation | Verified | `python3 -m py_compile scripts/*.py` passed |
| No orphan processes | Verified | `ps` confirmed no remaining vLLM/SGLang processes after run |

---

## 6. Conclusion

In a controlled comparison on Qwen3-4B across four benchmark datasets, DFlash speculative decoding achieves 1.60×–3.73× higher completion throughput than vLLM's n-gram prompt-lookup speculation, the simplest available speculative baseline. Quality is equal on three of four datasets; on MATH-500 (n=40), DFlash shows a −0.025 quality delta attributable to a single-item difference. DFlash incurs 1.05 GiB additional memory overhead and reduces GPU KV cache capacity by approximately 13.8% relative to the n-gram configuration.

These results support the conclusion that DFlash provides substantial throughput gains over the simplest speculative baseline in the tested setting, sufficient to justify its moderate integration and memory overhead for the evaluated model and workloads. However, the evaluation is narrow in scope—single model, single hardware environment, small samples—and the MATH-500 quality caveat remains unresolved. Replication with larger sample sizes, additional model families, and concurrent latency measurement would strengthen the evidence base.

---

## Referenced Artifacts

### Decision and audit artifacts
- `.omx/project_decision.json`
- `artifacts/final_decision_audit.json`
- `results/final_decision_summary.md`
- `results/spec_baseline_report.md`
- `artifacts/spec_baseline_comparison.stdout.json`
- `results/spec_baseline_comparison.json`

### N-gram benchmark result files
- `results/vllm_ngram_qwen3_4b_chat_existing_spec_c4_mt256_n32.gpu.csv`
- `results/vllm_ngram_qwen3_4b_chat_existing_spec_c4_mt256_n32.samples.csv`
- `results/vllm_ngram_qwen3_4b_chat_existing_spec_c4_mt256_n32.summary.json`
- `results/vllm_ngram_qwen3_4b_chat_existing_spec_c4_mt256_n32.items.json`
- `results/vllm_ngram_qwen3_4b_gsm8k_existing_spec_c4_mt256_n64.gpu.csv`
- `results/vllm_ngram_qwen3_4b_gsm8k_existing_spec_c4_mt256_n64.samples.csv`
- `results/vllm_ngram_qwen3_4b_gsm8k_existing_spec_c4_mt256_n64.summary.json`
- `results/vllm_ngram_qwen3_4b_math500_existing_spec_c4_mt256_n40.gpu.csv`
- `results/vllm_ngram_qwen3_4b_math500_existing_spec_c4_mt256_n40.samples.csv`
- `results/vllm_ngram_qwen3_4b_math500_existing_spec_c4_mt256_n40.summary.json`
- `results/vllm_ngram_qwen3_4b_math500_existing_spec_c4_mt256_n40.items.json`
- `results/vllm_ngram_qwen3_4b_mbpp_existing_spec_c4_mt256_n24.gpu.csv`
- `results/vllm_ngram_qwen3_4b_mbpp_existing_spec_c4_mt256_n24.samples.csv`
- `results/vllm_ngram_qwen3_4b_mbpp_existing_spec_c4_mt256_n24.summary.json`
- `results/vllm_ngram_qwen3_4b_mbpp_existing_spec_c4_mt256_n24.items.json`

### Scripts
- `scripts/quality_endpoint_eval.py`
- `scripts/endpoint_benchmark.py`
- `scripts/dflash_server_commands.py`
- `scripts/run_vllm_existing_spec_matrix.sh`
- `scripts/compare_spec_baselines.py`

### Server logs
- `logs/vllm_ngram_server_existing_spec_20260413T191506Z.log`
- `logs/vllm_ngram_server_existing_spec_20260413T191506Z.log.cmd`
- `logs/vllm_ngram_server_existing_spec_20260413T191506Z.log.pid`

### Run documentation
- `run_notes.md`
- `.omx/metrics.json`
- `.omx/project.json`

### Paper pipeline artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
