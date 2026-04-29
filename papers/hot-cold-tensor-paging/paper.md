# Hot-Cold Tensor Paging for Constrained GPU Residency: A Mixed-Result Study on NVIDIA GB10 UMA

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We investigate hot-cold tensor paging as a mechanism for running large language models whose total tensor bytes exceed a constrained GPU memory budget. Using Qwen2.5-32B (18.48 GiB tensor bytes) on an NVIDIA GB10 unified memory architecture with an 8 GiB CUDA model-buffer target, we evaluate a progression of strategies: static hot/cold residency, decode-position-aware prefetch, persistent mirror-buffer aliasing, and reusable eviction/reload paging. The toy-model simulator predicted a 2.31× speedup for decode-prefetch over static first-fit placement. However, real llama.cpp hook-prototype experiments on Qwen2.5-32B produced a mixed result. Static hot/cold residency—placing 24 of 64 transformer layers in the hot cache—retained 65–72% of unconstrained all-GPU decode throughput (5.65–5.91 tok/s vs. 8.07–8.81 tok/s). Persistent mirror-buffer aliasing with a fixed budget offered modest additional gains (+1% to +7%). All dynamic paging variants underperformed static residency: naive fixed-size staging copies achieved only 40% of all-GPU throughput, layer-aware double-buffered prefetch reached at best 90% of static, and true reusable eviction/reload paging lost approximately 42–43% versus static by copying 84–168 GiB per short decode window. We conclude that static hot/cold tensor placement and selective persistent mirrors are the useful mechanisms in this setting, while per-decode-step eviction/reload is not competitive without a materially different graph-partitioned async backend design.

## 1. Introduction

Running large language models on hardware with GPU memory smaller than the model's total tensor footprint requires mechanisms to manage which tensors reside in fast GPU memory and which remain in host memory. On unified memory architecture (UMA) platforms such as NVIDIA GB10, the GPU and CPU share a physical memory pool, but the CUDA model buffer—the portion of memory registered with the CUDA runtime for GPU compute—may be constrained to a fraction of total system RAM.

This study examines hot-cold tensor paging: partitioning model tensors into a hot set that resides in the CUDA model buffer and a cold set that remains in host-accessible memory, then evaluating whether dynamic paging (prefetch or eviction/reload) can recover throughput lost to cold-set access stalls.

The investigation proceeds through four stages of increasing fidelity: (1) a deterministic toy-model event simulator, (2) a llama.cpp hook-prototype probe with real GGUF tensor inventories and CUDA copy calibration, (3) a patched llama.cpp binary implementing static hot/cold residency with real Qwen2.5-32B inference, and (4) progressively more sophisticated dynamic paging implementations (naive staging, layer-aware double-buffered prefetch, persistent mirror aliasing, and reusable eviction/reload paging).

The result is mixed: the hypothesis that dynamic paging improves upon static residency is not supported by the empirical evidence, though static hot/cold residency itself is a viable strategy.

## 2. Method

### 2.1 Toy-Model Event Simulator

A deterministic Python event simulator (`scripts/hot_cold_paging_sim.py`) models a 36-layer, 144-tensor model with 21,590.7 MiB total tensor bytes constrained by an 8,192 MiB hot cache (2.64× over cache). The simulator exercises three strategies:

- **Static first-fit**: tensors placed in cache in model order until the budget is exhausted.
- **Hot frequency, no prefetch**: tensors ranked by access frequency, placed in cache by frequency, but no prefetch of cold tensors.
- **Hot frequency with decode prefetch**: same hot-set selection, plus decode-position-aware prefetch of cold tensors using a single DMA queue with configurable lookahead.

Host-to-GPU page bandwidth was calibrated via `np.copyto` on 256 MiB pages (median 22.44 GiB/s), with the simulation using a conservative 18 GiB/s.

### 2.2 llama.cpp Hook-Prototype Probe

A Python scaffold (`scripts/llamacpp_hotcold_probe.py`) inventories real GGUF tensor metadata, runs `llama-bench` on a small model (SmolLM2-135M) for real decode timing, and calibrates CUDA H2D copy/overlap on GB10 via a standalone CUDA microbenchmark (`scripts/cuda_overlap_prefetch_probe.cu`).

### 2.3 Patched llama.cpp with Hot/Cold Residency

A project-local detached worktree of llama.cpp (commit `6a4c34552`) was patched to add:

- `--hotcold-trace <file>`: per-layer graph-node timing trace output.
- `--hot-cache-mib <n>`: target CUDA model-buffer budget.
- `-ot <pattern>=CPU`: tensor buffer override to force selected tensors to CPU/CUDA_Host buffers.

The policy packs the largest transformer layers into the 8 GiB budget, placing 24 of 64 layers hot (7.98 GiB) and 40 layers cold (10.50 GiB). Cold-layer tensors are overridden to CPU buffers via llama.cpp's existing tensor buffer override mechanism.

### 2.4 Dynamic Paging Variants

Four dynamic paging variants were implemented as incremental extensions to the patched llama.cpp binary:

1. **Naive fixed-size staging copies** (`--hotcold-prefetch-mib`): allocates pinned host and device staging buffers, issues CUDA H2D copies of a fixed size per cold layer, and synchronizes when the layer is reached.

2. **Layer-aware double-buffered prefetch** (`--hotcold-prefetch-layer-bytes`, `--hotcold-prefetch-buffers`): copies bytes derived from actual GGUF cold-layer tensor sizes using multiple pinned/device buffers and CUDA streams, with configurable lookahead and copy-granularity caps.

3. **Persistent fixed-budget mirror aliasing** (`--hotcold-alias-layers`): allocates CUDA mirror tensors for selected cold layers, copies cold weights into mirrors via `ggml_backend_tensor_copy`, and swaps model tensor pointers before graph construction so compute consumes migrated tensors. Mirrors persist across decode steps.

4. **Reusable eviction/reload pager** (`--hotcold-reuse-pager`): extends mirror aliasing with a reusable arena. After a cold layer executes, its mirror is evicted (pointer restored to original CPU tensor), freeing the arena slot for the next cold layer. This requires per-decode-step copy-in and copy-out for every cold layer.

### 2.5 Hardware and Software Environment

- **GPU**: NVIDIA GB10 (Blackwell, compute capability 12.1), UMA architecture.
- **System RAM**: ~122 GiB available (130 GiB total).
- **OS**: Linux 6.17.0-1014-nvidia-aarch64, glibc 2.39, Python 3.12.3.
- **CUDA**: `/usr/local/cuda/bin/nvcc`, GGML_CUDA=ON.
- **Model**: Qwen2.5-32B-Instruct-Q4_K_M.gguf (18.48 GiB tensor bytes, 771 tensors, 64 transformer layers, 32.76B parameters).
- **Benchmark tool**: Patched `llama-bench` with decode-only tests (`-p 0 -n 8` or `-n 16`), 3 repetitions where noted, no warmup.

**Important UMA caveat**: On GB10, `nvidia-smi` reports memory fields as `[N/A]`. GPU memory accounting is non-authoritative; llama.cpp's own buffer size logging and `/proc/meminfo` are used instead.

## 3. Results

### 3.1 Toy-Model Simulator

| Strategy | tok/s | p50 latency (ms) | Transfer stall (ms) | Hidden transfer (ms) |
|---|---|---|---|---|
| Static first-fit | 2.07 | 482.3 | 210,337.5 | 0 |
| Hot frequency, no prefetch | 3.57 | 279.7 | 106,804.6 | 0 |
| Hot frequency, decode prefetch | 4.79 | 208.4 | 70,124.8 | 36,679.8 |

Decode prefetch achieved 2.31× speedup over static first-fit and 1.34× over hot frequency without prefetch. The simulator predicted that better hot-set selection combined with decode-position-aware prefetch materially reduces page stalls.

### 3.2 CUDA Copy/Overlap Calibration on GB10

| Metric | Value |
|---|---|
| 256 MiB H2D median bandwidth | 55.16 GiB/s (4.532 ms) |
| Serial copy + compute | 6.447 ms |
| Overlapped copy + compute | 4.587 ms |
| Hidden fraction | 0.289 |

At measured bandwidth, copying the full cold side (~10.5 GiB) costs approximately 0.193 s, which is not hideable behind a single SmolLM2 decode token (0.0014 s/token). This confirmed that prefetch must operate at layer granularity, not as a single bulk transfer.

### 3.3 Static Hot/Cold Residency on Qwen2.5-32B

| Case | Decode tok/s | Hot layers | Cold layers | Hot GiB | Cold GiB |
|---|---|---|---|---|---|
| All-GPU control (gen8, r=3) | 8.81 | — | — | — | — |
| Static 8 GiB hot/cold (gen8, r=3) | 5.81 | 24 | 40 | 7.98 | 10.50 |
| All-GPU control (gen8, r=1) | 8.68 | — | — | — | — |
| Static 8 GiB hot/cold (gen8, r=1) | 5.65 | 24 | 40 | 7.98 | 10.50 |

Static hot/cold residency retained 65.9% (r=3) to 65.1% (r=1) of all-GPU throughput. llama.cpp verbose logging confirmed the CUDA model buffer stayed at 7,754 MiB and cold-block tensors were placed in CPU_Mapped/CUDA_Host buffers.

### 3.4 Naive Fixed-Size Staging Prefetch

| Case | Decode tok/s | Prefetch GiB | Sync time (μs) | vs. static |
|---|---|---|---|---|
| All-GPU control | 8.29 | 0 | 0 | — |
| Static 8 GiB | 4.84 | 0 | 0 | 1.00× |
| Dynamic prefetch (256 MiB/layer) | 3.33 | 10.0 | 60,448 | 0.69× |

Naive one-layer-lookahead staging copies underperformed static residency by 31%, spending ~60.4 ms in synchronization stalls. The fixed 256 MiB copy granularity and single-layer lookahead did not hide sufficient transfer latency.

### 3.5 Layer-Aware Double-Buffered Prefetch

| Case | Decode tok/s | Copied GiB | Sync time (μs) | vs. static |
|---|---|---|---|---|
| All-GPU control (sweep) | 8.22 | — | — | — |
| Static 8 GiB (sweep) | 5.90 | — | — | 1.00× |
| Best sweep (LA=4, 64 MiB cap, 2 buffers) | 5.60 | 1.63 | 0 | 0.95× |
| All-GPU control (confirmation, r=3) | 8.68 | — | — | — |
| Static 8 GiB (confirmation, r=3) | 5.76 | — | — | 1.00× |
| Layer-aware prefetch (confirmation, r=3) | 5.17 | 4.88 | 5 | 0.90× |

The best sweep configuration approached but did not exceed static residency. The confirmation run confirmed a 10.3% deficit. Full per-layer-byte copies were consistently worse than capped 64 MiB copies because transferring the entire cold side (up to 10.50 GiB) adds visible overhead in short decode windows.

### 3.6 Persistent Fixed-Budget Mirror Aliasing

| Case | Decode tok/s | Alias tensors | Alias GiB | vs. static |
|---|---|---|---|---|
| All-GPU control (gen8) | 8.81 | 0 | 0 | — |
| Static 8 GiB (gen8) | 5.81 | 0 | 0 | 1.00× |
| Mirror 512 MiB (gen8) | 6.06 | 67 | 0.5 | 1.04× |
| Mirror 1024 MiB (gen8) | 6.11 | 85 | 1.0 | 1.05× |
| Mirror 2048 MiB (gen8) | 6.22 | 135 | 2.0 | 1.07× |
| All-GPU control (gen16) | 8.90 | 0 | 0 | — |
| Static 8 GiB (gen16) | 6.04 | 0 | 0 | 1.00× |
| Mirror 512 MiB (gen16) | 6.14 | 67 | 0.5 | 1.02× |
| Mirror 1024 MiB (gen16) | 6.02 | 85 | 1.0 | 1.00× |
| Mirror 2048 MiB (gen16) | 6.09 | 135 | 2.0 | 1.01× |

Persistent mirror aliasing produced modest positive signals in the 8-token decode window (+1% to +7%), with the benefit more pronounced at shorter generation lengths. The mirrors persist across decode steps and do not incur per-step copy overhead.

### 3.7 Reusable Eviction/Reload Pager

| Case | Decode tok/s | Copied GiB | Copy time (ms) | Reuse loads | vs. static |
|---|---|---|---|---|---|
| All-GPU control (gen8) | 8.68 | — | — | — | — |
| Static 8 GiB (gen8) | 5.65 | — | — | — | 1.00× |
| Reuse pager 512 MiB (gen8) | 3.29 | 84.01 | 1,561 | 320 | 0.58× |
| Reuse pager 1024 MiB (gen8) | 3.30 | 84.01 | 1,555 | 320 | 0.58× |
| Reuse pager 2048 MiB (gen8) | 3.28 | 84.01 | 1,556 | 320 | 0.58× |
| All-GPU control (gen16) | 8.85 | — | — | — | — |
| Static 8 GiB (gen16) | 5.81 | — | — | — | 1.00× |
| Reuse pager 512 MiB (gen16) | 3.31 | 168.03 | 3,107 | 640 | 0.57× |
| Reuse pager 1024 MiB (gen16) | 3.31 | 168.03 | 3,102 | 640 | 0.57× |
| Reuse pager 2048 MiB (gen16) | 3.31 | 168.03 | 3,101 | 640 | 0.57× |

The reusable pager swapped all 480 cold-layer tensors per decode step (40 layers × 12 tensors/layer). Over 8 generated tokens, it copied 84.0 GiB; over 16 tokens, 168.0 GiB. Increasing the arena budget from 512 MiB to 2 GiB had no measurable effect because the bottleneck is total reload volume, not arena capacity. The pager achieved only 57–58% of static hot/cold throughput, a 42–43% deficit.

## 4. Limitations

1. **Single hardware platform**: All experiments were conducted on one NVIDIA GB10 UMA system. Results may differ on discrete-GPU systems with separate HBM and PCIe/NVLink interconnects, where host-to-device bandwidth and latency characteristics are substantially different.

2. **Single model**: Only Qwen2.5-32B-Instruct-Q4_K_M was used for real inference experiments. Models with different layer-size distributions, MoE architectures, or quantization schemes may exhibit different hot/cold paging behavior.

3. **Short decode windows**: Benchmarks used 8 or 16 generated tokens. Longer generation lengths may change the relative economics of one-time copy costs versus per-step eviction overhead, though the reusable pager's per-step cost scales linearly with generation length.

4. **UMA memory measurement**: On GB10, `nvidia-smi` reports memory fields as `[N/A]`. GPU memory utilization was inferred from llama.cpp buffer accounting and `/proc/meminfo`, not from authoritative hardware counters.

5. **Staging copies vs. true migration**: The naive staging and layer-aware prefetch variants copied bytes into staging buffers but did not feed those bytes into graph execution. The persistent mirror and reusable pager variants did perform true tensor pointer swapping, but the reusable pager's eviction/reload cycle is inherent to its design and cannot be avoided without a fundamentally different backend architecture.

6. **No KV-cache pressure**: Decode-only benchmarks with zero prompt tokens and short generation do not exercise KV-cache memory pressure, which would further constrain the effective hot budget in production workloads.

7. **Deterministic workload**: The toy simulator used a deterministic access pattern. Real inference workloads may have variable per-layer compute times and branching that affect prefetch scheduling.

8. **No multi-query or batched serving**: All experiments used single-sequence decode. Batched serving would change the compute-to-transfer ratio and may alter the viability of dynamic paging.

## 5. Reproducibility Checklist

- [x] **Source code available**: `scripts/hot_cold_paging_sim.py`, `scripts/llamacpp_hotcold_residency.py`, `scripts/llamacpp_hotcold_probe.py`, `scripts/cuda_overlap_prefetch_probe.cu`.
- [x] **Patched llama.cpp source**: `external/llama.cpp-hotcold/tools/llama-bench/llama-bench.cpp` (detached worktree at commit `6a4c34552`).
- [x] **Reusable patches**: `results/llamacpp_hotcold_residency/llama-bench-hotcold-trace.patch`, `results/llamacpp_hotcold_residency/llama-bench-hotcold-prefetch-trace.patch`, `results/llamacpp_hotcold_residency/llama-bench-hotcold-layeraware-prefetch.patch`, `results/llamacpp_hotcold_residency/llama-bench-hotcold-reuse-pager.patch`.
- [x] **Model artifacts**: Qwen2.5-32B-Instruct-Q4_K_M.gguf and SmolLM2-135M-Instruct-Q4_K_M.gguf (publicly available GGUF models; local paths are symlinks to cached assets).
- [x] **Result data**: All JSON and CSV result files persisted under `results/` (see Referenced Artifacts).
- [x] **Build instructions**: llama.cpp built with `/usr/local/cuda/bin/nvcc`, `-DGGML_CUDA=ON`, `-DLLAMA_CURL=OFF` on aarch64 Linux.
- [x] **Random seeds**: Toy simulator uses seed 34; llama-bench runs are deterministic given the same model and flags.
- [x] **Telemetry recorded**: `/proc/meminfo`, `nvidia-smi` (non-authoritative on UMA), and process RSS captured before and after each benchmark case.
- [ ] **External replication**: Not yet performed on other hardware or by independent parties.
- [ ] **Peer review**: This draft has not been peer-reviewed.

## 6. Conclusion

This study evaluated hot-cold tensor paging for running Qwen2.5-32B (18.48 GiB) under an 8 GiB CUDA model-buffer budget on NVIDIA GB10 UMA. The findings are mixed:

**Supported**: Static hot/cold tensor residency is viable. Placing 24 of 64 transformer layers in the hot cache retains 65–72% of unconstrained all-GPU decode throughput (5.65–5.91 tok/s vs. 8.07–8.81 tok/s). Persistent mirror-buffer aliasing for selected cold tensors can provide modest additional improvement (+1% to +7%).

**Not supported**: Dynamic paging strategies that perform per-decode-step copies do not improve upon static residency in this setting. Naive staging copies, layer-aware double-buffered prefetch, and reusable eviction/reload paging all underperformed the static baseline. The reusable pager's 42–43% deficit is explained by its copying 84–168 GiB per short decode window, a volume that cannot be hidden behind the available compute on this workload.

The discrepancy between the toy simulator's optimistic 2.31× speedup prediction and the real-system results arises because the simulator modeled prefetch as perfectly hiding transfer latency behind compute, whereas the real llama.cpp graph lifecycle requires that cold-layer tensors be resident at graph execution time, and the current backend does not support asynchronous tensor migration interleaved with compute within a single graph evaluation.

The useful mechanism emerging from this study is selective persistent residency: choose a hot set of layers that fits the budget, accept the throughput reduction from cold-layer CPU execution, and optionally add persistent CUDA mirrors for the most frequently accessed cold tensors. Per-decode-step eviction and reload should not be pursued without a graph-partitioned async backend that can overlap cold-layer transfers with hot-layer compute within the same decode step.

## Referenced Artifacts

### Run notes and decision
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Claim audit
- `papers/source-record-redacted/publication/claim_audit.json`
- `papers/source-record-redacted/claim_ledger.json`

### Evidence bundle
- `papers/source-record-redacted/evidence_bundle.json`

### Toy simulator results
- `results/smoke.json`
- `results/smoke.csv`
- `results/hot_cold_sim_results.json`
- `results/hot_cold_sim_results.csv`
- `results/sensitivity_summary.csv`

### llama.cpp probe results
- `results/llamacpp_probe/hotcold_probe.json`
- `results/llamacpp_probe/hotcold_probe.csv`

### Hot/cold residency and paging results
- `results/llamacpp_hotcold_residency/qwen32b_hotcold_residency.json`
- `results/llamacpp_hotcold_residency/qwen32b_hotcold_residency_summary.csv`
- `results/llamacpp_hotcold_residency/qwen32b_hotcold_dynamic_prefetch_256mib_summary.csv`
- `results/llamacpp_hotcold_residency/qwen32b_hotcold_layeraware_prefetch_sweep.json`
- `results/llamacpp_hotcold_residency/qwen32b_hotcold_layeraware_prefetch_sweep_summary.csv`
- `results/llamacpp_hotcold_residency/qwen32b_hotcold_fixed_budget_pager_sweep.json`
- `results/llamacpp_hotcold_residency/qwen32b_hotcold_fixed_budget_pager_sweep_summary.csv`
- `results/llamacpp_hotcold_residency/qwen32b_hotcold_reuse_pager_sweep.json`
- `results/llamacpp_hotcold_residency/qwen32b_hotcold_reuse_pager_sweep_summary.csv`

### Patches
- `results/llamacpp_hotcold_residency/llama-bench-hotcold-trace.patch`
- `results/llamacpp_hotcold_residency/llama-bench-hotcold-prefetch-trace.patch`
- `results/llamacpp_hotcold_residency/llama-bench-hotcold-layeraware-prefetch.patch`
- `results/llamacpp_hotcold_residency/llama-bench-hotcold-reuse-pager.patch`

### Per-case trace CSVs
- `results/llamacpp_hotcold_residency/all_gpu_control_gen8_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_largest_layers_gen8_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_fixed_budget_pager_512mib_gen8_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_fixed_budget_pager_1024mib_gen8_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_fixed_budget_pager_2048mib_gen8_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_fixed_budget_pager_512mib_gen16_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_fixed_budget_pager_1024mib_gen16_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_fixed_budget_pager_2048mib_gen16_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_reuse_pager_512mib_gen8_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_reuse_pager_1024mib_gen8_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_reuse_pager_2048mib_gen8_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_reuse_pager_512mib_gen16_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_reuse_pager_1024mib_gen16_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_reuse_pager_2048mib_gen16_trace.csv`
- `results/llamacpp_hotcold_residency/all_gpu_control_gen16_trace.csv`
- `results/llamacpp_hotcold_residency/hot_cache_8gib_largest_layers_gen16_trace.csv`

### Scripts
- `scripts/hot_cold_paging_sim.py`
- `scripts/llamacpp_hotcold_probe.py`
- `scripts/llamacpp_hotcold_residency.py`
- `scripts/cuda_overlap_prefetch_probe.cu`

### Publication manifests
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/paper_manifest.json`
