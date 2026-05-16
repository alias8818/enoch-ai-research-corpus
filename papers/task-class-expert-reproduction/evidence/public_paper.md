# Task-Class Conditioned Expert Fertility in Mixture-of-Experts Upcycling: A Controlled Synthetic Reproduction

**AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, and benchmark outputs). The operator who released the artifacts claims no personal authorship credit for the writing or the experimental results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

We investigate whether class-conditioned expert fertility—duplicating mixture-of-experts (MoE) sub-networks targeted at underperforming task or token classes, rather than selecting duplicates by global utility—improves balanced performance during MoE upcycling. In a controlled synthetic NumPy regression benchmark with 6 task classes, 4 initial linear experts, and 3 added duplicate experts, class-conditioned fertility consistently outperformed global-utility duplication under compute-limited continuation (25–200 post-upcycle gradient steps), winning 30/30 random seeds at 100 steps and reducing balanced average MSE by 2.61 absolute over the global baseline. However, under near-converged continuation (500 steps), both methods approach zero MSE and the global baseline becomes slightly superior, with the class-conditioned variant winning only 1/30 seeds. A kill condition based on average-loss tolerance triggers in 29/30 seeds at 500 steps. These results suggest that class-conditioned expert fertility accelerates adaptation for underperforming slices in compute-limited settings but does not constitute an unconditional final-quality improvement. The finding is conditional on the synthetic, small-scale nature of the benchmark and has not been validated in full transformer MoE training.

## Introduction

Mixture-of-experts (MoE) architectures allocate different sub-networks to different subsets of the input distribution via a learned router. When upcycling a dense model into an MoE—by duplicating sub-networks and initializing a router—deciding *which* experts to duplicate and *how* to bias the router is consequential. A natural baseline duplicates experts with the highest mean utility across all classes. However, this may systematically under-allocate capacity to rare or underperforming classes whose needs are diluted in the global average.

We test an alternative: identify the worst-performing classes before upcycling, duplicate the expert with highest utility *for those classes specifically*, and add a positive router-row bias only for those classes. We call this **class-conditioned expert fertility**.

The core question is whether class-conditioned fertility improves balanced (per-class-averaged) performance relative to global-utility duplication, and whether any improvement persists to convergence or is limited to the compute-limited adaptation regime.

This study is deliberately narrow in scope. We do not train a transformer MoE on natural data. Instead, we construct a minimal synthetic MoE regression problem in NumPy, where the mechanism and its failure modes can be isolated and reproduced with low computational cost. The trade-off is that generalization to production-scale MoE models is untested and must be established separately.

## Method

### Synthetic Benchmark Design

We implemented a controlled MoE regression benchmark in NumPy (no GPU or deep learning framework required). The benchmark is intentionally minimal to isolate the mechanism under test.

**Task classes.** Six classes, each with a distinct linear target function $y_c = W_c x + b_c$ where $x \in \mathbb{R}^{16}$. Classes 0 and 1 are intentionally underrepresented in the training distribution and share less structure with the majority classes (2–5).

**Initial model.** Four linear experts, each producing $y = W_e x + b_e$ with $W_e \in \mathbb{R}^{4 \times 16}$, $b_e \in \mathbb{R}^4$. A class-conditioned router produces per-class weight vectors over experts.

**Upcycling protocol.** Three new experts are added by duplicating existing experts. The selection criterion differs between conditions:

- **Global baseline:** Duplicate the three experts with highest mean utility, where utility is the per-class loss increase when masking that expert and renormalizing the router distribution. Router rows for all classes receive uniform bias toward duplicates.
- **Class-conditioned treatment:** Identify the worst-performing classes pre-upcycle. For each, duplicate the expert with highest utility *for that class*. Add a positive router-row bias only for the targeted underperforming classes.

**Training.** Post-upcycle gradient descent on the full training set for a variable number of steps (25–500), with learning rate held constant across conditions.

**Evaluation.** Per-class MSE on balanced class-specific evaluation sets, then averaged across classes (balanced average MSE). This ensures rare classes contribute equally to the metric.

### Utility Proxy

Expert utility is estimated by masking: for each class $c$ and expert $e$, compute the loss increase when expert $e$ is removed and the router distribution is renormalized. This is a forward-pass proxy rather than a gradient-norm accumulation, chosen for simplicity and determinism in the synthetic setting. Its fidelity as a utility measure in deeper or nonlinear architectures is not established.

### Experimental Conditions

We varied the number of post-upcycle training steps across {25, 50, 100, 200, 500}. For each step count, we ran 12 seeds (ablation phase) and confirmed key step counts (100, 500) with 30 seeds. A smoke test with 2 seeds validated the harness before full runs.

### Kill Condition

A kill condition was defined: if the class-conditioned balanced average MSE exceeds the global baseline balanced average MSE, the run is flagged. This captures whether the treatment is net-harmful at the evaluation point. The kill condition does not incorporate a tolerance margin; even marginal excess loss triggers the flag.

### Environment

All experiments ran on a Linux aarch64 host with an NVIDIA GB10 GPU visible but unused (PyTorch was not installed). Computation was CPU-only via NumPy. The host had approximately 122.9 GB available memory, no swap configured, and peak RSS across all runs was approximately 39 MB. No swap events occurred.

## Results

### Compute-Limited Regime (25–200 Post Steps)

Class-conditioned fertility consistently outperformed global-utility duplication when post-upcycle training was limited.

| Post Steps | Seeds | Global Avg MSE | CC Avg MSE | CC − Global | CC Wins | Worst-Class Rel. Gain | Kill Count |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 25 | 12 | 3.8136 | 2.5164 | −1.2972 | 12/12 | +0.2566 | 0 |
| 50 | 12 | 3.6168 | 1.1845 | −2.4324 | 12/12 | +0.6153 | 0 |
| 100 | 12 | 2.7782 | 0.1530 | −2.6252 | 12/12 | +0.9320 | 0 |
| 200 | 12 | 0.2456 | 0.0030 | −0.2426 | 11/12 | +0.9614 | 1 |

The 30-seed confirmation at 100 steps confirmed this pattern: class-conditioned fertility won all 30 seeds, with a mean MSE reduction of −2.6093 (SE = 0.2129) and zero kill-condition triggers.

The worst-class relative gain—defined as the fractional MSE reduction for the single worst-performing class under the global baseline—increased with post steps, reaching +0.93 at 100 steps. This indicates that the mechanism is particularly effective at recovering underperforming slices.

One seed at 200 steps triggered the kill condition, suggesting that the advantage narrows as both methods approach low MSE even before full convergence.

### Near-Convergence Regime (500 Post Steps)

At 500 post steps, both methods approach zero MSE on this linear problem, but the global baseline becomes slightly superior:

| Post Steps | Seeds | Global Avg MSE | CC Avg MSE | CC − Global | CC Wins | Worst-Class Rel. Gain | Kill Count |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 12 | 0.000184 | 0.000284 | +0.000101 | 1/12 | −0.3724 | 11 |
| 500 | 30 | 0.000178 | 0.000293 | +0.000115 | 1/30 | −0.4052 | 29 |

The 30-seed confirmation at 500 steps showed the class-conditioned variant winning only 1/30 seeds, with the kill condition triggering in 29/30 seeds. The absolute MSE difference is small (approximately 0.0001), but the direction is consistent: global-utility duplication achieves slightly lower balanced average MSE at convergence.

### Interpretation

The mechanism appears to accelerate routing adaptation toward underperforming classes, yielding large gains in the compute-limited regime. Given sufficient optimization steps on this simple problem, the global baseline catches up and slightly surpasses the class-conditioned approach. The class-conditioned router bias may introduce a mild distortion that slows final convergence relative to the globally-selected, less-biased configuration.

An important caveat: the reversal at 500 steps involves absolute MSE values near $10^{-4}$. Whether this small, consistent disadvantage would appear at meaningful loss scales in real MoE training—or whether it is an artifact of the linear problem structure—is unknown.

## Limitations

1. **Synthetic scale.** The benchmark uses 6 classes, 4 initial experts, 3 duplicate experts, and 16-dimensional inputs with linear targets. This is a toy regression problem, not a full transformer MoE with nonlinear experts, token-level routing, or realistic data distributions. Generalization to production-scale MoE models is untested.

2. **No GPU or deep learning framework.** PyTorch was not installed in the execution environment. The NVIDIA GB10 GPU was visible but unused. All computation was CPU/NumPy. This limits the complexity of the benchmark but also eliminates framework-specific confounds.

3. **Utility proxy.** Expert utility was estimated by masking loss increase rather than gradient-norm accumulation or second-order methods. The masking proxy may not capture expert importance accurately in deeper or nonlinear architectures.

4. **Linear targets only.** The synthetic task uses linear target functions. Real MoE routing involves nonlinear interactions between expert outputs and router decisions. The class-conditioned fertility mechanism may interact differently with nonlinear experts.

5. **Fixed upcycle budget.** Only 3 duplicate experts were added. The interaction between the number of duplicates, the number of underperforming classes, and the degree of class imbalance was not explored.

6. **Single learning rate and architecture.** Post-upcycle learning rate and model architecture were held fixed. Sensitivity to these hyperparameters is unknown.

7. **No token-level routing.** The benchmark uses class-level routing (each class has a fixed router row). Real MoE models route per-token, introducing additional stochasticity and routing dynamics not captured here.

8. **Kill condition without tolerance margin.** The kill condition flags any excess loss, no matter how small. At 500 steps, the absolute loss difference triggering the kill condition is on the order of $10^{-4}$. Whether this constitutes a practically meaningful degradation depends on the application.

## Reproducibility Checklist

- [x] **Code available.** Harness script: `scripts/task_class_expert_repro.py`
- [x] **Random seeds reported.** All runs used explicit random seeds; 12-seed and 30-seed ensembles reported.
- [x] **Environment logged.** `artifacts/logs/00_environment.log` records OS, CPU, GPU, Python version, installed packages.
- [x] **Pre/post telemetry.** `artifacts/logs/02_pre_full_telemetry.log` and `artifacts/logs/04_post_full_telemetry.log` record memory, swap, and GPU utilization.
- [x] **Result artifacts stored.** JSON output files for all runs stored under `artifacts/results/`.
- [x] **Summary metrics.** `artifacts/results/summary_metrics.csv` and `summary_metrics.json` aggregate all runs.
- [x] **Command lines recorded.** All invocations with flags logged in run notes.
- [x] **Resource usage measured.** `/usr/bin/time -v` captured max RSS (39 MB) and elapsed time; no swap events occurred.
- [x] **Negative results reported.** The 500-step regime where class-conditioned fertility loses to the global baseline is fully reported.
- [x] **Kill condition defined and evaluated.** Kill condition (CC avg MSE > global avg MSE) assessed for every run.

## Conclusion

Class-conditioned expert fertility—duplicating experts targeted at underperforming classes and biasing only those class router rows—produces substantial and consistent improvements in balanced average MSE under compute-limited continuation in a synthetic MoE regression benchmark. At 100 post-upcycle steps, the treatment won 30/30 seeds and reduced balanced average MSE by 2.61 absolute. However, this advantage does not persist to convergence: at 500 steps, the global-utility baseline achieves slightly lower balanced average MSE in 29/30 seeds, and the kill condition triggers accordingly.

The mechanism is best understood as an **adaptation-speed intervention** for underperforming slices, not an unconditional quality improvement. In practical terms, class-conditioned fertility may be valuable when upcycling compute budgets are limited or when rapid recovery of rare-class performance is prioritized. It should be paired with an average-loss tolerance gate that reverts to the global baseline if the treatment becomes net-harmful during extended training.

These findings are confined to a synthetic linear MoE regression setting. Validation in a real transformer MoE with token-level routing, nonlinear experts, and natural data remains necessary before drawing conclusions about production applicability.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Harness script | `scripts/task_class_expert_repro.py` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Summary metrics (CSV) | `artifacts/results/summary_metrics.csv` |
| Summary metrics (JSON) | `artifacts/results/summary_metrics.json` |
| Key positive result (100 steps, 30 seeds) | `artifacts/results/confirm_post_100_30seeds.json` |
| Key kill-condition result (500 steps, 30 seeds) | `artifacts/results/confirm_post_500_30seeds.json` |
| Smoke test result | `artifacts/results/smoke.json` |
| Ablation results (25–500 steps, 12 seeds) | `artifacts/results/ablation_post_{25,50,100,200,500}.json` |
| Confirmation results (100, 500 steps, 30 seeds) | `artifacts/results/confirm_post_{100,500}_30seeds.json` |
| Environment log | `artifacts/logs/00_environment.log` |
| Smoke log | `artifacts/logs/01_smoke.log` |
| Pre-run telemetry | `artifacts/logs/02_pre_full_telemetry.log` |
| Full 12-seed log | `artifacts/logs/03_full_12seeds.log` |
| Post-run telemetry | `artifacts/logs/04_post_full_telemetry.log` |
| Ablation logs | `artifacts/logs/ablation_post_{25,50,100,200,500}.log` |
| Confirmation logs | `artifacts/logs/confirm_post_{100,500}_30seeds.log` |
| Claim ledger | `papers/source-record-redacted-20260502T230548818793+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T230548818793+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T230548818793+0000/paper_manifest.json` |
