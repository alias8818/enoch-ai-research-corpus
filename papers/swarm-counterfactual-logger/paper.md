# Swarm Counterfactual Logger: Compact Decision-Record Logging for Hindsight Scoring of Missed Alternatives in Swarm Task Allocation

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision records, metrics, and prototype outputs). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether a swarm controller can log compact counterfactual decision records during task allocation such that, once ground-truth outcomes become available, missed alternatives can be reconstructed and scored without replaying the entire swarm or relying on external services. We implement a dependency-free prototype consisting of a deterministic swarm simulator and a JSONL-based counterfactual logger, and evaluate it across synthetic workloads of up to 50,000 allocation decisions. The prototype sustains approximately 10,921 logged decisions per second at the 50k-decision scale with a peak resident set size of ~29 MB. However, the logging overhead ratio—defined as the throughput ratio of the no-log baseline to the logging configuration—is 7.81×, indicating that verbose JSONL writing dominates execution cost. Across five random seeds with 8 agents and 5,000 tasks, the mean hindsight regret is 0.108 and the mean rate at which the best alternative was missed is 0.498. These results are drawn entirely from a synthetic simulator and do not constitute validation on a real swarm controller. The claim ledger for this artifact is currently empty and has not passed structured claim/evidence audit. We discuss the storage, throughput, and privacy implications of deploying such logging in production.

## Introduction

Swarm-based task allocation systems make repeated assignment decisions under uncertainty. After outcomes are observed, it is often desirable to ask: *what would have happened had a different assignment been chosen?* Answering this question typically requires either full replay of the swarm state or access to an external model that can estimate counterfactual outcomes. Both approaches impose costs—replay in compute and state storage, external models in latency, dependency, and potential privacy exposure.

An alternative is to log sufficient information at decision time to enable *post hoc* counterfactual scoring once ground-truth outcomes arrive. This requires recording not only the chosen assignment but also the top-*k* alternatives that were considered, along with enough feature context to score them against observed outcomes.

This paper examines the feasibility of this approach through a prototype implementation. We do not claim production readiness; rather, we seek to establish baseline performance characteristics, identify structural bottlenecks, and quantify the informational yield of counterfactual logging under controlled synthetic conditions.

The research question, as stated in the project's originating prompt, is: *Can a swarm controller log compact counterfactual decision records during task allocation so that, after ground-truth outcomes arrive, we can reconstruct and score missed alternatives without replaying the entire swarm or requiring private/external services?*

## Method

### Design

The prototype comprises two components:

1. **Deterministic swarm simulator.** A lightweight simulator that models *m* agents and *n* tasks. At each decision point, the simulator evaluates all agent–task pairings, selects the assignment with the highest predicted utility, and records the top-*k* alternatives alongside their predicted utilities and feature snapshots.

2. **Counterfactual logger.** A JSONL writer that appends one record per decision. Each record contains the chosen assignment, the top-*k* alternatives, feature snapshots for each alternative, and a placeholder for the eventual ground-truth outcome. A separate hindsight-scoring pass joins logged records with observed outcomes and computes regret metrics.

The simulator is deterministic given a seed, enabling exact reproduction of any logged decision context. The implementation has no external dependencies beyond the Python standard library.

### Evaluation Protocol

We conducted the following experiments, all on a single local machine:

- **Smoke test:** 4 agents, 10 tasks, seed 1. Verified that output JSONL parses and that hindsight scores are computed correctly.
- **Calibration:** 1,000; 10,000; and 50,000 decisions with timing via `/usr/bin/time -v`, recording wall-clock time and maximum resident set size (RSS).
- **No-log baseline:** Identical simulator logic with all JSONL writes removed, to isolate logging overhead.
- **Streaming variant:** A refined logger supporting non-retained streaming simulation, re-tested for regression correctness.
- **Multi-seed evaluation:** 5 independent runs with 8 agents and 5,000 tasks (seeds 1–5), aggregating hindsight regret and missed-best rates.

All runs used Python 3 with no external dependencies beyond the standard library and `pytest` for testing.

### Metrics

- **Logged decisions per second:** throughput of the full logging pipeline.
- **No-log decisions per second:** throughput of the simulator alone.
- **Logging overhead ratio:** no-log throughput divided by logged throughput.
- **Bytes per decision:** average JSONL record size.
- **Max RSS (KB):** peak memory usage.
- **Hindsight regret:** normalized difference between the best possible outcome and the chosen outcome, averaged across decisions.
- **Missed-best rate:** fraction of decisions where the chosen assignment was not the best in hindsight.

## Results

### Throughput and Overhead

| Configuration | Decisions | Decisions/sec | Max RSS (KB) |
|---|---|---|---|
| Logged (streaming) | 50,000 | 10,921 | 29,928 |
| No-log baseline | 50,000 | 85,294 | — |

The logging overhead ratio is **7.81×**, meaning the logging configuration processes decisions at approximately 12.8% of the no-log baseline throughput. This overhead is attributable primarily to JSONL serialization and disk I/O; the simulator logic itself is identical in both configurations.

### Storage

At 8 agents, the average logged decision occupies **4,450 bytes** in JSONL format. This is verbose: each record serializes the full feature snapshot for every top-*k* alternative. At 50,000 decisions, the output file is approximately 213 MB uncompressed.

### Hindsight Scoring

Across five seeds (8 agents, 5,000 tasks each):

- **Mean hindsight regret:** 0.108
- **Mean missed-best rate:** 0.498

The missed-best rate near 0.50 indicates that, under the simulator's utility model, the chosen assignment fails to be the ex-post optimal one roughly half the time. This is consistent with a noisy prediction model and confirms that counterfactual records do carry non-trivial scoring information: in approximately half of all decisions, a logged alternative would have outperformed the chosen action.

Standard deviations and confidence intervals for these estimates are not available in the recorded artifacts (see Limitations).

### Correctness

Three regression tests passed on initial and final pytest runs, covering decision logging integrity, hindsight score computation, and streaming-mode equivalence.

## Limitations

1. **Synthetic evaluation only.** All results derive from a toy simulator with a hand-coded utility model. The simulator does not model real swarm dynamics, network effects, agent failure, or adversarial conditions. Whether counterfactual logging provides actionable insight in a production swarm controller remains untested.

2. **Verbose storage format.** At ~4.4 KB per decision, JSONL is impractical for large-scale or long-running deployments. Compression or columnar storage (e.g., Parquet) would be necessary before production use, and the overhead ratio may change substantially with a different serialization strategy.

3. **Overhead magnitude.** A 7.81× throughput reduction is significant. Whether this overhead is acceptable depends on the decision cadence of the target system. For low-frequency allocation (e.g., one decision per second), the absolute cost is negligible; for high-frequency loops, it may be prohibitive.

4. **Counterfactual outcome estimation.** In the simulator, ground-truth outcomes for unchosen alternatives are available by construction. In a real system, outcomes for actions not taken are unobserved and may require replay, randomized exploration, or model-based estimation—each introducing its own biases and costs.

5. **Privacy.** Feature snapshots logged at decision time may contain sensitive information. Production deployment would require redaction or differential-privacy mechanisms not addressed here.

6. **Limited statistical reporting.** The multi-seed evaluation reports means across five seeds but does not report standard deviations or confidence intervals, limiting the precision of the regret and missed-best estimates.

7. **Single-machine, single-configuration results.** All measurements were taken on one machine under unspecified load conditions. No cross-hardware or cross-configuration comparison is available. Specific CPU and RAM details were not recorded in the available artifacts.

8. **Empty claim ledger.** The structured claim ledger for this artifact contains no claims and has audit status "blocked_empty_claims." The results presented here are drawn from the project decision record and run notes rather than from a formally audited claim/evidence chain. This artifact must not be treated as having passed strict claim/evidence audit.

## Reproducibility Checklist

- [x] **Code available:** `src/counterfactual_logger.py` and `tests/test_counterfactual_logger.py` exist in the project directory.
- [x] **Deterministic seeding:** All runs accept a `--seed` flag; the simulator is deterministic given a seed.
- [x] **Test suite:** 3 pytest tests pass (recorded in `logs/pytest_final.log`).
- [x] **Artifact manifest:** Full file listing in `logs/artifact_manifest.txt`.
- [x] **Calibration data:** Raw timing and memory data in `logs/calibration_streaming_n*.json` and `logs/calibration_streaming_n*.time`.
- [x] **Evaluation data:** Per-seed results in `logs/eval_seed{1..5}.json`; aggregate in `results/aggregate_eval.json`.
- [x] **Baseline data:** No-log benchmark in `logs/no_log_benchmark.json`.
- [x] **Smoke data:** `results/smoke/summary_seed1_n10.json`.
- [x] **Decision record:** `.omx/project_decision.json` with machine-readable confidence, metrics, and rationale.
- [x] **Environment:** Python 3 (version recorded in `logs/env.log`); no external dependencies.
- [ ] **Hardware specification:** Single local machine; specific CPU/RAM not recorded in available artifacts (incomplete).

## Conclusion

A dependency-free prototype demonstrates that counterfactual decision logging for swarm task allocation is mechanically straightforward and can sustain ~10.9k logged decisions per second at 50k-decision scale with bounded memory (~29 MB). The hindsight scoring yields a mean regret of 0.108 and a missed-best rate of ~0.50, confirming that logged alternatives frequently contain better-than-chosen options and that the records carry scoring-relevant information.

However, the 7.81× logging overhead and the ~4.4 KB per decision storage cost indicate that the current JSONL-based approach is not directly suitable for production deployment at scale. The results are confined to a synthetic simulator and do not validate the approach under real swarm dynamics, real outcome distributions, or real privacy constraints. The claim ledger remains empty and has not passed structured audit.

The next step, as identified in the project decision record, is to instrument a real swarm decision point with top-*k* counterfactual logging and to compare JSONL against compressed or columnar storage formats. Until such validation is performed, the findings here should be regarded as a feasibility baseline rather than a deployment recommendation.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Logger source | `src/counterfactual_logger.py` |
| Test suite | `tests/test_counterfactual_logger.py` |
| Smoke summary | `results/smoke/summary_seed1_n10.json` |
| Aggregate evaluation | `results/aggregate_eval.json` |
| Research result narrative | `results/research_result.md` |
| Calibration (50k, streaming) | `logs/calibration_streaming_n50000.json` |
| Calibration timing (50k) | `logs/calibration_streaming_n50000.time` |
| No-log benchmark | `logs/no_log_benchmark.json` |
| Per-seed evaluation | `logs/eval_seed{1..5}.json` |
| Pytest (initial) | `logs/pytest.log` |
| Pytest (post-streaming) | `logs/pytest_after_streaming.log` |
| Pytest (final) | `logs/pytest_final.log` |
| Smoke run log | `logs/smoke.log` |
| Streaming smoke log | `logs/smoke_streaming.log` |
| Environment log | `logs/env.log` |
| Artifact manifest | `logs/artifact_manifest.txt` |
| Project decision | `.omx/project_decision.json` |
| Project metadata | `.omx/project.json` |
| Claim ledger | `papers/source-record-redacted-20260429T215748349314+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T215748349314+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T215748349314+0000/paper_manifest.json` |
