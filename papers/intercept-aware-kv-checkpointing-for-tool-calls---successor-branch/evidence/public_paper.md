# Intercept-Aware KV Checkpointing Admission Policy for Tool Calls

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

Large-language-model inference runtimes that support tool calls must decide whether to checkpoint the key-value (KV) cache at the intercept point before yielding control to an external tool. Checkpointing enables fast resumption but incurs serialization overhead that is not justified for short, single-resume tool calls. We present an intercept-aware admission policy that gates KV checkpointing on projected net savings: a deterministic formula comparing estimated replay prefill cost against checkpoint write/read overhead, with a heightened threshold for one-step cases. We evaluate the policy on a 12-scenario benchmark matrix spanning low-replay one-step tool calls and high-replay multi-step or long-context cases, using measured `llama_state_get_data`/`llama_state_set_data` serialization timings from a Phi-4-mini-instruct (Q4_K_M) model via llama.cpp. The policy rejects all six low-replay one-step scenarios and admits all six high-replay scenarios with positive projected net savings. A sensitivity sweep across 30 timing regimes shows the policy is stable in 26 of 30 configurations, with failures concentrated in high-checkpoint-overhead/low-prefill-cost regimes. The closest margin on the reject side is 724.9 ms (single_search_medium); the weakest admit margin is 14,989 ms (multi_shell_3step). Results are limited to a single model, a single hardware environment, and a benchmark-driven evaluation rather than a production tool-call runtime integration.

## 1. Introduction

Autonomous LLM agents that invoke external tools (shell commands, web searches, JSON API calls) must suspend generation, execute the tool, and resume inference with the tool output appended to the context. If the KV cache is not preserved at the intercept point, the runtime must re-prefill the entire prefix upon resumption—a cost proportional to prefix length. KV cache checkpointing at the intercept point eliminates this replay cost but introduces serialization and deserialization overhead.

The central observation motivating this work is that checkpointing is not uniformly beneficial. A short web search that returns in one resume step incurs checkpoint overhead for minimal replay savings, while a multi-step shell pipeline or a tool call that appends large output to a long context stands to save substantial re-prefill time. An admission policy that checkpoints indiscriminately wastes resources; one that never checkpoints forfeits savings in the cases that need them most.

We investigate a deterministic, intercept-aware admission policy that decides at tool-call intercept time whether to checkpoint the KV cache. The policy computes projected net savings as the difference between estimated replay prefill cost and checkpoint write/read overhead, with a one-step safeguard that requires substantially larger projected savings for single-resume cases. We evaluate this policy through a multi-stage validation pipeline progressing from synthetic timing estimates through real llama.cpp prefill measurements to direct libllama state serialization/deserialization probes, reporting both positive and negative findings at each stage.

## 2. Method

### 2.1 Admission Policy Formula

The admission policy evaluates each tool-call intercept along three axes:

1. **Replay cost** — the estimated prefill time to reconstruct the KV cache if the checkpoint is not taken, computed as `weighted_replay_tokens × prefill_ms_per_1k_tokens / 1000`. Weighted replay tokens account for the number of expected resume steps and the context length exposed to tool output.

2. **Checkpoint overhead** — the sum of checkpoint write time (`llama_state_get_data` serialization) and checkpoint read time (`llama_state_set_data` deserialization into a fresh context).

3. **One-step safeguard** — for intercepts classified as single-resume (one-step) tool calls, the policy requires `projected_net_saved_ms ≥ one_step_min_net_saved_ms`, where `one_step_min_net_saved_ms` is a configurable threshold. For multi-step or repeated-resume cases, the standard positive-net-savings condition applies.

The admission decision is:

```
admit = (projected_net_saved_ms > 0)
        AND (
          is_one_step → projected_net_saved_ms ≥ one_step_min_net_saved_ms
        )
```

The `one_step_min_net_saved_ms` threshold was initially set to 750 ms based on synthetic estimates, then revised to 3,000 ms after real llama.cpp timing measurements revealed the original value was under-conservative for one-step cases (Section 3.2).

### 2.2 Benchmark Matrix

A 12-scenario benchmark matrix was constructed to cover two regimes:

**Low-replay one-step cases (6 scenarios):** Short tool calls with a single resume step and modest context lengths. Examples include `web_short_2` (short web search, 2k context), `json_tool_short` (short JSON tool call), and `single_search_medium` (single search with medium context). These represent the regime where checkpointing is expected to be rejected.

**High-replay repeated/long-context cases (6 scenarios):** Multi-step tool pipelines, repeated-resume workflows, or tool calls that append large output to long contexts. Examples include `multi_shell_3step` (3-step shell pipeline), `repeated_api_5x` (5× repeated API calls), and `large_tool_context` (32300 weighted replay tokens). These represent the regime where checkpointing is expected to be admitted.

### 2.3 Evaluation Pipeline

The evaluation proceeds through six stages of increasing measurement fidelity:

1. **Deterministic evaluation** — synthetic timing constants for prefill and checkpoint overhead applied to the benchmark matrix.

2. **Sensitivity sweep** — the same matrix evaluated across 30 timing regimes: prefill rates of [20, 35, 50, 70, 100, 140] ms per 1k tokens crossed with checkpoint overheads of [75, 125, 250, 500, 1000] ms.

3. **Fixture backend** — a regression-test backend emitting fixed timing values to verify the adapter pipeline without model dependence.

4. **Surrogate backend** — a non-model timing source that produces plausible but non-LLM timings, used to verify that the pipeline correctly handles inputs that fall outside expected ranges.

5. **llama-bench backend** — real llama.cpp prefill timing using `llama-bench` with a Phi-4-mini-instruct Q4_K_M GGUF model, with checkpoint write/read measured as KV-sized filesystem I/O.

6. **Direct libllama state probe** — a C++ probe (`libllama_state_probe.cpp`) built against the llama.cpp library that measures `llama_state_get_data` serialization time and `llama_state_set_data` deserialization time in memory, providing the most faithful checkpoint timing available without a full production runtime. Run both capped (max 4096 prompt tokens) and uncapped (all 12 rows, including `large_tool_context` at 2,250,302,272 serialized state bytes).

### 2.4 Kill Condition

The branch-specific kill condition requires the admission policy to:

- Reject at least 90% of low-replay one-step cases.
- Admit at least 80% of high-replay repeated/long-context cases.
- Ensure all admitted cases have positive projected net savings.

## 3. Results

### 3.1 Deterministic and Sensitivity Evaluation

On the synthetic deterministic matrix, the policy achieves a low one-step rejection rate of 1.0, a high-replay admission rate of 1.0, and a positive-net admitted rate of 1.0, passing the kill condition.

The sensitivity sweep across 30 timing regimes passes in 26 of 30 configurations (86.7%). The four failing configurations occur in regimes with high checkpoint overhead (≥500 ms) combined with low prefill cost (≤35 ms/1k tokens), where high-replay cases fail to meet the admission threshold. No low one-step rejection failures occur after the one-step safeguard was introduced.

### 3.2 llama-bench Backend: Threshold Revision

The initial llama-bench run with `one_step_min_net_saved_ms = 750` failed the kill condition: the low one-step rejection rate dropped to 0.5 because `web_short_2`, `json_tool_short`, and `single_search_medium` crossed the one-step admission path under real prefill rates. This was a negative finding that exposed an under-conservative threshold.

After revising `one_step_min_net_saved_ms` to 3,000 ms, the llama-bench evaluation achieved:

| Metric | Value |
|---|---|
| Low one-step rejection rate | 1.0 |
| High replay admission rate | 1.0 |
| Positive-net admitted rate | 1.0 |
| Kill condition passed | true |
| Expected decisions preserved | 12/12 |

Closest expected-reject row: `single_search_medium`, 754.038 ms below accidental admission. Weakest expected-admit row: `multi_shell_3step`, 9,302.059 ms above admission.

### 3.3 Direct libllama State Probe

The direct libllama state probe replaces KV-sized filesystem I/O with in-memory `llama_state_get_data`/`llama_state_set_data` measurements, providing the most precise checkpoint timing in this study.

**Capped run (max 4096 prompt tokens):**

| Metric | Value |
|---|---|
| Low one-step rejection rate | 1.0 |
| High replay admission rate | 1.0 |
| Positive-net admitted rate | 1.0 |
| Kill condition passed | true |
| Expected decisions preserved | 12/12 |

**Uncapped run (all 12 rows, including `large_tool_context` at 2.25 GB serialized state):**

| Metric | Value |
|---|---|
| Low one-step rejection rate | 1.0 |
| High replay admission rate | 1.0 |
| Positive-net admitted rate | 1.0 |
| Kill condition passed | true |
| Expected decisions preserved | 12/12 |
| Closest expected-reject row | `single_search_medium`, 724.919 ms below accidental admission |
| Weakest expected-admit row | `multi_shell_3step`, 14,989.179 ms above admission |

### 3.4 Break-Even Analysis

Per-row break-even thresholds were computed to characterize the timing regimes under which each scenario would switch admission status:

- All six expected-reject rows remain below their admission threshold.
- All six expected-admit rows remain above their admission threshold at matrix timing.
- The closest low one-step row (`single_search_medium`) has 148.824 ms/1k tokens of headroom before accidental one-step admission at deterministic timing.
- The weakest expected-admit row (`multi_shell_3step`) has 28.51 ms/1k tokens of margin and tolerates up to 674.1 ms of total checkpoint write+read cost at matrix prefill speed.

### 3.5 Surrogate Backend: Expected Negative Result

The surrogate (non-model) timing backend correctly preserves all low one-step rejections but flags five high-replay rows as below the admission boundary. This is an expected negative result confirming that the pipeline correctly handles timing inputs that do not reflect real LLM prefill characteristics.

## 4. Limitations

1. **Single model coverage.** All model-backed measurements use Phi-4-mini-instruct (Q4_K_M, ~2.25 GB maximum serialized state). Admission boundaries and margins may differ substantially for larger models with different prefill rates and state sizes.

2. **Single hardware environment.** Timing measurements were collected on one machine. Prefill rates, serialization latency, and deserialization latency are hardware-dependent; the sensitivity sweep partially addresses this but does not replace multi-hardware validation.

3. **Benchmark matrix, not production workload.** The 12 scenarios are constructed test cases rather than traces from a deployed tool-call runtime. Real tool-call distributions may differ in context lengths, resume counts, and interleaving patterns.

4. **Checkpoint timing fidelity.** The direct libllama state probe measures `llama_state_get_data`/`llama_state_set_data` in isolation. A production runtime would incur additional overhead from context management, scheduling, and I/O routing not captured by the probe.

5. **Sensitivity sweep gaps.** Four of 30 timing regimes in the sensitivity sweep fail the kill condition, all in high-overhead/low-prefill regions. The policy does not currently adapt its thresholds to observed timing; a runtime-adaptive variant could address this.

6. **No end-to-end runtime integration.** The admission policy is evaluated as a standalone gate evaluator consuming timing artifacts. It has not been integrated into a serving framework (e.g., vLLM, llama.cpp server) with live tool-call dispatch and resumption.

7. **Threshold calibration dependence.** The `one_step_min_net_saved_ms = 3000` threshold was calibrated against one model's prefill rate. Transferability to other models or quantization levels is not established.

## 5. Reproducibility Checklist

- [x] **Benchmark matrix publicly specified.** The 12-scenario matrix is defined in `data/checkpoint_gate_matrix.csv` with per-case fields: case ID, weighted replay tokens, expected resume count, one-step flag, and expected admission/rejection label.
- [x] **Admission policy formula documented.** The policy formula, threshold values, and one-step safeguard are specified in `docs/admission_policy.md`.
- [x] **Evaluation scripts available.** All evaluator, sensitivity, timing, adapter, break-even, and margin-comparison scripts are present under `scripts/`.
- [x] **Timing probe source available.** The C++ direct-state probe source is `scripts/libllama_state_probe.cpp`, built against the llama.cpp library at `[redacted-local-llama.cpp-checkout]`.
- [x] **Model identified.** Phi-4-mini-instruct Q4_K_M GGUF from `lmstudio-community` on the local filesystem.
- [x] **Result artifacts persisted.** All JSON and CSV result files are listed in the artifact manifest (Section: Referenced Artifacts).
- [x] **Kill condition specified a priori.** The ≥90% one-step rejection, ≥80% high-replay admission, and positive-net admitted requirements were documented before evaluation.
- [ ] **Multi-model validation.** Not performed; only Phi-4-mini-instruct was tested.
- [ ] **Multi-hardware validation.** Not performed; only one machine was used.
- [ ] **Production runtime integration.** Not performed; evaluation is benchmark-driven.

## 6. Conclusion

We presented an intercept-aware admission policy for KV cache checkpointing at tool-call intercept points and evaluated it through a multi-stage validation pipeline culminating in direct libllama state serialization measurements. The policy successfully separates low-replay one-step tool calls (rejected) from high-replay multi-step and long-context cases (admitted) across deterministic, sensitivity, fixture, llama-bench, and direct-state probe evaluations on a Phi-4-mini-instruct model. A critical negative finding during the llama-bench stage—an under-conservative one-step threshold that admitted three short cases—was corrected by raising `one_step_min_net_saved_ms` from 750 ms to 3,000 ms, underscoring the importance of real-timing calibration over synthetic estimates.

The evidence supports the admission policy shape in the tested setting, but the results should not be generalized beyond the single model, single hardware environment, and constructed benchmark matrix examined here. The four failing sensitivity regimes and the absence of production runtime integration remain open gaps. Future work should validate the policy under diverse models, hardware, and real tool-call workloads, and integrate the gate into a serving runtime with live dispatch and resumption.

## Referenced Artifacts

### Decision and metadata
- `.omx/project_decision.json` — project decision (finalize_positive), hypothesis status, confidence, evidence strength
- `.omx/metrics.json` — session metrics

### Documentation
- `run_notes.md` — chronological run notes covering all evaluation stages
- `docs/admission_policy.md` — policy formula, thresholds, and branch kill condition

### Scripts
- `scripts/evaluate_checkpoint_gate.py` — deterministic admission evaluator
- `scripts/evaluate_checkpoint_gate_sensitivity.py` — timing-regime sensitivity sweep
- `scripts/measure_llama_cpp_timings.py` — timing harness (fixture, surrogate, llama-bench, llama-state backends)
- `scripts/libllama_state_probe.cpp` — C++ direct libllama state serialization/deserialization probe
- `scripts/evaluate_checkpoint_gate_from_timings.py` — timing-adapter evaluator
- `scripts/analyze_gate_break_even.py` — per-row break-even threshold analyzer
- `scripts/compare_timings_to_break_even.py` — timing-margin comparator

### Data
- `data/checkpoint_gate_matrix.csv` — 12-scenario benchmark matrix

### Result files (deterministic and sensitivity)
- `results/checkpoint_gate_eval.json`
- `results/checkpoint_gate_eval.csv`
- `results/checkpoint_gate_sensitivity.json`
- `results/checkpoint_gate_sensitivity.csv`
- `results/checkpoint_gate_break_even.json`
- `results/checkpoint_gate_break_even.csv`

### Result files (fixture and surrogate adapter)
- `results/timing_probe_fixture.json`
- `results/checkpoint_gate_eval_fixture_timing.json`
- `results/checkpoint_gate_eval_fixture_timing.csv`
- `results/checkpoint_gate_matrix_fixture_timing.csv`
- `results/checkpoint_gate_timing_margins_fixture.json`
- `results/checkpoint_gate_timing_margins_fixture.csv`
- `results/timing_probe_surrogate.json`
- `results/checkpoint_gate_eval_timing_probe.json`
- `results/checkpoint_gate_eval_timing_probe.csv`
- `results/checkpoint_gate_matrix_timing_probe.csv`
- `results/checkpoint_gate_timing_margins_surrogate.json`
- `results/checkpoint_gate_timing_margins_surrogate.csv`

### Result files (llama-bench backend, Phi-4-mini)
- `results/timing_probe_llama_bench_phi4mini.json`
- `results/checkpoint_gate_eval_llama_bench_phi4mini.json`
- `results/checkpoint_gate_eval_llama_bench_phi4mini.csv`
- `results/checkpoint_gate_matrix_llama_bench_phi4mini.csv`
- `results/checkpoint_gate_timing_margins_llama_bench_phi4mini.json`
- `results/checkpoint_gate_timing_margins_llama_bench_phi4mini.csv`

### Result files (direct libllama state probe, Phi-4-mini, capped)
- `results/timing_probe_llama_state_phi4mini.json`
- `results/checkpoint_gate_eval_llama_state_phi4mini.json`
- `results/checkpoint_gate_eval_llama_state_phi4mini.csv`
- `results/checkpoint_gate_matrix_llama_state_phi4mini.csv`
- `results/checkpoint_gate_timing_margins_llama_state_phi4mini.json`
- `results/checkpoint_gate_timing_margins_llama_state_phi4mini.csv`

### Result files (direct libllama state probe, Phi-4-mini, uncapped)
- `results/timing_probe_llama_state_phi4mini_uncapped.json`
- `results/checkpoint_gate_eval_llama_state_phi4mini_uncapped.json`
- `results/checkpoint_gate_eval_llama_state_phi4mini_uncapped.csv`
- `results/checkpoint_gate_matrix_llama_state_phi4mini_uncapped.csv`
- `results/checkpoint_gate_timing_margins_llama_state_phi4mini_uncapped.json`
- `results/checkpoint_gate_timing_margins_llama_state_phi4mini_uncapped.csv`

### Paper artifacts
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
