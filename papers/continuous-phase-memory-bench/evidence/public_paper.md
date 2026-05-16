# Continuous-Phase Memory Bench: A Synthetic Benchmark for Detecting Phase-Aligned Retrieval Failures in Temporal Memory Systems

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, metric summaries, and benchmark script outputs). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review has been performed.

---

## Abstract

We present Continuous-Phase Memory Bench, a synthetic benchmark designed to expose retrieval accuracy differences among memory system strategies that are invisible or muted under conventional discrete-time evaluation. The benchmark generates temporal knowledge graphs in which entity values rotate continuously by phase across repeated cycles. We evaluate five retrieval predictors—semantic majority, exponential decay, recency, discrete bucket, and a phase-aware circular kernel—under two query modes: a discrete control (querying shortly after observation) and a continuous-phase mode (querying at arbitrary phase positions, including cases where the relevant evidence is older but phase-aligned). Across 20 random seeds producing 384,000 events, 640,000 queries, and 3,200,000 predictor evaluations, recency and discrete-bucket strategies achieve 0.977 accuracy on discrete-control queries but only 0.692 on continuous-phase queries, while the phase-aware kernel maintains 0.962 (discrete) and 0.908 (continuous). The resulting +0.216 absolute accuracy gap on continuous-phase queries is stable across seeds (phase kernel range 0.902–0.915; recency range 0.684–0.697). These results establish construct validity for the benchmark within its synthetic, known-period setting but do not demonstrate external validity against real user-agent memory behavior.

## 1. Introduction

Memory systems for conversational agents and long-context language models typically retrieve stored facts using some combination of semantic similarity, recency weighting, and coarse temporal bucketing. Evaluating such systems commonly involves querying facts shortly after they are observed, or within the same session or episode. Under these discrete-time evaluation conditions, recency-based and bucket-based strategies perform well, and differences between more sophisticated temporal retrieval methods and simple baselines can be small.

However, real-world memory use includes situations where a fact's relevance rotates in and out of currency over time—seasonal preferences, recurring schedules, periodic policies. In such cases, the most recently observed value may not be the currently correct one; the correct value depends on the phase relationship between the query time and prior observations. A benchmark that only queries facts near their observation time will fail to distinguish systems that model this phase-aligned recurrence from systems that rely on recency or semantic frequency alone.

We propose a synthetic benchmark construct—continuous-phase memory evaluation—that specifically tests retrieval under arbitrary phase positions, including cases where the relevant evidence is older but shares the same phase as the query. We implement this as a parametric generator of temporal knowledge graphs with rotating entity values and evaluate five predictor strategies. The central claim under test is: *a continuous-phase synthetic memory benchmark exposes retrieval ranking differences that are mostly hidden by discrete recency controls.*

This work is a viability study. It demonstrates that the benchmark construct can discriminate among retrieval strategies under controlled synthetic conditions. Whether this discrimination transfers to real-world memory systems and naturalistic scenarios remains an open question.

## 2. Method

### 2.1 Benchmark Generator

The benchmark is implemented in `scripts/continuous_phase_memory_bench.py`. It generates a synthetic temporal knowledge graph with the following structure:

- **Entities** each carry key/value facts whose active value rotates continuously by phase over repeated cycles.
- Each cycle produces observations per entity; the value at observation time is determined by the entity's phase position within the cycle.
- Queries are issued at specified points and ask for the current value of an entity's key.

The generator is parametric: the number of entities, keys per entity, cycles, observations per cycle, queries per cycle, and noise rate are all configurable. This permits scaling from small smoke tests to larger calibrated runs.

### 2.2 Query Modes

Two query modes are used:

1. **`discrete_control`**: Queries are issued shortly after an observation. Recency and bucket baselines are expected to perform well here, as the most recent observation is likely to match the current phase.

2. **`continuous_phase`**: Queries are issued at arbitrary phase positions, including cases where the relevant evidence is older but phase-aligned with the query. This mode specifically tests whether a retrieval system can recover the correct value when recency is misleading.

### 2.3 Predictor Strategies

Five predictors are evaluated:

| Predictor | Description |
|---|---|
| `semantic_majority` | Returns the most frequently observed value (semantic frequency baseline). |
| `recency` | Returns the value from the latest matching event. |
| `exp_decay` | Exponential recency weighting over prior observations. |
| `discrete_bucket` | Coarse cycle/session bucket selection followed by recency within the bucket. |
| `phase_kernel` | Phase-aware circular kernel over prior observations; weights observations by their angular proximity to the query phase. |

The phase-aware kernel is provided the ground-truth period. Period estimation and multi-period scenarios are not tested in this version. This is a significant simplification: in realistic settings, the period would typically be unknown.

### 2.4 Experimental Configuration

**Smoke test** (construct validation):

```
--entities 3 --keys 1 --cycles 3 --obs-per-cycle 4 --query-per-cycle 2
```

**Calibrated run** (20 seeds):

```
--entities 50 --keys 4 --cycles 16 --obs-per-cycle 6 --query-per-cycle 5 --noise-rate 0.03
```

Each seed produces an independent random instance. The noise rate of 0.03 introduces a small fraction of incorrect observations to test robustness.

**Post-optimization validation** (seed 0 only):

```
--seed 0 --entities 50 --keys 4 --cycles 16 --obs-per-cycle 6 --query-per-cycle 5 --noise-rate 0.03
```

This was run after an indexing optimization to confirm correctness and measure throughput improvement. Accuracy results were confirmed unchanged; only throughput was affected.

### 2.5 Platform and Memory Posture

All runs were executed on Linux 6.17.0-1014-nvidia-aarch64, Python 3.12.3. The system ran with zero swap space (SwapTotal: 0 kB, SwapFree: 0 kB), consistent with a no-swap GB10 constraint. The earlyoom daemon was detected running (pid=1888) across all benchmark telemetry samples. MemAvailable before the calibrated run was 122,489,212 kB; after, 122,562,160 kB. Per-seed MemAvailable deltas ranged from −69,708 KiB to −5,384 KiB, indicating no memory pressure during execution.

These are toy simulation / synthetic benchmark runs on a single machine. They are not CUDA copy calibrations, llama.cpp hook prototypes, or production validations.

## 3. Results

### 3.1 Main Accuracy Results

Across 20 seeds, 384,000 events, 640,000 queries, and 3,200,000 predictor evaluations:

| Predictor | `discrete_control` mean acc | `continuous_phase` mean acc |
|---|---:|---:|
| `semantic_majority` | 0.410 | 0.329 |
| `exp_decay` | 0.639 | 0.394 |
| `recency` | 0.977 | 0.692 |
| `discrete_bucket` | 0.977 | 0.692 |
| `phase_kernel` | 0.962 | 0.908 |

On `discrete_control` queries, recency, discrete bucket, and phase-aware retrieval all achieve high accuracy (0.962–0.977). A discrete-time benchmark would largely fail to distinguish these strategies.

On `continuous_phase` queries, the phase-aware kernel reaches 0.908 mean accuracy, while recency and discrete bucket drop to 0.692. Semantic-only and decay baselines remain much lower (0.329 and 0.394 respectively).

The continuous-phase gap between `phase_kernel` and `recency` is +0.216 absolute accuracy.

### 3.2 Seed-Level Stability

Phase kernel continuous-phase accuracy ranges from 0.902 to 0.915 across the 20 seeds. Recency continuous-phase accuracy ranges from 0.684 to 0.697. The gap is consistent and does not depend on a particular random seed.

### 3.3 Throughput

Pre-optimization calibrated throughput: 3,200,000 predictor evaluations across 640,000 queries, yielding a mean of 4,742 predictor-query evaluations per second.

Post-optimization validation throughput (seed 0): 6,699 predictor-query evaluations per second.

The throughput improvement reflects an indexing optimization in the benchmark script; accuracy results were confirmed unchanged on seed 0 after the optimization.

### 3.4 Negative and Mixed Observations

Several findings qualify the positive interpretation:

- **Phase kernel underperforms on discrete control.** The `phase_kernel` predictor does not achieve the highest accuracy on `discrete_control` queries (0.962 vs. 0.977 for recency/discrete_bucket). This deficit of −0.015 reflects the fact that the circular kernel spreads some weight to same-phase observations from prior cycles even when the most recent observation is correct, introducing minor noise. This is a genuine trade-off: phase-awareness helps when recency is misleading but slightly hurts when recency is sufficient.

- **Poor baseline performance on both modes.** The `semantic_majority` and `exp_decay` baselines perform poorly on both query modes, confirming that neither semantic frequency nor simple decay is sufficient for this task. Their low discrete_control accuracy (0.410, 0.639) indicates the task is not trivially solvable by any non-temporal strategy, but also means these baselines are not competitive contenders.

- **Recency and discrete bucket produce identical results.** `recency` and `discrete_bucket` produce identical accuracy values (0.977 discrete, 0.692 continuous). This is expected given the benchmark's cycle structure: the discrete bucket collapses to recency when bucket boundaries align with cycles. This identity means the discrete_bucket predictor, as configured here, provides no additional information beyond recency.

- **Phase kernel does not reach ceiling.** Even on continuous-phase queries, the phase kernel achieves 0.908 rather than near-perfect accuracy. The 0.03 noise rate and the kernel's weighting scheme both contribute to this residual error. Whether a more sophisticated phase-aware method could close this gap is not tested.

## 4. Limitations

1. **Synthetic-only evidence.** The benchmark uses procedurally generated temporal knowledge graphs with known periodic structure. It establishes construct validity—showing that continuous-phase queries discriminate among retrieval strategies where discrete queries do not—but it does not establish external validity against real user-agent memory behavior. Real-world memory scenarios may involve irregular periods, partial observations, and ambiguous phase boundaries not modeled here.

2. **Known period.** The phase-aware kernel is provided the ground-truth period. In realistic settings, the period may be unknown, may vary across entities, or may not exist at all. Period estimation and multi-period scenarios remain future work. The current results therefore represent an upper bound on what a phase-aware system could achieve without period information.

3. **No LLM-in-the-loop.** This evaluation tests abstract retrieval strategies on synthetic data, not actual language model memory implementations. Whether the observed discrimination transfers to vector-memory, graph-memory, or other production retrieval systems is untested.

4. **Single noise rate.** Only a 3% noise rate was tested. Sensitivity to higher noise rates or adversarial noise patterns is not characterized.

5. **No human-authored scenarios.** The benchmark lacks manually crafted scenarios that might capture subtler forms of phase recurrence (e.g., seasonal preference shifts, recurring scheduling constraints). Such scenarios would strengthen external validity claims.

6. **No formal claims registered.** The claim ledger for this paper contains no registered claims at the time of generation. The results reported here are drawn directly from the run notes and project decision JSON; they have not undergone independent claim auditing.

7. **Identical recency and discrete_bucket results.** The structural identity of these two predictors under the current benchmark configuration limits what can be concluded about bucket-based strategies more generally.

## 5. Reproducibility Checklist

- [x] **Benchmark script available:** `scripts/continuous_phase_memory_bench.py`
- [x] **Random seeds recorded:** Seeds 0–19 used for calibrated run; seed 0 for validation.
- [x] **All command-line arguments documented:** Full invocation strings recorded in run notes.
- [x] **Output artifacts preserved:** Metric CSVs, telemetry JSON, and command logs at known paths.
- [x] **Platform details recorded:** OS version, Python version, swap configuration, earlyoom status.
- [x] **Memory posture verified:** Zero swap, earlyoom running, MemAvailable monitored before/after.
- [x] **Smoke test passed:** Small-configuration run completed before full calibrated run.
- [x] **Post-optimization validation:** Correctness confirmed after indexing optimization on seed 0.
- [ ] **Public repository:** Not yet released; packaging as a public benchmark harness is planned.
- [ ] **External LLM system evaluation:** Not performed in this study.
- [ ] **Readiness audit:** Not completed; flagged as a missing signal in the review item.

## 6. Conclusion

The Continuous-Phase Memory Bench demonstrates that a synthetic benchmark with continuous-phase query modes can expose retrieval accuracy differences among memory strategies that are largely invisible under discrete-time evaluation. On discrete-control queries, recency, discrete-bucket, and phase-aware retrieval all achieve accuracy above 0.96, making them difficult to distinguish. On continuous-phase queries, the phase-aware kernel maintains 0.908 accuracy while recency and discrete-bucket strategies drop to 0.692, producing a +0.216 absolute gap that is stable across 20 random seeds.

This is a positive viability result for the benchmark construct. The synthetic task is not simply harder overall; it is specifically easy for baselines under discrete controls and discriminative under continuous phase. This matches the proposed success criterion: expose ranking differences among memory systems that are invisible or muted on discrete-time evaluation sets.

However, the result is limited to synthetic, known-period scenarios without LLM-in-the-loop evaluation. The phase-aware kernel's advantage depends on access to ground-truth period information, which would not be available in realistic deployments. External validity—whether this discrimination transfers to real user-agent memory behavior and production retrieval systems—remains unestablished. The identical performance of recency and discrete-bucket predictors under the current configuration further limits the generality of conclusions about bucket-based strategies.

Next steps include packaging the generator as a public benchmark, adding human-authored scenarios with hidden or multiple periods, and evaluating at least one vector-memory and one graph/temporal-memory implementation.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Benchmark script | `scripts/continuous_phase_memory_bench.py` |
| Smoke test metrics | `artifacts/metrics/smoke_optimized_20260501T202035Z/` |
| Calibrated metrics (20 seeds) | `artifacts/metrics/calibrated_20260501T200833Z/` |
| Aggregate summary CSV | `artifacts/metrics/calibrated_20260501T200833Z/aggregate_summary.csv` |
| Aggregate telemetry JSON | `artifacts/metrics/calibrated_20260501T200833Z/aggregate_telemetry.json` |
| Calibrated command log | `artifacts/logs/calibrated_20260501T200833Z.log` |
| Post-optimization validation metrics | `artifacts/metrics/validation_optimized_20260501T202041Z/seed_0` |
| Post-optimization validation log | `artifacts/logs/validation_optimized_20260501T202041Z.log` |
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260501T200618567574+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T200618567574+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T200618567574+0000/paper_manifest.json` |
