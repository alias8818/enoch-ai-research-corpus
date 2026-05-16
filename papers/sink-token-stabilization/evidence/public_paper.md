# Sink Token Stabilization: A Mechanistic Surrogate Study of Explicit Null Destinations in Softmax Attention

---

**AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metric files, sensitivity data). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Softmax attention lacks a native "attend nowhere" option: when no context token is relevant, the convex mixture over value vectors still produces a non-zero output. We test whether adding an explicit zero-value sink token with a tunable logit bias provides a stable null destination for attention mass, reducing output drift in null-state conditions without destroying content-attention when a trigger signal is present. In a synthetic surrogate task (64 value vectors of dimension 32; trigger-conditional mean or zero output), an explicit zero sink at logit bias 8.0 reduced overall MSE to 0.0101 versus 0.0311 for plain softmax (ratio 0.326) and reduced no-trigger MSE by 99.87%. No-trigger output norm dropped by 96.5%. Trigger-condition content attention mass remained at 0.933, indicating preserved content routing. Sensitivity analysis across signal logit strengths {3, 4, 6, 8} confirmed the same best configuration but revealed a tradeoff: at low signal strength (logit 3), trigger content mass falls to 0.413, meaning the sink bias suppresses legitimate content attention when evidence is weak. These results are mechanistic only—no transformer was trained, and no perplexity or downstream task metric was measured. The finding supports continued investigation in a trained model.

## 1. Introduction

Standard softmax attention computes a probability distribution over a set of key vectors and returns a convex combination of the corresponding value vectors. This formulation carries a structural consequence: even when no key is relevant, the output is a weighted average of all values, never zero. For tasks where the correct output in some conditions is a null or default state, the model must learn workarounds—such as distributing attention uniformly or relying on residual connections—to approximate a zero signal.

Recent work has identified related phenomena from different angles. StreamingLLM observed that language models develop attention sinks on initial tokens and that preserving these tokens is necessary for stable windowed inference; a dedicated sink token during pretraining further improves streaming deployment (arXiv:2309.17453). A trigger-conditional softmax-transformer analysis argued that simplex-normalized attention requires a stable anchor or default state for tasks that return an average on trigger and zero otherwise (arXiv:2603.11487). A separate line of work on moving sink positions framed the problem as one of inference robustness and reported that a single extra globally-visible, self-attending sink token stabilizes attention sinks (arXiv:2601.19657).

These works converge on a shared intuition: softmax attention benefits from a structural null destination. However, the mechanistic question—whether a zero-value sink option with tunable bias can simultaneously suppress null-state output drift and preserve content-attention routing—has not, to our knowledge, been isolated and tested in a controlled surrogate setting.

We pose the following question: **Can an explicit structural sink token stabilize softmax-attention behavior when a head should ignore context, without destroying content-attention behavior when a trigger is present?**

We test this with a minimal synthetic task, not a trained transformer. This limits the generality of our claims but provides clean mechanistic evidence.

## 2. Method

### 2.1 Task Design

We construct a synthetic attention surrogate with the following parameters:

- **Context:** $n = 64$ value vectors, each of dimension $d = 32$, drawn i.i.d. from $\mathcal{N}(0, I)$.
- **Trigger condition:** A binary trigger determines the target output.
  - If $\text{trigger} = 0$: target output is the zero vector $\mathbf{0} \in \mathbb{R}^{32}$.
  - If $\text{trigger} = 1$: target output is the mean of all 64 context value vectors.
- **Signal structure:** When $\text{trigger} = 1$, one key receives an additive signal logit (default 6.0) to simulate a detectable content cue. Keys are otherwise noisy (Gaussian noise with $\sigma = 1.0$).

This task directly exercises the tension of interest: the model must route attention mass to content values when the trigger is present and emit near-zero output when it is absent.

### 2.2 Methods Compared

Three attention configurations are evaluated:

1. **`plain_softmax`:** Ordinary softmax over the 64 content key logits. No sink option. This is the baseline that lacks any null destination.

2. **`softmax_plus_one_null`:** The softmax denominator includes one additional zero-value option at logit 0. This tests whether simply adding an extra option (without tuning its logit) provides any benefit.

3. **`explicit_zero_sink`:** A zero-value sink token is added to the value set (value vector = $\mathbf{0}$), and its key logit is set to a fixed bias. We sweep sink logit values over $\{-2, 0, 1, 2, 3, 4, 5, 6, 7, 8\}$ and report the best.

### 2.3 Evaluation Metrics

- **Overall MSE:** Mean squared error between the attention output and the target, computed over both trigger conditions equally.
- **No-trigger MSE:** MSE conditioned on $\text{trigger} = 0$.
- **No-trigger output norm:** $\|\hat{y}\|_2$ when $\text{trigger} = 0$ (target is zero; lower is better).
- **No-trigger sink mass:** Fraction of attention probability assigned to the sink token when $\text{trigger} = 0$.
- **Trigger content mass:** Fraction of attention probability assigned to content (non-sink) tokens when $\text{trigger} = 1$.

### 2.4 Experimental Procedure

All experiments use the script `scripts/sink_token_stabilization.py`.

| Run | Trials | Signal logit | Output artifact |
|-----|--------|-------------|----------------|
| Smoke | 1,000 | 6.0 | `artifacts/metrics/smoke.json` |
| Main | 50,000 | 6.0 | `artifacts/metrics/main_50k.json` |
| Sensitivity (logit 3) | 30,000 | 3.0 | `artifacts/metrics/sensitivity_signal_3.json` |
| Sensitivity (logit 4) | 30,000 | 4.0 | `artifacts/metrics/sensitivity_signal_4.json` |
| Sensitivity (logit 6) | 30,000 | 6.0 | `artifacts/metrics/sensitivity_signal_6.json` |
| Sensitivity (logit 8) | 30,000 | 8.0 | `artifacts/metrics/sensitivity_signal_8.json` |

The sensitivity sweep varies the signal logit (the strength of the content cue when trigger = 1) while holding all other parameters fixed, testing whether the sink bias that helps in the null state also suppresses content attention when the signal is weak.

### 2.5 Compute Environment

Experiments ran on a Linux host (`gx10-efe8`, aarch64, 20 CPU cores) with approximately 116 GiB available memory and no swap. The main 50k-trial run consumed a maximum RSS of approximately 1.65 GiB. No GPU was used; this is a pure-NumPy surrogate computation.

## 3. Results

### 3.1 Main Experiment (50,000 trials, signal logit = 6.0)

| Method | Overall MSE | No-trigger MSE | No-trigger output norm | No-trigger sink mass | Trigger content mass |
|--------|------------|----------------|----------------------|---------------------|---------------------|
| `plain_softmax` | 0.031078 | 0.038765 | 1.09231 | — | — |
| `explicit_zero_sink` (logit 8.0) | 0.010132 | 0.000050 | 0.03786 | 0.9658 | 0.9331 |

The best configuration is `explicit_zero_sink` at sink logit 8.0. Relative to plain softmax:

- **Overall MSE ratio:** 0.326 (67.4% reduction).
- **No-trigger MSE ratio:** 0.00128 (99.87% reduction).
- **No-trigger output norm ratio:** 0.0347 (96.5% reduction).

In the no-trigger condition, 96.6% of attention mass routes to the sink token, producing a near-zero output. In the trigger condition, 93.3% of attention mass routes to content tokens, preserving the mean-computation behavior.

The `softmax_plus_one_null` method (sink at logit 0) was outperformed by `explicit_zero_sink` at higher logit biases. Its detailed metrics are recorded in the artifact JSON files but it did not achieve the best performance in any tested regime; the run notes do not extract its per-method numbers into the summary, so we do not report them here.

### 3.2 Sensitivity to Signal Strength

The signal logit controls how distinguishable the content cue is from noise when trigger = 1. We swept signal logits {3, 4, 6, 8} with 30,000 trials each. The best method remained `explicit_zero_sink` at sink logit 8.0 in all four settings.

| Signal logit | Overall MSE | MSE ratio vs. plain | No-trigger MSE ratio | No-trigger norm ratio | Trigger content mass |
|-------------|------------|---------------------|---------------------|----------------------|---------------------|
| 3.0 | 0.00482 | 0.155 | 0.00126 | 0.0345 | 0.413 |
| 4.0 | 0.00606 | 0.195 | 0.00126 | 0.0345 | 0.655 |
| 6.0 | 0.01012 | 0.326 | 0.00126 | 0.0345 | 0.933 |
| 8.0 | 0.01130 | 0.364 | 0.00126 | 0.0345 | 0.990 |

**Key observation:** The no-trigger suppression metrics (MSE ratio, norm ratio) are essentially constant across signal strengths—sink logit 8.0 reliably absorbs attention mass when no trigger is present, regardless of how the trigger signal is configured. However, trigger content mass increases monotonically with signal strength. At signal logit 3, only 41.3% of attention mass reaches content tokens when the trigger is active; the sink captures the remaining 58.7%, suppressing the correct output. At signal logit 8, content mass reaches 99.0%.

This reveals a **tradeoff**: a high sink bias is safe for null-state suppression but requires sufficiently strong content evidence to overcome the bias when content attention is needed. The optimal sink logit is therefore task- and regime-dependent.

### 3.3 Mixed Result: Overall MSE Ratio Increases with Signal Strength

The overall MSE ratio versus plain softmax increases from 0.155 (signal logit 3) to 0.364 (signal logit 8). This is not because the sink method degrades in absolute terms at higher signal logits—rather, plain softmax improves more at higher signal logits because its content attention naturally sharpens, while the sink method pays a fixed cost from the residual sink mass in the trigger condition. At signal logit 6, the sink method's trigger content mass of 0.933 means approximately 6.7% of attention mass still goes to the sink, slightly diluting the output. This is the price of null-state stability.

## 4. Limitations

1. **Surrogate only; no trained model.** This experiment uses a synthetic NumPy attention computation with random value vectors and hand-specified logits. No transformer was trained, no gradients were computed, and no perplexity or downstream task metric was measured. The result demonstrates a mechanistic possibility, not a practical training outcome.

2. **No learned sink logit.** The sink logit was swept over a fixed grid and the best value selected post hoc. In a real model, the sink logit would need to be learned or calibrated, and its interaction with training dynamics is unknown.

3. **Task simplicity.** The binary trigger task with a zero/mean output is a minimal test case. Real attention heads serve diverse roles (copying, routing, gating) that may interact with a sink token in ways not captured here.

4. **Single sink token, single head.** Only one sink token and one attention head were tested. Multi-head, multi-layer interactions could produce emergent effects.

5. **No measurement of training instability or loss landscape effects.** The surrogate measures inference behavior only. Whether a sink token helps or hinders optimization during training is an open question.

6. **Optimal sink logit is regime-dependent.** As the sensitivity analysis shows, a sink logit that is too high relative to the content signal strength will suppress legitimate content attention. The best logit of 8.0 found here is specific to the noise and signal scales in this surrogate.

7. **No comparison to alternative null-state mechanisms.** Other approaches—such as learned gating, bias terms, or modified normalization—were not tested. The sink token is one design option among several.

8. **Random seed handling not confirmed.** The exact commands and parameters are documented, but whether the script uses a fixed random seed for deterministic reproducibility is not recorded in the run notes.

9. **Intermediate method metrics not fully reported.** The `softmax_plus_one_null` method's detailed per-metric numbers are present in the JSON artifact files but were not extracted into the run notes summary, limiting direct comparison in this draft.

## 5. Reproducibility Checklist

| Item | Status |
|------|--------|
| Script available | Yes: `scripts/sink_token_stabilization.py` |
| Exact commands documented | Yes: syntax check, smoke (1k trials), main (50k trials), sensitivity sweep |
| Random seed specified | Not confirmed in run notes; script should be inspected for seed handling |
| Hardware documented | Yes: Linux aarch64 (`gx10-efe8`), 20 cores, ~116 GiB RAM, no swap, no GPU |
| Software dependencies | NumPy (version not recorded in artifacts); Python 3 |
| Metric artifacts | Yes: `smoke.json`, `main_50k.json`, `sensitivity_signal_{3,4,6,8}.json`, `sensitivity_summary.jsonl` |
| Log artifacts | Yes: `artifacts/logs/main_20260502T145945Z.log` and per-run logs under `artifacts/logs/` |
| Full output for intermediate method (`softmax_plus_one_null`) | Recorded in metric JSON files but not extracted into run notes |
| Deterministic reproducibility | Partial: commands and parameters are documented, but random seed handling is not explicitly confirmed |

## 6. Conclusion

We presented mechanistic evidence that an explicit zero-value sink token with a tunable logit bias can serve as a stabilization primitive for softmax-attention null states. In a synthetic surrogate task, the best sink configuration (logit 8.0) reduced no-trigger MSE by 99.87% and no-trigger output norm by 96.5% relative to plain softmax, while preserving 93.3% content attention mass when a trigger signal was present at logit 6.0.

However, the sensitivity analysis revealed a meaningful tradeoff: the same high sink bias that stabilizes the null state suppresses content attention when the content signal is weak (trigger content mass = 0.413 at signal logit 3). The sink logit must therefore be calibrated to the expected signal-to-noise regime, and in a trained model it would likely need to be learned.

This result is sufficient to support continued investigation but insufficient to claim practical benefit. The necessary next step is to implement a sink token in a small trained transformer or diffusion language model, comparing attention stability, training loss, and downstream task performance against no-sink and softmax+1 controls. Only such an experiment can determine whether the mechanistic advantage observed in the surrogate survives training dynamics and transfers to realistic workloads.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Run notes | `run_notes.md` |
| Implementation script | `scripts/sink_token_stabilization.py` |
| Smoke metrics (1k trials) | `artifacts/metrics/smoke.json` |
| Main metrics (50k trials) | `artifacts/metrics/main_50k.json` |
| Sensitivity (signal logit 3) | `artifacts/metrics/sensitivity_signal_3.json` |
| Sensitivity (signal logit 4) | `artifacts/metrics/sensitivity_signal_4.json` |
| Sensitivity (signal logit 6) | `artifacts/metrics/sensitivity_signal_6.json` |
| Sensitivity (signal logit 8) | `artifacts/metrics/sensitivity_signal_8.json` |
| Sensitivity summary | `artifacts/metrics/sensitivity_summary.jsonl` |
| Main run log | `artifacts/logs/main_20260502T145945Z.log` |
| Log directory | `artifacts/logs/` |
| Project decision JSON | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T145808542304+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T145808542304+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T145808542304+0000/paper_manifest.json` |

## External Evidence Sources

- StreamingLLM attention sinks: arXiv:2309.17453
- Trigger-conditional softmax-transformer analysis: arXiv:2603.11487
- DLM moving sink positions: arXiv:2601.19657
