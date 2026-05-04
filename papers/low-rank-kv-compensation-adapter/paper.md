# Low-Rank KV Compensation Adapter: A Model-Free Viability Study of Query-Conditioned Residual Correction for Compressed Key-Value Caches

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

Low-rank compression of key-value (KV) caches reduces the memory footprint of transformer inference but introduces approximation error in attention outputs. This study investigates whether a small, query-conditioned low-rank compensation adapter can recover that error. We test the isolated approximation $y_{\text{base}}(q) + qC_a$, where $C_a$ is a rank-$a$ residual map fit on calibration queries, applied on top of truncated-SVD rank-$r$ KV reconstructions. Using a model-free numpy attention harness with synthetic key-value distributions spanning three regimes (low-rank-friendly, hybrid, and retrieval), we find that compensation is conditionally viable. Under aggressive compression (KV rank 8, adapter rank 8, memory ratio 0.157×), the adapter reduces relative MSE by 95.0% for low-rank-friendly attention and 87.4% for hybrid attention. However, for retrieval-like distributions where attention depends on exact key identity, the adapter provides only 8.6% relative improvement and leaves absolute error high (rel-MSE 0.686). Under moderate compression (KV rank 16), where the base approximation is already strong for smooth regimes, adapter gains are small (1.5% hybrid) or slightly negative (−0.7% low-rank-friendly). A shifted-distribution test confirms the adapter does not collapse under distribution shift but also does not resolve retrieval error. We conclude that low-rank KV compensation is viable only for attention patterns that are themselves approximately low-rank, and recommend hybrid exact-salient plus compressed-background strategies for any practical deployment.

## 1. Introduction

Transformer inference at long context lengths is memory-bounded by the size of the key-value (KV) cache. Low-rank compression of stored keys and values—projecting them into a reduced subspace via truncated SVD—offers direct memory savings but introduces error in the computed attention outputs. The residual error between exact and compressed attention is a function of the query vector, raising the question of whether this residual is itself predictable from the query via a low-rank map.

If the residual $y_{\text{exact}}(q) - y_{\text{base}}(q)$ lies approximately in a low-dimensional subspace spanned by functions of $q$, then a compact adapter $q \mapsto qC_a$ trained on calibration queries could recover much of the lost accuracy at negligible additional memory cost. This would enable aggressive KV compression with a small compensation overhead, yielding large net memory savings.

However, not all attention patterns produce low-rank residuals. Retrieval-like attention—where the output depends on identifying a specific key among many near-orthogonal candidates—produces residuals that may not be query-predictable in a low-rank fashion. The viability of compensation therefore depends on the structure of the attention distribution.

This study tests the core compensation premise in isolation: given synthetic KV matrices and queries drawn from known distributions, can a rank-$a$ linear adapter recover the error introduced by rank-$r$ SVD compression? We deliberately avoid full-transformer benchmarks at this stage. The isolated test directly probes whether the residual is low-rank and query-predictable—a necessary condition for any such adapter to work inside a real model, but not a sufficient one for production utility.

## 2. Method

### 2.1 Formal Setup

Let $K \in \mathbb{R}^{n \times d}$ and $V \in \mathbb{R}^{n \times d_v}$ be the full key and value matrices for a context of length $n$. Exact scaled dot-product attention for a query $q \in \mathbb{R}^d$ produces:

$$y_{\text{exact}}(q) = \text{softmax}\!\left(\frac{qK^\top}{\sqrt{d}}\right) V$$

We compress $K$ and $V$ via truncated SVD to rank $r$, yielding reconstructions $K_r$ and $V_r$. The base compressed attention output is:

$$y_{\text{base}}(q) = \text{softmax}\!\left(\frac{qK_r^\top}{\sqrt{d}}\right) V_r$$

The compensation adapter adds a query-conditioned linear residual:

$$y_{\text{adapter}}(q) = y_{\text{base}}(q) + qC_a$$

where $C_a \in \mathbb{R}^{d \times d_v}$ is constrained to rank $a$, implemented as $C_a = AB^\top$ with $A \in \mathbb{R}^{d \times a}$, $B \in \mathbb{R}^{d_v \times a}$.

### 2.2 Adapter Fitting

Given a set of calibration queries $\{q_i\}_{i=1}^{N_c}$ with known exact outputs $\{y_{\text{exact}}(q_i)\}$, we compute residuals $r_i = y_{\text{exact}}(q_i) - y_{\text{base}}(q_i)$ and solve:

$$\min_{A,B} \sum_{i=1}^{N_c} \|r_i - q_i AB^\top\|^2 + \lambda \|AB^\top\|_F^2$$

This is solved via alternating ridge regression with regularization parameter $\lambda = 0.1$. The adapter is fit once per KV cache and evaluated on held-out test queries.

### 2.3 Synthetic Regimes

We generate KV matrices and queries from three distributions designed to span a range of attention structures:

- **Low-rank-friendly.** Keys and values lie near a low-dimensional subspace. SVD compression captures most structure; residuals are expected to be smooth and low-rank.
- **Hybrid.** A mixture of low-rank structure and moderate noise. Represents typical attention where some structure exists but is not perfectly low-rank.
- **Retrieval.** Keys are near-orthogonal random vectors; attention concentrates on a single key matching the query. SVD compression destroys the identity structure; residuals depend on token-specific softmax behavior and are not expected to be low-rank.

### 2.4 Evaluation Protocol

We report relative MSE against the exact attention output:

$$\text{rel-MSE} = \frac{\|y_{\text{approx}}(q) - y_{\text{exact}}(q)\|^2}{\|y_{\text{exact}}(q)\|^2}$$

computed over held-out test queries. We also report cosine similarity between approximate and exact outputs. Adapter improvement is measured as the percentage reduction in mean rel-MSE relative to the base (uncompensated) compressed attention.

Memory ratio is computed as the storage cost of the compressed KV plus adapter parameters, divided by the storage cost of the full KV:

$$\text{memory\_ratio} = \frac{2 \cdot n \cdot r + 2 \cdot d \cdot a}{2 \cdot n \cdot d}$$

where $n$ is context length, $d$ is key/query dimension, and $r$, $a$ are KV rank and adapter rank respectively.

### 2.5 Experimental Configurations

**Main experiment.** $n = 512$, $d = d_v = 64$, $N_c = N_t = 2048$ calibration and test queries, KV rank $r = 16$, adapter rank $a = 8$, ridge $\lambda = 0.1$, 10 random seeds (0–9), all three regimes.

**Shifted-distribution test.** Same configuration as main, but test queries for the retrieval regime are biased toward the latter half of the key index range, testing generalization of the fitted adapter under distribution shift.

**Rank sweep.** KV rank $r \in \{4, 8, 16, 32\}$, adapter rank $a \in \{4, 8, 16\}$, 5 seeds per configuration, all three regimes.

**Smoke test.** $n = 128$, $d = d_v = 32$, $N_c = N_t = 64$, single seed, to validate the harness before full runs.

### 2.6 Environment

Experiments ran on a Linux `aarch64` host with NVIDIA GB10 present. Python 3.12.3 with numpy; no deep learning frameworks were used. The harness is a pure-numpy implementation of scaled dot-product attention with SVD compression and ridge-regularized adapter fitting. System memory: 121 GiB total, 115 GiB available, no swap. All runs were CPU-only numpy sweeps; the GPU was present but idle and not used. This is a toy simulation study, not a production validation or real-model benchmark.

## 3. Results

### 3.1 Main Experiment: KV Rank 16, Adapter Rank 8

The compressed KV plus adapter occupies 0.297× the memory of the full KV cache. Table 1 summarizes per-regime results.

| Regime | Base rel-MSE | Adapter rel-MSE | Improvement (%) | Base cosine | Adapter cosine |
|---|---|---|---|---|---|
| Low-rank-friendly | 3.79 × 10⁻⁴ | 3.82 × 10⁻⁴ | −0.73 | 0.99983 | 0.99983 |
| Hybrid | 1.056 × 10⁻² | 1.040 × 10⁻² | +1.52 | 0.99577 | 0.99576 |
| Retrieval | 6.708 × 10⁻¹ | 6.036 × 10⁻¹ | +9.95 | 0.57111 | 0.62765 |

**Table 1.** Mean rel-MSE and cosine similarity across 10 seeds (KV rank 16, adapter rank 8). Improvement is percentage reduction in rel-MSE from base to adapter.

The overall mean adapter improvement across all regimes is +3.58%. The adapter helped 2 of 3 regimes. For the low-rank-friendly regime, the base approximation is already very accurate (rel-MSE 3.79 × 10⁻⁴), and the adapter slightly worsens performance (−0.73%), consistent with adding estimation noise to an already-solved case. The hybrid regime shows a small positive gain (+1.52%). The retrieval regime shows the largest relative gain (+9.95%) but the absolute error remains very high (rel-MSE 0.604), indicating that the compensation does not restore usable retrieval behavior.

### 3.2 Shifted-Distribution Test

With test queries biased toward the latter half of the key index range in the retrieval regime, the overall adapter improvement drops slightly to +3.17%. The retrieval regime shows +8.83% improvement with rel-MSE 0.612. The shift did not collapse the adapter, confirming that the linear compensation generalizes modestly across query distribution shifts, but also does not resolve the fundamental difficulty of retrieval-like attention.

### 3.3 Rank Sweep

Table 2 summarizes the rank sweep for adapter rank 8 across varying KV ranks.

| KV rank | Memory ratio | LR-friendly improve (%) | Hybrid improve (%) | Retrieval improve (%) | Adapter helped (frac.) |
|---|---|---|---|---|---|
| 4 | 0.086 | +86.6 | +83.7 | +8.5 | 1.0 |
| 8 | 0.157 | +95.0 | +87.4 | +8.6 | 1.0 |
| 16 | 0.297 | −0.8 | +1.6 | +8.5 | 0.67 |
| 32 | 0.579 | −0.8 | +1.9 | +8.6 | 0.67 |

**Table 2.** Adapter improvement by KV rank (adapter rank 8, 5 seeds per configuration). "Adapter helped" is the fraction of regime–seed combinations where the adapter reduced rel-MSE.

Under aggressive compression (KV rank 4 or 8), the adapter provides dramatic improvement for low-rank-friendly and hybrid regimes (83.7–95.0% reduction), while the retrieval regime sees only 8.5–8.6% improvement. At these aggressive compression levels, the base approximation is poor for all regimes, and the adapter recovers most of the error for smooth and hybrid attention but barely helps for retrieval.

Under moderate compression (KV rank 16 or 32), the base approximation is already strong for low-rank-friendly and hybrid regimes, so adapter gains are small or slightly negative. The retrieval regime consistently shows approximately 8.5% improvement regardless of KV rank, suggesting the adapter captures a small but systematic component of the retrieval residual that is independent of compression severity.

### 3.4 Absolute Error Levels

The relative improvement percentages can be misleading in isolation. Table 3 reports absolute rel-MSE values for the most aggressive compression condition.

| Regime | Base rel-MSE (KV rank 8) | Adapter rel-MSE (KV rank 8) |
|---|---|---|
| Low-rank-friendly | 0.268 | 0.013 |
| Hybrid | 0.254 | 0.032 |
| Retrieval | 0.750 | 0.686 |

**Table 3.** Absolute rel-MSE at KV rank 8, adapter rank 8. Despite large relative improvements for smooth regimes, retrieval rel-MSE remains 0.686 after compensation.

Even after 87–95% relative improvement, the low-rank-friendly and hybrid regimes achieve rel-MSE of 0.013 and 0.032 respectively—small but nonzero. The retrieval regime at 0.686 is far from functional for any task requiring exact key identification.

### 3.5 Computational Cost

Adapter fitting and evaluation times are modest. For the rank sweep configurations, total fit time ranged from 0.17–0.23 seconds and total evaluation time from 0.17–0.21 seconds per configuration (5 seeds, 3 regimes, 2048 test queries each). These timings reflect the numpy harness on CPU and are not directly indicative of production inference cost, but they confirm that the adapter fitting procedure is computationally lightweight within this experimental framework.

## 4. Limitations

1. **Model-free isolation.** The numpy attention harness tests the core compensation premise in isolation but is not a full transformer decoding benchmark. Real attention distributions, layer-norm interactions, multi-head effects, and downstream task metrics are not captured. The results establish a necessary condition (residual low-rank predictability) but not a sufficient one for production utility.

2. **Linear adapter only.** The tested adapter is a per-cache linear low-rank residual map ($qC_a$). Nonlinear adapters, per-head adapters, or adapters integrated into the attention computation (e.g., modifying the softmax logits) may behave differently and could potentially improve retrieval compensation.

3. **Synthetic distributions.** The three regimes (low-rank-friendly, hybrid, retrieval) are synthetic constructions. Real transformer attention patterns may not fall cleanly into these categories and may exhibit different residual structures.

4. **Retrieval remains unsolved.** Across all configurations, the adapter provides only approximately 8–10% relative improvement for retrieval-like attention, leaving absolute error high. This is a structural limitation: exact retrieval depends on token-specific softmax/key identity that a global low-rank query function cannot capture.

5. **No task-level evaluation.** We measure approximation error (rel-MSE, cosine similarity) rather than downstream task performance (perplexity, accuracy). The relationship between rel-MSE and task degradation is not established.

6. **Fixed context length and dimension.** All experiments use $n = 512$, $d = 64$. Scaling behavior to longer contexts or different dimensions is not tested.

7. **Single regularization setting.** Ridge parameter $\lambda = 0.1$ was used throughout. Sensitivity to this hyperparameter is not characterized.

## 5. Reproducibility Checklist

- **Code available:** `scripts/lowrank_kv_compensation_eval.py` (self-contained numpy harness).
- **Random seeds:** Explicitly reported (0–9 for main/shifted, 0–4 for rank sweep).
- **Hardware:** Linux aarch64 host, NVIDIA GB10 present but unused; all runs CPU-only.
- **Software:** Python 3.12.3, numpy. No GPU or deep learning framework dependencies.
- **Data generation:** All KV matrices and queries are synthetically generated in-code from seeded random number generators; no external data.
- **Metrics artifacts:** All JSON metric files and logs are listed in Section 7 (Referenced Artifacts).
- **Hyperparameters:** All hyperparameters (context length, dimensions, ranks, ridge, seeds, regimes) are specified in Section 2.5 and the run commands in the run notes.
- **Statistical reporting:** Means reported over multiple seeds; minimum and maximum improvement reported per regime in the project decision JSON for the main experiment.

## 6. Conclusion

A low-rank query-conditioned compensation adapter can substantially recover the error introduced by aggressive low-rank KV-cache compression, but only for attention patterns that are themselves approximately low-rank. Under aggressive compression (KV rank 8, adapter rank 8, memory ratio 0.157×), the adapter reduces relative MSE by 87–95% for smooth and hybrid attention regimes. This confirms the core premise: the residual left by low-rank KV compression is indeed low-rank and query-predictable when the underlying attention distribution is smooth.

However, the compensation is not generally effective. For retrieval-like attention where the output depends on exact key identity, the adapter provides only 8–10% relative improvement across all tested KV ranks, leaving absolute error high (rel-MSE 0.6–0.8). This is a structural limitation of a global low-rank query function applied to a task requiring token-specific softmax behavior.

Under moderate compression where the base approximation is already accurate, adapter gains are marginal and can be slightly negative due to estimation noise. The adapter is most valuable when compression is aggressive enough to produce substantial base error in smooth regimes.

These findings support a conditional viability classification: low-rank KV compensation is a viable strategy for applications where attention is predominantly smooth or where retrieval-critical spans can be identified and served with exact KV entries. A hybrid policy—retaining full KV for salient retrieval-critical spans while compressing background spans with compensation—represents the most promising path for practical deployment. We do not recommend pursuing low-rank KV compensation as a general replacement for full KV caches without a stronger mechanism for retrieval-like attention.

## 7. Referenced Artifacts

| Artifact | Path |
|---|---|
| Evaluation harness | `scripts/lowrank_kv_compensation_eval.py` |
| Run notes | `run_notes.md` |
| Smoke test metrics | `artifacts/smoke_lowrank_kv_compensation_eval.json` |
| Main experiment metrics | `artifacts/lowrank_kv_compensation_eval_main.json` |
| Shifted-distribution metrics | `artifacts/lowrank_kv_compensation_eval_shifted.json` |
| Rank sweep aggregate | `artifacts/lowrank_kv_compensation_rank_sweep.json` |
| Smoke test log | `artifacts/logs/smoke_lowrank_kv_compensation_eval.log` |
| Main experiment log | `artifacts/logs/main_lowrank_kv_compensation_eval.log` |
| Shifted-distribution log | `artifacts/logs/shifted_lowrank_kv_compensation_eval.log` |
| Rank sweep summary log | `artifacts/logs/rank_sweep_summary.log` |
| Per-sweep logs | `artifacts/logs/sweep_kv*_adapter*.log` |
| Project decision | `.omx/project_decision.json` |
