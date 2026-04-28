# vLLM Per-Request Attention-Sink Retention Under Continuous Serving: A 3B-Model Stress Campaign

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, benchmark results, and decision JSON). The operator claims no personal authorship credit for the writing or the results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We report results from a continuous-serving stress campaign evaluating a per-request attention-sink retention patch for vLLM 0.19.1, using Qwen2.5-3B-Instruct under an OpenAI-compatible serving interface. The patch allows callers to control attention-sink block retention on a per-request basis via flat `vllm_xargs` parameters. Across four paired baseline/retention configurations—varying concurrency (c8, c16), request count (n96–n256), and output length (64–128 tokens)—we observe zero request errors in all conditions and no paired p95 latency regression exceeding the pre-specified 10% kill gate. Three of four pairs show p95 latency improvements of 8–11% with retention enabled; one pair (n96/c8/out64 trial 2) shows a negligible +0.30% p95 delta. Output preview comparisons reveal non-zero text divergence (2–17 differing previews per trial), increasing with output length, which prevents a claim of semantic equivalence. Evidence strength is strong for the latency kill gate and moderate for output quality. These results support the viability of per-request attention-sink retention under the tested 3B serving envelope but do not establish generalizability to larger models, different hardware, or production workloads.

## 1. Introduction

Attention-sink tokens—early-sequence positions that accumulate disproportionate attention weights—have been identified as a stability concern in autoregressive transformer inference. In serving frameworks that evict key-value cache blocks under memory pressure, naive eviction of sink-adjacent blocks can degrade output quality or cause generation instability. Per-request attention-sink retention offers a mechanism to preserve designated sink blocks on a per-request basis, allowing callers to trade cache capacity for stability without imposing a global policy.

This technical report documents a stress campaign evaluating an installed per-request attention-sink retention patch for vLLM 0.19.1. The campaign was designed around a pre-specified kill gate: the patch would be rejected if it produced request errors or a p95 latency regression exceeding 10% relative to an unpatched baseline, measured under paired OpenAI-compatible continuous-serving conditions with Qwen2.5-3B-Instruct.

The contributions of this campaign are:

1. A calibrated latency characterization of per-request attention-sink retention across four serving configurations with paired baseline/retention trials.
2. Documentation of an API constraint in vLLM 0.19.1's OpenAI protocol that requires flat scalar `vllm_xargs` rather than nested policy objects.
3. An honest accounting of non-zero output divergence between baseline and retention conditions, which tempers any claim of output equivalence.

## 2. Method

### 2.1 Patch and Control Surface

The evaluated patch (`vllm_installed_0.19.1_attention_sink_per_request_portable.patch`) modifies vLLM 0.19.1 to support per-request attention-sink retention parameters. When enabled, the patch prevents eviction of designated sink blocks from the key-value cache for the duration of the requesting request.

Retention is controlled per request through the OpenAI-compatible API via `vllm_xargs` mapped to `SamplingParams.extra_args`. An important API constraint was discovered during testing: vLLM 0.19.1's validation for `extra_args` accepts only scalar or list values, not nested dictionaries. The serving harness therefore sends flat aliases:

- `attention_sink_retention_enabled` (boolean)
- `attention_sink_retention_block_budget` (integer)
- `attention_sink_retention_sink_blocks` (integer)

An initial attempt using nested `vllm_xargs` failed with HTTP 400 validation errors on all 16 requests in a preliminary smoke test. This failure mode is not reflected in the durable result artifacts but was observed in terminal output and corrected by switching to flat aliases.

### 2.2 Server Configuration

All calibrated sweep experiments used the following server configuration:

| Parameter | Value |
|---|---|
| vLLM version | 0.19.1 (patched install) |
| Model | `Qwen/Qwen2.5-3B-Instruct` (cached) |
| Served name | `qwen25-3b-sink-test` |
| dtype | float16 |
| Attention backend | FlashAttention |
| `max_model_len` | 1024 |
| `max_num_batched_tokens` | 4096 |
| `max_num_seqs` | 16 |
| `gpu_memory_utilization` | 0.50 |

Retention policy (when enabled): `attention_sink_retention_enabled=true`, `block_budget=8`, `sink_blocks=2`.

The server was launched from a neutral temporary directory (`/tmp/enoch_vllm_services`) and stopped between experimental phases.

### 2.3 Stress Harness

The stress harness (`scripts/run_vllm_openai_latency_stress.py`) is a stdlib-based OpenAI-compatible client that sends `/chat/completions` requests and records:

- Request latency (p50, p95, p99)
- Requests per second
- Completion tokens per second
- Error count and error rate
- Server process RSS (via `/proc`)
- System load
- UMA-aware `/proc/meminfo` samples (MemAvailable)
- GPU mean and peak utilization (via `nvidia-smi`, added for the calibrated sweep)

### 2.4 Experimental Design

The campaign proceeded in three phases:

**Phase 1: Offline smoke test.** Four prompts with `max_model_len=768`, `max_num_seqs=4`, comparing baseline and retention. Output texts were compared byte-wise.

**Phase 2: OpenAI latency smoke.** Sixteen requests at concurrency 4 with `max_model_len=768`, max output 16 tokens. Baseline and retention paired.

**Phase 3: Calibrated continuous-serving sweep.** Four paired baseline/retention configurations:

| Configuration | Requests (n) | Concurrency (c) | Max output tokens | Trials |
|---|---|---|---|---|
| c8/out64 | 96 | 8 | 64 | 2 |
| c16/out64 | 128 | 16 | 64 | 1 |
| c16/out128 | 256 | 16 | 128 | 1 |

The kill gate was defined a priori: the patch would be rejected if any paired retention condition produced request errors or a p95 latency regression exceeding 10% versus its paired baseline.

## 3. Results

### 3.1 Offline Smoke Test (n=4, 768×8)

| Condition | req/s | output tok/s | Answer containment |
|---|---|---|---|
| Baseline | 5.65 | 45.17 | 0.25 |
| Retention | 6.12 | 48.97 | 0.25 |

Output texts were byte-identical across all four prompts. The engine log recorded 44 pruned blocks under retention, confirming that the retention mechanism was actively engaged.

### 3.2 OpenAI Latency Smoke (n=16, c=4, 768×16)

| Condition | OK | Errors | req/s | comp tok/s | p50 (s) | p95 (s) | Peak RSS (GB) |
|---|---|---|---|---|---|---|---|
| Baseline | 16/16 | 0 | 6.38 | 102.04 | 0.600 | 0.715 | ~1.109 |
| Retention | 16/16 | 0 | 7.43 | 118.93 | 0.541 | 0.549 | ~1.109 |

MemAvailable remained stable (~61.36 GB → ~61.12 GB baseline; ~61.16 GB retention).

### 3.3 Calibrated Continuous-Serving Sweep

**Latency and throughput:**

| Configuration | Condition | p95 (s) | p95 Δ | req/s Δ | Errors |
|---|---|---|---|---|---|
| n96/c8/out64, trial 1 | Baseline | 2.193 | — | — | 0 |
| n96/c8/out64, trial 1 | Retention | 1.942 | −11.43% | +5.74% | 0 |
| n96/c8/out64, trial 2 | Baseline | 1.945 | — | — | 0 |
| n96/c8/out64, trial 2 | Retention | 1.951 | +0.30% | −0.11% | 0 |
| n128/c16/out64 | Baseline | 2.217 | — | — | 0 |
| n128/c16/out64 | Retention | 2.036 | −8.18% | +2.14% | 0 |
| n256/c16/out128 | Baseline | 4.360 | — | — | 0 |
| n256/c16/out128 | Retention | 4.007 | −8.09% | +5.31% | 0 |

Completion tok/s for the n256/c16/out128 pair: retention showed +5.22% improvement over baseline.

**Resource utilization:**

- GPU utilization: 90–96% mean, 96% peak across all calibrated sweep artifacts.
- Engine RSS: 2.34–2.42 GB (stable across conditions).
- MemAvailable: approximately 54.6–55.6 GB after warmup; no swap configured.

**Output divergence:**

| Configuration | Differing output previews |
|---|---|
| n96/c8/out64, trial 1 | 2 / 96 |
| n96/c8/out64, trial 2 | 3 / 96 |
| n128/c16/out64 | 7 / 128 |
| n256/c16/out128 | 17 / 256 |

Output preview differences were low but non-zero and increased with output length. This pattern is consistent with retention altering the effective context visible to the model during generation, producing divergent completions that are not necessarily degraded but are not identical to baseline outputs.

### 3.4 Kill-Gate Evaluation

The pre-specified kill gate required rejection if any paired condition showed request errors or a p95 latency regression exceeding 10%. No pair triggered the kill gate. The worst p95 delta was +0.30% (n96/c8/out64 trial 2); the remaining three pairs showed p95 improvements of 8–11%.

## 4. Limitations

1. **Single model.** All results are specific to Qwen2.5-3B-Instruct at float16. Generalization to larger models (7B, 13B, 70B), different architectures, or quantized formats is not established.

2. **Single hardware environment.** Experiments ran on one machine with sufficient GPU memory (MemAvailable ~55 GB after warmup). Behavior under memory pressure, on different GPU architectures, or in multi-GPU configurations is unknown.

3. **Output quality is not semantically validated.** Output preview comparisons reveal non-zero text divergence that increases with output length (2/96 to 17/256). Only surface-level string comparison was performed; no semantic grading, human evaluation, or reference-based quality metric was applied. The divergence may reflect benign sampling variability or meaningful quality shifts—this campaign cannot distinguish the two.

4. **Limited trial count.** Only the c8/out64 configuration was repeated (2 trials); the c16 configurations have single trials. The trial 2 result for c8/out64 (+0.30% p95 delta) demonstrates that inter-trial variability can erase the apparent latency benefit seen in trial 1 (−11.43%). The true effect size is uncertain.

5. **Short-duration serving.** The longest configuration (n256) represents minutes of sustained load, not hours or days. Memory leak accumulation, cache fragmentation, or degradation under extended uptime was not tested.

6. **API constraint.** The requirement for flat `vllm_xargs` aliases (rather than nested policy objects) is a vLLM 0.19.1-specific limitation. Future vLLM versions may alter the `extra_args` validation, breaking or simplifying this control surface.

7. **No comparison to alternative retention strategies.** This campaign evaluates one specific patch with fixed retention parameters (`block_budget=8`, `sink_blocks=2`). The sensitivity of results to these parameter choices was not explored.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Patch file archived and dry-run verified | Yes (`vllm_installed_0.19.1_attention_sink_per_request_portable.patch`, `patch --dry-run -p1` succeeded) |
| Backup/source provenance preserved | Yes (`results/vllm_site_patch_backup_per_request_20260419T155717/`) |
| vLLM version pinned | Yes (0.19.1, verified via `.venv-vllm/bin/python`) |
| Model identifier specified | Yes (`Qwen/Qwen2.5-3B-Instruct`, cached) |
| Server configuration fully specified | Yes (see Section 2.2) |
| Stress harness source archived | Yes (`scripts/run_vllm_openai_latency_stress.py`, `package_review/run_vllm_openai_latency_stress.py`) |
| Result JSON artifacts preserved | Yes (20 result files; see Referenced Artifacts) |
| Server logs preserved | Yes (4 server log files) |
| Kill gate defined before experimentation | Yes (errors or >10% p95 regression) |
| Paired baseline/retention trials | Yes (all configurations) |
| Random seed or sampling parameters specified | Not recorded in artifacts |

## 6. Conclusion

A per-request attention-sink retention patch for vLLM 0.19.1 was evaluated under a calibrated Qwen2.5-3B-Instruct continuous-serving stress campaign. Across four paired configurations spanning concurrency 8–16 and output lengths 64–128 tokens, zero request errors occurred and no paired p95 latency regression exceeded the 10% kill gate. Three of four pairs showed p95 improvements of 8–11%; one repeated trial showed a negligible +0.30% regression, indicating inter-trial variability. Non-zero output divergence (2–17 differing previews per trial) was observed and increased with output length, precluding a claim of semantic equivalence between baseline and retention outputs.

The evidence supports the viability of per-request attention-sink retention under the tested 3B serving envelope with respect to the latency kill gate. Evidence for output quality preservation is moderate, as only surface-level preview comparisons—not semantic grading—were performed. The project decision is `finalize_positive` with `medium` confidence and `strong` evidence strength for the latency dimension. Recommended follow-up is a dedicated semantic-quality soak if full-output equivalence is required, or patch review for integration consideration.

---

## Referenced Artifacts

### Run Notes and Decision
- `run_notes.md` — chronological execution and observation log
- `.omx/project_decision.json` — finalize_positive decision with rationale
- `.omx/metrics.json` — session metrics

### Patch and Review Bundle
- `results/vllm_0.19.1_attention_sink_retention_review_bundle.tgz` — packaged review bundle
- `results/vllm_installed_0.19.1_attention_sink_per_request_portable.patch` — portable patch
- `package_review/vllm_installed_0.19.1_attention_sink_per_request.patch` — original installed patch
- `package_review/vllm_installed_0.19.1_attention_sink_per_request_portable.patch` — portable patch (review copy)
- `package_review/vllm_installed_per_request_benchmark_summary.md` — parent benchmark summary
- `package_review/README.md` — review bundle README
- `results/vllm_site_patch_backup_per_request_20260419T155717/` — backup of pre-patch source tree

### Scripts
- `scripts/run_vllm_openai_latency_stress.py` — OpenAI-compatible latency stress harness (GPU-utilization-capable version)
- `scripts/run_vllm_sink_retention_benchmark.py` — offline benchmark script
- `package_review/run_vllm_openai_latency_stress.py` — harness copy in review bundle

### Data
- `data/attention_sink_probes.jsonl` — attention sink probe data

### Phase 1: Offline Smoke Results
- `results/qwen25_3b_per_request_smoke_n4_768x8.json`
- `results/qwen25_3b_per_request_smoke_n4_768x8.log`

### Phase 2: OpenAI Latency Smoke Results
- `results/qwen25_3b_openai_baseline_latency_n16_c4_768x16.json`
- `results/qwen25_3b_openai_retention_latency_n16_c4_768x16.json`
- `results/qwen25_3b_openai_server.log`

### Phase 3: Calibrated Sweep Results
- `results/qwen25_3b_openai_calibrated_sweep_summary.md`
- `results/qwen25_3b_openai_calibrated_sweep_summary.json`
- `results/qwen25_3b_openai_baseline_latency_n96_c8_1024x64_trial1.json`
- `results/qwen25_3b_openai_retention_latency_n96_c8_1024x64_trial1.json`
- `results/qwen25_3b_openai_baseline_latency_n96_c8_1024x64_trial2.json`
- `results/qwen25_3b_openai_retention_latency_n96_c8_1024x64_trial2.json`
- `results/qwen25_3b_openai_baseline_latency_n128_c16_1024x64_trial1.json`
- `results/qwen25_3b_openai_retention_latency_n128_c16_1024x64_trial1.json`
- `results/qwen25_3b_openai_baseline_latency_n256_c16_1024x128_trial1.json`
- `results/qwen25_3b_openai_retention_latency_n256_c16_1024x128_trial1.json`

### Server Logs
- `results/qwen25_3b_openai_server_sweep_20260420T000840Z.log`
- `results/qwen25_3b_openai_server_long_20260420T001353Z.log`
- `results/qwen25_3b_openai_server_long_20260420T001419Z.log`
- `results/qwen25_3b_openai_server_long_foreground_20260420T001441Z.log`

### Paper Artifacts
- `papers/.../claim_ledger.json` — audited claims with confidence levels and wording constraints
- `papers/.../evidence_bundle.json` — structured evidence summary
- `papers/.../paper_manifest.json` — paper artifact manifest
