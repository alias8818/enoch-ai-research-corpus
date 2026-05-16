# Autonomous Project Manager Kernel: A Deterministic Control-Plane Prototype for Auditable Agentic Project Execution

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metrics, and log summaries). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and evaluate its claims against the referenced evidence bundles accordingly.

---

## Abstract

We present a minimal, deterministic project-manager kernel designed to provide the control-plane primitives required for auditable agentic project execution. The kernel operates on task directed acyclic graphs (DAGs) and implements six core primitives: DAG validation with cycle rejection, dependency-satisfied readiness marking, skill/priority/capacity-based work assignment, structured event logging, transient-failure retry with permanent-failure blocking, and deterministic snapshot metrics. The prototype is implemented in pure Python standard library with no external dependencies. In unit testing, all five regression tests pass. In a synthetic smoke scenario, five sample tasks complete in five scheduler ticks. In a synthetic scaling evaluation across 10, 100, and 1,000 tasks, the kernel processes all tasks to completion with throughput ranging from approximately 87,769 tasks/s (10 tasks) to 2,952 tasks/s (1,000 tasks), and peak RSS growing modestly from 13,440 KB to 14,720 KB. These results constitute a positive prototype demonstration but do not establish real-world utility; no integration with language models, persistent storage, distributed execution, or human approval workflows was tested. The claim ledger for this artifact is currently empty and has not passed structured claim/evidence audit.

---

## Introduction

Autonomous agents that decompose and execute project work require a control-plane substrate that enforces dependency ordering, handles failures, and maintains an auditable event log. Without such a substrate, agent orchestration systems risk silent dependency violations, uncontrolled retry loops, and irreproducible execution histories.

This work investigates whether a small, deterministic kernel can provide the minimum control-plane primitives needed for auditable agentic project execution. We constrain the problem to six primitives:

1. **DAG validation** — accept well-formed task graphs and reject those containing dependency cycles.
2. **Readiness marking** — identify tasks whose dependencies are all satisfied.
3. **Skill-aware assignment** — dispatch ready tasks to agents matching required skills, respecting priority and capacity.
4. **Event recording** — log dispatch, completion, retry, and failure events.
5. **Retry and blocking** — retry transient failures up to a configured limit; on permanent failure, block all downstream dependents.
6. **Deterministic snapshots** — produce repeatable state snapshots and aggregate metrics.

The design goal is not an optimized scheduler but a correct, inspectable, and replayable core. We deliberately avoid external service dependencies, persistent databases, and non-deterministic scheduling heuristics in this prototype stage.

---

## Method

### Design

The kernel (`src/pm_kernel.py`) is implemented as a single-module, stdlib-only Python component. It maintains an in-memory task graph and agent pool. Each scheduling tick performs:

1. **Readiness scan**: For each task not yet in a terminal state, check whether all declared dependencies have reached a `done` state. If so, and no dependency is in a `failed` (permanent) state, mark the task `ready`.
2. **Assignment**: For each `ready` task, select the highest-priority task first, then match it to an available agent whose skill set is a superset of the task's required skills and whose concurrent capacity is not exhausted. On match, emit a `dispatch` event and transition the task to `running`.
3. **Completion handling**: When an agent reports a task result, the kernel either transitions the task to `done` (emitting a `done` event) or, on failure, increments the retry counter. If the retry counter is below the configured limit, the task returns to `ready` (emitting a `retry` event); otherwise, it transitions to `failed` (emitting a `failure` event), and all transitive dependents are marked `blocked`.
4. **Snapshot**: At any point, the kernel can produce a deterministic snapshot of all task states, event log, and aggregate metrics.

### Testing

Five unit tests (`tests/test_pm_kernel.py`) cover:

- **Success path**: A linear DAG completes end-to-end.
- **Retry path**: A task fails transiently and succeeds on retry.
- **Failure blocking**: A permanent failure propagates blocking to downstream tasks.
- **Missing skills**: A task requiring skills no agent possesses is never dispatched.
- **Cycle rejection**: A cyclic dependency graph is rejected at submission time.

A smoke scenario (`scripts/run_smoke.py`) exercises a five-task DAG with mixed dependencies and verifies all tasks reach `done`.

A synthetic scaling evaluation (`scripts/run_eval.py`) generates random DAGs of 10, 100, and 1,000 tasks with bounded fan-in/fan-out, assigns them to a pool of synthetic agents, and measures elapsed wall-clock time, scheduler ticks, throughput, and peak RSS.

### Environment

All experiments ran on a single machine:

- **OS**: Linux 6.17.0-1014-nvidia (aarch64), Ubuntu
- **Python**: 3.12.3
- **RAM available**: ~122.7 GB (no swap configured)

---

## Results

### Unit Tests

All five unit tests pass:

| Test | Result |
|------|--------|
| Success path | Pass |
| Retry path | Pass |
| Failure blocking | Pass |
| Missing skills | Pass |
| Cycle rejection | Pass |

Source: `logs/unittest.log`.

### Smoke Scenario

The five-task smoke scenario completed in 5 scheduler ticks. Final status counts: `done`: 5. No tasks entered `failed` or `blocked` states.

Source: `results/smoke_metrics.json`, `logs/smoke.log`.

### Synthetic Scaling Evaluation

| Tasks | Ticks | Elapsed (s) | Throughput (tasks/s) | Events | Peak RSS (KB) | All Done? |
|-------|-------|-------------|----------------------|--------|---------------|-----------|
| 10    | 3     | 0.000114    | 87,768.58            | 20     | 13,440        | Yes       |
| 100   | 13    | 0.003681    | 27,167.67            | 200    | 13,600        | Yes       |
| 1,000 | 102   | 0.338773    | 2,951.83             | 2,000  | 14,720        | Yes       |

Key observations:

- **Throughput degrades super-linearly** with task count. The drop from ~87K to ~2.9K tasks/s between 10 and 1,000 tasks suggests the per-tick readiness scan has complexity that grows with graph size. This is consistent with the unoptimized, linear-scan design and is not unexpected for a prototype.
- **Memory growth is modest**: peak RSS increases by only ~1,280 KB (approximately 9.5%) from 10 to 1,000 tasks, indicating the in-memory representation is compact.
- **All tasks completed** in every configuration, with no failures or blocked tasks in the synthetic DAGs (which contained no injected faults).

Source: `results/eval_metrics.json`, `logs/eval.log`.

### Compilation Check

`python3 -m compileall -q src scripts` completed with no output (no syntax errors).

Source: `logs/compileall.log`.

---

## Limitations

This prototype has significant limitations that prevent drawing conclusions about real-world utility:

1. **No LLM integration**: The kernel was tested with synthetic agents that always succeed (in scaling) or follow scripted failure patterns (in unit tests). No language-model-based decomposition or execution was evaluated. The kernel's behavior under realistic agent latency, partial outputs, or hallucinated dependencies is unknown.

2. **No persistence**: All state is in-memory. A process crash loses the entire execution history. Production use requires durable storage and resumable execution identifiers.

3. **No distributed execution**: The kernel runs in a single process. Multi-process or multi-node agent pools, network partitions, and partial failure modes are not addressed.

4. **No human approval or permission model**: The kernel has no concept of approval gates, permission boundaries, or human-in-the-loop review. These are essential for safe autonomous operation in real projects.

5. **No UI or observability interface**: Inspection is limited to JSON snapshots and log files. No dashboard, tracing, or real-time monitoring was implemented.

6. **Scheduling is not optimized**: The scheduler uses a simple priority-then-skill matching rule. It does not optimize critical-path duration, cost, or resource utilization. Whether more sophisticated policies would meaningfully improve outcomes is an open question.

7. **Synthetic evaluation only**: The scaling benchmarks use randomly generated DAGs with no correlation to real project structures. Throughput and memory figures may not generalize to production workloads.

8. **Single-machine, single-run results**: Each scaling configuration was executed once. No statistical confidence intervals or variance estimates are available. Results may be sensitive to system load, Python interpreter warm-up, and other environmental factors.

9. **Empty claim ledger**: The structured claim ledger for this artifact contains zero claims and has audit status `blocked_empty_claims`. The findings reported here have not passed formal claim/evidence audit against public evidence files.

---

## Reproducibility Checklist

| Item | Status |
|------|--------|
| Source code available locally | Yes: `src/pm_kernel.py`, `scripts/run_smoke.py`, `scripts/run_eval.py` |
| Test suite available locally | Yes: `tests/test_pm_kernel.py` |
| Exact commands recorded | Yes: in `run_notes.md` |
| Environment details recorded | Yes: `logs/environment.log` |
| Raw metrics files available | Yes: `results/smoke_metrics.json`, `results/eval_metrics.json` |
| Execution logs available | Yes: `logs/unittest.log`, `logs/smoke.log`, `logs/eval.log`, `logs/compileall.log` |
| Deterministic execution guaranteed | Partial: kernel logic is deterministic given fixed input; Python hash randomization and OS scheduling may introduce minor variance in wall-clock times |
| Multiple runs / variance reported | No: each configuration was run once |
| External dependencies required | No: stdlib-only Python 3.12 |
| Claim/evidence audit passed | No: claim ledger is empty (`blocked_empty_claims`) |

---

## Conclusion

We implemented and evaluated a minimal deterministic project-manager kernel that provides six core control-plane primitives for auditable agentic project execution. In prototype testing, the kernel correctly validates DAGs, dispatches skill-matched work, retries transient failures, blocks downstream work on permanent failures, and produces deterministic event logs and metrics. Synthetic scaling tests demonstrate that 1,000 tasks complete in 102 ticks with modest memory usage (14,720 KB peak RSS), though throughput degrades from ~87K to ~2.9K tasks/s as graph size increases, reflecting the unoptimized linear-scan design.

These results constitute a positive prototype demonstration: the kernel semantics are viable as a local deterministic control-plane core. However, the gap between this prototype and a production-ready system remains large. No evidence is available regarding integration with language models, persistent execution, distributed agents, human approval workflows, or real project traces. The claim ledger for this artifact remains empty and has not passed structured audit. Scientific closure on real-world value requires comparison against actual agent-project event traces or user studies, which were not available in this project.

The kernel's value, at this stage, is primarily as a specification-by-implementation of the minimum scheduling and failure-handling semantics that any agentic project control plane must provide. Whether these semantics, when composed with real agents and real projects, yield measurable improvements in project completion rates, failure recovery, or auditability remains an open empirical question.

---

## Referenced Artifacts

| Artifact | Description |
|----------|-------------|
| `src/pm_kernel.py` | Kernel implementation (stdlib-only) |
| `tests/test_pm_kernel.py` | Unit test suite (5 tests) |
| `scripts/run_smoke.py` | Smoke scenario runner |
| `scripts/run_eval.py` | Synthetic scaling evaluation runner |
| `README.md` | Run instructions |
| `run_notes.md` | Experimenter run notes and command log |
| `.omx/project_decision.json` | Decision ledger with evidence summaries |
| `.omx/metrics.json` | Session token and activity metrics |
| `results/smoke_metrics.json` | Smoke scenario output metrics |
| `results/eval_metrics.json` | Scaling evaluation output metrics |
| `logs/unittest.log` | Unit test execution log |
| `logs/smoke.log` | Smoke scenario execution log |
| `logs/eval.log` | Scaling evaluation execution log |
| `logs/compileall.log` | Compilation check log |
| `logs/environment.log` | Environment details (OS, Python version, memory) |
| `papers/.../claim_ledger.json` | Claim ledger (empty; audit status: `blocked_empty_claims`) |
| `papers/.../evidence_bundle.json` | Evidence bundle (source: `langgraph_control_plane_mvp`) |
| `papers/.../paper_manifest.json` | Paper generation manifest |
