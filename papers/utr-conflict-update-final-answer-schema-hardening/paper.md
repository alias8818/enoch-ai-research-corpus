# UTR Conflict-Update Final-Answer Schema Hardening

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We describe a schema-hardening intervention for the conflict-update subtask within a utility-task-routing (UTR) reread-and-resolve pipeline. The identified failure mode occurs when a language model, prompted for a final answer after reread, instead emits control-JSON tokens such as `{"need_reread": true}`, producing a non-answer at final-answer extraction time. We implement a deterministic fallback guard that, upon detecting such schema violations, extracts the allowed assignment directly from the reread evidence using a priority rule (reassignment destination, retained audit assignment, or visible dispatch assignment). On a 200-example endpoint slice served by Qwen2.5-7B-Instruct (Q4_K_M) via llama.cpp, the hardened policy achieves 1.000 conflict-update accuracy and 1.000 overall accuracy, compared to 0.980 conflict-update accuracy for the alias-only policy on the same slice. The guard resolved the single remaining schema-violation failure in the 200-example evaluation. An offline deterministic check confirmed that the extraction rule matches the gold answer for all 375 conflict-update rows in the synthetic dataset. Results are bounded to a single model, a single quantization, a single synthetic dataset, and a 200-example evaluation slice; generalization to other models, datasets, or deployment conditions is not established.

## 1. Introduction

In multi-turn reread-and-resolve pipelines for utility task routing, a language model may be asked to produce a final answer after reviewing accumulated evidence. A recurring failure mode arises when the model, rather than emitting a well-formed answer, regurgitates control-plane JSON intended for the reread loop (e.g., `{"need_reread": true}`). This schema violation causes the final-answer extractor to return a non-answer, degrading accuracy on the affected subtask.

This work addresses the conflict-update subtask specifically, where the model must determine the current valid assignment after a reassignment or audit conflict. Prior intervention on alias-resolution final-answer extraction (the parent alias intervention) improved alias_resolution accuracy to 1.000 but left conflict_update accuracy at 0.880 on the same evaluation slice, with remaining failures attributable to the control-JSON emission pattern described above.

We investigate whether a branch-specific schema guard—applied only at final-answer extraction time for conflict_update rows—can eliminate this failure mode without regressing alias_resolution accuracy or introducing new failure modes.

## 2. Method

### 2.1 Failure Mode Analysis

Inspection of parent-run failure records revealed that conflict_update final-answer failures consistently involved the model emitting reread-control JSON rather than an allowed answer string. The model appears to misinterpret the final-answer prompt as a continuation of the reread loop, producing `{"need_reread": true}` or similar control tokens where an assignment answer is expected.

### 2.2 Schema Guard Design

Two functions were added to `src/evaluate_llm_endpoint.py`:

1. **`conflict_evidence_answer()`**: A deterministic extractor that, given the reread evidence for a conflict_update row, applies a priority rule to determine the allowed assignment:
   - If a reassignment note exists, use the later revision destination.
   - Otherwise, if an audit note exists, use the retained assignment.
   - Otherwise, use the visible dispatch assignment.

2. **`final_answer_from_text(..., conflict_fallback=True)`**: An extension of the existing final-answer extraction function. When `conflict_fallback=True` and the extracted text lacks an allowed answer (e.g., it contains only control JSON), the function delegates to `conflict_evidence_answer()` using the available reread evidence.

The hardened policy (`conflict_schema_hardened_policy`) retains the parent alias final-answer intervention unchanged and adds the conflict_update schema guard as a fallback layer. No modifications are made to the prompt, the model, or the alias-resolution extraction path.

### 2.3 Kill Condition

The branch was to be finalized as negative if the schema guard did not reduce the known conflict_update `need_reread` final-answer failures on the 200-example endpoint slice, or if it regressed alias_resolution accuracy.

## 3. Experimental Setup

### 3.1 Model and Serving

- **Model**: Qwen2.5-7B-Instruct, quantized to Q4_K_M (GGUF format).
- **Serving**: llama.cpp server launched from cached artifacts at `/tmp/utr_conflict_llama_server`, bound to `127.0.0.1:8088`.
- **Verification**: The `/v1/models` endpoint was confirmed responsive before calibration and main runs. The server was stopped after evaluation.

### 3.2 Dataset

- **Source**: `data/utr_synthetic_1500.jsonl`, containing 1,500 synthetic UTR examples.
- **Conflict-update subset**: 375 rows with conflict_update labels.
- **Evaluation slice**: 200 examples sampled with seed 344.

### 3.3 Calibration

A 40-example calibration slice (seed 344) was run under both the alias-only policy and the conflict-schema-hardened policy. Both achieved 1.000 accuracy on the calibration slice, confirming that the guard did not introduce obvious regressions on a small sample before committing to the full evaluation.

### 3.4 Evaluation Conditions

Three conditions were compared on the same 200-example slice:

| Condition | Description |
|---|---|
| **Parent alias baseline** | Copied parent alias intervention results on the same slice (no schema guard). |
| **Alias-only policy** | Current-run alias final-answer policy without the conflict schema guard. |
| **Conflict-schema-hardened policy** | Alias policy plus the `conflict_fallback=True` schema guard. |

### 3.5 Offline Verification

The `conflict_evidence_answer()` extractor was tested deterministically against all 375 conflict_update rows in the full dataset, without model inference, to verify that the extraction rule produces the correct gold answer in every case.

### 3.6 Resource Monitoring

System resource usage was sampled at 2-second intervals during the main evaluation run (189 samples collected). Metrics include GPU utilization, RSS, PSS, MemAvailable, and SwapFree. GPU memory was not used as available-memory evidence on the GB10 UMA architecture.

## 4. Results

### 4.1 Main Evaluation

| Metric | Parent Alias Baseline | Alias-Only Policy | Conflict-Schema-Hardened Policy |
|---|---|---|---|
| Overall accuracy | 0.970 | 0.995 | 1.000 |
| Cost-adjusted utility | 0.940 | 0.965 | 0.970 |
| Alias_resolution accuracy | 1.000 | 1.000 | 1.000 |
| Conflict_update accuracy | 0.880 | 0.980 | 1.000 |
| Exception_rule/table_lookup accuracy | — | — | 1.000 |

### 4.2 Deltas

- **Hardened vs. parent alias baseline**: +0.030 overall accuracy, +0.030 utility, +0.120 conflict_update accuracy.
- **Hardened vs. same-run alias-only policy**: +0.005 overall accuracy, +0.005 utility, +0.020 conflict_update accuracy.

The schema guard resolved 1 out of 200 examples that the alias-only policy failed on the current-run slice. Zero hardened failures were observed.

### 4.3 Offline Extractor Verification

`conflict_evidence_answer()` matched the gold answer for all 375 conflict_update rows in the full synthetic dataset under deterministic (non-inference) evaluation.

### 4.4 Resource Usage

| Metric | Value |
|---|---|
| Samples collected | 189 |
| Sampling interval | 2 s |
| Mean GPU utilization | 88.79% |
| GPU utilization p50 / p95 / max | 95% / 95% / 95% |
| Mean RSS | 1,228,685 KB |
| Mean PSS | 1,224,470 KB |
| Mean MemAvailable | 116,409,349 KB |
| SwapFree | 0 KB |

### 4.5 Compilation and Integrity Checks

`python3 -m py_compile` passed for all four source modules: `generate_dataset.py`, `evaluate_policies.py`, `evaluate_llm_endpoint.py`, and `monitor_resources.py`.

## 5. Limitations

1. **Single model and quantization.** All results are obtained from Qwen2.5-7B-Instruct Q4_K_M GGUF. Whether the same failure mode exists or the same guard is effective for other models, sizes, or quantization levels is unknown.

2. **Synthetic dataset.** The evaluation uses `data/utr_synthetic_1500.jsonl`, a synthetic dataset. Performance on real-world UTR data is not established.

3. **Small evaluation slice.** The main evaluation covers 200 examples (seed 344). The observed improvement—resolving 1 out of 200 failures—has wide confidence intervals. A binomial proportion of 1/200 failing under the alias-only policy has an approximate 95% confidence interval of [0.001, 0.055] for the true failure rate; the hardened policy's 0/200 has an interval of [0.000, 0.037]. The difference is not statistically distinguishable at conventional thresholds with this sample size.

4. **Deterministic fallback scope.** The schema guard is a deterministic extraction rule applied only when the model fails to produce an allowed answer. It does not improve the model's ability to produce correct answers on its own; it compensates for one specific failure mode. If the model's reread evidence is itself incorrect, the fallback will extract an incorrect assignment.

5. **No production validation.** These are llama.cpp hook-prototype results on a local endpoint, not production deployment measurements. Latency, throughput, and failure-mode distributions under production load are not characterized.

6. **No external replication.** Results have not been replicated by an independent party or on different hardware.

7. **Alias-resolution preservation, not improvement.** The schema guard was designed not to regress alias_resolution accuracy. It does not improve alias_resolution, which was already at 1.000 under the parent intervention.

## 6. Reproducibility Checklist

| Item | Status |
|---|---|
| Model identity specified (Qwen2.5-7B-Instruct Q4_K_M GGUF) | Yes |
| Quantization format specified | Yes |
| Serving software specified (llama.cpp) | Yes |
| Dataset file identified (`data/utr_synthetic_1500.jsonl`) | Yes |
| Evaluation slice size and seed documented (200, seed 344) | Yes |
| Calibration slice size and seed documented (40, seed 344) | Yes |
| Source code compilation verified (`py_compile`) | Yes |
| Result artifacts written to named files | Yes |
| Helper server stopped after evaluation | Yes |
| Random seed for sampling specified | Yes |
| Deterministic offline check performed (375/375 rows) | Yes |
| Resource monitoring methodology described | Yes |

## 7. Conclusion

A deterministic schema guard for conflict-update final-answer extraction eliminates the observed control-JSON emission failure mode on a 200-example evaluation slice served by Qwen2.5-7B-Instruct Q4_K_M via llama.cpp. The guard applies a priority extraction rule over reread evidence when the model's final output lacks an allowed answer, and it preserves alias_resolution accuracy at 1.000. The improvement over the alias-only policy on the current-run slice is modest in absolute terms (+0.005 overall accuracy, +0.020 conflict_update accuracy), reflecting the resolution of a single remaining failure out of 200 examples. The offline deterministic verification confirms that the extraction rule is correct for all 375 conflict_update rows in the full dataset, suggesting the guard is sound for the synthetic data distribution tested. Whether this intervention generalizes to other models, real-world data, or production deployment conditions remains an open question. The project decision recommends merging or carrying forward the conflict-update schema guard alongside the alias evidence-summary policy as the current best UTR reread final-answer stack, subject to the limitations enumerated above.

## Referenced Artifacts

### Source files
- `src/evaluate_llm_endpoint.py` — contains `conflict_evidence_answer()` and `final_answer_from_text(..., conflict_fallback=True)`
- `src/evaluate_policies.py`
- `src/generate_dataset.py`
- `src/monitor_resources.py`

### Data
- `data/utr_synthetic_1500.jsonl`

### Decision and metadata
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`

### Run documentation
- `run_notes.md`

### Result files
- `results/conflict_guard_vs_parent.json`
- `results/conflict_guard_schema_fixes.json`
- `results/conflict_guard_failures.json`
- `results/conflict_guard_resource_summary.json`
- `results/conflict_guard_predictions.jsonl`
- `results/conflict_guard_eval.json`
- `results/conflict_guard_resource_samples.csv`
- `results/conflict_guard_resource_monitor.log`
- `results/conflict_vs_parent.json`
- `results/conflict_hardening_failures.json`
- `results/conflict_resource_summary.json`
- `results/conflict_hardening_predictions.jsonl`
- `results/conflict_hardening_eval.json`
- `results/conflict_resource_samples.csv`
- `results/conflict_resource_monitor.log`
- `results/conflict_hardening_calibration_predictions.jsonl`
- `results/conflict_hardening_calibration.json`
- `results/parent_alias_resource_summary.json`
- `results/parent_alias_failures.json`
- `results/parent_alias_intervention_predictions.jsonl`

### Paper artifacts
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
