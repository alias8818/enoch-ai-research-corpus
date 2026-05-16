# Per-Row Joint Search over N:M Sparsity and Quantization Bitwidths for Compressed Linear Layers

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, and result files). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review is asserted or implied.

---

## Abstract

We investigate whether a per-row joint search over semi-structured N:M pruning levels and quantization bitwidths can reduce calibration reconstruction error below the best feasible uniform or sequential compress-then-quantize baselines under a shared bits-per-weight budget. Using a NumPy-based post-training proxy for a single linear layer, we enumerate candidate (N:M, bitwidth) configurations per output row, score them by relative mean squared error on synthetic calibration activations, and greedily allocate budgets to minimize total error. Across 12 random seeds with moderate row-scale heterogeneity, the joint selector wins 12/12 comparisons at budgets of 2.0, 2.5, 3.0, and 4.0 bits/weight, yielding mean relative error reductions of 22.9%–42.5%. Under heavier outlier conditions the advantage grows to 37.1%–63.1% (8/8 wins at all budgets). However, when rows are homogeneous and the budget is loose (4.0 bits/weight, no outliers), the joint selector effectively ties the best uniform baseline (−0.1% ± 0.3%; 3/8 wins). These results are limited to a synthetic single-layer proxy; no end-to-end language model perplexity or hardware kernel throughput was measured. The findings suggest that joint N:M sparsity–quantization allocation is a viable research direction, particularly for layers with heterogeneous weight or activation distributions, but the boundary conditions under which the overhead of per-row search is justified remain to be characterized on real models.

## 1. Introduction

Post-training compression of large language models typically applies pruning and quantization in separate stages: weights are first sparsified, then the remaining weights are quantized, or vice versa. This sequential approach treats sparsity level and bitwidth as global hyperparameters, ignoring the possibility that different output channels (rows) of a linear layer may benefit from different trade-offs between sparsity and precision.

Recent work on one-shot LLM pruning has demonstrated that semi-structured N:M sparsity patterns (e.g., 2:4, 4:8) are compatible with weight quantization and can exploit hardware support on modern GPU sparse tensor cores. Concurrently, joint sparsification–quantization methods have been proposed on the grounds that separate compression degrades accuracy at high compression ratios. Prior work on automatic compression for convolutional networks framed per-layer sparsity–bitwidth allocation as constrained optimization, and recent preprints report favorable interactions between low-bit quantization and N:M sparsity.

This paper asks a specific, scoped question: **does a lightweight per-row joint search over N:M sparsity ratios and quantization bitwidths beat the best uniform or sequential baseline under the same compressed bits-per-weight budget, as measured by calibration reconstruction error on a single linear layer?** We deliberately restrict the evaluation to a local, proxy-level objective to determine whether the signal exists before committing to a full model-level implementation.

## 2. Method

### 2.1 Problem Formulation

Consider a linear layer with weight matrix $W \in \mathbb{R}^{R \times C}$ and calibration activations $X \in \mathbb{R}^{S \times C}$, where $R$ is the number of output rows, $C$ the input dimension, and $S$ the number of calibration samples. For each output row $r$, we seek a compressed representation $w_r'$ characterized by a sparsity pattern (N:M, with $M=4$ and $N \in \{1,2,3,4\}$) and a quantization bitwidth $b \in \{2,3,4,6,8\}$.

The cost of a candidate $(N\!:\!M, b)$ for row $r$ is modeled as:

$$\text{cost}(r) = \frac{N}{M} \cdot b + \frac{\log_2 \binom{M}{N}}{M}$$

where the first term captures the bits needed to store the $N$ non-zero values per group of $M$ at bitwidth $b$, and the second term is a lower bound on the sparse-pattern metadata overhead per weight element.

The quality of a candidate is measured by the calibration reconstruction relative MSE:

$$\text{rel-MSE}(r) = \frac{\mathbb{E}[(x_r^\top (w_r - w_r'))^2]}{\mathbb{E}[(x_r^\top w_r)^2]}$$

where expectations are taken over the calibration samples.

### 2.2 Candidate Enumeration

For each output row, all feasible $(N\!:\!M, b)$ pairs are enumerated. Each candidate's compressed weight is constructed by: (1) selecting the $N$ largest-magnitude weights per group of $M$ (magnitude-based N:M pruning), and (2) applying uniform symmetric quantization at bitwidth $b$ to the surviving weights.

### 2.3 Joint Budget Allocation

The joint selector operates as follows:

1. **Initialize**: Assign each row its lowest-error candidate (ignoring budget).
2. **Compute total cost**: Sum per-row costs; if within budget, stop.
3. **Greedy downgrade**: Iteratively replace the current candidate for the row whose downgrade causes the smallest increase in error per bit saved, until the average cost meets the budget constraint.

This greedy procedure is not guaranteed to find the global optimum but is computationally lightweight and provides a practical lower bound on the benefit of joint allocation.

### 2.4 Baselines

For each budget, we evaluate all feasible uniform (same N:M and bitwidth for every row) and sequential (prune-then-quantize, quant-then-prune) compression schemes whose cost does not exceed the budget. The best-performing baseline under each budget is reported as the comparison point.

### 2.5 Synthetic Data Generation

Weight matrices $W$ are generated with controlled row-scale heterogeneity. A base rank-$k$ structure is sampled, and per-row scales are drawn to create variation in row norms. Outliers are injected by rescaling a fraction `outlier_frac` of rows by `outlier_scale`. Calibration activations $X$ are drawn i.i.d. from a standard normal distribution.

Three regimes are tested:

- **Moderate outliers**: `outlier_frac=0.02`, `outlier_scale=4.0`
- **No outliers**: `outlier_frac=0`, `outlier_scale=1`
- **Heavy outliers**: `outlier_frac=0.05`, `outlier_scale=6.0`

## 3. Results

All experiments use $R=192$, $C=256$, $S=512$ calibration samples, and rank $k=64$ for the base weight structure. The prototype is a NumPy-only CPU implementation (peak RSS ~43 MB; no GPU utilization). Results are reported as toy simulation outcomes on a synthetic linear-layer proxy; they do not constitute end-to-end LLM benchmarks, llama.cpp hook-prototype results, CUDA copy calibrations, or production validations.

### 3.1 Moderate Outlier Regime (12 seeds)

Configuration: `outlier_frac=0.02`, `outlier_scale=4.0`.

| Budget (bits/wt) | Joint rel-MSE | Best uniform rel-MSE | Error reduction | Wins |
|---:|---:|---:|---:|---:|
| 2.0 | 0.112445 | 0.146000 | 22.9% ± 1.7% | 12/12 |
| 2.5 | 0.083381 | 0.144992 | 42.5% ± 1.4% | 12/12 |
| 3.0 | 0.061505 | 0.096640 | 36.4% ± 0.7% | 12/12 |
| 4.0 | 0.030540 | 0.047000 | 35.0% ± 1.0% | 12/12 |

The joint selector consistently outperforms the best uniform/sequential baseline at every budget and every seed. The largest relative improvement (42.5%) occurs at 2.5 bits/weight, where uniform baselines are constrained to particularly poor sparsity–bitwidth combinations.

### 3.2 No-Outlier Regime (8 seeds)

Configuration: `outlier_frac=0`, `outlier_scale=1`.

| Budget (bits/wt) | Joint rel-MSE | Best uniform rel-MSE | Error reduction | Wins |
|---:|---:|---:|---:|---:|
| 2.0 | 0.197484 | 0.386275 | 48.9% ± 0.7% | 8/8 |
| 2.5 | 0.118047 | 0.181332 | 34.9% ± 0.7% | 8/8 |
| 3.0 | 0.068690 | 0.089610 | 23.3% ± 1.5% | 8/8 |
| 4.0 | 0.016133 | 0.016124 | −0.1% ± 0.3% | 3/8 |

At tight budgets (2.0–3.0 bits/weight), the joint selector still provides substantial error reductions. However, at 4.0 bits/weight, the advantage vanishes: the mean error reduction is −0.1% (i.e., the uniform baseline is marginally better), and the joint selector wins only 3 of 8 seeds. This is an important boundary condition: when rows are homogeneous and the budget is loose enough that a single uniform configuration is near-optimal for all rows, the overhead of per-row search provides no measurable benefit.

### 3.3 Heavy Outlier Regime (8 seeds)

Configuration: `outlier_frac=0.05`, `outlier_scale=6.0`.

| Budget (bits/wt) | Joint rel-MSE | Best uniform rel-MSE | Error reduction | Wins |
|---:|---:|---:|---:|---:|
| 2.0 | 0.043990 | 0.081064 | 45.7% ± 1.2% | 8/8 |
| 2.5 | 0.029618 | 0.080355 | 63.1% ± 1.0% | 8/8 |
| 3.0 | 0.019653 | 0.042261 | 53.5% ± 1.5% | 8/8 |
| 4.0 | 0.008706 | 0.013871 | 37.1% ± 3.3% | 8/8 |

The joint selector's advantage increases with outlier severity, consistent with the intuition that heterogeneous rows benefit most from per-row allocation. The 63.1% error reduction at 2.5 bits/weight is the largest observed across all regimes. The higher standard error at 4.0 bits/weight (±3.3%) reflects greater seed-to-seed variability in this regime.

### 3.4 Allocation Patterns

The smoke-test single-seed run ($R=32$, $C=64$, `outlier_frac=0.02`, `outlier_scale=4.0`) provides a detailed histogram of the joint selector's per-row choices. At budget 2.0 bits/weight, the selector distributes rows across configurations including 1:4@2b (2 rows), 1:4@3b (4), 1:4@4b (10), 2:4@2b (1), 2:4@3b (5), 2:4@4b (3), 3:4@3b (3), and 4:4@3b (4) — confirming that the joint search exploits a diverse set of sparsity–bitwidth trade-offs rather than collapsing to a single uniform configuration. At budget 4.0 bits/weight, the distribution shifts toward denser, higher-bitwidth configurations (e.g., 4:4@4b, 3:4@6b, 2:4@6b), as expected when the budget constraint is relaxed.

## 4. Limitations

1. **Synthetic proxy only.** All experiments use a NumPy-based single linear layer with synthetic weights and activations. No real transformer weights, real calibration data, or end-to-end language model was evaluated. Reconstruction error on a proxy layer does not directly predict perplexity or downstream task performance.

2. **No end-to-end LLM evaluation.** The project environment did not have PyTorch or a HuggingFace Transformers stack installed at experiment time. No perplexity measurements on any language model were performed.

3. **No hardware kernel validation.** No sparse Tensor Core kernels were run or benchmarked. The cost model assumes that N:M sparsity patterns map to hardware-supported formats, but actual GB10 sparse-kernel throughput was not measured. Storage and error viability are the only validated claims.

4. **Simplified metadata cost model.** The sparse-pattern metadata cost uses a $\log_2 \binom{M}{N} / M$ lower bound. Production formats may have different overhead due to alignment, padding, or indexing structures.

5. **Greedy allocation suboptimality.** The joint selector uses a greedy per-row downgrade procedure. It is not guaranteed to find the global optimum under the budget constraint, so the reported gains are a lower bound on what a more sophisticated optimizer might achieve.

6. **Magnitude-based pruning only.** The N:M pruning within each candidate uses magnitude-based selection (largest absolute values retained). More sophisticated pruning criteria (e.g., Hessian-based, activation-aware) may change the error landscape and the relative advantage of joint search.

7. **Uniform quantization only.** Only symmetric uniform quantization was tested. The interaction of joint N:M search with more advanced quantization schemes (e.g., affine, group-quantized, floating-point) is unexplored.

8. **Boundary condition at loose budgets with homogeneous rows.** The no-outlier, 4.0 bits/weight condition shows that joint search can be neutral or slightly harmful when a single uniform configuration is already near-optimal. The conditions under which the search overhead is justified in practice require further characterization.

## 5. Reproducibility Checklist

- **Code**: `experiments/nm_quant_prune_search.py` (NumPy-only, no GPU required)
- **Python version**: 3.12.3, NumPy 2.4.4
- **Hardware**: GB10-class NVIDIA system (CPU-only execution; GPU utilization 0%)
- **Memory**: Peak RSS ~43 MB; system had ~122.6 GB available
- **Random seeds**: Explicitly controlled via `--seeds` flag; 12 seeds for main experiment, 8 for each sensitivity condition
- **Smoke test**: Passed before main experiment
- **Exact reproduction commands**:

```bash
# Smoke test
python3 experiments/nm_quant_prune_search.py --seeds 1 --rows 32 --cols 64 --samples 128 --rank 16 --out results/smoke.json

# Main experiment (moderate outliers, 12 seeds)
python3 experiments/nm_quant_prune_search.py --seeds 12 --rows 192 --cols 256 --samples 512 --rank 64 --budgets 2.0 2.5 3.0 4.0 --out results/nm_quant_prune_search_main.json

# No-outlier sensitivity (8 seeds)
python3 experiments/nm_quant_prune_search.py --seeds 8 --rows 192 --cols 256 --samples 512 --rank 64 --budgets 2.0 2.5 3.0 4.0 --outlier-frac 0 --outlier-scale 1 --out results/nm_quant_prune_search_no_outliers.json

# Heavy-outlier sensitivity (8 seeds)
python3 experiments/nm_quant_prune_search.py --seeds 8 --rows 192 --cols 256 --samples 512 --rank 64 --budgets 2.0 2.5 3.0 4.0 --outlier-frac 0.05 --outlier-scale 6 --out results/nm_quant_prune_search_heavy_outliers.json
```

- **Result files**: `results/smoke.json`, `results/nm_quant_prune_search_main.json`, `results/nm_quant_prune_search_no_outliers.json`, `results/nm_quant_prune_search_heavy_outliers.json`
- **Logs**: `.omx/logs/env_probe_20260430T120644.log`, `.omx/logs/smoke_20260430T120759.log`, `.omx/logs/main_experiment_20260430T120805.log`, `.omx/logs/sensitivity_20260430T120826.log`

## 6. Conclusion

A per-row joint search over N:M sparsity levels and quantization bitwidths consistently reduces calibration reconstruction error relative to the best feasible uniform or sequential baseline in a synthetic linear-layer proxy, with mean error reductions of 22.9%–42.5% under moderate row heterogeneity and up to 63.1% under heavy outlier conditions. The advantage is most pronounced at tight compression budgets and in the presence of row-scale heterogeneity, where uniform configurations are forced into poor sparsity–bitwidth trade-offs.

However, the advantage is not universal: when rows are homogeneous and the budget is loose (4.0 bits/weight, no outliers), the joint selector offers no measurable benefit and is marginally worse than the best uniform baseline (−0.1% ± 0.3%; 3/8 wins). This boundary condition tempers the scope of the claim and suggests that practical deployments should consider whether a given layer's weight and activation distributions exhibit sufficient heterogeneity to justify per-row search overhead.

These results establish that the local compression objective carries enough signal to warrant investigation at model scale. The necessary next steps are: (1) porting the joint selector to real transformer linear modules with actual calibration activations, (2) evaluating perplexity on open language models, and (3) benchmarking sparse quantized kernels on GB10-class hardware to validate the assumed throughput benefits of N:M patterns. Until those steps are completed, the present findings remain proxy-level evidence that joint N:M sparsity–quantization allocation is a promising but not yet validated compression strategy.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `experiments/nm_quant_prune_search.py` |
| Main results (moderate outliers) | `results/nm_quant_prune_search_main.json` |
| No-outlier sensitivity results | `results/nm_quant_prune_search_no_outliers.json` |
| Heavy-outlier sensitivity results | `results/nm_quant_prune_search_heavy_outliers.json` |
| Smoke test results | `results/smoke.json` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260430T170608367444+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T170608367444+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T170608367444+0000/paper_manifest.json` |
| Environment probe log | `.omx/logs/env_probe_20260430T120644.log` |
| Smoke test log | `.omx/logs/smoke_20260430T120759.log` |
| Main experiment log | `.omx/logs/main_experiment_20260430T120805.log` |
| Sensitivity runs log | `.omx/logs/sensitivity_20260430T120826.log` |
