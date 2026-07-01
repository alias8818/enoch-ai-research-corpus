# Stable Thread-ID Anchoring for Postgres-Backed LangGraph Checkpoint Recovery Under Concurrent Process Restarts

> **AI provenance note:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, benchmark outputs, and claim ledgers). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We evaluate whether stable per-run `thread_id` anchors, combined with Postgres-backed checkpointing, preserve deterministic graph state across hard process-restart boundaries in a LangGraph `StateGraph`. A deterministic counter graph with `interrupt_after` semantics forces every graph step to be a process-restart boundary. Across six scenarios scaling from 4 to 256 concurrent logical threads and from 5 to 160 steps per thread, Postgres-anchored runs completed 100% of logical threads with 100% checksum agreement and zero worker errors at the largest scale (40,960 step-process invocations, 32 concurrent workers, approximately 1,231 seconds elapsed). An in-memory restart baseline retained no progress across process boundaries (0% completion). An unanchored shared-thread-id Postgres ablation exhibited checkpoint-lineage contamination (87.5% checksum agreement, with one of eight threads producing a mismatched checksum despite nominal completion). A fresh-process independent audit of persisted terminal state confirmed zero mismatches across all 256 threads. These results support the scoped mechanism claim but remain bounded by significant constraints: single-machine Docker Postgres, a deterministic counter graph without LLM or tool nodes, no mid-node `SIGKILL` injection, no network faults, no multi-host database, and a maximum run duration of approximately 20.5 minutes. The claim ledger for this artifact recorded no structured claims at audit time. This is an engineering validation, not publication-grade evidence for general fault tolerance.

## 1. Introduction

LangGraph provides a checkpointing mechanism that allows a `StateGraph` to persist intermediate state so that execution can resume after interruption. When each graph step is executed by a separate short-lived process—a pattern common in controller-driven dispatch systems—the checkpointer becomes the sole mechanism for preserving progress across process boundaries. The `thread_id` configuration key serves as the logical identity under which checkpoints are stored and retrieved.

A potential failure mode arises when `thread_id` values are unstable across restarts or shared across distinct logical operations. If a restarted worker cannot locate its prior checkpoint, or if multiple logical operations write to the same checkpoint lineage, state may be lost or contaminated. This study asks: does a Postgres-backed `PostgresSaver`, when paired with stable per-run `thread_id` anchors, preserve deterministic graph progress correctly across hard process-restart boundaries under concurrent worker pressure?

We do not attempt to prove general fault tolerance for LangGraph workflows. The claim is explicitly scoped to a deterministic counter graph on a single local Postgres instance, with process exits occurring only at graph-step boundaries (not mid-node). The purpose is to determine whether the anchoring mechanism itself functions correctly under these bounded conditions, and whether the two natural failure modes—in-memory state loss and shared-thread contamination—manifest as expected in control scenarios.

## 2. Method

### 2.1 Graph Design

A deterministic `StateGraph` counter was constructed with the following properties:

- **State schema**: `count` (integer), `target` (integer), `checksum` (integer).
- **Single node**: increments `count` by 1 and updates `checksum` via a deterministic function of a per-thread seed and the current count.
- **Interrupt semantics**: `interrupt_after=["step"]`, causing the graph to yield after each node execution. Each worker process invokes the graph for exactly one step and then exits.
- **Expected terminal state**: `count == target`, `checksum == expected_checksum(seed, target)`, `next == []` (no remaining steps).

This design makes every graph step a process-restart boundary. State preservation depends entirely on the configured checkpointer.

### 2.2 Checkpoint Configurations

Three checkpoint configurations were tested:

1. **Postgres-anchored** (treatment): `PostgresSaver` with a unique `thread_id` of the form `anchored-{i:05d}` per logical thread, where `i` is the thread index. Each logical thread's checkpoint lineage is isolated.

2. **In-memory restart** (baseline control): `MemorySaver` with unique per-thread `thread_id` values. Because `MemorySaver` state is process-local, all progress is lost when the worker process exits. This control tests whether any state survives process boundaries without durable persistence.

3. **Postgres unanchored / shared-thread** (ablation control): `PostgresSaver` with all logical threads sharing a single `thread_id`. This tests whether shared checkpoint identity causes cross-thread state contamination.

### 2.3 Driver and Concurrency Model

The driver script (`run_validation.py`) orchestrates scenarios as follows:

1. For each logical thread, submit a step invocation to a `ProcessPoolExecutor` with a configurable maximum number of concurrent workers.
2. Each invocation launches a fresh Python process that: (a) constructs the graph with the configured checkpointer, (b) invokes the graph for one step under the thread's `thread_id`, (c) exits.
3. The driver repeats step invocations until all logical threads report `count == target` or a maximum iteration limit is reached.
4. After completion, the driver collects per-thread final state and computes checksum agreement.

### 2.4 Scenarios

| Scenario | Threads × Steps | Step Processes | Checkpoint Config | Concurrent Workers |
|---|---:|---:|---|---:|
| `smoke_postgres_anchored` | 4 × 5 | 20 | Postgres, anchored | 4 |
| `memory_restart_baseline` | 8 × 6 | 72 | In-memory, anchored | 8 |
| `postgres_unanchored_collision_ablation` | 8 × 6 | 15 | Postgres, shared thread_id | 8 |
| `medium_postgres_anchored` | 32 × 30 | 960 | Postgres, anchored | 8 |
| `bounded_postgres_anchored` | 64 × 60 | 3,840 | Postgres, anchored | 16 |
| `large_bounded_postgres_anchored` | 256 × 160 | 40,960 | Postgres, anchored | 32 |

The unanchored ablation produced only 15 step processes for 8 threads × 6 steps (expected 48) because shared checkpoint state caused threads to observe each other's progress, short-circuiting the driver's completion logic. This reduced process count is itself a signal of contamination.

### 2.5 Independent Audit

After the largest run, a fresh Python process (not the driver) independently queried the Postgres database, reconstructed the graph with `PostgresSaver`, and verified terminal state for all 256 threads against the expected checksum. This audit decouples verification from the driver's own state-tracking logic.

### 2.6 Environment

- Python 3.13.11
- LangGraph 1.1.10
- `langgraph-checkpoint-postgres`
- Postgres 16-alpine in Docker container `enoch-lg-pg-restart-6072ebb35f`
- DSN: `postgresql://postgres:postgres@<loopback-redacted>:55432/postgres?sslmode=disable`
- Single local machine; no replication or multi-host configuration

## 3. Results

### 3.1 Scenario Outcomes

| Scenario | Step Processes | Completion | Checksum OK | Worker Errors | Elapsed (s) | Throughput (steps/s) |
|---|---:|---:|---:|---:|---:|---:|
| `smoke_postgres_anchored` | 20 | 100% | 100% | 0 | 1.79 | 11.16 |
| `memory_restart_baseline` | 72 | 0% | 0% | 0 | 3.11 | 23.17 |
| `postgres_unanchored_collision_ablation` | 15 | 100% reported¹ | 87.5% | 0 | 0.81 | 18.61 |
| `medium_postgres_anchored` | 960 | 100% | 100% | 0 | 31.80 | 30.18 |
| `bounded_postgres_anchored` | 3,840 | 100% | 100% | 0 | 119.64 | 32.10 |
| `large_bounded_postgres_anchored` | 40,960 | 100% | 100% | 0 | 1,230.70 | 33.28 |

¹ The unanchored ablation reported 100% completion because the driver's per-thread completion check observed `count == target` for most threads, but the shared checkpoint lineage meant these observations were contaminated by other threads' progress. One thread (1/8 = 12.5%) had a checksum mismatch.

### 3.2 In-Memory Baseline

The in-memory restart baseline failed to retain any progress across process boundaries. All final observed counts remained at 1 (the value set during each process's single step), and no logical thread reached its target. This confirms that without durable persistence, process-local checkpointers provide no recovery across hard restarts. The throughput figure of 23.17 steps/s for this scenario reflects the fact that each step is a no-op from a persistence standpoint: the process starts, sets count to 1, and exits, with no meaningful state accumulation.

### 3.3 Shared-Thread Ablation

The unanchored Postgres ablation exhibited checkpoint-lineage contamination. All 8 logical workers wrote to and read from a single `thread_id`'s checkpoint history. The driver reported nominal completion for all threads, but only 7 of 8 (87.5%) had correct checksums. The shared lineage caused at least one thread to observe and report a final state that was not its own deterministic progression. The reduced step-process count (15 vs. expected 48) further indicates that cross-thread state visibility caused premature completion signals, as threads observed counts advanced by other threads sharing the same checkpoint lineage.

### 3.4 Postgres-Anchored Treatment

All four Postgres-anchored scenarios (smoke through large bounded) achieved 100% completion and 100% checksum agreement with zero worker errors. Throughput increased modestly with scale (11.16 to 33.28 steps/s), likely reflecting amortization of Postgres connection setup overhead across more concurrent workers. However, throughput measurements here conflate process-spawning overhead, Python startup time, and database round-trips; they should not be interpreted as pure database throughput benchmarks.

### 3.5 Database State After Largest Run

After the `large_bounded_postgres_anchored` scenario:

- `checkpoints` table: 41,472 rows
- `checkpoint_writes` table: 123,904 rows
- `checkpoint_blobs` table: 256 rows

The ratio of checkpoint rows to logical threads (41,472 / 256 ≈ 162) is consistent with the expected number of checkpoint writes per thread (160 steps plus initial and terminal checkpoints), though the exact accounting depends on LangGraph's internal checkpoint versioning semantics, which were not independently verified.

### 3.6 Independent Fresh-Process Audit

A fresh Python process queried all 256 thread states directly from Postgres:

- Audited threads: 256
- Bad threads (checksum mismatch, wrong count, or non-empty `next`): 0

This confirms that the persisted terminal state is self-consistent and independently verifiable, not an artifact of the driver's in-process tracking.

### 3.7 Claim Ledger Status

The claim ledger for this artifact recorded no structured claims at the time of audit generation (`audit_status: blocked_empty_claims`). The empirical results reported here are drawn directly from the run notes and scenario output files, not from a formally audited claim chain. This gap means the results have not passed structured claim/evidence audit and should be interpreted accordingly.

## 4. Limitations

This validation is subject to the following significant constraints, which limit the generality of the findings:

1. **Single-machine Docker Postgres**: All database operations occurred on one local Postgres 16-alpine container with no replication, failover, or network latency. Results may not transfer to multi-host or cloud-managed Postgres deployments.

2. **Deterministic counter graph only**: The graph contains a single node that increments a counter. There are no LLM calls, tool invocations, branching logic, or non-deterministic operations. Checkpoint payload size and structure are trivially simple compared to production LangGraph workflows.

3. **No real controller traffic**: The driver simulates restart-driven dispatch but does not exercise the actual Enoch controller's hard-cutover path, including its specific dispatch semantics, retry policies, or failure modes.

4. **No mid-node SIGKILL**: Process exits occur only at graph-step boundaries (after `interrupt_after`). The behavior of `PostgresSaver` under a `SIGKILL` delivered during node execution or during a checkpoint write was not tested. This is a critical gap: production restarts may occur at arbitrary points, and partial checkpoint writes could introduce corruption or inconsistency that this validation cannot detect.

5. **No network fault injection**: No network partitions, connection drops, or timeout scenarios were introduced between workers and Postgres.

6. **Short duration**: The largest run lasted approximately 20.5 minutes (1,230.70 seconds). This is far short of a 24-hour soak test and does not exercise long-running connection stability, Postgres vacuuming, or disk-pressure scenarios.

7. **No duplicate-side-effect measurement**: The counter graph has no external side effects. The validation confirms checkpoint consistency but does not measure whether a restarted worker could produce duplicate external actions (e.g., duplicate API calls or database writes) if the graph included side-effecting nodes. This is perhaps the most important open question for production use.

8. **Fixed seed determinism**: The checksum function is deterministic given a fixed seed per thread. Non-deterministic graph nodes would introduce additional failure modes not captured here.

9. **No structured claim audit**: The claim ledger was empty at audit time. The results reported here lack the formal claim-evidence chain that would be expected in a fully audited research artifact.

10. **Mixed control outcome**: The shared-thread ablation showed only 12.5% checksum failure (1 of 8 threads). While this confirms contamination, the relatively low failure rate under this specific ablation may understate the severity of shared-thread risks under different access patterns or higher concurrency.

## 5. Reproducibility Checklist

- **Code availability**: `scripts/lg_step_worker.py` (graph definition and worker), `scripts/run_validation.py` (scenario driver, Docker setup, metrics).
- **Result files**: `results/*_summary.json` (scenario metrics), `results/*_events.jsonl` (per-step process events).
- **Log files**: `logs/run_validation_full.log` (smoke through bounded runs), `logs/run_bounded_large.log` (large bounded run), `logs/fresh_state_audit.log` (independent audit).
- **Environment**: Python 3.13.11, LangGraph 1.1.10, `langgraph-checkpoint-postgres`, Postgres 16-alpine (Docker).
- **Database DSN**: `postgresql://postgres:postgres@<loopback-redacted>:55432/postgres?sslmode=disable` (local Docker container `enoch-lg-pg-restart-6072ebb35f`).
- **Seed**: Fixed seed `6072` used for the large bounded run; per-thread seed computed as `6072 + i` for thread index `i`.
- **Concurrency**: `ProcessPoolExecutor` with `max_workers` as specified per scenario (4, 8, 8, 8, 16, 32).
- **Reproduction commands**: Documented in run notes; exact command lines for each scenario and the independent audit are provided there.
- **Hardware**: Not specified in the run artifacts. Results may be hardware-dependent, particularly elapsed times and throughput figures.

## 6. Conclusion

Under the bounded conditions tested—a deterministic counter graph on a single local Postgres instance with process exits only at graph-step boundaries—stable per-run `thread_id` anchoring combined with `PostgresSaver` preserved deterministic graph state correctly across 40,960 process-restart boundaries under 32-way concurrent worker pressure. All 256 logical threads completed with correct checksums, and an independent fresh-process audit confirmed zero mismatches in persisted terminal state.

The two control scenarios behaved as expected: the in-memory baseline retained no progress across process boundaries (0% completion), and the shared-thread-id ablation exhibited checkpoint-lineage contamination with a 12.5% checksum mismatch rate and a reduced step-process count indicating premature completion signals.

These results support the scoped mechanism claim but do not constitute evidence for broader fault tolerance. The project decision records this as `finalize_negative` for publication gate with `research_outcome: useful_signal`—the mechanism is strongly supported locally, but this is an engineering validation rather than publication-grade evidence. The absence of mid-node kills, network faults, non-deterministic nodes, external side effects, multi-host databases, and long-duration soak testing means that several critical failure modes remain unexamined. The most important open question is whether Postgres-anchored thread identity prevents duplicate external side effects under hard restarts that occur during or after side-effecting node execution—a scenario this validation does not address.

A follow-up study with real controller-integrated dispatch, randomized `SIGKILL` injection at arbitrary graph phases, side-effecting nodes, and a 24-hour minimum duration (or 1,000,000 graph-step restarts) is needed before the mechanism can be considered validated for production use. The follow-up success threshold should require at least 99.99% of anchored logical threads to complete with zero checksum mismatches, zero duplicated committed steps, and zero skipped committed steps.

---

## Referenced Artifacts

| Artifact | Path / Description |
|---|---|
| Run notes | `run_notes.md` — harness description, commands, results table, interpretation |
| Project decision (Enoch) | `.enoch/project_decision.json` — `finalize_negative`, `useful_signal`, hypothesis `supported` |
| Project decision (OMX) | `.omx/project_decision.json` — `finalize_negative`, `useful_signal`, hypothesis `supported` |
| Claim ledger | `papers/.../claim_ledger.json` — `audit_status: blocked_empty_claims`, no structured claims recorded |
| Evidence bundle | `papers/.../evidence_bundle.json` — source, project ID, run ID |
| Paper manifest | `papers/.../paper_manifest.json` — generation metadata |
| Graph worker | `scripts/lg_step_worker.py` — one-step graph worker with deterministic counter |
| Scenario driver | `scripts/run_validation.py` — Docker Postgres setup, scenario execution, metrics |
| Scenario summaries | `results/*_summary.json` — per-scenario metrics |
| Step events | `results/*_events.jsonl` — per-step process event records |
| Full run log | `logs/run_validation_full.log` — smoke through bounded run output |
| Large run log | `logs/run_bounded_large.log` — large bounded run output |
| Audit log | `logs/fresh_state_audit.log` — independent fresh-process state audit |
