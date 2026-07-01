# GB10 Joule Router Live Calibration Adapter

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We present the design and empirical evaluation of a live calibration adapter for energy-aware request routing on the NVIDIA GB10 GPU platform. The adapter integrates sibling vLLM GPU power traces to derive idle-floor-subtracted joules-per-token constants, probes OpenAI-compatible local serving endpoints for liveness and compatibility, and applies a shadow-routing policy that can redirect requests when quality or energy metadata indicate the primary endpoint is insufficient. Calibration from 8 sibling GB10 vLLM runs (Qwen3-4B) yielded an idle power floor of approximately 21.97 W, an active base cost of approximately 7.36 J/request, prompt cost of approximately 0.221 J/token, and completion cost of approximately 0.250 J/token. Live shadow-routing was validated against a GB10-backed llama.cpp server serving Qwen3-0.6B-Q4_K_M, completing all sample chat requests with sub-second latencies (0.324–0.509 s) and demonstrating route changes on 2 of 3 requests when quality metadata differed. Point-in-time nvidia-smi readings confirmed GPU power escalation from approximately 12.16 W idle to approximately 34.00 W under load. A notable model-mismatch limitation exists: live serving used Qwen3-0.6B while calibration derived from Qwen3-4B traces, so the reported joules-per-token constants should not be applied to the live model without re-calibration. The project decision is finalize_positive with medium confidence and strong evidence strength within the tested setting.

## 1. Introduction

Energy-aware request routing for local LLM serving requires platform-specific calibration data and a mechanism to apply that calibration to live routing decisions. Prior work in this project lineage established a synthetic joule-per-request router simulator but did not validate against real GPU power traces or live serving endpoints. The present work extends that foundation with a concrete adapter that (a) calibrates from observed GB10 GPU power CSV traces, (b) probes OpenAI-compatible endpoints for availability, and (c) applies shadow-routing policies that can redirect requests based on quality and energy metadata.

The central question is whether a dependency-light adapter can successfully bridge calibrated energy profiles and live endpoint routing on the GB10 platform. We report results from two experimental phases: a calibration-only dry-run phase using sibling vLLM traces, and a live shadow-routing phase against a provisioned GB10-backed llama.cpp server. The results are positive but carry a model-mismatch caveat that limits the direct applicability of the calibration constants to the live serving configuration tested.

## 2. Method

### 2.1 Adapter Architecture

The adapter (`src/gb10_live_calibration_adapter.py`) is a dependency-light Python module implementing four functions:

1. **Sibling trace discovery and power parsing.** The adapter locates sibling vLLM summary and GPU power CSV files via a manifest (`artifacts/sibling_traces/manifest.json`). It supports two observed GB10 power CSV formats and performs idle-floor-subtracted power integration: energy is computed as the integral of (observed power − idle power floor) over the trace duration.

2. **Calibration.** From parsed power traces, the adapter derives calibrated constants: idle power (W), active base energy (J/request), prompt energy (J/token), and completion energy (J/token). These constants parameterize the energy cost model for subsequent routing decisions.

3. **Endpoint probing.** The adapter probes candidate endpoints by issuing HTTP requests to `/v1/models` or `/models` and `/v1/chat/completions` or `/chat/completions`. Endpoints that fail either probe are marked unavailable and excluded from live routing.

4. **Shadow routing.** Given a set of probe-verified endpoints with associated quality and energy metadata, the adapter applies a shadow-routing policy. When the primary endpoint's quality metadata is insufficient for a given request, the policy redirects to an alternative endpoint. The routing decision is recorded for analysis.

### 2.2 Calibration Data Source

Calibration used 8 sibling vLLM runs on the NVIDIA GB10 GPU, model hint Qwen/Qwen3-4B, with GPU power CSV traces recorded during those runs. The sibling trace manifest (`artifacts/sibling_traces/manifest.json`) indexes these traces.

### 2.3 Live Endpoint Provisioning

A llama.cpp server (`llama-server`) was started on `<loopback-redacted>:18240` with full GPU offload (`-ngl 99`) using the cached GGUF model `Qwen3-0.6B-Q4_K_M`. The server reported its CUDA device as `NVIDIA GB10` and served OpenAI-compatible `/v1/models` and `/v1/chat/completions` endpoints. The server was stopped after the live benchmark completed.

### 2.4 Shadow-Routing Validation

Two shadow-routing experiments were conducted:

- **Primary shadow benchmark:** One live llama.cpp endpoint and one non-live calibrated reference endpoint. The reference endpoint was expected to fail probing and be excluded from live routing.
- **Quality shadow validation:** Two probe-passing endpoint specs backed by the same live llama.cpp server but with different quality metadata, testing whether the shadow policy correctly redirects when the primary endpoint's quality is insufficient.

## 3. Results

### 3.1 Calibration Constants (Sibling vLLM/GB10 Traces)

From 8 sibling vLLM runs on GB10 with model hint Qwen/Qwen3-4B:

| Parameter | Value |
|---|---|
| Idle power floor | ~21.97 W |
| Active base energy | ~7.36 J/request |
| Prompt energy cost | ~0.221 J/token |
| Completion energy cost | ~0.250 J/token |
| p95 latency | ~7.41 s |

Three dry-run shadow requests completed with an estimated total energy of 223.62 J. These are estimates derived from the calibrated model, not direct measurements of the dry-run requests themselves.

### 3.2 Endpoint Probe Results

Probing of likely local-serving ports from sibling artifacts and common defaults yielded:

| Port | Result |
|---|---|
| 8240 (parent vLLM) | Connection refused |
| 8150 (parent vLLM) | Connection refused |
| 8000 | Non-OpenAI health service |
| 8080 | HTML web UI, not JSON OpenAI-compatible |

No pre-existing OpenAI-compatible endpoint was found. This motivated the provisioning of the llama.cpp server described in Section 2.3.

### 3.3 Live Shadow-Routing Benchmark

The primary live llama.cpp endpoint completed all 3 sample chat requests:

| Request | Latency (s) |
|---|---|
| 1 | ~0.324 |
| 2 | ~0.509 |
| 3 | ~0.471 |

The non-live calibrated reference endpoint was correctly probe-gated as unavailable.

### 3.4 Quality Shadow-Policy Validation

With two probe-passing endpoint specs backed by the same live llama.cpp server but different quality metadata:

- Both specs passed `/v1/models` and `/v1/chat/completions` probes.
- All 3 live requests succeeded.
- The shadow policy changed route on 2 of 3 requests (66.7%) when quality metadata made the primary endpoint insufficient.

### 3.5 GPU Power Observations

Point-in-time nvidia-smi readings captured before and after the first live run:

| State | Power (W) | GPU Utilization |
|---|---|---|
| Before (idle) | ~12.16 | — |
| After (under load) | ~34.00 | ~88% |

Note: The idle nvidia-smi reading (~12.16 W) is lower than the idle power floor derived from sibling vLLM traces (~21.97 W). This discrepancy may reflect differences between the llama.cpp/Qwen3-0.6B configuration and the vLLM/Qwen3-4B configuration used for calibration, or differences in measurement methodology (point-in-time snapshot vs. trace-averaged floor).

### 3.6 Regression Tests

All 6 regression tests passed, covering power parsing, power integration, calibration, and shadow policy behavior.

## 4. Limitations

1. **Model-mismatch between calibration and live serving.** The calibration constants were derived from Qwen3-4B vLLM runs, while live shadow-routing used Qwen3-0.6B via llama.cpp. The energy profiles of these configurations differ substantially: the Qwen3-4B model is approximately 6–7× larger, and vLLM and llama.cpp have different serving overheads. The reported joules-per-token constants should not be applied to the Qwen3-0.6B/llama.cpp configuration without re-calibration.

2. **No synchronized live power CSV.** The live llama.cpp benchmark captured only point-in-time nvidia-smi snapshots before and after requests, not a continuous power trace synchronized with request timing. This prevents direct validation of the calibrated energy model against the live serving configuration.

3. **Small request sample.** The live shadow-routing experiments used 3 sample chat requests each. This is insufficient to characterize the statistical distribution of latencies or energy costs.

4. **Single GPU platform.** All results are specific to the NVIDIA GB10. Generalization to other GPU platforms is not established.

5. **Single-serving-endpoint topology.** The quality shadow validation used two endpoint specs backed by the same physical server. This tests the routing policy logic but not the behavior of genuinely heterogeneous endpoint pools.

6. **Idle power discrepancy.** The nvidia-smi idle reading (~12.16 W) and the calibration-derived idle floor (~21.97 W) differ. The source of this discrepancy is not fully resolved and may affect the accuracy of idle-floor-subtracted energy estimates.

7. **Automated artifact provenance.** This draft and all reported results were generated by an automated research pipeline. No independent human verification of the raw data or analysis has been performed.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Source code available | `src/gb10_live_calibration_adapter.py`, `src/joule_router_sim.py` |
| Test suite available | `tests/test_gb10_live_calibration_adapter.py`, `tests/test_joule_router_sim.py` (6 tests, all passing) |
| Calibration input data referenced | `artifacts/sibling_traces/manifest.json` indexes 8 sibling vLLM/GB10 runs |
| Calibration output recorded | `results/gb10_live_calibration_adapter.json` |
| Live endpoint configuration documented | `artifacts/live_llama_cpp/endpoints.json`, `artifacts/live_llama_cpp/endpoints_quality_shadow.json` |
| Live shadow-routing results recorded | `results/gb10_live_llama_cpp_shadow.json`, `results/gb10_live_llama_cpp_quality_shadow.json` |
| GPU power snapshots recorded | `artifacts/live_llama_cpp/nvidia_smi_before.csv`, `artifacts/live_llama_cpp/nvidia_smi_after.csv` |
| Probe attempt results recorded | `results/gb10_live_calibration_with_probe_attempts.json`, `artifacts/local_endpoint_probe_attempts.json` |
| Hardware specified | NVIDIA GB10 GPU |
| Model specified (calibration) | Qwen/Qwen3-4B (vLLM) |
| Model specified (live) | Qwen3-0.6B-Q4_K_M (llama.cpp GGUF) |
| llama.cpp server configuration documented | `<loopback-redacted>:18240`, `-ngl 99`, model alias `Qwen3-0.6B-Q4_K_M` |
| Random seeds | Not recorded; sample requests are deterministic chat completions |
| External dependencies | Python standard library + `requests`; llama.cpp binary at documented path |

## 6. Conclusion

The GB10 Joule Router Live Calibration Adapter demonstrates that sibling GPU power traces can be integrated to produce calibrated energy constants, and that a probe-gated shadow-routing policy can operate against a live GB10-backed OpenAI-compatible endpoint. The adapter completed all live chat requests, correctly excluded non-live endpoints via probing, and demonstrated quality-based route changes in 2 of 3 test requests.

The results support the hypothesis that live calibration and shadow routing are feasible on the GB10 platform, but with medium confidence due to the model-mismatch between calibration (Qwen3-4B/vLLM) and live serving (Qwen3-0.6B/llama.cpp). The recommended next step is to repeat the live run with a Qwen3-4B vLLM endpoint and synchronized nvidia-smi CSV sampling to remove this mismatch. Until such a re-calibration is performed, the reported energy constants should be treated as applicable only to the Qwen3-4B/vLLM/GB10 configuration from which they were derived.

## Referenced Artifacts

### Result files
- `results/gb10_live_calibration_adapter.json` — calibration constants and dry-run shadow estimates
- `results/gb10_live_calibration_with_probe_attempts.json` — endpoint probe attempt outcomes
- `results/gb10_live_llama_cpp_shadow.json` — live shadow-routing benchmark results
- `results/gb10_live_llama_cpp_quality_shadow.json` — quality shadow-policy validation results

### Artifact files
- `artifacts/sibling_traces/manifest.json` — sibling vLLM/GB10 trace index
- `artifacts/local_endpoint_probe_attempts.json` — probe attempt details
- `artifacts/live_llama_cpp/endpoints.json` — live endpoint configuration
- `artifacts/live_llama_cpp/endpoints_quality_shadow.json` — quality shadow endpoint configuration
- `artifacts/live_llama_cpp/nvidia_smi_before.csv` — GPU power snapshot before live run
- `artifacts/live_llama_cpp/nvidia_smi_after.csv` — GPU power snapshot after live run

### Source and test files
- `src/gb10_live_calibration_adapter.py`
- `src/joule_router_sim.py`
- `tests/test_gb10_live_calibration_adapter.py`
- `tests/test_joule_router_sim.py`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `run_notes.md`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
