# Document-Field Importance for Prompt Packing: Validation via Local LLM Generation on SQuAD

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We investigate whether document-field importance signals, when used to guide prompt-packing policies for retrieval-augmented generation, improve generated-answer accuracy over similarity-centric packing baselines. Using a local `google/flan-t5-small` model on CUDA with greedy decoding, we evaluate four packing policies on 240 SQuAD development examples under a 70-token packing budget. The targeted field-importance policy (`targeted_fix_from_importance_set`) achieves 67.08% exact match and 75.54% token F1, compared to 57.50% exact match and 65.36% token F1 for similarity-centric packing—improvements of 9.58 and 10.18 points respectively. An oracle upper bound (`importance_oracle_upper_bound`) reaches 71.67% exact match, leaving a 4.58-point gap indicating that the learned policy captures most but not all answer-bearing field selection value. These results are limited to a single small instruction-tuned model, one dataset slice, and one hardware configuration; broader replication is needed before generalizing.

## 1. Introduction

Retrieval-augmented generation systems must select which retrieved passages or document fields to include in a language model's prompt, typically under a fixed token budget. The dominant approach ranks candidates by query similarity and packs the highest-scoring items until the budget is exhausted. However, similarity to the query does not necessarily indicate that a field contains the answer; it may instead reflect topical overlap without answer-bearing content.

An alternative is to use document-field importance signals—estimates of which fields are likely to contain answer-relevant information—to guide packing decisions. Prior work in this project line established that field-importance policies improve evidence-presence proxies (e.g., whether the answer string appears in the packed prompt). The present study extends that line by evaluating whether the uplift persists when the packed prompts are actually consumed by a local language model to generate answers, rather than being scored only on evidence-presence metrics.

We report results from a controlled local benchmark on a SQuAD slice, comparing four packing policies: similarity-centric packing, a field-prior baseline, a targeted field-importance policy, and an importance oracle upper bound. We find that the targeted field-importance policy substantially outperforms similarity-centric packing on both exact match and token F1, clearing a pre-registered success threshold of ≥5 exact-match points improvement.

## 2. Method

### 2.1 Problem Setting

Given a question and a set of document fields (passages), the task is to select a subset of fields that fits within a token budget and maximizes the quality of a language model's generated answer. Each packing policy implements a ranking and truncation strategy over the available fields.

### 2.2 Packing Policies

We evaluate four policies, listed in the order they ranked by exact-match accuracy:

1. **`importance_oracle_upper_bound`**: An oracle policy with access to ground-truth answer locations. This policy always includes fields containing the answer, establishing an upper bound on achievable performance under the token budget.

2. **`targeted_fix_from_importance_set`**: A learned policy that uses field-importance signals derived from the parent project's importance estimation to prioritize fields likely to contain answer-bearing content. This is the primary experimental condition.

3. **`field_prior_baseline`**: A baseline that uses generic field-level prior importance (not query-specific) to guide packing, providing a midpoint between uninformative and fully targeted importance.

4. **`similarity_centric`**: The standard baseline that ranks fields by their similarity to the query and packs the top-ranked fields until the budget is exhausted.

### 2.3 Evaluation Protocol

The benchmark script (`scripts/evaluate_squad_generation_field_importance.py`) reuses the parent project's SQuAD field-importance transformation. For each example and each policy, the script constructs a packed prompt from the selected fields and feeds it to the same local model with greedy decoding. Generated answers are then scored against reference answers.

### 2.4 Branch Decision Criterion

A pre-registered kill condition was defined before running the benchmark: finalize negative if `targeted_fix_from_importance_set` improves exact-answer accuracy by fewer than 5 points over `similarity_centric`, or if it ranks behind `similarity_centric` on the same local model. This criterion provides a clear success/failure threshold to prevent post-hoc rationalization of marginal results.

## 3. Results

### 3.1 Experimental Configuration

| Parameter | Value |
|---|---|
| Model | `google/flan-t5-small` |
| Decoding | Greedy |
| Hardware | Local CUDA GPU |
| Dataset | 240 SQuAD dev examples |
| Packing budget | 70 tokens |
| Batch size | 16 |
| Max generated tokens | 16 |

### 3.2 Main Results

| Policy | Exact Match (%) | Token F1 (%) | Evidence Recall (%) | Answer Present (%) |
|---|---|---|---|---|
| `importance_oracle_upper_bound` | 71.67 | 81.10 | 99.58 | 99.58 |
| `targeted_fix_from_importance_set` | 67.08 | 75.54 | 89.58 | 91.67 |
| `field_prior_baseline` | 65.42 | 73.29 | 80.42 | 89.58 |
| `similarity_centric` | 57.50 | 65.36 | 51.67 | 78.75 |

### 3.3 Key Comparisons

The targeted field-importance policy (`targeted_fix_from_importance_set`) improved over similarity-centric packing by:

- **+9.58 exact-match points** (57.50% → 67.08%), clearing the pre-registered ≥5-point threshold.
- **+10.18 token-F1 points** (65.36% → 75.54%).
- **+37.91 evidence-recall points** (51.67% → 89.58%), indicating that the importance-guided policy is substantially better at including answer-bearing fields in the packed prompt.
- **+12.92 answer-present points** (78.75% → 91.67%).

The field-prior baseline also outperformed similarity-centric packing (+7.92 exact-match points), suggesting that even non-query-specific field priors carry useful signal. However, the targeted policy exceeded the field-prior baseline by an additional 1.66 exact-match points, indicating that query-specific importance estimates add marginal value beyond static priors.

### 3.4 Oracle Gap Analysis

The remaining gap between `targeted_fix_from_importance_set` (67.08%) and `importance_oracle_upper_bound` (71.67%) is 4.58 exact-match points. This suggests the learned targeted policy captures most but not all of the answer-bearing field selection value available under the token budget. The oracle's near-perfect evidence recall (99.58%) versus the targeted policy's 89.58% indicates that approximately 10 percentage points of evidence recall remain uncaptured, which translates to the observed 4.58-point exact-match deficit.

## 4. Limitations

1. **Single model**: All results are from `google/flan-t5-small`. Whether the observed uplift scales to larger models (e.g., FLAN-T5-base, FLAN-T5-large, or decoder-only architectures) is unknown.

2. **Single dataset slice**: The benchmark uses 240 SQuAD development examples. SQuAD is a factoid short-answer dataset; performance on datasets requiring longer answers, multi-hop reasoning, or different domain distributions may differ.

3. **Small token budget**: The 70-token packing budget is restrictive and may amplify the advantage of importance-guided selection. Under larger budgets where similarity-centric packing can include more fields, the relative advantage may shrink.

4. **Greedy decoding only**: All generations use greedy decoding. Sampling-based or beam-search decoding may change the absolute and relative performance of the policies.

5. **No statistical significance testing**: Results are reported as point estimates on a single 240-example slice without confidence intervals or significance tests. The observed differences, while substantial in magnitude, have not been formally tested for statistical reliability.

6. **No cross-dataset or cross-model replication**: The claim ledger explicitly notes that external replication and broader hardware/model coverage have not been conducted.

7. **Confidence rating**: The project decision assigns medium confidence and strong evidence strength, reflecting that the result is internally consistent but not yet externally validated.

8. **Oracle is an upper bound, not an achievable target**: The importance oracle has access to ground-truth answer locations and thus represents an information-theoretic ceiling, not a practically attainable policy.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Benchmark script available | Yes: `scripts/evaluate_squad_generation_field_importance.py` |
| Script compiles cleanly | Yes: `python -m py_compile` passed |
| Model identifier specified | Yes: `google/flan-t5-small` |
| Decoding strategy specified | Yes: greedy |
| Hardware specified | Yes: local CUDA GPU (specific GPU model not recorded) |
| Dataset specified | Yes: SQuAD dev v1.1, 240-example slice (`data/squad_dev_v1.1.json`) |
| Token budget specified | Yes: 70 tokens |
| Batch size specified | Yes: 16 |
| Max generated tokens specified | Yes: 16 |
| Metrics artifact saved | Yes: `artifacts/squad_generation_field_importance_metrics.json` |
| Per-policy predictions saved | Yes: `data/squad_generation_field_importance_predictions.csv` |
| Pre-registered decision criterion | Yes: ≥5 exact-match points improvement over similarity-centric |
| Random seed specified | Not recorded in artifacts |
| Python environment specified | Partially: `.venv` with `torch`, `transformers`, `sentencepiece`, `tqdm` (exact versions not recorded) |

## 6. Conclusion

On a 240-example SQuAD slice with `google/flan-t5-small` and a 70-token packing budget, targeted field-importance prompt packing improves exact-match accuracy by 9.58 points and token F1 by 10.18 points over similarity-centric packing, clearing a pre-registered success threshold. The ranking of policies is consistent: oracle > targeted importance > field-prior baseline > similarity-centric. The 4.58-point gap between the targeted policy and the oracle upper bound indicates room for improvement in importance estimation.

These findings provide positive but bounded evidence that field-importance signals improve generated-answer quality when used to guide prompt packing. The result is specific to one small model, one dataset, one budget size, and one hardware configuration. Replication across models, datasets, and budget regimes is necessary before drawing broader conclusions.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Project config | `.omx/project.json` |
| Benchmark script | `scripts/evaluate_squad_generation_field_importance.py` |
| Metrics output | `artifacts/squad_generation_field_importance_metrics.json` |
| Per-policy predictions | `data/squad_generation_field_importance_predictions.csv` |
| SQuAD dev data | `data/squad_dev_v1.1.json` |
| Evidence bundle | `papers/source-record-redacted/evidence_bundle.json` |
| Claim ledger | `papers/source-record-redacted/claim_ledger.json` |
| Publication manifest | `papers/source-record-redacted/publication/publication_manifest.json` |
| Initial prompt | `prompts/initial.md` |
| Resume prompt | `prompts/resume.md` |
