# Context Rehydration Multi-Model Validation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We present a multi-model validation study for the Context Rehydration benchmark, extending prior single-model spot-check evidence to four locally-cached instruction-tuned language models of varying parameter counts (135M–1.5B). Using a stratified sample of 8 examples per task per split (80 predictions per model, 320 total), we observe non-flat ranking contrast across models: overall exact-match scores range from 0.050 (TinyLlama-1.1B-Chat) to 0.350 (Qwen2.5-1.5B-Instruct). Qwen-family models perform abstention calibration reliably, while reversible compression exact-match remains at 0.000 for all four models, indicating a consistent failure mode on non-abstention rehydration tasks. Scorer spot-check reliability is 1.000 for three of four models and 0.933 for TinyLlama (two possible false negatives from verbose outputs). These results are bounded by synthetic/weakly-labeled data and small local models; they should not be generalized to production settings or larger models without further validation.

## 1. Introduction

Context Rehydration refers to the task of reconstructing or selectively expanding compressed context from a condensed representation back into a form suitable for downstream use. A benchmark for this task was previously developed with a deterministic synthetic evaluation and a 40-example single-model spot check on Qwen2.5-0.5B-Instruct. The present study extends that work by evaluating four instruction-tuned models of different families and sizes on a larger stratified sample, with the goal of determining whether model-level ranking contrast exists and whether scorer reliability holds across models.

The central questions addressed are:

1. Does the Context Rehydration benchmark produce distinguishable performance rankings across multiple models, or do all models score identically within sampling noise?
2. Are there task-specific failure modes that persist across models (e.g., reversible compression)?
3. Is the automated scorer reliable across different model output styles?

A branch-level kill condition was defined prior to execution: terminate if all tested models produce indistinguishable exact scores within the sample, if scorer spot checks prove unreliable, or if no second executable model/variant can be evaluated. The kill condition was not met.

## 2. Method

### 2.1 Benchmark Structure

The Context Rehydration benchmark evaluates models on tasks related to compressed-context reconstruction. The benchmark comprises two data splits:

- **Curated split** (`data/curated_rehydration_mvp.jsonl`): hand-curated examples with verified labels.
- **Uncurated split** (`data/uncurated_trace_control.jsonl`): synthetically generated or weakly-labeled examples serving as a control.

Tasks include abstention calibration (correctly identifying when to refuse to answer given insufficient context) and reversible compression (reconstructing the original text from a compressed form). The evaluation uses exact-match scoring against reference answers.

### 2.2 Evaluation Harness

Two scripts from the parent project were reused without modification:

- `scripts/context_rehydration_benchmark.py`: defines the benchmark tasks and scoring logic.
- `scripts/evaluate_local_model.py`: loads a specified model, runs inference on the benchmark, and records predictions with scorer spot checks.

An aggregation script (`scripts/aggregate_multimodel_results.py`) was added to combine per-model summaries into a cross-model comparison.

### 2.3 Models

Four locally-cached instruction-tuned models were evaluated:

| Model | Parameters | Family |
|---|---|---|
| Qwen2.5-1.5B-Instruct | 1.5B | Qwen |
| Qwen2.5-0.5B-Instruct | 0.5B | Qwen |
| SmolLM2-135M-Instruct | 135M | SmolLM2 |
| TinyLlama-1.1B-Chat-v1.0 | 1.1B | TinyLlama |

All models were loaded via HuggingFace Transformers with CUDA support (`torch.cuda.is_available() == True` confirmed at environment setup).

### 2.4 Sampling and Scoring

Each model was evaluated with 8 examples per task per split, yielding 80 predictions per model and 320 predictions total. Scorer spot checks were performed with `--audit-n 30` for the full evaluation loop. Exact-match scoring was used as the primary metric.

## 3. Results

### 3.1 Overall Exact-Match Scores

| Model | Overall Exact | Curated Exact | Uncurated Exact |
|---|---|---|---|
| Qwen2.5-1.5B-Instruct | 0.350 | 0.350 | 0.350 |
| Qwen2.5-0.5B-Instruct | 0.2875 | 0.300 | 0.275 |
| SmolLM2-135M-Instruct | 0.2125 | 0.200 | 0.225 |
| TinyLlama-1.1B-Chat-v1.0 | 0.050 | 0.025 | 0.075 |

The overall exact-match range across models is 0.300 (from 0.050 to 0.350), confirming non-flat ranking contrast. The ranking is consistent: Qwen2.5-1.5B > Qwen2.5-0.5B > SmolLM2-135M > TinyLlama-1.1B.

### 3.2 Task-Specific Findings

**Reversible compression.** Exact-match score for reversible compression tasks was 0.000 for all four models. This represents a consistent failure mode: no tested model successfully reconstructed compressed text to exact-match standard. This negative result is one of the most salient findings.

**Abstention calibration.** Qwen-family models handled abstention calibration reliably, correctly identifying instances where the model should decline to answer given insufficient context. This task appears to drive the performance separation between Qwen and non-Qwen models.

**Non-abstention rehydration.** Non-abstention rehydration tasks were consistently weak across all models, contributing to the low overall scores.

### 3.3 Curated vs. Uncurated Split

Differences between curated and uncurated exact-match scores were small and inconsistent in direction. Qwen2.5-0.5B scored slightly higher on curated (0.300) than uncurated (0.275), while SmolLM2-135M scored slightly higher on uncurated (0.225) than curated (0.200). TinyLlama-1.1B also scored higher on uncurated (0.075) than curated (0.025). Given the small sample sizes (8 examples per task per split), these differences should not be interpreted as meaningful without further replication.

### 3.4 Scorer Spot-Check Reliability

| Model | Scorer Spot-Check Reliability | Notes |
|---|---|---|
| Qwen2.5-1.5B-Instruct | 1.000 | — |
| Qwen2.5-0.5B-Instruct | 1.000 | — |
| SmolLM2-135M-Instruct | 1.000 | — |
| TinyLlama-1.1B-Chat-v1.0 | 0.933 | Two possible false negatives due to verbose outputs |

Three of four models achieved perfect scorer spot-check reliability. TinyLlama's reliability of 0.933 reflects two possible false negatives where the model's verbose output style may have caused the exact-match scorer to reject correct-but-wordy responses. This suggests the scoring methodology may be partially sensitive to output format rather than semantic correctness alone.

### 3.5 Verification Checks

The following verification steps were completed successfully:

- Python compilation check (`py_compile`) on both benchmark and evaluator scripts.
- Smoke run of Qwen2.5-0.5B-Instruct with `--per-task 1 --audit-n 4`.
- Full four-model evaluation loop with `--per-task 8 --audit-n 30`.
- Aggregation script execution.
- Automated assertions confirming: 4 model summaries present, 320 total predictions, ranking contrast range > 0.05, and at least three scorer spot checks at reliability ≥ 0.99.

## 4. Limitations

1. **Synthetic and weakly-labeled data.** Both the curated and uncurated splits are derived from synthetic or weakly-labeled sources. Performance on these splits may not reflect performance on real-world context rehydration tasks.

2. **Small sample size.** Eight examples per task per split (80 predictions per model) provides limited statistical power. Confidence intervals on exact-match scores are wide at this sample size, and small differences between models or splits should not be over-interpreted.

3. **Small local models only.** All tested models have ≤ 1.5B parameters. Results may not extrapolate to larger or differently-trained models. No proprietary or API-served models were evaluated.

4. **Reversible compression failure is total.** The universal 0.000 exact-match on reversible compression may reflect a limitation of the scoring methodology (exact-match is stringent for reconstruction tasks) rather than complete inability to partially reconstruct compressed text. A softer metric (e.g., BLEU, ROUGE, or semantic similarity) might yield non-zero scores.

5. **Scorer format sensitivity.** TinyLlama's 0.933 spot-check reliability, with two possible false negatives attributed to verbose outputs, indicates that the exact-match scorer may penalize correct answers expressed in a different format. This is a known limitation of exact-match evaluation.

6. **Single evaluation environment.** All runs were conducted in a single local environment with CUDA. No cross-hardware or cross-environment replication was performed.

7. **No prompt variant comparison.** The evaluation used a fixed prompting strategy. Sensitivity to prompt design was not tested.

8. **No human evaluation.** Scorer reliability was assessed via automated spot checks, not human judgment of output quality.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Benchmark scripts available in project | Yes: `context_rehydration_benchmark.py`, `evaluate_local_model.py` |
| Data files available in project | Yes: `curated_rehydration_mvp.jsonl`, `uncurated_trace_control.jsonl` |
| Aggregation script available | Yes: `aggregate_multimodel_results.py` |
| Model identifiers specified | Yes: all four HuggingFace model IDs recorded |
| Sample size reported | Yes: 8 per task per split, 80 per model, 320 total |
| Scorer spot-check methodology described | Yes: `--audit-n 30` |
| Per-model predictions persisted | Yes: `predictions.jsonl` per model directory |
| Scorer spot-check results persisted | Yes: `scorer_spotcheck.jsonl` per model directory |
| Aggregate summaries persisted | Yes: `aggregate_summary.json` and `aggregate_summary.md` |
| Hardware environment described | Partial: CUDA confirmed; specific GPU not recorded in artifacts |
| Random seeds recorded | Not present in artifacts |
| Software versions recorded | Not explicitly recorded; Python venv with PyTorch + Transformers confirmed |

## 6. Conclusion

This multi-model validation of the Context Rehydration benchmark demonstrates that the benchmark produces non-flat ranking contrast across four small instruction-tuned models, with overall exact-match scores spanning a range of 0.300. The most salient findings are:

- **Ranking is distinguishable:** Qwen2.5-1.5B-Instruct leads at 0.350, while TinyLlama-1.1B-Chat trails at 0.050. The branch kill condition (indistinguishable scores) was not met.
- **Reversible compression is a universal failure mode:** All four models scored 0.000 exact-match on reversible compression tasks, indicating this subtask is beyond the capability of the tested models under exact-match evaluation.
- **Abstention calibration drives separation:** Qwen-family models' relative advantage appears concentrated in abstention calibration, suggesting this task is more tractable for current small models than reconstruction tasks.
- **Scorer reliability is high but format-sensitive:** Three of four models achieved perfect spot-check reliability; TinyLlama's verbose output style caused two possible false negatives.

The current project artifacts support these findings in the tested setting. Evidence remains bounded by synthetic/weakly-labeled data and small local models. The recommended next step is to use these recorded multi-model artifacts when deciding whether to graduate the benchmark to real traces or extraction-hardening work, rather than extending the same mechanism with additional small-model evaluations.

## Referenced Artifacts

### Run notes and decision
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Scripts
- `scripts/context_rehydration_benchmark.py`
- `scripts/evaluate_local_model.py`
- `scripts/aggregate_multimodel_results.py`

### Data
- `data/curated_rehydration_mvp.jsonl`
- `data/uncurated_trace_control.jsonl`

### Result files
- `results/multimodel/aggregate_summary.json`
- `results/multimodel/aggregate_summary.md`
- `results/multimodel/qwen2p5_1p5b/summary.json`
- `results/multimodel/qwen2p5_1p5b/summary.md`
- `results/multimodel/qwen2p5_1p5b/predictions.jsonl`
- `results/multimodel/qwen2p5_1p5b/scorer_spotcheck.jsonl`
- `results/multimodel/qwen2p5_0p5b/summary.json`
- `results/multimodel/qwen2p5_0p5b/summary.md`
- `results/multimodel/qwen2p5_0p5b/predictions.jsonl`
- `results/multimodel/qwen2p5_0p5b/scorer_spotcheck.jsonl`
- `results/multimodel/smollm2_135m/summary.json`
- `results/multimodel/smollm2_135m/summary.md`
- `results/multimodel/smollm2_135m/predictions.jsonl`
- `results/multimodel/smollm2_135m/scorer_spotcheck.jsonl`
- `results/multimodel/tinyllama_1p1b/summary.json`
- `results/multimodel/tinyllama_1p1b/summary.md`
- `results/multimodel/tinyllama_1p1b/predictions.jsonl`
- `results/multimodel/tinyllama_1p1b/scorer_spotcheck.jsonl`

### Paper and audit artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
