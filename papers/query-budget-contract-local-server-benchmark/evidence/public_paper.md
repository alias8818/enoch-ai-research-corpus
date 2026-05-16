```markdown
# Query Budget Contracts for Local LLM Serving: A Broker-Based Routing Benchmark

> **AI Provenance Notice.** This draft was generated automatically from research artifacts produced by the OMX automation pipeline. The operator releases it as an unreviewed AI-generated research artifact and claims no personal authorship credit for the writing or results. Readers should treat all claims, measurements, and interpretations herein as unreviewed and subject to independent verification.

---

## Abstract

We investigate whether a query-budget-contract (QBC) broker—interposed between clients and local OpenAI-compatible LLM servers—can reduce p95 latency and energy-per-correct-answer relative to fixed large-model routing, while preserving answer quality within one percentage point. We report results from two experimental tiers: (1) a deterministic FastAPI stand-in backend validating the broker and measurement harness, and (2) a real cached llama.cpp endpoint serving Qwen2.5-0.5B-Instruct and Qwen2.5-1.5B-Instruct (Q8 GGUF). In the llama.cpp calibration (240 requests, concurrency 8), the QBC broker reduced p95 latency by 40.2%, improved throughput by 77.7%, and reduced estimated joules per correct answer by 65.5% relative to fixed-large routing, while improving quality by +2.08 percentage points. However, the contract policy did not outperform fixed-small routing on any metric: the small model alone achieved higher quality (0.8125 vs. 0.7833), lower p95 latency (1.418 s vs. 2.328 s), and lower joules per correct answer (83.1 vs. 133.7). These results support the hypothesis that budget-contract routing can improve over naive large-model routing, but they also reveal that the specific contract policy tested is suboptimal whenever a sufficiently capable small model is available. The current project artifacts support this finding in the tested setting.

---

## 1. Introduction

Local LLM serving deployments face a tension between answer quality and serving cost. A common baseline routes all queries to the largest available model, maximizing quality at the expense of latency, throughput, and energy. An alternative is to route queries selectively: simple or low-stakes queries go to a smaller, faster model, while complex queries are escalated.

Query budget contracts formalize this idea. Each request carries metadata specifying a model preference, token budget, timeout, and priority. A broker interprets these contracts and forwards each request to an appropriate backend. The contract abstraction decouples the client's intent from the server's model selection, enabling per-request cost–quality tradeoffs without modifying client code.

This paper reports benchmark results for a QBC broker operating over local OpenAI-compatible endpoints. We evaluate against two fixed-routing baselines (always-small, always-large) on a 240-request calibration workload. The study was conducted within the OMX automated research pipeline; all claims are grounded in the recorded artifacts and are bounded to the specific models, hardware, and workload tested.

---

## 2. Method

### 2.1 Architecture

The system comprises four components:

1. **Backend servers.** Two OpenAI-compatible endpoints serving distinct models. In the deterministic tier, these are FastAPI stubs (`local_openai_backend.py`). In the llama.cpp tier, these are `llama-server` processes loading Qwen2.5-0.5B-Instruct-Q8 and Qwen2.5-1.5B-Instruct-Q8 from cached GGUF files.

2. **Dual OpenAI proxy** (`dual_openai_backend.py`). A FastAPI proxy that maps the abstract model names `local-small` and `local-large` to the two backend endpoints, presenting a single OpenAI-compatible API surface.

3. **Query Budget Contract broker** (`query_budget_broker.py`). An OpenAI-compatible broker that inspects per-request metadata, maps it to a query budget contract (model, max_tokens, timeout, priority, reason), and forwards the request to the dual proxy.

4. **Benchmark harness** (`local_server_benchmark.py`, `llama_cpp_benchmark.py`). Launches all services, verifies `/v1/models`, runs requests under each routing policy, scores answers, and records metrics.

### 2.2 Routing Policies

Three policies are compared:

- **Fixed-large:** All requests route to `local-large`.
- **Fixed-small:** All requests route to `local-small`.
- **Contract:** The QBC broker selects the model per request based on contract metadata. In the calibration runs, the contract routed 193 of 240 requests (80.4%) to `local-small` and 47 (19.6%) to `local-large`.

### 2.3 Quality Scoring

For the deterministic backend, exact-match scoring is used against known correct answers. For the llama.cpp backend, a semantic exact-answer scorer extracts numeric or string answers from terse model output and compares against reference answers. Quality is reported as the fraction of correct responses.

### 2.4 Energy Estimation

Estimated joules per correct answer is computed as:

$$J_{\text{correct}} = \frac{\text{CPU\_time\_s} \times P_{\text{est}}}{\text{num\_correct}}$$

where $P_{\text{est}}$ is an estimated average CPU power draw. This is a coarse proxy; actual GPU and system-level power are not instrumented.

### 2.5 Telemetry

The harness records p50/p95/p99 latency, tokens/sec, samples/sec, CPU load, process RSS/PSS, load average, and `/proc/meminfo` UMA snapshots before and after each run.

---

## 3. Results

### 3.1 Deterministic Local Server Harness (Toy Validation)

The deterministic backend validates the broker, scoring, and measurement infrastructure without introducing model-level variance. Results from the 240-request calibration (`results/local_calibration`):

| Policy       | Quality | p95 (s) | tokens/sec | samples/sec | J/correct |
|-------------|---------|---------|------------|-------------|-----------|
| Fixed-large | 1.000   | 0.420   | 5663.1     | 190.1       | 11.069    |
| Contract    | 1.000   | 0.056   | 13986.8    | 469.6       | 3.042     |

The contract policy improved p95 latency by 86.6%, throughput by 147.0%, and joules per correct answer by 72.5%, with zero quality loss. These numbers confirm that the broker and harness function correctly but do not reflect real model behavior.

### 3.2 Cached llama.cpp Endpoint (Hook-Prototype Validation)

Results from the 240-request calibration against real Qwen2.5 GGUF models (`results/llama_cpp_calibration`):

| Policy       | Model                    | Quality | p95 (s) | tokens/sec | samples/sec | J/correct |
|-------------|--------------------------|---------|---------|------------|-------------|-----------|
| Fixed-large | Qwen2.5-1.5B-Instruct Q8 | 0.7625  | 3.896   | 337.7      | 3.64        | 387.95    |
| Fixed-small | Qwen2.5-0.5B-Instruct Q8 | 0.8125  | 1.418   | 851.3      | 8.83        | 83.12     |
| Contract    | Mixed (80.4% small)      | 0.7833  | 2.328   | 600.0      | 6.33        | 133.73    |

**Contract vs. fixed-large:** p95 latency improved 40.2%, tokens/sec improved 77.7%, samples/sec improved 73.9%, joules per correct answer improved 65.5%, and quality improved by +2.08 percentage points.

**Contract vs. fixed-small:** The contract policy underperformed fixed-small routing on every measured dimension. Quality was lower (0.7833 vs. 0.8125, −2.92 pp), p95 latency was higher (2.328 s vs. 1.418 s, +64.3%), and joules per correct answer were higher (133.7 vs. 83.1, +61.0%).

### 3.3 UMA and Process Evidence

MemAvailable remained high throughout (121.8 GB before, 121.0 GB after), no swap was configured, and server RSS was approximately 2.98 GB. Recorded llama/proxy CPU time totaled 2390.3 s. No project-owned listener processes remained after cleanup.

### 3.4 Branch Kill Condition

The pre-registered kill condition required the broker to show at least 15% improvement in p95 latency or joules per correct answer over fixed-large routing while preserving quality within 1 percentage point. The contract met this condition (40.2% p95 improvement, 65.5% joules improvement, +2.08 pp quality). The branch was therefore not killed.

---

## 4. Limitations

1. **Small model selection.** Only two Qwen2.5 GGUF models (0.5B and 1.5B) were tested. The contract policy's effectiveness depends on the capability gap between available models, and results may differ substantially with other model pairs.

2. **Workload specificity.** The 240-request calibration workload is small and may not represent production query distributions. The workload's difficulty profile is unknown beyond the recorded quality scores.

3. **Energy estimation is coarse.** Joules per correct answer is estimated from CPU time and an assumed power draw. GPU power, memory bandwidth power, and system idle power are not instrumented. The relative comparisons between policies on the same hardware are more reliable than the absolute values.

4. **No production validation.** The llama.cpp results are hook-prototype results from a local server with cached weights, not from a production serving stack (e.g., vLLM, SGLang, TensorRT-LLM). Continuous batching, KV-cache management, and multi-GPU serving were not exercised.

5. **Contract policy is static.** The contract routed 80.4% of requests to the small model regardless of query content. A smarter contract that classifies query difficulty could improve results, but such a classifier was not implemented or tested.

6. **Fixed-small baseline outperforms the contract.** The most notable negative finding is that simply routing all requests to the smaller model yielded better quality, lower latency, and lower energy than the contract policy. This suggests the contract's routing heuristic was poorly matched to the workload, or that the small model was surprisingly capable on this particular benchmark. This result limits the practical significance of the contract-vs-large comparison.

7. **Single hardware configuration.** All runs were on a single machine with 121+ GB available memory. Results may not transfer to memory-constrained or GPU-limited environments.

8. **No external replication.** Results have not been independently replicated on different hardware, with different models, or by different researchers.

---

## 5. Reproducibility Checklist

| Item | Status | Detail |
|------|--------|--------|
| Code available | Present in artifacts | `src/query_budget_broker.py`, `src/local_server_benchmark.py`, `src/llama_cpp_benchmark.py`, `src/dual_openai_backend.py`, `src/local_openai_backend.py` |
| Model artifacts specified | Partial | Qwen2.5-0.5B-Instruct Q8 and Qwen2.5-1.5B-Instruct Q8 GGUF; cached via symlinks to sibling project artifacts, not independently versioned |
| Benchmark commands recorded | Yes | `python3 src/llama_cpp_benchmark.py --requests 240 --concurrency 8 --parallel-slots 8 --ctx-size 1024 --out results/llama_cpp_calibration` |
| Random seeds | Not recorded | Deterministic backend is fully reproducible; llama.cpp sampling may have used default seeds |
| Hardware recorded | Yes | `results/llama_cpp_calibration/host.json` |
| Raw responses preserved | Yes | `results/llama_cpp_calibration/responses.csv` |
| Server logs preserved | Yes | `results/llama_cpp_calibration/server_logs/` |
| Metrics JSON preserved | Yes | `results/llama_cpp_calibration/metrics.json` |
| Comparison JSON preserved | Yes | `results/llama_cpp_calibration/comparison.json` |
| Unit tests | Yes | 3 tests passed (`tests/test_local_server_benchmark.py`) |
| Cleanup verified | Yes | No project-owned listener processes remained after teardown |

---

## 6. Conclusion

A query-budget-contract broker interposed between clients and local OpenAI-compatible LLM servers reduced p95 latency by 40.2% and estimated joules per correct answer by 65.5% relative to fixed large-model routing on a 240-request llama.cpp calibration, while improving answer quality by 2.08 percentage points. These improvements met the pre-registered branch survival threshold.

However, the contract policy was outperformed by the simpler fixed-small routing baseline on all measured dimensions (quality, latency, energy). This negative finding is central to interpreting the results: the contract's value depends on the existence of queries that genuinely require the larger model, and on the contract's ability to identify those queries accurately. In the tested workload, the 0.5B model was sufficiently capable that routing 80.4% of requests to it—and occasionally escalating to the 1.5B model—produced worse outcomes than routing everything to the 0.5B model.

The current project artifacts support the finding that budget-contract routing can improve over naive large-model routing in the tested setting. Whether contract routing can improve over an informed fixed-small baseline remains an open question that would require a smarter contract policy and a more diverse workload to address.

---

## Referenced Artifacts

### Source files
- `src/query_budget_broker.py`
- `src/local_server_benchmark.py`
- `src/llama_cpp_benchmark.py`
- `src/dual_openai_backend.py`
- `src/local_openai_backend.py`
- `tests/test_local_server_benchmark.py`

### Decision and metadata
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `run_notes.md`

### Deterministic harness results
- `results/local_calibration/comparison.json`
- `results/local_calibration/responses.csv`
- `results/local_calibration/host.json`
- `results/local_calibration/metrics.json`

### llama.cpp smoke results
- `results/llama_cpp_smoke/comparison.json`
- `results/llama_cpp_smoke/responses.csv`
- `results/llama_cpp_smoke/host.json`
- `results/llama_cpp_smoke/metrics.json`
- `results/llama_cpp_smoke/server_logs/llama-small.log`
- `results/llama_cpp_smoke/server_logs/llama-large.log`
- `results/llama_cpp_smoke/server_logs/broker.log`
- `results/llama_cpp_smoke/server_logs/dual-backend.log`

### llama.cpp calibration results
- `results/llama_cpp_calibration/comparison.json`
- `results/llama_cpp_calibration/responses.csv`
- `results/llama_cpp_calibration/host.json`
- `results/llama_cpp_calibration/metrics.json`
- `results/llama_cpp_calibration/server_logs/llama-small.log`
- `results/llama_cpp_calibration/server_logs/llama-large.log`
- `results/llama_cpp_calibration/server_logs/broker.log`
- `results/llama_cpp_calibration/server_logs/dual-backend.log`

### Paper audit artifacts
- `papers/.../claim_ledger.json`
- `papers/.../evidence_bundle.json`
- `papers/.../paper_manifest.json`
```
