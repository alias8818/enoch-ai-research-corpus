# Executive/Worker Model Split: A Monte Carlo Viability Study of Tiered LLM Agent Allocation

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (simulation scripts, run logs, structured decision records, and local agent-roster inspection). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate whether an LLM-based agent runtime can retain a strong executive/planner/verifier model while delegating worker subtasks to cheaper, faster models without unacceptable loss of project success. Using a dependency-free Monte Carlo decision model calibrated against a locally observed agent role roster (11 frontier, 8 standard, 1 spark role), we simulate 5,000 projects under seven allocation policies. The homogeneous frontier team baseline achieves a 58.6% simulated success rate. The currently deployed role split saves 22.2% cost and 5.9% wall time but loses 8.6 percentage points of success. An executive-frontier/worker-standard policy saves 41.2% cost and 9.9% wall time at a 10.9 pp success penalty. An executive-frontier/worker-spark policy saves 52.6% cost but incurs a 26.1 pp success loss, failing all quality-preserving viability criteria. Sensitivity analysis reveals that the standard-worker split becomes quality-preserving (≤5 pp success loss) only when non-frontier worker quality exceeds the conservative default calibration by approximately 10%, yielding 42–44% cost savings under those conditions. We conclude that a guarded tiered split is viable, but a hard cutover to all-spark workers is not supported by the available evidence. All results derive from synthetic simulation with heuristic parameter calibration; they constitute viability-level evidence, not production validation.

## Introduction

LLM-based agent runtimes increasingly decompose complex projects into subtasks assigned to specialized roles: planning, execution, debugging, testing, verification, and writing. A natural cost-reduction strategy is to retain a capable "executive" model for high-stakes planning and verification while delegating implementation subtasks to cheaper, faster models. However, the quality–cost tradeoff is poorly characterized: cheaper models may introduce defects that the executive verifier cannot fully catch, and the cost of frontier-model repair loops may erode savings.

This study asks: can an agent runtime keep a strong executive/planner/verifier model while delegating worker subtasks to cheaper models without losing too much project success?

We approach this with a synthetic Monte Carlo decision model rather than live API benchmarks. This choice reflects the exploring-stage nature of the question and the availability of local configuration evidence. The approach provides viability-level evidence—sufficient to reject clearly non-viable policies and to identify promising candidates for live validation—but insufficient for production hard-cutover decisions.

The locally observed agent roster (inspected from `~/.codex/agents`) already implements a guarded tiered split: frontier models are assigned to planner, architect, executor, test, security, and code-review roles, while standard models serve debugger, build-fixer, verifier, writer, researcher, and dependency-expert roles. A single spark model serves the explore role. This motivates three questions: (1) whether the existing split is near-optimal, (2) whether more aggressive downgrading is safe, and (3) under what conditions cheaper workers become viable.

## Method

### Simulation Design

We constructed a dependency-free Monte Carlo simulator (`executive_worker_split_sim.py`) that models each project as three phases:

1. **Executive decomposition/scheduling.** The executive model decomposes the project into role-specific worker tasks and schedules them.
2. **Worker execution.** Each role-specific worker task (explore, executor, debugger, test-engineer, verifier, writer, etc.) is executed by the assigned model tier. Worker quality is parameterized per tier (frontier, standard, spark) and affects the probability of introducing defects.
3. **Executive synthesis/verification with bounded repair.** The executive synthesizes worker outputs and verifies the result. Detected defects trigger bounded frontier-model repair attempts (default maximum: 4 repairs). Verification recall is parameterized (default: 0.78), modeling the probability that the verifier catches a real defect.

Outputs are synthetic cost units, wall-time units, and binary project success. These are not live API billing figures or measured LLM accuracy; they are relative quantities suitable for policy comparison within the model.

### Calibration

The simulator was calibrated against the locally observed agent roster, which contains 11 frontier roles, 8 standard roles, and 1 spark role. Relative quality and cost parameters for each tier were set heuristically based on published model capability differentials, not on measured provider billing or accuracy. This is a significant limitation that we return to in the Limitations section.

### Policies Evaluated

Seven allocation policies were simulated:

| Policy | Executive | Workers | Parallelism |
|---|---|---|---|
| `homogeneous_frontier_team` | Frontier | Frontier | 4-way |
| `monolith_frontier_sequential` | Frontier | Frontier | 1 (sequential) |
| `current_role_split` | Frontier | Mixed (per roster) | 4-way |
| `executive_frontier_worker_standard` | Frontier | Standard | 4-way |
| `executive_frontier_worker_spark` | Frontier | Spark | 4-way |
| `homogeneous_standard_team` | Standard | Standard | 4-way |
| `homogeneous_spark_team` | Spark | Spark | 4-way |

The `current_role_split` policy reflects the actual tier assignments observed in the local agent roster: frontier for planner/architect/executor/test/security/code-review, standard for debugger/build-fixer/verifier/writer/researcher/dependency-expert, and spark for explore.

### Sensitivity Analysis

We varied worker quality multipliers and verification recall parameters across a grid. A policy was deemed "viable" if it achieved at least 15% cost savings and no worse than a 5 percentage-point success loss relative to the homogeneous frontier team baseline. This criterion is necessarily somewhat arbitrary; we report results for all policies regardless of whether they meet it.

### Execution Environment

All simulations ran on an NVIDIA GB10 host with approximately 122 GB available memory and zero swap. The main 5,000-project run consumed 28,712 kB peak RSS and completed in 4.14 seconds wall time. No GPU was used; this is a CPU-only Monte Carlo simulation.

## Results

### Main Simulation

The table below reports results from 5,000 simulated projects per policy (seed 3403677). The homogeneous frontier team serves as the reference baseline.

| Policy | Success Rate | Success Δ (pp) | Mean Cost | Cost Δ (%) | Mean Wall | Wall Δ (%) |
|---|---:|---:|---:|---:|---:|---:|
| `homogeneous_frontier_team` | 0.586 | 0.0 | 28.21 | 0.0 | 16.48 | 0.0 |
| `monolith_frontier_sequential` | 0.586 | 0.0 | 28.21 | 0.0 | 37.65 | +128.4 |
| `current_role_split` | 0.500 | −8.6 | 21.94 | −22.2 | 15.50 | −5.9 |
| `executive_frontier_worker_standard` | 0.477 | −10.9 | 16.59 | −41.2 | 14.85 | −9.9 |
| `executive_frontier_worker_spark` | 0.325 | −26.1 | 13.36 | −52.6 | 13.71 | −16.8 |
| `homogeneous_standard_team` | 0.463 | −12.3 | 12.29 | −56.4 | 12.69 | −23.0 |
| `homogeneous_spark_team` | 0.306 | −28.0 | 7.53 | −73.3 | 9.73 | −41.0 |

**Parallelism is valuable.** The monolithic sequential frontier policy matches the frontier team on success and cost but incurs 128.4% more wall time, confirming that 4-way worker parallelism itself contributes substantially to throughput regardless of model tier.

**The current role split saves cost but loses success.** At default calibration, the currently deployed role split reduces cost by 22.2% and wall time by 5.9%, but sacrifices 8.6 pp of success. This does not meet the ≤5 pp viability criterion under default assumptions.

**Standard workers offer a cost–quality middle ground.** The executive-frontier/worker-standard policy saves 41.2% cost and 9.9% wall time but loses 10.9 pp success at default calibration. The cost savings are substantial, but the success penalty exceeds the viability threshold.

**All-spark workers are not viable.** The executive-frontier/worker-spark policy loses 26.1 pp of success despite 52.6% cost savings. The homogeneous spark team performs worst overall (−28.0 pp success). Even with a frontier executive retaining verification authority, spark-tier workers introduce too many defects for the bounded repair mechanism to recover.

**Negative finding: no policy with non-frontier workers meets the viability criterion at default calibration.** Under the conservative default parameterization, every policy that assigns any worker to a non-frontier tier incurs more than 5 pp success loss. The viability of tiered splits depends entirely on whether real non-frontier models are stronger than the conservative default assumes.

### Sensitivity Analysis

Under the viability criterion (≥15% cost savings, ≤5 pp success loss):

- **`executive_frontier_worker_standard`**: 5 viable sensitivity cells. This policy becomes quality-preserving when non-frontier worker quality is approximately 10% above the conservative default calibration, at which point it delivers approximately 42–44% cost savings.
- **`current_role_split`**: 4 viable cells under similar quality/verification conditions, saving approximately 22–23% cost.
- **`executive_frontier_worker_spark`**: 0 viable cells. Even with high verification recall, all-spark workers remain too quality-risky in this model.

The sensitivity results indicate that the viability of standard-worker policies is sensitive to the assumed quality gap between frontier and standard tiers. If real standard-tier models perform closer to frontier than the conservative default assumes, the executive-frontier/worker-standard policy is the most promising candidate. If the quality gap is as large or larger than the default, no tiered split meets the viability criterion.

## Limitations

1. **Synthetic, not live.** All results derive from a Monte Carlo decision model with heuristic parameter calibration. They do not reflect actual LLM API calls, measured token costs, or real task completion rates. The cost and success units are relative, not dollar-denominated or empirically validated. These are toy simulation results, not production benchmarks.

2. **Heuristic calibration.** Relative model quality and cost assumptions are informed estimates, not measured provider billing or accuracy data. If real standard-tier models are stronger than the conservative default assumes, the results shift favorably for standard-worker policies; if weaker, the opposite. The sensitivity analysis partially addresses this, but the parameter space is not exhaustively explored.

3. **Verification model is simplified.** The simulator assumes a single verification recall parameter and bounded repair. Real verification may exhibit correlated failures, task-dependent difficulty, or escalation patterns not captured here. The 0.78 default recall is itself a heuristic choice.

4. **No live replay validation.** The recommended next step—a live replay on 20–50 archived tasks—has not been conducted. Simulation results alone are insufficient for a production hard cutover decision.

5. **Source page unavailable.** The original project Notion page returned 404; the study proceeded using local artifacts only, which may omit context from the original problem formulation.

6. **Single workload distribution.** The simulation draws project difficulty from a single parametric distribution. Real workloads may exhibit heavier tails or different defect profiles.

7. **Claim audit status is blocked.** The structured claim ledger for this artifact contains no extracted claims and carries an `audit_status` of `blocked_empty_claims`. The findings reported here have not passed a formal claim/evidence audit. Readers should weight the results accordingly.

8. **No causal mechanism for defect generation.** The simulator models defect introduction as a per-tier probability draw, not as a function of task complexity, context length, or model-specific failure modes. This abstracts away the very mechanisms that would determine real-world tier performance.

## Reproducibility Checklist

- **Simulation script:** `scripts/executive_worker_split_sim.py`
- **Agent roster script:** `scripts/inspect_agent_model_split.py`
- **Main run command:** `python3 scripts/executive_worker_split_sim.py --projects 5000 --seed 3403677 --verify-recall 0.78 --max-repairs 4 --outdir results/main --sensitivity`
- **Smoke test command:** `python3 scripts/executive_worker_split_sim.py --projects 20 --seed 34 --outdir results/smoke_v2`
- **Random seed:** 3403677 (main), 34 (smoke)
- **Key parameters:** verify-recall=0.78, max-repairs=4, projects=5000
- **Output artifacts:** `results/main/runs.csv`, `results/main/summary.json`, `results/main/sensitivity.csv`, `results/summary.md`, `results/agent_model_split.json`
- **Logs:** `logs/smoke_v2.log`, `logs/main.log`, `logs/main_time.log`, `logs/environment.log`
- **Runtime:** 4.14 s wall time, 28,712 kB peak RSS, CPU-only on NVIDIA GB10 host (~122 GB available memory, 0 swap)
- **Dependencies:** Python 3 standard library only; no external packages required
- **Reproducibility note:** The simulator is deterministic given the seed and parameters. Re-running the commands above should produce identical numerical results on any platform with a compatible Python 3 runtime.

## Conclusion

Synthetic Monte Carlo evidence supports a guarded tiered executive/worker model split but does not support a hard cutover to all-cheap or all-spark workers. Under default calibration, the currently deployed role split saves 22.2% cost at an 8.6 pp success penalty—outside the ≤5 pp viability threshold. However, sensitivity analysis shows that when non-frontier worker quality is modestly above the conservative default (approximately 10%), the executive-frontier/worker-standard policy meets the viability criterion with 42–44% cost savings. The all-spark worker policy fails the quality-preserving criterion in every sensitivity cell tested.

The central negative finding is that no tiered policy meets the viability criterion at the conservative default calibration. The central positive finding is that the standard-worker split is conditionally viable: it requires non-frontier models to be somewhat stronger than the conservative worst-case assumption. Whether this condition holds in practice is an empirical question that this simulation cannot answer.

These findings motivate a live replay validation: replay 20–50 archived tasks under (1) the current role split and (2) a frontier-executive/standard-worker policy with frontier escalation on failed verification. Promotion to production should proceed only if live success loss remains within 5 pp while cost drops at least 20%. Until such validation is completed, the simulation results should be treated as viability-level evidence, not as production recommendations.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Simulation script | `scripts/executive_worker_split_sim.py` |
| Agent roster inspection script | `scripts/inspect_agent_model_split.py` |
| Agent roster JSON | `results/agent_model_split.json` |
| Main run data | `results/main/runs.csv` |
| Main summary | `results/main/summary.json` |
| Sensitivity data | `results/main/sensitivity.csv` |
| Summary markdown | `results/summary.md` |
| Smoke test log | `logs/smoke_v2.log` |
| Main run log | `logs/main.log` |
| Main timing log | `logs/main_time.log` |
| Environment log | `logs/environment.log` |
| Run notes | `run_notes.md` |
| Project decision record | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260430T101015699270+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T101015699270+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T101015699270+0000/paper_manifest.json` |
