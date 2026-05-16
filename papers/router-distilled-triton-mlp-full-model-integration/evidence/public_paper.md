# Router-Distilled Triton MLP Full-Model Integration

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

We present an empirical evaluation of a router-distilled block-sparse Triton MLP integrated into a Llama-like decoder layer for prefill inference. The approach replaces a dense two-layer MLP with a routed variant that computes per-token router logits, builds an active-block list via a fused Triton kernel, and executes only the active blocks using device-side program masking. On a single GB10 GPU, the specialized Triton active-block-list builder reduces logits-to-mask compaction overhead from approximately 38–40 μs to approximately 12 μs (a 3.2× improvement over PyTorch-based compaction). When integrated into a concrete decoder layer with RMSNorm, causal scaled-dot-product attention, and residual connections, the routed MLP yields 1.21–1.24× whole-layer prefill speedup across tested batch/sequence shapes at parent-project keep rates (approximately 40% active blocks). A negative result is also reported: a naive max-grid counted implementation without device-side branching regressed below the dense baseline because inactive programs still incurred the full GEMM loop cost. All reported speedups are median timings from repeated benchmark runs on a single hardware configuration; generalization to other hardware, models, or decode-phase inference is not established.

---

## 1. Introduction

Block-sparse MLPs offer a mechanism to reduce computation in transformer feed-forward layers by executing only a subset of blocks per token, selected by a lightweight router. However, realizing practical speedups requires addressing several engineering challenges: the overhead of computing router logits and converting them into an active-block list, the cost of host–device synchronization when the active count must be read back, and the integration of the sparse MLP into the full decoder-layer computation graph where attention, normalization, and residual connections add latency that can dilute MLP-only gains.

This work evaluates a concrete integration path that addresses these challenges:

1. **Fused Triton active-block-list builder** that computes block-max-pooled router logits and produces a sorted active-block list entirely on device, avoiding PyTorch-level compaction overhead.
2. **Device-side active-count propagation** that eliminates host readback of the active block count, allowing the subsequent routed MLP kernels to read the count from device memory and branch out inactive programs.
3. **nn.Module boundary** (`RouterDistilledTritonMLP`) that wraps the router, builder, and routed MLP into a module-compatible interface with pre-allocated scratch buffers.
4. **Full decoder-layer integration** into a Llama-like prefill decoder layer with RMSNorm, causal SDPA attention, and residual connections.

The central question is whether the routed Triton MLP retains a meaningful speedup when all integration overhead—router computation, block-list construction, device-side dispatch, and surrounding layer operations—is included, not just in isolated MLP benchmarks.

---

## 2. Method

### 2.1 Block-Sparse MLP Substrate

The MLP is partitioned into blocks along the token dimension (block size = 32 tokens). Each block contains a standard two-layer feed-forward network (d_model → hidden → d_model). A router selects which blocks are active for a given input; inactive blocks are skipped entirely.

### 2.2 Router and Active-Block-List Builder

For each input tensor of shape `[batch, seq, d_model]`, the router computes per-token logits via a linear projection (`x @ router_w + b`). Block-level routing decisions are made by max-pooling token-level logits within each block and applying a calibrated threshold. The threshold is calibrated to match a target keep rate derived from a parent project.

Two builder implementations are compared:

- **PyTorch builder (baseline):** Computes logits in PyTorch, applies threshold to produce a boolean mask, and uses `nonzero()` to extract active block indices on the host.
- **Triton builder (fused):** A single Triton kernel performs block max-pooling of router logits, threshold comparison, and prefix-sum compaction to produce a sorted active-block list entirely on device. This avoids Python-level control flow and host–device synchronization for the list construction itself.

### 2.3 Device-Side Active-Count Routed MLP

The routed MLP kernels accept `active_count` as a device tensor rather than a host integer. Kernels are launched over the maximum block capacity, and each program reads the device-side `active_count` to determine whether it should execute the GEMM or branch out. This eliminates the need for the host to read back the active count before launching MLP kernels.

A negative result informed this design: a naive max-grid implementation that launched all programs but did not include a device-side branch caused inactive programs to still traverse the GEMM loop, resulting in performance worse than the dense baseline.

### 2.4 Module Boundary

`RouterDistilledTritonMLP` is an `nn.Module` that accepts `[batch, seq, d_model]` hidden states and performs:

1. Router logit computation
2. Triton active-block-list construction
3. Device-count routed MLP execution
4. Output assembly

Scratch buffers for active block indices, active count, output accumulation, and temporary storage are pre-allocated so that warm module forwards do not allocate per call.

### 2.5 Decoder-Layer Integration

A dependency-free Llama-like decoder layer harness was constructed with:

- RMSNorm (pre-attention and pre-MLP)
- Causal scaled-dot-product attention (8 heads)
- Residual connections
- A swappable MLP slot

`RouterDistilledTritonMLP` is bound into the MLP slot. Router thresholds are calibrated on the layer's post-attention MLP input for each batch/sequence shape. Correctness is verified by comparing routed whole-layer output against a masked dense-router reference.

---

## 3. Results

### 3.1 Active-Block-List Builder Comparison

Benchmarked with 1024 tokens, d_model=512, hidden=2048, block_tokens=32, 30 warmup iterations, 100 repeats.

| Requested keep | Realized block fraction | Active blocks | PyTorch builder median | Triton builder median | Builder speedup |
|---:|---:|---:|---:|---:|---:|
| 0.3874 | 0.3750 | 12/32 | 39.73 μs | 12.26 μs | 3.24× |
| 0.4349 | 0.4375 | 14/32 | 38.66 μs | 12.03 μs | 3.21× |
| 0.4180 | 0.4062 | 13/32 | 38.53 μs | 12.03 μs | 3.20× |

The Triton builder reduces compaction overhead by approximately 3.2×. The isolated builder launch did not reach a stretch target of <10 μs, but clears the 2× / 15 μs criterion defined in the branch kill condition.

### 3.2 Fused End-to-End MLP Speedup (Host-Known Active Count)

At parent keep rates, the fused path (Triton builder + routed MLP) yields 1.36–1.50× speedup over dense router+MLP:

| Requested keep | Dense router+MLP median | Routed fused median | Fused E2E speedup | Correctness |
|---:|---:|---:|---:|---:|
| 0.3874 | 129.87 μs | 86.72 μs | 1.498× | pass |
| 0.4349 | 129.26 μs | 94.96 μs | 1.361× | pass |
| 0.4180 | 129.33 μs | 92.50 μs | 1.398× | pass |

### 3.3 Device-Count Module Boundary

The no-host-readback counted variant and warm module boundary:

| Requested keep | Triton builder | Builder speedup | Fused counted E2E | Fused speedup | Module counted | Module speedup |
|---:|---:|---:|---:|---:|---:|---:|
| 0.3874 | 12.10 μs | 3.29× | 98.86 μs | 1.290× | 108.30 μs | 1.210× |
| 0.4349 | 12.00 μs | 3.23× | 102.40 μs | 1.244× | 112.32 μs | 1.167× |
| 0.4180 | 11.94 μs | 3.24× | 100.26 μs | 1.270× | 109.65 μs | 1.190× |

The module boundary introduces modest overhead relative to the fused counted path (approximately 8–10 μs), likely from Python-level dispatch and buffer management. Module speedup over dense module forward remains above 1.15× at all tested keep rates.

### 3.4 Negative Result: Naive Max-Grid Without Device Branch

A naive max-grid counted implementation that launched all programs without a device-side conditional branch was tested. This variant regressed below the dense baseline because inactive programs still executed the full GEMM loop. This result is recorded in `results/device_count_module_parent_keep_bt32` and confirms that device-side branching is necessary for the counted variant to achieve speedup.

### 3.5 Decoder-Layer Prefill Integration

Benchmarked with d_model=512, hidden=2048, heads=8, block_tokens=32, active_fraction=0.41796875, 20 warmup iterations, 60 repeats.

| Shape | Active blocks | Dense MLP | Routed MLP | MLP speedup | Dense layer | Routed layer | Layer speedup | Correctness |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1×1024 | 13/32 | 132.72 μs | 114.24 μs | 1.162× | 401.25 μs | 330.37 μs | 1.215× | pass |
| 2×512 | 13/32 | 132.40 μs | 112.62 μs | 1.176× | 385.60 μs | 312.29 μs | 1.235× | pass |
| 4×256 | 13/32 | 132.35 μs | 113.12 μs | 1.170× | 376.96 μs | 303.20 μs | 1.243× | pass |
| 1×2048 | 27/64 | 296.42 μs | 166.35 μs | 1.782× | 759.97 μs | 611.25 μs | 1.243× | pass |

Whole-layer speedup is 1.21–1.24× across all tested prefill shapes. The MLP-only speedup is notably larger at 2048 tokens (1.782×) because routed work scales with the number of active blocks rather than total blocks, and the active fraction remains near 42%. However, the layer-level speedup does not increase proportionally because attention, normalization, and residual costs are fixed and constitute a larger share of total layer time.

---

## 4. Limitations

1. **Single hardware configuration.** All results are measured on a single GB10 GPU. Performance characteristics may differ substantially on other architectures (e.g., different shared memory sizes, warp scheduling, or memory bandwidth).

2. **Prefill only.** Only prefill (full-sequence) shapes are benchmarked. Decode-phase (single-token or small-group) inference has different memory-access and kernel-launch patterns and is not evaluated.

3. **Synthetic model configuration.** The decoder layer uses d_model=512, hidden=2048, heads=8—smaller than production models. Scaling behavior to larger dimensions is unknown.

4. **Fixed keep rates from parent project.** Active fractions (~38–44%) are inherited from a parent project's calibrated keep rates. Performance at significantly different sparsity levels (e.g., <10% or >80% active blocks) is not characterized.

5. **No quality evaluation.** The router's threshold is calibrated to match a target keep rate, but no downstream task quality (perplexity, accuracy, etc.) is measured. The router weights are not trained; this work addresses only the systems question of whether a routed MLP can be made faster than a dense MLP when the keep rate is given.

6. **Builder did not meet stretch target.** The Triton builder median of ~12 μs did not reach the aspirational <10 μs target, though it cleared the 2× / 15 μs kill-condition criterion.

7. **Module boundary overhead.** The `nn.Module` wrapper introduces approximately 8–10 μs of overhead relative to the direct fused path, reducing the effective speedup. The source of this overhead (Python dispatch, buffer management, or other) is not fully characterized.

8. **No multi-layer or end-to-end model evaluation.** Speedups are measured per layer. Cumulative effects across many layers (e.g., numerical drift, compounding approximation error, or different per-layer keep rates) are not assessed.

9. **No comparison with alternative sparsity implementations.** Other approaches to block-sparse or structured-sparse MLPs (e.g., cuSPARSE, Sputnik, or other Triton implementations) are not compared.

---

## 5. Reproducibility Checklist

- **Hardware specified:** GB10 GPU (specific model name not recorded in artifacts; identified as "GB10" in run notes).
- **Software environment:** Python virtual environment (`.venv`), PyTorch, Triton. Exact package versions not recorded in artifacts.
- **Benchmark commands:** Full command lines are recorded in run notes (see Section 3).
- **Warmup and repeats:** Builder/module benchmarks use 30 warmup / 100 repeats; decoder-layer benchmarks use 20 warmup / 60 repeats.
- **Metric type:** Median latency (μs) across repeats.
- **Correctness checks:** Builder correctness, counted-MLP all-close, module-boundary all-close, and routed-layer vs. masked-dense-reference comparison all pass.
- **Random seeds:** Not recorded in artifacts.
- **Result files:** All CSV and JSON result files are preserved in the project directory (see Referenced Artifacts).
- **Source code:** Benchmark scripts are present in `src/` (see Referenced Artifacts).

---

## 6. Conclusion

This work demonstrates that a router-distilled block-sparse Triton MLP can be integrated into a Llama-like decoder layer and achieve 1.21–1.24× whole-layer prefill speedup over a dense MLP baseline on a single GB10 GPU at approximately 40% active-block keep rates. The primary engineering contribution is a fused Triton active-block-list builder that reduces logits-to-mask compaction overhead by 3.2×, and a device-side active-count propagation scheme that eliminates host readback. A negative result confirms that naive max-grid dispatch without device-side branching is insufficient—inactive programs must branch out to avoid regressing below the dense baseline.

These results are bounded to the tested hardware, model scale, keep rates, and prefill regime. Whether the approach generalizes to larger models, decode-phase inference, different sparsity levels, or other GPU architectures remains an open question. The project decision recommends finalizing the current artifacts and, if productization is pursued, porting the MLP slot adapter into a real Hugging Face model package for broader evaluation.

---

## Referenced Artifacts

### Source files
- `src/routed_block_mlp_benchmark.py` — parent-project block-sparse MLP benchmark
- `src/router_integrated_mlp_benchmark.py` — router-integrated MLP benchmark (builder comparison, device-count, module boundary)
- `src/decoder_layer_integration_benchmark.py` — Llama-like decoder layer integration benchmark

### Result files
- `results/decoder_layer_prefill_parent_keep/metrics.csv`
- `results/decoder_layer_prefill_parent_keep/aggregate_summary.json`
- `results/decoder_layer_prefill_parent_keep/summary_b1_s2048.json`
- `results/decoder_layer_prefill_parent_keep/summary_b4_s256.json`
- `results/decoder_layer_prefill_parent_keep/summary_b2_s512.json`
- `results/decoder_layer_prefill_parent_keep/summary_b1_s1024.json`
- `results/decoder_layer_smoke/metrics.csv`
- `results/decoder_layer_smoke/aggregate_summary.json`
- `results/decoder_layer_smoke/summary_b1_s128.json`
- `results/device_count_module_scratch_parent_keep_bt32/metrics.csv`
- `results/device_count_module_scratch_parent_keep_bt32/aggregate_summary.json`
- `results/device_count_module_scratch_parent_keep_bt32/summary_active_0.417969.json`
- `results/device_count_module_scratch_parent_keep_bt32/summary_active_0.434896.json`
- `results/device_count_module_scratch_parent_keep_bt32/summary_active_0.38737.json`
- `results/device_count_module_parent_keep_bt32_branch/metrics.csv`
- `results/device_count_module_parent_keep_bt32_branch/aggregate_summary.json`
- `results/device_count_module_parent_keep_bt32_branch/summary_active_0.417969.json`
- `results/device_count_module_parent_keep_bt32_branch/summary_active_0.434896.json`
- `results/device_count_module_parent_keep_bt32_branch/summary_active_0.38737.json`
- `results/device_count_branch_smoke/metrics.csv`

### Decision and metadata artifacts
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`
- `run_notes.md`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
