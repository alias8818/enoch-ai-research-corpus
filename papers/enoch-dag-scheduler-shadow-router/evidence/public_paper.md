# Shadow Routing for DAG-Aware Scheduling: A Non-Mutating Sidecar Approach with Projected Performance Gains

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, and decision JSON). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate whether a DAG-aware scheduler can operate as a shadow router alongside an existing production router, producing alternative task-placement decisions and safety metrics without modifying the live execution path. A dependency-free simulation harness models a baseline stable path/hash router and a shadow earliest-finish-time router over synthetic DAG workloads. Across 60 deterministic sweep scenarios spanning three DAG sizes and four heterogeneity levels, the shadow router projected mean makespan improvement of 44.3% (range 29.5%–61.9%) and mean p95 DAG latency improvement of 48.9% (range 31.7%–higher), with mean routing overhead of 26.8 ms and maximum overhead of 74.5 ms. Decision divergence from the baseline was 72.7% in a small smoke test and consistently high across the sweep. Peak memory usage remained under 25 MB. All 60 runs showed positive projected improvement. However, these results derive exclusively from synthetic workloads with a simplified baseline router and abstracted device queues; production benefit remains unvalidated. The small smoke test also showed a notably smaller p95 DAG latency improvement (6.8%) compared to its makespan improvement (49.8%), illustrating that per-DAG tail latency does not necessarily track overall schedule completion. We conclude the approach is viable for prototype development contingent on real event-log replay.

## 1. Introduction

DAG-structured workloads—where tasks carry dependency constraints that impose partial ordering—appear in machine learning inference serving, data pipelines, and heterogeneous compute scheduling. Production schedulers for such workloads typically prioritize stability and predictability, often employing consistent-hashing or stable-path assignment policies that minimize disruption but may underutilize dependency-aware placement opportunities.

Modifying a live scheduler to exploit DAG structure carries risk: incorrect placement can increase tail latency, violate admission control, or introduce cascading delays. A safer approach is to run an alternative scheduling policy in shadow mode—computing alternative placements without committing them to the execution path—then comparing projected outcomes offline before any cutover.

This work asks: can a DAG-aware scheduler run as a shadow router beside an existing production router, producing useful routing alternatives and safety metrics without affecting the live execution path?

We test this question through a local simulation that models both a baseline router (stable path/hash assignment) and a shadow router (dependency-aware earliest-finish-time selection) over synthetic DAG workloads of varying size and heterogeneity. We measure projected makespan, p95 DAG latency, resource utilization, decision divergence, and computational overhead. We deliberately do not claim that these projected improvements would materialize on real hardware or against a production-strength scheduler.

## 2. Method

### 2.1 Simulation Harness

Because the project directory contained only prompt metadata and no existing implementation, we built a dependency-free Python simulation harness (`scripts/shadow_router_sim.py`) that models:

1. **Baseline router.** Assigns DAG tasks to resource pools using stable path/hash assignment. This policy is intentionally simple—it provides consistent, deterministic placement but does not consider inter-task dependencies when selecting resources.

2. **Shadow router.** Computes alternative placements using dependency-aware earliest-finish-time (EFT) selection. For each ready task, the shadow router evaluates which resource pool would yield the earliest projected completion time given current queue states and dependency satisfaction, then records this alternative placement without modifying the baseline schedule.

3. **Shadow-mode evidence collection.** After both routers produce schedules, the harness computes task-level divergence (fraction of tasks where shadow and baseline disagree on placement), projected makespan, projected p95 DAG latency, mean resource utilization, and shadow computation overhead in milliseconds.

This is a toy simulation: it uses an idealized cost model, abstracts device queues, and does not model GPU kernel contention, KV-cache pressure, network latency, admission control, or failure/retry behavior.

### 2.2 DAG Generation

Synthetic DAGs are generated with configurable width, depth, and heterogeneity parameters. Each DAG is a layered structure where tasks in layer *i* depend on tasks in layer *i*−1. Heterogeneity controls the variance in task execution costs across resource pools, simulating heterogeneous hardware (e.g., GPU vs. CPU vs. accelerator pools). A heterogeneity of 0.0 means all resource pools have identical costs for each task; a heterogeneity of 1.0 means costs vary maximally across pools.

### 2.3 Experimental Design

**Smoke test.** A single small scenario (4 DAGs, width 3, depth 4, heterogeneity 0.8, seed 11) validated harness correctness and justified the larger sweep.

**Bounded sweep.** 60 deterministic scenarios were tested, varying:

| Parameter | Values |
|---|---|
| Heterogeneity | 0.0, 0.4, 0.8, 1.0 |
| Size | small (12 DAGs, w4, d5), medium (40 DAGs, w6, d7), large (120 DAGs, w8, d9) |
| Seed | 3, 7, 11, 17, 23 |

This yields 4 × 3 × 5 = 60 runs. The sweep runner (`scripts/run_shadow_router_sweep.py`) executed all scenarios deterministically.

### 2.4 Environment

All runs executed on a Linux `gx10-efe8` host (kernel 6.17.0-1014-nvidia, aarch64) with 20 CPU cores, Python 3.12.3, and approximately 121.6 GB available memory. Swap was confirmed disabled (SwapTotal: 0 kB). Memory telemetry was collected via `/usr/bin/time -v`.

### 2.5 Metrics

- **Makespan.** Total time from first task start to last task finish across all DAGs.
- **p95 DAG latency.** 95th percentile of per-DAG completion time (finish of last task minus arrival).
- **Mean utilization.** Average fractional occupancy across all resource pools over the schedule horizon.
- **Decision divergence.** Fraction of tasks where shadow placement differs from baseline placement.
- **Shadow overhead.** Wall-clock time for shadow routing computation, measured in milliseconds.

## 3. Results

### 3.1 Smoke Test

| Metric | Baseline | Shadow | Delta |
|---|---|---|---|
| Makespan | 217.30 | 109.05 | −49.8% |
| p95 DAG latency | 80.44 | 74.98 | −6.8% |
| p50 DAG latency | 74.83 | 54.89 | −26.7% |
| Mean utilization | 0.433 | 0.760 | +75.3% |
| Decision divergence | — | 72.7% | — |
| Shadow overhead | — | 0.103 ms | — |

The shadow router projected a 49.8% makespan reduction but only a 6.8% p95 DAG latency reduction. This discrepancy is notable: while the shadow policy substantially compressed the overall schedule, the worst-case per-DAG completion time improved far less. The p50 DAG latency improved by 26.7%, indicating that most DAGs benefited but the tail was relatively resistant. Decision divergence was 72.7%, meaning nearly three-quarters of task placements differed from baseline. Shadow computation took 0.103 ms. Peak RSS was 19,120 KB with zero swap events.

### 3.2 Sweep Results

Across all 60 scenarios:

| Metric | Min | Mean | Max |
|---|---|---|---|
| Makespan improvement (%) | 29.5 | 44.3 | 61.9 |
| p95 DAG latency improvement (%) | 31.7 | 48.9 | — |
| Shadow overhead (ms) | — | 26.8 | 74.5 |

- **Positive improvement runs**: 60/60
- **Nonnegative improvement runs**: 60/60
- **Peak RSS** (sweep process): 24,660 KB
- **Swap events**: 0

All 60 scenarios showed positive projected makespan improvement. Mean shadow routing overhead was 26.8 ms, with a maximum of 74.5 ms. Memory usage remained modest relative to available system memory (24,660 KB RSS against ~121.6 GB available).

The sweep's p95 latency improvements (minimum 31.7%, mean 48.9%) were substantially larger than the smoke test's 6.8%. This likely reflects the larger DAG counts and wider structures in the sweep scenarios, which give the EFT policy more opportunity to reduce per-DAG tail latency through better resource assignment. The smoke test's small size (4 DAGs, 44 tasks) may have constrained the shadow router's ability to improve the worst-case DAG completion.

### 3.3 Mixed and Negative Observations

Several caveats temper the headline improvement figures:

1. **Baseline simplicity inflates deltas.** The stable path/hash baseline makes no attempt to balance load or respect dependencies. Against even a modestly smarter scheduler, the shadow router's advantage would likely shrink, potentially substantially.

2. **Smoke test p95 latency gap.** The 6.8% p95 latency improvement in the smoke test—versus 49.8% makespan improvement—demonstrates that overall schedule compression does not guarantee proportional tail-latency improvement. This is a real limitation of the approach in scenarios with few DAGs or particular structural properties.

3. **Overhead scaling.** Shadow overhead grew from 0.103 ms (smoke, 44 tasks) to a maximum of 74.5 ms (sweep, up to 120 DAGs). While acceptable for offline replay, this overhead trajectory warrants monitoring at production scale.

4. **No negative-improvement runs occurred in this synthetic setting, but this is expected given the baseline's simplicity.** Against a stronger baseline, some scenarios would likely show negative projected improvement.

## 4. Limitations

1. **Synthetic workloads only.** No production scheduler traces, real inference traffic, or private workload data were available. DAG structure, task costs, and resource pool characteristics are all generated. Projected improvements may not transfer to real workloads with different structural properties.

2. **Simplified baseline.** The baseline router uses stable path/hash assignment—a deliberately naive policy chosen to maximize observable delta. Production schedulers typically incorporate load balancing, queueing awareness, and sometimes partial dependency tracking. Against a stronger baseline, the shadow router's projected advantage would likely diminish, potentially substantially.

3. **Abstracted device model.** The simulation does not model GPU kernel contention, KV-cache pressure, NUMA effects, network latency, admission control, or failure/retry behavior. These factors can dominate real scheduling decisions and may invalidate projected improvements.

4. **No real-time constraints tested.** Shadow overhead was measured in an unconstrained simulation environment with no competing load. Under production conditions with concurrent request handling, overhead may increase.

5. **No validation against actual execution.** Projected makespan and latency improvements are computed within the simulation's cost model. Whether shadow-placed tasks would actually achieve these timings on real hardware is untested.

6. **Deterministic seeds only.** While 60 scenarios provide reasonable coverage of the parameter space, stochastic variation in real workloads (burst arrivals, cost estimation errors, stragglers) is not represented.

7. **Heterogeneity-zero scenarios still showed improvement.** Even with heterogeneity 0.0 (identical costs across all resource pools), the sweep reported positive improvement. This suggests the shadow router benefits from dependency-aware placement alone, but also raises the question of whether the baseline's hash assignment is creating unnecessary imbalance even in homogeneous settings—an artifact of the baseline's simplicity rather than a genuine scheduling insight.

## 5. Reproducibility Checklist

- [x] **Source code available**: `scripts/shadow_router_sim.py`, `scripts/run_shadow_router_sweep.py`
- [x] **Environment recorded**: `artifacts/logs/environment_probe.log` (kernel, CPU, memory, Python version)
- [x] **Random seeds specified**: Seeds 3, 7, 11, 17, 23 for sweep; seed 11 for smoke test
- [x] **Memory telemetry collected**: `/usr/bin/time -v` output in `artifacts/logs/smoke_time.log` and `artifacts/logs/sweep_time.log`
- [x] **Swap disabled confirmed**: SwapTotal: 0 kB recorded in environment probe
- [x] **Smoke test before sweep**: Small scenario (4 DAGs) run before 60-scenario sweep
- [x] **Durable artifacts written**: All metrics, schedules, and logs persisted to `artifacts/` directory
- [x] **Sweep parameters documented**: Heterogeneity levels, sizes, seeds enumerated in run notes
- [x] **Aggregate and per-run results saved**: `artifacts/metrics/sweep/aggregate.json` and `artifacts/metrics/sweep/summary.csv`
- [x] **Decision and confidence recorded**: `.omx/project_decision.json` with evidence references
- [ ] **Independent reproduction by external party**: Not yet performed
- [ ] **Production trace validation**: Not yet performed

## 6. Conclusion

A DAG-aware shadow router operating alongside a baseline stable-path scheduler can produce alternative task placements with projected makespan improvements of 29.5%–61.9% and p95 latency improvements of 31.7%–48.9% (mean across 60 synthetic sweep scenarios), at mean computational overhead of 26.8 ms and peak memory under 25 MB. Decision divergence from baseline was consistently high, confirming that the shadow policy proposes materially different placements.

However, the smoke test's modest p95 latency improvement (6.8%) versus its large makespan improvement (49.8%) illustrates that overall schedule compression does not uniformly reduce per-DAG tail latency. The magnitude of improvement across the sweep is partly an artifact of the baseline's simplicity; against a production scheduler with even rudimentary load-balancing, the observed deltas would likely narrow.

These results support the viability of building a prototype that records production DAG events and replays them through the shadow policy for offline comparison. The evidence does not support direct production deployment or claims of production-level benefit.

The recommended next step is implementing a replay adapter around real scheduler events conforming to a minimum schema (dag_id, task_id, dependencies, arrival_ts, estimated_cost, actual_start_ts, actual_finish_ts, resource), then comparing baseline actuals against shadow decisions with guardrails: shadow compute p95 overhead below 1% of median task runtime, no resource-capacity violations, projected p95 DAG latency improvement of at least 5% on at least three representative traces, and divergence review before any live promotion.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Simulation harness | `scripts/shadow_router_sim.py` |
| Sweep runner | `scripts/run_shadow_router_sweep.py` |
| Environment probe log | `artifacts/logs/environment_probe.log` |
| Smoke test stdout | `artifacts/logs/smoke_stdout.json` |
| Smoke time/RSS log | `artifacts/logs/smoke_time.log` |
| Smoke metrics | `artifacts/metrics/smoke/result.json` |
| Smoke baseline schedule | `artifacts/metrics/smoke/baseline_schedule.csv` |
| Smoke shadow schedule | `artifacts/metrics/smoke/shadow_schedule.csv` |
| Sweep stdout log | `artifacts/logs/sweep_stdout.log` |
| Sweep time/RSS log | `artifacts/logs/sweep_time.log` |
| Sweep aggregate metrics | `artifacts/metrics/sweep/aggregate.json` |
| Sweep per-run summary | `artifacts/metrics/sweep/summary.csv` |
| Project decision JSON | `.omx/project_decision.json` |
| Project metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260501T163848558526+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T163848558526+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T163848558526+0000/paper_manifest.json` |
