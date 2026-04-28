# Draft-Value Router: Supervised Three-Arm Routing Over Draft Utility Observables

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We investigate whether a lightweight supervised router, operating only on pre-decision observables (task class, model family, prompt/draft surface cues), can select among three draft-handling arms—direct solve, scaffold-only reuse, and full revision—to reduce average inference cost while maintaining or improving accuracy. A Naive Bayes router is trained on outcome-derived labels from paired draft-utility atlas data and evaluated on task-id-held-out splits. On a 128-case real-trace benchmark with observed scaffold-only completions, the learned router achieves 0.1750 accuracy at 1.1138 average cost, compared to 0.1000 at 2.0000 for always-full-revision and 0.0500 at 1.0000 for always-direct, yielding a cost reduction of approximately 44% versus full revision at equal-or-better accuracy. On a 5,000-case synthetic atlas, the router achieves 0.5820 accuracy at 1.4865 cost, outperforming both fixed baselines (0.4733 and 0.4153) while falling short of the oracle (0.6980). Evidence supports the routing hypothesis in the tested setting, but confidence remains medium due to small real-trace sample size, task-id-grouped holdout, and model-pair specificity.

---

## 1. Introduction

When a language model is presented with a draft—whether from a prior turn, a retrieved document, or a cheaper model—there are at least three qualitatively different ways to use it:

1. **Direct solve**: Ignore the draft entirely and solve from the prompt alone.
2. **Scaffold-only reuse**: Retain the draft's structural skeleton (ordering, section headings, argument flow) but discard its factual or content claims, then regenerate.
3. **Full revision**: Present the draft verbatim and request a corrected or improved version.

These arms differ in both expected cost and expected accuracy. Full revision is typically the most expensive (requiring the model to process the full draft context) but may benefit from the draft's content. Direct solve is cheapest but forgoes any structural information the draft may contain. Scaffold-only reuse occupies a middle cost tier, preserving structural priors while avoiding propagation of draft errors.

The central question of this work is: can a lightweight classifier, using only information available *before* the routing decision is made, learn to assign tasks to the arm that yields the best accuracy-per-cost tradeoff? We treat this as a supervised classification problem where the oracle label for each case is the arm that achieves the highest accuracy at the lowest cost, and the router must predict this label from pre-routing features alone.

---

## 2. Method

### 2.1 Router Architecture

The router is implemented as a Naive Bayes classifier (`scripts/draft_value_router_mvp.py`) operating on the following pre-routing observables:

- **Task class**: The domain category of the task (code, math, mcq, tool_planning).
- **Known model family**: The model family identifier associated with the case.
- **Prompt/draft surface cues**: Surface-level features extracted from the prompt and draft text prior to any outcome evaluation.

Outcome-derived labels (which arm actually performed best) are used exclusively as supervision and evaluation targets; they are never provided to the router as input features. This design ensures the router makes decisions based only on information available at routing time.

### 2.2 Three-Arm Cost Model

Each arm is assigned a unit cost reflecting its relative inference expense:

| Arm | Unit Cost | Rationale |
|-----|-----------|-----------|
| Direct | 1.0 | No draft context processed |
| Scaffold-only | 1.35 | Structural prompt overhead |
| Full revision | 2.0 | Full draft context processed |

These costs are derived from the ratio of input tokens processed relative to the direct-solve baseline and are consistent across both the synthetic and real-trace evaluations.

### 2.3 Oracle Label Derivation

For each case, the oracle label is the arm that achieves the best observed accuracy. When multiple arms achieve equal accuracy, the lower-cost arm is preferred. This produces a per-case ground-truth routing decision that the classifier is trained to predict.

### 2.4 Data Acquisition

Paired outcome logs are acquired from sibling draft-utility atlas runs (provenance recorded in `artifacts/acquisition_manifest.json`). Two data sources are used:

- **Synthetic atlas**: 5,000 cases with oracle label distribution {direct: 3565, full_revision: 1007, scaffold_only: 428}.
- **Real traces**: 128 cases with oracle label distribution {direct: 114, full_revision: 12, scaffold_only: 2} (counterfactual phase); updated to observed scaffold outcomes in the second phase.

### 2.5 Scaffold-Only Execution

In the initial real-trace evaluation, scaffold-only outcomes were counterfactual—conservatively inferred from benefit attribution rather than directly generated. To strengthen evidence, a second phase executed actual scaffold-only prompts on all 128 real-trace cases using cached local models (`Qwen/Qwen2.5-0.5B-Instruct` and `google/flan-t5-base`). The scaffold-only prompt explicitly reuses only structure and ordering from the draft while discarding all factual and content claims. Outputs and provenance are persisted in `data/real_traces_with_observed_scaffold.jsonl`.

### 2.6 Evaluation Protocol

Cases are split by task ID into train/test sets to prevent leakage across related task variants:

- **Synthetic atlas**: 3,500 train / 1,500 test.
- **Real traces**: 88 train / 40 test.

The router is compared against three fixed baselines (always-direct, always-scaffold-only, always-full-revision) and an oracle upper bound. The primary success criteria are:

1. Cost reduction versus always-full-revision at equal-or-better accuracy.
2. Accuracy improvement versus always-direct.
3. Non-collapsed routing (the router must use more than one arm).

---

## 3. Results

### 3.1 Synthetic Atlas (5,000 Cases)

| Policy | Test Accuracy | Avg Cost |
|--------|--------------|----------|
| Always direct | 0.4153 | 1.0000 |
| Always scaffold-only | — | 1.3500 |
| Always full revision | 0.4733 | 2.0000 |
| Learned router | 0.5820 | 1.4865 |
| Oracle | 0.6980 | 1.2233 |

The learned router outperforms both fixed baselines in accuracy while incurring lower average cost than always-full-revision. Router arm selections: {direct: 518, full_revision: 594, scaffold_only: 388}, confirming non-collapsed routing. Cost reduction versus full revision at equal-or-better accuracy: 0.2567. Accuracy delta versus always-direct: 0.1150.

The router falls substantially short of the oracle (0.5820 vs. 0.6980), indicating substantial room for improvement in feature representation or model capacity.

### 3.2 Real Traces — Counterfactual Scaffold Phase (128 Cases)

| Policy | Test Accuracy | Avg Cost |
|--------|--------------|----------|
| Always direct | 0.0500 | 1.0000 |
| Always full revision | 0.1000 | 2.0000 |
| Learned router | 0.1000 | 1.1025 |
| Oracle | 0.1250 | 1.0588 |

The learned router matches full-revision accuracy at approximately 45% lower cost. Router arm selections: {direct: 32, full_revision: 2, scaffold_only: 6}. Cost reduction versus full revision: 0.4488. Code accuracy delta versus direct: 0.125. Collapsed single mode: False.

However, the scaffold-only arm in this phase uses counterfactual outcomes rather than directly observed outputs, which limits the strength of conclusions about scaffold-only routing specifically.

### 3.3 Real Traces — Observed Scaffold Phase (128 Cases)

After generating actual scaffold-only completions and re-evaluating:

**Observed scaffold-only accuracy by domain:**

| Domain | Accuracy | N |
|--------|----------|---|
| Code | 0.3750 | 32 |
| Math | 0.1875 | 32 |
| MCQ | 0.3438 | 32 |
| Tool planning | 0.0313 | 32 |
| **Overall** | **0.2344** | **128** |

**Router evaluation with observed scaffold outcomes:**

| Policy | Test Accuracy | Avg Cost |
|--------|--------------|----------|
| Always direct | 0.0500 | 1.0000 |
| Always scaffold-only | 0.1500 | 1.3500 |
| Always full revision | 0.1000 | 2.0000 |
| Learned router | 0.1750 | 1.1138 |
| Oracle | — | — |

The learned router achieves the highest test accuracy (0.1750) among all non-oracle policies while maintaining cost well below full revision. Router arm selections: {direct: 27, scaffold_only: 13}, indicating the router learns to route a substantial fraction of cases to the scaffold-only arm. Cost reduction versus full revision at equal-or-better accuracy: 0.4431. Code accuracy delta versus direct: 0.5000. Collapsed single mode: False.

Replacing the counterfactual scaffold arm with observed scaffold completions strengthens the result: the router now strictly outperforms all three fixed baselines in accuracy, not just matching full revision at lower cost.

### 3.4 Summary of Key Metrics

| Metric | Synthetic Atlas | Real (Counterfactual) | Real (Observed) |
|--------|----------------|----------------------|-----------------|
| Router accuracy | 0.5820 | 0.1000 | 0.1750 |
| Router cost | 1.4865 | 1.1025 | 1.1138 |
| Cost reduction vs. full revision | 0.2567 | 0.4488 | 0.4431 |
| Accuracy delta vs. direct | +0.1667 | +0.0500 | +0.1250 |
| Non-collapsed routing | Yes | Yes | Yes |

---

## 4. Limitations

1. **Small real-trace sample.** The 128-case real-trace dataset (40 test cases) is small. The observed improvements, while consistent across both evaluation phases, may not generalize to broader task distributions.

2. **Task-ID-grouped holdout.** The train/test split groups by task ID to prevent leakage, but with only 40 test cases, variance in the held-out set is high. Confidence intervals are not reported and would be wide.

3. **Model-pair specificity.** Scaffold-only completions are generated by two specific small local models (Qwen2.5-0.5B-Instruct and flan-t5-base). Results may differ substantially with larger or differently trained models. The relationship between scaffold quality and routing benefit is not characterized.

4. **Class imbalance.** Oracle labels are heavily skewed toward the direct arm (114/128 in real traces, 3565/5000 in synthetic). The Naive Bayes router may be biased toward the majority class, and the rare full_revision and scaffold_only labels are poorly represented in training.

5. **Scaffold-only arm definition.** The scaffold-only prompt discards all factual content from the draft and retains only structure. This is one specific operationalization; other definitions (e.g., retaining some verified facts) may yield different cost-accuracy tradeoffs.

6. **No cross-model or cross-domain transfer validation.** All experiments use data from a single atlas source. The recommended next step—cross-model/domain-transfer validation—has not been performed.

7. **Cost model simplification.** Unit costs (1.0, 1.35, 2.0) are fixed ratios that may not reflect actual inference costs on different hardware or with different token lengths.

8. **No comparison to alternative router architectures.** Only Naive Bayes is evaluated. More expressive classifiers (logistic regression, small neural networks) may improve routing accuracy.

---

## 5. Reproducibility Checklist

- **Code available**: `scripts/draft_value_router_mvp.py`, `scripts/run_scaffold_only_real_traces.py`
- **Input data provenance**: Recorded in `artifacts/acquisition_manifest.json`; source datasets are `data/acquired_draft_utility_atlas_5k.jsonl` and `data/acquired_draft_utility_atlas_real_traces_expanded.jsonl`
- **Scaffold-only outputs**: `data/real_traces_with_observed_scaffold.jsonl`
- **Result files**: All prediction and summary files listed in Section 6 (Referenced Artifacts)
- **Train/test split**: Task-ID-held-out; split sizes reported (88/40 real, 3500/1500 synthetic)
- **Model versions**: Qwen/Qwen2.5-0.5B-Instruct, google/flan-t5-base (cached locally)
- **Router type**: Naive Bayes, no external dependencies beyond standard Python scientific stack
- **Random seed**: Not explicitly reported in run notes; this is a gap
- **Hardware**: Local execution; specific GPU/CPU not recorded in artifacts

---

## 6. Conclusion

This MVP provides evidence that a lightweight supervised router can select among direct, scaffold-only, and full-revision arms to reduce average inference cost while maintaining or improving accuracy relative to fixed baselines. On the primary real-trace benchmark with observed scaffold completions, the router achieves 0.1750 accuracy at 1.1138 average cost—outperforming always-full-revision (0.1000 / 2.0000), always-direct (0.0500 / 1.0000), and always-scaffold-only (0.1500 / 1.3500)—yielding approximately 44% cost reduction versus full revision. On the synthetic atlas, the router outperforms both fixed baselines but remains well below the oracle.

These findings support the draft-value routing hypothesis in the tested setting. However, confidence is medium: the real-trace sample is small, the holdout variance is high, and results are specific to the model pairs and task distributions present in the acquired atlas. The recommended next step is to use the observed-scaffold dataset to design a cross-model/domain-transfer validation that tests whether the routing benefit generalizes beyond the current setting.

---

## Referenced Artifacts

### Result files
- `results/real_trace_router_observed_scaffold/draft_value_router_policy_table.csv`
- `results/real_trace_router_observed_scaffold/draft_value_router_predictions_test.jsonl`
- `results/real_trace_router_observed_scaffold/draft_value_router_predictions_train.jsonl`
- `results/real_trace_router_observed_scaffold/draft_value_router_summary.json`
- `results/observed_scaffold/scaffold_summary.json`
- `results/synthetic_atlas_router/draft_value_router_policy_table.csv`
- `results/synthetic_atlas_router/draft_value_router_predictions_test.jsonl`
- `results/synthetic_atlas_router/draft_value_router_predictions_train.jsonl`
- `results/synthetic_atlas_router/draft_value_router_summary.json`
- `results/real_trace_router/draft_value_router_policy_table.csv`
- `results/real_trace_router/draft_value_router_predictions_test.jsonl`
- `results/real_trace_router/draft_value_router_predictions_train.jsonl`
- `results/real_trace_router/draft_value_router_summary.json`

### Data and provenance files
- `artifacts/acquisition_manifest.json`
- `data/real_traces_with_observed_scaffold.jsonl`
- `data/acquired_draft_utility_atlas_5k.jsonl`
- `data/acquired_draft_utility_atlas_real_traces_expanded.jsonl`

### Code
- `scripts/draft_value_router_mvp.py`
- `scripts/run_scaffold_only_real_traces.py`

### Decision and metadata
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `run_notes.md`

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
