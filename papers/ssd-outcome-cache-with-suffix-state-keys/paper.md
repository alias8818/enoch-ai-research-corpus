# SSD Outcome Cache with Suffix-State Keys

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We evaluate an SSD-backed outcome cache keyed by a cryptographic digest of `(prior_state, suffix)` as a mechanism for reusing deterministic suffix computations. The central finding is that including the prior state in the cache key is necessary for correctness: a suffix-only key produces incorrect results whenever the same suffix appears under different preceding states. In a local prototype using SQLite/WAL on SSD, the suffix-state key cache produced zero mismatches against a no-cache baseline across all test configurations (smoke, sweep, and warm-cache benchmarks), while the suffix-only negative control produced thousands of mismatches in sweep runs. Warm-cache speedup reached 81.8× versus no-cache at 100% hit rate; sweep speedups ranged from 1.01× to 4.85× depending on hit rate and configuration. The estimated mean breakeven hit rate is approximately 3.3%. These results are from a local prototype on a single machine with approximately 116 GB available RAM and no swap; cold-cache SSD performance with realistic outcome sizes and cache sizes exceeding RAM remains unmeasured. We conclude that suffix-state keys are correct and can be performant for exact repeated deterministic subproblems, but production deployment requires target-workload repeat telemetry and cold-cache benchmarks that were not performed in this work.

## Introduction

When a computational pipeline repeatedly encounters the same suffix of work under identical prior states, recomputing the outcome each time is wasteful. A natural optimization is to cache the outcome on persistent storage, keyed by the suffix alone. However, if the outcome depends on both the suffix and the state preceding it, a suffix-only key is semantically incorrect: two invocations sharing a suffix but differing in prior state would retrieve the same cached value, producing a wrong answer for at least one invocation.

This work examines whether an SSD-backed cache keyed by a cryptographic digest of `(prior_state, suffix)` can safely reuse exact repeated deterministic subproblems without the correctness failures inherent in suffix-only caching. We further ask whether the overhead of SSD lookups is low enough, and the hit rate high enough, for the scheme to break even or improve wall-clock time.

The hypothesis is twofold: (1) suffix-state keys preserve bit-for-bit correctness while suffix-only keys do not, and (2) the cache is net beneficial when the product of hit rate and per-hit compute savings exceeds the per-lookup SSD overhead.

## Method

### Cache Design

The cache is implemented as an SQLite database in WAL mode stored on SSD. Each entry maps a key—computed as a cryptographic digest of `(prior_state_fingerprint, suffix_digest)`—to a serialized outcome. On a cache hit, the stored outcome is returned directly; on a miss, the outcome is computed, stored, and returned.

### Key Construction

Two key schemes are compared:

- **Suffix-state key**: `hash(prior_state_fingerprint || suffix_digest)`. This encodes the full dependency: the outcome is a function of both the state preceding the suffix and the suffix itself.
- **Suffix-only key** (negative control): `hash(suffix_digest)`. This omits the prior state and is expected to produce incorrect results whenever the same suffix occurs under different prior states.

### Benchmark Harness

A synthetic deterministic workload is used: a function `f(prior_state, suffix) → outcome` where the outcome is computed by a fixed pseudo-random procedure seeded from both inputs. This guarantees determinism (same inputs always produce the same output) while allowing control over compute cost per invocation, suffix diversity, and state diversity.

The benchmark harness (`src/ssd_outcome_cache.py`) accepts parameters for the number of distinct suffixes, rounds of repeated evaluation, compute cost per invocation, and cache mode (no-cache, suffix-state, suffix-only).

### Correctness Testing

Correctness is verified by comparing cached outputs against a no-cache baseline. A mismatch count of zero for suffix-state keys and a nonzero count for suffix-only keys (on state-dependent workloads) constitutes the expected result.

### Performance Measurement

Wall-clock time is measured for each cache mode under varying hit rates and compute costs. Speedup is computed as `time_no_cache / time_cached`. Breakeven hit rate is estimated from measured miss cost (compute + write) and hit cost (SSD read) as:

```
breakeven_hit_rate ≈ miss_overhead / (miss_overhead + compute_savings_per_hit)
```

### Experimental Configurations

1. **Smoke test**: Small-scale correctness and performance sanity check (n=300, rounds=80).
2. **Sweep**: Multiple configurations varying suffix count, rounds, and compute cost to explore the speedup range.
3. **Warm-cache benchmark**: Pre-populated cache with 100% hit rate to measure maximum achievable speedup.
4. **Value-size profile**: Measurement of cache entry sizes for the synthetic workload.

All experiments ran on a single machine with 122,074,524 kB (approximately 116 GB) available RAM and 0 kB swap.

## Results

### Correctness

| Configuration | Suffix-State Mismatches | Suffix-Only Mismatches |
|---|---|---|
| Smoke test | 0 | Not measured in this config |
| Sweep (all configs) | 0 | Thousands |
| Warm-cache benchmark | 0 | Not measured in this config |

The suffix-state cache produced zero mismatches against the no-cache baseline across all test configurations. The suffix-only negative control produced thousands of mismatches in sweep runs, confirming that omitting the prior state from the key is unsound for state-dependent workloads. The exact mismatch count for the suffix-only control in sweep runs is recorded in the sweep summary metrics but was not extracted as a single aggregate figure; the project decision JSON characterizes it qualitatively as "thousands."

### Performance

| Metric | Value |
|---|---|
| Sweep speedup range vs. no-cache | 1.007× – 4.846× |
| Warm-cache speedup vs. no-cache (100% hit rate) | 81.81× |
| Mean breakeven hit rate estimate | 3.27% |

The sweep speedups vary substantially with hit rate and per-invocation compute cost. At low hit rates or low compute cost, the SSD lookup overhead nearly cancels the savings (1.007×). At higher hit rates with expensive computations, speedups approach 4.85×. The warm-cache benchmark, representing an idealized scenario with full population and 100% hit rate, shows 81.81× speedup, establishing an upper bound on what is achievable when every lookup is a hit and compute cost dominates.

The breakeven hit rate of approximately 3.3% indicates that the cache becomes net beneficial even with very sparse repetition, provided the workload is deterministic and the per-invocation compute cost matches the prototype's assumptions. This breakeven estimate is derived from prototype overhead measurements on a single machine and may not transfer to different hardware or workload profiles.

### Cache Size

Cache value sizes were profiled (recorded in `artifacts/metrics/cache_value_size_profile.json`). The specific distribution is not reproduced here because the values are specific to the synthetic workload's serialization format and may not generalize to other domains.

## Limitations

1. **Synthetic workload only.** All measurements use a synthetic deterministic function. Real workloads may have different compute-cost distributions, outcome sizes, and repeat patterns. The 81.81× warm-cache speedup is an upper bound for this specific workload, not a general prediction.

2. **Single machine, likely warm SSD.** All benchmarks ran on a single machine with approximately 116 GB RAM and no swap. The cache was likely warm (recently written or read) for many benchmark iterations, meaning SSD read latency may reflect OS page-cache hits rather than true cold-storage random reads. Cold-cache random-read performance with realistic outcome sizes and a cache larger than RAM is unmeasured and may be substantially worse.

3. **No target-workload telemetry.** The breakeven hit rate of approximately 3.3% is computed from prototype overhead measurements, but the actual repeat rate in a target workload is unknown. If the target workload has fewer than approximately 3.3% exact `(state, suffix)` repeats, the cache will be net harmful in wall-clock time.

4. **Determinism assumption.** The cache is correct only if the outcome is a deterministic function of `(prior_state, suffix)`. Any nondeterminism (floating-point nondeterminism across hardware, runtime version changes, configuration drift) silently corrupts the cache. No mechanism for key invalidation across model, runtime, or config changes was implemented or tested.

5. **No concurrency testing.** The prototype was tested in a single-process setting. Concurrent readers and writers under SQLite/WAL may exhibit different performance or correctness characteristics.

6. **Confidence: medium.** The project decision records medium confidence, reflecting the gap between prototype evidence and production requirements.

7. **Claim audit status: blocked.** The automated claim ledger for this artifact recorded no structured claims and is in a "blocked_empty_claims" state. This paper must not be treated as having passed a strict claim/evidence audit until claims reference public evidence files.

## Reproducibility Checklist

- [x] Source code available: `src/ssd_outcome_cache.py`, `scripts/test_ssd_outcome_cache.py`, `scripts/run_sweep.py`, `scripts/warm_cache_benchmark.py`, `scripts/cache_value_size_profile.py`
- [x] Exact commands recorded in run notes
- [x] Test logs preserved: `artifacts/logs/test_smoke.log`, `artifacts/logs/test_after_determinism_fix.log`, `artifacts/logs/final_pytest.log`
- [x] Benchmark logs preserved: `artifacts/logs/benchmark_smoke.log`, `artifacts/logs/sweep_summary.log`, `artifacts/logs/warm_cache_benchmark.log`, `artifacts/logs/cache_value_size_profile.log`
- [x] Metrics artifacts preserved: `artifacts/metrics/smoke.json`, `artifacts/metrics/sweep_summary.json`, `artifacts/metrics/warm_cache.json`, `artifacts/metrics/cache_value_size_profile.json`
- [x] Machine-readable decision: `.omx/project_decision.json`
- [x] Hardware context recorded: approximately 116 GB RAM, 0 kB swap
- [ ] Cold-cache SSD benchmarks not performed
- [ ] Real-workload repeat-rate telemetry not collected
- [ ] Concurrency tests not performed
- [ ] Claim/evidence audit not passed (claim ledger is in blocked_empty_claims state)

## Conclusion

An SSD-backed outcome cache keyed by `(prior_state, suffix)` is correct—producing zero mismatches against a no-cache baseline across all prototype tests—while a suffix-only key is demonstrably unsound, producing thousands of mismatches on state-dependent workloads. The suffix-state cache is performant in prototype conditions: sweep speedups range from 1.01× to 4.85×, and a warm cache at 100% hit rate achieves 81.81× speedup. The estimated breakeven hit rate of approximately 3.3% suggests viability even with sparse repetition.

However, these results are from a local prototype on a single machine with a synthetic workload and likely warm SSD reads. Production deployment requires three steps before the results can be generalized: (1) instrument the target workload to measure the actual rate of exact `(state_fingerprint, suffix_digest)` repeats, (2) benchmark cold-cache random reads with realistic outcome sizes and cache sizes exceeding RAM, and (3) define a state-fingerprint invalidation strategy across model, runtime, and configuration changes. Without these, the prototype evidence supports viability only under the stated constraints, and the medium confidence rating reflects this gap.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Cache implementation | `src/ssd_outcome_cache.py` |
| Correctness tests | `scripts/test_ssd_outcome_cache.py` |
| Sweep runner | `scripts/run_sweep.py` |
| Warm-cache benchmark | `scripts/warm_cache_benchmark.py` |
| Value-size profiler | `scripts/cache_value_size_profile.py` |
| Smoke test log | `artifacts/logs/test_smoke.log` |
| Post-fix test log | `artifacts/logs/test_after_determinism_fix.log` |
| Final pytest log | `artifacts/logs/final_pytest.log` |
| Smoke benchmark log | `artifacts/logs/benchmark_smoke.log` |
| Sweep summary log | `artifacts/logs/sweep_summary.log` |
| Warm-cache benchmark log | `artifacts/logs/warm_cache_benchmark.log` |
| Value-size profile log | `artifacts/logs/cache_value_size_profile.log` |
| Smoke metrics | `artifacts/metrics/smoke.json` |
| Sweep summary metrics | `artifacts/metrics/sweep_summary.json` |
| Warm-cache metrics | `artifacts/metrics/warm_cache.json` |
| Value-size profile metrics | `artifacts/metrics/cache_value_size_profile.json` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260505T232452454131+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260505T232452454131+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260505T232452454131+0000/paper_manifest.json` |
