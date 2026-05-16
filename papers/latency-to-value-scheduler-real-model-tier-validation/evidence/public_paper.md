# Latency-to-Value Scheduling with Real Model Tiers: A Local Two-Endpoint Validation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, evidence bundles, claim ledgers, benchmark results, and decision JSON). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We report results from validating a latency-to-value scheduler against two real, locally hosted model tiers, replacing the single-model accounting proxy used in prior work. Two quantized instruction-tuned models—Qwen2.5-0.5B-Instruct-Q8_0 (cheap tier, 507 MiB) and Qwen2.5-1.5B-Instruct-Q8_0 (expensive tier, 1.6 GiB)—were served via separate OpenAI-compatible `llama-server` endpoints on an aarch64 host. The scheduler's typed latency-to-value policy was compared against a manual confidence broker across a smoke test and four calibrated seeds (8 tasks per policy, 2 parallel slots, max 2 attempts, retry budget ratio 0.6). Aggregate typed-minus-manual deltas showed positive useful-value differences (mean +2.676, range +1.646 to +3.896), reduced spend proxy (mean −0.811), reduced wall time (mean −1.623 s), and increased throughput (mean +58.512 tokens/s), with success-rate parity and zero retry regression across all seeds. These findings are consistent with the hypothesis that latency-aware tier dispatch can improve cost-efficiency without sacrificing task success, but the evidence is bounded: compact generated agent subtasks, heuristic output-contract scoring, a narrow model capability gap, a single hardware configuration, and limited seed coverage all constrain the scope of the claims.

---

## Introduction

Latency-to-value scheduling routes inference requests across model tiers of differing cost and capability, seeking to maximize useful output per unit of time and compute. Prior work on this scheduler established its behavior under a single-model accounting proxy, where tier differences were simulated by bookkeeping rather than served by genuinely distinct models. The parent project decision explicitly recommended validation against two actual model tiers on messier agent workflows before any claim of external validity could be sustained.

This paper reports the results of that stronger validation. We replace the single-model proxy with two real, locally hosted quantized models served by independent `llama-server` instances, and we compare the typed latency-to-value scheduler against a manual confidence broker on generated agent subtasks. The central question is whether the scheduler's cost and throughput advantages persist when tier differences are genuine—when the cheap tier produces observably weaker outputs and the expensive tier incurs observably higher latency and resource cost.

---

## Method

### Hardware and Software Environment

All experiments ran on a single aarch64 host. Inference was served by `llama-server` (build `50494a2`, version 1). Two GGUF-quantized instruction-tuned models constituted the two tiers:

| Tier | Model | Quantization | Disk Size |
|------|-------|-------------|-----------|
| Cheap | Qwen2.5-0.5B-Instruct | Q8_0 | 507 MiB |
| Expensive | Qwen2.5-1.5B-Instruct | Q8_0 | 1.6 GiB |

Each tier was served by a separate `llama-server` instance launched from `/tmp/enoch_services/latency_to_value_real_tiers`. Endpoints exposed OpenAI-compatible `/v1/models` and `/v1/chat/completions` routes. After each run, both server processes were terminated and port liveness was verified across ports 18180–18343 to confirm no residual listeners.

### Adapter Architecture

A real-model-tier adapter (`src/real_model_tier_adapter.py`) was implemented with the following responsibilities:

1. Launch two local `llama-server` instances, one per model, on distinct ports.
2. Verify endpoint readiness by querying `/v1/models` on each.
3. Dispatch `cheap` policy calls to the 0.5B endpoint and `expensive` policy calls to the 1.5B endpoint.
4. Record per-tier server RSS and system `/proc/meminfo` MemAvailable before and after each run.
5. Terminate both server processes on exit.

The adapter integrates with the existing scheduler harness: `src/latency_to_value_scheduler.py`, `src/live_broker_latency_to_value.py`, `src/openai_compatible_broker_adapter.py`, and `src/replay_latency_to_value_scheduler.py`.

### Pre-Benchmark Verification

Prior to benchmarking, the full harness passed 17 unit tests (`python -m unittest discover -s tests -v`; log: `logs/unittest.log`) and a compile check (`python -m compileall src scripts tests`; log: `logs/compileall.log`).

### Experimental Design

**Smoke test.** Configuration: 2 tasks per policy, 1 parallel slot, max 1 attempt, seed 17. Purpose: verify endpoint readiness, basic dispatch correctness, and telemetry collection before committing to longer runs.

**Calibrated runs.** Configuration: 8 tasks per policy, 2 parallel slots, max 2 attempts, retry budget ratio 0.6, seeds 17, 23, 31, 43. Purpose: measure scheduler behavior under a more realistic configuration with retry headroom and parallelism.

### Metrics

All runs recorded the following typed-minus-manual deltas (scheduler policy minus manual confidence broker):

- **Useful value**: difference in heuristic output-contract score.
- **Success rate**: difference in fraction of tasks completed successfully.
- **Spend proxy**: difference in approximate compute cost.
- **Wall time**: difference in end-to-end elapsed time (seconds).
- **Tokens/s**: difference in throughput.
- **Retries**: difference in retry count.

System telemetry was collected via `/usr/bin/time -v` (elapsed time, CPU%, maximum RSS, swaps) and `/proc/meminfo` (MemAvailable, SwapTotal, SwapFree). Swap was intentionally excluded from capacity evidence; all runs reported zero swaps.

### Scoring Caveat

Task success and useful value were assessed by heuristic output-contract scoring on compact generated agent subtasks. This scoring is an automated proxy and does not represent human evaluation on open-ended or genuinely messy real-world workflows. The absolute magnitude of useful-value deltas is meaningful only relative to the internal scoring scale and should not be interpreted as a domain-independent effect size.

---

## Results

### Smoke Test

| Metric | Delta (typed − manual) |
|--------|----------------------|
| Useful value | +1.443 |
| Success rate | +0.000 (parity) |
| Spend proxy | −0.709 |
| Wall time | −1.184 s |
| Tokens/s | +220.954 |
| Retries | 0 |

System telemetry: elapsed 5.45 s, CPU 504%, max RSS 1,746,288 kB, swaps 0.

The smoke test confirmed endpoint readiness, correct tier dispatch, and telemetry integrity. The large tokens/s delta reflects the throughput advantage of routing more calls to the smaller, faster model. This result motivated proceeding to calibrated runs.

### Calibrated Runs

Aggregate typed-minus-manual deltas across four seeds:

| Metric | Mean | Median | Range | Direction consistency |
|--------|------|--------|-------|-----------------------|
| Useful value | +2.676 | +2.581 | +1.646 to +3.896 | Positive in 4/4 seeds |
| Success rate | +0.000 | +0.000 | Parity | Nonnegative in 4/4 seeds |
| Spend proxy | −0.811 | — | Negative | Lower spend in 4/4 seeds |
| Wall time | −1.623 s | — | Negative | Faster in 4/4 seeds |
| Tokens/s | +58.512 | — | Positive | Higher throughput in 4/4 seeds |
| Retries | 0 | — | Zero | Zero delta in 4/4 seeds |

All four seeds showed positive useful-value deltas, reduced spend, reduced wall time, and increased throughput. No seed exhibited success-rate regression or retry increase. However, with only four seeds, these directional consistencies do not constitute statistically robust estimates of effect size or confidence intervals.

### Tier Dispatch Behavior

The typed scheduler consistently routed more calls to the cheap tier than the manual broker, while preserving success parity:

| Seed | Typed (cheap, expensive) | Manual (cheap, expensive) |
|------|--------------------------|---------------------------|
| 17 | (5, 3) | (2, 6) |
| 31 | (3, 5) | (0, 8) |

(Tier dispatch counts for seeds 23 and 43 were recorded in per-seed result artifacts but not transcribed in the run notes summary.)

This shift toward cheap-tier dispatch, without success-rate loss, is the primary mechanism behind the spend and wall-time improvements. The fact that success parity was maintained despite heavier cheap-tier usage suggests the scheduler's value estimation correctly identified tasks where the smaller model sufficed.

### Per-Seed System Telemetry

| Seed | Elapsed (s) | CPU (%) | Max RSS (kB) | Swaps |
|------|-------------|---------|--------------|-------|
| 17 | 13.21 | 803 | 1,784,744 | 0 |
| 23 | 12.78 | 778 | 1,792,888 | 0 |
| 31 | 15.32 | 743 | 1,801,376 | 0 |
| 43 | 13.69 | 798 | 1,780,356 | 0 |

Memory footprint was stable across seeds (~1.78–1.80 GB max RSS). No swap usage occurred in any run. The seed-31 elapsed time was approximately 2.5 s longer than the per-seed mean; this outlier did not reverse the wall-time advantage of the typed policy for that seed.

---

## Limitations

1. **Bounded task domain.** Experiments used compact generated agent subtasks with heuristic output-contract scoring. Results may not generalize to open-ended, human-reviewed, or genuinely messy workflows. The scoring heuristic may systematically favor outputs from one tier or the other in ways not representative of real task quality.

2. **Narrow model capability gap.** The tier gap (0.5B vs 1.5B parameters) is narrow relative to production deployments that might contrast, for example, a 7B model with a 70B+ model. A wider capability gap could change the success-rate parity finding: the cheap tier might fail more often, or the expensive tier might provide qualitatively different outputs that the heuristic does not capture.

3. **Single hardware configuration.** All runs executed on one aarch64 host with CPU-only inference. GPU-accelerated or multi-GPU environments may exhibit different latency and throughput profiles that alter the scheduler's cost–quality tradeoff. The absolute wall-time and tokens/s numbers are not portable across hardware.

4. **Heuristic scoring, not human judgment.** Useful value was computed by an automated output-contract heuristic. The magnitude of the useful-value delta (+1.646 to +3.896) is meaningful only relative to the scoring scale and should not be interpreted as a domain-independent effect size. Human evaluation might yield different rankings.

5. **Limited seed coverage and statistical power.** Four seeds provide directional evidence but limited statistical power. Confidence intervals are not reported because the sample size is insufficient for robust estimation. The consistency of direction across all four seeds is suggestive but not conclusive.

6. **Llama.cpp hook-prototype results, not production validation.** These experiments used local `llama-server` instances on a single machine. They do not account for network latency, rate limits, variable load, or the operational characteristics of managed API tiers. The results should be characterized as llama.cpp hook-prototype validation, not final production validation.

7. **Swap excluded from capacity evidence.** Memory capacity evidence relies solely on RSS and MemAvailable; swap was intentionally ignored. On systems where swap is active, memory pressure behavior may differ.

8. **No negative or mixed results observed.** While the absence of regression is a positive finding, the experimental conditions were sufficiently controlled that negative results might not emerge. Messier conditions (wider tier gaps, harder tasks, network latency) could plausibly produce mixed or negative outcomes.

---

## Reproducibility Checklist

- **Code availability**: Harness source files are present in the project directory (`src/latency_to_value_scheduler.py`, `src/real_model_tier_adapter.py`, `src/live_broker_latency_to_value.py`, `src/openai_compatible_broker_adapter.py`, `src/replay_latency_to_value_scheduler.py`, `scripts/`, `tests/`).
- **Model artifacts**: Qwen2.5-0.5B-Instruct-Q8_0.gguf (507 MiB) and Qwen2.5-1.5B-Instruct-Q8_0.gguf (1.6 GiB), both publicly available GGUF quantizations.
- **Server binary**: `llama-server` build `50494a2` (aarch64, version 1).
- **Command logs**: `logs/real_model_tier_smoke.command.log`, `logs/real_model_tier_calibrated_seed23.command.log`, `logs/real_model_tier_multiseed.command.log`.
- **Result artifacts**: Per-seed JSON/MD in `results/real_model_tier_calibrated_seed{17,23,31,43}.{json,md}`; aggregate in `results/real_model_tier_calibrated_summary.{json,md}`; smoke in `results/real_model_tier_smoke.{json,md}`.
- **Random seeds**: Explicitly recorded (17, 23, 31, 43 for calibrated runs; 17 for smoke test).
- **Configuration**: Calibrated: 8 tasks/policy, 2 parallel slots, max 2 attempts, retry budget ratio 0.6. Smoke: 2 tasks/policy, 1 slot, max 1 attempt.
- **Environment telemetry**: `/usr/bin/time -v` output and `/proc/meminfo` snapshots recorded per run.
- **Port cleanup**: Verified post-run across ports 18180–18343.
- **Pre-benchmark checks**: 17 unit tests passed; compile check passed.

---

## Conclusion

Replacing a single-model accounting proxy with two real locally hosted model tiers (Qwen2.5-0.5B-Instruct and Qwen2.5-1.5B-Instruct, both Q8_0 GGUF) preserved the latency-to-value scheduler's previously observed advantages. Across four calibrated seeds, useful value improved (mean +2.676), spend decreased (mean −0.811), wall time decreased (mean −1.623 s), and throughput increased (mean +58.512 tokens/s), with success-rate parity and zero retry regression. The typed scheduler achieved these gains by routing materially more calls to the cheap tier than the manual confidence broker, without incurring success-rate penalties.

These results support the hypothesis under test at medium confidence and moderate evidence strength, consistent with the project decision to finalize this validation branch as positive. However, the validation remains bounded by compact generated tasks, heuristic scoring, a narrow model gap, a single hardware configuration, and limited seed coverage. The findings are sufficient to warrant using the two-endpoint adapter as a regression gate but insufficient to claim production generality. The recommended next step is to conduct a separate human-reviewed evaluation on messy agent workflows with a wider tier gap if production external validity is required.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Metrics metadata | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260501T003848907852+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T003848907852+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T003848907852+0000/paper_manifest.json` |
| Scheduler source | `src/latency_to_value_scheduler.py` |
| Replay harness | `src/replay_latency_to_value_scheduler.py` |
| Live broker | `src/live_broker_latency_to_value.py` |
| OpenAI-compatible adapter | `src/openai_compatible_broker_adapter.py` |
| Real-tier adapter | `src/real_model_tier_adapter.py` |
| Real-tier launch script | `scripts/run_real_model_tier_adapter.py` |
| Unit test log | `logs/unittest.log` |
| Compile check log | `logs/compileall.log` |
| Smoke command log | `logs/real_model_tier_smoke.command.log` |
| Calibrated seed-23 command log | `logs/real_model_tier_calibrated_seed23.command.log` |
| Multi-seed command log | `logs/real_model_tier_multiseed.command.log` |
| Smoke results (JSON) | `results/real_model_tier_smoke.json` |
| Smoke results (MD) | `results/real_model_tier_smoke.md` |
| Calibrated seed 17 (JSON/MD) | `results/real_model_tier_calibrated_seed17.json`, `.md` |
| Calibrated seed 23 (JSON/MD) | `results/real_model_tier_calibrated_seed23.json`, `.md` |
| Calibrated seed 31 (JSON/MD) | `results/real_model_tier_calibrated_seed31.json`, `.md` |
| Calibrated seed 43 (JSON/MD) | `results/real_model_tier_calibrated_seed43.json`, `.md` |
| Calibrated summary (JSON) | `results/real_model_tier_calibrated_summary.json` |
| Calibrated summary (MD) | `results/real_model_tier_calibrated_summary.md` |
