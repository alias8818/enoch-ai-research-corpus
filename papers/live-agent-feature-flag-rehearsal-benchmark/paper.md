# Feature-Flag Rehearsal as a Safety Gate for Live-Agent Controller Cutovers: A Local Benchmark Pilot

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX orchestration system. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We evaluate whether a feature-flag rehearsal gate—running a canary window on a candidate controller before promotion—can reduce production failure exposure during live-agent controller cutovers, compared to immediate hard cutover. A self-contained Python benchmark replays observed agent telemetry (601 ticks, all failing with `leader_nudge_failed`) and runs stochastic sweeps across healthy, low-flake, borderline, broken, and catastrophic candidate profiles. In the full sweep (641 scenario rows per policy), hard cutover exposed 22,237 production-failed ticks out of 77,401, while flag rehearsal exposed 729 out of 74,697—a 96.72% relative reduction in production failure ticks and 310 fewer bad promotions. The rehearsal gate would have blocked the observed `leader_nudge_failed` failure mode entirely. However, 170 bad promotions persisted under rehearsal, corresponding to low-flake candidates that passed the canary window and failed post-promotion. Rehearsal should therefore be paired with post-promotion monitoring and rollback rather than treated as a complete safety proof. This result is a local benchmark pilot; production validation with a live controller integration remains necessary.

## Introduction

Live-agent orchestration systems that switch between controller implementations face a reliability risk at the cutover boundary. A hard cutover—immediately routing all production traffic through a candidate controller—exposes every production tick to a potentially broken path. When the candidate is faulty, the blast radius is total.

Feature-flag rehearsal offers an alternative: run a canary window where production remains on the baseline controller while the candidate is evaluated, and block promotion if the canary exhibits hard failures. This pattern is well-established in deployment pipelines but has not, to our knowledge, been evaluated specifically for live-agent controller cutovers where the "traffic" consists of agent decision ticks and the failure semantics involve orchestration-level errors such as leader nudge failures.

The motivating observation for this work came from the orchestration system's own telemetry: during a hard-cutover event in the current session, 601 of 601 observed ticks failed with `leader_nudge_failed`. A rehearsal gate would have observed this failure in the canary window and kept production on the baseline.

We ask: can a feature-flag rehearsal gate catch bad live-agent controller cutovers before they affect production ticks, and at what cost in modeled overhead and residual failure exposure?

## Method

### Benchmark Design

We implemented a self-contained Python benchmark using only the standard library (`src/live_agent_feature_flag_rehearsal_benchmark.py`) with accompanying unit tests (`tests/test_feature_flag_rehearsal_benchmark.py`). The benchmark compares two policies:

1. **Hard cutover** (`hard_cutover`): Immediately routes all production ticks through the candidate controller path. No canary window; no blocking condition.

2. **Flag rehearsal** (`flag_rehearsal`): Runs a canary window while production remains on the baseline controller. With the `--hard-fail-block` flag enabled, any canary hard failure blocks promotion to the candidate.

### Evidence Sources

The benchmark draws on two evidence sources:

1. **Observed telemetry**: Local live-agent heartbeat data from `.omx/state/heartbeats/heartbeats.ndjson`. This file recorded 601 ticks from the current session's hard-cutover surface, all failing with reason `leader_nudge_failed`. The baseline error rate was 0.0 and the candidate error rate was 1.0, with both exhibiting 1.0 ms latency.

2. **Synthetic calibrated workloads**: Stochastic profiles spanning healthy, low-flake, borderline, broken, and catastrophic candidate behaviors. Each profile specifies a candidate error rate and latency, allowing controlled sweeps across the failure-rate spectrum. These profiles are researcher-defined and do not derive from production workload characterization.

### Benchmark Modes

Three modes were executed:

- **Smoke**: A fast sanity check with reduced scenario count.
- **Calibration**: A mid-scale sweep to validate the mechanism across the profile space.
- **Full**: A comprehensive stochastic sweep across all profiles and seeds (641 rows per policy).

### Execution Environment

All runs executed on a machine with approximately 117 GiB available memory (MemAvailable started at 122,535,060 KiB and ended at 122,533,728 KiB). Swap is disabled (0B reported). The benchmark is pure-Python with no external dependencies beyond the standard library.

### Verification

Unit tests (3 passed) confirmed core logic correctness. A `py_compile` check verified syntactic validity. Memory posture was stable across the full run, with negligible memory consumption change (~1.3 MiB delta). These checks confirm the benchmark ran without runtime errors but do not validate the realism of the synthetic profiles.

## Results

### Observed Telemetry Replay

The observed heartbeat trace contained 601 ticks with a candidate error rate of 1.0 (all ticks failing with `leader_nudge_failed`) and a baseline error rate of 0.0. Under hard cutover, every observed tick was exposed to the broken candidate. Under flag rehearsal with `--hard-fail-block`, the canary window would have observed the failure before promotion and kept production on baseline, avoiding all 601 production failures.

This result is deterministic given the observed trace and does not depend on the stochastic sweep.

### Smoke Benchmark

| Metric | Hard Cutover | Flag Rehearsal |
|---|---|---|
| Production ticks | 220 | 192 |
| Production failed ticks | 81 | 9 |
| Bad promotions avoided | — | 5 |
| Relative failure reduction | — | 88.89% |
| Extra modeled overhead | — | 16.0 ms |

The reduced production-tick count for flag rehearsal reflects ticks that were never routed to the candidate because promotion was blocked.

### Calibration Benchmark

| Metric | Hard Cutover | Flag Rehearsal |
|---|---|---|
| Production ticks | 6,480 | 6,144 |
| Production failed ticks | 1,867 | 43 |
| Bad promotions avoided | — | 39 |
| Relative failure reduction | — | 97.70% |
| Extra modeled overhead | — | 312.0 ms |

### Full Benchmark

| Metric | Hard Cutover | Flag Rehearsal |
|---|---|---|
| Rows per policy | 641 | 641 |
| Production ticks | 77,401 | 74,697 |
| Production failed ticks | 22,237 | 729 |
| Mean production failure rate | 0.2828 | 0.0102 |
| Median production failure rate | 0.05 | 0.0 |
| Promotions | 641 | 338 |
| Bad promotions | 480 | 170 |
| Bad promotions avoided | — | 310 |
| Contained candidate failures | 0 | 21,480 |
| False blocks | 0 | 0 |
| Relative failure reduction | — | 96.72% |
| Extra modeled overhead | — | 2,424.0 ms |
| Elapsed model time | 77,401.0 ms | 79,825.0 ms |

Flag rehearsal reduced production failure ticks by 96.72% relative to hard cutover and avoided 310 bad promotions. The 170 remaining bad promotions under rehearsal correspond to scenarios where low-flake candidates passed the canary window but failed later in production. Zero false blocks were observed: no healthy candidate was incorrectly blocked by the rehearsal gate in this sweep.

The modeled decision/work overhead was 2,424.0 ms across the full sweep, a modest increment relative to the total elapsed model time of 79,825.0 ms.

### Failure Containment

Under flag rehearsal, 21,480 candidate failures were contained—meaning they occurred in the canary window or in blocked-candidate scenarios rather than in production. Under hard cutover, no candidate failures were contained; all failures propagated directly to production ticks.

### Mixed and Negative Results

The 170 bad promotions under rehearsal represent a meaningful residual failure channel. These occur because candidates with low per-tick failure probabilities can survive a short canary window and subsequently fail in production. The median production failure rate of 0.0 under rehearsal indicates that most scenarios had zero production failures, but the mean of 0.0102 shows that a minority of scenarios contributed disproportionately to the failure count. The rehearsal gate alone does not eliminate this tail risk.

Additionally, the reduction in total production ticks from 77,401 to 74,697 reflects the fact that blocked promotions reduce the number of ticks where the candidate path is exercised at all. Whether this tick reduction is beneficial or harmful depends on whether the candidate would have succeeded; for blocked bad candidates it is protective, but for blocked good candidates it would represent lost opportunity. No false blocks were observed in this sweep, but the false-block rate is parameter-dependent (see Limitations).

## Limitations

1. **Local benchmark, not production integration.** This benchmark models controller behavior with stochastic profiles and replays a single observed heartbeat trace. It does not toggle an actual feature flag in a live controller or measure real agent task-completion outcomes. Production effect sizes may differ from the modeled results reported here.

2. **Low-flake candidates evade short canaries.** The 170 bad promotions under rehearsal demonstrate that candidates with low per-tick failure probabilities can pass a short canary window and fail later. Rehearsal is a pre-promotion filter, not a post-promotion safety net. It must be paired with ongoing monitoring and rollback thresholds.

3. **Modeled overhead, not measured wall-clock cost.** The 2,424.0 ms overhead is a modeled decision/work cost, not a measured latency in a live system. Actual production overhead depends on canary window duration, tick rate, and the cost of the decision logic itself.

4. **Single observed trace.** The heartbeat replay covers one session with one failure mode (`leader_nudge_failed`). Generalization to other failure modes, multi-session scenarios, and different agent topologies requires additional evidence.

5. **No false blocks observed, but false-block risk is parameter-dependent.** Zero false blocks occurred in this sweep, but the false-block rate depends on canary window length and the variance of healthy candidate latency. Shorter canaries reduce overhead but increase the risk of blocking a healthy candidate on a transient flake. The absence of false blocks in this sweep should not be taken as evidence that false blocks are impossible.

6. **Stochastic profiles are synthetic.** The healthy, low-flake, borderline, broken, and catastrophic profiles are researcher-defined. Real candidate controllers may exhibit failure modes not captured by these profiles, including correlated failures, latency degradation without hard errors, and partial functionality loss.

7. **Claim ledger audit blocked.** The structured claim ledger for this artifact was not populated prior to draft generation (audit status: `blocked_empty_claims`). The quantitative results reported here are drawn directly from the run notes and project decision JSON, but they have not passed a formal claim-evidence audit requiring explicit claim-to-evidence-file references.

## Reproducibility Checklist

- [x] **Source code available**: `src/live_agent_feature_flag_rehearsal_benchmark.py`
- [x] **Test suite available**: `tests/test_feature_flag_rehearsal_benchmark.py` (3 passed)
- [x] **No external dependencies**: Pure stdlib Python; no pip install required
- [x] **Exact commands recorded**: All four benchmark invocations logged in `run_notes.md`
- [x] **Output artifacts preserved**: Smoke, calibration, and full result JSON files in `results/`
- [x] **Execution logs preserved**: `logs/pytest_20260430T200851Z.log`, `logs/smoke_20260430T200851Z.log`, `logs/calibration_20260430T200851Z.log`, `logs/full_20260430T200851Z.log`
- [x] **Memory posture verified**: MemAvailable recorded before and after; swap confirmed disabled
- [x] **Syntax check passed**: `py_compile` completed without errors
- [ ] **Live controller integration**: Not performed; required for production validation
- [ ] **Multi-session live trials**: Not performed
- [ ] **Structured claim-evidence audit**: Not passed; claim ledger was empty at draft time

## Conclusion

A feature-flag rehearsal gate substantially reduces production failure exposure during live-agent controller cutovers in a local benchmark. Across a full stochastic sweep, rehearsal reduced production-failed ticks by 96.72% and avoided 310 of 480 bad promotions, at a modest modeled overhead of 2,424.0 ms. The mechanism would have entirely blocked the observed `leader_nudge_failed` failure mode that affected 100% of ticks under hard cutover.

However, rehearsal is not a complete safety proof. Low-flake candidates can pass a short canary and fail post-promotion, accounting for the 170 remaining bad promotions. The mechanism should be deployed as one layer in a defense-in-depth strategy that includes post-promotion monitoring and automated rollback.

This result constitutes a positive local benchmark pilot. Full scientific closure requires integrating the rehearsal gate into the actual hard-cutover controller and running multi-session live trials with endpoints including canary failure rate, bad promotion rate, rollback latency, agent task completion, and production failed ticks. That external controller evidence is not available within this project directory and remains future work.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Benchmark script | `src/live_agent_feature_flag_rehearsal_benchmark.py` |
| Unit tests | `tests/test_feature_flag_rehearsal_benchmark.py` |
| Smoke results | `results/rehearsal_smoke.json` |
| Calibration results | `results/rehearsal_calibration.json` |
| Full results | `results/rehearsal_full.json` |
| Metrics summary | `results/metrics_summary.json` |
| Observed heartbeat source | `.omx/state/heartbeats/heartbeats.ndjson` |
| Pytest log | `logs/pytest_20260430T200851Z.log` |
| Smoke log | `logs/smoke_20260430T200851Z.log` |
| Calibration log | `logs/calibration_20260430T200851Z.log` |
| Full log | `logs/full_20260430T200851Z.log` |
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260430T200618561521+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T200618561521+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T200618561521+0000/paper_manifest.json` |
