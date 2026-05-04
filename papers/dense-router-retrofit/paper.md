# Dense Router Retrofit: Block-Sparse MLP Execution with Input-Dependent Routing on NVIDIA GB10

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run logs, benchmark outputs, decision records). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate whether a dense transformer MLP layer can be retrofitted with an input-dependent router and Triton block-sparse execution so that it preserves a masked dense-router reference while reducing wall-clock latency versus the ordinary dense router+MLP path. On an NVIDIA GB10 system (PyTorch 2.11.0+cu130, Triton 3.6.0, CUDA 13.0), we implement a fused router-logit integration, a device-side block-list builder, and a block-sparse MLP kernel, then benchmark both the isolated module and a Llama-like decoder-layer prefill harness. At medium transformer shapes (d_model=512, hidden=2048, 1024 tokens), the fused block-list builder completes in under 13 μs—3.2× faster than a generic PyTorch compaction path—and the full routed module achieves 1.16–1.19× speedup over dense router+MLP while passing correctness against the masked reference. In the decoder-layer harness, whole-layer prefill latency improves 1.21–1.25× across tested batch/sequence configurations. However, at small shapes (d_model=128, hidden=512, 256 tokens), kernel and router overhead dominate and the routed path is slower than dense (maximum observed speedup ~0.85×, i.e., a slowdown). Correctness is measured against a masked dense-router reference, not the original unmasked model, and router thresholds are calibrated on synthetic random activations rather than language-model validation loss. These results establish the retrofit as viable for medium-to-large prefill shapes on this hardware target but not as a blanket optimization across all regimes.

## Introduction

Mixture-of-expert (MoE) and routed architectures reduce per-token compute by activating only a subset of model parameters. A natural question is whether an existing dense transformer MLP—already deployed and trained—can be retrofitted with a router and block-sparse execution to recover some compute savings of MoE without retraining the full model from scratch.

Two prior local evidence threads motivate this work. First, a toy/mechanistic experiment demonstrated that router-distilled dense masks reduced teacher MSE by 76.2% versus an equal-parameter dense student, but did not demonstrate inference speedup because it still computed dense hidden activations. Second, a Triton routed-MLP harness was developed but not evaluated with actual router logits or within a decoder-layer boundary.

The present work closes those gaps by testing the following hypothesis: compute actual router logits from hidden states, compact token blocks whose router scores exceed a calibrated threshold, then run Triton block-sparse MLP kernels over only active blocks. Correctness is measured against a masked dense-router reference (i.e., the same router policy applied to a dense MLP with masking), not the unmasked dense model. The practical question is whether the fused router + compaction + sparse-MLP pipeline can beat the dense router+MLP path on wall-clock latency while faithfully implementing the router's intended activation policy.

We evaluate on an NVIDIA GB10 system across three levels of integration: (1) the isolated Triton block-sparse MLP, (2) the router-integrated module with fused block-list construction, and (3) a Llama-like decoder-layer prefill harness with RMSNorm, causal scaled-dot-product attention, and residual connections.

## Method

### Architecture

The retrofit replaces a standard dense MLP with a routed block-sparse MLP. Given hidden states $x \in \mathbb{R}^{T \times d}$, where $T$ is the token count and $d$ the model dimension:

1. **Router logit computation.** A linear router $W_r \in \mathbb{R}^{d \times 1}$ produces scalar logits per token: $\ell = x W_r$.

2. **Block-list construction.** Tokens are partitioned into blocks of size $B$ (block-tokens). A fused Triton kernel computes which blocks contain at least one token whose logit exceeds a calibrated threshold $\tau$. The output is a compact list of active block indices and an active-block count.

3. **Block-sparse MLP execution.** A Triton block-sparse MLP kernel processes only the active blocks through the two-layer MLP (up-projection, activation, down-projection). Inactive blocks are skipped entirely.

4. **Output assembly.** Results from active blocks are written back to their original positions in the output tensor; inactive-block positions retain their residual-path values (equivalent to zero MLP contribution for skipped tokens).

### Fused block-list builder

A key engineering contribution is the fused device-side block-list builder. The naive PyTorch path applies a threshold to router logits, calls `.nonzero()`, and copies indices to the device—requiring multiple kernel launches and a host-device round-trip. The fused Triton kernel performs threshold comparison, block-level reduction, and compaction in a single kernel launch, avoiding host-device synchronization.

### Decoder-layer integration

To test the retrofit in a realistic context, we implement a Llama-like decoder layer with:
- RMSNorm (pre-norm)
- Causal scaled-dot-product attention (SDPA) with 8 heads
- Residual connections
- Swappable dense or routed MLP

The routed MLP replaces the dense MLP in-place; all other components remain identical.

### Correctness criterion

Correctness is defined as agreement with a *masked dense-router reference*: the same router logits and threshold are applied, but the dense MLP is computed for all tokens and the output is masked to zero for tokens whose block is inactive. This verifies that the sparse path implements the router policy correctly. It does **not** establish that the router policy preserves the quality of the original unmasked dense model.

### Calibration of active fractions

Router thresholds are calibrated to produce target active-block fractions on synthetic random hidden states (standard normal initialization). The three target fractions tested—0.3874, 0.4349, and 0.4180—correspond to "parent keep" rates from prior local experiments. These are not trained on language-model validation data.

## Results

### Small-shape smoke test (calibration)

At small MLP shapes (256 tokens, d_model=128, hidden=512, block-tokens=32), correctness passed but the routed module was slower than dense. The maximum module speedup observed was approximately 0.85× (i.e., a ~15% slowdown). This is an important negative result: kernel launch overhead, router computation, and block-list construction dominate at small shapes, and the sparse MLP compute savings are insufficient to compensate.

This calibration result establishes a lower bound on the shape regime where the retrofit is viable. The fused block-list builder itself was ~3.18–3.24× faster than the PyTorch compaction path even at this small shape, but the builder's contribution is a small fraction of total module latency here.

### Router-integrated module benchmark

At medium shapes (1024 tokens, d_model=512, hidden=2048, block-tokens=32), the fused block-list builder and routed MLP module were benchmarked with 20 warmup iterations and 50 repeats.

| Requested active fraction | Realized active blocks | Builder median (μs) | Builder speedup vs. PyTorch | Fused counted speedup vs. dense | Module speedup vs. dense | Correctness |
|---:|---:|---:|---:|---:|---:|---|
| 0.3874 | 12/32 | 12.37 | 3.22× | 1.278× | 1.192× | pass |
| 0.4349 | 14/32 | 12.22 | 3.22× | 1.244× | 1.155× | pass |
| 0.4180 | 13/32 | 12.06 | 3.20× | 1.254× | 1.180× | pass |

The fused block-list builder completes in under 13 μs and is consistently 3.2× faster than the generic PyTorch logits-to-`nonzero` compaction path. The full routed module (router + builder + sparse MLP) is 1.16–1.19× faster than the dense router+MLP baseline at these active fractions. All configurations pass correctness against the masked dense-router reference.

The module speedup is modest because the active fraction (~40–43%) means roughly 40% of blocks are still processed, and the routing/builder overhead partially offsets the compute savings from skipping ~57–61% of blocks.

### Decoder-layer prefill benchmark

The retrofit was tested within a Llama-like decoder layer across four batch/sequence configurations (10 warmup, 30 repeats), with an active fraction of 0.4180 (13/32 blocks active for 1024-token shapes; 27/64 for 2048 tokens).

| Batch × Seq | Active blocks | Dense MLP median (μs) | Routed MLP median (μs) | MLP speedup | Dense layer median (μs) | Routed layer median (μs) | Layer speedup | Correctness |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 × 1024 | 13/32 | 134.93 | 115.01 | 1.173× | 396.45 | 328.80 | 1.206× | pass |
| 2 × 512 | 13/32 | 134.37 | 114.21 | 1.177× | 377.60 | 310.70 | 1.215× | pass |
| 4 × 256 | 13/32 | 134.42 | 114.06 | 1.178× | 370.59 | 302.32 | 1.226× | pass |
| 1 × 2048 | 302.85 | 166.66 | 1.817× | 754.42 | 603.95 | 1.249× | pass |  |

The MLP-level speedup ranges from 1.17× (at 1024 tokens) to 1.82× (at 2048 tokens, where sparsity is applied over more blocks). Whole-layer speedup is 1.21–1.25×, diluted by the fixed costs of attention, normalization, and residual connections that are not affected by the retrofit. The 2048-token configuration shows the strongest MLP-level speedup (1.82×) because the block-sparse kernel amortizes overhead over more active blocks, though the layer-level gain (1.25×) remains bounded by the non-MLP fraction of the layer.

All configurations pass correctness against the masked dense-router reference.

### Summary of primary metrics

Aggregated from the project decision record:

| Metric | Minimum | Mean |
|---|---:|---:|
| Router builder speedup vs. PyTorch | 3.20× | 3.21× |
| Router fused end-to-end speedup vs. dense | 1.24× | — |
| Router module speedup vs. dense | 1.16× | 1.18× |
| Decoder MLP speedup vs. dense | 1.17× | 1.34× |
| Decoder layer speedup vs. dense | 1.21× | 1.22× |
| Small-shape module speedup (max, i.e., best case) | — | 0.85× (slowdown) |
| Correctness | all passed | — |

## Limitations

1. **Synthetic, not linguistic, evaluation.** The decoder layer is a local Llama-like harness with random hidden states, not a full Hugging Face checkpoint replacement. Router thresholds are calibrated to target active-block fractions on standard-normal activations, not trained on language-model validation loss. The retrofit's effect on perplexity or downstream task quality is unknown.

2. **Correctness scope.** Correctness is verified against a masked dense-router reference, confirming that the sparse path faithfully implements the router policy. This does not establish that the router policy preserves the quality of the original unmasked dense model. A router that drops the wrong tokens could pass this correctness check while degrading model output.

3. **Shape-dependent viability.** The retrofit is not viable at small MLP shapes. At 256 tokens and d_model=128, kernel and router overhead dominate and the routed path is approximately 15% slower than dense. The method should be gated to medium and large prefill shapes in any deployment.

4. **Prefill-only.** All benchmarks measure prefill latency. Decode-phase (single-token autoregressive) performance is not evaluated; the overhead profile may differ substantially in that regime.

5. **Benchmark depth.** Repeat counts (50 for the module benchmark, 30 for the decoder-layer benchmark) are sufficient for a local go/no-go decision but shorter than what would be expected for publication-grade statistical reporting. Variance statistics beyond the median are available in the raw CSV artifacts but are not analyzed here.

6. **Single hardware target.** All results are from one NVIDIA GB10 system. Performance characteristics may differ on other GPU architectures, especially those with different memory hierarchies or kernel launch overhead profiles.

7. **No end-to-end model quality data.** The central claim is about latency and correctness of the sparse execution path, not about model quality after retrofit. Whether a retrofitted dense model retains acceptable quality is an open question requiring integration with a real checkpoint and language evaluation.

## Reproducibility Checklist

- **Hardware:** NVIDIA GB10 (device name as reported by `nvidia-smi`), swap disabled, ~122 GB system RAM available.
- **Software:** Python 3.12.3, PyTorch 2.11.0+cu130, Triton 3.6.0, CUDA 13.0. Full environment log: `logs/setup_env.log`.
- **Dependencies:** Specified in `requirements.txt`; installed via `uv pip install` with the cu130 PyTorch index.
- **Source code:**
  - `src/routed_block_mlp_benchmark.py` — Triton block-sparse routed MLP kernels and reference helpers.
  - `src/router_integrated_mlp_benchmark.py` — Actual-router-logit integration, fused block-list builder, device-side active-count routed MLP.
  - `src/decoder_layer_integration_benchmark.py` — Llama-like decoder-layer prefill harness with swappable dense/routed MLP.
- **Benchmark commands:** Fully specified in the run notes, including all flags, token counts, dimensions, block sizes, active fractions, warmup, and repeat counts.
- **Raw results:**
  - `results/smoke_router_integrated/metrics.csv` and `aggregate_summary.json`
  - `results/router_integrated_parent_keep_bt32/metrics.csv` and `aggregate_summary.json`
  - `results/decoder_layer_prefill_parent_keep/metrics.csv` and `aggregate_summary.json`
- **Logs:** `logs/setup_env.log`, `logs/smoke_router_integrated.log`, `logs/router_integrated_parent_keep_bt32.log`, `logs/decoder_layer_prefill_parent_keep.log` — include full command output and `/usr/bin/time -v` resource posture (max RSS, swap status).
- **Randomness:** Hidden states are initialized from standard-normal distributions; no random seed is explicitly fixed in the benchmark commands. Reproducibility of exact timing values is not guaranteed; correctness results are deterministic given the same initialization.
- **Memory posture:** Max RSS ~1.40 GB (router-integrated run) and ~1.50 GB (decoder-layer run). No swap activity observed. `MemAvailable` stable at 121.7–122.1 GB pre/post.

## Conclusion

A dense transformer MLP can be retrofitted with an input-dependent router and Triton block-sparse execution to achieve measurable latency improvements over the dense router+MLP path on NVIDIA GB10, provided the MLP shape is large enough to amortize routing and kernel overhead. At medium shapes (d_model=512, hidden=2048, 1024+ tokens), the full routed module is 1.16–1.19× faster than dense, and within a Llama-like decoder layer the whole-layer prefill improves 1.21–1.25×. The fused block-list builder is a key enabler, completing in under 13 μs and 3.2× faster than the generic PyTorch compaction path. Correctness against the masked dense-router reference is preserved across all tested configurations.

However, the retrofit is not viable at small shapes (observed ~15% slowdown at d_model=128, 256 tokens), correctness does not imply preservation of original model quality, and router thresholds are calibrated on synthetic data rather than language-model validation loss. The method should be understood as a latency optimization for medium-to-large prefill shapes that faithfully implements a given router policy, not as a quality-preserving model compression technique.

The next scientific step is integration with a real transformer checkpoint—either a dense model or an open MoE-to-dense distillation target—where router thresholds are trained or distilled on language activations and evaluated by validation loss or perplexity. Without that step, the quality implications of the retrofit remain unknown.

---

## Referenced Artifacts

| Artifact | Description |
|---|---|
| `run_notes.md` | Full research log: hypothesis, environment, commands, metrics, interpretation, decision |
| `README.md` | Project documentation |
| `requirements.txt` | Python dependencies for reproduction |
| `src/routed_block_mlp_benchmark.py` | Triton block-sparse routed MLP kernels and reference helpers |
| `src/router_integrated_mlp_benchmark.py` | Router-logit integration, fused block-list builder, device-side routed MLP |
| `src/decoder_layer_integration_benchmark.py` | Llama-like decoder-layer prefill harness |
| `logs/setup_env.log` | Environment verification output |
| `logs/smoke_router_integrated.log` | Small-shape smoke test log |
| `logs/router_integrated_parent_keep_bt32.log` | Router-integrated main benchmark log |
| `logs/decoder_layer_prefill_parent_keep.log` | Decoder-layer benchmark log |
| `results/smoke_router_integrated/metrics.csv` | Smoke test per-configuration metrics |
| `results/smoke_router_integrated/aggregate_summary.json` | Smoke test aggregate summary |
| `results/router_integrated_parent_keep_bt32/metrics.csv` | Router-integrated main metrics |
| `results/router_integrated_parent_keep_bt32/aggregate_summary.json` | Router-integrated aggregate summary |
| `results/decoder_layer_prefill_parent_keep/metrics.csv` | Decoder-layer per-configuration metrics |
| `results/decoder_layer_prefill_parent_keep/aggregate_summary.json` | Decoder-layer aggregate summary |
| `.omx/project_decision.json` | Decision record with primary metrics, limitations, and next steps |
