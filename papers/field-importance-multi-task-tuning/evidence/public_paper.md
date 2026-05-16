# Field Importance Multi-Task Tuning: Field-Selective Regularization from Calibration Correlations

> **AI Provenance Notice.** This draft was generated entirely by an automated research pipeline from prototype artifacts (run notes, claim ledger, benchmark metrics, and decision JSON). No human claims authorship of the writing or the experimental results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer endorsement is implied.

---

## Abstract

We investigate whether a simple field-importance signal, derived from calibration-set correlations, can improve multi-task generalization when several related regression targets depend on a sparse subset of input fields. We propose Field Importance Tuning (FIT): estimate per-field importance as the mean absolute Pearson correlation across tasks on labeled calibration data, then assign field-specific ridge penalties inversely proportional to importance, so that low-importance fields receive stronger shrinkage. On a synthetic benchmark with 4 tasks, 80 candidate fields, and 14 truly active fields, FIT reduces held-out MSE by 34.7% relative to uniform ridge regularization over 120 random seeds (paired 95% CI on MSE difference: [−1.019, −0.959]). A randomized-importance control that applies the same heterogeneous penalty distribution but with shuffled field assignments worsens MSE by 8.1% versus baseline, confirming that gains depend on meaningful field rankings rather than arbitrary penalty heterogeneity. However, FIT's benefit is not universal: when most fields are genuinely active (dense control), the relative improvement shrinks to −0.7% with a confidence interval that includes zero; when training data are abundant (512 samples), the improvement shrinks to −5.2%. These results establish FIT as effective in sparse-field, scarce-data regimes but highlight clear boundary conditions where the method offers negligible or uncertain benefit.

## Introduction

Multi-task learning often assumes that shared representations benefit related tasks, but when input dimensionality is high and only a sparse subset of fields drives the shared signal, uniform regularization can under-penalize nuisance fields or over-penalize informative ones. The core question motivating this work is whether a cheap, data-driven field-importance estimate can guide task-specific regularization to improve generalization.

We study a minimal instantiation of this problem: multi-output ridge regression where the penalty coefficient varies per field rather than being globally uniform. Field importance is estimated from calibration data using mean absolute Pearson correlation across tasks—a deliberately simple, non-iterative signal. The resulting method, Field Importance Tuning (FIT), requires no architecture changes, no gradient-based hyperparameter search, and no held-out validation beyond the calibration split already used for model selection.

A critical concern is whether any heterogeneous penalty scheme would produce similar gains, rendering the importance ranking irrelevant. To address this, we include a randomized-importance control that applies the same distribution of penalty values but randomly shuffled across fields. If heterogeneous penalties alone sufficed, this control would match or approach FIT's performance.

We evaluate FIT against a uniform-ridge baseline and the randomized-importance control across four experimental conditions that systematically vary field sparsity and data abundance. The results show a strong but conditional benefit: FIT is effective when the true generative structure is sparse and data are scarce, but its advantage collapses or diminishes when either assumption is relaxed.

## Method

### Problem Setting

We consider $T$ regression tasks sharing an input space of $F$ fields. Training data $\{(x_i, y_i)\}_{i=1}^{N_{\text{train}}}$ and calibration data $\{(x_j, y_j)\}_{j=1}^{N_{\text{cal}}}$ are drawn i.i.d. from the same distribution. The target vector $y \in \mathbb{R}^T$ is generated from a sparse subset of the $F$ fields.

### Uniform Baseline

Multi-output ridge regression with a single global regularization strength $\alpha$, selected to minimize calibration-set MSE:

$$\hat{W} = \arg\min_W \|Y_{\text{train}} - X_{\text{train}} W\|^2 + \alpha \|W\|_F^2$$

$\alpha$ is selected from a grid via calibration-set performance.

### Field Importance Tuning (FIT)

1. **Estimate field importance.** For each field $f$ and task $t$, compute the Pearson correlation $r_{f,t}$ between field $f$ and task $t$ on the combined train and calibration data. Define field importance as:

$$\text{imp}_f = \frac{1}{T} \sum_{t=1}^{T} |r_{f,t}|$$

2. **Map importance to field-specific penalties.** Assign each field a penalty weight inversely related to its importance. Fields with low importance receive stronger shrinkage; fields with high importance receive weaker shrinkage. A global scaling parameter $\alpha$ is still selected on the calibration split, controlling overall regularization strength.

3. **Solve field-weighted ridge.** The penalty term becomes $\sum_f \lambda_f \|w_f\|^2$ where $\lambda_f$ is inversely proportional to $\text{imp}_f$, normalized so that a global $\alpha$ controls overall strength.

### Randomized-Importance Control

Same penalty distribution $\{\lambda_f\}$ as FIT, but the mapping from penalty values to fields is randomly shuffled. This controls for the possibility that any heterogeneous penalty scheme—not one aligned with true field importance—explains the observed gains.

### Synthetic Benchmark

The benchmark is implemented in `scripts/fit_experiment.py` with the following default parameters:

- **Tasks:** $T = 4$ related regression tasks.
- **Fields:** $F = 80$ candidate input fields.
- **Sparse causal structure:** 2 fields shared by all tasks plus 3 task-specific fields per task, yielding 14 truly active fields out of 80.
- **Data:** $N_{\text{train}} = 96$, $N_{\text{cal}} = 96$ (scarce default); test set evaluated separately.
- **Evaluation metrics:** Held-out test MSE (primary), test $R^2$, FIT win rate over seeds, paired MSE difference 95% CI, and precision@$k$ for recovering the true active fields.

### Experimental Conditions

Four conditions isolate the effect of sparsity and data abundance:

1. **Main sparse/scarce:** Default parameters (14/80 active fields, 96 train + 96 calibration), 120 seeds.
2. **Dense-field control:** 20 active fields per task (most fields genuinely active), 120 seeds.
3. **More-data sparse control:** Default sparsity but $N_{\text{train}} = 512$, $N_{\text{cal}} = 512$, 120 seeds.
4. **Smoke sparse:** 3 seeds only, used for pipeline validation before full runs.

## Results

### Main Sparse/Scarce Condition

Over 120 random seeds, FIT substantially outperforms the uniform baseline:

| Metric | Uniform Baseline | FIT | Random Control |
|---|---:|---:|---:|
| Test MSE (mean) | 2.8384 | 1.8496 | 3.0658 |
| Test $R^2$ (mean) | 0.6023 | 0.7405 | — |
| Relative MSE change vs. baseline | — | −34.67% | +8.07% |
| FIT win rate over baseline | — | 120/120 | — |
| Paired MSE diff 95% CI | — | [−1.019, −0.959] | — |
| Precision@$k$ for active fields | — | 0.8137 | — |

FIT wins over the baseline in all 120 seeds. The paired confidence interval excludes zero by a wide margin. The randomized-importance control performs *worse* than the uniform baseline (+8.07% MSE), confirming that the gain requires the importance ranking to be informative, not merely that penalties be heterogeneous.

### Dense-Field Control

When 20 fields per task are active (making most fields genuinely relevant), FIT's advantage collapses:

| Metric | Value |
|---|---:|
| Baseline test MSE | 4.3174 |
| FIT test MSE | 4.2816 |
| Relative MSE change | −0.71% |
| FIT win rate | 70/120 |
| Paired MSE diff 95% CI | [−0.0724, 0.0007] |

The confidence interval includes zero. FIT is not reliably beneficial when the field sparsity assumption is violated. The 70/120 win rate is only marginally above chance, consistent with a near-null effect.

### More-Data Sparse Control

With 512 training and 512 calibration samples (same 14/80 sparsity), FIT still wins consistently but the magnitude shrinks:

| Metric | Value |
|---|---:|
| Baseline test MSE | 1.2100 |
| FIT test MSE | 1.1468 |
| Relative MSE change | −5.21% |
| FIT win rate | 120/120 |
| Paired MSE diff 95% CI | [−0.0655, −0.0608] |

The benefit remains statistically significant but is much smaller than in the scarce-data regime, consistent with the interpretation that FIT's primary value is mitigating overfitting to nuisance fields when data are limited.

### Resource Profile

The workload is CPU-bound closed-form linear algebra. GPU remained idle throughout by design. Maximum resident set size was approximately 44–45 MiB. No swap was used (confirmed via `/usr/bin/time -v` reporting Swaps: 0). Available memory remained above 122 GiB throughout all runs.

## Limitations

1. **Synthetic data only.** All evidence comes from a controlled synthetic benchmark. No real-world or domain-specific dataset was tested. The extent to which real tabular multi-task problems exhibit the sparse-field structure assumed here remains unknown.

2. **Linear models only.** FIT is implemented as field-weighted ridge regression. Whether the same importance signal improves neural multi-task architectures, classification losses, or non-linear feature encodings is untested.

3. **Calibration-set dependency.** Field importance is estimated from labeled calibration data. Production deployment requires a comparable labeled calibration set or an alternative source of field priors (e.g., domain expertise, unsupervised signals).

4. **Dense-field boundary.** FIT provides negligible and statistically uncertain benefit when most fields are genuinely active. The method is not universally helpful; its value is conditional on the sparsity assumption holding.

5. **Inaccessible project page.** The Notion project page returned HTTP 404 from the execution environment, so any additional requirements or context documented there could not be incorporated.

6. **Global importance only.** Field importance is averaged across all tasks. Task-specific importance rankings, which might better capture fields that are informative for some tasks but not others, were not evaluated.

7. **Single importance estimator.** Only mean absolute Pearson correlation was tested as the importance signal. Other estimators (mutual information, partial correlation, model-based feature importance) remain unexplored.

## Reproducibility Checklist

- **Code available:** `scripts/fit_experiment.py` (included in project artifacts).
- **Random seeds:** 120 seeds per condition; script accepts `--seeds` argument for full control.
- **Machine-readable metrics:** `results/metrics/fit_full_latest.json`, `results/metrics/fit_dense_control_latest.json`, `results/metrics/fit_more_data_control_latest.json`, `results/metrics/fit_smoke_latest.json`.
- **Execution logs:** `results/logs/full_120.log`, `results/logs/dense_control_120.log`, `results/logs/more_data_control_120.log`, `results/logs/smoke.log`.
- **Resource monitoring:** `/usr/bin/time -v` output captured in logs; `nvidia-smi` telemetry captured; swap disabled and confirmed unused (Swaps: 0); max RSS approximately 45 MiB.
- **Hyperparameters:** All defaults are explicit in the script and logged. Dense control uses `--active-per-task 20`; more-data control uses `--n-train 512 --n-val 512`.
- **Statistical protocol:** Paired comparisons across seeds; approximate 95% confidence intervals on paired MSE differences; win rates reported directly without adjustment.
- **Controls:** Randomized-importance control built into the experiment script; dense-field and more-data conditions serve as additional boundary controls.
- **Pipeline validation:** Smoke test (3 seeds) completed and passed before full runs.

## Conclusion

Field Importance Tuning—assigning field-specific ridge penalties inversely proportional to calibration-set correlation importance—substantially improves multi-task generalization in a synthetic sparse-field, scarce-data regime (−34.7% MSE, 120/120 seed wins). The randomized-importance control demonstrates that this gain requires meaningful field rankings: shuffling the same penalty distribution across fields worsens performance by 8.1% relative to uniform regularization, ruling out the hypothesis that arbitrary heterogeneous penalties suffice.

However, FIT's benefit is sharply conditional. It shrinks to near-zero when most fields are genuinely active (−0.71% relative MSE, CI includes zero, 70/120 win rate), and it diminishes when training data are abundant (−5.21% relative MSE). These boundary conditions are consistent with the proposed mechanism—FIT selectively protects against overfitting to nuisance fields—and they delimit the regime where the method is useful.

The evidence supports proceeding to a next-stage prototype on real tabular multi-task data. The concrete priorities are: (1) replicating the baseline/FIT/randomized-control protocol on a real labeled dataset with sufficient fields to make field selection meaningful; (2) evaluating task-specific rather than globally averaged field importances; and (3) testing neural multi-task encoders with feature-wise dropout or weight decay derived from calibration importances.

---

## Referenced Artifacts

| Artifact | Path / Identifier |
|---|---|
| Experiment script | `scripts/fit_experiment.py` |
| Main metrics (sparse/scarce) | `results/metrics/fit_full_latest.json` |
| Smoke test metrics | `results/metrics/fit_smoke_latest.json` |
| Dense-field control metrics | `results/metrics/fit_dense_control_latest.json` |
| More-data control metrics | `results/metrics/fit_more_data_control_latest.json` |
| Main run log | `results/logs/full_120.log` |
| Dense control log | `results/logs/dense_control_120.log` |
| More-data control log | `results/logs/more_data_control_120.log` |
| Smoke test log | `results/logs/smoke.log` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Project metadata | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260502T124148768024+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T124148768024+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T124148768024+0000/paper_manifest.json` |
| Project ID | `source-record-redacted` |
| Run ID | `source-record-redacted-20260502T124148768024+0000` |
