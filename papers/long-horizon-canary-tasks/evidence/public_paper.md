# Long-Horizon Canary Tasks: A Deterministic Prototype Suite for Detecting Agent Failure Modes Before Expensive Inference

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, harness logs, and metrics). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review is asserted or implied.

---

## Abstract

We present a low-cost, locally verifiable canary suite of four long-horizon tasks designed to detect agent failure modes—context decay, instruction forgetting, non-idempotent retry, and resource accumulation—before committing to expensive model inference runs. The suite uses exact deterministic verifiers and three simulated policies (reference, forgetful, greedy) to establish discriminative baselines. In a full calibration run of 240 task cases on an NVIDIA GB10 system, the reference policy achieved a pass rate of 1.00, the forgetful policy 0.25, and the greedy policy 0.00, confirming that the suite cleanly separates intended behavior from two characteristic long-horizon failure patterns under deterministic simulation. The harness executed at approximately 133 cases per second with a peak resident set size of 265 MB and zero swap events. These results establish the feasibility of the canary suite as a local regression gate. They do not characterize any frontier model's long-horizon capability, and no live model or agent was evaluated. The structured claim ledger for this artifact remains empty and flagged as blocked for formal audit; the numerical results reported here are drawn directly from run notes and result files and have not undergone independent claim/evidence verification.

## Introduction

Long-horizon agent reliability—whether an AI system can maintain coherent state, instruction adherence, and resource discipline over many sequential steps—is a central concern for deployed autonomous systems. Existing benchmark frameworks such as METR's time-horizon methodology and Terminal-Bench 2.0 emphasize self-contained tasks with clear success criteria and automatic evaluation. However, running such benchmarks against frontier models requires significant inference time and cost, making them impractical as rapid regression checks during development.

We investigate whether a small, inexpensive, locally verifiable suite of canary tasks can detect long-horizon failure modes before spending time on expensive model or GPU inference runs. The key design principle is that each canary should be self-contained, automatically checkable, and focused on observable task-state outcomes rather than trajectory style—aligning with established evaluation guidance from METR, Terminal-Bench, and OpenAI evaluation best practices.

This paper reports on a deterministic prototype implementation and calibration. We do not evaluate any live language model or agent. Instead, we demonstrate that the suite's verifiers are satisfiable by intended behavior and that they discriminate against two characteristic degraded policies under deterministic simulation. This establishes the suite as a viable regression gate; it does not establish model-level claims about any frontier system.

## Method

### System Environment

All experiments were conducted on an NVIDIA GB10 system with the following configuration:

| Property | Value |
| --- | --- |
| Architecture | aarch64 |
| OS | Ubuntu 24.04.4 LTS |
| GPU | NVIDIA GB10, driver 580.142, CUDA 13.0 |
| Memory | 127,536 MB total; 122,684 MB available at probe |
| Swap | Intentionally disabled (0 kB total) |

The swap-disabled posture is a deliberate constraint: the memory canary verifies peak allocation under a budget with zero-swap semantics, matching the GB10 deployment target. No GPU inference was performed during these experiments; the prototype is a CPU-only deterministic harness.

### Canary Task Design

The suite comprises four canaries, each targeting a distinct long-horizon failure mode:

1. **breadcrumb_integrity** (64 steps): Preserves a hidden digest through distractor transformations. Catches lost long-range state. A correct agent must carry a cryptographic digest across 64 intermediate steps that include noise and transformation, then produce the original digest at the end.

2. **delayed_instruction_guardrail** (48 steps): Applies an early forbidden-token instruction and a delayed required suffix. Catches instruction decay and finalization failures. The agent must respect a constraint introduced at step 1 and apply a suffix instruction introduced at step 40, testing whether both early and late instructions are retained.

3. **tool_failure_recovery** (36 steps): Simulates transient write failures with a ledger verifier. Catches non-idempotent retries and insufficient recovery. The agent must maintain a consistent ledger despite simulated write failures, requiring idempotent retry logic.

4. **memory_budget_posture** (20 steps): Allocates bounded memory and verifies peak allocation under a budget while recording `MemAvailable` and zero-swap posture. Catches gradual resource accumulation.

Each canary has an exact verifier: a deterministic function that inspects the final task state and returns pass/fail plus a numeric score in [0, 1].

### Simulated Policies

Three deterministic policies provide baselines:

- **reference**: Implements intended behavior for all four canaries. Expected to pass all tasks.
- **forgetful**: Simulates context/state decay after a horizon threshold. The policy performs correctly for early steps but loses long-range state and instruction adherence beyond a cutoff.
- **greedy**: Simulates local-option optimization without global state discipline. The policy always selects the locally optimal action, ignoring global invariants such as digest continuity, instruction constraints, or memory budgets.

These policies are not language models; they are deterministic simulations of failure modes that long-horizon agents are hypothesized to exhibit. Their purpose is to validate that the verifiers discriminate between correct and degraded behavior under controlled conditions. They do not represent the full distribution of errors that real language models produce, and the discrimination observed here may not generalize to live agent failures.

### Harness

The harness (`canary_suite/long_horizon_canary.py`) enumerates all policy × task × seed combinations, executes each case, and records pass/fail, score, and per-case metadata. A task manifest (`canary_suite/task_manifest.json`) defines the four canaries declaratively.

### Procedure

1. **System probe**: Record hardware, OS, GPU, memory, and swap configuration.
2. **Initial smoke test** (2 seeds): Expose harness and verifier bugs at low cost.
3. **Corrected smoke test** (2 seeds): Re-run after fixing a discovered verifier bug (see Results).
4. **Full calibration run** (20 seeds): Execute all 3 policies × 4 tasks × 20 seeds = 240 cases. Measure wall-clock time, harness time, peak RSS, and swap events.
5. **Verification**: Assert that reference pass rate equals 1.0, forgetful pass rate is below 0.5, and greedy pass rate equals 0.0.

## Results

### Full Calibration Run

The full calibration run executed 240 task cases in 1.8058 seconds of harness-measured time (1.85 seconds wall clock per `/usr/bin/time -v`), yielding a throughput of approximately 132.9 cases per second. Peak resident set size was 264,812 kB. Zero swap events occurred. These timing and memory figures characterize the deterministic harness itself, not any model inference workload.

### Policy-Level Results

| Policy | Cases | Pass rate | Mean score |
| --- | ---: | ---: | ---: |
| reference | 80 | 1.00 | 1.0000 |
| forgetful | 80 | 0.25 | 0.3899 |
| greedy | 80 | 0.00 | 0.1500 |

The reference policy passes all 80 cases, confirming that the verifiers are satisfiable by intended behavior. The forgetful policy passes 20 of 80 cases (pass rate 0.25), indicating that the suite detects long-range state, instruction, and recovery decay while the memory canary (which has a shorter horizon) still permits some passes. The greedy policy passes zero cases (pass rate 0.00), confirming that local-choice policies ignoring global invariants are uniformly detected under this simulation.

The pass-rate gap between reference and forgetful is 0.75; between reference and greedy, 1.0. Both gaps are substantial and in the expected direction for these deterministic policies. Whether similar gaps would appear with live agents is not addressed by this experiment.

### Task-Level Results

Pass rates aggregated across all three policies:

| Task | Pass rate |
| --- | ---: |
| breadcrumb_integrity | 0.3333 |
| delayed_instruction_guardrail | 0.3333 |
| tool_failure_recovery | 0.3333 |
| memory_budget_posture | 0.6667 |

The memory_budget_posture canary has a higher aggregate pass rate (0.6667) because the forgetful policy retains enough short-horizon discipline to pass it in some seeds, while failing the longer-horizon canaries. This differential sensitivity is consistent with the design intent: the suite varies in horizon length to detect failure at different scales. However, the aggregate pass rate conflates across policies and should not be interpreted as a task-difficulty ranking without disaggregation.

### Verifier Bug Discovery

The initial smoke test (2 seeds) exposed a bug in the `tool_failure_recovery` verifier: the expected sum was recomputed incorrectly from a repeatedly reset RNG, causing the reference policy to fail a case it should have passed. The verifier was fixed by recording expected ledger values during the run rather than recomputing them afterward. The corrected smoke test and subsequent full run confirmed the fix. This incident provides empirical evidence that the canary harness can self-test its own satisfiability before being used for model claims. It also illustrates the value of a reference policy that is expected to pass unconditionally: any reference-policy failure signals a verifier or harness defect rather than a policy defect.

## Limitations

1. **No live model evaluation.** The pilot evaluates deterministic simulated policies, not a live LLM or agent. The discriminative results apply to the simulated failure modes only. Scientific closure on model capability requires running the suite through a real agent/model adapter with fixed prompts, token/tool logs, and repeated seeds. That extension is not addressed here.

2. **No human duration calibration.** Human expert duration was not measured, so the suite cannot express results in METR-style time-horizon units. It functions as a canary/regression gate, not a calibrated time-horizon benchmark.

3. **Deterministic policies are simplifications.** The forgetful and greedy policies simulate specific failure modes but do not capture the full distribution of errors that real language models exhibit. A model may fail for reasons not covered by these two policies, or may pass canaries that a more sophisticated degraded policy would fail. The observed discrimination may overestimate or underestimate the suite's sensitivity to real agent failures.

4. **Single hardware configuration.** All results were collected on one GB10 system. Memory and timing behavior may differ on other platforms, though the verifiers themselves are platform-independent.

5. **Limited task diversity.** Four canaries cover four failure modes. A production regression suite would likely require additional canaries targeting, for example, multi-tool orchestration failures, adversarial prompt injection, or distributed state corruption.

6. **No trajectory analysis.** The verifiers inspect only final task state, not the trajectory of intermediate steps. A failing agent might exhibit informative failure patterns in its trajectory that the current verifiers do not capture.

7. **Empty claim ledger.** The structured claim ledger for this artifact contains no formalized claims and is flagged as blocked for strict claim/evidence audit. The results reported here are drawn directly from the run notes, decision JSON, and result files, not from a formally audited claim set. Readers should exercise corresponding caution in citing specific numerical results.

8. **No cross-validation or statistical uncertainty.** The calibration uses 20 seeds per policy–task combination, which provides point estimates of pass rates but no confidence intervals or statistical tests. The pass rates reported (1.00, 0.25, 0.00) are sample statistics from a deterministic simulation, not estimates of a stochastic process, so conventional confidence intervals do not directly apply. However, the absence of uncertainty quantification limits the strength of conclusions about effect sizes.

## Reproducibility Checklist

- [x] **Harness source**: `canary_suite/long_horizon_canary.py` — included in project artifacts.
- [x] **Task manifest**: `canary_suite/task_manifest.json` — declarative task definitions.
- [x] **Full run results**: `results/long_horizon_canary_full/summary.json` and `results/long_horizon_canary_full/results.jsonl`.
- [x] **Derived metrics**: `results/long_horizon_canary_metrics.json`.
- [x] **System probe log**: `.omx/logs/system_probe_20260429T214750Z.log`.
- [x] **Corrected smoke run log**: `.omx/logs/canary_smoke2_20260429T214913Z.log`.
- [x] **Full run log**: `.omx/logs/canary_full_20260429T214924Z.log`.
- [x] **Seed count specified**: 20 seeds per policy–task combination.
- [x] **Hardware and software environment recorded**: GB10, aarch64, Ubuntu 24.04.4, CUDA 13.0, Python 3.
- [x] **Timing methodology stated**: harness-internal timing and `/usr/bin/time -v` wall clock.
- [x] **Memory measurement methodology stated**: `/proc/meminfo` `MemAvailable`, `/usr/bin/time -v` max RSS, zero swap.
- [x] **Verification assertions documented**: reference pass rate = 1.0, forgetful < 0.5, greedy = 0.0.
- [x] **Known verifier bug and fix documented**: `tool_failure_recovery` expected-sum recomputation bug found in initial smoke test, fixed before full run.
- [ ] **Structured claim audit**: Claim ledger is empty and flagged as blocked. Formal claim/evidence audit has not been completed.

## Conclusion

A deterministic prototype suite of four long-horizon canary tasks was implemented and calibrated on an NVIDIA GB10 system. The suite cleanly discriminates between a reference policy (pass rate 1.00) and two degraded policies modeling characteristic long-horizon failure modes (pass rates 0.25 and 0.00) under deterministic simulation. The harness is fast (approximately 133 cases/second), lightweight (265 MB peak RSS, zero swap), and self-verifying: an initial smoke test exposed a verifier bug that was corrected before the full run.

These results establish the suite as a viable low-cost regression gate for detecting long-horizon agent failure modes before committing to expensive inference runs, within the scope of the simulated failure modes tested. They do not characterize any frontier model's long-horizon capability, and no such claim is made. The discriminative results are limited to deterministic policy simulations and may not generalize to the error distributions of live language models. The natural next step is to build an adapter layer that presents each canary as an agent-facing workspace task, captures token and tool-call traces, and compares repeated-seed pass rates against the deterministic baselines established here.

---

## Referenced Artifacts

| Artifact | Path |
| --- | --- |
| Harness | `canary_suite/long_horizon_canary.py` |
| Task manifest | `canary_suite/task_manifest.json` |
| Full run summary | `results/long_horizon_canary_full/summary.json` |
| Full run results | `results/long_horizon_canary_full/results.jsonl` |
| Derived metrics | `results/long_horizon_canary_metrics.json` |
| System probe log | `.omx/logs/system_probe_20260429T214750Z.log` |
| Corrected smoke log | `.omx/logs/canary_smoke2_20260429T214913Z.log` |
| Full run log | `.omx/logs/canary_full_20260429T214924Z.log` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260429T214648388599+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T214648388599+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T214648388599+0000/paper_manifest.json` |
