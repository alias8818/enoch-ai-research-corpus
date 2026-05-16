# Backend-Switched Verifier Pretraining: Reducing Shortcut Learning via Multi-Backend Rendering of Identical Semantic Cases

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision logs, benchmark outputs). The operator claims no personal authorship credit for the writing or results beyond releasing the artifacts. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has validated its claims.

---

## Abstract

We investigate whether training a verifier on multiple backend renderings of the same semantic verification case—where backend identity is rendered non-predictive of the correctness label—reduces backend-specific shortcut learning relative to single-backend training or naively pooled multi-backend training with label/backend confounds. Using a synthetic arithmetic verification benchmark with three training backends (`alpha_direct`, `beta_verbose`, `gamma_json`) and one held-out backend (`delta_markdown`), we train TF-IDF + logistic regression verifiers under three regimes and evaluate across in-domain, seen-alternate, and held-out backends. Backend-switched training yields a mean accuracy gain of +0.025 over single-backend training and +0.053 over pooled-biased training on seen alternate backends, with improved calibration (lower ECE). However, all regimes perform near chance on the held-out `delta_markdown` backend, and backend-switched training slightly underperforms single-backend training on held-out ROC-AUC (Δ = −0.008). These results support the narrow mechanism that backend switching suppresses shortcut learning on backends represented during training, but do not support a claim that switching alone generalizes to substantially novel held-out backends under a bag-of-ngram verifier.

## Introduction

Verifier models trained to assess the correctness of proposed solutions risk learning superficial correlations between rendering format and correctness labels rather than evaluating semantic content. When certain backends systematically correlate with correct or incorrect labels in the training distribution, a verifier can exploit these shortcuts, achieving high in-domain accuracy while failing on alternate renderings of the same semantic content.

We formalize this concern as a **backend/label confound** problem and propose **backend-switched pretraining** as a mitigation: render each semantic training case under all available training backends with the same correctness label, thereby making backend identity a non-predictive feature. This study asks:

1. Does backend-switched training reduce shortcut learning relative to single-backend training?
2. Does it improve over naively pooled multi-backend training where backend identity correlates with label?
3. Does the benefit generalize to a held-out backend not seen during training?

We test these questions using a controlled synthetic benchmark rather than production LLM outputs, isolating the mechanism from confounds introduced by model-generated text quality variation. This is a local proxy experiment; it is not a claim about production LLM verifier pretraining. It is useful for testing the core mechanism: backend-switching removes label/backend shortcuts in the training distribution.

## Method

### Benchmark Design

We construct a synthetic arithmetic verification benchmark. Each semantic case is a triple `(expression, proposed_answer, correctness_label)`. Expressions are drawn from a space of simple arithmetic operations; proposed answers are either correct or incorrect with balanced label frequency.

Each semantic case is rendered into textual form by one of four backend-specific formatters:

- **`alpha_direct`**: Plain-text inline format (e.g., "Compute 7 + 3. Proposed answer: 10. Correct? yes")
- **`beta_verbose`**: Verbose natural-language format with explanatory framing
- **`gamma_json`**: JSON-structured format with fields for expression, answer, and label
- **`delta_markdown`**: Markdown-formatted with headers and code blocks (held out at train time)

### Training Regimes

Three training regimes are compared:

1. **`single_alpha`**: Train only on `alpha_direct` renderings. This is the baseline with no multi-backend exposure.
2. **`pooled_biased`**: Pool renderings from `alpha_direct`, `beta_verbose`, and `gamma_json`, but with a deliberate correlation between backend identity and correctness label. This simulates a naive multi-backend collection where shortcuts are available.
3. **`backend_switched`**: Render each semantic training case under all three training backends (`alpha_direct`, `beta_verbose`, `gamma_json`) with the same correctness label. Backend identity is thus non-predictive of label. Training set size is 3× the number of semantic cases.

### Model

We use a TF-IDF vectorizer (character and word n-grams) followed by logistic regression. This model class is deliberately chosen as a weak semantic verifier: it can capture surface-level lexical patterns but lacks explicit arithmetic or semantic parsing capacity. This makes it a suitable probe for shortcut learning, as it will readily exploit format/label correlations if available, but cannot evaluate the underlying arithmetic.

### Evaluation

We evaluate on four splits:

- **In-domain** (`alpha_direct`): Same backend as `single_alpha` training.
- **Seen alternate** (`beta_verbose`, `gamma_json`): Backends present in `pooled_biased` and `backend_switched` training but not in `single_alpha` training.
- **Held-out** (`delta_markdown`): Backend not seen during training under any regime.

Metrics: accuracy, ROC-AUC, Brier score, and Expected Calibration Error at 10 bins (ECE@10).

### Experimental Protocol

- **Smoke test**: 1 seed, 80 train / 80 eval examples per regime.
- **Full run**: 10 seeds, 2000 train semantic cases / 1000 eval examples per regime. Results reported are from the full 10-seed run.
- Hardware: `gx10-efe8`, Linux aarch64 6.17.0-1014-nvidia, ~121.6 GiB total memory, swap disabled. Full run elapsed time: 18.16 s. Peak process RSS: 279,436 KiB.

## Results

### In-Domain Performance (alpha_direct)

| Regime | Accuracy | ROC-AUC | Brier | ECE@10 |
|---|---:|---:|---:|---:|
| single_alpha | 0.5671 | 0.5985 | 0.2499 | 0.0871 |
| pooled_biased | 0.5022 | 0.5524 | 0.3641 | 0.3390 |
| backend_switched | 0.5630 | 0.5951 | 0.2539 | 0.1024 |

`single_alpha` achieves the highest in-domain accuracy and ROC-AUC, as expected given its exclusive exposure to the `alpha_direct` format. `pooled_biased` performs substantially worse, likely because the backend/label confound introduces noise that degrades even in-domain performance. `backend_switched` closely matches `single_alpha` in-domain (accuracy Δ = −0.004, ROC-AUC Δ = −0.003), suggesting that the 3× expansion with format diversity does not materially harm in-domain discrimination.

### Seen Alternate Backends

| Split | Regime | Accuracy | ROC-AUC | Brier | ECE@10 |
|---|---|---:|---:|---:|---:|
| beta_verbose | single_alpha | 0.5344 | 0.5956 | 0.2651 | 0.1457 |
| beta_verbose | pooled_biased | 0.4999 | 0.5423 | 0.3631 | 0.3369 |
| beta_verbose | backend_switched | 0.5617 | 0.5934 | 0.2494 | 0.0792 |
| gamma_json | single_alpha | 0.5216 | 0.5684 | 0.2572 | 0.1079 |
| gamma_json | pooled_biased | 0.5002 | 0.5083 | 0.3634 | 0.3317 |
| gamma_json | backend_switched | 0.5447 | 0.5668 | 0.2546 | 0.0792 |

`backend_switched` achieves the highest accuracy on both seen alternate backends. Mean seen-alternate accuracy gain versus `single_alpha` is **+0.025** and versus `pooled_biased` is **+0.053**. Calibration is also substantially better: ECE@10 for `backend_switched` is 0.079 on both alternate backends, compared to 0.146 / 0.108 for `single_alpha` and 0.337 / 0.332 for `pooled_biased`.

`pooled_biased` performs near chance on both alternate backends (accuracy ≈ 0.500), consistent with the interpretation that the model exploits the backend/label confound during training and this shortcut fails on alternate backends where the confound does not hold.

### Held-Out Backend (delta_markdown)

| Regime | Accuracy | ROC-AUC | Brier | ECE@10 |
|---|---:|---:|---:|---:|
| single_alpha | 0.5088 | 0.5122 | 0.2667 | 0.1071 |
| pooled_biased | 0.4976 | 0.4958 | 0.2666 | 0.1077 |
| backend_switched | 0.5005 | 0.5047 | 0.2803 | 0.1488 |

All regimes perform near chance on the held-out `delta_markdown` backend. `backend_switched` slightly underperforms `single_alpha` on ROC-AUC (Δ = −0.008) and has worse calibration (ECE@10 = 0.149 vs. 0.107). No regime demonstrates meaningful generalization to a truly novel backend format.

### Throughput

Mean fit throughput decreases with training set expansion: `single_alpha` at ~17,769 examples/s, `pooled_biased` at ~11,155 examples/s, and `backend_switched` at ~9,405 examples/s. The 3× expansion in `backend_switched` is partially offset by per-example efficiency, yielding roughly a 1.9× throughput reduction rather than the full 3×.

## Limitations

1. **Synthetic benchmark only.** All results derive from a synthetic arithmetic verification task with hand-crafted backend formatters. Generalization to real LLM-generated outputs, where backend formatting correlates with model capability and error modes, is not established.

2. **Weak verifier model.** TF-IDF + logistic regression cannot perform semantic arithmetic verification; it relies on surface lexical cues. Backend switching removes format/label shortcuts but cannot grant the model semantic parsing ability it lacks. A stronger verifier (e.g., a small transformer with arithmetic reasoning) might show different held-out generalization behavior.

3. **Limited backend diversity.** Four backends (three train, one held-out) provide minimal diversity. The held-out `delta_markdown` format may differ from training formats in ways that are particularly challenging for bag-of-ngram models (e.g., markdown headers and code blocks introduce token patterns far from training vocabulary).

4. **No real-world confound structure.** The `pooled_biased` regime uses an artificial label/backend correlation. Real multi-backend data collections may exhibit more complex or subtler confounds.

5. **Near-chance baseline performance.** Even the best in-domain accuracy (0.567) is only modestly above chance (0.500), indicating the task is difficult for this model class. Small absolute gains should be interpreted cautiously given the limited headroom.

6. **Single task domain.** Results are specific to arithmetic verification. Whether backend switching helps for code verification, factual verification, or other domains is unknown.

7. **Held-out generalization not demonstrated.** The central negative finding is that backend switching does not improve performance on a held-out backend. This limits the practical scope of the mechanism to settings where all deployment backends are represented during training.

## Reproducibility Checklist

- **Code available**: `scripts/backend_switched_verifier_experiment.py`, `scripts/summarize_backend_switched_results.py`
- **Raw results**: `results/backend_switched_verifier/full_10x2k.json`
- **Summary results**: `results/backend_switched_verifier/full_10x2k_summary.json`
- **Smoke test results**: `results/backend_switched_verifier/smoke.json`
- **Execution logs**: `logs/smoke_backend_switched_verifier.log`, `logs/full_10x2k_backend_switched_verifier.log`, `logs/summary_backend_switched_verifier.log`
- **Decision record**: `.omx/project_decision.json`
- **Seeds**: 10 independent seeds reported; smoke test at 1 seed
- **Hardware**: `gx10-efe8`, Linux aarch64 6.17.0-1014-nvidia, ~121.6 GiB RAM, swap disabled
- **Runtime**: 18.16 s wall-clock for full 10-seed run
- **Memory**: Peak RSS 279,436 KiB; system memory utilization 4.0%
- **Random seed control**: Seeds passed via `--seeds` flag; exact seed values recorded in raw JSON output
- **Determinism**: TF-IDF + logistic regression is deterministic given fixed seed and input; variance across seeds reflects training data sampling

## Conclusion

Backend-switched rendering—presenting each semantic verification case under all training backends with the same label—reduces backend/label shortcut learning in a controlled synthetic benchmark. On seen alternate backends, backend-switched training improves mean accuracy by +0.025 over single-backend training and +0.053 over pooled but confounded multi-backend training, with substantially better calibration.

However, the benefit does not generalize to a held-out backend format. All regimes perform near chance on `delta_markdown`, and backend-switched training slightly underperforms single-backend training on held-out ROC-AUC (Δ = −0.008). This negative finding is consistent with the interpretation that removing format shortcuts is necessary but not sufficient: a verifier that lacks the semantic capacity to evaluate the underlying content cannot generalize to a format where no learned surface cues apply.

The mechanism-level finding is **promising but limited**. Backend switching appears to be an effective debiasing strategy for backends represented during training, but its utility for truly novel formats depends on the verifier possessing sufficient semantic abstraction capacity—a property not provided by the bag-of-ngram model tested here. Future work should: (1) replace the bag-of-ngram verifier with a small transformer or feature extractor with explicit arithmetic/semantic parsing capacity; (2) add backend-invariance metrics over paired renderings of identical semantic cases; (3) evaluate on real model/backend outputs rather than synthetic renderers; and (4) maintain backend-balanced and counter-biased splits to avoid shortcut false positives. Final scientific closure for production value requires external evidence: real verifier pretraining data or real multi-backend generation traces with correctness labels.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `scripts/backend_switched_verifier_experiment.py` |
| Summary script | `scripts/summarize_backend_switched_results.py` |
| Smoke test raw results | `results/backend_switched_verifier/smoke.json` |
| Full run raw results | `results/backend_switched_verifier/full_10x2k.json` |
| Full run summary | `results/backend_switched_verifier/full_10x2k_summary.json` |
| Smoke test log | `logs/smoke_backend_switched_verifier.log` |
| Full run log | `logs/full_10x2k_backend_switched_verifier.log` |
| Summary log | `logs/summary_backend_switched_verifier.log` |
| Project decision | `.omx/project_decision.json` |
| Project metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260501T222148916475+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T222148916475+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T222148916475+0000/paper_manifest.json` |
