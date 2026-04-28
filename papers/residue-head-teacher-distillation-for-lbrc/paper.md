# Residue-Head Teacher Distillation for LBRC

> **AI Provenance Notice:** This draft was generated entirely by AI from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether a small language model (SmolLM) can be calibrated to emit correct digit predictions for the Long-Budget Residue Computation (LBRC) task via direct digit-logit distillation from a verified residue-head teacher. The residue-head teacher achieves perfect accuracy on all 343 (7³) digit combinations, but distilling its digit distribution into the LM via cross-entropy supervision on 1,000 examples for 140 gradient steps reduces held-out digit cross-entropy from 2.208 to 1.979 while remaining above the random baseline of ln(7) ≈ 1.946. The distillation gate (loss ≤ 1.90, accuracy ≥ 0.25) is not met. As a fallback, we evaluate a hard constrained decoder that overrides the LM's digit emission with the residue-head teacher's prediction. This mechanism achieves 1.0 accuracy on a balanced 64-example bounded LBRC evaluation, passing the long-context gate. The result is mixed: direct distillation moves loss in the correct direction but fails to calibrate the LM sufficiently for unconstrained deployment, while constrained decoding provides a viable engineering path at the cost of requiring the teacher at inference time.

## 1. Introduction

Structured computation tasks such as modular arithmetic and residue computation pose a challenge for autoregressive language models. Even when a compact, verifiable computational module (a "residue head") exists and achieves perfect accuracy on the target digit space, transferring that knowledge into a general-purpose LM through standard fine-tuning is not guaranteed to succeed.

This report examines a specific instance of this problem within the LBRC (Long-Budget Residue Computation) framework. A residue-head teacher—a small neural module that maps input digit triples to their correct residue digit in {0,…,6}—has been previously validated with perfect accuracy across all 7³ = 343 input combinations. The central question is whether this teacher's digit distribution can be distilled into a SmolLM checkpoint such that the LM independently emits correct digits without the teacher at inference time.

We report two experimental paths:

1. **Direct digit-logit distillation**, which supervises the LM's next-token digit logits against the residue-head teacher's targets.
2. **Hard constrained decoding**, which retains the LM for text generation but overrides digit tokens with the teacher's prediction.

The distillation experiment produces a partial but insufficient improvement. The constrained decoding experiment passes all evaluation gates trivially, as expected when the teacher is perfect. The overall finding is mixed: the distillation signal is real but too weak at the tested budget, while constrained decoding is effective but requires the teacher at inference time.

## 2. Method

### 2.1 Residue-Head Teacher

The residue-head teacher is a pre-trained neural module stored at `artifacts/digit_head_residue_gate.pt`. It maps triples of digits in {0,…,6} to a single residue digit in {0,…,6}. Before any distillation, the teacher is verified by probing all 7³ = 343 digit combinations and confirming that the cross-entropy loss is 0.001439 and accuracy is 1.0. This verification step is performed by `src/lbrc/train_residue_teacher_distill.py` at initialization.

### 2.2 Direct Digit-Logit Distillation

The distillation procedure (`src/lbrc/train_residue_teacher_distill.py`) operates on the exact downstream measurement surface: for each generated LBRC prompt, the script scores only the next-token digit logits over the vocabulary subset {0,…,6} and minimizes cross-entropy against the residue-head teacher's target digit. This is a targeted form of knowledge distillation that restricts supervision to the digit token position rather than the full token sequence.

**Base model.** The starting checkpoint is an inherited SmolLM model previously fine-tuned for retrieval-summary with a digit-gate head (`smol_retrieval_summary_sft_digitgate_2k_l80`).

**Training configuration.** 1,000 training examples, 140 update steps, maximum sequence length 256, batch size 16, learning rate 2×10⁻⁴. Training completed in 36.861 seconds at 3.798 steps/second and 15,388.6 tokens/second, with mean GPU utilization of 91.2% and peak RSS of 1,955.4 MB.

**Held-out evaluation.** Digit-gate evaluation is performed on 512 held-out generated rows not seen during training, measuring 7-way cross-entropy loss and classification accuracy over digits {0,…,6}.

**Branch kill condition.** The experiment is terminated if held-out digit cross-entropy cannot be reduced below the random 7-way baseline of ln(7) ≈ 1.946, or if accuracy cannot reach 0.25. The specific gate thresholds are loss ≤ 1.90 and accuracy ≥ 0.25.

### 2.3 Hard Constrained Decoding

As a fallback mechanism, `src/lbrc/evaluate_residue_constrained_decoder.py` implements a constrained decoder that retains the LM's digit logits for telemetry but hard-constrains the emitted digit token to the residue-head teacher's prediction. The LM generates all non-digit tokens normally; only the digit token is overridden.

**Evaluation configuration.** 64 balanced examples drawn from `artifacts/lbrc_digit_head_eval_examples.jsonl` with 16 examples per token-budget bucket, using the `retrieval_summary_answer_prefix` prompt format, maximum sequence length 256, and batch size 8.

## 3. Results

### 3.1 Direct Digit-Logit Distillation

| Metric | Before Distillation | After Distillation (140 steps) | After Distillation (80 steps) | Random Baseline | Gate Threshold |
|---|---|---|---|---|---|
| Held-out digit CE loss | 2.208 | 1.979 | 2.008 | 1.946 | ≤ 1.90 |
| Held-out digit accuracy | 0.146 | 0.150 | 0.137 | 0.143 | ≥ 0.25 |

The 140-step distillation run reduced held-out digit cross-entropy by 0.230 (from 2.208 to 1.979) and improved accuracy from 0.146 to 0.150. However, the loss remained above the random baseline of ln(7) ≈ 1.946, and accuracy remained near the random expectation of 1/7 ≈ 0.143. The gate thresholds (loss ≤ 1.90, accuracy ≥ 0.25) were not met.

A shorter 80-step pilot run also failed, producing a held-out loss of 2.008 and accuracy of 0.137. A longer uncapped 3-epoch training attempt was terminated around step 150 before metrics were written; the 140-step run is therefore the durable result.

### 3.2 Hard Constrained Decoding

| Metric | LM-Only | Hard Constrained Decoder |
|---|---|---|
| Accuracy | 0.1875 | 1.0 |
| Long-context gate | Failed (below 0.25 threshold) | Passed |

The hard constrained decoder achieved 1.0 accuracy across all token-budget buckets and positions on the 64-example balanced sample. Throughput was 86.791 samples/second with mean GPU utilization of 2.0% (inference-light workload). The LM-only accuracy on the same sample was 0.1875, which is below the 0.25 long-context gate threshold.

### 3.3 Summary of Findings

The results are mixed:

- **Distillation signal exists but is insufficient.** The 0.230 reduction in held-out cross-entropy confirms that the residue-head teacher's digit distribution provides a learnable signal to the LM. However, the LM's digit predictions remain effectively random after training at the tested budget.
- **Constrained decoding is trivially effective.** When the teacher's prediction is forced at the digit token position, accuracy is perfect by construction, since the teacher itself has verified perfect accuracy. This is an engineering result rather than a learning result.
- **The distillation gate was not met.** The experiment's own pre-specified success criterion (loss ≤ 1.90, accuracy ≥ 0.25) was not satisfied, meaning the distillation path does not authorize unconstrained long-context deployment.

## 4. Limitations

1. **Small model and small budget.** The experiments use a single SmolLM checkpoint and at most 1,000 training examples with 140 gradient steps. It is unknown whether larger models, more data, or longer training would close the gap between the distillation loss and the random baseline.

2. **Single random baseline comparison.** The comparison to ln(7) ≈ 1.946 assumes a uniform random distribution over 7 digits. The actual pre-distillation LM distribution may be non-uniform, which complicates the interpretation of the "near-random" post-distillation accuracy.

3. **Constrained decoding requires the teacher at inference time.** The hard constrained decoder is not a distillation result; it is a deployment architecture that requires the residue-head teacher to be available during inference. This adds latency and complexity compared to a fully self-contained LM.

4. **Bounded evaluation sample.** The constrained decoding evaluation uses 64 examples (16 per bucket). While balanced across token-budget buckets, this sample is small and may not be representative of the full LBRC evaluation distribution.

5. **Incomplete training curve.** The longer 3-epoch training run was killed before metrics were written, so the behavior of distillation beyond 140 steps at this data scale is uncharacterized.

6. **No external replication.** All results are from a single hardware environment and a single code execution. No external validation or cross-platform replication has been performed.

7. **Task specificity.** The residue-head teacher and LBRC task are narrow. Generalization of these findings to other structured computation tasks or broader LM capabilities is not established.

## 5. Reproducibility Checklist

- [x] **Code compilation verified.** All source files (`src/lbrc/train_residue_teacher_distill.py`, `src/lbrc/evaluate_residue_constrained_decoder.py`, `src/lbrc/evaluate_hf_lms.py`, `src/digit_head/evaluate_lbrc_gate.py`, `tests/test_evaluate_hf_lms.py`) pass `py_compile`.
- [x] **Unit tests executed.** `tests/test_evaluate_hf_lms.py` passed before experiments.
- [x] **Training script executed with fixed seed and bounded steps.** The 140-step run is the durable result; the 80-step pilot is also recorded.
- [x] **Evaluation script executed on held-out data.** 512 held-out rows for digit-gate evaluation; 64 balanced examples for constrained decoding.
- [x] **Teacher verification performed.** Residue-head teacher probed on all 343 digit combinations with loss 0.001439 and accuracy 1.0 before distillation.
- [x] **Metrics and checkpoints saved to artifacts.** All result files listed in the artifact manifest are present on disk.
- [x] **Branch kill condition pre-specified.** The gate thresholds (loss ≤ 1.90, accuracy ≥ 0.25) were defined before the experiment and were not met.
- [ ] **External replication.** Not performed.
- [ ] **Broader model/hardware coverage.** Only one model checkpoint and one GPU environment tested.

## 6. Conclusion

Direct residue-head teacher distillation into a SmolLM checkpoint produces a measurable but insufficient improvement in held-out digit prediction for the LBRC task. The 0.230 reduction in cross-entropy confirms a learnable signal, but the post-distillation model remains near-random (loss 1.979 vs. ln(7) ≈ 1.946; accuracy 0.150 vs. 0.143 expected by chance). The pre-specified distillation gate was not met.

The hard constrained decoding fallback achieves perfect accuracy by overriding the LM's digit emission with the verified residue-head teacher's prediction. This is an effective engineering mechanism but does not constitute learned calibration of the LM itself.

The project decision recommends productizing the constrained decoder as a hard digit mask/parser path and refraining from further unconstrained distillation at the same budget unless a held-out digit gate first beats the random baseline of ln(7). Whether larger models, more training data, or different distillation architectures can close the calibration gap remains an open question.

## Referenced Artifacts

### Source code
- `src/lbrc/train_residue_teacher_distill.py` — digit-logit distillation training script
- `src/lbrc/evaluate_residue_constrained_decoder.py` — constrained decoding evaluation script
- `src/lbrc/evaluate_hf_lms.py` — HF LM evaluation utilities
- `src/digit_head/evaluate_lbrc_gate.py` — LBRC gate evaluation
- `src/digit_head/__init__.py`
- `src/lbrc/__init__.py`
- `tests/test_evaluate_hf_lms.py` — unit tests

### Training and evaluation results
- `artifacts/smol_residue_teacher_digitlogit_1k_l140_train_metrics.json` — 140-step distillation training metrics
- `artifacts/smol_residue_teacher_digitlogit_1k_l80_train_metrics.json` — 80-step pilot training metrics
- `artifacts/residue_constrained_decoder_smol_l140_metrics.json` — constrained decoding evaluation metrics
- `artifacts/residue_constrained_decoder_smol_l140_records.jsonl` — constrained decoding per-record results
- `artifacts/residue_teacher_branch_summary.json` — branch summary

### Model checkpoints
- `artifacts/smol_residue_teacher_digitlogit_1k_l140/` (model.safetensors, config.json, tokenizer.json, tokenizer_config.json, chat_template.jinja, generation_config.json)
- `artifacts/smol_residue_teacher_digitlogit_1k_l80/` (model.safetensors, config.json, tokenizer.json, tokenizer_config.json, chat_template.jinja, generation_config.json)

### Training data
- `artifacts/smol_residue_teacher_digitlogit_1k_l140_train_examples.jsonl`
- `artifacts/smol_residue_teacher_digitlogit_1k_l80_train_examples.jsonl`
- `artifacts/smol_residue_teacher_digitlogit_1k_e3_train_examples.jsonl`
- `artifacts/lbrc_digit_head_eval_examples.jsonl`

### Decision and audit
- `.omx/project_decision.json` — project decision (finalize_positive, hypothesis: mixed)
- `.omx/metrics.json` — session metrics
- `run_notes.md` — execution log
- `papers/source-record-redacted/claim_ledger.json` — claim audit
- `papers/source-record-redacted/evidence_bundle.json` — evidence bundle
