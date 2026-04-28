# OpenAI-Compatible Deployment of a Syntax-Preserving RAG Adapter: An Evidence-Grounded Technical Report

> **AI Provenance Notice:** This draft was generated entirely by AI from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We report on the deployment of a syntax-preserving retrieval-augmented generation (RAG) adapter behind an OpenAI-compatible HTTP endpoint. The adapter, `RAGServingAdapter`, is wrapped by a lightweight HTTP shim (`openai_adapter_server.py`) that exposes `GET /v1/models` and `POST /v1/chat/completions`, accepting per-request context chunks and RAG control parameters. In a local prototype benchmark using Qwen2.5-3B-Instruct with batch-4 HTTP concurrency across 5 RAG cases (10 rows, 20 requests), the distilled (adapter-mediated) condition achieved an answer F1 of 0.4333 compared to a baseline answer F1 of 0.0000, yielding a +43.33 percentage-point gain under identical retrieval. End-to-end p95 latency overhead was 4.73% (5564.33 ms distilled vs. 5313.11 ms baseline). Throughput was 1.30 requests/second. These results are limited to a single local hardware configuration, a small synthetic benchmark, and one model; the zero baseline F1 warrants careful interpretation. The current project artifacts support the finding that the adapter can operate behind an OpenAI-compatible HTTP boundary with preserved quality signal and modest latency overhead in the tested setting.

## 1. Introduction

Retrieval-augmented generation systems commonly inject raw retrieved document chunks into a language model's prompt context. This approach can degrade output quality when chunks are noisy, redundant, or syntactically incompatible with the model's expected input format. Syntax-preserving RAG adapters address this by distilling or restructuring retrieved context before it reaches the model, aiming to improve answer quality without modifying the underlying model.

A practical deployment concern is compatibility: many production systems and toolchains expect an OpenAI-compatible API surface (`/v1/models`, `/v1/chat/completions`). If a RAG adapter requires a custom client protocol, adoption friction increases. This work investigates whether a syntax-preserving RAG adapter can be deployed behind a standard OpenAI-compatible HTTP boundary while preserving its quality improvement signal and imposing acceptable latency overhead.

The central hypothesis is that wrapping `RAGServingAdapter` in an OpenAI-compatible HTTP shim will (a) pass standard endpoint smoke tests, (b) preserve or improve the adapter's quality signal when requests traverse the HTTP boundary, and (c) impose modest latency overhead relative to direct invocation.

## 2. Method

### 2.1 OpenAI-Compatible HTTP Shim

A dependency-light HTTP server (`src/openai_adapter_server.py`) was implemented to wrap `RAGServingAdapter`. The server exposes two endpoints conforming to the OpenAI API shape:

- **`GET /v1/models`**: Returns the served model identifier and metadata.
- **`POST /v1/chat/completions`**: Accepts standard OpenAI-shaped chat completion requests. The request body supports an extended `context_chunks` field (a list of retrieved text segments) and a `rag` control object that includes a `distill` boolean flag. When `rag.distill=true`, the adapter distills the context chunks before forwarding them to the model; when `rag.distill=false`, raw chunks are passed through as the baseline condition.

The server supports two backends:

1. **Extractive backend**: A deterministic, model-free backend that performs syntax-preserving extraction on context chunks without invoking a language model.
2. **Transformers backend**: A local PyTorch/Transformers backend that loads a Hugging Face model (e.g., Qwen2.5-3B-Instruct) and generates responses from the (optionally distilled) context.

### 2.2 HTTP Benchmark Client

A benchmark harness (`src/run_http_adapter_benchmark.py`) was added to send RAG requests through the HTTP endpoint. The harness:

- Constructs mixed RAG test cases from the parent project's benchmark suite.
- Sends each case twice through the HTTP boundary: once with `rag.distill=false` (baseline) and once with `rag.distill=true` (distilled).
- Uses batch-4 HTTP concurrency (up to 4 concurrent requests).
- Records per-request quality metrics (answer F1 against gold references), end-to-end latency (p50, p95), throughput, and resource telemetry (GPU utilization, UMA memory availability, client RSS).

### 2.3 Test Protocol

The following verification steps were performed:

1. Static compilation check: `python3 -m py_compile src/*.py tests/run_tests.py` — passed.
2. Unit/regression tests: `python3 tests/run_tests.py` — passed (adapter/distiller regressions).
3. Extractive backend smoke test: Server started with `--backend extractive`, `/v1/models` and `/v1/chat/completions` verified, extractive HTTP batch-4 smoke benchmark run, server stopped.
4. Transformers backend full benchmark: Server started with `--backend transformers --model Qwen/Qwen2.5-3B-Instruct --served-model-name syntax-rag-qwen-http --port 8018`, endpoints verified, full mixed RAG HTTP batch-4 benchmark run, server stopped.

No helper server was left running after benchmark completion.

## 3. Results

### 3.1 Endpoint Conformance

Both `/v1/models` and `/v1/chat/completions` returned structurally valid OpenAI-shaped responses. The `/v1/models` endpoint returned model id `syntax-rag-qwen-http`. The `/v1/chat/completions` endpoint included `rag_adapter` metrics in its response payload, confirming that adapter processing occurred server-side.

### 3.2 Quality Metrics

The Qwen HTTP batch-4 benchmark comprised 10 rows across 5 cases, with 20 total HTTP requests at concurrency 4.

| Condition | Answer F1 |
|---|---|
| Baseline (`rag.distill=false`) | 0.0000 |
| Distilled (`rag.distill=true`) | 0.4333 |
| **Gain** | **+43.33 pp** |

The `success_quality_gain_same_retrieval` flag was `True`, and the kill condition (`avg_distilled_answer_f1 <= avg_baseline_answer_f1`) was not hit.

**Interpretation of zero baseline F1:** The baseline condition produced answers with zero F1 against gold references. This indicates that, without distillation, the model's responses shared no token overlap with the reference answers in this benchmark. The distilled condition's F1 of 0.4333, while a large relative improvement, remains modest in absolute terms. The zero baseline may reflect the specific prompt construction, the nature of the gold references, or the model's tendency to produce verbose or tangential responses when given raw chunks. This result should not be generalized as evidence that undistilled RAG always produces zero-quality answers.

### 3.3 Latency

| Metric | Baseline | Distilled | Overhead |
|---|---|---|---|
| End-to-end p50 | 2129.20 ms | 2843.55 ms | +33.6% |
| End-to-end p95 | 5313.11 ms | 5564.33 ms | +4.73% |

The p95 overhead is modest at 4.73%. The p50 overhead is larger (33.6%), which may reflect the fixed cost of adapter processing becoming proportionally more visible at lower latencies. The p95 overhead being smaller suggests that the adapter's cost is largely additive and does not compound with tail-latency effects.

### 3.4 Throughput

- Throughput: 1.3004 HTTP requests/second
- Wall time: 15,380.27 ms
- HTTP-level p50/p95: 2195.61 ms / 5319.21 ms

### 3.5 Resource Telemetry

| Metric | Value |
|---|---|
| GPU utilization (sample) | 92% |
| UMA MemAvailable (before) | 113,079,308 kB |
| UMA MemAvailable (after) | 113,167,984 kB |
| Client max RSS | 25,404 kB |

GPU utilization at 92% indicates near-saturation during the benchmark. UMA memory availability slightly increased after the benchmark (by ~88,676 kB), which is unexpected and may reflect measurement noise, OS-level memory management, or the release of transient allocations. Client RSS of ~25 MB is negligible relative to GPU memory.

## 4. Limitations

1. **Small benchmark size.** The benchmark comprises only 5 cases (10 rows, 20 requests). This is insufficient for statistical generalization. Confidence intervals are not reported because the sample size precludes reliable estimation.

2. **Zero baseline F1.** The baseline answer F1 of 0.0000 is an unusual result that demands scrutiny. It may indicate that the baseline prompt configuration is poorly matched to the gold references, or that the gold references are narrowly scoped. The +43.33 pp gain should be interpreted relative to this degenerate baseline, not as evidence of robust quality improvement across diverse settings.

3. **Single model and hardware configuration.** All results are from Qwen2.5-3B-Instruct on one local machine with a CUDA/PyTorch stack. No cross-model, cross-hardware, or cross-environment replication has been performed.

4. **Prototype HTTP server.** The `openai_adapter_server.py` shim is a lightweight prototype, not a production-grade server. It lacks authentication, rate limiting, request validation beyond basic shape checks, and robust error handling. Concurrency is handled by Python's built-in HTTP server, which is not designed for high-throughput production workloads.

5. **No streaming support.** The current implementation returns complete responses rather than streaming tokens, which limits compatibility with clients that depend on server-sent events.

6. **Resource measurement limitations.** GPU utilization was sampled (not continuously monitored), and UMA memory figures may be affected by OS-level caching and buffer management. The slight increase in available memory after the benchmark is not fully explained.

7. **No comparison to alternative deployment patterns.** This work does not compare the HTTP-shim approach to other integration strategies (e.g., middleware, sidecar, or in-process adapter injection), so no claim can be made about relative efficiency.

8. **Automated provenance.** This draft and the underlying experiments were produced by an automated research pipeline. No independent human verification of the experimental procedure, data integrity, or metric computation has been performed.

## 5. Reproducibility Checklist

| Item | Status | Notes |
|---|---|---|
| Source code available | Partial | `src/openai_adapter_server.py`, `src/run_http_adapter_benchmark.py`, `src/serving_adapter.py` are present in the project directory; no public repository URL is recorded. |
| Benchmark data available | Partial | Result CSV and JSON files are present in `artifacts/`; the RAG test cases are constructed programmatically from the parent project's harness. |
| Model identifier specified | Yes | `Qwen/Qwen2.5-3B-Instruct`, loaded from local Hugging Face cache. |
| Hardware specified | Partial | CUDA/PyTorch stack confirmed; GPU model, CPU model, and RAM are not explicitly recorded in the artifacts. UMA memory figures imply substantial GPU memory. |
| Software dependencies specified | Partial | Python 3, PyTorch, Transformers, Hugging Face Hub; exact version numbers not recorded in artifacts. |
| Random seeds specified | No | No random seed is recorded; the extractive backend is deterministic, but the Transformers backend may exhibit variance across runs. |
| Statistical tests performed | No | Sample size (n=5 cases) is too small for meaningful statistical testing. |
| Negative results reported | Yes | Zero baseline F1 is reported honestly. |
| Server lifecycle documented | Yes | Server started from `/tmp`, verified, benchmarked, and stopped. No residual processes. |

## 6. Conclusion

This report presents evidence that a syntax-preserving RAG adapter can be deployed behind an OpenAI-compatible HTTP endpoint and that, in a small local benchmark with Qwen2.5-3B-Instruct, the adapter-mediated (distilled) condition improved answer F1 by 43.33 percentage points over a degenerate zero-F1 baseline, with p95 latency overhead of 4.73%. The endpoint conformed to the OpenAI `/v1/models` and `/v1/chat/completions` API shape.

These findings are bounded by significant limitations: the benchmark is small (5 cases), the baseline F1 of zero complicates interpretation of the quality gain, only one model and one hardware configuration were tested, and the HTTP server is a prototype not intended for production deployment. The current project artifacts support the finding in the tested setting, but external replication across models, datasets, and hardware is necessary before broader claims can be made.

The project decision recommends finalizing this deployment branch and directing future work toward optimizing true batched model-server scheduling rather than creating additional generic successors.

## Referenced Artifacts

### Source files
- `src/openai_adapter_server.py` — OpenAI-compatible HTTP shim
- `src/run_http_adapter_benchmark.py` — HTTP endpoint benchmark harness
- `src/serving_adapter.py` — RAGServingAdapter implementation
- `src/run_serving_adapter_benchmark.py` — Direct (non-HTTP) serving adapter benchmark
- `src/run_rag_integration_benchmark.py` — RAG integration benchmark
- `tests/run_tests.py` — Adapter/distiller regression tests

### Result files
- `artifacts/http_adapter_rag_syntax-rag-qwen-http_batch4.json`
- `artifacts/http_adapter_rag_syntax-rag-qwen-http_batch4.csv`
- `artifacts/http_adapter_rag_syntax-rag-http-smoke_batch4.json`
- `artifacts/http_adapter_rag_syntax-rag-http-smoke_batch4.csv`
- `artifacts/serving_adapter_smoke.json`
- `artifacts/rag_integration_Qwen__Qwen2.5-3B-Instruct_new56_batch4.json`
- `artifacts/rag_integration_Qwen__Qwen2.5-3B-Instruct_new48_batch4.json`
- `artifacts/rag_integration_Qwen__Qwen2.5-3B-Instruct_new64_batch8.json`
- `artifacts/rag_integration_Qwen__Qwen2.5-3B-Instruct_new64_batch4.json`
- `artifacts/rag_integration_local_gold_aware_extractive_new64_batch4.json`
- `artifacts/rag_integration_Qwen__Qwen2.5-3B-Instruct_new64.json`
- `artifacts/rag_integration_local_gold_aware_extractive_new64.json`
- `artifacts/rag_integration_Qwen__Qwen2.5-3B-Instruct.json`
- `artifacts/rag_integration_local_gold_aware_extractive.json`

### Decision and metadata files
- `.omx/project_decision.json` — Project decision (finalize_positive)
- `.omx/metrics.json` — Session metrics
- `run_notes.md` — Detailed run notes
- `papers/.../claim_ledger.json` — Claim audit ledger
- `papers/.../evidence_bundle.json` — Evidence bundle
