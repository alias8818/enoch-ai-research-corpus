# Value-per-Joule Broker Online Canary on GB10 Endpoints

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We report results from deploying a value-per-joule (VPJ) routing broker as a controlled online canary against local GB10 llama.cpp endpoints. The VPJ policy routes inference requests to the model tier that maximizes estimated successful-output value per joule of energy consumed, using calibration data from prior offline measurement. We evaluated the canary in two modes: (1) replay of previously recorded parent-project telemetry and (2) live inference against temporary local llama.cpp servers serving SmolLM2-135M and Qwen3-0.6B GGUF models. In replay mode, the VPJ policy reduced cost-per-success by 32.06% and joules-per-success by 27.92% relative to a confidence-only baseline, with no quality or SLA regression. In live mode, cost-per-success fell 79.44% and joules-per-success fell 82.52%, with a +5.56 percentage-point success-rate improvement and a 167 ms p95 latency reduction. All pre-specified rollback guards passed in both modes. These results are bounded to the specific small-model, single-host, short-duration canary setting; generalization to larger models, multi-host deployments, or sustained production traffic is not established.

## 1. Introduction

Inference routing for language model endpoints typically relies on confidence thresholds or static tier assignments, selecting between model sizes without explicit consideration of the energy cost of each successful response. A value-per-joule (VPJ) broker attempts to improve on this by estimating the ratio of output value (e.g., task success) to energy consumed, then routing to whichever model tier maximizes that ratio for a given request.

Prior work in this project lineage developed an offline VPJ broker and calibrated it against recorded endpoint telemetry. The present work extends that broker into a controlled online canary harness that can shadow live requests, apply the VPJ routing policy, and compare outcomes against confidence-only and static-tiering baselines — all while enforcing pre-specified rollback guards.

The central question is whether the VPJ policy, when applied in an online setting against real (if small) local endpoints, can reduce cost and energy per successful outcome without degrading quality, SLA compliance, or latency below acceptable thresholds.

## 2. Method

### 2.1 Value-per-Joule Routing Policy

The VPJ broker maintains per-tier calibration estimates of success probability and energy consumption per request. For each incoming request, the policy computes:

$$\text{VPJ}_t = \frac{P(\text{success} \mid \text{tier } t)}{J_t}$$

where $P(\text{success} \mid \text{tier } t)$ is the estimated probability of a successful outcome at tier $t$ and $J_t$ is the estimated joules consumed per request at tier $t$. The request is routed to the tier with the highest VPJ score. Calibration values derive from prior offline measurement runs stored in the parent project's telemetry artifacts.

### 2.2 Canary Harness

The online canary harness (`scripts/online_canary.py`) performs the following steps for each request:

1. **Endpoint verification**: Confirms that `/v1/models` and `/v1/chat/completions` routes respond on the configured OpenAI-compatible endpoints.
2. **Request shadowing**: Each request is shadowed across three arms: `small_model`, `retrieval_tool`, and `frontier_model`.
3. **VPJ routing**: The canary arm routes through the measured-calibrated VPJ policy.
4. **Baseline comparison**: Outcomes are compared against a confidence-only baseline (routing based solely on model confidence scores) and a static-tiering baseline.
5. **Rollback guard evaluation**: Pre-specified kill conditions are checked after each canary run.
6. **Artifact emission**: JSON, CSV, and Markdown summaries are written for post-hoc analysis.

### 2.3 Rollback Guards

The following pre-specified kill conditions trigger an automatic rollback of the VPJ canary:

| Guard | Threshold |
|-------|-----------|
| VPJ cost-per-success reduction vs. confidence-only | < 20% |
| Joules-per-success regression | Any increase |
| Quality (success rate) drop | > 5 pp |
| SLA hit-rate drop | > 0.25 pp |
| p95 latency increase | > 100 ms |
| Endpoint error rate | > 2% |
| Minimum observed requests | < 12 |

### 2.4 Evaluation Modes

**Replay mode.** The canary replays previously recorded parent-project telemetry through the VPJ routing logic without issuing live inference requests. This constitutes a simulation-based validation against historical request distributions.

**Live mode.** The canary issues actual inference requests to temporary llama.cpp servers running on the local host. This constitutes a llama.cpp hook-prototype validation: real inference occurs, but on ephemeral single-host servers with small models, not on a production deployment.

## 3. Results

### 3.1 Regression Tests

All 15 unit and integration tests passed in 0.11 seconds, covering guard behavior and replay-mode canary logic.

### 3.2 Replay-Mode Canary

The replay canary processed recorded parent telemetry through the VPJ policy. Results relative to the confidence-only baseline:

| Metric | Delta |
|--------|-------|
| Cost per success | −32.06% |
| Joules per success | −27.92% |
| Success rate | 0.00 pp |
| SLA hit rate | 0.00 pp |
| p95 latency | −71.09 ms |

All rollback guards passed.

### 3.3 Live-Mode Canary

The live canary ran against temporary local llama.cpp servers:

- **Small route**: SmolLM2-135M-Instruct-Q4_K_M on `127.0.0.1:8001`
- **Frontier route**: Qwen3-0.6B-Q4_K_M on `127.0.0.1:8002`

Results relative to the confidence-only baseline:

| Metric | Delta |
|--------|-------|
| Cost per success | −79.44% |
| Joules per success | −82.52% |
| Success rate | +5.56 pp |
| SLA hit rate | 0.00 pp |
| p95 latency | −167.17 ms |

All rollback guards passed. Both temporary servers were confirmed stopped after the canary run; no residual processes remained on ports 8001 or 8002.

### 3.4 Discrepancy Between Replay and Live Results

The live-mode cost-per-success reduction (79.44%) substantially exceeds the replay-mode reduction (32.06%). This discrepancy likely reflects differences in the request distributions and model behavior between the historical telemetry (which was recorded against different or larger models in the parent project) and the live small-model endpoints used here. The live models' energy profiles and success rates differ from the calibration assumptions embedded in the replay telemetry, which may inflate or deflate the apparent VPJ advantage. We caution against interpreting the live-mode percentage as a stable or transferable figure.

## 4. Limitations

1. **Small models only.** The live canary used SmolLM2-135M and Qwen3-0.6B, both quantized to Q4_K_M. These are far smaller than production-grade models. VPJ routing advantages may change — potentially shrink or reverse — with larger models whose energy profiles and success-rate curves differ substantially.

2. **Single-host, ephemeral deployment.** Both llama.cpp servers ran on the same host, launched and terminated within the canary command. This does not exercise network latency, multi-node scheduling, or sustained-load thermal behavior.

3. **Short duration.** The canary run covered a bounded number of requests in a single session. It does not establish behavior under sustained production traffic, diurnal load variation, or extended soak conditions.

4. **Replay–live distribution mismatch.** The replay mode uses parent-project telemetry that was recorded under different model configurations. The live mode uses locally served small models. The two modes therefore test different (and not directly comparable) request distributions and calibration assumptions.

5. **No external replication.** All results are from a single hardware configuration (local GB10 host). Replication on different hardware, model families, or quantization levels is not established.

6. **Energy estimation method.** Joules-per-request figures depend on the measurement methodology inherited from the parent project. If the underlying energy measurement has systematic bias (e.g., from sampling granularity or power-meter accuracy), the absolute joule values and derived VPJ ratios may be affected, though relative comparisons within the same measurement framework remain valid.

7. **Automated artifact provenance.** This draft and all reported results were generated by an automated research pipeline. No independent human verification of the numerical results has been performed.

## 5. Reproducibility Checklist

| Item | Status |
|------|--------|
| Can the canary harness be re-executed from project files? | Yes; `scripts/online_canary.py` and `tests/test_online_canary.py` are present in the project directory. |
| Are model files specified? | Yes; SmolLM2-135M-Instruct-Q4_K_M.gguf and Qwen3-0.6B-Q4_K_M.gguf, symlinked from parent cache. |
| Are result artifacts available? | Yes; JSON, CSV, and Markdown outputs listed in artifact manifest below. |
| Are rollback guard thresholds documented? | Yes; specified in run notes and this paper. |
| Can the regression test suite be re-run? | Yes; 15 tests pass under `pytest`. |
| Is the calibration data from the parent project available? | Yes; `results/scaled_qwen25_endpoint_replay.json`, `results/large_calibrated_replay.json`, and associated summaries are present. |
| Is the live canary reproducible without manual server startup? | Yes; the canary harness launches and tears down temporary llama.cpp servers automatically. |
| Has this been validated on different hardware? | No. |
| Has this been validated with different model families or sizes? | No. |
| Has independent human verification been performed? | No. |

## 6. Conclusion

A value-per-joule routing broker was deployed as a controlled online canary on local GB10 llama.cpp endpoints and evaluated in both replay and live modes. In both modes, the VPJ policy reduced cost-per-success and joules-per-success relative to a confidence-only baseline while passing all pre-specified rollback guards. The live-mode canary additionally showed a modest success-rate improvement and a p95 latency reduction.

These findings support the hypothesis that VPJ routing can improve energy and cost efficiency without quality degradation in the tested setting. However, the results are bounded to small quantized models on a single host in short-duration runs. The substantial gap between replay-mode and live-mode improvement magnitudes underscores that VPJ advantages are sensitive to the calibration data and request distribution. Generalization to larger models, multi-host deployments, and sustained production traffic remains an open question. A longer production-soak evaluation would be a natural next step if the canary harness is to be promoted beyond its current controlled scope.

## Referenced Artifacts

### Result files
- `results/online_canary_replay.json`
- `results/online_canary_decisions.csv`
- `results/online_canary_summary.md`
- `results/online_canary_live.json`
- `results/online_canary_live_decisions.csv`
- `results/online_canary_live_summary.md`
- `results/online_canary_live.json`
- `results/endpoint_discovery.json`
- `results/live_small_llama_server.log`
- `results/live_frontier_llama_server.log`
- `results/scaled_qwen25_endpoint_replay.json`
- `results/scaled_qwen25_endpoint_summary.md`
- `results/large_calibrated_replay.json`
- `results/large_calibrated_summary.md`

### Source and test files
- `scripts/online_canary.py`
- `scripts/value_per_joule_broker.py`
- `scripts/measured_endpoint_replay.py`
- `scripts/large_calibrated_replay.py`
- `scripts/bootstrap_measured_replay.py`
- `services/transformers_openai_shim.py`
- `tests/test_online_canary.py`
- `tests/test_large_calibrated_replay.py`
- `tests/test_bootstrap_measured_replay.py`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`
- `run_notes.md`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`

### Model files (symlinked from parent cache)
- `models/SmolLM2-135M-Instruct-Q4_K_M.gguf`
- `models/Qwen3-0.6B-Q4_K_M.gguf`
