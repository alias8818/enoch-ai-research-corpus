# Draft Token Value Distillation: Offline Training of a Selective Verification Helper for Speculative Decoding

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision logs, metric files, and script outputs). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

Speculative decoding accelerates autoregressive inference by having a small draft model propose tokens that a larger target model verifies in parallel. However, every verification step incurs cost proportional to the target model, regardless of whether the draft was already acceptable. We investigate whether an offline-trained lightweight value predictor—a "helper"—can anticipate which draft tokens are likely to match the target model, enabling selective verification that skips the target model when the draft is predicted to be sufficient. In a controlled proxy experiment using n-gram character language models on the Tiny Shakespeare corpus, a gradient-boosted helper trained on 100,000 offline draft traces achieves ROC-AUC of 0.853 (versus 0.593 for raw draft confidence) and average precision of 0.770 (versus 0.523). At approximately 75% target-model call rate, the helper policy preserves 94.34% teacher-greedy agreement while skipping 25.79% of target calls, compared to 88.98% agreement for a static draft-confidence baseline at the same budget. These results provide positive evidence for the offline value-distillation mechanism in a simplified setting, but they do not constitute validation on real transformer models or under exact speculative decoding acceptance semantics. We detail the proxy setup, results, and specific gaps that must be closed before drawing conclusions about production speculative decoding.

## Introduction

Speculative decoding reduces the latency of autoregressive generation by having a small draft model propose candidate tokens that a larger target model verifies in a single forward pass. When the draft is accepted, multiple tokens are produced per target-model invocation; when rejected, the target model's distribution is sampled at the rejection point. The expected speedup depends on the acceptance rate and the draft-target latency ratio.

A key inefficiency in standard speculative decoding is that the target model is invoked for every draft span, even when the draft token is highly likely to be acceptable. If one could predict—cheaply—which draft tokens require target verification and which do not, unnecessary target invocations could be skipped, reducing compute and memory bandwidth.

This paper explores a specific mechanism: **offline training of a small value predictor ("helper") from recorded draft-target traces**. The helper is trained on features available at draft time (i.e., without target-model computation) to predict whether the draft's proposed token matches the target model's greedy selection. At inference, the helper scores each draft token; if the score exceeds a threshold, the target verification is skipped and the draft token is accepted directly.

We emphasize at the outset that this is a mechanism probe in a simplified setting, not a complete solution for production speculative decoding. The experiment uses n-gram character language models rather than transformers, and the quality metric is teacher-greedy token agreement rather than exact speculative acceptance probabilities or downstream task quality. The results are promising but not conclusive.

## Method

### Proxy Setup

To isolate the value-prediction mechanism from the complexities of transformer inference and exact speculative decoding, we construct a minimal proxy using character-level n-gram language models.

**Dataset.** The Tiny Shakespeare character stream (approximately 1.1 MB of text), obtained from the standard `char-rnn` repository. The first 80% of the corpus is used for model training; the remaining 20% is held out for trace generation and evaluation.

**Teacher model.** A 5-gram character language model trained on the training split. At each position, the teacher assigns probability over the vocabulary based on the preceding four characters.

**Draft model.** A 2-gram character language model trained on the same training split. The draft model conditions only on the immediately preceding character.

**Offline trace generation.** For each position in the held-out set, we record:

- The draft model's top-1 predicted token and its probability (the "draft confidence").
- Additional draft-only features: the entropy of the draft distribution, the rank of the draft's top token in the draft distribution, and the margin between the top two draft probabilities.
- The label: whether the draft's top-1 token matches the teacher's greedy token at that position.

This yields a binary classification dataset where all input features are computable from the draft model alone, and the label requires the teacher model.

**Helper model.** A `HistGradientBoostingClassifier` (from scikit-learn) trained on 100,000 trace positions from the held-out set, using draft-only features to predict the binary match label. This model is intentionally lightweight: it operates on a small feature vector and is fast to evaluate.

**Baselines.** We compare against:

1. **Always teacher:** Invoke the teacher at every position. Teacher-greedy match is 100% by definition.
2. **Always draft:** Never invoke the teacher. Teacher-greedy match equals the raw draft accuracy.
3. **Static draft-confidence threshold:** Skip the teacher when the draft model's top-token probability exceeds a threshold. This is the natural baseline that uses only the draft model's own confidence signal.
4. **Random same-budget threshold:** Skip the teacher at random positions to match the helper's call rate, providing a budget-matched lower bound.

### Online Policy

The helper policy operates as follows: at each position, compute the helper's predicted probability that the draft token matches the teacher. If this probability exceeds a threshold $\tau$, skip the teacher and accept the draft token; otherwise, invoke the teacher. By varying $\tau$, we trace a curve of teacher-call rate versus teacher-greedy match rate.

The same procedure applies to the static draft-confidence baseline, substituting the draft model's top-token probability for the helper's score.

### Evaluation Metrics

- **ROC-AUC:** Discrimination ability of the helper versus static draft confidence as binary classifiers for the match label.
- **Average precision:** Area under the precision-recall curve, which is more informative under class imbalance.
- **Teacher-greedy match rate:** Fraction of positions where the accepted token (whether from draft or teacher) matches the teacher's greedy token.
- **Accepted draft precision:** Among positions where the teacher is skipped, the fraction where the draft token matches the teacher's greedy token.
- **Teacher call rate:** Fraction of positions where the teacher is invoked.

### Hardware and Reproducibility

All experiments ran on a single NVIDIA GB10 system (CUDA 13.0) with swap disabled. The proxy experiment is CPU-only (no GPU utilization), as it involves n-gram models and scikit-learn classifiers. Peak RSS was 307,008 KB. End-to-end throughput was 42,206 trace positions per second (wall time approximately 4.84 seconds for the full 100k train / 80k eval run). Memory available before the full run was approximately 116.6 GiB; after completion, approximately 116.6 GiB, indicating negligible memory pressure.

## Results

### Helper Discrimination

The helper substantially outperforms raw draft confidence as a predictor of whether the draft token will match the teacher's greedy token:

| Metric | Helper | Static Draft Confidence |
|---|---:|---:|
| ROC-AUC | 0.853 | 0.593 |
| Average Precision | 0.770 | 0.523 |

The helper's ROC-AUC of 0.853 indicates that the draft-only features, when combined through a learned model, carry substantial information about teacher agreement that is not captured by the draft model's own confidence score (ROC-AUC 0.593). The gap in average precision (0.770 vs. 0.523) is similarly large, indicating that the helper's precision-recall tradeoff is materially better across operating points.

### Policy Tradeoffs

The following table reports teacher-greedy match rate and accepted draft precision at approximately 50% and 75% teacher-call rates, for both the helper policy and the static draft-confidence baseline:

| Policy | Teacher Call Rate | Teacher Calls Skipped | Teacher-Greedy Match | Accepted Draft Precision |
|---|---:|---:|---:|---:|
| Always teacher | 100.00% | 0.00% | 100.00% | 100.00% |
| Always draft | 0.00% | 100.00% | 38.89% | 38.89% |
| Helper @ ~50% calls | 49.90% | 50.10% | 82.55% | 65.17% |
| Static conf. @ ~50% calls | 48.90% | 51.10% | 72.52% | 46.22% |
| Helper @ ~75% calls | 74.21% | 25.79% | 94.34% | 78.05% |
| Static conf. @ ~75% calls | 74.84% | 25.16% | 88.98% | 56.20% |

At the ~50% teacher-call budget, the helper preserves 82.55% teacher-greedy agreement versus 72.52% for static confidence—a 10.03 percentage-point improvement. At the ~75% budget, the gap is 94.34% versus 88.98%—a 5.36 percentage-point improvement. The accepted draft precision column shows that when the helper decides to skip the teacher, its decision is correct 65.17% of the time (at ~50% budget) versus 46.22% for static confidence.

The always-draft baseline achieves only 38.89% teacher-greedy match, confirming that the draft model alone is a poor substitute for the teacher and that selective verification is necessary.

### Summary of Findings

The central positive result is that a lightweight helper, trained offline on draft-target traces, can predict draft token value substantially better than the draft model's own confidence. At matched teacher-call budgets, the helper policy preserves meaningfully more teacher agreement than a static confidence threshold.

However, the helper does not achieve perfect discrimination, and the policy tradeoff is real: at ~50% teacher-call rate, the helper policy still loses 17.45 percentage points of teacher agreement relative to always-teacher. The helper's value lies in achieving a more favorable point on the teacher-call versus agreement frontier, not in eliminating the tradeoff entirely.

## Limitations

We enumerate the specific limitations of this experiment with care, as each represents a gap between the current proxy result and a validated mechanism for real speculative decoding.

1. **Proxy models, not transformers.** The teacher and draft are n-gram character language models, not transformer LLMs. The feature space, distributional properties, and error modes of n-gram models differ substantially from those of transformers. The helper's discrimination advantage may not transfer.

2. **Greedy-match labels, not acceptance probabilities.** The binary label is whether the draft's top-1 token matches the teacher's greedy token. In real speculative decoding, acceptance is governed by the full probability ratio between target and draft distributions, not just greedy agreement. A draft token that matches the teacher's mode but with different probability mass may still be rejected under exact speculative decoding, and conversely, a non-greedy draft token may be accepted if it falls within the target distribution's support.

3. **Selective approximation, not lossless decoding.** The helper policy skips teacher calls entirely for high-confidence draft tokens. This means the output distribution is a mixture of teacher-verified and draft-only tokens, which does not preserve the target model's distribution exactly. Standard speculative decoding is distribution-preserving; this policy is not. The quality implications of this distributional shift are not evaluated here.

4. **No downstream quality evaluation.** Teacher-greedy match rate is a proxy for output quality, not a direct measure. We do not evaluate perplexity, BLEU, human preference, or any task-specific metric on generated text.

5. **Single dataset, single model pair.** All results are on Tiny Shakespeare with one specific 5-gram/2-gram pair. Generalization to other corpora, vocabularies, or model size ratios is unknown.

6. **No latency measurement.** The throughput figure (42,206 positions/sec) reflects the proxy experiment's speed, not the wall-clock latency impact of selective verification in a real inference pipeline. The helper's overhead, the cost of a mis-skip, and the interaction with batched GPU inference are all unmeasured.

7. **Helper model choice.** The `HistGradientBoostingClassifier` is a reasonable choice for a proxy but may not meet the latency budget for online inference in production settings. The feasibility of a sufficiently fast helper (e.g., a small neural network or lookup table) remains to be demonstrated.

8. **Random seeds not fixed.** The reported runs did not explicitly set random seeds. Exact numerical reproduction may vary across runs, though the magnitude of the observed effects suggests the directional findings are robust to this concern.

9. **Train-eval split overlap concern.** The trace positions used for helper training are drawn from the held-out corpus (the same 20% split used for evaluation). The specific positions used for training versus evaluation within that split should be disjoint, but this separation was not explicitly verified in the reported logs, introducing a potential data-leakage concern.

## Reproducibility Checklist

- **Code available:** The experiment script is at `scripts/draft_token_value_distill.py` within the project directory.
- **Dataset:** Tiny Shakespeare, publicly available at `https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt`.
- **Random seeds:** Not explicitly fixed in the reported runs. This is a gap; exact numerical reproduction may vary.
- **Software versions:** Python 3 with scikit-learn (specific version recorded in `logs/00_system_snapshot.log`).
- **Hardware:** NVIDIA GB10, CUDA 13.0, swap disabled, ~116 GiB available memory.
- **Command to reproduce full run:**
  ```
  python3 scripts/draft_token_value_distill.py \
    --train-traces 100000 --eval-traces 80000 \
    --out artifacts/full_results_100k_80k.json
  ```
- **Smoke test command:**
  ```
  python3 scripts/draft_token_value_distill.py --smoke \
    --out artifacts/smoke_results.json
  ```
- **Artifact files:** See Referenced Artifacts section below.

## Conclusion

This paper presents evidence that offline draft-token value distillation is a viable mechanism in a controlled setting. A helper trained on 100,000 offline draft-target traces predicts whether a draft token will match the teacher's greedy selection with ROC-AUC of 0.853, substantially exceeding the draft model's own confidence signal (ROC-AUC 0.593). At approximately 75% teacher-call rate, the helper policy preserves 94.34% teacher-greedy agreement while skipping 25.79% of teacher calls, compared to 88.98% agreement for a static confidence baseline at the same budget.

However, this is a mechanism probe in a simplified proxy, not a validated technique for production speculative decoding. The models are n-gram character LMs, the labels are greedy matches rather than exact acceptance probabilities, the policy is distributionally approximate rather than lossless, and no downstream quality or real-latency measurements are reported. Each of these gaps must be closed before drawing conclusions about practical benefit.

The recommended next step is a real-model validation: apply the same trace-helper-policy pipeline to a small transformer draft/target pair under actual speculative decoding, measuring target acceptance length, wall-clock tokens per second, memory utilization, and downstream task quality. Only such an experiment can determine whether the discrimination advantage observed here transfers to the setting where it would matter.

---

## Referenced Artifacts

The following local files constitute the empirical evidence for this paper:

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Experiment script | `scripts/draft_token_value_distill.py` |
| Smoke test results | `artifacts/smoke_results.json` |
| Full run results | `artifacts/full_results_100k_80k.json` |
| System snapshot log | `logs/00_system_snapshot.log` |
| Smoke test log | `logs/01_smoke.log` |
| Full run stdout log | `logs/05_full_100k_80k.log` |
| Full run time/resource log | `logs/05_full_100k_80k.time.log` |
| Syntax verification log | `logs/06_py_compile.log` |
| Project decision JSON | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
