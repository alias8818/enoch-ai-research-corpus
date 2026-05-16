# Multi-Tenant Cache Fairness Guard: A Tenant-Aware Eviction Policy for Shared Caches

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, simulator output, claim ledger). The operator who released the artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human has verified, edited, or endorsed the claims herein. The claim ledger for this paper currently carries `blocked_empty_claims` audit status, meaning no structured claims have passed formal evidence audit. All quantitative statements below derive from the raw run notes and decision JSON and should be read accordingly.

---

## Abstract

In multi-tenant systems sharing a single cache, a tenant with scan-heavy access patterns can externalize eviction costs onto co-tenants, degrading their hit rates even when those tenants have small, reusable hot sets. This paper evaluates a tenant-aware fairness guard for LRU caches that tracks per-tenant occupancy and preferentially evicts entries from tenants exceeding a protected fair share. In a deterministic simulation with three tenants—two latency-sensitive tenants with small hot sets and one scan-heavy noisy neighbor—the fairness guard improved mean total hit rate by +0.052, Jain fairness index by +0.021, and minimum normalized tenant hit rate by +0.110 across four cache capacities (360–750 entries, 10 seeds each, 200,000 requests per run). Protected tenants gained approximately 9.5 percentage points of hit rate, while the noisy tenant lost approximately 1.3 percentage points. The guard policy incurred approximately 2.4× the per-access bookkeeping overhead of plain LRU within the simulator, though absolute policy execution time remained modest (~0.10 s per 200k-request aggregate). These results are limited to a synthetic, adversarial workload in a single-threaded Python simulator; production validation with real traces, weighted shares, and concurrency benchmarks remains necessary.

## 1. Introduction

Shared caches are a common architectural pattern for amortizing memory costs across tenants in database engines, object stores, and inference serving systems. When tenants share a single global LRU eviction policy, however, a tenant with scan-heavy or low-locality access patterns can displace entries belonging to tenants with small, high-value hot sets. The noisy neighbor problem in caches is well-recognized in operational practice, but the quantitative trade-offs of introducing tenant-aware eviction guards—particularly the cost imposed on the noisy tenant and the bookkeeping overhead—have received limited rigorous characterization.

This work asks: can a lightweight tenant-aware eviction guard prevent a scan-heavy tenant from degrading co-tenant hit rates, while preserving acceptable total cache efficiency? We implement and evaluate a deterministic simulator comparing two policies:

1. **Shared LRU**: A single global LRU with no tenant awareness.
2. **Fairness Guard LRU**: A global LRU augmented with per-tenant occupancy tracking. On insertion when the cache is full, the guard preferentially evicts from the requesting tenant if it exceeds a soft cap, then from any tenant above its cap or floor, falling back to global LRU otherwise.

We test these policies against an intentionally adversarial workload: two latency-sensitive tenants (`alpha`, `beta`) with small reusable hot sets and occasional cold misses, and one scan-heavy tenant (`gamma`) with limited locality. We sweep four cache capacities (360, 450, 600, 750 entries) with 10 random seeds and 200,000 requests per run.

The results show that the fairness guard consistently improves overall hit rate, Jain fairness, and minimum normalized tenant utility across all tested capacities. The trade-off is a modest hit-rate reduction for the noisy tenant and increased per-access bookkeeping. We emphasize that these are simulation results on a synthetic workload; they establish directional viability but do not constitute production validation.

## 2. Method

### 2.1 Workload Model

The simulator models three tenants:

- **`alpha`**: Latency-sensitive tenant with a small reusable hot set and occasional cold misses.
- **`beta`**: Latency-sensitive tenant with a small reusable hot set and occasional cold misses (independent key space from `alpha`).
- **`gamma`**: Noisy neighbor with predominantly scan traffic and limited locality.

The workload is intentionally adversarial: `gamma`'s scan pattern is designed to stress the shared LRU by flooding it with low-reuse entries, while `alpha` and `beta` depend on a small set of frequently re-accessed keys. This design maximizes the observable fairness gap but does not represent the full distribution of real multi-tenant workloads.

### 2.2 Eviction Policies

**Shared LRU.** A single global LRU list. On insertion when the cache is full, the least-recently-used entry is evicted regardless of tenant identity.

**Fairness Guard LRU.** The cache maintains a global LRU list augmented with per-tenant occupancy counters. Each tenant is assigned a protected fair share (equal division of capacity among active tenants in this prototype). On insertion when the cache is full, the eviction target is selected as follows:

1. If the requesting tenant's occupancy exceeds its soft cap, evict the requesting tenant's least-recently-used entry.
2. Otherwise, evict from any tenant whose occupancy exceeds its cap or floor.
3. If no tenant exceeds its allocation, fall back to global LRU eviction.

This design ensures that a tenant consuming more than its fair share bears the eviction cost of its own inserts before displacing entries from other tenants. The policy is stateless beyond the occupancy counters and per-tenant LRU sublists; it does not require a priori knowledge of tenant access distributions.

### 2.3 Metrics

- **Total hit rate**: Fraction of requests served from the cache across all tenants.
- **Per-tenant hit rate**: Hit rate computed per tenant.
- **Normalized hit rate**: Per-tenant hit rate divided by the hit rate that tenant would achieve with an isolated cache of its fair-share capacity. This normalizes for differences in tenant locality.
- **Jain fairness index**: Computed over the three tenants' normalized hit rates. A value of 1.0 indicates perfectly fair allocation according to this metric.
- **Minimum normalized hit rate**: The lowest normalized hit rate among all tenants, capturing worst-case tenant utility.

### 2.4 Experimental Design

We sweep cache capacity at four levels: 360, 450, 600, and 750 entries. For each capacity, we run 10 independent seeds (0–9) with 200,000 requests per seed. A smoke test with 20,000 requests and 2 seeds validated the simulator before full runs.

All runs were executed on an `aarch64` Linux host (kernel 6.17.0-1014-nvidia) with 128 GB RAM, no swap, and `earlyoom` active. Maximum RSS across runs was approximately 67.8 MB with zero swap events. Python 3.12.3 was used. Resource usage was monitored via `/usr/bin/time -v`.

### 2.5 Artifacts

The following scripts and outputs constitute the reproducible artifact set:

- Simulator: `scripts/cache_fairness_sim.py`
- Aggregator: `scripts/aggregate_results.py`
- Per-capacity metrics: `artifacts/metrics/cache_fairness_*.json`
- Aggregate summary: `artifacts/metrics/aggregate_summary.json`
- Run logs: `artifacts/logs/run_cap*.log`

## 3. Results

### 3.1 Hit Rate and Fairness Across Capacities

Table 1 presents the primary results across all four capacities. Each row aggregates 10 seeds × 200,000 requests.

**Table 1: Shared LRU vs. Fairness Guard LRU across cache capacities.**

| Capacity | Shared Hit | Guard Hit | Δ Hit | Shared Jain | Guard Jain | Δ Jain | Δ α Hit | Δ β Hit | Δ γ Hit |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 360 | 0.4654 | 0.5156 | +0.0502 | 0.9758 | 1.0000 | +0.0241 | +0.0928 | +0.0916 | −0.0129 |
| 450 | 0.4860 | 0.5386 | +0.0526 | 0.9772 | 1.0000 | +0.0228 | +0.0970 | +0.0959 | −0.0132 |
| 600 | 0.5109 | 0.5641 | +0.0532 | 0.9793 | 1.0000 | +0.0207 | +0.0981 | +0.0973 | −0.0135 |
| 750 | 0.5287 | 0.5793 | +0.0506 | 0.9819 | 1.0000 | +0.0181 | +0.0932 | +0.0932 | −0.0134 |

The fairness guard improved total hit rate at every capacity, with improvements ranging from +0.0502 to +0.0532 absolute. Jain fairness reached 1.0000 under the guard at all capacities, compared to 0.9758–0.9819 under shared LRU. The improvement is consistent rather than capacity-dependent: the guard's advantage does not vanish as capacity increases, though the Jain fairness gap narrows slightly because shared LRU becomes somewhat fairer at larger capacities.

The fact that Jain fairness reaches exactly 1.0000 at all capacities under the guard warrants scrutiny. In a stochastic simulation with 10 seeds, perfect fairness is unlikely unless the guard's occupancy enforcement is sufficiently strong to equalize normalized hit rates to within the reported precision. This may reflect a structural property of the guard policy under this particular workload rather than a general guarantee.

### 3.2 Per-Tenant Breakdown

Protected tenants `alpha` and `beta` gained approximately 9.2–9.8 percentage points of hit rate across all capacities. The noisy tenant `gamma` lost approximately 1.3 percentage points. The asymmetry is expected: `gamma`'s scan traffic has low reuse, so entries evicted from `gamma`'s occupancy are less likely to be re-requested than entries displaced from `alpha` or `beta` under shared LRU. The net positive effect on total hit rate (+0.052) confirms that the guard's preferential eviction from the over-occupying tenant removes lower-value entries on average.

Aggregate means across all four capacities:

- Mean total hit-rate improvement: **+0.05164** absolute.
- Mean Jain fairness improvement: **+0.02142** absolute.
- Mean minimum normalized hit-rate improvement: **+0.10987** absolute.
- Mean protected-tenant hit-rate improvement: `alpha` **+0.09527**, `beta` **+0.09450** absolute.
- Mean noisy-tenant hit-rate cost: `gamma` **−0.01325** absolute.

The near-symmetry between `alpha` and `beta` improvements is consistent with their symmetric workload profiles. The small residual difference (+0.00077) likely reflects random seed variation rather than a systematic policy bias.

### 3.3 Overhead

The guard policy's per-access bookkeeping (occupancy tracking, cap checks, tenant-aware eviction selection) incurred approximately **2.37×** the elapsed time of plain LRU within the instrumented simulator. However, absolute policy execution time was approximately 0.10 s per 200k-request/10-seed aggregate, with trace generation dominating wall time.

This overhead ratio is directional only and should not be interpreted as a production performance prediction. A Python simulator's cost model does not directly translate to production cache latency, where the relevant costs are per-access lock hold times, memory barriers, and cache-line effects rather than Python-level instruction counts. The 2.37× figure establishes that the guard adds non-trivial per-access work; whether this work is negligible or prohibitive in a real system depends on the target cache's access path architecture.

## 4. Limitations

1. **Synthetic workload.** The three-tenant model is intentionally adversarial but artificial. Production workloads exhibit more complex access distributions, variable tenant counts, burst patterns, and time-varying locality. The results here establish that the guard works in the designed-for scenario; they do not establish general applicability. Workloads where the "noisy" tenant also has significant locality may produce different trade-offs, as the guard would then evict entries with non-trivial reuse value.

2. **Simulation, not production.** All measurements come from a deterministic Python simulator. No real cache implementation was modified. The 2.37× overhead ratio reflects Python-level bookkeeping cost, not real-system lock contention, memory overhead, or integration complexity. Production benchmarking in the target cache layer is required before drawing performance conclusions.

3. **Equal tenant shares.** The prototype assigns equal protected fair shares to all tenants. Production systems typically require weighted shares, active-tenant detection (to avoid reserving capacity for idle tenants), and dynamic adjustment. These are not modeled.

4. **Tenant identity assumption.** The guard requires tenant identity at cache access time. In systems where tenant identity is unavailable or expensive to determine, the guard is not directly applicable.

5. **Single noisy-neighbor profile.** Only one scan-heavy profile was tested. Different scan rates, mixed scan-and-locality profiles, or multiple noisy tenants may produce different trade-offs.

6. **No concurrency effects.** The simulator is single-threaded. Real caches face concurrent access, lock contention, and NUMA effects that may alter both the fairness dynamics and the overhead profile.

7. **Narrow capacity range.** Capacities from 360 to 750 entries were tested. Behavior at very small or very large capacities relative to tenant hot sets was not explored.

8. **Claim audit status.** The claim ledger for this paper carries `blocked_empty_claims` audit status, indicating that no structured claims have been extracted and verified against the evidence bundle. The quantitative statements in this paper derive from the raw run notes and project decision JSON and have not passed formal claim/evidence audit.

9. **No variance reporting.** The results table reports means over 10 seeds but does not include standard deviations or confidence intervals. The consistency of the sign and approximate magnitude across all four capacities provides informal robustness, but formal statistical inference is not supported by the reported data.

## 5. Reproducibility Checklist

- **Simulator source**: `scripts/cache_fairness_sim.py` — deterministic, seed-controlled.
- **Aggregator source**: `scripts/aggregate_results.py` — produces `aggregate_summary.json` from per-run JSON.
- **Environment log**: `artifacts/logs/environment_20260429T001733Z.log` — captures host, kernel, Python version, memory, swap, and `earlyoom` status.
- **Random seeds**: 0–9 for full runs; 0–1 for smoke test. Explicitly passed via `--seeds` flag.
- **Command lines**: Full command lines for smoke test, capacity sweep, and aggregation are recorded in run notes and logs.
- **Resource monitoring**: `/usr/bin/time -v` used for all full runs; maximum RSS ~67.8 MB, zero swap.
- **Output artifacts**: Per-capacity JSON metrics files and aggregate summary are listed in the evidence section. Logs for each capacity run are preserved.
- **No external dependencies beyond Python 3.12 stdlib** (as implied by the simulator script structure).
- **Determinism**: The simulator is described as deterministic given a fixed seed. Reproducibility depends on the simulator implementation being unmodified between runs; no hash or commit ID for the simulator source is recorded in the available artifacts.

## 6. Conclusion

A tenant-aware fairness guard for shared LRU caches was evaluated in a deterministic simulation with an adversarial three-tenant workload. Across four cache capacities and 10 random seeds per capacity, the guard consistently improved total hit rate (+0.052 absolute), Jain fairness (+0.021 absolute), and minimum normalized tenant utility (+0.110 absolute). Protected tenants gained approximately 9.5 percentage points of hit rate; the noisy tenant lost approximately 1.3 percentage points. The guard incurred 2.37× per-access bookkeeping overhead in the simulator, though absolute execution time remained modest.

These results are sufficient to establish directional viability for prototyping but insufficient for production deployment claims. The key remaining evidence gaps are: (1) validation against production or representative benchmark traces, (2) implementation and measurement in a real cache with concurrent access, (3) support for weighted shares and dynamic tenant sets, and (4) quantification of real-system latency and throughput impact. The absence of variance statistics and the `blocked_empty_claims` audit status on the claim ledger further limit the strength of the conclusions that can be drawn. Until these gaps are addressed, the fairness guard should be considered a promising prototype mechanism rather than a validated production solution.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Simulator | `scripts/cache_fairness_sim.py` |
| Aggregator | `scripts/aggregate_results.py` |
| Smoke test metrics | `artifacts/metrics/cache_fairness_20260428T191721.json` |
| Capacity 360 metrics | `artifacts/metrics/cache_fairness_20260428T191750.json` |
| Capacity 450 metrics | `artifacts/metrics/cache_fairness_20260428T191808.json` |
| Capacity 600 metrics | `artifacts/metrics/cache_fairness_20260428T191825.json` |
| Capacity 750 metrics | `artifacts/metrics/cache_fairness_20260428T191842.json` |
| Aggregate summary | `artifacts/metrics/aggregate_summary.json` |
| Environment log | `artifacts/logs/environment_20260429T001733Z.log` |
| Smoke test log | `artifacts/logs/smoke_20260429T001721Z.log` |
| Capacity 360 run log | `artifacts/logs/run_cap360_20260429T001733Z.log` |
| Capacity 450 run log | `artifacts/logs/run_cap450_20260429T001750Z.log` |
| Capacity 600 run log | `artifacts/logs/run_cap600_20260429T001808Z.log` |
| Capacity 750 run log | `artifacts/logs/run_cap750_20260429T001825Z.log` |
| Aggregation log | `artifacts/logs/aggregate_20260429T001917Z.log` |
| Project decision JSON | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260429T001448418308+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T001448418308+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T001448418308+0000/paper_manifest.json` |
| Run notes | `run_notes.md` |
