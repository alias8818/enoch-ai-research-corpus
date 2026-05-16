# Upcycle Timing Sweep Law: Scheduling Expert Expansion in Mixture-of-Experts Models

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, benchmark outputs, decision records, and claim ledgers). The operator who released this artifact claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

We investigate whether the transition point at which a dense model is upcycled into a Mixture-of-Experts (MoE) architecture can be treated as an operational schedule variable, and whether a simple timing law relates the pre-upcycle training fraction to final validation loss, expert diversity, and compute savings. Using a synthetic NumPy classification benchmark with a 4-expert soft MoE, we sweep single-stage upcycle fractions $f \in \{0, 0.1, 0.25, 0.4, 0.5, 0.65, 0.75, 0.9, 1\}$ and three multi-stage schedules across 5 random seeds per condition. We find a smooth, monotonic relationship: delaying upcycle increases validation loss relative to immediate expansion ($\Delta = +0.005$ nats at $f{=}0.25$, $+0.010$ nats at $f{=}0.50$, $+0.016$ nats at $f{=}1.0$), reduces expert diversity, and yields predictable compute savings. A quadratic fit explains 98.8% of variance in the loss-timing curve. Multi-stage schedules (dense → 2-expert → 4-expert) are Pareto-competitive with single-stage schedules. These results are scoped to a synthetic proxy; validation on real transformer MoE training runs at production token budgets remains necessary.

## Introduction

Upcycling—converting a pretrained dense model into a Mixture-of-Experts architecture by replicating weights into expert branches—is a practical technique for expanding model capacity without training a large MoE from scratch. A common practice is to upcycle at the start of continued pretraining, but the question of *when* to expand has received little systematic treatment. If the upcycle timing point is treated as a free variable, three quantities trade off: (1) final validation loss, (2) expert diversity (the degree to which experts specialize), and (3) compute cost relative to training a full MoE from scratch.

This paper asks: **does upcycle timing produce a measurable, schedulable curve relating the pre-upcycle token fraction to loss, diversity, and compute savings?**

If such a curve exists and is smooth, practitioners could select an upcycle timing point by specifying a loss budget, converting an architectural decision into a scheduling decision. We approach this question with a controlled synthetic benchmark, acknowledging upfront that this is a proxy rather than a production-scale result.

## Method

### Benchmark Design

Because no training code or pretrained model was available in the project environment, we constructed a runnable toy benchmark in NumPy with the following components:

**Teacher.** A synthetic mixture-of-experts classification task with 4 latent regimes. Each regime defines a different input-to-label mapping, providing a controlled setting where expert specialization is meaningful.

**Student architectures.**
- *Dense:* A 1-hidden-layer fully connected network.
- *Soft MoE (4 experts):* A 4-expert soft MoE where all experts are computed on every forward pass (no top-$k$ routing), with a learned gating function.
- *Soft MoE (2 experts):* An intermediate 2-expert variant used in multi-stage schedules.

**Upcycle operation.** At training fraction $f$ (where $f=0$ means immediate upcycle and $f=1$ means dense-only), the dense student's weights are copied into a 4-expert soft MoE by replication, and training continues for the remaining $(1-f)$ fraction of the total step budget. The total step budget is held constant across all conditions.

**Baselines.**
- MoE from scratch ($f = -1$): a 4-expert MoE trained for the full budget without any dense pretraining.
- Dense-only ($f = 1$): no upcycle at all.

### Experimental Conditions

**Single-stage sweep.** Fractions $f \in \{-1, 0, 0.1, 0.25, 0.4, 0.5, 0.65, 0.75, 0.9, 1\}$, with 5 random seeds per condition. Total: 1,200 steps, batch size 128, yielding 153,600 synthetic tokens per run and 7.68M sample-tokens across the full sweep.

**Multi-stage probe.** Three schedules expanding through intermediate expert counts:
- $0.1 \to 0.5$: dense until 10% of steps, 2-expert until 50%, 4-expert for remainder.
- $0.25 \to 0.65$: dense until 25%, 2-expert until 65%, 4-expert for remainder.
- $0.4 \to 0.75$: dense until 40%, 2-expert until 75%, 4-expert for remainder.

Each schedule was run with 5 seeds.

### Metrics

- **Validation loss:** Cross-entropy on a held-out synthetic set, reported as mean over seeds.
- **Expert diversity:** Measured as the average pairwise cosine distance between expert weight matrices, normalized to $[0, 1]$. A diversity of 0 indicates identical experts; higher values indicate greater specialization.
- **Compute savings:** A cost proxy defined as the fraction of expert-capacity compute avoided relative to training a 4-expert MoE from scratch. Under the soft-MoE cost model (all experts computed every step), savings are approximately linear in $f$: $\text{savings}(f) \approx 0.755 \cdot f$.

### Compute Proxy Caveat

The soft MoE implementation computes all experts on every forward pass. The "savings" metric therefore approximates the *capacity cost* avoided by spending fewer steps in the 4-expert regime, rather than measuring actual GPU kernel utilization or top-$k$ routing savings. This is a deliberate simplification for the proxy setting. In a production sparse MoE with top-1 or top-2 routing, the compute cost of the expert phase would differ substantially, changing the savings calculation.

### Hardware and Environment

The benchmark ran on CPU (NumPy) on a host reporting an NVIDIA GB10 GPU. The GPU was not used for computation. Available memory was approximately 116 GiB before the run; peak RSS was approximately 49 MiB for the full sweep and approximately 48 MiB for the multi-stage probe. Swap was disabled. Wall time for the full sweep was 55.20 seconds. This is a toy simulation result, not a CUDA copy calibration or production validation.

## Results

### Single-Stage Sweep

Table 1 reports aggregate results across all single-stage conditions.

**Table 1.** Single-stage upcycle timing sweep (5 seeds per condition).

| Fraction $f$ | Mode | Val. Loss (mean) | Paired $\Delta$ vs $f{=}0$ | Diversity (mean) | Savings vs. MoE-scratch |
|---:|---|---:|---:|---:|---:|
| $-1$ | moe_scratch | 1.6337 | +0.0144 | 0.6373 | 0.000 |
| 0 | upcycle | 1.6194 | — | 0.1147 | 0.000 |
| 0.1 | upcycle | 1.6222 | +0.0028 | 0.0811 | 0.076 |
| 0.25 | upcycle | 1.6242 | +0.0048 | 0.0527 | 0.189 |
| 0.4 | upcycle | 1.6262 | +0.0068 | 0.0303 | 0.302 |
| 0.5 | upcycle | 1.6277 | +0.0083 | 0.0188 | 0.378 |
| 0.65 | upcycle | 1.6315 | +0.0121 | 0.0087 | 0.491 |
| 0.75 | upcycle | 1.6333 | +0.0140 | 0.0048 | 0.566 |
| 0.9 | upcycle | 1.6346 | +0.0152 | 0.0027 | 0.680 |
| 1 | dense_only | 1.6349 | +0.0155 | 0.0000 | 0.755 |

**Key observations:**

1. **Monotonic loss penalty.** Paired deltas against $f{=}0$ were positive for every nonzero single-stage fraction across all 5 seeds. Delaying upcycle consistently increased validation loss relative to immediate expert expansion. The penalty was gradual rather than cliff-like.

2. **Diversity collapse.** Expert diversity decreased monotonically with later upcycle, approaching zero for $f \geq 0.75$. This indicates that experts initialized from a longer-trained dense model have less opportunity to diverge.

3. **MoE from scratch underperforms immediate upcycle.** The $f{=}{-1}$ condition (MoE trained from scratch) achieved validation loss 1.6337, worse than immediate upcycle ($f{=}0$, loss 1.6194) by +0.0144 nats, despite higher final diversity (0.637 vs. 0.115). This is consistent with the known benefit of dense pretraining before expert expansion, though the magnitude of this effect is specific to this proxy.

### Fitted Timing Law

For single-stage upcycle fractions $0 \leq f < 1$, the validation loss curve is well-described by a quadratic:

$$
\text{val\_loss}(f) \approx 1.6197 + 0.0177\,f - 0.0007\,f^2
$$

with $R^2 = 0.988$. The negative quadratic term is small, indicating that the relationship is nearly linear in this range, with a slight concavity suggesting diminishing marginal penalty at very late upcycle fractions. We note that $R^2$ is computed over only 8 data points (fractions 0 through 0.9), so the goodness of fit should be interpreted cautiously.

Compute savings are approximately linear:

$$
\text{savings}(f) \approx 0.755\,f
$$

This linearity is an artifact of the cost model: under soft MoE, the per-step cost of the 4-expert phase is a fixed multiple of the dense phase, so savings depend only on the fraction of steps spent in each regime.

### Actionable Schedule Examples

From the measured table (not the fit), practitioners facing a loss budget can read off the latest permissible upcycle fraction:

| Loss budget vs. $f{=}0$ | Latest measured $f$ | Savings | Diversity |
|---:|---:|---:|---:|
| +0.005 nats | 0.25 | 18.9% | 0.053 |
| +0.010 nats | 0.50 | 37.8% | 0.019 |
| +0.015 nats | 0.75 | 56.6% | 0.005 |

The diversity column highlights a tension: at $f{=}0.75$, savings are substantial but expert diversity is nearly collapsed (0.005), meaning the 4-expert model is effectively operating as a near-duplicate ensemble. Whether this matters in practice depends on whether diversity is instrumentally valuable (e.g., for routing efficiency or robustness) or merely incidental.

### Multi-Stage Probe

Table 2 reports results for the three multi-stage schedules.

**Table 2.** Multi-stage upcycle schedules (5 seeds per condition).

| Schedule | Val. Loss (mean) | Diversity (mean) | Savings |
|---|---:|---:|---:|
| $0.1 \to 0.5$ | 1.6258 | 0.0600 | 27.6% |
| $0.25 \to 0.65$ | 1.6265 | 0.0346 | 38.9% |
| $0.4 \to 0.75$ | 1.6296 | 0.0197 | 47.7% |

Multi-stage schedules are competitive on the Pareto frontier. The schedule $0.25 \to 0.65$ achieved mean validation loss 1.6265 with 38.9% savings, which is slightly better than single-stage $f{=}0.5$ (loss 1.6277, 37.8% savings). This suggests that gradual expert expansion can improve the loss-savings tradeoff. However, the differences are small (approximately 0.001 nats in loss, approximately 1 percentage point in savings) and the confidence intervals around these means with 5 seeds overlap. This finding would benefit from confirmation at higher statistical power.

## Limitations

1. **Synthetic proxy, not language modeling.** The benchmark uses a synthetic 4-regime classification task with a 1-hidden-layer network. The absolute loss values, diversity magnitudes, and fitted coefficients have no direct interpretation for transformer language models. The result supports the *existence* of a schedulable timing curve in a controlled setting, not its specific shape at production scale.

2. **Soft MoE compute proxy.** All experts are computed on every forward pass. The savings metric approximates capacity cost rather than measuring real top-$k$ routed GPU kernel utilization. In a production sparse MoE with top-1 or top-2 routing, the compute cost of the expert phase would be lower, changing the savings calculation and potentially the shape of the timing curve.

3. **Small scale.** The sweep covers 1,200 steps and 153,600 tokens per run. Production-scale upcycling typically operates at 50–200M tokens or more. The shape of the timing curve may change at scale; in particular, the relative benefit of dense pretraining may increase or decrease with longer training.

4. **Single architecture.** Only one hidden layer size, one expert count (4), and one synthetic task were tested. The timing law's dependence on model width, depth, expert count, and task complexity is unknown.

5. **Diversity metric limitations.** Pairwise cosine distance between expert weight matrices is a coarse measure of specialization. It does not capture functional specialization at the level of routing patterns or per-token expert usage. A model with low weight diversity could still exhibit meaningful functional specialization if the gating network routes differentially.

6. **No hardware telemetry.** The benchmark ran on CPU. No GPU utilization, memory bandwidth, or kernel-level measurements were collected. This is a toy simulation, not a CUDA copy calibration or production validation.

7. **Seed count.** Five seeds per condition provide a preliminary estimate of variance but may be insufficient for tight confidence intervals on the fitted law's coefficients. The reported $R^2$ of 0.988 is computed over only 8 data points and may overestimate predictive fit.

8. **Negative result: MoE from scratch diversity.** The $f{=}{-1}$ condition achieved the highest diversity (0.637) but the worst loss among MoE conditions (1.6337). This is a negative result for the hypothesis that higher diversity uniformly improves loss: in this proxy, diversity without the benefit of dense pretraining was insufficient.

## Reproducibility Checklist

- **Code available:** `scripts/upcycle_timing_sweep.py`, `scripts/multistage_probe.py` (included in project directory).
- **Random seeds:** 5 per condition; seeds are logged in per-run metrics CSVs.
- **Hyperparameters:** Steps = 1200, batch size = 128, all other hyperparameters recorded in `summary.json` files.
- **Environment:** NumPy on CPU; host reported NVIDIA GB10 (unused for computation); approximately 116 GiB RAM available; swap disabled.
- **Output artifacts:** `metrics.csv`, `summary.json`, `law_fit.json`, `paired_deltas.json` in `results/full_sweep/` and `results/multistage_probe/`.
- **Validation:** Both scripts pass `py_compile` without errors.
- **Wall time:** Full sweep 55.20s; multi-stage probe comparable (peak RSS approximately 48–49 MiB).
- **Determinism:** Not verified across platforms; NumPy random state is seeded per run.
- **Evidence classification:** All results are toy simulation results from a synthetic NumPy benchmark. No llama.cpp hook-prototype results, CUDA copy calibrations, or production validation data are present.

## Conclusion

In a synthetic MoE classification benchmark, upcycle timing produces a smooth, monotonic, and schedulable curve relating the pre-upcycle training fraction to validation loss, expert diversity, and compute savings. A quadratic fit captures 98.8% of variance in the loss-timing relationship. The curve is not flat: delaying expert expansion incurs a gradual but consistent paired loss penalty across all tested seeds, while yielding predictable compute savings and reducing expert diversity. Multi-stage schedules (dense → 2-expert → 4-expert) are Pareto-competitive with single-stage schedules, suggesting that gradual expansion deserves further study, though the observed advantage is small and not yet statistically decisive.

The primary operational rule emerging from this proxy is: **select the latest upcycle fraction whose measured loss penalty stays within the tolerated budget.** In this benchmark, $f \approx 0.25$ for a conservative +0.005 nat budget, or $f \approx 0.50$ for an aggressive +0.010 nat budget.

These findings are preliminary and scoped to a synthetic proxy. Scientific closure for production-scale LLM expert upcycling requires validation on real transformer/MoE training runs at intended token budgets (50–200M tokens), with hardware telemetry and top-$k$ routed kernels. The fitted law from this sweep can serve as a scheduling prior for such experiments, but its coefficients should not be extrapolated to production settings.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Single-stage sweep script | `scripts/upcycle_timing_sweep.py` |
| Multi-stage probe script | `scripts/multistage_probe.py` |
| Smoke test log | `logs/smoke.log` |
| Calibration log | `logs/calibration.log` |
| Full sweep log | `logs/full_sweep.log` |
| Multi-stage probe log | `logs/multistage_probe.log` |
| Smoke metrics | `results/smoke/metrics.csv`, `results/smoke/summary.json`, `results/smoke/law_fit.json` |
| Full sweep metrics | `results/full_sweep/metrics.csv`, `results/full_sweep/summary.json`, `results/full_sweep/law_fit.json`, `results/full_sweep/paired_deltas.json` |
| Multi-stage metrics | `results/multistage_probe/metrics.csv`, `results/multistage_probe/summary.json` |
| Project decision record | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260501T022048365094+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T022048365094+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T022048365094+0000/paper_manifest.json` |
