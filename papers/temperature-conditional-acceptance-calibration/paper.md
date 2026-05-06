# Temperature-Conditional Acceptance Calibration for Speculative Decoding

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is claimed or implied.

---

## Abstract

Speculative decoding accelerates autoregressive inference by verifying draft tokens against a target model. The acceptance probability α governs the expected draft length and thus throughput, making accurate calibration of α essential for optimal draft-length (γ) selection. We investigate whether acceptance calibration must condition on sampling temperature, or whether a global or draft-feature-only estimate suffices. Using a reproducible synthetic verifier/draft distribution experiment over 6,000 contexts and 7 temperatures (42,000 distribution–temperature cells), we compute exact one-token speculative acceptance and evaluate held-out calibration models. A temperature-conditioned gradient-boosted decision tree achieves RMSE 0.1533 and R² 0.635 on held-out acceptance prediction, an 11.1% RMSE reduction over the best no-temperature baseline (RMSE 0.1725, R² 0.538). Downstream draft-length selection regret improves by 7.7%. Mean acceptance varies substantially across temperatures (0.172 at T = 0.2 to 0.710 at T = 2.2), and the no-temperature calibrator exhibits systematic per-temperature bias that the conditioned model partially corrects. These results are positive but bounded: the experiment uses synthetic paired distributions rather than a live target/draft model pair, R² remains moderate at 0.635, and production deployment requires validation on actual model logits, prompt distributions, and sampler configurations.

## 1. Introduction

Speculative decoding reduces inference latency by proposing multiple tokens from a fast draft model and verifying them in parallel against a target model. The acceptance probability α determines the expected number of accepted tokens per draft sequence and therefore the optimal draft length γ for throughput maximization.

In practice, α is often estimated from draft-model features alone or from a global average, implicitly assuming that the acceptance rate is either invariant to sampling temperature or that temperature's effect is absorbed by other features. However, the exact acceptance formula,

$$\alpha_T = \sum_x \min\bigl(p_T(x),\, q_T(x)\bigr),$$

depends on both the target distribution $p_T$ and the draft distribution $q_T$ at temperature $T$. If temperature changes the overlap $\sum_x \min(p_T, q_T)$ non-uniformly across contexts, then a calibrator that ignores temperature will exhibit systematic bias.

This paper asks: does speculative-decoding acceptance calibration need to condition on sampling temperature, or is a global or draft-feature-only estimate sufficient?

We address this with a controlled synthetic experiment that computes exact acceptance probabilities, fits calibration models with and without temperature conditioning, and evaluates both acceptance prediction accuracy and downstream draft-length selection regret on held-out data. The experiment is intentionally narrow in scope — synthetic distributions, single-token acceptance, no sampler truncation — in order to isolate the temperature effect under exact computation and avoid confounding from Monte Carlo noise or model-specific artifacts.

## 2. Method

### 2.1 Exact Acceptance Computation

For each context and temperature, we compute the exact one-token speculative acceptance probability:

$$\alpha_T = \mathbb{E}_{x \sim q_T}\!\left[\min\!\left(1,\, \frac{p_T(x)}{q_T(x)}\right)\right] = \sum_x \min\!\bigl(p_T(x),\, q_T(x)\bigr).$$

This identity holds exactly for the standard speculative decoding acceptance rule and avoids Monte Carlo variance in the ground-truth labels. The computation is feasible because the synthetic vocabulary is of moderate size (1,024 tokens); this would be costlier but conceptually identical for production vocabularies.

### 2.2 Experimental Design

The experiment is implemented in `scripts/temperature_acceptance_calibration.py` and uses the following configuration:

| Parameter | Value |
|---|---|
| Contexts | 6,000 |
| Vocabulary size | 1,024 |
| Temperatures | [0.2, 0.4, 0.7, 1.0, 1.3, 1.7, 2.2] |
| Total distribution–temperature cells | 42,000 |
| Held-out split | 29,400 train / 12,600 test (grouped by context ID) |
| Empirical accept samples per cell | 32 |
| Wall-clock elapsed | 2.88 s |

Context-level grouping in the train/test split ensures that the held-out evaluation measures generalization to unseen contexts rather than interpolation within known contexts. This is a stricter test than random row-level splitting and better reflects the deployment scenario where the calibrator must generalize to new prompts.

### 2.3 Calibration Models

We compare three calibration strategies:

1. **Global mean baseline.** Predicts the overall mean acceptance rate, ignoring all features. This establishes a floor for calibration quality.
2. **Draft-feature-only (no-temperature) model.** Uses draft-distribution features but withholds temperature as an input. This represents the common practice of conditioning on draft-model statistics alone.
3. **Temperature-conditioned GBDT.** Uses draft-distribution features plus temperature and temperature–feature interactions.

All models are gradient-boosted decision trees. The no-temperature model uses the same architecture with temperature withheld from the feature set, isolating the effect of the temperature signal rather than differences in model capacity.

### 2.4 Evaluation Metrics

- **Acceptance prediction accuracy:** RMSE, MAE, and R² on held-out α values.
- **Downstream regret:** Draft-length (γ) selection regret under a simple throughput proxy, measuring the cost of choosing a suboptimal γ due to miscalibrated α. This metric captures the operational consequence of calibration error rather than prediction accuracy alone.

## 3. Results

### 3.1 Acceptance Varies Substantially with Temperature

Mean exact acceptance is not constant across temperatures. It increases monotonically from 0.172 (T = 0.2) to 0.710 (T = 2.2), with decreasing variance at higher temperatures:

| Temperature | Mean α | Std α | Min α | Max α |
|---:|---:|---:|---:|---:|
| 0.2 | 0.1718 | 0.2974 | 1.04 × 10⁻⁹ | 1.0000 |
| 0.4 | 0.2148 | 0.2317 | 5.21 × 10⁻⁵ | 0.9999 |
| 0.7 | 0.3247 | 0.1540 | 0.0082 | 0.9974 |
| 1.0 | 0.4412 | 0.1106 | 0.0719 | 0.9757 |
| 1.3 | 0.5379 | 0.0863 | 0.1769 | 0.9265 |
| 1.7 | 0.6321 | 0.0668 | 0.3704 | 0.8435 |
| 2.2 | 0.7100 | 0.0524 | 0.5751 | 0.8787 |

This variation is operationally significant: a global calibrator that predicts a single mean would be wrong by 0.1–0.3 α units for most temperatures. The high variance at low temperatures (std = 0.297 at T = 0.2) indicates that some contexts have near-perfect acceptance while others have near-zero acceptance, making context-level calibration especially important at low T.

### 3.2 Temperature Conditioning Improves Calibration

| Model | RMSE(α) | MAE(α) | R² |
|---|---:|---:|---:|
| Global mean baseline | 0.2538 | — | — |
| Draft-feature-only (no temp) | 0.1725 | 0.1105 | 0.5376 |
| Temperature-conditioned GBDT | 0.1533 | 0.0846 | 0.6349 |

The temperature-conditioned GBDT reduces RMSE by 11.1% and MAE by 23.3% relative to the no-temperature baseline. The R² improvement from 0.538 to 0.635 indicates that temperature explains a meaningful but partial share of residual variance not captured by draft features alone.

It is worth noting that even the best model leaves substantial unexplained variance (R² = 0.635). Draft features and temperature together do not fully determine acceptance; context-level variation in the target–draft distribution alignment remains a significant source of error.

### 3.3 Systematic Bias in the No-Temperature Model

The no-temperature calibrator exhibits systematic per-temperature bias (detailed in `artifacts/results/full/calibration_by_temperature.csv`): it over-predicts acceptance at low temperatures and under-predicts at high temperatures, consistent with the monotonic trend in mean α across temperatures. The temperature-conditioned GBDT reduces the largest temperature-dependent errors by incorporating temperature and its interactions with draft features.

This bias pattern is predictable from the structure of the problem: when the calibrator has no temperature input, it must predict a context-conditional expectation that averages across temperatures. For contexts where acceptance is highly temperature-sensitive, this averaging introduces systematic error whose sign depends on whether the actual temperature is above or below the cross-temperature mean.

### 3.4 Downstream Draft-Length Selection Regret

Under a simple throughput proxy, the temperature-conditioned model reduces γ-selection regret by 7.7% relative to the no-temperature baseline. This is a modest improvement. The mapping from α error to regret is nonlinear and saturates when α is far from the decision boundary for γ selection: small calibration errors near the optimal γ boundary are costly, while large errors in regions where any reasonable γ is acceptable may incur little regret. The 7.7% regret improvement is smaller in relative terms than the 11.1% RMSE improvement, reflecting this nonlinearity.

## 4. Limitations

1. **Synthetic distributions, not live models.** This experiment uses synthetic paired distributions over a 1,024-token vocabulary. Real target/draft LLM pairs have vocabularies of 32k–128k tokens, different distributional structure, and domain-specific prompt distributions. The magnitude of the temperature effect and the calibration improvement may differ substantially in production settings. This is the most important limitation: the result establishes a principle (temperature conditioning is necessary when overlap varies non-uniformly with T) but does not quantify the effect size for any specific model pair.

2. **No top-p/top-k sampler effects.** Production samplers typically apply nucleus (top-p) or top-k truncation, which modifies the effective acceptance probability. The exact acceptance formula used here assumes full-support sampling. Calibration under truncated samplers remains an open question; truncation may amplify, attenuate, or qualitatively change the temperature effect.

3. **One-token acceptance only.** The experiment computes single-token acceptance. Multi-token speculative decoding involves sequential acceptance with potential correlation across positions, which may amplify or attenuate the temperature effect. The relationship between single-token α calibration error and multi-token throughput loss is not explored.

4. **R² of 0.635 leaves substantial unexplained variance.** Even the best model explains only approximately 63% of held-out acceptance variance. Draft features and temperature together do not fully determine acceptance; context-level variation in the target–draft distribution alignment is a remaining source of error. Whether additional features (e.g., target-model entropy, distributional distance metrics) could close this gap is not investigated.

5. **No hardware cost model.** The throughput proxy used for regret evaluation is simplified. Production γ selection depends on measured draft/verify latency on specific hardware, which was not modeled here. The 7.7% regret improvement is specific to the proxy used and may not transfer to real cost models.

6. **Single experimental configuration.** Results are reported for one set of hyperparameters (6,000 contexts, 7 temperatures, 1,024 vocab). Sensitivity to these choices — particularly vocabulary size and the number and range of temperatures — is not explored.

7. **Claim audit status.** The claim ledger for this artifact records no structured claims and is flagged as `blocked_empty_claims`. The results reported here are drawn directly from run notes and project decision records and have not passed a formal claim/evidence audit. Readers should weight the findings accordingly.

## 5. Reproducibility Checklist

- **Experiment script:** `scripts/temperature_acceptance_calibration.py`
- **Command (smoke test):** `python3 scripts/temperature_acceptance_calibration.py --mode smoke --out-dir artifacts/results/smoke`
- **Command (full run):** `python3 scripts/temperature_acceptance_calibration.py --mode full --out-dir artifacts/results/full`
- **Environment logs:** `artifacts/logs/00_environment.log`, `artifacts/logs/03_postrun_environment.log`
- **Run logs:** `artifacts/logs/01_smoke.log`, `artifacts/logs/02_full.log`
- **Summary JSON:** `artifacts/results/full/summary.json`
- **Model metrics:** `artifacts/results/full/model_metrics.csv`
- **Per-temperature calibration:** `artifacts/results/full/calibration_by_temperature.csv`
- **Held-out predictions:** `artifacts/results/full/heldout_predictions.csv`
- **Literature notes:** `artifacts/sources/literature_summary.md`
- **Random seed:** Set within script (deterministic given same inputs and environment)
- **Wall-clock time:** 2.88 s for the full run on the recorded environment
- **Data split:** Context-grouped (29,400 train / 12,600 test); no context appears in both splits
- **Evidence classification:** Synthetic distribution simulation (not llama.cpp hook-prototype, not CUDA copy calibration, not production validation)

## 6. Conclusion

Temperature conditioning improves speculative acceptance calibration in a controlled synthetic setting. The exact acceptance identity makes temperature conditioning theoretically necessary whenever temperature changes the distributional overlap $\sum_x \min(p_T, q_T)$ non-uniformly across contexts. The experiment confirms this in a paired-distribution setting: adding temperature and temperature–feature interactions to a GBDT calibrator reduces held-out RMSE by 11.1% and downstream γ-selection regret by 7.7% relative to a draft-feature-only baseline. The no-temperature calibrator exhibits systematic per-temperature bias — over-predicting at low T and under-predicting at high T — that the conditioned model partially corrects.

However, the result is bounded in several important ways. R² remains at 0.635, indicating that temperature and draft features together explain only a majority of acceptance variance. The setting is synthetic (1,024-token vocabulary, no sampler truncation, single-token acceptance), and the effect sizes may not transfer directly to production model pairs. Production deployment requires validation on actual target/draft model logits, real prompt distributions, and any top-p/top-k sampler settings in use.

The experiment serves as a calibration-screening artifact: it identifies the failure mode a global or temperature-agnostic calibrator would have (systematic per-temperature bias) and quantifies the potential gain from temperature conditioning under exact computation. Scientific closure for production requires live-model benchmarking on the intended target/draft pair and prompt distribution, with a hardware-grounded cost model for γ selection.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `scripts/temperature_acceptance_calibration.py` |
| Environment log | `artifacts/logs/00_environment.log` |
| Smoke test log | `artifacts/logs/01_smoke.log` |
| Full run log | `artifacts/logs/02_full.log` |
| Post-run environment log | `artifacts/logs/03_postrun_environment.log` |
| Summary JSON | `artifacts/results/full/summary.json` |
| Model metrics | `artifacts/results/full/model_metrics.csv` |
| Per-temperature calibration | `artifacts/results/full/calibration_by_temperature.csv` |
| Held-out predictions | `artifacts/results/full/heldout_predictions.csv` |
| Literature summary | `artifacts/sources/literature_summary.md` |
| Project decision record | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260506T011652272749+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260506T011652272749+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260506T011652272749+0000/paper_manifest.json` |
