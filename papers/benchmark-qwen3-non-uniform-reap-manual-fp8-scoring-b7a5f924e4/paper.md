# Benchmark Qwen3 Non-Uniform REAP Manual-FP8 Scoring

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We benchmark two 25%-sparsity pruning plans—uniform baseline and global/ragged non-uniform—applied to Qwen3-Coder-30B-A3B in FP8 precision, using a manual FP8/BF16 prompt-loss scorer. The scorer is evaluated across three prompt sets of increasing size: a 3-prompt parent smoke test, a 16-prompt mixed general/code set, and a 64-prompt code-eval fixture. The scoring mechanism itself scales reliably across all three settings. However, the pruning-quality comparison between uniform and global/ragged plans yields mixed and inconclusive results. On the 16-prompt set, global/ragged achieves slightly lower mean loss (Δ = −0.010) but loses more individual prompts (7 vs. 9 wins). On the 64-prompt code-eval set, the sign reverses: uniform achieves lower mean loss (Δ = +0.099) while prompt-level wins are exactly tied (32 vs. 32). Paired bootstrap 95% confidence intervals for the mean delta cross zero in both cases: [−0.489, 0.463] for 16 prompts and [−0.119, 0.324] for 64 prompts. We conclude that the manual FP8/BF16 scoring path is supported as a viable evaluation mechanism, but there is no statistically decisive evidence favoring either pruning plan at 25% sparsity on the tested fixtures.

---

## 1. Introduction

Non-uniform (ragged) sparsity allocation in neural network pruning hypothesizes that allowing different sparsity levels across layers or expert components can outperform uniform sparsity, because not all parameters contribute equally to model quality. For Mixture-of-Experts (MoE) architectures such as Qwen3-Coder-30B-A3B, this hypothesis is particularly salient: expert routing patterns and activation magnitudes vary substantially across layers, suggesting that a global sparsity budget might be better spent non-uniformly.

This project benchmarks two 25%-sparsity pruning plans applied to Qwen3-Coder-30B-A3B in FP8 precision:

1. **Uniform baseline plan**: 25% sparsity applied uniformly across all prunable parameters.
2. **Global/ragged plan**: 25% overall sparsity allocated non-uniformly across parameters, implemented via the REAP (Ragged Expert-Aware Pruning) framework.

The evaluation uses a manual FP8/BF16 prompt-loss scorer that loads pruned FP8 checkpoints and computes per-prompt cross-entropy loss, avoiding the overhead and potential confounds of full generation-based evaluation. We report results across three prompt sets of increasing size and domain coverage, with paired bootstrap confidence intervals to quantify uncertainty.

The central question is whether the global/ragged plan demonstrates a consistent quality advantage over the uniform baseline at 25% sparsity, as measured by prompt loss.

---

## 2. Method

### 2.1 Model and Quantization

The target model is Qwen3-Coder-30B-A3B, an MoE architecture with approximately 30B total parameters and 3B active parameters per token. The model is stored and loaded in FP8 precision. Pruned checkpoints at 25% sparsity were materialized under both the uniform baseline plan and the global/ragged plan, each approximately 48 GiB on disk.

### 2.2 Pruning Plans

- **Uniform baseline plan**: Applies 25% sparsity uniformly across all prunable weight tensors.
- **Global/ragged plan**: Allocates the 25% overall sparsity budget non-uniformly across tensors, implemented via the patched REAP framework's non-uniform MoE loader.

Both plans produce pruned checkpoints that are re-serializable and loadable by the manual FP8/BF16 scorer without further modification.

### 2.3 Manual FP8/BF16 Prompt-Loss Scorer

The scorer (`src/manual_fp8_scoring.py`, `src/run_qwen3_manual_fp8_prompt_loss.py`) loads a pruned FP8 checkpoint, tokenizes each prompt, runs a forward pass with `max_length=64`, and records the mean cross-entropy loss per prompt. The scorer operates in BF16 compute precision with FP8-weight loading, matching the inference path of the pruned model.

### 2.4 Paired Bootstrap Analysis

A post-hoc analysis utility (`src/analyze_prompt_loss_delta.py`) computes:

- Per-prompt delta: `loss_global − loss_uniform` for each prompt.
- Mean delta across prompts.
- Prompt-level win counts (how many prompts each plan wins on).
- Paired bootstrap 95% confidence intervals for the mean delta, using 20,000 resamples with a fixed seed (3423677).
- Bootstrap probability that the global plan has lower mean loss (i.e., that the mean delta is negative).

### 2.5 Prompt Sets

Three prompt sets were evaluated:

1. **Parent 3-prompt smoke test**: A minimal set from the parent project, used to validate the scoring pipeline.
2. **16-prompt mixed set**: Hand-curated prompts spanning general reasoning and code tasks (`artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/prompts.json`).
3. **64-prompt code-eval fixture**: Hand-curated code-eval tasks spanning Python, JavaScript, TypeScript, Rust, Go, SQL, algorithms, debugging, testing, systems, ML, and security (`artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/prompts.json`).

An attempt to load the OpenAI HumanEval dataset via `datasets.load_dataset('openai/openai_humaneval')` produced no output after approximately 3.5 minutes and was killed. No HumanEval, MBPP, or APPS datasets were found in the local Hugging Face cache. The 64-prompt fixture was therefore constructed locally as a substitute.

---

## 3. Results

### 3.1 16-Prompt Mixed Benchmark

| Metric | Uniform Baseline | Global/Ragged |
|---|---|---|
| Mean loss | 10.902 | 10.892 |
| Mean perplexity | 54,299 | 53,767 |
| Prompt-level wins | 9 | 7 |
| Delta (global − uniform) | — | −0.010 |
| Bootstrap 95% CI for mean delta | — | [−0.489, 0.463] |
| Bootstrap P(global lower) | — | 0.512 |

The global/ragged plan achieves slightly lower mean loss, but the uniform baseline wins on more individual prompts (9 vs. 7). The bootstrap confidence interval is wide and crosses zero, consistent with no statistically discernible difference at this sample size.

### 3.2 64-Prompt Code-Eval Benchmark

| Metric | Uniform Baseline | Global/Ragged |
|---|---|---|
| Mean loss | 11.090 | 11.189 |
| Prompt-level wins | 32 | 32 |
| Delta (global − uniform) | — | +0.099 |
| Bootstrap 95% CI for mean delta | — | [−0.119, 0.324] |
| Bootstrap P(global lower) | — | 0.191 |
| Peak CUDA allocation | ~22.320 GiB | ~22.320 GiB |

On the larger code-eval fixture, the sign of the mean delta reverses: uniform achieves lower mean loss. However, prompt-level wins are exactly tied (32 vs. 32), and the bootstrap confidence interval again crosses zero. The bootstrap probability that the global plan has lower mean loss is 0.191, indicating that while the point estimate favors uniform, the data do not rule out a global advantage at conventional significance levels.

### 3.3 Memory and Runtime

Peak CUDA allocation was approximately 22.320 GiB for both arms in all benchmarks, confirming that the two pruning plans impose identical memory footprints at inference time. Runtime was comparable across arms within each benchmark.

### 3.4 Test Suite

All source modules compiled successfully. The combined test suite (project tests plus REAP regression tests) yielded 41 passed, 2 warnings. The manual FP8 scoring test suite had 2 passed.

---

## 4. Limitations

1. **Short context window**: All benchmarks used `max_length=64`. Loss at longer context lengths may behave differently, particularly for code-eval tasks where longer completions are typical.

2. **Hand-curated prompts**: The 16-prompt and 64-prompt fixtures were constructed manually rather than drawn from a canonical benchmark suite. The attempt to load HumanEval failed due to a network/cache timeout, and no HumanEval, MBPP, or APPS data was available locally. The hand-curated prompts may not be representative of broader task distributions.

3. **Single model and sparsity level**: Results are specific to Qwen3-Coder-30B-A3B at 25% sparsity. Generalization to other models, architectures, or sparsity levels is not established.

4. **Single hardware configuration**: All runs were conducted on the same GPU with the same CUDA environment. Hardware-dependent effects (e.g., different FP8 behavior across GPU generations) are not captured.

5. **Loss as a proxy for quality**: Prompt loss is an imperfect proxy for downstream task performance. A model with lower loss on short contexts may not generate better completions, especially for code tasks where correctness depends on exact token sequences.

6. **Inconclusive pruning comparison**: The central hypothesis—that non-uniform pruning outperforms uniform pruning—receives neither support nor refutation. The 16-prompt set shows a slight mean-loss advantage for global/ragged but fewer prompt wins; the 64-prompt set shows a slight mean-loss advantage for uniform but tied prompt wins. Both confidence intervals cross zero.

7. **No generation-based evaluation**: The benchmarks measure loss only, not pass@k or functional correctness on code tasks. A complete evaluation would include generation metrics.

8. **Parent 3-prompt results not independently re-analyzed**: The parent 3-prompt smoke test artifacts were copied for reference but were not re-scored or re-analyzed with bootstrap CIs in this branch.

---

## 5. Reproducibility Checklist

- **Model identifier**: Qwen3-Coder-30B-A3B-FP8
- **Pruning sparsity**: 25%
- **Pruning plans**: uniform baseline, global/ragged (REAP non-uniform MoE loader)
- **Scorer source**: `src/manual_fp8_scoring.py`, `src/run_qwen3_manual_fp8_prompt_loss.py`
- **Analysis utility**: `src/analyze_prompt_loss_delta.py`
- **max_length**: 64 (all benchmarks)
- **Bootstrap resamples**: 20,000; seed: 3423677
- **Prompt fixtures**: `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/prompts.json` (16 prompts), `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/prompts.json` (64 prompts)
- **Pruned checkpoints**: Linked from parent project directory (`../source-record-redacted`), approximately 48 GiB per checkpoint
- **Python environment**: Linked `.venv` from parent project
- **REAP checkout**: Patched, at `external/reap/`
- **Test results**: 41 passed, 2 warnings (combined project + REAP suite)
- **Peak CUDA allocation**: ~22.320 GiB (both arms)
- **Decision**: `finalize_positive`; hypothesis status: `mixed`

---

## 6. Conclusion

This benchmark evaluates two 25%-sparsity pruning plans for Qwen3-Coder-30B-A3B-FP8 using a manual FP8/BF16 prompt-loss scorer across prompt sets of size 3, 16, and 64. The scoring mechanism itself is supported: it scales from the minimal smoke test to the 64-prompt fixture without errors, and the paired bootstrap analysis provides interpretable uncertainty quantification.

The pruning-quality comparison between uniform and global/ragged plans is inconclusive. The 16-prompt mixed set shows a marginal mean-loss advantage for global/ragged (Δ = −0.010) but fewer prompt-level wins. The 64-prompt code-eval set reverses the mean-loss sign in favor of uniform (Δ = +0.099) while prompt-level wins are exactly tied. In both cases, bootstrap 95% confidence intervals for the mean delta cross zero, and the probability that global/ragged has lower mean loss ranges from 0.19 to 0.51 depending on the fixture.

These results do not support a strong claim that non-uniform pruning outperforms uniform pruning at 25% sparsity for this model, nor do they provide kill-condition evidence that the global/ragged plan is clearly worse. The appropriate interpretation is that the difference, if it exists, is small relative to the variance observed across prompts, and larger or more targeted evaluation sets would be needed to resolve it.

Future work should prioritize evaluation on canonical code-eval benchmarks (HumanEval, MBPP) with locally cached data, longer context lengths, and generation-based metrics such as pass@k, rather than loss alone. A materially different REAP-observer pruning plan—rather than the current global/ragged allocation—may also warrant separate investigation.

---

## Referenced Artifacts

### Result files
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/summary.md`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/benchmark_summary.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/qwen3_manual_fp8_prompt_loss_report.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/global_plan_prompt_loss.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/uniform_baseline_plan_prompt_loss.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/prompts.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/run_broader_16prompt.log`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/summary.md`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/benchmark_summary.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/qwen3_manual_fp8_prompt_loss_report.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/global_plan_prompt_loss.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/uniform_baseline_plan_prompt_loss.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/prompts.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/run_codeeval64.log`
- `artifacts/parent_qwen3_coder_30b_fp8_manual_prompt_loss_3prompt/qwen3_manual_fp8_prompt_loss_report.json`
- `artifacts/parent_qwen3_coder_30b_fp8_manual_prompt_loss_3prompt/global_plan_prompt_loss.json`
- `artifacts/parent_qwen3_coder_30b_fp8_manual_prompt_loss_3prompt/uniform_baseline_plan_prompt_loss.json`
- `artifacts/parent_qwen3_coder_30b_fp8_manual_prompt_loss_3prompt/run_3prompt.log`

### Source and test files
- `src/manual_fp8_scoring.py`
- `src/run_qwen3_manual_fp8_prompt_loss.py`
- `src/analyze_prompt_loss_delta.py`
- `tests/test_manual_fp8_scoring.py`
- `tests/test_analyze_prompt_loss_delta.py`
- `tests/test_run_qwen3_manual_fp8_prompt_loss.py`

### Project metadata and decision files
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`
- `prompts/initial.md`
- `prompts/resume.md`

### Paper audit artifacts
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
