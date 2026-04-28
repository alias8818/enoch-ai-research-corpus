# Real Trace Near-Miss Refusal Adapter Validation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We investigate whether a lightweight calibrated classifier, trained on real agent trace text, can reduce missed stop/refusal interventions compared to a lexical continuation baseline, while preserving the allow-rate for true-continue decisions. From 204 non-generated local project traces mined from an operational agent controller, we extract leakage-controlled text features and train a logistic classifier evaluated via leave-one-category-out cross-validation across six task families. At a fixed conservative threshold of 0.75, the classifier reduces near-miss recurrence from 0.865 to 0.594 (a 31.3% relative reduction) with a continue allow-rate of 1.0, clearing a predeclared success criterion of ≥25% recurrence reduction at ≥95% continue preservation. Evidence strength is moderate: labels derive from local controller decisions rather than independent human safety adjudications, and the adapter is a classifier gate rather than a weight-level LLM adapter. The result supports the mechanism at moderate strength in the tested setting but does not establish generalizability beyond the local trace population.

## 1. Introduction

Autonomous agent systems require mechanisms to detect when a proposed action should be refused or interrupted. A near-miss refusal adapter aims to identify cases where an agent's trajectory warrants a stop or refusal intervention before the action is committed, while preserving the ability to allow benign continuations.

Prior work in this project lineage examined synthetic and simulated proxies for refusal detection. This branch was designed to test the mechanism against real, non-generated intervention traces from an operational agent controller. The central question is whether trace text features—absent decision-label leakage—carry sufficient signal for a lightweight classifier to outperform a naive lexical continuation baseline on held-out task families.

A predeclared branch kill condition specified that the experiment would be terminated if the classifier could not achieve ≥25% reduction in missed stop/refusal decisions versus the baseline while preserving ≥95% of true-continue cases, or if trace labels proved too sparse to support training and evaluation.

## 2. Method

### 2.1 Trace Mining

We implemented a dependency-free mining and classification pipeline (`src/real_trace_refusal_adapter.py`) that extracts 204 non-generated local project traces from an operational Enoch/OMX project directory. Each trace comprises project prompts, metadata, and turn-log previews sourced from project artifacts. Intervention labels are derived from `.omx/project_decision.json` fields, which record the controller's decision for each project turn.

### 2.2 Label Mapping

Controller decisions are mapped to binary labels:

- **Continue** (no refusal/stop intervention): `continue`
- **Stop/refusal intervention**: `finalize_positive`, `finalize_negative`, `branch_new_project`, `needs_review`, `blocked`

The resulting label distribution is: `finalize_positive` (46), `branch_new_project` (66), `continue` (27), `needs_review` (3), `finalize_negative` (62). The continue class constitutes 13.2% of the corpus (27 of 204), reflecting the intervention-heavy nature of the controller's decision distribution.

### 2.3 Leakage Controls

To prevent the classifier from exploiting decision-label leakage rather than genuine trace signal, four leakage controls are enforced:

1. Classifier input excludes all `.omx/project_decision.json` fields.
2. Mandatory prompt decision-schema boilerplate is stripped from feature text.
3. Exact decision label tokens (e.g., "finalize_positive", "branch_new_project") are removed from feature text.
4. Candidate output previews are included only after sanitization, modeling a gate over an agent's proposed final action before commit.

### 2.4 Classifier and Evaluation

A calibrated logistic classifier is trained on leakage-controlled text features. Evaluation uses leave-one-category-out cross-validation across six task families: architecture, datasets, inferencing, optimization, training, and uncategorized. This protocol ensures that the classifier is evaluated on project families unseen during training, testing generalization across task domains.

The classifier operates at a fixed conservative threshold of 0.75, biased toward preserving true-continue decisions.

### 2.5 Baseline

The lexical continuation baseline classifies all cases as "continue," yielding a near-miss recurrence equal to the stop/refusal intervention rate and a perfect continue allow-rate of 1.0. This baseline represents the default behavior of an agent system with no refusal adapter.

## 3. Results

### 3.1 Primary Metrics

| Condition | Near-Miss Recurrence | Stop Recall | Continue Allow-Rate |
|---|---|---|---|
| Lexical continuation baseline | 0.8647 | 0.1353 | 1.0 |
| Calibrated classifier (threshold 0.75) | 0.5941 | 0.4059 | 1.0 |

The classifier reduces near-miss recurrence by 0.3129 (31.29% relative reduction) compared to the baseline, with a utility delta of 0.0 (no reduction in true-continue allow-rate).

### 3.2 Success Criterion

The predeclared success threshold required ≥25% recurrence reduction and ≥95% continue allow-rate. Both conditions are met: recurrence reduction = 31.29% (≥25%), continue allow-rate = 1.0 (≥95%).

### 3.3 Verification

Post-hoc verification confirmed:

- `python3 -m py_compile src/real_trace_refusal_adapter.py` — compilation succeeded.
- `python3 src/real_trace_refusal_adapter.py --out artifacts` — re-execution produced consistent results.
- JSON/CSV assertions confirmed: ≥150 traces (observed: 204), ≥20 continue labels (observed: 27), ≥4 held-out families (observed: 6), recurrence reduction ≥0.25 (observed: 0.3129), continue allow-rate ≥0.95 (observed: 1.0), and matching corpus row count.

### 3.4 Feature Audit

Aggregate high-weight feature audit results are recorded in `artifacts/real_trace_refusal_features.json`. The classifier's decisions are driven by trace text features after leakage removal, though the specific feature weights are not detailed in the available artifacts.

## 4. Limitations

1. **Label provenance.** Intervention labels are derived from a local agent controller's decisions, not from independent human safety adjudications. The controller's decision criteria may introduce systematic biases that do not generalize to other agent systems or to human-judged safety boundaries.

2. **Classifier vs. weight adapter.** The adapter is a classifier gate operating on extracted text features, not a weight-level LLM adapter (e.g., LoRA or refusal head). The extent to which these results predict the performance of an actual LLM weight adapter is unknown.

3. **Corpus size and class imbalance.** The corpus contains 204 traces with only 27 continue labels (13.2%). The `needs_review` category contains only 3 instances. Small and imbalanced classes may produce unstable estimates, particularly in leave-one-category-out folds where the held-out family may contain few examples of a given label.

4. **Local trace population.** All traces originate from a single local project directory. Generalization to other agent systems, task domains, or controller configurations is not established.

5. **Effect size relative to synthetic proxies.** The observed effect (31.29% recurrence reduction) is smaller than effects reported in parent simulations using synthetic data. This is expected given the shift from synthetic to real traces but limits the strength of the evidence.

6. **Threshold selection.** The classifier threshold of 0.75 was fixed rather than optimized on a validation set. The sensitivity of results to threshold choice is recorded in the threshold sweep within `artifacts/real_trace_refusal_results.json` but is not detailed in this draft.

7. **No independent human evaluation.** No independent human reviewers assessed the correctness of the controller's intervention labels or the classifier's predictions on held-out data.

## 5. Reproducibility Checklist

- **Code availability:** `src/real_trace_refusal_adapter.py` — dependency-free Python script for mining, feature extraction, classification, and evaluation.
- **Corpus:** `artifacts/real_trace_refusal_corpus.csv` — 204 mined traces with labels and source paths.
- **Results:** `artifacts/real_trace_refusal_results.json` — fold metrics, threshold sweep, limitations, and success flag.
- **Feature audit:** `artifacts/real_trace_refusal_features.json` — aggregate high-weight feature audit.
- **Run output:** `artifacts/real_trace_refusal_stdout.json` — full run output.
- **Re-execution command:** `python3 src/real_trace_refusal_adapter.py --out artifacts`
- **Compilation check:** `python3 -m py_compile src/real_trace_refusal_adapter.py`
- **Assertion checks:** ≥150 traces, ≥20 continue labels, ≥4 held-out families, recurrence reduction ≥0.25, continue allow-rate ≥0.95, matching corpus row count — all passed.
- **Random seed:** Not specified in available artifacts; exact numerical reproducibility of classifier training is not guaranteed.
- **Hardware environment:** Local execution on the project machine; no GPU required (logistic classifier on 204 samples).

## 6. Conclusion

A lightweight calibrated logistic classifier trained on leakage-controlled real trace text from 204 operational agent projects reduced missed stop/refusal interventions by 31.29% relative to a lexical continuation baseline, while preserving all true-continue decisions (allow-rate 1.0). This result clears the predeclared success criterion of ≥25% recurrence reduction at ≥95% continue preservation, evaluated via leave-one-category-out cross-validation across six task families.

The evidence supports the near-miss refusal adapter mechanism at moderate strength in the tested setting. However, the result is bounded by several important limitations: labels originate from a local controller rather than independent human adjudication, the adapter is a classifier gate rather than a weight-level LLM modification, and the trace population is local and relatively small. The effect size is smaller than that observed in prior synthetic simulations, consistent with the expected degradation when moving from synthetic proxies to real data.

A meaningful next step would require a materially different experimental target—specifically, an independently human-adjudicated trace set or an actual lightweight LLM adapter (e.g., LoRA or refusal head) benchmark—rather than further classifier-gate evaluations on the same trace population.

---

## Referenced Artifacts

| Artifact | Path | Description |
|---|---|---|
| Source code | `src/real_trace_refusal_adapter.py` | Miner, leakage-controlled feature extraction, logistic classifier, held-out-family evaluation |
| Corpus | `artifacts/real_trace_refusal_corpus.csv` | 204 mined real traces with labels and source paths |
| Results | `artifacts/real_trace_refusal_results.json` | Fold metrics, threshold sweep, limitations, success flag |
| Feature audit | `artifacts/real_trace_refusal_features.json` | Aggregate high-weight feature audit |
| Run output | `artifacts/real_trace_refusal_stdout.json` | Full run output |
| Project decision | `.omx/project_decision.json` | finalize_positive, hypothesis supported, confidence medium |
| Run notes | `run_notes.md` | Execution plan, results, interpretation |
| Evidence bundle | `papers/.../evidence_bundle.json` | Aggregated evidence for publication |
| Claim ledger | `papers/.../claim_ledger.json` | Audited claims with confidence and allowed/forbidden wording |
| Metrics | `.omx/metrics.json` | Session metrics |
