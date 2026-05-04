# Research Claim Unit Tests: An Executable Abstraction for Falsifiable Scientific Claims

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, decision JSON, and metrics). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We present "claim unit tests," a lightweight abstraction that ties atomic research claims to evidence provenance and deterministic executable checks over local data. Each claim produces one of four statuses—*supported*, *refuted*, *inconclusive*, or *error*—depending on whether its checks pass and whether evidence objects are present. We implement this abstraction in a stdlib-only Python prototype (`claimtest.py`) and demonstrate it on a synthetic 8-row treatment/control dataset with three deliberately designed claims exercising three of the four status paths. In the demonstration, one claim is supported (treatment–control mean difference = 7.75, exceeding a threshold of 6), one is refuted (the assertion that every subject improved by more than 3 fails with 3 row violations and a minimum observed change of 2), and one is inconclusive (numeric check passes but no evidence objects are attached). The prototype runs in 0.04 seconds wall-clock time with 15,252 KB peak memory. All three unit tests pass. These results establish mechanical viability of the abstraction on synthetic data but do not validate any domain-scientific conclusion. The formal claim ledger for this artifact remains in a blocked state with no structured claims extracted, indicating that the prototype's own claims have not yet been subjected to the discipline it proposes. The approach is further limited by the absence of statistical inference, automated evidence retrieval, and domain-expert review of claim-to-check operationalization.

## Introduction

Scientific claims in published literature are typically verified through narrative peer review, which depends on expert judgment and is difficult to scale or automate. Recent work on automated scientific claim verification has emphasized retrieval of evidence, structured scoring, and verifiable published findings. Valsci (2025) frames scientific claim verification as evidence-grounded literature review at scale, emphasizing retrieval, structured scoring, and verifiable published findings rather than standalone model memory. CliVER (2024) formulates automated scientific claim verification as retrieval of evidence, rationale sentence selection, and support/refute/neutral label prediction, reporting evaluation on SciFact and CoVERt benchmarks alongside clinician comparisons. Separately, metamorphic testing for scientific software has shown that executable relations can serve as practical oracles when exact expected outputs are unavailable, motivating the encoding of claim-level invariants and checks rather than relying solely on narrative review.

These threads share a common gap: there is no lightweight, deterministic abstraction that binds an atomic research claim to both its evidence provenance and an executable check that can be run locally. We ask: **Can a "unit test" abstraction for research claims make those claims more concrete and falsifiable by tying each claim to evidence provenance plus deterministic executable checks?**

This paper introduces such an abstraction and reports results from a minimal prototype evaluated on synthetic data. We do not claim that this abstraction replaces literature review, statistical inference, or expert judgment. Rather, we investigate whether it can operationalize part of the claim-verification pipeline by producing machine-readable, reproducible statuses.

## Method

### Claim Bundle Schema

Each claim is encoded as a JSON object containing three required fields:

1. **Atomic statement**: A single declarative assertion (e.g., "treatment effect exceeds control by at least 6 units").
2. **Evidence/provenance objects**: A list of objects linking the claim to data sources, DOIs, or local file references. An empty list is permitted but triggers an *inconclusive* status even if checks pass.
3. **Deterministic checks**: Executable predicates over local tabular data. Each check specifies a data source, an operation (e.g., column mean, row-wise comparison), and a threshold or relation.

### Status Logic

The runner evaluates claims according to the following deterministic logic:

| Condition | Status |
|---|---|
| All checks pass **and** at least one evidence object exists | `supported` |
| At least one check fails | `refuted` |
| No executable checks defined, **or** all checks pass but evidence list is empty | `inconclusive` |
| Malformed or non-runnable check definition | `error` |

This four-way distinction is deliberate. A claim whose checks pass but lacks evidence provenance is not declared *supported*; it remains *inconclusive*, reflecting the epistemic principle that computation alone is insufficient without grounding in documented evidence.

### Implementation

The prototype (`claimtest.py`) is implemented in Python using only the standard library. It accepts a path to a JSON claim bundle, resolves data references to local CSV files, evaluates each check, and emits a JSON report with per-claim statuses and check details. The implementation comprises approximately 200 lines of code. No external packages are required.

### Demonstration Dataset

To exercise multiple status paths, we constructed:

- **`data/demo_trial.csv`**: An 8-row synthetic dataset with treatment/control assignment and a numeric change score.
- **`claims/demo_claims.json`**: Three claims:
  - **C1**: "Treatment mean change exceeds control mean change by ≥ 6." Designed to be *supported*.
  - **C2**: "Every subject improved by > 3." Designed to be *refuted* (some control subjects have change ≤ 3).
  - **C3**: A numeric check that passes, but with an empty evidence list. Designed to be *inconclusive*.

No claim was designed to trigger the *error* status path in the demonstration run.

### Verification Procedure

We verified the prototype through four procedures:

1. **Unit tests**: `python3 -m unittest discover -s tests -v` (3 test cases).
2. **Static syntax check**: `python3 -m py_compile` on both source and test files.
3. **Claim runner execution**: `python3 claimtest.py claims/demo_claims.json --out results/demo_claim_report.json`.
4. **Resource measurement**: `/usr/bin/time -v` for wall-clock time and peak RSS.

All commands were executed and logged as documented in the run notes.

## Results

### Claim Evaluation Outcomes

The runner produced the following results, recorded in `results/demo_claim_report.json`:

| Claim | Status | Detail |
|---|---|---|
| C1 | `supported` | Treatment mean change = 10.75, control mean change = 3.0, difference = 7.75 ≥ 6. Evidence objects present. |
| C2 | `refuted` | Assertion "every subject improved by > 3" violated by 3 rows. Minimum observed change = 2. |
| C3 | `inconclusive` | Numeric check passes, but evidence list is empty. |

Three of the four status paths were exercised as designed. The `error` path was not triggered by the demo claims; its correctness is covered only by unit tests, not by an end-to-end claim run.

### Unit Test Results

All 3 unit tests passed with exit code 0. The test suite validates core runner logic including status assignment and check evaluation.

### Resource Footprint

| Metric | Value |
|---|---|
| Claim run wall-clock time | 0.04 s |
| Claim run peak RSS | 15,252 KB |
| Unit-test peak RSS | 15,732 KB |

The resource footprint is negligible, consistent with a stdlib-only tool operating on a small synthetic dataset. These numbers characterize the prototype's overhead on an 8-row dataset; they do not constitute a scalability claim for large corpora.

### Static Verification

Both `claimtest.py` and `tests/test_claimtest.py` passed `py_compile` with exit code 0, confirming syntactic validity.

### Claim Ledger Status

The formal claim ledger (`claim_ledger.json`) for this artifact is in a `blocked_empty_claims` state: no structured claims were extracted into the ledger, and the ledger notes that the artifact must not pass strict claim/evidence audit until claims reference public evidence files. This is a notable internal inconsistency—the prototype proposes a discipline of structured, evidence-grounded claims, but its own claims have not been formalized through that discipline.

## Limitations

We enumerate the principal limitations honestly:

1. **Synthetic data only.** The demonstration dataset is an 8-row artificial table. It validates the tool's mechanical behavior, not any domain-scientific claim. No real experimental or observational data was used.

2. **No automated evidence retrieval.** Evidence objects are user-supplied local provenance entries. The prototype does not implement retrieval from literature databases, DOI resolution, or RAG-based evidence search. This is a significant gap relative to the external literature on automated claim verification (Valsci, CliVER).

3. **No statistical inference.** The checks are deterministic predicates (threshold comparisons, row-wise assertions). No confidence intervals, hypothesis tests, multiple-testing corrections, or causal inference methods are included. A claim that passes a deterministic check has not been statistically validated.

4. **Claim-to-check operationalization requires human judgment.** Deciding whether a particular check adequately represents a real-world scientific claim is a domain-expert decision. The prototype provides no mechanism for expert review or approval of this mapping.

5. **No evaluation on public benchmarks.** The prototype has not been evaluated against established claim-verification benchmarks such as SciFact or CoVERt, which would be necessary to compare its utility against existing approaches.

6. **Single-prototype, single-dataset evidence.** The viability conclusion rests on one implementation and one synthetic dataset. Generalization to other claim types, data modalities, or scientific domains is untested.

7. **The `error` status path is unexercised in end-to-end runs.** No malformed claim was included in the demonstration, so the error-handling logic is verified only through unit tests, not through an end-to-end claim run.

8. **Internal claim ledger is blocked.** The artifact's own claim ledger contains no structured claims and is in a blocked audit state. The prototype has not been applied to itself in a closed-loop fashion, which undermines the credibility of proposing it as a discipline for others.

9. **No LLM or retrieval integration.** The prototype operates exclusively on user-supplied local data and evidence. It does not integrate with any language model, retrieval system, or literature database.

## Reproducibility Checklist

| Item | Status |
|---|---|
| Code availability | `claimtest.py`, `tests/test_claimtest.py` present in project directory |
| Data availability | `data/demo_trial.csv` (8-row synthetic dataset) present |
| Claim bundle availability | `claims/demo_claims.json` present |
| Result files availability | `results/demo_claim_report.json`, `results/metrics.json` present |
| Log files availability | `logs/unit-tests.log`, `logs/unit-tests.time.txt`, `logs/claim-run.stdout.json`, `logs/claim-run.time.txt`, `logs/py-compile.log` present |
| Dependencies | Python 3 standard library only; no external packages |
| Execution commands | Documented in run notes and Method section |
| Randomness | None; all checks are deterministic |
| Hardware | Execution on `worker.example`; resource measurements reported |
| Claim ledger audit | Blocked; no structured claims extracted |

## Conclusion

We have shown that a lightweight "unit test" abstraction for research claims is mechanically viable: claims can be decomposed into atomic assertions, bound to evidence provenance, and evaluated by deterministic checks producing unambiguous statuses. On synthetic data, the prototype correctly distinguishes *supported* (checks pass, evidence present), *refuted* (at least one check fails), and *inconclusive* (checks pass but evidence absent) claims.

However, the current results establish only tool mechanics on an 8-row synthetic dataset, not scientific utility. The approach is bounded by the quality of claim-to-check operationalization, the absence of automated evidence retrieval, the lack of statistical inference, and the fact that the artifact's own claim ledger remains blocked with no structured claims. The strongest use of claim unit tests is not replacing literature review or expert judgment; it is creating executable guardrails that make the current support status of a claim transparent, falsifiable, and reproducible—provided that the claims and checks themselves have been adequately operationalized and reviewed.

Future work should add statistical check types (confidence intervals, equivalence tests) without treating them as implicit proof of causality, integrate evidence adapters for literature metadata (DOI, PubMed, Semantic Scholar), define a review schema for expert approval of claim decompositions, evaluate against a public benchmark such as SciFact, and close the self-application gap by formalizing the artifact's own claims in its claim ledger.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Claim runner source | `claimtest.py` |
| Unit test source | `tests/test_claimtest.py` |
| Demo claim bundle | `claims/demo_claims.json` |
| Demo dataset | `data/demo_trial.csv` |
| Claim report output | `results/demo_claim_report.json` |
| Metrics output | `results/metrics.json` |
| Unit test log | `logs/unit-tests.log` |
| Unit test resource log | `logs/unit-tests.time.txt` |
| Claim run stdout | `logs/claim-run.stdout.json` |
| Claim run resource log | `logs/claim-run.time.txt` |
| Static check log | `logs/py-compile.log` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260430T104748393236+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T104748393236+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T104748393236+0000/paper_manifest.json` |

### External References

- Valsci (BMC Bioinformatics, 2025): https://doi.org/10.1186/s12859-025-06159-4
- CliVER (JAMIA Open, 2024): https://doi.org/10.1093/jamiaopen/ooae021
- Metamorphic testing for scientific software (IEEE CiSE, 2018): https://doi.org/10.1109/MCSE.2018.2880577
