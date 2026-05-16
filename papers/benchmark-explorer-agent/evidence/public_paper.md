# Benchmark Explorer Agent: Autonomous Discovery of Non-Monotonic Thread-Count Optima on GB10 CPU/OpenBLAS GEMM

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, log summaries, and metrics). The operator who released this artifact claims no personal authorship credit for the writing or scientific results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism. No human reviewer has endorsed the claims herein.

---

## Abstract

We describe a minimal autonomous benchmark explorer that, within a bounded budget on a single NVIDIA GB10 aarch64 host, discovers actionable performance structure in CPU/OpenBLAS GEMM workloads. The explorer executes a four-phase protocol—smoke test, calibration, first-pass grid exploration, and repeat-neighbor validation—and produces durable metrics and recommended next runs. On the GB10 platform (20 logical CPU cores, approximately 122 GiB available RAM, no swap), the explorer found that 8 OpenBLAS threads consistently outperformed both lower and higher thread counts across matrix sizes n = 512, 1024, and 2048, with the effect strongest at n = 2048 (mean 1010.8 GFLOP/s at 8 threads versus 676.3 GFLOP/s at 16 threads and 733.9 GFLOP/s at 20 threads). Repeat validation corrected a noisy first-pass optimum at n = 512 (initially suggesting 20 threads, revised to 8 threads), demonstrating the necessity of the validation loop. These results support the viability of the benchmark-explorer mechanism for CPU GEMM settings on this platform but do not address GPU or model-inference workloads. Total wall-clock time for all phases was 43.39 seconds. The study is limited to a single host, a single benchmark family, and a scripted (non-adaptive) exploration strategy.

## Introduction

Performance tuning of numerical kernels on heterogeneous platforms often requires selecting thread counts, matrix sizes, and library configurations that interact non-trivially with hardware topology. Manual benchmarking is time-consuming and error-prone, particularly when optima are non-monotonic—i.e., when adding threads degrades performance past a threshold that is not simply "all available cores."

We investigate whether a minimal autonomous benchmark explorer can, within a small time budget, (1) design and execute a bounded benchmark on a single host, (2) discover actionable performance structure, (3) explain variance across configurations, and (4) propose concrete next runs. The scope is deliberately limited: we target CPU/OpenBLAS GEMM on one GB10 aarch64 host, not GPU inference or multi-node scaling.

The central empirical question is whether the explorer's four-phase protocol (smoke → calibrate → explore → repeat-validate) can produce discoveries that survive replication, particularly when first-pass results are noisy. This is a toy-scale validation of the mechanism, not a production benchmarking system.

## Method

### Platform

All experiments ran on a single NVIDIA GB10 aarch64 host with the following characteristics:

- **CPU:** 20 logical cores (full `lscpu` details recorded in `logs/00_environment.log`).
- **Memory:** Approximately 122 GiB available throughout; swap disabled (SwapTotal = 0 KiB).
- **GPU:** NVIDIA GB10 present via `nvidia-smi` but intentionally idle (0% utilization recorded in all phases). This experiment targeted CPU/OpenBLAS GEMM exclusively.
- **Kernel:** `6.17.0-1014-nvidia` (aarch64).
- **Software:** Python 3 with NumPy (OpenBLAS backend) and psutil. No additional dependencies were installed.

### Explorer Protocol

The benchmark explorer (`scripts/benchmark_explorer.py`) implements a four-phase protocol:

1. **Smoke test.** A single GEMM run confirms the environment is functional. Result: 1/1 pass.
2. **Calibration.** Five runs at a default configuration verify timing stability and telemetry collection. Result: 5/5 pass.
3. **First-pass exploration.** A scripted grid search varies OpenBLAS thread count and matrix size (dtype float32). Each configuration is run in a subprocess so that `OPENBLAS_NUM_THREADS` takes effect per-run. The explorer records per-run GFLOP/s, CPU utilization, RSS, MemAvailable, and NVIDIA GPU telemetry to JSONL. Result: 33/33 runs in 19.04 s wall-clock.
4. **Repeat-neighbor validation.** A separate script (`scripts/repeat_best_neighbors.py`) re-runs the discovered optima and their neighbors 5× each to assess stability. Result: 60/60 runs in 24.35 s wall-clock.

### Configuration Space

The exploration grid covered matrix sizes n ∈ {512, 1024, 2048} and OpenBLAS thread counts from 1 to 20 (select values). All GEMM operations used float32. The number of inner repetitions varied by phase: 12 for exploration, 20 for the best repeat configuration.

### Metrics

**Primary metric:** GFLOP/s (giga floating-point operations per second), computed as 2n³ / (wall-clock seconds × 10⁹) for each GEMM of size n × n.

**Secondary telemetry:** CPU utilization percentage, process RSS, `/proc/meminfo` MemAvailable, and `nvidia-smi` GPU utilization, all recorded per run to JSONL.

### Validation Strategy

The repeat-neighbor phase serves two purposes: (1) confirm that first-pass optima are not artifacts of timing noise, and (2) check whether near-optimal configurations are competitive. A discovery is considered "stable" if the best thread count from the repeat phase matches the first-pass finding, and "corrected" if repeat evidence changes the recommendation. This distinction is important because a corrected optimum is evidence that the validation loop adds value beyond the first pass.

## Results

### First-Pass Exploration

The first-pass grid search (33 runs, 19.04 s wall-clock) identified the following best configurations:

| Matrix size (n) | Best threads (first-pass) | Peak GFLOP/s |
|---|---|---|
| 512 | 20 | Noisy; corrected in repeat phase |
| 1024 | 8 | 942.5 |
| 2048 | 8 | 981.0 |

The overall best first-pass configuration was n = 2048, threads = 8, at 981.043 GFLOP/s.

### Repeat-Neighbor Validation

After repeating optima and neighbors 5× each (60 runs, 24.35 s wall-clock), the stable results were:

| n | Best threads (repeat) | Mean GFLOP/s | Stdev GFLOP/s | Min | Max | Speedup vs. worst mean |
|---|---|---|---|---|---|---|
| 512 | 8 | 600.8 | 84.5 | 479.1 | 682.5 | 1.41× |
| 1024 | 8 | 886.4 | 85.1 | 735.4 | 942.5 | 1.71× |
| 2048 | 8 | 1010.8 | 10.8 | 1000.1 | 1023.2 | 1.92× |

The peak single repeat was 1023.158 GFLOP/s at n = 2048, threads = 8.

### Key Discovery: Non-Monotonic Thread Optimum

The most salient finding is that 8 OpenBLAS threads consistently outperformed all other thread counts, including the full 20-core allocation, across all three matrix sizes in the repeat phase. The penalty for oversubscription is substantial:

- At n = 2048: 8 threads → 1010.8 GFLOP/s mean; 16 threads → 676.3 GFLOP/s; 20 threads → 733.9 GFLOP/s.
- The 8-thread optimum represents a 1.92× speedup over the worst repeated mean at n = 2048.

This non-monotonic behavior is consistent with known OpenBLAS thread-scheduling overhead and cache-coherence effects on many-core aarch64 systems. The specific crossover at 8 threads (rather than, say, 10 or 12) likely reflects the GB10's core-cluster topology, though we did not independently verify the topology mapping in this run.

### First-Pass Correction at n = 512

The first-pass exploration at n = 512 suggested 20 threads as optimal. Repeat validation corrected this to 8 threads, with the first-pass result attributable to high variance at small matrix sizes (stdev/mean ≈ 14% at n = 512, versus ≈ 1.1% at n = 2048). This correction is a concrete demonstration that the repeat-validation phase is necessary for small-workload benchmarks where timing noise is high relative to the signal. It also serves as a negative result for the first-pass explorer in isolation: without repeat validation, the explorer would have produced a misleading recommendation at n = 512.

### Resource Utilization

MemAvailable remained above 122 GiB throughout (ending at 122,304,140 KiB). Swap was not required (SwapTotal = 0 KiB). GPU utilization was 0% by design. No runs failed in any phase (0/33 exploration failures, 0/60 repeat failures).

### Discovery Rate

The bounded run produced 5 distinct discoveries in 43.39 s total wall-clock time. Extrapolated linearly, this yields approximately 9,956 discoveries/day. This figure is a sanity check on mechanism throughput, not a production KPI; it assumes a continuous supply of similarly structured benchmark surfaces, which is not realistic for most workflows.

## Limitations

1. **CPU GEMM only; no model inference workload.** No llama.cpp, vLLM, or other inference framework was exercised. The results speak to the benchmark-explorer mechanism and OpenBLAS thread-count tuning, not to GPU inference performance or end-to-end model serving. The GB10 GPU was present but intentionally unused.

2. **Single host, no cross-machine replication.** All results are from one GB10 aarch64 machine. The 8-thread optimum may not generalize to other topologies, core counts, or OpenBLAS builds. No replication on a second machine was performed.

3. **Scripted (non-adaptive) exploration.** The first-pass explorer uses a fixed grid rather than adaptive selection. A more capable version would choose runs based on marginal information gain, track uncertainty explicitly, and stop early when the confidence interval on the optimum narrows. The current prototype does not implement these strategies.

4. **No independent manual baseline.** A fixed-grid timing sweep serves as a provisional baseline context, but no independent manual or control-plane baseline was available locally for direct comparison of explorer efficiency versus human-driven tuning. Claims about the explorer's efficiency relative to manual benchmarking are therefore unsupported.

5. **High variance at small matrix sizes.** The n = 512 results (stdev/mean ≈ 14%) are too noisy for confident optimization. The repeat phase mitigates but does not eliminate this uncertainty. The corrected optimum at n = 512 should be treated with more caution than the n = 2048 result.

6. **No GPU offload sweep.** The GB10 GPU was present but unused. The explorer's behavior under mixed CPU/GPU workloads is untested.

7. **Claim ledger is empty.** The formal claim ledger for this paper contains no registered claims at the time of draft generation, limiting the auditability of specific quantitative assertions beyond what is recorded in the run notes and summary JSONs.

8. **First-pass explorer is not a full LLM planning agent.** The evidence supports the control/verification loop shape (smoke → calibrate → explore → repeat-validate), not mature autonomy in experiment design.

## Reproducibility Checklist

- [x] **Platform described:** GB10 aarch64, 20 cores, approximately 128 GiB RAM, kernel 6.17.0-1014-nvidia.
- [x] **Software environment specified:** Python 3, NumPy with OpenBLAS backend, psutil. Full `lscpu` in `logs/00_environment.log`.
- [x] **Source code available:** `scripts/benchmark_explorer.py`, `scripts/repeat_best_neighbors.py`.
- [x] **Raw data preserved:** JSONL logs (`logs/benchmark_explorer_explore.jsonl`, `logs/benchmark_explorer_repeat.jsonl`), CSV metrics (`results/benchmark_explorer_metrics.csv`).
- [x] **Summary artifacts preserved:** JSON summaries for smoke, calibration, exploration, and repeat phases.
- [x] **Command lines recorded:** All four phases documented with exact invocations in run notes.
- [x] **Stdout/stderr captured:** `logs/01_smoke.log`, `logs/02_calibrate.log`, `logs/03_explore.log`, `logs/04_repeat.log`.
- [x] **Random seeds:** Not applicable (deterministic GEMM; no stochastic sampling).
- [x] **Negative results reported:** First-pass n = 512 optimum correction documented; high variance at small sizes noted.
- [ ] **Cross-machine replication:** Not performed (single-host study).
- [ ] **GPU workload tested:** Not performed (CPU-only by design).
- [ ] **Independent manual baseline:** Not available locally.

## Conclusion

A minimal autonomous benchmark explorer, running a smoke → calibrate → explore → repeat-validate protocol on a single GB10 host, discovered a robust non-monotonic thread-count optimum for OpenBLAS GEMM: 8 threads outperformed all other counts including the full 20-core allocation, with the effect strongest at n = 2048 (1.92× speedup over worst repeated mean). Repeat validation corrected a noisy first-pass optimum at n = 512, confirming that the validation loop is necessary when timing variance is high. Total wall-clock time was 43.39 seconds with zero failed runs across all phases.

These results support the viability of the benchmark-explorer mechanism for bounded CPU GEMM tuning on this platform. The project decision records the hypothesis status as "supported on bounded GB10 CPU benchmark" with medium confidence and moderate evidence strength. However, the study does not address GPU inference, model serving, multi-host scaling, or adaptive exploration strategies. The recommended next step is to extend the explorer to actual local inference workloads (e.g., llama.cpp prompt throughput sweeps across context length, batch size, thread count, and GPU offload layers), using the same four-phase protocol with a manual fixed-grid baseline for comparison.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Explorer script | `scripts/benchmark_explorer.py` |
| Repeat-validation script | `scripts/repeat_best_neighbors.py` |
| Environment log | `logs/00_environment.log` |
| Smoke log | `logs/01_smoke.log` |
| Calibration log | `logs/02_calibrate.log` |
| Exploration log | `logs/03_explore.log` |
| Repeat log | `logs/04_repeat.log` |
| Exploration JSONL | `logs/benchmark_explorer_explore.jsonl` |
| Repeat JSONL | `logs/benchmark_explorer_repeat.jsonl` |
| Smoke summary | `results/benchmark_explorer_smoke_summary.json` |
| Calibration summary | `results/benchmark_explorer_calibrate_summary.json` |
| Exploration summary | `results/benchmark_explorer_summary.json` |
| Repeat summary | `results/benchmark_explorer_repeat_summary.json` |
| Metrics CSV | `results/benchmark_explorer_metrics.csv` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T194518609429+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T194518609429+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T194518609429+0000/paper_manifest.json` |
