# Benchmark Qwen3 Non-Uniform REAP Manual-FP8 Scoring: An Inconclusive Result on Global Pruning Quality

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its conclusions.

---

## Abstract

We evaluate whether non-uniform (global/ragged) REAP pruning with manual FP8/BF16 scoring yields lower prompt-level loss than uniform baseline pruning on Qwen3-Coder-30B-A3B. Two benchmark suites were executed: a 16-prompt mixed-topic slice and a 64-prompt code-evaluation fixture. In the 16-prompt suite, global/ragged pruning produced a mean loss of 10.892 versus uniform 10.902 (Δ = −0.0098), but the paired bootstrap confidence interval crossed zero. In the 64-prompt code-evaluation suite, global/ragged pruning produced a mean loss of 11.189 versus uniform 11.090 (Δ = +0.0992), again with a bootstrap 95% CI spanning zero (CI: [−0.119, +0.323]). The probability that global pruning yields lower loss was 0.191, and per-prompt wins were tied at 32/32. We conclude that the manual FP8/BF16 scoring pipeline is functional and reproducible, but the hypothesis that non-uniform global pruning improves prompt-level loss quality is not supported by the observed evidence. The result is mixed and inconclusive rather than a decisive win for either pruning strategy.

## 1. Introduction

Mixture-of-experts (MoE) models such as Qwen3-Coder-30B-A3B activate only a subset of expert parameters per token, creating an opportunity for non-uniform pruning strategies that exploit the heterogeneous importance of different experts. The REAP (Routed Expert Activation Pruning) framework provides a mechanism for scoring and pruning experts based on activation patterns, with the option to apply either uniform pruning (the same fraction removed across all layers) or global/ragged pruning (non-uniform removal rates per layer based on estimated importance).

The central hypothesis under test is whether global/ragged pruning—where the pruning budget is allocated non-uniformly across layers according to per-layer importance scores—produces lower prompt-level loss than uniform baseline pruning when applied to Qwen3-Coder-30B-A3B under manual FP8/BF16 scoring. A secondary objective is to validate that the manual FP8/BF16 scoring pipeline itself functions correctly and produces reproducible loss measurements.

This report documents a mixed and inconclusive result. The scoring pipeline is verified, but the quality advantage of non-uniform pruning is not established at conventional significance thresholds.

## 2. Method

### 2.1 Model and Pruning Framework

The target model is Qwen3-Coder-30B-A3B, a mixture-of-experts architecture. Pruning is performed via the REAP framework, which supports two pruning strategies:

- **Uniform baseline pruning**: A fixed pruning fraction is applied identically across all MoE layers.
- **Global/ragged pruning**: The total pruning budget is distributed non-uniformly across layers based on per-layer importance scores derived from activation statistics, allowing some layers to retain more experts while others are pruned more aggressively.

### 2.2 Manual FP8/BF16 Scoring Pipeline

The scoring pipeline (`src/manual_fp8_scoring.py`, `src/run_qwen3_manual_fp8_prompt_loss.py`, `src/analyze_prompt_loss_delta.py`) computes per-prompt cross-entropy loss under each pruning strategy. The pipeline loads the model with the specified pruning plan (global or uniform), runs forward passes on each prompt, and records the resulting loss values. Loss deltas between the two strategies are then analyzed via paired bootstrap resampling.

### 2.3 Benchmark Suites

Two benchmark suites were executed:

1. **16-prompt mixed-topic slice** (`artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/`): A set of 16 prompts spanning diverse topics, intended to capture general pruning quality effects.

2. **64-prompt code-evaluation fixture** (`artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/`): A set of 64 code-generation prompts, intended to stress-test pruning quality in a domain-specific setting.

A smaller 3-prompt parent fixture (`artifacts/parent_qwen3_coder_30b_fp8_manual_prompt_loss_3prompt/`) was also retained from the predecessor branch for traceability.

### 2.4 Statistical Analysis

Per-prompt loss values under global and uniform pruning were compared using paired bootstrap resampling with 95% confidence intervals. The probability that global pruning yields lower loss was estimated from the bootstrap distribution. Per-prompt win counts (global lower vs. uniform lower) were also recorded.

## 3. Results

### 3.1 16-Prompt Mixed-Topic Slice

| Metric | Global/Ragged | Uniform Baseline | Delta |
|--------|--------------|-----------------|-------|
| Mean loss | 10.8924 | 10.9023 | −0.0098 |

The observed delta favors global/ragged pruning by approximately 0.01 nats, but the paired bootstrap confidence interval crosses zero, indicating that this difference is not statistically distinguishable from noise at the 95% level.

### 3.2 64-Prompt Code-Evaluation Fixture

| Metric | Global/Ragged | Uniform Baseline | Delta |
|--------|--------------|-----------------|-------|
| Mean loss | 11.1893 | 11.0901 | +0.0992 |
| Paired bootstrap 95% CI | — | — | [−0.1190, +0.3234] |
| P(global lower) | — | — | 0.191 |
| Per-prompt wins (global/uniform) | — | — | 32/32 (tied) |

In the code-evaluation fixture, the direction reverses: uniform baseline pruning yields numerically lower mean loss. However, the bootstrap 95% CI again spans zero, and the per-prompt win count is exactly tied at 32/32. The estimated probability that global pruning yields lower loss is 0.191, well below any conventional significance threshold.

### 3.3 Pipeline Verification

The benchmark code was verified via:

- Successful compilation of all three source modules (`src/run_qwen3_manual_fp8_prompt_loss.py`, `src/analyze_prompt_loss_delta.py`, `src/manual_fp8_scoring.py`).
- Passage of the full test suite: `41 passed, 2 warnings` across `tests/` and `external/reap/tests/test_non_uniform_moe_loader.py`.

No vLLM, SGLang, or scorer process was found running from this project directory at verification time.

### 3.4 Summary of Findings

The manual FP8/BF16 scoring pipeline is functional and reproducible. The hypothesis that non-uniform global pruning improves prompt-level loss over uniform baseline pruning is not supported. In the 16-prompt suite, the point estimate slightly favors global pruning but is statistically indistinguishable from zero. In the 64-prompt suite, the point estimate slightly favors uniform pruning, again statistically indistinguishable from zero. The overall result is mixed and inconclusive.

## 4. Limitations

1. **Single model architecture**: Results are limited to Qwen3-Coder-30B-A3B. Generalization to other MoE architectures or dense models is not established.

2. **Prompt set size and coverage**: The largest suite contains 64 prompts. This may be insufficient to detect small but real effects, particularly if pruning quality effects are prompt-dependent and highly variable.

3. **Loss as sole quality metric**: Only cross-entropy loss was measured. Downstream task performance (e.g., code generation accuracy on HumanEval/MBPP) was not evaluated. Loss differences that are statistically indistinguishable at current sample sizes could still correspond to meaningful downstream differences—or not.

4. **Artifact provenance**: The benchmark artifacts were copied from a predecessor project branch rather than freshly generated in this run. While the code was re-verified (compilation and test passage), the loss measurements themselves were not independently re-executed on this branch due to the computational cost of re-running the Qwen3 scorer.

5. **Bootstrap CI interpretation**: Bootstrap confidence intervals that cross zero do not prove the absence of an effect; they indicate that the observed data do not provide sufficient evidence to reject the null hypothesis at the stated confidence level.

6. **No external replication**: These results have not been independently replicated on different hardware, software versions, or random seeds beyond what is documented in the project artifacts.

7. **Pruning hyperparameters**: The specific pruning fractions and global budget allocation strategy are those encoded in the REAP configuration used. Sensitivity of results to these hyperparameters was not systematically explored.

## 5. Reproducibility Checklist

| Item | Status | Detail |
|------|--------|--------|
| Code available | Yes | `src/run_qwen3_manual_fp8_prompt_loss.py`, `src/analyze_prompt_loss_delta.py`, `src/manual_fp8_scoring.py` |
| Tests passing | Yes | 41 passed, 2 warnings |
| Model specified | Yes | Qwen3-Coder-30B-A3B |
| Pruning strategies specified | Yes | Uniform baseline and global/ragged (non-uniform) |
| Prompt sets documented | Yes | 16-prompt mixed slice, 64-prompt code-eval fixture, 3-prompt parent fixture |
| Loss values per-prompt | Yes | Stored in `global_plan_prompt_loss.json` and `uniform_baseline_plan_prompt_loss.json` for each suite |
| Statistical method specified | Yes | Paired bootstrap resampling, 95% CI |
| Random seed documented | Not recorded in available artifacts | |
| Hardware specified | Not recorded in available artifacts | |
| Software versions pinned | Partial | `.venv` linked to parent environment; exact package versions not in artifacts |
| Independent re-execution on this branch | No | Artifacts reused from predecessor branch; scorer not re-run due to compute cost |

## 6. Conclusion

We evaluated non-uniform (global/ragged) REAP pruning against uniform baseline pruning on Qwen3-Coder-30B-A3B using a manual FP8/BF16 scoring pipeline across two benchmark suites totaling 80 prompts. The scoring pipeline is verified and reproducible. However, the central hypothesis—that non-uniform pruning allocation improves prompt-level loss—is not supported by the observed evidence. The 16-prompt suite shows a negligible point estimate favoring global pruning (Δ = −0.010) with a CI crossing zero. The 64-prompt suite shows a point estimate favoring uniform pruning (Δ = +0.099) with a CI crossing zero and exactly tied per-prompt win counts. The result is mixed and inconclusive.

These findings do not rule out a real effect of non-uniform pruning; they indicate that any such effect, if present, is smaller than the measurement noise at the current sample size. Future work should consider substantially larger prompt sets, downstream task evaluation (e.g., HumanEval/MBPP pass rates), systematic hyperparameter sweeps over pruning budgets, and replication across additional MoE architectures.

---

## Referenced Artifacts

### Project decision and metadata
- `.omx/project_decision.json` — Final project decision (finalize_positive, hypothesis: mixed)
- `.omx/metrics.json` — Session metrics
- `run_notes.md` — Dated run notes with acquisition and verification log

### Source code
- `src/run_qwen3_manual_fp8_prompt_loss.py`
- `src/analyze_prompt_loss_delta.py`
- `src/manual_fp8_scoring.py`

### Tests
- `tests/test_run_qwen3_manual_fp8_prompt_loss.py`
- `tests/test_analyze_prompt_loss_delta.py`
- `tests/test_manual_fp8_scoring.py`
- `external/reap/tests/test_non_uniform_moe_loader.py`

### 16-prompt mixed-topic suite
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/summary.md`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/benchmark_summary.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/qwen3_manual_fp8_prompt_loss_report.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/global_plan_prompt_loss.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/uniform_baseline_plan_prompt_loss.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/prompts.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_broader/run_broader_16prompt.log`

### 64-prompt code-evaluation suite
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/summary.md`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/benchmark_summary.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/qwen3_manual_fp8_prompt_loss_report.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/global_plan_prompt_loss.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/uniform_baseline_plan_prompt_loss.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/prompts.json`
- `artifacts/qwen3_coder_30b_fp8_manual_prompt_loss_codeeval64/run_codeeval64.log`

### 3-prompt parent fixture
- `artifacts/parent_qwen3_coder_30b_fp8_manual_prompt_loss_3prompt/qwen3_manual_fp8_prompt_loss_report.json`
- `artifacts/parent_qwen3_coder_30b_fp8_manual_prompt_loss_3prompt/global_plan_prompt_loss.json`
- `artifacts/parent_qwen3_coder_30b_fp8_manual_prompt_loss_3prompt/uniform_baseline_plan_prompt_loss.json`
- `artifacts/parent_qwen3_coder_30b_fp8_manual_prompt_loss_3prompt/run_3prompt.log`

### Paper audit artifacts
- `papers/.../claim_ledger.json` — Claim audit with confidence levels and forbidden wordings
- `papers/.../evidence_bundle.json` — Full evidence bundle with decision, run notes, and file manifest
- `papers/.../publication_manifest.json` — Publication manifest
