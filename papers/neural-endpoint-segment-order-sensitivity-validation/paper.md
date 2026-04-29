# Neural Endpoint Segment Order Sensitivity Validation

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate whether the order of fixed-content evidence segments within a prompt affects the evidence-selection accuracy of a locally served neural language model endpoint. Using a synthetic fixed-content segment permutation dataset, we evaluate two llama.cpp OpenAI-compatible serving configurations of Phi-4-mini-instruct (Q4_K_M GGUF): one with full CPU offload and one with full CUDA offload. Across 50 permutation bases (200 evaluation examples per configuration), both configurations achieve perfect accuracy on canonical-order prompts (1.000) and slightly reduced accuracy on permuted-order prompts (0.980), yielding a canonical-versus-permuted delta of +0.020. All observed failures consist of unparseable or empty segment-number responses occurring exclusively on permuted rows where the target segment remained in position 0; no failures appeared when the target evidence was displaced to later positions. These results provide weak evidence of segment-order sensitivity at the neural endpoint level. However, because both configurations share the same model weights and differ only in inference hardware path, the external validity of this signal is limited. We report the findings with medium confidence and moderate evidence strength, and recommend replication with distinct model families and serving stacks before drawing stronger conclusions.

---

## 1. Introduction

Large language models accessed through OpenAI-compatible endpoints are increasingly used as reasoning components in retrieval-augmented and evidence-grounded systems. A known concern in such systems is prompt-order sensitivity: the tendency of models to attend disproportionately to evidence appearing in certain positional slots within the prompt. Prior work has documented positional bias in various model families and prompt structures, but the question of whether this sensitivity manifests consistently across different serving configurations of the same model weights—specifically, CPU-only versus GPU-accelerated inference paths—has received less attention.

This study tests whether permuting the order of fixed-content evidence segments in a structured prompt measurably affects the evidence-selection accuracy of a locally served neural endpoint. We use a synthetic dataset where the factual content of each segment is held constant across permutations, isolating the effect of segment position from content variation. Two serving configurations of the same model are evaluated to probe whether the inference hardware path modulates any observed order sensitivity.

The central hypothesis is that permuted segment order will produce a measurable accuracy decrement relative to canonical order. The recorded project decision is `finalize_positive` with hypothesis status `supported`, but confidence is rated `medium` and evidence strength `moderate`, reflecting the limited diversity of the tested configurations.

---

## 2. Method

### 2.1 Dataset

The evaluation uses a fixed-content segment permutation dataset (`data/segment_order_sensitivity_synthetic.jsonl`), derived from a parent project's synthetic benchmark. Each example in the dataset presents multiple evidence segments containing entity–decision records. A subset of segments contain verified (correct) records for a queried entity, while others contain unverified or conflicting records. The dataset includes both canonical-order presentations (where the verified record appears in a consistent position) and permuted presentations (where segment positions are shuffled while content is preserved). A spot-check subset of 50 examples is also retained (`data/spot_check_50.jsonl`).

### 2.2 Serving Configurations

Two llama.cpp OpenAI-compatible server configurations were provisioned from a single cached GGUF model file:

| Configuration identifier | GPU layers | Context length | Port |
|---|---|---|---|
| `llama_cpp_phi4_cpu_layers0_ctx4096` | 0 (full CPU offload) | 4096 | 18110 |
| `llama_cpp_phi4_cuda_all_layers_ctx4096` | 999 (full CUDA offload) | 4096 | 18111 |

Both configurations serve the same model: `Phi-4-mini-instruct-Q4_K_M.gguf` from the `lmstudio-community` GGUF cache. The llama.cpp server binary was located at `llama-server`. Each configuration was launched from `/tmp`, verified through both the `/v1/models` and `/v1/chat/completions` endpoints, evaluated sequentially, and stopped before yielding control. No helper server process persisted after evaluation.

### 2.3 Evaluation Harness

The evaluation script (`scripts/neural_endpoint_segment_order_eval.py`) was designed to work around the observed brittleness of direct answer-code generation for the Phi-4-mini GGUF on the synthetic code format. Rather than asking the model to produce the final answer code directly, the harness prompts the model to return the segment number containing the verified record for the requested entity/decision. The returned segment number is then mapped back to the existing answer-code target from the parent dataset.

This indirect evaluation strategy preserves the same segment-order permutation set while testing the neural endpoint's evidence-selection behavior under changing segment order. The harness was run with `--max-bases 50`, producing 400 total prediction rows (200 per configuration) plus associated metrics and report artifacts.

### 2.4 Metrics

The primary metric is accuracy: the proportion of examples for which the model's selected segment number correctly identifies the segment containing the verified record. Accuracy is computed separately for canonical-order and permuted-order examples within each configuration. The canonical-versus-permuted delta (canonical accuracy minus permuted accuracy) quantifies order sensitivity.

---

## 3. Results

### 3.1 Accuracy by Configuration and Order Condition

| Configuration | Canonical accuracy | Permuted accuracy | Delta |
|---|---|---|---|
| CPU-offload (`llama_cpp_phi4_cpu_layers0_ctx4096`) | 1.000 | 0.980 | +0.020 |
| CUDA-offload (`llama_cpp_phi4_cuda_all_layers_ctx4096`) | 1.000 | 0.980 | +0.020 |

Both configurations achieve identical accuracy profiles: perfect accuracy on canonical-order prompts and a 2-percentage-point decrement on permuted-order prompts. The delta of +0.020 is consistent across the CPU-only and CUDA-offload inference paths.

### 3.2 Failure Mode Analysis

All observed failures were unparseable or empty segment-number responses. Critically, these failures occurred exclusively on permuted rows where the target segment remained in position 0 (i.e., the first segment in the prompt). No failures appeared when the target evidence was displaced to a later position in the prompt.

This failure pattern is counterintuitive under a simple recency-bias model: one might expect position-0 targets to be the easiest to identify. The observed failures instead suggest that permutation of surrounding segments may disrupt the model's parsing of the structured prompt even when the target segment itself has not moved, leading to format-breaking outputs rather than incorrect segment selections.

### 3.3 Configuration Equivalence

The CPU-offload and CUDA-offload configurations produced identical accuracy values and identical failure modes. This is expected given that both configurations serve the same model weights with the same quantization; the only difference is the computational backend for inference. The absence of any accuracy divergence between configurations suggests that the observed order sensitivity is a property of the model's token-level processing rather than an artifact of floating-point differences between CPU and CUDA execution paths, though this cannot be conclusively determined from two configurations alone.

---

## 4. Limitations

1. **Single model family.** Both serving configurations use the same Phi-4-mini-instruct Q4_K_M GGUF weights. The two configurations differ only in inference hardware path (CPU vs. CUDA), not in model architecture, training, or quantization. This severely limits the external validity of the findings. A stronger study would evaluate at least one additional model family or serving stack.

2. **Small evaluation sample.** The evaluation covers 50 permutation bases with 200 examples per configuration. While sufficient to detect the observed 2-percentage-point delta, the sample is too small to characterize the failure mode distribution with high precision or to detect smaller effects.

3. **Synthetic dataset.** The fixed-content permutation dataset is synthetic and may not reflect the distributional properties of naturally occurring evidence-grounded prompts. Real-world retrieval-augmented generation tasks may exhibit different order-sensitivity profiles.

4. **Indirect evaluation proxy.** Because direct answer-code generation was brittle for this model on the synthetic format, the evaluation uses segment-number selection as a proxy for evidence identification. This proxy may not capture all aspects of order sensitivity relevant to downstream task performance.

5. **Identical delta across configurations.** The identical +0.020 delta across both configurations, while consistent, provides no evidence that the effect generalizes beyond this specific model–quantization combination. The two configurations are not independent tests of the hypothesis in a meaningful sense.

6. **Failure mode ambiguity.** The observed failures (unparseable responses on permuted prompts with position-0 targets) may reflect prompt-format sensitivity rather than evidence-order sensitivity per se. Distinguishing these mechanisms would require additional controlled experiments.

7. **No statistical significance testing.** The results are reported as raw accuracy values without confidence intervals or hypothesis tests. Given the small sample, the observed delta should be interpreted cautiously.

8. **No cross-model replication.** The project decision explicitly recommends reopening only for a materially stronger cross-model endpoint study using a distinct cached model family or server stack. This study does not provide such replication.

---

## 5. Reproducibility Checklist

| Item | Status | Detail |
|---|---|---|
| Model identifier specified | Yes | `lmstudio-community/Phi-4-mini-instruct-GGUF/Phi-4-mini-instruct-Q4_K_M.gguf` |
| Quantization specified | Yes | Q4_K_M |
| Serving binary specified | Yes | `llama-server` |
| Server launch parameters recorded | Yes | `--n-gpu-layers` (0 or 999), context 4096, ports 18110/18111 |
| Dataset file identified | Yes | `data/segment_order_sensitivity_synthetic.jsonl` |
| Evaluation script identified | Yes | `scripts/neural_endpoint_segment_order_eval.py` |
| Script compiles cleanly | Yes | `python3 -m py_compile` passed |
| Raw predictions saved | Yes | Two JSONL files (400 rows total) |
| Metrics artifact saved | Yes | `results/neural_endpoint_segment_order_metrics.json` |
| Report artifact saved | Yes | `results/neural_endpoint_segment_order_report.md` |
| Helper processes cleaned up | Yes | `pgrep` confirmed no lingering llama-server |
| Endpoint verification performed | Yes | Both `/v1/models` and `/v1/chat/completions` verified for each configuration |
| Random seed documented | No | Not recorded in available artifacts |
| Hardware environment documented | Partial | DGX system inferred from port-probe results; full specs not in artifacts |
| Statistical tests performed | No | Not performed; only raw accuracy reported |

---

## 6. Conclusion

This study provides weak evidence that permuting the order of fixed-content evidence segments in a structured prompt reduces the evidence-selection accuracy of a locally served Phi-4-mini-instruct endpoint, with a canonical-versus-permuted accuracy delta of +0.020 observed across two serving configurations. The failure mode—unparseable responses on permuted prompts where the target remains in position 0—suggests that segment permutation may disrupt prompt parsing rather than simply biasing evidence selection toward certain positions.

The external validity of these findings is limited by the use of a single model family, a single quantization, and a synthetic dataset. The two serving configurations tested are not independent replications, as they share identical model weights. The project decision of `finalize_positive` with `medium` confidence and `moderate` evidence strength reflects these constraints.

The recommended next step is replication with a distinct model family and serving stack. Until such replication is performed, the observed +0.020 delta should be treated as a preliminary signal rather than an established effect.

---

## Referenced Artifacts

### Result files
- `results/neural_endpoint_segment_order_report.md`
- `results/neural_endpoint_segment_order_metrics.json`
- `results/neural_endpoint_predictions_llama_cpp_phi4_cpu_layers0_ctx4096.jsonl`
- `results/neural_endpoint_predictions_llama_cpp_phi4_cuda_all_layers_ctx4096.jsonl`

### Source and data files
- `scripts/neural_endpoint_segment_order_eval.py`
- `data/segment_order_sensitivity_synthetic.jsonl`
- `data/spot_check_50.jsonl`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `run_notes.md`

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/README.md`
