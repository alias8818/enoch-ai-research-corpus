# Real-Document Retrieval Compression Teacher Validation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We report a real-document validation of the retrieval compression teacher-survival framework previously established on synthetic data. Using a curated set of 20 examples drawn from actual project documentation and source code, we evaluate five compressor methods—`teacher_oracle`, `targeted_fix`, `naive_keyword`, `lead_budget`, and `random_budget`—under the same evaluation schema and bootstrap ranking protocol as the parent synthetic minimum viable experiment. At medium budget, `targeted_fix` ranks first with a bootstrap first-place share of 1.000 (500 repetitions) and a task-success rate of 1.000 versus 0.800 for `naive_keyword`, yielding a 20.0 percentage-point uplift. These results clear the pre-registered kill conditions (first-place share ≥ 0.70; uplift ≥ 5 points). However, the real-slice uplift of 20.0 points is lower than the parent synthetic uplift of 29.9 points, and the validation set is small and locally sourced. We characterize the evidence as moderate and the confidence as medium. The current project artifacts support this finding in the tested setting; the result does not establish universal applicability.

## 1. Introduction

Retrieval-augmented generation and document question-answering systems depend on compressing retrieved context to fit within budget constraints while preserving task-relevant information. A teacher-survival framework evaluates compressor quality by measuring whether compressed context retains the evidence spans a teacher model identifies as essential for correct task completion.

A prior synthetic minimum viable experiment (MVE) demonstrated that the `targeted_fix` compressor— which uses teacher-identified evidence spans to guide budget allocation—outperformed `naive_keyword`, `lead_budget`, and `random_budget` baselines on synthetic examples, achieving a first-place bootstrap share of 1.000 and a 29.9 percentage-point task-success uplift over `naive_keyword` at medium budget.

The present work addresses a key limitation of that MVE: its reliance on synthetic documents. We ask whether the same ranking and uplift patterns hold when the evaluation examples are drawn from real project artifacts—actual result files and source code—rather than procedurally generated text. This is a smoke-test validation, not a comprehensive external-corpus benchmark. We pre-register kill conditions to avoid interpreting weak or ambiguous evidence as supportive.

## 2. Method

### 2.1 Validation Harness

We implemented a self-contained validation harness (`src/real_document_teacher_validation.py`) that reuses the parent project's teacher-survival schema and evaluation code. The harness loads real-document examples, runs each compressor method, and records per-example task success, evidence-span survival, and failure tags.

### 2.2 Real-Document Dataset

We constructed 20 examples from two real parent-project artifacts:

- `RESULTS.md`: a structured results document containing numerical outcomes, rankings, and interpretive text.
- `src/retrieval_compression_experiment.py`: source code implementing the retrieval compression experiment logic.

The resulting dataset (`data/real_document_teacher_set.jsonl`) includes four example categories:

1. **Real result lookup**: Questions answerable from numerical data in `RESULTS.md`.
2. **Real code navigation**: Questions requiring identification of specific functions, parameters, or logic in the source code.
3. **Structured extraction**: Questions requiring extraction of structured information (rankings, metric values) from formatted text.
4. **Abstention examples**: Questions where the correct behavior is to abstain because the document does not contain sufficient evidence.

Each example includes explicit evidence span IDs, teacher survival levels, failure tags, and annotation metadata to ensure auditability.

### 2.3 Compressor Methods

We evaluate the same five compressor methods as the parent MVE:

- **`teacher_oracle`**: Oracle compressor with access to teacher-identified evidence spans; serves as an upper bound.
- **`targeted_fix`**: Budget-aware compressor that prioritizes teacher-identified evidence spans for inclusion.
- **`naive_keyword`**: Keyword-matching compressor that selects segments based on lexical overlap with the query.
- **`lead_budget`**: Compressor that allocates budget to the leading portion of the document.
- **`random_budget`**: Compressor that allocates budget to randomly selected segments.

### 2.4 Evaluation Protocol

We apply the same evaluation protocol as the parent MVE:

- **Budget level**: Medium budget (the same level at which the parent MVE reported its primary results).
- **Task success**: Binary indicator of whether the compressed context contains sufficient information for correct task completion, as determined by the teacher-survival criterion.
- **Bootstrap ranking stability**: 500 bootstrap resamples over the 20 examples, recording the first-place method in each resample. The first-place share for a method is the fraction of resamples in which it ranks first.

### 2.5 Pre-Registered Kill Conditions

Before running the experiment, we established two kill conditions. The validation would be finalized as negative if either condition held at medium budget:

1. `targeted_fix` does not rank first in bootstrap first-place share, or its first-place share falls below 0.70.
2. `targeted_fix` task-success uplift over `naive_keyword` is below 5 percentage points.

These conditions were chosen to be substantially weaker than the parent synthetic results (first-place share 1.000, uplift 29.9 points), reflecting the expectation that real-document performance may degrade relative to synthetic data.

### 2.6 Annotation Audit

We performed a mechanical spot-check audit of all 20 examples and their 18 evidence spans, verifying:

- All span offsets are exact.
- All evidence spans are exact substrings of the parent artifacts.

Audit results are recorded in `results/annotation_audit.json`.

## 3. Results

### 3.1 Ranking

At medium budget, the compressor ranking is:

| Rank | Method | Task Success |
|------|--------|-------------|
| 1 | `targeted_fix` | 1.000 |
| 2 | `naive_keyword` | 0.800 |
| 3 | `lead_budget` | 0.600 |
| 4 | `random_budget` | 0.400 |

The `teacher_oracle` method is not included in the competitive ranking as it serves as an upper-bound reference.

### 3.2 Task-Success Uplift

`targeted_fix` achieves a task-success rate of 1.000 compared to 0.800 for `naive_keyword`, yielding a real-slice uplift of 20.0 percentage points. This is lower than the parent synthetic uplift of 29.9 points, consistent with the expectation that real documents present harder compression challenges.

### 3.3 Bootstrap Stability

Over 500 bootstrap resamples, `targeted_fix` achieves a first-place share of 1.000, identical to the parent synthetic result. No other method appears in first place in any resample.

### 3.4 Kill Condition Assessment

Neither kill condition is triggered:

- First-place share = 1.000 ≥ 0.70 ✓
- Uplift = 20.0 points ≥ 5 points ✓

### 3.5 Annotation Integrity

The mechanical audit confirms all 18 evidence spans across 20 examples have exact offsets and are exact substrings of the source artifacts. No annotation errors were detected.

## 4. Limitations

1. **Small validation set**: The 20-example dataset, while drawn from real artifacts, is small. Bootstrap stability of 1.000 over 500 resamples is consistent with a strong effect but also with a small sample where one method dominates most examples. A larger dataset could reveal ranking instability not visible at this scale.

2. **Locally sourced documents**: Both source artifacts (`RESULTS.md` and `src/retrieval_compression_experiment.py`) come from the same project that produced the compressor methods. This introduces a risk of constructive alignment between document structure and compressor design. Validation on an external corpus with no such alignment is absent.

3. **Reduced uplift relative to synthetic data**: The 20.0-point real-slice uplift is 9.9 points lower than the 29.9-point synthetic uplift. While still clearing the kill condition, this reduction suggests that real-document compression is harder and that the advantage of `targeted_fix` may attenuate further on more diverse or adversarial corpora.

4. **No version control**: The project directory was not under git version control at the time of the experiment. No commit hash or diff is available to pin the exact code state, though the harness was verified via `py_compile` and a full execution run.

5. **Single budget level**: Results are reported only at medium budget. Performance at low or high budgets may differ.

6. **No external replication**: These results have not been independently replicated by a separate team or on separate infrastructure.

7. **Curated example selection**: The 20 examples were curated rather than randomly sampled from a defined population, which limits the statistical generality of the findings.

## 5. Reproducibility Checklist

| Item | Status |
|------|--------|
| Validation harness source | `src/real_document_teacher_validation.py` — compiles and executes cleanly |
| Dataset | `data/real_document_teacher_set.jsonl` — 20 examples, 18 evidence spans |
| Annotation audit | `results/annotation_audit.json` — all spans verified as exact substrings |
| Result files | `results/metrics.json`, `results/ranking_stability.json`, `results/failure_coverage.json`, `results/per_example_rows.jsonl` |
| Pre-registered kill conditions | Documented in `run_notes.md` before execution |
| Execution command | `python3 src/real_document_teacher_validation.py --out-dir .` |
| Compilation check | `python3 -m py_compile src/real_document_teacher_validation.py` — passed |
| Version control | Not available (no git repository) |
| Hardware/software environment | Not recorded in artifacts |
| Random seeds | Not recorded in artifacts |

## 6. Conclusion

We validated the retrieval compression teacher-survival framework on 20 real-document examples drawn from project artifacts, using the same compressor methods, evaluation schema, and bootstrap ranking protocol as a prior synthetic MVE. The `targeted_fix` compressor ranked first with a bootstrap first-place share of 1.000 and a 20.0 percentage-point task-success uplift over `naive_keyword`, clearing both pre-registered kill conditions. The real-slice uplift was lower than the synthetic uplift (20.0 vs. 29.9 points), indicating that real documents present harder compression challenges while still preserving the relative advantage of targeted compression. The evidence strength is moderate and confidence is medium, bounded by the small, locally sourced validation set and the absence of external replication. The project decision recommends archiving this branch as a positive real-document smoke validation and allocating further budget to a larger external-corpus benchmark only if explicitly queued as a separate project.

---

## Referenced Artifacts

### Run notes and decision
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Source code
- `src/real_document_teacher_validation.py`

### Dataset
- `data/real_document_teacher_set.jsonl`

### Result files
- `results/annotation_audit.json`
- `results/failure_coverage.json`
- `results/ranking_stability.json`
- `results/per_example_rows.jsonl`
- `results/metrics.json`

### Paper artifacts
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/README.md`

### Parent project reference
- `RESULTS.md` (source artifact for real-document examples)
- `src/retrieval_compression_experiment.py` (source artifact for real-document examples)
