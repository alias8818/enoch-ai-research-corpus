# Plan Drift Tribunal: Deterministic Detection of Agent Execution Divergence from Stated Plans

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, benchmark results, and decision JSON). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

Autonomous agents executing multi-step plans can silently diverge from their stated objectives—skipping steps, reordering prerequisites, expanding scope, contradicting prior decisions, or claiming completion without verification. We present the Plan Drift Tribunal, a lightweight deterministic framework that audits structured plan–execution trace pairs using independent rule-based judges, each targeting a distinct drift modality. On 100,000 synthetically generated cases spanning five drift classes plus clean traces, the tribunal achieves perfect classification (accuracy, precision, recall, and F1 all 1.000) at 23,783 cases/sec with 123 MB peak memory. However, because the synthetic generator and the tribunal share the same rule surface, this result confirms internal coherence rather than real-world robustness. A five-case adversarial boundary suite reveals that token-overlap matching produces false positives on semantically equivalent paraphrases (precision 0.750, F1 0.857), establishing a clear limitation for natural-language agent logs. We conclude that the approach is viable as a deterministic first-pass gate for structured traces with stable vocabulary but requires either controlled trace vocabularies or a semantic entailment layer before deployment on unconstrained natural-language logs.

## Introduction

As autonomous software agents take on increasingly complex multi-step tasks, the gap between an agent's stated plan and its actual execution becomes a meaningful failure mode. An agent may skip a validation step, reorder operations in a way that violates a dependency, introduce tasks outside the original scope, contradict an earlier decision, or mark a step as complete without evidence. Such *plan drift* can propagate silently through long-running workflows, producing outcomes that diverge from user intent without any explicit error signal.

Existing approaches to agent monitoring typically rely on either end-state evaluation—checking whether the final output meets a specification—or LLM-based self-critique, where a model judges its own trace. End-state evaluation cannot localize where drift occurred; LLM-based critique is expensive, non-deterministic, and difficult to audit.

This work asks: can a small, auditable set of deterministic checks detect when an agent execution trace materially diverges from its stated plan, using only local structured plan/event text?

We approach this question by constructing a Plan Drift Tribunal: a panel of independent judges, each responsible for one drift modality, operating on structured plan and event representations. We evaluate on synthetic traces and an adversarial boundary suite, and we report both the positive results and the demonstrated limitations with equal specificity.

## Method

### Problem Formulation

Given a plan $P = [p_1, p_2, \ldots, p_n]$ consisting of ordered steps and an execution trace $E = [e_1, e_2, \ldots, e_m]$ consisting of ordered events, the tribunal produces a drift verdict $V \in \{\text{drift}, \text{clean}\}$ and, when drift is detected, a set of drift labels indicating which modalities were observed.

### Drift Classes

The tribunal defines five drift classes, each adjudicated by an independent judge:

| Class | Description |
|---|---|
| `skip` | A planned step has no corresponding event in the trace. |
| `reorder` | Events occur in an order that inverts a required prerequisite relationship. |
| `scope_creep` | An event references work outside the scope of any planned step. |
| `contradiction` | An event explicitly contradicts a prior event or a planned constraint. |
| `unverified_done` | A step is marked complete without a corresponding verification event. |

A clean trace (`none`) contains events that cover all planned steps in order, within scope, without contradiction, and with verified completions.

### Tribunal Architecture

Each judge operates independently and deterministically:

1. **Coverage Judge** checks whether every planned step has at least one matching event, using token-overlap matching between step descriptions and event text.
2. **Order Judge** checks whether prerequisite-annotated steps appear in the correct sequence in the trace.
3. **Scope Judge** checks whether any event references work not covered by any planned step.
4. **Contradiction Judge** checks for explicit negation or conflict markers between events and plan constraints.
5. **Verification Judge** checks whether steps marked as done have associated verification events.

The tribunal's final verdict is the union of all judges' findings: if any judge reports drift, the trace is labelled as drift, and the specific drift classes are reported.

### Synthetic Trace Generator

To evaluate the tribunal, we constructed a synthetic generator that produces labelled plan–trace pairs. The generator:

1. Creates a random plan of 3–8 steps with optional prerequisite and verification annotations.
2. Either produces a clean trace (all steps covered, in order, in scope, verified) or injects one or more drift classes by selectively removing events, reordering them, adding out-of-scope events, inserting contradictions, or omitting verification events.

The generator labels each case with its ground-truth drift class(es). This is a toy simulation: the generator's drift injection mechanisms directly correspond to the tribunal's detection rules, which means perfect classification on this distribution is expected and does not constitute evidence of real-world robustness.

### Adversarial Boundary Suite

To probe limitations beyond the synthetic distribution, we constructed a five-case adversarial suite:

- **Case 1**: Benign instrumentation event (`note: started timer`) added to an otherwise clean trace. Expected classification: clean.
- **Cases 2–4**: Hard drift cases combining multiple drift modalities. Expected classification: drift.
- **Case 5**: Semantic paraphrase of a clean trace (`repo surveyed`, `tiny validation passed`, `decision recorded` instead of the original step vocabulary). Expected classification: clean.

This suite specifically targets the boundary between benign variation and true drift, and the token-overlap matching strategy's vulnerability to paraphrase.

### Implementation

The tribunal and generator are implemented in a single Python file (`scripts/plan_drift_tribunal.py`) with no external dependencies beyond the standard library. The adversarial suite is implemented in `scripts/adversarial_boundary.py`. Both files compile cleanly under `py_compile`. This is a llama.cpp-hook-prototype-class implementation: a standalone Python harness with no integration into any agent runtime or production pipeline.

## Results

### Synthetic Holdout (100,000 Cases)

| Metric | Value |
|---|---|
| Cases | 100,000 |
| Accuracy | 1.000 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 | 1.000 |
| True Positives | 83,454 |
| False Positives | 0 |
| True Negatives | 16,546 |
| False Negatives | 0 |
| Throughput | 23,783 cases/sec |
| Wall-clock time | 4.205 sec |
| Peak RSS | 123,576 KB |

Per-type accuracy was 1.000 across all six generated classes (five drift classes plus clean).

**Interpretation.** Perfect classification on synthetic data is expected and should not be interpreted as evidence of real-world robustness. The synthetic generator and the tribunal share the same rule surface: the generator produces drift by applying transformations that the tribunal's judges are explicitly designed to detect, and it produces clean traces using vocabulary that the tribunal's token-overlap matching will accept. This result confirms that the tribunal is internally coherent and that its judges fire correctly on their target drift modalities. It does not establish that the tribunal generalizes to vocabulary, phrasing, or drift patterns outside the generator's distribution.

### Adversarial Boundary Suite (5 Cases)

| Metric | Value |
|---|---|
| Cases | 5 |
| Accuracy | 0.800 |
| Precision | 0.750 |
| Recall | 1.000 |
| F1 | 0.857 |
| True Positives | 3 |
| False Positives | 1 |
| True Negatives | 1 |
| False Negatives | 0 |

**Per-case outcomes:**

- Benign instrumentation: correctly allowed (TN).
- Three hard drift cases: correctly detected (TP).
- Semantic paraphrase: **falsely flagged as drift** (FP).

The false positive on the paraphrase case directly demonstrates the token-overlap matching limitation: when a clean trace uses different vocabulary than the plan steps (e.g., `repo surveyed` vs. the original step text), the coverage judge cannot establish a match and reports a skip, even though the trace is semantically equivalent to the plan.

### Performance Characteristics

The tribunal processes 23,783 cases per second with a peak memory footprint of approximately 121 MB, making it suitable for per-step control-plane gating or CI integration on the test machine. Memory availability before and after the run (122,659,788 KB → 122,569,900 KB) confirms negligible memory pressure. These figures are single-machine calibration results, not production validation.

## Limitations

1. **Synthetic–detector alignment.** The 100,000-case perfect classification result is tautological in structure: the generator and detector share the same rule surface. This proves internal coherence, not real-world accuracy. No claim of production-grade drift detection on arbitrary natural-language logs is warranted by this evidence.

2. **Token-overlap matching.** The coverage judge relies on token overlap between plan step text and event text. This produces false positives on semantically equivalent paraphrases, as demonstrated by the adversarial boundary suite. Any deployment on natural-language traces must address this limitation, either by constraining trace vocabulary or by adding a semantic matching layer.

3. **No real-world labelled data.** All evaluation uses synthetic or hand-crafted cases. No labelled corpus of real agent plans and execution traces was available or used. The tribunal's performance on real agent logs remains unknown.

4. **Limited drift taxonomy.** The five drift classes may not cover all drift modalities present in real agent behavior. Subtle drifts—such as partial completion, goal substitution, or gradual scope expansion across many steps—may not be captured by the current judges.

5. **Adversarial suite size.** The boundary suite contains only five cases. While it successfully identifies a specific failure mode (paraphrase false positives), it does not comprehensively characterize the tribunal's failure distribution.

6. **Single-machine evaluation.** All performance metrics were collected on one machine. Throughput and memory figures may differ on other hardware.

7. **No Notion page content.** The project's Notion page URL was recorded but the page body was not accessible through available session tools. No private page content influenced the design or evaluation.

8. **No integration with agent runtime.** The tribunal operates on pre-generated trace files. It has not been tested as a live control-plane gate within an actual agent execution loop.

## Reproducibility Checklist

- [x] **Source code available.** `scripts/plan_drift_tribunal.py` and `scripts/adversarial_boundary.py` are present in the project directory.
- [x] **Deterministic execution.** Both scripts accept a `--seed` flag; the main harness was run with `--seed 20260430`.
- [x] **Exact commands recorded.** All smoke, calibration, and adversarial commands are logged in `run_notes.md` and `logs/*.log`.
- [x] **Result artifacts preserved.** JSON summaries, JSONL case records, and CSV exports are present under `results/smoke_v3/`, `results/full_100k_v2/`, and `results/adversarial_boundary_v2/`.
- [x] **No external dependencies.** The tribunal and generator use only the Python standard library.
- [x] **Compilation verified.** Both scripts pass `py_compile`.
- [x] **Metrics JSON committed.** `.omx/project_decision.json` and `.omx/metrics.json` contain the same numerical results reported here.
- [ ] **Real-world labelled data.** Not available; acknowledged gap.
- [ ] **Cross-machine validation.** Not performed; acknowledged gap.

## Conclusion

The Plan Drift Tribunal demonstrates that a small panel of deterministic, auditable judges can detect five classes of plan–execution divergence on structured traces with high throughput and low memory overhead. On synthetic data aligned with the detector's rule surface, classification is perfect; on an adversarial boundary suite, the tribunal correctly identifies hard drift cases and benign instrumentation but falsely flags semantic paraphrases, yielding precision 0.750 and F1 0.857.

These results support a bounded conclusion: the approach is viable as a deterministic first-pass gate for agent traces that use reasonably stable vocabulary relative to their plans. It is not yet viable for unconstrained natural-language logs, where paraphrase and vocabulary variation are common.

The path to production-grade natural-language drift detection requires one or both of: (a) controlled trace vocabularies that constrain event descriptions to terms the tribunal can match, or (b) a semantic entailment layer (e.g., embedding similarity or a lightweight LLM judge) that resolves paraphrases before the tribunal's token-overlap judges operate. Collecting labelled real agent plans and execution traces is a prerequisite for either path.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Tribunal script | `scripts/plan_drift_tribunal.py` |
| Adversarial boundary script | `scripts/adversarial_boundary.py` |
| Run notes | `run_notes.md` |
| Smoke test log | `logs/smoke_v3.log` |
| Full 100k run log | `logs/full_100k_v2.log` |
| Adversarial run log | `logs/adversarial_v2.log` |
| Smoke test summary | `results/smoke_v3/summary.json` |
| Full 100k summary | `results/full_100k_v2/summary.json` |
| Adversarial boundary summary | `results/adversarial_boundary_v2/summary.json` |
| Smoke test cases | `results/smoke_v3/cases.jsonl`, `results/smoke_v3/cases.csv` |
| Full 100k cases | `results/full_100k_v2/cases.jsonl`, `results/full_100k_v2/cases.csv` |
| Adversarial boundary cases | `results/adversarial_boundary_v2/cases.jsonl`, `results/adversarial_boundary_v2/cases.csv` |
| Project decision JSON | `.omx/project_decision.json` |
| Project metadata | `.omx/project.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260430T043518316413+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T043518316413+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T043518316413+0000/paper_manifest.json` |
