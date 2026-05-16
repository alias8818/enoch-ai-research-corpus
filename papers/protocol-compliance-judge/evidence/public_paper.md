# Protocol Compliance Judge: A Deterministic Preflight Gate for Machine-Checkable Protocol Clauses

> **AI provenance notice.** This draft was AI-generated from automated research artifacts produced by an autonomous system (writer model: `hf:zai-org/GLM-5.1` via `synthetic.new`, response ID `source-record-redacted`). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We present Protocol Compliance Judge, a dependency-free deterministic system for evaluating protocol compliance of transcripts and artifact maps against machine-checkable predicate clauses. The system classifies episodes into three verdicts—*compliant*, *needs_review*, and *non_compliant*—using text-, order-, and artifact-presence predicates rather than learned semantic inference. On a 10-episode labelled synthetic fixture set, the judge achieves gold accuracy of 1.000 with zero mismatches across all three verdict categories. In a broader artifact-audit sweep of 110 episodes, the system processes approximately 153,261 episodes per second with a mean compliance score of 0.985, surfacing one project with missing required artifacts. These results support the viability of the approach as a bounded deterministic preflight gate for expressible protocol clauses. However, the system does not perform general semantic or policy judging; requirements involving private content, paraphrased intent, or manual human review remain correctly routed to *needs_review* rather than resolved. The evaluation is limited to synthetic fixtures and local artifact-presence checks. No private Notion page content was available for testing page-specific protocol requirements, and no baseline comparison was conducted. The perfect accuracy on the gold fixture is expected given the self-consistent design-evaluation pipeline and should not be overinterpreted.

## Introduction

Automated research and agent orchestration pipelines increasingly require preflight checks that verify whether a given run or project has satisfied protocol requirements before proceeding. These requirements may include the presence of specific artifacts (e.g., `run_notes.md`, `project_decision.json`), the ordering of operations, or the inclusion of particular text clauses in outputs.

A central tension in building such checks is between expressiveness and reliability. Learned or LLM-based judges can handle paraphrased or implicit requirements but introduce nondeterminism, latency, and cost. Deterministic predicate-based judges are fast and reproducible but can only evaluate requirements that are expressible as explicit text, order, or artifact-presence predicates.

This work explores the design space of a deterministic protocol compliance judge intended as a preflight and regression gate. The system evaluates episodes—structured records of agent runs—against a set of protocol clauses derived from local operating constraints. It produces JSON verdicts and scores, enabling integration into CI-like gating pipelines.

The primary contributions are:

1. A dependency-free Python implementation of a deterministic protocol compliance judge.
2. A 10-episode labelled fixture set covering compliant, needs-review, and non-compliant cases.
3. Empirical characterization of accuracy on gold fixtures and throughput on both fixture and artifact-audit workloads.
4. An honest accounting of the approach's scope limitations, particularly its inability to judge semantic policy compliance or evaluate private/external content.

## Method

### Protocol Clause Derivation

The protocol clauses under test were derived from explicit local prompt clauses and AGENTS/OMX operating constraints. An attempt was made to fetch the project's Notion page for additional protocol requirements; however, the public fetch returned only generic Notion HTML without page content. This is evidenced by `logs/notion_title_extract_20260502T181139.log`, which recorded `contains_project_title=False` and `contains_access_notice=True` with the extracted title being the generic string `Notion`. Consequently, the protocol under test is limited to locally available constraints, and any page-specific requirements from the Notion source remain unevaluated.

### Judge Design

The judge (`scripts/protocol_compliance_judge.py`) is a dependency-free, deterministic Python script that:

1. Accepts an input file of episodes (JSONL format) and an optional audit directory.
2. Evaluates each episode against a set of protocol predicates covering text presence, ordering constraints, and artifact-presence requirements.
3. Assigns a verdict (`compliant`, `needs_review`, or `non_compliant`) and a numeric score to each episode.
4. Outputs structured JSON results including verdict counts, mismatches against gold labels, and throughput metrics.

The three-verdict scheme is intentional: *needs_review* serves as an explicit escape hatch for conditions that cannot be resolved by deterministic predicates alone (e.g., private content requirements, manual human review triggers, paraphrased intent). This design choice means the system explicitly declines to resolve certain classes of questions rather than risking false resolution.

### Fixture Construction

A fixture set of 10 labelled episodes (`fixtures/protocol_episodes.jsonl`) was constructed to cover:

- 4 compliant episodes satisfying all evaluated predicates.
- 3 needs-review episodes triggering conditions requiring human or external evaluation.
- 3 non-compliant episodes violating one or more deterministic protocol clauses.

These fixtures are synthetic and were generated alongside the judge implementation within the same autonomous run. They represent the protocol clauses explicitly encoded in the local operating constraints, not a representative sample of real-world compliance scenarios.

### Artifact Audit Mode

In artifact-audit mode, the judge additionally scans a directory for the presence of required durable artifacts (e.g., `run_notes.md`, `project_decision.json`) across historical projects. This mode checks artifact *presence*, not artifact *quality*—a significant limitation acknowledged in the Limitations section.

### Evaluation Protocol

Two evaluation runs were conducted:

1. **Smoke fixture evaluation**: The judge processes the 10-episode gold-labelled fixture, and predicted verdicts are compared against gold labels.
2. **Artifact audit evaluation**: The judge processes 110 episodes (the 10 fixtures plus 100 historical project audits from the parent directory), evaluating both protocol compliance and artifact presence.

Both runs are prototype-level measurements on a single system. They should not be confused with production validation.

All runs were executed on a system with 122,449,904 kB available memory, 0 kB swap, and earlyoom v1.7 active. System telemetry was captured in `logs/environment_and_source_20260502T181130Z.log`.

## Results

### Smoke Fixture Evaluation

| Metric | Value |
|---|---|
| Labelled episodes | 10 |
| Gold accuracy | 1.000 |
| Mismatches | 0 |
| Compliant | 4 |
| Needs review | 3 |
| Non-compliant | 3 |
| Mean score | 0.860 |
| Throughput | ~40,621 episodes/sec |
| Elapsed time | 0.000246 s |

The confusion matrix shows perfect diagonal agreement: all four gold-compliant episodes were predicted compliant, all three gold-needs-review episodes were predicted needs_review, and all three gold-non-compliant episodes were predicted non_compliant. No false positives or false negatives were observed in this fixture set.

However, this result must be interpreted with caution. The fixture set was constructed to test the specific predicates encoded in the judge, and the judge was designed against the same protocol clauses. Perfect accuracy on a self-consistent synthetic fixture is expected and does not generalize to unseen or paraphrased requirements.

### Artifact Audit Evaluation

| Metric | Value |
|---|---|
| Total episodes/audits | 110 |
| Compliant | 103 |
| Needs review | 4 |
| Non-compliant | 3 |
| Mean score | 0.985 |
| Throughput | ~153,261 episodes/sec |
| Elapsed time | 0.000718 s |

The artifact audit surfaced one project (`source-record-redacted`) with missing required artifacts. The high compliant count (103 of 110) reflects the fact that most historical projects in the audit directory possessed the required artifact files. The four needs-review verdicts correspond to conditions that the deterministic predicates could not resolve.

No gold labels exist for the 100 historical project audits, so accuracy cannot be computed for that subset. The mean score of 0.985 reflects the scoring function's output across all 110 episodes but should not be interpreted as a validated accuracy metric.

### Throughput Comparison

The artifact-audit mode achieved higher throughput (~153,261 episodes/sec) than the smoke fixture mode (~40,621 episodes/sec). This apparent inversion is likely an artifact of the small sample sizes and fixed overhead: the 10-episode fixture run's per-episode cost is dominated by startup and I/O overhead, while the 110-episode audit amortizes these costs more effectively. Neither number should be treated as a stable production benchmark; both are prototype measurements on trivially small workloads.

## Limitations

1. **Regex and text-predicate brittleness.** The deterministic predicates rely on text matching and artifact-presence checks. They can miss paraphrased or implicitly satisfied requirements and can overflag benign text that happens to match a failure pattern. This is a fundamental scope limitation of the predicate-based approach, not a remediable bug.

2. **No private or external content evaluation.** The Notion page content was inaccessible during this run. Any page-specific protocol requirements stored in that private resource were not evaluated and remain outside the judge's scope. When such conditions are encountered, the judge correctly routes them to *needs_review* rather than attempting resolution, but this means the judge is incomplete with respect to the full protocol as originally specified.

3. **Artifact presence vs. quality.** The artifact audit verifies that required files exist but does not evaluate their content quality. A project with an empty or malformed `run_notes.md` would still pass the artifact-presence check. This is a known gap that would require semantic content analysis to close.

4. **Synthetic fixture scope.** The 10-episode gold fixture is synthetic and covers only the protocol clauses explicitly encoded. It does not represent the full distribution of real-world protocol compliance scenarios. Gold accuracy of 1.000 on this fixture should not be interpreted as evidence of general accuracy.

5. **Small workload sizes.** Both evaluations processed trivially small numbers of episodes (10 and 110). Throughput figures are unstable at these scales and should not be extrapolated to production workloads.

6. **No comparison to baseline.** This prototype has no baseline comparison (e.g., against an LLM-based judge or a random classifier). The gold accuracy result is meaningful only relative to the specific fixture, not as an absolute performance claim. Without a baseline, it is impossible to assess whether the predicate approach offers any advantage over simpler alternatives.

7. **Single-system evaluation.** All measurements were taken on a single high-memory system (122 GB available). No cross-platform or resource-constrained evaluation was performed. Performance on memory-limited systems may differ.

8. **Self-consistent design and evaluation.** The protocol clauses, the judge predicates, and the gold fixtures were all produced within the same autonomous run. There is no independent specification or external gold standard against which to validate the system. This circularity limits the evidential weight of the perfect accuracy result.

## Reproducibility Checklist

- **Algorithm description**: Deterministic text/order/artifact-predicate evaluation; full source in `scripts/protocol_compliance_judge.py`.
- **Fixture data**: 10 labelled episodes in `fixtures/protocol_episodes.jsonl`.
- **Test suite**: `tests/test_protocol_compliance_judge.py`; runnable via `python3 -m unittest discover -s tests`.
- **Command log**: All evaluation commands recorded in `run_notes.md` under "Commands and logs."
- **Output artifacts**: `results/smoke_protocol_judge.json`, `results/protocol_judge_with_artifact_audit.json`, `results/metrics.json`.
- **Execution logs**: `logs/unit_20260502T181118Z.log`, `logs/smoke_protocol_judge_20260502T181118Z.log`, `logs/artifact_audit_20260502T181118Z.log`, `logs/final_verification_20260502T181251Z.log`.
- **Environment logs**: `logs/environment_and_source_20260502T181130Z.log`.
- **Source access log**: `logs/notion_title_extract_20260502T181139.log`, `logs/audit_failure_extract_20260502T181139Z.log`.
- **Dependencies**: None (dependency-free Python 3 implementation).
- **Randomness**: None (fully deterministic; no random seeds required).
- **Hardware context**: 122,449,904 kB available memory, 0 kB swap, earlyoom v1.7 present.
- **Final verification**: Confirmed in `logs/final_verification_20260502T181251Z.log` — unit tests pass, gold accuracy 1.000, project decision JSON valid, required durable artifacts present.

## Conclusion

Protocol Compliance Judge demonstrates that a deterministic, dependency-free predicate system can serve as a fast preflight and regression gate for machine-checkable protocol clauses. On a synthetic gold fixture of 10 episodes spanning all three verdict categories, the system achieves perfect accuracy. On a broader 110-episode artifact audit, it processes over 150,000 episodes per second and correctly surfaces missing-artifact projects while routing unresolvable conditions to *needs_review*.

These results are bounded. The system judges only what is expressible as text, order, or artifact-presence predicates. It cannot evaluate semantic policy compliance, private external content, or artifact quality. The gold fixture is small, synthetic, and self-consistent with the judge design; the throughput measurements are unstable at these scales; and no baseline comparison exists. The perfect accuracy on the gold fixture is expected given the circularity of the design-evaluation pipeline and should not be overinterpreted.

The recommended integration path is to use `scripts/protocol_compliance_judge.py` as a fast preflight gate for machine-checkable protocol clauses while routing semantic, private, and manual-review requirements to the *needs_review* escape hatch for human evaluation. Scientific closure for this prototype is achieved for deterministic clauses in the fixture and local artifact-audit surface. Broader closure over private Notion requirements or human policy decisions remains out of scope and should remain *needs_review* when encountered.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Judge implementation | `scripts/protocol_compliance_judge.py` |
| Gold fixture episodes | `fixtures/protocol_episodes.jsonl` |
| Test suite | `tests/test_protocol_compliance_judge.py` |
| Smoke results | `results/smoke_protocol_judge.json` |
| Audit results | `results/protocol_judge_with_artifact_audit.json` |
| Metrics summary | `results/metrics.json` |
| Report | `results/protocol_compliance_judge_report.md` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Unit test log | `logs/unit_20260502T181118Z.log` |
| Smoke judge log | `logs/smoke_protocol_judge_20260502T181118Z.log` |
| Artifact audit log | `logs/artifact_audit_20260502T181118Z.log` |
| Environment log | `logs/environment_and_source_20260502T181130Z.log` |
| Audit failure extract | `logs/audit_failure_extract_20260502T181139Z.log` |
| Notion title extract | `logs/notion_title_extract_20260502T181139.log` |
| Final verification log | `logs/final_verification_20260502T181251Z.log` |
| Claim ledger | `papers/source-record-redacted-20260502T180834767498+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T180834767498+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T180834767498+0000/paper_manifest.json` |
