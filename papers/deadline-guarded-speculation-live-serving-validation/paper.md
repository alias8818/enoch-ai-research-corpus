# Deadline-Guarded Speculation for Live LLM Serving: A Controlled Validation Study

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, benchmark results, and decision JSON produced by the OMX research automation pipeline). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact. It has not been subjected to human peer review.

---

## Abstract

We evaluate a deadline-guarded admission and fallback controller for live language model serving under mixed chat-and-extraction workloads. The controller combines earliest-deadline-first (EDF) admission, bounded concurrency, and a speculative fallback path that returns shorter completions when deadlines are at risk. We validate the controller in two phases: first against a synthetic FastAPI OpenAI-compatible shim that models concurrent serving dynamics, and second against a real cached Transformers endpoint serving HuggingFaceTB/SmolLM2-135M-Instruct on an NVIDIA GB10 GPU. In the synthetic-shim main run (n=180 requests), the deadline-guarded controller reduced p95 latency by 46.6% and deadline-miss rate by 70.0 percentage points, with a 4.2% throughput reduction and zero output success loss. In the real-model main run (n=120 requests), p95 latency improved by 39.2%, but deadline-miss rate increased by 0.83 percentage points—within the predeclared +1 percentage-point guardrail but not an improvement. Throughput decreased by 0.65% and output success was unchanged. These results support the hypothesis that deadline-guarded admission materially reduces tail latency under mixed workloads, but they do not establish that the controller resolves deadline misses under hard-overload single-stream serving. All evidence is confined to one small model, one GPU, and a project-local serving stack; external replication is needed.

## 1. Introduction

Latency-sensitive applications of large language models (LLMs)—including interactive chat, real-time extraction, and tool-augmented pipelines—impose deadline constraints on inference. When a serving endpoint is shared across heterogeneous request types with different latency budgets, a throughput-maximizing scheduler that admits all requests indiscriminately can produce severe tail-latency inflation and high deadline-miss rates. A natural alternative is to admit requests selectively based on their remaining slack and to fall back to shorter or approximate completions when deadlines are at risk.

This study evaluates a **deadline-guarded speculation** controller that combines three mechanisms:

1. **EDF-based admission**: incoming requests are admitted only if their deadline slack exceeds a threshold given current queue depth and concurrency.
2. **Bounded concurrency**: a cap on in-flight requests prevents queue buildup that would violate deadlines of already-admitted work.
3. **Speculative fallback**: when a request's remaining slack falls below a threshold during generation, the controller triggers a fallback that returns a truncated completion rather than missing the deadline.

The controller was originally developed and tested in a trace-driven simulator (parent project), where it showed substantial improvements in p95 latency and deadline-miss rate under simulated mixed chat/extraction pressure. The present work validates the same controller logic against live HTTP endpoints, progressing from a synthetic shim to a real cached Transformers model server.

We define a predeclared kill condition: the validation is positive only if the deadline-guarded controller achieves at least a 10% p95 latency improvement over throughput-only scheduling, without increasing the deadline-miss rate by more than 1 percentage point and without more than 0.2 percentage-point quality/correctness loss on the mixed-pressure workload, after a smoke run and one calibration pass.

## 2. Method

### 2.1 Controller Design

The deadline-guarded controller operates as a middleware layer between the client workload generator and the OpenAI-compatible serving endpoint. For each incoming request, the controller:

- Assigns a deadline based on the request type (chat requests receive a longer deadline than extraction requests).
- Evaluates admission using an EDF policy: if the estimated completion time given current queue state exceeds the request's deadline, the request is either queued with lower priority or rejected.
- Enforces a concurrency cap (`guard-concurrency`) on in-flight requests.
- Monitors in-flight requests; when a request's remaining slack drops below a threshold, the controller invokes a fallback path that returns a shorter completion.

The throughput-only baseline admits all requests immediately with no concurrency cap and no fallback mechanism.

### 2.2 Workload Generation

The benchmark generates a mixed workload of chat and extraction requests. Each request is sent as an OpenAI-compatible `/v1/chat/completions` call with a `max_tokens` cap. The mix ratio and deadline assignments are fixed across runs to ensure comparability.

### 2.3 Measurement

The benchmark records per-request end-to-end latency (from request submission to response receipt), deadline compliance (whether the response arrived before the assigned deadline), tokens per second, queue wait time, fallback invocation rate, cache hit rate, and error count. Aggregate statistics (p50, p95, p99) are computed from the per-request data. Server-side metrics include RSS, CUDA allocator usage, request count, token count, and GPU utilization samples.

## 3. Experimental Setup

### 3.1 Phase 1: Synthetic FastAPI Shim

Because no existing OpenAI-compatible endpoint was available on the host (ports 8000, 11434, and 8080 returned 404, connection refused, or non-model responses, and the global Python environment lacked `transformers`/`torch`), we implemented a project-local synthetic shim (`scripts/openai_compat_shim.py`). This FastAPI server models concurrent serving dynamics including prefix-cache hits and evictions, active token memory pressure, and a deadline-guard fallback metadata path. It does not perform real model inference.

**Runs:**

| Run | Requests | Duration (s) | Concurrency | Guard Concurrency | Port | Purpose |
|-----|----------|---------------|-------------|-------------------|------|---------|
| Smoke | 48 | 4.5 | 8 | 5 | 8219 | Calibration (over-conservative) |
| Calibrated | 96 | 5.0 | 8 | 8 | 8220 | Tuned calibration |
| Main | 180 | 9.0 | 8 | 8 | 8221 | Primary synthetic-shim result |

### 3.2 Phase 2: Real Cached-Model Transformers Server

We implemented a real OpenAI-compatible endpoint (`scripts/openai_compat_transformers_server.py`) backed by `AutoModelForCausalLM` from the Hugging Face Transformers library. The model `HuggingFaceTB/SmolLM2-135M-Instruct` was loaded from the local Hugging Face cache (`local_files_only=True`) onto `cuda:0` of an NVIDIA GB10 GPU. The server exposes `/v1/models`, `/v1/chat/completions`, and `/metrics`.

**Software environment:** project-local `.venv` with `torch==2.11.0+cu130`, `transformers==5.5.4`, `fastapi`, `uvicorn`.

**Runs:**

| Run | Requests | max_tokens Cap | Purpose |
|-----|----------|----------------|---------|
| Smoke | 24 | 24 | Route verification and calibration |
| Calibration | 80 | 64 | Kill-condition check |
| Main | 120 | 64 | Primary real-model result |

### 3.3 Hardware

- CPU: 20 cores
- GPU: NVIDIA GB10
- System memory: ~121 GB available at benchmark time
- Benchmark process max RSS: 28,124 KB (synthetic shim phase); server max RSS: 2,062,232 KB (real-model phase)
- Max CUDA allocated: 315,619,840 bytes (~301 MB)

## 4. Results

### 4.1 Phase 1: Synthetic Shim

**Smoke run (guard-concurrency=5).** The over-conservative concurrency cap caused p95 latency to regress by 55.8% relative to throughput-only, with no miss-rate benefit. This run served as a calibration signal: the guard concurrency must match or exceed the workload concurrency to avoid artificial starvation.

**Calibrated run (guard-concurrency=8).** With guard concurrency equal to workload concurrency, the deadline-guarded controller achieved p95 improvement of 20.0%, deadline-miss delta of −44.8 percentage points, zero success delta, fallback rate 18.75%, and tok/s change of −4.2% (approximate from run notes context).

**Main run (n=180).**

| Metric | Throughput-only | Deadline-guarded | Delta |
|--------|----------------|------------------|-------|
| p50 latency | 2,444.5 ms | 880.7 ms | −63.9% |
| p95 latency | 3,395.4 ms | 1,813.8 ms | −46.6% |
| p99 latency | 3,583.3 ms | 2,117.0 ms | −40.9% |
| Deadline-miss rate | 0.7278 | 0.0278 | −70.0 pp |
| Tokens/sec | 1,009.96 | 967.67 | −4.2% |
| Success rate | 1.0 | 1.0 | 0.0 pp |
| Fallback rate | 0.0 | 0.2667 | — |
| Cache hit rate | 0.8 | 1.0 | — |
| Errors | 0 | 0 | — |

The synthetic-shim results show that the controller substantially reduces both tail latency and deadline-miss rate under simulated concurrent pressure, at a modest throughput cost and with no output success degradation.

### 4.2 Phase 2: Real Cached-Model Server

**Smoke run (cap=24).** Route verification succeeded (`models_count=1`, `chat_completion_ok=true`). No deadline pressure or fallback benefit was observed; this run confirmed endpoint correctness and served as calibration evidence.

**Calibration run (cap=64, n=80).** The deadline-guarded controller achieved p95 improvement of 37.4%, deadline-miss delta of 0.0 percentage points, success delta 0, fallback rate 83.75%, and tok/s change of −0.23%. The kill condition was not triggered.

**Main run (cap=64, n=120).**

| Metric | Throughput-only | Deadline-guarded | Delta |
|--------|----------------|------------------|-------|
| p95 latency | 41,041.9 ms | 24,959.4 ms | −39.2% |
| Deadline-miss rate | — | — | +0.83 pp |
| Success rate | 1.0 | 1.0 | 0.0 pp |
| Tokens/sec | — | — | −0.65% |
| Fallback rate | 0.0 | 0.8917 | — |
| Errors | 0 | 0 | — |

The p95 improvement of 39.2% exceeds the 10% threshold. The deadline-miss rate increased by 0.83 percentage points, which is within the +1 percentage-point guardrail but represents a slight degradation rather than an improvement. The success/quality delta is 0.0 percentage points, within the 0.2 pp allowance. The kill condition was not triggered.

**Server-side metrics (main run):** 402 requests served, 0 errors, 20,237 total completion tokens, average generation time 0.3524 s, max server RSS 2,062,232 KB, max CUDA allocated 315,619,840 bytes. A mid-run utilization sample recorded approximately 60% GPU utilization, 18.85 W power, server CPU approximately 85.7%, and MemAvailable approximately 113 GiB.

### 4.3 Summary of Evidence

The deadline-guarded controller passes the predeclared acceptance criteria in both the synthetic-shim and real-model phases. However, the nature of the evidence differs substantially between phases:

- **Synthetic shim**: large improvements in both p95 latency and deadline-miss rate. The shim's simplified serving model may overstate the controller's effectiveness on deadline misses.
- **Real model**: large p95 improvement but a small increase in deadline-miss rate rather than a decrease. The high fallback rate (89.2%) indicates that the controller is aggressively truncating completions to preserve latency, which reduces per-request latency but does not prevent all deadline misses under the single-stream serving configuration tested.

## 5. Limitations

1. **Single small model.** All real-model results use SmolLM2-135M-Instruct, a 135M-parameter model. The controller's behavior on larger models with different latency profiles and batching characteristics is unknown.

2. **Single-stream serving.** The Transformers server processes requests sequentially without continuous batching. Production serving stacks (vLLM, SGLang, TensorRT-LLM) employ continuous batching, prefix caching, and paged attention, which change the queueing dynamics the controller relies on. The results here do not predict controller behavior under continuous batching.

3. **Deadline-miss rate did not improve in the real-model main run.** The +0.83 percentage-point increase was within the predeclared guardrail, but it contradicts the improvement observed in simulation and in the synthetic shim. This suggests the controller's fallback mechanism reduces tail latency by truncating completions but may not prevent deadline misses when the serving stack lacks the headroom to complete even truncated requests within the deadline.

4. **High fallback rate.** In the real-model main run, 89.2% of deadline-guarded requests triggered the fallback path. This raises questions about whether the controller is providing meaningful admission control or simply defaulting to truncated outputs for most requests. The relationship between fallback rate, output quality, and downstream task utility was not evaluated.

5. **No quality evaluation beyond success rate.** The benchmark measures whether the endpoint returns a valid completion (success rate) but does not evaluate output quality, correctness, or task performance of truncated versus full completions. A 0.0 percentage-point success delta confirms that no requests failed outright, but does not address whether truncated fallback completions are useful.

6. **Single hardware configuration.** All experiments ran on one NVIDIA GB10 GPU with one CPU configuration. GPU utilization during the main run was approximately 60%, indicating the server was not fully saturated; results under higher saturation may differ.

7. **Calibration dependency.** The smoke run with guard-concurrency=5 produced a 55.8% p95 regression, demonstrating that the controller's parameters require tuning for the workload. The reported results reflect one tuning pass; performance under different concurrency levels, deadline assignments, or workload mixes is not characterized.

8. **No comparison to alternative admission controllers.** The study compares deadline-guarded speculation only against an unadmitted throughput-only baseline. Other admission control strategies (e.g., simple concurrency limits, priority queues, latency-aware scheduling) were not evaluated.

## 6. Reproducibility Checklist

| Item | Status |
|------|--------|
| Code available | `scripts/openai_compat_shim.py`, `scripts/openai_compat_transformers_server.py`, `scripts/live_deadline_guard_bench.py` are project-local |
| Model specified | HuggingFaceTB/SmolLM2-135M-Instruct, loaded from local HF cache |
| Hardware specified | NVIDIA GB10, 20 CPU cores, ~121 GB RAM |
| Software versions | torch==2.11.0+cu130, transformers==5.5.4, fastapi, uvicorn |
| Random seeds | Not recorded in artifacts; synthetic shim uses modeled dynamics |
| Hyperparameters | Concurrency=8, guard-concurrency=8, max_tokens cap=64 (real-model main), duration=9.0 s (shim main) |
| Statistical tests | No formal hypothesis tests reported; comparisons are descriptive |
| Kill condition predeclared | Yes: ≥10% p95 improvement, ≤+1 pp miss-rate delta, ≤0.2 pp success delta |
| All runs reported | Smoke, calibration, and main runs for both phases are documented |
| Negative results reported | Yes: smoke run p95 regression (+55.8%), real-model miss-rate increase (+0.83 pp) |
| Server cleaned up | Yes: helper servers stopped before yield; no lingering endpoints |

## 7. Conclusion

This study provides evidence that a deadline-guarded admission and fallback controller can materially reduce p95 latency in live LLM serving under mixed chat/extraction workloads. In a synthetic-shim benchmark, the controller reduced p95 latency by 46.6% and deadline-miss rate by 70.0 percentage points. Against a real cached Transformers endpoint serving SmolLM2-135M-Instruct, the controller reduced p95 latency by 39.2% with a negligible throughput cost (−0.65%) and no output success loss, but deadline-miss rate increased by 0.83 percentage points rather than decreasing.

The evidence supports the hypothesis that deadline-guarded speculation improves tail latency, but it does not support the stronger claim that the controller resolves deadline misses under hard-overload conditions in single-stream serving. The discrepancy between the synthetic-shim and real-model results on deadline-miss rate highlights the importance of validating scheduling controllers against real inference stacks rather than simulated serving dynamics alone.

The project decision is to finalize this branch as supported with medium confidence. The recommended next step is to evaluate the same controller and acceptance criteria against a production-grade serving stack with continuous batching (e.g., vLLM or SGLang), which would provide evidence about whether the controller's benefits generalize beyond single-stream Transformers serving.

## Referenced Artifacts

### Project-local source files
- `scripts/openai_compat_shim.py` — Synthetic FastAPI OpenAI-compatible shim
- `scripts/openai_compat_transformers_server.py` — Real cached-model Transformers server
- `scripts/live_deadline_guard_bench.py` — Live endpoint benchmark harness

### Decision and metadata
- `.omx/project_decision.json` — Project decision (finalize_positive, supported, medium confidence)
- `.omx/metrics.json` — Session metrics
- `run_notes.md` — Detailed run notes and interpretation

### Synthetic-shim result files
- `results/live_main/live_benchmark_report.md`
- `results/live_main/live_summary.csv`

### Real-model result files
- `results/real_model_main/transformers_server_metrics_final.json`
- `results/real_model_main/live_benchmark_report.md`
- `results/real_model_main/live_summary.csv`
- `results/real_model_main/live_requests.csv`
- `results/real_model_main/live_benchmark_results.json`
- `results/real_model_calib_cap64/live_benchmark_report.md`
- `results/real_model_calib_cap64/live_summary.csv`
- `results/real_model_calib_cap64/live_requests.csv`
- `results/real_model_calib_cap64/live_benchmark_results.json`
- `results/real_model_calib/live_benchmark_report.md`
- `results/real_model_calib/live_summary.csv`
- `results/real_model_calib/live_requests.csv`
- `results/real_model_calib/live_benchmark_results.json`
- `results/real_model_smoke/live_benchmark_report.md`
- `results/real_model_smoke/live_summary.csv`
- `results/real_model_smoke/live_requests.csv`
- `results/real_model_smoke/live_benchmark_results.json`
- `results/real_model_smoke/transformers_server.log`

### Paper audit artifacts
- `papers/.../claim_ledger.json` — Claim audit with confidence levels and forbidden wording
- `papers/.../evidence_bundle.json` — Full evidence bundle with decision, run notes, and file manifest
- `papers/.../paper_manifest.json` — Paper artifact manifest
