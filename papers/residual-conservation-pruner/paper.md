# Residual Conservation Pruning: Structured Pruning via Residual-Update Preservation

> **AI Provenance Notice:** This draft was generated entirely by an automated AI research pipeline from prototype artifacts, run logs, and decision records. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

We investigate Residual Conservation Pruning (RCP), a structured pruning criterion that selects weights to remove by minimizing disruption to the residual update within residual connections. On a controlled NumPy residual MLP (3 residual blocks, 48 residual-branch units per block) evaluated on synthetic 3-class spiral classification across 20 random seeds with no post-prune fine-tuning, RCP achieves the lowest residual conservation error at all tested sparsity levels (25%, 50%, 75%). At 25% pruning, RCP preserves accuracy best (mean accuracy drop 2.26 percentage points versus 3.19 for magnitude pruning and 18.22 for random). At 50% pruning, RCP and magnitude pruning perform comparably on accuracy (mean drops of 20.08 and 20.20 points respectively), though RCP maintains substantially lower residual conservation error. At 75% pruning, magnitude pruning outperforms RCP on accuracy (mean drop 36.66 versus 42.09 points), revealing that residual conservation alone is an insufficient criterion at high sparsity. These results characterize RCP as a viable low-to-moderate sparsity strategy that should be combined with loss-aware or sensitivity-based terms for aggressive compression regimes.

## Introduction

Structured pruning of neural networks seeks to remove parameters while preserving task performance. Classical approaches rank weights by magnitude or by estimated impact on the loss function. In architectures with residual connections—where a skip pathway carries information forward—the residual branch's contribution to the output is the *update* it adds to the skip stream. Pruning weights that contribute heavily to this update risks collapsing the residual pathway toward the identity function, potentially discarding learned features.

The Residual Conservation Pruner (RCP) proposes a pruning criterion that explicitly minimizes the squared error between the pre-prune and post-prune residual updates. Rather than selecting weights by magnitude alone, RCP ranks candidate pruning targets by how much they would distort the residual update vector, preferring to remove weights whose contribution can be absorbed with minimal disruption.

This paper presents empirical evidence for RCP on a toy residual MLP, reporting both its advantages at low-to-moderate sparsity and its limitations at high sparsity. The evidence is drawn from a controlled NumPy simulation and does not constitute validation on production-scale architectures.

## Method

### Problem Formulation

Consider a residual block with input $x$, residual branch function $\mathcal{F}(x)$, and output $y = x + \mathcal{F}(x)$. The residual update is $r = \mathcal{F}(x)$. When a subset of weights $W_p$ is pruned (set to zero), the post-prune residual update becomes $r' = \mathcal{F}_{\setminus W_p}(x)$. The Residual Conservation Error (RCE) for a pruning decision is:

$$\text{RCE} = \|r - r'\|_2^2$$

RCP selects weights to prune that minimize this quantity, subject to a target sparsity constraint.

### Pruning Criterion

For a linear layer within the residual branch, $z = Wx + b$, pruning weight $w_{ij}$ changes the output by $\Delta z_k = -w_{ij} x_j$ if $k = i$. The contribution of weight $w_{ij}$ to RCE, under a first-order approximation with fixed activations, is proportional to $w_{ij}^2 \cdot \mathbb{E}[x_j^2]$. RCP therefore ranks weights by this scaled magnitude, pruning those with the smallest contribution to the residual update norm.

### Baselines

Two baselines were compared:

- **Magnitude pruning**: Prunes weights with the smallest absolute value $|w_{ij}|$, ignoring activation statistics.
- **Random pruning**: Prunes a random subset of weights of the target size, providing a lower-bound reference.

### Experimental Setup

All experiments used a pure-NumPy implementation (no PyTorch or sklearn dependencies) consisting of:

- **Architecture**: Residual MLP with 3 residual blocks, each containing a residual branch of 48 hidden units with ReLU activation and a skip connection.
- **Task**: Synthetic 3-class spiral classification, a nonlinear boundary problem requiring the residual branches to learn nontrivial feature transformations.
- **Training**: Full training to convergence before pruning.
- **Pruning**: One-shot structured pruning at 25%, 50%, and 75% sparsity of residual-branch weights, with **no post-prune fine-tuning**. This design isolates the immediate damage of each pruning criterion.
- **Evaluation**: 20 independent seeds controlling data generation, initialization, and training. Mean accuracy and mean RCE are reported across seeds.
- **Hardware**: Single machine; smoke test confirmed max RSS of 43,996 KB with no swap usage.

This is a toy simulation, not a production validation. The NumPy MLP differs substantially from transformer residual streams in scale, attention mechanisms, and layer normalization behavior.

## Results

### Baseline Performance

The unpruned model achieves a mean accuracy of 0.9910 across 20 seeds, confirming that the residual MLP learns the spiral task effectively.

### Accuracy After Pruning

| Sparsity | RCP Acc. Drop | Magnitude Acc. Drop | Random Acc. Drop |
|----------|--------------|--------------------|--------------------|
| 25%      | 0.0226       | 0.0319             | 0.1822             |
| 50%      | 0.2008       | 0.2020             | 0.3121             |
| 75%      | 0.4209       | 0.3666             | 0.4307             |

At 25% sparsity, RCP preserves accuracy better than both baselines, with an accuracy drop of 2.26 percentage points compared to 3.19 for magnitude pruning. At 50% sparsity, RCP and magnitude pruning are nearly indistinguishable on accuracy (difference of 0.12 percentage points). At 75% sparsity, magnitude pruning outperforms RCP by 5.43 percentage points—a negative result for RCP at aggressive compression.

### Residual Conservation Error

| Sparsity | RCP RCE  | Magnitude RCE | Random RCE |
|----------|----------|---------------|------------|
| 25%      | 0.00326  | 0.01034       | 0.08155    |
| 50%      | 0.02959  | 0.05836       | 0.22590    |
| 75%      | 0.13540  | 0.21804       | 0.40098    |

RCP achieves the lowest residual conservation error at every sparsity level, confirming that the criterion successfully minimizes its stated objective. The gap between RCP and magnitude pruning widens with sparsity: at 75%, RCP's RCE is approximately 38% lower than magnitude pruning's. However, this conservation advantage does not translate to an accuracy advantage at 75%, indicating that low RCE is necessary but not sufficient for accuracy preservation at high sparsity.

### Summary of Findings

1. **RCP is accuracy-competitive at low-to-moderate sparsity** (25–50%), with a clear advantage at 25% and parity at 50%.
2. **RCP consistently minimizes residual conservation error**, validating the mechanism even when accuracy diverges.
3. **RCP underperforms magnitude pruning at 75% sparsity**, demonstrating that residual conservation alone is an insufficient accuracy criterion at high compression.
4. **All structured pruning methods degrade sharply between 50% and 75% sparsity** without fine-tuning, with accuracy dropping below 63% for all methods.

## Limitations

1. **Toy architecture evidence only.** The residual MLP with 3 blocks and 48 units per block is a controlled testbed, not a production model. These results do not demonstrate performance on transformer residual streams, large-scale attention blocks, or LLM-scale architectures. The spiral classification task, while requiring nonlinear residual features, is far simpler than natural language or vision benchmarks.

2. **No post-prune fine-tuning.** All results measure immediate pruning damage only. In practice, fine-tuning after pruning can recover substantial accuracy. The relative ranking of RCP versus magnitude pruning may change with fine-tuning, but this was not tested.

3. **Conservation does not imply accuracy at high sparsity.** RCP optimizes residual-update conservation, which is a proxy for feature preservation, not a direct loss-aware or class-boundary sensitivity criterion. At 75% sparsity, this proxy breaks down: magnitude pruning, which also does not optimize for the loss directly, happens to preserve accuracy better. This suggests that at high sparsity, the residual update is no longer the dominant factor in accuracy preservation—perhaps because the remaining capacity is so constrained that the structure of what is preserved matters more than minimizing total disruption.

4. **First-order approximation.** The RCP ranking assumes fixed activations and ignores higher-order interactions between pruned weights. When many weights are pruned simultaneously, the cumulative error may violate the first-order assumption.

5. **Single task and architecture.** Results are specific to one synthetic task and one architecture configuration. Generalization to other residual architectures, deeper networks, or real-world tasks is untested.

6. **Incomplete statistical reporting.** Only mean values across seeds are reported in the decision record. Per-seed standard deviations and paired statistical tests are available in the raw CSV artifacts but are not summarized in this draft, limiting the strength of comparative claims.

## Reproducibility Checklist

- [x] **Code available**: Experiment script at `scripts/residual_conservation_pruner.py`
- [x] **Syntax-verified**: Passed `python -m py_compile` check
- [x] **Smoke test passed**: Baseline accuracy 0.94495 on seed 0; max RSS 43,996 KB; no swap
- [x] **Full run completed**: 20 seeds, all three sparsity levels, all three methods
- [x] **Metrics archived**: JSON metrics at `results/rcp_full_metrics.json`; CSV rows at `results/rcp_full_rows.csv`
- [x] **Summary tables archived**: `results/rcp_summary.csv`; `results/rcp_paired_comparisons.csv`
- [x] **Run logs preserved**: `logs/smoke.stdout.log`, `logs/smoke.time.log`, `logs/full_20seeds.stdout.log`, `logs/full_20seeds.time.log`
- [x] **No external dependencies beyond NumPy**: Install-free execution confirmed
- [x] **Random seeds controlled**: 20 independent seeds specified via `--seeds 20`
- [x] **Decision record preserved**: `.omx/project_decision.json` with full evidence bundle
- [ ] **Paired statistical tests**: Paired comparisons file exists (`results/rcp_paired_comparisons.csv`) but detailed test statistics are not extracted in this draft
- [ ] **Standard deviation reported**: Only means are reported in the decision JSON; per-seed variance is available in the CSV but not summarized here

## Conclusion

Residual Conservation Pruning successfully minimizes disruption to the residual update in a controlled residual MLP, achieving the lowest residual conservation error at all tested sparsity levels. At 25% pruning, this translates to a meaningful accuracy advantage over magnitude and random pruning. At 50% pruning, RCP and magnitude pruning perform comparably on accuracy despite RCP's lower conservation error. At 75% pruning, magnitude pruning outperforms RCP on accuracy, revealing that residual conservation is a necessary but insufficient criterion for high-sparsity regimes.

These findings support using RCP as a conservative pruning pre-filter at low-to-moderate sparsity, particularly in architectures where preserving the residual stream's learned transformations is important. For aggressive compression, RCP should be combined with a loss-aware, Hessian-based, or classifier-sensitivity term rather than used as a standalone criterion. Validation on transformer residual streams with real-world tasks and post-prune fine-tuning remains essential before drawing conclusions about LLM-scale applicability.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Experiment script | `scripts/residual_conservation_pruner.py` |
| Smoke test stdout | `logs/smoke.stdout.log` |
| Smoke test resource log | `logs/smoke.time.log` |
| Full run stdout | `logs/full_20seeds.stdout.log` |
| Full run resource log | `logs/full_20seeds.time.log` |
| Full metrics (JSON) | `results/rcp_full_metrics.json` |
| Full per-seed rows (CSV) | `results/rcp_full_rows.csv` |
| Summary table (CSV) | `results/rcp_summary.csv` |
| Paired comparisons (CSV) | `results/rcp_paired_comparisons.csv` |
| Research report | `results/research_report.md` |
| Project decision record | `.omx/project_decision.json` |
| Context snapshot | `.omx/context/` |
