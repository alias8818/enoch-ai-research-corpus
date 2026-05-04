# Controller-Integrated Uncertainty Heatmap Ranker

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, experiment logs, and metrics). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated the claims, code, or analysis herein.

---

## Abstract

We investigate a controller-integrated uncertainty heatmap ranker that prioritizes graph actions by composing posterior defect heat, a bounded uncertainty-and-recency bonus, local graph impact, a dependency-gate signal, and inspection cost into a single calibrated scoring cell. Evaluation is conducted in a dependency-free stochastic DAG harness across 1,000 random seeds and four ranking policies (heatmap, risk-only, impact-only, random) under a fixed action budget of 18. The heatmap ranker achieves a mean utility recall of 0.4147 (SD 0.1294), compared to 0.3140 (SD 0.1234) for the strongest baseline (risk-only). The paired utility-recall delta against risk-only is +0.1007 (95% CI half-width ±0.0079, win rate 0.767, tie rate 0.043). Discounted utility shows a mean paired delta of +1.176 (95% CI half-width ±0.115, win rate 0.755). An earlier variant using unbounded recursive downstream blast radius was rejected during smoke calibration because it over-selected early low-risk root nodes. All results are synthetic and local; no production controller traces were used, and production validation remains an open requirement.

## Introduction

Autonomous controllers operating over directed acyclic graphs (DAGs) of actions face a recurring allocation problem: given a bounded action budget, which nodes should be inspected or re-executed first? Single-dimension heuristics—ranking by posterior risk alone, by local impact alone, or by downstream descendant count—each capture part of the decision surface but leave utility unrecovered in scenarios where the optimal action depends on the interaction of multiple signals.

This work examines whether a composite scoring cell that integrates five signals can improve utility-weighted defect and action discovery over single-signal baselines. The proposed heat cell combines:

1. **Posterior defect heat** — the controller's current belief that a node is defective.
2. **Bounded uncertainty and recency bonus** — a capped additive term reflecting epistemic uncertainty and recency of evaluation, bounded to prevent domination by high-uncertainty nodes.
3. **Local action impact** — the immediate graph-level consequence of acting on the node.
4. **Dependency-gate signal** — a binary or graded indicator of whether upstream dependencies have resolved favorably.
5. **Inspection cost** — a divisor normalizing by the resource expenditure of acting.

The composite formula is:

```
heat = (posterior_risk + bounded_uncertainty_recency_bonus) × local_impact × dependency_gate / cost
```

A prior variant using raw recursive downstream blast radius (unbounded descendant weighting) was tested and rejected during smoke calibration. It systematically over-selected early low-risk root nodes with large descendant counts, reducing utility recall below the risk-only baseline. This failure mode is documented in the calibration artifacts and informs the design decision to bound the uncertainty/recency contribution and use local rather than recursive impact.

The central claim under test is: *a controller-integrated uncertainty heatmap ranker is viable in a local stochastic-DAG harness, improving utility-weighted defect/action discovery over random, risk-only, and impact-only rankers under equal action budget.*

## Method

### Stochastic DAG Harness

The evaluation uses a dependency-free stochastic DAG harness implemented in `src/uncertainty_heatmap_ranker.py`. The harness generates random DAGs with stochastic node defect probabilities. Each scenario presents a set of candidate actions (nodes) with associated costs, posterior risk estimates, uncertainty values, recency indicators, local impact scores, dependency-gate signals, and utility weights. The harness has no external dependencies beyond the Python standard library.

### Ranking Policies

Four deterministic ranking policies are compared under identical action budgets:

- **Heatmap** — the proposed composite cell: `(posterior_risk + bounded_uncertainty_recency_bonus) × local_impact × dependency_gate / cost`.
- **Risk-only** — ranks solely by posterior defect risk, divided by cost.
- **Impact-only** — ranks solely by local action impact, divided by cost.
- **Random** — uniform random selection without replacement.

All policies consume actions greedily in rank order until the budget is exhausted. Within a given seed, all four policies operate on the identical DAG instance, enabling paired comparisons.

### Metrics

- **Utility recall** — the fraction of total utility (weighted by defect severity) recovered by the selected actions within budget. This is the primary metric.
- **Discounted utility** — utility weighted by a temporal discount factor favoring earlier defect discovery.
- **Precision at budget** — fraction of selected actions that target true defects.
- **First defect step** — the rank position at which the first true defect is discovered.
- **Cost** — total inspection cost consumed within budget.

### Calibration Procedure

A staged calibration was conducted before the final experiment:

1. **Smoke run** — 5 seeds, budget 12. Identified the failure mode of the unbounded downstream-impact variant.
2. **Calibration 50** — 50 seeds, budget 18. Confirmed the failure mode persisted at moderate scale.
3. **Calibration 100** — 100 seeds, budget 18. Validated the bounded local-impact formulation.

The unbounded recursive downstream-impact variant was rejected based on the smoke and 50-seed calibration results. All subsequent runs, including the final experiment, use the calibrated bounded heat cell.

### Final Experiment

The final experiment runs 1,000 seeds with budget 18, yielding 4,000 total policy runs (1,000 per policy). Paired comparisons are computed seed-by-seed to control for DAG structure variability. Confidence intervals are computed as ±1.96 × (standard deviation of paired deltas / √1000).

## Results

### Summary Statistics

| Policy | Mean Utility Recall | SD | Mean Discounted Utility | SD | Mean Precision@Budget | SD | Mean First Defect Step | Mean Cost | SD Cost |
|---|---|---|---|---|---|---|---|---|---|
| Heatmap | 0.4147 | 0.1294 | 3.9972 | 2.4737 | 0.2679 | 0.1060 | 3.513 | 25.48 | 1.964 |
| Risk-only | 0.3140 | 0.1234 | 2.8213 | 1.9120 | 0.2304 | 0.1014 | 4.092 | 20.69 | 1.255 |
| Impact-only | 0.2057 | 0.1004 | 1.3959 | 1.0328 | 0.1824 | 0.0934 | 6.116 | 26.54 | 2.067 |
| Random | 0.2998 | 0.1184 | 2.5618 | 1.7502 | 0.2223 | 0.0967 | 4.411 | 30.77 | 2.072 |

The heatmap ranker achieves the highest mean utility recall and mean discounted utility among all policies. It also discovers the first defect earliest (mean step 3.513) and achieves the highest precision at budget (0.2679). However, the heatmap ranker incurs a higher mean cost (25.48) than risk-only (20.69), reflecting its willingness to spend budget on higher-cost actions when the composite signal justifies it. Impact-only, despite spending comparable cost (26.54), achieves substantially lower utility recall (0.2057), indicating that cost alone does not explain the heatmap's advantage.

### Paired Comparisons

**Utility recall deltas (heatmap minus baseline), 1,000 paired seeds:**

| Baseline | Mean Δ | SD Δ | 95% CI Half-Width | Win Rate | Tie Rate |
|---|---|---|---|---|---|
| Risk-only | +0.1007 | 0.1267 | 0.0079 | 0.767 | 0.043 |
| Random | +0.1149 | 0.1730 | 0.0107 | 0.750 | 0.002 |
| Impact-only | +0.2090 | 0.1699 | 0.0105 | 0.906 | 0.001 |

**Discounted utility deltas (heatmap minus baseline), 1,000 paired seeds:**

| Baseline | Mean Δ | SD Δ | 95% CI Half-Width | Win Rate | Tie Rate |
|---|---|---|---|---|---|
| Risk-only | +1.1759 | 1.8543 | 0.1149 | 0.755 | 0.000 |
| Random | +1.4354 | 2.7575 | 0.1709 | 0.694 | 0.000 |
| Impact-only | +2.6013 | 2.5578 | 0.1585 | 0.857 | 0.000 |

All paired 95% confidence intervals for utility recall exclude zero, supporting the claim that the heatmap ranker outperforms each baseline on this metric in the synthetic harness. The win rate against risk-only on utility recall is 0.767, with a non-trivial tie rate of 0.043 (cases where both policies recover identical utility fractions, likely in scenarios with few defects or trivial DAG structure). Against impact-only, the win rate rises to 0.906.

On discounted utility, the heatmap ranker also outperforms all baselines, though the confidence intervals are wider and the win rate against random (0.694) is lower than against risk-only (0.755), reflecting the higher variance of discounted-utility deltas.

### Throughput

The harness processed 4,000 runs in approximately 2.56 seconds, yielding 1,564.4 runs per second on the test machine (20 CPUs, Python 3.12.3, ~122 GB available RAM, no swap). This throughput is a property of the lightweight synthetic harness and should not be interpreted as indicative of production controller performance.

### Calibration Rejection of Unbounded Downstream Impact

The unbounded downstream-impact variant (raw recursive descendant weighting) was rejected during smoke and early calibration runs. It over-selected early low-risk root nodes that had large descendant counts but low posterior risk, reducing utility recall below the risk-only baseline. This failure mode is documented in `results/smoke/` and `results/calibration_50/`. The rejection was made on the basis of smoke (5 seeds) and 50-seed calibration; a more thorough characterization of this variant's failure modes under diverse graph topologies was not performed.

## Limitations

1. **Synthetic harness only.** All evidence derives from a local stochastic DAG harness with randomly generated graphs. No real controller traces, production telemetry, or LangGraph hard-cutover histories were used. The DAG structures, defect distributions, and cost models may not reflect production conditions. The results should be interpreted as evidence of viability in this specific harness, not as evidence of production readiness.

2. **No counterfactual production validation.** Production closure requires connecting the rank interface to real controller histories and measuring whether the heatmap ranker would have selected higher-utility actions than the policies actually deployed. This has not been done.

3. **Bounded uncertainty bonus is heuristic.** The recency and uncertainty bonus is capped to prevent domination by high-uncertainty nodes. The cap value was set during calibration on synthetic data and may not transfer to production distributions.

4. **Cost model simplicity.** Inspection costs are drawn from the harness distribution and may not reflect the heterogeneous cost structures of real controller actions (e.g., API calls, model inference, human review).

5. **No temporal belief updating within a scenario.** The ranker is stateless across steps within a scenario; it does not update beliefs based on intermediate observations during budget consumption. A production controller would likely incorporate observation feedback.

6. **Rejected variant not fully characterized.** The raw downstream-impact variant was rejected based on smoke (5 seeds) and 50-seed calibration. A more thorough characterization of its failure modes under diverse graph topologies and budget levels was not performed. The possibility remains that it could outperform the bounded variant under specific graph structures not represented in the calibration seeds.

7. **Single budget level.** All final comparisons use budget 18. Sensitivity to budget level was not systematically evaluated. Performance at very low or very high budgets may differ.

8. **No comparison to learned or adaptive policies.** The baselines are simple heuristic rankers. The heatmap ranker was not compared against learned ranking models, Thompson sampling, or other adaptive strategies that might outperform all four fixed policies.

9. **Tie rate interpretation.** The 4.3% tie rate between heatmap and risk-only on utility recall indicates a non-negligible fraction of scenarios where the composite signal provides no advantage. Characterizing these scenarios (e.g., low-defect DAGs, trivial topology) was not performed.

## Reproducibility Checklist

- **Source code:** `src/uncertainty_heatmap_ranker.py` — dependency-free stochastic DAG harness and all four ranking policies.
- **Test suite:** `tests/test_uncertainty_heatmap_ranker.py` — determinism, ranker, policy-budget, and summary tests.
- **Random seeds:** 1,000 seeds in the final run; 5, 50, and 100 in calibration runs. Seeds are generated deterministically within the harness.
- **Environment:** Python 3.12.3; 20 CPUs; MemTotal 127,535,908 kB; MemAvailable 122,544,340 kB; SwapTotal 0 kB; no external dependencies beyond the Python standard library.
- **Command to reproduce final run:** `python src/uncertainty_heatmap_ranker.py --seeds 1000 --budget 18 --outdir results/final_1000`
- **Expected output files:** `results/final_1000/summary.json`, `results/final_1000/policy_runs.csv`, `results/final_1000/sample_traces.json`.
- **Verification:** `python -m unittest discover -s tests` passes before and after calibration and final runs (test logs attest to this).
- **Throughput reference:** approximately 1,564 runs/sec on the described hardware; substantial deviation may indicate environmental differences.
- **Calibration runs reproducible:** `python src/uncertainty_heatmap_ranker.py --seeds 5 --budget 12 --outdir results/smoke`, `python src/uncertainty_heatmap_ranker.py --seeds 50 --budget 18 --outdir results/calibration_50`, `python src/uncertainty_heatmap_ranker.py --seeds 100 --budget 18 --outdir results/calibration_100`.

## Conclusion

A controller-integrated uncertainty heatmap ranker that composes posterior risk, bounded uncertainty/recency, local impact, dependency-gate signals, and cost into a single calibrated cell outperforms risk-only, impact-only, and random baselines on utility recall and discounted utility in a stochastic DAG harness. The primary result is a paired utility-recall delta of +0.101 against the strongest baseline (risk-only), with a 95% confidence interval half-width of ±0.008 and a win rate of 76.7% across 1,000 seeds. An unbounded downstream-impact variant was rejected during calibration for over-selecting low-risk roots.

These results support the viability of composite multi-signal ranking for controller-side action prioritization in synthetic settings. However, the evidence is entirely local and synthetic. The heatmap ranker incurs higher mean cost than risk-only, and a non-trivial fraction of scenarios (4.3%) yield ties where the composite signal provides no advantage. Whether the heatmap ranker improves action quality on real controller histories with production graph structures, cost distributions, and defect regimes remains an open question requiring replay against private production traces.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Harness source | `src/uncertainty_heatmap_ranker.py` |
| Test suite | `tests/test_uncertainty_heatmap_ranker.py` |
| Final summary | `results/final_1000/summary.json` |
| Final per-run data | `results/final_1000/policy_runs.csv` |
| Sample controller traces | `results/final_1000/sample_traces.json` |
| Research metrics mirror | `results/research_metrics.json` |
| Project decision | `.omx/project_decision.json` |
| Smoke run results | `results/smoke/` |
| 50-seed calibration results | `results/calibration_50/` |
| 100-seed calibration results | `results/calibration_100/` |
| Smoke experiment log | `logs/experiment_smoke_20260501T103155Z.log` |
| Calibration 50 log | `logs/experiment_calibration_50_20260501T103210Z.log` |
| Calibration 100 log | `logs/experiment_calibration_100_20260501T103220Z.log` |
| Final experiment log | `logs/experiment_final_1000_20260501T103251Z.log` |
| Telemetry log | `logs/telemetry_smoke_20260501T103155Z.log` |
| Test log (smoke) | `logs/test_smoke_20260501T103155Z.log` |
| Test log (after calibration 50) | `logs/test_after_calibration_20260501T103210Z.log` |
| Test log (after recalibration 100) | `logs/test_after_recalibration_20260501T103220Z.log` |
| Test log (final) | `logs/test_final_20260501T103251Z.log` |
| Claim ledger | `papers/source-record-redacted-20260501T103015653722+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T103015653722+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T103015653722+0000/paper_manifest.json` |
