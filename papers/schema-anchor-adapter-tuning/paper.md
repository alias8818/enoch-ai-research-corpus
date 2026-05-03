# Schema-Anchor Adapter Tuning for Schema Matching

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, and benchmark results). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

Schema matching—mapping noisy source column headers and values to canonical target fields—remains a practical bottleneck in data integration. We investigate whether enriching target field descriptions with structured schema anchors (field name, description, type, and examples) and training a lightweight supervised adapter on sparse feature representations can improve matching accuracy over purely lexical baselines. On a reproducible synthetic held-out-alias benchmark with 16 canonical target fields, we compare four methods: (1) lexical name-only matching via character n-gram cosine similarity, (2) untuned schema-anchor TF-IDF cosine, (3) a tuned sparse adapter without an explicit type-match scalar, and (4) a tuned sparse adapter with an explicit type-match scalar. Schema-anchor cosine alone raises mean top-1 accuracy from 0.3125 to 0.9660 across 10 seeds. The tuned adapter with type scalar achieves a mean top-1 of 1.0000 (std 0.0000), yielding a mean lift of +0.0340 over schema-anchor cosine. However, the benchmark is synthetic, the target field set is small (16 fields), and the strongest result depends on an available type-match signal whose generalization to noisy real-world schemas is uncertain. We report these results as positive local evidence requiring validation on real schema corpora before any production or external scientific claim.

## Introduction

Schema matching is the task of aligning source data fields—column headers, observed values, type hints—to canonical target fields in a reference schema. In practice, source headers are frequently ambiguous, abbreviated, or inconsistent, making pure lexical matching unreliable. Approaches to schema matching have explored type-aware matching, schema enrichment, and learned matching functions, but the specific contribution of structured target-side anchors—combining field name, textual description, data type, and representative examples—has not been isolated in a controlled setting.

This study asks: can target-schema anchors plus a small tuned adapter improve schema matching from noisy source column headers and values to canonical target fields, relative to lexical and untuned baselines?

We design a controlled synthetic benchmark and compare four progressively richer methods. We report results honestly, including the ceiling effect observed in the strongest condition and the synthetic nature of the evaluation. We deliberately avoid extrapolating these findings to production settings.

## Method

### Benchmark Design

We constructed a synthetic schema matching benchmark with the following properties:

- **16 canonical target fields**, each annotated with a schema anchor comprising field name, description, data type, and example values.
- **Train and test alias separation**: aliases used during adapter training are held out from the test set, ensuring the adapter must generalize to unseen surface forms rather than memorize alias–field pairings.
- **Source evidence**: each test example provides a source column header, observed values, and type-pattern hints.
- **Full evaluation configuration**: 10 random seeds, 4 training examples per train alias, 3 test examples per test alias.

### Methods Compared

1. **Lexical name only** (`lexical_name_only`): Character n-gram cosine similarity computed between the source header text and the target field name only. No value, type, or description information is used.

2. **Schema-anchor cosine** (`schema_anchor_cosine`): TF-IDF cosine similarity between a source evidence string (header + values + type hints) and the target schema anchor text (field name + description + type + examples). No supervised training is applied.

3. **Tuned adapter, no type scalar** (`tuned_schema_anchor_adapter_no_type_scalar`): A supervised pair scorer using sparse product and difference features derived from the source–anchor pair representations. An L2-regularized logistic regression model is trained on positive (correct match) and negative (incorrect match) pairs. No explicit type-match scalar feature is included.

4. **Tuned adapter, with type scalar** (`tuned_schema_anchor_adapter`): Identical to method 3, with the addition of an explicit type-match/length scalar feature encoding whether the source and target types agree.

### Adapter Training

The adapter is a sparse logistic regression model trained on constructed positive and negative pairs. In the smoke test (seed 0, 1 train example per alias, 3 negatives per positive), the model operated on 6,616 features across 196 training pairs, achieving a training log loss of 0.085. The full evaluation uses 4 training examples per alias. Training is fast and CPU-only; no GPU is required.

### Evaluation Metrics

- **Top-1 accuracy**: fraction of test examples where the highest-scoring target field is the correct match.
- **Top-3 accuracy**: fraction where the correct match appears in the top 3 scores.
- **Mean Reciprocal Rank (MRR)**: average of 1/rank of the correct match.
- **Median rank** and **p95 rank**: distributional statistics on the rank of the correct match.

### Computational Environment

All experiments ran on a CPU-only workstation (Python 3.12.3, ~116 GiB available memory, no swap). Full evaluation wall time was approximately 8 seconds. Peak RSS was approximately 200 MB. An NVIDIA GB10 GPU was present but entirely unused (0% utilization).

## Results

### Full Evaluation (10 Seeds)

| Method | Top-1 mean | Top-1 std | Top-3 mean | MRR mean |
|---|---:|---:|---:|---:|
| Lexical name only | 0.3125 | 0.0000 | 0.4583 | 0.4340 |
| Schema-anchor cosine | 0.9660 | 0.0152 | 1.0000 | 0.9830 |
| Tuned adapter, no type scalar | 0.9917 | 0.0072 | 1.0000 | 0.9956 |
| Tuned adapter, with type scalar | 1.0000 | 0.0000 | 1.0000 | 1.0000 |

The observed top-1 lift of the tuned adapter with type scalar over untuned schema-anchor cosine is: mean +0.0340, minimum +0.0139, maximum +0.0556 across the 10 seeds.

### Smoke Test (Seed 0, Single Train Example)

The smoke test confirmed the pipeline and produced consistent directional results, though with wider confidence intervals. The 95% confidence interval for the tuned-vs-anchor top-1 difference was [−0.0625, +0.0625], reflecting the high variance expected from a single-seed, single-example configuration. The smoke test included only three of the four methods (lexical name only, schema-anchor cosine, and the tuned adapter with type scalar); the no-type-scalar variant was added in the full evaluation.

Smoke test detail (seed 0, 48 test examples, 16 targets, 6,616 adapter features, 196 training pairs):

| Method | Top-1 | Top-3 | MRR | Median rank | p95 rank |
|---|---:|---:|---:|---:|---:|
| Lexical name only | 0.3125 | 0.4583 | 0.4340 | 4.5 | 14.65 |
| Schema-anchor cosine | 0.9792 | 1.0000 | 0.9896 | 1.0 | 1.0 |
| Tuned adapter, with type scalar | 0.9792 | 1.0000 | 0.9896 | 1.0 | 1.0 |

In the smoke test, the tuned adapter and schema-anchor cosine produced identical top-1 accuracy (0.9792), consistent with the wide confidence interval that cannot distinguish them at this sample size.

### Key Observations

1. **Schema anchors are strongly useful.** Moving from lexical name-only to schema-anchor cosine produces a top-1 improvement of +0.6535 (from 0.3125 to 0.9660), the dominant effect in the study.

2. **Adapter tuning provides a small but consistent improvement.** The tuned adapter with type scalar achieves perfect top-1 accuracy across all 10 seeds, but the absolute lift over schema-anchor cosine is modest (+0.034 mean). The no-type-scalar adapter also improves over cosine (+0.0257 mean) but does not reach ceiling.

3. **The type-match scalar matters.** The difference between the adapter with and without the type scalar is +0.0083 in top-1 mean, and the type-scalar variant achieves zero variance across seeds. This suggests the type signal is informative in this benchmark, though its contribution is small relative to the anchor enrichment itself.

4. **Ceiling effects are present.** Top-3 accuracy is 1.0000 for all methods except lexical name-only, and MRR is near ceiling for all anchor-based methods. The discriminative margin of the study is primarily in top-1 accuracy.

## Limitations

1. **Synthetic benchmark.** The 16-field benchmark is constructed, not drawn from a real schema corpus. Alias distributions, value patterns, and type hints may be cleaner or more structured than encountered in production. The results demonstrate local viability, not external scientific closure.

2. **Small target field set.** With only 16 canonical targets, the ranking task is easier than in realistic schemas with hundreds or thousands of fields. Scaling behavior is unknown.

3. **Type-match scalar availability.** The strongest result (1.000 top-1) depends on an explicit type-match feature. In real schemas, type information may be missing, inconsistent, or ambiguous, which could degrade this variant disproportionately.

4. **No cross-domain evaluation.** All aliases and fields share a single domain. Leave-one-domain-out splits are needed before claiming generalization.

5. **Sparse logistic adapter only.** The adapter is a simple sparse logistic regression, not a neural adapter (e.g., LoRA). Whether the observed improvements transfer to the intended deployed adapter family is untested.

6. **No private or production schema data.** No real labeled schema corpus was available within the project directory. All claims are limited to the synthetic setting.

7. **Single benchmark domain.** The benchmark covers one domain with 16 fields. Performance on broader, noisier, or multi-domain schema corpora remains uncharacterized.

8. **Ceiling effects limit discriminative power.** The near-ceiling performance of schema-anchor cosine on top-3 and MRR metrics compresses the observable improvement from adapter tuning, making it difficult to assess the adapter's true marginal value.

## Reproducibility Checklist

- [x] **Source code available**: `scripts/schema_anchor_adapter_experiment.py`
- [x] **Full evaluation results**: `results/full_v2.json`
- [x] **Smoke test results**: `results/smoke_v2.json`, `results/smoke.json`
- [x] **Calibration results**: `results/calibrate.json`
- [x] **Metrics summary**: `results/metrics_summary.json`
- [x] **Standard output logs**: `logs/smoke_v2.stdout.log`, `logs/full_v2.stdout.log`
- [x] **Timing and memory logs**: `logs/smoke_v2.time.log`, `logs/full_v2.time.log`, `logs/final_mem_snapshot.log`
- [x] **GPU telemetry**: `logs/final_nvidia_smi.log`
- [x] **Decision artifact**: `.omx/project_decision.json`
- [x] **Run notes**: `run_notes.md`
- [x] **Random seeds specified**: 10 seeds in full evaluation; seed 0 in smoke test
- [x] **Train/test split enforced**: train aliases held out from test aliases
- [x] **Hardware specified**: CPU-only, ~116 GiB RAM, Python 3.12.3, NVIDIA GB10 (unused)
- [x] **Wall time reported**: ~8 seconds for full evaluation
- [x] **Peak memory reported**: ~200 MB RSS

## Conclusion

On a reproducible synthetic held-out-alias schema matching benchmark, structured schema anchors (field name + description + type + examples) provide a large improvement over lexical name-only matching (top-1: 0.966 vs. 0.312). A lightweight supervised adapter trained on sparse pair features yields a further small but consistent top-1 improvement (+0.034 mean over schema-anchor cosine), reaching perfect top-1 accuracy when an explicit type-match scalar is included. However, these results are obtained on a small, synthetic benchmark with only 16 target fields. The dominant effect is the anchor enrichment itself; the adapter's marginal contribution, while consistent, is modest and may not survive transfer to noisier, larger, or cross-domain real-world schemas. We classify this as a positive local result with medium confidence. The necessary next step is evaluation on a real labeled schema corpus with cross-domain splits before any production readiness or external publication claim can be justified.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `scripts/schema_anchor_adapter_experiment.py` |
| Full evaluation results | `results/full_v2.json` |
| Smoke test results (v2) | `results/smoke_v2.json` |
| Smoke test results (v1) | `results/smoke.json` |
| Calibration results | `results/calibrate.json` |
| Metrics summary | `results/metrics_summary.json` |
| Smoke stdout log | `logs/smoke_v2.stdout.log` |
| Full stdout log | `logs/full_v2.stdout.log` |
| Smoke timing log | `logs/smoke_v2.time.log` |
| Full timing log | `logs/full_v2.time.log` |
| Memory snapshot | `logs/final_mem_snapshot.log` |
| GPU telemetry | `logs/final_nvidia_smi.log` |
| Decision JSON | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Project metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260502T150848612685+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T150848612685+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T150848612685+0000/paper_manifest.json` |
