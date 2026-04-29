# FlashAttention-4 Kernel Pipelining for sm_121 (FA4-sm121)

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We investigate whether Blackwell sm_121 Tensor Memory Accelerator (TMA) hardware, accessible via CUDA 13.0 on the NVIDIA GB10 GPU (compute capability 12.1), can support FlashAttention-4-style pipelined attention kernels with meaningful speedups over non-TMA baselines. Through a sequence of progressively more realistic probes—compile-path smoke tests, CUtensorMap-backed runtime roundtrips, tile-size microbenchmarks, and forward-only attention scaffolds—we establish that: (1) the sm_121 TMA path is functionally correct and compiles through `cp.async.bulk.tensor` PTX; (2) TMA becomes throughput-competitive at tile sizes ≥32×32; (3) a single-stage TMA attention scaffold achieves 2.88× speedup over a matched non-TMA fallback at seq_len=4096, head_dim=64; (4) naive pipelining with K/V staging buffers regresses severely due to shared-memory-induced occupancy collapse (1 vs 2 active blocks/SM); (5) a reduced-footprint sliced double-buffer (32×64 K/V slices) recovers most of the regression, reaching 2.58× over fallback but still 0.91× of single-stage TMA; and (6) after retuning the staging footprint for head_dim=128 (tile64/slice32), a split-prefetch kernel achieves 4.48× speedup over a patched FlashAttention-3 baseline at seq_len=131072. The positive results are bounded to the specific GB10 hardware, CUDA 13.0 toolchain, and single-head forward-only configurations tested. Naive pipelining without occupancy-aware design is counterproductive on this architecture.

---

## 1. Introduction

NVIDIA's Blackwell architecture introduces sm_121 compute capability with enhanced Tensor Memory Accelerator (TMA) units, exposing `cp.async.bulk.tensor` PTX instructions for asynchronous bulk transfers between global and shared memory. The potential for TMA-backed producer/consumer pipelining in attention kernels—where K/V tile loads overlap with math—motivates the question: can sm_121 TMA deliver practical speedups for FlashAttention-style kernels, and what design constraints govern whether pipelining helps or hurts?

This question is not trivial. TMA introduces setup overhead (CUtensorMap encoding, barrier synchronization) that may dominate at small tile sizes. Pipelining requires additional shared-memory staging buffers that can reduce occupancy, potentially overwhelming any overlap benefit. Prior work on FlashAttention-3 targets sm_90 (Hopper) and sm_120 (Blackwell), but sm_121-specific validation with TMA pipelining remains unexplored in published artifacts.

We report a systematic investigation from compile-path feasibility through end-to-end attention benchmarks on GB10 hardware, including both positive and negative results. The central finding is that sm_121 TMA delivers substantial speedups when staging footprints are tuned to preserve occupancy, but naive pipelining is counterproductive and can regress performance by more than 2×.

---

## 2. Method

### 2.1 Hardware and Toolchain

All experiments were conducted on an NVIDIA GB10 GPU (compute capability 12.1) with CUDA 13.0 (nvcc 13.0.88). The CUTLASS library was cloned locally with `CUTLASS_ARCH_MMA_SM121_ENABLED=1` and `CUTE_ARCH_TMA_SM120_ENABLED=1` confirmed active. The upstream FlashAttention snapshot exposed explicit Blackwell support only as sm_120 software paths; the most relevant structural reference was CUTLASS example 77 (blackwell_fmha), which required arch retargeting for sm_121.

### 2.2 Experimental Progression

The investigation proceeded through six phases of increasing fidelity:

**Phase 1 — Compile-path smoke test.** A minimal kernel (`sm121_tma_smoke.cu`) was compiled for sm_121 to verify that the toolchain accepts Blackwell-specific TMA PTX. The generated PTX was inspected for `cp.async.bulk.tensor.2d` instructions.

**Phase 2 — Runtime TMA roundtrip probe.** A CUtensorMap-backed probe (`sm121_tma_runtime_probe.cu`) performed 1000 repeated load-modify-store roundtrips on a 16×16 integer tile, verifying byte-level correctness and measuring per-launch latency.

**Phase 3 — TMA vs. fallback microbenchmark.** A sweep (`sm121_tma_vs_fallback_bench.cu`) compared CUtensorMap-backed TMA roundtrips against simple global-memory fallback copies across nine configurations: tile sizes 16×16, 32×32, 64×64, each with per-tile work stages 1, 4, and 16.

**Phase 4 — Forward attention scaffold.** A single-head forward-only softmax attention kernel (`sm121_attention_scaffold_bench.cu`) was implemented at seq_len=4096, head_dim=64, query_count=64, with TMA tile loads for K/V and a functionally equivalent non-TMA baseline. Correctness was verified against a CPU reference implementation.

**Phase 5 — Pipelining variants.** Three overlap-oriented variants were added to the scaffold:
- *Full ping-pong pipeline:* double-buffered 64×64 K/V staging with shared-memory barriers.
- *K-prefetch-only pipeline:* overlap only the K-tile prefetch, reducing write scope.
- *Sliced 32×64 pipeline:* double-buffered 32×64 K/V slices to preserve occupancy while enabling overlap.

All variants used dynamic shared memory with explicit `cudaFuncSetAttribute` opt-in for allocations exceeding 48 KiB.

**Phase 6 — head_dim=128 retuned scaffold.** The initial head_dim=128 configuration (tile64/slice64) failed badly. A retuned configuration (tile64/slice32, query_group=1) was benchmarked at seq_len=131072, query_count=4 against a patched FlashAttention-3 baseline.

### 2.3 Correctness Verification

All kernel variants were cross-checked against a CPU reference implementation. The maximum absolute error threshold was 2×10⁻⁸ for head_dim=64 and 1.391×10⁻⁵ for head_dim=128 split-prefetch kernels.

### 2.4 Occupancy Measurement

Active blocks per SM were recorded for each kernel variant using CUDA occupancy query APIs, providing a direct diagnosis mechanism for shared-memory-induced occupancy collapse.

---

## 3. Results

### 3.1 Compile-Path and Runtime Feasibility

The sm_121 target was accepted by nvcc 13.0.88. Generated PTX contained `cp.async.bulk.tensor.2d.shared::cta.global.tile.mbarrier::complete_tx::bytes` for `.target sm_121`. Runtime execution on GB10 confirmed compute capability 12.1 and `compiled___CUDA_ARCH__=1210`. The feature macro `__CUDA_ARCH_FEAT_SM121_ALL` was not defined in the simple probe.

The CUtensorMap-backed runtime roundtrip succeeded with zero mismatches over 1000 launches. Average kernel time on a 16×16 integer tile was 2.073 μs, yielding an effective bandwidth of 0.988 GB/s—dominated by per-launch overhead on the tiny 1 KiB tile.

### 3.2 TMA vs. Fallback Microbenchmark

| Tile | Stages | TMA (μs) | Fallback (μs) | TMA/Fallback |
|------|--------|----------|---------------|--------------|
| 16×16 | 1 | 2.073 | 2.065 | 1.004× |
| 16×16 | 4 | 7.194 | 4.123 | 0.573× |
| 16×16 | 16 | 28.77 | 16.22 | 0.564× |
| 32×32 | 1 | 4.085 | 4.095 | 0.998× |
| 32×32 | 4 | 5.914 | 4.897 | 1.208× |
| 32×32 | 16 | 23.57 | 16.39 | 1.438× |
| 64×64 | 1 | 4.094 | 8.186 | 1.999× |
| 64×64 | 4 | 6.153 | 8.185 | 1.330× |
| 64×64 | 16 | 15.14 | 8.197 | 0.541× |

TMA roughly ties or exceeds the fallback at 32×32 and clearly wins at 64×64 for low-to-moderate per-tile work. TMA loses on small tiles with heavy work and on large tiles with very heavy work, where the single roundtrip barrier pattern cannot amortize setup overhead.

### 3.3 Forward Attention Scaffold (head_dim=64, seq_len=4096)

| Kernel | Avg Time (μs) | Speedup vs Fallback | Active Blocks/SM | Shared Mem |
|--------|---------------|---------------------|-------------------|------------|
| Single-stage TMA | 314.3 | 2.84× | 2 | 33,920 B static |
| Full ping-pong pipeline | 682.8 | 1.31× | 1 | 1,152 B static + 65,536 B dynamic |
| K-prefetch-only | 751.7 | 1.19× | 1 | (dynamic shared) |
| Sliced 32×64 pipeline | 346.2 | 2.58× | 2 | (reduced footprint) |
| Non-TMA fallback | 893.4 | 1.00× | 2 | 33,800 B static |

All kernels matched the CPU reference at max_abs_err = 2×10⁻⁸. Approximate throughput: TMA kernel 0.216 TFLOPS, fallback 0.075 TFLOPS.

**Key negative result:** The full ping-pong pipeline and K-prefetch-only variants regressed to 0.41–0.45× of single-stage TMA despite using TMA loads. Occupancy data confirms the mechanism: the additional staging buffers increased shared-memory footprint beyond the threshold for 2 blocks/SM, collapsing residency to 1 block/SM.

**Partial recovery:** The sliced 32×64 pipeline preserved 2 active blocks/SM and recovered to 0.91× of single-stage TMA (2.58× vs fallback), demonstrating that the regression was primarily occupancy-driven rather than indicating a fundamental limitation of overlap on sm_121.

### 3.4 head_dim=128 Retuned Results (seq_len=131072, query_count=4)

The initial head_dim=128 configuration with tile64/slice64 produced a severely regressed result (8,167.37 μs). Retuning to tile64/slice32 with query_group=1:

| Configuration | Avg Time (μs) | Speedup vs FA3 | Max Abs Err |
|---------------|---------------|----------------|-------------|
| Split-prefetch tile64/slice32 | 952.9 | 4.48× | 1.391×10⁻⁵ |
| Split-prefetch tile64/slice16 | 1,232.98 | 3.47× | 1.391×10⁻⁵ |
| Patched FA3 baseline | 4,272.6 | 1.00× | — |
| Earlier tile64/slice64 (losing) | 8,167.4 | 0.52× | — |

The split-prefetch partials time was 951.2 μs with a 4.07 μs reduce step. The winning slice32 point is 8.57× faster than the earlier losing slice64 configuration.

**Constraint:** QUERY_GROUP=2 remains unsupported for head_dim=128; both attempted builds fail the compile-time constraint `kThreadsPerQuery >= kHeadDim`.

---

## 4. Limitations

1. **Single-GPU, single-architecture results.** All measurements are from one NVIDIA GB10 GPU (cc 12.1). Generalization to other Blackwell variants (e.g., B200, B100) or future architectures is not established.

2. **Forward-only, single-head kernels.** The attention scaffolds implement only the forward pass for a single attention head. Backward-pass behavior, multi-head configurations, and multi-query/grouped-query attention beyond the limited query_group settings tested are not covered.

3. **Baseline comparison scope.** The head_dim=64 comparison is against an in-project non-TMA fallback scaffold, not against upstream FlashAttention-3. The head_dim=128 comparison is against a patched FA3 baseline adapted for sm_121, not the original unmodified FA3 codebase. The patching methodology may affect baseline performance.

4. **Limited configuration coverage at head_dim=128.** The 4.48× result is measured at a single operating point: seq_len=131072, query_count=4, tile64/slice32, query_group=1. Broader query-count and sequence-length coverage at head_dim=128 was not completed before project closure.

5. **No tensor-core integration.** The kernels use TMA for data movement but do not integrate Blackwell tensor-core MMA operations. The reported throughput (0.216 TFLOPS for the best head_dim=64 kernel) is far below hardware peak, indicating that math throughput, not memory, may become the bottleneck with tensor-core integration.

6. **Pipelining does not beat single-stage TMA at head_dim=64.** The best pipelined variant (sliced 32×64) achieves only 0.91× of single-stage TMA. True warp-specialized producer/consumer overlap—where one warp group issues TMA loads while another performs math—was not implemented. The remaining ~9% gap may close with such a design, but this is not demonstrated.

7. **Occupancy-driven performance cliffs.** The results show that shared-memory budget is the primary design constraint on GB10 for attention kernels. Kernels that exceed the occupancy threshold for 2 blocks/SM suffer severe regressions (up to 2.4× slowdown). This constraint is architecture-specific and may differ on GPUs with different shared-memory capacities.

8. **No end-to-end model-level evaluation.** The benchmarks measure isolated kernel latency, not end-to-end training or inference throughput in a transformer model.

---

## 5. Reproducibility Checklist

- **Hardware specified:** NVIDIA GB10, compute capability 12.1.
- **Software specified:** CUDA 13.0 (nvcc 13.0.88), CUTLASS (cloned local snapshot with SM121 macros active).
- **Source files available:** `src/sm121_tma_smoke.cu`, `src/sm121_toolchain_probe.cu`, `src/sm121_tma_runtime_probe.cu`, `src/sm121_tma_vs_fallback_bench.cu`, `src/sm121_attention_scaffold_bench.cu`.
- **Runner scripts available:** `scripts/run_sm121_tma_probe.sh`, `scripts/run_sm121_tma_runtime_probe.sh`, `scripts/run_sm121_tma_vs_fallback_bench.sh`, `scripts/run_sm121_attention_scaffold_bench.sh`, `scripts/run_sm121_attention_scaffold_sweep.sh`, `scripts/run_fa3_sm121_patch_probe.sh`, `scripts/run_fa3_sm121_baseline_probe.sh`.
- **Durable result artifacts captured:** PTX disassembly, SASS disassembly, build logs, runtime logs, metadata JSON, and summary Markdown files for each experiment phase (see Referenced Artifacts).
- **Random seeds:** Not applicable; all kernels are deterministic.
- **Statistical reporting:** Latency values are averages over 10–1000 repeated launches depending on the experiment phase. No confidence intervals are reported; variance was not captured in the durable artifacts.
- **Correctness verification:** All kernel outputs verified against CPU reference implementations with max_abs_err thresholds reported per configuration.

---

## 6. Conclusion

This investigation establishes that sm_121 TMA on the NVIDIA GB10 GPU is functionally correct and can deliver substantial speedups for attention kernels when staging footprints are carefully tuned to preserve occupancy. The strongest result—a 4.48× speedup over a patched FlashAttention-3 baseline at seq_len=131072, head_dim=128—demonstrates that the sm_121 TMA mechanism is viable for long-context attention workloads.

However, the results also reveal a critical design constraint: naive pipelining that increases shared-memory usage beyond the occupancy threshold for 2 blocks/SM causes severe regressions (up to 2.4× slower than single-stage TMA). The occupancy collapse mechanism was directly confirmed via active-blocks-per-SM measurements. A reduced-footprint sliced double-buffer design recovered most of the lost performance but still did not exceed single-stage TMA at head_dim=64, suggesting that true warp-specialized producer/consumer overlap—rather than buffer duplication alone—is necessary to realize further gains.

The current project artifacts support the finding that sm_121 TMA pipelining is a viable mechanism for attention acceleration on GB10 in the tested setting. The project decision recommends branching a follow-on effort to generalize the validated head_dim=128 tile64/slice32 split-prefetch kernel across more query counts and to integrate Blackwell tensor-core MMA operations, which the current scaffolds do not use.

---

## Referenced Artifacts

### Project Decision
- `.omx/project_decision.json`

### Run Documentation
- `run_notes.md`
- `docs/source_map.md`

### Source Code
- `src/sm121_tma_smoke.cu`
- `src/sm121_toolchain_probe.cu`
- `src/sm121_tma_runtime_probe.cu`
- `src/sm121_tma_vs_fallback_bench.cu`
- `src/sm121_attention_scaffold_bench.cu`

### Scripts
- `scripts/run_sm121_tma_probe.sh`
- `scripts/run_sm121_toolchain_probe.sh`
- `scripts/run_sm121_tma_runtime_probe.sh`
- `scripts/run_sm121_tma_vs_fallback_bench.sh`
- `scripts/run_sm121_attention_scaffold_bench.sh`
- `scripts/run_sm121_attention_scaffold_sweep.sh`
- `scripts/run_fa3_sm121_patch_probe.sh`
- `scripts/run_fa3_sm121_baseline_probe.sh`

### Result Summaries
- `results/sm121_hd128_split_retune_summary.md`
- `results/sm121_hd128_long_context_comparison_summary.md`
- `results/sm121_slice64_parallelsoftmax_query_sweep_summary.md`
- `results/sm121_q16_slice64_split_partial_threads_summary.md`
- `results/sm121_parallel_split_softmax_summary.md`
- `results/sm121_q16_slice64_voverlap_summary.md`
- `results/sm121_q16_slice_sweep_summary.md`
- `results/sm121_split_group_q2_crossover_recheck_summary.md`
- `results/sm121_split_group_q16_summary.md`
- `results/sm121_grouped_query_parallel_q16_summary.md`
- `results/sm121_grouped_query_reuse_q16_summary.md`
- `results/sm121_q16_tile128_vslice_summary.md`
- `results/sm121_q16_vprefetch_summary.md`
- `results/sm121_q16_split_threads64_summary.md`
- `results/sm121_q16_threads64_vs_fa3_summary.md`

### Detailed Result Directories
- `results/sm121_attention_scaffold_bench_seq69888_q16_tile128_split_auto_threads64/` (summary.md, metadata.json, sass.txt, ptx.txt, run.log)
- `results/sm121_tma_probe/`
- `results/sm121_tma_runtime_probe/`
- `results/sm121_tma_vs_fallback_bench/`
- `results/sm121_attention_scaffold_bench/`

### Paper Artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
