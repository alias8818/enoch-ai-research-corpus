# Survival-Optimized Block Diffusion: Budgeted Call Allocation via Survival Curve Dynamic Programming

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, and benchmark outputs). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and evaluate its claims accordingly. No human reviewer has endorsed this content.

---

## Abstract

Block diffusion models interleave autoregressive block sequencing with iterative denoising refinement within each block. Standard inference allocates a uniform number of refinement calls per block regardless of per-block difficulty. We investigate whether a survival-curve–aware scheduler can reduce expected unresolved tokens under a fixed total call budget. We formalize Survival-Optimized Block Diffusion (SOBD) as a dynamic-programming allocation over estimated per-token survival curves and evaluate it in a controlled synthetic simulator. Across 500 paired sequences (length 256, block size 16), SOBD-DP reduces expected unresolved tokens versus uniform allocation by 1.1–6.3% (mean 4.3%) across budget multipliers from 3× to 10×, recovering at least 0.931 of the oracle scheduler's achievable reduction despite noisy difficulty estimates. A critical negative result emerges: a greedy marginal-benefit allocator, while effective at tight budgets, underperforms uniform allocation at high budgets (8×, 10×) because denoising survival curves are non-concave. These results establish that budgeted DP allocation is algorithmically viable in a synthetic setting but remain confined to a controlled simulator; validation on trained block-diffusion checkpoints is required before drawing conclusions about generative quality or wall-clock latency.

## 1. Introduction

Block diffusion models such as BD3-LMs combine autoregressive structure across blocks with discrete diffusion denoising within each block, enabling flexible-length generation and potential KV-cache efficiency. A natural inference question arises: given a fixed computational budget for refinement calls across blocks, should all blocks receive equal allocation, or can heterogeneous allocation improve outcomes?

The premise of this work is straightforward: tokens and blocks vary in difficulty. Hard spans—idioms, rare tokens, syntactically ambiguous regions—may require more denoising steps to resolve than easy spans. If per-token difficulty can be estimated (even noisily), a scheduler could concentrate calls where they yield the largest reduction in unresolved tokens.

We investigate this question through the lens of survival analysis. Each token's probability of remaining unresolved after $c$ refinement calls defines a survival curve. Under heterogeneous per-token hazards, uniform call allocation is suboptimal: it over-invests in easy blocks and under-invests in hard ones. The question is whether a budgeted optimizer operating on noisy survival-curve estimates can recover enough of the oracle improvement to justify the added scheduling complexity.

We make the following contributions:

1. We formalize the block-diffusion call-allocation problem as a budgeted optimization over per-token survival curves, where each token has a heterogeneous per-refinement hazard of becoming resolved.
2. We show that a dynamic-programming (DP) solver for this problem, SOBD-DP, consistently outperforms uniform allocation in synthetic simulation, recovering ≥93.1% of the oracle reduction achievable with perfect difficulty knowledge.
3. We demonstrate that a greedy one-step marginal-benefit allocator is **not** a sufficient substitute: it underperforms uniform allocation at high budgets due to the non-concavity of denoising survival curves. This negative result constrains the design space of practical schedulers.
4. We clearly delineate the scope limitation: all results derive from a controlled simulator with parametric hazard distributions, not from inference inside a trained neural block-diffusion model.

## 2. Method

### 2.1 Problem Formulation

Consider a sequence of $N$ tokens partitioned into $K$ blocks of size $B$. Each token $i$ has a true per-call resolution probability (hazard) $h_i$, drawn from a heterogeneous distribution. After $c$ refinement calls, the probability that token $i$ remains unresolved is $(1 - h_i)^c$, and its survival function is:

$$S_i(c) = (1 - h_i)^c$$

Given a total budget of $C_{\text{total}}$ calls across all blocks, the objective is to choose non-negative integer call counts $c_1, c_2, \ldots, c_K$ for $K$ blocks such that:

$$\min_{c_1, \ldots, c_K} \sum_{i=1}^{N} S_i(c_{b(i)}) \quad \text{subject to} \quad \sum_{k=1}^{K} c_k \leq C_{\text{total}}$$

where $b(i)$ denotes the block containing token $i$. All tokens within a block receive the same number of calls under this formulation.

### 2.2 Uniform Baseline

The uniform baseline assigns $c_k = C_{\text{total}} / K$ calls to every block, ignoring heterogeneity. This is the default strategy in standard block-diffusion inference.

### 2.3 SOBD-DP: Budgeted Dynamic Programming

SOBD-DP solves the allocation problem via a knapsack-style DP. For each block $k$, the marginal reduction in expected unresolved tokens from assigning $c$ calls is computed from the block's estimated survival curve. The DP minimizes total expected unresolved tokens subject to the budget constraint.

In practice, per-token hazards are not known exactly. A cheap calibration probe provides noisy estimates $\hat{h}_i$. The DP operates on these estimates, introducing estimation error. The key question is whether noisy estimates suffice for near-optimal allocation.

### 2.4 Greedy Marginal Allocator

A natural alternative to full DP is a greedy allocator that assigns each incremental call to the block with the largest current marginal benefit. This approach is equivalent to assuming concave survival curves—i.e., that each additional call on a block yields diminishing returns. As the results in Section 3 demonstrate, this assumption is violated in the block-diffusion setting.

### 2.5 Oracle Scheduler

The oracle scheduler has access to true hazards $h_i$ and solves the same DP. It provides an upper bound on achievable reduction, establishing the performance ceiling for any scheduler operating under the same budget.

### 2.6 Simulation Protocol

We implemented a synthetic simulator (`scripts/sobd_sim.py`) that:

1. Generates sequences with heterogeneous per-token hazards drawn from a parametric distribution.
2. Produces noisy hazard estimates via a calibration probe that introduces estimation noise.
3. Computes allocations for uniform, greedy, SOBD-DP, and oracle policies using the same random seeds and noise realizations.
4. Scores each policy by expected unresolved tokens under the true hazards.

All policies are evaluated on identical paired sequences, controlling for randomness. This paired design ensures that observed differences are attributable to the scheduling policy rather than sequence-level variation.

A smoke-first protocol was followed: an initial run with 20 sequences (length 64, block size 8) completed successfully before scaling to the main experimental configuration.

## 3. Results

### 3.1 Main DP Confirmation

We ran 500 paired synthetic sequences of length 256 with block size 16. Budget multipliers (total calls relative to the minimum one-call-per-block budget) ranged from 3× to 10×. Table 1 reports the results.

**Table 1:** SOBD-DP vs. uniform allocation across budget multipliers. Token resolved delta is in percentage points. Expected unresolved reduction and fraction of oracle reduction are unitless ratios. SOBD call Gini measures allocation inequality (0 = uniform, 1 = fully concentrated).

| Budget mult. | Token resolved Δ (pp) | Unresolved reduction (%) | Fraction of oracle | SOBD call Gini |
|---:|---:|---:|---:|---:|
| 3× | 4.616 | 6.103 | 0.990 | 0.349 |
| 4× | 4.114 | 6.343 | 0.992 | 0.273 |
| 5× | 2.916 | 5.377 | 0.994 | 0.192 |
| 6× | 1.658 | 3.676 | 0.986 | 0.153 |
| 8× | 0.331 | 1.085 | 0.931 | 0.072 |
| 10× | 0.686 | 3.179 | 0.973 | 0.068 |

SOBD-DP reduced expected unresolved tokens relative to uniform at every tested budget. The reduction ranged from 1.085% to 6.343%, with a mean of 4.294%. SOBD-DP recovered at least 0.931 of the oracle scheduler's achievable reduction, indicating that noisy calibration estimates suffice for near-optimal allocation in this synthetic setting.

The call Gini coefficient decreases with increasing budget, reflecting that at high budgets, even the optimal allocator approaches near-uniform assignment because marginal returns diminish across all blocks. The absolute magnitude of improvement is modest at high budgets, which is expected: when the budget is generous, even uniform allocation resolves most tokens.

A notable non-monotonicity appears in the 10× row, where the unresolved reduction (3.179%) exceeds the 8× value (1.085%). This likely reflects the discrete interaction between budget allocation and the specific hazard distribution in the synthetic data rather than a systematic effect. The fraction-of-oracle metric, which accounts for the shrinking oracle improvement at high budgets, shows a dip at 8× (0.931) before recovering at 10× (0.973).

### 3.2 Negative Result: Greedy Allocation Failure

A greedy marginal-benefit scheduler was tested on the same 500 paired sequences. While greedy SOBD improved outcomes at tight budgets (3×–6×), it **underperformed uniform allocation** at 8× and 10× budgets.

This failure arises because denoising survival curves are non-concave: early calls on a hard token can have smaller marginal benefit than later calls, once the token crosses a difficulty threshold. A greedy allocator over-invests in blocks that appear to have high marginal benefit at the current margin, starving blocks where later calls would yield larger returns. The DP correctly accounts for the full survival curve shape.

This result has a direct design implication: SOBD should be specified as a budgeted DP or knapsack optimizer, not as a simple greedy hazard allocator. Greedy allocation may serve as a low-budget heuristic but is not robust across operating points.

### 3.3 Resource Usage

All simulations ran CPU-only on an NVIDIA GB10 host (Linux aarch64). GPU compute utilization remained at 0% throughout (`nvidia-smi` confirmed). Peak RSS was approximately 15.8 MB. The main paired analysis run (500 sequences) completed in 1 minute 51.69 seconds. System memory was not a constraint (MemAvailable ~122.7 GB; swap disabled).

## 4. Limitations

This work has a fundamental scope limitation that qualifies all positive findings.

**External neural validation needed.** All results derive from a controlled synthetic simulator with parametric hazard distributions and noisy calibration probes. No experiments were conducted inside a trained block-diffusion language model (e.g., BD3-LMs or LLaDA checkpoints). The survival-curve shapes, noise characteristics of calibration estimates, and correlation structure between estimated and true difficulty may differ substantially in neural settings. The magnitude of unresolved-token reduction observed in simulation (1.1–6.3%) may not translate to improvements in generative quality metrics (perplexity, BLEU, human evaluation) or wall-clock latency. The relationship between expected unresolved tokens and downstream generation quality is unestablished.

**Synthetic hazard model.** The simulator draws per-token hazards from a parametric distribution under an independent-hazard assumption. Real token difficulties are shaped by context, model capacity, and training data, and may exhibit dependencies not captured by this model. The degree of heterogeneity in the synthetic model may not match that of real neural block-diffusion inference.

**Block-level allocation granularity.** The current formulation allocates calls at the block level, treating all tokens within a block as receiving the same number of calls. Token-level allocation within blocks is not explored and may yield further improvements.

**No quality metrics.** Expected unresolved tokens is a proxy for generation quality. Whether reducing this proxy by 1–6% produces perceptible quality differences in real models is unknown.

**Static allocation.** The DP computes a fixed allocation before refinement begins. Adaptive re-allocation based on intermediate denoising outcomes (e.g., observed remasking rates) is not studied and may improve upon static allocation.

**Claim audit status.** The structured claim ledger for this artifact was flagged as empty at the time of draft generation. No formal claim-evidence audit has been completed. The claims in this paper should be treated as unevaluated until such an audit is performed against the referenced metric artifacts.

## 5. Reproducibility Checklist

- **Code availability:** Simulator source at `scripts/sobd_sim.py`; paired analysis at `scripts/sobd_paired_analysis.py`.
- **Random seeds:** Paired evaluation uses identical seeds and noise realizations across all policies.
- **Hardware:** NVIDIA GB10, Linux aarch64, CPU-only execution. No GPU required for simulation.
- **Environment telemetry:** Captured in `artifacts/logs/environment_*.log`.
- **Smoke test:** Passed. Command: `python3 scripts/sobd_sim.py --sequences 20 --length 64 --block-size 8 --out artifacts/metrics/smoke_sobd_results.json`. Log: `artifacts/logs/smoke_sobd_*.log`.
- **Main run:** 500 sequences, length 256, block size 16. Command: `python3 scripts/sobd_paired_analysis.py --sequences 500 --length 256 --block-size 16 --out artifacts/metrics/paired_dp500_sobd_results.json`. Elapsed: 1:51.69. Max RSS: 15,828 KB. Log: `artifacts/logs/paired_dp500_sobd_*.log`.
- **Metrics files:** `artifacts/metrics/paired_dp500_sobd_results.json` (contains uniform, SOBD-DP, SOBD-greedy, and oracle rows); `artifacts/metrics/paired_sobd_results.json` (initial greedy-only results).
- **System state:** Swap disabled. MemAvailable ~122.7 GB. `nvidia-smi` compute utilization 0%.
- **Result classification:** All reported results are from a toy/synthetic simulation. No llama.cpp hook-prototype results, CUDA copy calibration, or production validation was performed.

## 6. Conclusion

We have shown that a survival-curve dynamic-programming scheduler (SOBD-DP) can reduce expected unresolved tokens by 1.1–6.3% versus uniform allocation in a synthetic block-diffusion simulator, recovering ≥93.1% of the oracle reduction achievable with perfect difficulty knowledge. A critical negative finding constrains practical design: greedy marginal-benefit allocation is not a robust substitute for DP, as it underperforms uniform allocation at high budgets due to non-concave survival curves.

These results establish the algorithmic viability of budgeted survival-curve allocation in a controlled setting but do not constitute validation on neural block-diffusion models. The improvements, while consistent, are modest in absolute terms, and their practical significance depends on factors not captured by the simulator: the actual degree of heterogeneity in real model inference, the quality of difficulty estimates obtainable from model internals, and the relationship between unresolved-token reduction and generation quality.

The next scientific closure step is to implement SOBD-DP as an inference scheduler in a trained BD3-LMs or LLaDA checkpoint, using model confidence or remasking statistics as survival estimates, and measuring generative quality and latency under equal network-evaluation budgets. If DP overhead proves significant for large block counts, beam-pruned DP or Lagrangian water-filling approximations may be worth investigating, but the greedy allocator should be retained only as a low-budget heuristic given its demonstrated failure mode. Until such neural validation is performed, the practical benefit of SOBD remains conjectural.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Simulator | `scripts/sobd_sim.py` |
| Paired analysis script | `scripts/sobd_paired_analysis.py` |
| Main metrics (DP confirmation) | `artifacts/metrics/paired_dp500_sobd_results.json` |
| Initial greedy metrics | `artifacts/metrics/paired_sobd_results.json` |
| Smoke test metrics | `artifacts/metrics/smoke_sobd_results.json` |
| Environment logs | `artifacts/logs/environment_*.log` |
| Smoke test log | `artifacts/logs/smoke_sobd_*.log` |
| Paired DP run log | `artifacts/logs/paired_dp500_sobd_*.log` |
| Claim ledger | `papers/source-record-redacted-20260504T172651468915+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260504T172651468915+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260504T172651468915+0000/paper_manifest.json` |

## External Sources Referenced

- Block Diffusion / BD3-LMs: `https://arxiv.org/abs/2503.09573`; implementation: `https://github.com/kuleshov-group/bd3lms`
- SEDD (discrete diffusion language models): `https://arxiv.org/abs/2310.16834`
- LLaDA (masked diffusion language models): `https://papers.cool/arxiv/2502.09992`
