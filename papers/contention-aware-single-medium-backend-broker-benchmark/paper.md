# Contention-Aware Single-Medium Backend Isolation in an LLM Serving Broker: A Live Benchmark Study

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We evaluate a contention-aware single-medium backend isolation policy for an OpenAI-compatible LLM serving broker and compare it against a shape-to-small routing baseline. In a live benchmark using two llama.cpp backends (small and medium) on a unified memory architecture GPU, the single-medium policy routes all measured traffic to the medium backend and applies a broker-side concurrency semaphore. Across a two-seed pressure sweep at concurrency levels 8 and 12 (24 requests per cell), the single-medium policy with cap=12 (matching the llama.cpp `--parallel 12` slot count) yielded a mean p95 latency improvement of 38.3% and a mean total throughput gain of 63.4% versus shape-to-small routing. The improvement is concentrated at c12 pressure (65.1% p95 improvement, 125.6% throughput gain), while c8 results are mixed: p95 improves by 11.4% but throughput is near-flat (mean +1.3%, with one seed showing a −1.4% regression). A cap-tuning grid at c12 shows that setting the concurrency cap below the backend slot count introduces broker-side queueing that degrades the isolation benefit. These results are specific to the tested hardware, model configuration, and workload; external replication is required before generalizing.

## 1. Introduction

LLM serving brokers that route requests across multiple backends of varying capacity face a fundamental contention problem: when a smaller backend shares accelerator resources with a larger backend, offloading requests to the small backend can degrade the performance of the medium backend through GPU memory and compute contention. A natural alternative is to isolate the medium backend entirely, routing all measured traffic to it and applying broker-side concurrency control to prevent over-subscription.

This study evaluates that alternative. We implement a `contention_medium_control` policy within an existing OpenAI-compatible broker harness and compare it against the parent `shape_broker` shape-to-small routing policy under controlled live pressure. The central question is whether single-medium backend isolation, combined with a broker-side concurrency semaphore, improves both p95 latency and total throughput relative to shape-to-small routing under concurrent load.

We report results from a two-seed pressure sweep at concurrency levels 8 and 12, plus a concurrency-cap tuning grid at c12. The results support the hypothesis at c12 pressure but reveal mixed throughput at c8, bounding the conditions under which the mechanism is beneficial.

## 2. Method

### 2.1 Broker Policies

Two policies are compared:

**Shape-to-small routing (`shape_broker`)**. The parent broker policy routes requests to backends based on request shape. Under the tested workload, this policy routes a subset of requests (4–5 out of 24 at c12) to the small backend, with the remainder directed to the medium backend.

**Contention-aware single-medium isolation (`contention_medium_control`)**. This policy routes all measured traffic to the medium backend exclusively, eliminating small-backend offload and the associated GPU contention. A broker-side semaphore (`--medium-control-cap`) enforces a concurrency ceiling on in-flight requests to the medium backend. When the cap is reached, additional requests queue at the broker rather than being dispatched.

### 2.2 Backend Configuration

Two llama.cpp server instances serve as backends:

- **Small backend**: a smaller model configuration (specific model identity preserved in backend logs).
- **Medium backend**: a larger model configuration.

Both backends share the same GPU under a unified memory architecture. The llama.cpp server parameters are:

| Parameter | Value |
|---|---|
| Context size | 16384 |
| Parallel slots | 12 |
| Batch size | 512 |
| Micro-batch size | 256 |
| GPU layers | 999 |
| Flash attention | Enabled |

### 2.3 Benchmark Harness

The benchmark is implemented in `contention_broker_benchmark.py` and driven by `contention_live_sweep.py`. Each benchmark cell issues 24 requests at a specified concurrency level. The harness records per-request latency, token counts, routing decisions, and aggregate metrics (p95 latency, total tokens per second). Backend logs, workload definitions, route events, and process telemetry are preserved per run.

### 2.4 Experimental Design

**Pressure sweep.** A two-seed (3473677, 3473678) sweep at concurrency levels 8 and 12, with `--medium-control-cap 12`, comparing both policies. This yields four benchmark cells per policy per seed.

**Cap-tuning grid.** At c12 only, a grid over semaphore caps 8, 10, and 12 across both seeds, comparing the single-medium policy against shape-to-small routing. This yields six cells per seed.

**Smoke test.** A preliminary smoke test at cap=3 confirmed that an aggressively low cap introduces visible queueing and underperforms, validating that the cap parameter requires tuning rather than being set arbitrarily low.

## 3. Results

### 3.1 Two-Seed Pressure Sweep (cap=12)

All four benchmark cells completed with no failures. Both policies completed 24/24 requests in every cell.

**Concurrency 8 (c8).** The single-medium policy improved p95 latency by a mean of 11.4% versus shape-to-small routing. Total throughput showed a mean gain of 1.3%, but one seed exhibited a −1.4% regression. The c8 throughput result is therefore mixed: latency improves modestly, while throughput is effectively flat.

**Concurrency 12 (c12).** The single-medium policy improved p95 latency by a mean of 65.1% and total throughput by a mean of 125.6% versus shape-to-small routing. The candidate routed 24/24 requests to the medium backend; shape-to-small routed 4–5/24 to the small backend.

**Aggregate.** Across both concurrency levels and both seeds, the mean p95 latency improvement was 38.3% and the mean total throughput gain was 63.4%.

### 3.2 C12 Cap-Tuning Grid

| Cap | p95 Improvement vs. Shape-to-Small | Throughput Gain vs. Shape-to-Small | Candidate p95 Queue Wait |
|-----|-------------------------------------|-------------------------------------|--------------------------|
| 8   | 21.6%                               | 6.6%                                | 1.87 s                   |
| 10  | 34.3%                               | 30.1%                               | 0.84 s                   |
| 12  | 65.0%                               | 100.2%                              | ~0.000004 s              |

Lower caps introduce broker-side queueing (1.87 s and 0.84 s at caps 8 and 10, respectively) that partially negates the isolation benefit. At cap=12, queue wait is negligible (~4 µs), and the full isolation benefit is realized. The best cap by mean p95 improvement and then throughput is cap=12, which matches the llama.cpp `--parallel 12` slot count.

### 3.3 Resource Utilization

GPU utilization during measured runs reached 91–93% with power draw of approximately 39–46 W, confirming genuine accelerator pressure. UMA `MemAvailable` remained around 111 GB with `SwapFree=0` throughout, indicating no memory pressure. Process RSS/PSS snapshots and backend logs are preserved in the artifact directories.

## 4. Limitations

1. **Single hardware configuration.** All results were obtained on a single unified-memory-architecture GPU. Performance characteristics may differ on discrete-GPU systems, multi-GPU configurations, or different accelerator architectures.

2. **Single model pair.** Only one small/medium model pair was tested. The magnitude of contention effects depends on the specific models and their resource profiles; different model combinations may yield different results.

3. **Limited seed and workload coverage.** Two seeds and 24 requests per cell provide a directional signal but limited statistical power. Workload characteristics (prompt length, generation length, request distribution) were fixed.

4. **Mixed c8 results.** At concurrency 8, throughput is near-flat with one seed showing a slight regression. The mechanism's benefit is concentrated at c12 pressure, which exceeds or matches the backend slot count. The c8 result does not contradict the hypothesis but bounds its applicability.

5. **No cross-environment replication.** These results have not been replicated on independent hardware or by independent researchers. The current project artifacts support the finding in the tested setting only.

6. **Broker-side queueing trade-off.** The cap parameter introduces a trade-off: caps below the slot count add queueing delay that can partially or fully offset the isolation benefit. The optimal cap is workload-dependent and requires tuning; it is not a universal constant.

7. **No production validation.** These are live benchmark prototype results, not production deployment measurements. Production traffic patterns, mixed workloads, and sustained load may yield different outcomes.

## 5. Reproducibility Checklist

- [x] **Benchmark harness source files** available: `contention_broker_benchmark.py`, `contention_live_sweep.py`
- [x] **Sweep summary artifacts** preserved: `artifacts/contention_sweep_c8_c12_2seed_20260420/sweep_summary.json`
- [x] **Cap grid summary** preserved: `artifacts/contention_c12_cap_grid_2seed_20260420/cap_grid_summary.json`
- [x] **Per-run raw results** preserved: `benchmark_results.json`, `shape_broker_results.json`, `contention_medium_control_results.json` for each seed/cap combination
- [x] **Backend logs** preserved: `llama_server_small_*.log`, `llama_server_medium_*.log` for each run
- [x] **Workload definitions** preserved: `workload.json` per run directory
- [x] **Process telemetry** preserved: RSS/PSS snapshots, GPU utilization samples
- [x] **Liveness verification** performed: no residual benchmark or server processes after runs
- [x] **Syntax verification** performed: `py_compile` on both harness scripts before each sweep
- [x] **Smoke test** performed and documented: cap=3 confirmed queueing behavior
- [ ] **External replication**: not performed
- [ ] **Multi-hardware validation**: not performed
- [ ] **Statistical significance testing**: not performed (two seeds provide directional evidence only)

## 6. Conclusion

In a live benchmark on a unified-memory-architecture GPU with two llama.cpp backends, a contention-aware single-medium isolation policy with a concurrency cap matching the backend slot count (cap=12, parallel=12) substantially outperformed shape-to-small routing at c12 pressure, yielding a mean 65.1% p95 latency improvement and 125.6% throughput gain across two seeds. At c8, the benefit is confined to latency (11.4% improvement) with mixed throughput results. The cap-tuning grid confirms that the concurrency cap should match or exceed the backend slot count; lower caps introduce broker-side queueing that degrades performance. The current project artifacts support this finding in the tested setting. External replication across different hardware, model configurations, and workload patterns is necessary before the result can be generalized.

## Referenced Artifacts

### Decision and metadata
- `.omx/project_decision.json` — project decision (finalize_positive), hypothesis status, confidence, evidence strength
- `.omx/metrics.json` — session metrics
- `run_notes.md` — detailed execution log and interpretation

### Claim audit
- `papers/.../claim_ledger.json` — claim definitions, confidence levels, allowed/forbidden wording

### Evidence bundle
- `papers/.../evidence_bundle.json` — aggregated evidence, result file manifest, status

### Sweep summaries
- `artifacts/contention_sweep_c8_c12_2seed_20260420/sweep_summary.json` — two-seed c8/c12 pressure sweep
- `artifacts/contention_c12_cap_grid_2seed_20260420/cap_grid_summary.json` — c12 cap-tuning grid (caps 8/10/12)

### Per-run raw results (cap=12, seed 3473677)
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473677/benchmark_results.json`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473677/shape_broker_results.json`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473677/contention_medium_control_results.json`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473677/workload.json`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473677/llama_server_small_19050.log`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473677/llama_server_medium_19051.log`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473677_stdout.txt`

### Per-run raw results (cap=12, seed 3473678)
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473678/benchmark_results.json`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473678/shape_broker_results.json`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473678/contention_medium_control_results.json`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473678/workload.json`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473678/llama_server_small_19080.log`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473678/llama_server_medium_19081.log`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap12_seed3473678_stdout.txt`

### Per-run raw results (cap=10, seed 3473678)
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap10_seed3473678/benchmark_results.json`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap10_seed3473678/contention_medium_control_results.json`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap10_seed3473678/shape_broker_results.json`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap10_seed3473678/llama_server_small_19020.log`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap10_seed3473678/llama_server_medium_19021.log`
- `artifacts/contention_c12_cap_grid_2seed_20260420/c12_cap10_seed3473678_stdout.txt`

### Source files
- `contention_broker_benchmark.py` — benchmark harness
- `contention_live_sweep.py` — sweep driver
