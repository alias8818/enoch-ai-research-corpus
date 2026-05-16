# Load-Balancer-Free Symmetry Breaking via Client-Side Rendezvous Hashing: A Simulation Study

> **AI provenance notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, and simulation logs). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate whether a cluster of independent clients can break routing symmetry without a central load balancer, using only locally computable placement rules. We implement and evaluate Highest-Random-Weight (HRW) rendezvous hashing as a client-side deterministic symmetry breaker, comparing it against four baselines—no symmetry breaking (first-backend), modulo hashing, per-request random choice, and power-of-two-choices with global load state—across three traffic scenarios (uniform keys, single hot key, 16 hot keys) with 200,000 requests over 64 backends. Under uniform traffic, HRW reduces the max-to-mean load ratio from 64.0 (no breaker) to 1.035, comparable to random routing (1.031), while preserving deterministic client-side agreement and incurring only ~1.5% key remapping on membership changes versus ~98.5% for modulo hashing. However, under a single dominant hot key absorbing 90% of traffic, HRW's deterministic affinity maps that key to one backend, yielding max/mean ≈ 57.8—no meaningful improvement over the no-breaker baseline. Under 16 hot keys, HRW achieves max/mean = 14.454, which is worse than modulo hashing (7.352), though modulo retains catastrophic resize churn (~98.5% remap). We conclude that HRW is conditionally viable as a stateless placement primitive for uniform or request-id-addressed workloads but is not a complete load-balancer replacement for sticky hot-key traffic without additional mechanisms such as sub-key splitting, bounded-load feedback, or replication.

## 1 Introduction

In distributed systems with multiple symmetric backend replicas, a fundamental routing problem arises: if all clients independently select a backend using the same default rule (e.g., "choose the first available"), all traffic converges on a single backend, wasting the remaining capacity. The conventional solution places a central load balancer on the request path, but this introduces a stateful, potentially bottlenecked component.

An alternative is to equip clients with a deterministic, stateless placement rule that produces the same mapping without coordination yet distributes load across backends. Highest-Random-Weight (HRW) hashing, also known as rendezvous hashing, maps each object key to the backend scoring highest under `hash(key, backend)`, enabling clients to agree on mappings without shared state. A key operational property is low churn: when the backend set changes, only a small fraction of keys remap, unlike modulo hashing.

This study asks: **Can a cluster break routing symmetry without a central load balancer, using only client-computable placement rules, and under what conditions does this approach suffice?**

We do not assume that HRW solves all load-balancing problems. In particular, deterministic key-to-backend affinity implies that a single dominant key cannot be split across backends without changing the assignment unit. We evaluate this trade-off explicitly.

## 2 Method

### 2.1 Algorithms

We compare five assignment algorithms:

1. **first**: No symmetry breaker. All requests route to backend 0. This represents the pathological baseline of uncoordinated clients sharing a default.
2. **modulo**: Deterministic `hash(key) % N`. Balances uniformly distributed keys but remaps nearly all keys when `N` changes.
3. **random**: Per-request uniform random choice among backends. Balances load statistically but provides no key affinity or client consensus.
4. **hrw**: Highest-Random-Weight rendezvous hashing. For each request key `k` and each backend `b`, compute `hash(k, b)`; assign to the backend with the highest score. Clients computing the same hash function agree on the same backend without coordination.
5. **p2c_oracle**: Power-of-two choices with access to global load state. Samples two candidate backends and selects the less-loaded one. This is not load-balancer-free; it serves as an upper-bound reference for what telemetry-aware routing can achieve.

### 2.2 Traffic Scenarios

- **uniform**: All 200,000 request keys are unique. This is the favorable case for any hash-based scheme.
- **hotspot_90pct_1key**: 90% of requests share a single sticky key; 10% are unique. This stress-tests deterministic affinity under extreme skew.
- **hotspot_90pct_16keys**: 90% of requests are spread over 16 sticky hot keys; 10% are unique. This tests whether spreading the hot set across more keys allows HRW to improve.

### 2.3 Metrics

- **max/mean**: Maximum backend load divided by mean backend load. Ideal value is 1.0; higher values indicate imbalance.
- **Coefficient of variation (CV)**: Standard deviation of backend loads divided by mean. Closer to 0 is better.
- **Gini coefficient**: Inequality measure over backend load distribution. Closer to 0 is better.
- **Remap fraction**: Fraction of keys that change backend assignment when one backend is added or removed. Lower is better for operational stability. Applicable only to deterministic mappings (modulo, hrw).

### 2.4 Experimental Setup

The simulation was implemented in `experiments/symmetry_breaker_sim.py` and executed on an NVIDIA GB10 system (Linux aarch64, 20 CPUs, ~122 GB available memory). A smoke test with 10,000 requests and 16 backends preceded the full run. The full run used 200,000 requests and 64 backends. Wall time was 1 minute 45 seconds at 99% CPU utilization with a maximum resident set of 49,308 kB. No swap was available or required. GPU utilization was 0%; this is a CPU/hash simulation, not a GPU workload.

**This is a toy simulation** measuring assignment counts and load distribution. It does not model real network latency, queueing effects, or service-time distributions. It is not a llama.cpp hook-prototype, CUDA copy calibration, or production validation.

## 3 Results

### 3.1 Uniform Traffic

| Algorithm | max/mean | CV | Gini | Add-one remap | Remove-one remap |
|-----------|---------:|----:|-----:|---------------:|-----------------:|
| first | 64.000 | 7.937 | 0.984 | n/a | n/a |
| modulo | 1.045 | 0.021 | 0.012 | 0.985 | 0.985 |
| hrw | 1.035 | 0.016 | 0.009 | 0.015 | 0.016 |
| random | 1.031 | 0.015 | 0.008 | n/a | n/a |
| p2c_oracle | 1.000 | 0.000 | 0.000 | n/a | n/a |

Under uniform traffic, HRW achieves max/mean = 1.035, comparable to random routing (1.031) and modulo hashing (1.045). The p2c_oracle achieves perfect balance (1.000) by construction. The no-breaker baseline is catastrophically imbalanced at 64.0.

The critical operational difference is remap fraction. HRW remaps only ~1.5% of keys on a membership change, while modulo hashing remaps ~98.5%. This confirms the well-known property of rendezvous hashing: minimal disruption on resize.

### 3.2 Single Hot Key (90% traffic to one key)

| Algorithm | max/mean | CV | Gini |
|-----------|---------:|-----:|-----:|
| first | 64.000 | 7.937 | 0.984 |
| modulo | 57.764 | 7.152 | 0.890 |
| hrw | 57.772 | 7.153 | 0.890 |
| random | 1.031 | 0.015 | 0.008 |
| p2c_oracle | 28.839 | 5.000 | 0.870 |

When 90% of traffic carries a single key, both HRW and modulo hashing map that key to one backend, producing max/mean ≈ 57.8. This is only marginally better than the no-breaker baseline (64.0), because the 10% unique-key traffic distributes across the remaining 63 backends while the single hot backend absorbs 90% of all requests.

Random routing balances well (1.031) because it ignores key identity, but it sacrifices deterministic affinity and client consensus entirely. The p2c_oracle improves to 28.839 because it can route the 10% unique-key traffic to the least-loaded backend, but it still cannot split the single sticky key across backends.

HRW's remap fraction remains low (0.2% add, 0.1% remove) in this scenario, but this property is irrelevant when the dominant problem is hot-key concentration.

### 3.3 16 Hot Keys (90% traffic spread over 16 keys)

| Algorithm | max/mean | CV | Gini |
|-----------|---------:|-----:|-----:|
| first | 64.000 | 7.937 | 0.984 |
| modulo | 7.352 | 1.687 | 0.705 |
| hrw | 14.454 | 2.381 | 0.787 |
| random | 1.031 | 0.015 | 0.008 |
| p2c_oracle | 2.884 | 1.078 | 0.550 |

With 16 hot keys, modulo hashing (max/mean = 7.352) outperforms HRW (14.454). This is an unexpected negative result for HRW: its random score assignment does not guarantee that 16 keys spread evenly across 64 backends, and in this sample, some backends received multiple hot keys while others received none. Modulo hashing, by contrast, deterministically spreads consecutive hash values across backends, yielding a more even spread for this particular key count and backend count.

The p2c_oracle (2.884) substantially outperforms both, confirming that load awareness matters for skewed traffic. Random routing again balances well at the cost of all affinity.

### 3.4 Summary of Trade-offs

No single algorithm dominates across all scenarios. HRW provides an attractive combination of near-random balance under uniform traffic, deterministic client consensus, and minimal resize churn. However, it fails to balance sticky hot keys, and in the 16-hot-key scenario, it is outperformed by the simpler modulo hashing on balance—though modulo retains its catastrophic resize churn.

## 4 Limitations

1. **Toy simulation only.** This study measures assignment counts, not real network latency, queueing delays, or service-time distributions. Backend load is measured as request count, not utilization or latency. A production system with variable service times could exhibit different behavior.

2. **No heavy-tailed service times.** All requests are treated as unit-weight. Real workloads with highly variable per-request cost may amplify or alter the observed imbalances.

3. **No backend heterogeneity.** All backends are assumed identical in capacity. HRW can be adapted with weighted scores, but this was not tested.

4. **Single hash function.** The simulation uses one hash function. Hash quality (uniformity, collision resistance) affects HRW balance; a poor hash could degrade results.

5. **No implementation beyond simulation.** No real networking stack, no concurrency, no failure handling, no actual client-server protocol was implemented. This is a combinatorial/assignment simulation, not a system prototype.

6. **Hot-key results are inherent to the design, not a flaw.** HRW's inability to split a single key across backends is a direct consequence of its deterministic key-affinity property. Whether this is acceptable depends on the application's requirement for key-level session stickiness.

7. **Notion page unavailable.** The original project description was not accessible from the execution environment; the experiment interprets the project title as a client-side distributed request placement problem. If the original intent differed, the scope of this study may not fully align.

8. **Random seed reproducibility.** Random seed behavior is not explicitly documented in the run notes. Reproducibility of exact numeric results depends on hash implementation and seed. The simulation script should be inspected for seed handling.

## 5 Reproducibility Checklist

- [x] Source code available: `experiments/symmetry_breaker_sim.py`
- [x] Smoke test executed before full run: 10,000 requests, 16 backends
- [x] Full run parameters documented: 200,000 requests, 64 backends
- [x] Host telemetry recorded before and after: `logs/host_telemetry_before.txt`, `logs/host_telemetry_after.txt`
- [x] Resource usage measured: `/usr/bin/time -v` output in `logs/full_metrics.time`
- [x] Exit status verified: 0 (clean exit)
- [x] Swap disabled and confirmed: 0 kB swap total, 0 swaps occurred
- [x] Raw metrics preserved: `logs/smoke_metrics.json`, `logs/full_metrics.json`
- [x] Decision and evidence logged: `.omx/project_decision.json`
- [ ] Random seed explicitly documented: Not confirmed in run notes
- [ ] Independent reproduction by third party: Not performed

## 6 Conclusion

Client-side rendezvous hashing (HRW) is a conditionally viable load-balancer-free symmetry breaker. Under uniform or request-id-addressed traffic with 64 backends, it reduces the max-to-mean load ratio from 64.0 (no breaker) to 1.035, comparable to random routing while preserving deterministic client consensus and incurring only ~1.5% key remapping on membership changes—versus ~98.5% for modulo hashing. These are meaningful advantages for systems that value stateless agreement and operational stability.

However, HRW is not a complete replacement for a load balancer. Under a single dominant hot key (90% of traffic), max/mean remains ~57.8, identical to the no-breaker baseline in practical terms. Under 16 hot keys, HRW's balance (max/mean = 14.454) is worse than modulo hashing (7.352), though modulo's catastrophic resize churn remains. These results confirm that deterministic key-to-backend affinity, while useful for consensus, is fundamentally incompatible with splitting a hot key's load across multiple backends.

For workloads with sticky hot keys, HRW alone is insufficient. Viable extensions include: (a) splitting the assignment unit below the hot key by incorporating request IDs or substream identifiers into the HRW key; (b) bounded-load HRW with backend-advertised capacity budgets; (c) replication with secondary choices and backpressure; or (d) a telemetry-aware scheduler such as power-of-two choices. The recommended next experiment is to implement k-choice HRW candidates with local load budgets and evaluate against heavy-tailed service times and heterogeneous backend capacities.

---

## Referenced Artifacts

| Artifact | Path / Key |
|----------|-----------|
| Simulation script | `experiments/symmetry_breaker_sim.py` |
| Smoke test metrics | `logs/smoke_metrics.json` |
| Smoke test stdout | `logs/smoke_metrics.stdout` |
| Full run metrics | `logs/full_metrics.json` |
| Full run stdout | `logs/full_metrics.stdout` |
| Full run time log | `logs/full_metrics.time` |
| Host telemetry (before) | `logs/host_telemetry_before.txt` |
| Host telemetry (after) | `logs/host_telemetry_after.txt` |
| Project decision JSON | `.omx/project_decision.json` |
| Project session metrics | `.omx/metrics.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260502T233050806203+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T233050806203+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T233050806203+0000/paper_manifest.json` |
| Project directory | `<control-plane-projects>/source-record-redacted` |
| Project ID | `source-record-redacted` |
