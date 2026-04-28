# Adapter-Projected GaLore with Decoupled Projection Refresh: Downstream Transfer Evaluation at 192 Steps

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We evaluate whether the optimizer-state memory savings of adapter-projected GaLore—a low-rank gradient projection method that decouples projection subspace refresh from rank-change events—transfers to downstream task performance. Using a matched 192-step continued pretraining protocol on Qwen3-0.6B with a domain-specific corpus, we compare adapter-projected LoRA-GaLore (no-refresh, update-gap 16) against standard LoRA with Adam. On held-out continued-pretraining loss, adapter-projected GaLore achieves a 6.99% reduction over LoRA while using only 25.1% of the optimizer-state memory. On a 256-example deterministic MMLU cloze evaluation, adapter-projected GaLore scores 81/256 (31.64%) versus LoRA at 80/256 (31.25%), with marginally better correct-choice negative log-likelihood (6.1658 vs. 6.3879) and margin (−0.9272 vs. −0.9670). However, both finetuned checkpoints substantially underperform the base model (97/256, 37.89%), indicating that the short domain-specific continuation degrades general knowledge regardless of optimizer choice. The downstream accuracy difference of +1/256 is within noise for this evaluation size. The results are mixed: adapter-projected GaLore preserves its memory advantage and does not underperform LoRA on downstream accuracy, but the transfer signal is too weak and the evaluation too narrow to claim a downstream benefit with confidence.

---

## 1. Introduction

Low-rank gradient projection methods such as GaLore reduce optimizer-state memory by projecting gradients into a low-rank subspace and maintaining optimizer moments in that compressed space. A practical difficulty with GaLore is that periodic subspace refresh—recomputing the projection matrix from accumulated gradients—introduces throughput overhead and requires tuning the refresh schedule.

Adapter-projected GaLore modifies the standard GaLore procedure in two ways: (1) it applies the low-rank projection through a LoRA-style adapter structure rather than directly modifying weight gradients, and (2) it decouples projection refresh from rank-change events, allowing the projection subspace to persist across rank transitions. The "no-refresh" variant (`norefresh_gap16`) computes the projection matrix at initialization and updates it every 16 steps without resetting optimizer state, avoiding the costly re-initialization that standard GaLore performs on rank changes.

Prior profiling on this codebase (3-seed, 192-step runs) established that adapter-projected GaLore with the `norefresh_gap16` policy achieves mean held-out CPT loss of 0.1979 versus 0.2063 for matched LoRA, retains approximately 75% optimizer-state byte reduction, and recovers 31.8% of the throughput gap incurred by refresh-heavy GaLore variants. The present study asks whether these continued-pretraining advantages transfer to a downstream task: does the lower CPT loss and smaller optimizer state yield equal-or-better performance on a general knowledge benchmark?

---

## 2. Method

### 2.1 Adapter-Projected LoRA-GaLore

The method applies GaLore-style low-rank gradient projection within a LoRA adapter framework. For each trainable weight matrix $W \in \mathbb{R}^{m \times n}$, the adapter decomposition introduces low-rank matrices $A \in \mathbb{R}^{m \times r}$ and $B \in \mathbb{R}^{r \times n}$, where $r$ is the current adapter rank. The GaLore projection matrix $P \in \mathbb{R}^{m \times p}$ (with $p < m$) is computed via a low-rank factorization of accumulated gradient information and is used to project the optimizer state into a compressed subspace.

### 2.2 Decoupled Refresh Policy

Standard GaLore refreshes the projection matrix whenever the effective rank changes, discarding the accumulated optimizer moments. The decoupled refresh policy (`no-refresh-on-rank-change`) separates these two events: the projection matrix is updated at a fixed interval (every `update-gap` steps) regardless of rank transitions, and optimizer moments are preserved across rank changes. This study uses `update-gap = 16`.

### 2.3 Rank Schedule

The adapter rank follows a staircase schedule from `rank-start = 8` to `rank-end = 4` with `staircase-rungs = 4`, meaning the rank decreases in four evenly-spaced steps over the 192 training steps. The projection method is `lowrank` with `projection-oversampling = 2` and `projection-niter = 0` (single-pass SVD approximation).

---

## 3. Experimental Setup

### 3.1 Model and Corpus

- **Base model:** Qwen/Qwen3-0.6B (0.6 billion parameter transformer)
- **Corpus:** `domain_multistep_corpus.txt` (domain-specific text, 32,768 tokens maximum)
- **Precision:** bfloat16 on CUDA

### 3.2 Training Configuration

Both conditions share identical hyperparameters except for the optimizer/adapter method:

| Parameter | Value |
|---|---|
| Steps | 192 |
| Batch size | 1 |
| Sequence length | 64 |
| Learning rate | 3e-4 |
| Weight decay | 0.0 |
| Eval tokens | 4,096 |
| Eval steps | 8 |
| Seed | 17 |

**LoRA Adam condition:** LoRA rank 16, LoRA alpha 32.0, standard Adam optimizer on LoRA parameters.

**Adapter-projected LoRA-GaLore condition:** Rank schedule 8→4 (staircase, 4 rungs), update-gap 16, no-refresh-on-rank-change, lowrank projection with oversampling 2 and 0 SVD iterations.

### 3.3 Evaluation

Downstream evaluation uses a deterministic cloze-format MMLU probe consisting of 256 multiple-choice examples (`mmlu_validation_256_cloze_examples.json`). For each example, the model assigns negative log-likelihood to each answer choice given the question prompt, and the lowest-NLL choice is selected. Metrics reported are accuracy (fraction correct), mean correct-choice NLL, and mean margin (difference in NLL between the correct choice and the lowest-NLL incorrect choice; negative values indicate the correct choice was not the model's top selection on average).

### 3.4 Regression Testing

The project test suite (31 tests) was run before and after the experiment. All tests passed in both runs (4.36s pre-experiment, 1.60s post-experiment).

---

## 4. Results

### 4.1 Continued Pretraining Metrics

| Metric | LoRA Adam | Adapter-Projected GaLore (norefresh_gap16) | Ratio |
|---|---|---|---|
| Validation loss | 0.2134 | 0.1985 | 0.930 (−6.99%) |
| Final train loss | 0.1389 | 0.1586 | 1.142 |
| Throughput (tokens/s) | 799.4 | 572.2 | 0.716 |
| Optimizer state (bytes) | 40,370,176 | 10,142,720 | 0.251 |
| Projection refreshes | — | 4,704 total (24.5/step) | — |

Adapter-projected GaLore achieves lower held-out validation loss than LoRA, consistent with the prior 3-seed profiling result (mean 0.1979 vs. 0.2063). The optimizer state is reduced to approximately one quarter of the LoRA baseline. Throughput is 28.4% lower than LoRA, an improvement over refresh-heavy GaLore variants (which recovered 31.8% of the throughput gap in prior profiling). The final training loss is higher for adapter-projected GaLore (0.1586 vs. 0.1389), suggesting the method's validation advantage arises from implicit regularization rather than tighter fitting.

### 4.2 MMLU Cloze Evaluation (256 Examples)

| Condition | Accuracy | Mean Correct-Choice NLL | Mean Margin |
|---|---|---|---|
| Base Qwen3-0.6B | 97/256 (37.89%) | 5.0536 | −0.7400 |
| 192-step LoRA Adam | 80/256 (31.25%) | 6.3879 | −0.9670 |
| 192-step Adapter-Projected GaLore | 81/256 (31.64%) | 6.1658 | −0.9272 |

### 4.3 Interpretation of Downstream Results

The adapter-projected GaLore checkpoint outperforms the LoRA checkpoint by +1/256 on accuracy, with better (lower) correct-choice NLL (6.1658 vs. 6.3879) and better (less negative) margin (−0.9272 vs. −0.9670). These differences are directionally consistent with the CPT-loss advantage but are small: a +1/256 accuracy difference is well within the binomial noise expected for 256 trials at approximately 31% accuracy (the standard error of the difference under the null is approximately $\sqrt{2 \cdot 0.31 \cdot 0.69 / 256} \approx 0.041$, or about 10.5/256).

The most notable finding is negative: both finetuned checkpoints substantially underperform the base model on this MMLU subset (−17/256 and −16/256 respectively). This indicates that 192 steps of domain-specific continued pretraining on a small corpus degrades the model's general knowledge, regardless of the optimizer or adapter method used. The CPT-loss improvement of adapter-projected GaLore over LoRA does not translate into a recovery of base-model-level MMLU performance.

---

## 5. Limitations

1. **Single-seed evaluation.** The downstream MMLU evaluation was conducted on a single seed (17). The prior 3-seed CPT profiling showed consistent validation-loss advantages across seeds, but downstream transfer was only evaluated for one seed. The +1/256 accuracy difference is not distinguishable from noise at this sample size.

2. **Small evaluation set.** The 256-example MMLU cloze probe is a subset, not the full MMLU benchmark. Accuracy estimates on 256 items have wide confidence intervals (approximately ±6 percentage points at 95% confidence for rates near 31–38%).

3. **Short training horizon.** Only 192 training steps were used. The degradation of general knowledge may be an artifact of the extremely short continuation on a narrow domain corpus; results may differ at longer horizons or with data-mixing strategies.

4. **Single model scale.** Results are specific to Qwen3-0.6B. Scaling behavior to larger models is unknown.

5. **Domain-specific corpus.** The training corpus is small (32,768 tokens maximum) and domain-specific. The observed general-knowledge degradation may not generalize to broader or larger corpora.

6. **No statistical testing.** No formal hypothesis tests or confidence intervals are reported for the downstream accuracy comparison. The sample size (256) and single-seed design limit the strength of any comparative claim.

7. **Throughput cost.** Adapter-projected GaLore incurs a 28.4% throughput penalty relative to LoRA Adam in this configuration. Whether this tradeoff is acceptable depends on the relative value of optimizer-state memory savings versus training time in the target deployment.

8. **CPT-loss vs. downstream divergence.** The method achieves lower held-out CPT loss but both finetuned models degrade on MMLU. This raises the question of whether CPT loss on a small domain corpus is a reliable proxy for downstream task quality; the present data suggest it is not, at least at this scale.

---

## 6. Reproducibility Checklist

| Item | Status |
|---|---|
| Model identifier specified | Yes: Qwen/Qwen3-0.6B |
| Training corpus identified | Yes: `artifacts/domain_multistep_corpus.txt` |
| All hyperparameters listed | Yes (see Section 3.2) |
| Random seed reported | Yes: seed 17 |
| Hardware specified | CUDA GPU (specific model not recorded in artifacts) |
| Precision specified | Yes: bfloat16 |
| Software versioned | Yes: project installed via `uv pip install -e '.[hf]'`; test suite 31/31 passed |
| Checkpoints saved | Yes: `lora_trainable.pt`, `lora_galore_trainable.pt` |
| Evaluation script specified | Yes: `scripts/domain_cloze_eval.py` |
| Evaluation examples specified | Yes: `artifacts/mmlu_validation_256_cloze_examples.json` |
| Pre/post regression tests | Yes: 31 passed both times |
| Full command lines recorded | Yes (see run notes) |
| Multi-seed replication | No: downstream eval on seed 17 only; seeds 23 and 31 have CPT profiling but no MMLU eval |

---

## 7. Conclusion

Adapter-projected GaLore with decoupled projection refresh (no-refresh, update-gap 16) achieves a 6.99% reduction in held-out CPT loss over matched LoRA Adam at 192 steps on Qwen3-0.6B, while using only 25.1% of the optimizer-state memory. On a 256-example MMLU cloze evaluation, the adapter-projected GaLore checkpoint marginally outperforms the LoRA checkpoint (81/256 vs. 80/256) with better correct-choice NLL and margin, but this difference is within expected noise. Both finetuned checkpoints substantially underperform the base model on general knowledge, indicating that short domain-specific continued pretraining degrades MMLU performance regardless of optimizer choice.

The hypothesis that adapter-projected GaLore's CPT-loss advantage transfers to equal-or-better downstream accuracy is weakly supported by the directional signal but cannot be confirmed at this evaluation scale. The optimizer-state memory reduction (~75%) is the clearest positive finding and is robust across seeds in prior profiling. Whether this memory savings justifies the throughput cost and the uncertainty in downstream transfer depends on the target application.

If further budget is allocated, the most informative next step would be to repeat the 192-step MMLU cloze evaluation across seeds 23 and 31 (which already have CPT profiling data) to establish whether the directional downstream advantage is consistent or seed-dependent.

---

## Referenced Artifacts

### Decision and run metadata
- `.omx/project_decision.json` — project decision (finalize_positive), hypothesis status (mixed), confidence (medium)
- `run_notes.md` — full execution log, command lines, and interpretation
- `.omx/metrics.json` — session metrics

### Training metrics
- `artifacts/qwen_192step_lora_train_metrics.json` — LoRA Adam 192-step training metrics
- `artifacts/qwen_192step_norefresh_gap16_train_metrics.json` — adapter-projected GaLore 192-step training metrics

### Checkpoints
- `artifacts/qwen_192step_decoupled_checkpoints/lora_trainable.pt`
- `artifacts/qwen_192step_decoupled_checkpoints/lora_galore_trainable.pt`

### Evaluation metrics
- `artifacts/qwen_192step_decoupled_mmlu256_eval_metrics.json` — full per-example evaluation data
- `artifacts/qwen_192step_decoupled_mmlu256_summary.json` — compact comparison summary

### Prior multi-seed profiling (CPT only, no MMLU eval)
- `artifacts/qwen_adapter_multiseed_192_profile.json`
- `artifacts/qwen_adapter_multiseed_192_profile.run.log`
- `artifacts/qwen_adapter_multiseed_192_profile_seed23_norefresh_gap16.json` / `.log`
- `artifacts/qwen_adapter_multiseed_192_profile_seed23_rank_refresh_gap4.json` / `.log`
- `artifacts/qwen_adapter_multiseed_192_profile_seed23_lora.json` / `.log`
- `artifacts/qwen_adapter_multiseed_192_profile_seed31_norefresh_gap16.json` / `.log`
- `artifacts/qwen_adapter_multiseed_192_profile_seed31_rank_refresh_gap4.json` / `.log`
- `artifacts/qwen_adapter_multiseed_192_profile_seed31_lora.json` / `.log`

### Claim audit
- `papers/.../claim_ledger.json` — registered claims, confidence levels, and allowed/forbidden wording
- `papers/.../evidence_bundle.json` — full evidence bundle linking claims to artifacts
