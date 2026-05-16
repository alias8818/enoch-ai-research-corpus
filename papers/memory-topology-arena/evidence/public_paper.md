# Memory Topology Arena: Contiguous Index vs. Scattered Pointer Traversal on GB10-Class UMA Hardware

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, calibration metrics, hardware-counter summaries, and a project decision ledger). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed the claims herein.

---

## Abstract

We present a reproducible C microbenchmark evaluating how memory topology affects linked-cycle traversal throughput on an NVIDIA GB10 system operating under a single-node UMA memory model. Three topologies are compared: (1) a contiguous arena with sequential index traversal, (2) a contiguous arena with random-cycle index traversal, and (3) a scattered `malloc`-per-node pointer graph with the same random-cycle structure. At 10 million nodes, sequential arena traversal achieves 1.75 ns/step (570 Msteps/s), while random-cycle arena traversal degrades to 107 ns/step (9.35 Msteps/s)—a 61× slowdown. The malloc pointer topology adds a further 1.12× slowdown at this scale and consumes 3.64× the resident memory. At intermediate scales (1M nodes), however, the malloc penalty is 4.87×, indicating that allocator overhead and TLB pressure dominate before the working set fully exceeds cache. Hardware counter data from the ARM PMU domain shows that the malloc topology exhibits a *lower* reported cache-miss ratio (5.4%) than the random arena (17.5%) at 1M nodes, yet incurs 3.7× more cycles per step, suggesting that the selected PMU events on this platform do not fully capture the miss costs (e.g., TLB misses, page-table walks) that disproportionately affect scattered allocations. These results confirm that memory locality dominates traversal throughput on this UMA host, and that contiguous arena indexing provides meaningful memory savings and throughput gains for random-cycle traversals at small-to-medium scales, but cannot compensate for the loss of algorithmic locality at very large working sets.

## Introduction

Memory access patterns are a well-known determinant of performance on modern hardware. Prefetchers, cache hierarchies, and TLBs reward contiguous and predictable access, while pointer-chasing through scattered allocations penalizes throughput. Despite broad understanding of these effects, quantifying their magnitude on specific hardware under controlled conditions remains valuable for system design—particularly on emerging UMA-class SoCs where CPU and GPU share a unified memory pool.

This study asks: can a small local arena benchmark produce actionable evidence about memory topology effects on GB10-class UMA hardware, specifically whether contiguous arena/index topologies outperform scattered pointer topologies under equivalent linked-cycle traversal?

We implement a minimal C11 microbenchmark comparing three traversal topologies over the same logical cycle structure, measure wall-clock throughput and resident memory across four problem sizes, and supplement with ARM PMU hardware counter data. The benchmark is deliberately confined to the CPU side of the UMA system; CUDA-managed memory behavior is identified as a separate target requiring its own harness.

The contribution is a controlled, reproducible quantification of topology effects on a specific UMA platform, with an unexpected finding regarding PMU counter coverage: the standard `perf` cache-miss events on this ARM platform appear to undercount the true cost of scattered allocations relative to contiguous ones.

## Method

### Platform

All measurements were collected on an NVIDIA GB10 system running Linux 6.17.0-1014-nvidia (aarch64). The host reports 20 CPU cores and 127,535,908 kB total memory. `numactl --hardware` reports a single NUMA node. Swap was intentionally disabled (SwapTotal: 0 kB) to ensure that memory pressure manifests as RSS growth rather than swap activity. GPU-side memory accounting via `nvidia-smi` reports "Not Supported" for this platform, so all memory measurements rely on `/proc/meminfo` and per-process RSS.

### Benchmark Design

The benchmark (`src/memory_topology_arena.c`) implements three topologies over a logical cycle of *N* nodes:

1. **`index_arena_sequential`** — A contiguous array of *N* node structs. The next-pointer is the numerically next index (`i + 1`, wrapping). This represents optimal spatial and temporal locality.

2. **`index_arena_random_cycle`** — The same contiguous array, but the next-pointer for each node is assigned via a Fisher-Yates shuffle that guarantees a single Hamiltonian cycle visiting every node exactly once. This preserves spatial contiguity of the allocation but destroys sequential access order.

3. **`malloc_pointer_random_cycle`** — Each node is individually `malloc`-ed. Pointers follow the same class of shuffled cycle. This destroys both spatial contiguity and sequential order, representing the worst-case topology among the three.

All three topologies traverse the same number of nodes per round. The traversal kernel is a simple loop following the next-pointer until it returns to the start node. No computation is performed beyond pointer dereference.

### Build and Execution

The source was compiled with:

```
gcc -O3 -march=native -std=c11 -Wall -Wextra -Werror \
    src/memory_topology_arena.c -o memory_topology_arena
```

A deterministic seed (34336771) was used for all runs to ensure reproducible shuffle order.

### Measurement Protocol

**Calibration runs** varied node count and rounds:

| Nodes        | Rounds |
|--------------|--------|
| 100,000      | 10     |
| 1,000,000    | 5      |
| 5,000,000    | 3      |
| 10,000,000   | 2      |

Wall-clock time per step and max RSS after build were recorded for each topology and scale.

**Hardware counter runs** used `perf stat` at 1M nodes, 5 rounds, recording `cycles`, `instructions`, `cache-references`, and `cache-misses` for each topology individually. The PMU domain on this platform is `armv8_pmuv3_1`.

### Reproduction Steps

The project provides `Makefile` targets:

- `make smoke` — Build and run a small sanity check (10k nodes, 3 rounds).
- `make calibrate` — Run the full calibration matrix.
- `make perf` — Run the hardware counter probe.

## Results

### Throughput and Memory at 10M Nodes

| Topology              | ns/step | Msteps/s | Max RSS (kB) |
|-----------------------|---------|----------|--------------|
| Sequential arena      | 1.754   | 570.0    | 79,404       |
| Random-cycle arena    | 107.005 | 9.35     | 118,528      |
| Malloc random-cycle   | 120.187 | 8.32     | 431,012      |

The sequential arena is 60.99× faster than the random-cycle arena. The malloc topology is 1.12× slower than the random arena at this scale, while consuming 3.64× the resident memory.

### Scale-Dependent Slowdown

The slowdown of random-cycle arena relative to sequential arena grows with working set size:

| Nodes         | Random arena vs. sequential slowdown |
|---------------|--------------------------------------|
| 100,000       | 2.20×                                |
| 1,000,000     | ~12.77× (derived from perf data)    |
| 10,000,000    | 60.99×                               |

The malloc penalty relative to the random arena shrinks with scale:

| Nodes         | Malloc vs. random arena slowdown |
|---------------|----------------------------------|
| 1,000,000     | 4.87×                            |
| 10,000,000    | 1.12×                            |

At 1M nodes, the malloc topology is nearly 5× slower than the random arena, suggesting that allocator overhead and TLB effects from scattered pages are significant when the working set is still partially cache-friendly. At 10M nodes, both random topologies are dominated by the cost of random access to a working set far exceeding cache, and the allocator penalty becomes a secondary factor. This crossover is an important negative result for any design strategy that relies on arena allocation alone to rescue random-access performance at large scales.

### Hardware Counters at 1M Nodes

| Topology       | ns/step | Cycles         | Cache-miss ratio |
|----------------|---------|----------------|------------------|
| Sequential     | 1.73    | 51,896,761     | 1.09%            |
| Random arena   | 22.09   | 469,397,040    | 17.52%           |
| Malloc random  | 104.52  | 1,733,265,966  | 5.4%             |

The malloc topology reports a *lower* cache-miss ratio (5.4%) than the random arena (17.5%), yet requires 3.7× more cycles and is 4.7× slower in wall time. This apparent contradiction is the most notable mixed finding in this study. The most plausible explanation is that the `armv8_pmuv3_1` PMU event domain on this platform does not fully capture the hierarchy of miss costs relevant to scattered allocations: TLB misses, page-table walks, and possibly cache-miss events at levels not instrumented by the selected `perf` events may contribute substantially to the malloc topology's overhead without being reflected in the reported cache-miss ratio. The raw perf logs are preserved for further analysis, but we cannot resolve this discrepancy with the available counter data.

### Memory Footprint

The contiguous arena topologies use substantially less resident memory than the malloc topology at all measured scales. At 10M nodes, the random arena uses 118,528 kB versus 431,012 kB for the malloc topology—a 3.64× difference attributable to per-allocation metadata and alignment padding in the glibc allocator. The sequential arena is slightly more compact still (79,404 kB), likely because its simpler access pattern requires fewer allocator bookkeeping structures during the build phase.

## Limitations

1. **CPU/UMA only.** This benchmark exercises the CPU memory path exclusively. CUDA-managed memory behavior, GPU-side traversal, and unified-memory migration effects are not measured. Scientific closure for cross-GPU/CPU or CUDA-managed-memory behavior requires a separate CUDA harness and longer utilization runs.

2. **Single platform.** All results are from one GB10 host with a single NUMA node. Multi-socket or multi-NUMA systems may exhibit different crossover points and different allocator behavior.

3. **PMU event coverage.** The `armv8_pmuv3_1` PMU domain on this platform provides limited event coverage for the selected `perf` events. The cache-miss ratios reported here should be interpreted as lower bounds on actual miss costs, particularly for the malloc topology where TLB and page-table effects are likely undercounted. The counter anomaly (lower reported miss ratio but higher cycle cost for malloc) is an unresolved limitation of the measurement apparatus.

4. **Allocator specificity.** The malloc results depend on the glibc allocator behavior on this platform. Other allocators (e.g., `jemalloc`, `tcmalloc`) may yield different RSS and throughput tradeoffs.

5. **No GPU memory accounting.** `nvidia-smi` memory usage reporting is not supported on this GB10 configuration, precluding direct GPU-side memory measurement.

6. **Synthetic workload.** The traversal kernel performs no computation beyond pointer dereference. Real workloads with per-node computation may dilute the observed topology effects, reducing the practical magnitude of the slowdowns reported here.

7. **Scale-dependent data is incomplete.** The calibration matrix covers four node counts, but the crossover behavior between 1M and 10M nodes (where the malloc penalty shrinks from 4.87× to 1.12×) is not sampled at intermediate points. The exact crossover scale is not determined.

8. **Model-authored draft.** This paper was generated by an AI system from automated research artifacts. The claim ledger records no independently audit-approved claims. Human review of both the analysis and the underlying data is recommended before relying on these results for design decisions.

## Reproducibility Checklist

- **Source code:** `src/memory_topology_arena.c`, `Makefile`, `scripts/*.sh`, `scripts/*.py` are present in the project directory.
- **Deterministic seed:** 34336771 for all runs.
- **Compiler and flags:** `gcc -O3 -march=native -std=c11 -Wall -Wextra -Werror`.
- **Platform:** NVIDIA GB10, Linux 6.17.0-1014-nvidia, aarch64, 20 cores, single NUMA node, swap disabled.
- **Host inventory log:** `artifacts/logs/host_inventory_20260501T181222Z.log`.
- **Calibration data:** `artifacts/metrics/calibration_20260501T183520Z.jsonl` (raw) and `artifacts/metrics/calibration_20260501T183520Z_summary.json` (summary).
- **Calibration log:** `artifacts/logs/calibration_20260501T183520Z.log`.
- **Perf data:** `artifacts/metrics/perf_20260501T183548Z_summary.json`.
- **Reproduction commands:** `make smoke`, `make calibrate`, `make perf`.
- **Randomness:** All shuffle order is deterministic given the fixed seed.
- **PMU raw logs:** Preserved in the artifacts directory for independent analysis of the counter anomaly.

## Conclusion

On this GB10 UMA host, memory topology is the dominant factor in linked-cycle traversal throughput. Sequential access through a contiguous arena is 61× faster than random-cycle access at 10M nodes. Contiguous arena indexing provides a meaningful advantage over scattered `malloc`-per-node allocation at small-to-medium scales (4.87× at 1M nodes) and a consistent 3.64× memory savings at all scales. However, once the working set far exceeds cache and TLB capacity, the random-access cost dominates regardless of allocation strategy, and the malloc penalty shrinks to 1.12×. This is a negative result for any approach that treats arena allocation as a sufficient remedy for random-access workloads at large scales.

The PMU counter anomaly—where the malloc topology reports a lower cache-miss ratio but substantially higher cycle cost than the random arena—highlights a measurement gap on this platform. The selected `perf` events do not fully account for the costs of scattered allocation, and practitioners should be cautious about relying on cache-miss ratios alone when comparing allocation strategies on ARM-based UMA systems.

These findings support a practical design principle: contiguous arena allocation should be preferred for pointer-chasing data structures when the working set may fit partially in cache, both for throughput and memory efficiency. For very large random-access working sets, algorithmic locality—preserving sequential or near-sequential access patterns—matters more than allocation strategy, and no amount of allocator optimization can substitute for topological locality.

The benchmark is reproducible and the raw data artifacts are preserved. Extending this work to CUDA-managed memory and GPU-side traversal on the same UMA hardware remains an open target.

## Referenced Artifacts

| Artifact              | Path |
|-----------------------|------|
| Source code           | `src/memory_topology_arena.c` |
| Build system          | `Makefile`, `scripts/*.sh`, `scripts/*.py` |
| Host inventory        | `artifacts/logs/host_inventory_20260501T181222Z.log` |
| Calibration raw data  | `artifacts/metrics/calibration_20260501T183520Z.jsonl` |
| Calibration summary   | `artifacts/metrics/calibration_20260501T183520Z_summary.json` |
| Calibration log       | `artifacts/logs/calibration_20260501T183520Z.log` |
| Perf summary          | `artifacts/metrics/perf_20260501T183548Z_summary.json` |
| Run notes             | `run_notes.md` |
| Project decision      | `.omx/project_decision.json` |
| Claim ledger          | `papers/source-record-redacted-20260501T181148597856+0000/claim_ledger.json` |
| Evidence bundle       | `papers/source-record-redacted-20260501T181148597856+0000/evidence_bundle.json` |
| Paper manifest        | `papers/source-record-redacted-20260501T181148597856+0000/paper_manifest.json` |
