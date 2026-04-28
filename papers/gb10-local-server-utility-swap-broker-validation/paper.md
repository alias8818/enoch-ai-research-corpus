# Utility-Based Swap Broker Scheduling for Local LLM Serving: A Live-Server Validation Study

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We evaluate a utility-based swap broker scheduling policy against a fixed FIFO baseline for local OpenAI-compatible LLM serving on a GB10 server. Prior simulator-only evidence from a parent project suggested the utility broker could reduce tail latency under memory pressure, but required live-server validation with hardware telemetry. We constructed a replay harness targeting a real llama.cpp server endpoint and conducted a three-phase validation: (1) a mock-server smoke test confirming harness correctness, (2) a low-pressure live smoke test against Phi-4-mini-instruct establishing calibration, and (3) a pressure-calibrated three-seed replay at elevated concurrency and reduced broker capacity. In the clean multiseed decision run, the utility broker reduced session p95 latency by a mean of 16.8% (median 18.9%, range 11.9%–19.5%) with zero request errors across all seeds, clearing a pre-registered 10% improvement threshold. However, request-level p95 reduction was inconsistent across seeds (mean 17.5%, but one seed showed a 3.2% regression), scheduler churn improved by only 5.3% on average, and throughput was essentially flat (mean +0.7%). The live evidence thus supports a latency-oriented broker benefit under the tested conditions, but does not establish throughput or cache-churn gains. Results are bounded by the small model choice (Phi-4-mini-instruct Q4_K_M), modest GPU utilization (25–42%), and single-hardware configuration.

---

## 1. Introduction

Local LLM serving on consumer and edge hardware faces scheduling decisions when concurrent sessions compete for limited KV-cache and GPU memory. A fixed first-in-first-out (FIFO) admission policy processes requests in arrival order regardless of their expected resource cost or latency sensitivity. An alternative approach assigns each request a utility score reflecting its expected contribution to session-level latency objectives and admits or reorders requests accordingly.

A prior project (parent project `source-record-redacted`) developed a simulator (`swap_broker_sim.py`) that produced moderate evidence supporting a utility-broker mechanism. However, that work explicitly required live OpenAI-compatible serving validation with hardware telemetry before the hypothesis could be considered supported.

This study addresses that requirement. We report results from a live-server replay harness that wraps the utility/FIFO policy comparison around a real llama.cpp server endpoint, recording request and session latency, throughput, scheduler churn, and hardware telemetry. The project established a pre-registered kill condition: the branch would be terminated if a real replay showed the utility broker failing to improve p95 latency or cache-churn/throughput by at least 10% versus FIFO under comparable request mix and memory-pressure settings.

---

## 2. Method

### 2.1 Replay Harness

We implemented `openai_swap_replay.py`, a dependency-free Python harness that:

1. Verifies server availability via the `/v1/models` endpoint.
2. Sends `/v1/chat/completions` requests organized into sessions, replaying the same mixed workload under two scheduling policies: `fixed_fifo` and `utility_broker`.
3. Records per-request latency, per-session latency, completion tokens per second, scheduler cache-churn and admission events, CPU load (via `/proc/stat`), process memory, `/proc/meminfo` UMA pressure, and optional GPU utilization and power from `nvidia-smi`.
4. Outputs raw request rows, telemetry CSVs, and summary JSON/Markdown artifacts.

A companion script, `mock_openai_server.py`, provides a minimal OpenAI-compatible mock server used exclusively for harness smoke testing. It has no real KV-cache or server scheduler and therefore cannot produce meaningful policy-separation evidence.

### 2.2 Scheduling Policies

- **Fixed FIFO**: Requests are admitted and processed in arrival order with no reordering.
- **Utility Broker**: Each request receives a utility score based on session-level factors (remaining context budget, session age, token-scale class). The broker admits, defers, or reorders requests to maximize aggregate utility within a configurable capacity limit. When the capacity is saturated, lower-utility requests are deferred, potentially reducing cache churn and improving tail latency for higher-utility sessions.

### 2.3 Server Configuration

The target server was `llama-server` from llama.cpp, launched with the following parameters across validation phases:

| Phase | Model | `-np` | `-c` | `-ngl` | `n_ctx_seq` (approx.) |
|---|---|---|---|---|---|
| Live smoke | Phi-4-mini-instruct Q4_K_M | 2 | 2048 | all | ~512 |
| Calibration 1 | Phi-4-mini-instruct Q4_K_M | 6 | 4096 | all | ~768 |
| Calibration 2 | Phi-4-mini-instruct Q4_K_M | 6 | 4096 | all | ~768 |
| Multiseed decision | Phi-4-mini-instruct Q4_K_M | 4 | 8192 | all | ~2048 |

The context-length increase in the final phase was necessary to eliminate HTTP 400 context-limit errors observed during calibration while preserving scheduling pressure.

### 2.4 Workload Parameters

The workload generator preserves the mixed-workload shape from the parent simulator project. Key parameters for the clean decision run:

- **Sessions**: 36 per policy per seed
- **Concurrency**: 4
- **Broker capacity**: 220
- **Token scale**: 0.14
- **Seeds**: 101, 202, 303

### 2.5 Metrics

- **Session p95 latency**: 95th-percentile wall-clock time from first request in a session to last token of the final response.
- **Request p95 latency**: 95th-percentile per-request response time.
- **Completion throughput**: Tokens per second averaged across completed requests.
- **Scheduler churn**: Number of cache eviction/admission events recorded by the broker harness.
- **Deadline misses**: Requests exceeding a configured time budget (0 in all reported runs).
- **Request errors**: HTTP 4xx/5xx responses (0 in clean decision runs; nonzero in calibration due to context limits).
- **Hardware telemetry**: GPU utilization (%), GPU power (W), CPU utilization (%), MemAvailable (GiB), swap activity.

---

## 3. Results

### 3.1 Phase 1: Mock Smoke Test

The mock server completed 8 sessions and 15 requests per policy with 0 errors. As expected, no meaningful policy separation was observed because the mock server lacks a real KV-cache scheduler. This phase validated harness correctness only.

### 3.2 Phase 2: Live Smoke Test (Low Pressure)

Against a live llama.cpp instance with minimal concurrency (`-np 2`, 6 sessions, 10 requests per policy):

| Metric | FIFO | Utility Broker | Change |
|---|---|---|---|
| Request p95 latency | 0.250 s | 0.231 s | −7.4% |
| Session p95 latency | 1.649 s | 1.637 s | −0.7% |
| Completion throughput | 1.406 tok/s | 1.405 tok/s | ~0% |
| Scheduler churn | 6 | 6 | 0% |
| Mean GPU utilization | 1.26% | 2.80% | — |
| Request errors | 0 | 0 | — |
| Deadline misses | 0 | 0 | — |

The very low GPU utilization confirms this was a harness-validation and throughput-calibration run, insufficient to test the 10% improvement threshold.

### 3.3 Phase 3a: Pressure Calibration

Two calibration passes increased workload pressure to induce scheduler activity:

**Calibration pass 1** (24 sessions, concurrency 6, capacity 350, token scale 0.12): Produced HTTP 400 context-limit errors. Utility broker showed request p95 −15.0%, session p95 −3.7%, churn −8.9%, throughput −7.3% (utility lower).

**Calibration pass 2** (36 sessions, concurrency 6, capacity 220, token scale 0.14): Also produced context-limit errors. Utility broker showed session p95 −10.3%, request p95 −8.0%, throughput nearly flat.

Both calibration runs were retained as tuning evidence but excluded from the clean decision due to request errors that confound the latency comparison.

### 3.4 Phase 3b: Clean Multiseed Decision Run

After restarting the server with `-np 4 -c 8192` (eliminating context-limit errors), three seeds were run at 36 sessions, concurrency 4, capacity 220, token scale 0.14. Both policies achieved 0 request errors and 0 deadline misses across all seeds.

**Session p95 latency reduction (utility vs. FIFO):**

| Seed | Reduction |
|---|---|
| 101 | 19.5% |
| 202 | 18.9% |
| 303 | 11.9% |
| **Mean** | **16.8%** |
| **Median** | **18.9%** |

All three seeds cleared the pre-registered 10% session-p95 threshold.

**Request p95 latency reduction (utility vs. FIFO):**

| Seed | Reduction |
|---|---|
| 101 | 34.4% |
| 202 | 21.3% |
| 303 | −3.2% |
| **Mean** | **17.5%** |
| **Median** | **21.3%** |

Request-level p95 reduction was positive on average but inconsistent: seed 303 showed a 3.2% regression at the request level despite an 11.9% improvement at the session level.

**Other metrics:**

| Metric | Mean Change | Per-Seed Range |
|---|---|---|
| Scheduler churn | −5.3% | — |
| Completion throughput | +0.7% | −1.6% to +4.4% |
| Deadline misses | 0 (both policies) | — |

**Hardware telemetry (clean decision run):**

| Metric | FIFO | Utility Broker |
|---|---|---|
| Mean GPU utilization | ~25–42% (seed-dependent) | ~28–34% (seed-dependent) |
| CPU utilization | ~2–3% | ~2–3% |
| Min MemAvailable | ~112–116 GiB | ~112–116 GiB |
| Swap activity | None | None |

---

## 4. Limitations

1. **Small model only.** All results were obtained with Phi-4-mini-instruct Q4_K_M (~2.4B parameters quantized to Q4_K_M). The utility broker's behavior under larger models (e.g., 70B-class) with substantially different KV-cache pressure profiles is unknown.

2. **Modest GPU utilization.** Peak GPU utilization during the decision run ranged from ~25% to ~42%. Production deployments under heavier batch load may exhibit different scheduling dynamics, and the broker's benefit may increase or decrease under sustained high utilization.

3. **Single hardware configuration.** All runs were conducted on a single GB10 server. No cross-hardware replication was performed.

4. **Inconsistent request-level p95.** While session-level p95 improved consistently, request-level p95 showed a 3.2% regression in one of three seeds. The mechanism's effect on per-request tail latency is less stable than its effect on session-level tail latency.

5. **No throughput or cache-churn win established.** Scheduler churn improved by only 5.3% on average, and throughput was essentially flat. The pre-registered kill condition specified a 10% threshold for these metrics as well; the evidence does not support a broad throughput or cache-churn benefit.

6. **Calibration runs contained errors.** The two pressure-calibration passes produced HTTP 400 context-limit errors that confounded latency measurement. Although the final multiseed run eliminated these errors by increasing the context window, the calibration artifacts reflect a configuration that would not be suitable for clean measurement.

7. **Broker capacity was manually tuned.** The capacity parameter (220) and token scale (0.14) were selected through calibration to produce scheduling pressure. The sensitivity of results to these parameters has not been systematically explored.

8. **No comparison against other scheduling baselines.** Only FIFO was tested as a baseline. Priority-based, shortest-job-first, or other scheduling policies were not evaluated.

9. **Automated artifact provenance.** This draft and its supporting evidence were generated by an automated research pipeline. No independent human replication has been performed.

---

## 5. Reproducibility Checklist

- [x] **Harness source available**: `src/openai_swap_replay.py` and `src/mock_openai_server.py` are present in the project directory.
- [x] **Server configuration documented**: llama.cpp launch parameters (`-ngl all -c 8192 -np 4 -cb --metrics --jinja`) and model path are recorded in run notes.
- [x] **Workload parameters specified**: Sessions (36), concurrency (4), capacity (220), token scale (0.14), seeds (101, 202, 303).
- [x] **Raw request data retained**: `requests.csv` for each seed.
- [x] **Telemetry data retained**: Per-seed telemetry CSVs for both policies; server `/metrics` (Prometheus format) and `/slots` JSON captured post-run.
- [x] **Summary artifacts retained**: Per-seed and aggregate `summary.json` and `summary.md`.
- [x] **Server logs retained**: `llama_server_pressure_np4_ctx8192.log`.
- [x] **Pre-registered threshold documented**: Kill condition (≥10% improvement in p95 latency or cache-churn/throughput) stated in run notes before the decision run.
- [ ] **External replication**: Not performed. Results are bounded to the single hardware/software configuration described.
- [ ] **Cross-model validation**: Not performed. Only Phi-4-mini-instruct Q4_K_M was tested.
- [ ] **Statistical significance testing**: Not performed. Three seeds provide informal consistency evidence but not formal significance.

---

## 6. Conclusion

Under a live llama.cpp server on GB10 hardware with a pressure-calibrated workload, the utility-based swap broker scheduling policy reduced session p95 latency by a mean of 16.8% across three clean seeds, clearing a pre-registered 10% improvement threshold. The current project artifacts support this finding in the tested setting.

However, the evidence is mixed for non-latency metrics: request-level p95 improvement was inconsistent (one seed regressed by 3.2%), scheduler churn improved by only 5.3%, and throughput was essentially flat. The live evidence therefore supports a latency-oriented broker benefit rather than a broad throughput or cache-churn improvement.

The recommended follow-up is to carry the utility broker forward as a latency-supported mechanism while explicitly caveating that throughput and cache-churn gains were not established. Future work should address cross-model validation, higher GPU utilization regimes, systematic parameter sensitivity analysis, and comparison against additional scheduling baselines.

---

## Referenced Artifacts

### Run notes and decision
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Source code
- `src/openai_swap_replay.py`
- `src/mock_openai_server.py`

### Mock smoke test
- `artifacts/mock_smoke/` (harness validation only; no model-serving evidence)

### Live smoke test
- `artifacts/llama_phi_smoke/summary.json`
- `artifacts/llama_phi_smoke/requests.csv`
- `artifacts/llama_phi_smoke/llama_metrics.prom`
- `artifacts/llama_phi_smoke/slots.json`
- `artifacts/logs/llama_server_phi.log`

### Pressure calibration (contains request errors; tuning evidence only)
- `artifacts/pressure_calibration/s24_c6_cap350_scale0.12/`
- `artifacts/pressure_calibration/s36_c6_cap220_scale0.14/`

### Clean multiseed decision run
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/aggregate_summary.json`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/aggregate_summary.md`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/llama_metrics_after_multiseed.prom`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/slots_after_multiseed.json`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_101/summary.json`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_101/summary.md`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_101/requests.csv`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_101/telemetry_fixed_fifo.csv`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_101/telemetry_utility_broker.csv`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_202/summary.json`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_202/summary.md`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_202/requests.csv`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_202/telemetry_fixed_fifo.csv`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_202/telemetry_utility_broker.csv`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_303/summary.json`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_303/summary.md`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_303/requests.csv`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_303/telemetry_fixed_fifo.csv`
- `artifacts/pressure_multiseed/s36_c4_cap220_scale0.14_multiseed/seed_303/telemetry_utility_broker.csv`
- `artifacts/logs/llama_server_pressure_np4_ctx8192.log`

### Paper and audit artifacts
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
