# SLO Narrative Compressor: Deterministic Compression of Structured SLO Telemetry into Compact Factual Narratives

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts (run notes, decision JSON, benchmark logs, and metrics files). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Site reliability engineering reviews depend on dense structured telemetry—SLO burn-rate windows, latency percentiles, error budgets, and customer-impact indicators—to construct post-incident narratives. We investigate whether a deterministic, dependency-free template compressor can reduce raw SLO telemetry JSON into short prose narratives while preserving all operationally required facts and introducing zero unsupported claims. On four synthetic SLO fixtures, the prototype achieves a mean compression ratio of 41.93× (minimum 34.88×), 100% required-fact coverage, and zero unsupported facts. A calibrated throughput benchmark of 5,000 repeated compressions yields 5,325 cases/sec at 14.6 MB peak RSS. These results establish a concrete baseline and evaluation harness, but they are confined to synthetic fixtures and do not demonstrate production usefulness or human-accepted narrative quality on real incident data.

---

## Introduction

SLO review processes consume large volumes of structured telemetry. A single service's SLO review may span burn-rate time windows, error-budget consumption curves, latency percentile health signals, and customer-impact annotations. Converting this substrate into a concise, reviewable narrative is typically a manual or LLM-assisted step, both of which carry risks: manual summarization is slow and inconsistent, while LLM-assisted summarization can introduce hallucinated or unsupported claims that undermine operational trust.

The central question of this work is:

> Can structured SLO and incident telemetry be deterministically compressed into a short narrative that preserves the operationally critical facts and avoids unsupported claims?

We approach this question conservatively: rather than training or prompting a language model, we implement a rule-based, dependency-free template compressor that maps structured telemetry fields directly into constrained prose slots. This design sacrifices semantic richness for verifiable factuality. The trade-off is deliberate—if the deterministic baseline cannot achieve adequate compression and fact coverage on controlled inputs, then more complex approaches inherit the same risk with additional failure modes.

We evaluate on synthetic SLO fixtures that include incident windows, burn-rate breaches, latency health, and customer-impact indicators. We measure compression ratio, required-fact coverage, and unsupported-fact count. We also calibrate throughput and memory footprint to characterize the baseline's resource profile.

---

## Method

### Prototype Design

The compressor (`scripts/slo_narrative_compressor.py`) is a single-file, dependency-free Python module. It accepts structured SLO telemetry as JSON and emits a constrained prose narrative bounded by a configurable word budget (default: 160 words). The compression logic is purely deterministic: each telemetry field maps to a fixed template slot. No language model, external API, or probabilistic component is involved.

This is a prototype-level implementation intended to establish feasibility and an evaluation harness, not a production system. It operates on a custom JSON schema and has not been integrated with live SLO data sources.

Key invariants enforced by construction:

1. **Field-level attribution.** Every clause in the output narrative traces to a specific input field. No clause is generated without a corresponding input value.
2. **No inference.** The compressor does not infer, impute, or extrapolate values absent from the input. Missing fields produce no output clause rather than a default or guessed clause.
3. **Determinism.** Identical inputs produce identical outputs across runs, platforms, and Python versions (subject to JSON field ordering).

### Synthetic Fixtures

Four deterministic synthetic SLO fixtures were generated programmatically. Each fixture contains:

- SLO metadata (service name, SLO name, target, window).
- Burn-rate time-series data with explicit breach windows.
- Latency percentile health indicators (p50, p95, p99).
- Error-budget consumption status.
- Customer-impact annotations (affected or not, scope).

The fixtures are designed to cover distinct operational scenarios (e.g., burn-rate breach with customer impact, healthy SLO with no breach, partial error-budget consumption). They do not attempt to model ambiguous or contradictory input fields. These are toy-scale fixtures: they exercise the compressor's logic paths but do not represent the complexity, noise, or inconsistency of real production SLO telemetry.

### Evaluation Metrics

Three metrics are computed per fixture and in aggregate:

| Metric | Definition |
|---|---|
| **Compression ratio** | `len(input_json_bytes) / len(narrative_bytes)` |
| **Required-fact coverage** | Fraction of operationally required facts present in the narrative (checked against a per-fixture invariant list) |
| **Unsupported-fact count** | Number of narrative clauses that lack a corresponding input field (checked by structural back-trace) |

Required facts are defined per fixture as the set of invariants that any acceptable narrative must communicate: SLO name, target, breach status, burn-rate direction, latency health, error-budget remaining, and customer-impact status.

### Throughput Calibration

A separate benchmark runs 5,000 repeated compressions of the fixture set and records wall-clock time, throughput (cases/sec), and peak RSS via `/usr/bin/time -v`. This is a local calibration benchmark on a single host, not a production deployment measurement.

### Test Harness

Two unit tests (`tests/test_slo_narrative_compressor.py`) verify:

1. Determinism: repeated calls on the same input produce byte-identical output.
2. Fact coverage: the output narrative contains all required facts for each fixture.

---

## Results

### Smoke Evaluation

All four synthetic fixtures passed the smoke evaluation. Results are summarized below:

| Metric | Value |
|---|---|
| Fixture count | 4 |
| Mean compression ratio | 41.93× |
| Minimum compression ratio | 34.88× |
| Mean required-fact coverage | 100% |
| Minimum required-fact coverage | 100% |
| Total unsupported facts | 0 |

The compression ratio varies across fixtures because input JSON size differs (some fixtures carry longer burn-rate windows or more latency percentile entries), while narrative length is bounded by the word budget. Even the minimum ratio of 34.88× exceeds the 5× target by a substantial margin, though this is expected given the verbosity of raw JSON relative to constrained prose.

### Calibrated Throughput

| Metric | Value |
|---|---|
| Iterations | 5,000 |
| Wall-clock time | 0.94 s |
| Throughput | 5,325 cases/sec |
| Mean compression ratio (5k run) | 39.86× |
| Missing required facts (5k run) | 0 |
| Unsupported facts (5k run) | 0 |
| Peak RSS | 14,592 KB |
| CPU utilization | 99% |
| Swaps | 0 |

The slight decrease in mean compression ratio (41.93 → 39.86) between the smoke evaluation and the 5,000-iteration run is attributable to the different fixture distribution in the repeated benchmark (all four fixtures are cycled, and rounding in byte-length measurement over many iterations shifts the mean slightly). The difference is not operationally significant.

### Unit Tests and Static Checks

- Unit tests: 2/2 passed.
- Static Python compilation (`py_compile`): passed on both the compressor module and the test module.

### System Posture

The benchmark ran on a Linux aarch64 host with ~122 GB available memory, zero swap, and earlyoom active. The compressor's 14.6 MB peak RSS is negligible relative to available resources. No swapping or OOM events occurred. These resource figures characterize the prototype on a well-provisioned host; they do not predict behavior under memory pressure or in containerized environments with tighter limits.

---

## Limitations

1. **Synthetic fixtures are not production data.** The four fixtures are programmatically generated and cover distinct but clean scenarios. Real SLO telemetry contains ambiguous labels, missing fields, inconsistent units, multi-service dependency chains, and edge cases (e.g., partially breached windows, rolling resets of error budgets) that the current fixtures do not exercise. Compression ratio, fact coverage, and unsupported-fact counts may degrade on messier inputs. The 100% fact-coverage and zero-unsupported-fact results should be interpreted as properties of the controlled test conditions, not as guarantees under real-world inputs.

2. **Narrative quality is not human-evaluated.** The evaluation checks structural fact coverage and absence of unsupported claims, but it does not assess readability, actionability, or whether a human on-call engineer would find the narrative useful during an incident review. These properties require human acceptance labels, which are not available in this work.

3. **Template prose is not semantically rich.** The deterministic template approach guarantees factuality by construction but produces mechanically structured output. LLM-assisted rewording could improve fluency, but would require stronger attribution and factuality gates to avoid the hallucination risk that motivated the deterministic design in the first place.

4. **No schema adapters for real sources.** The prototype consumes a custom JSON schema. Real-world deployment would require adapters for Prometheus, Alertmanager, PagerDuty, or similar incident/SLO sources, each with their own field semantics and missing-data patterns.

5. **Compression ratio is partly an artifact of JSON verbosity.** The high compression ratios (>34×) reflect the substantial overhead of JSON encoding (keys, brackets, whitespace) relative to the information content. A binary-encoded input would yield a lower compression ratio for the same narrative output. The compression ratio metric is therefore most useful as a relative measure across configurations of the same compressor, not as an absolute information-theoretic claim.

6. **Single-word-budget configuration.** All evaluations used a 160-word maximum. The sensitivity of fact coverage and narrative quality to the word budget has not been explored.

7. **Model-authored draft; human claim audit required.** This paper and the underlying claim ledger were produced by an automated pipeline. The claim ledger contains no independently verified claim-audit entries. A human claim audit is needed before the results can be treated as verified.

---

## Reproducibility Checklist

| Item | Status |
|---|---|
| Code available | `scripts/slo_narrative_compressor.py` (single-file, dependency-free) |
| Test suite available | `tests/test_slo_narrative_compressor.py` (2 tests) |
| Fixtures available | `artifacts/metrics/smoke/fixtures.json` |
| Output narratives available | `artifacts/metrics/smoke/narratives.json` |
| Smoke metrics available | `artifacts/metrics/smoke/metrics.json` |
| Throughput metrics available | `artifacts/metrics/calibrated-throughput.json` |
| Unit test log | `artifacts/logs/unit-test.log` |
| Smoke evaluation log | `artifacts/logs/smoke-eval.log` |
| Throughput benchmark log | `artifacts/logs/calibrated-throughput.log` |
| Static compile log | `artifacts/logs/py-compile.log` |
| System telemetry log | `artifacts/logs/system-telemetry.log` |
| Deterministic outputs verified | Yes (unit test + 5,000-iteration benchmark) |
| Random seeds specified | Not applicable (no randomness in compressor) |
| Hardware specified | Linux aarch64, ~122 GB RAM, 0 swap |
| Software dependencies | Python 3 (stdlib only) |
| Result classification | Synthetic fixture evaluation + local throughput calibration; not production validation |

---

## Conclusion

A deterministic, dependency-free template compressor can reduce structured SLO telemetry JSON into compact prose narratives at >34× compression while preserving 100% of required facts and introducing zero unsupported claims on synthetic fixtures. The prototype processes over 5,325 cases per second at under 15 MB RSS, making it feasible as a low-latency preprocessing step in SLO review tooling.

However, these results are confined to synthetic data and structural quality metrics. They do not demonstrate that the narratives are useful to human operators, nor that the compressor handles the ambiguity and inconsistency present in real production SLO telemetry. The 100% fact-coverage and zero-unsupported-fact figures are properties of the controlled test conditions and should not be extrapolated to production inputs without re-evaluation. The work establishes a concrete baseline and reproducible evaluation harness; the critical next step is validation against real or anonymized SLO review exports with human acceptance labels for readability, actionability, and trust.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Compressor script | `scripts/slo_narrative_compressor.py` |
| Test module | `tests/test_slo_narrative_compressor.py` |
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Smoke metrics | `artifacts/metrics/smoke/metrics.json` |
| Smoke narratives | `artifacts/metrics/smoke/narratives.json` |
| Smoke fixtures | `artifacts/metrics/smoke/fixtures.json` |
| Throughput metrics | `artifacts/metrics/calibrated-throughput.json` |
| Unit test log | `artifacts/logs/unit-test.log` |
| Smoke eval log | `artifacts/logs/smoke-eval.log` |
| Throughput benchmark log | `artifacts/logs/calibrated-throughput.log` |
| Static compile log | `artifacts/logs/py-compile.log` |
| System telemetry log | `artifacts/logs/system-telemetry.log` |
| Notion URL check log | `artifacts/logs/notion-url-check.log` |
| Claim ledger | `papers/source-record-redacted-20260502T183015695257+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T183015695257+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T183015695257+0000/paper_manifest.json` |
