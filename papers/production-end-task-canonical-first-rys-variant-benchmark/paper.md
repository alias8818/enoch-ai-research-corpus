# Production End-Task Canonical-First RYS Variant Benchmark

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has approved this content.

---

## Abstract

We benchmark a production end-task canonical-first RYS (Reorder-Your-Stack) variant selection mechanism against full-model and canonical-only baselines on GSM8K answer-token completion negative log-likelihood (NLL). Using GPT-2 as the base model, we evaluate 48 partial-layer variant programs drawn from 16 source candidates on 256 GSM8K examples. The central finding is mixed: order-aware variants improve over the canonical layer ordering within 14 of 16 candidate families (canonical-is-best rate: 0.125), with a mean best-over-canonical improvement of +0.978 NLL points. However, zero of the 48 partial-layer variants beat the full GPT-2 model on absolute answer NLL (full-model baseline: 7.440). These results support the canonical-first variant mechanism as a within-family improvement over canonical-only selection, but do not support deployment of the current partial-layer GPT-2 candidate pool as a substitute for the full model. The benchmark is confined to GPT-2-scale models and answer-completion NLL; generalization to larger models or answer-accuracy metrics remains untested.

---

## 1. Introduction

Layer reordering in transformer models has been explored as a mechanism for constructing efficient or task-adapted sub-models from a pretrained base. The RYS (Reorder-Your-Stack) variant mechanism generates candidate layer programs—partial subsets of the full model's layers arranged in specified orders—and selects among them according to a scoring criterion. A canonical-first variant strategy preserves the original (canonical) layer ordering as a fallback while exploring bounded order-aware alternatives within each candidate family.

Prior work in this project lineage evaluated RYS variants using generic prompt NLL as the scoring signal. The present work shifts to an end-task evaluation: answer-token completion NLL on GSM8K, where the model is conditioned on `Question: ...\nAnswer:` prompts and scored only on the answer tokens. This metric is closer to downstream task performance than whole-sequence NLL, though it remains a proxy for answer accuracy rather than a direct accuracy measurement.

The specific questions addressed are:

1. Within a candidate family, do order-aware variants improve answer-token NLL over the canonical ordering?
2. Can any partial-layer variant approach or exceed the full model's answer-token NLL?
3. How much score variation exists within a candidate family, and does the canonical ordering reliably select the best variant?

---

## 2. Method

### 2.1 Benchmark Design

The benchmark evaluates candidate layer programs by measuring answer-token completion NLL. Each GSM8K example is formatted as:

```
Question: <problem text>
Answer: <answer text>
```

The model computes conditional log-likelihood over the answer tokens only (the tokens following `Answer:`), given the full prompt as context. This isolates the metric to the model's ability to assign probability to the correct answer continuation, rather than to the question or formatting tokens.

### 2.2 Candidate Layer Programs

Candidate layer programs were sourced from a predecessor project (`source-record-redacted`) that exported canonical-first order-aware variant manifests and measured variant summaries. These artifacts were copied into the current project directory:

- `data/acquired_canonical_first_order_aware_manifest.json` — variant manifest
- `data/acquired_canonical_first_order_aware_candidates.csv` — candidate layer program definitions
- `data/acquired_prior_measured_integrated_gpt2_variants_summary.json` — prior generic-prompt NLL measurements

Each source candidate defines a family of partial-layer programs: subsets of GPT-2's 12 transformer layers arranged in various orders. The canonical-first constraint ensures that the original layer ordering is always included as one variant per family.

### 2.3 Implementation

The benchmark was implemented in `scripts/end_task_canonical_first_benchmark.py`, which:

1. Loads GPT-2 with `--local-files-only` to use cached weights.
2. Reads candidate layer programs from the acquired CSV.
3. For each variant, constructs the corresponding sub-model by selecting and reordering layers.
4. Computes answer-token NLL on each GSM8K example.
5. Aggregates per-variant and per-family statistics.

Regression tests were added in `tests/test_end_task_canonical_first_benchmark.py` covering input-schema validation and candidate filtering.

### 2.4 Evaluation Protocol

| Parameter | Value |
|---|---|
| Base model | GPT-2 (124M) |
| Dataset | GSM8K main-test (QC-generated subset) |
| Example limit | 256 |
| Batch size | 16 |
| Max sequence length | 192 tokens |
| Metric | Answer-token completion NLL (sum over answer tokens) |
| Baseline | Full GPT-2 (all 12 layers, canonical order) |

---

## 3. Results

### 3.1 Full-Model Baseline

The full GPT-2 model achieves an answer-token NLL of **7.440** over 285 answer tokens across the 256-example evaluation set. This serves as the upper-bound reference: any partial-layer variant that approaches or exceeds this value would indicate competitive performance with fewer computational layers.

### 3.2 Variant Performance Relative to Full Model

Across 48 evaluated partial-layer GPT-2 variant rows (drawn from 16 source candidates), **0 out of 48** beat the full GPT-2 baseline in absolute answer NLL. Every partial-layer variant produces worse answer-token likelihood than the full model.

This is a negative result for the deployment hypothesis: the current candidate pool of partial-layer GPT-2 programs does not substitute for the full model on this end-task metric.

### 3.3 Within-Family Variant Comparison

The within-family comparison yields a different picture:

- **Order-aware variants beat canonical within 14 of 16 source candidates** (87.5% of families).
- **Canonical-is-best rate: 0.125** (12.5%). In only 2 of 16 families did the canonical ordering achieve the lowest NLL among all variants in that family.
- **Mean best-over-canonical improvement: +0.978** NLL points (computed as baseline canonical NLL minus best variant NLL within each family; positive values indicate the best variant outperforms canonical).
- **Mean within-family score spread: 1.589** NLL points; **max spread: 4.633**.

These figures indicate that the canonical ordering is rarely the best within its family, and that order-aware exploration consistently finds variants with lower answer-token NLL. The magnitude of improvement is non-trivial relative to the within-family spread.

### 3.4 Summary Table

| Comparison | Result |
|---|---|
| Partial variants vs. full model | 0/48 beat full GPT-2 |
| Order-aware vs. canonical (within-family) | 14/16 families favor order-aware |
| Canonical-is-best rate | 0.125 |
| Mean best-over-canonical improvement | +0.978 NLL |
| Mean within-family spread | 1.589 NLL |
| Max within-family spread | 4.633 NLL |

---

## 4. Limitations

1. **Model scale.** All results are for GPT-2 (124M parameters). Whether the canonical-first variant mechanism yields similar within-family improvements at larger scales (e.g., GPT-2 Medium, LLaMA-family models) is unknown from these artifacts.

2. **Metric proxy.** Answer-token completion NLL is a proxy for answer accuracy, not accuracy itself. A variant with lower NLL may or may not produce the correct final answer more often. Direct accuracy evaluation (exact match, numeric tolerance) was not performed.

3. **Dataset scope.** The evaluation uses 256 examples from a QC-generated subset of GSM8K. This is a small sample of a single dataset. Results may not generalize to other reasoning datasets, natural-language generation tasks, or the full GSM8K test set.

4. **Candidate pool provenance.** The 16 source candidates and their variant families were generated by a predecessor project's search procedure. The properties observed here (canonical-is-best rate, within-family spread) are contingent on that specific search output and may differ under alternative candidate generation strategies.

5. **No external replication.** These results have not been independently replicated on different hardware, software stacks, or random seeds beyond the single recorded run.

6. **Partial-layer constraint.** All variants are partial-layer programs (fewer than 12 layers). The benchmark does not address whether order-aware full-depth variants (all 12 layers in non-canonical order) would behave differently.

7. **NLL aggregation.** The reported NLL values are sums over answer tokens. Per-token averages or per-example distributions were not recorded in the summary artifacts, limiting analysis of variance and outlier behavior.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Benchmark script available | Yes: `scripts/end_task_canonical_first_benchmark.py` |
| Test suite available | Yes: `tests/test_end_task_canonical_first_benchmark.py` |
| Candidate definitions available | Yes: `data/acquired_canonical_first_order_aware_candidates.csv` |
| Variant manifest available | Yes: `data/acquired_canonical_first_order_aware_manifest.json` |
| Input data specified | Yes: `data/acquired_gsm8k_main_test_qc_generated.jsonl` |
| Raw per-variant results available | Yes: `results/end_task_gsm8k256_canonical_first_variants.csv` |
| Summary statistics available | Yes: `results/end_task_gsm8k256_canonical_first_variants_summary.json` |
| Run log available | Yes: `artifacts/end_task_benchmark_gsm8k256_run.log` |
| Model and version specified | Yes: GPT-2, loaded via HuggingFace Transformers with `--local-files-only` |
| Hardware environment recorded | Not present in artifacts |
| Random seed recorded | Not present in artifacts |
| Software dependencies pinned | Partial: `.venv` created with `uv`, cached CUDA PyTorch + Transformers installed; exact version pins not in artifacts |

---

## 6. Conclusion

This benchmark produces a mixed scientific result with two distinct findings:

**Finding 1 (Positive):** Within candidate families, order-aware variants consistently improve over the canonical layer ordering on answer-token completion NLL. The canonical ordering is the best variant in only 12.5% of families, and the mean improvement from selecting the best order-aware variant over canonical is approximately 1 NLL point. This supports the canonical-first variant mechanism as a useful within-family improvement strategy: the canonical fallback is preserved, but bounded order exploration typically finds a better variant.

**Finding 2 (Negative):** No partial-layer GPT-2 variant from the current candidate pool matches the full model on absolute answer-token NLL. The gap between the best partial-layer variants and the full-model baseline remains substantial. This does not support deploying the current partial-layer candidate pool as a replacement for the full model on GSM8K-scale reasoning tasks.

The project decision is `finalize_positive` with hypothesis status `mixed`: the canonical-first mechanism shows meaningful within-family improvement, but the candidate pool as a whole does not close the gap to the full model. The recommended next step is a distinct benchmark on larger models with direct answer-accuracy evaluation, which would constitute a materially different project rather than continued iteration on the same mechanism at GPT-2 scale.

---

## Referenced Artifacts

### Result files
- `results/end_task_canonical_first_summary.md`
- `results/end_task_gsm8k256_canonical_first_variants.csv`
- `results/end_task_gsm8k256_canonical_first_variants_summary.json`
- `results/end_task_gsm8k_canonical_first_variants.csv`
- `results/end_task_gsm8k_canonical_first_variants_summary.json`
- `artifacts/end_task_benchmark_gsm8k256_run.log`
- `artifacts/end_task_benchmark_run.log`

### Source and data files
- `scripts/end_task_canonical_first_benchmark.py`
- `tests/test_end_task_canonical_first_benchmark.py`
- `scripts/measure_order_permutation_nll.py`
- `data/acquired_gsm8k_main_test_qc_generated.jsonl`
- `data/acquired_canonical_first_order_aware_manifest.json`
- `data/acquired_canonical_first_order_aware_candidates.csv`
- `data/acquired_prior_measured_integrated_gpt2_variants_summary.json`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `run_notes.md`
- `prompts/resume.md`

### Paper pipeline artifacts
- `papers/.../evidence_bundle.json`
- `papers/.../claim_ledger.json`
- `papers/.../paper_manifest.json`
- `papers/.../README.md`
