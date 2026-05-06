# Corpus quality gates

The corpus uses separate gates so public readers can distinguish release hygiene from evidence strength.

## Packaging/provenance gate

A paper can be packaged into the public corpus only if:

- it has an AI provenance notice;
- it has no `TODO`, `FIXME`, `citation needed`, or placeholder citation markers;
- it does not imply human authorship;
- it has an evidence bundle or clearly states evidence is missing;
- it has a claim ledger or clearly states claim audit is missing;
- it does not claim peer review;
- it preserves negative or mixed results honestly.

This gate is a publication-hygiene check. It does not prove scientific correctness, novelty, or reproducibility.

## Strict claim/evidence audit

The stricter audit is separate. It asks whether generated claims can be traced to public result files or explicit public unavailability metadata. A paper can pass packaging/provenance lint and still fail strict claim/evidence audit.

When citing a result, prefer artifacts with non-empty claim ledgers, public result-file references, and a strict-audit pass. Otherwise describe the result as reported and bounded, then reproduce it independently before relying on it.
