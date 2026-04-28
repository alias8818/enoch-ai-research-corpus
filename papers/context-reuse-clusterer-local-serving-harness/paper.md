# Context Reuse Clusterer for Local LLM Serving: A Harness and Validation Study

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We present a local serving harness and experimental evaluation of context-aware request clustering for OpenAI-compatible LLM inference endpoints. The harness replays synthetic enterprise FAQ traces under two scheduling policies—fixed arrival-order microbatching and topic/prefix-based context clustering—against a vLLM endpoint with prefix caching enabled. In experiments on a single GB10 node using Qwen2.5-0.5B-Instruct across three workload scenarios (60 requests each, concurrency 4), context clustering reduced p95 latency by 9.05–15.74% and prefill KV computed tokens by 96.69–97.95%, with no answer-quality degradation. Energy-per-correct-response reductions ranged from 4.47% to 24.65%, with the enterprise FAQ scenario falling below the 5% threshold. These results are limited to a single small model, one hardware configuration, and synthetic traces; broader validation is needed before generalizing.

---

## 1. Introduction

Autoregressive language model serving incurs significant computational cost during the prefill phase, when the key-value (KV) cache for the input prompt is constructed. When multiple requests share common prefix tokens—as is typical in enterprise FAQ, retrieval-augmented generation, and template-driven workloads—serving frameworks such as vLLM can reuse cached KV blocks across requests if those requests arrive in proximity. However, default request scheduling typically processes requests in arrival order, which may interleave requests with unrelated prefixes and reduce cache reuse.

The core hypothesis under evaluation is that reordering requests by topic or shared prefix before dispatch (context clustering) can measurably improve prefix-cache hit rates, reduce redundant prefill computation, and consequently lower both latency and energy per correct response—without degrading answer quality—when compared against arrival-order scheduling under the same serving infrastructure.

This paper documents the construction of a dependency-light replay harness, its validation against both a deterministic local shim and a live vLLM endpoint, and the observed results. The project decision recorded in the automation pipeline is `finalize_positive` with confidence `medium`, reflecting supportive but narrow evidence.

---

## 2. Method

### 2.1 Harness Design

The harness (`src/local_serving_harness.py`) is implemented in Python using only the standard library, targeting any OpenAI-compatible inference endpoint. Its components include:

- **Synthetic trace generation**: Enterprise FAQ traces with embedded answer keys, supporting configurable scenario profiles (`enterprise_faq_local`, `high_prefix_sharing`, `mixed_workload`).
- **Two scheduling policies**:
  - *Fixed microbatch* (`fixed_microbatch`): Processes requests in arrival order, serving as the baseline.
  - *Context clusterer* (`context_clusterer`): Groups requests by topic or shared prefix before dispatch, aiming to maximize prefix overlap within each batch.
- **Endpoint interaction**: Probes `/v1/models` and `/v1/chat/completions` endpoints; records per-request latency, token counts, and answer correctness against embedded answer keys.
- **Telemetry collection**: Optional scraping of Prometheus `/metrics` for prefix-cache hit tokens and prefill KV computed tokens; optional `nvidia-smi` polling for GPU power and memory readings (with handling for partial `nvidia-smi` output where memory fields report `[N/A]`).
- **Deterministic local shim**: A built-in OpenAI-compatible server for smoke testing without external model weights, preserving the endpoint contract.

### 2.2 Experimental Protocol

The branch kill condition required that a real OpenAI-compatible local serving replay demonstrate at least one of: (a) ≥5% p95 latency reduction, (b) ≥5% energy-per-correct reduction, or (c) improved cache/offload behavior without >1% answer-quality loss, comparing context clustering against fixed arrival-order replay under the same endpoint and model.

Each scenario was run with both policies, with per-policy cache state reset between runs to ensure fair comparison. Answer correctness was measured by exact answer-key match.

---

## 3. Results

### 3.1 Shim Smoke Validation

The deterministic shim was exercised with 160 requests at concurrency 8 and a shim cache capacity of 12. Both policies achieved 100% exact answer-key success. The p95 latency delta under the shim was −0.50%, which is expected: the shim validates the endpoint contract and scheduling logic but does not implement real KV-cache behavior, so it cannot reflect prefix-cache reuse effects. This result confirms harness correctness, not serving efficiency.

A second smoke run (40 requests, concurrency 4) after a telemetry parsing fix produced consistent results, confirming no regression from the fix.

### 3.2 Real vLLM Endpoint Validation

A temporary vLLM service was launched with `Qwen/Qwen2.5-0.5B-Instruct`, `--enable-prefix-caching`, and `/metrics` enabled. The harness was run with 60 requests per scenario at concurrency 4 and a maximum of 24 output tokens.

Both policies achieved 100% exact answer-id success across all three scenarios. The comparative results are:

| Scenario | p95 Latency Δ | Joules/Correct Δ | Prefix-Cache Hit Tokens Δ | Prefill KV Computed Tokens Δ |
|---|---|---|---|---|
| `enterprise_faq_local` | −9.05% | −4.47% | +226% | −97.19% |
| `high_prefix_sharing` | −9.43% | −7.55% | +132% | −96.69% |
| `mixed_workload` | −15.74% | −24.65% | +349% | −97.95% |

All values represent the change from fixed arrival-order to context clustering (negative = improvement for latency, energy, and prefill KV; positive = improvement for cache hits).

**Latency**: All three scenarios exceeded the 5% p95 latency reduction threshold, with reductions of 9.05%, 9.43%, and 15.74%.

**Energy**: Two of three scenarios exceeded the 5% joules-per-correct reduction threshold (7.55% and 24.65%). The `enterprise_faq_local` scenario achieved only 4.47%, falling short of the 5% energy criterion.

**Cache behavior**: Prefix-cache hit tokens increased by 132–349%, and prefill KV computed tokens decreased by 96.69–97.95% across all scenarios, indicating substantial reduction in redundant prefill computation.

**Answer quality**: No degradation was observed; both policies achieved 100% exact answer-id success in all scenarios.

### 3.3 Kill Condition Assessment

The branch kill condition was not met: the real vLLM run demonstrated >5% p95 latency reduction in all scenarios, >5% energy-per-correct reduction in two of three scenarios, materially improved cache/KV behavior, and no answer-quality loss.

---

## 4. Limitations

1. **Single small model**: All real-endpoint results use Qwen2.5-0.5B-Instruct (0.5B parameters). Behavior at larger model sizes, where prefill cost dominates more significantly, may differ in magnitude or direction.

2. **Single hardware configuration**: Experiments were conducted on one GB10 node. GPU architecture, memory hierarchy, and power characteristics may affect generalizability.

3. **Small request counts**: Each scenario used only 60 requests. Statistical variability at this sample size is non-trivial; the observed percentages should be interpreted as point estimates rather than precise population parameters.

4. **Synthetic traces**: The enterprise FAQ, high-prefix-sharing, and mixed-workload traces are synthetically generated. Real production traffic distributions, including request arrival patterns, prefix overlap structure, and payload sizes, may yield different results.

5. **Incomplete energy criterion**: The `enterprise_faq_local` scenario did not meet the ≥5% joules-per-correct reduction threshold (4.47%). This mixed result means the energy benefit is not uniform across workload types.

6. **No multi-tenant or concurrent-workload interference testing**: The harness ran scenarios in isolation. Under concurrent mixed workloads with competing tenants, scheduling interactions may alter the observed benefits.

7. **No comparison with other scheduling strategies**: Only arrival-order baseline was tested. Other scheduling approaches (e.g., longest-prefix-first, priority-based) were not evaluated.

8. **Short output lengths**: Maximum output tokens were capped at 24. Workloads with longer generation lengths may exhibit different latency and energy profiles.

9. **Temporary vLLM instance**: The vLLM service was launched temporarily for the experiment and stopped before yielding; no warm-start or long-running stability data are available.

---

## 5. Reproducibility Checklist

- **Code availability**: `src/local_serving_harness.py` is present in the project directory and uses only the Python standard library.
- **Serving framework**: vLLM with `--enable-prefix-caching` and `/metrics` endpoint enabled.
- **Model**: `Qwen/Qwen2.5-0.5B-Instruct` (publicly available).
- **Hardware**: GB10 node with NVIDIA GPU (specific model recorded in `nvidia-smi` telemetry; memory fields partially reported as `[N/A]`).
- **Command for real-endpoint run**: `python3 src/local_serving_harness.py run --base-url http://127.0.0.1:38082/v1 --metrics-url http://127.0.0.1:38082/metrics --model local-model --requests 60 --concurrency 4 --max-tokens 24 --timeout 120 --scenarios enterprise_faq_local,high_prefix_sharing,mixed_workload --outdir results/local_serving_vllm_qwen05b_energy`
- **Command for shim smoke**: `python3 src/local_serving_harness.py smoke --requests 160 --concurrency 8 --shim-cache-capacity 12 --scenarios enterprise_faq_local --outdir results/local_serving_smoke`
- **Result artifacts**: JSON and CSV summaries, per-request logs, and server log paths are recorded (see Referenced Artifacts).
- **Randomness control**: The harness uses deterministic synthetic trace generation; shim responses are deterministic. Real model outputs introduce sampling variability, but answer-key matching is exact.
- **Cache reset**: Per-policy cache state was reset between runs to ensure fair comparison.

---

## 6. Conclusion

Context-aware request clustering, as implemented in the local serving harness, demonstrated measurable improvements in p95 latency (9.05–15.74%), prefix-cache hit rates (132–349% increase), and prefill KV computation (96.69–97.95% reduction) across three synthetic workload scenarios when evaluated against a vLLM Qwen2.5-0.5B-Instruct endpoint with prefix caching enabled. Energy-per-correct-response improvements were observed in all scenarios but fell below the 5% threshold in one case (4.47%). No answer-quality degradation was detected.

These findings are bounded by the experimental scope: a single small model, one hardware configuration, synthetic traces, and small request counts. The results support the hypothesis that context clustering can improve serving efficiency in prefix-cache-enabled deployments, but the magnitude and consistency of the benefit under broader conditions remain to be established. The harness and artifacts are available for replication and extension to larger models, production traces, and additional hardware configurations.

---

## Referenced Artifacts

### Source files
- `src/local_serving_harness.py` — replay harness implementation
- `README.md` — smoke and real-endpoint usage instructions
- `run_notes.md` — execution plan, notes, and final recommendation
- `.omx/project_decision.json` — project decision state (finalize_positive)
- `.omx/project.json` — project metadata
- `.omx/metrics.json` — session metrics

### Result files (real vLLM endpoint)
- `results/local_serving_vllm_qwen05b_energy/summary.json`
- `results/local_serving_vllm_qwen05b_energy/summary.csv`
- `results/local_serving_vllm_qwen05b_energy/requests.csv`
- `results/local_serving_vllm_qwen05b_energy/digest.json`
- `results/local_serving_vllm_qwen05b_energy/server_log_path.txt`

### Result files (shim smoke validation)
- `results/local_serving_smoke/summary.json`
- `results/local_serving_smoke/summary.csv`
- `results/local_serving_smoke/requests.csv`
- `results/local_serving_smoke_after_energy_fix/summary.json`
- `results/local_serving_smoke_after_energy_fix/summary.csv`
- `results/local_serving_smoke_after_energy_fix/requests.csv`

### Result files (earlier vLLM run)
- `results/local_serving_vllm_qwen05b/summary.json`
- `results/local_serving_vllm_qwen05b/summary.csv`
- `results/local_serving_vllm_qwen05b/requests.csv`
- `results/local_serving_vllm_qwen05b/server_log_path.txt`

### Paper and audit artifacts
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
