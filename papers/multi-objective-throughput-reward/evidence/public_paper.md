# Multi-Objective Throughput Reward for LLM Serving Controllers: Trading Peak Tokens/Second for Operational Safety

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts (simulation scripts, telemetry logs, statistical analysis outputs, and structured decision records). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

LLM serving controllers that optimize raw tokens/sec tend to select aggressive concurrency and batch-size settings, achieving high throughput at the cost of elevated latency, memory pressure, out-of-memory events, and poor request fairness. We investigate a multi-objective reward function that penalizes constraint violations alongside throughput, comparing it against throughput-only and throughput-plus-latency rewards in a synthetic GB10-like serving controller benchmark. Across 120 independent seeds and 120 epochs per seed (50-epoch tail analysis), the multi-objective reward reduced latency violation rates by 92.5%, low-memory violation rates by 92.7%, and OOM-event rates by 90.1% relative to throughput-only reward, while improving Jain fairness by 8.6% and evaluation utility by 24.7%. The throughput cost was 17.1% fewer tokens/sec. Seed-paired analysis confirmed a utility improvement of +0.115 absolute (95% CI [+0.102, +0.128]). These results are limited to a synthetic controller environment with hand-set reward weights and have not been validated against live serving backends or real request traces.

## Introduction

Throughput maximization is a natural objective for LLM serving controllers. However, raw tokens/sec is an incomplete proxy for operational utility: aggressive concurrency and batch-size configurations that maximize throughput can simultaneously degrade tail latency, exhaust memory headroom, trigger out-of-memory errors, and distribute service unfairly across requests. A controller that converges to such configurations may appear performant on a single metric while being operationally unsafe.

The central hypothesis of this work is that a multi-objective throughput reward—one that trades some peak throughput for constraint satisfaction across latency, memory headroom, error rates, and fairness—will yield higher operational utility and far fewer constraint violations than a throughput-only reward, with an acceptable throughput penalty.

We operationalize this hypothesis as a reward-shaping experiment in a synthetic serving controller that selects (max_concurrency, batch) actions under a GB10-like resource profile. We compare three reward functions of increasing constraint awareness and report on their convergence behavior, constraint violation rates, and overall utility. The experiment is deliberately synthetic: it tests reward geometry and controller selection behavior before committing to long live-serving runs on physical hardware.

## Method

### Environment and Assumptions

The experiment uses a dependency-free simulator (`scripts/throughput_reward_sim.py`) modeling a GB10-class LLM serving controller. The host environment (recorded in `logs/environment_telemetry.log`) reports an NVIDIA GB10 GPU, approximately 117 GiB available system memory, zero swap, and idle GPU utilization prior to the run. The simulator models the relationship between concurrency/batch actions and observable metrics—tokens/sec, p95 latency, memory headroom, OOM/error events, and Jain fairness index—using GB10-calibrated response surfaces. The memory and OOM model is calibrated to the observed hardware profile but is not fitted to measured KV-cache allocation curves from a live backend.

### Action Space

The controller selects discrete actions of the form `(max_concurrency, batch_size)`, denoted e.g., `c14_b28`, `c12_b24`, `c8_b16`, `c10_b20`. Higher concurrency and batch values yield greater throughput but increase latency, memory pressure, and error risk in the simulated environment.

### Reward Functions

Three reward functions were compared:

1. **throughput_only**: Raw `tokens_per_s`. No penalty terms.
2. **throughput_latency**: Normalized throughput minus a p95-latency penalty. Intermediate constraint awareness.
3. **multi_objective**: Normalized throughput minus penalties for:
   - p95 latency exceeding 4.5 s
   - Memory headroom below 12 GiB
   - Error rate / OOM events
   - Jain fairness index below 0.92

All reward weights are hand-set. An evaluation-only utility function (not visible to the controller during action selection) computes the ground-truth operational utility incorporating all constraint dimensions.

### Controller

The controller uses initial action coverage followed by UCB-like online selection. Each epoch, the controller observes metrics for its chosen action and updates its reward estimates. The experiment measures behavior in the tail epochs after the controller has had sufficient experience to differentiate actions.

### Experimental Protocol

A smoke test was executed first (`--smoke`), followed by the calibrated full run:

```
python3 scripts/throughput_reward_sim.py --seeds 120 --epochs 120 --tail 50 \
    --outdir results/throughput_reward_full
```

This produces 120 independent seeds × 120 epochs per reward function, with analysis restricted to the final 50 epochs per seed (the tail where the controller has converged). Post-hoc analysis was performed with:

```
python3 scripts/analyze_results.py results/throughput_reward_full/epoch_metrics.csv \
    --tail 50 --out results/throughput_reward_full/analysis.json
```

Both scripts were syntax-verified via `py_compile`.

## Results

### Aggregate Tail-Epoch Metrics

Table 1 reports mean metrics across the final 50 epochs of 120 seeds for each reward function.

**Table 1.** Tail-epoch aggregate metrics (120 seeds × 50 epochs/seed).

| Reward | Mean tok/s | Mean p95 latency (ms) | Latency violation rate | Low-mem violation rate | OOM event rate | Jain fairness | Utility |
|---|---:|---:|---:|---:|---:|---:|---:|
| throughput_only | 2210.8 | 4175.4 | 0.317 | 0.270 | 0.111 | 0.817 | 0.466 |
| throughput_latency | 2188.4 | 4031.7 | 0.219 | 0.172 | 0.078 | 0.827 | 0.503 |
| multi_objective | 1833.1 | 3345.6 | 0.024 | 0.020 | 0.011 | 0.887 | 0.581 |

### Multi-Objective vs. Throughput-Only Deltas

Relative to throughput-only reward, the multi-objective reward produced:

- **Tokens/sec:** −17.1% (−377.8 tok/s absolute)
- **Mean p95 latency:** −19.9% (−829.9 ms absolute)
- **Latency violation rate:** −92.5%
- **Low-memory violation rate:** −92.7%
- **OOM event rate:** −90.1%
- **Jain fairness:** +8.6% (+0.070 absolute)
- **Evaluation utility:** +24.7%

The throughput-latency reward was intermediate on all metrics, reducing some violations relative to throughput-only but leaving materially higher memory and OOM risk than the full multi-objective reward. This pattern suggests that penalizing latency alone is insufficient to control memory-related constraint violations.

### Seed-Paired Statistical Analysis

Seed-paired analysis (recorded in `results/throughput_reward_full/analysis.json`) found:

- Utility improvement: +0.1149 absolute (95% CI [+0.1019, +0.1280])
- p95 latency reduction: −829.9 ms
- OOM-event rate reduction: −0.1002 absolute
- Jain fairness improvement: +0.0703 absolute
- Throughput cost: −377.8 tok/s (−17.1%)

The confidence interval for utility improvement excludes zero by a substantial margin, supporting the claim that the multi-objective reward yields higher operational utility under the simulated conditions. However, the magnitude of this improvement depends on the specific utility function construction, which is itself synthetic (see Limitations).

### Convergence Behavior

The throughput-only reward converged predominantly to aggressive actions (`c14_b28`, `c12_b24`), which maximize raw tokens/sec but frequently violate latency, memory, and fairness constraints. The multi-objective reward converged to safer actions (`c8_b16`, `c10_b20`), accepting lower throughput to maintain constraint satisfaction. The throughput-latency reward fell between these extremes. This divergence in action selection is the primary mechanism behind the observed metric differences: the reward functions are steering the controller toward different regions of the action space, and the multi-objective reward's preferred region happens to have far fewer constraint violations at moderate throughput cost.

## Limitations

1. **Synthetic environment.** The simulator uses GB10-calibrated response surfaces, not measurements from a live vLLM or llama.cpp serving backend. The memory and OOM model does not incorporate measured KV-cache allocation curves. Results characterize reward geometry and controller selection behavior, not production serving performance.

2. **Hand-set reward weights.** The penalty thresholds (p95 latency > 4.5 s, memory headroom < 12 GiB, fairness < 0.92) and weight magnitudes were chosen by the experimenter. A production deployment should sweep or learn these weights against workload-specific service-level objectives. The observed improvement magnitudes are contingent on these choices.

3. **No real request traces.** The experiment uses synthetic workload generation rather than replayed production traces. Request arrival patterns, prompt-length distributions, and generation-length distributions may differ materially from real workloads, potentially changing which action region is optimal.

4. **Single hardware profile.** All results are specific to a GB10-like memory and compute profile. Generalization to other GPU classes or memory configurations is not established.

5. **Evaluation utility is synthetic.** The ground-truth utility function used for evaluation is itself a constructed metric. Whether it corresponds to operator preferences in production is unvalidated. The large utility improvement partly reflects the fact that the multi-objective reward's penalty terms align with the evaluation utility's construction, which may constitute a form of reward hacking rather than genuine operational improvement.

6. **Notion page content unavailable.** The project's Notion page was reachable only as an HTML shell; no structured requirements or prior results beyond the prompt metadata were available as local evidence.

7. **No reward-weight sensitivity analysis.** The robustness of the multi-objective advantage to variations in penalty thresholds and weight magnitudes has not been tested. It is possible that small changes in weights could substantially alter the trade-off surface.

## Reproducibility Checklist

- [x] Simulation script available: `scripts/throughput_reward_sim.py`
- [x] Analysis script available: `scripts/analyze_results.py`
- [x] Both scripts pass `py_compile` syntax verification
- [x] Random seeds explicitly parameterized (120 seeds)
- [x] Full epoch-level metrics recorded: `results/throughput_reward_full/epoch_metrics.csv`
- [x] Paired statistical analysis output: `results/throughput_reward_full/analysis.json`
- [x] Run summaries recorded: `results/throughput_reward_smoke/summary.json`, `results/throughput_reward_full/summary.json`
- [x] Environment telemetry logged: `logs/environment_telemetry.log`
- [x] Full execution log captured: `logs/throughput_reward_full.log`
- [x] Smoke test log captured: `logs/throughput_reward_smoke.log`
- [x] Hardware profile documented (NVIDIA GB10, ~117 GiB RAM, zero swap)
- [x] Python version recorded in telemetry log
- [x] Command lines for all runs documented in run notes
- [ ] Live serving backend validation (not performed; recommended next step)
- [ ] Reward-weight sensitivity sweep (not performed)

## Conclusion

A multi-objective throughput reward that penalizes latency violations, low memory headroom, OOM events, and fairness degradation substantially outperformed a throughput-only reward on operational utility (+24.7%, paired 95% CI excluding zero) in a 120-seed synthetic GB10-like serving controller benchmark. The improvement came at a −17.1% throughput cost and was accompanied by reductions exceeding 90% in latency, memory, and OOM violation rates, plus an 8.6% fairness improvement.

These results support the hypothesis that multi-objective reward shaping is viable for safe sustained serving throughput, but they are confined to a synthetic controller environment with hand-set weights. The claim is scoped to reward geometry and controller action selection, not to production serving performance. The alignment between the multi-objective reward's penalty terms and the evaluation utility's construction warrants caution in interpreting the utility improvement magnitude. Scientific closure requires replaying real or generated request traces through an actual local serving backend (e.g., vLLM or llama.cpp), fitting memory and latency curves from measured data, shadow-testing the multi-objective reward against live workload conditions, and performing a reward-weight sensitivity sweep to establish robustness.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Simulation script | `scripts/throughput_reward_sim.py` |
| Analysis script | `scripts/analyze_results.py` |
| Smoke test log | `logs/throughput_reward_smoke.log` |
| Full run log | `logs/throughput_reward_full.log` |
| Environment telemetry | `logs/environment_telemetry.log` |
| Smoke test summary | `results/throughput_reward_smoke/summary.json` |
| Full run summary | `results/throughput_reward_full/summary.json` |
| Full epoch metrics | `results/throughput_reward_full/epoch_metrics.csv` |
| Paired statistical analysis | `results/throughput_reward_full/analysis.json` |
| Project decision record | `.omx/project_decision.json` |
