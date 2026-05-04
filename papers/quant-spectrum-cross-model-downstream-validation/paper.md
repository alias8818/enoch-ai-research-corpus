# Quantization-Spectrum Cross-Model Downstream Validation: A Diagnostic Harness Study

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by an autonomous research loop. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has verified these claims.

---

## Abstract

We investigate whether post-training quantization-spectrum retention curves—downstream accuracy retention as a function of uniform symmetric weight quantization bit width—exhibit sufficient cross-model agreement to serve as a transferable diagnostic. Using a reproducible local harness on three sklearn classification datasets (digits, wine, breast cancer) and three model classes (L2 logistic regression, linear SVC, MLP with 64 hidden units), we sweep quantization from 32-bit to 2-bit and measure held-out accuracy and macro-F1 retention across three random seeds. On two of three datasets (digits, breast cancer), cross-model retention curves agree strongly (minimum pairwise Pearson correlation ≥ 0.959), consistent with a shared task-level quantization sensitivity signal. However, on the small wine dataset, cross-model agreement collapses (mean pairwise correlation −0.221, minimum −0.782), driven by flat or improving low-bit retention in some model classes. Furthermore, 4-bit quantization does not universally preserve ≥99% accuracy retention; the digits/linear-SVC combination requires 6 bits, while other combinations tolerate 2–3 bits. We conclude that quantization-spectrum retention is a viable and inexpensive downstream diagnostic, but it is not a universal cross-model invariant. Any operational use requires per-task-family calibration and at least spot-checking per model class. These findings are limited to small sklearn models and datasets and do not directly transfer to transformer-scale architectures or modern LLM quantization schemes.

## Introduction

Post-training quantization reduces the numerical precision of learned model weights to decrease memory and compute requirements at inference time. A natural question is whether the relationship between quantization bit width and downstream task performance—the "quantization spectrum"—captures a property of the task itself, independent of the specific model class applied. If quantization-spectrum retention curves were approximately invariant across model classes for a given task, a curve measured on one model could predict degradation on another, enabling cheap proxy evaluation before committing to full re-evaluation.

This work tests the claim that post-training quantization-spectrum retention curves support cross-model downstream validation. We do not assume the claim is true; rather, we design a minimal experiment to expose both supporting and contradicting evidence. The experimental design is intentionally narrow: small sklearn classification tasks, simple model classes, and per-array symmetric uniform quantization applied to learned coefficients. This scope is sufficient to test the structural hypothesis—does cross-model agreement exist?—while being transparent about its distance from production LLM quantization scenarios.

The question is of practical relevance because quantization-spectrum evaluation is cheap. If the spectrum transfers across model classes, it could reduce the computational burden of quantization robustness testing. If it does not transfer reliably, that fact should be established rather than assumed.

## Method

### Datasets

We use three standard sklearn datasets:

- **digits** (10-class, 64 features, 1797 samples): Handwritten digit classification. Split into 1168 train / 629 test.
- **wine** (3-class, 13 features, 178 samples): Wine cultivar classification. Small and relatively easy.
- **breast_cancer** (2-class, 30 features, 569 samples): Binary diagnostic classification.

### Model Classes

Three model classes spanning different inductive biases:

- **logreg_l2**: L2-regularized logistic regression (multi-class via one-vs-rest where applicable).
- **linear_svc**: Linear support vector classifier.
- **mlp_64**: Single-hidden-layer MLP with 64 hidden units and ReLU activation.

### Quantization Scheme

Per-array symmetric uniform quantization is applied to all learned coefficient and intercept tensors after training. For a tensor with values in $[-v_{\max}, v_{\max}]$, the quantized value at bit width $b$ is:

$$q(x) = \mathrm{round}\!\left(\frac{x}{v_{\max}} \cdot (2^{b-1} - 1)\right) \cdot \frac{v_{\max}}{2^{b-1} - 1}$$

Bit widths tested: 32, 16, 8, 6, 4, 3, 2. This scheme does not model per-channel scaling, group quantization, activation quantization, or KV-cache quantization used in modern LLM compression methods.

### Evaluation Protocol

For each (dataset, model, seed, bit-width) combination:

1. Train the model on the training split at full (32-bit) precision.
2. Quantize all learned parameters to the target bit width.
3. Evaluate held-out accuracy and macro-F1 on the test split.
4. Compute retention: $\text{retention} = \text{metric}_{\text{quantized}} / \text{metric}_{\text{baseline}}$.

Seeds: 0, 1, 2. Total: 3 datasets × 3 models × 3 seeds × 7 bit widths = 189 quantized evaluations, plus 27 baseline fits.

### Cross-Model Agreement Metric

For each dataset, we compute pairwise Pearson correlations between the three model classes' mean retention curves (averaged over seeds). We report both the mean and minimum pairwise correlation as indicators of cross-model agreement. High positive correlation indicates that the model classes agree on which bit widths cause degradation; low or negative correlation indicates disagreement.

### Hardware and Environment

- Platform: NVIDIA GB10, aarch64, Linux 6.17.0-1014-nvidia
- Python 3.12.3, scikit-learn, pandas, joblib
- GPU present but idle; this CPU-only sklearn harness did not use GPU acceleration
- Available memory: ~116.78 GiB; memory usage ~4% throughout; swap disabled (intentionally)
- Full grid completed in 1.01 seconds (187.0 eval/s, 26.7 fits/s)

## Results

### Mean Accuracy Retention by Bit Width

| Bit Width | Mean Accuracy Retention |
|----------:|------------------------:|
| 2         | 0.873                   |
| 3         | 0.996                   |
| 4         | 0.997                   |
| 6         | 1.000                   |
| 8         | 1.000                   |
| 16        | 1.000                   |
| 32        | 1.000                   |

Mean retention recovers to ≥99% at 3 bits and above when aggregated across all datasets and models. However, this aggregate masks substantial per-condition variation, as detailed below.

### Minimum Bit Width for ≥99% Accuracy Retention

| Dataset        | Model      | Min Bits (≥99% Ret.) | Retention @ 4-bit | Retention @ 2-bit |
|:--------------|:-----------|---------------------:|------------------:|------------------:|
| breast_cancer | linear_svc | 3                    | 0.998             | 0.948             |
| breast_cancer | logreg_l2  | 3                    | 0.998             | 0.986             |
| breast_cancer | mlp_64     | 3                    | 1.006             | 0.971             |
| digits        | linear_svc | 6                    | 0.983             | 0.343             |
| digits        | logreg_l2  | 4                    | 0.994             | 0.672             |
| digits        | mlp_64     | 3                    | 1.001             | 0.923             |
| wine          | linear_svc | 3                    | 0.995             | 0.984             |
| wine          | logreg_l2  | 2                    | 0.995             | 0.995             |
| wine          | mlp_64     | 2                    | 1.007             | 1.039             |

The digits/linear_svc combination is the most fragile, requiring 6 bits for ≥99% retention and suffering catastrophic degradation at 2 bits. In contrast, wine/logreg_l2 and wine/mlp_64 tolerate 2-bit quantization with no degradation (retention ≥ 0.995), and wine/mlp_64 shows slight improvement at 2 bits (retention 1.039), likely due to regularization-like effects of coarse quantization on an already-easy task.

### Cross-Model Retention Curve Agreement

| Dataset        | Mean Pairwise Correlation | Min Pairwise Correlation |
|:--------------|--------------------------:|-------------------------:|
| breast_cancer | 0.971                     | 0.959                    |
| digits        | 0.999                     | 0.998                    |
| wine          | −0.221                    | −0.782                   |

On digits and breast_cancer, all three model classes produce highly correlated retention curves, consistent with the hypothesis that quantization sensitivity is partially a task-level property. On wine, agreement collapses: the mean pairwise correlation is negative (−0.221), and the worst pair reaches −0.782. This failure mode arises because the wine task is small and easy enough that some models experience flat or even beneficial effects from aggressive quantization, producing non-monotonic or idiosyncratic curves that do not correlate with those of other models.

### Worst-Case Degradation

The three worst individual evaluations (by accuracy retention) all occur on digits/linear_svc at 2-bit quantization:

| Seed | Accuracy | Baseline Accuracy | Accuracy Retention | Accuracy Drop (pp) |
|-----:|---------:|------------------:|-------------------:|-------------------:|
| 1    | 0.267    | 0.955             | 0.280              | 68.8               |
| 2    | 0.312    | 0.944             | 0.330              | 63.3               |
| 0    | 0.397    | 0.948             | 0.419              | 55.0               |

These results confirm that 2-bit quantization is destructively insufficient for some model/task combinations, reducing a 95%+ classifier to near-chance performance on a 10-class task. The degradation is consistent across seeds, indicating it is a structural property of the model/task/bit-width combination rather than a random fluctuation.

### Retention Values Exceeding 1.0

Several conditions show retention slightly above 1.0 (e.g., wine/mlp_64 at 2-bit: 1.039; breast_cancer/mlp_64 at 3-bit: 1.006; digits/mlp_64 at 3-bit: 1.001). This reflects quantization acting as an implicit regularizer on easy or overparameterized tasks, not a measurement error. It complicates the interpretation of retention as a purely monotonic degradation signal and is a genuine feature of the data.

## Limitations

1. **Scale gap.** All models are small sklearn classifiers with tens to hundreds of parameters. The quantization-spectrum behavior of billion-parameter transformers with attention layers, layer normalization, and residual connections may differ qualitatively. These results should not be extrapolated to LLM-scale architectures.

2. **Quantization scheme simplicity.** Per-array symmetric uniform quantization does not reflect modern LLM compression techniques (GPTQ, AWQ, group quantization, activation quantization, KV-cache quantization). The spectrum measured here is a coarse proxy for the degradation patterns seen in production quantization pipelines.

3. **Small/easy task instability.** The wine dataset demonstrates that cross-model agreement can fail on tasks where quantization effects are weak or beneficial. This raises the question of whether the spectrum is informative only when quantization actually degrades performance—a potential tautological limitation of the diagnostic approach.

4. **Dataset diversity.** Three sklearn datasets, while convenient, do not span the diversity of real-world downstream evaluations. Tasks with structured output, generation, or retrieval components are untested.

5. **No activation or runtime quantization.** Only weight tensors are quantized post-training. Runtime quantization effects (e.g., on intermediate activations during inference) are not captured.

6. **Negative correlation as structural failure.** The negative cross-model correlation on wine is a genuine failure of the cross-model invariance claim. We report it without dismissing it as an outlier; it is a structural feature of easy-task regimes that any operational use of this diagnostic must account for.

7. **Retention above 1.0.** The occurrence of retention values exceeding 1.0 in several conditions means that the spectrum is not a pure degradation curve. Any downstream use of the spectrum must handle non-monotonic retention gracefully.

8. **Toy simulation scope.** This study is a toy simulation / harness validation, not a production validation. It validates the harness and triages the hypothesis but does not constitute final proof for any LLM-specific quantization claim.

## Reproducibility Checklist

- **Code available:** `scripts/quant_spectrum_validation.py`
- **Random seeds specified:** 0, 1, 2
- **Datasets specified:** sklearn `digits`, `wine`, `breast_cancer` (standard, version-pinned via scikit-learn)
- **Quantization scheme fully specified:** Per-array symmetric uniform quantization (formula in Method section)
- **Hardware specified:** NVIDIA GB10, aarch64, Linux 6.17.0-1014-nvidia, Python 3.12.3
- **All conditions reported:** Full grid (3 datasets × 3 models × 3 seeds × 7 bit widths); no conditions excluded
- **Negative results reported:** Yes—wine cross-model correlation failure and digits/linear_svc catastrophic degradation are reported in full
- **Raw data available:** `results/quant_spectrum_full/full_results.csv` (189 rows)
- **Summary data available:** `results/quant_spectrum_full/summary_by_curve.csv`, `results/quant_spectrum_full/thresholds.csv`, `results/quant_spectrum_full/summary.json`
- **Environment log available:** `logs/000_environment.log`
- **Execution logs available:** `logs/001_smoke.log`, `logs/002_full_grid.log`, `logs/003_posthoc_summary.log`
- **Smoke test performed:** Yes, passed before full grid execution

## Conclusion

Quantization-spectrum retention curves show strong cross-model agreement on two of three tested datasets (minimum pairwise correlation ≥ 0.959), demonstrating that task-level quantization sensitivity is a real and measurable signal. However, the same curves show complete cross-model disagreement on the wine dataset (mean pairwise correlation −0.221), and 4-bit quantization is not universally safe at ≥99% accuracy retention—the digits/linear_svc combination requires 6 bits.

These mixed results support a scoped conclusion: **quantization-spectrum retention is a viable, inexpensive downstream diagnostic, but it is not a universal cross-model invariant.** Operational use requires calibration per task family and at least spot-checking per model class. The current evidence does not support assuming global transfer of quantization-spectrum properties across model architectures.

Continuation of this line of work would require testing on target model families (e.g., transformer weights) with real downstream evaluation tasks and more realistic quantization schemes. The present study should be treated as harness validation and hypothesis triage, not as final proof for LLM-scale quantization claims.

---

## Referenced Artifacts

| Artifact | Path |
|:---------|:-----|
| Run notes | `run_notes.md` |
| Validation script | `scripts/quant_spectrum_validation.py` |
| Environment log | `logs/000_environment.log` |
| Smoke test log | `logs/001_smoke.log` |
| Full grid log | `logs/002_full_grid.log` |
| Post-hoc summary log | `logs/003_posthoc_summary.log` |
| Raw results | `results/quant_spectrum_full/full_results.csv` |
| Per-curve summary | `results/quant_spectrum_full/summary_by_curve.csv` |
| Bit-threshold table | `results/quant_spectrum_full/thresholds.csv` |
| Cross-model retention correlations | `results/quant_spectrum_full/retention_corr_*.csv` |
| JSON summary | `results/quant_spectrum_full/summary.json` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260501T105148651589+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T105148651589+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T105148651589+0000/paper_manifest.json` |
