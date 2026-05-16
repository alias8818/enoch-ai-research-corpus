# DFlash Code-Generation Quality Guard: A Post-Run Quality Gate for Speculative Decoding in Code-Generation Workloads

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

Speculative decoding methods such as DFlash promise throughput gains for large-language-model inference, but their impact on code-generation quality—where syntactic correctness, unit-test pass rates, and structured-output validity are critical—remains under-characterized. We present a deterministic post-run quality guard that checks whether DFlash speculative decoding preserves code-generation quality while delivering meaningful throughput improvements. The guard enforces four kill conditions: pass-rate delta below 0.01 absolute, no increase in syntax or JSON invalidity, no increase in request failures, and throughput speedup of at least 1.10×. We evaluate the guard on two target–draft model pairs: Qwen3-4B with its DFlash draft, and Qwen3-Coder-30B-A3B-Instruct (BF16) with its DFlash draft, served via vLLM with a Triton MoE backend. Across four code-generation datasets (HumanEval-style function completion, MBPP-style standalone functions, tool-call JSON validity, and repository-edit file rewrites) at n=8 prompts per dataset, the Qwen3-Coder-30B-A3B pair showed zero quality regression on all datasets and throughput speedups ranging from 1.60× to 2.28×. The Qwen3-4B pair showed similar results with speedups from 1.61× to 4.17× across chat, reasoning, and code tasks. However, the evidence strength is moderate: sample sizes are small (n=8 per dataset), the HumanEval and MBPP subsets are compact local proxies rather than full benchmarks, and two preferred model pairs (gpt-oss-20b-DFlash and Qwen3-Coder-30B-A3B-Instruct-FP8) could not be served on the available hardware due to kernel and attention-backend incompatibilities. The JSON validity task revealed a shared baseline weakness (quality 0.375) that DFlash did not exacerbate but also did not resolve.

---

## 1. Introduction

Speculative decoding accelerates autoregressive inference by drafting candidate tokens with a smaller model and verifying them against the target model in a single forward pass. DFlash is one such method that pairs a target model with a distilled draft model. While throughput improvements have been reported for general text generation, code-generation workloads impose stricter quality constraints: a single syntactically invalid token can render a completion unusable, and structured outputs such as tool-call JSON must satisfy schema constraints.

The central question this work addresses is: **does DFlash speculative decoding preserve code-generation quality—measured by pass rates, syntactic validity, and JSON schema validity—while delivering meaningful throughput gains?**

To answer this, we constructed a deterministic post-run quality guard (`dflash_quality_guard.py`) that compares baseline (target-only) and DFlash (target + draft) inference runs on paired datasets and enforces explicit kill conditions. We applied this guard to two model pairs across multiple code-generation task types on a single GB10 GPU server.

---

## 2. Method

### 2.1 Quality Guard Design

The quality guard is a deterministic post-hoc comparator that takes as input a paired comparison JSON (baseline vs. DFlash summary statistics per dataset) and evaluates four kill conditions:

1. **Pass-rate delta**: The absolute difference in quality (pass rate) between DFlash and baseline must not exceed 0.01. A negative delta exceeding this threshold triggers a kill.
2. **Throughput speedup**: DFlash completion tokens-per-second must be at least 1.10× the baseline rate.
3. **Request failure increase**: The number of failed requests under DFlash must not exceed the baseline count.
4. **Invalidity increase**: Where validity fields are present (syntax-invalid count for code tasks, JSON-invalid count for structured-output tasks), DFlash must not show an increase.

The guard emits a JSON report with per-dataset verdicts and an overall pass/fail verdict. An overall pass requires all datasets to pass all applicable kill conditions.

### 2.2 Evaluation Datasets

We implemented four code-generation datasets within a unified endpoint evaluator (`quality_endpoint_eval.py`):

- **HumanEval-style** (`humaneval`): Eight deterministic Python function-completion prompts with subprocess unit-test scoring and `ast.parse` syntax-invalid counting. This is a compact local subset, not the full 164-problem HumanEval benchmark. An optional `HUMANEVAL_USE_HF=1` flag enables the upstream `openai/openai_humaneval` dataset when available, but this was not used in the reported runs.

- **MBPP-style** (`mbpp`): Eight local standalone Python function-test prompts with subprocess unit-test scoring and syntax-invalid counting.

- **Tool-call JSON** (`json`): Eight prompts requesting structured JSON output with required keys, types, and enum constraints. Scoring checks strict JSON extractability plus schema compliance, reporting `json_invalid` and `invalid_count`.

- **Repository-edit** (`repoedit`): Eight deterministic small Python file-rewrite prompts with subprocess unit-test scoring and syntax-invalid accounting.

### 2.3 Serving Configuration

All inference was performed via vLLM (version 0.19.1rc1.dev242) on a single GB10 GPU server. Key configuration parameters:

- Concurrency: 1
- `max_new_tokens`: 256
- `max_model_len`: 2048
- `max_num_batched_tokens`: 8192
- `gpu_memory_utilization`: 0.82
- `--enforce-eager --moe-backend triton`

The Triton MoE backend was required because the default FlashInfer CUTLASS MoE backend produced a `TypeError` (mismatched argument count in `flashinfer.fused_moe`) for the Qwen3-Coder-30B-A3B model on this stack. The FP8 variant of the same model failed with a CUTLASS GEMM kernel error and could not be served at all.

### 2.4 Model Pairs

Two target–draft pairs were evaluated:

| Pair | Target | Draft | Status |
|------|--------|-------|--------|
| Qwen3-4B | `Qwen/Qwen3-4B` | `z-lab/Qwen3-4B-DFlash-b16` | Fully evaluated (n=8 per dataset) |
| Qwen3-Coder-30B-A3B | `Qwen/Qwen3-Coder-30B-A3B-Instruct` (BF16) | `z-lab/Qwen3-Coder-30B-A3B-DFlash` | Fully evaluated (n=8 per dataset) |

Two additional pairs were probed but could not be served:

| Pair | Target | Draft | Failure Mode |
|------|--------|-------|-------------|
| gpt-oss-20b | `openai/gpt-oss-20b` | `z-lab/gpt-oss-20b-DFlash` | DFlash draft attention backend incompatible with GB10/SM121 (attention sinks + non-causal draft attention); also `AssertionError: All drafting layers should belong to the same kv cache group` |
| Qwen3-Coder-30B-A3B-FP8 | `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` | `z-lab/Qwen3-Coder-30B-A3B-DFlash` | `RuntimeError: cutlass_gemm_caller ... Error Internal` during vLLM warmup |

### 2.5 Comparison and Guard Pipeline

Baseline and DFlash runs were executed sequentially using `run_vllm_codegen_guard_matrix.sh`, which launches the vLLM server in each mode, waits for readiness, runs the evaluator, stops the server, and emits per-dataset summaries. Summaries were combined into a comparison JSON via `compare_quality_runs.py`, then passed to `dflash_quality_guard.py` for the kill-condition check.

A practical note: when running baseline followed immediately by DFlash in a single script, GPU memory from the baseline server process was not fully released before DFlash launch, causing an out-of-memory failure. Rerunning DFlash after memory was released resolved this. Baseline and DFlash runs were otherwise identical in all serving parameters except speculative decoding enablement.

---

## 3. Results

### 3.1 Qwen3-Coder-30B-A3B (Preferred Target, n=8 per Dataset)

| Dataset | Baseline Quality | DFlash Quality | Quality Δ | Syntax/JSON Invalid (B→D) | Failures (B→D) | Baseline tok/s | DFlash tok/s | Speedup |
|---------|-----------------|----------------|-----------|---------------------------|----------------|---------------|--------------|---------|
| HumanEval-style | 0.875 | 0.875 | 0.000 | 0 → 0 | 0 → 0 | 26.74 | 61.08 | 2.28× |
| Tool-call JSON | 0.375 | 0.375 | 0.000 | 5 → 5 | 0 → 0 | 26.48 | 42.39 | 1.60× |
| MBPP-style | 1.000 | 1.000 | 0.000 | 0 → 0 | 0 → 0 | 26.51 | 56.79 | 2.14× |
| Repo-edit | 1.000 | 1.000 | 0.000 | 0 → 0 | 0 → 0 | 24.96 | 45.06 | 1.81× |

Guard verdict: **overall_pass = true**.

DFlash speculative decoding statistics from vLLM logs: 1,676 accepted out of 3,680 drafted tokens (45.5% acceptance rate), mean acceptance length 8.46, average draft acceptance rate 46.6%.

### 3.2 Qwen3-4B (n=8 per Dataset, Code-Generation Guard)

| Dataset | Baseline Quality | DFlash Quality | Quality Δ | Syntax/JSON Invalid (B→D) | Failures (B→D) | Baseline tok/s | DFlash tok/s | Speedup |
|---------|-----------------|----------------|-----------|---------------------------|----------------|---------------|--------------|---------|
| HumanEval-style | 0.750 | 0.750 | 0.000 | 0 → 0 | 0 → 0 | 45.57 | 143.30 | 3.14× |
| Tool-call JSON | 0.375 | 0.375 | 0.000 | 5 → 5 | 0 → 0 | 47.36 | 183.91 | 3.88× |

Guard verdict: **overall_pass = true**.

### 3.3 Qwen3-4B (Acquired from Adjacent Project, Chat/Reasoning Tasks)

| Dataset | Quality Δ | Failures (B→D) | Speedup |
|---------|-----------|----------------|---------|
| Chat | 0.000 | 0 → 0 | 1.61× |
| GSM8K | 0.000 | 0 → 0 | 3.04× |
| MATH-500 | 0.000 | 0 → 0 | 4.17× |
| MBPP-local | 0.000 | 0 → 0 | 3.96× |

Guard verdict: **overall_pass = true**.

### 3.4 Negative Results: Models That Could Not Be Served

The gpt-oss-20b DFlash pair failed at the serving layer: vLLM on GB10/SM121 lacks a valid backend for the attention-sink and non-causal draft attention patterns required by this draft model. Experimental local gating patches bypassed the initial check but subsequently failed with a KV-cache group assertion. The baseline target-only mode completed successfully, but no DFlash comparison was possible.

The Qwen3-Coder-30B-A3B-Instruct-FP8 target failed during vLLM warmup with a CUTLASS GEMM internal error, likely a kernel compatibility issue on this hardware/software stack. No baseline or DFlash metrics were produced for this variant.

The non-FP8 Qwen3-Coder-30B-A3B-Instruct target also failed under the default FlashInfer CUTLASS MoE backend (argument-count mismatch in `flashinfer.fused_moe`). Switching to `--moe-backend triton` resolved this, enabling the results reported in Section 3.1.

### 3.5 Shared Weakness: Tool-Call JSON Quality

Both model pairs produced low quality on the tool-call JSON dataset (0.375 for both baseline and DFlash), with 5 of 8 responses failing JSON schema validation in both modes. This is a shared weakness of the models on this task type, not a DFlash regression. DFlash preserved the baseline's invalidity count exactly (5 → 5) for both pairs.

---

## 4. Limitations

1. **Small sample sizes.** All reported results use n=8 prompts per dataset. These are compact local subsets, not the full HumanEval (164 problems), MBPP (500 problems), or large-scale repository-edit benchmarks. The n=8 design provides directional evidence but limited statistical power. A single additional failure or success can shift quality by 0.125.

2. **Single hardware configuration.** All experiments ran on one GB10 GPU server with vLLM 0.19.1rc1.dev242. Throughput numbers and serving compatibility are hardware- and stack-dependent. The FP8 and FlashInfer CUTLASS MoE failures illustrate this dependency directly.

3. **Incomplete model-pair coverage.** Two of four probed model pairs (gpt-oss-20b-DFlash and Qwen3-Coder-30B-A3B-FP8) could not be served on the available stack. The quality guard hypothesis remains untested for these pairs. The gpt-oss-20b failure is particularly notable because it reflects a fundamental attention-backend incompatibility rather than a simple configuration issue.

4. **Sequential rather than concurrent baseline/DFlash runs.** Baseline and DFlash runs were performed sequentially on the same GPU, not simultaneously on independent hardware. GPU thermal state, memory fragmentation, and the observed memory-release delay between runs introduce potential variance that is not captured by the current guard.

5. **Deterministic prompt subsets.** The HumanEval-style, MBPP-style, and repo-edit prompts are fixed local subsets. Results may not generalize to different prompt selections, longer generation lengths, or higher concurrency levels.

6. **No latency measurement.** The guard measures completion tokens-per-second (throughput) but not per-request latency (time to first token or total request time). Throughput and latency can diverge under speculative decoding, and latency-sensitive applications may require separate evaluation.

7. **JSON quality is low for both modes.** The 0.375 quality on tool-call JSON tasks indicates that neither baseline nor DFlash reliably produces valid structured output for these prompts. The guard correctly identifies that DFlash does not worsen this, but the result should not be interpreted as evidence that DFlash is suitable for structured-output tasks where baseline quality is already marginal.

8. **Draft acceptance rate is moderate.** The 45.5% token acceptance rate and 46.6% draft acceptance rate for Qwen3-Coder-30B-A3B suggest that the draft model frequently diverges from the target. Higher acceptance rates would yield larger speedups; lower rates could reduce or eliminate the throughput benefit.

---

## 5. Reproducibility Checklist

| Item | Status | Details |
|------|--------|---------|
| Model identifiers | Specified | `Qwen/Qwen3-Coder-30B-A3B-Instruct`, `z-lab/Qwen3-Coder-30B-A3B-DFlash`, `Qwen/Qwen3-4B`, `z-lab/Qwen3-4B-DFlash-b16` |
| Serving stack | Specified | vLLM 0.19.1rc1.dev242, `--enforce-eager --moe-backend triton` |
| Hardware | Partially specified | GB10 GPU server; exact VRAM and SM architecture not recorded in artifacts |
| Inference parameters | Specified | concurrency=1, max_new_tokens=256, max_model_len=2048, max_num_batched_tokens=8192, gpu_memory_utilization=0.82 |
| Evaluation scripts | Available in project | `scripts/quality_endpoint_eval.py`, `scripts/dflash_quality_guard.py`, `scripts/compare_quality_runs.py`, `scripts/dflash_server_commands.py`, `scripts/run_vllm_codegen_guard_matrix.sh` |
| Prompt subsets | Deterministic, local | 8 prompts per dataset; not the full public benchmarks |
| Random seeds | Not controlled | vLLM sampling uses default temperature/top-p; exact reproducibility of individual completions is not guaranteed |
| Result artifacts | Available | See Referenced Artifacts section |
| Failed configurations | Documented | gpt-oss-20b DFlash (attention backend), Qwen3-Coder FP8 (CUTLASS GEMM), FlashInfer CUTLASS MoE (argument mismatch) |

---

## 6. Conclusion

We presented a deterministic post-run quality guard for evaluating whether DFlash speculative decoding preserves code-generation quality while delivering throughput gains. Applied to the Qwen3-Coder-30B-A3B-Instruct (BF16) target with its DFlash draft on a GB10 server, the guard passed on all four code-generation datasets (HumanEval-style, MBPP-style, tool-call JSON, and repository-edit) at n=8, with zero quality regression and throughput speedups of 1.60×–2.28×. The Qwen3-4B pair showed consistent results with higher speedups (1.61×–4.17×) across chat, reasoning, and code tasks.

These findings support the hypothesis that DFlash speculative decoding can preserve code-generation quality under the tested conditions, but the evidence strength is moderate. The small sample sizes, single hardware configuration, incomplete model-pair coverage (two of four pairs could not be served), and moderate draft acceptance rate (45.5%) all bound the generality of the conclusion. The low JSON quality (0.375) shared by baseline and DFlash on tool-call tasks highlights that quality preservation is not equivalent to quality sufficiency.

Future work should extend the evaluation to full HumanEval and MBPP benchmarks, larger repository-edit suites, additional hardware configurations, and the model pairs that were blocked by serving incompatibilities in this study. The guard framework itself—the four kill conditions and the paired comparison pipeline—is directly reusable for such extensions.

---

## Referenced Artifacts

### Project decision and metadata
- `.omx/project_decision.json` — project decision (`finalize_positive`), hypothesis status, confidence, evidence strength
- `.omx/metrics.json` — session metrics
- `run_notes.md` — chronological run notes documenting all execution steps, failures, and results

### Claim audit
- `papers/source-record-redacted/claim_ledger.json` — placeholder/blocked claim ledger; strict claim/evidence audit is blocked because no structured claims were extracted

### Evidence bundle
- `papers/source-record-redacted/evidence_bundle.json` — consolidated evidence including decision, run notes tail, and result file inventory

### Primary guard report (Qwen3-Coder-30B-A3B, n=8)
- `results/dflash_qwen3_coder_30b_bf16_triton_n8plus_guard_report.json` — overall_pass=true
- `results/vllm_qwen3_coder_30b_bf16_triton_n8plus_codegen_guard_comparison.json` — paired comparison data

### Per-dataset result files (Qwen3-Coder-30B-A3B, n=8)
- `results/vllm_dflash_qwen3_coder_30b_bf16_triton_n8plus_humaneval_codeguard_c1_mt256_n8.{gpu.csv,samples.csv,summary.json,items.json}`
- `results/vllm_dflash_qwen3_coder_30b_bf16_triton_n8plus_json_codeguard_c1_mt256_n8.{gpu.csv,samples.csv,summary.json,items.json}`
- `results/vllm_dflash_qwen3_coder_30b_bf16_triton_n8plus_mbpp_codeguard_c1_mt256_n8.{gpu.csv,samples.csv,summary.json,items.json}`
- `results/vllm_dflash_qwen3_coder_30b_bf16_triton_n8plus_repoedit_codeguard_c1_mt256_n8.{gpu.csv,samples.csv,summary.json,items.json}`

### Probe and acquisition artifacts
- `artifacts/qwen3_coder_30b_bf16_triton_n8plus_probe_summary.json`
- `artifacts/qwen3_coder_30b_nonfp8_download.json`
- `artifacts/qwen3_coder_30b_download.json`
- `artifacts/gpt_oss_dflash_download.json`
- `artifacts/preferred_pair_probe_summary.json`
- `artifacts/model_availability_check.json`
- `artifacts/vllm_dflash_models_codegen_guard.json`
- `artifacts/evaluator_extension_selftest.json`
- `artifacts/repoedit_evaluator_selftest.json`

### Earlier guard reports (Qwen3-4B)
- `results/dflash_quality_guard_report.json` — overall_pass=true (chat, GSM8K, MATH-500, MBPP-local)
- `results/dflash_codegen_guard_report.json` — overall_pass=true (HumanEval-style, JSON)

### Evaluation and guard scripts
- `scripts/quality_endpoint_eval.py`
- `scripts/dflash_quality_guard.py`
- `scripts/compare_quality_runs.py`
- `scripts/dflash_server_commands.py`
- `scripts/run_vllm_codegen_guard_matrix.sh`
