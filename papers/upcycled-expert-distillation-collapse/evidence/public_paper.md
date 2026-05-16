# Upcycled Expert Distillation Collapse: A Symmetry-Induced Failure Mode in Mixture-of-Experts Initialization

**AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, metrics, and decision records). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its contents.

---

## Abstract

Mixture-of-experts (MoE) models are sometimes initialized by "upcycling"—copying a single dense checkpoint into each expert slot. We investigate whether exact cloning of a dense distilled model into all MoE experts constitutes a collapse mode under pure knowledge distillation (KD). On a controlled synthetic mixture-of-linear-classifiers benchmark (4 experts, 16-dimensional input, 3 classes), we find that it does: cloned experts remain functionally identical throughout training (pairwise Jensen–Shannon divergence = 0.0), the router stays effectively uniform (perplexity ≈ 4.0 over 4 experts), and symmetry-broken variants achieve substantially lower distillation cross-entropy. Across five random seeds, the mean KD cross-entropy improvement over the cloned baseline is 0.269 nats (range 0.222–0.302). The mechanism is that permutation symmetry in the cloned initialization produces identical gradients for all experts and the router, preserving equality and preventing specialization. This is a local, synthetic demonstration of a collapse mechanism; it does not constitute a claim about production-scale transformer MoE distillation.

## 1. Introduction

Upcycling—initializing an MoE model by copying a single dense checkpoint into each expert—is a practical strategy for converting a trained dense model into a sparse architecture without training from scratch. The dense model's learned representations are preserved, and only the routing and expert specialization need to be discovered during subsequent training.

However, a fundamental symmetry problem arises when every expert begins as an identical copy and the training signal is pure knowledge distillation from a teacher. Under these conditions, all experts produce identical outputs for every input, receive identical gradients, and remain identical indefinitely. The router, observing no differentiation among experts, likewise receives no gradient signal to break uniformity. The system is trapped at a permutation-symmetric stationary point.

This paper asks: does this symmetry constitute a genuine collapse mode that prevents the MoE from specializing and approaching teacher performance, or does the system eventually escape through numerical noise or other implicit perturbations? We answer affirmatively on a controlled synthetic benchmark: exact cloning is a collapse mode, and the system does not self-correct within the training regimes we examined. We further show that even small explicit symmetry breakers (parameter noise at σ = 0.01, random initialization) are sufficient to escape the collapse and achieve substantially better distillation performance.

We emphasize at the outset that this is a synthetic, small-scale result. The collapse mechanism is general insofar as it follows from permutation symmetry, but its practical prevalence and magnitude in production-scale transformer MoE distillation pipelines remain unestablished.

## 2. Method

### 2.1 Synthetic Teacher

We construct a mixture-of-linear-classifiers teacher with the following configuration:

- Input dimension: 16
- Number of classes: 3
- Number of experts/modes: 4
- The teacher uses a true router that selects one of four linear classifiers based on input region, producing soft targets via softmax.

This design ensures that expert specialization is genuinely useful: the teacher's output distribution varies across input regions in a way that distinct expert functions can capture.

### 2.2 Student Variants

Three student MoE initialization strategies are compared:

1. **upcycled_clone**: Every expert is initialized from the same dense logistic regression baseline. The router is initialized uniformly. This is the naive upcycling strategy.
2. **upcycled_noise**: The same dense baseline is copied into every expert, then small Gaussian noise (σ = 0.01 or σ = 0.05) is added to expert parameters and/or router parameters. This tests whether minimal perturbation suffices to break the symmetry.
3. **random**: Fully asymmetric random initialization of all experts and router. This provides an upper bound on what is achievable without any upcycling benefit.

### 2.3 Training Protocol

All variants are trained under identical pure KD: the loss is cross-entropy between the student MoE output and the teacher's soft targets. No auxiliary losses are applied—no load-balancing penalties, no diversity objectives, no expert dropout, and no data partitioning across experts. This isolation is deliberate: it tests whether the KD signal alone can overcome the symmetry of cloned initialization.

### 2.4 Metrics

- **KD cross-entropy (KD CE)**: Cross-entropy of the student mixture output against teacher soft targets. Lower is better.
- **Expert Jensen–Shannon divergence (expert_JS)**: Mean pairwise JSD between expert output distributions across the evaluation set. Zero indicates that all experts produce identical distributions for every input.
- **Router perplexity**: Perplexity of the router's assignment distribution over the 4 experts. A value of 4.0 indicates a perfectly uniform router; lower values indicate increasing routing specialization.
- **Route-share balance**: Distribution of routing mass across experts, reported for diagnostic purposes.

### 2.5 Collapse Criterion

Collapse is identified when all three of the following hold:

1. Cloned experts exhibit near-zero output diversity (expert_JS ≈ 0).
2. The cloned router remains uniform (perplexity ≈ number of experts).
3. A non-cloned (symmetry-broken) variant improves KD CE by more than 0.01 nats over the cloned baseline.

The third criterion ensures that the collapse is consequential—that specialization would have been beneficial if it had occurred.

### 2.6 Implementation

The experiment is implemented in `scripts/upcycled_expert_distillation_collapse.py` using NumPy and scikit-learn only. No GPU or deep learning framework is required. This design choice prioritizes reproducibility and transparency over scale.

### 2.7 Hyperparameters and Run Configuration

| Parameter | Smoke test | Main run | Replicates |
|---|---|---|---|
| n (samples) | 4,000 | 24,000 | 24,000 |
| steps | 30 | 900 | 900 |
| batch size | default | 512 | 512 |
| learning rate | default | 0.55 | 0.55 |
| seeds | 0 | 0 | 1, 2, 3, 4, 5 |

The smoke test (4,000 samples, 30 steps) verified correct execution. The main calibrated run (24,000 samples, 900 steps, seed 0) provided the primary evidence. Five additional replicates (seeds 1–5) assessed robustness to random initialization.

## 3. Results

### 3.1 Smoke Test

The smoke test completed successfully in approximately 0.72 seconds wall time with peak RSS of approximately 186 MB. No anomalies were observed.

### 3.2 Main Calibrated Run

The main run (n = 24,000, 900 steps, seed 0) yields the following key results:

| Metric | Value |
|---|---|
| `supports_collapse` | true |
| Cloned expert_JS | 0.0 |
| Cloned router perplexity | 3.999999984 |
| Best non-clone KD CE | 0.7324 |
| KD CE improvement over clone | 0.2567 |

The cloned experts produce identical output distributions for every input (expert_JS = 0.0 exactly, not merely approximately). The router perplexity of 3.999999984 confirms that the router assigns effectively equal weight to all four experts throughout training. The best symmetry-broken variant achieves a KD CE that is 0.257 nats lower than the cloned baseline—a substantial gap relative to the cloned baseline's KD CE of approximately 0.989.

### 3.3 Five-Seed Robustness Check

All five replicates support the collapse finding (5/5). Summary statistics:

| Statistic | Value |
|---|---|
| Mean KD CE improvement over clone | 0.2687 |
| Minimum KD CE improvement over clone | 0.2219 |
| Maximum KD CE improvement over clone | 0.3019 |
| Maximum cloned expert_JS across all seeds | 0.0 |

Per-seed results:

| Seed | Clone KD CE | Best non-clone KD CE | Improvement | Cloned expert_JS | Best variant |
|---:|---:|---:|---:|---:|---|
| 1 | 1.0200 | 0.7484 | 0.2716 | 0.0 | upcycled_noise σ=0.01 |
| 2 | 0.9892 | 0.7407 | 0.2484 | 0.0 | upcycled_noise σ=0.01 |
| 3 | 0.9613 | 0.6593 | 0.3020 | 0.0 | upcycled_noise σ=0.05 |
| 4 | 1.0007 | 0.7011 | 0.2996 | 0.0 | random |
| 5 | 0.9711 | 0.7493 | 0.2219 | 0.0 | random |

Several observations merit attention:

- **The collapse is consistent.** In every seed, cloned experts remain exactly identical (expert_JS = 0.0), and the router remains uniform. The system does not self-correct through numerical noise or implicit perturbations within 900 training steps.
- **The improvement from symmetry breaking is substantial.** The minimum improvement across seeds is 0.222 nats, and the maximum is 0.302 nats. These are large relative to the cloned baseline KD CE values (0.96–1.02), indicating that the collapse is not a minor inefficiency but a qualitative failure to learn the teacher's expert structure.
- **The best symmetry-breaking strategy varies.** In seeds 1 and 2, the best variant is `upcycled_noise` with σ = 0.01; in seed 3, it is `upcycled_noise` with σ = 0.05; in seeds 4 and 5, it is `random` initialization. This variation suggests that the optimal perturbation scale may depend on the specific random draw, but even the smallest tested perturbation (σ = 0.01) consistently escapes the collapse.
- **No intermediate regime was observed.** The cloned variants do not show partial specialization—they remain exactly identical. The transition from collapse to specialization appears to be triggered by any nonzero symmetry breaking in this benchmark.

### 3.4 Mechanistic Interpretation

The collapse mechanism is straightforward: under exact cloning, all experts produce the same distribution for every sample. With a uniform router, each expert receives the same gradient. The router gradient is also symmetric because every expert contributes identically to the mixture loss. Training therefore preserves equality of experts and cannot discover mode specialization without an asymmetry source.

Formally, the cloned initialization is a fixed point of the training dynamics under pure KD: if all experts are identical and the router is uniform, the gradient step preserves both properties. This fixed point is not an artifact of learning rate or step count—it is a structural property of the loss landscape under permutation symmetry.

Small noise perturbations (σ = 0.01) are sufficient to break this symmetry and allow the MoE to specialize toward the teacher's mode structure. The fact that even minimal perturbation works suggests that the loss landscape near the symmetric fixed point has directions of decreasing loss that are accessible once the symmetry is broken, but inaccessible from the symmetric point itself.

### 3.5 Resource Usage

All runs were CPU-only. The main calibrated run required approximately 2.78 seconds wall time with peak RSS of approximately 194 MB. No swap was used. System memory available before runs was approximately 117 GiB. Resource constraints were not a factor in any run.

## 4. Limitations

1. **Synthetic scale.** This is a controlled synthetic experiment using linear classifiers in 16 dimensions with 4 experts and 3 classes. It is not a transformer-scale result. The magnitude and prevalence of this collapse mode in production MoE distillation pipelines remain unestablished. The linear classifier setting may amplify or suppress the collapse relative to deep networks.

2. **Task simplicity.** The mixture-of-linear-classifiers benchmark is intentionally constructed so that specialization is useful. In real MoE settings, the degree to which specialization helps may vary by domain, architecture, and data distribution. It is possible that in some settings, the collapse is inconsequential because specialization provides little benefit.

3. **No auxiliary objectives.** The experiment uses pure KD without load-balancing penalties, diversity objectives, expert dropout, or data partitioning—all of which are common in practice and may partially mitigate collapse even under cloned initialization. The experiment isolates the KD-only regime to establish the mechanism, but this isolation means the results represent a worst case that may not fully apply to pipelines with such mitigations.

4. **Single architecture family.** Only one synthetic MoE configuration (4 experts, 16-dim input, 3 classes) is tested. The collapse mechanism is general—it follows from permutation symmetry—but the quantitative improvement from symmetry breaking, the sensitivity to perturbation scale, and the dynamics of escape may differ across architectures.

5. **No transformer-scale validation.** Final production relevance would require evidence from actual MoE training logs, router/expert-diversity telemetry, and ablations at transformer scale. Such evidence is not present in the current artifacts.

6. **Finite training horizon.** The experiments run for 900 steps. While the cloned experts show no tendency toward de-symmetrization, we cannot rule out that much longer training might eventually produce divergence through accumulated floating-point effects. However, the practical relevance of such slow escape, if it exists, would be limited.

7. **No analysis of partial upcycling.** We test only the extreme case where all experts are cloned. Partial upcycling (cloning some experts while randomly initializing others) may exhibit different dynamics and is not examined here.

## 5. Reproducibility Checklist

- **Code available:** `scripts/upcycled_expert_distillation_collapse.py` (NumPy + scikit-learn, no GPU required).
- **Dependencies:** NumPy, scikit-learn, Python 3.
- **Random seeds:** Seeds 0 (main), 1–5 (replicates) are specified and logged.
- **Hyperparameters:** n = 24,000, steps = 900, batch = 512, lr = 0.55 for main and replicate runs; n = 4,000, steps = 30 for smoke test.
- **Hardware:** CPU-only; peak RSS < 200 MB; wall time ~2.8 s for main run, ~0.7 s for smoke test. No GPU or specialized hardware required.
- **Output artifacts:** All metric JSON files and logs are referenced in the Referenced Artifacts section below.
- **Statistical robustness:** 5/5 replicates support the collapse finding. The minimum improvement over clone across seeds is 0.222 nats, well above the 0.01-nat collapse criterion.
- **Determinism:** Results are deterministic given the specified seeds and hyperparameters. Floating-point reproducibility across platforms has not been verified but is expected given the simplicity of the computation.

## 6. Conclusion

Exact cloned upcycling of a dense distilled model into all MoE experts is a collapse mode under pure knowledge distillation. On a synthetic mixture-of-linear-classifiers benchmark, cloned experts remain functionally identical throughout training (expert_JS = 0.0 exactly), the router stays uniform (perplexity ≈ 4.0), and symmetry-broken variants achieve 0.22–0.30 nats lower KD cross-entropy across five random seeds. The mechanism is that permutation symmetry in the initialization produces identical gradients for all experts and the router, preserving equality and preventing specialization.

This result establishes a local, reproducible counterexample to naive exact-clone upcycling under pure KD. It does not establish the prevalence or magnitude of this collapse in production-scale transformer MoE distillation, where auxiliary objectives, data partitioning, and architectural differences may alter the dynamics. The result does, however, identify a clear mechanism that practitioners should account for: if upcycled initialization is used, at least one symmetry-breaking mechanism should be present—whether parameter noise, expert diversity initialization, router pretraining, load-balancing or mode-discovery objectives, or data partitioning across experts.

The question of how this collapse manifests at transformer scale, and which mitigation strategies are most effective in that regime, remains open.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `scripts/upcycled_expert_distillation_collapse.py` |
| Smoke test log | `logs/smoke.log` |
| Main run log | `logs/main.log` |
| Replicate logs | `logs/replicates/seed_1.log`, `logs/replicates/seed_2.log`, `logs/replicates/seed_3.log`, `logs/replicates/seed_4.log`, `logs/replicates/seed_5.log` |
| Main metrics | `results/main/synthetic_moe_distillation_metrics.json` |
| Smoke metrics | `results/smoke/synthetic_moe_distillation_metrics.json` |
| Replicate metrics | `results/replicates/seed_1/synthetic_moe_distillation_metrics.json`, `results/replicates/seed_2/synthetic_moe_distillation_metrics.json`, `results/replicates/seed_3/synthetic_moe_distillation_metrics.json`, `results/replicates/seed_4/synthetic_moe_distillation_metrics.json`, `results/replicates/seed_5/synthetic_moe_distillation_metrics.json` |
| Replicate summary | `results/replicates_summary.json` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260502T235552145786+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T235552145786+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T235552145786+0000/paper_manifest.json` |
