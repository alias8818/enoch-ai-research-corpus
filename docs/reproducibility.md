# Reproducibility notes

This corpus is designed for inspection and follow-up replication, not as a claim that every generated result has already been independently reproduced.

## What is included

Each packaged artifact is expected to include:

- `paper.md` — the generated report text;
- `metadata.json` — public provenance metadata, including AI-generated/no-human-authorship flags;
- `evidence_bundle.json` — public pointers to the evidence bundle or explicit evidence-unavailability metadata;
- `claim_ledger.json` — claim-level audit rows when available;
- corpus index rows that expose packaging/provenance status and strict claim/evidence status.

The public quality reports separate two different gates:

- **Packaging/provenance lint**: currently `496/496`. This checks release hygiene, public provenance, evidence/ledger file presence, and placeholder/secret patterns.
- **Strict claim/evidence audit**: currently `3/496`. This stricter audit only passes when generated claims can be traced to public result files or explicit public unavailability metadata.

Do not treat the packaging/provenance pass count as scientific validation. It is a publication-hygiene gate.

## What is intentionally excluded

The public corpus intentionally excludes private runtime state such as:

- live service tokens, API keys, and bearer tokens;
- local SQLite/Supabase connection secrets;
- private LAN addresses unless already part of a sanitized public deployment explanation;
- raw production logs that could contain paths, credentials, or private operator context;
- unredacted worker-machine filesystem snapshots;
- unpublished scratch state, transient tmux/session state, and local agent memory.

Where a generated artifact mentions a result file that is not public, the strict claim/evidence audit should count that as missing unless there is explicit public unavailability metadata and a safe surrogate.

## How to inspect an artifact

1. Open the paper from `papers/index.md`.
2. Read the `metadata.json` for provenance and generated-artifact framing.
3. Open the `evidence_bundle.json` and confirm whether referenced evidence paths are public and sanitized.
4. Open the `claim_ledger.json`; prefer claims with public result-file links or explicit unavailability metadata.
5. Check `quality/claim_evidence_audit.md` before citing a result as evidence-backed.
6. Re-run or independently reproduce the experiment before treating a result as established.

## Recommended public wording

Use wording such as:

- "AI-generated research artifact"
- "reported result"
- "bounded local evidence"
- "replication-worthy candidate"
- "not independently reproduced"

Avoid wording that implies peer review, human authorship of the paper text, or established scientific truth.
