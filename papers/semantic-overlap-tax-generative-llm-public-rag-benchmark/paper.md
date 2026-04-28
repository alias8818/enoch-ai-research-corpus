# Semantic Overlap Tax for Retrieval-Augmented Generation: Evidence from a Public SQuAD Benchmark

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has certified this document.

---

## Abstract

We present evidence on the effect of a semantic overlap tax—a penalty on retrieved context passages that redundantly overlap already-selected context—on retrieval-augmented generation (RAG) performance. In a 200-case evaluation on the SQuAD v1.1 development set using extractive QA, the overlap-tax packer achieved answer F1 of 0.6349 versus a vanilla baseline of 0.5959 (+0.0390), exact match of 0.5633 versus 0.5183 (+0.0450), and gold context selection of 0.8100 versus 0.7667 (+0.0433), while reducing mean context token usage by 2.52%. The F1 tie/win rate was 0.8950. A separate 8-case branch-verification smoke test using a deterministic fallback generator confirmed improved gold context selection and reduced token usage but showed a slight F1 decrease of −0.0050, illustrating that the method's answer-quality benefit is not uniform across all generator configurations. Confidence in the overall finding is medium; the primary evidence is limited to extractive QA on a single public dataset and does not yet cover instruction-tuned or seq2seq generative LLMs.

## 1. Introduction

Retrieval-augmented generation (RAG) systems select context passages from a corpus to condition a generator model's output. A common failure mode is the inclusion of semantically redundant passages in the retrieved context, which wastes the fixed token budget on duplicate information and can dilute the signal available to the generator.

The semantic overlap tax addresses this by applying a penalty to candidate passages whose content substantially overlaps passages already selected for the context window. The intuition is straightforward: if a passage adds little novel information beyond what is already in the context, its selection should be dispreferred in favor of a passage that covers different aspects of the query.

This paper reports empirical evidence from a public SQuAD v1.1 benchmark evaluating the overlap-tax context packer against a vanilla (no-overlap-penalty) baseline. The evaluation focuses on four metrics: answer F1, exact match (EM), gold context selection rate, and context token usage. We also report a smaller verification smoke test executed in a separate branch to confirm harness executability.

The evidence supports the hypothesis that the overlap tax improves context selection quality and answer quality in the tested extractive-QA setting, though the effect is not uniformly positive across all generator configurations, and the evaluation scope has meaningful limitations.

## 2. Method

### 2.1 Semantic Overlap Tax

The semantic overlap tax modifies the context-packing stage of a RAG pipeline. Given a ranked list of candidate passages retrieved for a query, the packer iteratively selects passages to fill a fixed token budget. At each step, the score of a candidate passage is adjusted by subtracting a penalty proportional to its semantic overlap with the set of already-selected passages. This penalizes redundancy and promotes diversity in the assembled context.

The overlap tax parameter (e.g., 0.90 in the smoke test) controls the strength of this penalty. A tax of 0.0 reduces to the vanilla baseline; higher values impose stronger penalties on overlapping content.

### 2.2 Benchmark Harness

The evaluation harness comprises four source modules:

- `semantic_overlap_tax.py`: Core overlap-tax computation and context-packing logic.
- `overlap_tax_benchmark.py`: Benchmark driver for the overlap-tax packer.
- `generated_rag_benchmark.py`: Benchmark driver for generative RAG evaluation.
- `public_qa_rag_benchmark.py`: Public SQuAD-based QA/RAG benchmark driver with configurable token budgets, corpus size, top-k retrieval, generator type, and overlap-tax parameter.

The harness supports both extractive QA (used in the primary evaluation) and a fallback deterministic generator (used in the smoke test). The extractive QA mode selects answers from the provided context, while the fallback generator provides a deterministic baseline for harness verification.

### 2.3 Evaluation Protocol

For each query, the harness runs two conditions: (1) the overlap-tax packer and (2) a vanilla packer with no overlap penalty. Both conditions share the same retrieval results and token budget. The evaluation computes paired deltas across conditions for answer F1, exact match, gold context selection, and context token count. The F1 tie/win rate reports the fraction of cases where the overlap-tax condition achieves equal or higher F1 than the vanilla condition.

## 3. Results

### 3.1 Primary Evaluation: 200-Case SQuAD Benchmark

The primary result comes from a 200-case evaluation on the SQuAD v1.1 development set using extractive QA generation. This artifact was acquired from a validated parent branch and verified as executable in the current branch.

| Metric | Overlap Tax | Vanilla | Delta |
|---|---|---|---|
| Answer F1 | 0.6349 | 0.5959 | +0.0390 |
| Exact Match | 0.5633 | 0.5183 | +0.0450 |
| Gold Context Selection | 0.8100 | 0.7667 | +0.0433 |
| Context Tokens (mean) | 166.25 | 171.05 | −2.52% |
| F1 Tie/Win Rate | — | — | 0.8950 |

The overlap-tax condition improved all four primary metrics. The F1 improvement of +0.0390 and the tie/win rate of 0.8950 indicate that the overlap tax provides a consistent benefit across the majority of cases. The 2.52% reduction in context token usage confirms that the tax is filtering redundant content as intended.

### 3.2 Branch Verification Smoke Test

An 8-case smoke test was executed in the current branch using a deterministic fallback generator with the following parameters: budgets 160 and 220, corpus size 100, top-k 18, overlap tax 0.90.

| Metric | Overlap Tax | Vanilla | Delta |
|---|---|---|---|
| Gold Context Selection | 0.875 | 0.750 | +0.125 |
| Context Tokens (mean) | 160.12 | 176.00 | −8.11% |
| Answer F1 | 0.2038 | 0.2087 | −0.0050 |
| F1 Tie/Win Rate | — | — | 0.625 |

The smoke test confirmed improved gold context selection and reduced token usage. However, answer F1 showed a slight decrease of −0.0050, and the tie/win rate was 0.625—lower than the primary benchmark's 0.8950. This mixed result is consistent with the fallback generator providing only deterministic extraction without the model capacity to exploit improved context; it illustrates that improved context selection does not automatically translate to improved answer quality under all generator configurations. The branch kill condition (F1 loss > 0.02 or tie/win rate < 0.50) was not triggered.

The smoke test processed 32 rows in 0.071 seconds (450.97 rows/s), confirming the harness is executable in the current branch environment.

### 3.3 Regression Verification

All six unit tests passed, and source compilation (`compileall`) completed without errors, confirming that the harness code is syntactically valid and functionally consistent with the test suite.

## 4. Limitations

1. **Generator scope.** The primary evaluation uses extractive QA, not instruction-tuned or seq2seq generative LLMs. The overlap tax's effect on generative answer quality—where the model must synthesize rather than extract—remains untested. The project title references "Generative LLM," but the current evidence is limited to extractive QA.

2. **Single dataset.** All results are on SQuAD v1.1, a single-answer factoid QA dataset. Performance on multi-answer, abstractive, or open-domain QA datasets is unknown.

3. **Small smoke test.** The 8-case branch smoke test is too small for statistical inference. Its slight F1 decrease (−0.0050) cannot be distinguished from noise at this sample size.

4. **No statistical significance testing.** The reported deltas and tie/win rates are descriptive. No confidence intervals, p-values, or effect-size measures were computed.

5. **No hyperparameter sensitivity analysis.** The overlap-tax parameter was fixed (0.90 in the smoke test; the primary benchmark's tax value is not separately recorded in the available artifacts). The sensitivity of results to this parameter is uncharacterized.

6. **No external replication.** Results were produced in a single computational environment. Cross-environment or cross-hardware replication has not been performed.

7. **Acquired artifacts.** The primary 200-case result was acquired from a parent branch rather than generated de novo in the current branch. While the harness was verified as executable and the regression tests pass, the 200-case benchmark was not re-executed from scratch in the current branch.

## 5. Reproducibility Checklist

- **Source code available:** `src/semantic_overlap_tax.py`, `src/overlap_tax_benchmark.py`, `src/generated_rag_benchmark.py`, `src/public_qa_rag_benchmark.py`
- **Test suite available:** `tests/test_semantic_overlap_tax.py` (6 tests, all passing)
- **Dataset:** SQuAD v1.1 development set (`artifacts/datasets/squad_dev_v1.1.json`)
- **Primary result artifacts:** `artifacts/public_qa_rag_200/public_qa_rag_summary.json`, `artifacts/public_qa_rag_200/public_qa_rag_paired_deltas.jsonl`, `artifacts/public_qa_rag_200/public_qa_rag_rows.jsonl`
- **Smoke test artifacts:** `artifacts/current_branch_smoke/public_qa_rag_summary.json`, `artifacts/current_branch_smoke/public_qa_rag_paired_deltas.jsonl`, `artifacts/current_branch_smoke/public_qa_rag_rows.jsonl`
- **Evidence summary:** `artifacts/final_branch_evidence_summary.json`
- **Environment:** Python 3, dependencies installed via `uv` (`pytest`, `requests`)
- **Randomness control:** Smoke test used deterministic fallback generator; primary benchmark's randomization control is not separately documented in available artifacts.
- **Paired evaluation:** Both conditions share the same retrieval results and token budget; deltas are computed per-case.

## 6. Conclusion

The semantic overlap tax improved answer F1 by +0.0390, exact match by +0.0450, and gold context selection by +0.0433 on a 200-case SQuAD v1.1 extractive-QA benchmark, while reducing context token usage by 2.52%. The F1 tie/win rate of 0.8950 indicates the benefit is consistent across the large majority of cases. However, an 8-case smoke test with a deterministic fallback generator showed a slight F1 decrease (−0.0050), demonstrating that improved context selection does not guarantee improved answer quality under all generator configurations.

The current project artifacts support the finding that the overlap tax provides a meaningful improvement in the tested extractive-QA setting. Confidence is medium due to the limitations enumerated above—particularly the absence of evaluation on generative LLMs, the single-dataset scope, and the lack of statistical significance testing. A separate benchmark evaluating the overlap tax with instruction-tuned or seq2seq generative models on additional datasets would substantially strengthen the evidence base.

---

## Referenced Artifacts

### Source files
- `src/semantic_overlap_tax.py`
- `src/overlap_tax_benchmark.py`
- `src/generated_rag_benchmark.py`
- `src/public_qa_rag_benchmark.py`
- `tests/test_semantic_overlap_tax.py`

### Result files
- `artifacts/final_branch_evidence_summary.json`
- `artifacts/current_branch_smoke/public_qa_rag_summary.json`
- `artifacts/current_branch_smoke-summary.stdout.json`
- `artifacts/current_branch_smoke/public_qa_rag_paired_deltas.jsonl`
- `artifacts/current_branch_smoke/public_qa_rag_rows.jsonl`
- `artifacts/public_qa_rag_200/public_qa_rag_summary.json`
- `artifacts/public_qa_rag_200/public_qa_rag_paired_deltas.jsonl`
- `artifacts/public_qa_rag_200/public_qa_rag_rows.jsonl`
- `artifacts/public_qa_rag/public_qa_rag_summary.json`
- `artifacts/public_qa_rag/public_qa_rag_paired_deltas.jsonl`
- `artifacts/public_qa_rag/public_qa_rag_rows.jsonl`
- `artifacts/datasets/squad_dev_v1.1.json`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `run_notes.md`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
