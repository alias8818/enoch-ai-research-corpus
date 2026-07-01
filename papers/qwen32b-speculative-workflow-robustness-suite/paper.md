# Speculative Decoding with Qwen3-32B on NVIDIA GB10: Workflow Robustness and Throughput Calibration

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, metrics). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We evaluate the viability and throughput characteristics of speculative decoding in llama.cpp using a Qwen3-32B Q4_K_M target model with a Qwen3-0.6B Q8_0 draft model on an NVIDIA GB10 platform. Across 13 smoke-test and calibration cases (1 smoke, 3 baseline, 9 speculative), all runs completed successfully with zero exit codes and no memory errors under a no-swap configuration. Decode-only speculative speedups ranged from 1.08× to 2.55× depending on prompt type and draft length, with a mean of 1.37×. The best-performing configuration (draft length 4, draft-p-min 0.8) yielded 1.30× speedup on a short-instruction prompt, 1.29× on a structured-list prompt, and 2.55× on a code/text prompt. Acceptance rates were strongly prompt-sensitive: 66% for code/text but only 10–20% for the two prose-oriented prompts. Increasing draft length from 4 to 8 sharply reduced acceptance and largely eliminated gains on non-code prompts. Lowering draft-p-min from 0.8 to 0.5 produced no change in acceptance counts under deterministic (temperature 0) generation. These results are decode-throughput measurements from per-process invocations that include model-loading overhead; end-to-end latency under persistent serving remains unvalidated. We conclude the workflow is technically viable for follow-up research but that the small draft model's utility is bounded by prompt-dependent acceptance rates.

## 1. Introduction

Speculative decoding accelerates autoregressive inference by using a smaller draft model to propose candidate tokens that a larger target model verifies in parallel. When the draft model's distribution aligns with the target's, multiple tokens can be accepted per verification pass, increasing effective throughput without changing the output distribution.

This work addresses a practical question: can a local NVIDIA GB10 system run a Qwen3-32B target model with a Qwen3-0.6B draft under llama.cpp speculative decoding, and is the resulting workflow robust enough to justify further research investment? We do not attempt to establish new theoretical bounds or compare against alternative serving frameworks. Instead, we provide a calibration-level characterization of throughput, acceptance rates, and memory behavior under controlled but limited conditions.

The contributions are: (1) evidence that the Qwen3-32B/Qwen3-0.6B speculative pair runs stably on GB10 hardware under llama.cpp with no swap and ample memory headroom; (2) quantitative calibration of decode-speed gains and acceptance rates across three prompt types and two draft-length settings; and (3) identification of prompt-sensitivity and draft-length sensitivity as the primary bounded factors on realizable speedup.

## 2. Method

### 2.1 Hardware and Software Environment

All runs were executed on a single GB10 host (`Linux gx10-efe8`, aarch64, 20 CPU cores) with an NVIDIA GB10 GPU and CUDA 13.0 driver. Swap was disabled (`Swap: 0B`) for the duration of the suite. The llama.cpp binary was located at `<local-path-redacted>`. System memory availability was sampled via `/proc/meminfo MemAvailable` by the harness throughout execution.

### 2.2 Models

- **Target:** Qwen3-32B, quantized to Q4_K_M format (`Qwen3-32B-Q4_K_M.gguf`, approximately 18.4 GiB), sourced from `ggml-org/Qwen3-32B-GGUF`.
- **Draft:** Qwen3-0.6B, quantized to Q8_0 format (`Qwen3-0.6B-Q8_0.gguf`, approximately 0.75 GiB), sourced from `ggml-org/Qwen3-0.6B-GGUF`.

The draft model is approximately 53× smaller than the target in parameter count, which raises the question of whether its distribution tracks the target sufficiently for useful acceptance rates.

### 2.3 Harness and Protocol

The suite was driven by `scripts/run_spec_suite.py`, which launched llama.cpp as a separate process per test case. Each invocation reloaded the model from disk. The primary run command was:

```bash
./scripts/run_spec_suite.py \
  --predict 48 \
  --ctx 2048 \
  --timeout 240 \
  --out results/spec_suite_qwen32b_q4km_qwen06_q8 \
  --target models/Qwen3-32B-Q4_K_M.gguf \
  --draft models/Qwen3-0.6B-Q8_0.gguf
```

Each case generated 48 tokens with a context window of 2048 and a per-case timeout of 240 seconds. Temperature was set to 0 (deterministic generation) for all cases.

### 2.4 Test Cases

The suite comprised 13 cases:

- **1 smoke test** (`00_target_smoke_baseline`): target-only, verifying model load and basic generation.
- **3 baseline cases**: target-only generation for each of three prompt types (short instruction, structured list, code/text).
- **9 speculative cases**: combinations of draft length (4, 8) and draft-p-min (0.5, 0.8) across the three prompt types. Draft length 4 was tested only at draft-p-min=0.8, yielding three draft=4 cases and six draft=8 cases.

### 2.5 Metrics

Primary metrics were:

- **eval_tps** (decoded tokens per second): reported by llama.cpp for the decode phase.
- **Acceptance rate** (`accept_pct`): the fraction of drafted tokens accepted by the target verifier.
- **Speedup**: ratio of speculative decode tps to baseline decode tps for the same prompt.
- **MemAvailable minimum**: lowest sampled value of `/proc/meminfo MemAvailable` during execution.
- **GPU memory allocation**: reported by llama.cpp's CUDA memory telemetry.

Wall-clock elapsed time was recorded but includes model-loading overhead in every case; it is not reported as a primary metric because it conflates I/O with decode performance.

## 3. Results

### 3.1 Smoke Test and Memory

The target model loaded and generated successfully. llama.cpp reported a model GPU buffer of 18,423 MiB and total self-allocation of 19,002 MiB (context 272 MiB, compute 306 MiB, unaccounted 6,003 MiB). The GPU reported 124,546 MiB total memory with 99,540 MiB free after allocation. Minimum sampled MemAvailable across the smoke test was 97.23 GiB. No swap was present or needed. The memory posture is comfortable: the target model consumes approximately 19 GiB of GPU memory on a device with 124 GiB total, leaving substantial headroom for the draft model and KV cache.

### 3.2 Baseline Throughput

Baseline (target-only) decode speeds were stable across the three prompt types:

| Prompt type | Baseline tok/s |
|---|---:|
| Short instruction | 10.22 |
| Structured list | 10.26 |
| Code/text | 10.25 |

The consistency (~10.2 tok/s) indicates that baseline throughput is not prompt-sensitive at this sequence length and quantization level.

### 3.3 Speculative Decoding Throughput

Table 1 presents all nine speculative cases. Speedup is computed as `spec_tps / baseline_tps` for the matching prompt.

**Table 1.** Speculative decoding results across prompt types, draft lengths, and draft-p-min thresholds.

| Case | Prompt | Draft len | p_min | Decoded tok/s | Baseline tok/s | Speedup | Accept % | n_drafted | n_accept |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_d4_p08_short_instruction | Short instruction | 4 | 0.8 | 13.255 | 10.22 | 1.30 | 20.37 | 108 | 22 |
| spec_d8_p08_short_instruction | Short instruction | 8 | 0.8 | 11.522 | 10.22 | 1.13 | 10.65 | 216 | 23 |
| spec_d8_p05_short_instruction | Short instruction | 8 | 0.5 | 11.456 | 10.22 | 1.12 | 10.65 | 216 | 23 |
| spec_d4_p08_structured_list | Structured list | 4 | 0.8 | 13.221 | 10.26 | 1.29 | 19.64 | 112 | 22 |
| spec_d8_p08_structured_list | Structured list | 8 | 0.8 | 11.065 | 10.26 | 1.08 | 9.82 | 224 | 22 |
| spec_d8_p05_structured_list | Structured list | 8 | 0.5 | 11.149 | 10.26 | 1.09 | 9.82 | 224 | 22 |
| spec_d4_p08_code_text | Code/text | 4 | 0.8 | 26.135 | 10.25 | 2.55 | 66.07 | 56 | 37 |
| spec_d8_p08_code_text | Code/text | 8 | 0.8 | 14.177 | 10.25 | 1.38 | 15.91 | 176 | 28 |
| spec_d8_p05_code_text | Code/text | 8 | 0.5 | 13.979 | 10.25 | 1.36 | 15.91 | 176 | 28 |

All cases exited with return code 0. No crashes, out-of-memory events, or timeouts occurred.

### 3.4 Aggregate Statistics

Across all nine speculative cases:

- Mean speedup: 1.37×
- Mean acceptance rate: 19.87%
- Best single-case speedup: 2.55× (code/text, draft=4, p_min=0.8)
- Worst single-case speedup: 1.08× (structured list, draft=8, p_min=0.8)

The mean speedup of 1.37× is dominated by the single high-acceptance code/text case at draft=4. The median speedup is considerably lower (approximately 1.13×), reflecting that most configurations produced modest gains.

### 3.5 Draft Length Sensitivity

Draft length 4 consistently outperformed draft length 8. For the short instruction prompt, speedup dropped from 1.30× (draft=4) to 1.13× (draft=8). For structured list, the drop was from 1.29× to 1.08×. For code/text, the drop was from 2.55× to 1.38×. The mechanism is clear: longer draft sequences give the small 0.6B model more opportunity to diverge from the 32B target's distribution, causing rejection cascades that waste draft computation without producing accepted tokens.

Notably, for the two prose-oriented prompts, the absolute number of accepted tokens barely increased with draft length 8 (22 accepted at draft=4 vs. 22–23 at draft=8), meaning the additional drafted tokens were almost entirely rejected. The speculative overhead of generating and verifying those rejected tokens produced net slowdown relative to the shorter draft.

### 3.6 Draft-p-min Sensitivity

Lowering draft-p-min from 0.8 to 0.5 produced no change in acceptance counts for the draft=8 cases tested (all at temperature 0). Acceptance counts were identical: 23 vs. 23 (short instruction), 22 vs. 22 (structured list), 28 vs. 28 (code/text). Decoded tok/s values were also nearly identical, differing only in the second decimal place (e.g., 11.522 vs. 11.456 for short instruction).

This is expected under deterministic (temperature 0) generation: when the draft model's top token is accepted, the probability threshold is irrelevant; when it is rejected, lowering the threshold does not help. The draft-p-min parameter may exhibit different behavior under non-zero temperature, which was not tested.

### 3.7 Prompt Sensitivity

The most striking result is the prompt-dependence of acceptance rates. The code/text prompt achieved 66% acceptance at draft=4, yielding a 2.55× speedup. The two prose-oriented prompts achieved only ~20% acceptance at the same setting, yielding modest ~1.3× speedups. This suggests the 0.6B draft model tracks the 32B target's distribution substantially better for code-structured output than for general prose, possibly because code has more constrained token distributions that a small model can approximate. However, with only one code/text prompt tested, this observation should not be generalized without further evidence.

## 4. Limitations

1. **Per-process invocation with model reload.** Each test case launched a fresh llama.cpp process, incurring model-loading I/O overhead. The reported speedups are decode-phase metrics only. End-to-end latency including load time would be substantially worse. A persistent server or reused-context setup is necessary to validate realizable wall-clock gains.

2. **Short generation length.** All cases generated only 48 tokens. Speculative decoding's amortization of verification overhead may differ at longer sequence lengths, where KV-cache effects and batch dynamics change.

3. **Single quantization configuration.** Only Q4_K_M (target) and Q8_0 (draft) were tested. Different quantization levels may alter both baseline throughput and acceptance rates.

4. **No output quality evaluation.** The suite verified that generation completed successfully (exit code 0) but did not score output quality. Under speculative decoding with a correct verifier, output distribution is preserved by construction; however, implementation bugs could violate this guarantee, and we did not independently verify distributional equivalence.

5. **Deterministic generation only.** All cases used temperature 0. The draft-p-min parameter had no observable effect under this setting. Results may differ under stochastic sampling.

6. **Limited prompt diversity.** Three prompt types are insufficient to characterize the full acceptance-rate distribution. The code/text prompt's high acceptance may not generalize to all code prompts, and the prose prompts' low acceptance may not represent all non-code workloads.

7. **Single hardware configuration.** Results are specific to the GB10 GPU. Different GPU memory hierarchies, compute capabilities, and CUDA versions may yield different baseline and speculative throughputs.

8. **Small draft model.** The 0.6B draft is a 53× parameter reduction from the 32B target. A larger or better-aligned draft model could improve acceptance rates on prose workloads, but this was not tested.

9. **No repeated trials.** Each configuration was run once. No confidence intervals or variance estimates are available, so the precision of the reported speedups is unknown.

10. **llama.cpp commit not pinned.** The exact commit hash of the llama.cpp binary was not captured in the available artifacts, which limits exact reproducibility of the software environment.

## 5. Reproducibility Checklist

- **Hardware specified:** Yes — NVIDIA GB10, aarch64 host with 20 CPU cores, CUDA 13.0.
- **Software versions specified:** Partially — llama.cpp binary path given; exact commit hash not captured in the available artifacts.
- **Model files specified:** Yes — `Qwen3-32B-Q4_K_M.gguf` from `ggml-org/Qwen3-32B-GGUF` and `Qwen3-0.6B-Q8_0.gguf` from `ggml-org/Qwen3-0.6B-GGUF`.
- **Random seeds specified:** Not applicable — all runs used temperature 0 (deterministic).
- **Complete command lines provided:** Yes — the harness invocation is recorded with all flags.
- **Raw data available:** Yes — summary JSON, metrics CSV, per-case stdout/stderr logs, and metadata JSONs are present in the results directory.
- **Environment capture:** Yes — `environment.json` was recorded.
- **Statistical uncertainty reported:** No — each configuration was run once; no confidence intervals or repeated trials are available.

## 6. Conclusion

Speculative decoding with Qwen3-32B (Q4_K_M) and Qwen3-0.6B (Q8_0) under llama.cpp is technically viable on the GB10 platform. All 13 test cases completed successfully with no memory pressure under a no-swap configuration. Decode-only speedups were positive in every speculative case, ranging from 1.08× to 2.55×, with a mean of 1.37×.

However, the results are bounded in two important ways. First, acceptance rates are strongly prompt-dependent: the 0.6B draft model achieves useful acceleration (2.55×) on one code-structured prompt but only modest gains (~1.3×) on two prose and list prompts, where acceptance rates fall to 10–20%. Whether this pattern generalizes beyond the three prompts tested is unknown. Second, the per-process benchmarking methodology includes model-loading overhead that masks decode-speed gains in wall-clock time; persistent serving is needed to confirm end-to-end benefits.

The configuration draft=4 with draft-p-min=0.8 is the recommended starting point for follow-up work. Draft length 8 consistently underperformed draft length 4 due to rejection cascades. The draft-p-min parameter had no effect under deterministic generation. Future work should (1) validate under a persistent llama.cpp server to measure end-to-end latency, (2) test longer generation lengths and non-zero temperatures, and (3) evaluate whether a larger or better-aligned draft model can raise acceptance rates above 25% on prose workloads, which is the threshold below which speculative overhead may not justify deployment complexity.

---

## Referenced Artifacts

| Artifact | Path / Identifier |
|---|---|
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Summary JSON | `results/spec_suite_qwen32b_q4km_qwen06_q8/summary.json` |
| Metrics CSV | `results/spec_suite_qwen32b_q4km_qwen06_q8/metrics.csv` |
| Environment capture | `results/spec_suite_qwen32b_q4km_qwen06_q8/environment.json` |
| Per-case logs | `results/spec_suite_qwen32b_q4km_qwen06_q8/logs/*.stdout.txt`, `*.stderr.txt`, `*.meta.json` |
| Downloader script | `scripts/download_models.py` |
| Suite harness | `scripts/run_spec_suite.py` |
| Target model | `models/Qwen3-32B-Q4_K_M.gguf` (source: `ggml-org/Qwen3-32B-GGUF`) |
| Draft model | `models/Qwen3-0.6B-Q8_0.gguf` (source: `ggml-org/Qwen3-0.6B-GGUF`) |
| Claim ledger | `papers/source-record-redacted-20260501T130748661817+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T130748661817+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T130748661817+0000/paper_manifest.json` |
| Project ID | `source-record-redacted` |
| Run ID | `source-record-redacted-20260501T130748661817+0000` |
