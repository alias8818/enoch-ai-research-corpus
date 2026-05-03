# Sequential Safe Design-of-Experiments via Gaussian-Process Expected Improvement: A Simulation Viability Study

> **AI provenance notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, benchmark logs, decision records, and telemetry). The operator who released the artifact claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact. The claim ledger for this paper contains no completed claim-audit entries, and the review checklist (9 items) remains entirely in pending status. No human reviewer has endorsed this document.

---

## Abstract

We evaluate whether a small autonomous design-of-experiments (DOE) agent can produce safe, useful next-run recommendations for a constrained physical experiment, with measurable improvement over naïve safe random sampling or a one-shot space-filling design. The agent combines a maximin Latin-hypercube initial design with a Gaussian-process surrogate (Matérn 5/2 kernel, white-noise term) and sequential expected-improvement acquisition, subject to hard deterministic safety constraints enforced before proposal. On a three-factor noisy reactor-yield toy simulation over 20 independent seeds at a 20-run budget, the agent achieved a mean best observed yield of 92.84 (SD 0.36), compared to 89.73 (SD 2.30) for safe random sampling and 88.76 (SD 2.47) for LHS-only designs. Paired t-tests yielded *p* ≈ 6.5 × 10⁻⁶ (agent vs. safe random, mean Δ = +3.11, 95% CI [2.05, 4.16]) and *p* ≈ 1.3 × 10⁻⁶ (agent vs. LHS-only, mean Δ = +4.08, 95% CI [2.85, 5.31]). All three methods recorded zero unsafe proposals. These results constitute positive toy-simulation evidence for the viability of constrained GP-EI DOE agents in low-dimensional, run-scarce physical experiments. However, the evidence is limited to a single simulated response surface with known deterministic safety constraints; closure on real physical workflows would require learned probabilistic safety constraints, instrument interfaces, and calibration runs.

## Introduction

Design of experiments (DOE) for physical processes faces a fundamental tension: each run consumes material, time, and instrument capacity, yet the experimenter must explore a continuous factor space efficiently enough to locate optima before the budget is exhausted. Classical response-surface designs (central composite, Box-Behnken) address this for small factor counts but allocate the entire budget upfront, leaving no room for sequential adaptation. NIST guidance on experimental design selection notes that for two-to-four-factor response-surface objectives, these families are appropriate, while also emphasizing the need to reserve resources for center-point replication and confirmation runs—an implicit argument against spending the full budget in a single batch. NIST's response-surface guidance further highlights the run explosion of full three-level factorial designs and the importance of designs capable of modeling curvature, supporting the use of surrogate-based sequential acquisition when runs are scarce.

Sequential Bayesian optimization offers an alternative: fit a probabilistic surrogate to observed data, then use an acquisition function to select the next run. Gaussian-process (GP) regression is a natural surrogate choice because it provides posterior means and standard deviations, enabling uncertainty-aware acquisition. However, GP regression as implemented in common libraries (e.g., scikit-learn) is not sparse and can lose efficiency in high-dimensional spaces, constraining the viable scope to low- or moderate-dimensional expensive experiments.

A further complication in physical settings is safety: certain factor combinations may violate hard process constraints (e.g., pressure limits, precipitation thresholds). An autonomous DOE agent must enforce these constraints before proposing any run, not merely penalize violations after the fact.

This study asks: **Can a small autonomous DOE agent, combining safe Latin-hypercube initialization with GP-based expected-improvement acquisition, produce measurably better recommendations than safe random sampling or one-shot LHS designs, while maintaining zero unsafe proposals?**

We address this question through a controlled toy-simulation study rather than a physical experiment, and we report the results with their limitations honestly.

## Method

### Agent design

The DOE agent (`src/doe_agent.py`) operates in six stages:

1. **Factor definition.** Bounded continuous physical factors are declared with lower and upper limits.
2. **Safety enforcement.** Known hard safety constraints are checked before any candidate is accepted. Candidates violating constraints are rejected regardless of acquisition value.
3. **Initial design.** A maximin Latin-hypercube sample (LHS) of configurable size is generated within the safe region to provide initial coverage.
4. **Surrogate fitting.** A Gaussian-process regressor with a Matérn 5/2 kernel and a WhiteKernel noise term is fit to all observed (factor, response) pairs.
5. **Sequential acquisition.** Expected improvement (EI) is computed over a large pool of candidate points drawn uniformly within bounds. The highest-EI candidate that satisfies all safety constraints is selected as the next run.
6. **Trace emission.** The agent logs its proposals, surrogate state, and acquisition values for post-hoc analysis.

### Benchmark problem

The toy physical benchmark is a three-factor reactor optimization:

- **Factors:** catalyst percentage, residence time (minutes), temperature (°C).
- **Response:** noisy yield, computed from a hidden curved response surface with additive Gaussian observation noise.
- **Hard constraints:** pressure-like and precipitation-like deterministic constraints that exclude a portion of the factor space.

This benchmark is deliberately low-dimensional and noisy, reflecting the intended use case of scarce-run physical experiments. It is important to emphasize that this is a toy simulation: the response surface and constraints are synthetic, and no physical instrument or lab data is involved.

### Baselines

Two baselines are compared:

1. **Safe random.** At each step, a candidate is drawn uniformly at random from the factor bounds and accepted only if it satisfies all safety constraints. This controls for the effect of safety enforcement alone.
2. **LHS-only.** A single maximin Latin-hypercube design of size equal to the full budget is generated, filtered for safety, and evaluated. This represents a one-shot space-filling strategy with no sequential adaptation.

### Experimental configuration

The primary benchmark uses the following parameters:

| Parameter | Value |
|---|---|
| Seeds | 20 |
| Budget per seed | 20 runs |
| Initial design size | 6 runs |
| Candidate pool per acquisition step | 3,000 |
| GP kernel | Matérn 5/2 + WhiteKernel |

A preliminary smoke test was run with 3 seeds, budget 10, initial 4, and 500 candidates to verify the pipeline before the full benchmark.

### Statistical analysis

For each seed, the best observed noisy yield over the 20-run budget is recorded for each method. Paired t-tests (agent vs. safe random; agent vs. LHS-only) are computed across the 20 seeds, with 95% confidence intervals on the mean difference.

An oracle context is established via Monte Carlo search: 500,000 safe random samples are drawn, and the best clean (noiseless) objective value is recorded. This provides a reference ceiling, though the agent's noisy observations may exceed the clean oracle value due to observation noise.

### System environment

All runs were executed on a machine with 122,364,676 kB available memory and 0 kB swap. The total wall time for the 20-seed benchmark was 17.55 seconds. The workload was small enough that no long-run memory or thermal calibration was required.

## Results

### Best observed yield

Over 20 independent seeds at a 20-run budget:

| Method | Mean best yield | SD | Min | Max |
|---|---|---|---|---|
| DOE agent (GP-EI) | 92.84 | 0.36 | 92.40 | 94.02 |
| Safe random | 89.73 | 2.30 | — | — |
| LHS-only | 88.76 | 2.47 | — | — |

The DOE agent's mean best observed yield exceeds safe random by 3.11 points and LHS-only by 4.08 points. Min and max values for the two baselines were not recorded in the benchmark summary; only mean and SD are available from the stored artifacts.

### Statistical significance

Paired t-tests across 20 seeds:

| Comparison | Mean Δ | 95% CI | *p*-value |
|---|---|---|---|
| Agent − Safe random | +3.11 | [2.05, 4.16] | 6.49 × 10⁻⁶ |
| Agent − LHS-only | +4.08 | [2.85, 5.31] | 1.31 × 10⁻⁶ |

Both differences are statistically significant at conventional thresholds. However, the sample size of 20 seeds, while sufficient to detect these effect sizes, remains modest; wider replication would strengthen confidence in the magnitude of the advantage.

### Safety

All three methods recorded **zero unsafe proposals** across all seeds and all runs. The deterministic safety-constraint filter was effective in every case. This confirms that the agent's sequential acquisition does not degrade safety enforcement, but it also reflects the relative ease of enforcing known deterministic constraints in simulation. The safety result should not be interpreted as evidence that the agent would maintain perfect safety under uncertain or learned constraints.

### Oracle context

The Monte Carlo oracle search (500,000 safe samples) found a best clean objective of 92.16 at catalyst_pct ≈ 2.92, residence_min ≈ 34.76, temperature_c ≈ 118.37. The DOE agent's mean noisy best (92.84) exceeds this clean oracle value. This is expected and does not indicate that the agent outperforms the true optimum: observation noise inflates the maximum of a finite sample. The appropriate comparison is between methods' noisy best values under identical noise conditions, not between noisy observations and the noiseless oracle. The oracle serves only to confirm that the agent is exploring the correct region of factor space.

### Variability

The DOE agent exhibits substantially lower variance across seeds (SD = 0.36) than either baseline (SD ≈ 2.3–2.5). This suggests that the sequential acquisition strategy not only improves mean performance but also reduces run-to-run variability, which is practically important in physical experiments where reproducibility matters. However, this variance reduction may be partly an artifact of the agent converging to a similar region across seeds; further investigation with diverse response surfaces would be needed to confirm generality.

## Limitations

1. **Toy simulation evidence only.** The benchmark is a toy simulation with a known hidden response surface and known deterministic constraints. No physical instrument, lab data, or real experimental logbook was involved. Real physical systems introduce calibration drift, unmodeled constraints, batch effects, and operator error, none of which are captured here. The project decision record classifies this as a "positive viable local prototype" with medium confidence, reflecting this gap.

2. **Known deterministic safety constraints.** The agent relies on hard constraints that are fully specified a priori. In practice, safety boundaries may be uncertain, probabilistic, or discovered only through near-miss events. A production system would need learned probabilistic safety constraints, approval gates, and potentially calibration runs before autonomous operation.

3. **Low-dimensional scope.** The three-factor benchmark is well within the regime where non-sparse GP regression is tractable. Scikit-learn's GP implementation does not scale favorably to high-dimensional or large-data settings. For problems with many factors, dimensionality reduction, factor screening, or sparse/structured kernel approximations would be necessary.

4. **Single benchmark topology.** Only one response surface (with one constraint geometry) was tested. The magnitude of the agent's advantage depends on the degree of curvature, the size of the feasible region, and the noise level. Different topologies could yield smaller or larger advantages.

5. **Modest seed count.** Twenty seeds provide reasonable power for the observed effect sizes, but the confidence intervals on the mean differences are still several tenths of a point wide. Broader replication would tighten these estimates.

6. **No comparison to classical response-surface designs.** The baselines are safe random and LHS-only. A more complete comparison would include central composite or Box-Behnken designs adapted to the safe region, which might perform better than LHS-only for this type of curved response surface. Their absence means we cannot claim the agent is superior to all reasonable alternatives—only to the two baselines tested.

7. **Observation noise inflation.** The agent's noisy best exceeding the clean oracle is a known statistical artifact of taking maxima over noisy observations, but it means that absolute yield values should not be compared to noiseless optima without correction.

8. **Incomplete baseline statistics.** Min and max values for safe random and LHS-only baselines were not recorded in the benchmark summary, limiting the ability to assess the full distributional shape of baseline performance.

9. **Claim audit incomplete.** The claim ledger for this paper contains no completed claim-audit entries. The review checklist (9 items) remains entirely in pending status. The results and interpretations presented here have not undergone independent verification or human expert review.

## Reproducibility Checklist

- **Code availability:** Implementation at `src/doe_agent.py`; benchmark script at `scripts/run_doe_benchmark.py`; tests at `tests/test_doe_agent.py`.
- **Random seeds:** 20 independent seeds; the benchmark script accepts a `--seeds` flag.
- **Hyperparameters:** Budget 20, initial design 6, candidate pool 3,000, Matérn 5/2 kernel with WhiteKernel noise. All configurable via command-line arguments.
- **Environment:** 122 GB available memory, 0 kB swap, Python 3 with scikit-learn. No GPU required.
- **Artifact locations:**
  - Benchmark results: `artifacts/metrics/benchmark_results.csv`
  - Benchmark summary: `artifacts/metrics/benchmark_summary.json`
  - Agent traces: `artifacts/metrics/agent_traces_seed0_2.json`
  - Oracle search: `artifacts/metrics/oracle_safe_search.json`
  - Statistical tests: `artifacts/metrics/stat_tests.json`
  - Test log: `artifacts/logs/pytest.log`
  - Benchmark log (20 seeds): `artifacts/logs/benchmark_20seeds.log`
  - Smoke test log: `artifacts/logs/benchmark_smoke.log`
  - Statistical test log: `artifacts/logs/stat_tests.log`
  - Oracle search log: `artifacts/logs/oracle_safe_search.log`
  - System telemetry: `artifacts/logs/system_telemetry.log`
- **Wall time:** 17.55 seconds for the full 20-seed benchmark.
- **External references consulted:** NIST Engineering Statistics Handbook (sections on experimental design selection and response-surface methods), scikit-learn Gaussian-process documentation. No private data or lab records were used.
- **Claim audit status:** Claim ledger is empty; no claims have been formally audited. Review checklist: 0/9 passed, 9 pending.

## Conclusion

A constrained sequential DOE agent combining safe Latin-hypercube initialization with Gaussian-process expected-improvement acquisition demonstrated a statistically significant advantage over both safe random sampling and one-shot LHS designs in a three-factor noisy reactor-yield toy simulation. Over 20 seeds at a 20-run budget, the agent improved mean best observed yield by approximately 3.1 points over safe random and 4.1 points over LHS-only, with zero unsafe proposals and substantially reduced cross-seed variability.

These results constitute positive but bounded evidence. The agent is viable for low-dimensional physical experiments where hard constraints are known and each run is expensive. However, the gap between this toy-simulation viability result and operational deployment in a real laboratory remains substantial: real systems require learned or uncertain safety constraints, instrument calibration, approval workflows, and validation against actual physical data. We do not claim that this prototype closes that gap.

The most important next step would be integration with a real experimental workflow—connecting the agent's proposal output to an instrument interface, logging results in a physical experiment logbook, and evaluating whether the simulation advantage transfers to measured physical responses. Additionally, comparison against classical response-surface designs and evaluation across multiple benchmark topologies would strengthen the evidence base.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Implementation | `src/doe_agent.py` |
| Benchmark script | `scripts/run_doe_benchmark.py` |
| Tests | `tests/test_doe_agent.py` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T172015860399+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T172015860399+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T172015860399+0000/paper_manifest.json` |
| Benchmark results (CSV) | `artifacts/metrics/benchmark_results.csv` |
| Benchmark summary (JSON) | `artifacts/metrics/benchmark_summary.json` |
| Agent traces | `artifacts/metrics/agent_traces_seed0_2.json` |
| Oracle search results | `artifacts/metrics/oracle_safe_search.json` |
| Statistical test results | `artifacts/metrics/stat_tests.json` |
| Pytest log | `artifacts/logs/pytest.log` |
| Benchmark log (20 seeds) | `artifacts/logs/benchmark_20seeds.log` |
| Smoke test log | `artifacts/logs/benchmark_smoke.log` |
| Statistical test log | `artifacts/logs/stat_tests.log` |
| Oracle search log | `artifacts/logs/oracle_safe_search.log` |
| System telemetry log | `artifacts/logs/system_telemetry.log` |
