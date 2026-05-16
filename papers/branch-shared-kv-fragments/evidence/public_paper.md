# Branch-Shared KV Fragments: Memory-Efficient Key-Value Cache Sharing for Branchy Decoding

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Branchy decoding—where multiple generation paths diverge from a shared prefix—arises in speculative decoding, beam search, and tree-of-thought inference. Each branch conventionally clones the full prefix key-value (KV) cache, producing memory that scales linearly with branch count. We investigate *branch-shared KV fragments*, a scheme in which the immutable prefix KV cache is stored once and referenced by all divergent branches via paged fragment descriptors, with each branch appending only its private suffix. Through CPU-side microbenchmarks on an NVIDIA GB10 (Grace-Blackwell) host and an analytical memory model, we find that fragment sharing reduces KV cache storage by 70–96% depending on branch count and prefix-to-suffix ratio. However, the performance picture is mixed: a naive adapter that materializes contiguous KV arrays from fragments before each attention step incurs 4.1–7.1× slowdown versus cloned contiguous arrays. A paged-attention-compatible path shows overhead that decreases sharply with page size (3.83× at 32 tokens, 1.09× at 256 tokens, 0.81× at 512 tokens), but these are CPU/NumPy isolation measurements and do not constitute GPU kernel validation. The sub-unity figure at 512 tokens falls within measurement noise and should not be interpreted as a speedup. We conclude that branch-shared KV fragments are a viable memory optimization only when paired with a paged or ragged KV attention backend that consumes fragment references directly; they are not viable as a drop-in layer that reconstructs contiguous per-branch KV each decode step.

## Introduction

Autoregressive transformer inference maintains a growing KV cache that dominates memory allocation for long sequences. When multiple decoding branches share a common prefix—as in speculative decoding, beam search, or parallel sampling—conventional implementations clone the entire prefix KV cache per branch. Since the prefix KV tensors are immutable once produced (the prefix tokens and their representations do not change), this cloning is redundant.

The core insight is straightforward: if the prefix is shared and immutable, its KV cache can be stored once and referenced via lightweight fragment descriptors, with each branch maintaining only its private suffix KV entries. This is analogous to copy-on-write page tables in operating systems, applied to the KV cache.

This paper examines the concrete trade-offs of this approach along three axes:

1. **Memory savings** are potentially large but depend critically on the ratio of shared prefix length to per-branch suffix length.
2. **Attention throughput** may be unaffected or degraded depending on whether the attention backend can consume paged fragment references or must materialize contiguous arrays.
3. **Fragment management overhead** (page lookup, indirection) varies with page granularity.

We report CPU-side microbenchmark results and an analytical memory model. GPU kernel-level validation remains an open task; the results here should be understood as prototype-level evidence for the memory model and CPU-side page overhead trends, not as production throughput measurements.

## Method

### Memory Model

We model KV cache memory for a transformer with fp16 precision, 32 layers, 8 KV heads, and head dimension 128. Under these parameters, each token requires 128 KiB for K and V tensors combined across all layers.

For $B$ branches sharing a prefix of $P$ tokens, each with a private suffix of $S$ tokens:

- **Cloned (baseline):** $B \times (P + S) \times 128 \text{ KiB}$
- **Shared + metadata:** $P \times 128 \text{ KiB} + B \times S \times 128 \text{ KiB} + \text{metadata overhead}$

Metadata overhead (page tables, reference counts) is small relative to the KV tensors and is omitted from the tabulated model for clarity, though it could erode savings at very small suffix lengths or very large page tables.

### Fragment Representation

The shared prefix KV is divided into fixed-size pages of $T_p$ tokens each. A fragment descriptor maps logical page indices to physical storage offsets. Branch-private suffixes are stored as contiguous append-only arrays. During attention, the effective KV sequence for a branch is the concatenation of shared prefix pages and the private suffix—logically, not physically.

### Benchmark Design

We implemented three access patterns for comparison:

1. **Cloned contiguous:** Each branch holds a full independent copy of prefix + suffix KV. Attention reads a single contiguous array. This is the baseline.
2. **Paged (no materialize):** Shared prefix is accessed via page descriptors; private suffix is appended logically. Attention operates over the paged representation directly.
3. **Materialize-then-attend:** Fragment descriptors are resolved into a contiguous temporary array before each attention step. This represents a naive drop-in adapter.

All benchmarks use NumPy on CPU (no GPU kernels). The host is an NVIDIA GB10 (Grace-Blackwell) system with 121 GiB RAM, 20 CPU cores, running Linux 6.17.0 on aarch64. No swap is configured. Maximum RSS observed via `/usr/bin/time` was 127 MiB; MemAvailable remained at 116.2 GiB throughout, confirming no memory pressure.

### Benchmark Configurations

**Smoke benchmark:** 4 branches, 256-token prefix, 64-token suffix per branch, 128 channels, 64-token pages, 2 repeats. Purpose: validate correctness and dependency availability.

**Medium benchmark:** 16 branches, 2048-token prefix, 256-token suffix per branch, 512 channels, 128-token pages, 5 repeats. Purpose: quantify overhead at a moderate scale.

**Page-size sweep:** Page sizes of 32, 64, 128, 256, and 512 tokens, measuring paged-access and materialization overhead relative to cloned contiguous access. Purpose: characterize page-granularity sensitivity.

## Results

### Memory Savings

The medium benchmark (16 branches, 2048+256 tokens, 512 channels) measured 83.3% storage savings: 72.0 MiB for the cloned configuration versus 12.0 MiB for the shared configuration.

The analytical memory model projects savings across several configurations:

| Branches | Prefix tokens | Suffix/branch | Cloned | Shared+metadata | Saving | Capacity multiplier |
|---------:|--------------:|--------------:|-------:|----------------:|-------:|-------------------:|
| 4 | 4,096 | 256 | 2.12 GiB | 0.63 GiB | 70.6% | 3.4× |
| 16 | 8,192 | 512 | 17.00 GiB | 2.00 GiB | 88.2% | 8.5× |
| 64 | 8,192 | 512 | 68.00 GiB | 5.00 GiB | 92.6% | 13.6× |
| 128 | 32,768 | 1,024 | 528.00 GiB | 20.00 GiB | 96.2% | 26.4× |

Savings increase with both branch count and prefix-to-suffix ratio. The 128-branch, 32K-prefix configuration reduces a 528 GiB requirement to 20 GiB—a 26.4× capacity multiplier. This is a model projection, not a live measurement at that scale; the medium benchmark (83.3% measured saving) provides empirical grounding at a smaller configuration.

### Access-Pattern Overhead

The medium benchmark (128-token pages) yielded:

- **Paged/no-materialize:** 1.75× slowdown versus cloned contiguous access.
- **Materialize-then-attend:** 7.14× slowdown versus cloned contiguous access.

Materialization is clearly impractical: the cost of copying fragment pages into a contiguous temporary array each decode step dominates. This result is consistent across all tested page sizes (see below).

### Page-Size Sensitivity

The page-size sweep reveals a strong dependence of paged-access overhead on page granularity:

| Page tokens | Paged slowdown | Materialize slowdown |
|------------:|---------------:|--------------------:|
| 32 | 3.83× | 5.76× |
| 64 | 3.58× | 6.33× |
| 128 | 1.87× | 5.11× |
| 256 | 1.09× | 6.32× |
| 512 | 0.81× | 4.15× |

Paged-access overhead decreases monotonically with larger pages, falling below 1.1× at 256 tokens and registering 0.81× at 512 tokens. The sub-1.0× figure at 512 tokens should not be interpreted as a true speedup; it falls within CPU/BLAS timing noise for these array sizes and reflects measurement granularity rather than a genuine performance improvement. The meaningful conclusion is that page-lookup overhead becomes negligible at page sizes of 256 tokens and above in this CPU isolation.

Materialization overhead remains high (4.15–6.33×) across all page sizes, confirming that materialization is not a viable strategy regardless of page granularity.

### Attention FLOP Consideration

Fragment sharing reduces storage but does not reduce attention FLOPs. Every live branch still attends to the full shared prefix during each decode step, meaning the prefix K/V bytes are read per branch. The memory savings are in *storage capacity*, not in *bandwidth consumed per decode step*, unless a higher-level algorithm prunes or batches prefix attention differently.

## Limitations

1. **CPU-only benchmarks.** All timing measurements were collected using NumPy on CPU cores. No GPU attention kernels were implemented or measured. The overhead figures (1.75×, 7.14×, etc.) reflect CPU array operations and may not transfer directly to GPU paged-attention kernels, which have different memory access patterns, caching behavior, and parallelism characteristics.

2. **No inference backend integration.** The benchmarks operate on synthetic KV arrays, not within a live inference framework. Effects such as scheduler interaction, garbage collection of dead branches, and copy-on-write refcount overhead were not measured.

3. **Synthetic workloads.** The prefix/suffix lengths and branch counts are parameter sweeps, not traces from real speculative-decoding or beam-search sessions. Real workloads may exhibit different prefix-to-suffix ratios and branch lifetime distributions.

4. **Metadata overhead not quantified.** The memory model omits page table and refcount storage. For very small suffixes or very large page tables, metadata could erode savings. This was not measured.

5. **The 0.81× paged-access figure is not a speedup.** This result is within measurement noise for the CPU/BLAS timing granularity at these array sizes and should not be cited as evidence that paged access is faster than contiguous access.

6. **Single host architecture.** Results are from an aarch64 GB10 host. x86 hosts, different BLAS libraries, or GPU-resident paged attention may exhibit different overhead profiles.

7. **No end-to-end latency measurement.** Tokens-per-second under real decoding workloads was not measured and cannot be inferred from these microbenchmarks.

8. **No GPU kernel validation.** These artifacts prove the memory model and CPU-side page overhead trend, not GB10 CUDA attention-kernel throughput. Final production closure requires integration with a specific inference backend and measuring tokens/s, UMA pressure, and GPU utilization on target workloads.

## Reproducibility Checklist

- **Hardware specified:** Yes — NVIDIA GB10 (Grace-Blackwell), aarch64, 20 CPU cores, 121 GiB RAM, no swap, CUDA 13.0 / Driver 580.142.
- **Software specified:** Yes — Linux 6.17.0-1014-nvidia, Python 3.12.3, NumPy, psutil (from pip install logs).
- **Benchmark scripts available:** Yes — `scripts/branch_shared_kv_bench.py`, `scripts/page_sweep.py`.
- **Random seeds:** Not applicable — benchmarks are deterministic array operations with no stochastic components.
- **Number of repeats stated:** Yes — smoke: 2 repeats; medium: 5 repeats; page sweep: as logged in per-page logs.
- **Full logs preserved:** Yes — see Referenced Artifacts.
- **Memory telemetry captured:** Yes — MemAvailable (116.2 GiB) captured by script; maximum RSS 127 MiB in `/usr/bin/time` logs.
- **Negative results reported:** Yes — materialization overhead (4.15–7.14×) and paged overhead at small page sizes (up to 3.83×) are reported.
- **Claim scope limited to evidence:** Yes — GPU kernel claims are explicitly deferred; memory model projections are labeled as such; the 0.81× figure is explicitly caveated.

## Conclusion

Branch-shared KV fragments offer substantial memory savings for branchy decoding scenarios—70–96% depending on configuration—by eliminating redundant storage of immutable prefix KV entries. However, these savings come with access-pattern constraints that are not automatically satisfied:

- **Materialization is impractical.** Reconstructing contiguous KV arrays from fragments before each attention step incurs 4.1–7.1× slowdown and negates the purpose of the optimization. This holds across all tested page sizes.
- **Paged access is conditionally viable.** When the attention backend natively supports paged or ragged KV access, overhead can be reduced to near-negligible levels at page sizes of 256 tokens or more (in CPU isolation). This requires backend integration, not a drop-in adapter layer.
- **Storage savings do not imply bandwidth savings.** Each branch still reads the full shared prefix during decode; the optimization targets capacity, not per-step compute or memory bandwidth.

The technique is **viable with constraints**: it should be implemented only behind a paged/ragged KV attention backend that consumes fragment references directly, with page sizes of at least 256 tokens for long prefixes. Copy-on-write fragment refcounts and live-branch garbage collection must be handled by the scheduler. GPU kernel validation—measuring actual tokens/s, UMA pressure, and GPU utilization on target workloads—remains necessary before production adoption.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Run notes | `run_notes.md` |
| Decision JSON | `.omx/project_decision.json` |
| Benchmark script | `scripts/branch_shared_kv_bench.py` |
| Page sweep script | `scripts/page_sweep.py` |
| Smoke results | `artifacts/smoke/branch_shared_kv_results.json` |
| Medium results | `artifacts/medium/branch_shared_kv_results.json` |
| Page sweep data | `artifacts/page_sweep/page_sweep.csv` |
| Environment log | `logs/000_env_modules.log` |
| Pip install log | `logs/002_pip_install_numpy_psutil.log` |
| Smoke bench log | `logs/010_smoke_bench.log` |
| Medium bench log | `logs/020_medium_bench.log` |
| Medium bench time | `logs/020_medium_bench.time` |
| Page sweep log | `logs/030_page_sweep.log` |
| Page sweep time | `logs/030_page_sweep.time` |
| Per-page logs | `logs/030_page_*.log` |
