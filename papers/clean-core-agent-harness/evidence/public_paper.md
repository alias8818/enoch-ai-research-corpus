# Clean-Core Agent Harness: A Deterministic Evaluation Core for Inspectable Agent Contracts

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, benchmark logs, and evidence bundles). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present the Clean-Core Agent Harness, a lightweight, dependency-free Python prototype that enforces deterministic evaluation of agent behavior by requiring all agent outputs and side effects to pass through inspectable JSON contracts. The harness defines scenarios with expected answers, runs agent adapters repeatedly with fixed seeds, validates result schemas, snapshots per-run workspaces to detect undeclared file writes, and hashes canonical answers to flag nondeterminism across repetitions. In calibration runs of 25 repetitions across 3 scenarios (225 total runs), a deterministic positive-control agent achieved a 75/75 pass rate with zero schema or side-effect violations, while two negative-control agents—a nondeterministic agent and an undeclared-write agent—were correctly flagged in 75/75 and 75/75 runs respectively. The calibration completed in 0.07 seconds wall-clock time with 20,532 kB peak RSS. These results demonstrate that the harness mechanics function as designed at prototype scale, though generalization to real agent CLIs, broader task sets, and OS-level isolation remains unvalidated.

## Introduction

Agent systems increasingly perform autonomous actions with real-world side effects, yet their evaluation often conflates task correctness with behavioral compliance. A system may produce a correct answer while simultaneously performing undeclared filesystem writes, exhibiting nondeterministic behavior across runs, or violating output schemas. Standard evaluation pipelines that check only task accuracy miss these violations.

The central question of this work is: *Can a small "clean-core" harness make agent behavior testable by keeping the evaluation core deterministic and forcing agent outputs and side effects through inspectable contracts?*

The design principle is separation: the evaluation core itself must be deterministic and replayable, while agent behavior is treated as an external, potentially unreliable input that must prove compliance. This inverts the typical framing—rather than trusting the agent and auditing failures, the harness distrusts the agent by default and requires positive evidence of compliance.

We implement and evaluate a prototype that embodies this principle through three mechanisms: (1) schema validation of structured agent outputs, (2) workspace diffing to detect undeclared side effects, and (3) answer-hash comparison across repeated runs to detect nondeterminism. We report results from unit tests, a 5-repetition smoke run, and a 25-repetition calibration run, using built-in positive and negative controls.

## Method

### Design

The Clean-Core Agent Harness is implemented as a single dependency-free Python script (`scripts/clean_core_harness.py`) requiring only the standard library. The harness operates on JSON-compatible scenarios, each specifying:

- A scenario identifier
- An expected answer
- A list of declared file-write paths the agent may perform

Agent adapters are Python callables that receive a scenario and a workspace directory, and must return a result dictionary conforming to the contract:

```json
{
  "answer": "<canonical answer string>",
  "declared_writes": ["<list of file paths the agent intends to write>"],
  "trace": "<arbitrary trace string>"
}
```

The harness evaluates each agent–scenario pair across multiple repetitions with a fixed random seed, performing four checks per run:

1. **Schema validation**: The result must contain `answer`, `declared_writes`, and `trace` keys with appropriate types.
2. **Expected-answer match**: The `answer` field must match the scenario's expected answer.
3. **Workspace diff**: After execution, the harness compares the workspace snapshot to its pre-run state. Any file writes not present in `declared_writes` constitute an undeclared-write violation.
4. **Nondeterminism detection**: Across repetitions, the harness hashes each run's `answer` field. Divergent hashes for the same scenario indicate nondeterministic behavior.

A run passes only if all four checks succeed. The harness records per-run and aggregate results in machine-readable JSON (`harness_report.json`, `harness_summary.json`), along with duration and `/proc/meminfo` `MemAvailable` telemetry.

### Controls

Three built-in agent adapters serve as controls:

- **clean**: Returns deterministic answers matching expectations, declares all writes, and performs no undeclared side effects. This is the positive control.
- **nondeterministic**: Intentionally uses wall-clock time and global randomness to produce varying answers across repetitions. This is a negative control for nondeterminism detection.
- **undeclared_write**: Returns correct, deterministic answers but writes a file without declaring it. This is a negative control for workspace-diff detection.

### Scenarios

Three scenarios are used: `empty`, `small-even`, and `small-odd`. These are intentionally minimal, designed to validate harness mechanics rather than task-general agent quality.

### Execution Protocol

The following commands were executed sequentially:

1. **Unit tests**: `python3 -m unittest discover -s tests -v`
2. **Smoke run**: `python3 scripts/clean_core_harness.py --repetitions 5 --output-dir artifacts/results/smoke`
3. **Environment logging**: Platform, Python version, kernel, memory, and swap status recorded.
4. **Calibration run**: `/usr/bin/time -v python3 scripts/clean_core_harness.py --repetitions 25 --output-dir artifacts/results/calibration`
5. **Compilation check**: `python3 -m py_compile` on both harness and test files.

## Results

### Unit Tests

All 3 unit tests passed in 0.004 seconds. The test suite validates core harness mechanics including schema validation, workspace diffing, and answer-hash comparison.

### Smoke Run (5 Repetitions, 3 Scenarios)

| Agent | Runs | Pass | Violations | Expected Match | Nondeterministic Scenarios | Undeclared Write Runs |
|---|---:|---:|---:|---:|---|---:|
| clean | 15 | 15 | 0 | 15 | [] | 0 |
| nondeterministic | 15 | 0 | 15 | 0 | empty, small-even, small-odd | 0 |
| undeclared_write | 15 | 0 | 15 | 15 | [] | 15 |

The clean agent passed all 15 runs. The nondeterministic agent failed all 15 runs, with nondeterminism detected across all three scenarios. The undeclared-write agent matched expected answers in all 15 runs but was rejected in all 15 due to workspace-diff violations.

### Calibration Run (25 Repetitions, 3 Scenarios)

| Agent | Runs | Pass | Violations | Expected Match | p50 Duration (ms) | Max Duration (ms) |
|---|---:|---:|---:|---:|---:|---:|
| clean | 75 | 75 | 0 | 75 | 0.013 | 0.067 |
| nondeterministic | 75 | 0 | 75 | 0 | 0.011 | 0.028 |
| undeclared_write | 75 | 0 | 75 | 75 | 0.025 | 0.044 |

The clean agent achieved a 100% pass rate (75/75) with zero violations. The nondeterministic agent was flagged in 75/75 runs. The undeclared-write agent produced correct answers in 75/75 runs but was rejected in 75/75 runs for undeclared side effects.

### Resource Usage

The `/usr/bin/time -v` measurement for the full calibration command (225 runs) reported:

- **Elapsed wall-clock time**: 0.07 seconds
- **Maximum RSS**: 20,532 kB
- **Exit status**: 0

### Host Environment

- **Platform**: Linux (aarch64), NVIDIA kernel line present
- **Python**: 3.12.3
- **MemAvailable**: 122,638,796 kB at measurement time
- **SwapTotal/SwapFree**: 0 kB (swap-disabled)
- **earlyoom**: Running with `-m 4 -r 60`

## Limitations

1. **Detection, not prevention**: The harness detects filesystem side effects after execution by comparing workspace snapshots. It is not an OS-level security sandbox and cannot prevent side effects while an untrusted agent is executing. A malicious agent could escape the workspace or perform network operations that the harness does not monitor.

2. **Adapter scope**: Built-in adapters are Python functions invoked in-process. A production harness would require subprocess or JSON-RPC adapters to isolate real agent CLIs. The current prototype does not validate this integration path.

3. **Scenario coverage**: The three scenarios are intentionally minimal and validate harness mechanics, not task-general agent quality. Whether the harness scales to complex, multi-step tasks with ambiguous expected answers is unknown.

4. **Nondeterminism detection scope**: The harness detects answer-level nondeterminism via hash comparison. It does not detect nondeterminism in `trace` content, intermediate reasoning, or side-effect timing if the final answer remains stable.

5. **No real-agent validation**: No external agent CLI was integrated in this run. The controls are synthetic. Whether real agents conform to the JSON contract, and whether the harness catches real rather than injected violations, remains untested.

6. **Resource measurement granularity**: Duration telemetry is at the per-run level using Python's standard timing. No GPU, network, or fine-grained CPU profiling was performed. The workload is lightweight harness validation, not model inference, so these measurements characterize the harness overhead rather than agent computation.

7. **Claim audit status**: The automated claim ledger for this artifact recorded zero structured claims and an audit status of `blocked_empty_claims`. This artifact has not passed a strict claim/evidence audit. The empirical results reported here are drawn directly from run notes and decision JSON, not from a formally audited claim chain.

## Reproducibility Checklist

- [x] **Code available**: `scripts/clean_core_harness.py` and `tests/test_clean_core_harness.py` are present in the project repository.
- [x] **No external dependencies**: The harness uses only the Python 3.12 standard library.
- [x] **Deterministic seed**: The harness accepts and fixes random seeds for repeated runs.
- [x] **Machine-readable outputs**: `harness_report.json` and `harness_summary.json` are produced for every run.
- [x] **Environment logged**: Platform, Python version, kernel, memory, and swap status recorded in `artifacts/logs/environment.log`.
- [x] **Execution logs preserved**: Unit test, smoke, calibration, and compilation logs are in `artifacts/logs/`.
- [x] **Resource measurement**: `/usr/bin/time -v` output captured for the calibration run.
- [x] **Compilation check**: `py_compile` passed for both harness and test files.
- [ ] **OS-level isolation**: Not implemented; the harness runs agents in-process.
- [ ] **Real-agent integration**: Not performed; only synthetic controls were tested.
- [ ] **Broad scenario validation**: Not performed; only 3 minimal scenarios were used.
- [ ] **Structured claim audit**: Claim ledger recorded zero claims; audit status is `blocked_empty_claims`.

## Conclusion

The Clean-Core Agent Harness prototype demonstrates that a small, dependency-free evaluation core can effectively separate deterministic compliance checking from agent behavior. In 225 calibration runs across three synthetic controls, the harness correctly passed all deterministic, compliant runs (75/75) and correctly rejected all nondeterministic runs (75/75) and all runs with undeclared side effects (75/75), even when task answers were correct.

The key finding is that compliance and correctness are orthogonal dimensions: the undeclared-write control produced correct answers in every run yet was rejected in every run. An evaluation that checks only task accuracy would have missed these violations entirely. This supports the design principle that the evaluation core should distrust the agent by default.

However, these results characterize harness mechanics at prototype scale only. The scenario set is minimal, the agents are synthetic, and the harness detects but does not prevent side effects. The confidence in the result is high for harness mechanics and medium for real-agent generalization, as recorded in the project decision. The recommended next step is a real-agent CLI pilot: wrapping one local CLI agent behind the same JSON contract, running 20–50 deterministic tasks, and comparing harness detections against known injected violations. OS-level isolation (e.g., bubblewrap, containers, or user namespaces) should be added only after the JSON contract and evidence format stabilize.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Harness script | `scripts/clean_core_harness.py` |
| Test suite | `tests/test_clean_core_harness.py` |
| Unit test log | `artifacts/logs/unittest.log` |
| Smoke run log | `artifacts/logs/smoke.log` |
| Smoke report | `artifacts/results/smoke/harness_report.json` |
| Smoke summary | `artifacts/results/smoke/harness_summary.json` |
| Calibration stdout | `artifacts/logs/calibration.stdout.log` |
| Calibration stderr | `artifacts/logs/calibration.stderr.log` |
| Calibration report | `artifacts/results/calibration/harness_report.json` |
| Calibration summary | `artifacts/results/calibration/harness_summary.json` |
| Environment log | `artifacts/logs/environment.log` |
| Compilation check log | `artifacts/logs/py_compile.log` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/.../claim_ledger.json` |
| Evidence bundle | `papers/.../evidence_bundle.json` |
| Paper manifest | `papers/.../paper_manifest.json` |
