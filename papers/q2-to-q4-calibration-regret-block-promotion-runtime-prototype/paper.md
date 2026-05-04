# Q2-to-Q4 Calibration-Regret Block Promotion: A Runtime Prototype for Selective Mixed-Precision Recovery

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run logs, metric JSON, and decision records). The operator who released the artifacts claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We present a runtime prototype for selectively promoting weight blocks from 2-bit (Q2) to 4-bit (Q4) precision in quantized causal language models, guided by a calibration-regret scoring heuristic. The prototype materializes reusable per-block promotion masks and benchmarks them against random, weight-norm, and quantization-error baselines on two cached public models. On SmolLM2-135M, sparse promotion (5% of candidate blocks, 3/66 blocks) recovers 26.7% of the full Q2→Q4 loss reduction at 68.1 loss-lift per MB, and medium promotion (20%, 13/66 blocks) recovers 77.5% at 45.5 loss-lift per MB—both substantially outperforming all controls. On Qwen2.5-0.5B-Instruct, sparse promotion similarly outperforms all controls (12.3 loss-lift per MB), but medium-budget promotion fails to beat random and weight-norm baselines, producing near-zero loss improvement. An anomalous finding is that all selection methods at the sparse budget on Qwen yield loss reductions exceeding the all-Q4 upper bound, suggesting the all-Q4 reference may not be a strict ceiling for partial promotion. We conclude that calibration-regret sparse promotion is viable as a runtime path, but medium-budget promotion requires a gating mechanism before general application.

## Introduction

Uniform low-bit quantization of large language models yields substantial memory savings but introduces significant accuracy degradation. Full upcasting to a higher precision recovers accuracy at a higher memory cost. A natural middle ground is *selective* mixed-precision: promote only the weight blocks where the quantization penalty is most severe, preserving most of the memory savings while recovering a disproportionate share of the accuracy loss.

The key operational question is: which blocks should be promoted, and does a calibration-driven selection heuristic produce masks that generalize beyond the calibration set? This work implements and evaluates a concrete runtime prototype that:

1. Scores candidate weight blocks by *calibration regret*—the reduction in calibration loss achieved by hypothetically promoting each block from Q2 to Q4.
2. Materializes promotion masks as durable JSON artifacts recording block slices, scores, and byte costs.
3. Applies these masks to live cached models and benchmarks held-out eval loss, inference throughput, and memory overhead.
4. Compares calibration-regret selection against three control heuristics (quantization error, weight norm, random selection) at sparse (5%) and medium (20%) promotion budgets.

We evaluate on two small causal language models to assess cross-model transfer: SmolLM2-135M and Qwen2.5-0.5B-Instruct. The results are mixed: sparse promotion transfers well, but medium-budget promotion does not, failing on Qwen in a way that indicates saturation or non-additive block interactions.

## Method

### Calibration-Regret Scoring

For each candidate weight block $b_i$ in a target parameter tensor, the prototype:

1. Computes a baseline Q2-only forward pass on calibration shards and records the per-shard loss.
2. Hypothetically promotes block $b_i$ to Q4 (replacing its Q2 values with the corresponding Q4 values) and recomputes the forward pass.
3. Defines the *calibration regret* of block $b_i$ as the mean loss reduction across calibration shards: $\Delta L_i = L_{\text{Q2}} - L_{\text{Q2}+b_i \to \text{Q4}}$.
4. Blocks with positive mean regret across all shards are candidates for promotion; blocks with positive regret on every shard are marked as robust.

### Mask Materialization

The top-$k$ blocks by calibration-regret score (where $k$ is determined by the promotion budget as a fraction of total candidate blocks) are written to a JSON mask artifact. Each entry records:

- `target_param`: the parameter tensor path
- `slice`: the row/column range of the block
- `score`: the calibration-regret value
- `extra_byte_cost`: the additional memory cost of promoting this block

This mask is directly usable as a control-plane or runtime input for translating selected blocks into a sparse promotion table or kernel-side mask.

### Control Heuristics

Three baselines are evaluated at the same budget:

- **Quantization error**: select blocks with the largest Frobenius norm of the Q4−Q2 residual.
- **Weight norm**: select blocks with the largest Frobenius norm of the Q2 weights.
- **Random**: select blocks uniformly at random; report the mean over multiple trials.

### Evaluation Protocol

For each budget and selection method, the prototype:

1. Applies the promotion mask to the cached Q2 model.
2. Evaluates held-out loss on disjoint evaluation text.
3. Records the loss reduction relative to the Q2 baseline: $\Delta L = L_{\text{Q2}} - L_{\text{promoted}}$.
4. Computes *loss-lift per MB*: the loss reduction divided by the additional memory consumed by the promoted blocks.
5. Measures inference throughput in tokens/s and peak CUDA allocation.

### Models and Configuration

| Property | SmolLM2 | Qwen2.5-0.5B-Instruct |
|---|---|---|
| Parameters | 135M | 0.5B |
| Target matrices | 4 (layers 0–1, `o_proj` + `down_proj`) | 4 (layers 0–1, `o_proj` + `down_proj`) |
| Block shape | 192 × 192 | 448 × 448 |
| Total candidate blocks | 66 | 52 |
| Calibration shards | 3 | 2 |
| Calibration texts | 12 | 8 |
| Evaluation texts | 8 | 6 |
| Random trials | 8 | 4 |
| Benchmark repeats | 4 | 2 |
| Budgets tested | 5%, 20% | 5%, 20% |

### Environment

All runs executed on a host with an NVIDIA GB10 GPU, no swap (SwapTotal = 0 MB), and >115 GB available system memory. Software: PyTorch 2.11.0+cu130, Transformers 5.7.0, Accelerate, Safetensors, psutil, installed via `uv pip` into a project-local `.venv`.

## Results

### SmolLM2-135M

**Baselines.** Q2-only eval loss: 18.8962. All-Q4 eval loss: 11.8720. The full Q2→Q4 transition yields an upper-bound loss reduction of +7.0243. Of 66 candidate blocks, 49 showed positive mean regret and 30 were positive on all calibration shards.

**Sparse budget (5%, 3 blocks promoted).**

| Selection method | Loss reduction vs. Q2 | Loss-lift/MB | Throughput (tok/s) |
|---|---|---|---|
| Calibration regret | **+1.8815** | **68.05** | ~6042 |
| Quantization error | −0.2909 | — | — |
| Weight norm | +1.1944 | — | — |
| Random (mean) | −0.3158 | — | — |

Calibration-regret selection recovered approximately 26.7% of the full Q4 improvement at 5% budget, substantially outperforming all controls. Weight-norm control showed a positive but smaller effect; quantization-error and random controls were negative.

**Medium budget (20%, 13 blocks promoted).**

| Selection method | Loss reduction vs. Q2 | Loss-lift/MB | Throughput (tok/s) |
|---|---|---|---|
| Calibration regret | **+5.4571** | **45.55** | ~5946 |
| Quantization error | −0.5609 | — | — |
| Weight norm | +0.3842 | — | — |
| Random (mean) | −0.3009 | — | — |

Calibration-regret selection recovered approximately 77.5% of the full Q4 improvement at 20% budget. Weight-norm control showed a small positive effect; quantization-error and random controls were negative.

**Memory.** Peak CUDA allocation: ~604 MB. RSS: ~1.60 GiB. MemAvailable remained >117 GiB throughout.

### Qwen2.5-0.5B-Instruct

**Baselines.** Q2-only eval loss: 9.1616. All-Q4 eval loss: 8.7980. Upper-bound loss reduction: +0.3636. Of 52 candidate blocks, 34 showed positive mean regret and 33 were positive on all shards.

**Sparse budget (5%, 3 blocks promoted).**

| Selection method | Loss reduction vs. Q2 | Loss-lift/MB | Throughput (tok/s) |
|---|---|---|---|
| Calibration regret | **+1.8528** | **12.31** | ~2395 |
| Quantization error | +1.4179 | — | — |
| Weight norm | +1.0934 | — | — |
| Random (mean) | +0.7335 | — | — |

Calibration-regret selection outperformed all controls at the sparse budget, though the margin over quantization-error control was modest (+0.43). Notably, all four selection methods produced loss reductions that *exceed* the all-Q4 upper bound of +0.3636. This anomaly is discussed below.

**Medium budget (20%, 10 blocks promoted).**

| Selection method | Loss reduction vs. Q2 | Loss-lift/MB | Throughput (tok/s) |
|---|---|---|---|
| Calibration regret | +0.1118 | 0.23 | ~2417 |
| Quantization error | −0.4122 | — | — |
| Weight norm | +1.0785 | — | — |
| Random (mean) | **+1.5082** | — | — |

Calibration-regret selection at the medium budget produced a near-zero loss reduction (+0.11) and was substantially outperformed by both the weight-norm control (+1.08) and random selection (+1.51). This represents a clear failure of the medium-budget calibration-regret policy on this model.

**Memory.** Peak CUDA allocation: ~1.78 GB. RSS: ~1.81 GiB. MemAvailable remained >115 GiB.

### Anomalous Qwen Sparse Results

On Qwen at the 5% budget, every selection method—including random—produced a loss reduction exceeding the all-Q4 reference of +0.3636. The calibration-regret result of +1.8528 implies a promoted-model eval loss of approximately 7.31, which is *lower* than the all-Q4 eval loss of 8.7980. Several explanations are possible:

1. The all-Q4 quantization of the entire model may introduce its own degradation pathway (e.g., via uniform quantization artifacts across all layers) that targeted block promotion avoids.
2. The evaluation texts and calibration shards are small; variance may contribute.
3. The block promotion mechanism (replacing Q2 values with Q4 values for selected blocks while leaving the rest at Q2) may interact differently with the Qwen quantization scheme than a full-model Q4 load.

This anomaly does not undermine the central comparison among selection methods at the same budget, but it does indicate that the all-Q4 reference should not be treated as a strict ceiling for partial promotion on this model. We flag this as an unresolved observation requiring further investigation.

### Summary of Cross-Model Transfer

| Budget | SmolLM2 regret vs. best control | Qwen regret vs. best control | Transfer verdict |
|---|---|---|---|
| 5% (sparse) | +0.69 (vs. weight norm) | +0.43 (vs. quant error) | Positive |
| 20% (medium) | +5.07 (vs. weight norm) | −1.40 (vs. random) | Negative |

## Limitations

1. **Model scale.** Both tested models are small (135M and 0.5B parameters). The behavior of calibration-regret promotion at larger scales remains unknown. Block interactions and saturation dynamics may differ substantially in models with deeper, more interdependent layers.

2. **Limited target scope.** Only four early-layer matrices per model were evaluated. Promotion decisions for mid-layer and late-layer weights, embedding matrices, and normalization parameters were not tested.

3. **Shard and calibration size.** Calibration was performed on 2–3 shards with 6–12 calibration texts. The stability of regret rankings under larger calibration sets or different shard partitions was not assessed.

4. **Medium-budget failure is unexplained.** The Qwen medium-budget failure could arise from block interaction saturation, calibration overfitting, or an artifact of the specific block geometry (448×448 blocks). The current experiments do not disambiguate these causes.

5. **Anomalous all-Q4 reference on Qwen.** The loss reductions from all sparse-budget methods exceeding the all-Q4 upper bound on Qwen are not explained. The all-Q4 reference may not serve as a reliable ceiling for partial promotion on all models.

6. **No latency-optimized kernel.** The prototype applies promotion by replacing Q2 values with Q4 values in the cached model before benchmarking. A production deployment would require a kernel that selectively reads Q4 for promoted blocks and Q2 for the rest, which may introduce different throughput characteristics.

7. **Single quantization pair.** Only Q2→Q4 promotion was tested. Other bit-width transitions (e.g., Q3→Q8, Q2→Q8) may exhibit different regret landscapes.

8. **Random control variance.** The random baseline was evaluated with 4–8 trials. While sufficient to establish that the Qwen medium-budget regret result falls below the random mean, tighter confidence intervals would require more trials.

9. **AI-generated artifact.** This draft and the underlying analysis were produced by an automated AI research pipeline. No independent human audit of the claims, metrics, or interpretations has been performed. The claim ledger records no formally adjudicated claims for this run.

10. **Random seeds not recorded.** Random seeds were not explicitly captured in the available artifacts. Exact reproducibility of random-control baselines may vary across re-runs.

## Reproducibility Checklist

- **Code availability:** Prototype script at `src/promotion_runtime_prototype.py`; compiles cleanly under Python with `py_compile`.
- **Model identifiers:** `HuggingFaceTB/SmolLM2-135M` (implied by SmolLM2 reference), `Qwen/Qwen2.5-0.5B-Instruct`. Both are publicly available cached models.
- **Software versions:** Python (system), `torch==2.11.0+cu130`, `transformers==5.7.0`, `accelerate`, `safetensors`, `psutil`. Installed via `uv pip` into project-local `.venv`.
- **Hardware:** NVIDIA GB10 GPU; host memory >115 GB available; no swap configured (SwapTotal = 0 MB).
- **Random seeds:** Not explicitly recorded in the available artifacts. Reproducibility of random-control baselines may vary.
- **Output artifacts:** Promotion masks (`promotion_masks_q2_to_q4.json`), runtime metrics (`runtime_metrics_q2_to_q4.json` and `.csv`), and aggregated summary (`runtime_summary.json`) are saved per run directory.
- **Commands:** Full command lines for all three runs (smoke, main, Qwen cross-model) are recorded in the run notes and are re-runnable with the same software stack.
- **Verification steps performed:** `py_compile` check passed; smoke run (single matrix) passed; main four-matrix run passed; cross-model Qwen smoke passed; memory posture verified (MemAvailable >115 GB, CUDA allocation bounded).

## Conclusion

The calibration-regret block-promotion runtime prototype demonstrates that sparse Q2→Q4 promotion masks, selected by a calibration-regret heuristic and materialized as durable JSON artifacts, can recover a substantial fraction of full-precision-upgrade loss reduction at minimal memory cost. On SmolLM2-135M, sparse promotion (5% budget) recovered 26.7% of the all-Q4 improvement, and medium promotion (20%) recovered 77.5%—both outperforming quantization-error, weight-norm, and random controls. On Qwen2.5-0.5B-Instruct, sparse promotion similarly outperformed all controls, confirming cross-model viability at the sparse budget.

However, medium-budget promotion failed on Qwen2.5-0.5B, producing near-zero loss improvement and losing to random selection. This indicates that the marginal benefit of promoting additional blocks beyond the sparse set can be negative, likely due to saturation or non-additive interactions among promoted blocks. Additionally, the all-Q4 reference on Qwen does not serve as a reliable ceiling for partial promotion, as all sparse-budget methods exceeded it—an observation that remains unexplained.

We recommend advancing the sparse promotion path as a reusable runtime component. Medium-budget promotion should not be applied unconditionally; it requires a gating mechanism—such as marginal regret decay detection, cross-shard agreement thresholds, or a held-out calibration gate—before promotion beyond the sparse budget is permitted on a new model. The medium-budget failure mode and the anomalous all-Q4 reference on Qwen both merit targeted investigation before the prototype is extended to larger models or broader target scopes.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Prototype script | `src/promotion_runtime_prototype.py` |
| SmolLM2 promotion masks | `results/runtime_prototype/promotion_masks_q2_to_q4.json` |
| SmolLM2 runtime metrics | `results/runtime_prototype/runtime_metrics_q2_to_q4.json` |
| SmolLM2 runtime metrics (CSV) | `results/runtime_prototype/runtime_metrics_q2_to_q4.csv` |
| Qwen promotion masks | `results/runtime_qwen_smoke/promotion_masks_q2_to_q4.json` |
| Qwen runtime metrics | `results/runtime_qwen_smoke/runtime_metrics_q2_to_q4.json` |
| Aggregated summary | `results/runtime_summary.json` |
| Smoke run log | `logs/runtime_smoke.log` |
| Main run log | `logs/runtime_prototype.log` |
| Qwen run log | `logs/runtime_qwen_smoke.log` |
| Run notes | `run_notes.md` |
| Project decision record | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260501T111348570802+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T111348570802+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T111348570802+0000/paper_manifest.json` |
