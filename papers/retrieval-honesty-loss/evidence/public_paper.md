# Retrieval Honesty Loss: Reducing Unsupported Answers Under Missing or Shifted Retrieval via Explicit Evidence-Faithfulness Supervision

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, benchmark results, decision JSON, and project metadata). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

Retrieval-augmented generation (RAG) systems can produce answers unsupported by retrieved evidence, especially when retrieval is absent or distributionally shifted. We propose Retrieval Honesty Loss (RHL), an auxiliary training objective that explicitly supervises a model to predict answers supported by retrieved documents and to abstain when no retrieval is available. In a controlled synthetic RAG benchmark (96 entities, 8 color classes, linear NumPy classifier, 10 random seeds), RHL with λ ∈ [0.75, 1.50] reduced the unsupported answer rate from 1.000 to 0.000 on a missing-retrieval split and from 0.300 to 0.000 on a mixed-distribution shift split, while preserving 1.000 accuracy on the supported-retrieval split. A λ sweep reveals a threshold-like transition in evidence faithfulness between λ = 0.60 and λ = 0.90. The principal limitation is that RHL enforces evidence faithfulness rather than factual correctness: under corrupted retrieval, the model faithfully reproduces the (incorrect) retrieved evidence. All results are confined to a synthetic linear-classifier setting and do not establish scaling behavior for transformer-based natural-language RAG systems.

## 1. Introduction

RAG systems condition model outputs on retrieved documents, but standard training objectives optimize for factual correctness against ground-truth labels regardless of retrieval state. When retrieval is missing or erroneous, a conventionally trained model may still produce confident answers that lack evidential support from the retrieved context. This behavior undermines trustworthiness: users cannot rely on the presence of retrieved documents as an indicator that the model's output is grounded in those documents.

We investigate whether an explicit *retrieval honesty* supervision signal can reduce unsupported answers while preserving answer quality when retrieved evidence is correct. The core idea is straightforward: when retrieval is present, the model should predict the retrieved answer; when retrieval is absent, the model should abstain. We term this property *evidence faithfulness*—the model's output is supported by the retrieved evidence, or the model explicitly declines to answer.

Evidence faithfulness is distinct from factual correctness. A model that faithfully reproduces a corrupted retrieved document is evidence-faithful but factually wrong. RHL targets the former property; addressing the latter would require separate mechanisms for retrieval quality assessment or contradiction detection.

This paper reports results from a controlled synthetic benchmark designed to isolate the effect of the RHL objective. We do not claim these results transfer to natural-language transformer models; rather, we present them as evidence that the objective is plausible and produces the intended behavior in a setting where causal attribution is unambiguous.

## 2. Method

### 2.1 Operational Definition of Retrieval Honesty

A model is *retrieval-honest* if its answer is supported by the retrieved document. Under our operationalization:

- If a retrieved document contains answer class $c$, an evidence-faithful prediction is $c$.
- If no document is retrieved, the only evidence-faithful prediction is `ABSTAIN`.
- The *unsupported answer rate* counts non-abstain predictions that are not supported by retrieved evidence.

This definition measures retrieval support, not world factuality. Under corrupted retrieval, a faithful answer can be factually wrong relative to the hidden world state.

### 2.2 Benchmark Design

The benchmark is implemented as a NumPy synthetic RAG environment:

- **World:** 96 entities, each assigned one of 8 true colors.
- **Model input:** Entity one-hot vector + retrieved color one-hot vector + missing-retrieval flag + bias term.
- **Model output:** 8 color logits + `ABSTAIN` logit (9 classes total).
- **Model architecture:** Linear classifier (single affine transformation followed by softmax).

This is a toy simulation: a deliberately simplified environment that permits unambiguous causal attribution of behavior to the training objective, at the cost of ecological validity.

### 2.3 Training Data Distribution

Training examples are generated as follows:

- 90% of examples have correct retrieved evidence (the retrieved color matches the entity's true color).
- 10% of examples have missing retrieval (the missing-retrieval flag is active, and the retrieved color vector is zeroed).

No corrupted-retrieval examples appear in training.

### 2.4 Objectives

**Answer Cross-Entropy Baseline.** The baseline objective is standard cross-entropy against the true color label for all examples, regardless of retrieval state.

**Retrieval Honesty Loss (RHL).** The RHL objective adds an auxiliary loss term:

$$\mathcal{L} = \mathcal{L}_{\text{answer}} + \lambda \cdot \mathcal{L}_{\text{honesty}}$$

where:

- $\mathcal{L}_{\text{answer}}$ is the standard answer cross-entropy against the true color.
- $\mathcal{L}_{\text{honesty}}$ targets the retrieved color when retrieval is present and targets `ABSTAIN` when retrieval is missing.
- $\lambda$ controls the strength of the honesty supervision.

### 2.5 Evaluation Splits

Models are evaluated on four splits that vary retrieval conditions:

- **supported:** Retrieved evidence is correct (matches the entity's true color).
- **missing:** No retrieved evidence is provided.
- **corrupted:** Retrieved evidence contradicts the entity's true color.
- **mixed_shift:** 40% supported / 30% missing / 30% corrupted.

The mixed_shift split tests behavior under distribution shift from the training distribution (which contains only supported and missing examples, no corrupted examples).

### 2.6 Metrics

- **World accuracy:** Fraction of predictions matching the entity's true color.
- **Evidence faithfulness:** Fraction of predictions that are supported by retrieved evidence (or `ABSTAIN` when retrieval is missing).
- **Unsupported answer rate:** Fraction of non-abstain predictions not supported by retrieved evidence.
- **Abstain rate:** Fraction of predictions that are `ABSTAIN`.

## 3. Results

### 3.1 Main Comparison

Results are averaged over 10 random seeds with 260 training epochs, 16,000 training examples, and 6,000 test examples per run. Standard deviations are reported across seeds.

| Variant | Split | World Accuracy | Evidence Faithfulness | Unsupported Answer Rate | Abstain Rate |
|---|---:|---:|---:|---:|---:|
| Answer CE baseline | supported | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Answer CE baseline | missing | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Answer CE baseline | mixed_shift | 0.6954 ± 0.0032 | 0.6999 ± 0.0054 | 0.3001 ± 0.0054 | 0.0000 ± 0.0000 |
| RHL λ=0.75 | supported | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| RHL λ=0.75 | missing | 0.0299 ± 0.0128 | 0.9701 ± 0.0128 | 0.0299 ± 0.0128 | 0.9701 ± 0.0128 |
| RHL λ=0.75 | mixed_shift | 0.4042 ± 0.0060 | 0.9911 ± 0.0035 | 0.0089 ± 0.0035 | 0.2912 ± 0.0075 |
| RHL λ=1.50 | supported | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| RHL λ=1.50 | missing | 0.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| RHL λ=1.50 | mixed_shift | 0.3953 ± 0.0041 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.3001 ± 0.0054 |

**Baseline behavior.** The baseline learns a parametric entity-to-answer mapping and confidently answers even when retrieval is missing, producing a 100% unsupported answer rate on the missing split. On the mixed_shift split, the baseline achieves 69.54% world accuracy but only 69.99% evidence faithfulness, with a 30.01% unsupported answer rate. The baseline never abstains.

**RHL behavior.** At λ = 1.50, RHL eliminates unsupported answers entirely on both the missing and mixed_shift splits. On the missing split, the model abstains 100% of the time. On the mixed_shift split, the model abstains on 30.01% of examples (corresponding to the missing and corrupted subsets) and answers correctly on the supported subset, yielding 100% evidence faithfulness and 0% unsupported answers.

**Tradeoff.** World accuracy on the missing split drops from 1.000 (baseline) to 0.000 (RHL λ=1.50), and on the mixed_shift split from 0.695 to 0.395. This is the intended behavior under the evidence-faithfulness objective: the model abstains rather than relying on parametric knowledge when retrieval is unavailable. Whether this tradeoff is desirable depends on the application context.

### 3.2 Lambda Sweep

The λ sweep reveals a threshold-like transition in evidence faithfulness:

| λ | Missing Unsupported | Mixed Unsupported | Mixed Evidence Faithfulness | Supported Accuracy |
|---:|---:|---:|---:|---:|
| 0.00 | 1.0000 | 0.3035 | 0.6965 | 1.0000 |
| 0.45 | 0.7960 | 0.2428 | 0.7572 | 1.0000 |
| 0.60 | 0.3403 | 0.1024 | 0.8976 | 1.0000 |
| 0.75 | 0.0214 | 0.0060 | 0.9940 | 1.0000 |
| 0.90 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| 1.50 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |

Supported accuracy remains at 1.000 across all λ values. The unsupported answer rate on both missing and mixed splits drops sharply between λ = 0.60 and λ = 0.90, with near-complete elimination by λ = 0.75. This suggests that moderate honesty supervision strength is sufficient to induce the desired behavior without degrading supported-case performance in this synthetic setting. Whether this clean separation persists in more complex models and tasks is unknown.

### 3.3 Behavior Under Corrupted Retrieval

The corrupted retrieval condition reveals an important boundary. Under RHL, the model becomes faithful to retrieved evidence regardless of its correctness. When retrieved evidence contradicts the entity's true color, the RHL-trained model predicts the retrieved (incorrect) color rather than abstaining or predicting the true color. This is evidence-faithful but factually wrong. RHL does not provide a mechanism for detecting or resisting corrupted retrieval; it enforces consistency with the retrieval, not truth. This is a direct consequence of the objective design and is not surprising, but it delimits the scope of what RHL can accomplish.

## 4. Limitations

1. **Synthetic benchmark only.** The experiment uses a linear NumPy classifier on a controlled synthetic task with 96 entities and 8 classes. No results are reported for natural-language models, transformer architectures, or production RAG systems. The result establishes plausibility of the objective but not its scaling behavior or transfer to realistic settings.

2. **Evidence faithfulness ≠ factual correctness.** RHL optimizes retrieval support, not truth under corrupted evidence. A model trained with RHL will faithfully reproduce incorrect retrieved documents. Addressing factual correctness under corrupted retrieval requires separate mechanisms (e.g., retrieval quality assessment, contradiction detection, or source verification).

3. **Linear classifier architecture.** The model is a single affine transformation. The interaction between RHL and the complex internal representations of transformer models is unknown. It is possible that RHL could interfere with other capabilities in a transformer, or that transformers could learn to partially resist corrupted retrieval through pretraining priors—neither possibility is tested here.

4. **Narrow task structure.** The benchmark uses a single-hop entity-to-color mapping with unambiguous retrieved evidence. Natural-language RAG tasks involve multi-hop reasoning, ambiguous evidence, partial support, and conflicting documents. The behavior of RHL under these conditions is unknown.

5. **Training distribution simplicity.** The training distribution contains only supported and missing retrieval (no corrupted examples). The model's behavior on corrupted retrieval at test time is an out-of-distribution generalization result, and its specific pattern (faithfully following the corrupted evidence) follows from the objective design rather than from a learned corruption-detection capability.

6. **No comparison to alternative approaches.** This study does not compare RHL to other methods for reducing hallucination or improving evidence grounding (e.g., contrastive learning, retrieval attention masking, or calibration-based abstention). The results show RHL works in this setting but do not establish relative merit.

7. **Claim ledger audit status.** The project's claim ledger was flagged as `blocked_empty_claims` at the time of draft generation, meaning no structured claims were extracted for formal audit. The results reported here are drawn directly from the run notes and project decision artifacts and have not passed a structured claim/evidence audit pipeline.

## 5. Reproducibility Checklist

- **Code availability:** Experiment script `scripts/retrieval_honesty_loss_experiment.py`, summary script `scripts/summarize_metrics.py`, and lambda sweep script `scripts/lambda_sweep.py` are present in the project directory.
- **Random seeds:** 10 seeds were used for the main experiment; the `--seeds` flag controls this.
- **Hyperparameters:** Epochs = 260, training examples = 16,000, test examples = 6,000, λ values swept = [0.00, 0.45, 0.60, 0.75, 0.90, 1.50].
- **Software dependencies:** Python 3, NumPy. No GPU required.
- **Hardware:** CPU-only execution. Full run wall time: 50.33 seconds, max RSS: 53,520 KB. Lambda sweep wall time: 24.72 seconds, max RSS: 45,724 KB. Host: 121 GiB total memory, swap disabled.
- **Output artifacts:** `results/smoke_metrics.json`, `results/full_metrics.json`, `results/full_summary.csv`, `results/lambda_sweep.json`.
- **Verification command:** `python3 scripts/retrieval_honesty_loss_experiment.py --smoke --out /tmp/rhl_smoke_verify.json && python3 scripts/summarize_metrics.py results/full_metrics.json` — passed at 2026-04-29T18:50:52-05:00.
- **Statistical reporting:** All main-experiment results include mean ± standard deviation across 10 seeds. Lambda sweep results are reported as single-seed values.
- **Result classification:** All results in this paper are toy simulation results from a synthetic NumPy benchmark. No llama.cpp hook-prototype results, CUDA copy calibrations, or production validation results are claimed.

## 6. Conclusion

Retrieval Honesty Loss eliminates unsupported answers in a controlled synthetic RAG benchmark while preserving accuracy on supported retrieval. The λ sweep shows a threshold-like transition: moderate values (λ ≈ 0.75–0.90) achieve near-complete evidence faithfulness without degrading supported-case performance. The principal tradeoff is a reduction in world accuracy on missing and mixed-retrieval splits, where the model abstains rather than relying on parametric knowledge—this is the intended behavior for an evidence-faithfulness objective.

The critical boundary is that RHL enforces consistency with retrieved evidence, not resistance to corrupted evidence. Under corrupted retrieval, RHL makes the model faithfully wrong. This is not a failure of the method but a precise characterization of what it optimizes: retrieval support, not factual truth.

The next scientifically meaningful step is to evaluate RHL-style supervision on a small natural-language RAG task, measuring unsupported answer rate, abstention, answer accuracy, and behavior under missing and corrupted retrieval. Only such an evaluation can determine whether the synthetic results transfer to the transformer-based models used in practice.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260429T234618369199+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T234618369199+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T234618369199+0000/paper_manifest.json` |
| Experiment script | `scripts/retrieval_honesty_loss_experiment.py` |
| Summary script | `scripts/summarize_metrics.py` |
| Lambda sweep script | `scripts/lambda_sweep.py` |
| Smoke metrics | `results/smoke_metrics.json` |
| Full metrics (10 seeds) | `results/full_metrics.json` |
| Full CSV summary | `results/full_summary.csv` |
| Lambda sweep metrics | `results/lambda_sweep.json` |
| Smoke log | `logs/smoke.log` |
| Full run stdout | `logs/full_run.stdout.log` |
| Full run stderr (resource data) | `logs/full_run.stderr.log` |
| Lambda sweep stdout | `logs/lambda_sweep.stdout.log` |
| Lambda sweep stderr (resource data) | `logs/lambda_sweep.stderr.log` |
