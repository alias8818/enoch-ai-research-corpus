# Provenance policy

Each report should identify:

- `generated_by`: Enoch Agentic Research Pipeline;
- `released_by`: corpus maintainer/operator;
- `human_authorship_claimed`: `false`;
- `ai_generated`: `true`;
- `review_status`: AI-generated research artifact;
- `evidence_available`: `true` or `false`;
- `claim_ledger_available`: `true` or `false`.

The corpus should preserve the distinction between:

1. software/system authorship;
2. operational release responsibility;
3. generated research text and claims.

## Reproducibility link

Provenance metadata is necessary but not sufficient for reproducibility. Public readers should combine it with:

- the paper's `evidence_bundle.json`;
- the paper's `claim_ledger.json`;
- the corpus-wide packaging/provenance report;
- the strict claim/evidence audit report;
- independent reruns or replication when a claim matters.

See [`reproducibility.md`](reproducibility.md) for what public artifacts include and what private runtime state is intentionally excluded.
