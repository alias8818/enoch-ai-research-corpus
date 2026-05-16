# Stalled Agent Rescuer: Local Classification of Agent Health from Durable OMX Artifacts

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, evidence bundles, claim ledgers, and benchmark logs). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present a controller-side classifier, the Stalled Agent Rescuer, that makes local decisions from durable OMX/Codex artifacts about whether an agent is healthy, degraded, or hard-stalled, and recommends a safe rescue action. The prototype fuses independent liveness signals—heartbeat event streams, session state, process ID (PID) liveness, and metrics staleness—to produce a classification with an associated confidence level. In a live project assessment, the classifier identified a degraded-not-dead state: 1,742 consecutive heartbeat errors with `leader_nudge_failed` semantics were observed, yet the recorded session PID remained alive and recent heartbeat events continued to arrive. A critical false-positive guardrail was identified: relying solely on `metrics.json:last_activity` staleness would have triggered a hard restart, contradicting evidence from heartbeat recency and PID liveness. The prototype parses 1,742 heartbeat events in 0.0094 seconds (~185,871 heartbeats/second) with a maximum RSS of 19,212 KB, indicating throughput sufficient for controller integration. All recommended rescue actions in this artifact are side-effect-free dry runs; actual remediation requires controller integration outside the research prototype. Confidence in the classification approach is medium, limited by the availability of only one labeled live trace and synthetic unit tests. The claim ledger for this artifact recorded no structured claims at audit time, which constrains the strength of conclusions that can be drawn.

## Introduction

Autonomous agents operating in long-running sessions can enter states where progress stalls—either because of infrastructure degradation, channel failures, or true process death. A controller supervising such agents needs a reliable, local mechanism to distinguish between a degraded agent that may recover with targeted repair and a hard-stalled agent requiring a full restart. Incorrect classification in either direction carries cost: a premature hard restart wastes in-progress work, while failing to restart a dead agent wastes time and compute budget.

The central research question is: can a controller-side classifier make a reliable local decision from durable OMX/Codex artifacts about whether an agent is healthy, degraded, or hard-stalled, and recommend a safe rescue action?

This work makes the following contributions:

1. A stdlib-only classifier that reads `.omx/state/session.json`, `.omx/metrics.json`, `.omx/state/heartbeats/*.ndjson`, and `.omx/logs/*.jsonl` to produce a status classification with confidence and dry-run recommended actions.
2. Identification of a false-positive guardrail: metrics staleness alone is insufficient to declare a hard stall when contradicted by recent heartbeat evidence or live PID confirmation.
3. Empirical throughput and memory characterization of the heartbeat parser on a live project trace.

These contributions are grounded in prototype-level evidence from a single live project trace and synthetic unit tests. Generalization to diverse failure modes has not been established.

## Method

### Architecture

The Stalled Agent Rescuer (`src/stalled_agent_rescuer.py`) is implemented as a stdlib-only Python CLI/library. It reads four categories of durable OMX artifacts:

- **Session state** (`.omx/state/session.json`): provides the recorded session PID and session metadata.
- **Metrics** (`.omx/metrics.json`): provides `last_activity` timestamp and token usage counters.
- **Heartbeat events** (`.omx/state/heartbeats/*.ndjson`): provides timestamped liveness and error events.
- **Agent logs** (`.omx/logs/*.jsonl`): provides supplementary error and activity evidence.

The classifier emits a JSON assessment containing `status` (one of `healthy`, `degraded`, `hard_stalled`), `confidence` (one of `low`, `medium`, `high`), `signals` (the fused evidence), `metrics` (quantitative summaries), and `recommended_actions` (dry-run only).

### Signal Fusion Logic

The classifier independently evaluates three liveness signals:

1. **Metrics staleness**: If `metrics.json:last_activity` exceeds a configurable threshold (default 180 seconds), this signal alone would suggest a stall.
2. **Heartbeat recency**: If recent heartbeat events exist (including error events), the agent's process is still emitting events, contradicting a hard-stall classification.
3. **PID liveness**: If the session PID recorded in `session.json` is alive (checked via OS signal), the agent process has not terminated.

The fusion rule is conservative: a hard-stall classification requires either a dead PID or absent/stale heartbeat evidence. Metrics staleness alone, when contradicted by heartbeat recency or PID liveness, is downgraded to a warning contributing to a `degraded` classification rather than triggering a hard restart.

### Rescue Action Hierarchy

Recommended actions follow a graduated hierarchy:

1. **Repair or bypass nudge channel**: When heartbeat errors indicate a specific channel failure (e.g., `leader_nudge_failed`) but the PID is alive.
2. **Hard cutover restart**: Reserved for cases where the PID is dead or heartbeat evidence is absent/stale.

All actions in this research artifact are side-effect-free dry runs. The prototype does not execute remediation.

### Calibration

A calibration tool (`tools_calibrate.py`) measures parser throughput and memory usage by reading all heartbeat files and reporting elapsed time and maximum RSS via the Python `resource` module.

## Results

### Unit Tests

Five unit tests passed in 0.01 seconds. These tests exercise the classifier on synthetic inputs covering healthy, degraded, and hard-stalled scenarios, as well as edge cases in signal fusion. These are toy-scale tests and do not constitute comprehensive validation of the fusion logic under diverse real-world conditions.

### Live Project Assessment

Running the rescuer against the live project directory produced:

| Field | Value |
|---|---|
| Status | `degraded` |
| Confidence | `medium` |
| Heartbeat events parsed | 1,742 |
| Nudge error count | 1,742 |
| Latest nudge error reason | `leader_nudge_failed` |
| Latest nudge error run_count | 871 |
| Session PID alive | Yes (PID 2145829) |

All 1,742 heartbeat events were error events matching `leader_nudge_failed` semantics. Despite this high error count, the session PID was alive and heartbeat events continued to be emitted, indicating the agent process was running but experiencing a degraded nudge channel. This is a single-observation result; whether this pattern generalizes to other sessions or failure modes is unknown.

### False-Positive Guardrail

During the live assessment, `metrics.json:last_activity` exceeded the 180-second stale threshold. A classifier relying solely on this signal would have classified the agent as hard-stalled and recommended a hard restart. However, recent heartbeat events and a live PID contradicted this classification. The fused assessment correctly downgraded the status to `degraded` with a recommended action of repairing or bypassing the nudge channel rather than restarting.

This finding is significant: in a production controller, a metrics-only stall detector would have caused an unnecessary hard restart of a live agent with an active session. However, this observation is drawn from a single trace and has not been replicated across multiple sessions or failure modes.

### Parser Throughput and Memory

| Metric | Value |
|---|---|
| Heartbeat events | 1,742 |
| Parse elapsed time | 0.009372 s |
| Throughput | ~185,871 heartbeats/s |
| Max RSS | 19,212 KB |

The parser throughput is approximately two orders of magnitude faster than any realistic controller polling interval, indicating no throughput bottleneck for controller integration at this scale. These figures represent a single calibration run on one trace; performance under substantially larger heartbeat logs has not been measured.

### System Memory Posture

System telemetry at observation time:

| Metric | Value |
|---|---|
| MemAvailable | ~122 GB |
| SwapTotal | 0 kB (swap disabled) |
| earlyoom | Installed (v1.7) |

With swap disabled and earlyoom present, the system is configured to kill processes under memory pressure rather than swapping. This is relevant context: a hard-stalled agent consuming memory without releasing it could be killed by earlyoom before the rescuer classifies it, making PID liveness checks a time-sensitive signal.

## Limitations

1. **Single live trace**: The classifier has been validated against one live project trace plus synthetic unit tests. Confidence thresholds and fusion rules may not generalize to other failure modes (e.g., infinite loops without heartbeat errors, resource exhaustion without nudge failures, or partial process death such as zombie PIDs).

2. **Side-effect-free prototype**: All recommended rescue actions are dry runs. The actual efficacy of nudge-channel repair or hard restart has not been validated in an integrated controller. The prototype cannot execute remediation.

3. **Heartbeat log growth**: The current implementation reads all heartbeat files in full on each invocation. With 1,742 events already present in a single session, unbounded log growth will eventually degrade throughput and memory. Production integration should stream, tail, or maintain a compact index rather than performing full file reads.

4. **Confidence is medium**: The `medium` confidence rating reflects the limited validation surface. More labeled traces covering diverse stall modes would be required to calibrate confidence thresholds rigorously.

5. **No temporal decay modeling**: The classifier treats heartbeat recency as a binary signal (recent vs. stale) rather than applying a continuous decay model. The boundary between "degraded" and "hard-stalled" may shift under different workload patterns.

6. **PID liveness is a point-in-time check**: A PID alive at check time may die immediately after. The classifier does not currently track PID liveness over multiple assessment windows.

7. **Empty claim ledger**: The structured claim ledger for this artifact recorded no claims at audit time (`audit_status: blocked_empty_claims`). This means no claim has passed a structured evidence-audit gate. The findings reported here are drawn directly from run notes and project decision artifacts and have not been independently verified through a formal claim-evidence pipeline.

8. **Missing readiness audit signal**: The paper review process flagged a missing `readiness_audit` signal, and the review checklist shows 9 pending items with 0 passed. This draft should be treated as preliminary and unreviewed.

9. **Python version and OS not recorded**: The execution environment details (Python version, OS, kernel version) were not captured in the artifacts, which limits reproducibility of the calibration and assessment results.

## Reproducibility Checklist

- [x] Prototype source: `src/stalled_agent_rescuer.py` (stdlib-only Python)
- [x] Test source: `tests/test_stalled_agent_rescuer.py`
- [x] Calibration tool: `tools_calibrate.py`
- [x] Unit test results: 5 passed in 0.01s (see `.omx/logs/smoke-pytest-final.log`)
- [x] Live assessment output: `.omx/rescuer_assessment.json`
- [x] Live assessment log: `.omx/logs/real-assessment-final2.log`
- [x] Calibration log: `.omx/logs/parser-calibration-final2.log`
- [x] System telemetry log: `.omx/logs/system-telemetry.log`
- [x] Run notes: `run_notes.md`
- [x] Project decision: `.omx/project_decision.json`
- [x] Metrics snapshot: `.omx/metrics.json`
- [ ] Python version and OS details: not recorded in artifacts
- [x] Random seeds: not applicable (no stochastic components)
- [x] Hardware: system had ~122 GB available RAM, swap disabled, earlyoom v1.7
- [ ] Claim ledger audit: blocked (no structured claims extracted)
- [ ] Readiness audit: missing

## Conclusion

A local, side-effect-free classifier can distinguish between degraded and hard-stalled agent states by fusing independent liveness signals from durable OMX artifacts. The key finding is that metrics staleness alone is an unreliable stall indicator: in the observed live trace, `metrics.json:last_activity` exceeded the stale threshold while the agent PID was alive and heartbeat events continued, which would have caused a false-positive hard restart in a metrics-only detector. The correct classification—degraded with a nudge-channel failure—was achieved only by fusing heartbeat recency and PID liveness signals.

The prototype demonstrates sufficient throughput (~185,871 heartbeats/s, 19 MB RSS) for controller integration at the observed scale. However, confidence remains medium due to validation against only one live trace and synthetic tests, and the claim ledger for this artifact is empty, meaning no finding has passed a structured evidence audit. The recommended integration path is to use the classifier as a pre-cutover gate in the LangGraph controller, wire the nudge-channel repair action to a concrete controller operation, and gate hard restarts on dead PID or absent/stale heartbeat evidence rather than metrics staleness alone. Substantial additional validation across diverse failure modes and multiple labeled traces is needed before production deployment.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Prototype | `src/stalled_agent_rescuer.py` |
| Tests | `tests/test_stalled_agent_rescuer.py` |
| Calibration tool | `tools_calibrate.py` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Assessment output | `.omx/rescuer_assessment.json` |
| Metrics snapshot | `.omx/metrics.json` |
| Unit test log | `.omx/logs/smoke-pytest-final.log` |
| Assessment log | `.omx/logs/real-assessment-final2.log` |
| Calibration log | `.omx/logs/parser-calibration-final2.log` |
| System telemetry | `.omx/logs/system-telemetry.log` |
| Claim ledger | `papers/source-record-redacted-20260430T003518302298+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T003518302298+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T003518302298+0000/paper_manifest.json` |
