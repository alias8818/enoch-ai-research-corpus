# Trajectory Rulebook Distillation: Interpretable Decision Rules from Historical Controller Outcomes

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate whether historical controller trajectory outcomes can be distilled into a compact, interpretable rulebook that predicts or explains controller decisions. Using a directed acyclic graph of 563 historical project nodes with 224 edge-evidence records from the Enoch controller system, we train shallow decision trees across four feature regimes of increasing information richness: metadata-only, pre-evidence without success probability, controller-prior (including upstream success probability), and post-evidence audit. Cold-start feature regimes (metadata-only, pre-evidence) fail to exceed the majority-class baseline on accuracy and achieve only marginal macro-F1 improvement. The controller-prior regime achieves 50.3% accuracy and 0.389 macro-F1, compared to the majority baseline of 31.4% accuracy and 0.080 macro-F1. Adding post-evidence audit features yields no additional gain. Distilled single-feature rules achieve perfect precision on extreme success-probability regions (≤0.12 → finalize_negative, >0.92 → finalize_positive), covering 54.7% of nodes. However, these rules depend on an upstream success-probability estimate that itself encodes prior judgment. We conclude that trajectory rulebook distillation is viable as an explanation and audit layer when controller-prior signals are available, but is not supported as a cold-start replacement for evidence collection.

## Introduction

Automated controller systems accumulate trajectory histories that encode implicit decision policies. Making these policies explicit—distilling them into interpretable rules—could serve auditing, standardization, or cold-start prediction for new projects before evidence is collected.

This work examines a concrete instance of this problem using the Enoch controller system's historical trajectory data. The central question is whether a compact rulebook can be extracted that is both interpretable and predictive. The answer is conditional: interpretability and predictive power are achievable when upstream controller-prior signals (notably a success-probability estimate) are available, but the rulebook does not function as an independent cold-start predictor from project metadata alone.

We evaluate four feature regimes of increasing information richness, use shallow decision trees and single-rule precision scans as interpretable models, and compare against a majority-class baseline. We report both positive and negative findings with equal care.

## Method

### Data

The dataset is a historical directed acyclic graph (DAG) of Enoch controller decisions, sourced from a local artifact (`real_enoch_history_dag.json`). The graph contains 563 nodes and 224 edge-evidence rows. Each node carries a decision label from six classes:

| Label | Count |
|---|---:|
| `branch_new_project` | 209 |
| `finalize_positive` | 203 |
| `finalize_negative` | 123 |
| `continue` | 21 |
| `needs_review` | 6 |
| `blocked` | 1 |

The label distribution is heavily imbalanced. The `blocked` and `needs_review` classes contain 1 and 6 examples respectively, rendering reliable rule learning for these classes infeasible with this sample size.

### Train-Test Split

A chronological split was used: the first 70% of nodes ordered by `manual_order` formed the training set, and the remaining 30% formed the test set. This respects temporal ordering and avoids leaking future information into training. No random seed was specified; decision tree training may exhibit minor stochastic variation across runs.

### Feature Regimes

Four feature sets were defined, each a strict superset of the previous:

1. **metadata_only**: Project title, category, graph structure, and time metadata.
2. **pre_without_success_prior**: All metadata features plus feasibility, leverage, and cost scores, excluding success-probability and post-evidence fields.
3. **controller_prior**: All pre-evidence features plus the upstream `success_prob` field.
4. **post_evidence_audit**: All controller-prior features plus confidence, hypothesis status, and evidence audit fields.

This design isolates the marginal contribution of success probability and post-evidence signals.

### Models

- **Baseline**: Majority-class dummy classifier (predicts the most frequent class in training) evaluated on the same chronological split.
- **Interpretable model**: Balanced shallow decision tree with `max_depth=4` and `min_samples_leaf=12`, trained with class-weight balancing to partially compensate for label imbalance.
- **Single-rule lift/precision scan**: Exhaustive scan over single-feature threshold rules, reporting precision and coverage on the full dataset.

### Implementation

All analysis was performed using a single Python script (`scripts/distill_rulebook.py`). A smoke test with `--limit 80` was run first to validate the pipeline, followed by a full run over all 563 nodes. This constitutes a CPU-bound tabular analysis prototype; no GPU, CUDA calibration, or production deployment was involved. Both runs completed in approximately 0.09 seconds on CPU with negligible memory footprint (system memory remained at approximately 122 GB throughout, with no measurable change).

## Results

### Classification Performance

| Feature Set | Accuracy | Macro-F1 | Majority Acc. | Majority Macro-F1 |
|---|---:|---:|---:|---:|
| metadata_only | 0.189 | 0.110 | 0.314 | 0.080 |
| pre_without_success_prior | 0.284 | 0.140 | 0.314 | 0.080 |
| controller_prior | 0.503 | 0.389 | 0.314 | 0.080 |
| post_evidence_audit | 0.503 | 0.389 | 0.314 | 0.080 |

**Cold-start regimes fail on accuracy.** Both `metadata_only` and `pre_without_success_prior` fall below the majority-class baseline on accuracy (0.189 and 0.284 vs. 0.314). The `metadata_only` regime slightly exceeds the baseline on macro-F1 (0.110 vs. 0.080), and `pre_without_success_prior` improves macro-F1 further (0.140 vs. 0.080), but these gains are modest and come at the cost of worse accuracy—indicating that the model is spreading predictions across classes more evenly but incorrectly.

**Controller-prior regime is viable.** The inclusion of `success_prob` produces a substantial jump: accuracy rises to 0.503 and macro-F1 to 0.389, both well above the baseline. This confirms that the upstream success-probability estimate carries significant discriminative information for the decision label.

**Post-evidence audit adds no gain.** The `post_evidence_audit` regime achieves identical metrics to `controller_prior` (0.503 accuracy, 0.389 macro-F1). In this dataset, confidence, hypothesis status, and evidence audit fields provide no additional predictive value beyond what `success_prob` already encodes.

### Distilled Rules

The single-rule precision scan identified the following high-precision rules:

| Rule | Prediction | Precision | Coverage |
|---|---|---:|---:|
| `success_prob ≤ 0.12` | `finalize_negative` | 1.00 | 113/563 |
| `success_prob > 0.92` | `finalize_positive` | 1.00 | 195/563 |
| `out_degree > 0` | `branch_new_project` | 0.59 | 222/563 |
| `hypothesis_status == unsupported` | `finalize_negative` | 0.94 | 104/563 |

The first two rules cover 308 of 563 nodes (54.7%) with perfect precision, cleanly partitioning the extreme tails of the success-probability distribution. The `out_degree` rule for `branch_new_project` is weaker (precision 0.59) and reflects the structural tendency of projects with downstream children to spawn branches. The audit-only rule on `hypothesis_status` achieves high precision (0.94) but is largely redundant with the `success_prob` rule in most cases.

### Decision Tree Structure

Extracted tree rules were saved for all four feature regimes. The `controller_prior` tree uses `success_prob` as the primary split, with secondary splits on graph-structural features (notably `out_degree`). The `metadata_only` and `pre_without_success_prior` trees show fragmented, low-confidence splits that do not generalize meaningfully—consistent with their poor test metrics.

## Limitations

1. **`success_prob` is not independent evidence.** The strongest rules depend on an upstream success-probability estimate that itself encodes prior human or model judgment. These rules are useful for auditing whether the controller's final decisions are consistent with its own prior, but they should not be treated as independent scientific discovery about what makes projects succeed.

2. **Cold-start prediction is not supported.** Feature regimes that exclude `success_prob` fail to beat the majority-class baseline on accuracy and achieve only marginal macro-F1 improvement. Project title, category, graph structure, and pre-evidence scores are insufficient for reliable prediction.

3. **Rare labels are underpowered.** The `blocked` (1 example) and `needs_review` (6 examples) classes have too few instances for any rule-learning approach to produce reliable rules. Even the `continue` class (21 examples) is marginal.

4. **Temporal drift is unmodeled.** The chronological split evaluates performance on the most recent 30% of decisions, but no explicit drift model was fit. If the controller's decision policy has shifted over time, the rules may be stale for future decisions.

5. **No prospective validation.** All results are retrospective. The rules have not been tested on decisions made after the study period.

6. **Notion source text was unavailable.** The original Notion page for this project was not available as a local artifact. If it contains a stricter or different intended hypothesis, these results should be reconciled against it.

7. **Single system, single dataset.** All data comes from one controller system (Enoch). Generalization to other controller systems or domains is unknown.

8. **No random seed recorded.** Minor stochastic variation in decision tree training is possible across runs, though the overall pattern of results is expected to be stable given the sample size and the dominance of the `success_prob` feature.

## Reproducibility Checklist

- **Data source**: `../source-record-redacted/data/real_enoch_history_dag.json` (563 nodes, 224 edge-evidence rows)
- **Analysis script**: `scripts/distill_rulebook.py`
- **Smoke test command**: `python scripts/distill_rulebook.py --limit 80 --outdir results/smoke`
- **Full run command**: `python scripts/distill_rulebook.py --outdir results/full`
- **Full run metrics**: `results/full/metrics.json`
- **Full run rulebook**: `results/full/rulebook.md`
- **Extracted tree rules**: `results/full/metadata_only_tree_rules.txt`, `results/full/pre_without_success_prior_tree_rules.txt`, `results/full/controller_prior_tree_rules.txt`, `results/full/post_evidence_audit_tree_rules.txt`
- **Smoke test metrics**: `results/smoke/metrics.json`
- **Smoke test rulebook**: `results/smoke/rulebook.md`
- **Logs**: `logs/smoke_distill.log`, `logs/full_distill.log`
- **Run notes**: `run_notes.md`
- **Project decision**: `.omx/project_decision.json`
- **Validation checks performed**: `python -m py_compile scripts/distill_rulebook.py` (passed); `python -m json.tool results/full/metrics.json` (passed); `python -m json.tool .omx/project_decision.json` (passed)
- **Hardware**: CPU-only; no GPU required. Runtime: ~0.09 seconds for full run. Memory: negligible (~122 GB available, no measurable change)
- **Random seed**: Not specified in run notes; decision tree training may have minor stochastic variation
- **Split**: Chronological 70/30 by `manual_order` field
- **Experiment classification**: CPU-bound tabular analysis prototype; not a CUDA calibration or production validation

## Conclusion

Trajectory rulebook distillation from historical controller outcomes produces interpretable, high-precision rules when an upstream success-probability estimate is available. The rules `success_prob ≤ 0.12 → finalize_negative` and `success_prob > 0.92 → finalize_positive` achieve perfect precision and cover over half the dataset. However, these rules audit consistency between prior and decision rather than providing independent predictive signal.

Without `success_prob`, no feature regime exceeds the majority-class baseline on accuracy, and macro-F1 improvements are marginal. Post-evidence audit features add no predictive value beyond what `success_prob` already encodes in this dataset.

The appropriate role for a distilled trajectory rulebook is as an explanation and standardization layer—a checklist that confirms whether final decisions are consistent with the controller's own prior assessments. It is not supported as a cold-start autonomous decision controller. Deploying these rules prospectively would require richer trajectory features, explicit temporal drift modeling, and validation on out-of-sample decisions.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Analysis script | `scripts/distill_rulebook.py` |
| Full run metrics | `results/full/metrics.json` |
| Full run rulebook | `results/full/rulebook.md` |
| Metadata-only tree rules | `results/full/metadata_only_tree_rules.txt` |
| Pre-without-success-prior tree rules | `results/full/pre_without_success_prior_tree_rules.txt` |
| Controller-prior tree rules | `results/full/controller_prior_tree_rules.txt` |
| Post-evidence audit tree rules | `results/full/post_evidence_audit_tree_rules.txt` |
| Smoke test metrics | `results/smoke/metrics.json` |
| Smoke test rulebook | `results/smoke/rulebook.md` |
| Smoke test log | `logs/smoke_distill.log` |
| Full run log | `logs/full_distill.log` |
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Source data DAG | `../source-record-redacted/data/real_enoch_history_dag.json` |
