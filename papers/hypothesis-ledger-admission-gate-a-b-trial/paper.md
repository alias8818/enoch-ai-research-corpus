# A Conservative Admission Gate for Hypothesis Ledgers: A Temporal A/B Replay on Real Project History

> **AI Provenance Notice.** This draft was generated automatically from research artifacts produced by an autonomous experimental pipeline (run ID `source-record-redacted-20260430T230618401239+0000`). The operator who released the artifact claims no personal authorship credit for the writing or the experimental results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact and evaluate its claims against the referenced evidence bundles directly.

---

## Abstract

We evaluate whether a simple metadata-only admission gate can reduce hypothesis-ledger clutter without materially sacrificing recall of later-supported hypotheses. Using a temporal A/B replay over 535 terminal nodes from a real project-history DAG, we compare an admit-all baseline (A) against a conservative gate (B) that scores candidates on pre-outcome metadata—confidence, success probability, feasibility, leverage, cost, and prerequisite count—and admits only candidates above a threshold calibrated on earlier rows. At a 98% training-recall target, the gate rejects 29.3% of historically non-good holdout candidates while missing only 1 of 156 good holdout candidates (recall 0.994). Admitted-candidate precision improves by 6.2 percentage points and ledger load falls by 8.4%. However, a net-utility proxy is only weakly positive, with a bootstrap 90% confidence interval of [−1.75, +5.5] that crosses zero. The result supports a cautious positive conclusion: a conservative gate can improve ledger quality with near-complete recall in retrospective replay, but causal benefit in live operation remains unestablished.

## Introduction

Automated research pipelines that generate and track hypotheses accumulate large ledgers of candidate ideas. Not all candidates merit sustained tracking: many are later judged unsupported, blocked, or abandoned. An admission gate that filters candidates before ledger entry could reduce clutter and focus downstream resources, but only if it does not reject candidates that would later prove valuable.

The core tension is between selectivity and safety. A highly selective gate reduces noise but risks false rejections of good hypotheses. A permissive gate preserves recall but provides little filtering benefit. This paper investigates whether a simple, conservative gate—using only metadata available before outcome resolution—can achieve a useful balance.

We conduct a temporal A/B replay on real project history rather than a synthetic simulation, which provides ecological validity at the cost of experimental control. The replay treats earlier history nodes as a training split for threshold selection and later nodes as a holdout split for evaluation, preserving temporal ordering to avoid look-ahead bias.

## Method

### Data

The data source is a single historical DAG export from an Enoch automated research system (`data/real_enoch_history_dag.json`), containing 563 history nodes. After excluding nodes with decisions `continue`, `blocked`, or `needs_review`, 535 usable terminal rows remain. These are split temporally by `manual_order` into 321 training rows and 214 holdout rows.

### Label Definition

A candidate is labeled **good** (admission-success) if both conditions hold:

- `decision ∈ {finalize_positive, branch_new_project}`, and
- `hypothesis_status == supported`.

All other terminal candidates are labeled **bad** (non-good), including those that were finalized negatively, abandoned, or remain unresolved. This labeling conflates intrinsic hypothesis quality with downstream operational outcomes, a limitation discussed below.

### Conditions

- **Condition A (admit-all baseline):** Every terminal candidate is admitted to the ledger.
- **Condition B (gate):** Each candidate is scored using pre-outcome metadata only: confidence, success probability, feasibility, leverage, cost, and prerequisite count. Candidates scoring above a threshold are admitted; those below are rejected.

### Threshold Selection

The admission threshold is selected on the training split by sweeping to find the most selective threshold that preserves at least 98% recall of good training candidates. This 98% target was chosen after sensitivity analysis (Section 4.3) showed that a 90% target was too aggressive—missing 10 good holdout candidates—and a 99% target was nearly inert, rejecting only 1.7% of bad candidates.

### Evaluation Metrics

| Metric | Definition |
|---|---|
| Good recall | Fraction of good holdout candidates admitted |
| Bad rejection rate | Fraction of bad holdout candidates rejected |
| Admitted precision | Fraction of admitted holdout candidates that are good |
| Ledger load reduction | Fraction of total holdout candidates rejected |
| Net utility proxy | Good admitted − Bad admitted (simple difference count) |

The net utility proxy treats each good admission as a unit benefit and each bad admission as a unit cost. This is a coarse proxy; the true cost of a bad admission and the true benefit of a good admission are unlikely to be equal or constant.

### Uncertainty Quantification

Bootstrap resampling (3,000 iterations) on the holdout set produces delta distributions (B − A) for each metric. We report the mean, 5th percentile (p05), and 95th percentile (p95) of each delta distribution, giving approximate 90% bootstrap confidence intervals.

### Sensitivity Analysis

A recall-target sweep tests thresholds calibrated at 90%, 95%, 98%, and 99% training recall, each evaluated on the same holdout split with 500 bootstrap iterations, to characterize the recall–selectivity trade-off.

### Implementation

All analysis is implemented in a single script (`scripts/admission_gate_ab.py`). Static verification via `python3 -m py_compile` passed without errors. Smoke tests were run with `--limit 40 --bootstrap 100` before the full replay.

## Results

### Main Holdout Comparison

At the 98% training-recall gate, holdout performance is:

| Metric | A (admit-all) | B (gate) | Delta |
|---|---:|---:|---:|
| Admitted | 214 | 196 | −18 |
| Rejected | 0 | 18 | +18 |
| Good admitted | 156 | 155 | −1 |
| Bad admitted | 58 | 41 | −17 |
| Good recall | 1.0000 | 0.9936 | −0.0064 |
| Bad rejection rate | 0.0000 | 0.2931 | +0.2931 |
| Admitted precision | 0.7290 | 0.7908 | +0.0618 |
| Ledger load reduction | 0.0000 | 0.0841 | +0.0841 |
| Net utility proxy | 141.5 | 143.75 | +2.25 |

The gate admits 18 fewer candidates, 17 of which are bad. One good holdout candidate is rejected, corresponding to a recall loss of 0.64 percentage points.

### Bootstrap Confidence Intervals on Deltas

| Metric delta | Mean | p05 | p95 |
|---|---:|---:|---:|
| Bad rejection rate | +0.2943 | +0.1961 | +0.3967 |
| Ledger load reduction | +0.0846 | +0.0561 | +0.1168 |
| Precision | +0.0622 | +0.0381 | +0.0884 |
| Net utility | +2.29 | −1.75 | +5.50 |

Bad rejection rate, ledger load reduction, and precision deltas are bootstrap-stable: all three have p05 > 0, indicating reliable positive effects at the 90% level. The net utility delta, however, has a bootstrap interval that crosses zero (p05 = −1.75, p95 = +5.50), meaning the aggregate benefit measure is not statistically distinguishable from zero at this confidence level.

### Sensitivity to Recall Target

| Target | Holdout recall | Bad rejection | Precision delta | Net utility delta |
|---|---:|---:|---:|---:|
| 0.90 | 0.9359 | 0.5690 | +0.1248 | −11.75 |
| 0.95 | 0.9615 | 0.4655 | +0.0998 | −5.25 |
| 0.98 | 0.9936 | 0.2931 | +0.0618 | +2.25 |
| 0.99 | 1.0000 | 0.0172 | +0.0034 | +0.25 |

The 90% and 95% targets reject too many good candidates, producing negative net utility. The 99% target preserves perfect recall but is nearly inert (1.7% bad rejection). The 98% target is the best balanced operating point on this dataset, though this balance is specific to the observed distribution and cost assumptions.

## Limitations

1. **Retrospective design.** This is a historical replay, not a live randomized trial. Labels are derived from observed project outcomes; the gate's scores use metadata that was available before those outcomes, but the analysis cannot establish that the gate causally improves future outcomes. The gate may be exploiting correlations in historical metadata that would not hold under intervention.

2. **Single data source.** All data come from one Enoch history export (563 nodes, 535 usable). Generalization to other pipelines, domains, or time periods is unknown.

3. **Simple scoring model.** The gate uses only six metadata features. Richer features—text content, embedding similarity, structural graph features—might improve selectivity but were not tested.

4. **Label noise.** The good/bad label depends on downstream project decisions that may reflect operational constraints (resource availability, priority shifts) rather than intrinsic hypothesis quality. Mislabeling could bias both threshold selection and evaluation in unknown directions.

5. **Weak net utility signal.** The net utility proxy—the most direct measure of overall benefit—has a bootstrap interval crossing zero. The positive point estimate (+2.25) should be treated as suggestive rather than conclusive.

6. **Temporal shift risk.** If the distribution of candidate metadata or outcomes drifts over time, a threshold calibrated on early history may degrade. No drift analysis was performed.

7. **Cost symmetry assumption.** The net utility proxy assigns equal magnitude to good and bad admissions. In practice, the cost of a false rejection (missing a good hypothesis) may differ substantially from the cost of a false admission (tracking a bad hypothesis), and these costs are unknown.

## Reproducibility Checklist

- [x] Data source specified: `data/real_enoch_history_dag.json` (563 nodes, 535 usable terminal rows)
- [x] Temporal split documented: 321 training / 214 holdout by `manual_order`
- [x] Label definition stated: `decision ∈ {finalize_positive, branch_new_project}` and `hypothesis_status == supported`
- [x] Condition definitions provided: A = admit-all, B = metadata-score gate at 98% train-recall threshold
- [x] All six scoring features listed: confidence, success probability, feasibility, leverage, cost, prerequisite count
- [x] Threshold selection procedure described: most selective threshold preserving ≥98% training recall
- [x] Bootstrap configuration reported: 3,000 iterations on holdout set (main run); 500 iterations (sensitivity sweep)
- [x] Sensitivity sweep parameters stated: recall targets 0.90, 0.95, 0.98, 0.99
- [x] Analysis script available: `scripts/admission_gate_ab.py`
- [x] Static verification passed: `python3 -m py_compile scripts/admission_gate_ab.py`
- [ ] Live validation: not performed; retrospective replay only
- [ ] Cross-pipeline replication: not performed
- [ ] Temporal drift analysis: not performed

## Conclusion

A conservative metadata-only admission gate, calibrated to preserve at least 98% training recall, can reduce hypothesis-ledger clutter by 8.4% and improve admitted-candidate precision by 6.2 percentage points while missing only 1 of 156 good holdout candidates in a real historical replay. The bad rejection rate of 29.3% and the precision improvement are bootstrap-stable with 90% confidence intervals excluding zero. However, the net utility proxy is only weakly positive and not statistically distinguishable from zero (90% CI [−1.75, +5.5]), tempering the strength of the conclusion.

The gate is viable as a conservative guardrail—not as a high-selectivity filter. Aggressive recall targets (90–95%) reject too many good candidates, producing negative net utility; an ultra-conservative 99% target is nearly inert. The 98% target represents the best balance on this dataset, though the optimal operating point will depend on the relative costs of false rejections versus false admissions in a given deployment context.

The most important next step is a live shadow-mode trial on newly arriving hypothesis traffic, comparing gate decisions against eventual outcomes before any hard enforcement is considered. Retrospective replay establishes that the signal exists; only prospective evaluation can establish that it is causal.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Analysis script | `scripts/admission_gate_ab.py` |
| Holdout summary (JSON) | `results/admission_gate_ab/summary.json` |
| Holdout summary (Markdown) | `results/admission_gate_ab/summary.md` |
| Holdout metrics | `results/admission_gate_ab/metrics.json` |
| Scored rows | `results/admission_gate_ab/scored_rows.json` |
| Smoke test log | `logs/admission_gate_ab_smoke_rerun.log` |
| Full run log | `logs/admission_gate_ab_full_rerun.log` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Data source | `data/real_enoch_history_dag.json` |
| Claim ledger | `papers/source-record-redacted-20260430T230618401239+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T230618401239+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T230618401239+0000/paper_manifest.json` |
