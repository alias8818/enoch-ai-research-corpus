# BFI-DFlash: Bonus Feature Imputation for Adaptive Speculative Decoding Block-Size Control

> **AI provenance notice:** This draft was generated entirely by an AI system from automated research artifacts (simulation logs, decision records, and metrics files). The operator who released the artifact claims no personal authorship credit for the writing or scientific results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Speculative decoding accelerates autoregressive language model inference by proposing multiple draft tokens per verifier call, but the optimal block size depends on verifier-side acceptance statistics observable only after verification. We investigate Bonus Feature Imputation (BFI), which trains a lightweight ridge regressor during a short burn-in to predict target/draft acceptance mass from cheap draft-side, cache, and state features, enabling per-step adaptive block-size control. In a controlled exact-rejection-sampling simulator with paired Markov target/draft language models (32 seeds, 10,000 tokens per seed), BFI imputed acceptance mass with MAE 0.026 and R² 0.888, closely matching an oracle controller with access to true acceptance mass. BFI increased accepted draft tokens per verifier call by 16.2% over a fixed K=4 baseline. However, under a default hardware cost proxy (draft token cost 0.075, verify-per-token cost 0.035 target-call units), tokens-per-cost improved by only 2.0%, falling below a predeclared 5% positive threshold, while wasted draft tokens per accepted token increased by 49.9%. A 48-point cost-sensitivity grid showed that BFI achieves ≥5% cost improvement in only 16 of 48 settings, requiring combined draft and per-token verification costs ≤0.075 target-call units. The result is conditionally viable: BFI successfully imputes bonus features and improves acceptance rates, but whether this translates to wall-clock speedup depends on hardware-specific marginal costs that this simulation-only study does not measure.

## Introduction

Speculative decoding reduces inference latency by having a small draft model propose a sequence of tokens that a larger target model verifies in parallel. The number of draft tokens proposed per verification call—the block size K—strongly affects efficiency. A block size that is too small underutilizes the target model's parallel verification capacity; one that is too large wastes draft computation on tokens likely to be rejected.

The theoretically optimal block size depends on the acceptance probability between the draft and target distributions. This acceptance mass, however, is a verifier-side quantity: it is observed only after the target model has verified the draft sequence. This creates a temporal dependency—the controller needs acceptance information to choose K, but acceptance information is available only after K has been chosen and verification completed.

Prior work on DFlash-adjacent speculative decoding has demonstrated that verifier-side acceptance signals can strongly predict speculative acceptance, but also that naively exploiting these signals can increase wasted draft FLOPs. A natural question follows: can verifier-side "bonus features" be *imputed* from cheap draft-side signals available before verification, and can the imputed values inform a better block-size controller?

This paper investigates Bonus Feature Imputation (BFI). During a short burn-in phase, BFI trains a ridge regressor to predict target/draft acceptance mass from features available before verification (draft entropy, cache state, positional features). After burn-in, the imputed acceptance mass feeds a block-size controller that adapts K per step.

We evaluate BFI in a controlled exact-rejection-sampling simulator using paired Markov target/draft language models. We compare BFI against a fixed block-size baseline, a draft-entropy heuristic, and an oracle controller with access to true acceptance mass. We predeclare a positive result threshold of ≥5% improvement in tokens-per-cost and ≥35% oracle-gap closure.

Our findings are mixed. BFI successfully imputes the bonus feature and matches oracle performance in acceptance rate, but the default cost model yields only a marginal efficiency gain because longer blocks increase wasted draft computation. The viability of BFI therefore hinges on hardware-specific cost parameters that this simulation-only study does not close.

## Method

### Simulator Design

We constructed a paired target/draft Markov language model simulator (`scripts/bfi_dflash_sim.py`) that performs exact speculative rejection sampling. The target and draft models are finite-state Markov chains over a shared vocabulary. At each step, the draft model proposes K tokens; the target model verifies them via exact rejection sampling against its distribution. Rejected tokens are resampled from the residual distribution, preserving the target sampling distribution by construction.

This design isolates the block-size control question from confounds of approximate sampling, tokenization, and model architecture. The trade-off is that this is a toy simulation rather than a full LLM closure: the Markov assumption (no long-range dependencies) may over- or under-state the predictability of acceptance mass from draft-side features compared to real transformer models.

### Policies Compared

Four policies control the block size K per verification call:

1. **fixed_k4**: Fixed block size K=4. This is the primary baseline.
2. **draft_entropy**: A cheap heuristic that adjusts K based on draft-model entropy alone, without verifier-side information.
3. **bfi_imputed_bonus**: A ridge regressor trained during a burn-in phase (220 verifier calls) to predict target/draft acceptance mass from cheap features (draft entropy, cache hit rate, positional index, draft confidence statistics). After burn-in, the imputer predicts acceptance mass before each verification call, and the controller selects K accordingly.
4. **oracle_bonus**: Upper bound using the true target/draft acceptance mass before verification. This represents the best achievable performance if bonus features were observed exactly.

### Cost Model

The cost model accounts for three components:

- **Verifier call cost**: 1.0 unit per call (representing the target model forward pass).
- **Draft token cost**: 0.075 units per draft token (representing draft model compute).
- **Verify-per-token cost**: 0.035 units per verified token (representing marginal target-model cost per token in the verification pass).

Total cost per step: `cost = verifier_calls × 1.0 + draft_tokens × 0.075 + draft_tokens × 0.035`.

This cost model is a simplified proxy. Actual marginal costs depend on GPU architecture, memory hierarchy, batch size, KV-cache behavior, and implementation details. The cost-sensitivity analysis (Section 4.4) partially addresses this limitation by sweeping over a grid of cost parameters.

### Predeclared Success Criteria

Before running the full experiment, we declared BFI as positive if it simultaneously satisfies:

1. Imputation predicts the bonus feature with useful accuracy.
2. Accepted draft tokens per verifier call improves by ≥15% over fixed K=4.
3. Tokens-per-cost improves by ≥5% over fixed K=4 under the default cost model.
4. Exact sampling quality is preserved.
5. The result closes at least 35% of the oracle gap in tokens-per-cost.

### Experimental Configuration

- **Seeds**: 32 independent random seeds.
- **Tokens per seed**: 10,000 generated tokens.
- **Burn-in calls per seed**: 220 verifier calls (after which the ridge imputer is frozen and used for prediction).
- **Smoke test**: 8 seeds × 2,000 tokens × 80 burn-in calls (passed; results not reported as primary).
- **Environment**: Python 3.12.3; numpy, sklearn, scipy available; torch and transformers not used. CPU-only execution on host `gx10-efe8`; NVIDIA GB10 GPU visible but unused. Peak RSS: 32,684 KB. Wall time: 8.30 s. Swap disabled.

### Cost-Sensitivity Analysis

A separate script (`scripts/analyze_bfi_cost_sensitivity.py`) sweeps a 48-point grid over draft token cost and verify-per-token cost to characterize the conditions under which BFI yields positive efficiency gains.

## Results

### Main Comparison

Table 1 reports the primary metrics across 32 seeds × 10,000 tokens.

**Table 1.** Policy comparison under default cost model (draft token cost = 0.075, verify-per-token cost = 0.035).

| Policy | Accepted draft / verifier call | Δ vs fixed | Tokens / cost | Δ vs fixed | Wasted draft / accepted | Mean K |
|---|---:|---:|---:|---:|---:|---:|
| fixed_k4 | 1.991 | 0.0% | 1.869 | 0.0% | 1.010 | 4.000 |
| draft_entropy | 0.923 | −53.6% | 1.078 | −42.3% | 0.520 | 1.405 |
| bfi_imputed_bonus | 2.313 | +16.2% | 1.906 | +2.0% | 1.514 | 5.812 |
| oracle_bonus | 2.302 | +15.6% | 1.904 | +1.9% | 1.511 | 5.776 |

BFI increases accepted draft tokens per verifier call by 16.2% over the fixed baseline, slightly exceeding the oracle controller's 15.6% gain. However, tokens-per-cost improves by only 2.0%, well below the predeclared 5% threshold. The draft-entropy heuristic performs substantially worse than the fixed baseline on both metrics, suggesting that naive draft-side heuristics without imputed verifier information can be actively harmful.

BFI and the oracle controller choose similar mean block sizes (5.812 and 5.776, respectively, vs. 4.000 for the fixed baseline), confirming that BFI successfully imputes the acceptance signal. However, the longer blocks increase wasted draft tokens per accepted token by 49.9% relative to the fixed baseline (1.514 vs. 1.010).

### Imputation Quality

The ridge imputer predicts acceptance mass with:

- **Mean absolute error (MAE)**: 0.0262
- **R²**: 0.888

across all states in the test set (post-burn-in). This indicates that the cheap draft-side features carry substantial information about the verifier-side acceptance mass in the Markov model, and the ridge regressor captures this relationship effectively. Whether this predictability transfers to real transformer-based draft/target pairs remains an open question.

### Sampling Quality Verification

Exact rejection sampling preserves the target distribution by construction. To verify this empirically, we computed unigram total variation distance between target-only sampling and BFI exact speculative sampling for the first three seeds:

- Seed 1: TV = 0.0208
- Seed 2: TV = 0.0245
- Seed 3: TV = 0.0225

These values are consistent with finite-sample noise for exact rejection sampling and do not indicate distributional drift.

### Cost-Sensitivity Analysis

The 48-point cost-sensitivity grid reveals a sharp dependence on hardware cost parameters:

- BFI achieved positive tokens-per-cost delta in **30 of 48** settings.
- BFI achieved ≥5% tokens-per-cost improvement in **16 of 48** settings.
- The ≥5% improvement region requires combined draft + per-token verification cost ≤ approximately 0.075 target-call units.
- In the best case (draft token cost = 0, verify-per-token cost = 0), BFI achieved +16.08% tokens-per-cost, essentially matching the oracle upper bound.
- At the default cost (0.075 + 0.035 = 0.110 combined), BFI achieved only +1.96% tokens-per-cost despite +16.19% accepted tokens per verifier call.

This confirms that the acceptance-rate improvement from BFI is genuine but does not automatically translate to cost efficiency when draft and verification marginal costs are non-negligible.

### Success Criteria Assessment

| Criterion | Result |
|---|---|
| Imputation predicts bonus feature | ✓ (MAE 0.026, R² 0.888) |
| Accepted per call improves ≥15% | ✓ (+16.2%) |
| Tokens/cost improves ≥5% (default cost) | ✗ (+2.0%) |
| Exact sampling quality preserved | ✓ (TV ≤ 0.025) |
| Closes ≥35% oracle gap in tokens/cost | ✗ (oracle itself only +1.9%) |

The oracle gap in tokens-per-cost is itself only 1.9% under the default cost model, meaning that even perfect knowledge of acceptance mass cannot overcome the cost of longer blocks at these cost ratios. BFI closes 100% of the (small) oracle gap, but the gap itself is below the practical significance threshold. Criteria 3 and 5 fail not because of imputation error but because the cost structure limits the achievable gain from any acceptance-informed controller.

## Limitations

1. **Synthetic proxy, not LLM closure.** The simulator uses paired Markov language models rather than real transformer-based draft and target models. The Markov assumption (no long-range dependencies) may over- or under-state the predictability of acceptance mass from draft-side features. No real DFlash implementation or LLM trace was available in this project; this is a controlled proxy study, not a production validation.

2. **Cost model is a proxy.** The cost model (verifier call = 1.0, draft token = 0.075, verify-per-token = 0.035) is a simplified abstraction. Actual marginal costs depend on GPU architecture, memory hierarchy, batch size, KV-cache behavior, and implementation details. The cost-sensitivity grid partially addresses this, but real hardware measurement is needed.

3. **No wall-clock validation.** No timing was performed on actual hardware. The tokens-per-cost metric is a proxy for wall-clock speedup, but the mapping from cost units to seconds depends on hardware-specific throughput characteristics. The NVIDIA GB10 GPU on the host was visible but unused; no CUDA copy calibration or production timing was performed.

4. **Single bonus feature.** Only acceptance mass was imputed. Other verifier-side signals (e.g., per-position acceptance probability, residual entropy) might provide additional control leverage or might be harder to impute.

5. **Burn-in cost not amortized.** The 220-call burn-in phase incurs cost that is not included in the per-step cost accounting. For short sequences, this overhead could be significant.

6. **Ridge regressor capacity.** The imputer is a linear model. More expressive models (e.g., small neural networks) might capture nonlinear relationships between draft-side features and acceptance mass, but would increase imputation cost and burn-in data requirements.

7. **Wasted draft computation.** BFI increases mean block size from 4.0 to 5.8, which increases wasted draft tokens by 49.9%. In throughput-limited serving scenarios, this waste may reduce batch-level efficiency even if per-request latency improves.

8. **No confidence intervals.** All metrics are reported as means over 32 seeds without confidence intervals or hypothesis tests. The magnitude of the effects (e.g., +16.2% acceptance, +2.0% tokens/cost) is large relative to typical seed-to-seed variance in this simulator, but formal uncertainty quantification is absent.

9. **Related prior result not fully integrated.** A prior project (`source-record-redacted`, Verifier-Feature Acceptance Classifier) found that verifier/target acceptance signals can strongly predict speculative acceptance but warned that accepted-token gains can increase wasted draft FLOPs. The present result is consistent with that warning but does not constitute a direct replication or extension, as the experimental setups differ.

## Reproducibility Checklist

- **Code available**: `scripts/bfi_dflash_sim.py`, `scripts/analyze_bfi_cost_sensitivity.py`
- **Full command**: `python3 scripts/bfi_dflash_sim.py --seeds 32 --tokens 10000 --burnin-calls 220`
- **Cost-sensitivity command**: `python3 scripts/analyze_bfi_cost_sensitivity.py`
- **Random seeds**: 32 independent seeds (seed indices 0–31)
- **Environment**: Python 3.12.3; numpy, sklearn, scipy available; torch and transformers not used
- **Hardware**: CPU-only on host `gx10-efe8`; NVIDIA GB10 present but unused
- **Memory**: Peak RSS 32,684 KB; swap disabled (SwapTotal: 0 kB)
- **Wall time**: 8.30 s for full run
- **Output files**: `results/bfi_dflash/summary.json`, `results/bfi_dflash/per_seed_metrics.csv`, `results/bfi_dflash/imputation_metrics.csv`, `results/bfi_dflash/cost_sensitivity.json`
- **Logs**: `logs/bfi_dflash_smoke.log`, `logs/bfi_dflash_full.log`, `logs/bfi_cost_sensitivity.log`
- **Decision record**: `.omx/project_decision.json`
- **Predeclared criteria**: Specified in simulation script before full run
- **Statistical reporting**: All metrics are means over 32 seeds; no confidence intervals were computed (noted as a limitation)
- **Evidence type**: Toy simulation (paired Markov models with exact rejection sampling); not llama.cpp hook-prototype, CUDA copy calibration, or final production validation

## Conclusion

Bonus Feature Imputation successfully predicts verifier-side acceptance mass from cheap draft-side features in a controlled speculative decoding simulator, achieving MAE 0.026 and R² 0.888 with a ridge regressor trained on 220 burn-in observations. The BFI controller matches oracle performance in acceptance rate, increasing accepted draft tokens per verifier call by 16.2% over a fixed K=4 baseline.

However, under the default hardware cost proxy, this acceptance improvement translates to only a 2.0% gain in tokens-per-cost—below the predeclared 5% positive threshold—because the longer blocks selected by BFI increase wasted draft computation by 49.9%. The cost-sensitivity analysis reveals that BFI achieves meaningful cost improvements (≥5%) only when combined draft and per-token verification costs are sufficiently low (≤0.075 target-call units in this grid). At the default cost ratio, even the oracle controller achieves only 1.9% cost improvement, indicating that the cost model itself limits the achievable gain rather than imputation error.

The result is conditionally viable. BFI is not a standalone positive result under the default cost assumption, but it demonstrates that bonus features are imputable and that adaptive block-size control can improve acceptance rates. Whether BFI improves wall-clock performance in practice depends on hardware-specific marginal costs that this study does not measure. We recommend that any follow-up work first instrument a real DFlash implementation to measure actual draft-token and verify-per-token marginal costs; if these fall in the cheap regime identified by the sensitivity analysis, BFI warrants an implementation pass. Otherwise, a cost-constrained controller that directly penalizes wasted draft FLOPs should be pursued instead.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Main simulator | `scripts/bfi_dflash_sim.py` |
| Cost-sensitivity analyzer | `scripts/analyze_bfi_cost_sensitivity.py` |
| Summary metrics | `results/bfi_dflash/summary.json` |
| Per-seed metrics | `results/bfi_dflash/per_seed_metrics.csv` |
| Imputation metrics | `results/bfi_dflash/imputation_metrics.csv` |
| Cost-sensitivity grid | `results/bfi_dflash/cost_sensitivity.json` |
| Smoke test log | `logs/bfi_dflash_smoke.log` |
| Full run log | `logs/bfi_dflash_full.log` |
| Cost-sensitivity log | `logs/bfi_cost_sensitivity.log` |
| Decision record | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260504T180350506127+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260504T180350506127+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260504T180350506127+0000/paper_manifest.json` |
| Related prior project | `../source-record-redacted` (Verifier-Feature Acceptance Classifier) |
