# Reversible Prune Masks: Exact Logit Recovery via Binary Mask Restoration, Without Inherent Speedup

**AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, benchmark results, and decision JSON). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

We investigate "reversible prune masks"—binary masks stored separately from dense weights, where the effective weight is computed as `weight * mask`—as a mechanism for pruning that preserves the possibility of exact rollback. On a synthetic 3-class spiral classification task using a two-layer ReLU MLP implemented in NumPy, we find that restoring all mask bits to 1 exactly recovers the original dense model's logits (maximum logit delta = 0.0 across all five random seeds and all four sparsity levels tested). By contrast, hard-deleting masked weights and subsequently setting mask bits to 1 does not recover the original model (logit deltas > 1.0 in all cases). However, dense binary masks confer no inference speedup: masked forward passes using dense NumPy kernels were approximately 1.8% slower than unmasked dense forward passes (mean timing ratio 1.0184, SD 0.00054). Magnitude-based masks outperformed random masks at moderate sparsity (50–85%), but both degraded to near-chance accuracy at 95% sparsity. Fine-tuning under a fixed mask partially recovered accuracy at 85% sparsity (mean 0.897 vs. raw masked 0.488), but altered surviving weights, meaning subsequent unmasking no longer reproduces the original dense model. These results support reversible prune masks as a control-plane and audit primitive—not as a standalone compression or acceleration technique.

## Introduction

Neural network pruning is commonly understood as the removal of weights deemed unimportant, typically implemented via a binary mask over the weight matrix. The Lottery Ticket Hypothesis frames pruning in precisely this way: a binary mask identifies a sparse subnetwork that, under certain training conditions, can match dense accuracy (Frankle & Carbin, 2018, https://arxiv.org/abs/1803.03635). Practical pruning toolkits such as NNI explicitly distinguish between mask simulation (applying a binary mask to dense weights to evaluate sparse model quality) and real speedup (which requires sparse kernels or model compaction; https://nni.readthedocs.io/zh/stable/tutorials/pruning_speedup.html).

A natural question arises: if pruning is implemented as a mask over preserved dense weights, is the operation reversible? That is, can one restore the original dense model exactly by setting all mask bits back to 1? This question has practical implications for:

1. **Safety and audit**: rolling back a pruning decision without retraining.
2. **Checkpointing**: storing masks as diffs rather than creating irreversible weight deletions.
3. **Control-plane semantics**: treating pruning as a toggleable configuration rather than a destructive operation.

We operationalize a "reversible prune mask" as a binary mask stored separately from dense weights, with forward and backward passes computing `effective_weight = weight * mask`. We test whether masked pruning is reversible by restoring all mask bits to 1, and we characterize the practical limits of this approach—including the interaction with fine-tuning, the contrast with hard deletion, and the absence of inference speedup when using dense kernels.

The reversibility result is, in retrospect, mathematically expected: if weights are preserved and only the mask changes, then restoring the mask is an identity operation on the weight tensor. The contribution of this work is not the mathematical observation itself, but the empirical confirmation that this property holds exactly (not merely approximately) in practice, the quantification of what breaks it (hard deletion, fine-tuning), and the explicit negative result that masks alone do not accelerate inference under dense execution.

## Method

### Task and Model

We used a deterministic synthetic 3-class spiral dataset to avoid external data dependencies. The model was a two-layer ReLU MLP with a hidden dimension of 96, implemented entirely in NumPy (version 2.4.4). Training used 360 samples per class (1,080 total). No deep learning framework (e.g., PyTorch, TensorFlow) was required or used. This is a toy-scale experiment intended for local falsification and proof-of-concept validation, not production benchmarking.

### Pruning Procedure

After dense training, global magnitude pruning was applied to produce binary masks at four sparsity levels: 50%, 70%, 85%, and 95%. Global magnitude pruning ranks all weight magnitudes across the entire model and sets the lowest-ranked fraction to zero in the mask. For each sparsity level, the experiment measured:

1. **Dense baseline accuracy**: accuracy of the unpruned model.
2. **Magnitude-mask accuracy**: accuracy with the top-k magnitude mask applied.
3. **Random-mask accuracy**: accuracy with a random mask at equal sparsity (uniform random selection of weights to prune).
4. **Reversible unmask accuracy**: accuracy after restoring all mask bits to 1, and the maximum absolute logit delta between the original dense model and the unmasked model.
5. **Hard-delete-then-unmask accuracy**: accuracy after zeroing out masked weights in the weight matrix (hard deletion), then setting all mask bits to 1, and the maximum absolute logit delta between the original dense model and the hard-deleted-then-unmasked model.
6. **Fixed-mask fine-tune accuracy**: accuracy after fine-tuning the surviving weights under a fixed mask, and subsequent unmask behavior.
7. **Dense vs. masked forward timing**: wall-clock ratio of masked forward pass to dense forward pass using dense NumPy kernels (element-wise multiply then matrix multiply, no sparse-kernel optimization).

### Replication

The main configuration used 1,800 training epochs and 250 fine-tuning epochs. Five replicate runs were conducted with seeds 11, 17, 23, 31, and 43, each with 1,600 training epochs and 220 fine-tuning epochs. Aggregate statistics (mean and standard deviation) were computed across all five replicates.

### Environment

All experiments ran on a CPU-only system with approximately 122.68 GB available RAM and no swap partition. Python 3.12.3 was used with a venv-local NumPy 2.4.4. Maximum RSS for the main single run was 37,548 KB; replicates were similarly small. No memory pressure was observed. No GPU was used or required.

## Results

### Exact Reversibility of Mask Restoration

Across all five seeds and all four sparsity levels, restoring all mask bits to 1 exactly recovered the original dense model's logits. The maximum absolute logit delta was exactly 0.0 in every tested case. Dense baseline test accuracy was mean 0.9933 (SD 0.0064); unmasked accuracy matched this exactly in all conditions.

This confirms that when the original dense weights are preserved and only the mask is modified, pruning via binary masking is fully reversible at the logit level—not merely at the accuracy level. The result is consistent with the mathematical expectation that `weight * 1.0 = weight` for all entries, but the empirical confirmation rules out floating-point accumulation errors or implementation bugs that could have broken this property in practice.

### Non-Reversibility of Hard Deletion

Hard-deleting masked weights (setting them to zero in the weight matrix) and subsequently setting all mask bits to 1 did not recover the original model. Maximum absolute logit deltas were all greater than 1.0 across all seeds and sparsity levels. This establishes that the reversibility property depends critically on preserving the original weight values; the mask alone cannot undo weight destruction. This is the key asymmetry: masking is reversible, deletion is not.

### Magnitude vs. Random Masks

Magnitude-based masks outperformed random masks at moderate sparsity:

| Sparsity | Magnitude mask acc (mean) | Random mask acc (mean) |
|----------:|-------------------------:|-----------------------:|
| 50%      | 0.8896                   | 0.5563                 |
| 70%      | 0.7185                   | 0.4067                 |
| 85%      | 0.4881                   | 0.3207                 |
| 95%      | 0.3644                   | 0.3600                 |

At 95% sparsity, both magnitude and random masks produced accuracy near chance level (0.333 for 3 classes), indicating that the model's effective capacity is exhausted at this sparsity on this task. The convergence of magnitude and random mask accuracy at 95% sparsity suggests that the remaining 5% of weights, even when selected by magnitude, are insufficient for the task.

### Fine-Tuning Under a Fixed Mask

Fine-tuning surviving weights under a fixed mask partially recovered accuracy:

| Sparsity | Raw magnitude mask acc (mean) | Fine-tuned mask acc (mean) | Reversible unmask acc (mean) |
|----------:|------------------------------:|---------------------------:|-----------------------------:|
| 50%      | 0.8896                        | 0.9926                     | 0.9933                       |
| 70%      | 0.7185                        | 0.9844                     | 0.9933                       |
| 85%      | 0.4881                        | 0.8970                     | 0.9933                       |
| 95%      | 0.3644                        | 0.3430                     | 0.9933                       |

Fine-tuning was effective at moderate sparsity (50% and 70%) and partially effective at 85% sparsity, but failed at 95% sparsity (fine-tuned accuracy 0.343 was actually slightly below raw masked accuracy 0.364, though this difference is small and may not be meaningful given the near-chance baseline). Critically, fine-tuning alters the surviving weights, so unmasking after fine-tuning no longer reproduces the original dense model's behavior. The "reversible unmask acc" column above reflects unmasking the *original* dense weights (pre-fine-tuning), not the fine-tuned weights. This creates a practical design tension: fine-tuning improves sparse performance but breaks exact reversibility unless the original dense checkpoint is separately preserved.

### No Inference Speedup from Dense Masking

Masked forward passes using dense NumPy kernels were not faster than unmasked dense forward passes. The masked-to-dense timing ratio was mean 1.0184 (SD 0.00054), indicating approximately 1.8% overhead rather than any speedup. This is consistent with the NNI documentation's distinction between mask simulation and real speedup: applying a binary mask to dense weights does not reduce computation when using dense kernels, because the masked-out positions are still multiplied (by zero) and accumulated. The small overhead likely reflects the cost of the element-wise mask multiplication itself.

This result falsifies the hypothesis that binary masks alone speed up inference under dense execution. It does not address whether sparse kernels or structured pruning could yield speedup—that would require a separate experimental path with appropriate sparse runtime support.

## Limitations

1. **Synthetic task and small model only.** All experiments used a 3-class synthetic spiral dataset and a two-layer ReLU MLP with hidden dimension 96. No evidence is provided for transformers, CNNs, LLMs, or real-world datasets. The reversibility result is mathematically expected (mask restoration is an identity operation on preserved weights), but the practical implications for large models—including whether floating-point behavior differs at scale—remain untested.

2. **Dense-kernel timing only.** The timing result (1.8% overhead from masking) falsifies the claim that binary masks alone speed up inference under dense kernels, but it does not evaluate sparse kernels, structured pruning, or hardware-aware compaction. Speedup claims would require a separate experimental path with appropriate sparse runtime support. The timing measurement itself is from a toy-scale NumPy implementation and may not reflect production inference framework overhead profiles.

3. **No GPU or hardware-specific evaluation.** All experiments were CPU/NumPy. No GPU utilization experiments were conducted. The memory and timing characteristics on GPU architectures may differ substantially, and GPU sparse-kernel support (e.g., block-sparse operations) was not evaluated.

4. **Fine-tuning breaks exact reversibility.** After fine-tuning under a mask, unmasking does not restore the original dense model. This is an inherent tension: any weight modification under the mask creates a branch. The experiment confirms this but does not evaluate mitigation strategies such as weight delta storage or checkpoint branching.

5. **Global unstructured magnitude pruning only.** The experiment uses global unstructured magnitude pruning. Structured pruning (e.g., channel-level, head-level) may exhibit different accuracy–sparsity tradeoffs and different interactions with reversibility. Structured masks may also interact differently with sparse kernel execution.

6. **Limited sparsity resolution.** Only four sparsity levels were tested (50%, 70%, 85%, 95%). The transition behavior between these points is not characterized, and the exact sparsity at which magnitude and random masks converge may vary by task and model.

7. **Claim audit status.** The claim ledger for this artifact was in a blocked state with no structured claims extracted at the time of draft generation. The claims in this paper are grounded in the aggregate metrics and run notes but have not passed a formal claim/evidence audit pipeline.

## Reproducibility Checklist

- **Code available**: `scripts/reversible_prune_masks_experiment.py`, `scripts/aggregate_reversible_prune_masks.py`
- **Deterministic**: Synthetic spiral dataset is deterministic; seeds are explicitly specified.
- **Seeds reported**: Main run (default seed) and replicates at seeds 11, 17, 23, 31, 43.
- **Dependencies**: Python 3.12.3, NumPy 2.4.4 (no PyTorch or other ML frameworks required).
- **Hardware**: CPU-only, ~122 GB RAM available, no swap. Max RSS ~37.5 MB.
- **Raw metrics files**: `results/smoke_metrics.json`, `results/calibration_metrics.json`, `results/main_metrics.json`, `results/main_seed_11.json`, `results/main_seed_17.json`, `results/main_seed_23.json`, `results/main_seed_31.json`, `results/main_seed_43.json`, `results/aggregate_metrics.json`.
- **Logs**: `logs/*.stdout.log`, `logs/*.stderr.log`, `logs/pip-install-numpy.log`, `logs/pip-upgrade.log`.
- **Commands**: Full command sequences documented in run notes (see Referenced Artifacts).
- **Statistical reporting**: Means and standard deviations reported across 5 replicates.
- **Negative results reported**: No speedup from masking (1.8% overhead); fine-tuning at 95% sparsity did not improve accuracy; hard deletion is not reversible.
- **Experiment tier**: Toy-scale synthetic simulation (NumPy MLP, CPU-only). Not production validation, not CUDA calibration, not llama.cpp hook prototype.

## Conclusion

Reversible prune masks—binary masks applied to preserved dense weights—provide exact logit-level recovery when mask bits are restored to 1. This was confirmed across all tested sparsity levels (50%, 70%, 85%, 95%) and all five random seeds on a synthetic MLP task, with maximum logit delta of exactly 0.0 in every case. The property fails if weights are hard-deleted rather than merely masked (logit deltas > 1.0 in all cases), confirming that reversibility requires weight preservation.

However, reversible prune masks do not provide inference speedup when executed via dense kernels (measured ~1.8% overhead), and they do not provide storage compression (both weights and masks must be retained). Fine-tuning under a mask improves sparse accuracy at moderate sparsity but sacrifices exact reversibility by modifying surviving weights.

These results support reversible prune masks as a **control-plane and audit primitive**—a mechanism for toggling pruning decisions, rolling back to exact dense checkpoints, and auditing sparse subnetwork behavior—rather than as a standalone compression or acceleration technique. The core finding is a separation of concerns: mask semantics provide reversibility; deployment benefits require additional, potentially irreversible steps such as sparse kernel execution, structured compaction, or sidecar storage that can reconstruct dense weights on demand.

Future work should test these findings on transformer blocks and CNNs with real-world datasets, evaluate structured mask variants, benchmark sparse kernel execution paths separately from the reversible mask semantics validated here, and investigate weight-delta or checkpoint-branching strategies that preserve rollback capability after fine-tuning.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `scripts/reversible_prune_masks_experiment.py` |
| Aggregation script | `scripts/aggregate_reversible_prune_masks.py` |
| Autopilot spec | `.omx/plans/autopilot-spec.md` |
| Autopilot plan | `.omx/plans/autopilot-impl.md` |
| Context snapshot | `.omx/context/reversible-prune-masks-20260429T222517Z.md` |
| Smoke metrics | `results/smoke_metrics.json` |
| Calibration metrics | `results/calibration_metrics.json` |
| Main single-run metrics | `results/main_metrics.json` |
| Replicate metrics (seed 11) | `results/main_seed_11.json` |
| Replicate metrics (seed 17) | `results/main_seed_17.json` |
| Replicate metrics (seed 23) | `results/main_seed_23.json` |
| Replicate metrics (seed 31) | `results/main_seed_31.json` |
| Replicate metrics (seed 43) | `results/main_seed_43.json` |
| Aggregate metrics | `results/aggregate_metrics.json` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260429T222448332052+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T222448332052+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T222448332052+0000/paper_manifest.json` |
| Standard output logs | `logs/*.stdout.log` |
| Standard error logs | `logs/*.stderr.log` |
| Pip install log | `logs/pip-install-numpy.log` |
| Pip upgrade log | `logs/pip-upgrade.log` |
