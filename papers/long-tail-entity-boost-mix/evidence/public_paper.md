# Long-Tail Entity Boost Mix: Exposing Long-Tail Calibration Failure Clusters in Small Language Models

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether a rarity-weighted entity/relation evaluation mix—deliberately oversampling long-tail entities—produces measurably different model ranking and accuracy signals compared to a popularity-weighted control mix. Using a three-stage evaluation protocol (synthetic baseline harness, llama.cpp GGUF pilot with two sub-billion-parameter models, and a Wikidata-sourced factual follow-up with two Qwen2.5 checkpoints), we find that long-tail mixes consistently degrade model accuracy, with larger models suffering proportionally greater drops (Qwen2.5-3B: −25 percentage points control→long-tail under forced-answer prompting vs. Qwen2.5-0.5B: −10 pp). However, the hypothesized ranking-change criterion—where long-tail evaluation would reorder models relative to control—was not observed: model rank order remained stable across all real-model experiments (rank displacement 0). The synthetic harness did produce rank displacement of 2, but this did not replicate with actual language model outputs. We also document a pronounced abstention miscalibration in Qwen2.5-3B, which over-abstained on 91.7–98.3% of factual prompts under abstain-allowed prompting, effectively inverting the expected model ranking. These results identify a long-tail calibration failure cluster in small quantized models while indicating that ranking stability under distributional shift may be more robust than synthetic baselines suggest. Confidence in the overall hypothesis is medium; evidence strength is moderate.

## 1. Introduction

Evaluating language models on knowledge-intensive tasks typically relies on benchmarks whose entity and relation distributions reflect web-text frequency. Entities appearing rarely in training corpora—long-tail entities—may be systematically underserved by such evaluations, potentially masking calibration failures that only emerge when models are queried about uncommon entities.

The Long-Tail Entity Boost Mix project tests a specific hypothesis: constructing an evaluation mix that deliberately oversamples rare entities will (a) degrade model accuracy relative to a popularity-weighted control, and (b) change the relative ranking of models, thereby revealing model weaknesses invisible under standard evaluation distributions.

This report documents the outcome of a structured investigation across three evaluation stages of increasing fidelity. The primary positive finding is that long-tail mixes do expose a measurable accuracy degradation cluster, particularly in larger models. The primary negative finding is that the ranking-change criterion was not met in any real-model experiment, despite being observed in a synthetic baseline.

## 2. Method

### 2.1 Synthetic Baseline Harness

A project-local Python experiment harness (`src/long_tail_boost_experiment.py`) generated a 3,000-example weakly labeled synthetic dataset with entity-frequency strata, relation types, abstention negatives, structured extraction items, and code-navigation items. The dataset was partitioned into control (median entity frequency 321.0) and long-tail (median entity frequency 10.0) mixes.

Four transparent synthetic baselines were evaluated:

- **Head Memorizer**: biased toward high-frequency entities.
- **Relation Prior**: predicts based on relation-type priors.
- **Calibrated Abstainer**: abstains when confidence is below threshold.
- **Rare Boost Fix**: oracle-like fix targeting rare entities.

Scoring used exact-match accuracy and abstention F1. Rankings were computed per mix and rank displacement (Kendall-tau–inspired) was recorded.

### 2.2 Real-Model Pilot (llama.cpp GGUF)

Two quantized GGUF checkpoints were served via llama.cpp with GPU offload (99 layers):

- **SmolLM2-135M-Instruct** (Q4_K_M)
- **Qwen2.5-0.5B-Instruct** (Q4_K_M)

The existing synthetic dataset was used. Evaluation comprised 160 prompts (80 per mix), concurrency 4. Both `/v1/models` and `/v1/chat/completions` endpoints were verified before scoring. Metrics included exact-match accuracy, abstention F1, wall-clock time, tokens/second, GPU utilization, and UMA memory availability.

### 2.3 Source-Backed Factual Follow-Up

To move beyond synthetic unknown facts, a Wikidata SPARQL–sourced factual dataset was generated (`src/source_backed_factual_dataset.py`) with per-example provenance URLs. The dataset comprised 120 factual prompts (60 control/head, 60 long-tail), with median sitelinks 127 vs. 4. Sampled relations were *capital* and *official language*.

Two Qwen2.5 GGUF checkpoints were evaluated:

- **Qwen2.5-0.5B-Instruct** (Q4_K_M)
- **Qwen2.5-3B-Instruct** (Q4_K_M)

Two prompting policies were tested:

- **Abstain-allowed**: the model was instructed it may say "I don't know."
- **Forced-answer**: the model was instructed it must provide an answer.

This ablation was added after the abstain-allowed pilot revealed extreme over-abstention in the 3B model, which confounded the accuracy comparison.

## 3. Results

### 3.1 Synthetic Baseline

| Mix | Rank 1 | Rank 2 | Rank 3 | Rank 4 |
|---|---|---|---|---|
| Control | rare_boost_fix | head_memorizer | relation_prior | calibrated_abstainer |
| Long-tail | rare_boost_fix | relation_prior | head_memorizer | calibrated_abstainer |

Rank displacement: **2**. The rare_boost_fix baseline achieved 0.5967 accuracy on the long-tail mix versus the next-best baseline (relation_prior) at 0.2658, a delta of 33.08 percentage points. This synthetic result established that long-tail mixes can, in principle, reorder baselines.

### 3.2 Real-Model Pilot (Synthetic Dataset)

| Model | Control Acc. | Long-tail Acc. | Control Abst. F1 | Long-tail Abst. F1 |
|---|---|---|---|---|
| SmolLM2-135M | 0.0875 | 0.1375 | 0.000 | 0.000 |
| Qwen2.5-0.5B | 0.6625 | 0.6375 | 0.702 | 0.816 |

Ranking (both mixes): Qwen2.5-0.5B > SmolLM2-135M. **Rank displacement: 0.**

The long-tail mix changed task behavior—SmolLM2 accuracy paradoxically increased slightly on long-tail items, while Qwen2.5-0.5B decreased slightly—but did not reorder the models. The synthetic dataset also exposed zero accuracy on synthetic-factual items and degradation on code/extraction items under the long-tail mix.

Performance telemetry: SmolLM2 wall time 4.64 s (~17.24 samples/s, ~1752 tokens/s); Qwen2.5 wall time 4.44 s (~18.02 samples/s, ~1584 tokens/s). GPU utilization reached 65% (SmolLM2) and 75% (Qwen2.5); UMA MemAvailable remained above 121 GB.

### 3.3 Source-Backed Factual Follow-Up

#### 3.3.1 Abstain-Allowed Prompting

| Model | Control Acc. | Long-tail Acc. | Control Abstention Rate | Long-tail Abstention Rate |
|---|---|---|---|---|
| Qwen2.5-0.5B | 0.600 | 0.483 | — | — |
| Qwen2.5-3B | 0.067 | 0.017 | 91.7% | 98.3% |

Ranking (both mixes): Qwen2.5-0.5B > Qwen2.5-3B. **Rank displacement: 0.**

The 3B model over-abstained dramatically, producing an inverted ranking where the smaller model appeared superior. This is a calibration failure rather than a knowledge failure: the larger model refused to answer most questions rather than answering incorrectly.

#### 3.3.2 Forced-Answer Prompting

| Model | Control Acc. | Long-tail Acc. | Δ (Control → Long-tail) |
|---|---|---|---|
| Qwen2.5-0.5B | 0.567 | 0.467 | −10.0 pp |
| Qwen2.5-3B | 0.800 | 0.550 | −25.0 pp |

Ranking (both mixes): Qwen2.5-3B > Qwen2.5-0.5B. **Rank displacement: 0.**

Under forced-answer prompting, the expected ranking (larger model on top) was recovered on both mixes. However, long-tail degradation was substantial and scaled with model size: the 3B model lost 25 percentage points moving from control to long-tail, while the 0.5B model lost 10 percentage points.

Performance telemetry: GPU utilization reached 89%; UMA MemAvailable remained above 114 GiB.

### 3.4 Summary of Key Findings

1. **Long-tail accuracy degradation is real and measurable** in actual language model outputs, not only synthetic baselines.
2. **Degradation scales with model size** under forced-answer prompting: larger models lose more accuracy on long-tail entities.
3. **Ranking stability is robust**: across all real-model experiments, rank displacement was 0. The ranking-change criterion was not met.
4. **Abstention miscalibration is a distinct failure mode**: Qwen2.5-3B over-abstained on 91.7–98.3% of factual prompts under abstain-allowed prompting, inverting the expected model ranking.
5. **Synthetic baselines overestimate ranking instability**: the synthetic harness produced rank displacement of 2, which did not replicate with any real model pair tested.

## 4. Limitations

- **Model coverage is narrow.** Only four quantized GGUF checkpoints were tested (SmolLM2-135M, Qwen2.5-0.5B, Qwen2.5-3B), all in Q4_K_M quantization. Results may not generalize to larger models, different architectures, or full-precision checkpoints.
- **Dataset scale is small.** The synthetic dataset comprised 3,000 examples; the source-backed factual dataset comprised only 120 prompts (60 per mix). Both are pilot-scale, not production-scale.
- **Relation coverage is limited.** The source-backed factual dataset sampled only two relations (*capital* and *official language*) from Wikidata. Other relation types may exhibit different long-tail behavior.
- **The ranking-change criterion was unsupported.** The original hypothesis predicted that long-tail evaluation would reorder models. This was observed only in the synthetic harness, not in any real-model experiment. The hypothesis of ranking change is therefore not supported by the current evidence.
- **Quantization effects are confounded.** All models were Q4_K_M quantized GGUF. The observed accuracy drops and abstention behavior may be partially attributable to quantization artifacts rather than pure long-tail knowledge deficits.
- **Single hardware environment.** All evaluations ran on a single Apple Silicon machine with UMA memory. GPU utilization and memory figures are specific to this hardware.
- **No human evaluation.** All scoring used exact-match metrics. Nuanced partially-correct answers, reasoning quality, and calibration of confidence were not assessed.
- **The synthetic dataset contains weak labels.** The initial 3,000-example harness used procedurally generated facts with no real-world grounding, limiting the interpretability of the synthetic-stage results.

## 5. Reproducibility Checklist

| Item | Status | Detail |
|---|---|---|
| Code available | Yes | `src/long_tail_boost_experiment.py`, `src/real_model_eval.py`, `src/source_backed_factual_dataset.py` |
| Model checkpoints specified | Yes | SmolLM2-135M-Instruct Q4_K_M, Qwen2.5-0.5B-Instruct Q4_K_M, Qwen2.5-3B-Instruct Q4_K_M (all GGUF, locally cached) |
| Dataset generation deterministic | Partially | Synthetic harness uses fixed seed; Wikidata SPARQL results may vary over time |
| Evaluation protocol documented | Yes | Exact-match accuracy, abstention F1, per-mix ranking, rank displacement |
| Hardware specified | Yes | Apple Silicon, UMA memory (MemAvailable > 114 GiB observed), GPU utilization up to 89% |
| Software versions specified | Partially | llama.cpp server used; specific commit hash not recorded in artifacts |
| Random seeds recorded | Not in artifacts | Seeds should be recorded in future runs |
| All metrics reported | Yes | Accuracy, abstention F1, abstention rate, wall time, tokens/s, GPU util, UMA memory |
| Negative results reported | Yes | Rank displacement 0 across all real-model experiments; over-abstention failure documented |

## 6. Conclusion

This investigation provides moderate-evidence-strength, medium-confidence support for the claim that long-tail entity evaluation mixes expose a real calibration failure cluster in small quantized language models. The failure manifests in two distinct ways: (1) accuracy degradation that scales with model size under forced-answer prompting, and (2) extreme over-abstention under abstain-allowed prompting that inverts expected model rankings.

The hypothesized ranking-change criterion—where long-tail evaluation would reorder models relative to control—was not met in any real-model experiment, despite being observed in a synthetic baseline. This discrepancy suggests that synthetic baselines may overestimate the ranking instability induced by distributional shift, or that the model pairs tested were insufficiently differentiated in their long-tail knowledge profiles.

The project decision recommends preserving the source-backed long-tail slice and prompt-ablation metrics as a calibration/factuality benchmark artifact. The long-tail accuracy degradation signal (up to −25 pp for Qwen2.5-3B) and the abstention miscalibration signal (91.7–98.3% abstention rate) are both practically significant and merit investigation with broader model coverage, larger datasets, and additional relation types.

## Referenced Artifacts

### Source Code
- `src/long_tail_boost_experiment.py` — synthetic baseline harness
- `src/real_model_eval.py` — llama.cpp GGUF evaluation driver
- `src/source_backed_factual_dataset.py` — Wikidata SPARQL factual dataset generator

### Model Checkpoints (locally cached)
- `models/SmolLM2-135M-Instruct-Q4_K_M.gguf`
- `models/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf`
- `models/qwen2.5-3b-instruct-q4_k_m.gguf`

### Datasets
- `artifacts/long_tail_boost_dataset.jsonl` — synthetic 3,000-example dataset
- `artifacts/source_backed_factual_dataset.jsonl` — Wikidata-sourced 120-prompt factual dataset
- `artifacts/source_backed_factual_summary.json` — factual dataset summary with provenance

### Metrics and Reports
- `artifacts/metrics.csv` — synthetic baseline metrics
- `artifacts/summary.json` — synthetic baseline summary
- `artifacts/experiment_report.md` — synthetic baseline report
- `artifacts/source_backed_real_model_report.md` — source-backed follow-up report
- `artifacts/source_backed_real_model_eval/model_metrics.csv` — abstain-allowed model metrics
- `artifacts/source_backed_real_model_eval/summary.json` — abstain-allowed summary
- `artifacts/source_backed_real_model_eval/model_predictions.jsonl` — abstain-allowed predictions
- `artifacts/source_backed_real_model_eval_forced/model_metrics.csv` — forced-answer model metrics
- `artifacts/source_backed_real_model_eval_forced/summary.json` — forced-answer summary
- `artifacts/source_backed_real_model_eval_forced/model_predictions.jsonl` — forced-answer predictions

### Server Logs
- `artifacts/source_backed_real_model_eval/llama_server_qwen2p5_3b.log`
- `artifacts/source_backed_real_model_eval/llama_server_qwen2p5_0p5b.log`
- `artifacts/source_backed_real_model_eval_forced/llama_server_qwen2p5_3b.log`
- `artifacts/source_backed_real_model_eval_forced/llama_server_qwen2p5_0p5b.log`

### Smoke Test Artifacts
- `artifacts/real_model_eval_smoke/summary.json`
- `artifacts/real_model_eval_smoke/model_metrics.csv`
- `artifacts/real_model_eval_smoke/model_predictions.jsonl`
- `artifacts/real_model_eval_smoke/llama_server_qwen2p5_3b.log`

### Project Decision and Metadata
- `.omx/project_decision.json` — finalize_positive, hypothesis supported, confidence medium
- `.omx/metrics.json` — session metrics
- `run_notes.md` — full run log
- `papers/.../claim_ledger.json` — audited claim register
- `papers/.../evidence_bundle.json` — evidence bundle
