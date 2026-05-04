# Enoch Experiment Lifecycle Gate Integration: Eliminating Silent Orphaned Projects via Durable-Artifact State Evaluation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, evaluation metrics, and verification logs). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review is asserted or required by this notice.

---

## Abstract

Autonomous experiment management systems that enqueue and execute projects without enforcing terminal-state decisions accumulate "silent orphans": project rows bearing durable run evidence (logs, results, run notes) but lacking a recorded terminal lifecycle decision, rendering them invisible to review and archival. This paper reports on the integration of a lifecycle gate into the Enoch LangGraph control plane, implementing the state machine `idea → claim → setup → run → result → interpretation → next_action → archive` as a durable-artifact evaluator. In an observational audit of 827 sibling project directories, 204 rows (24.7%) were identified as evidence-bearing orphans without terminal decisions. After applying the integrated lifecycle gate in a temporary control-plane store, the count of silent orphans dropped to zero, with 220 nonterminal evidence-bearing rows surfaced as `needs_review` and 619 rows advanced to `archive`. Regression tests (20 passed) and compile verification confirm implementation correctness. These results are observational rather than from a live deployed A/B comparison; final production orphan-rate deltas require deployment and subsequent queue monitoring.

## Introduction

Autonomous research orchestration systems face a governance problem: projects that produce intermediate artifacts (run logs, result files, evaluation scripts) but never reach a recorded terminal decision become invisible to both human review and automated archival. We term these *silent orphans*—project rows that appear completed or queued in the control plane but lack the `.omx/project_decision.json` or equivalent terminal artifact that signals a deliberate conclusion.

A prior manual audit of the Enoch system identified 25 orphaned projects. However, that audit sampled a subset of the project population. A broader scan was needed to assess the true scope and to validate a structural fix.

The parent Experiment State Machine defines a lifecycle: `idea → claim → setup → run → result → interpretation → next_action → archive`. The hypothesis under test was that wiring this lifecycle as a gate—evaluating durable local artifacts and queue metadata to determine whether a project has reached a terminal state—would eliminate silent orphans by surfacing nonterminal evidence-bearing projects as `needs_review` rather than allowing them to persist in ambiguous states.

This paper reports on the implementation and evaluation of that integration.

## Method

### System Architecture

The lifecycle gate was implemented as a set of changes to the Enoch wake-gate control plane at `/mnt/usb<local-path-redacted>`:

1. **`lifecycle.py` (new module):** A durable-artifact lifecycle evaluator. It inspects Notion/project metadata, run fields, `run_notes.md`, and `.omx/project_decision.json` to determine the lifecycle state of each project row. Projects with evidence artifacts but no terminal decision are classified as `needs_review`; projects with a terminal decision are advanced to `archive` (or the appropriate terminal state).

2. **`models.py` (modified):** Extended the queue row model with `lifecycle_state` and `lifecycle_blockers_json` fields, enabling the control plane to persist and expose the gate's evaluation per project.

3. **`store.py` (modified):** Schema bumped to v2. On process start, the store migrates legacy SQLite databases by adding the two new columns if absent. New methods `refresh_lifecycle_gate()` and `refresh_all_lifecycle_gates()` re-evaluate lifecycle state for individual or all project rows. Lifecycle state is projected to Notion fields via the existing sync path.

4. **`router.py` (modified):** Added `POST /control/lifecycle/refresh` to expose the lifecycle gate as an executable controller API endpoint, enabling on-demand re-evaluation without process restart.

### Evaluation Design

The evaluation used `scripts/evaluate_lifecycle_gate.py`, which imports sibling Enoch project rows into a *temporary* control-plane store and measures lifecycle-gate behavior without mutating production state. This design isolates the gate's logic from the live queue.

The evaluation scanned all 827 current sibling project directories under the configured root, accepting logs, results, and `run_notes.md` as durable evidence of project activity. Projects with such evidence but no terminal `.omx/project_decision.json` were counted as baseline orphans. The gate was then applied, and post-gate state distributions were recorded.

This constitutes a hook-prototype evaluation: the gate logic is integrated into the live control-plane code path, but the audit was executed against a temporary store rather than the production database.

### Verification

Two levels of verification were performed:

1. **Static compilation:** All four modified/new Python modules were compiled via `python3 -m py_compile` to confirm syntactic validity. Result: passed (recorded in `logs/lifecycle_gate_verification.log`).

2. **Regression tests:** The full test suite (store, router, dispatch endpoint, Notion sync) was executed:

   ```
   20 passed, 4 warnings in 0.48s
   ```

   Warnings were pre-existing FastAPI `on_event` deprecations, unrelated to the lifecycle gate changes.

## Results

### Baseline Orphan Count

The broad scan identified **204** sibling project rows with durable run/result evidence but no terminal lifecycle decision. This figure exceeds the parent audit's 25-project count because the evaluation scanned all 827 directories (rather than a sampled subset) and accepted a wider set of artifacts (logs, results, run notes) as evidence of project activity. The two figures are not directly comparable due to differing populations and evidence-acceptance criteria.

### Post-Gate State Distribution

After applying the lifecycle gate in the temporary store:

| Lifecycle State | Count |
|---|---|
| `archive` | 619 |
| `next_action` | 36 |
| `result` | 168 |
| `run` | 4 |

Projected to status-level aggregation:

| Status | Count |
|---|---|
| `completed` | 606 |
| `needs_review` | 220 |
| `blocked` | 1 |

**Silent orphans after gate: 0.** All 204 evidence-bearing orphans were surfaced as `needs_review` (along with 16 additional rows that were in nonterminal lifecycle states for other reasons), making them visible for human or automated review.

### Composition of Surfaced Projects

The 220 `needs_review` rows include temporary preparation artifacts (e.g., `tmp-prepare-webhook-001`, `smoke-prepare-handoff-20260413T0038Z`, `prepare-smoke-001`) and idea-stage projects that accumulated evidence without reaching a decision (e.g., `source-record-redacted` and 16 similar idea-prefixed IDs). This distribution suggests that both smoke-test scaffolding and genuine research ideas contribute to the orphan population.

### Mixed Observations

While the elimination of silent orphans is a structurally positive result, several caveats temper the interpretation:

- The 220 `needs_review` rows represent a substantial review backlog that did not previously exist as a visible workload. Surfacing orphans creates an operational obligation.
- One row was classified as `blocked`, indicating the gate identified a project that cannot proceed but also cannot be archived. The gate surfaces such cases but does not resolve them.
- The `result` (168) and `run` (4) lifecycle states represent projects that have progressed past execution but have not yet reached interpretation or next-action stages. These are correctly classified by the gate but remain incomplete.

## Limitations

1. **Observational, not interventional.** The evaluation applied the lifecycle gate to a temporary store rather than the live production queue. The measured orphan reduction (204 → 0 silent orphans) reflects gate logic applied in isolation, not a deployed A/B comparison. Live queue behavior may differ due to concurrent mutations, timing, or Notion sync latency.

2. **Incomparable baselines.** The 204 baseline orphans are not directly comparable to the parent audit's 25 because the scan populations and evidence-acceptance criteria differ. The parent audit sampled a subset; this evaluation scanned all 827 directories. The appropriate interpretation is that the orphan problem is substantially larger than the initial sample suggested, and the gate addresses it structurally—but the magnitude of improvement relative to the original baseline cannot be precisely quantified.

3. **Artifact-based inference, not direct Notion writes.** The lifecycle evaluator reads durable local artifacts and queue metadata. It does not directly write to Notion; it exposes projections and refresh state for the existing Notion sync path. Orphan visibility in Notion depends on the sync path executing after a refresh.

4. **Schema migration dependency.** Existing live SQLite databases require the v2 migration (adding `lifecycle_state` and `lifecycle_blockers_json` columns) to run on process start. The code handles this automatically for missing columns, but deployment requires a process restart.

5. **No measurement of review throughput.** Surfacing 220 rows as `needs_review` eliminates silent orphans but does not guarantee timely human review. The gate makes orphans *visible*; resolving them remains a separate operational concern. The net effect on project governance depends on whether the surfaced backlog is actually processed.

6. **Single evaluation run.** The audit was executed once. Reproducibility depends on the stability of the sibling project directory contents and the evaluator's deterministic logic. No independent re-execution has been performed.

7. **No live production validation.** The lifecycle gate has not been exercised against the deployed control plane with real concurrent mutations. The `readiness_audit` signal is flagged as missing in the review metadata, indicating that production readiness has not been formally assessed.

## Reproducibility Checklist

- [x] **Code available:** Modified files are in `omx_wake_gate/omx_wake_gate/control_plane/` (`lifecycle.py`, `models.py`, `store.py`, `router.py`).
- [x] **Evaluation script available:** `scripts/evaluate_lifecycle_gate.py`.
- [x] **Metrics artifact available:** `results/lifecycle_gate_metrics.json`.
- [x] **Verification log available:** `logs/lifecycle_gate_verification.log`.
- [x] **Evaluation log available:** `logs/lifecycle_gate_eval.log`.
- [x] **Decision artifact available:** `.omx/project_decision.json`.
- [x] **Run notes available:** `run_notes.md`.
- [x] **Test suite:** `tests/test_control_plane_store.py`, `tests/test_control_plane_router.py`, `tests/test_dispatch_endpoint.py`, `tests/test_notion_sync.py` — 20 tests passing.
- [ ] **Live production validation:** Not yet performed. Requires deployment, schema migration, and `POST /control/lifecycle/refresh` execution with subsequent queue monitoring.
- [ ] **Independent re-execution of the audit:** Not yet performed by a second operator or environment.
- [ ] **Readiness audit:** Not yet performed; flagged as a missing signal in the review metadata.

## Conclusion

Integrating the Experiment State Machine lifecycle gate into the Enoch control plane structurally eliminates silent orphaned projects by requiring a terminal `.omx/project_decision.json` before a project can be archived or marked completed. In an observational audit of 827 projects, 204 evidence-bearing orphans were identified at baseline; after gate application, zero silent orphans remained, with 220 nonterminal rows surfaced as `needs_review`.

The implementation is complete at the code level: the lifecycle evaluator, schema migration, API refresh endpoint, Notion projection fields, and regression tests are all in place. The result supports the hypothesis that a durable-artifact lifecycle gate is a viable mechanism for orphan elimination.

However, the evidence remains at the hook-prototype level: the gate was evaluated in a temporary store, not under live production conditions. The critical remaining step is deployment—the live control plane must be restarted to apply the v2 schema migration, followed by execution of `POST /control/lifecycle/refresh` and monitoring of Notion execution projections to confirm that the observational results hold under production conditions. Until that validation occurs, the orphan elimination result should be treated as a promising prototype finding rather than a confirmed production outcome.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Lifecycle evaluator | `omx_wake_gate/omx_wake_gate/control_plane/lifecycle.py` |
| Queue row model | `omx_wake_gate/omx_wake_gate/control_plane/models.py` |
| Store (schema v2) | `omx_wake_gate/omx_wake_gate/control_plane/store.py` |
| Router (refresh endpoint) | `omx_wake_gate/omx_wake_gate/control_plane/router.py` |
| Store tests | `omx_wake_gate/tests/test_control_plane_store.py` |
| Router tests | `omx_wake_gate/tests/test_control_plane_router.py` |
| Dispatch endpoint tests | `omx_wake_gate/tests/test_dispatch_endpoint.py` |
| Notion sync tests | `omx_wake_gate/tests/test_notion_sync.py` |
| Evaluation script | `scripts/evaluate_lifecycle_gate.py` |
| Evaluation metrics | `results/lifecycle_gate_metrics.json` |
| Verification log | `logs/lifecycle_gate_verification.log` |
| Evaluation log | `logs/lifecycle_gate_eval.log` |
| Claim ledger | `papers/source-record-redacted-20260430T234448438950+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T234448438950+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T234448438950+0000/paper_manifest.json` |
| Notion page | `https://www.notion.so/Enoch-Experiment-Lifecycle-Gate-Integration-source-record-redacted` |
