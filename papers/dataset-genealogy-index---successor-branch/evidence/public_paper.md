# Dataset Genealogy Index: Successor Branch Evaluation of Lineage-Manifest Reproducibility in a Model-Preparation Pipeline

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review is asserted or implied.

---

## Abstract

We report results from a successor branch of the Dataset Genealogy Index project that extends prior metadata-only lineage pilots to a concrete model-preparation and training loop. A deterministic multinomial Naive Bayes classifier is trained from data whose preparation steps—quality pruning, prompt transformation, synthetic augmentation, deduplication, and train/validation splitting—are recorded as lineage manifest nodes. We compare full-lineage replay against sparse manual run cards that omit common hidden preparation facts. In the bounded toy setting (120 synthetic JSONL records, CPU-only execution), lineage-manifest replay achieves a dataset reproduction rate of 1.00 and a downstream model reproduction rate of 1.00, while the manual run-card condition achieves a model reproduction rate of 0.25. Lineage accessibility answerability is 1.000 versus a manual baseline of 0.556. These results support the mechanism within the tested scope but do not establish production-scale viability. A code defect discovered during integration—synthetic augmentation silently dropping task-label fields—illustrates that connecting lineage manifests to end-to-end model pipelines surfaces schema-preservation requirements earlier than metadata-only provenance tracking.

## Introduction

Dataset provenance and reproducibility remain practical challenges in machine learning pipelines. Prior work on the Dataset Genealogy Index (parent project `source-record-redacted`) demonstrated that structured lineage manifests could support metadata-level reproducibility in both clean and messy settings. That work identified a concrete model-training integration benchmark as the next useful target, since metadata-only pilots cannot reveal whether lineage manifests suffice to reproduce downstream model outputs.

This successor branch addresses that gap. Rather than testing lineage tracking in isolation, we ask two questions:

1. Does replaying lineage manifests reproduce not only intermediate datasets but also downstream deterministic model outputs?
2. How does lineage-manifest reproduction compare against the reproduction fidelity achievable from sparse manual or control-plane run cards alone?

The evaluation is deliberately bounded: a synthetic JSONL-scale corpus, a deterministic classifier, and CPU-only execution. This scope tests the provenance mechanism's correctness under controlled conditions rather than its performance or robustness at production scale.

## Method

### Lineage Store and Manifest Structure

The Dataset Genealogy Index records each data transformation as a lineage node. For this benchmark, the following transformations are recorded as separate nodes:

1. **Quality pruning** — filtering records by quality criteria.
2. **Prompt transform** — applying a prompt-formatting transformation.
3. **Synthetic augmentation** — generating synthetic records to expand the training set.
4. **Deduplication** — removing duplicate records.
5. **Train/validation split** — partitioning records into training and validation subsets.

Each node captures sufficient metadata to deterministically replay the transformation given its input. During this work, a schema-preservation defect was identified and corrected in the synthetic augmentation step: the original implementation dropped non-core record fields, including `label`, which silently corrupted downstream task metadata. This fix is covered by regression tests.

### Model Integration

A deterministic multinomial Naive Bayes classifier serves as the downstream model. The classifier is trained on the replayed training set and evaluated on the replayed validation set. Determinism is ensured by fixed random seeds and a fully deterministic algorithm, enabling bit-exact comparison of model hashes, prediction hashes, and evaluation metrics across independent replays.

### Comparison Condition

Sparse manual run cards—representing typical control-plane or ad-hoc experiment logging—omit common hidden data-preparation and training facts (e.g., augmentation parameters, deduplication thresholds, split seeds). We measure whether these incomplete records suffice to reproduce the same datasets and model outputs. This baseline is a constructed sparse condition rather than an empirical sample of real-world experiment logs; the resulting reproduction rate reflects the specific set of facts omitted and should not be generalized to arbitrary logging practices.

### Measurement Protocol

All measurements were collected on a single CPU-only machine with swap disabled. Memory was assessed via `/proc/meminfo` `MemAvailable` and process RSS. Runtime was measured wall-clock over the full replay-train-eval pipeline. No GPU or CUDA calibration was applicable to this benchmark.

## Results

### Reproduction Rates

| Condition | Dataset Replay Rate | Model Reproduction Rate |
|---|---|---|
| Lineage-manifest replay | 1.00 | 1.00 |
| Manual/control-plane run cards | — | 0.25 |

Lineage-manifest replay reproduced the training dataset hash, validation dataset hash, model hash, prediction hash, and validation accuracy identically across runs. The manual run-card condition reproduced only 1 of 4 target artifacts (validation accuracy), failing on dataset hashes, model hash, and prediction hash due to missing transformation parameters.

### Accessibility Answerability

| Condition | Accessibility Answerability |
|---|---|
| Lineage manifests | 1.000 |
| Manual baseline | 0.556 |

Accessibility answerability measures the fraction of auditable questions about the pipeline that can be answered from the available records. Lineage manifests provide complete coverage in this toy setting; manual run cards leave approximately 44% of questions unanswerable.

### Model Performance

The deterministic classifier achieved a validation accuracy of 1.000 on 36 validation records (84 training records). This perfect accuracy reflects the simplicity of the synthetic toy corpus and is not a generalizable performance claim.

### Resource Usage

| Metric | Value |
|---|---|
| Total pipeline runtime (replay + train + eval) | 0.0105 s |
| Throughput | 11,423.3 records/s |
| Process RSS | 18.9 MB |
| MemAvailable | ~122.6 GB |
| SwapFree | 0 (swap disabled) |

The pipeline is lightweight in this toy setting. No meaningful memory pressure was observed. These throughput and memory figures characterize a synthetic 120-record workload and should not be extrapolated to production-scale corpora.

### Bug Discovery During Integration

During the initial integration run, the synthetic augmentation step was found to drop the `label` field from augmented records. This defect was not visible in the parent project's metadata-only pilots and was only surfaced when lineage manifests were connected to a downstream model that required task labels. The fix was verified by regression tests: 6 tests passing both before and after the fix, with the post-fix run confirming label preservation in synthetic records.

This finding is a mixed result: while the mechanism ultimately worked correctly after the fix, the defect's existence indicates that the lineage store's synthetic augmentation module had an implicit schema contract that was not enforced or tested until an end-to-end model consumer was attached.

## Limitations

1. **Scale.** The benchmark operates on 120 synthetic JSONL records with a deterministic toy classifier. It does not demonstrate performance, correctness, or feasibility at production dataset scales (millions of records, multi-gigabyte corpora) or with non-deterministic training (e.g., stochastic gradient descent, GPU nondeterminism).

2. **Scope of reproducibility.** The model reproduction rate of 1.00 relies on the classifier being fully deterministic. Real training frameworks introduce sources of nondeterminism (floating-point ordering, hardware-dependent reductions) that this benchmark does not address.

3. **Data governance.** The synthetic corpus involves no privacy, licensing, or access-control constraints. The lineage mechanism's behavior under messy human or private data governance regimes is untested.

4. **Framework integration.** The lineage manifest writer is a standalone Python module. Integration friction with real training frameworks (Hugging Face Datasets, PyTorch data loaders, LoRA pipelines) remains unmeasured.

5. **Comparison baseline.** The manual run-card condition is a constructed sparse baseline rather than an empirical sample of real-world experiment logs. The 0.25 reproduction rate reflects the specific set of facts omitted in this construction and should not be generalized.

6. **Single execution environment.** All results are from one machine with one execution. Cross-environment reproducibility (different OS, Python version, library versions) is not tested.

7. **Confidence and evidence strength.** The project decision records medium confidence and moderate evidence strength, reflecting the gap between toy-scale positive results and the absence of production-scale validation.

## Reproducibility Checklist

- **Code available:** `src/run_model_prep_benchmark.py`, `src/dataset_genealogy.py`, `tests/test_model_prep_benchmark.py`
- **Deterministic by design:** Fixed seeds, deterministic algorithm (multinomial Naive Bayes), no GPU nondeterminism
- **Artifact paths:**
  - Benchmark metrics: `artifacts/model_prep_benchmark/metrics.json`
  - Model card: `artifacts/model_prep_benchmark/model_card.json`
  - Train lineage: `artifacts/model_prep_benchmark/train_ancestors.json`
  - Validation lineage: `artifacts/model_prep_benchmark/validation_ancestors.json`
- **Execution logs:**
  - `.omx/logs/experiments/pytest.log`
  - `.omx/logs/experiments/pytest_after_synthetic_fix.log`
  - `.omx/logs/experiments/model_prep_benchmark.stdout.json`
  - `.omx/logs/experiments/model_prep_benchmark.stderr.log`
- **Environment:** CPU-only, swap disabled, Python 3, `PYTHONPATH=src`
- **Commands:**
  - `python3 -m pytest -q` (6 passed)
  - `PYTHONPATH=src python3 src/run_model_prep_benchmark.py`
- **Known defect fixed:** Synthetic augmentation label-dropping bug; regression tests added and passing

## Conclusion

Within the bounded scope of a synthetic JSONL-scale toy classifier, the Dataset Genealogy Index lineage-manifest mechanism achieves full reproduction of both intermediate datasets and downstream deterministic model outputs, substantially outperforming sparse manual run cards. The integration also surfaced a schema-preservation defect in the synthetic augmentation step that was invisible in metadata-only pilots, suggesting that connecting lineage manifests to end-to-end model pipelines provides earlier and more actionable correctness signals than metadata-only provenance tracking alone.

These results support the mechanism at toy scale with medium confidence and moderate evidence strength, but do not establish production viability. The most useful next step, if pursued, would be integrating the lineage manifest writer with a real dataset-preparation and training framework to measure framework friction, schema-versioning challenges, and performance at realistic scale. Creating additional generic successor branches without such integration would not meaningfully advance the evidence.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Benchmark metrics | `artifacts/model_prep_benchmark/metrics.json` |
| Model card | `artifacts/model_prep_benchmark/model_card.json` |
| Train ancestors | `artifacts/model_prep_benchmark/train_ancestors.json` |
| Validation ancestors | `artifacts/model_prep_benchmark/validation_ancestors.json` |
| Pytest log (initial) | `.omx/logs/experiments/pytest.log` |
| Pytest log (post-fix) | `.omx/logs/experiments/pytest_after_synthetic_fix.log` |
| Benchmark stdout | `.omx/logs/experiments/model_prep_benchmark.stdout.json` |
| Benchmark stderr | `.omx/logs/experiments/model_prep_benchmark.stderr.log` |
| Benchmark runner | `src/run_model_prep_benchmark.py` |
| Genealogy module | `src/dataset_genealogy.py` |
| Regression tests | `tests/test_model_prep_benchmark.py` |
| Parent project | `../source-record-redacted` |
