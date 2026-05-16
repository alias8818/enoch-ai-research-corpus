# Robotic Procedure Verifier: A Lightweight Runtime Checker for Symbolic and Safety Constraints on Robotic Execution Traces

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision records, benchmark logs, and prototype source). The operator who released this artifact claims no personal authorship credit for the writing or the results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

We present a lightweight, dependency-free robotic procedure verifier that checks recorded execution traces against declarative procedure specifications combining symbolic task constraints and quantitative safety thresholds. The verifier validates step ordering, symbolic preconditions and effects, deadline compliance, required confirmations, final obligations, and telemetry bounds for collision margins, contact forces, speed limits, and forbidden zones. In a prototype evaluation on synthetic traces, the verifier correctly accepted a compliant trace (zero violations) and rejected a deliberately non-compliant trace (12 distinct violation codes spanning all implemented check categories). A throughput calibration on 10,000 repeated verifications of a 10-item trace yielded a mean latency of 0.0116 ms per run (p95: 0.0117 ms) and a mean throughput of 864,223 trace items per second on a development-grade aarch64 host. These results establish that combined symbolic-and-safety procedure verification is feasible as a lightweight post-hoc check on normalized trace data, but they do not demonstrate integration with live robotic middleware, real robot deployments, or noisy sensor data. The prototype remains a hook-prototype result requiring integration evidence before deployment claims can be supported.

## Introduction

Robotic task execution is conventionally governed by task-and-motion planners, behavior trees, or state machines that assume environmental and sensor conditions hold at runtime. When these assumptions break silently—due to sensor drift, unexpected obstacles, or unmodeled interactions—plans can fail without explicit notification. This gap motivates runtime verification: independent monitoring that checks whether an executed trace actually satisfies the intended procedure and safety constraints.

Prior work establishes the relevance of this direction from several angles. Verification and falsification alongside task-and-motion planning has been identified as necessary for safe autonomous robot operation by NASA's Space Technology Research Grants program, which funds work developing formal verification in parallel with integrated task and motion planning for robotic autonomy. Runtime assumption monitoring has been proposed to detect when temporal task planning assumptions are violated during execution, enabling mitigation rather than silent failure. Structured requirement languages (e.g., FRET) have been translated into temporal logic and used to generate ROS2 monitoring nodes automatically. Spatial and temporal constraint languages such as SpaTiaL have been demonstrated for object-oriented robotic tasks with combined spatial relations and temporal patterns, evaluated on recorded data, simulations, and real robots. Practical safety monitoring in production robotics stacks—exemplified by the Nav2 Collision Monitor—independently filters velocity commands using quantitative collision, speed, and zone checks with reported frame processing times. Behavior-tree frameworks (BehaviorTree.CPP) are positioned as production-ready robot behavior infrastructure with XML-defined trees, logging, ROS2 integration, and real-time monitoring support.

However, existing approaches tend to address either symbolic/temporal correctness or quantitative safety in isolation, and often require heavyweight formal-methods toolchains or deep middleware integration. This raises the question: can a minimal, dependency-free verifier simultaneously check both symbolic procedure compliance and quantitative safety constraints on execution traces, at sufficient speed for near-real-time use?

We investigate this question by implementing and evaluating a stdlib-only Python prototype that accepts a declarative procedure specification and an execution trace, then reports violations across both symbolic and safety dimensions. We do not claim this prototype constitutes a complete robotic safety system; rather, we assess whether the core verification logic is correct and performant enough to serve as a foundation for integration with robotic middleware.

## Method

### Design

The verifier operates on two inputs: a **procedure specification** (JSON) and an **execution trace** (JSON). The procedure specification declares:

- **Initial symbolic state**: a set of key-value pairs representing the robot's starting conditions.
- **Ordered steps**: a sequence of named steps, each with preconditions, effects, deadline limits, and required confirmations.
- **Resources**: named resources consumed or produced by steps.
- **Final obligations**: conditions that must hold after all steps complete.
- **Safety thresholds**: numeric bounds for obstacle distance, contact force, speed, and forbidden zone definitions.

The execution trace provides:

- **Events**: ordered records of step initiations and completions, with timestamps.
- **Telemetry**: timestamped sensor readings for obstacle distance, contact force, speed, and position.

### Verification Checks

The verifier performs the following checks in sequence:

1. **Unknown step detection**: flags any trace event referencing a step not defined in the procedure.
2. **Step ordering**: verifies that steps occur in the declared order.
3. **Symbolic preconditions**: at each step, checks that all declared preconditions hold in the current symbolic state.
4. **Symbolic effects**: after each step, applies declared effects to the symbolic state.
5. **Deadline compliance**: checks that each step completes within its declared maximum duration.
6. **Confirmation requirements**: verifies that required sensor or operator confirmations are present in the trace.
7. **Final obligations**: after all steps, checks that declared final conditions hold.
8. **Telemetry thresholds**: for each telemetry reading, checks obstacle distance ≥ minimum, contact force ≤ maximum, speed ≤ maximum, and position not within any declared forbidden zone.

Each violation is recorded with a code identifying the check type and contextual details.

### Implementation

The prototype is implemented in pure Python 3.12 using only the standard library. The implementation comprises:

- `src/rpv/verifier.py`: core verification logic and command-line entry point.
- `examples/coffee_procedure.json`: a sample procedure for a robotic coffee-serving task.
- `examples/trace_pass.json`: a compliant execution trace for the coffee procedure.
- `examples/trace_fail.json`: a deliberately non-compliant trace violating all checkable constraints.
- `tests/test_verifier.py`: unit tests for the verifier.

### Evaluation Protocol

We evaluated the prototype through five checks:

1. **Positive smoke test**: run the verifier on the compliant trace; expect `ok=true` with zero violations.
2. **Negative smoke test**: run the verifier on the non-compliant trace; expect `ok=false` with multiple violations covering all check types.
3. **Unit tests**: run `unittest` discovery; expect all tests to pass.
4. **Compile check**: run `compileall` on source and test directories; expect no syntax errors.
5. **Throughput calibration**: run the verifier 10,000 times on the compliant trace and measure per-run latency and throughput.

All evaluations were conducted on a single machine (Linux 6.17.0-1014-nvidia, aarch64, Python 3.12.3, ~122 GB available RAM, no swap). This is a development-grade host, not an embedded robot computer; the throughput figures should be interpreted accordingly.

## Results

### Correctness

The positive smoke test produced `ok=true` with 5 events, 5 telemetry readings, and 0 violations, as expected.

The negative smoke test produced `ok=false` with 12 violations. The detected violation codes were: `order`, `precondition`, `deadline`, `missing_confirmation`, `incomplete`, `final_obligation`, `collision_margin`, `force_limit`, `speed_limit`, and `forbidden_zone`. This confirms that the verifier detects violations across all implemented check categories.

Unit tests passed (2 tests, 0 failures). The compile check completed without errors.

### Throughput

On the throughput calibration (10,000 verifier invocations on a 10-item trace):

| Metric | Value |
|---|---|
| Mean latency per run | 0.0116 ms |
| p95 latency per run | 0.0117 ms |
| Mean throughput | 864,223.2 trace items/s |

The tight clustering of mean and p95 latencies suggests low variance under this synthetic workload. These figures indicate that the core verification logic imposes negligible overhead relative to typical robotic control loop rates (1–1000 Hz), though this claim applies only to the prototype's normalized JSON input on a development host and not to middleware-integrated operation on embedded hardware.

### Negative and Mixed Results

Several aspects of the evaluation warrant explicit acknowledgment as negative or mixed findings:

- **No false-positive characterization**: The evaluation includes no traces that are borderline compliant (e.g., near-threshold telemetry, partially satisfied preconditions). The verifier's false-positive rate on ambiguous inputs is unknown.
- **No partial-failure testing**: The negative trace was constructed to violate all constraints simultaneously. Behavior on traces with isolated or subtle violations (e.g., a single missed confirmation in an otherwise compliant execution) has not been characterized.
- **No real-data validation**: All traces are hand-crafted JSON. The verifier has not been tested against noisy, incomplete, or out-of-order data that real robotic middleware would produce.
- **No adversarial testing**: The evaluation does not include traces designed to exploit edge cases in the verification logic (e.g., empty traces, duplicate events, zero-duration steps, contradictory preconditions and effects).

## Limitations

1. **Synthetic traces only**: The verifier has been evaluated on hand-crafted JSON traces, not on logs from real or simulated robots. Correctness on synthetic inputs does not guarantee correct behavior on noisy, incomplete, or out-of-order real-world data.

2. **No middleware integration**: The prototype consumes normalized JSON. It does not parse ROS2 bag files, BehaviorTree.CPP XML logs, MoveIt trajectory messages, or live ROS2 topics. Integration with these formats requires adapter layers not yet implemented.

3. **No continuous geometry**: Safety checks are limited to scalar telemetry thresholds (e.g., obstacle distance ≥ 0.3 m). The verifier does not perform continuous collision checking against robot or world geometry models. A robot operating near complex geometry could satisfy threshold checks while still being in collision.

4. **No temporal logic syntax**: Procedure constraints are expressed in an ad-hoc JSON schema. Richer specification languages (e.g., FRET-structured requirements, linear temporal logic) are not supported, limiting expressiveness for complex mission requirements.

5. **Single-machine calibration**: Throughput measurements reflect a single aarch64 host with abundant RAM (~122 GB available). Performance on embedded robot computers with constrained resources may differ substantially.

6. **No formal soundness proof**: The verifier is tested against known-positive and known-negative traces, but no formal proof guarantees that it detects all violations or produces no false positives for arbitrary inputs.

7. **Deliberately constructed negative trace**: The negative trace was designed to violate all constraints simultaneously. This confirms that each check type can fire, but does not characterize the verifier's behavior on subtle or borderline violations.

8. **No deployment evidence**: The project decision record rates confidence as "medium_high" and identifies integration with real or simulated robot scenarios as a required next step. The current result is a hook-prototype, not a production-validated system.

9. **Minimal unit test coverage**: Only 2 unit tests were executed. This is insufficient to exercise the full space of verification logic paths, edge cases, and interaction effects between check types.

## Reproducibility Checklist

- [x] **Source code available**: `src/rpv/verifier.py`, `tests/test_verifier.py`
- [x] **Example inputs available**: `examples/coffee_procedure.json`, `examples/trace_pass.json`, `examples/trace_fail.json`
- [x] **Run logs available**: `logs/smoke_test.log`, `logs/compile.log`
- [x] **Decision record available**: `.omx/project_decision.json`
- [x] **Run notes available**: `run_notes.md`
- [x] **Environment specified**: Linux 6.17.0-1014-nvidia aarch64, Python 3.12.3, 127 GB total RAM, 122 GB available, no swap
- [x] **Exact commands documented**: All five evaluation commands are recorded in run notes and reproducible from the project directory
- [x] **Randomness**: No random seeds required; the verifier is deterministic
- [x] **Dependencies**: Python 3.12 standard library only; no external packages
- [ ] **Real-robot or simulation validation**: Not yet performed
- [ ] **Formal soundness argument**: Not provided
- [ ] **False-positive rate characterization**: Not performed
- [ ] **Embedded-hardware performance**: Not measured

## Conclusion

We have demonstrated that a lightweight, stdlib-only robotic procedure verifier can simultaneously check symbolic procedure compliance (step ordering, preconditions, effects, deadlines, confirmations, final obligations) and quantitative safety constraints (collision margins, force limits, speed limits, forbidden zones) on execution traces. On synthetic test inputs, the verifier correctly accepts compliant traces and rejects non-compliant traces across all implemented check categories, with per-run latency of approximately 0.012 ms on a development host.

These results support the feasibility of the approach as a bounded offline verification layer for normalized trace data, but they do not constitute evidence of deployment readiness. The critical gap is integration: the verifier currently operates on normalized JSON rather than native robotic middleware formats, and has not been validated against real or simulated robot execution logs. The evaluation also lacks characterization of false-positive rates, borderline inputs, adversarial cases, and embedded-hardware performance.

Closing the integration gap requires adapter implementations for ROS2 bags, BehaviorTree.CPP logs, and MoveIt telemetry, followed by evaluation on at least one domain-specific robotic procedure with realistic safety requirements. The prototype's minimal dependency footprint and high throughput on synthetic data suggest that integration is unlikely to be blocked by verification performance, but this remains unconfirmed under actual middleware data rates and on embedded hardware.

---

## Referenced Artifacts

| Artifact | Path / Identifier |
|---|---|
| Core verifier | `src/rpv/verifier.py` |
| Unit tests | `tests/test_verifier.py` |
| Procedure specification | `examples/coffee_procedure.json` |
| Compliant trace | `examples/trace_pass.json` |
| Non-compliant trace | `examples/trace_fail.json` |
| Run notes | `run_notes.md` |
| Smoke test log | `logs/smoke_test.log` |
| Compile check log | `logs/compile.log` |
| Project decision record | `.omx/project_decision.json` |
| Research metrics | `.omx/research_metrics.json` |
| Project README | `README.md` |
| Claim ledger | `papers/source-record-redacted-20260502T170918662389+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T170918662389+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T170918662389+0000/paper_manifest.json` |
| Project identifier | `source-record-redacted` |
| Run identifier | `source-record-redacted-20260502T170918662389+0000` |
