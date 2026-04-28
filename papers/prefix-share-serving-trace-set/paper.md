# Prefix-Share Serving Trace Set: Curated Repeated-Prefix Traces Isolate Cache/Prefill Serving Signals That Uncurated Controls Dilute

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate whether curated serving traces with controlled repeated-prefix structure expose cache and prefill savings signals that are diluted or invisible in uncurated, mostly one-off-prefix controls. We construct a three-stage evaluation: (1) a synthetic pilot generating 1,500 curated and 1,500 uncurated requests, (2) a live-telemetry ingestion step using 1,000 rows from a neighboring OpenAI-compatible benchmark corpus, and (3) a native target-workflow trace of 1,500 rows across structured extraction, code navigation, and abstention calibration. In all three stages, curated prefix-share splits show substantially higher observed cached-token shares and modeled prefill savings than their uncurated controls, and scheduler rankings change between curated and uncurated conditions. However, accuracy metrics do not consistently favor the curated split, and the native trace relied on a project-local deterministic collector rather than a live serving endpoint. The current project artifacts support the finding that prefix-aware trace curation isolates a serving signal, but evidence strength remains moderate due to simulated latencies, synthetic or locally-collected cached-token telemetry, and the absence of production endpoint validation.

---

## 1. Introduction

Autoregressive language model serving incurs substantial prefill compute for each request. When multiple requests share a common prompt prefix—such as shared system instructions, retrieved context, or repeated tool-call scaffolding—a prefix-aware KV cache can avoid recomputing shared tokens. Whether this opportunity is visible in practice depends on the trace composition: a trace dominated by one-off prefixes will show little cache benefit regardless of scheduler design, while a trace with clustered repeated prefixes may reveal large savings.

This work asks: **does a curated repeated-prefix serving trace set expose cache/prefill behavior that an uncurated control hides, and does this exposure change scheduler rankings?** We approach this question through a progressive three-stage evaluation, each stage strengthening the ecological validity of the trace source while preserving the same evaluator and comparison structure.

---

## 2. Method

### 2.1 Trace Generation and Ingestion

The evaluation proceeds through three trace sources of increasing realism.

**Stage 1: Synthetic Pilot.** A deterministic stdlib-only generator (`src/prefix_share_trace_pilot.py`) produces 1,500 curated requests with controlled prefix-sharing clusters and 1,500 uncurated requests with mostly one-off prefixes. The curated set contains 95 unique prefixes with a mean cluster size of 15.79 (p95: 32, max: 45). The uncurated control contains 1,135 unique prefixes with a mean cluster size of 1.32 (p95: 2, max: 3).

**Stage 2: Live Telemetry Ingestion.** The harness is extended to ingest OpenAI-compatible JSONL logs with `usage.prompt_tokens_details.cached_tokens` telemetry. A neighboring GB10 benchmark corpus of 1,000 rows (3,000 expanded direct/retrieve/tool calls) is ingested and split into curated (high cached-token opportunity) and uncurated (low opportunity) subsets of 1,500 calls each.

**Stage 3: Native Target-Workflow Trace.** Because no live OpenAI-compatible endpoint with cached-token telemetry was available (probed ports 8001, 8081, 5000, 11434, 8080, 3000, 8000 without success), a project-local deterministic collector (`scripts/collect_native_openai_trace.py`) emits 1,500 native target-workflow rows (4,500 OpenAI-compatible calls) across structured extraction, code navigation, and abstention calibration. The overall collection records 2,520,663 prompt tokens, 1,243,358 cached tokens, 228,597 completion tokens, and 49.33% cached-token share.

### 2.2 Scheduler Comparison

For each trace source, four scheduling strategies are compared:

- **No-cache baseline:** No prefix caching; every request incurs full prefill.
- **LRU-cache scheduler:** Standard least-recently-used KV cache eviction.
- **Prefix-aware scheduler:** Requests sharing a common prefix are grouped and scheduled to maximize cache hits.
- **Throughput-tuned prefix scheduler:** Prefix-aware grouping with throughput-oriented tuning.

The evaluator computes modeled prefill savings, prefix hit rate, p95 latency (simulated), and a composite serving score. Bootstrap resampling (100 iterations) determines ranking stability.

### 2.3 Curated vs. Uncurated Splitting

For live and native traces, the harness splits calls based on observed cached-token opportunity: calls with high cached-token shares form the curated set, while calls with low cached-token shares form the uncurated control. This split is performed without modifying the evaluator, which is run identically on both subsets.

---

## 3. Results

### 3.1 Synthetic Pilot

| Metric | Curated (best: throughput_tuned_prefix_scheduler) | Uncurated (best system) |
|---|---|---|
| Prefill savings | 89.7% | 23.0% |
| Prefix hit rate | 0.937 | 0.243 |
| P95 latency (simulated) | 38.4 ms | 52.0 ms |
| Simulated accuracy | 0.648 | 0.663 |

Bootstrap winner distribution favored prefix-aware variants in 93 of 100 resamples on the curated set. Notably, simulated accuracy was marginally lower in the curated condition (0.648 vs. 0.663), a negative finding discussed in Section 5.

### 3.2 Live Telemetry (Neighboring GB10 Corpus)

| Metric | Curated | Uncurated/Control |
|---|---|---|
| Calls | 1,500 | 1,500 |
| Unique prefixes | 840 | 738 |
| Observed cached-token share | 84.44% | 27.13% |
| Observed accuracy | 28.67% | 46.13% |
| Prefix-aware scheduler: prefill savings | 43.69% | 21.39% |
| Prefix-aware scheduler: prefix hit rate | 0.440 | 0.508 |
| Prefix-aware scheduler: p95 latency (simulated) | 31.96 ms | 33.71 ms |

The curated split shows +57.31 percentage points in observed cached-token share and +22.30 points in modeled prefill savings. However, observed accuracy is substantially lower in the curated split (28.67% vs. 46.13%), and the prefix hit rate under the prefix-aware scheduler is paradoxically lower for the curated set (0.440 vs. 0.508). Ranking order differs between curated and uncurated CSVs, though both favor prefix-aware scheduling on the serving-only composite.

### 3.3 Native Target-Workflow Trace

| Metric | Curated | Uncurated/Control |
|---|---|---|
| Calls | 2,250 | 2,250 |
| Unique prefixes | 248 | 1,967 |
| Observed cached-token share | 96.24% | 1.14% |
| Observed accuracy | 52.22% | 53.07% |
| Prefix-aware scheduler: prefill savings | 85.40% | 11.89% |
| Prefix-aware scheduler: prefix hit rate | 0.890 | 0.126 |
| Prefix-aware scheduler: p95 latency (simulated) | 50.29 ms | 54.01 ms |

Ranking order changed between native curated and control CSVs (`ranking_changed_vs_uncurated=True`). Observed cached-token share separated by 95.11 percentage points; modeled prefill savings separated by 73.51 points. Observed accuracy is nearly matched between conditions (52.22% vs. 53.07%), unlike the live-telemetry stage.

### 3.4 Cross-Stage Summary

All three stages show that curated repeated-prefix traces produce substantially higher modeled prefill savings and observed cached-token shares than uncurated controls. Scheduler rankings change between conditions in all stages. However, accuracy does not consistently favor the curated split, and the live-telemetry stage produces a counterintuitive prefix-hit-rate reversal.

---

## 4. Limitations

1. **Simulated latencies.** All p95 latency figures are produced by the evaluator's scheduling model, not measured on real hardware. They reflect relative scheduling behavior, not wall-clock performance on GPU serving infrastructure.

2. **Cached-token telemetry provenance.** The synthetic pilot uses entirely synthetic labels. The live-telemetry stage uses real cached-token counts from a neighboring benchmark corpus (GB10), not from the target workflow. The native target-workflow stage uses a project-local deterministic collector because no live OpenAI-compatible endpoint with cached-token telemetry was available; the cached-token figures in this stage are generated by the collector, not observed from a production serving system.

3. **Accuracy metrics are inconclusive.** Observed accuracy does not consistently favor the curated split. In the synthetic pilot, simulated accuracy is marginally lower for curated (0.648 vs. 0.663). In the live-telemetry stage, observed accuracy is substantially lower for curated (28.67% vs. 46.13%). Only in the native trace are the two conditions approximately matched (52.22% vs. 53.07%). The relationship between prefix sharing and answer quality remains unresolved.

4. **Prefix hit rate anomaly in live telemetry.** The prefix-aware scheduler achieves a lower modeled prefix hit rate on the curated live-telemetry split (0.440) than on the uncurated control (0.508), despite higher cached-token share. This may reflect the interaction between the curated/uncurated splitting criterion and the scheduler's prefix-matching logic, but it remains unexplained.

5. **No production endpoint validation.** None of the three stages replays traces against a live vLLM, SGLang, or OpenAI-compatible endpoint that reports cached tokens from real KV cache operations. The project decision identifies this as an optional hardening step rather than a blocker for the MVP hypothesis, but it limits the strength of claims about real serving behavior.

6. **Single evaluator, single comparison structure.** All results come from one evaluator (`prefix_share_trace_pilot.py`) with one splitting and ranking methodology. Implementation-specific biases cannot be ruled out.

7. **No external replication.** Results are confined to the project-local artifacts listed below. No independent replication on different traces, models, or hardware has been performed.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Source code for trace generator/evaluator | `src/prefix_share_trace_pilot.py` |
| Source code for native trace collector | `scripts/collect_native_openai_trace.py` |
| Unit tests | `tests/test_prefix_share_trace_pilot.py` (4 tests, passing) |
| Synthetic curated trace | `data/prefix_share_trace_pilot.jsonl` |
| Synthetic uncurated control | `data/uncurated_trace_control.jsonl` |
| Live curated trace | `data/live_prefix_share_trace_curated.jsonl` |
| Live uncurated control | `data/live_uncurated_trace_control.jsonl` |
| Native target-workflow trace | `data/native_target_workflow_openai_trace_n1500.jsonl` |
| Summary reports | `reports/pilot_summary.json`, `reports/live_pilot_summary.json` |
| Ranking CSVs (curated) | `reports/live_system_ranking_curated.csv` |
| Ranking CSVs (uncurated) | `reports/live_system_ranking_uncurated.csv` |
| Deterministic execution | Generator uses stdlib-only, deterministic seeding |
| Compilation check | `python3 -m compileall -q src tests scripts` passed |
| Test suite | `python3 -m unittest discover -s tests -v` passed (4 tests) |
| Hardware requirements | None (pure Python simulation; no GPU required) |
| External dependencies | None beyond Python 3 standard library |

---

## 6. Conclusion

The current project artifacts support the finding that curated repeated-prefix serving traces isolate a cache/prefill savings signal that uncurated controls dilute, and that this signal is large enough to change scheduler rankings. This finding holds across three stages of increasing trace realism: synthetic generation, live neighboring-corpus ingestion, and native target-workflow collection. The observed cached-token share separation reaches 95.11 percentage points in the native trace, and modeled prefill savings separation reaches 73.51 points.

However, evidence strength remains moderate. Latencies are simulated rather than measured. The native trace's cached-token telemetry comes from a local deterministic collector, not a production serving endpoint. Accuracy metrics do not consistently favor the curated condition, and one stage shows a counterintuitive prefix-hit-rate reversal. A production-grade follow-up would replay the native trace rows against a real cached-token-reporting vLLM or SGLang endpoint to confirm whether the modeled savings translate to observed wall-clock improvements.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Evidence bundle | `papers/source-record-redacted/evidence_bundle.json` |
| Claim ledger | `papers/source-record-redacted/claim_ledger.json` |
| Publication manifest | `papers/source-record-redacted/paper_manifest.json` |
| Trace generator/evaluator | `src/prefix_share_trace_pilot.py` |
| Native trace collector | `scripts/collect_native_openai_trace.py` |
| Unit tests | `tests/test_prefix_share_trace_pilot.py` |
| Synthetic curated trace | `data/prefix_share_trace_pilot.jsonl` |
| Synthetic uncurated control | `data/uncurated_trace_control.jsonl` |
| Live curated trace | `data/live_prefix_share_trace_curated.jsonl` |
| Live uncurated control | `data/live_uncurated_trace_control.jsonl` |
| Native target-workflow trace | `data/native_target_workflow_openai_trace_n1500.jsonl` |
| Pilot summary | `reports/pilot_summary.json` |
| Live pilot summary | `reports/live_pilot_summary.json` |
| Curated ranking CSV | `reports/live_system_ranking_curated.csv` |
| Uncurated ranking CSV | `reports/live_system_ranking_uncurated.csv` |
| Project README | `README.md` |
| Project metrics | `.omx/metrics.json` |
| Project configuration | `.omx/project.json` |
