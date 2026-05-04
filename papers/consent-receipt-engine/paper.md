# Consent Receipt Engine: A Proof-of-Concept Implementation for Interoperable Consent Record and Receipt Generation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by an autonomous research pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated the claims, code, or conclusions herein.

---

## Abstract

We present a proof-of-concept Consent Receipt Engine that records consent events, validates required notice and processing fields, issues a principal-facing receipt, and preserves a controller-side record for later audit or withdrawal. The design is informed by ISO/IEC TS 27560:2023 (consent record/receipt information structure), ISO/IEC 29184:2020 (online privacy notice and consent controls), the Kantara Consent Receipt Specification v1.1.0, and GDPR Article 7's requirement for demonstrable consent and symmetric withdrawal. A dependency-free Python implementation generates linked record–receipt bundles with stable identifiers and content hashes. In local testing, 3 validation tests passed, and a synthetic throughput benchmark produced approximately 34,377 receipt bundles per second over 10,000 bundles. These results establish baseline mechanical viability but do not constitute production validation; significant gaps remain in secure storage, access control, jurisdiction-specific legal review, and schema versioning against the forthcoming revision of ISO/IEC TS 27560. The claim ledger for this artifact was audited as blocked with no structured claims extracted, meaning no claim in this paper has passed formal evidence audit.

---

## Introduction

Privacy regulations increasingly require data controllers to demonstrate that consent was obtained validly and to enable consent withdrawal with equal facility. GDPR Article 7 imposes both obligations explicitly. However, the software mechanisms for issuing, storing, and verifying consent records remain fragmented across platforms and jurisdictions.

Several standards bodies have attempted to provide interoperable structures:

- **ISO/IEC TS 27560:2023** defines an open, extensible information structure for recording PII principals' consent, providing consent records and receipts, exchanging consent information, and managing lifecycle. This technical specification is currently marked for revision, introducing schema versioning risk.
- **ISO/IEC 29184:2020**, confirmed as current through 2026-03-20, defines controls for online privacy notices and consent processes.
- **Kantara Consent Receipt Specification v1.1.0** provides a JSON-representable consent receipt format as a human-readable record of authority granted by a PII principal to a PII controller.

These standards create demand but do not supply a concrete, deployable engine. This work investigates whether a minimal, dependency-free software artifact can bridge the gap: accepting a consent event, validating required fields, generating a linked controller-side record and principal-facing receipt, and preserving sufficient structure for later audit or withdrawal.

The central question is not whether such an engine is legally sufficient in any jurisdiction—that requires jurisdiction-specific review—but whether the mechanical core is viable as a software artifact.

---

## Method

### Design Criteria

The engine was designed to satisfy the following field-level requirements, derived from the referenced standards:

1. A consent event must contain: controller identity, principal identity, notice reference, processing purpose, PII categories, consent type, timestamps, and a withdrawal URL.
2. The engine must produce two linked artifacts per consent event:
   - A **controller-side record** preserving the full consent event and metadata for audit.
   - A **principal-facing receipt** suitable for display or delivery to the data subject.
3. Both artifacts must carry stable identifiers and content hashes to support integrity verification.
4. The implementation must be dependency-free (standard library only) to minimize supply-chain risk.

### Implementation

A single-file Python module (`src/consent_receipt_engine.py`) implements the engine. The module defines:

- A **validation function** that checks a consent event dictionary for the presence and non-emptiness of all required fields.
- A **record generation function** that produces a controller-side record including the full event, a unique record identifier, a content hash (SHA-256), and creation timestamps.
- A **receipt generation function** that produces a principal-facing receipt including a subset of fields, a unique receipt identifier, a content hash, and a link to the corresponding record identifier.
- A **bundle generation function** that composes record and receipt into a single output structure.

No external libraries, databases, or network services are used. Identifiers are generated using Python's `uuid4`. Hashes are computed using `hashlib.sha256` over the canonical JSON serialization of the record or receipt content.

### Testing

Three unit tests (`tests/test_consent_receipt_engine.py`) were implemented:

1. **Valid consent event** — verifies that a complete event passes validation and produces a bundle containing both a record and a receipt with matching and well-formed identifiers and hashes.
2. **Missing required field** — verifies that an event missing a required field fails validation.
3. **Receipt–record linkage** — verifies that the receipt references the correct record identifier and that content hashes are distinct and well-formed.

Tests were executed with `pytest`. Full test output is recorded in `logs/test.log`.

### Benchmarking

A synthetic throughput benchmark was executed: generating 10,000 consent receipt bundles in a tight loop, measuring wall-clock time. The benchmark was run on the local development machine; hardware specifications were not recorded. Benchmark output is recorded in `logs/benchmark.log` and `metrics/benchmark.json`.

---

## Results

### Test Results

All 3 tests passed in 0.01 seconds. The validation function correctly accepted complete events and rejected events with missing fields. Record and receipt identifiers were unique UUIDs. Content hashes were valid 64-character hexadecimal SHA-256 digests. Receipt-to-record linkage was confirmed.

### Benchmark Results

| Metric | Value |
|---|---|
| Bundles generated | 10,000 |
| Total wall-clock time | 0.290891 seconds |
| Throughput | ~34,377.14 receipts/sec |

This benchmark measures in-process Python object creation, serialization, and hashing with no I/O, no network calls, and no persistence. It represents an upper bound on generation throughput for this implementation under synthetic conditions. Production throughput with storage, encryption, and network delivery will be substantially lower.

### Sample Output

A sample receipt bundle (`sample_receipt_bundle.json`) was generated, containing both the controller-side record and the principal-facing receipt with linked identifiers and content hashes. This artifact is available in the project directory.

### Claim Audit Status

The claim ledger for this artifact was audited with status `blocked_empty_claims`: no structured claims were extracted, and the audit notes that the artifact must not pass strict claim/evidence audit until claims reference public evidence files. The results reported above are drawn directly from local prototype execution logs and benchmark output but have not undergone independent claim-level verification.

---

## Limitations

1. **No production validation.** The implementation is a proof of concept with no secure storage, no access controls, no encryption at rest or in transit, and no integration with withdrawal execution workflows. Deploying this engine in production would require all of these.

2. **No jurisdiction-specific legal review.** Field-level compliance with GDPR, CCPA, LGPD, or other frameworks was not assessed. The engine validates structural completeness, not legal sufficiency. Real notices, user interfaces, and consent flows require evidence beyond what this artifact provides.

3. **Minimal test coverage.** Three unit tests cover the primary happy path and one failure mode. Edge cases—malformed inputs, duplicate identifiers under concurrency, hash collisions, timestamp manipulation, and field value semantics—are not tested.

4. **Synthetic benchmark only.** The throughput figure reflects in-memory Python computation on unspecified hardware. It does not account for database writes, network latency, concurrent access, or cryptographic signing overhead. The number should not be cited as a production performance claim.

5. **Schema versioning risk.** ISO/IEC TS 27560:2023 is marked for revision. The current field mapping may become outdated. Any production implementation must version its schema and plan for migration.

6. **No withdrawal implementation.** While the receipt includes a withdrawal URL field, the engine does not implement withdrawal processing. GDPR Article 7 requires withdrawal to be as easy as giving consent; this obligation is acknowledged but not addressed in code.

7. **No principal identity verification.** The engine accepts any principal identifier string. In practice, binding a receipt to a verified identity requires authentication infrastructure not present here.

8. **Claim audit blocked.** The automated claim ledger audit found no structured claims to verify. No result in this paper has passed independent evidence-grounded claim review. All findings remain at prototype confidence level only.

9. **Missing readiness audit signal.** The paper review process flagged a missing `readiness_audit` signal, indicating that the artifact has not been assessed for publication readiness through the control plane's standard audit pathway.

---

## Reproducibility Checklist

- [x] Source code available: `src/consent_receipt_engine.py`
- [x] Test suite available: `tests/test_consent_receipt_engine.py`
- [x] Test log available: `logs/test.log`
- [x] Benchmark script and log available: `logs/benchmark.log`, `metrics/benchmark.json`
- [x] Sample output available: `sample_receipt_bundle.json`
- [x] Decision record available: `.omx/project_decision.json`
- [x] Run notes available: `run_notes.md`
- [x] Autoresearch result available: `.omx/specs/autoresearch-consent-receipt-engine/result.json`
- [ ] Hardware specifications for benchmark: **not recorded**
- [ ] Python version recorded: **not recorded in available artifacts**
- [ ] Random seed for UUID generation: **not controlled (uuid4 is non-deterministic)**
- [ ] Independent replication by third party: **not performed**
- [ ] Claim-level evidence audit passed: **blocked (no structured claims extracted)**

---

## Conclusion

A dependency-free Python proof of concept for a Consent Receipt Engine is mechanically viable. It validates consent events against a field schema informed by ISO/IEC TS 27560:2023, ISO/IEC 29184:2020, and the Kantara Consent Receipt Specification v1.1.0; generates linked controller-side records and principal-facing receipts with stable identifiers and content hashes; and passes its minimal test suite. Synthetic throughput of approximately 34,377 bundles per second demonstrates that the core computation is lightweight.

However, this result is a prototype validation, not a production readiness assessment. The gaps—secure persistence, access control, encryption, withdrawal execution, jurisdiction-specific legal review, schema versioning against the forthcoming ISO/IEC TS 27560 revision, and comprehensive test coverage—are substantial. Each gap represents mandatory work before any deployment that processes real personal data or makes compliance claims. Additionally, the claim audit for this artifact is blocked with no structured claims having been extracted or verified, meaning no finding herein has passed independent evidence review.

The engine's value is as a reference structure: a minimal, inspectable artifact that demonstrates the mechanical core of consent receipt generation is straightforward to implement. Whether that core is sufficient in any legal or operational context remains an open question requiring domain-specific expertise beyond the scope of this artifact.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Prototype source | `src/consent_receipt_engine.py` |
| Test suite | `tests/test_consent_receipt_engine.py` |
| Test log | `logs/test.log` |
| Benchmark log | `logs/benchmark.log` |
| Benchmark metrics | `metrics/benchmark.json` |
| Sample receipt bundle | `sample_receipt_bundle.json` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Autoresearch result | `.omx/specs/autoresearch-consent-receipt-engine/result.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260430T152248347401+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T152248347401+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T152248347401+0000/paper_manifest.json` |
