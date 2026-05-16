# Self-Maintaining Conformance Test Rigs for Agent Lifecycle Event Envelopes: A Bronze-MVP Prototype

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, claim ledger, and metrics). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

We investigate whether a local conformance test rig for agent lifecycle event envelopes can maintain confidence in its own scoring logic by combining deterministic fixture traces with mutation-based fault probes. We implement a prototype scorer that verifies ten envelope and lifecycle invariants derived from the AgentHook specification, then validate the scorer against itself by injecting six categories of faults into known-good traces and requiring detection of each. In the prototype evaluation, all six fault probes were detected (self-maintenance score 1.0), all five regression tests passed, and the upstream AgentHook package smoke test reported a Bronze-tier pass. However, the upstream formal conformance suite is documented as not yet implemented, and the draft Bronze scenario specification contains unresolved gaps around failure pairing, prompt payload keys, spec-version declaration, deterministic driver contracts, and duplicate delivery semantics. We conclude that a self-maintaining Bronze-MVP test rig is viable as a development harness, but this result does not constitute formal AgentHook conformance certification.

## Introduction

Agent systems that emit structured lifecycle event envelopes require conformance test rigs to verify that published traces satisfy specification invariants. A persistent risk for such rigs is scorer regression: a bug introduced into the scoring logic could silently accept invalid traces, producing false passes that undermine downstream consumers' trust in the conformance result.

The AgentHook specification defines a one-envelope lifecycle evidence model with ten canonical event types and three conformance tiers (Bronze, Silver, Gold). However, the formal machine-checkable conformance suite for these tiers is not yet implemented. Early adopters currently have access only to smoke-test commands, and the draft Bronze scenario document explicitly lists specification gaps that block full automated verification.

This raises a practical question: in the absence of a formal upstream conformance suite, can a local test rig maintain confidence in its own scoring logic? We approach this by building a self-maintaining rig that (a) scores deterministic valid and invalid traces against a defined set of envelope and lifecycle invariants, and (b) verifies its own scorer by injecting known faults into known-good traces and confirming that each fault is detected. This paper reports the design, implementation, and evaluation of that prototype.

## Method

### Specification Baseline

We derived scoring invariants from the following upstream sources, cloned at commit `222cd1da0147aee9188f6f00ec2c06853cb01294`:

- AgentHook `SPEC.md`: defines required envelope fields (`event_id`, `event_type`, `timestamp`, `source`), canonical event names, and pre/post lifecycle semantics.
- AgentHook `CONFORMANCE/README.md`: documents that the formal Bronze/Silver/Gold suite is not implemented and that early adopters have smoke-test commands only.
- AgentHook `CONFORMANCE/scenarios-bronze-draft.md`: provides draft Bronze scenario categories and explicitly lists gaps that block full machine-checkable conformance.

### Scoring Invariants

The local scorer verifies the following ten invariants on each trace:

1. Required envelope fields exist.
2. `event_id` is a valid UUID.
3. `event_type` is one of the ten canonical AgentHook events.
4. `timestamp` parses as a datetime and is non-decreasing across the trace.
5. `source` is present and appears stable.
6. Object-valued fields (`tool_input`, `metadata`, `annotations`) are objects.
7. `PreToolUse` and `PostToolUse` events include `tool_name`.
8. Distinct events do not reuse the same `event_id`.
9. `PreLLMCall`/`PostLLMCall` and `PreToolUse`/`PostToolUse` pairing is balanced and ordered.
10. Session boundaries and single-session consistency hold for the deterministic MVP fixture.

### Self-Maintenance Mutation Probes

To verify that the scorer catches regressions, the self-maintenance loop intentionally mutates a known-good trace and requires the scorer to detect each injected fault. Six probe categories are encoded:

- Missing required field
- Invalid UUID in `event_id`
- Duplicate `event_id` on a distinct event
- Timestamp regression (out-of-order timestamp)
- Orphan `PostToolUse` (no matching `PreToolUse`)
- Missing `tool_name` on a tool-use event

Each probe produces a mutated trace; the scorer must reject it. A self-maintenance score is computed as the fraction of injected faults detected.

### Implementation

The prototype consists of the following files:

| File | Role |
|------|------|
| `src/test_rig_self_maintainer/rig.py` | Deterministic trace builder, Bronze-style scorer, and self-maintenance mutation probes |
| `src/test_rig_self_maintainer/__init__.py` | Package exports |
| `tests/test_rig.py` | Regression tests for valid traces, explicit error path, duplicate IDs, orphan post events, and all self-maintenance probes |
| `pyproject.toml` | Minimal project metadata and pytest path configuration |

The implementation is fixture-based: it constructs deterministic traces programmatically rather than capturing output from a live agent runtime. This is a deliberate scope restriction for the Bronze-MVP prototype; it means the rig validates structural and ordering invariants on synthetic traces but does not exercise a live agent runtime end-to-end.

## Results

### Regression Tests

```
python3 -m pytest -q
```

Result: **5 passed in 0.01s.** Tests cover valid trace acceptance, explicit error-path rejection, duplicate ID detection, orphan post-event detection, and self-maintenance probe execution.

### Self-Maintenance Mutation Probes

```
python3 src/test_rig_self_maintainer/rig.py --out artifacts/self_maintenance_report.json
```

Result: **passed = true; score = 1.0; 6/6 fault probes detected.** Every injected mutation was caught by the scorer.

### Upstream AgentHook Smoke Test

```
PYTHONPATH=external/agenthook/packages/python python3 -m agenthook.cli test publisher --source test-rig-self-maintainer
```

Result: **Bronze: pass; Silver: partial; Gold: partial.** The partial results for Silver and Gold are expected given that the prototype targets Bronze-level invariants only. The "partial" status for Silver and Gold reflects the upstream smoke-test command's behavior when run against a source that does not emit the richer transcript and reasoning evidence those tiers require; it should not be interpreted as partial conformance.

### Upstream AgentHook Package Tests

```
PYTHONPATH=external/agenthook/packages/python python3 -m unittest discover -s external/agenthook/packages/python/tests -q
```

Result: **Ran 6 tests ... OK.**

### Syntax and Import Check

```
python3 -m compileall -q src tests
```

Result: **exit 0** (no syntax or import errors).

### Environment

- Python: 3.12.3
- Platform: Linux aarch64 / NVIDIA kernel

All results were collected in a single session on a single platform. No cross-platform or repeated-run variance data are available.

## Limitations

1. **Not formal conformance certification.** The upstream AgentHook conformance documentation states that the formal Bronze/Silver/Gold suite is not yet implemented. Our prototype covers a deterministic Bronze-MVP subset and does not constitute a certified conformance result.

2. **Incomplete Bronze scenario coverage.** The draft Bronze scenario document lists 21 scenarios; the prototype currently encodes a subset of invariants rather than the full scenario catalog. Coverage of the full draft scenario set has not been attempted.

3. **Unresolved specification gaps.** The upstream draft explicitly notes gaps around failure pairing semantics, prompt payload key requirements, spec-version declaration, deterministic driver contracts, and duplicate delivery semantics. These gaps mean that some invariants the scorer checks may not align with a future formal specification, and other invariants that a formal spec would require are not yet checkable.

4. **Fixture-based, not runtime-based.** The trace builder constructs deterministic traces programmatically. It does not exercise a live agent runtime end-to-end, so it cannot validate that real agent outputs satisfy the same invariants the fixture traces satisfy. The positive results reported here apply only to the synthetic fixture traces.

5. **Self-maintenance probe coverage is manual.** The six mutation probe categories were hand-selected. They do not automatically expand as new scoring invariants are added, creating a risk that future invariants lack corresponding negative probes. A scorer regression that affects an unchecked invariant would not be caught by the current self-maintenance loop.

6. **Single-platform, single-run evidence.** All results were collected on one platform (Linux aarch64) in a single session. No cross-platform or repeated-run variance data are available, so we cannot rule out platform-specific or non-deterministic failures.

7. **Medium-high confidence only.** The project decision records confidence as "medium-high," reflecting the fact that while all prototype tests pass, the unresolved upstream specification gaps limit the strength of any conformance-related conclusion.

## Reproducibility Checklist

- [x] Source code for the prototype is included (`src/test_rig_self_maintainer/rig.py`, `__init__.py`)
- [x] Test suite is included (`tests/test_rig.py`)
- [x] Project configuration is included (`pyproject.toml`)
- [x] Machine-readable self-maintenance report is included (`artifacts/self_maintenance_report.json`)
- [x] Run metrics are included (`artifacts/metrics.json`)
- [x] Command outputs are logged (`logs/pytest-final.log`, `logs/self-maintenance-run.log`, `logs/agenthook-publisher-smoke.log`, `logs/agenthook-upstream-tests.log`, `logs/compileall.log`)
- [x] Upstream AgentHook commit hash is recorded (`222cd1da0147aee9188f6f00ec2c06853cb01294`)
- [x] Python version and platform are recorded (3.12.3, Linux aarch64)
- [x] All commands used to produce results are documented in run notes
- [ ] Cross-platform replication: not performed
- [ ] Independent re-run by a different operator: not performed
- [ ] Formal conformance certification: not applicable (upstream suite not implemented)

## Conclusion

A compact self-maintaining conformance test rig for agent lifecycle event envelopes is viable as a Bronze-MVP development harness. The key evidence is that the prototype scorer accepts deterministic valid traces, rejects an explicit error-path trace, and catches all six currently encoded mutation probes (score 1.0). This directly reduces the risk that a future scorer bug silently turns invalid publisher traces into false passes.

However, this result is bounded in important ways. The upstream formal conformance suite is not yet implemented, and the draft Bronze scenarios contain unresolved specification gaps. The prototype covers a deterministic subset of invariants, not the full scenario catalog, and its traces are fixture-generated rather than captured from a live agent runtime. The self-maintenance probes are hand-encoded and do not automatically expand with new scoring invariants. The single-platform, single-run evidence limits generalizability.

The recommended next step is to encode the draft Bronze scenarios as a versioned JSON or YAML scenario manifest with expected sequence constraints, then derive mutation probes automatically from that manifest. This would ensure that every new scenario generates at least one corresponding negative probe, improving maintenance coverage as the rig grows and reducing the risk of silent scorer regressions.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Scorer and self-maintenance logic | `src/test_rig_self_maintainer/rig.py` |
| Package exports | `src/test_rig_self_maintainer/__init__.py` |
| Regression tests | `tests/test_rig.py` |
| Project configuration | `pyproject.toml` |
| Self-maintenance report | `artifacts/self_maintenance_report.json` |
| Run metrics | `artifacts/metrics.json` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Pytest log | `logs/pytest-final.log` |
| Self-maintenance run log | `logs/self-maintenance-run.log` |
| AgentHook publisher smoke log | `logs/agenthook-publisher-smoke.log` |
| AgentHook upstream tests log | `logs/agenthook-upstream-tests.log` |
| Compile check log | `logs/compileall.log` |
| AgentHook source (cloned) | `external/agenthook` at commit `222cd1da0147aee9188f6f00ec2c06853cb01294` |
| Claim ledger | `papers/source-record-redacted-20260502T163618592868+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T163618592868+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T163618592868+0000/paper_manifest.json` |
