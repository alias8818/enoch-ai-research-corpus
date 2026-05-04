# Prefix Reuse Consistency Loss: A Diagnostic Metric for KV-Cache Correctness

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

Key-value (KV) cache reuse for shared prefixes is a common optimization in transformer inference, but incorrect cache state—due to position encoding errors, wrong prefix content, or lossy storage—can silently corrupt downstream token distributions without causing a crash. We propose Prefix Reuse Consistency Loss (PRCL), defined as the mean KL divergence in nats between next-token distributions produced by full recomputation and by prefix-cache reuse over suffix positions. In a deterministic NumPy transformer harness, correct prefix reuse yields PRCL of exactly zero across all tested configurations, while injected defects produce measurable drift: position-reset errors yield mean PRCL of 0.225 nats with 52.7% top-1 disagreement, a subtler +1 position offset yields 0.027 nats with 17.5% disagreement, wrong-prefix-content reuse yields 0.834 nats with 82.1% disagreement, and int8-like quantized cache storage yields 5.21 × 10⁻⁵ nats with 1.8% disagreement. These results are reproducible across random seeds. PRCL is viable as a local regression and acceptance metric for prefix-cache implementations, though validation on production inference runtimes remains necessary future work.

## Introduction

Transformer inference engines commonly cache key-value pairs from previously processed tokens to avoid redundant computation. When multiple requests share a common prefix—for example, a system prompt—the cached KV pairs for that prefix can be reused, with only the suffix tokens requiring fresh forward passes. This optimization is standard in serving frameworks.

Several classes of implementation defects can corrupt the reused cache state:

1. **Position encoding errors.** Rotary position embeddings (RoPE) and other positional schemes require that cached positions align correctly with the suffix's position offsets. A common bug is resetting suffix positions to zero rather than continuing from the prefix length, or introducing off-by-one errors.

2. **Wrong prefix content.** Reusing a cache that was computed for a different prefix sequence produces key-value pairs that are semantically unrelated to the current input.

3. **Lossy cache storage.** Quantized or compressed cache representations introduce rounding errors that propagate through subsequent layers.

Such defects are difficult to detect in production because the model still produces plausible-looking outputs; the corruption is a distributional shift rather than a crash or an obvious error signal. We propose a direct diagnostic: compare the token distributions produced by prefix-cache reuse against those produced by full recomputation, and measure the divergence. Under correct implementation, these distributions should be identical up to floating-point precision. Under defective implementations, the divergence should be measurable.

This paper introduces PRCL, reports its behavior under controlled defect injection in a deterministic toy transformer, and discusses its applicability and limitations. We emphasize at the outset that all experiments are conducted on a small NumPy-based transformer harness; this is a proof-of-concept calibration, not a production validation.

## Method

### Metric Definition

Let $p_{\text{full}}(x_t \mid x_{<t})$ denote the next-token distribution at suffix position $t$ produced by full recomputation (no cache reuse), and $p_{\text{cache}}(x_t \mid x_{<t})$ denote the corresponding distribution produced by prefix-cache reuse. The **Prefix Reuse Consistency Loss** is:

$$\text{PRCL} = \frac{1}{|S|} \sum_{t \in S} D_{\text{KL}}\!\left(p_{\text{full}}(\cdot \mid x_{<t}) \;\|\; p_{\text{cache}}(\cdot \mid x_{<t})\right)$$

where $S$ is the set of suffix positions and $D_{\text{KL}}$ is the KL divergence in nats. PRCL is zero if and only if the two distributions are identical at every suffix position.

### Supporting Metrics

We additionally report:

- **Max absolute logit delta:** the largest element-wise difference between the logit vectors of the two paths.
- **Mean absolute logit delta:** the average element-wise absolute logit difference across suffix positions.
- **Top-1 disagreement rate:** the fraction of suffix positions where the argmax token differs between the two paths.
- **Teacher-forced NLL delta:** the difference in negative log-likelihood (under the full-recomputation distribution) of the true suffix tokens, computed for both paths. This metric is noisy for random token sequences and is treated as secondary.

### Defect Injection Modes

We test five modes:

| Mode | Description |
|------|-------------|
| `correct` | Prefix cache is populated with the correct prefix tokens at the correct positions. |
| `position_plus_one` | Suffix positions are offset by +1 relative to the correct continuation. |
| `position_reset` | Suffix positions restart from 0 instead of continuing from the prefix length. |
| `quantized_cache` | Cached key-value pairs are rounded to 256 discrete levels (simulating int8 quantization) before reuse. |
| `wrong_prefix_content` | The cache is populated with a different random prefix than the one actually prepended to the suffix. |

### Harness

The experiment uses a custom deterministic transformer implemented in NumPy. The primary grid configuration uses embedding dimension 96, 4 attention heads, and 2 layers. The model is initialized with random weights (default seed) and processes random token sequences. No GPU or CUDA is involved; the harness runs entirely on CPU. This is a toy simulation, not a production inference runtime.

The harness computes both paths (full recomputation and cache reuse with the specified defect mode) for the same input, extracts the logit vectors at each suffix position, converts to probability distributions via softmax, and computes all metrics.

### Experimental Configuration

The primary experimental grid uses:

- Prefix lengths: 8, 32, 128
- Suffix lengths: 8, 32
- Trials per configuration: 5
- Total configurations: 5 modes × 3 prefix lengths × 2 suffix lengths × 5 trials = 150 runs

A reproducibility check uses seed 13, prefix lengths 16 and 64, suffix length 16, and 3 trials per configuration.

## Results

### Primary Grid

The grouped results across suffix lengths and trials, broken down by mode and prefix length:

| Mode | Prefix Len | Mean PRCL (nats) | Top-1 Disagree | Max Abs Logit Δ |
|------|-----------:|-----------------:|---------------:|----------------:|
| correct | 8 | 0 | 0.000 | 0.000 |
| correct | 32 | 0 | 0.000 | 0.000 |
| correct | 128 | 0 | 0.000 | 0.000 |
| position_plus_one | 8 | 0.0240 | 0.156 | 1.034 |
| position_plus_one | 32 | 0.0331 | 0.206 | 1.430 |
| position_plus_one | 128 | 0.0225 | 0.163 | 1.126 |
| position_reset | 8 | 0.1622 | 0.434 | 2.654 |
| position_reset | 32 | 0.2573 | 0.616 | 3.490 |
| position_reset | 128 | 0.2562 | 0.531 | 3.287 |
| quantized_cache | 8 | 4.30 × 10⁻⁵ | 0.016 | 0.041 |
| quantized_cache | 32 | 6.30 × 10⁻⁵ | 0.022 | 0.050 |
| quantized_cache | 128 | 5.03 × 10⁻⁵ | 0.016 | 0.047 |
| wrong_prefix_content | 8 | 0.8948 | 0.850 | 5.597 |
| wrong_prefix_content | 32 | 0.9199 | 0.881 | 5.839 |
| wrong_prefix_content | 128 | 0.6861 | 0.731 | 4.977 |

### Aggregate Results Across All Prefix Lengths

| Mode | Mean PRCL (nats) | Max PRCL (nats) | Mean Abs Logit Δ | Top-1 Disagree | NLL Δ (nats) |
|------|-----------------:|----------------:|------------------:|---------------:|-------------:|
| correct | 0.0 | 0.0 | 0.0 | 0.0% | 0.0 |
| position_plus_one | 0.0265 | 0.0733 | 0.176 | 17.5% | −0.0028 |
| position_reset | 0.2252 | 0.5103 | 0.528 | 52.7% | 0.0156 |
| quantized_cache | 5.21 × 10⁻⁵ | 1.13 × 10⁻⁴ | 0.008 | 1.8% | −1.48 × 10⁻⁴ |
| wrong_prefix_content | 0.8336 | 1.4390 | 1.036 | 82.1% | 0.0063 |

### Key Observations

**Correct reuse is lossless.** Across all prefix lengths, suffix lengths, and trials, correct prefix-cache reuse reproduced full recomputation exactly: PRCL, all logit deltas, top-1 disagreement, and NLL delta were zero. This confirms that in a deterministic transformer, correct KV-cache reuse is mathematically equivalent to full recomputation.

**Position errors are detectable.** The `position_reset` defect (restarting position indices) produced the second-largest PRCL at 0.225 nats, with over half of suffix positions disagreeing on the top-1 token. The subtler `position_plus_one` defect still produced a clearly nonzero PRCL of 0.027 nats and 17.5% top-1 disagreement, demonstrating that even small positional misalignments are detectable.

**Wrong prefix content is strongly detected.** The `wrong_prefix_content` mode produced the largest PRCL at 0.834 nats and 82.1% top-1 disagreement, confirming that semantic mismatch in the cache is readily identified.

**Quantized cache produces small but nonzero drift.** The `quantized_cache` mode, simulating int8 rounding of cached key-value pairs, yielded a mean PRCL of 5.21 × 10⁻⁵ nats—approximately four orders of magnitude above zero but well below the position-error modes. Top-1 disagreement was 1.8%, indicating that quantization-induced drift rarely changes the argmax prediction but is statistically present.

**Teacher-forced NLL delta is noisy.** The NLL delta metric showed inconsistent signs across modes (negative for `position_plus_one` and `quantized_cache`, positive for `position_reset` and `wrong_prefix_content`) and small magnitudes relative to the other metrics. This is expected when suffix tokens are random rather than drawn from the model's distribution, making NLL delta a less reliable diagnostic than KL divergence or top-1 disagreement.

**PRCL does not increase monotonically with prefix length.** For `position_reset` and `wrong_prefix_content`, PRCL at prefix length 128 was slightly lower than at prefix length 32. This may reflect saturation effects in the small model or interaction with the random token distribution; the trend is not conclusive given the small number of trials.

### Reproducibility

The second-seed check (seed 13, prefix lengths 16 and 64, suffix length 16, 3 trials) reproduced the same ordering of modes by PRCL:

correct (0) < quantized_cache (~6.01 × 10⁻⁵) < position_reset (~0.297) < wrong_prefix_content (~1.02)

This confirms that the relative detectability of defect classes is robust to random seed variation, though exact magnitudes differ with configuration.

## Limitations

1. **Toy transformer only.** All results are from a small deterministic NumPy transformer (d_model = 96, 4 heads, 2 layers). This is not a production-scale model. Whether PRCL magnitudes transfer to large language models with different architectures, vocabulary sizes, or numerical precisions is unknown.

2. **No production runtime validation.** The experiment does not test any specific inference framework (vLLM, TensorRT-LLM, llama.cpp, etc.). Production closure requires that the target runtime expose logits from both cached and uncached paths, which is not always straightforward.

3. **Random token inputs.** Inputs are random token sequences rather than natural language. Natural language inputs may exhibit different sensitivity to cache defects due to structured attention patterns.

4. **Small model and configuration space.** Only one architecture configuration was tested on the primary grid. The interaction between model depth, head count, embedding dimension, and PRCL sensitivity is unexplored.

5. **Quantization simulation is approximate.** The `quantized_cache` mode rounds float values to 256 levels, which approximates but does not exactly replicate any specific production quantization scheme (e.g., FP8, INT8 with different scaling strategies).

6. **No GPU or CUDA path tested.** The harness is CPU/NumPy only. Floating-point non-associativity and reduced-precision arithmetic on GPU paths could introduce additional drift that this experiment does not capture. A correct GPU implementation might yield a nonzero PRCL baseline due to nondeterminism alone.

7. **Teacher-forced NLL delta is unreliable for random tokens.** This metric is included for completeness but should not be used as a primary diagnostic when suffix tokens are not drawn from the model's distribution.

8. **Non-monotonic prefix-length trends are unexplained.** The slight decrease in PRCL at prefix length 128 for `position_reset` and `wrong_prefix_content` modes is not fully understood and may be an artifact of the small model or the random-input regime.

## Reproducibility Checklist

- **Code available:** Harness script `scripts/prefix_reuse_consistency.py` is part of the project artifacts.
- **Random seeds:** Primary grid uses the default seed; reproducibility check uses seed 13. Both are recorded in run notes and command lines.
- **Hardware:** NVIDIA GB10 (aarch64), 121 GB RAM, swap disabled. Experiment used CPU only; no GPU computation was involved.
- **Software:** Python 3.12.3, NumPy, Linux 6.17.0-1014-nvidia, CUDA 13.0 driver present but unused.
- **Primary result files:** `results/prcl_results.json`, `results/prcl_rows.csv`
- **Smoke test result:** `results/prcl_smoke.json`
- **Reproducibility check result:** `results/prcl_repro_seed13.json`
- **Execution logs:** `logs/prcl_smoke.stdout.log`, `logs/prcl_smoke.stderr.log`, `logs/prcl_results.stdout.log`, `logs/prcl_results.stderr.log`, `logs/prcl_repro_seed13.stdout.log`, `logs/prcl_repro_seed13.stderr.log`
- **Resource usage:** Primary run completed in 0.594 s model time; max RSS 43,248 kB; 0 swaps.
- **Exact commands:** Recorded in the run notes under the "Commands" section and reproducible verbatim.

## Conclusion

Prefix Reuse Consistency Loss provides a principled, zero-baseline diagnostic for KV-cache correctness in transformer inference. In a controlled toy-transformer setting, it exactly distinguishes correct cache reuse (PRCL = 0) from four classes of injected defects, with clear separation in magnitude: quantization drift (~10⁻⁵ nats), subtle position offset (~10⁻² nats), position reset (~10⁻¹ nats), and wrong prefix content (~10⁰ nats). The metric is reproducible across random seeds and requires only the ability to extract token distributions from both cached and uncached inference paths.

PRCL is viable as a local regression test and acceptance criterion for prefix-cache implementations. However, the present validation is confined to a small deterministic NumPy transformer. Transferring PRCL to production inference stacks requires: (a) access to logits from both computation paths in the target runtime, (b) calibration of acceptable PRCL thresholds for the specific model and precision regime, and (c) attention to floating-point non-determinism that may establish a nonzero baseline even for correct implementations on GPU paths. These steps constitute the necessary follow-up work before PRCL can serve as a production acceptance metric.

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Harness script | `scripts/prefix_reuse_consistency.py` |
| Run notes | `run_notes.md` |
| Smoke test results | `results/prcl_smoke.json` |
| Primary results (JSON) | `results/prcl_results.json` |
| Primary results (CSV) | `results/prcl_rows.csv` |
| Grouped summary table | `results/prcl_grouped_table.md` |
| Reproducibility check results | `results/prcl_repro_seed13.json` |
| Smoke test stdout log | `logs/prcl_smoke.stdout.log` |
| Smoke test stderr log | `logs/prcl_smoke.stderr.log` |
| Primary run stdout log | `logs/prcl_results.stdout.log` |
| Primary run stderr log | `logs/prcl_results.stderr.log` |
| Repro check stdout log | `logs/prcl_repro_seed13.stdout.log` |
| Repro check stderr log | `logs/prcl_repro_seed13.stderr.log` |
| Project decision record | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T072618522530+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T072618522530+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T072618522530+0000/paper_manifest.json` |
