# CI-Log Cost-Gated Failure Signature Sentinel

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review is asserted or implied.

---

## Abstract

Large-language-model (LLM) assistants integrated into continuous-integration (CI) pipelines can accelerate failure triage but incur per-query token costs that scale poorly when the same deterministic failure recurs across builds. We investigate a lightweight, dependency-free pre-LLM sentinel that normalizes CI log excerpts, matches prioritized regex signatures for common failure classes, emits stable fingerprints for deduplication, estimates LLM token-cost exposure, and gates escalation of unknown or low-confidence failures by a configurable spend cap. On a synthetic smoke corpus of nine labeled CI failure logs, the sentinel achieves perfect label agreement (9/9) and resolves 77.78% (7/9) of cases deterministically without LLM escalation. The two remaining cases—a network flake below the confidence threshold and an unknown custom build failure—are escalated or blocked as appropriate. An over-budget gate correctly prevents LLM escalation on the unknown failure when the spend cap is set aggressively. Throughput calibration over 2,250 analyses yields approximately 15,027 log analyses per second with a peak RSS of roughly 35 MB. These results are constrained by the small, synthetic evaluation corpus; we do not claim generalization to production CI environments without further shadow-mode validation on real historical failures.

## Introduction

CI pipelines produce failure logs at high volume and often high redundancy. The same dependency import error, typecheck violation, or out-of-memory kill may recur across dozens of builds before a human intervenes. LLM-based diagnostic assistants can accelerate triage, but each invocation carries a token cost. When failures are deterministic and repetitive, LLM escalation is both unnecessary and wasteful.

The core hypothesis of this work is that a lightweight, rule-based pre-filter can recognize the most common deterministic failure signatures in CI logs, fingerprint them for deduplication, estimate the LLM cost that would be incurred by escalation, and enforce a configurable spend cap—thereby reducing unnecessary LLM spend without sacrificing diagnostic coverage for genuinely novel failures.

This paper reports on a prototype implementation and smoke-scale evaluation. We make no claim of production readiness; the evaluation corpus is synthetic and small. The contribution is the demonstration that the mechanism is locally sound, cheap, and fast enough to warrant shadow-mode evaluation on real CI histories.

## Method

### Sentinel Design

The sentinel (`src/ci_log_sentinel.py`) is a dependency-free Python CLI that performs five operations in sequence:

1. **Log normalization.** Path fragments, timestamps, line numbers, and other variable noise are stripped or replaced with stable placeholders, producing a canonical form intended to be invariant across reruns of the same failure.

2. **Signature matching.** A prioritized list of regex signatures covers seven failure classes: dependency errors (missing module/package), assertion failures, typecheck errors, lint violations, concurrency/race conditions, resource exhaustion (e.g., OOM, exit 137), and external-flake failures (network timeouts, DNS errors). Signatures are evaluated in priority order; the first match determines the category.

3. **Fingerprint emission.** Each matched signature produces a stable fingerprint of the normalized excerpt, enabling deduplication across builds without storing raw logs.

4. **Cost estimation.** The sentinel estimates the LLM token count for the normalized excerpt using a conservative character-to-token approximation (characters divided by four). A per-token cost parameter converts this to an estimated dollar exposure.

5. **Cost gating.** If the estimated LLM cost exceeds a configurable maximum, or if the failure is classified as "unknown" (no signature matched) and the estimated cost exceeds the cap, escalation is blocked and a `gate_reason` is emitted.

### Evaluation Corpus

Nine labeled smoke logs were created under `fixtures/*.log` with corresponding ground-truth labels in `fixtures/labels.json`. The corpus covers:

| Fixture | Failure Class |
|---|---|
| Python missing module | Dependency |
| Node missing module | Dependency |
| Pytest assertion | Assertion |
| TypeScript typecheck | Typecheck |
| ESLint/lint | Lint |
| Go race/concurrent map write | Concurrency |
| OOM/exit 137 | Resource |
| Network/external flake | External flake |
| Unknown custom build failure | Unknown |

This corpus is synthetic and intentionally unambiguous; it is designed to verify mechanism correctness, not to estimate real-world precision or recall.

### Experimental Procedure

Four experiments were conducted:

1. **Unit tests.** `python3 -m unittest discover -s tests -v` verified internal logic correctness.

2. **Labeled smoke evaluation.** The sentinel analyzed all nine fixtures with ground-truth labels, recording category agreement, deterministic resolution rate, and LLM escalation count.

3. **Over-budget gate test.** The sentinel analyzed the unknown-build fixture with an aggressively low spend cap (`--max-cost 0.00001`) to confirm that the gate blocks escalation for unknown signatures when the estimated cost exceeds the cap.

4. **Throughput calibration.** A Python subprocess wrapper executed 2,250 fixture analyses to measure logs-per-second throughput and peak RSS.

Host telemetry (`/proc/meminfo`, `platform`) was captured for reproducibility context.

## Results

### Label Agreement

On the nine-fixture labeled smoke corpus, the sentinel's category output agreed with ground-truth labels in all nine cases (accuracy = 1.0). Because the corpus is synthetic and small, this result confirms mechanism correctness but does not bound real-world accuracy.

### Deterministic Resolution and LLM Escalation

Of the nine fixtures, seven were resolved deterministically without LLM escalation (77.78%). Two cases were escalated:

- **Network/external flake:** Confidence fell below the escalation threshold, resulting in LLM escalation. This is a design choice: low-confidence flake signatures may benefit from LLM interpretation, but the trade-off between false escalation and missed diagnosis is repository-dependent and has not been tuned on real data.
- **Unknown custom build failure:** No signature matched, so the failure was classified as unknown and escalated to LLM analysis.

### Over-Budget Gate

When the unknown-build fixture was analyzed with `--max-cost 0.00001`, the sentinel correctly blocked LLM escalation and emitted `gate_reason=unknown_signature_over_budget`. The over-budget path was not escalated, confirming that the spend cap is enforced as designed.

### Throughput and Memory

Throughput calibration over 2,250 analyses yielded approximately 15,027 log analyses per second. Peak RSS was approximately 35 MB (35,004 KB). The host reported 122,640,948 KB MemAvailable and 0 KB SwapTotal, consistent with a no-swap memory constraint. These figures characterize the prototype's resource footprint on a single host under a synthetic workload; they should not be extrapolated to production CI load patterns without further measurement.

### Summary Metrics

| Metric | Value |
|---|---|
| Fixture accuracy | 9/9 (1.0) |
| Deterministic no-LLM decisions | 7/9 (77.78%) |
| LLM escalations | 2/9 |
| Over-budget gate triggered | Yes |
| Throughput | ~15,027 logs/sec |
| Peak RSS | ~35 MB |

## Limitations

This work has several significant limitations that prevent drawing strong generalization claims:

1. **Synthetic, small corpus.** The evaluation corpus consists of nine hand-crafted logs with unambiguous failure signatures. Real CI logs are noisier, may contain multiple interleaved errors, and exhibit repository-specific patterns. Accuracy on this corpus is an upper bound, not an estimate of production performance.

2. **Regex signature coverage.** The seven signature classes cover common failure modes but cannot capture organization-specific errors (custom build system failures, proprietary test framework output, etc.). Precision and recall on real CI histories are unknown and likely lower than the smoke results suggest.

3. **Token-cost approximation.** The character-divided-by-four heuristic for token estimation is conservative but imprecise. Provider-specific tokenizers (e.g., BPE variants) may deviate significantly, causing the sentinel to over- or under-estimate actual LLM cost.

4. **No shadow-mode or production validation.** The sentinel has not been evaluated on real historical CI failures. The recommended next step—shadow-mode evaluation on 200–500 real CI failures with human-labeled categories—has not been performed.

5. **Single-pass classification.** The sentinel matches the first signature in priority order. Logs containing multiple distinct failures are classified by the highest-priority match only; secondary failures are ignored.

6. **No deduplication persistence.** Fingerprints are emitted but not stored or queried across runs in the current prototype. Deduplication across builds requires an external store, which is not implemented.

7. **Confidence threshold tuning.** The confidence threshold that determines whether a matched signature is resolved deterministically or escalated to LLM analysis was set by design intuition rather than empirical optimization. The network-flake escalation observed in the smoke evaluation may represent a false escalation or a correct conservative choice; this cannot be determined without labeled production data.

## Reproducibility Checklist

- **Source code:** `src/ci_log_sentinel.py` (dependency-free Python CLI)
- **Test suite:** `tests/test_ci_log_sentinel.py`
- **Fixtures:** `fixtures/*.log` (9 logs), `fixtures/labels.json`
- **Primary results:** `results/fixture_report.json`, `results/over_budget_unknown.json`, `results/research_metrics.json`
- **System telemetry:** `results/system_telemetry.json`
- **Execution logs:** `logs/unittest_discover.log`, `logs/throughput_benchmark.log`, `logs/fixture_stdout.json`, `logs/over_budget_stdout.json`
- **Decision record:** `.omx/project_decision.json`
- **Runtime:** Python 3, no external dependencies
- **Commands for replication:**
  - `python3 -m py_compile src/ci_log_sentinel.py`
  - `python3 -m unittest discover -s tests -v`
  - `python3 src/ci_log_sentinel.py fixtures/*.log --labels fixtures/labels.json --out results/fixture_report.json`
  - `python3 src/ci_log_sentinel.py fixtures/unknown_build.log --max-cost 0.00001 --out results/over_budget_unknown.json`
- **Hardware context:** Captured in `results/system_telemetry.json`; MemAvailable ~117 GB, SwapTotal 0 kB.

## Conclusion

A dependency-free pre-LLM CI log sentinel can identify common deterministic failure signatures, fingerprint normalized excerpts, estimate LLM cost exposure, and enforce a spend cap before escalation. On a synthetic smoke corpus of nine labeled logs, the prototype achieves perfect label agreement and resolves 77.78% of cases without LLM invocation, while correctly gating an over-budget unknown failure. Throughput (~15,027 logs/sec) and memory footprint (~35 MB RSS) are consistent with lightweight inline deployment.

However, these results are preliminary and should not be interpreted as evidence of production readiness. The evaluation corpus is synthetic and small, the token-cost model is approximate, and no shadow-mode or production validation has been performed. The sentinel's regex signatures will require repository-specific tuning, and real CI logs with multiple interleaved failures may degrade classification accuracy. The 77.78% deterministic resolution rate is an upper bound on a curated corpus, not a prediction of real-world LLM avoidance. We recommend shadow-mode evaluation on 200–500 real historical CI failures with human-labeled categories and per-repository confidence-threshold tuning as the necessary next step before any production deployment claim.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Sentinel source | `src/ci_log_sentinel.py` |
| Unit tests | `tests/test_ci_log_sentinel.py` |
| Smoke fixtures | `fixtures/*.log` |
| Fixture labels | `fixtures/labels.json` |
| Fixture report | `results/fixture_report.json` |
| Over-budget gate result | `results/over_budget_unknown.json` |
| Research metrics | `results/research_metrics.json` |
| System telemetry | `results/system_telemetry.json` |
| Unit test log | `logs/unittest_discover.log` |
| Throughput benchmark log | `logs/throughput_benchmark.log` |
| Fixture stdout log | `logs/fixture_stdout.json` |
| Over-budget stdout log | `logs/over_budget_stdout.json` |
| Project decision | `.omx/project_decision.json` |
