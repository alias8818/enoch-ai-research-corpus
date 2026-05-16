# Tool-Boundary Non-Speculate Gate: Capping Speculative Draft Length at Predicted Action Boundaries

> **AI provenance / no-human-credit note:** This draft was AI-generated from automated research artifacts produced by an autonomous research pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated the claims, code, or data herein.

---

## Abstract

Speculative decoding accelerates large-language-model inference by drafting multiple tokens with a small model and verifying them in a single forward pass of the target model. In tool-using agent workloads, however, the draft model may generate tokens across an external-action boundary (e.g., a tool-call invocation), forcing the verifier to reject the draft and the runtime to execute the tool before generation can resume. We investigate a *non-speculate gate* that caps the draft length at the predicted distance to the nearest action boundary, preventing the drafter from crossing it. Using a reproducible Monte Carlo simulator modeling agent token streams with external-action boundaries, we compare four policies: fixed-depth speculation, naive acceptance-based gamma adaptation, boundary-gated speculation, and their combination. Under the default synthetic workload (mean 48 tokens between boundaries, 90% boundary-predictor recall), the boundary gate reduces wasted draft compute by 18.8% and improves useful-token throughput by 6.6% relative to fixed-depth speculation, but does not meet a pre-registered 15% speedup threshold. At higher boundary density (mean 16 tokens between boundaries), the gate achieves 15.3% speedup and 30.3% waste reduction, clearing both thresholds. Naive acceptance-based gamma adaptation reduces waste but regresses throughput by increasing verifier-call frequency. These results are simulation-only; no real LLM draft/verifier pair or tool-agent trace distribution was available. The mechanism appears viable for workloads with frequent or predictable tool boundaries, but requires validation on real agent traces before production deployment.

## Introduction

Speculative decoding reduces the latency of autoregressive inference by having a small draft model propose multiple tokens that a larger target model then verifies in a single forward pass. When all drafted tokens are accepted, the amortized cost per token drops substantially. The method's efficiency depends on the acceptance rate: rejected tokens represent wasted draft compute and, in some formulations, wasted verifier compute.

In tool-using agent systems, the token stream is punctuated by *action boundaries*—points at which the agent must pause generation to execute an external tool call and incorporate its result. If the draft model speculates across such a boundary, the verifier must reject the post-boundary tokens (which depend on an unobserved tool result), and the runtime must execute the tool before generation can resume. This creates a particularly costly form of rejection: not only are the post-boundary draft tokens wasted, but the serial tool-execution latency is added to the critical path.

We propose a simple intervention: a *non-speculate gate* that predicts the distance to the nearest action boundary and caps the draft length so that generation stops before the boundary is reached. The verifier remains authoritative for all accepted tokens, so output quality is preserved; the intervention targets systems efficiency alone.

This paper reports results from a controlled Monte Carlo simulation that models agent token streams with explicit action boundaries. We do not benchmark a real LLM draft/verifier pair. The simulation answers the question: under plausible action-boundary conditions and predictor quality, can a boundary gate improve useful-token throughput or reduce wasted draft compute relative to fixed-depth speculative decoding?

## Method

### Simulator

We implemented a reproducible Monte Carlo simulator (`scripts/tool_boundary_sd_sim.py`) that models an agent token stream as a sequence of segments separated by action boundaries. Each segment's length is drawn from an exponential distribution with a configurable mean. Within each segment, token acceptance follows a Bernoulli process with probability $p_{\text{normal}}$. Near an action boundary (within a configurable window), acceptance probability drops to a floor $p_{\text{boundary}}$, modeling the increased rejection rate when the draft approaches a tool-call invocation that depends on an unavailable external result.

### Policies

Four drafting policies were compared:

1. **Static** — Fixed-depth speculative decoding with draft length $\gamma = 8$. One drafter, one verifier call per step.
2. **Adaptive acceptance** — Naive online gamma adaptation: the draft length is adjusted based on recent acceptance rates, without boundary information.
3. **Boundary gate** — Fixed $\gamma = 8$ capped by the predicted distance to the nearest action boundary. If the boundary predictor estimates $d$ tokens to the next boundary, the draft length is $\min(\gamma, d)$.
4. **Adaptive boundary gate** — Combines naive acceptance-based gamma adaptation with the boundary cap.

### Cost Model

The per-step cost is:

$$C_{\text{step}} = C_{\text{verifier}} + C_{\text{draft}}$$

where:

$$C_{\text{verifier}} = 1.0 + 0.05 \times n_{\text{drafted}}$$

$$C_{\text{draft}} = 0.08 \times n_{\text{drafted}}$$

Useful-token throughput is defined as the number of accepted tokens that contribute to the final output divided by total cost. Waste rate is the fraction of drafted tokens that are rejected by the verifier.

### Boundary Predictor Model

The boundary predictor is modeled with configurable recall and false-positive rate. When a boundary exists within the draft window, the predictor detects it with probability equal to the recall parameter. False positives cause the gate to cap the draft length prematurely, reducing speculation depth when no boundary is near.

### Default Parameters

| Parameter | Value |
|---|---|
| Draft length ($\gamma$) | 8 |
| Normal token acceptance probability | 0.90 |
| Near-boundary acceptance probability floor | 0.38 |
| Boundary predictor recall | 0.90 |
| Boundary predictor false-positive rate | 0.015 |
| Mean action segment length | 48 tokens |
| Runs | 500 |
| Useful tokens per run | 4,096 |

### Sensitivity Sweep

We varied mean segment length (16, 32, 48, 96, 192 tokens) and boundary predictor recall (0.5, 0.7, 0.9, 1.0) to characterize the conditions under which the gate provides meaningful benefit.

### Environment

All runs were CPU-only. The machine reported an NVIDIA GB10 GPU with 0% compute utilization during the run. RAM: 121 GiB total, 116 GiB available. Swap disabled. earlyoom active. Python 3.12.3. Environment details were captured in `logs/calibration_env.log`.

This is a controlled systems simulation, not an LLM benchmark. No GPU compute was used.

## Results

### Main Results

Under the default condition (mean segment length 48 tokens, 90% boundary recall), the four policies produced the following outcomes over 500 runs of 4,096 useful tokens each:

| Policy | Useful tok/time | Δ speed vs static | Waste rate | Δ waste vs static | Boundary-cross waste/run |
|---|---:|---:|---:|---:|---:|
| Static | 1.9781 | 0.0% | 0.4614 | 0.0% | 320.6 |
| Boundary gate | 2.1088 | +6.61% | 0.3745 | −18.83% | 32.8 |
| Adaptive acceptance | 1.7323 | −12.43% | 0.3664 | −20.58% | 189.0 |
| Adaptive boundary gate | 1.8527 | −6.34% | 0.3316 | −28.14% | 23.5 |

The boundary gate nearly eliminated boundary-crossing waste (320.6 → 32.8 wasted tokens per run, an 89.8% reduction in this specific waste category) and improved useful throughput by 6.6%. However, it did not meet the pre-registered success threshold of ≥15% speedup. It approached but did not clearly exceed the ≥20% wasted-compute reduction threshold (achieving 18.8%).

The naive acceptance-based adaptive controller reduced waste but regressed throughput by 12.4%, because it over-shrank the draft length and increased verifier-call frequency. This policy should not be used as implemented.

The combined adaptive boundary gate achieved the largest waste reduction (28.1%) but still regressed throughput (−6.3%) due to the acceptance-adaptation component's tendency to reduce draft depth.

### Sensitivity Results

At 90% boundary recall, the simple boundary gate's benefit varied with mean segment length:

| Mean segment length | Δ speed vs static | Δ waste vs static |
|---:|---:|---:|
| 16 | +15.35% | −30.29% |
| 32 | +9.33% | −23.47% |
| 48 | +6.52% | −18.77% |
| 96 | +3.54% | −11.96% |
| 192 | +1.69% | −6.97% |

The boundary gate meets both the speed and waste thresholds when tool boundaries are frequent (mean ≤ 16 tokens between boundaries). It clears the waste threshold but not the speed threshold at mean 32 tokens. Benefits decay monotonically as boundaries become sparser, because fixed-depth speculation already amortizes verifier calls well over long natural-language spans.

The adaptive boundary gate showed a different trade-off profile: at mean segment 16, it achieved a larger waste reduction (−44.0%) but a smaller speed improvement (+3.6%) than the simple boundary gate, and at longer segments it regressed throughput (−3.8% at 32, −6.3% at 48, −9.3% at 96, −11.1% at 192).

## Limitations

1. **No real LLM benchmark.** The simulator models token acceptance and boundary detection as stochastic processes with assumed parameters. No real draft/verifier model pair was benchmarked. The acceptance probabilities, cost coefficients, and boundary predictor quality are all assumptions, not measurements.

2. **No real tool-agent trace distribution.** The mean segment length and boundary frequency were swept parametrically. The actual distribution of tool-call intervals in production agent workloads is unknown and may differ substantially from the exponential model used here.

3. **Predictor quality is assumed.** Boundary predictor recall (0.90) and false-positive rate (0.015) were set, not measured against a real boundary detector. A real predictor's quality will depend on the agent's tool-calling patterns and the detection method used.

4. **Cost model is simplified.** The linear cost model ($C_{\text{verifier}} = 1.0 + 0.05 \times n_{\text{drafted}}$, $C_{\text{draft}} = 0.08 \times n_{\text{drafted}}$) abstracts away hardware-specific latency, memory hierarchy effects, and batch scheduling. Real speculative decoding systems may exhibit different cost structures.

5. **Tool-execution latency is not modeled.** The simulator accounts for wasted draft tokens at boundaries but does not model the serial latency of tool execution itself, which would further penalize boundary-crossing drafts in practice.

6. **Default condition does not meet the speed threshold.** Under the default medium-boundary setting (mean 48 tokens), the boundary gate improved speed by only 6.6%, below the 15% target. The result should not be treated as evidence of ≥15% production speedup until validated on real traces.

7. **Naive acceptance adaptation is a negative result.** The acceptance-based adaptive policy regressed throughput in all tested conditions. This finding is specific to the implemented controller; more sophisticated cost-aware adaptation may perform differently.

8. **Claim audit is incomplete.** The project's claim ledger contains no structured claims linked to public evidence files, and its audit status is blocked. The numerical results reported here are drawn directly from simulator output logs and the machine-readable decision record, but no independent claim-level evidence audit has been completed.

## Reproducibility Checklist

- [x] Simulator source code included: `scripts/tool_boundary_sd_sim.py`
- [x] Simulator passes `py_compile` without errors
- [x] Smoke test (5 runs × 512 tokens) logged: `logs/smoke_tool_boundary_sd.log`
- [x] Main run (500 runs × 4,096 tokens) logged: `logs/main_tool_boundary_sd.log`
- [x] Sensitivity sweep logged: `logs/sensitivity_tool_boundary_sd.log`
- [x] Environment calibration logged: `logs/calibration_env.log`
- [x] Raw results: `results/main_tool_boundary_sd_raw.csv`
- [x] Summary results: `results/main_tool_boundary_sd_summary.csv`, `results/main_tool_boundary_sd_summary.json`
- [x] Sensitivity results: `results/sensitivity_summary.csv`, `results/sweep_*_summary.json/csv`
- [x] Machine-readable decision: `.omx/project_decision.json`
- [x] All random seeds and parameters are specified in the simulator source and logs
- [x] No GPU compute was used; all runs are CPU-reproducible
- [ ] Real LLM benchmark: not performed
- [ ] Real tool-agent trace validation: not performed
- [ ] Structured claim audit: blocked (claim ledger empty)

## Conclusion

A non-speculate gate that caps speculative draft length at predicted action boundaries can reduce wasted draft compute and improve useful-token throughput in agent workloads with frequent tool calls. Under synthetic conditions with mean 16 tokens between boundaries and 90% boundary-predictor recall, the gate achieves 15.3% speedup and 30.3% waste reduction relative to fixed-depth speculative decoding. Under a medium-density default (mean 48 tokens), the gate provides a more modest 6.6% speedup and 18.8% waste reduction—beneficial but below the pre-registered success thresholds.

The mechanism's value is therefore conditional on workload characteristics: it is most effective when tool boundaries are frequent and predictable, and its benefits decay quickly as boundaries become sparse. Naive acceptance-based gamma adaptation without boundary awareness should be avoided, as it regresses throughput by increasing verifier-call frequency.

The central remaining question is whether real tool-using agent workloads exhibit boundary densities in the regime where the gate provides meaningful benefit. We recommend instrumenting a real tool-using agent runtime to log token positions of tool-call starts, tool-call spans, tool execution starts, accepted speculative lengths, and rejected draft tokens, then replaying those traces through the simulator's cost model before integrating a gate into a production speculative decoding pipeline.

## Referenced Artifacts

| Artifact | Description |
|---|---|
| `scripts/tool_boundary_sd_sim.py` | Monte Carlo simulator source |
| `logs/smoke_tool_boundary_sd.log` | Smoke test output (5 runs × 512 tokens) |
| `logs/calibration_env.log` | GB10 / memory / earlyoom environment calibration |
| `logs/main_tool_boundary_sd.log` | Main benchmark output (500 runs × 4,096 tokens) |
| `logs/sensitivity_tool_boundary_sd.log` | Sensitivity sweep output |
| `results/main_tool_boundary_sd_raw.csv` | Raw per-run results |
| `results/main_tool_boundary_sd_summary.csv` | Aggregated summary |
| `results/main_tool_boundary_sd_summary.json` | Aggregated summary (JSON) |
| `results/sensitivity_summary.csv` | Sensitivity sweep summary |
| `results/sweep_*_summary.json/csv` | Per-sweep summary files |
| `.omx/project_decision.json` | Machine-readable decision record |
| `run_notes.md` | Research run notes |
