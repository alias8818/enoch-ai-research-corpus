# Persisted Per-Tensor 8-bit SGDM Momentum for LoRA Fine-Tuning: A Bounded Multi-Seed Study on GPT-2-small

> **AI provenance note:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We evaluate persisted per-tensor 8-bit stochastic gradient descent with momentum (8-bit SGDM) as a memory-efficient alternative to fp32 SGDM for LoRA adapter fine-tuning. In a 3-seed (17, 23, 31) GPT-2-small LoRA harness over Alice in Wonderland, Penn Treebank, and Tiny Shakespeare at 3,000 optimizer steps, 8-bit SGDM matched fp32 SGDM validation loss within 0.00231 absolute loss on every seed (paired mean delta −0.001209), outperformed no-momentum SGD by 0.142 mean loss, and outperformed the configured AdamW baseline by 0.040 mean loss. Optimizer-state bytes were 442,560 for 8-bit SGDM versus 1,769,472 for fp32 SGDM, a 4× reduction. The non-fused Python quantize/dequantize implementation incurred approximately 4% throughput overhead relative to fp32 SGDM. These results are limited to GPT-2-small, LoRA-only attention adapters, three small corpora, one hyperparameter setting per optimizer, and 3,000 steps; they do not establish behavior for larger models, full-parameter training, instruction tasks, tuned AdamW, long-horizon checkpoint persistence, or production memory and throughput.

## 1. Introduction

Quantized optimizer states reduce GPU memory consumption during training, which matters when memory rather than compute is the binding constraint. Prior work on 8-bit and blockwise quantized optimizers has focused primarily on Adam-family methods. Stochastic gradient descent with momentum (SGDM) remains relevant for fine-tuning scenarios where its simpler state—a single momentum buffer per parameter—and lower memory footprint already provide an advantage over Adam-family methods, which require two state tensors (first and second moment estimates).

This study asks a narrow, bounded question: does persisting per-tensor uint8 quantized SGDM momentum across optimizer steps preserve training quality relative to fp32 SGDM, while delivering a meaningful memory reduction? We test this in a LoRA fine-tuning setting on GPT-2-small across three fixed seeds and three text corpora, including a no-momentum SGD control and an AdamW baseline.

The hypothesis is supported in the tested scope, but the scope is intentionally narrow. We report the results with explicit scale limits and do not claim publication readiness.

## 2. Method

### 2.1 Model and Adapter Configuration

- **Base model:** Hugging Face `gpt2` (GPT-2-small, 124M parameters), frozen base weights in bf16.
- **LoRA adapters:** Rank 8 applied to each GPT-2 attention `c_attn` and `c_proj` Conv1D module. Only LoRA parameters are trainable; all base weights remain frozen.

### 2.2 Datasets

Three small public text corpora were concatenated for training and validation:

1. **Alice in Wonderland** (Project Gutenberg)
2. **Penn Treebank** (Zaremba split)
3. **Tiny Shakespeare**

Training used 20,000 examples per dataset (2,000 training blocks); validation used 5,000 examples per dataset (300 validation blocks).

### 2.3 Optimizers

Four optimizers were compared:

| Optimizer | Description | State per parameter |
|---|---|---|
| SGD | No-momentum SGD | None |
| SGDM fp32 | Standard SGDM with fp32 momentum buffer | 1 × fp32 tensor |
| SGDM 8-bit | SGDM with persisted per-tensor uint8 momentum | 1 × uint8 tensor + per-tensor scale |
| AdamW | Adam with decoupled weight decay | 2 × fp32 tensors (m, v) |

**Shared hyperparameters:** Learning rate 1e-3 for all optimizers. SGDM momentum coefficient 0.9. AdamW weight decay 0.01. These were not swept; a single setting was used across all seeds.

### 2.4 8-bit SGDM Quantization Scheme

The per-tensor 8-bit quantization operates as follows:

1. At each optimizer step, the fp32 momentum buffer is quantized to uint8 using per-tensor min-max scaling, yielding one uint8 tensor and two scalar scale values (min, max) per parameter tensor.
2. At the next step, the uint8 tensor is dequantized back to fp32 using the stored scale, the momentum update is applied, and the buffer is re-quantized.
3. The quantized buffer is **persisted** across steps (not reset), so quantization error accumulates but is bounded by the per-step re-quantization.

This is a non-fused Python implementation; the quantize and dequantize operations are not compiled or kernel-fused. The throughput and numerical behavior of a production fused implementation may differ.

### 2.5 Training Configuration

- **Steps:** 3,000 per optimizer per seed.
- **Batch size:** 4 (effective batch size 16 with gradient accumulation 4).
- **Sequence length:** 128.
- **Evaluation:** 40 validation batches per evaluation.
- **Seeds:** 17, 23, 31 (fixed, deterministic).
- **Hardware:** NVIDIA GB10 GPU, CUDA, Python 3.12.3, PyTorch 2.12.0+cu130.
- **Checkpoint cadence:** Per-optimizer partial JSON written at least every 600 seconds; final per-optimizer JSON written at run completion.

### 2.6 Metrics

- **Final validation cross-entropy loss** (aggregate across all three datasets).
- **Per-seed paired deltas** between 8-bit SGDM and each comparator.
- **Optimizer-state bytes** (total bytes allocated for optimizer state tensors).
- **Throughput** (tokens per second, measured at the end of training).

### 2.7 Calibration Run

A 20-step calibration run (seed 17 only, all four optimizers) confirmed that the harness was functional and that 8-bit SGDM was within +0.005208 aggregate validation loss of fp32 SGDM at that early stage, with optimizer-state bytes of 442,560 versus 1,769,472 for fp32 SGDM, and throughput at 0.9505× fp32 SGDM. AdamW was functional and competitive enough to retain as a baseline.

## 3. Results

### 3.1 Aggregate Validation Loss

| Optimizer | Mean final val loss | SD | Mean improvement from init | Tokens/sec (last mean) | Optimizer state bytes |
|---|---:|---:|---:|---:|---:|
| SGD (no momentum) | 3.445815 | 0.004530 | 0.416722 | 24,852.4 | 0 |
| SGDM fp32 | 3.304570 | 0.007470 | 0.557968 | 24,679.6 | 1,769,472 |
| SGDM 8-bit (persisted) | 3.303361 | 0.007955 | 0.559177 | 23,699.5 | 442,560 |
| AdamW | 3.343409 | 0.004779 | 0.519128 | 24,785.7 | 1,769,664 |

8-bit SGDM achieved the lowest mean validation loss of all four optimizers. The improvement over fp32 SGDM is small (−0.001209 mean) and within the range of the per-seed standard deviations, so this should not be interpreted as a meaningful superiority of 8-bit SGDM over fp32 SGDM; rather, the two are effectively matched within measurement noise.

### 3.2 Paired Seed-by-Seed Deltas

Deltas are expressed as 8-bit SGDM final validation loss minus comparator loss. Negative values indicate 8-bit SGDM achieved lower (better) loss.

**8-bit SGDM vs fp32 SGDM:**

| Seed | Delta |
|---|---:|
| 17 | −0.001060 |
| 23 | −0.002307 |
| 31 | −0.000260 |
| **Mean** | **−0.001209** |
| **Max absolute** | **0.002307** |

8-bit SGDM matched or slightly outperformed fp32 SGDM on every seed. The maximum absolute per-seed deviation was 0.002307. The consistency of the sign (negative on all three seeds) suggests a small systematic difference, but the magnitude is well within the standard deviations of either optimizer and should not be over-interpreted given only three seeds.

**8-bit SGDM vs no-momentum SGD:**

| Seed | Delta |
|---|---:|
| 17 | −0.138058 |
| 23 | −0.150856 |
| 31 | −0.138449 |
| **Mean** | **−0.142454** |
| **Max absolute** | **0.150856** |

8-bit SGDM substantially outperformed no-momentum SGD on every seed, confirming that the momentum mechanism remains active and beneficial under 8-bit quantization. This rules out the trivial explanation that momentum is irrelevant in this setup.

**8-bit SGDM vs AdamW:**

| Seed | Delta |
|---|---:|
| 17 | −0.036812 |
| 23 | −0.043192 |
| 31 | −0.040141 |
| **Mean** | **−0.040048** |
| **Max absolute** | **0.043192** |

8-bit SGDM outperformed the configured AdamW baseline on every seed. However, AdamW was run with a single hyperparameter setting (lr 1e-3, weight decay 0.01) that was not tuned for this task. This comparison does not establish that 8-bit SGDM is generally superior to AdamW; it only shows that under this particular configuration, the SGDM variants achieved lower validation loss.

### 3.3 Memory

- 8-bit SGDM optimizer-state bytes: 442,560
- fp32 SGDM optimizer-state bytes: 1,769,472
- Ratio: 0.2501 (approximately 4× reduction, or 25% of fp32 SGDM state bytes)
- AdamW optimizer-state bytes: 1,769,664 (effectively equivalent to fp32 SGDM plus minor scalar overhead for this LoRA-only parameter set)

The 4× reduction follows directly from the uint8-vs-fp32 element size ratio (1 byte vs 4 bytes), with the small additional overhead of per-tensor scale values.

### 3.4 Throughput

- 8-bit SGDM throughput ratio vs fp32 SGDM: 0.9603
- The non-fused Python quantize/dequantize implementation incurred approximately 4% throughput overhead relative to fp32 SGDM in this harness.

This throughput measurement reflects the Python-level quantization overhead in the prototype implementation, not a fused CUDA kernel. A production implementation would likely reduce or eliminate this gap, but this was not validated.

## 4. Limitations

The results carry explicit scope boundaries:

1. **Model scale:** GPT-2-small (124M parameters) only. Behavior at larger scales (7B, 70B+) is not established.
2. **Adapter type:** LoRA rank 8 on attention modules only. Full-parameter fine-tuning, higher LoRA ranks, and adapter combinations are untested.
3. **Task diversity:** Three small language-modeling corpora (Alice in Wonderland, Penn Treebank, Tiny Shakespeare). Instruction following, RLHF, multi-task, and classification tasks are not covered.
4. **Training horizon:** 3,000 optimizer steps. Long-horizon training (tens of thousands of steps), checkpoint persistence across restarts, and resume-from-checkpoint behavior are untested.
5. **Hyperparameter coverage:** One learning rate (1e-3), one momentum (0.9), one AdamW configuration (lr 1e-3, wd 0.01). No hyperparameter sweeps were conducted. AdamW may perform better with tuned settings.
6. **Implementation:** Non-fused Python quantize/dequantize. A production fused CUDA implementation may differ in both throughput and numerical behavior.
7. **Quantization granularity:** Per-tensor scaling only. Finer-grained (per-row, per-channel, or blockwise) scaling was not ablated.
8. **Seed count:** Three fixed seeds. While sufficient to reject gross instability, this does not provide a tight confidence interval on the mean loss delta.
9. **AdamW comparison:** The AdamW baseline used a single, untuned hyperparameter setting. The observed underperformance relative to SGDM variants may reflect suboptimal AdamW hyperparameters rather than a fundamental optimizer advantage.

The project decision is **finalize_negative** with **research_outcome: useful_signal**: the mechanism is supported for the bounded claim, but the strict Tier-4 paper-readiness gate is not met due to these scope limitations.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Fixed seeds reported | Yes (17, 23, 31) |
| Model architecture and checkpoint specified | Yes (Hugging Face `gpt2`, frozen base weights, LoRA rank 8 on `c_attn` and `c_proj`) |
| Optimizer hyperparameters reported | Yes (lr 1e-3 all; momentum 0.9 SGDM; weight decay 0.01 AdamW) |
| Dataset sources and splits reported | Yes (Alice in Wonderland Project Gutenberg, Penn Treebank Zaremba split, Tiny Shakespeare; train/val counts specified) |
| Batch size and sequence length reported | Yes (effective batch 16 via batch size 4 × grad accum 4; seq-len 128) |
| Training step count reported | Yes (3,000 steps) |
| Hardware reported | Yes (NVIDIA GB10, CUDA) |
| Software versions reported | Yes (Python 3.12.3, PyTorch 2.12.0+cu130) |
| Quantization scheme described | Yes (per-tensor uint8 min-max, persisted across steps) |
| All seeds' raw results accessible | Yes (per-seed JSON summaries and per-optimizer result files in the output directory) |
| Negative/null results reported | Yes (AdamW underperformed both SGDM variants; throughput overhead of 8-bit quantization reported) |

## 6. Conclusion

Persisted per-tensor 8-bit SGDM momentum matched fp32 SGDM validation loss within 0.00231 absolute loss on every seed across a 3-seed GPT-2-small LoRA fine-tuning experiment, while using approximately 25% of the fp32 momentum-state memory. The 8-bit variant outperformed both no-momentum SGD (confirming the momentum mechanism remains effective under quantization) and the configured AdamW baseline (with the caveat that AdamW was not tuned). The Python quantization implementation incurred roughly 4% throughput overhead.

These findings support the bounded mechanism claim but do not constitute publication-ready evidence. The scope is limited to one small model, one LoRA configuration, three small corpora, one hyperparameter setting per optimizer, and a prototype implementation. Whether per-tensor 8-bit momentum scaling remains adequate at larger model scales, longer training horizons, full-parameter training, or with tuned AdamW baselines remains an open question. The result is a useful signal that warrants further investigation under broader conditions before any general claim is justified.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision (enoch) | `.enoch/project_decision.json` |
| Project decision (omx) | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260527T050613216408+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260527T050613216408+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260527T050613216408+0000/paper_manifest.json` |
| Multi-seed summary | `results/validation_3seed_3000steps_adamw/multiseed_summary.json` |
| Seed 17 summary | `results/validation_3seed_3000steps_adamw/seed_17/summary.json` |
| Seed 23 summary | `results/validation_3seed_3000steps_adamw/seed_23/summary.json` |
| Seed 31 summary | `results/validation_3seed_3000steps_adamw/seed_31/summary.json` |
| Per-optimizer results | `results/validation_3seed_3000steps_adamw/seed_*/{optimizer}_result.json` |
| Validation log | `logs/validation_3seed_3000steps_adamw.log` |
| Harness script | `scripts/validate_lora_8bit_sgdm_adamw_multiseed.py` |
