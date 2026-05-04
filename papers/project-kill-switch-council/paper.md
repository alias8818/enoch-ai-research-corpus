# Kill Switch Council: A Deterministic Evidence-Gated Control-Plane Primitive for Automated Project Lifecycle Decisions

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, decision JSON, and metrics). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We present Kill Switch Council, a deterministic, evidence-gated decision procedure for automated project lifecycle control. The system evaluates local telemetry and artifact evidence through four independent council members—scientific closure, operations, cost/risk, and evidence hygiene—to produce one of three decisions: `continue`, `kill`, or `needs_review`. We implement a dependency-free Python prototype and evaluate it against a hand-authored synthetic case matrix of 15 representative control-plane scenarios. On this matrix, the council achieves 15/15 agreement with oracle labels (0.000 false-kill rate, 0.000 false-continue rate), compared to 6/15 for a naive single-threshold baseline (0.133 false-kill rate, 0.467 false-continue rate). Development exposed one design defect: the initial prototype produced `needs_review` rather than `kill` on repeated out-of-memory conditions, requiring the addition of a hard-override mechanism. These results are limited to synthetic, hand-labeled scenarios and do not constitute production validation. The claim ledger for this artifact is in a blocked state with no structured claims extracted, meaning no claim herein has passed a formal claim/evidence audit. We discuss remaining risks including oracle coverage, threshold calibration, and the absence of private external evidence during evaluation.

## Introduction

Automated research control planes must decide whether running projects should continue, be terminated, or escalate for human review. A naive approach—applying a single threshold to a single metric—risks both false kills (terminating projects that could have succeeded) and false continues (allowing projects to consume resources after they have effectively failed). The former is particularly damaging when project closure depends on private or external evidence not available to the control plane, since the control plane may kill a project that a human reviewer, possessing fuller information, would have continued.

We investigate whether a deterministic "council" pattern—multiple independent evidence evaluators with veto and override rules—can serve as a viable primitive for these decisions. The design goals are:

1. **Avoid unsafe false kills** when the control plane lacks access to private or external evidence that might justify continuation.
2. **Detect clear failure modes** (e.g., repeated out-of-memory events) that warrant termination even without human review.
3. **Escalate ambiguous cases** to a `needs_review` state rather than forcing a binary continue/kill decision.

This paper describes the prototype implementation, a synthetic evaluation against a hand-authored oracle, and an analysis of the design defect discovered during testing. We emphasize that the evaluation is small-scale and synthetic; the results demonstrate implementability and basic correctness properties on the studied edge cases, not generalization to arbitrary production scenarios.

## Method

### Council Architecture

The prototype (`src/kill_switch_council.py`, 8819 bytes) implements four council members, each examining a distinct evidence dimension:

| Council Member | Responsibility |
|---|---|
| Scientific closure | Whether the project has produced sufficient scientific output to justify continuation or termination |
| Operations | Whether system-level signals (memory, errors, hangs) indicate operational failure |
| Cost/risk | Whether cumulative resource expenditure or risk profile exceeds policy bounds |
| Evidence hygiene | Whether the evidence base is complete enough to support a confident decision; vetoes kills when critical evidence is private or external |

Each member returns a vote: `continue`, `kill`, or `needs_review`. The council aggregates votes through deterministic rules:

- **Kill quorum**: A kill vote from operations (with hard-override conditions, e.g., repeated OOM) is not vetoable.
- **Kill veto**: The evidence-hygiene member can veto a kill when the decision would depend on unavailable private/external evidence, downgrading to `needs_review`.
- **Continue quorum**: Requires no kill votes and no unresolved `needs_review` flags.
- **Default**: Ambiguous configurations resolve to `needs_review`.

### Hard Override for Repeated OOM

During initial testing, a design defect was identified: repeated out-of-memory events produced only `needs_review` rather than `kill`. The corrected prototype introduces a hard-override rule: if the operations member detects repeated OOM conditions (as reported by system telemetry), the council decision is forced to `kill` regardless of other votes. This override cannot be vetoed by any other council member. The defect and its fix are discussed further in the Results section as a negative finding.

### Baseline

The naive single-threshold baseline applies a single metric threshold (e.g., memory availability below a cutoff) to produce a binary `continue`/`kill` decision. It has no `needs_review` state and no evidence-hygiene check. This baseline represents the simplest plausible automated control and serves as a lower bound on acceptable performance.

### Evaluation Procedure

The synthetic evaluation (`scripts/run_synthetic_eval.py`, 5492 bytes) defines 15 hand-labeled control-plane scenarios covering:

- Normal continuation with adequate resources and evidence
- Resource exhaustion (single and repeated OOM)
- Missing private/external evidence that should prevent a kill
- Ambiguous operational signals warranting review
- Cost/risk threshold exceedance

Each scenario includes an oracle label (`continue`, `kill`, or `needs_review`). The council and baseline each produce a decision per scenario; accuracy, false-kill rate, and false-continue rate are computed against oracle labels. The oracle labels are hand-authored and encode the designer's judgments about correct decisions; they are not derived from historical data.

### Self-Application

After evaluation, the prototype is applied to its own project run (`scripts/decide_current_project.py`, 832 bytes), using the actual telemetry and artifacts from this session as input. This serves as a smoke test for the decision procedure on real (albeit favorable) evidence.

## Results

### Unit Tests

Initial test run (log: `.omx/logs/research/pytest.log`): 3 of 4 tests passed. The failing test exposed the repeated-OOM design defect described in the Method section—the council produced `needs_review` for a scenario where repeated OOM events unambiguously warranted `kill`.

After implementing the hard-override fix, rerun (log: `.omx/logs/research/pytest_rerun.log`): **4 of 4 tests passed**, covering:

- Kill veto by evidence-hygiene member
- Hard override for repeated OOM
- Continue quorum
- Override precedence rules

### Synthetic Evaluation

Results from the 15-scenario case matrix (artifact: `results/synthetic_eval.json`):

| Metric | Council | Naive Baseline |
|---|---|---|
| Correct (agreement with oracle) | 15/15 | 6/15 |
| Accuracy | 1.000 | 0.400 |
| False-kill rate | 0.000 | 0.133 |
| False-continue rate | 0.000 | 0.467 |

The council's zero false-kill rate reflects the evidence-hygiene veto: scenarios where a kill would be unsafe due to missing private evidence are correctly downgraded to `needs_review`. The baseline's 0.133 false-kill rate arises from scenarios where the single threshold triggers termination despite evidence dependencies that would have justified continuation or review.

The baseline's 0.467 false-continue rate indicates that nearly half the failure scenarios are missed by a single-threshold approach, as it lacks the multi-dimensional evaluation needed to detect cost/risk exceedance or evidence-hygiene problems that do not correlate with the thresholded metric.

**Important caveat**: The council's perfect accuracy reflects consistency with the hand-authored oracle, which was designed with knowledge of the council's intended behavior. These figures should not be interpreted as an unbiased estimate of production performance.

### Self-Application Decision

The council applied to this project's own run produced a `continue` decision (artifact: `results/current_project_council_decision.json`), consistent with the project's `viable` completion status and adequate available memory (MemAvailable: 122,700,184 kB; SwapTotal: 0 kB). This result is unsurprising—the project had completed successfully at the time of evaluation—and serves primarily as a smoke test rather than a rigorous validation.

### Design Defect Discovered During Development

The initial prototype's handling of repeated OOM conditions constitutes a negative result worth emphasizing. Without the hard-override mechanism, the council would have produced `needs_review` for a scenario that unambiguously warrants `kill`. The operations member voted `kill`, but the aggregation rules allowed other members' votes to downgrade the decision. This demonstrates that even a multi-member council with explicit veto rules can fail to capture certain operational realities if the voting rules do not include non-overridable escape hatches for catastrophic conditions. The defect was caught by a targeted unit test, not by the synthetic case matrix alone, suggesting that scenario coverage was initially insufficient for this edge case.

## Limitations

1. **Synthetic oracle labels.** The 15-scenario case matrix is hand-authored and representative, not derived from historical production traces. The oracle labels encode the designer's judgments about correct decisions; different policy choices could yield different labels. The council's 15/15 accuracy should be interpreted as consistency with the designed oracle, not as a generalization guarantee. The oracle was likely constructed with implicit knowledge of the council's intended behavior, which may inflate accuracy estimates.

2. **No production replay validation.** The prototype has not been evaluated against historical Enoch project traces with known outcomes. Production adoption requires such replay to calibrate thresholds and validate oracle coverage. This is the most significant gap in the current evidence.

3. **Thresholds are policy choices.** The specific numeric thresholds in the prototype (memory cutoffs, cost bounds, OOM repeat counts) are configurable but were set for the synthetic evaluation. Real deployment requires calibration against actual cost and failure data.

4. **Private evidence unavailable.** The Notion page associated with this project returned an empty record map via `loadPageChunk`. If that page contains materially different requirements or constraints, the prototype's design should be reviewed against those requirements. This limitation is itself an instance of the evidence-hygiene problem the council is designed to address.

5. **Small evaluation scale.** Fifteen scenarios are sufficient to demonstrate implementability and basic correctness properties but insufficient to characterize failure modes comprehensively. Edge cases in vote aggregation precedence, tie-breaking, and interaction effects between council members may exist beyond the tested scenarios.

6. **No concurrency or distributed evaluation.** The prototype is single-threaded and single-host. A production control plane may need to handle concurrent project decisions, race conditions in telemetry reads, and distributed evidence aggregation.

7. **Claim ledger audit blocked.** The formal claim ledger for this artifact (`claim_ledger.json`) is in a `blocked_empty_claims` state with no structured claims extracted. No claim in this paper has passed a formal claim/evidence audit. The limitations note in the ledger states that "this artifact must not pass strict claim/evidence audit until claims reference public evidence files."

8. **Evidence bundle is minimal.** The evidence bundle (`evidence_bundle.json`) contains only the source identifier, project ID, and run ID, with no detailed evidence linkage. This limits the auditability of the reported results to the raw artifact files themselves rather than a structured evidence chain.

## Reproducibility Checklist

- [x] **Source code available**: `src/kill_switch_council.py` (SHA256: `70fd9dc3928929560669088f0588f4b33160da32df85e33217e368f198e00890`, 8819 bytes)
- [x] **Test suite available**: `tests/test_kill_switch_council.py` (SHA256: `c987d69cf8f860f45e2728a840d36eeadc6b567816873ad9baac9432f41a5859`, 1340 bytes)
- [x] **Evaluation script available**: `scripts/run_synthetic_eval.py` (SHA256: `10259d13af8849d451a4b9aff6f49ff59c8083161da41982e15049bf46f7775d`, 5492 bytes)
- [x] **Raw evaluation data available**: `results/synthetic_eval.json` (SHA256: `a2444ade8c70774c0cc9e03de3f636676db477e9101daba7ec4b8eaaa1738bb9`, 8241 bytes)
- [x] **Human-readable evaluation summary**: `results/synthetic_eval.md` (SHA256: `072378725d18b759158574f251a39e94ba79f7597c58e7730adaf7e6fd13dc5f`, 1098 bytes)
- [x] **Self-application decision artifact**: `results/current_project_council_decision.json` (SHA256: `056aee778e642af275967bf2ff8fa5eefa297b233c5621435b962cd9bb3d812d`, 1759 bytes)
- [x] **Run notes available**: `run_notes.md` (SHA256: `5ce9c66f7ec45c81fe5cedc0bb24e04cfe52aa5a6dfb96610b4d5063d22aed99`, 3697 bytes)
- [x] **Execution logs preserved**: `.omx/logs/research/pytest.log`, `.omx/logs/research/pytest_rerun.log`, `.omx/logs/research/synthetic_eval_rerun.log`, `.omx/logs/research/telemetry.log`
- [x] **No external dependencies**: Prototype is dependency-free Python
- [x] **Hardware environment documented**: Linux gx10-efe8 aarch64, MemAvailable 122,700,184 kB, SwapTotal 0 kB, earlyoom v1.7
- [ ] **Production replay validation**: Not performed (see Limitations)
- [ ] **Threshold sensitivity analysis**: Not performed
- [ ] **Formal claim/evidence audit**: Claim ledger is in blocked_empty_claims state; no claims have been audited

## Conclusion

The Kill Switch Council prototype demonstrates that a deterministic, evidence-gated multi-member decision procedure is implementable and testable as a control-plane primitive. On a synthetic 15-scenario case matrix, the council achieves perfect agreement with oracle labels and zero false-kill and false-continue rates, substantially outperforming a naive single-threshold baseline (accuracy 0.400, false-kill rate 0.133, false-continue rate 0.467). However, the oracle was hand-authored with knowledge of the council's intended behavior, and the evaluation scale is small, so these figures should be treated as consistency checks rather than unbiased performance estimates.

The development process itself provided a meaningful negative result: the initial design failed to produce a `kill` decision on repeated OOM conditions, requiring a hard-override mechanism. This finding underscores that multi-member voting architectures need non-overridable escape hatches for catastrophic operational conditions, and that such defects may not be apparent from specification alone—the defect was caught by a targeted unit test, not by the initial scenario matrix.

The results are limited to synthetic evaluation and should not be interpreted as production validation. The council pattern appears viable as a local control-plane primitive, particularly because it provides an explicit `needs_review` state and evidence-hygiene vetoes that guard against unsafe false kills when critical evidence is unavailable. However, adoption requires replay on historical project traces, threshold calibration against real cost and failure data, and review against any requirements present in private or external evidence sources not accessible during this evaluation. The blocked claim ledger status further indicates that the evidence chain for this artifact has not yet met the standard for formal claim/evidence audit.

---

## Referenced Artifacts

| Artifact | Path | SHA256 |
|---|---|---|
| Council implementation | `src/kill_switch_council.py` | `70fd9dc3928929560669088f0588f4b33160da32df85e33217e368f198e00890` |
| Test suite | `tests/test_kill_switch_council.py` | `c987d69cf8f860f45e2728a840d36eeadc6b567816873ad9baac9432f41a5859` |
| Synthetic evaluation script | `scripts/run_synthetic_eval.py` | `10259d13af8849d451a4b9aff6f49ff59c8083161da41982e15049bf46f7775d` |
| Self-application script | `scripts/decide_current_project.py` | `c441bf89139cd58b18ef1ccb19f83e72c4e35411c984af168f3802ed78b5760d` |
| Synthetic evaluation data | `results/synthetic_eval.json` | `a2444ade8c70774c0cc9e03de3f636676db477e9101daba7ec4b8eaaa1738bb9` |
| Synthetic evaluation summary | `results/synthetic_eval.md` | `072378725d18b759158574f251a39e94ba79f7597c58e7730adaf7e6fd13dc5f` |
| Current project decision | `results/current_project_council_decision.json` | `056aee778e642af275967bf2ff8fa5eefa297b233c5621435b962cd9bb3d812d` |
| Run notes | `run_notes.md` | `5ce9c66f7ec45c81fe5cedc0bb24e04cfe52aa5a6dfb96610b4d5063d22aed99` |
| Project decision record | `.omx/project_decision.json` | — |
| Claim ledger | `papers/.../claim_ledger.json` | — |
| Evidence bundle | `papers/.../evidence_bundle.json` | — |
| Paper manifest | `papers/.../paper_manifest.json` | — |
| Metrics | `.omx/metrics.json` | — |
| Initial pytest log | `.omx/logs/research/pytest.log` | — |
| Final pytest log | `.omx/logs/research/pytest_rerun.log` | — |
| Synthetic eval log | `.omx/logs/research/synthetic_eval_rerun.log` | — |
| Telemetry log | `.omx/logs/research/telemetry.log` | — |
