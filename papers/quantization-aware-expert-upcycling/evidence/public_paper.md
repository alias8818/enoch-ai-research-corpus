# Quantization-Aware Expert Upcycling: Reducing Deployed Quantization Error in Dense-to-MoE Conversion

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, and metric files). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact and evaluate its claims against the referenced primary data.

---

## Abstract

Dense-to-Mixture-of-Experts (MoE) upcycling duplicates a trained dense feed-forward network into routed experts and specializes each expert on its assigned data subset. When the resulting MoE model is deployed under low-bit weight-only quantization, post-training quantization (PTQ) applied after float specialization can erase much of the upcycling gain. We investigate whether making the expert-specialization phase quantization-aware—by inserting fake-quantized weights with straight-through estimator (STE) gradients during training—reduces deployed quantization error. In a controlled synthetic experiment (two-domain regression with one-hidden-layer ReLU FFNs, oracle routing, symmetric per-matrix weight-only quantization at 4, 3, and 2 bits), quantization-aware upcycling reduced deployed quantized MSE relative to float-upcycle-then-PTQ by 54.3% at 4 bits, 58.7% at 3 bits, and 87.7% at 2 bits, winning all 10 random seeds at each bit width. However, quantization-aware upcycling sacrificed float-domain quality (MSE 0.892 vs. 0.503 at the 4-bit configuration), indicating a quantization–accuracy trade-off. These results are limited to a synthetic NumPy-only setting with oracle routing, no learned router, no real transformer, and no production quantization kernels. The finding is a positive mechanistic signal but requires validation on real language models with learned routing and MoE-aware calibration baselines before any general claim can be made.

## 1. Introduction

Upcycling—converting a trained dense model into a sparse Mixture-of-Experts model by duplicating feed-forward layers into routed experts—has emerged as a practical method for increasing model capacity from existing checkpoints. Prior work demonstrates that upcycling can outperform continued dense training under certain conditions and introduces initialization and routing best practices (Upcycling Large Language Models into Mixture of Experts, arXiv:2410.07524). Scaling-law analysis further characterizes the data and model interaction limits of upcycling (Scaling Laws for Upcycling Mixture-of-Experts Language Models, arXiv:2502.03009).

A separate line of work highlights that MoE models present distinctive challenges for low-bit quantization. Sparse and dynamic routing induces inter-expert and intra-expert activation imbalance, and MoE-aware quantization methods can materially improve low-bit accuracy over naive PTQ (MoEQuant, arXiv:2505.03804).

These two directions motivate a natural question: rather than making quantization MoE-aware *after* training, can we make the upcycling specialization phase itself aware of the target quantization? If the final deployment uses low-bit weight-only quantization, then training each expert with fake-quantized weights in the forward pass should, in principle, allow the expert to adapt its weight distribution to the quantization grid, reducing deployed quantization error compared with training in float and applying PTQ afterward.

This paper reports a controlled test of that hypothesis. We do not claim a general solution; rather, we isolate the mechanism in a synthetic setting and report both positive and negative findings with full uncertainty.

## 2. Method

### 2.1 Task and Model Architecture

We use a synthetic two-domain regression task. Input vectors are drawn such that the first feature `x[0]` determines the domain: `x[0] > 0` routes to domain A, otherwise domain B. Each domain has a distinct teacher implemented as a one-hidden-layer ReLU feed-forward network (FFN). The student dense model is a single small ReLU FFN trained on both domains jointly.

### 2.2 Upcycling Procedure

The trained dense FFN is duplicated into two expert copies. Each expert is then fine-tuned (specialized) on its assigned domain. To isolate the effect of quantization-aware training from router learning, we use **oracle routing** based on the ground-truth domain indicator `x[0]`. This intentionally removes router learning as a confound.

### 2.3 Quantization

We apply symmetric per-matrix signed weight-only quantization at 4, 3, and 2 bits. Biases remain in fp32. The quantization scheme maps each weight matrix to a uniform grid centered at zero, with scale determined by the maximum absolute weight value per matrix.

### 2.4 Training Conditions

Five conditions are compared:

1. **Dense float**: The original dense FFN evaluated in floating point.
2. **Dense quantized**: The dense FFN with PTQ applied.
3. **Float upcycling (float eval)**: Experts specialized in float, evaluated in float.
4. **Float upcycling + PTQ (quantized eval)**: Experts specialized in float, PTQ applied, evaluated quantized.
5. **Quantization-aware upcycling (quantized eval)**: Experts specialized with fake-quantized weights in the forward pass using straight-through estimator (STE) gradients, then evaluated with actual quantized weights.

### 2.5 Implementation

The experiment is implemented in pure Python with NumPy 2.4.4, intentionally avoiding PyTorch or other deep learning frameworks to isolate the mechanism and minimize dependency confounds. All computation runs on CPU (ARM Cortex-X925 + Cortex-A725, 20 cores). No GPU computation is used despite GPU availability (NVIDIA GB10), as the experiment is CPU-only. Maximum resident set size was approximately 42 MiB, far below available memory.

### 2.6 Evaluation

The primary metric is mean squared error (MSE) on a held-out test set. Each configuration is run over 10 independent random seeds, and we report mean ± standard deviation. We additionally report the quantization penalty (quantized MSE minus float MSE) for each approach, and the relative change in deployed quantized MSE between float-upcycle+PTQ and quantization-aware upcycling.

## 3. Results

### 3.1 Main Comparison: Deployed Quantized MSE

Table 1 reports the deployed quantized MSE for float-upcycle+PTQ versus quantization-aware upcycling across bit widths, averaged over 10 seeds.

**Table 1.** Deployed quantized MSE comparison (mean ± std over 10 seeds). Lower is better.

| Bits | Float upcycle + PTQ MSE | Q-aware upcycle MSE | Relative change | Q-aware wins |
|-----:|------------------------:|--------------------:|----------------:|-------------:|
| 4 | 2.709 ± 0.881 | 1.210 ± 0.323 | −54.3% ± 7.0% | 10/10 |
| 3 | 7.062 ± 1.798 | 2.872 ± 0.733 | −58.7% ± 7.9% | 10/10 |
| 2 | 45.680 ± 22.795 | 3.948 ± 0.459 | −87.7% ± 9.7% | 10/10 |

Quantization-aware upcycling consistently outperformed float-upcycle+PTQ at every bit width and every seed. The advantage grows substantially as bit width decreases: from a 54.3% relative MSE reduction at 4 bits to an 87.7% reduction at 2 bits. This is consistent with the expectation that lower bit widths produce larger quantization errors that float-specialized weights are not adapted to absorb.

### 3.2 Full 4-Bit Decomposition

Table 2 decomposes the 4-bit results to reveal the quantization–accuracy trade-off.

**Table 2.** 4-bit condition decomposition (mean ± std over 10 seeds).

| Condition | MSE |
|---|---:|
| Dense float | 1.189 ± 0.341 |
| Dense quantized (PTQ) | 3.508 ± 0.977 |
| Float upcycled (float eval) | 0.503 ± 0.078 |
| Float upcycled + PTQ (quantized eval) | 2.709 ± 0.881 |
| Q-aware upcycled (float eval) | 0.892 ± 0.193 |
| Q-aware upcycled (quantized eval) | 1.210 ± 0.323 |

Key observations:

- **Float upcycling works**: Specialized float experts (MSE 0.503) substantially outperform the dense float model (MSE 1.189), confirming the basic upcycling mechanism on this task.
- **PTQ erases upcycling gains**: Applying PTQ to float-specialized experts increases MSE from 0.503 to 2.709, a quantization penalty of +2.206 MSE. The quantized upcycled model (2.709) is worse than the dense float model (1.189).
- **Q-aware upcycling trades float quality for quantized robustness**: The quantization-aware experts have worse float performance (0.892 vs. 0.503) but much better quantized performance (1.210 vs. 2.709). The quantization penalty for Q-aware upcycling is only +0.318 MSE, compared to +2.206 for float upcycling.
- **Q-aware quantized approaches dense float**: At 4 bits, the quantization-aware upcycled model (1.210) is close to the dense float baseline (1.189), while float-upcycle+PTQ (2.709) is substantially worse.

### 3.3 3-Bit and 2-Bit Ablations

At 3 bits, the pattern intensifies. Dense quantized MSE rises to 7.956 ± 2.056, and float-upcycle+PTQ MSE reaches 7.062 ± 1.798. Quantization-aware upcycling maintains deployed MSE of 2.872 ± 0.733, a 58.7% reduction. The Q-aware upcycled float MSE at 3 bits is 2.334 ± 0.644, substantially worse than the 4-bit float MSE of 0.892, suggesting that the fake quantization noise during training at 3 bits degrades float quality more severely.

At 2 bits, the effect is most dramatic. Float-upcycle+PTQ MSE reaches 45.680 ± 22.795 with very high variance, while Q-aware upcycling maintains deployed MSE of 3.948 ± 0.459. A notable anomaly: the Q-aware quantization penalty at 2 bits is negative (−13.002 ± 9.820), meaning the quantized model outperforms the float model. This may reflect regularization effects of the 2-bit quantization grid on a model trained to expect that grid; the float weights may overfit to the quantization-aware training distribution in a way that actual quantization corrects. This anomaly is not fully explained and warrants further investigation.

### 3.4 Variance and Seed Consistency

The Q-aware approach wins all 10 seeds at every bit width. However, the variance of the relative improvement is non-trivial (7.0–9.7% standard deviation in the percentage reduction). At 2 bits, the float-upcycle+PTQ condition has extremely high variance (std 22.795 on a mean of 45.680), indicating that some seeds produce catastrophically bad PTQ outcomes. The Q-aware approach exhibits much lower variance in deployed MSE at all bit widths, suggesting it is not only better on average but also more robust to random initialization.

## 4. Limitations

This study has substantial limitations that prevent drawing general conclusions for production LLM deployment:

1. **Synthetic task only**: The experiment uses a two-domain synthetic regression task with one-hidden-layer ReLU FFNs. No real language modeling data, transformer architecture, or token-level evaluation was involved.

2. **Oracle routing**: Domain assignment is provided by ground truth rather than a learned router. In practice, router learning interacts with expert specialization, and routing errors may change the quantization-aware training dynamics.

3. **No MoE-aware PTQ baseline**: The PTQ compared against is naive per-matrix quantization. MoE-aware calibration methods (e.g., expert-balanced sampling and affinity-guided calibration as proposed in MoEQuant) may narrow the gap between float-upcycle+PTQ and quantization-aware upcycling. The absence of this baseline means the reported improvements may overstate the practical advantage.

4. **No real quantization kernels**: The experiment simulates quantization in NumPy. Production quantized inference uses specialized kernels with different numerical properties, memory layouts, and accumulation behavior.

5. **Small model scale**: The FFNs used are small. Scaling behavior to models with billions of parameters, hundreds of experts, and multiple MoE layers is unknown.

6. **Weight-only quantization**: Only weight-only quantization is tested. Activation quantization, KV-cache quantization, and mixed-precision schemes are not addressed.

7. **Single upcycling recipe**: Only one upcycling procedure (duplicate-and-specialize) is tested. Other initialization schemes, expert counts, or fine-tuning schedules may interact differently with quantization-aware training.

8. **Negative float-quality trade-off**: Quantization-aware upcycling consistently degrades float-domain performance. If deployment requires both float and quantized inference paths, this trade-off must be managed.

9. **Anomalous 2-bit result**: The negative quantization penalty at 2 bits is unexpected and not fully explained. It may reflect an artifact of the small model scale or the specific quantization scheme.

## 5. Reproducibility Checklist

- **Code availability**: The experiment script `scripts/quant_aware_upcycling_experiment.py` is included in the project directory and is self-contained (pure Python + NumPy).
- **Dependencies**: Python 3.12.3, NumPy 2.4.4. No GPU or CUDA required.
- **Random seeds**: 10 independent seeds per bit-width configuration. Seeds are set internally by the script.
- **Hardware**: ARM-based host (Linux 6.17.0-1014-nvidia aarch64, 20 cores, ~121 GiB RAM). No GPU used. Maximum RSS ~42 MiB.
- **Execution time**: ~2.8–2.9 seconds per 10-seed run (~3.5 seeds/second).
- **Smoke test**: A single-seed smoke test completed in ~0.021–0.031 seconds, confirming environment functionality before full runs.
- **Output artifacts**: All metric JSON files and log files are preserved (see Section 7).
- **Quantization scheme**: Symmetric per-matrix signed weight-only quantization. Scale = max(|W|) per matrix. Biases in fp32.
- **Routing**: Oracle (ground-truth domain indicator). No learned router.

## 6. Conclusion

In a controlled synthetic experiment, quantization-aware expert upcycling—training upcycled experts with fake-quantized weights and STE gradients—substantially reduces deployed quantization error compared to the standard practice of float specialization followed by post-training quantization. The effect is consistent across all tested seeds and grows with decreasing bit width, from a 54.3% MSE reduction at 4 bits to an 87.7% reduction at 2 bits.

However, this improvement comes at the cost of degraded float-domain performance, and the experiment isolates only one mechanism in a highly simplified setting. The results do not constitute evidence that quantization-aware upcycling will succeed in production LLMs with learned routing, real token distributions, MoE-aware calibration baselines, or production quantization kernels.

The finding is best interpreted as a positive mechanistic signal warranting next-stage validation. Specifically, future work should: (1) test on a small but real transformer or language model checkpoint; (2) replace oracle routing with learned top-k routing and expert-balance loss; (3) include MoE-aware calibration as a PTQ baseline; and (4) measure real GPU utilization and memory with a Torch/CUDA implementation.

## 7. Referenced Artifacts

The following local artifacts from project `source-record-redacted` contain the primary evidence for this report:

| Artifact | Path | Description |
|---|---|---|
| Run notes | `run_notes.md` | Full experimental log and interpretation |
| Experiment script | `scripts/quant_aware_upcycling_experiment.py` | Reproducible experiment source |
| Smoke metrics | `results/smoke_metrics.json` | Single-seed smoke-test metrics |
| 4-bit metrics | `results/quant_aware_upcycling_int4_metrics.json` | Main 4-bit run (10 seeds) |
| 3-bit metrics | `results/quant_aware_upcycling_int3_metrics.json` | 3-bit ablation (10 seeds) |
| 2-bit metrics | `results/quant_aware_upcycling_int2_metrics.json` | 2-bit ablation (10 seeds) |
| Convenience copy | `results/quant_aware_upcycling_metrics.json` | Copy of 4-bit metrics |
| Smoke log | `logs/smoke.log` | Smoke-test stdout |
| 4-bit run log | `logs/int4_run.log` | Full 4-bit metric payload |
| 3-bit run log | `logs/int3_run.log` | Full 3-bit metric payload |
| 2-bit run log | `logs/int2_run.log` | Full 2-bit metric payload |
| 4-bit resource log | `logs/int4_run.time.log` | `/usr/bin/time -v` output |
| 3-bit resource log | `logs/int3_run.time.log` | `/usr/bin/time -v` output |
| 2-bit resource log | `logs/int2_run.time.log` | `/usr/bin/time -v` output |
| Project decision | `.omx/project_decision.json` | Machine-readable decision and metadata |

### External Sources Referenced

- Upcycling Large Language Models into Mixture of Experts. arXiv:2410.07524
- Scaling Laws for Upcycling Mixture-of-Experts Language Models. arXiv:2502.03009
- MoEQuant: Enhancing Quantization for Mixture-of-Experts Large Language Models via Expert-Balanced Sampling and Affinity Guidance. arXiv:2505.03804
