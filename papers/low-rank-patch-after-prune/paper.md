# Low-Rank Patch After Prune: Recovering Accuracy in Hard-Pruned Networks via Frozen-Sparse Additive Low-Rank Deltas

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, and metric files). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact.

---

## Abstract

We investigate whether a hard magnitude-pruned neural network can recover useful accuracy by freezing the sparse base weights and training small additive low-rank patches (LoRA-style deltas) on each pruned weight matrix. In a controlled NumPy-based experiment on a 784→128→10 MLP trained on 10k MNIST samples, hard pruning at 90–98% sparsity collapses test accuracy from a 94.45% dense baseline to 20–52%. Training additive low-rank factors (ranks 4, 8, 16) on the frozen sparse base recovers a substantial fraction of the lost accuracy. At the most aggressive compression point (98% sparsity, rank 8), patched accuracy averaged 91.65% across three seeds (population std 0.51 pp) versus 94.10% dense and 24.35% pruned-only, using 10,572 effective parameters (~10.4% of the dense count). The rank sweep was not monotonic: higher rank did not consistently improve accuracy under the fixed optimizer and epoch budget, suggesting optimizer sensitivity or overfitting. These results support the viability of the frozen-sparse-plus-low-rank-delta protocol in a small-scale setting but do not constitute evidence for transformer- or LLM-scale behavior.

## Introduction

Magnitude pruning is among the simplest and most widely used methods for reducing neural network parameter counts. At high sparsity levels, however, it catastrophically degrades accuracy. Standard recovery approaches include fine-tuning the surviving sparse weights, retraining from scratch under a sparsity constraint, or applying distillation. An alternative is to treat the pruned network as a frozen substrate and learn a compact additive correction.

This work asks: *after hard magnitude pruning, can a small trained low-rank additive patch recover most of the lost accuracy while keeping the sparse base frozen?* The approach is structurally similar to LoRA-style adaptation but applied post-pruning rather than for task adaptation. If effective, it would allow pruned models to be patched without modifying the sparse base, potentially enabling deployment scenarios where the sparse structure must remain fixed (e.g., hardware-compiled sparse kernels).

We test this question in a minimal setting: a two-layer ReLU MLP on MNIST, pruned at 90%, 95%, and 98% sparsity, with additive low-rank corrections at ranks 4, 8, and 16. We report the main grid results and a three-seed replication at the most aggressive compression point. This is a local mechanistic test of viability for the proposed intervention, not a claim about LLM-scale behavior.

## Method

### Architecture and Training

The experiment is implemented in pure NumPy (no PyTorch or sklearn dependency) in `scripts/run_low_rank_patch_experiment.py`. The pipeline is:

1. **Data:** Download MNIST IDX files to `data/mnist/`. Sample 10,000 training images and 2,000 test images.
2. **Dense training:** Train a 784→128 (ReLU)→10 MLP via SGD with cross-entropy loss for 10 epochs. This yields the dense baseline weights $W_1 \in \mathbb{R}^{128 \times 784}$, $W_2 \in \mathbb{R}^{10 \times 128}$, and biases.
3. **Hard magnitude pruning:** Zero out the smallest-magnitude entries in $W_1$ and $W_2$ to reach target sparsity (90%, 95%, or 98%). Biases are not pruned. The pruned weights are denoted $\hat{W}_1, \hat{W}_2$.
4. **Low-rank patch training:** Freeze $\hat{W}_1, \hat{W}_2$. For each pruned matrix, learn an additive low-rank correction $\Delta W = U V^T$ where $U \in \mathbb{R}^{d_{out} \times r}$, $V \in \mathbb{R}^{d_{in} \times r}$, and $r \in \{4, 8, 16\}$. The forward pass becomes:

$$h = \text{ReLU}(x (\hat{W}_1 + U_1 V_1^T)^T + b_1)$$
$$\hat{y} = h (\hat{W}_2 + U_2 V_2^T)^T + b_2$$

Train $U_1, V_1, U_2, V_2$ via SGD for 8 epochs with the same cross-entropy loss. The sparse base remains frozen throughout.

5. **Evaluation:** Report test accuracy on the 2,000-sample test subset.

### Parameter Accounting

**Effective parameters** count both the surviving sparse nonzeros and the low-rank factors. For a matrix of shape $d_{out} \times d_{in}$ at sparsity $s$ with rank-$r$ patch:

$$\text{effective params} = (1 - s) \cdot d_{out} \cdot d_{in} + r \cdot (d_{out} + d_{in})$$

This accounting assumes ideal unstructured sparse storage (i.e., each nonzero is stored individually). Real hardware speedups would require sparse kernels or structured pruning, which are not evaluated here. The effective parameter fraction does not translate directly to a proportional speedup.

### Replication

The main grid runs with seed 0. For the strongest compression point (98% sparsity, rank 8), we run two additional seeds (1, 2) and report mean and population standard deviation.

### Environment

- Python 3 with NumPy 2.4.4; CPU-only execution.
- Machine: NVIDIA GB10 system; GPU utilization 0% (experiment ran on CPU/NumPy).
- Available memory: ~122 GB; swap disabled.

## Results

### Dense Baseline

The dense MLP achieved 94.45% test accuracy with 101,770 total parameters (weights and biases).

### Main Grid

Hard pruning severely degrades accuracy, as expected. The low-rank patch recovers a substantial fraction of the loss across all sparsity-rank combinations:

| Sparsity | Pruned Acc | Rank | Patched Acc | Effective Params | Patch Params |
|---------:|-----------:|-----:|------------:|----------------:|-------------:|
| 90%      | 51.55%     | 4    | 92.00%      | 14,502          | 4,200        |
| 90%      | 51.55%     | 8    | 90.95%      | 18,702          | 8,400        |
| 90%      | 51.55%     | 16   | 89.15%      | 27,102          | 16,800       |
| 95%      | 32.10%     | 4    | 90.70%      | 9,420           | 4,200        |
| 95%      | 32.10%     | 8    | 91.85%      | 13,620          | 8,400        |
| 95%      | 32.10%     | 16   | 91.45%      | 22,020          | 16,800       |
| 98%      | 20.50%     | 4    | 89.10%      | 6,372           | 4,200        |
| 98%      | 20.50%     | 8    | 92.30%      | 10,572          | 8,400        |
| 98%      | 20.50%     | 16   | 90.05%      | 18,972          | 16,800       |

At 98% sparsity with rank 8, the patched model achieves 92.30% accuracy using 10,572 effective parameters (10.4% of the dense count), recovering 71.9% of the accuracy lost to pruning: $(92.30 - 20.50) / (94.45 - 20.50)$.

### Non-Monotonic Rank Behavior

Higher rank did not consistently improve patched accuracy. At 90% sparsity, rank 4 (92.00%) outperformed rank 8 (90.95%) and rank 16 (89.15%). At 95% and 98% sparsity, rank 8 was the best, with rank 16 underperforming both rank 4 and rank 8 in some cells. This non-monotonicity likely reflects optimizer sensitivity or overfitting under the fixed 8-epoch patch training budget, rather than a fundamental capacity limitation. We do not claim a scaling law from these results.

### Replication at 98% Sparsity, Rank 8

| Seed | Dense Acc | Pruned Acc | Patched Acc |
|-----:|----------:|-----------:|------------:|
| 0    | 94.45%    | 20.50%     | 92.30%      |
| 1    | 94.10%    | 28.25%     | 91.05%      |
| 2    | 93.75%    | 24.30%     | 91.60%      |

Mean patched accuracy: **91.65%** (population std 0.51 pp). Mean dense accuracy: 94.10%. Mean pruned accuracy: 24.35%. The recovery is consistent across seeds, though the pruned-only accuracy varies substantially (20.50%–28.25%), reflecting the instability of hard pruning at extreme sparsity.

## Limitations

1. **Scale and architecture.** All evidence comes from a small MNIST MLP (101,770 parameters, 2 layers). Transformer weights, attention patterns, and LLM-scale optimization landscapes may behave differently. No claim about LLM-scale behavior is warranted.

2. **Effective parameter accounting assumes ideal sparse storage.** The effective parameter counts treat unstructured sparse nonzeros as individually stored. Real inference speedups and memory savings require sparse kernels or structured pruning, which were not evaluated. The 10.4% effective parameter fraction does not translate directly to a 10× speedup.

3. **No comparison against alternative recovery methods.** The experiment does not compare against (a) fine-tuning the surviving sparse weights, (b) retraining a low-rank model from scratch, (c) knowledge distillation, or (d) gradual pruning with retraining. The additive low-rank patch may be inferior to some of these baselines under equal parameter or compute budgets.

4. **Optimizer and hyperparameter sensitivity.** The non-monotonic rank behavior suggests sensitivity to the patch training procedure (learning rate, epoch count, initialization). No hyperparameter search was performed. Different settings could shift the optimal rank or improve higher-rank patches.

5. **Single dataset.** Results are on MNIST only. Generalization to other datasets and domains is unknown.

6. **No structured pruning or hardware evaluation.** The pruning is unstructured magnitude-based. Structured pruning (e.g., channel, head, or block pruning) may interact differently with low-rank patching.

7. **Residual accuracy gap.** Even at the best observed point, patched accuracy (91.65%) remains 2.45 pp below the dense baseline (94.10%). Whether this gap can be closed with more patch training, higher rank, or different patch architectures is not determined.

## Reproducibility Checklist

- **Code available:** Yes. Experiment script: `scripts/run_low_rank_patch_experiment.py` (pure NumPy, no GPU required).
- **Data:** Standard MNIST IDX files; downloaded automatically by the script.
- **Random seeds:** Main grid uses seed 0; replicates use seeds 1 and 2 (passed via `--seed` flag).
- **Hyperparameters fully specified:** Yes. Train samples: 10,000; test samples: 2,000; hidden dim: 128; dense epochs: 10; patch epochs: 8; sparsities: 0.90, 0.95, 0.98; ranks: 4, 8, 16. Learning rate and other SGD details are in the script.
- **Hardware:** CPU-only (NumPy). System had NVIDIA GB10 GPU but it was not used. ~122 GB RAM available, swap disabled.
- **Result files:** `results/smoke_metrics.json`, `results/main_metrics.json`, `results/replicate_seed1_s98_r8.json`, `results/replicate_seed2_s98_r8.json`, `results/summary_metrics.json`.
- **Logs:** `logs/smoke_20260430T111949.log`, `logs/main_20260430T111923.log`, `logs/replicates_20260430T111937.log`.
- **Statistical uncertainty:** Three seeds at the primary claim point (98% sparsity, rank 8); population std reported. No confidence intervals or significance tests computed.
- **Negative/mixed results reported:** Yes. Non-monotonic rank behavior and residual accuracy gap are reported.

## Conclusion

In a controlled MNIST MLP setting, freezing a hard magnitude-pruned network and training small additive low-rank patches recovers most of the accuracy lost to pruning. At 98% sparsity with rank-8 patches, three-seed mean patched accuracy was 91.65% versus 94.10% dense and 24.35% pruned-only, using approximately 10.4% of the dense parameter count. The approach is viable at this scale, but the non-monotonic rank response and the absence of comparisons against alternative recovery methods temper the strength of the claim. The residual 2.45 pp gap below the dense baseline remains unexplained. The decisive next step is to apply the same frozen-sparse-plus-low-rank-delta protocol to a small transformer or toy language model and compare against sparse fine-tuning under matched parameter and update budgets.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Experiment script | `scripts/run_low_rank_patch_experiment.py` |
| Smoke test metrics | `results/smoke_metrics.json` |
| Main grid metrics | `results/main_metrics.json` |
| Replicate metrics (seed 1) | `results/replicate_seed1_s98_r8.json` |
| Replicate metrics (seed 2) | `results/replicate_seed2_s98_r8.json` |
| Summary metrics | `results/summary_metrics.json` |
| Smoke test log | `logs/smoke_20260430T111949.log` |
| Main grid log | `logs/main_20260430T111923.log` |
| Replicates log | `logs/replicates_20260430T111937.log` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260430T161718583872+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T161718583872+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T161718583872+0000/paper_manifest.json` |
