# Engine-Level Prefix Cache Cohort Scheduler

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We evaluate whether engine-level longest-common-prefix (LCP) slot assignment in llama.cpp's multi-slot server improves prompt-cache reuse and request latency over the default least-recently-used (LRU) slot selection. Using a live A/B harness against llama-server with Phi-4-mini-instruct (Q4_K_M), we compare `--slot-prompt-similarity 0.0` (LRU baseline) against nonzero similarity thresholds across three workload scenarios: repeated system prompts, mixed chat extraction, and adversarial unrelated prompts. On the repeated-prefix workload, LCP slot selection at threshold 0.10 reduced p95 latency by 14.3% and mean prompt-evaluation time by 47.4% relative to LRU baseline. On the mixed-chat workload, the same threshold yielded 6.3% p95 improvement and 15.9% prompt-eval improvement. The adversarial-unrelated scenario showed no material latency harm (p95 change between −0.9% and +0.2%). These results are narrow in scope—single model, single hardware host, 24 requests per scenario—and confidence is medium. The findings support adopting `--slot-prompt-similarity 0.10` as a default for deployments with repeated-prefix traffic patterns, pending production-scale validation.

## 1. Introduction

Autoregressive language model serving incurs substantial cost in prompt evaluation (prefill), particularly when concurrent requests share common prefix content such as system prompts or shared context. KV-cache reuse across requests that share a prefix can eliminate redundant prompt evaluation, but only if the serving engine assigns incoming requests to slots that already hold compatible cached prefix state.

A prior project (the parent branch) attempted to achieve prefix-cache reuse through external request reordering against an OpenAI-compatible API endpoint. That approach failed: the external reordering layer could not control which internal server slot received which request, and server logs showed no increase in LCP slot selections. The present work investigates whether modifying the engine's own slot-assignment policy—rather than reordering requests externally—can unlock measurable prefix-cache reuse.

We find that llama.cpp's server already implements an LCP slot-selection mechanism, exposed via the `--slot-prompt-similarity` flag (also `-sps`), with a documented default of 0.10 in the inspected checkout. When this mechanism is disabled (threshold 0.0), the server falls back to LRU slot selection. We conduct live benchmarks comparing these two regimes across multiple workload shapes and similarity thresholds.

## 2. Method

### 2.1 Mechanism Under Study

The llama.cpp server (`tools/server/server-context.cpp`) implements slot selection in `get_available_slot()`. When `--slot-prompt-similarity` is set to a nonzero value, the server computes the longest common prefix between the incoming prompt and each idle slot's cached prompt. If the similarity ratio exceeds the threshold, the server selects the slot with the highest prefix overlap, enabling KV-cache reuse for the shared prefix tokens. When the threshold is 0.0 or no slot meets the threshold, the server selects the least-recently-used idle slot.

### 2.2 Harness Design

We implemented `src/engine_slot_lcp_ab.py`, a Python-stdlib harness that:

1. Launches a fresh llama-server process from a neutral working directory (`/tmp/enoch_engine_slot_lcp_service`) with a specified `--slot-prompt-similarity` value.
2. Waits for the `/v1/models` and `/v1/chat/completions` endpoints to become responsive.
3. Sends a defined sequence of chat completion requests according to a scenario specification.
4. Captures per-request latency, prompt-evaluation time, and token counts into CSV and JSON artifacts.
5. Stops the server process and verifies cleanup via port probes.

The harness supports two modes:

- **Focused mode:** A two-cohort A/B comparison between threshold 0.0 and a single nonzero threshold on a bursty repeated-prefix workload.
- **Parent mode:** A threshold sweep across multiple scenarios and similarity values, launching a fresh server for each combination.

### 2.3 Workload Scenarios

Three scenarios were adapted from the parent project's workload generator:

- **repeated_system_prompts:** Requests alternate between two cohorts, each sharing a long system prompt within cohort but differing across cohorts. This scenario maximizes prefix reuse opportunity when LCP slot selection is active.
- **mixed_chat_extraction:** Requests share a moderate-length system prompt with varying user instructions. Prefix reuse is partial.
- **adversarial_unrelated:** Requests carry unrelated prompts with minimal prefix overlap. This scenario tests whether LCP slot selection causes latency harm when no reuse opportunity exists.

### 2.4 Threshold Sweep

For the parent-mode sweep, four similarity thresholds were tested: 0.0 (LRU baseline), 0.05, 0.10, and 0.20. Each scenario × threshold combination was run as an independent server session.

## 3. Results

### 3.1 Focused Two-Cohort A/B Test

Configuration: llama.cpp server, Phi-4-mini-instruct Q4_K_M, 24 sequential chat requests, `--parallel 2`, `--ctx-size 4096`, `max_tokens=8`.

| Metric | LRU Baseline (threshold 0.0) | LCP Selection (threshold 0.10) | Change |
|---|---|---|---|
| p50 latency | 134.86 ms | 121.90 ms | −9.6% |
| p95 latency | 286.39 ms | 245.41 ms | −14.3% |
| Mean prompt-eval time | 23.33 ms | 12.27 ms | −47.4% |
| LCP slot selections (server log) | 0 | 22 | — |
| LRU slot selections (server log) | 25 | 3 | — |

Server logs confirm that the LCP mechanism was active: at threshold 0.0, all 25 slot selections were LRU; at threshold 0.10, 22 of 25 selections were LCP. The reduction in mean prompt-evaluation time is consistent with KV-cache reuse on shared prefix tokens.

### 3.2 Parent Workload Threshold Sweep

Configuration: same model and hardware; 24 sequential chat requests per scenario per threshold, `--parallel 2`, `--ctx-size 4096`, `max_tokens=8`.

**repeated_system_prompts:**

| Threshold | p95 Latency Change vs Baseline | Mean Prompt-Eval Change vs Baseline | LCP Selections |
|---|---|---|---|
| 0.0 (baseline) | — | — | 0 |
| 0.05 | Not reported separately | Not reported separately | Present |
| 0.10 | Not reported separately | Not reported separately | Present |
| 0.20 | −14.6% | −37.9% | 14–15 |

The best result for this scenario occurred at threshold 0.20, with p95 improvement of 14.6% and prompt-eval improvement of 37.9%. LCP selections appeared 14–15 times versus 0 in the baseline.

**mixed_chat_extraction:**

| Threshold | p95 Latency Change vs Baseline | Mean Prompt-Eval Change vs Baseline | LCP Selections |
|---|---|---|---|
| 0.0 (baseline) | — | — | 0 |
| 0.10 | −6.3% | −15.9% | 4–5 |

The best result for this scenario occurred at threshold 0.10, with p95 improvement of 6.3% and prompt-eval improvement of 15.9%. LCP selections appeared 4–5 times versus 0 in the baseline. The lower improvement magnitude relative to repeated_system_prompts is expected given the partial prefix overlap in this scenario.

**adversarial_unrelated:**

| Threshold | p95 Latency Change vs Baseline |
|---|---|
| 0.0 (baseline) | — |
| 0.05 | Within [−0.9%, +0.2%] |
| 0.10 | Within [−0.9%, +0.2%] |
| 0.20 | Within [−0.9%, +0.2%] |

No material latency harm was observed. The p95 latency change across all nonzero thresholds fell between −0.9% and +0.2% relative to baseline, below the branch's predefined harm threshold.

### 3.3 Summary of Findings

- LCP slot selection produces measurable latency and prompt-evaluation improvements on workloads with shared prefixes.
- Improvement magnitude scales with prefix reuse opportunity: largest for repeated system prompts, moderate for mixed chat, and negligible (with no harm) for adversarial unrelated prompts.
- The similarity threshold affects which scenario benefits most: threshold 0.20 was best for the high-reuse scenario, while 0.10 was best for the moderate-reuse scenario.
- No adversarial latency degradation was observed at any tested threshold.

## 4. Limitations

1. **Single model and quantization.** All results were obtained with Phi-4-mini-instruct at Q4_K_M on a single host. Performance characteristics may differ for larger models, different quantizations, or GPU-accelerated serving where prompt-evaluation cost profiles differ substantially.

2. **Small request counts.** Each scenario × threshold cell used 24 sequential requests. Statistical power is limited; the observed improvements are consistent with LCP cache reuse but should be confirmed with larger samples and multiple random seeds.

3. **Sequential request pattern.** Requests were sent sequentially with `--parallel 2`. Under higher concurrency or different arrival patterns, slot contention may alter the LCP selection rate and benefit magnitude.

4. **No production-scale validation.** These are prototype/live benchmark results on a single machine, not production validation under sustained multi-user load. The project decision explicitly reserves production-scale multi-seed/load testing as future work.

5. **Existing mechanism, not novel implementation.** The LCP slot-selection mechanism already exists in the inspected llama.cpp checkout. This work validated and characterized its behavior rather than introducing a new algorithm. The novelty claim is limited to demonstrating that engine-level slot assignment resolves the failure mode of external request reordering.

6. **Incomplete threshold reporting.** The parent sweep reported best-threshold results per scenario but did not report full per-threshold latency numbers for all intermediate thresholds (0.05, 0.10) in the repeated_system_prompts scenario. The full data exists in server logs but was not summarized in the run notes.

7. **Confidence is medium.** The project decision assigned medium confidence, reflecting that the evidence is strong within the tested scope but has not been externally replicated or validated at scale.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Model specified | Yes: Phi-4-mini-instruct Q4_K_M GGUF |
| Engine version specified | Partial: llama.cpp server binary at stated path; specific commit hash not recorded in artifacts |
| Hardware described | Partial: single host; GPU/CPU, RAM, and OS not recorded in run notes |
| Random seeds recorded | No |
| Full command lines preserved | Yes: harness commands and server flags documented in run notes |
| Server logs captured | Yes: per-scenario, per-threshold logs in result files |
| Request-level CSV/JSON captured | Yes: `requests.csv` and `summary.json` per run |
| Cleanup verified | Yes: port probes confirmed no residual server processes |
| Harness source available | Yes: `src/engine_slot_lcp_ab.py` |
| Multiple thresholds tested | Yes: 0.0, 0.05, 0.10, 0.20 |
| Adversarial/harm scenario included | Yes: adversarial_unrelated |

## 6. Conclusion

Engine-level longest-common-prefix slot assignment in llama.cpp, activated via `--slot-prompt-similarity`, reduces prompt-evaluation cost and request latency on workloads with shared prefixes. In live benchmarks against Phi-4-mini-instruct, p95 latency improved by 14.3–14.6% on repeated-prefix workloads and 6.3% on mixed-prefix workloads, with no measurable harm on adversarial unrelated prompts. These results resolve the failure mode identified in the parent project: external request reordering could not control slot assignment, but the engine's native LCP mechanism can and does.

The recommended default for this substrate is `--slot-prompt-similarity 0.10`, which provided the best mixed-workload result, or a calibration sweep in the 0.05–0.20 range during deployment. These findings are bounded by the tested scope—single model, single host, small sample sizes—and should not be generalized to all serving configurations without further validation. Production-scale load testing with diverse models, concurrency levels, and arrival patterns remains necessary before broad deployment.

---

## Referenced Artifacts

### Decision and metadata
- `.omx/project_decision.json` — project decision (finalize_positive), hypothesis status, confidence, evidence strength
- `.omx/metrics.json` — session metrics
- `run_notes.md` — full execution log and interpretation

### Source code
- `src/engine_slot_lcp_ab.py` — live A/B and threshold-sweep harness

### Focused A/B test results
- `results/engine_slot_lcp/summary.json`
- `results/engine_slot_lcp/requests.csv`
- `results/engine_slot_lcp/report.md`
- `results/engine_slot_lcp/server_lcp_similarity.log`
- `results/engine_slot_lcp/server_lru_baseline.log`

### Parent workload threshold sweep results
- `results/engine_slot_lcp_parent_sweep/summary.json`
- `results/engine_slot_lcp_parent_sweep/requests.csv`
- `results/engine_slot_lcp_parent_sweep/report.md`
- `results/engine_slot_lcp_parent_sweep/server_sps_0_lru_repeated_system_prompts.log`
- `results/engine_slot_lcp_parent_sweep/server_sps_0_lru_mixed_chat_extraction.log`
- `results/engine_slot_lcp_parent_sweep/server_sps_0_lru_adversarial_unrelated.log`
- `results/engine_slot_lcp_parent_sweep/server_sps_0p05_repeated_system_prompts.log`
- `results/engine_slot_lcp_parent_sweep/server_sps_0p05_mixed_chat_extraction.log`
- `results/engine_slot_lcp_parent_sweep/server_sps_0p05_adversarial_unrelated.log`
- `results/engine_slot_lcp_parent_sweep/server_sps_0p1_repeated_system_prompts.log`
- `results/engine_slot_lcp_parent_sweep/server_sps_0p1_mixed_chat_extraction.log`
- `results/engine_slot_lcp_parent_sweep/server_sps_0p1_adversarial_unrelated.log`
- `results/engine_slot_lcp_parent_sweep/server_sps_0p2_repeated_system_prompts.log`
- `results/engine_slot_lcp_parent_sweep/server_sps_0p2_mixed_chat_extraction.log`
- `results/engine_slot_lcp_parent_sweep/server_sps_0p2_adversarial_unrelated.log`

### Paper artifacts
- `papers/.../claim_ledger.json` — audited claims and allowed/forbidden wording
- `papers/.../evidence_bundle.json` — full evidence bundle with decision, run notes, and file manifest
- `papers/.../paper_manifest.json` — paper metadata and written artifact list
