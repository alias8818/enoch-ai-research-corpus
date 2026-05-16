# Proof-Carrying PRs: CI-Enforced Evidence Contracts for Pull Requests

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision records, metrics, and log files). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present Proof-Carrying PRs (PCPR), a mechanism for enforcing evidence contracts on pull requests through machine-verifiable proof bundles. A proof bundle is a structured collection of claims and their supporting evidence records, verified by a lightweight, dependency-free checker designed for CI integration. We implement a prototype verifier and evaluate it against synthetic positive and adversarial fixtures. In prototype evaluation, the verifier correctly accepts a well-formed bundle (3 claims, 3 evidence records, 0 errors) and rejects all three adversarial fixture types (tampered evidence, missing claims, and path-escape attempts). However, no live CI integration, cryptographic attestation, or real-world PR evaluation was performed. The structured claim ledger for this artifact remains in a blocked audit state with no formal claims extracted, reflecting the preliminary nature of the evidence. We conclude that PCPR is viable as a CI-enforced evidence contract but emphasize that author-supplied bundles do not constitute trustworthy cryptographic proof unless a trusted CI environment independently regenerates or attests the evidence.

## Introduction

Code review on pull requests (PRs) typically relies on human judgment to verify that claimed properties—test coverage, lint compliance, build success—actually hold. Reviewers must either re-run checks locally or trust CI status indicators, which may be spoofable or stale. This trust gap motivates a more rigorous approach: requiring that PRs carry machine-checkable evidence of the properties they claim.

The concept of proof-carrying code, in which programs are accompanied by formal proofs of safety properties checkable by a simple verifier, has a well-established history in programming languages research. We adapt this idea to the PR workflow: a *proof bundle* accompanies each PR, containing structured claims and evidence records. A CI-integrated verifier checks the bundle's internal consistency and rejects the PR if claims lack supporting evidence or if evidence appears tampered.

This paper reports on a prototype implementation and its evaluation against synthetic fixtures. We deliberately limit our claims: this is a feasibility demonstration, not a production deployment. No real PRs were processed, no GitHub App integration was exercised, and no cryptographic attestation layer was implemented. The claim ledger associated with this artifact was flagged as blocked during audit, with no structured claims extracted, which should temper confidence in the results reported here.

## Method

### Design

A PCPR proof bundle is a directory containing:

1. **Claims**: Structured assertions about the PR (e.g., "all tests pass," "no new lint errors," "build succeeds").
2. **Evidence records**: Artifacts supporting each claim (e.g., test output, lint logs, build logs).
3. **Manifest**: A mapping from claims to their supporting evidence.

The verifier checks:

- Every claim has at least one linked evidence record.
- Evidence records reference files that exist within the bundle.
- No evidence path escapes the bundle directory (preventing path traversal attacks).
- Evidence has not been tampered with relative to the manifest (integrity check).

### Implementation

We implemented a dependency-free Python verifier (`src/pcpr/verify.py`). The choice of zero external dependencies was deliberate: it minimizes supply-chain attack surface and simplifies CI installation. The verifier can be invoked as:

```
python3 src/pcpr/verify.py <bundle-path> --json
```

It exits with code 0 on acceptance and code 1 on rejection, producing JSON output summarizing claims, evidence records, and any errors.

A CI workflow sketch (`.github/workflows/proof-carrying-pr.yml`) was created to illustrate integration, but was not exercised against a live repository.

### Test Fixtures

Four fixtures were created under `fixtures/`:

| Fixture | Type | Expected Outcome |
|---|---|---|
| `good` | Positive | Accepted |
| `tampered` | Negative (integrity violation) | Rejected |
| `missing-claim` | Negative (orphaned evidence) | Rejected |
| `path-escape` | Negative (path traversal) | Rejected |

### Evaluation Protocol

1. Run the verifier against each fixture.
2. Record exit code and JSON output.
3. Run the unit test suite (`tests/test_verify.py`).
4. Verify all source files compile without errors.

All commands and outputs were logged with timestamps.

## Results

### Unit Tests

The test suite comprised 4 tests, all passing:

| Metric | Value |
|---|---|
| Tests passed | 4 |
| Tests failed | 0 |

### Fixture Verification

| Fixture | Exit Code | Claims | Evidence Records | Errors | Outcome |
|---|---|---|---|---|---|
| `good` | 0 | 3 | 3 | 0 | Accepted |
| `tampered` | 1 | — | — | — | Rejected |
| `missing-claim` | 1 | — | — | — | Rejected |
| `path-escape` | 1 | — | — | — | Rejected |

All three negative fixtures were rejected for their expected reasons. The positive fixture was accepted with all claims and evidence records accounted for.

### Build and Environment

- All source files under `src/` and `tests/` compiled without errors.
- No external dependencies were installed.
- Environment telemetry confirmed expected memory posture (swap disabled, `MemAvailable` captured in environment log).

### Claim Ledger Audit Status

The structured claim ledger for this artifact was evaluated and received an audit status of `blocked_empty_claims`, with no formal claims extracted. The ledger notes that the artifact "must not pass strict claim/evidence audit until claims reference public evidence files." This status indicates that the evidence presented in this paper has not been subjected to formal claim-evidence binding and should be interpreted accordingly.

### Summary

The prototype verifier correctly discriminates between well-formed and adversarial proof bundles in all tested synthetic cases. However, this evaluation is limited to four fixtures in a controlled environment, and the associated claim ledger did not pass audit.

## Limitations

1. **No live CI integration.** The GitHub Actions workflow was sketched but never executed against a real repository. The verifier's behavior under real CI conditions (concurrent runs, network failures, large repositories) is unknown.

2. **No cryptographic attestation.** The current integrity check detects simple tampering within the bundle but does not employ cryptographic signatures or Sigstore/GitHub attestation. A sophisticated attacker who controls the bundle could forge both evidence and manifest.

3. **Author-supplied bundles are not trustworthy in isolation.** The central limitation of PCPR as currently implemented is that an author who supplies a proof bundle also controls its contents. Unless a trusted CI environment independently regenerates or verifies the evidence and then signs or attests the bundle, the "proof" is only as trustworthy as the author. This is a fundamental trust assumption, not an implementation bug.

4. **No real-world evaluation.** No real PRs were processed. Metrics such as reviewer time saved, false-positive rate, and developer experience friction remain unmeasured.

5. **Fixture coverage is minimal.** Four fixtures exercise three failure modes. Edge cases such as empty bundles, extremely large evidence files, Unicode path names, and symlink attacks were not tested.

6. **No SLSA or supply-chain integration.** The prototype does not integrate with SLSA provenance frameworks or GitHub's attestation API, which would be necessary for release-bound proof summaries.

7. **Claim ledger audit failure.** The formal claim ledger for this artifact is in a blocked state with no extracted claims. This means the results reported here lack the structured claim-evidence binding that PCPR itself advocates, representing an internal inconsistency that should be resolved in future work.

## Reproducibility Checklist

- [x] Source code available: `src/pcpr/verify.py`
- [x] Test suite available: `tests/test_verify.py`
- [x] Fixtures available: `fixtures/{good,tampered,missing-claim,path-escape}`
- [x] CI workflow sketch available: `.github/workflows/proof-carrying-pr.yml`
- [x] Test execution log: `logs/pytest-20260429T233730Z.log`
- [x] Verification logs for all fixtures: `logs/verify-*-20260429T233737Z.json`
- [x] Compilation log: `logs/compileall-20260429T233743Z.log`
- [x] Environment log: `logs/env-20260429T233744Z.log`
- [x] Metrics file: `reports/metrics.json`
- [x] Project decision record: `.omx/project_decision.json`
- [x] Research report: `docs/proof-carrying-prs-report.md`
- [x] Zero external dependencies required
- [ ] Live CI integration tested
- [ ] Cryptographic attestation implemented
- [ ] Real-world PR evaluation conducted
- [ ] Claim ledger audit passed

## Conclusion

Proof-Carrying PRs offer a viable mechanism for enforcing evidence contracts on pull requests. Our prototype demonstrates that a dependency-free verifier can correctly accept well-formed proof bundles and reject common adversarial patterns (tampered evidence, missing claims, path-escape attempts) across all four tested fixtures.

However, the current prototype is a feasibility demonstration, not a production system. The critical gap is trust: author-supplied proof bundles are self-attesting and therefore not cryptographically meaningful unless a trusted CI environment independently regenerates or verifies the evidence and produces a signed attestation. Without this layer, PCPR functions as a structured evidence contract—a useful discipline—but not as a proof in the formal or cryptographic sense.

An additional irony deserves acknowledgment: the claim ledger for this very artifact failed audit, receiving a `blocked_empty_claims` status. The PCPR approach advocates for structured claim-evidence binding, yet this paper's own evidence was not subjected to the discipline it proposes. Resolving this gap—applying PCPR to its own artifacts—is a necessary step before the approach can be recommended with confidence.

Next steps include: (1) integrating the verifier into a GitHub App or required check-run, (2) adding Sigstore or GitHub attestation verification for release-bound proof summaries, (3) evaluating the system on real PRs to measure reviewer time savings and false-positive rates, and (4) applying the PCPR discipline to the project's own outputs so that the claim ledger passes audit. Until these steps are completed, PCPR remains a promising but unvalidated approach.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Verifier source | `src/pcpr/verify.py` |
| Unit tests | `tests/test_verify.py` |
| Positive fixture | `fixtures/good` |
| Negative fixture (tampered) | `fixtures/tampered` |
| Negative fixture (missing claim) | `fixtures/missing-claim` |
| Negative fixture (path escape) | `fixtures/path-escape` |
| CI workflow sketch | `.github/workflows/proof-carrying-pr.yml` |
| Research report | `docs/proof-carrying-prs-report.md` |
| Metrics | `reports/metrics.json` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260429T233518353199+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T233518353199+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T233518353199+0000/paper_manifest.json` |
| Pytest log | `logs/pytest-20260429T233730Z.log` |
| Verify good log | `logs/verify-good-20260429T233737Z.json` |
| Verify tampered log | `logs/verify-tampered-20260429T233737Z.json` |
| Verify missing-claim log | `logs/verify-missing-claim-20260429T233737Z.json` |
| Verify path-escape log | `logs/verify-path-escape-20260429T233737Z.json` |
| Compile log | `logs/compileall-20260429T233743Z.log` |
| Environment log | `logs/env-20260429T233744Z.log` |
| Session metrics | `.omx/metrics.json` |
| Run notes | `run_notes.md` |
