# DFlash Speculative Decoding on NVIDIA GB10 with Qwen3-4B: A Transformers Smoke Validation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We report empirical results from running DFlash speculative decoding with the public Qwen3-4B target model and Qwen3-4B-DFlash-b16 draft model on a single NVIDIA GB10 GPU using the Hugging Face Transformers backend. Across 24 deterministic short and medium prompts (GSM8K-style, math, code, reasoning, and text), DFlash achieved a mean latency speedup of 3.55× over target-only greedy decoding (median 3.32×, p90 not reported for speedup), with 100% deterministic final-answer equivalence and 91.67% exact token-level match. One very short reasoning prompt exhibited a latency regression (0.78×). Two prompts produced token-level mismatches that preserved the final numeric answer. These results are limited to a single GPU, a single model pair, 24 hand-crafted prompts, and a maximum of 96 generated tokens. The findings support the accessibility of DFlash speculative decoding on GB10 hardware with publicly available model artifacts, but do not constitute a comprehensive benchmark.

---

## 1. Introduction

Speculative decoding accelerates autoregressive language model inference by using a smaller draft model to propose candidate token sequences, which the target model then verifies in parallel. When the draft model's proposals align with the target model's distribution, multiple tokens can be emitted per verification step, reducing wall-clock latency without changing the output distribution.

DFlash is an implementation of speculative decoding distributed by z-lab, integrated with the Hugging Face Transformers library. The central question motivating this work is whether DFlash speculative decoding can operate on NVIDIA GB10 hardware using publicly available, ungated model artifacts—specifically, the Qwen3-4B target model and its companion Qwen3-4B-DFlash-b16 draft model—without requiring the user to train a custom draft model.

This report documents two experimental phases: an initial 3-prompt smoke test and a subsequent 24-prompt short/medium benchmark. Both phases were executed on a single NVIDIA GB10 GPU with CUDA 13.0 and PyTorch 2.11.0. The results are presented with full disclosure of negative findings, including a latency regression on one short prompt and two token-level output mismatches.

---

## 2. Method

### 2.1 Software Environment

The DFlash repository (`z-lab/dflash`) was cloned at commit `6a13dfe956380821bb4e1a4f232b5d765ec17f7c` and installed in editable mode. The environment used Python 3 with `uv`-managed virtual environment, PyTorch 2.11.0+cu130, and Transformers 4.57.1 (installed as a DFlash dependency). Attention was handled by SDPA (Scaled Dot-Product Attention) with bf16 precision throughout.

### 2.2 Model Artifacts

Two publicly available, ungated Hugging Face model repositories were used:

- **Target model:** `Qwen/Qwen3-4B` (~8.06 GB on disk), providing weights, configuration, and tokenizer.
- **Draft model:** `z-lab/Qwen3-4B-DFlash-b16` (~1.08 GB on disk), providing the DFlash draft configuration and weights.

Both were downloaded to local storage (`models/Qwen3-4B/` and `models/Qwen3-4B-DFlash-b16/`) using `aria2c` after initial Hugging Face `snapshot_download` transfers stalled on xet large-file transfers.

### 2.3 Hardware

All experiments ran on a single NVIDIA GB10 GPU with CUDA 13.0. No multi-GPU or distributed configuration was used.

### 2.4 Experimental Harness

Two deterministic benchmark scripts were developed:

1. **`scripts/run_transformers_smoke.py`** — Initial 3-prompt smoke test with max 64 new tokens.
2. **`scripts/run_transformers_benchmark.py`** — Broader 24-prompt benchmark with max 96 new tokens, recording per-prompt latency, token equivalence, acceptance lengths, and GPU memory.

A post-hoc answer-equivalence analysis was performed using **`scripts/analyze_answer_equivalence.py`**, which extracted final numeric answers from outputs that did not match at the exact token level.

### 2.5 Prompt Design

**Phase 1 (smoke test):** 3 deterministic tiny prompts covering GSM8K-style arithmetic, math arithmetic, and a code snippet. Maximum 64 new tokens.

**Phase 2 (broader benchmark):** 24 deterministic prompts divided into 12 short and 12 medium prompts, spanning five categories: GSM8K-style, math, code, reasoning, and text. Maximum 96 new tokens. The prompts were hand-crafted for determinism rather than sampled from a standard benchmark corpus.

### 2.6 Metrics

The following metrics were recorded per prompt and in aggregate:

- **Target greedy latency:** Wall-clock time for target-only greedy decoding.
- **DFlash latency:** Wall-clock time for DFlash speculative decoding.
- **Speedup:** Ratio of target greedy latency to DFlash latency.
- **Exact token match:** Whether the full generated token sequence is identical between target-only and DFlash outputs.
- **Final-answer equivalence:** Whether the final numeric answer extracted from both outputs matches, even if surrounding text differs.
- **Acceptance length:** Number of tokens accepted per DFlash verification step.
- **GPU memory:** Post-load allocation, reservation, and peak reservation.

---

## 3. Results

### 3.1 Phase 1: Smoke Test (3 Prompts)

| Metric | Value |
|---|---|
| Model load time | 41.19 s |
| Post-load GPU allocation | ~9.12 GB |
| Post-load GPU reservation | ~9.12 GB |
| Peak GPU reservation | ~9.19 GB |
| Exact token match rate | 3/3 (100%) |
| Mean target greedy latency | 1.067 s |
| Mean DFlash latency | 0.336 s |
| Mean speedup | 2.69× |
| Mean acceptance length | 3.53 tokens |

Per-prompt speedups: GSM8K-style 3.21×, math 1.43×, code 3.43×.

The smoke test confirmed that DFlash loaded and executed on GB10 without errors, preserved greedy outputs on all three prompts, and reduced latency on each prompt.

### 3.2 Phase 2: Short/Medium Benchmark (24 Prompts)

| Metric | Value |
|---|---|
| Model load time | 41.16 s |
| Post-load GPU allocation | ~9.12 GB |
| Post-load GPU reservation | ~9.12 GB |
| Peak GPU reservation during run | ~9.20 GB |

**Latency and speedup:**

| Metric | Overall | Short prompts | Medium prompts |
|---|---|---|---|
| Mean target greedy latency | 2.214 s | — | — |
| Median target greedy latency | 2.115 s | — | — |
| p90 target greedy latency | 4.905 s | — | — |
| Mean DFlash latency | 0.551 s | — | — |
| Median DFlash latency | 0.438 s | — | — |
| p90 DFlash latency | 0.995 s | — | — |
| Mean speedup | 3.55× | 2.44× | 4.66× |
| Median speedup | 3.32× | 1.44× | 4.61× |
| Min speedup | 0.78× | 0.78× | 1.77× |
| Max speedup | 8.87× | — | — |

One very short reasoning prompt (`short_reason_10`) was slower under DFlash than under target-only greedy decoding (0.78× speedup). This is consistent with the known behavior of speculative decoding, where the overhead of draft-model forward passes and verification can exceed the cost of simply decoding a small number of tokens.

**Acceptance lengths:**

| Metric | Overall | Short prompts | Medium prompts |
|---|---|---|---|
| Mean acceptance length | 4.98 tokens | 4.73 tokens | 5.12 tokens |

**Output equivalence:**

| Metric | Value |
|---|---|
| Exact token/text match | 22/24 (91.67%) |
| Final-answer equivalence | 24/24 (100%) |

The two exact-token mismatches were:

1. **`short_reason_10`:** Target greedy produced `0.25`; DFlash produced `0.25 is larger than 0.2... Answer: 0.25`. The final numeric answer (0.25) matched.
2. **`medium_gsm_02`:** Target greedy produced `79 pencils remain`; DFlash produced `79 pencils left`. The final numeric answer (79) matched.

Both mismatches reflect differences in surface-form text while preserving the correct final answer. The first case is notable because DFlash produced a longer, more verbose output than target-only greedy decoding, which also contributed to the latency regression on that prompt.

### 3.3 Negative and Mixed Findings

- **Latency regression on short prompts:** The minimum observed speedup was 0.78×, occurring on a very short reasoning prompt. Short prompts exhibited higher variance in speedup (median 1.44× vs. mean 2.44×), indicating that speculative decoding overhead can dominate when the target model would generate few tokens.
- **Token-level mismatches:** 2 of 24 prompts (8.33%) did not produce byte-for-byte identical output. While final-answer equivalence was preserved, this confirms that DFlash speculative decoding is not guaranteed to reproduce the exact token sequence of target-only greedy decoding in all cases.
- **No long-prompt data:** No prompts exceeding the "medium" length category were tested. Speedup characteristics at longer generation lengths remain uncharacterized in this study.

---

## 4. Limitations

1. **Small prompt sample:** The benchmark comprises 24 hand-crafted deterministic prompts. This is insufficient to characterize performance on standard evaluation corpora such as GSM8K, HumanEval, or MATH at scale.
2. **Single hardware configuration:** All results were obtained on one NVIDIA GB10 GPU. Performance on other GPUs (e.g., A100, H100, consumer RTX) may differ substantially.
3. **Single model pair:** Only Qwen3-4B with Qwen3-4B-DFlash-b16 was tested. Results do not generalize to other target or draft models without additional experimentation.
4. **Short generation lengths:** Maximum generation was 96 tokens. Real-world use often involves much longer outputs, where acceptance-length dynamics and memory behavior may differ.
5. **No training of draft models:** The draft model was used as-is from a public repository. The effect of draft-model quality on acceptance rates and speedup was not investigated.
6. **Token-level non-identity:** DFlash speculative decoding did not produce byte-for-byte identical output on every prompt. Applications requiring exact reproducibility of greedy decoding should account for this.
7. **Deterministic prompts only:** All prompts were designed to have deterministic correct answers. Performance on open-ended or creative generation tasks was not evaluated.
8. **No comparison to other acceleration methods:** Results are reported relative to target-only greedy decoding only. Comparison against other inference acceleration techniques (e.g., quantization, KV-cache optimization, other speculative decoding implementations) was not performed.
9. **Confidence assessment:** The project decision assigned medium confidence and strong evidence strength to the hypothesis that DFlash works on GB10 with public artifacts. This reflects the positive but narrow evidence base.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Code repository and commit hash | Recorded: `z-lab/dflash` at `6a13dfe956380821bb4e1a4f232b5d765ec17f7c` |
| Model identifiers | Recorded: `Qwen/Qwen3-4B`, `z-lab/Qwen3-4B-DFlash-b16` |
| Hardware specification | Recorded: NVIDIA GB10, CUDA 13.0 |
| Software versions | Recorded: PyTorch 2.11.0+cu130, Transformers 4.57.1 |
| Random seeds | Deterministic greedy decoding (temperature 0); no sampling randomness |
| Prompt set | Recorded in `artifacts/transformers_benchmark_short_medium/records.jsonl` |
| Per-prompt results | Recorded in `records.jsonl` files |
| Aggregate summaries | Recorded in `summary.json` files |
| Answer equivalence analysis | Recorded in `answer_equivalence.json` |
| Execution logs | Recorded in `logs/` directory |
| Benchmark scripts | `scripts/run_transformers_smoke.py`, `scripts/run_transformers_benchmark.py`, `scripts/analyze_answer_equivalence.py` |
| Model download procedure | `scripts/download_hf_local.sh` using `aria2c` |

---

## 6. Conclusion

DFlash speculative decoding with the public Qwen3-4B target and Qwen3-4B-DFlash-b16 draft model ran successfully on a single NVIDIA GB10 GPU using the Transformers backend with SDPA attention and bf16 precision. Across 24 deterministic short and medium prompts, the mean latency speedup was 3.55× over target-only greedy decoding, with 100% final-answer equivalence. However, one short prompt exhibited a latency regression (0.78×), and 8.33% of prompts showed token-level output differences despite preserving the final answer. These results support the accessibility of DFlash on GB10 hardware with publicly available artifacts at the tested scale, but do not constitute a comprehensive benchmark. A larger-scale evaluation with curated answer checkers, longer generation lengths, and additional hardware configurations would be necessary to establish more general claims.

---

## Referenced Artifacts

### Result files
- `artifacts/transformers_benchmark_short_medium/answer_equivalence.json`
- `artifacts/transformers_benchmark_short_medium/summary.json`
- `artifacts/transformers_benchmark_short_medium/records.jsonl`
- `artifacts/transformers_smoke_acceptance/summary.json`
- `artifacts/transformers_smoke_acceptance/records.jsonl`
- `artifacts/transformers_smoke/summary.json`
- `artifacts/transformers_smoke/records.jsonl`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`
- `run_notes.md`

### Scripts
- `scripts/run_transformers_smoke.py`
- `scripts/run_transformers_benchmark.py`
- `scripts/analyze_answer_equivalence.py`
- `scripts/download_hf_local.sh`

### Logs
- `logs/transformers_smoke_qwen3_4b_acceptance.log`
- `logs/transformers_benchmark_short_medium.log`
- `logs/answer_equivalence_short_medium.log`

### Paper and audit files
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
