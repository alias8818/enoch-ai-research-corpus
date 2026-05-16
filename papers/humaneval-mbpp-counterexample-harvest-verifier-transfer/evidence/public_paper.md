# Counterexample-Harvest Training Reduces False Accepts in Code Verification: A Transfer Study on HumanEval and MBPP

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated these claims.

---

## Abstract

We investigate whether counterexample-harvested hard negatives—code candidates that pass public tests but fail hidden tests—improve verifier accuracy when transferred to standard code-generation benchmarks. Using a self-contained harness on a subset of HumanEval (80 tasks) and MBPP (120 tasks), we generate 3,415 semantic AST/code mutants from canonical solutions and partition them into 15 train and 8 held-out mutation families. On held-out families, counterexample-harvest training reduces the text verifier's false-accept rate at 50% positive-recall (FAR@0.5) from 0.3235 (random baseline) and 0.3382 (equal-budget random) to 0.1324, a reduction of approximately 59–61%. AUC gains are more modest: +2.72 points over random baseline and +2.65 over equal-budget random, below a pre-specified 10-point success bar. A hybrid AST verifier achieves AUC 1.0000 under all regimes, but the FAR@0.5 advantage of counterexample-harvest (0.0000 vs. 1.0000) is threshold-sensitive and should be interpreted cautiously. Evidence strength is moderate; confidence is medium. These results support the hypothesis that counterexample-harvested hard negatives transfer to reduce false accepts, but the AUC improvement remains modest and replication on fuller benchmarks is warranted.

## 1. Introduction

Automated code verification—determining whether a generated program is semantically correct—is a critical component of code-generation pipelines. A persistent challenge is the prevalence of false accepts: incorrect programs that pass a surface-level or public test suite but fail on inputs not exposed during verification. Hard negatives—candidates that pass public tests but fail hidden tests—offer a potentially informative training signal for verifiers, since they directly target the failure mode of interest.

Prior work on counterexample harvesting has demonstrated that training verifiers on such hard negatives can reduce false-accept rates in controlled settings. However, it remains unclear whether this benefit transfers to standard code-generation benchmarks with realistic mutation distributions and held-out mutation families.

This study tests the transfer hypothesis: if a verifier is trained on counterexample-harvested hard negatives derived from one set of mutation families, does it generalize to reduce false accepts on held-out mutation families from the same benchmark tasks? We construct a self-contained transfer harness on HumanEval and MBPP, generate semantic AST/code mutants from canonical solutions, and compare three training regimes—random negative sampling, equal-budget random sampling, and counterexample-harvested hard negatives—on held-out mutation families.

## 2. Method

### 2.1 Benchmark Acquisition and Task Selection

We acquire HumanEval (JSONL gzip from OpenAI's `human-eval` repository) and MBPP (JSONL from Google Research's `google-research` repository). The harness loads up to 80 HumanEval tasks and 120 MBPP tasks (200 total), of which 194 pass canonical validation. Benchmark data is cached locally in `artifacts/benchmark_cache/`.

### 2.2 Semantic Mutant Generation

Rather than applying syntactic no-op variants of hand-authored bug templates, we generate fresh semantic AST/code mutants from canonical solutions. Each task receives up to 32 mutant candidates (parameter `--max-mutants-per-problem 32`), with a per-candidate execution timeout of 0.25 seconds. This yields 3,415 total generated candidates, all with unique code hashes.

### 2.3 Public/Hidden Test Split and Hard Negative Harvesting

For each task, the test suite is sparsely partitioned into public and hidden subsets. A candidate that passes all public tests but fails at least one hidden test is classified as a **hard negative** (public-pass/hidden-fail). This split directly operationalizes the false-accept scenario: a verifier that accepts such a candidate has produced a false accept.

### 2.4 Train/Held-Out Family Split

Mutation families are partitioned into 15 train families (yielding 201 train hard negatives) and 8 held-out families (yielding 68 held-out eval hard negatives). No held-out mutation family appears in training. Zero duplicate hard-negative code hashes are observed across the split.

### 2.5 Verifier Regimes

We compare three training regimes for each verifier type:

1. **Random baseline**: Standard random negative sampling.
2. **Equal-budget random**: Random negative sampling constrained to the same training budget as the counterexample-harvest regime.
3. **Counterexample-harvest**: Training on hard negatives identified by the public-pass/hidden-fail split.

Two verifier architectures are evaluated:

- **Text verifier**: Operates on source code text.
- **Hybrid AST verifier**: Incorporates structural AST features alongside text.

### 2.6 Evaluation Metrics

- **AUC**: Area under the ROC curve on held-out hard negatives.
- **FAR@0.5**: False-accept rate at the threshold achieving 50% positive recall. Lower is better.
- **95%-positive-recall FAR**: False-accept rate at the threshold achieving 95% positive recall.

## 3. Results

### 3.1 Dataset Summary

| Metric | Value |
|---|---|
| Total loaded tasks | 200 |
| Canonical-valid tasks | 194 |
| Total generated candidates | 3,415 |
| Unique candidate code hashes | 3,415 |
| Train hard negatives | 201 (15 families) |
| Held-out hard negatives | 68 (8 families) |
| Duplicate hard-negative hashes | 0 |

### 3.2 Text Verifier: Held-Out Results

| Regime | AUC | FAR@0.5 |
|---|---|---|
| Random baseline | 0.6811 | 0.3235 |
| Equal-budget random | 0.6819 | 0.3382 |
| Counterexample-harvest | 0.7083 | 0.1324 |

Counterexample-harvest training improves AUC by +2.72 points over random baseline and +2.65 points over equal-budget random. The false-accept rate at 50% recall is reduced by 59.1% relative to random baseline (0.3235 → 0.1324) and by 60.9% relative to equal-budget random (0.3382 → 0.1324).

The AUC gains are positive but below a pre-specified 10-point success threshold. The FAR@0.5 reduction is substantial and exceeds the pre-specified 15% reduction bar for the branch kill condition.

### 3.3 Hybrid AST Verifier: Held-Out Results

| Regime | AUC | FAR@0.5 |
|---|---|---|
| Random baseline | 1.0000 | 1.0000 |
| Equal-budget random | 1.0000 | 1.0000 |
| Counterexample-harvest | 1.0000 | 0.0000 |

All regimes achieve perfect AUC on this split. The FAR@0.5 difference (1.0000 vs. 0.0000) favors counterexample-harvest, but this result requires careful interpretation. The 95%-positive-recall threshold metric was already 0.0000 FAR for all hybrid regimes, indicating that the FAR@0.5 operating point is threshold-sensitive. The hybrid verifier's structural features may already separate most hard negatives from positives at conservative thresholds, making the FAR@0.5 comparison less informative than the text verifier's result. This signal is useful for calibration but should not be taken as evidence of a large practical improvement.

### 3.4 Mixed and Negative Findings

Several aspects of the results temper the overall conclusion:

1. **AUC gains are modest.** The +2.7-point AUC improvement for the text verifier, while consistent, falls below the 10-point bar that would constitute strong evidence of transfer under the pre-specified criterion.
2. **Hybrid AST results are threshold-sensitive.** The dramatic FAR@0.5 difference for the hybrid verifier is an artifact of the operating point chosen; at the 95%-recall threshold, all regimes achieve 0.0000 FAR.
3. **No confidence intervals are reported.** The experiment was conducted as a single run; variance across random seeds or benchmark subsamples is unknown.
4. **Benchmark coverage is partial.** Only 80 of 164 HumanEval tasks and 120 of 974 MBPP tasks are included.

## 4. Limitations

1. **Partial benchmark coverage.** The harness operates on a subset (80/164 HumanEval, 120/974 MBPP). Results may not generalize to the full benchmarks or to other code-generation benchmarks not tested here.
2. **Single execution.** The experiment was run once with fixed random seeds. No confidence intervals, standard errors, or cross-validation folds are reported. The observed FAR@0.5 reduction of ~59–61% could vary under different random initializations or task orderings.
3. **Mutation family coverage.** Only 23 mutation families are observed (15 train, 8 held-out). The diversity and representativeness of these families for real-world code errors is not established.
4. **Hybrid AST verifier ambiguity.** The perfect AUC across all regimes and the threshold-sensitive FAR@0.5 difference make the hybrid verifier results difficult to interpret. The apparent advantage of counterexample-harvest may reflect the choice of operating point rather than a genuine generalization improvement.
5. **No LLM-sampled mutants.** All mutants are generated via AST-level semantic mutations of canonical solutions. Mutants produced by large language models (which may exhibit different error distributions) are not represented.
6. **Verifier architecture specificity.** Results are reported for two specific verifier architectures. Transfer to other verifier designs (e.g., execution-based, neural) is not tested.
7. **Automated pipeline provenance.** The entire experiment was executed by an automated research pipeline. While the harness script passed `py_compile` verification and produced durable artifacts, no independent human replication has been performed.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Benchmark sources specified | Yes: OpenAI `human-eval` repository (HumanEval), Google Research `google-research` repository (MBPP) |
| Run parameters documented | Yes: `--max-humaneval 80 --max-mbpp 120 --max-mutants-per-problem 32 --timeout 0.25` |
| Harness script available | Yes: `scripts/run_humaneval_mbpp_transfer.py` |
| Result JSON written | Yes: `artifacts/humaneval_mbpp_transfer_results.json` |
| Dataset CSV written | Yes: `artifacts/humaneval_mbpp_transfer_dataset.csv` |
| Benchmark cache preserved | Yes: `artifacts/benchmark_cache/HumanEval.jsonl.gz`, `artifacts/benchmark_cache/mbpp.jsonl` |
| Pre-specified kill condition | Yes: finalize negative if <20 held-out hard negatives or FAR@0.5 reduction <15% vs. both baselines |
| Kill condition outcome | Not met: 68 held-out hard negatives; FAR@0.5 reduced by >15% vs. both baselines |
| Confidence intervals reported | No |
| Multiple random seeds tested | No |
| Independent human replication | No |

## 6. Conclusion

On a subset of HumanEval and MBPP, counterexample-harvested hard negatives reduce the text verifier's false-accept rate at 50% recall by approximately 59–61% relative to both random and equal-budget random baselines, while improving AUC by a more modest 2.7 points. The hybrid AST verifier shows a threshold-sensitive FAR@0.5 advantage that is difficult to interpret given perfect AUC across all regimes. The pre-specified kill condition for a negative finding is not met, and the project decision is `finalize_positive` with moderate evidence strength and medium confidence.

The AUC improvement, though positive, is below the 10-point bar that would constitute strong evidence of transfer. The FAR@0.5 reduction is the more robust signal for the text verifier, but the absence of confidence intervals and the partial benchmark coverage limit the strength of the conclusion. Replication on the full MBPP set, with LLM-sampled mutants, and with multiple random seeds would substantially strengthen external validity.

## Referenced Artifacts

### Run notes
- `run_notes.md`

### Decision and metrics
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Result files
- `artifacts/humaneval_mbpp_transfer_results.json`
- `artifacts/humaneval_mbpp_transfer_dataset.csv`

### Benchmark cache
- `artifacts/benchmark_cache/HumanEval.jsonl.gz`
- `artifacts/benchmark_cache/mbpp.jsonl`

### Harness source
- `scripts/run_humaneval_mbpp_transfer.py`

### Evidence and claim audit
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
