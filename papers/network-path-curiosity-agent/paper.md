# Network Path Curiosity Agent: Curiosity-Driven Probing for Online Network Anomaly Detection and Topology Recommendation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, metrics files, and logs). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present a curiosity-driven probing policy for online network anomaly detection that prioritizes probe targets based on path uncertainty, observation staleness, and observed risk. The agent learns per-path baselines for latency, packet loss, and route stability, then detects anomalies via z-score thresholds, loss clustering, and route-change signals. In a synthetic network simulation with injected incidents (latency spikes, packet loss, route flaps, congestion), the curiosity policy achieved a mean F1 of 0.9322 across five seeded runs, compared to 0.8218 for a round-robin baseline—a delta of +0.1104. The curiosity policy also sampled 90.2 more anomalous path observations per run on average. A local hardware smoke test on a GB10-class machine confirmed basic probing functionality and telemetry posture. However, all F1 evidence derives from simulator ground-truth labels, not production network traces. We report these results as sufficient for lab-pilot continuation but insufficient for production deployment claims.

## Introduction

Network operators routinely probe paths to detect degradation, but fixed probe schedules allocate effort uniformly regardless of path state. Stable paths receive the same attention as paths experiencing incipient faults, wasting probe budget on uninformative observations while potentially under-sampling deteriorating routes. Adaptive probing strategies that concentrate effort where information gain is highest could improve detection quality without increasing probe volume.

The core hypothesis under evaluation is that a curiosity policy—one that prioritizes paths with high uncertainty, stale observations, or elevated risk—can learn per-path baselines online, detect anomalies more effectively than a fixed schedule, and emit actionable topology recommendations. This paper reports on a bounded prototype evaluation of that hypothesis using synthetic network simulation with labeled incidents.

The contribution is empirical: we demonstrate that curiosity-driven target selection yields measurably higher detection quality than round-robin probing under a controlled incident generator, and we characterize the gap between these simulator results and production network conditions. We do not claim production readiness.

## Method

### Simulation Environment

The prototype (`scripts/network_path_curiosity.py`) is a dependency-free Python harness that simulates multiple network paths. Each path produces observations of latency, packet loss, hop count, and a route hash. The simulator injects labeled incidents of four types: `latency_spike`, `packet_loss`, `route_flap`, and `congestion`. Truth labels are available for evaluation, enabling computation of F1, precision, and recall against ground truth.

### Curiosity Policy

The curiosity policy selects the next probe target by scoring each path on three dimensions:

1. **Uncertainty**: variance in recent observations relative to the learned baseline.
2. **Staleness**: time since the last observation of the path.
3. **Risk**: historical anomaly rate for the path.

Paths with higher composite scores are probed first. This contrasts with the round-robin baseline, which cycles through all paths in fixed order regardless of observed state.

### Online Baseline Learning

Per-path baselines for latency and loss are maintained as running statistics. Anomalies are detected when:

- Latency z-score exceeds a threshold relative to the path baseline.
- A cluster of recent losses exceeds an expected count.
- A route hash change is observed (route flap).

### Topology Recommendations

When anomalies are detected, the agent emits rule-based advisory recommendations (e.g., suggesting alternative routes or flagging congested links). These recommendations are text output only; no route changes are applied automatically.

### Evaluation Protocol

Anomaly detection quality is measured by F1 score against simulator truth labels. A viability threshold of F1 ≥ 0.65 was established prior to running experiments. Three experimental conditions were evaluated:

1. **Small smoke**: 3 paths, 120 probes, single run.
2. **Calibration**: 5 runs with seeds 11–15, reporting mean and minimum F1.
3. **Policy comparison**: 5 runs each for curiosity and round-robin policies (seeds 21–25), reporting mean F1, precision, recall, alert rate, and sampled anomaly count.

A local network smoke test was also performed on GB10 hardware to verify basic probing functionality and telemetry posture. This test did not evaluate detection quality.

## Results

### Small Smoke Test

| Metric | Value |
|---|---|
| Paths | 3 |
| Probes | 120 |
| F1 | 0.8000 |
| Precision | 0.6667 |
| Recall | 1.0000 |
| Truth anomalies sampled | 12 |
| Viable (F1 ≥ 0.65) | Yes |

The smoke test exceeded the viability threshold. Precision was modest (0.6667), indicating a non-trivial false positive rate even in this small sample, while recall was perfect. This single short run is insufficient to draw strong conclusions but confirmed that the prototype produces non-degenerate output.

### Calibration (5 Runs, Seeds 11–15)

| Metric | Value |
|---|---|
| Mean F1 | 0.9401 |
| Minimum F1 | 0.8764 |
| Mean precision | 0.9181 |
| Mean recall | 0.9639 |
| Mean alert rate | 0.1756 |
| Mean truth anomalies sampled | 120.0 |
| All runs viable | Yes |

All five calibration runs exceeded the viability threshold, with a minimum F1 of 0.8764—well above the 0.65 bar. The mean alert rate of 0.1756 suggests the detector is not excessively noisy under these simulation conditions. However, the relatively narrow spread between minimum and mean F1 (0.8764–0.9401) reflects the controlled nature of the synthetic environment; wider variance should be expected under real-world conditions.

### Curiosity vs. Round-Robin Policy Comparison (5 Runs Each, Seeds 21–25)

| Metric | Curiosity | Round-Robin | Delta |
|---|---|---|---|
| Mean F1 | 0.9322 | 0.8218 | +0.1104 |
| Minimum F1 | 0.8449 | 0.6833 | — |
| Mean precision | 0.8912 | 0.7557 | +0.1355 |
| Mean recall | 0.9787 | 0.9075 | +0.0712 |
| Mean alert rate | 0.2036 | 0.0725 | +0.1311 |
| Mean truth anomalies sampled | 132.8 | 42.6 | +90.2 |

The curiosity policy outperformed round-robin on all reported metrics. The F1 delta of +0.1104 is driven by both improved precision (+0.1355) and improved recall (+0.0712). The curiosity policy sampled substantially more anomalous observations per run (+90.2), meaning it directed probes toward paths that were in fact experiencing incidents.

The curiosity policy's higher alert rate (0.2036 vs. 0.0725) is a trade-off: more alerts are emitted, but they are more often correct. Whether this alert rate is operationally acceptable depends on context not evaluated here. The round-robin policy's lower alert rate reflects its tendency to probe paths regardless of current state, thereby diluting alert density.

The round-robin minimum F1 (0.6833) barely exceeded the viability threshold, while the curiosity minimum F1 (0.8449) remained comfortably above it. This suggests the curiosity policy is more robust to unfavorable random conditions within the simulator, though this observation does not generalize to production without further evidence.

### Local Network Smoke (GB10 Hardware)

The prototype was exercised on a GB10-class machine with the following observed properties:

- **Kernel**: Linux 6.17.0-1014-nvidia, aarch64
- **MemAvailable**: ~122,373,808 kB at smoke start
- **SwapTotal**: 0 kB (consistent with GB10 no-swap constraint)
- **Default route**: <private-ip-redacted> via enP7p1s0, source <private-ip-redacted>
- **ping <loopback-redacted>** (5 counts): 0% loss, avg ~0.017 ms
- **ping <private-ip-redacted>** (5 counts): 0% loss, avg ~0.466 ms

This test confirmed basic probing functionality and hardware telemetry posture. It did not provide labeled real incidents and does not constitute detection-quality evidence. The absence of packet loss on these trivial paths is expected and uninformative regarding anomaly detection capability.

## Limitations

1. **Simulator ground truth, not production labels.** All F1 scores are computed against the simulator's injected incident labels. Production networks exhibit messier fault modes, correlated failures, and label noise that the simulator does not capture. The reported F1 values should not be interpreted as expected production performance.

2. **No real-network incident replay.** The local network smoke verified probing mechanics and hardware compatibility but did not evaluate detection quality against real traffic. The next required gate is replay against collected GB10 lab traces (iperf, ping, traceroute) with known or injected incidents.

3. **Advisory recommendations only.** Topology recommendations are rule-based text output. No route changes are applied automatically, and no operator study has evaluated whether the recommendations are actionable without excessive false positives.

4. **Synthetic incident distribution.** The simulator's incident types (`latency_spike`, `packet_loss`, `route_flap`, `congestion`) and their frequencies may not reflect real-world distributions. Detection quality on incident types not represented in the simulator is unknown.

5. **Limited path count and duration.** The smoke test used only 3 paths and 120 probes. Calibration and comparison runs used more paths and longer durations, but still within synthetic bounds. Scaling behavior to hundreds of paths over days or weeks is untested.

6. **Alert rate trade-off.** The curiosity policy's higher alert rate (0.2036 vs. 0.0725) may impose operator burden in production, even though precision is higher. The acceptable alert rate depends on operational context and has not been calibrated against operator tolerance.

7. **Rule-based anomaly detection.** The detection logic uses fixed z-score thresholds, loss clustering heuristics, and route-hash comparison. These are not learned end-to-end and may not adapt well to distributional shift in production traffic.

8. **Unreviewed AI-generated artifact.** This draft and the underlying prototype were produced by an automated research pipeline. The claim ledger contains no completed claim-audit entries. The results have not undergone independent human review or replication.

## Reproducibility Checklist

- **Prototype source**: `scripts/network_path_curiosity.py` (dependency-free Python)
- **Command documentation**: `artifacts/commands.md`
- **Smoke run log**: `artifacts/logs/smoke_run.log`
- **Smoke metrics**: `artifacts/metrics/smoke_metrics.json`
- **Calibration logs**: `artifacts/logs/calibration_seed11.log` through `calibration_seed15.log`
- **Calibration metrics (per-seed)**: `artifacts/metrics/calibration_seed11_metrics.json` through `calibration_seed15_metrics.json`
- **Calibration aggregate**: `artifacts/metrics/aggregate_metrics.json`
- **Curiosity policy logs**: `artifacts/logs/curiosity_seed21.log` through `curiosity_seed25.log`
- **Curiosity policy metrics (per-seed)**: `artifacts/metrics/curiosity_seed21_metrics.json` through `curiosity_seed25_metrics.json`
- **Round-robin policy logs**: `artifacts/logs/round_robin_seed21.log` through `round_robin_seed25.log`
- **Round-robin policy metrics (per-seed)**: `artifacts/metrics/round_robin_seed21_metrics.json` through `round_robin_seed25_metrics.json`
- **Policy comparison aggregate**: `artifacts/metrics/policy_comparison.json`
- **Probe CSV examples**: `artifacts/metrics/smoke_probes.csv`, `artifacts/metrics/curiosity_seed21_probes.csv`, `artifacts/metrics/round_robin_seed21_probes.csv`
- **Local network smoke log**: `artifacts/logs/local_network_smoke.log`
- **Project decision**: `.omx/project_decision.json`
- **Run notes**: `run_notes.md`
- **Random seeds**: Explicitly recorded (11–15 for calibration; 21–25 for policy comparison)
- **Viability threshold**: F1 ≥ 0.65, stated a priori
- **Claim audit status**: Claim ledger contains no completed claim-audit entries at time of draft generation

## Conclusion

A curiosity-driven probing policy that prioritizes paths by uncertainty, staleness, and risk outperformed a round-robin baseline in synthetic network simulation, achieving a mean F1 of 0.9322 versus 0.8218 (delta +0.1104) and sampling 90.2 more anomalous observations per run. The curiosity policy also achieved higher precision (+0.1355), indicating that its additional probes yielded informative rather than noisy alerts under these simulation conditions.

These results are sufficient to support continuation to a lab-pilot phase in which the harness is replayed against real GB10 network traces with known incidents. They are not sufficient to claim production readiness. The critical gap is the absence of evaluation on real network data with real or semi-real incident labels. The next gate requires F1 ≥ 0.65 on such traces and operator-actionable recommendations without excessive false positives.

The prototype demonstrates that curiosity-driven probe allocation is a plausible strategy for improving network anomaly detection efficiency. Whether it survives contact with real network complexity remains an open empirical question.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Prototype script | `scripts/network_path_curiosity.py` |
| Command documentation | `artifacts/commands.md` |
| Smoke run log | `artifacts/logs/smoke_run.log` |
| Smoke metrics | `artifacts/metrics/smoke_metrics.json` |
| Calibration aggregate metrics | `artifacts/metrics/aggregate_metrics.json` |
| Calibration per-seed metrics | `artifacts/metrics/calibration_seed{11..15}_metrics.json` |
| Calibration logs | `artifacts/logs/calibration_seed{11..15}.log` |
| Policy comparison aggregate | `artifacts/metrics/policy_comparison.json` |
| Curiosity per-seed metrics | `artifacts/metrics/curiosity_seed{21..25}_metrics.json` |
| Curiosity logs | `artifacts/logs/curiosity_seed{21..25}.log` |
| Round-robin per-seed metrics | `artifacts/metrics/round_robin_seed{21..25}_metrics.json` |
| Round-robin logs | `artifacts/logs/round_robin_seed{21..25}.log` |
| Probe CSV examples | `artifacts/metrics/smoke_probes.csv`, `artifacts/metrics/curiosity_seed21_probes.csv`, `artifacts/metrics/round_robin_seed21_probes.csv` |
| Local network smoke log | `artifacts/logs/local_network_smoke.log` |
| Project decision JSON | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260502T195618524134+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T195618524134+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T195618524134+0000/paper_manifest.json` |
