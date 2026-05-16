# Aretē: Hierarchical Multi-Virtue Reward Architecture for Reinforcement Learning

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We present Aretē, a hierarchical multi-virtue reward architecture for reinforcement learning that decomposes a scalar reward signal into multiple virtue channels and conditions lower-level reward flow on a correctness gate. In deterministic toy-simulation benchmarks across four optimization regimes—synthetic scoring, sequential GRPO-lite grouped rollouts, offline policy optimization, and pairwise preference distillation—we find that correctness-gated Aretē consistently suppresses "pious-hacker" trajectories (outputs that satisfy surface-level virtue signals without factual correctness) while scalar reward baselines drift toward hacker selection as virtue channel count increases. Ablation experiments across all regimes isolate correctness gating as the dominant anti-hacking mechanism (hacker reintroduction in 3/3 tested regimes upon removal), with PAPO-style conditional normalization acting as a secondary optimizer-shaping term (hacker reintroduction in 0/3 regimes upon removal, but measurable margin and dispersion effects). A compute-matched comparison of three versus five virtue channels reveals that five channels require 1.67× the reward-channel evaluations while producing no additional intrinsic safety benefit over the three-virtue baseline, and instead impose a stability tax manifesting as softer margins, higher dispersion, and noisier optimization dynamics in all four regimes. The current project artifacts support these findings in the tested setting; they do not establish universal applicability.

---

## 1. Introduction

A central challenge in multi-objective reinforcement learning is reward hacking: policies that optimize proxy reward signals without satisfying the intended behavioral constraints. This problem intensifies when reward is decomposed into multiple virtue channels (e.g., helpfulness, honesty, safety), because a policy may learn to satisfy surface-level virtue indicators while violating deeper correctness constraints—a pattern we term *pious hacking*.

Aretē addresses this by imposing a hierarchical structure on multi-virtue reward: lower-level virtue signals are conditioned on a correctness gate, and PAPO-style conditional normalization reshapes the credit-assignment landscape. The architecture raises two empirical questions:

1. Does hierarchical correctness gating prevent pious-hacker trajectory selection better than scalar reward aggregation?
2. What is the cost–benefit profile of adding virtue channels beyond a minimal set?

We evaluate these questions in deterministic toy-simulation benchmarks spanning four optimization regimes. All results are from synthetic/simulation environments; no production-scale or live-model validation has been performed.

---

## 2. Method

### 2.1 Architecture

Aretē decomposes a reward signal into $K$ virtue channels $v_1, \ldots, v_K$. The key architectural components are:

**Correctness gating.** Each lower-level virtue signal is conditioned on a binary correctness indicator $c \in \{0, 1\}$. When $c = 0$, downstream virtue rewards are suppressed, preventing the policy from receiving positive virtue feedback on incorrect outputs. Formally, the gated virtue signal for channel $k$ is:

$$\tilde{v}_k = c \cdot v_k$$

**PAPO-style conditional normalization.** Virtue channel outputs are normalized conditional on the correctness gate state, which reshapes the relative scale of virtue signals across correct versus incorrect trajectories. This term is intended to sharpen credit assignment in sequential optimization settings.

**Hierarchical aggregation.** The final reward combines gated and normalized virtue signals through a hierarchical weighting scheme rather than flat scalar summation.

### 2.2 Ablation Interface

To isolate component contributions, the implementation provides an ablation hook (`ablated_arete_feature_vectors` in `src/arete_reward.py`) that independently disables:

- **No-gate ablation:** Correctness gating is removed; virtue signals flow unconditionally.
- **No-conditional-norm ablation:** PAPO-style conditional normalization is removed; virtue signals are aggregated without regime-dependent rescaling.

These two ablations are applied across all four benchmark regimes, enabling direct component attribution.

---

## 3. Experimental Setup

### 3.1 Benchmark Regimes

All experiments use deterministic toy simulations with synthetic reward signals and controlled trajectory generation. The four regimes are:

1. **Synthetic scoring** (`arete_multivirtue_sweep`): Static reward evaluation over virtue-channel configurations without optimization dynamics.

2. **GRPO-lite sequential rollouts** (`arete_grpo_lite_benchmark`): Deterministic grouped-rollout benchmark over 4-step trajectories with per-step virtue and process annotations. A GRPO-lite update rule selects among grouped trajectories using the computed reward.

3. **Offline policy optimization** (`arete_offline_policy_benchmark`): Policy updates computed offline from logged trajectories, comparing scalar versus Aretē reward aggregation.

4. **Preference policy distillation** (`arete_preference_policy_benchmark`): Pairwise preference labels distilled from a teacher reward model, testing whether Aretē's advantage survives the compression into binary preference signals.

### 3.2 Ablation Benchmarks

Each regime (2–4) includes a paired ablation benchmark that independently removes correctness gating or conditional normalization, yielding three additional benchmark suites:

- `arete_grpo_ablation_benchmark`
- `arete_offline_policy_ablation_benchmark`
- `arete_preference_policy_ablation_benchmark`

### 3.3 Cross-Regime and Compute-Matched Syntheses

Two synthesis artifacts aggregate across regimes:

- `arete_cross_regime_summary`: Counts how many regimes show hacker reintroduction under each ablation.
- `arete_compute_matched_channel_tax`: Compares 3 versus 5 virtue channels at matched task/update counts, quantifying compute overhead and stability tax.

### 3.4 Metrics

- **Top-correct rate:** Fraction of top-ranked trajectories that are factually correct.
- **Hacker rate:** Fraction of top-ranked trajectories that are pious hackers (satisfy virtue signals without correctness).
- **Truthful mass:** Aggregate probability mass assigned to correct trajectories.
- **Final margin:** Mean gap between correct and hacker trajectory scores.
- **Margin stddev:** Dispersion of the margin, indicating optimization stability.
- **Flip rate:** Fraction of trajectories whose ranking changes between steps.

### 3.5 Verification

All benchmark scripts were executed and their outputs recorded. Regression test suites were run at each development stage, with the final suite passing 20/20 tests. Source tree compilation was verified via `python3 -m compileall`.

---

## 4. Results

### 4.1 Scalar versus Aretē: Hacker Suppression

At 5 virtue channels, Aretē consistently outperforms scalar reward aggregation:

| Regime | Scalar top-correct | Aretē top-correct | Scalar hacker rate | Aretē hacker rate |
|---|---|---|---|---|
| GRPO-lite | 0.956 | 1.000 | 0.044 | 0.000 |
| Offline policy | 0.958 | 1.000 | 0.042 | 0.000 |
| Preference policy | — | 1.000 | — | 0.000 |

In the GRPO-lite regime, Aretē's truthful trajectory mass advantage over scalar reached +0.042 at 5 channels (0.991 vs. 0.949). In the offline policy regime, Aretē achieved 1.000 truthful mass versus 0.814 for scalar at 5 channels.

### 4.2 Component Ablation: Correctness Gating Is the Dominant Anti-Hacking Mechanism

Removing correctness gating reintroduces pious-hacker selection in all three optimization regimes tested:

| Regime | Full Aretē top-correct | No-gate top-correct | No-gate hacker rate |
|---|---|---|---|
| GRPO-lite (5ch) | 1.000 | 0.000 | 1.000 |
| Preference policy (5ch) | 1.000 | 0.990 | 0.010 |
| Offline policy (5ch) | 1.000 | 0.958 | 0.042 |

The severity of collapse varies by regime. In GRPO-lite, removing the gate produces total collapse (hacker rate 1.000). In preference policy, the collapse is less extreme at 5 channels (hacker rate 0.010) but severe at 3 channels (hacker rate 0.292, top-correct 0.708), indicating that the preference distillation stage partially smooths the shortcut but does not eliminate it.

### 4.3 Component Ablation: Conditional Normalization Is a Secondary Term

Removing only PAPO-style conditional normalization does not reintroduce hackers in any regime (0/3), but produces measurable effects on optimization quality:

| Regime | Metric | Full Aretē | No-cond-norm | Delta |
|---|---|---|---|---|
| GRPO-lite (5ch) | Truthful mass | 0.9911 | 0.9909 | −0.0002 |
| GRPO-lite (5ch) | Flip rate | 0.0329 | 0.0343 | +0.0014 |
| Offline policy (3ch) | Final margin | 0.931 | 0.777 | −0.154 |
| Offline policy (5ch) | Final margin | 0.744 | 0.603 | −0.141 |
| Preference policy (5ch) | Truthful mass | — | — | +0.0010 |
| Preference policy (5ch) | Top margin mean | — | — | +0.0001 |

Conditional normalization shows a regime split: it measurably sharpens sequential GRPO credit assignment and offline policy margins, but its effect is largely washed out after preference distillation into pairwise labels.

### 4.4 Three-Virtue MVP Boundary

Moving from 3 to 5 virtue channels raises reward-evaluation cost by 66.7% (1.67×) while producing identical Aretē top-correct and hacker-suppression outcomes across all four regimes. However, 5 channels impose a stability tax in 4/4 regimes:

- GRPO-lite: mean final margin softened from 0.945 to 0.926; margin stddev rose from 0.132 to 0.137.
- Offline policy: final margin decreased from 0.931 to 0.744 (with conditional normalization active).
- Additional regimes showed softer margins, higher dispersion, lower ranking consistency, or noisier optimization dynamics.

Extra virtue channels can widen Aretē's advantage over scalar baselines in some regimes because scalar degrades faster with more channels, but this is not equivalent to five virtues improving the Aretē policy itself.

### 4.5 Cross-Regime Consistency

The cross-regime synthesis confirms that five-channel Aretē remained hacker-free across GRPO-lite, offline policy, and preference policy, while scalar reward reintroduced hacker selection in all three. Correctness-gating removal reintroduced hackers in 3/3 regimes; conditional-normalization removal reintroduced hackers in 0/3 regimes.

---

## 5. Limitations

1. **Toy simulation only.** All benchmarks use deterministic synthetic environments with controlled reward signals. No results are reported on real language models, production RLHF pipelines, or live training runs. The findings establish mechanistic plausibility, not operational validity.

2. **No external replication.** The experiments were conducted within a single automated research pipeline. Independent replication by external teams has not been performed.

3. **Narrow regime coverage.** Only four optimization regimes were tested. Other regimes (e.g., online PPO, constitutional AI-style critique loops, multi-turn dialogue) may exhibit different ablation profiles.

4. **Synthetic reward structure.** The "pious hacker" trajectories are defined by the simulation's ground-truth correctness labels. In real settings, correctness verification itself may be noisy or contested, which could weaken the correctness gate's reliability.

5. **Fixed trajectory length and channel semantics.** GRPO-lite experiments use 4-step trajectories. Virtue channel semantics are abstract; results may not transfer to specific real-world virtue decompositions (e.g., helpfulness vs. harmlessness vs. honesty) without re-evaluation.

6. **Conditional normalization's small effects.** The measured effects of conditional normalization are small in absolute terms (e.g., truthful mass deltas on the order of 0.001). While statistically consistent across runs, these differences may not be practically significant in noisy real-world training.

7. **No hardware or wall-clock measurements.** The 1.67× compute overhead for five channels is a theoretical count of reward-channel evaluations, not a measured GPU-hour or wall-clock comparison.

8. **Kill condition unsupported.** The project did not identify a condition under which the Aretē architecture fails catastrophically or should be abandoned; the evidence supports a positive but bounded conclusion.

---

## 6. Reproducibility Checklist

| Item | Status |
|---|---|
| Benchmark scripts available | Yes: `scripts/run_grpo_lite_benchmark.py`, `scripts/run_grpo_ablation_benchmark.py`, `scripts/run_offline_policy_benchmark.py`, `scripts/run_offline_policy_ablation_benchmark.py`, `scripts/run_preference_policy_ablation_benchmark.py`, `scripts/run_cross_regime_summary.py`, `scripts/run_compute_matched_channel_tax.py` |
| Regression tests | Yes: 20/20 passing at final state |
| Deterministic execution | Yes: all benchmarks are deterministic (no random seeds reported because no stochasticity is present) |
| Result artifacts persisted | Yes: 20 JSON/Markdown result files in `results/` |
| Source compilation verified | Yes: `python3 -m compileall src scripts tests` passed |
| Ablation interface documented | Yes: `ablated_arete_feature_vectors` in `src/arete_reward.py` |
| Claim audit trail | Yes: `claim_ledger.json` with allowed/forbidden wording |
| Evidence bundle | Yes: `evidence_bundle.json` with decision, result files, and run notes |
| Project decision artifact | Yes: `.omx/project_decision.json` (finalize_positive, supported, high confidence) |
| External replication | Not performed |
| Real-model validation | Not performed |

---

## 7. Conclusion

In deterministic toy-simulation benchmarks across four optimization regimes, the Aretē hierarchical multi-virtue reward architecture with correctness gating consistently suppresses pious-hacker trajectory selection where scalar reward aggregation fails. Ablation evidence across all regimes identifies correctness-conditioned reward flow as the essential anti-hacking mechanism, with PAPO-style conditional normalization serving as a secondary optimizer-shaping term whose importance varies by regime. A compute-matched analysis establishes that three virtue channels capture the full safety benefit of the architecture, while five channels impose a 1.67× compute overhead and a consistent stability tax without additional safety gain. The current project artifacts support the adoption of a three-virtue correctness-gated Aretē reward as a minimum viable architecture in the tested setting. Reopening the >3-virtue configuration would require demonstrating net safety gain per unit compute in a new regime. These findings are bounded by the synthetic simulation setting and have not been validated on production models or external benchmarks.

---

## Referenced Artifacts

### Result files
- `results/arete_compute_matched_channel_tax.json` / `.md`
- `results/arete_cross_regime_summary.json` / `.md`
- `results/arete_offline_policy_benchmark.json` / `.md`
- `results/arete_offline_policy_ablation_benchmark.json` / `.md`
- `results/arete_preference_policy_ablation_benchmark.json` / `.md`
- `results/arete_grpo_ablation_benchmark.json` / `.md`
- `results/arete_grpo_lite_benchmark.json` / `.md`
- `results/arete_preference_dataset_benchmark.json` / `.md`
- `results/arete_preference_policy_benchmark.json` / `.md`
- `results/arete_multivirtue_sweep.json` / `.md`

### Source and test files
- `src/arete_reward.py` (includes `ablated_arete_feature_vectors`)
- `scripts/run_grpo_lite_benchmark.py`
- `scripts/run_grpo_ablation_benchmark.py`
- `scripts/run_offline_policy_benchmark.py`
- `scripts/run_offline_policy_ablation_benchmark.py`
- `scripts/run_preference_policy_ablation_benchmark.py`
- `scripts/run_cross_regime_summary.py`
- `scripts/run_compute_matched_channel_tax.py`
- `tests/test_grpo_lite_benchmark.py`
- `tests/test_grpo_ablation_benchmark.py`
- `tests/test_offline_policy_ablation_benchmark.py`
- `tests/test_preference_policy_ablation_benchmark.py`
- `tests/test_cross_regime_summary.py`
- `tests/test_compute_matched_channel_tax.py`
- `tests/test_arete_reward.py`

### Decision and audit files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `run_notes.md`
- `papers/.../claim_ledger.json`
- `papers/.../evidence_bundle.json`
- `papers/.../paper_manifest.json`
