# Real-Mode Stress Regularization: A Paired Consistency Penalty for Label-Invariant Stress Robustness in Controller Decisions

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, benchmark outputs, claim ledger, evidence bundle). The operator who released this artifact claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate Real-Mode Stress Regularization (RMSR), a consistency penalty that encourages a controller to issue the same decision under clean and stressed operational views without requiring labels on the stressed view. In a 30-seed synthetic benchmark of a binary accept/reject controller facing telemetry dropout, latency spikes, stale confidence bias, heavy-tailed noise, and risk-channel drift, the best RMSR configuration ($\lambda=3.0$) improved stressed-view accuracy by +11.12 percentage points (95% CI [+10.60, +11.64]) and reduced the false-accept rate by −25.92 points (95% CI [−26.92, −24.91]) relative to a clean-only baseline, while preserving clean-mode accuracy (0.9489 vs. 0.9471). RMSR approximately matched the supervised stress-augmentation upper bound (stressed accuracy 0.8822 vs. 0.8814) despite using no stress labels. These results are limited to a synthetic logistic controller under the assumption that stress does not change the correct decision. We do not claim production robustness.

## 1. Introduction

Controllers operating in real deployment modes frequently encounter stressed observations: missing telemetry channels, latency-induced staleness, heavy-tailed sensor noise, and risk-channel drift. A controller trained only on clean observations may flip its decision under such stress, producing unsafe accept/reject outcomes.

A natural remedy is supervised stress augmentation—training on labeled stressed views alongside clean ones. However, in operational settings, stress labels are often unavailable or expensive to obtain, while paired clean/stress observation traces may be readily collected from deployment logs.

We propose Real-Mode Stress Regularization (RMSR): a penalty on the squared disagreement between the controller's clean and stressed predictions, trained using only clean labels plus paired stressed views. The key assumption is that the correct decision is invariant under the stress perturbation for the cases considered.

This paper reports a mechanism-level evaluation of RMSR on a synthetic binary controller benchmark across 30 random seeds. We compare RMSR against both a clean-only baseline and a supervised stress-augmentation upper bound. We report positive local results with tight confidence intervals, and we explicitly delineate the boundary conditions under which RMSR is and is not safe to apply.

RMSR is conceptually related to consistency regularization methods in semi-supervised learning and prediction-smoothness regularization under perturbation. It differs from generic data augmentation by using paired operational stress views—telemetry dropout, latency spikes, stale confidence, and risk drift—as the perturbation family, and by requiring only clean labels plus paired observations rather than labels on the stressed views.

## 2. Method

### 2.1 Problem Setting

We consider a binary controller that maps a feature vector $z$ to an accept/reject decision via logistic parameters $w$. For each latent case, we observe:

- A clean view $z_c$ drawn from the nominal feature distribution.
- A stressed view $z_s$ produced by applying a real-mode stress transformation to $z_c$, incorporating: missing telemetry (feature dropout), heavy-tailed additive noise, latency spike scaling, stale confidence bias, and risk-channel drift.
- A label $y \in \{0, 1\}$ that is invariant under the stress transformation in the primary test setting.

### 2.2 Training Objectives

**Clean-only baseline.** Standard logistic regression on clean views:

$$\mathcal{L}_{\text{clean}} = \text{CE}(y, \sigma(w^T z_c)) + \gamma \|w\|^2$$

**Supervised stress augmentation (upper bound).** Uses labels on both views:

$$\mathcal{L}_{\text{sup}} = \text{CE}(y, \sigma(w^T z_c)) + \text{CE}(y, \sigma(w^T z_s)) + \gamma \|w\|^2$$

This is an upper-bound comparison because it requires stress labels that RMSR explicitly avoids.

**Real-Mode Stress Regularization (RMSR).** Uses clean labels plus a paired consistency penalty:

$$\mathcal{L}_{\text{RMSR}} = \text{CE}(y, \sigma(w^T z_c)) + \lambda \left(\sigma(w^T z_c) - \sigma(w^T z_s)\right)^2 + \gamma \|w\|^2$$

The penalty encourages the controller to issue the same predicted probability under clean and stressed views, without requiring the stress label. The strength $\lambda$ controls the trade-off between clean-label fit and stress consistency.

### 2.3 Stress Transformation

The real-mode stress transformation applied to each clean feature vector includes five components:

1. **Telemetry dropout:** Random feature masking simulating missing sensor channels.
2. **Heavy-tailed noise:** Additive noise drawn from distributions with heavier tails than Gaussian.
3. **Latency spikes:** Multiplicative scaling of time-sensitive features.
4. **Stale confidence bias:** Additive shift toward prior predictions, simulating stale cached confidence.
5. **Risk-channel drift:** Systematic shift in risk-related feature channels.

The transformation is deterministic given the random seed, ensuring reproducible paired views.

### 2.4 Evaluation Metrics

- **Clean accuracy:** Accuracy on clean test views.
- **Stressed accuracy:** Accuracy on stressed test views (higher is better).
- **False-accept rate:** Proportion of negative cases accepted under stress (lower is better).
- **Flip rate:** Proportion of cases where the clean and stressed decisions disagree.

### 2.5 Experimental Protocol

The experiment was implemented as a pure NumPy logistic trainer with synthetic data generation. A smoke test (single seed) was run and passed before the main experiment. The main result uses 30 seeds (seeds 0–29), with all seeds explicitly specified on the command line. Paired confidence intervals are computed across seeds, comparing each RMSR configuration to the clean-only baseline on the same seed.

## 3. Results

### 3.1 Main Comparison (30 Seeds)

| Method | Clean Acc. | Stressed Acc. | Δ Stressed Acc. | False-Accept | Δ False-Accept | Flip Rate |
|---|---:|---:|---:|---:|---:|---:|
| clean_only | 0.9471 | 0.7710 | — | 0.3734 | — | 0.2282 |
| stress_supervised_aug | 0.9489 | 0.8814 | +0.1104 | 0.1178 | −0.2557 | 0.1125 |
| rmsr_0.25 | 0.9489 | 0.8613 | +0.0902 | 0.1467 | −0.2267 | 0.1352 |
| rmsr_0.75 | 0.9496 | 0.8782 | +0.1072 | 0.1221 | −0.2513 | 0.1164 |
| rmsr_1.50 | 0.9494 | 0.8811 | +0.1101 | 0.1171 | −0.2563 | 0.1125 |
| rmsr_3.00 | 0.9489 | 0.8822 | +0.1112 | 0.1143 | −0.2592 | 0.1108 |

All deltas are computed relative to the clean-only baseline within each seed.

### 3.2 Paired Confidence Intervals

For the best RMSR configuration ($\lambda=3.0$) versus clean-only, 95% paired confidence intervals:

- **Stressed accuracy delta:** +0.1112, CI [+0.1060, +0.1164]
- **False-accept delta:** −0.2592, CI [−0.2692, −0.2491]

The intervals exclude zero by a wide margin, confirming that the improvement is not a sampling artifact at this benchmark scale.

### 3.3 Clean-Mode Accuracy Preservation

A critical concern is whether stress regularization degrades clean-mode performance. No such collapse was observed:

- Clean-only baseline: 0.9471
- Best RMSR ($\lambda=3.0$): 0.9489

The difference is negligible and slightly favorable to RMSR, suggesting the consistency penalty does not interfere with clean-label learning at the tested $\lambda$ values.

### 3.4 RMSR vs. Supervised Upper Bound

RMSR at $\lambda=3.0$ achieved stressed accuracy of 0.8822, marginally exceeding the supervised stress-augmentation upper bound of 0.8814. This difference is within noise and should not be interpreted as RMSR outperforming supervised augmentation; rather, RMSR approximately matches the upper bound in this benchmark while requiring no stress labels.

### 3.5 Sensitivity to $\lambda$

Increasing $\lambda$ from 0.25 to 3.0 monotonically improved stressed accuracy and reduced the false-accept rate, with diminishing returns above $\lambda=1.50$. Clean accuracy remained stable across all settings. No regularization-induced degradation was observed at $\lambda=3.0$, though higher values were not tested and may exhibit different behavior.

## 4. Limitations

1. **Synthetic benchmark only.** The controller, feature distribution, and stress transformation are synthetic. This validates mechanism plausibility, not production effect size. Real controller traces may exhibit stress patterns not captured here.

2. **Label-invariance assumption.** RMSR assumes that the correct decision is the same under clean and stressed views. If real-mode stress changes the true operational label (e.g., a genuinely different risk profile under degraded telemetry), a consistency-only objective can be unsafe. In such cases, stress labels or a different objective (e.g., distributionally robust optimization) is required.

3. **Linear controller only.** Only a logistic (linear) controller was tested. No deep controller, LLM endpoint, or non-linear model was evaluated. The behavior of RMSR with high-capacity function approximators is unknown from these experiments.

4. **No formal robustness guarantee.** RMSR is an empirical regularization technique. No formal proof of robustness to bounded perturbations or distributional shift is provided.

5. **Single stress family.** The five-component stress transformation is one specific perturbation family. Generalization to qualitatively different stress types (adversarial perturbations, distributional shift in the label marginal, etc.) is not tested.

6. **No semantic-shift evaluation.** Cases where stress changes the correct action were explicitly excluded from the benchmark. RMSR's behavior under semantic shift is untested and potentially dangerous.

## 5. Reproducibility Checklist

- **Code availability:** Implementation in `src/rmsr_experiment.py` (synthetic benchmark and NumPy logistic trainer) and `src/analyze_rmsr.py` (summary tables and paired CI analysis). Both files passed `python3 -m py_compile` syntax checks.
- **Random seeds:** 30 seeds (0–29) used for the main result. Seed list explicitly specified on the command line.
- **Environment:** Python 3.12.3, NumPy 2.4.4, SciPy 1.17.1, scikit-learn 1.8.0, pandas 3.0.2, Linux 6.17.0-1014-nvidia-aarch64, glibc 2.39.
- **Hardware:** ~122 GB available memory; experiment peak RSS < 50 MB; swap disabled. No GPU required.
- **Runtime:** 30-seed run completed in 12.34s wall time, 99.09s user time, ~803% CPU utilization, 46,416 KB max RSS.
- **Smoke test:** Passed before main run (`results/rmsr_smoke/smoke_results.json`).
- **Determinism:** Stress transformation is seed-deterministic. Logistic training uses fixed optimization parameters.
- **Metrics artifacts:** Raw results in `results/rmsr_main_30seed/main_results.json`; analysis in `results/rmsr_main_30seed/analysis/decision_table.json` and `results/rmsr_main_30seed/analysis/summary.md`.

## 6. Conclusion

Real-Mode Stress Regularization is a locally viable mechanism for improving controller robustness to operational stress when paired clean/stress views are available and the correct decision is label-invariant under stress. In a 30-seed synthetic benchmark, RMSR at $\lambda=3.0$ improved stressed accuracy by +11.12 percentage points and reduced the false-accept rate by −25.92 points relative to a clean-only baseline, with tight paired confidence intervals and no degradation in clean-mode accuracy. RMSR approximately matched a supervised stress-augmentation upper bound while requiring no stress labels.

These results establish mechanism plausibility only. Before any deployment claim, RMSR must be evaluated on real controller traces with held-out stress labels, tested with non-linear controllers, and explicitly probed on semantic-shift cases where stress changes the correct action. The label-invariance assumption is the central safety boundary of this method: outside that boundary, consistency regularization alone is insufficient and potentially harmful.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Implementation (experiment) | `src/rmsr_experiment.py` |
| Implementation (analysis) | `src/analyze_rmsr.py` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Environment log | `logs/env.log` |
| Smoke test log | `logs/smoke.log` |
| 10-seed run log | `logs/main.log` |
| 10-seed analysis log | `logs/analyze_main.log` |
| 30-seed run log | `logs/main_30seed.log` |
| 30-seed analysis log | `logs/analyze_30seed.log` |
| Smoke results | `results/rmsr_smoke/smoke_results.json` |
| 10-seed results | `results/rmsr_main/main_results.json` |
| 10-seed decision table | `results/rmsr_main/analysis/decision_table.json` |
| 10-seed summary | `results/rmsr_main/analysis/summary.md` |
| 30-seed results | `results/rmsr_main_30seed/main_results.json` |
| 30-seed decision table | `results/rmsr_main_30seed/analysis/decision_table.json` |
| 30-seed summary | `results/rmsr_main_30seed/analysis/summary.md` |
| Claim ledger | `papers/source-record-redacted-20260501T215448674289+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T215448674289+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T215448674289+0000/paper_manifest.json` |
