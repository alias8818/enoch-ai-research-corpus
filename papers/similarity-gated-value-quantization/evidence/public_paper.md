# Similarity-Gated Value Quantization: An Error-Control Mechanism for Attention Value Caches

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run logs, experiment JSON outputs, and a project decision record). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether query–key similarity can gate value-cache quantization in transformer attention, retaining high-precision values only for tokens receiving high attention and quantizing the remainder. In a model-free synthetic attention setting (2,048 tokens, dimension 128, 10 seeds, four attention regimes), a dynamic per-query similarity gate that keeps 10% of value vectors in full precision reduces output error relative to uniform int4 quantization by a factor of 1.02–1.86× when attention is diffuse (normalized entropy ≥ 0.95), 1.74–5.92× at medium entropy, and 4.4–17,396× when attention is peaked (entropy < 0.70). However, a static calibration-based salience policy—the variant closest to a deployable cache compression scheme—yields only 1.04–1.14× improvement on clustered queries and collapses to near parity (1.00×) under query distribution shift. These results confirm that similarity-gated value quantization is a real error-control mechanism when attention is peaked, but the currently tested deployable static-cache version does not reliably convert this mechanism into a general memory-saving policy. End-to-end validation on real transformer KV traces and perplexity metrics remains necessary.

## Introduction

Quantizing the key-value (KV) cache is a common strategy for reducing memory pressure during transformer inference. Uniform quantization of value vectors introduces error proportional to the quantization noise on each value, weighted by the attention probabilities. When attention is peaked—concentrating mass on a small subset of tokens—quantization error on low-attention tokens contributes little to the output, while error on high-attention tokens dominates. This asymmetry suggests a mixed-precision strategy: retain full-precision values for tokens likely to receive high attention and quantize the rest.

The core question is whether this asymmetry can be exploited effectively. Two sub-problems arise:

1. **Mechanism:** Does keeping high-attention value vectors exact while quantizing low-attention ones substantially reduce output error compared to uniform quantization?
2. **Deployability:** Can a practical cache policy predict which tokens will receive high attention from future queries, so that only those values need to be stored at full precision?

We decompose the investigation by testing four policies of increasing specificity: uniform int4 quantization (baseline), random mixed precision (ablation), static calibration-based salience selection (deployable candidate), and dynamic per-query similarity gating (upper-bound mechanism probe). We evaluate across synthetic attention regimes that span diffuse to peaked attention distributions, measuring relative L2 output error and its relationship to attention entropy.

## Method

### Problem Formulation

Given query vector $q$, key matrix $K$, and value matrix $V$, the standard attention output is:

$$y = \text{softmax}(q K^T) V$$

We quantize each value vector $v_i$ to symmetric int4 with a per-vector scale $s_i$:

$$\hat{v}_i = s_i \cdot \text{round}(v_i / s_i)$$

where $s_i = \max(|v_i|) / 7$ (for 4-bit symmetric range $[-7, 7]$). The quantized output is:

$$\hat{y} = \text{softmax}(q K^T) \hat{V}$$

The relative L2 error is $\|y - \hat{y}\|_2 / \|y\|_2$.

### Policies

We compare four policies for selecting which value vectors remain at full precision (fp16), with the remainder quantized to int4:

1. **All-int4 (baseline):** Quantize all value vectors. No mixed precision.
2. **Random mixed precision:** Keep a fixed fraction `exact_frac` of value vectors at full precision, chosen uniformly at random. This serves as an ablation controlling for the effect of simply retaining some exact values.
3. **Static calibration salience:** On a calibration set of queries, compute the maximum attention weight each token receives across all calibration queries. Keep the top `exact_frac` tokens by this salience score at full precision; quantize the rest. This policy is determined before evaluation and does not change per query, making it compatible with a deployable cache that stores only the predicted-salient values at full precision.
4. **Dynamic similarity gate:** For each evaluation query, compute $q \cdot k_i$ for all keys, keep the top `exact_frac` by current similarity at full precision, and quantize the rest. This is an upper-bound probe: it assumes the system has access to exact values for whichever tokens the current query selects, which may require storing both exact and quantized copies or a perfect prediction mechanism.

### Synthetic Attention Regimes

To span a range of attention concentration levels, we generate key and query vectors under four regimes:

- **Random:** Keys and queries drawn i.i.d. from a standard normal distribution, scaled by a logit scale factor.
- **Clustered:** Keys drawn from a small number of clusters; queries drawn from the same cluster centers plus noise. Produces peaked attention at high logit scales.
- **Shifted:** Calibration queries drawn from one cluster structure; evaluation queries drawn from a different cluster structure. Tests robustness of static salience to distribution shift.
- **Flat:** Keys and queries drawn to produce near-uniform attention (low logit scale). Produces diffuse attention.

Logit scale controls the sharpness of the softmax: scale 1 yields near-uniform attention; scale 16 yields highly peaked attention.

### Experimental Configuration

| Parameter | Value |
|---|---|
| Sequence length | 2,048 tokens |
| Dimension | 128 |
| Calibration queries | 128 |
| Evaluation queries | 256 |
| Seeds | 10 |
| Quantization bits | 4 (symmetric int4) |
| Exact fractions | 0.02, 0.05, 0.10, 0.20 |
| Logit scales | 1, 4, 8, 16, 32 |
| Regimes | random, clustered, shifted, flat |

This yields 4 × 5 × 4 × 10 = 800 experimental rows. The primary analysis focuses on `exact_frac = 0.10`, which provides approximately 3.01× compression versus a full fp16 value cache (mixed bytes per token: 22.6 vs. 64.0 for fp16).

### Metric

The primary metric is the relative L2 error of the attention output, averaged over evaluation queries and seeds. Improvement ratios are computed as the baseline (all-int4) error divided by the policy error, so values greater than 1 indicate error reduction.

### Compute Environment

All experiments ran on an aarch64 host (Linux 6.17.0, Python 3.12.3, NumPy) with 20 CPU cores and 121 GiB RAM, swap disabled. The full grid completed in 84.88 seconds at 9.43 rows/s with peak RSS of 64,088 KiB. Available memory remained at approximately 117 GiB throughout. These are CPU-only NumPy simulations; no GPU, CUDA, or llama.cpp implementations were involved.

## Results

### Dynamic Similarity Gate: Strong Dependence on Attention Entropy

The dynamic similarity gate's improvement over uniform int4 quantization varies dramatically with attention concentration:

| Entropy bucket | Normalized entropy range | Mean dynamic improvement | Range |
|---|---|---|---|
| Flat-ish | H ≥ 0.95 | 1.23× | 1.02–1.86× |
| Medium | 0.70 ≤ H < 0.95 | 3.32× | 1.74–5.92× |
| Peaked | H < 0.70 | 1,935× | 4.42–17,396× |

The extremely large improvements in the peaked regime occur because the top 10% of tokens by similarity carry nearly all attention mass (e.g., 0.909 at logit scale 16 in the clustered regime), so keeping their values exact drives output error close to zero. These large ratios should be interpreted with caution: they reflect that the dynamic gate nearly eliminates error in peaked regimes, not that the baseline error itself is large.

Representative rows at `exact_frac = 0.10`:

| Regime | Logit scale | Norm. entropy | Top-10% attn mass | All-int4 rel L2 | Dynamic rel L2 | Dynamic improvement |
|---|---:|---:|---:|---:|---:|---:|
| clustered | 1 | 0.999 | 0.126 | 0.0422 | 0.0388 | 1.09× |
| clustered | 8 | 0.900 | 0.501 | 0.0436 | 0.0127 | 3.43× |
| clustered | 16 | 0.643 | 0.909 | 0.0576 | 0.0015 | 37.97× |
| shifted | 16 | 0.643 | 0.909 | 0.0567 | 0.0015 | 37.87× |
| flat | 4 | 0.992 | 0.177 | 0.1057 | 0.0899 | 1.18× |
| flat | 16 | 0.872 | 0.548 | 0.0879 | 0.0240 | 3.67× |

The dynamic gate's benefit scales with the fraction of attention mass captured by the exact subset, which in turn depends on entropy. When entropy is high and attention mass is spread across many tokens, the 10% exact subset captures little mass and the gate provides marginal benefit.

### Static Calibration Salience: Modest and Fragile

The static salience policy, which selects the exact subset based on calibration queries, shows substantially weaker improvement:

| Regime | Mean static improvement | Notes |
|---|---|---|
| clustered | 1.14× | Max 1.52×; benefits from calibration–eval alignment |
| random / flat | ~1.05× | Marginal over all-int4 |
| shifted | 1.02× | Min ~1.00×; calibration salience collapses under distribution shift |

At `exact_frac = 0.10` in the clustered regime, static salience achieves 1.06–1.18× improvement depending on logit scale. Under the shifted regime, the calibration-derived salience ranking is uncorrelated with the evaluation queries' attention pattern, reducing improvement to parity with all-int4. This is the most consequential negative result: the deployable variant of the approach fails precisely when the query distribution at inference differs from calibration.

### Random Mixed Precision

Random selection of the exact subset provides negligible improvement over all-int4 (typically 1.00–1.07×), confirming that the benefit of similarity gating is not an artifact of simply retaining some exact values but depends on which values are retained.

### Compression Trade-off

At `exact_frac = 0.10`, the mixed-precision cache uses 22.6 bytes per token versus 64.0 for fp16 (3.01× compression) and 18.0 for all-int4 (3.56× compression). The 0.55× compression gap between mixed precision and all-int4 is the cost of retaining the exact subset; the error reduction must justify this cost. For the static policy, where mean improvement is 1.02–1.14×, this compression cost is difficult to justify. For the dynamic gate in peaked regimes, the error reduction is substantial but the gate itself is not deployable without solving the prediction problem.

## Limitations

1. **Model-free synthetic setting.** All experiments use synthetic query, key, and value vectors. No real transformer's KV cache, attention patterns, perplexity, or downstream task metrics were measured. The attention regimes are designed to span a range of concentration levels but do not reflect the distribution of entropies across layers, heads, and tokens in actual language models.

2. **Dynamic gate is an upper bound, not a deployable design.** The dynamic similarity gate assumes exact values are available for whichever tokens the current query selects. If the system stores both exact and quantized copies for all tokens, memory savings vanish. If it stores exact values only for a predicted subset, the prediction problem becomes the core risk and is not addressed here.

3. **Static salience is the deployable candidate and is weak.** The static calibration-based policy is the variant closest to a practical cache compression scheme, but it provides only modest error reduction and fails under distribution shift. We do not have evidence that a more sophisticated static or adaptive policy would close this gap.

4. **Single quantization scheme.** Only symmetric per-vector int4 quantization was tested. Other schemes (per-group, asymmetric, 2-bit or 8-bit) may change the error landscape and the relative benefit of gating.

5. **No latency or throughput measurement.** The experiments measure only output error. Any real deployment must also account for the overhead of maintaining mixed-precision caches, the cost of salience prediction, and the impact on decode-step latency.

6. **Limited sequence length and dimension.** Experiments use 2,048 tokens and dimension 128. Longer contexts and higher dimensions may exhibit different attention concentration properties.

7. **No real-model validation.** No GPU/CUDA implementation, no llama.cpp hook prototype, and no production validation were performed. Results are CPU-only NumPy simulations of isolated attention operations.

## Reproducibility Checklist

- [x] Experiment script available: `experiments/svq_experiment.py`
- [x] Full command lines recorded in run notes
- [x] Random seeds explicitly set (10 seeds per configuration)
- [x] Hardware and software environment specified (aarch64, Linux 6.17.0, Python 3.12.3, NumPy)
- [x] Peak memory usage recorded (64,088 KiB RSS)
- [x] All parameter ranges specified (tokens, dim, exact fractions, logit scales, regimes, seeds)
- [x] Raw results files preserved (`results/smoke.json`, `results/calibrate.json`, `results/full_grid.json`, `results/metrics_summary.json`, `results/selected_exact_frac_0_10.csv`)
- [x] Run logs preserved (`logs/smoke.log`, `logs/calibration.log`, `logs/full_run.log`)
- [ ] No real-model KV traces or perplexity benchmarks included
- [ ] No GPU/CUDA implementation; CPU-only NumPy simulation

## Conclusion

Similarity-gated value quantization is a real error-control mechanism: when attention is peaked, retaining full-precision values for the small subset of tokens that carry most attention mass reduces output error by orders of magnitude compared to uniform int4 quantization. However, this mechanism's strength is tightly coupled to attention entropy, and it provides only marginal benefit (mean 1.23× error reduction) when attention is diffuse.

The critical gap is between mechanism and deployability. The dynamic per-query gate that demonstrates the largest improvements is an upper bound that assumes runtime access to exact values for the currently-attended subset. The static calibration-based policy—the variant compatible with a memory-saving cache design—provides only modest improvements (mean 1.14× on aligned distributions) and collapses under query distribution shift (mean 1.02×). Converting the mechanism into a robust cache compression policy requires solving the prediction problem: identifying, before inference, which tokens will receive high attention from future queries, and storing only those values at full precision.

These results do not support a claim of general KV-cache compression gains. They do motivate further investigation with real transformer attention traces, where the distribution of attention entropy across layers and heads may reveal opportunities for targeted mixed-precision caching that the synthetic averages obscure. A deployable design that stores fp16 values only for tokens predicted to receive high future attention, evaluated on end-to-end perplexity and memory metrics, is the necessary next step.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `experiments/svq_experiment.py` |
| Smoke test results | `results/smoke.json` |
| Smoke test log | `logs/smoke.log` |
| Calibration results | `results/calibrate.json` |
| Calibration log | `logs/calibrate.log` |
| Full grid results | `results/full_grid.json` |
| Full grid run log | `logs/full_run.log` |
| Metrics summary | `results/metrics_summary.json` |
| Selected metrics CSV (exact_frac=0.10) | `results/selected_exact_frac_0_10.csv` |
| Run notes | `run_notes.md` |
| Project decision record | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260428T223248262659+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260428T223248262659+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260428T223248262659+0000/paper_manifest.json` |
