# vLLM attention-sink strict claim/evidence pass run note

Target: `papers/vllm-attention-sink-retention-3b-continuous-serving-stress-campaign`

Scope: make exactly one featured artifact pass the strict claim/evidence audit without changing the meaning of the public honesty language.

Evidence decision:
- The raw `results/*` JSON/log/archive files named by the generated evidence bundle are not present in this public repository.
- Public evidence that does exist: `paper.md` and `evidence_bundle.json`, including run-notes tail, decision metadata, result-file names, metric summaries, and limitations.
- Created `public_evidence/strict_claim_evidence_summary.{json,md}` as public surrogates derived only from those public files.
- Added five narrow claim-ledger entries that trace to the public surrogate, `evidence_bundle.json`, and `paper.md`.
- Preserved raw result-file absence with 20 `unavailable_result_files` records. Their `sha256`/`bytes` explicitly use `sha256_scope: public_surrogate`; `original_sha256_status` remains unknown because the original raw files are not in the public repo.

Strict pass meaning preserved:
- Traceability only.
- Not peer review.
- Not scientific correctness.
- Not independent replication.
- Not statistical power.
- Not semantic output quality.
- Not human-written status.

Validation snapshot:
- `python3 scripts/quality_scan.py` -> 159 / 159 packaging/provenance pass; strict count regenerated downstream.
- `python3 scripts/build_index.py` -> regenerated `papers/index.*`.
- `python3 scripts/validate_public_trust_surfaces.py` -> PASS.

Follow-up caveat:
- Corpus-level strict audit remains blocked overall because 296 artifacts still have empty claim ledgers and 1,405 public result-file references remain missing/unavailable without strict-pass claim ledgers.
