# Entropy-Binned Online Bandit Routing for Multi-Policy Speculative Decoding

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (simulator scripts, run logs, structured decision records, and telemetry). The operator who released this artifact claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated the claims, code, or data herein.

---

## Abstract

Speculative decoding accelerates autoregressive inference by generating candidate token sequences with a fast draft model and verifying them in parallel against a target model. The optimal speculation policy—governing draft length, tree structure, or candidate count—depends on local token-level entropy, which varies across inputs and within a single sequence. We investigate whether an online contextual bandit router that bins on per-token entropy and selects among multiple speculation policies can outperform any single fixed policy or a hand-coded static entropy gate. In a transparent toy simulator modeling three policies (conservative *k*=2, balanced *k*=4, aggressive *k*=8) under four workload regimes, the proposed entropy-binned UCB bandit with exponential decay improved tokens-per-latency by 4.9–5.3% over the best fixed policy in heterogeneous and nonstationary entropy settings, and by 2.9–3.2% over a static entropy gate. However, in stationary homogeneous regimes—where a single fixed policy is near-optimal—the bandit router underperformed the best fixed policy by 1.5–3.2%, as exploration and bin-local learning incurred unnecessary regret. These results are conditional and simulation-only: the entropy-to-acceptance relationship is synthetic, and no real LLM serving benchmark or hardware measurement supports deployment claims. The approach appears algorithmically viable for heterogeneous or nonstationary workloads but is not a universal replacement for a well-chosen fixed speculation policy.

---

## 1 Introduction

Speculative decoding reduces the latency of autoregressive transformer inference by proposing multiple candidate tokens from a fast draft model and verifying them in a single forward pass of the target model. Prior work has demonstrated 2×–3× speedups with identical output distributions when the draft and target models agree sufficiently often (Leviathan et al., 2023; Chen et al., 2023). Subsequent work has explored multi-head and tree-structured candidate verification, establishing that multiple speculative policies and candidate structures constitute a plausible design surface (Cai et al., 2024; Miao et al., 2023).

The effectiveness of a given speculation policy depends on the agreement rate between draft and target models, which correlates with the entropy of the target model's next-token distribution. Low-entropy (confident) predictions tend to yield longer accepted prefixes, favoring aggressive speculation with longer drafts. High-entropy predictions yield shorter accepted prefixes, where the overhead of generating long drafts is wasted. This suggests that routing among multiple speculation policies conditioned on entropy could improve throughput relative to any single fixed policy.

However, the optimal mapping from entropy to policy is not known a priori and may shift over time as input distributions change. A contextual bandit formulation offers a natural learning mechanism: the router observes entropy, selects a policy, and receives reward based on accepted tokens per unit latency, updating its preferences online.

This paper asks: **Can a router that uses target entropy plus online bandit feedback choose among multiple speculative decoding policies better than a single fixed policy or a static entropy gate?**

We evaluate this question in a self-contained toy simulator and report both positive and negative findings. We are explicit about what these results do *not* establish: no real model pair, no CUDA or hardware-level measurement, and no serving-framework integration were involved.

---

## 2 Method

### 2.1 Speculative Decoding Model

We model speculative decoding with an accounting approximation. On each step, a draft policy proposes a sequence of *k* candidate tokens. The target model verifies the sequence in a single forward pass. The accepted prefix length *a* (0 ≤ *a* ≤ *k*) depends on the agreement between draft and target distributions. The verifier then emits *a* + 1 tokens (the accepted prefix plus one correction or extra token). The latency cost includes draft generation cost (increasing with *k*) and a single target verification pass (increasing sublinearly with *k*).

The per-step reward is:

$$r = \frac{a + 1}{c_{\text{draft}}(k) + c_{\text{verify}}(k)}$$

where $c_{\text{draft}}(k)$ and $c_{\text{verify}}(k)$ are the draft and verification costs for draft length *k*.

This is a toy approximation. Real speculative decoding costs depend on GPU memory hierarchy, batch scheduling, KV-cache management, and draft/target model sizes. The sublinear verification cost assumption may not hold across all hardware configurations.

### 2.2 Policies

Three speculation policies are modeled:

1. **conservative_k2**: Draft length *k* = 2. Low draft cost, robust at high entropy where acceptance rates are short.
2. **balanced_k4**: Draft length *k* = 4. Medium draft cost, best in low-to-medium entropy.
3. **aggressive_k8**: Draft length *k* = 8. High draft cost, best only when draft–target agreement is high (low entropy).

### 2.3 Entropy-to-Acceptance Relationship

The simulator uses a synthetic but plausible mapping from per-token entropy to expected acceptance length. Low entropy yields longer accepted prefixes; high entropy yields shorter prefixes. The exact functional form is defined in the simulator source (`scripts/spec_router_sim.py`). This relationship has not been validated against real model pairs.

### 2.4 Routers Compared

Five router configurations are evaluated:

1. **fixed_0_conservative_k2**: Always selects conservative_k2.
2. **fixed_1_balanced_k4**: Always selects balanced_k4.
3. **fixed_2_aggressive_k8**: Always selects aggressive_k8.
4. **static_entropy_gate**: Hand-coded entropy thresholds mapping entropy ranges to policies without learning.
5. **entropy_binned_ucb** (proposed): Contextual UCB bandit that bins the entropy space into discrete bins and maintains per-bin action-value estimates with exponential decay. The UCB exploration bonus encourages trying alternatives within each entropy regime, while decay allows adaptation to nonstationary reward distributions.

A sixth router, **noncontext_eps_greedy**, was also implemented but is not the focus of the reported comparisons.

### 2.5 Workload Regimes

Four regimes are tested:

- **mixed + nonstationary**: Entropy varies across low, medium, and high regimes with nonstationary shifts over time.
- **drift + nonstationary**: Entropy drifts smoothly over time with nonstationary reward perturbations.
- **low stationary**: Persistent low-entropy traffic (homogeneous).
- **high stationary**: Persistent high-entropy traffic (homogeneous).

### 2.6 Experimental Protocol

Each configuration is run for 30,000 steps across 30 independent random seeds. The primary metric is mean tokens per latency unit. Results are aggregated across seeds. Memory telemetry is collected via `/usr/bin/time -v`.

---

## 3 Results

### 3.1 Heterogeneous and Nonstationary Regimes

| Regime | Proposed (entropy_binned_ucb) | Best Fixed | vs. Best Fixed | vs. Static Gate |
|---|---:|---:|---:|---:|
| mixed + nonstationary | 1.9572 | 1.8583 (conservative_k2) | +5.32% | +3.20% |
| drift + nonstationary | 1.9488 | 1.8581 (conservative_k2) | +4.88% | +2.93% |

In both heterogeneous and nonstationary settings, the proposed entropy-binned UCB router outperformed every fixed policy and the static entropy gate. The best fixed policy in these regimes was consistently conservative_k2, suggesting that a risk-averse default is the strongest non-adaptive baseline when entropy varies widely. The bandit router's ability to switch to balanced or aggressive policies in low-entropy windows recovered throughput that the fixed conservative policy leaves on the table.

The improvement over the static gate (2.9–3.2%) indicates that learning the entropy-to-policy mapping online provides gains beyond hand-coded thresholds, particularly when the mapping shifts over time. However, these margins are modest and should be interpreted in the context of a toy simulation with synthetic acceptance curves.

### 3.2 Stationary Homogeneous Regimes

| Regime | Proposed (entropy_binned_ucb) | Best Fixed | vs. Best Fixed | vs. Static Gate |
|---|---:|---:|---:|---:|
| low stationary | 2.3869 | 2.4232 (balanced_k4) | −1.50% | +9.78% |
| high stationary | 1.6500 | 1.7051 (conservative_k2) | −3.23% | −1.84% |

In stationary homogeneous regimes, the bandit router underperformed the best fixed policy. In the low-entropy setting, balanced_k4 is near-optimal and the bandit's exploration of inferior policies incurs regret (−1.50%). In the high-entropy setting, conservative_k2 dominates and exploration is actively harmful (−3.23%).

Notably, in the low-entropy regime, the bandit router substantially outperformed the static gate (+9.78%), suggesting the static gate's hand-coded thresholds were poorly tuned for this regime. In the high-entropy regime, the static gate also underperformed the best fixed policy, and the bandit router did slightly worse than even the static gate (−1.84%).

These negative results are important: they establish that the bandit router is not universally beneficial. When the workload is homogeneous and stationary, the exploration overhead and bin-local learning introduce unnecessary regret.

### 3.3 Memory and Resource Posture

Memory telemetry from calibrated runs shows a lightweight footprint: maximum RSS approximately 20 MB, with 122 GB of available memory and zero swap activity. The simulator itself is not representative of a production serving system's memory profile, but this confirms the simulation runs were not resource-constrained.

---

## 4 Limitations

1. **Simulation-only evidence.** All results come from a transparent toy simulator (`spec_router_sim.py`). The entropy-to-acceptance curves are synthetic and plausible but not validated against real model pairs. No real LLM inference, CUDA kernels, or serving framework was involved. These are toy simulation results, not llama.cpp hook-prototype results, CUDA copy calibrations, or final production validations.

2. **No hardware-level validation.** The latency model uses an accounting approximation. Real speculative decoding costs depend on GPU memory hierarchy, batch scheduling, KV-cache management, and draft/target model sizes. The sublinear verification cost assumption may not hold across all hardware configurations.

3. **Negative results in homogeneous regimes.** The bandit router is not beneficial when traffic is stationary and homogeneous. In such settings, the exploration overhead and bin-local learning introduce unnecessary regret. The approach is conditionally useful, not universally superior.

4. **Limited policy space.** Only three policies with fixed draft lengths are modeled. Real systems may offer a richer policy space (tree-structured speculation, variable draft lengths, multiple draft models), which could change the regret landscape in either direction.

5. **No real entropy traces.** Per-token entropy distributions in real LLM serving may differ from the synthetic patterns used here. The relationship between entropy and acceptance rate may be noisier or more structured than modeled.

6. **Router overhead not measured in a serving loop.** The bandit computation itself is negligible in simulation but has not been profiled inside a real inference serving loop where microsecond-level overhead matters.

7. **No quality preservation audit.** The simulator assumes speculative decoding preserves output quality by construction. In practice, numerical precision, sampling strategies, and verification correctness require separate validation.

8. **Claim ledger is empty.** The automated claim extraction process did not produce structured claims for this artifact. The claim ledger audit status is "blocked_empty_claims," meaning no structured claims were extracted that reference public evidence files. The findings reported here are drawn directly from the run notes and project decision record and have not passed a formal claim/evidence audit.

---

## 5 Reproducibility Checklist

- **Simulator source**: `scripts/spec_router_sim.py` — self-contained Python script.
- **Command to reproduce smoke test**: `python3 scripts/spec_router_sim.py --steps 200 --seeds 2 --pattern mixed --nonstationary --outdir results/smoke`
- **Command to reproduce calibrated runs**: `python3 scripts/spec_router_sim.py --steps 30000 --seeds 30 --pattern {mixed,drift,low,high} {--nonstationary} --outdir results/{regime}`
- **Seeds**: 30 independent seeds per regime.
- **Random number generation**: Python `random` module (seeded per run).
- **Output format**: `summary.json` and `runs.csv` per regime.
- **Hardware**: Runs executed on a machine with ≥122 GB available RAM, zero swap. Max RSS ≈20 MB.
- **Software dependencies**: Python 3 (standard library only; no external packages required by the simulator).
- **Raw logs**: `logs/smoke.log`, `logs/calibrated_runs.log`.
- **Evidence status**: The claim ledger for this paper contains no structured claims and has audit status "blocked_empty_claims." Findings are summarized from run notes and the project decision record but have not passed formal claim/evidence audit.

---

## 6 Conclusion

An entropy-binned online UCB bandit router for multi-policy speculative decoding shows conditional promise in toy simulation. In heterogeneous and nonstationary entropy regimes—where no single fixed policy is consistently optimal—the bandit router improved throughput by 4.9–5.3% over the best fixed policy and 2.9–3.2% over a static entropy gate. These gains arise from the router's ability to adapt its policy selection as entropy conditions change.

However, in stationary homogeneous regimes, the bandit router underperformed the best fixed policy by 1.5–3.2%, demonstrating that exploration and contextual learning add regret when a single policy is already near-optimal. The approach is therefore a workload-adaptive mechanism, not a universal improvement.

The critical next step is validation on real LLM decoding traces: collecting per-token entropy, draft acceptance lengths, and verifier latency from actual model pairs, then replaying the router logic on those traces. Only such trace-driven evaluation can determine whether the synthetic entropy-to-acceptance relationship holds in practice and whether router overhead remains negligible in a real serving loop. Until then, the results reported here should be interpreted as algorithmic viability evidence from a toy simulation, not as a deployment-ready claim.

---

## Referenced Artifacts

| Artifact | Path / Identifier |
|---|---|
| Simulator source | `scripts/spec_router_sim.py` |
| Smoke test results | `results/smoke/summary.json`, `results/smoke/runs.csv` |
| Mixed nonstationary results | `results/mixed_nonstationary/summary.json`, `results/mixed_nonstationary/runs.csv` |
| Drift nonstationary results | `results/drift_nonstationary/summary.json`, `results/drift_nonstationary/runs.csv` |
| Low stationary results | `results/low_stationary/summary.json`, `results/low_stationary/runs.csv` |
| High stationary results | `results/high_stationary/summary.json`, `results/high_stationary/runs.csv` |
| Smoke test log | `logs/smoke.log` |
| Calibrated runs log | `logs/calibrated_runs.log` |
| Run notes | `run_notes.md` |
| Project decision record | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260506T005040218197+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260506T005040218197+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260506T005040218197+0000/paper_manifest.json` |
| Project identifier | `source-record-redacted` |
| Run identifier | `source-record-redacted-20260506T005040218197+0000` |

### Supporting External Sources

- Leviathan, Kalman, and Matias, *Fast Inference from Transformers via Speculative Decoding*, ICML 2023. https://proceedings.mlr.press/v202/leviathan23a.html
- Chen et al., *Accelerating Large Language Model Decoding with Speculative Sampling*, arXiv:2302.01318. https://arxiv.org/abs/2302.01318
- Cai et al., *Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads*, arXiv:2401.10774. https://arxiv.org/abs/2401.10774
- Miao et al., *SpecInfer: Accelerating Generative Large Language Model Serving with Tree-based Speculative Inference and Verification*, arXiv:2305.09781. https://arxiv.org/abs/2305.09781
