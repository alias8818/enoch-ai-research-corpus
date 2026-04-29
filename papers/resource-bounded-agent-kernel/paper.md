# Resource-Bounded Agent Kernel: Enforcing Multi-Dimensional Resource Quotas in Autonomous Agent Subprocesses

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

Autonomous software agents that execute arbitrary code or invoke external tools risk resource runaways—unbounded CPU consumption, excessive output, unauthorized network access, or uncontrolled file system modification. We present a Resource-Bounded Agent Kernel architecture that mediates agent actions through typed action dispatch with pre-execution quota checks and, in a subprocess variant, OS-level enforcement via `setrlimit`, wall-clock timeouts, live stdout byte accounting, and `strace`-based syscall monitoring. In a two-stage experimental evaluation—first an in-process toy-model smoke test (120 runs) and then a subprocess-backed replay harness (36 runs)—the bounded kernel preserved normal-task success at parity with an unbounded baseline (1.0 success rate in both conditions) while preventing all tested runaway classes (prevention rate 1.0 vs. 0.0 for baseline). Mean wall-clock time decreased under the bounded kernel for runaway workloads (in-process: 0.0008 s vs. 0.0336 s; subprocess: 0.3884 s vs. 0.5205 s). These results are limited to synthetic, deterministic workloads on a single Linux host; the `strace`-based network and file monitoring kills after syscall observation rather than preventing entry, and no real LLM token accounting or production agent framework was exercised. The current project artifacts support the finding that typed kernel-layer mediation with OS-level enforcement can prevent resource runaways while preserving in-quota task success in the tested setting.

---

## 1. Introduction

Autonomous agents—systems that interpret instructions, select tools, and execute actions with limited human oversight—introduce a fundamental safety problem: a mis-specified or misbehaving agent can consume unbounded resources. A single runaway agent loop may exhaust CPU time, emit megabytes of spurious output, touch thousands of files, or open network connections to arbitrary endpoints. Transcript-based monitoring, which records actions after execution, provides observability but not enforcement: by the time a runaway is logged, the damage is already done.

This work investigates whether a *resource-bounded agent kernel*—a control-plane layer that mediates every agent action through typed dispatch with pre-execution quota checks and OS-level process controls—can prevent resource runaways while preserving the ability of in-quota tasks to complete successfully. We test this in two stages of increasing fidelity:

1. An **in-process toy model** where typed actions (`emit_tokens`, `burn_cpu`, `touch_file`, `network_call`, `sleep`) are dispatched through a kernel that checks quotas before execution.
2. A **subprocess-backed replay harness** where agent workloads run as child processes under `setrlimit(RLIMIT_CPU)`, parent-enforced wall-clock timeouts, live stdout byte accounting, and `strace -ff -e trace=file,network` monitoring.

We compare both against unbounded baselines that record but do not enforce. The central question is whether enforcement preserves normal-task success while preventing runaway completion.

---

## 2. Method

### 2.1 In-Process Toy-Model Harness

The first harness (`experiments/resource_kernel.py`) implements two modes:

- **TranscriptWrapper (baseline):** Accepts and logs all typed actions after execution. No quota checks are performed before operations proceed. Runaway actions complete fully.
- **ResourceKernel (bounded):** A typed action dispatcher that maintains quota counters for CPU work units, token budget, wall-clock time, network calls, and file touches. Each action is checked against its quota before execution; actions exceeding quotas are denied with a hard rejection.

Five typed actions are defined: `emit_tokens` (increments a token counter), `burn_cpu` (performs a CPU-bound loop), `touch_file` (creates a file artifact), `network_call` (simulates a network request), and `sleep` (wall-clock delay). Workload variants cover normal in-quota tasks plus five runaway classes: token overflow, CPU burn, file-touch excess, unauthorized network calls, and wall-clock overrun.

The harness was invoked with `--repeats 10`, producing 120 measured runs (10 repeats × 6 workload variants × 2 modes).

### 2.2 Subprocess-Backed Replay Harness

The second harness (`experiments/subprocess_kernel.py`) extends enforcement to real OS processes:

- **subprocess_baseline:** Launches a long-task child script and records results after completion. No resource limits are imposed.
- **subprocess_resource_kernel:** Launches the same child under:
  - `setrlimit(RLIMIT_CPU)` for CPU-second caps.
  - Parent-enforced wall-clock timeout (process group killed on expiry).
  - Live stdout byte accounting as a proxy for token/transcript budget.
  - `strace -ff -e trace=file,network` monitoring for file and network policy violations. The parent terminates the process group when a quota is exceeded.

Workload variants replay a Codex/OMX-style long-task shape across normal useful work plus token/stdout, file-touch, network, wall-clock, and CPU runaway behaviors.

The harness was invoked with `--repeats 3`, producing 36 subprocess replay runs (3 repeats × 6 workload variants × 2 modes).

### 2.3 Metrics

The primary metrics are:

- **Normal task success rate:** Fraction of in-quota workloads that complete successfully.
- **Runaway prevention rate:** Fraction of runaway workloads that are stopped before completion.
- **Runaway completion rate:** Fraction of runaway workloads that run to completion (lower is better).
- **Mean wall-clock seconds:** Average elapsed time per run.
- **Mean file touches:** Average number of file operations observed.
- **Mean traced network events:** Average network-related syscalls observed in bounded runs.

System telemetry (CPU count, load averages, process max RSS, MemAvailable, SwapFree) was captured but not used as a primary comparison dimension.

---

## 3. Results

### 3.1 In-Process Toy-Model Smoke Test

| Metric | TranscriptWrapper | ResourceKernel |
|--------|-------------------|----------------|
| Normal task success rate | 1.0 | 1.0 |
| Runaway prevention rate | 0.0 | 1.0 |
| Mean wall seconds | ~0.0336 | ~0.0008 |
| p95 wall seconds | ~0.1801 | ~0.0040 |
| Mean network calls (zero-network policy) | 0.1667 | 0.0 |

The ResourceKernel denied all runaway actions before execution, reducing mean wall-clock time by approximately two orders of magnitude for runaway workloads. Normal-task success was preserved at parity. The runaway prevention delta was +1.0.

### 3.2 Subprocess-Backed Replay

| Metric | subprocess_baseline | subprocess_resource_kernel |
|--------|---------------------|---------------------------|
| Normal task success rate | 1.0 | 1.0 |
| Runaway prevention rate | 0.0 | 1.0 |
| Runaway completion rate | 1.0 | 0.0 |
| Mean wall seconds | ~0.5205 | ~0.3884 |
| Mean file touches | 5.5 | ~3.22 |
| Mean traced network events | N/A | ~0.333 |

Kill reasons observed across bounded runs: `stdout_bytes>30000`, `file_touches>8`, `network_calls>0`, `wall_seconds>0.9`, `cpu_seconds>1`. All five runaway classes were detected and terminated. Normal-task success remained at parity with the baseline.

The mean wall-clock time reduction (0.5205 s → 0.3884 s) is smaller in relative terms than the in-process result because subprocess startup and `strace` overhead contribute fixed costs regardless of workload type. The mean traced network event count of ~0.333 per mixed workload group reflects that some network syscalls were observed by `strace` before the kill signal took effect.

### 3.3 Negative and Mixed Observations

- **`strace` kills are reactive, not preventive.** The `strace`-based monitor observes a syscall after entry and then kills the process group. At least one network syscall may complete before termination, as reflected in the ~0.333 mean traced network events. This is a fundamental limitation of userspace syscall tracing as an enforcement mechanism.
- **No real LLM token accounting was exercised.** The "token" dimension uses stdout byte count as a proxy. Whether this proxy correlates with actual LLM API token consumption in a production agent loop remains untested.
- **Synthetic workloads only.** Both harnesses use deterministic, hand-crafted workload scripts. No real CLI tools, package managers, web browsers, or LLM inference backends were involved.
- **Single-host, single-OS results.** All experiments ran on a single Linux host. `setrlimit` and `strace` are Linux-specific; portability to other operating systems is not addressed.

---

## 4. Limitations

1. **Synthetic workloads.** The evaluated workloads are deterministic toy programs designed to exhibit specific runaway behaviors. They do not represent the complexity, nondeterminism, or tool-chain diversity of real autonomous agent sessions. The current project artifacts support the finding in the tested setting; they do not establish that the mechanism works universally.

2. **Reactive syscall enforcement.** The `strace`-based file and network monitoring kills after observing a violating syscall rather than preventing it before entry. At least one violating syscall may complete before termination. A production enforcement layer would require seccomp-bpf, cgroups, or nftables to block syscalls before execution.

3. **No real LLM integration.** Token budget enforcement uses stdout byte count as a proxy for LLM token consumption. The correlation between stdout bytes and actual API token usage has not been validated against any LLM inference provider.

4. **Single-environment results.** All experiments were conducted on a single Linux host (20 CPUs reported by telemetry). No cross-platform, cross-hardware, or multi-tenant results are available.

5. **No adversarial evaluation.** The runaway workloads are cooperative (they exhibit the runaway behavior directly). An adversarial agent that deliberately attempts to circumvent quota enforcement—for example, by spawning child processes, using shared memory, or exploiting `strace` race conditions—was not tested.

6. **Small sample sizes.** The subprocess replay used 3 repeats per condition (36 total runs). The in-process smoke test used 10 repeats (120 total runs). These are sufficient to demonstrate a clear signal in synthetic conditions but do not support strong statistical claims about variance or tail behavior.

7. **Automated artifact provenance.** This draft and the underlying project decision were produced by an automated research pipeline. No independent human review of the experimental design, data collection, or interpretation has been performed.

---

## 5. Reproducibility Checklist

| Item | Status |
|------|--------|
| Code available in project directory | Yes: `experiments/resource_kernel.py`, `experiments/subprocess_kernel.py` |
| Unit tests available | Yes: `tests/test_resource_kernel.py`, `tests/test_subprocess_kernel.py` (7 tests total, all passing) |
| Exact commands recorded | Yes: `python3 experiments/resource_kernel.py --out artifacts/resource_kernel_smoke --repeats 10`; `python3 experiments/subprocess_kernel.py --out artifacts/subprocess_replay --repeats 3` |
| Raw result data persisted | Yes: `results.json`, `results.csv` for both experiments |
| Summary statistics persisted | Yes: `summary.json`, `summary_stdout.json` for both experiments |
| Workspace traces persisted | Yes: `strace` trace logs and child scripts in `artifacts/subprocess_replay/workspaces/` |
| System telemetry captured | Yes: CPU count, load averages, max RSS, MemAvailable, SwapFree |
| Random seeds or determinism statement | Workloads are deterministic by construction; no random seeds required |
| Hardware specification | Single Linux host, 20 CPUs (full hardware details not in artifacts) |
| External dependencies | None beyond Python 3 standard library, `strace`, and Linux `setrlimit` |

---

## 6. Conclusion

We evaluated a resource-bounded agent kernel architecture in two experimental stages of increasing fidelity. In both the in-process toy model (120 runs) and the subprocess-backed replay harness (36 runs), the bounded kernel preserved normal-task success at parity with an unbounded baseline while preventing all tested runaway classes. The mechanism—typed action dispatch with pre-execution quota checks, supplemented by OS-level process controls including `setrlimit`, wall-clock timeouts, stdout byte accounting, and `strace`-based syscall monitoring—produced a clear and measurable signal in the tested setting.

These results are bounded by significant caveats: workloads are synthetic, syscall enforcement is reactive rather than preventive, no real LLM token accounting was exercised, and no adversarial evaluation was performed. The evidence supports the architectural principle but does not establish production readiness. The project decision recommends finalizing this validation and only branching to a successor if a concrete production enforcement target (such as cgroup/nftables/seccomp integration for a named agent runner) is selected.

---

## Referenced Artifacts

### Source code
- `experiments/resource_kernel.py` — in-process toy-model harness
- `experiments/subprocess_kernel.py` — subprocess-backed replay harness
- `tests/test_resource_kernel.py` — unit tests for in-process harness
- `tests/test_subprocess_kernel.py` — unit tests for subprocess harness

### In-process smoke-test results
- `artifacts/resource_kernel_smoke/results.json`
- `artifacts/resource_kernel_smoke/results.csv`
- `artifacts/resource_kernel_smoke/summary.json`
- `artifacts/resource_kernel_smoke/summary_stdout.json`

### Subprocess replay results
- `artifacts/subprocess_replay/results.json`
- `artifacts/subprocess_replay/results.csv`
- `artifacts/subprocess_replay/summary.json`
- `artifacts/subprocess_replay/summary_stdout.json`

### Subprocess workspace traces
- `artifacts/subprocess_replay/workspaces/subprocess_resource_kernel_cpu_runaway_jyqd8yui/trace.log.1335184`
- `artifacts/subprocess_replay/workspaces/subprocess_resource_kernel_cpu_runaway_jyqd8yui/long_task.py`
- `artifacts/subprocess_replay/workspaces/subprocess_baseline_cpu_runaway_p5_sd7t3/result.txt`
- `artifacts/subprocess_replay/workspaces/subprocess_baseline_cpu_runaway_p5_sd7t3/long_task.py`
- `artifacts/subprocess_replay/workspaces/subprocess_resource_kernel_wall_runaway_foyzj6m6/trace.log.1335174`
- `artifacts/subprocess_replay/workspaces/subprocess_resource_kernel_wall_runaway_foyzj6m6/long_task.py`
- `artifacts/subprocess_replay/workspaces/subprocess_baseline_wall_runaway_gx8b3k_e/result.txt`
- `artifacts/subprocess_replay/workspaces/subprocess_baseline_wall_runaway_gx8b3k_e/long_task.py`
- `artifacts/subprocess_replay/workspaces/subprocess_resource_kernel_network_runaway_zflnvyvz/trace.log.1335169`
- `artifacts/subprocess_replay/workspaces/subprocess_resource_kernel_network_runaway_zflnvyvz/long_task.py`
- `artifacts/subprocess_replay/workspaces/subprocess_baseline_network_runaway_k5ba2prj/result.txt`
- `artifacts/subprocess_replay/workspaces/subprocess_baseline_network_runaway_k5ba2prj/long_task.py`
- `artifacts/subprocess_replay/workspaces/subprocess_resource_kernel_file_runaway_8r5g59sa/trace.log.1335163`
- `artifacts/subprocess_replay/workspaces/subprocess_resource_kernel_file_runaway_8r5g59sa/notes/artifact_05.txt`
- `artifacts/subprocess_replay/workspaces/subprocess_resource_kernel_file_runaway_8r5g59sa/notes/artifact_06.txt`
- `artifacts/subprocess_replay/workspaces/subprocess_resource_kernel_file_runaway_8r5g59sa/notes/artifact_07.txt`

### Project metadata and decisions
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `run_notes.md`

### Paper audit artifacts
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
