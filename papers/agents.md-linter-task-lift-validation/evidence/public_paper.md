# AGENTS.md Linter Task-Lift Validation: A Deterministic Control-Plane Simulation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, claim ledgers, benchmark outputs, decision records, and evidence bundles). The operator who released these artifacts claims no personal authorship credit for the writing or the results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Instruction files such as `AGENTS.md` govern coding-agent lifecycle behavior, yet frequently contain latent defects—contradictions, unsafe directives, and scope ambiguities—that can degrade downstream task outcomes. Prior work on a static `AGENTS.md` linter demonstrated defect detection capability but left open whether linter feedback lifts actual task-level outcomes rather than merely classifying instruction defects. We present a bounded, deterministic control-plane simulation comparing a baseline direct-instruction follower against a linter-mediated intervention policy across eight lifecycle scenarios. The linter-mediated policy maps issue labels to conservative interventions: fallback smoke tests for test contradictions, refusal for destructive-action directives, scope repair for nested-scope conflicts, and resolution for autonomy contradictions. After correcting a linter gap in concrete pytest contradiction detection discovered during the initial benchmark run, the linter-mediated condition achieved 8/8 scenario success (100%) versus 2/8 (25%) for the baseline, yielding an absolute task lift of +75 percentage points. These results constitute evidence that linter findings are actionable and can produce task-level lift under controlled, deterministic conditions. However, the simulation is mechanism-aligned and does not measure stochastic live LLM-agent behavior; the result should be interpreted as a limited positive validation of the intervention mechanism, not as a claim about production agent performance.

## Introduction

Coding agents increasingly rely on instruction files—commonly named `AGENTS.md`—to configure lifecycle behavior including test execution policies, destructive-action permissions, scope boundaries, and autonomy levels. When these instruction files contain defects, agents may execute contradictory directives, perform unsafe operations, or stall on ambiguous scopes. A static linter for `AGENTS.md` files can detect such defects, but detection alone does not establish that the findings are actionable or that acting on them improves downstream outcomes.

The central research question is: **does linter feedback lift downstream coding-agent lifecycle outcomes, rather than merely classify instruction defects?**

This question matters because a linter's utility depends not on its ability to flag issues in isolation, but on whether those flags correspond to real failure modes that can be mitigated. If linter findings are not actionable—if they point to defects that do not materially affect agent behavior—then the linter's utility is limited to code-review hygiene rather than task-level improvement.

To investigate this, we constructed a deterministic control-plane task-lift harness comparing two conditions:

1. **Baseline direct-agent**: A brittle direct-instruction follower that performs edits but is affected by flawed `AGENTS.md` lifecycle directives.
2. **Linter-mediated**: A control-plane policy that first lints `AGENTS.md`, maps issue labels to conservative interventions, and then proceeds with task execution.

The harness evaluates both conditions across eight lifecycle scenarios and scores task success deterministically. This design trades external validity for internal validity: by controlling the agent model and scenario set, we isolate the mechanism by which linter findings translate into task lift, but we cannot generalize to the distribution of real, stochastic LLM-agent behavior.

## Method

### Linter

The linter (`src/agents_linter.py`) is a dependency-free Python implementation carried forward from a prior sibling project, with one targeted improvement. It parses `AGENTS.md` files and emits labeled issues covering categories including test contradictions, destructive-action directives, nested-scope conflicts, and autonomy contradictions.

During initial benchmark execution, the linter failed to detect a contradiction scenario involving the concrete instruction `Run python -m pytest` alongside a contradictory test directive. The root cause was that the test-contradiction positive patterns recognized generic forms (e.g., `run tests`) but not concrete pytest invocations. The fix expanded positive patterns to include:

- `python -m pytest`
- JS package-manager test/check commands
- `go test`
- `ctest`
- `make test/check/lint/verify`

A regression test (`test_concrete_pytest_contradiction_detected`) was added to prevent reversion.

### Task-Lift Harness

The benchmark harness (`scripts/run_task_lift_benchmark.py`) is a deterministic simulator evaluating eight lifecycle scenarios. Each scenario presents an `AGENTS.md` file containing a known defect class and a task that the defect would derail under the baseline condition.

For each scenario, the harness evaluates:

- **Baseline condition**: The direct-instruction follower executes the task using the unmodified, defective `AGENTS.md`. Success is scored as a binary outcome based on whether the task completes correctly given the defect.
- **Linter-mediated condition**: The linter analyzes the `AGENTS.md`, emits issue labels, and the control-plane policy maps each label to a conservative intervention:
  - Test contradictions → fallback smoke tests
  - Destructive-action directives → refusal
  - Nested-scope conflicts → scope repair
  - Autonomy contradictions → resolution

The harness scores success deterministically: if the intervention correctly neutralizes the defect, the scenario succeeds; otherwise it fails.

### Success Criterion

The benchmark was considered successful if both conditions held:

1. Linter-mediated success rate exceeds baseline by ≥25 percentage points.
2. Expected linter-label misses are empty (i.e., the linter correctly labels all scenarios).

### Verification

All source files were compiled with `py_compile`. Unit and regression tests were run via `python3 -m unittest scripts/test_agents_linter.py -v`. The benchmark was executed twice: once before the pytest contradiction fix, and once after.

### Environment

- Host: Linux `6.17.0-1014-nvidia aarch64`
- Python: 3.12.3
- Available memory: ~121 GB
- Swap: disabled

## Results

### Initial Run (Pre-Fix)

The initial benchmark run showed strong lift but failed the success criterion because the linter missed the concrete pytest contradiction label:

- Scenario: `test_contradiction`
- Expected label: `test_contradiction`
- Observed: miss

This failure was itself a finding: the linter had a real gap in recognizing concrete test-invocation forms as contradictory. The benchmark thus functioned as a regression oracle for the linter itself.

### Final Run (Post-Fix)

After expanding the contradiction positive patterns and adding regression coverage, the final benchmark results were:

| Metric | Value |
|---|---|
| Scenarios | 8 |
| Baseline direct-agent success | 2/8 (25.0%) |
| Linter-mediated success | 8/8 (100.0%) |
| Absolute task lift | +75.0 percentage points |
| Expected label misses | none |
| Success criterion met | yes |

Unit and regression verification: 15 tests passed. All `py_compile` checks passed.

### Per-Scenario Summary

The six scenarios where the baseline failed correspond to the six defect classes that the linter detects and the intervention policy neutralizes. The two baseline-success scenarios represent cases where the `AGENTS.md` defect did not directly derail the specific task under evaluation. The linter-mediated condition succeeded on all eight, including those where the baseline also succeeded, indicating no intervention-induced regressions in this scenario set.

### Negative and Mixed Observations

The initial run's label miss is a mixed result: while the final numbers are strongly positive, they required a targeted linter fix discovered through the benchmark process itself. An earlier linter version would have produced a lower linter-mediated success rate, illustrating that task lift is directly mediated by linter coverage and is not an inherent property of the intervention policy alone.

## Limitations

1. **Deterministic simulation, not live agent closure.** The harness models agent behavior deterministically. Real LLM agents exhibit stochastic behavior, and their response to flawed instructions may differ from the brittle direct-instruction follower modeled here. The +75-point lift is a property of the simulation, not a prediction about production agent performance.

2. **Small, mechanism-aligned scenario set.** Eight scenarios were designed to exercise the specific defect classes the linter targets. This alignment inflates the apparent lift relative to a random sample of real-world `AGENTS.md` files, where defects may be less frequent or less impactful.

3. **Baseline is a worst-case model.** The baseline direct-instruction follower is deliberately brittle—it always follows flawed directives to their logical failure. A more robust baseline (e.g., an agent with its own safety heuristics) would likely show a higher baseline success rate and thus a smaller lift.

4. **No stochastic variance.** Because the simulation is deterministic, there are no confidence intervals or significance tests to report. The lift is exact for this harness but has no statistical generalization.

5. **Single linter version.** The results reflect the linter after one targeted fix. Earlier versions would have shown a lower linter-mediated success rate due to the pytest contradiction miss, illustrating that linter coverage directly mediates task lift.

6. **No measurement of intervention cost.** The conservative interventions (refusals, fallbacks, repairs) may introduce latency, user friction, or false-positive blocks in live settings. The harness does not model these costs.

7. **Claim scope is narrow.** The project decision record classifies this result as `validated_limited_positive` with medium confidence, explicitly scoped to "local deterministic control-plane simulator, not live LLM-agent task closure."

## Reproducibility Checklist

- [x] Source code for the linter is available (`src/agents_linter.py`)
- [x] Benchmark harness source is available (`scripts/run_task_lift_benchmark.py`)
- [x] Test suite is available (`scripts/test_agents_linter.py`)
- [x] Machine-readable results are available (`artifacts/task_lift_results.json`)
- [x] Human-readable report is available (`artifacts/task_lift_report.md`)
- [x] Verification logs are available (`logs/verification_20260430T225741Z.log`, `logs/verification_rerun_20260430T225805Z.log`)
- [x] Decision record is available (`.omx/project_decision.json`)
- [x] Run notes are available (`run_notes.md`)
- [x] Environment details are recorded (OS, Python version, architecture)
- [x] All commands for reproduction are documented in run notes
- [ ] Live-agent validation has **not** been performed
- [ ] Statistical significance testing is **not applicable** (deterministic simulation)

## Conclusion

A deterministic control-plane simulation demonstrates that linter-mediated interventions can produce large task-success lifts (+75 percentage points) across eight `AGENTS.md` lifecycle scenarios, raising baseline success from 25% to 100%. The benchmark also served as a practical quality check: it discovered and drove the fix of a real linter gap in concrete pytest contradiction detection, confirming that the task-lift harness can function as a linter regression oracle.

However, these results are bounded. The simulation is deterministic, the scenario set is small and mechanism-aligned, and the baseline is a worst-case model. The result constitutes evidence for the *mechanism*—that linter findings are actionable and can produce task-level lift under controlled conditions—but does not constitute evidence for the *magnitude* of that lift under real, stochastic LLM-agent conditions.

The recommended next step is to run the same scenario matrix with live, sandboxed agent invocations (e.g., Codex or OMX task sandboxes), scoring actual file edits, test execution, stalls, and unsafe-action avoidance. Only at that tier can the task-lift claim be validated against the distribution of real agent behavior.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Linter source | `src/agents_linter.py` |
| Benchmark harness | `scripts/run_task_lift_benchmark.py` |
| Test suite | `scripts/test_agents_linter.py` |
| Benchmark results (JSON) | `artifacts/task_lift_results.json` |
| Benchmark report (Markdown) | `artifacts/task_lift_report.md` |
| Initial verification log | `logs/verification_20260430T225741Z.log` |
| Final verification log | `logs/verification_rerun_20260430T225805Z.log` |
| Final review log | `logs/final_review_20260430T225902Z.log` |
| Project decision record | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Prior linter source (seed) | `<local-path-redacted>` |
