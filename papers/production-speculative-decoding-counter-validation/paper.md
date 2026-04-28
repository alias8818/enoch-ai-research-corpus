# Production Speculative Decoding Counter Validation: Reproducing Local Trace-Ranking Divergence with a Serving Engine's Speculative Counters

> **AI Provenance Notice.** This draft was generated automatically from research-run artifacts (run notes, evidence bundles, claim ledgers, and result files) by an AI pipeline. The operator releases these artifacts and claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact. It has not been peer-reviewed, and all claims are bounded to the specific hardware, models, and configurations documented below.

---

## Abstract

Speculative decoding accelerates autoregressive inference by proposing candidate tokens from a fast draft model and verifying them against a larger target model. Selecting the best speculative configuration typically relies on aggregate accuracy and latency metrics. Prior local experiments with a 270-row true-token prompt set found that aggregate accuracy/latency and per-request trace scoring can diverge in their preferred configuration: accuracy/latency favored one draft setting (`draft_k2`) while trace-level acceptance counters favored another (`draft_k1`). This study asks whether that divergence reproduces under a production serving engine with continuous batching, scheduler slots, and engine-level speculative counters. Using `llama.cpp` `llama-server` with Qwen2.5-1.5B-Instruct (target) and Qwen2.5-0.5B-Instruct (draft) in GGUF format, we ran the same 90-task, 270-row prompt set at concurrency 4 with 4 server slots. The production engine's speculative counters (`timings.draft_n`, `timings.draft_n_accepted`) reproduced the parent divergence: accuracy/latency ranked `draft_k2` first (mean acceptance 0.639, mean latency 338.7 ms, 380/585 accepted/proposed), while trace scoring ranked `draft_k1` first (mean acceptance 0.588, mean latency 349.4 ms, 261/421 accepted/proposed, trace score 0.284). Failure clusters were sparse (2 of 270 rows). These results are limited to a single model pair, a single serving engine, and a single hardware configuration; vLLM validation was blocked by a local extension ABI mismatch and remains future work.

---

## 1. Introduction

Speculative decoding reduces the latency of autoregressive language model inference by having a small draft model propose candidate continuations that a larger target model verifies in parallel. The number of draft tokens proposed per step, the draft model's quality, and the acceptance mechanism all affect the speedup achieved. In practice, the "best" speculative configuration depends on which metric is optimized: raw throughput, per-request latency, acceptance rate, or a composite trace-level score.

A prior experiment (the "parent" project) using local Hugging Face Transformers inference on a 270-row true-token prompt set observed that two draft configurations—`draft_k1` and `draft_k2`—were ranked differently depending on whether one used aggregate accuracy/latency or per-request trace scoring. This raises a practical question: does the same ranking divergence appear when speculative decoding is run inside a production serving engine with continuous batching, scheduler slots, and engine-exposed speculative counters?

If the divergence is an artifact of single-request local inference, it may not matter for deployment. If it reproduces under serving conditions, then deployment metric selection has real consequences for which speculative configuration is chosen. This paper reports a validation experiment designed to answer that question.

---

## 2. Method

### 2.1 Hypothesis

A production serving engine with scheduler slots and engine-level speculative counters will reproduce the parent project's ranking divergence: aggregate accuracy/latency will prefer `draft_k2`, while per-request accepted/draft counter telemetry (trace scoring) will prefer `draft_k1`.

### 2.2 Kill Condition

The branch would be terminated as unsupported if production-engine speculative counters failed to reproduce the parent decision signal—specifically, if server-level accepted/draft counters did not change the preferred speculative configuration relative to aggregate accuracy/latency, or if the production top trace diverged from the parent top trace without a scheduler/batching explanation.

### 2.3 Serving Engine

We used `llama.cpp` `llama-server` as the production serving engine. This server exposes speculative decoding counters in its per-response timing metadata: `timings.draft_n` (number of draft tokens proposed) and `timings.draft_n_accepted` (number accepted by the target model). Continuous batching was enabled, and the server was configured with 4 parallel slots.

An attempt to use `vLLM` as an alternative serving engine failed due to a compiled-extension ABI mismatch (`ImportError: vllm/_C.abi3.so: undefined symbol`), indicating a PyTorch/vLLM version incompatibility in the local checkout. This is recorded as attempted evidence, not a blocker for the llama.cpp result.

### 2.4 Models

Cached Hugging Face models were converted to GGUF format for llama.cpp serving:

- **Draft model:** Qwen2.5-0.5B-Instruct, Q8_0 quantization, 507M parameters (`models/qwen2.5-0.5b-instruct-q8_0.gguf`)
- **Target model:** Qwen2.5-1.5B-Instruct, Q8_0 quantization, 1.6G parameters (`models/qwen2.5-1.5b-instruct-q8_0.gguf`)

The initial GGUF conversion failed due to a missing `sentencepiece` dependency; after installing `sentencepiece==0.2.1`, conversion succeeded.

### 2.5 Task Set

The experiment reused the parent project's 90-task, 270-row true-token prompt set. Each task produces 3 rows (one per speculative configuration variant), yielding 270 total evaluation rows.

### 2.6 Experimental Protocol

1. **Smoke test.** A 3-task, 9-row calibration run at 2 slots and concurrency 2 confirmed that `timings.draft_n` and `timings.draft_n_accepted` were correctly collected and that the smoke-test ranking matched the parent direction (accuracy top: `draft_k2`; trace top: `draft_k1`).

2. **Scaled run.** The full 90-task, 270-row benchmark was executed with:
   - Request concurrency: 4
   - Parallel server slots: 4
   - Base port: 18280
   - Command: `python3 src/llama_server_counter_validation.py --n 90 --out artifacts/llama_server_scaled --request-concurrency 4 --parallel-slots 4 --base-port 18280`

3. **Telemetry collection.** In addition to speculative counters, the run collected per-request latency, throughput, GPU utilization, CPU load, UMA memory availability, swap status, server process memory (PSS/RSS), and sampled power consumption.

---

## 3. Results

### 3.1 Configuration Rankings

The production-server ranking reproduced the parent 270-row decision signal:

| Metric | Top Configuration | Accuracy | Mean Acceptance | Mean Latency (ms) | Mean Rejected Tokens | Accepted/Proposed | Trace Score |
|---|---|---|---|---|---|---|---|
| Accuracy/Latency | `draft_k2` | 0.42222 | 0.63897 | 338.663 | 2.27778 | 380/585 | — |
| Trace Scoring | `draft_k1` | 0.42222 | 0.58836 | 349.422 | 1.77778 | 261/421 | 0.28420 |

Both configurations achieve the same accuracy (0.42222), but they differ in their acceptance profiles and latency. `draft_k2` proposes more tokens per step (higher proposed count, higher acceptance count, higher rejection count) and achieves lower mean latency. `draft_k1` proposes fewer tokens, has a lower acceptance rate, slightly higher latency, but ranks higher under trace scoring.

The parent comparison confirms: production top accuracy matches parent `draft_k2`; production top trace matches parent `draft_k1`. The divergence between accuracy/latency ranking and trace ranking is preserved under production serving conditions.

### 3.2 Throughput and Utilization

| Metric | Value |
|---|---|
| Benchmark wall time | 29.255 s |
| Total rows | 270 |
| Total generated tokens | 2460 |
| Throughput | 84.088 tokens/sec |
| Row rate | 9.229 rows/sec |
| p50 request latency | 349.897 ms |
| p95 request latency | 561.558 ms |
| GPU utilization (snapshot) | 83% |
| CPU load average | 1.258 |
| UMA MemAvailable | 121,276,460 KB |
| SwapFree | 0 KB |
| Server process PSS/RSS | ~1.19–1.21 GB |
| Mean sampled power | 32.7–34.6 W |

### 3.3 Failure Clusters

Failure clusters were sparse in this server run:

- `code_context_draft_mismatch`: 1 occurrence
- `low_accept_high_rollback`: 1 occurrence

This indicates that the production engine's batching/counter signal operates primarily at the ranking level rather than the cluster-volume level under this prompt/model setup. The divergence in preferred configuration is not driven by a large subset of pathological requests.

### 3.4 Smoke Test Confirmation

The 3-task, 9-row smoke test at 2 slots / concurrency 2 produced the same ranking direction (accuracy top: `draft_k2`; trace top: `draft_k1`), consistent with both the parent result and the scaled run.

### 3.5 vLLM Attempt

The local vLLM checkout at `/home/jeremy/projects/vllm` failed to serve due to an ABI mismatch between the compiled vLLM extension (`vllm/_C.abi3.so`) and the installed PyTorch version. This negative result is recorded: vLLM-based validation was not achieved in this run.

---

## 4. Limitations

1. **Single model pair.** Only Qwen2.5-0.5B-Instruct (draft) and Qwen2.5-1.5B-Instruct (target) were tested. The ranking divergence may not hold for other model pairs, quantization levels, or size ratios.

2. **Single serving engine.** Only `llama.cpp` `llama-server` was validated. The vLLM comparison was blocked by a local ABI mismatch and remains untested. Different serving engines may expose different counter semantics or batching behavior.

3. **Single hardware configuration.** Results were collected on a single machine with UMA memory architecture. GPU utilization was 83% and CPU load was low (1.258), suggesting the system was not heavily contended, but results may differ under different load profiles or hardware.

4. **Limited task diversity.** The 90-task, 270-row prompt set is a specific benchmark. Generalization to other prompt distributions, longer sequences, or different domains is not established.

5. **Equal accuracy across configurations.** Both `draft_k1` and `draft_k2` achieved identical accuracy (0.42222). The ranking divergence is driven by acceptance rates, latency, and trace scoring—not by accuracy differences. If accuracy had differed substantially, the ranking might have converged.

6. **No external replication.** All results come from a single automated run. No independent replication has been performed.

7. **Quantization effects.** Both models used Q8_0 quantization. The effect of different quantization levels on the ranking divergence is unknown.

8. **Power measurement granularity.** Mean sampled power (32.7–34.6 W) was collected at coarse granularity and may not capture transient power effects of speculative verification steps.

---

## 5. Reproducibility Checklist

| Item | Status | Detail |
|---|---|---|
| Code available | Present in project | `src/llama_server_counter_validation.py`, `src/sd_energy_trace_experiment.py`, `src/real_inference_energy_smoke.py`; all pass `py_compile` |
| Model files specified | Yes | `models/qwen2.5-0.5b-instruct-q8_0.gguf` (507M), `models/qwen2.5-1.5b-instruct-q8_0.gguf` (1.6G) |
| Serving engine version specified | Partial | `llama.cpp` `llama-server` (local checkout); exact commit hash not recorded in artifacts |
| Hardware described | Partial | UMA memory architecture, GPU utilization 83%, CPU loadavg 1.258; specific GPU/CPU model not in artifacts |
| Random seeds | Not recorded | Deterministic task/prompt set reused from parent; server-side sampling seeds not captured |
| Hyperparameters documented | Yes | Concurrency 4, slots 4, base port 18280, Q8_0 quantization |
| Output artifacts stored | Yes | CSV trace rows, summary JSON, reports JSON, run output JSON for both smoke and scaled runs |
| Statistical uncertainty | Not computed | Single run; no confidence intervals or significance tests reported |
| Negative results reported | Yes | vLLM ABI mismatch failure documented; sparse failure clusters reported |

---

## 6. Conclusion

This experiment provides evidence that the ranking divergence between accuracy/latency metrics and trace-scoring metrics in speculative decoding configuration selection reproduces under a production serving engine. Using `llama.cpp` `llama-server` with continuous batching and engine-level speculative counters on a 270-row prompt set, aggregate accuracy/latency preferred `draft_k2` while trace scoring preferred `draft_k1`—matching the prior local-inference result.

The practical implication is that the choice of optimization metric matters for speculative decoding configuration even in deployed serving settings. An operator optimizing for mean latency would select a different configuration than one optimizing for per-request acceptance trace quality, and these two objectives can diverge even when accuracy is held constant.

These findings are bounded to the specific model pair, serving engine, hardware, and prompt set tested. External replication across additional serving engines (particularly vLLM, once the local ABI issue is resolved), model pairs, and prompt distributions would strengthen the generality of this result. The sparse failure clusters suggest the divergence is a systematic ranking-level effect rather than an artifact of outlier requests, but the mechanism underlying the divergence—whether it stems from draft-token distribution shifts under batching, verification-path differences, or metric sensitivity—remains an open question.

---

## Referenced Artifacts

### Result files
- `artifacts/llama_server_scaled/llama_server_trace_rows.csv`
- `artifacts/llama_server_scaled/llama_server_summary.json`
- `artifacts/llama_server_scaled/llama_server_reports.json`
- `artifacts/llama_server_scaled/llama_server_run_output.json`
- `artifacts/llama_server_smoke/llama_server_trace_rows.csv`
- `artifacts/llama_server_smoke/llama_server_summary.json`
- `artifacts/llama_server_smoke/llama_server_reports.json`
- `artifacts/llama_server_smoke/llama_server_run_output.json`

### Source and configuration files
- `src/llama_server_counter_validation.py`
- `src/sd_energy_trace_experiment.py`
- `src/real_inference_energy_smoke.py`
- `models/qwen2.5-0.5b-instruct-q8_0.gguf`
- `models/qwen2.5-1.5b-instruct-q8_0.gguf`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `run_notes.md`
- `README.md`
- `prompts/initial.md`
- `prompts/resume.md`

### Paper-specific artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
