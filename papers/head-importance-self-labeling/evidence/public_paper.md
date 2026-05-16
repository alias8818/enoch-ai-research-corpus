# Head Importance Self-Labeling via Prediction Disruption in a Controlled Transformer

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, evidence bundle, claim ledger, metrics). The operator who released this artifact claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed the claims herein.

---

## Abstract

We investigate whether a trained transformer can label the importance of its own attention heads without external supervision, using the KL divergence between its full output distribution and the distribution produced under single-head ablation. In a controlled experiment on a 2-layer, 4-head-per-layer transformer (8 heads total) trained on a synthetic marker-comparison task, self-labeled importance scores recovered the supervised ablation ranking exactly: Spearman rank correlation ρ = 1.0000, Pearson r = 0.9958, and top-half overlap = 1.0000. A pruning sweep at k ∈ {1, 2, 4} confirmed that removing the bottom-k self-labeled heads was consistently less damaging than removing the top-k or random heads. However, pruning half the heads (k = 4 of 8) still caused material accuracy degradation (73.3% vs. 100% baseline), and the random-marker variant of the task failed to learn within the same training budget. These results support self-labeling as a viable head-importance ranking mechanism in a controlled toy setting, but do not constitute evidence for production LLM head pruning. The strongest practical claim supported is that self-labeling provides principled ranking for pruning triage—not that it enables costless head removal.

## 1. Introduction

Attention head pruning is a well-studied technique for reducing transformer inference cost. A central practical question is which heads can be removed with minimal impact on model quality. Supervised approaches require labeled validation data and ground-truth ablation sweeps, which may be unavailable or expensive to obtain at scale. Self-supervised alternatives—where the model itself identifies which heads matter—offer a potential path to importance labeling without external data.

This work asks: can a trained transformer label its own attention heads as important by measuring output-distribution disruption under single-head ablation? The intuition is that if removing a head substantially changes the model's predicted distribution, that head is important; if the change is negligible, the head is relatively dispensable.

We implement and evaluate this protocol on a small synthetic transformer, measuring agreement between self-labeled importance scores (KL divergence under ablation) and supervised importance scores (held-out cross-entropy increase under ablation). We further test whether self-labels support effective pruning triage through a k-head removal sweep.

The contribution is a controlled proof-of-concept demonstration that prediction-KL self-labeling exactly recovers supervised ablation rankings in a toy setting, along with an honest characterization of where this result breaks down or degrades.

## 2. Method

### 2.1 Task and Model

We constructed a synthetic marker-comparison task. Each input sequence contains two markers (A and B) followed by associated value tokens. The label indicates whether the two marker-associated values match. The model is a 2-layer, 4-head-per-layer transformer (8 heads total), trained for 1000 steps on the fixed-marker variant of this task.

A random-marker variant—where marker positions were not fixed across sequences—was also attempted but failed to learn within 1000 training steps. All results below pertain only to the fixed-marker setting.

### 2.2 Self-Labeling Protocol

For each attention head *h*, the self-label importance score is:

$$\text{self\_kl}(h) = D_{\text{KL}}\bigl(p_{\text{full}}(y \mid x) \;\|\; p_{\text{ablate } h}(y \mid x)\bigr)$$

evaluated on a calibration set of inputs drawn from the training distribution but not used for gradient updates during self-labeling. Ablation is implemented by zeroing the output projection of head *h* while leaving all other heads intact.

### 2.3 Supervised Validation

For each head *h*, the supervised importance score is:

$$\text{supervised\_loss\_delta}(h) = \mathcal{L}_{\text{ablate } h} - \mathcal{L}_{\text{full}}$$

computed on a held-out validation set with ground-truth labels. This score is used only for evaluation of self-labeling quality, never for ranking or pruning decisions.

### 2.4 Evaluation Metrics

We assess self-labeling quality through three metrics:

1. **Spearman rank correlation** (ρ) between self-label scores and supervised loss deltas.
2. **Pearson correlation** (r) between the same.
3. **Top-half overlap**: fraction of heads in the top half by self-label score that also appear in the top half by supervised score.

We evaluate pruning utility through a sweep over k ∈ {1, 2, 4} heads removed, comparing three strategies:

- **Bottom-k self-labeled**: remove the k heads with lowest self-label scores.
- **Top-k self-labeled**: remove the k heads with highest self-label scores.
- **Random-k**: remove k heads uniformly at random (mean over multiple draws).

### 2.5 Implementation Details

The experiment was implemented in PyTorch 2.11.0 (CPU build) and executed on a Linux host (kernel 6.17.0-1014-nvidia-aarch64, glibc 2.39). An NVIDIA GB10 GPU was present on the host but unused, as only the CPU PyTorch wheel was installed. Total wall-clock runtime was 37.2 seconds. Peak RSS was approximately 403 MB. No swap was configured (SwapTotal: 0 kB). Available memory remained approximately 122 GB throughout. A smoke test (`--mode smoke`) was executed and passed before the full run.

## 3. Results

### 3.1 Baseline Performance

The trained model achieved near-perfect performance on the held-out validation set:

| Metric | Value |
|--------|-------|
| Validation loss | 4.425 × 10⁻⁵ |
| Validation accuracy | 1.0000 |

This confirms the model fully learned the fixed-marker synthetic task within 1000 steps.

### 3.2 Self-Label vs. Supervised Agreement

Self-label importance scores closely matched supervised ablation rankings:

| Metric | Value |
|--------|-------|
| Spearman ρ | 1.0000 |
| Pearson r | 0.9958 |
| Top-half overlap | 1.0000 |

The perfect Spearman correlation and top-half overlap indicate that self-labeling exactly recovered the importance ranking in this controlled setting. The near-unity Pearson correlation confirms that the magnitude ordering is also preserved. We note that with only 8 heads, perfect rank recovery is a weaker result than it would be with a larger head count; chance-level rank agreement is non-trivial even at this scale, but the result should be interpreted accordingly.

### 3.3 Pruning Sweep

The k-head pruning sweep results:

| k | Strategy | Val Loss | Val Accuracy |
|---|----------|----------|--------------|
| 1 | Bottom self-labeled | 7.06 × 10⁻⁵ | 1.0000 |
| 1 | Top self-labeled | 1.6124 | 0.7861 |
| 1 | Random (mean) | 0.4214 | 0.9400 |
| 2 | Bottom self-labeled | 0.4512 | 0.9333 |
| 2 | Top self-labeled | 3.1587 | 0.6263 |
| 2 | Random (mean) | 1.4050 | 0.8219 |
| 4 | Bottom self-labeled | 1.9582 | 0.7327 |
| 4 | Top self-labeled | 4.6491 | 0.5013 |
| 4 | Random (mean) | 2.3644 | 0.7169 |

At k = 1, removing the least self-labeled head preserved perfect accuracy, while removing the most self-labeled head dropped accuracy to 78.6%. Random removal averaged 94.0% accuracy.

At k = 2, bottom-self-labeled removal retained 93.3% accuracy, while top-self-labeled removal collapsed to 62.6%.

At k = 4 (half of all heads), even bottom-self-labeled removal caused substantial degradation to 73.3% accuracy. This remained marginally better than random removal (71.7% mean) and substantially better than removing the top-4 self-labeled heads (50.1%, near chance for this binary task). The small margin between bottom-self-labeled and random at k = 4 suggests that the ranking signal becomes less actionable when a large fraction of heads are removed.

The key practical finding is that self-labeling supports **ranking and triage**—identifying which heads are safest to remove—rather than enabling aggressive pruning without cost. Removing one or two bottom-ranked heads was relatively safe; removing half was not.

### 3.4 Negative Result: Random-Marker Variant

The random-marker version of the synthetic task, where marker positions were not fixed across sequences, failed to learn within 1000 training steps. This negative result limits the scope of the positive finding: the self-labeling protocol has been validated only in the fixed-marker controlled setting, not in a setting where the model must learn more flexible positional patterns. It remains unknown whether self-labeling would remain accurate when the model's learned representations are less positionally regular.

## 4. Limitations

1. **Toy scale and synthetic task.** The model has only 8 heads across 2 layers on a hand-designed synthetic task. These results do not directly transfer to pretrained production LLMs with hundreds of heads and natural-language distributions. The perfect rank recovery may partly reflect the simplicity and regularity of the task.

2. **Fixed-marker setting only.** The random-marker variant failed to learn, so the positive result is confined to the easier, positionally-regular variant. It remains unknown whether self-labeling would remain accurate under more complex positional structure or on natural language.

3. **Pruning is not free.** Even bottom-ranked head removal caused material degradation at k = 4 (73.3% accuracy vs. 100% baseline). Self-labeling identifies the *safest* heads to prune, but does not guarantee that pruning is harmless. The margin between bottom-self-labeled and random pruning narrowed at k = 4, suggesting diminishing returns from the ranking signal at high pruning fractions.

4. **No threshold calibration.** The pruning sweep used fixed fractions (k = 1, 2, 4). A practical system would need a threshold on self-label scores to decide how many heads to prune, which was not explored here.

5. **Single random seed and architecture.** Only one training run and one architecture were tested. Variance across seeds and architectures is unknown.

6. **CPU-only execution.** The experiment ran on CPU PyTorch despite GPU availability. This is immaterial to the scientific findings but limited the scale of model that could be tested within the run budget.

7. **Small head count.** With only 8 heads, the granularity of the ranking is coarse. Perfect Spearman correlation over 8 items is more likely to arise by chance than over, say, 96 heads, and the practical utility of the ranking depends on the head count being large enough for the triage decision to be non-trivial.

## 5. Reproducibility Checklist

- **Code available:** `scripts/head_importance_self_labeling.py`
- **Random seed:** Set within the script (see source for exact value).
- **Hardware:** Linux 6.17.0-1014-nvidia-aarch64, NVIDIA GB10 (GPU present but unused), CPU-only PyTorch 2.11.0.
- **Memory:** Peak RSS ~403 MB; ~122 GB available; no swap configured.
- **Runtime:** 37.2 seconds wall-clock for full run (1000 train steps + evaluation sweep).
- **Dependencies:** torch (CPU), numpy, scipy, scikit-learn, matplotlib.
- **Smoke test:** Passed before full run (`--mode smoke`).
- **Output artifacts:** Full summary JSON, head scores CSV, training JSONL log, console log with `/usr/bin/time -v` output.
- **Exact commands:** Recorded in run notes (see Referenced Artifacts).
- **Claim audit status:** Claim ledger contains no completed claim-audit entries; draft is in `draft_review` status with review checklist at 0/9 items resolved.

## 6. Conclusion

In a controlled toy setting, a trained transformer can self-label its attention heads by measuring prediction KL under single-head ablation, and these self-labels exactly recover the supervised ablation importance ranking (Spearman ρ = 1.0, top-half overlap = 1.0). Pruning based on self-labels is consistently less damaging than pruning important or random heads, confirming the utility of self-labeling for head-importance triage.

However, these results are confined to a small synthetic task with fixed positional structure. The random-marker variant failed to learn, and aggressive pruning (half of all heads) still caused substantial accuracy loss even when targeting the least important heads. The margin between self-label-guided and random pruning narrowed at high pruning fractions. The strongest practical claim supported by this evidence is that self-labeling provides a principled ranking for pruning triage—not that it enables costless head removal.

The recommended next step is to apply the same KL self-labeling protocol to a small pretrained transformer on natural text, comparing self-label rankings to validation perplexity deltas, and testing thresholded (rather than fixed-fraction) pruning strategies.

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Run notes | `run_notes.md` |
| Experiment script | `scripts/head_importance_self_labeling.py` |
| Full summary | `artifacts/head_importance_self_labeling/full_summary.json` |
| Head scores | `artifacts/head_importance_self_labeling/full_head_scores.csv` |
| Training log | `artifacts/head_importance_self_labeling/full_train.log` |
| Console log (with `/usr/bin/time -v`) | `logs/full_run_console_fixed_sweep.log` |
| Smoke summary | `artifacts/head_importance_self_labeling/smoke_summary.json` |
| Pip install log (torch) | `logs/pip_torch_cpu.log` |
| Pip install log (numeric) | `logs/pip_numeric.log` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T132518515482+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T132518515482+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T132518515482+0000/paper_manifest.json` |
