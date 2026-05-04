# Sandbox Risk Oracle: Live Harness Calibration with Typed Action Metadata

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision logs, metrics JSON, execution logs, and claim ledgers). The operator who released this artifact claims no personal authorship credit for the writing or results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has validated the claims, labels, or interpretations herein.

---

## Abstract

We calibrate a typed sandbox-risk oracle against a live execution harness on a 24-candidate corpus of shell commands annotated with structured action metadata. The oracle scores typed metadata capturing eight risk categories—irreversible state change, credential exposure, network reach, external side effects, namespace crossing, TTL expiry, unpinned provenance, and privilege escalation—and selects a risk threshold that blocks all labeled risky candidates while preserving all labeled useful actions. At a threshold of 0.37, the typed oracle achieves perfect separation on this corpus (AUC 1.0, recall 1.0, precision 1.0), compared to a transcript keyword baseline (AUC 0.786) that cannot reach the same risk recall without blocking every useful action. All 10 oracle-allowed commands execute successfully in a temporary sandbox; all 14 denied candidates are correctly contained. Scoring throughput is approximately 530k samples/sec with sub-millisecond latency. These results support the viability of typed-metadata risk scoring at bounded smoke scale, but the corpus is small, labels are authored safety-policy labels rather than independent human-review outcomes, and no distributional-shift or adversarial evaluation has been performed. Production validation remains an open requirement.

## Introduction

Automated agents that execute shell commands or invoke tools in sandboxed environments face a fundamental tension: preserving the ability to perform useful work while containing actions that carry irreversible risk. A prior result in this lineage (carried forward as `prior_sandbox_risk_oracle/`) established a synthetic and policy-log signal suggesting that typed action metadata—structured records of what an action *does* rather than merely what its command string *says*—can separate risky from safe actions more effectively than raw transcript keyword matching.

The central question for this follow-up is whether a typed risk oracle, calibrated against a live execution harness, can select an operating point that blocks risky actions at high recall while preserving useful work in actual sandbox execution. This is a calibration study at bounded smoke scale, not a production deployment: we seek concrete local evidence that the mechanism works end-to-end before investing in deployed workflow instrumentation.

We compare the typed oracle against a transcript keyword baseline at matched risk-recall operating points, execute only oracle-allowed commands in a disposable sandbox, and record execution outcomes. The risk categories evaluated include irreversible state change, credential exposure, network reach, external side effects, namespace crossing, TTL expiry, unpinned provenance, and privilege escalation. Several of these categories are weakly represented in raw command text, creating a structural disadvantage for keyword-based approaches that typed metadata may overcome.

## Method

### Harness Design

The live calibration harness (`scripts/live_harness_calibration.py`) is implemented as a dependency-free Python 3 script using only standard-library modules and common Linux utilities. No external packages, GPU resources, or network services are required.

The harness proceeds in four phases:

1. **Candidate enumeration.** A fixed corpus of 24 typed command/action candidates is defined, comprising 10 candidates labeled "allow/useful" and 14 labeled "deny/risk." Labels are explicit safety-policy labels authored for the harness, covering the eight risk categories listed above.

2. **Scoring and threshold selection.** Each candidate receives a risk score from the typed oracle (based on typed action metadata) and from a transcript keyword baseline (based on raw command text). The harness sweeps thresholds to find the lowest threshold achieving ≥95% risk recall for each scorer, then records confusion matrices at those operating points.

3. **Sandbox execution.** Only candidates predicted "allow" by the typed oracle at the selected threshold are executed as subprocesses inside a temporary sandbox directory. Denied candidates are skipped, and their deny reasons are logged.

4. **Metrics persistence.** Scoring throughput, latency, memory, and platform posture are recorded alongside decision and execution logs.

### Risk Categories

The 14 deny-labeled candidates span eight risk categories:

- **Irreversible state change** (e.g., `rm -rf /`-class operations)
- **Credential exposure** (e.g., reading or exfiltrating secrets)
- **Network reach** (e.g., outbound connections to uncontrolled endpoints)
- **External side effects** (e.g., posting to external APIs)
- **Namespace crossing** (e.g., accessing memory or state outside the agent's namespace)
- **TTL expiry** (e.g., operating on expired-cache memory)
- **Unpinned provenance** (e.g., executing skills or code from unverified sources)
- **Privilege escalation** (e.g., `sudo`-class operations)

Several of these categories—particularly unpinned provenance, cross-namespace memory, expired TTL memory, and external mutations—produce commands whose raw text contains no obvious shell-danger token. This structurally disadvantages keyword-based approaches, since the risk signal resides in the typed metadata rather than the command string.

### Baseline

The transcript keyword baseline scores candidates by matching danger-associated tokens in the raw command string. This represents a naive but commonly deployed defense layer. We evaluate it at the same ≥95% risk-recall constraint to enable a fair comparison of useful-action preservation. The keyword baseline is intentionally minimal; more sophisticated text-based classifiers might close part of the observed gap, but that comparison is outside the scope of this calibration.

### Platform and Resources

All runs execute on an aarch64 Linux system (kernel 6.17.0-1014-nvidia-aarch64) with approximately 122 GB available memory (`MemAvailable` ~122,577,804 kB), zero swap (`SwapTotal` 0, `SwapFree` 0), and earlyoom active. Scoring is CPU-only with no GPU tensor workload. Maximum RSS during the run was 19,096 KB.

### Iteration History

The harness required three execution iterations to reach the reported results. The first revealed a threshold-selection bug. The second (with the bug fixed) showed that one useful sandbox-cleanup command was incorrectly blocked, prompting a final calibration adjustment. The third and final run produced the metrics reported below. This iteration history is documented in the console logs and reflects the prototype nature of the harness.

## Results

### Discrimination Performance

On the 24-candidate corpus, the typed oracle achieves an AUC of 1.0, indicating perfect separation between allow and deny labels. The transcript keyword baseline achieves an AUC of 0.786.

| Scorer | AUC | Threshold (≥95% recall) | TP | FP | TN | FN | Recall | Precision |
|---|---|---|---|---|---|---|---|---|
| Typed oracle | 1.000 | 0.37 | 14 | 0 | 10 | 0 | 1.0 | 1.0 |
| Keyword baseline | 0.786 | 0.0 | 14 | 10 | 0 | 0 | 1.0 | 0.583 |

At the matched recall constraint (≥95%, realized as 1.0 for both scorers), the typed oracle produces zero false positives, while the keyword baseline produces 10 false positives—every useful candidate is misclassified as risky.

Perfect separation on a 24-candidate corpus is expected to be fragile. The result confirms that the typed metadata carries discriminative signal for these risk categories, but AUC on this sample is an overestimate of generalization performance.

### Useful-Action Preservation

The critical operational metric is the blocked-useful ratio: the fraction of labeled-useful candidates that are denied at the selected threshold.

- **Typed oracle:** blocked-useful ratio = 0.0 (0/10). All useful actions are preserved.
- **Keyword baseline:** blocked-useful ratio = 1.0 (10/10). No useful actions are preserved.

This difference arises because several risk categories in the corpus (unpinned skill provenance, cross-namespace memory, expired TTL memory, external mutations) produce commands whose raw text lacks distinctive danger tokens. The keyword baseline can only achieve high risk recall by setting its threshold so low that it flags everything, rendering it operationally unusable at this recall target.

### Live Execution Outcomes

All 10 oracle-allowed commands were executed as subprocesses in a temporary sandbox. All 10 returned exit code 0 with no failures. All 14 denied candidates were not executed, and their deny reasons were logged.

| Outcome | Count |
|---|---|
| Allowed and executed successfully | 10 |
| Allowed but failed | 0 |
| Denied and contained | 14 |

The zero-failure execution result is expected given that the allowed commands are simple, well-understood operations (e.g., file creation, directory listing, sandbox cleanup). This confirms that the sandbox infrastructure works correctly for these commands but does not test edge cases in execution reliability.

### Scoring Performance

| Metric | Value |
|---|---|
| Throughput | ~529,661 samples/sec |
| p50 latency | ~0.000592 ms |
| Max latency | ~0.002672 ms |
| Max RSS | 19,096 KB |

Scoring latency is negligible relative to any realistic agent decision loop. The throughput figure reflects CPU-only scoring on a single platform and may vary on different hardware.

## Limitations

1. **Small corpus.** The 24-candidate corpus is a bounded smoke test, not a representative sample of production agent workloads. Perfect separation (AUC 1.0) on 24 candidates provides no statistical guarantee of generalization. Performance on larger, noisier corpora is expected to degrade.

2. **Authored labels, not independent reviews.** The allow/deny labels were written by the harness author as explicit safety-policy labels. They are not independent human-review outcomes from a deployed workflow. Label quality, inter-annotator agreement, and label independence are unmeasured. This is the most significant limitation: the oracle's apparent performance may reflect label-author alignment with the scoring logic rather than genuine generalization.

3. **Risk-category coverage.** The eight risk categories tested may not exhaust the risk surface of real agent deployments. Novel risk classes, compositional risks (sequences of individually safe actions that combine unsafely), and context-dependent risks are not evaluated.

4. **No distributional shift evaluation.** The corpus is static and authored. We do not test robustness to adversarially chosen candidates, distributional drift over time, or boundary cases where typed metadata is incomplete, misleading, or adversarially crafted.

5. **Single-platform, single-run evidence.** All results come from one platform (aarch64 Linux) and one final run. We do not evaluate cross-platform consistency or run-to-run variance in threshold selection.

6. **Keyword baseline is minimal.** The transcript keyword baseline is a simple token-matching scorer. More sophisticated text-based classifiers (e.g., learned models on command strings) might close part of the gap. The comparison here establishes that typed metadata carries signal absent from raw tokens, not that typed metadata is optimal among all possible approaches.

7. **No production workflow integration.** The harness executes commands in a temporary local sandbox. It does not integrate with a real control plane, CI/CD pipeline, or multi-agent orchestration system. The gap between smoke-test calibration and production deployment is substantial and unmeasured.

8. **Threshold fragility.** The selected threshold of 0.37 is calibrated on this specific corpus. Its stability under corpus expansion, label noise, or distributional shift is unknown. A threshold that works perfectly on 24 candidates may require significant adjustment in production.

9. **No statistical confidence intervals.** The corpus size (N=24) makes reliable interval estimation infeasible. All reported metrics are point estimates on a single small sample.

## Reproducibility Checklist

- [x] **Code available:** `scripts/live_harness_calibration.py` (dependency-free Python 3, stdlib only).
- [x] **Compilation verified:** `python3 -m py_compile` passed before each run.
- [x] **Full decision log:** `artifacts/live_harness_decisions.jsonl` and `artifacts/live_harness_decisions.csv` record typed score, keyword score, and allow/deny decision per candidate.
- [x] **Execution log:** `artifacts/live_harness_execution_log.jsonl` records subprocess return codes for allowed commands and deny reasons for blocked commands.
- [x] **Metrics JSON:** `artifacts/live_harness_metrics.json` records all numeric results.
- [x] **Console log:** `logs/live_harness_calibration_20260501T054526Z.log` captures the full final run output.
- [x] **Platform posture recorded:** Kernel, architecture, memory, swap, earlyoom status, RSS.
- [x] **No external dependencies:** Standard-library Python 3 and Linux utilities only.
- [x] **Deterministic corpus:** The 24-candidate corpus is hardcoded in the script.
- [ ] **Independent label validation:** Not performed. Labels are authored safety-policy labels, not independently reviewed.
- [ ] **Cross-platform replication:** Not performed. Single platform only.
- [ ] **Statistical confidence intervals:** Not computed. Corpus size (N=24) makes interval estimation unreliable.

## Conclusion

A typed sandbox-risk oracle, calibrated against a live execution harness on a 24-candidate corpus, selects a threshold (0.37) that blocks all 14 labeled risky candidates while preserving and successfully executing all 10 labeled useful actions. The typed oracle (AUC 1.0) substantially outperforms a transcript keyword baseline (AUC 0.786) at the same risk-recall operating point, primarily because several risk categories—unpinned provenance, cross-namespace memory, expired TTL memory, external mutations—lack distinctive danger tokens in raw command text but carry clear risk signals in typed metadata.

These results support the viability of typed-metadata risk scoring as a sandbox containment mechanism at bounded smoke scale. The evidence is moderate, not conclusive. The most important limitations are the small authored corpus (which inflates discrimination metrics), the lack of independent label validation (which confounds oracle performance with label-author alignment), and the absence of distributional-shift or adversarial evaluation (which leaves robustness untested).

The appropriate next step is to instrument a real sandbox or control-plane workflow to capture unredacted typed action metadata alongside independent human-review allow/deny labels, then validate whether the calibrated threshold (or a nearby value) preserves useful actions at production risk recall. The project decision record identifies this as the recommended follow-up, under the branch name "Sandbox Risk Oracle Human-Reviewed Workflow Calibration," reflecting that the remaining uncertainty is primarily about external label validity and production representativeness rather than harness mechanism viability.

---

## Referenced Artifacts

| Artifact | Description |
|---|---|
| `run_notes.md` | Operator run notes covering objective, plan, commands, iteration history, metrics, and interpretation |
| `scripts/live_harness_calibration.py` | Dependency-free live calibration harness (Python 3, stdlib only) |
| `artifacts/live_harness_metrics.json` | Final numeric metrics (AUC, confusion, throughput, latency, RSS, platform posture) |
| `artifacts/live_harness_decisions.jsonl` | Per-candidate typed score, keyword score, and allow/deny decision |
| `artifacts/live_harness_decisions.csv` | Tabular copy of per-candidate decisions |
| `artifacts/live_harness_execution_log.jsonl` | Subprocess results for allowed commands; deny reasons for blocked commands |
| `logs/live_harness_calibration_20260501T054526Z.log` | Full console output of the final calibrated run |
| `prior_sandbox_risk_oracle/` | Prior same-lineage synthetic + policy-log result (copied for continuity) |
| `.omx/project_decision.json` | Project-level decision record with key metrics, confidence assessment, and recommended next action |
| `papers/.../claim_ledger.json` | Claim ledger for this paper (empty claims; limitation: model-authored draft requires human claim audit) |
| `papers/.../evidence_bundle.json` | Evidence bundle linking to project and run identifiers |
| `papers/.../paper_manifest.json` | Paper manifest with generation metadata and writer provider information |
