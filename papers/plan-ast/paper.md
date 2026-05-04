# Executable Plan ASTs for Agent Governance: A Bounded Smoke Test

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metrics, and log references). The operator who released these artifacts claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Long-running autonomous agents risk drift when execution proceeds linearly past failed quality gates, accumulating stale partial artifacts and violating budget constraints. We investigate whether representing agent plans as executable abstract syntax trees (ASTs) — with explicit dependency edges, conditional guards, loop expansion, budget enforcement, and rollback stacks — can mitigate this drift relative to naive linear command lists. A dependency-free prototype runner was evaluated on three hand-authored local smoke plans and one failure-injection scenario. In the injected-failure scenario, the AST runner passed 5 of 5 governance checks (dependency blocking, budget enforcement, rollback execution, typed evidence emission, and drift prevention), while a naive linear baseline passed only 1 of 3 checks — detecting the failure but proceeding to execute a dependent step and leaving a stale artifact. These results are bounded: plan artifacts were hand-authored rather than compiled from natural language, and workflows were local filesystem and shell operations rather than long-running live agents. The smoke signal is positive but does not establish robustness under messy real-workflow conditions or natural-language plan compilation quality.

## Introduction

Autonomous agents that execute multi-step plans face a governance problem: when an intermediate step fails or exceeds a budget, subsequent steps that depend on the failed step's output should not execute. Without enforcement, agents drift — continuing along a plan whose preconditions are no longer satisfied, producing unreliable artifacts and compounding errors.

A common approach is to document dependencies, budgets, and rollback procedures in natural language or comments, relying on the agent's runtime to interpret them. This places the enforcement burden on the agent itself, which may lack the discipline or capability to honor these constraints under pressure.

An alternative is to make the plan itself executable: represent it as an AST where control-flow semantics — dependencies, conditions, loops, budgets, and rollback — are first-class, machine-checked constructs rather than advisory documentation. If the AST runtime enforces these semantics, the agent cannot bypass governance by simply continuing past a failure.

This paper reports on a bounded smoke test of this mechanism. We built a minimal, dependency-free AST runner and compared it against a naive linear baseline on a failure-injection scenario. The question is narrow: can an executable plan AST enforce governance semantics that a linear command list does not, on toy local workflows? We do not yet address whether natural-language plans can be reliably compiled into such ASTs, or whether the approach survives messy real-world workflows with concurrent modification, partial writes, or network failures.

## Method

### Prototype Implementation

A dependency-free Python runner (`scripts/plan_ast_runner.py`) was implemented with the following AST features:

- **Steps with stable IDs and dependency edges.** Each step declares a `depends_on` list. The runner topologically validates and executes steps only when all dependencies have succeeded.
- **Conditional guards.** Steps may specify conditions (e.g., `exists(path)`) that must evaluate true before execution proceeds.
- **`foreach` expansion.** A step may iterate over a list, generating subplan instances for each element.
- **Command budget enforcement.** A plan-level `budget.max_commands` cap causes the run to abort if exceeded.
- **Rollback stack.** Steps annotated with `on_failure: rollback` push rollback actions (file deletion, shell commands) onto a stack. On failure, the runner executes the rollback stack in reverse order.
- **Typed evidence records.** The runner emits machine-readable evidence: file artifacts, numeric metrics, and per-step status records.

Plan artifacts use JSON syntax saved with `.yaml` extension. JSON is a valid YAML subset, which keeps the runner install-free (no YAML parser dependency) while producing YAML-compatible AST artifacts. This is a pragmatic shortcut for the smoke test; a production system would require a proper YAML parser or a dedicated AST serialization format.

### Experimental Design

Three smoke plans were executed:

1. **success_with_loop.yaml** — a plan with `foreach` expansion and dependency chains, expected to complete successfully.
2. **failure_with_rollback.yaml** — a plan where an intermediate step fails, triggering rollback of prior steps' artifacts.
3. **condition_and_budget.yaml** — a plan testing conditional guards and command budget enforcement.

A naive linear baseline (`experiments/naive_baseline.py`) was also executed against the same failure-injection scenario as plan 2. The naive baseline processes steps sequentially without dependency checking, rollback, or budget enforcement.

### Evaluation Criteria

The viability criteria, established before execution, required the prototype to:

1. Execute a plan AST from a YAML-compatible artifact without external services.
2. Enforce dependencies, conditions, and budgets rather than merely documenting them.
3. Produce typed evidence and machine-readable run results.
4. Handle failure with rollback and dependency blocking.
5. Beat a naive linear baseline on at least one drift/failure-injection scenario.

### Test Infrastructure

Unit tests were implemented in `tests/test_runner.py` and executed via `pytest`. All experiment runs were logged to `logs/`. No external services, network calls, or GPU resources were involved.

## Results

### Unit Tests

All 3 unit tests passed (`pytest: 3 passed`).

### Smoke Plan Execution

All three smoke plans completed and produced machine-readable run results:

- `results/success_with_loop/run_result.json` — successful completion with loop expansion.
- `results/failure_with_rollback/run_result.json` — failure detected, rollback executed, partial artifacts removed.
- `results/condition_and_budget/run_result.json` — conditions evaluated, budget enforced.

All AST core checks passed (`all_ast_core_checks_pass: true`).

### Failure-Injection Scenario Comparison

The critical comparison is the failure-injection scenario, where an intermediate quality-gate step fails:

| Metric | AST Runner | Naive Linear Baseline |
|--------|-----------|----------------------|
| Checks passed | 5 / 5 | 1 / 3 |
| Detected failure | Yes | Yes |
| Blocked dependent step | Yes | No |
| Rolled back partial artifact | Yes | No |

The naive baseline detected the failed quality gate but continued to execute the dependent drift step and did not roll back the partial artifact. The AST runner blocked the dependent step via dependency enforcement and executed rollback actions to remove the stale artifact.

### Summary Metrics

The consolidated metrics (`results/metrics_summary.json`) confirm:

- AST failure scenario: 5 passes out of 5 total checks.
- Naive failure scenario: 1 pass out of 3 total checks.

The project decision record classifies this as a `positive_bounded_smoke` result with `medium` confidence and `moderate` evidence strength.

## Limitations

This smoke test carries several important limitations:

1. **Hand-authored plans.** Plan artifacts were written by hand. Natural-language-to-AST compilation — the step that would make this approach usable by agents drafting plans in English — was not evaluated. Compilation quality remains the critical unknown.

2. **Toy workflows.** Smoke tasks are local filesystem and shell operations. They do not represent long-running live agents, network-dependent services, or concurrent multi-agent interactions.

3. **JSON-as-YAML convention.** The runner accepts JSON syntax saved with `.yaml` extension to avoid adding a YAML parser dependency. This is a pragmatic shortcut for the smoke test; a production system would need a proper YAML parser or a dedicated AST serialization format.

4. **No GPU or heavy compute.** This was a control-plane and prototype evaluation. No GPU workloads, large model inference, or distributed computation was involved.

5. **Single failure scenario.** Only one failure-injection pattern was tested. The robustness of rollback, budget enforcement, and dependency blocking under diverse failure modes (partial writes, timeouts, concurrent modification) is unknown.

6. **No governance overhead measurement.** The runtime cost of AST enforcement versus naive execution was not profiled. For toy plans this cost is negligible, but it may matter for large plans or time-sensitive workflows.

7. **No comparison to existing workflow engines.** Systems providing dependency enforcement and retry semantics exist in production use. The novelty claim here is narrow: an agent-governance-oriented AST with rollback and typed evidence, not the general concept of dependency-based execution.

8. **Empty claim ledger.** The structured claim ledger for this artifact contains no formal claims and its audit status is `blocked_empty_claims`. The results reported here are drawn directly from the run notes and decision JSON rather than from a formally audited claim-evidence chain.

## Reproducibility Checklist

- **Source code:** `scripts/plan_ast_runner.py`
- **Test suite:** `tests/test_runner.py` (3 tests, all passing)
- **Plan artifacts:**
  - `experiments/plans/success_with_loop.yaml`
  - `experiments/plans/failure_with_rollback.yaml`
  - `experiments/plans/condition_and_budget.yaml`
- **Baseline:** `experiments/naive_baseline.py`
- **Result files:**
  - `results/success_with_loop/run_result.json`
  - `results/failure_with_rollback/run_result.json`
  - `results/condition_and_budget/run_result.json`
  - `results/naive_baseline/naive_result.json`
  - `results/metrics_summary.json`
- **Logs:**
  - `logs/pytest_runner.log`
  - `logs/experiment_run.log`
  - `logs/metrics_summary.log`
  - `logs/environment.log`
- **Decision record:** `.omx/project_decision.json`
- **Run notes:** `run_notes.md`
- **Dependencies:** Python 3 standard library only (no external packages)
- **Execution commands:** Listed verbatim in `run_notes.md`
- **Hardware:** Local execution; no GPU required
- **Result classification:** Toy simulation / local prototype (not CUDA calibration, not llama.cpp hook-prototype, not production validation)

## Conclusion

An executable plan AST can enforce governance semantics — dependency blocking, budget enforcement, rollback, and typed evidence — that a naive linear command list does not. In a single failure-injection scenario, the AST runner passed all 5 governance checks while the naive baseline passed only 1 of 3, proceeding past a failed gate and leaving stale artifacts.

This is a bounded positive signal, not a validation. The plans were hand-authored, the workflows were toy local operations, and only one failure pattern was tested. The critical next step is natural-language plan compilation: can an agent's English-language plan be reliably translated into an executable AST that preserves the governance properties demonstrated here? A follow-on validation should compile real agent plans into this AST, replay messy workflow traces with crash and fault injection, and compare fidelity, rollback completeness, evidence coverage, and governance overhead against current manual and control-plane baselines.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Runner | `scripts/plan_ast_runner.py` |
| Tests | `tests/test_runner.py` |
| Plan: success with loop | `experiments/plans/success_with_loop.yaml` |
| Plan: failure with rollback | `experiments/plans/failure_with_rollback.yaml` |
| Plan: condition and budget | `experiments/plans/condition_and_budget.yaml` |
| Naive baseline | `experiments/naive_baseline.py` |
| Result: success with loop | `results/success_with_loop/run_result.json` |
| Result: failure with rollback | `results/failure_with_rollback/run_result.json` |
| Result: condition and budget | `results/condition_and_budget/run_result.json` |
| Result: naive baseline | `results/naive_baseline/naive_result.json` |
| Metrics summary | `results/metrics_summary.json` |
| Pytest log | `logs/pytest_runner.log` |
| Experiment log | `logs/experiment_run.log` |
| Metrics log | `logs/metrics_summary.log` |
| Environment log | `logs/environment.log` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260430T123503219374+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T123503219374+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T123503219374+0000/paper_manifest.json` |
| Notion source | `https://www.notion.so/Plan-AST-source-record-redacted` |
