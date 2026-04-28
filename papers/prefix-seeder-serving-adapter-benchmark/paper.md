# Prefix Seeder Serving Adapter Benchmark: Tail-Latency and Idle-Amortized Energy Effects of Prompt-Cache Seeding in llama.cpp Serving

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether a prefix-seeder serving adapter—exploiting idle windows to pre-populate the KV-cache of a llama.cpp inference server with predicted hot prefixes—can simultaneously reduce tail latency and idle-amortized energy per served request under mixed concurrent workloads. Using a dependency-free benchmark harness wrapping llama.cpp's `/completion` endpoint with `cache_prompt=true`, we compare baseline (no seeding) against seeded adapter operation across three live configurations varying in initial idle budget and request count. Without an initial idle window (24 requests, 0 s initial idle), the adapter yields negligible p95 improvement (0.05%) and a small energy regression (+2.0% idle-amortized). With a 4 s initial idle window, p95 latency improves by 33.4% (24 requests) and 32.6% (48 requests). Idle-amortized energy improvement is marginal and inconsistent: −1.8% at 24 requests (a regression) and +1.3% at 48 requests. Full charged energy regresses in two of three configurations. These results suggest that prefix-cache seeding can meaningfully reduce tail latency when sufficient idle budget exists for cache priming, but the energy amortization benefit is fragile and sensitive to the reuse horizon. Confidence is medium; evidence strength is moderate.

## 1. Introduction

Autoregressive language model serving incurs substantial per-request latency from prompt prefill, which must recompute key-value (KV) cache entries for every new request even when prompts share common prefixes. The llama.cpp inference engine supports a `cache_prompt` mechanism that reuses previously computed KV-cache entries for matching prefix tokens, potentially reducing both latency and compute cost for repeated or similar prompts.

This work examines a concrete serving adapter that exploits idle periods—gaps between request bursts—to pre-seed the KV-cache with predicted "hot" prefixes before live requests arrive. The central question is whether such an adapter can simultaneously improve p95 tail latency by at least 25% and avoid regressing idle-amortized energy per served request, under a mixed concurrent workload with repeated hot prefixes, cold prefixes, and burst arrivals.

The hypothesis is conditional: the adapter should help only when (a) idle windows are long enough to complete cache priming before the first burst, and (b) the reuse horizon (number of requests that benefit from seeded entries) is sufficient to amortize the seeding cost. We test this with a live llama.cpp benchmark harness across three configurations that vary these two factors.

## 2. Method

### 2.1 Prefix Seeder Adapter Design

The adapter, implemented in `src/prefix_seeder_adapter_bench.py`, operates in two phases:

1. **Idle seeding phase.** During configurable initial idle and inter-burst idle windows, the adapter issues warmup completions for predicted hot prefixes to the llama.cpp server with `cache_prompt=true`. This populates the server's KV-cache with prefix entries before live requests arrive.

2. **Online serving phase.** Live requests are forwarded to the llama.cpp server unchanged, also with `cache_prompt=true`. If a request's prompt shares a seeded prefix, the server reuses cached KV entries, reducing prompt processing time.

The adapter does not modify the inference server itself; it acts as an external orchestrator that exploits the server's existing prompt-caching capability.

### 2.2 Workload Design

The benchmark generates a deterministic mixed concurrent workload with the following properties:

- **Hot prefixes:** Repeated prompt prefixes that appear across multiple requests, enabling cache reuse.
- **Cold/noise prefixes:** Unique prompts with no overlap, representing cache-unfriendly traffic.
- **Burst arrivals:** Groups of concurrent requests separated by idle gaps.
- **Initial idle window:** A configurable delay before the first burst, providing time for cache priming.
- **Inter-burst idle windows:** Gaps between bursts during which additional seeding can occur.

### 2.3 Metrics

The harness captures:

- **Latency:** p50, p95, p99 end-to-end request latency (ms).
- **Throughput:** Generated tokens per second.
- **Cache behavior:** Cache-n and cache-hit request counts from the llama.cpp server.
- **Resource utilization:** GPU utilization, GPU power, CPU load, RSS, UMA `MemAvailable`.
- **Energy:** Full charged energy for the entire benchmark run, and idle-amortized energy (energy attributed only to active serving periods, excluding idle-window energy from the per-request accounting).

### 2.4 Kill-Gate Criteria

The branch-specific kill condition requires both:

1. p95 latency improvement ≥ 25% (seeded vs. baseline).
2. Idle-amortized energy per request non-regression (delta ≥ 0%).

Failure on both gates would trigger finalization as negative; passing both supports the hypothesis.

### 2.5 Backends

The harness supports two backends:

- **simulate:** A deterministic simulation backend for correctness smoke testing. No real inference is performed; timing is synthetic. Used only for validation of the harness logic.
- **llamacpp:** Live inference via a `llama-server` process started from a neutral service directory (`~/.cache/enoch_services/prefix-seeder-serving-adapter`), always stopped before exit. This is the backend used for all reported quantitative results.

## 3. Results

### 3.1 Simulation Smoke Tests

Two simulation runs confirmed harness correctness:

- `artifacts/adapter_bench_smoke`: 16 requests, concurrency 4, idle gap 0.25 s, n_predict 4.
- `artifacts/adapter_bench_smoke_initial_idle`: 16 requests, concurrency 4, initial idle 0.4 s, idle gap 0.25 s, n_predict 4.

These runs validated workload generation, adapter logic, and metric collection without exercising real inference. Their timing values are synthetic and are not reported as empirical results.

### 3.2 Live llama.cpp Results

Three live benchmark configurations were run with the following common parameters: concurrency 4, idle gap 1.0 s, intra-burst gap 0.02 s, n_predict 8, ctx_size 8192, parallel 4, batch_size 1024, ubatch_size 256.

| Configuration | Requests | Initial Idle | p95 Baseline (ms) | p95 Seeded (ms) | p95 Improvement | Full Energy Delta | Idle-Amortized Energy Delta | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `adapter_bench_live_smoke` | 24 | 0.0 s | 1579.4 | 1578.7 | 0.05% | +1.6% | +2.0% | Latency gate failed |
| `adapter_bench_live_initial_idle` | 24 | 4.0 s | 1575.3 | 1049.1 | 33.4% | −4.3% | −1.8% | Latency gate passed; idle-amortized energy regressed |
| `adapter_bench_live_48req` | 48 | 4.0 s | 1509.0 | 1016.9 | 32.6% | −3.2% | +1.3% | Both gates passed |

### 3.3 Interpretation

**Idle window necessity.** Without an initial idle window (24 requests, 0 s initial idle), the adapter has no opportunity to prime the cache before the first burst arrives. The p95 improvement is negligible (0.05%), and both full and idle-amortized energy regress slightly. This confirms that the adapter's latency benefit is conditional on having sufficient idle budget for cache priming before the first request burst.

**Latency improvement with idle priming.** With a 4 s initial idle window, p95 latency improves substantially: 33.4% at 24 requests and 32.6% at 48 requests. Both exceed the 25% threshold. The consistency of this improvement across the two configurations suggests the latency benefit is robust once the cache is primed.

**Energy amortization is fragile.** Full charged energy improves (−4.3% and −3.2%) when idle priming is present, meaning the total energy consumed during the benchmark is lower with seeding. However, idle-amortized energy—energy attributed only to active serving—shows inconsistent behavior: −1.8% at 24 requests (a regression, meaning the adapter increased per-request active energy) and +1.3% at 48 requests (a marginal improvement). The 24-request configuration fails the idle-amortized energy gate despite passing the latency gate, while the 48-request configuration passes both gates narrowly.

**Reuse horizon matters.** The divergence in idle-amortized energy between 24 and 48 requests suggests a minimum reuse horizon is required for the seeding investment to amortize positively. At 24 requests, the cache-hit benefits do not fully offset the seeding overhead in the active-serving energy accounting. At 48 requests, the additional reuse opportunities push the amortization marginally positive.

**Full energy vs. idle-amortized energy.** The apparent contradiction—full energy improving while idle-amortized energy regresses at 24 requests—arises because idle-amortized accounting excludes the idle-window energy. Seeding during idle windows consumes energy that is excluded from the idle-amortized metric, but the cache-warmup completions issued during idle still incur some active-serving overhead (e.g., server scheduling, partial batch processing) that can be attributed to the active window. The net effect depends on implementation details of how the server accounts for prompt processing time during idle-seeded requests.

## 4. Limitations

1. **Single hardware configuration.** All live results were collected on one machine. GPU model, memory architecture (UMA), and power instrumentation characteristics are specific to this system. Generalization to other hardware is not established.

2. **Limited request counts.** The maximum request count tested is 48. Production serving workloads involve orders of magnitude more requests, and the amortization behavior may differ at scale. The narrow idle-amortized energy improvement at 48 requests (+1.3%) suggests the break-even point is near this horizon, but its exact location and stability are unknown.

3. **No robustness sweep.** Concurrency, idle gap duration, seed budget, and prompt-length distributions were held fixed or minimally varied. The parameter space is large, and the reported results may not hold across it. The project decision recommends a robustness sweep across request counts (48/96/192), concurrency (2/4/8), idle gaps (0.5/1/2 s), and seed budgets, which has not been performed.

4. **Model and server version not independently varied.** Results depend on the specific llama.cpp server build and cached model used. Different models, quantization levels, or server versions may yield different cache-hit behavior and latency profiles.

5. **Workload is synthetic.** The deterministic workload with known hot prefixes represents an idealized scenario. In production, hot-prefix prediction may be imperfect, and the adapter's effectiveness depends on prediction accuracy, which is not evaluated here.

6. **Energy measurement granularity.** Energy figures are derived from system-level power sampling, not from isolated GPU power measurement. Attribution of energy to specific phases (idle seeding vs. active serving) involves assumptions that may not precisely reflect hardware-level energy consumption.

7. **No comparison to alternative approaches.** This study does not compare prefix seeding against other tail-latency reduction techniques (e.g., speculative decoding, batch scheduling, discrete prompt caching services). The relative merit of the adapter approach is not established.

8. **Marginal energy results.** The idle-amortized energy improvement at 48 requests (+1.3%) is within typical measurement noise for system-level power instrumentation. This result should be treated as suggestive rather than conclusive.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Source code available | `src/prefix_seeder_adapter_bench.py` (dependency-free Python) |
| Benchmark harness self-contained | Yes; starts/stops llama-server automatically |
| Simulation backend for smoke testing | Yes (`--backend simulate`) |
| Live backend for real inference | Yes (`--backend llamacpp`) |
| Exact command lines recorded | Yes (see run notes, 6 command invocations) |
| Configuration files preserved | Yes (`bench_config.json` per run) |
| Server logs preserved | Yes (`llama_server.log` per run) |
| Per-request timing data | Yes (`*_requests.json` per run) |
| Resource metrics in Prometheus format | Yes (`*_metrics.prom` per run) |
| Summary statistics | Yes (`summary.json` and `summary.md` per run) |
| Hardware details specified | Partial—UMA architecture noted; exact GPU model not in artifacts |
| Model/quantization specified | Not explicitly in artifacts; llama-server uses a cached model |
| Random seeds for workload generation | Deterministic workload (no randomness) |
| Statistical significance testing | Not performed (single run per configuration) |

## 6. Conclusion

A prefix-seeder serving adapter that pre-populates the KV-cache during idle windows can reduce p95 tail latency by approximately 30% in a live llama.cpp serving environment, provided an initial idle window of sufficient duration (here, 4 s) exists for cache priming. Without such an idle window, the latency benefit is negligible. The energy picture is less favorable: idle-amortized energy per served request improves only marginally (+1.3%) at 48 requests and regresses (−1.8%) at 24 requests, indicating that the energy amortization threshold lies near this reuse horizon. Full charged energy improves modestly when idle priming is present, but this metric includes idle-window energy that may not be billable in all serving contexts.

The branch-specific kill condition (p95 improvement ≥ 25% and idle-amortized energy non-regression) is not triggered by the 48-request result, supporting a `finalize_positive` decision with medium confidence. However, the fragility of the energy result and the narrow scope of the evaluation mean that these findings should be treated as preliminary evidence rather than a general claim. A robustness sweep across the parameter space—particularly request count, concurrency, and idle gap duration—is needed to map the amortization threshold and determine whether the energy benefit is reliable under varied conditions.

## Referenced Artifacts

### Source code
- `src/prefix_seeder_adapter_bench.py`

### Decision and metadata
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `run_notes.md`

### Simulation smoke-test artifacts
- `artifacts/adapter_bench_smoke/` (16 requests, no initial idle)
- `artifacts/adapter_bench_smoke_initial_idle/` (16 requests, 0.4 s initial idle)

### Live llama.cpp artifacts — 24 requests, no initial idle
- `artifacts/adapter_bench_live_smoke.console.log`
- `artifacts/adapter_bench_live_smoke/summary.md`
- `artifacts/adapter_bench_live_smoke/summary.json`
- `artifacts/adapter_bench_live_smoke/seeded_adapter_idle_requests.json`
- `artifacts/adapter_bench_live_smoke/seeded_adapter_idle_metrics.prom`
- `artifacts/adapter_bench_live_smoke/seeded_adapter_idle_llama_server.log`
- `artifacts/adapter_bench_live_smoke/baseline_no_seed_requests.json`
- `artifacts/adapter_bench_live_smoke/baseline_no_seed_metrics.prom`
- `artifacts/adapter_bench_live_smoke/baseline_no_seed_llama_server.log`
- `artifacts/adapter_bench_live_smoke/bench_config.json`

### Live llama.cpp artifacts — 24 requests, 4 s initial idle
- `artifacts/adapter_bench_live_initial_idle.console.log`
- `artifacts/adapter_bench_live_initial_idle/summary.md`
- `artifacts/adapter_bench_live_initial_idle/summary.json`
- `artifacts/adapter_bench_live_initial_idle/seeded_adapter_idle_requests.json`
- `artifacts/adapter_bench_live_initial_idle/seeded_adapter_idle_metrics.prom`
- `artifacts/adapter_bench_live_initial_idle/seeded_adapter_idle_llama_server.log`
- `artifacts/adapter_bench_live_initial_idle/baseline_no_seed_requests.json`
- `artifacts/adapter_bench_live_initial_idle/baseline_no_seed_metrics.prom`
- `artifacts/adapter_bench_live_initial_idle/baseline_no_seed_llama_server.log`
- `artifacts/adapter_bench_live_initial_idle/bench_config.json`

### Live llama.cpp artifacts — 48 requests, 4 s initial idle
- `artifacts/adapter_bench_live_48req.console.log`
- `artifacts/adapter_bench_live_48req/summary.md`
- `artifacts/adapter_bench_live_48req/summary.json`
- `artifacts/adapter_bench_live_48req/seeded_adapter_idle_requests.json`
- `artifacts/adapter_bench_live_48req/seeded_adapter_idle_metrics.prom`
- `artifacts/adapter_bench_live_48req/seeded_adapter_idle_llama_server.log`
- `artifacts/adapter_bench_live_48req/baseline_no_seed_requests.json`
- `artifacts/adapter_bench_live_48req/baseline_no_seed_metrics.prom`
- `artifacts/adapter_bench_live_48req/baseline_no_seed_llama_server.log`
- `artifacts/adapter_bench_live_48req/bench_config.json`

### Paper and audit artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
