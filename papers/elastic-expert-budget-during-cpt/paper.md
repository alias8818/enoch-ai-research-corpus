# Elastic Expert Budget During Continual Pre-Training: A Toy-Scale Viability Study

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Mixture-of-experts (MoE) models conventionally activate a fixed number of experts per token. During continual pre-training (CPT), where token difficulty and domain composition shift across the training stream, a fixed budget may be suboptimal. We investigate whether an elastic per-token expert activation budget—allocating additional experts to tokens the router identifies as uncertain—can improve loss and accuracy over fixed-budget baselines at the same or lower average compute. In a controlled NumPy toy MoE classifier experiment across 12 seeds, we compare five policies: fixed top-1, fixed top-2, random extra-budget allocation, and two elastic policies (router-entropy and router-margin) that grant a second expert to the 35% most uncertain tokens. Router-entropy elastic budgeting (1.35 average expert calls per token) reduces mean loss by 0.389 over fixed top-1, by 0.022 over random extra-budget allocation at the same average calls, and by 0.009 over fixed top-2 despite using 32.5% fewer expert calls. These results support the viability of elastic expert budgeting as a research direction, but they do not establish that the effect survives transformer-scale CPT, distributed expert parallelism, real text corpora, or hardware kernel constraints. We report all results with honest uncertainty and detail the gap between toy-scale evidence and scientific closure.

## 1. Introduction

Continual pre-training (CPT) is a widely used technique for adapting large language models to new domains while retaining prior knowledge. In MoE architectures, CPT introduces a particular tension: the router must allocate experts to tokens drawn from both the original and new domains, and a fixed top-k budget may be insufficient for tokens at the domain boundary or for harder examples.

Several lines of prior work identify related problems. Token-choice routing with fixed top-k can produce load imbalance across experts and token dropping under capacity constraints. Expert Choice Routing demonstrates that allowing variable expert counts per token can improve load balance and model quality. Dynamic Routing in MoE Models proposes adjusting activated experts by input difficulty, reporting gains over fixed top-2 with fewer activated parameters. Alloc-MoE formalizes activation budget redistribution at the token level under constrained expert activations. Expert Upcycling expands MoE capacity during continued pre-training while holding top-k fixed, which is adjacent to but distinct from elastic per-token budgeting. These prior works motivate the question but do not directly evaluate elastic per-token budgets during CPT.

The central question of this study is: during CPT, is it viable to use an elastic per-token expert activation budget, where tokens the router identifies as uncertain or hard receive additional experts, instead of a fixed top-k budget?

We approach this question conservatively. Rather than making claims at transformer scale, we implement a minimal toy MoE classifier and measure whether the elastic-budget signal is detectable at all in a controlled setting. A negative or null result at toy scale would have suggested the idea is unlikely to survive at scale; a positive result at toy scale is a viability signal but not scientific closure.

## 2. Method

### 2.1 Toy MoE Classifier

We implemented a dependency-light NumPy MoE classifier (`scripts/elastic_expert_budget_toy.py`) with the following components:

- **Experts:** 4 linear experts, each mapping a 16-dimensional input to class logits over 5 classes.
- **Router:** A linear gating network producing expert selection scores, followed by softmax normalization.
- **Training:** Standard cross-entropy loss with Adam optimizer (learning rate 1e-3).

### 2.2 Data Generation

Synthetic data is generated from two domains:

- **Domain A:** Inputs drawn from a Gaussian mixture with 3 components in 16 dimensions. Labels assigned by a linear teacher.
- **Domain B:** Inputs drawn from a different Gaussian mixture with 4 components. Labels assigned by a composed latent teacher (two linear transformations with a ReLU nonlinearity between them), making Domain B inherently harder.

The hard subset within Domain B is an explicit consequence of the composed teacher: tokens whose true class depends on the nonlinear interaction are harder for a linear expert to classify correctly.

### 2.3 Training Protocol

1. **Pre-training:** Train on Domain A for 260 steps with batch size 384.
2. **Continual pre-training:** Continue training on a stream of 70% Domain B / 30% Domain A for 340 steps with batch size 384.
3. **Evaluation:** Evaluate on 4096 samples from a held-out mixture of both domains after CPT.

All policies begin CPT from the same pretrained checkpoint, ensuring that differences arise from the CPT-phase routing policy alone.

### 2.4 Routing Policies

We compare five routing policies:

| Policy | Description | Avg expert calls |
|---|---|---:|
| `fixed1` | Standard top-1 routing | 1.00 |
| `fixed2` | Standard top-2 routing | 2.00 |
| `random_extra` | 35% of tokens receive a second expert, selected uniformly at random | 1.35 |
| `elastic_entropy` | 35% of tokens with highest router entropy receive a second expert | 1.35 |
| `elastic_margin` | 35% of tokens with lowest top1–top2 margin receive a second expert | 1.35 |

The `random_extra` policy controls for the effect of simply adding more expert capacity, isolating the contribution of the uncertainty-based selection criterion. Both elastic policies and `random_extra` are matched at 1.35 average expert calls per token, enabling fair compute-normalized comparison.

### 2.5 Uncertainty Signals

- **Router entropy:** $H = -\sum_i p_i \log p_i$, where $p_i$ is the router's softmax probability for expert $i$. High entropy indicates the router is uncertain among experts.
- **Router margin:** $m = p_{\text{top1}} - p_{\text{top2}}$. Low margin indicates the top two experts are nearly equally preferred.

### 2.6 Experimental Configuration

- **Seeds:** 12 independent runs per policy with different random seeds.
- **Hardware:** CPU-only NumPy execution on a system with an NVIDIA GB10 GPU (GPU utilization 0% for this experiment). Memory available before run: ~122,424 MB; after: ~122,423 MB. Max RSS: ~41 MB. No swap usage.
- **Wall-clock time:** 10.58 seconds for the full calibrated run (all seeds, all policies).

## 3. Results

### 3.1 Primary Results

Mean metrics over 12 seeds:

| Policy | Avg calls | loss_avg | acc_avg | loss_A | acc_A | loss_B | acc_B |
|---|---:|---:|---:|---:|---:|---:|---:|
| fixed1 | 1.00 | 1.2375 | 0.5334 | 1.4085 | 0.4774 | 1.0665 | 0.5894 |
| random_extra | 1.35 | 0.8705 | 0.6792 | 0.7710 | 0.7224 | 0.9700 | 0.6361 |
| elastic_entropy | 1.35 | **0.8486** | **0.6844** | **0.7321** | **0.7302** | **0.9651** | **0.6386** |
| elastic_margin | 1.35 | 0.8544 | 0.6818 | 0.7360 | 0.7315 | 0.9727 | 0.6320 |
| fixed2 | 2.00 | 0.8579 | 0.6788 | 0.7443 | 0.7249 | 0.9715 | 0.6328 |

### 3.2 Paired Comparisons

Paired deltas computed across the 12 seeds:

- **elastic_entropy vs fixed1:** loss_avg −0.3889, acc_avg +0.1510. Adding a second expert to 35% of tokens based on entropy substantially improves over fixed top-1.
- **elastic_entropy vs random_extra** (same 1.35 avg calls): loss_avg −0.0219, acc_avg +0.0052. The uncertainty-based selection criterion provides a measurable but small improvement over random allocation of the same extra budget.
- **elastic_entropy vs fixed2** (32.5% fewer calls): loss_avg −0.0093, acc_avg +0.0056. Elastic entropy slightly outperforms fixed top-2 despite using substantially fewer expert calls on average.

### 3.3 Domain-Specific Patterns

Both elastic policies show their largest gains on Domain A (the original domain retained during CPT). For Domain A, `elastic_entropy` achieves acc_A = 0.7302 versus `fixed2` acc_A = 0.7249, despite using 32.5% fewer expert calls. For Domain B, the differences between policies are smaller: `elastic_entropy` acc_B = 0.6386 versus `fixed2` acc_B = 0.6328. This pattern suggests that the elastic budget's primary benefit in this toy setup is in preserving performance on the original domain during CPT, rather than in accelerating adaptation to the new domain.

### 3.4 Entropy vs Margin

Router entropy slightly outperformed router margin as the uncertainty signal (loss_avg 0.8486 vs 0.8544; acc_avg 0.6844 vs 0.6818). However, the gap is small relative to the variance across seeds, and we do not consider this a definitive ranking of the two signals.

### 3.5 Negative and Mixed Observations

Several findings temper the positive direction:

- The improvement of elastic_entropy over random_extra is modest (loss_avg difference of 0.022). While consistent across seeds, this margin may not survive at scale or may be absorbed by other sources of variance in real training runs.
- The elastic_margin policy did not consistently outperform random_extra on Domain B (acc_B 0.6320 vs 0.6361), suggesting that not all uncertainty signals are equally effective and that margin-based selection may misallocate budget on the newer domain.
- No policy achieved high absolute accuracy on Domain B (best acc_B = 0.6386), reflecting the inherent difficulty of the composed teacher even with additional expert capacity.

## 4. Limitations

This study has substantial limitations that prevent drawing conclusions at transformer scale:

1. **Toy architecture.** The experiment uses linear experts on synthetic Gaussian-mixture data with 16-dimensional inputs and 5 classes. Real transformer MoE layers operate on high-dimensional residual streams with nonlinear FFN experts, layer normalization, and multi-head attention. The routing dynamics and expert specialization patterns may differ fundamentally.

2. **No wall-clock or throughput measurement.** The experiment measures expert-call budget (a proxy for compute) but not actual wall-clock training time or tokens-per-second. In a real distributed MoE system, dynamic per-token expert counts introduce irregular dispatch patterns that may reduce hardware utilization, potentially negating the compute savings suggested by the expert-call count.

3. **No kernel or communication cost modeling.** Elastic budgets require variable-size expert dispatch, which interacts with all-to-all communication in expert-parallel training and with GPU kernel efficiency. These costs are not captured here.

4. **Small scale and synthetic data.** The training runs involve 260 pretrain + 340 CPT steps on synthetic data. Real CPT involves billions of tokens from heterogeneous text corpora with complex domain boundaries.

5. **Narrow policy space.** We tested only two uncertainty signals (entropy and margin) and one extra-budget fraction (35%). The optimal fraction likely depends on domain difficulty, training stage, and model capacity. We did not explore per-layer budget schedules, curriculum-based budgeting, or other adaptive schemes.

6. **No inference-time evaluation.** CPT is often followed by fine-tuning and deployment. Whether elastic budgets during CPT produce models that are better at inference (with fixed or elastic budgets) is untested.

7. **Seed variance and statistical rigor.** While 12 seeds provide a reasonable sample for a toy experiment, the paired deltas between elastic and random-extra policies are small (loss_avg difference of 0.022), and we have not computed formal confidence intervals or performed significance testing. The direction of the effect is consistent across seeds, but the magnitude is modest and its statistical robustness is not formally established.

8. **Single architecture and hyperparameter setting.** All results are for a 4-expert, 16-dimensional model with a single learning rate and batch size. Sensitivity to these choices is unknown.

## 5. Reproducibility Checklist

- **Code available:** `scripts/elastic_expert_budget_toy.py` (syntax-validated via `python -m py_compile`).
- **Smoke test command:** `python scripts/elastic_expert_budget_toy.py --seeds 1 --pretrain-steps 5 --cpt-steps 5 --batch 32 --eval-n 128 --out metrics/smoke.json`
- **Calibrated run command:** `python scripts/elastic_expert_budget_toy.py --seeds 12 --pretrain-steps 260 --cpt-steps 340 --batch 384 --eval-n 4096 --extra-frac 0.35 --out metrics/elastic_expert_budget_toy_calibrated.json`
- **Primary data artifact:** `metrics/elastic_expert_budget_toy_calibrated.json`
- **Smoke test artifact:** `metrics/smoke.json`
- **Execution logs:** `logs/smoke.log`, `logs/calibrated_run.log`, `logs/paired_analysis.log`
- **Hardware:** CPU-only NumPy execution. NVIDIA GB10 GPU present but unused (0% utilization). System memory: ~122 GB available; max RSS: ~41 MB; no swap.
- **Wall-clock:** 10.58 seconds for full calibrated run.
- **Random seeds:** 12 seeds per policy. Seed handling is deterministic within the script.
- **Dependencies:** NumPy only (no PyTorch, JAX, or deep learning frameworks).
- **Statistical testing:** Not performed. Paired deltas are reported as raw means across seeds. Formal confidence intervals remain uncomputed.

## 6. Conclusion

In a controlled toy MoE classifier experiment, allocating a limited second-expert budget to high router-entropy tokens during continual pre-training improved average loss and accuracy over three baselines: fixed top-1 routing, random extra-budget allocation at the same average expert calls, and fixed top-2 routing despite using 32.5% fewer expert calls. The improvement over random allocation at matched compute is small but consistent across seeds, suggesting that the uncertainty-based selection criterion provides a genuine signal rather than a compute-quantity artifact.

However, this result constitutes a viability signal at toy scale, not scientific closure. The effect has not been validated at transformer scale, on real text corpora, under distributed expert parallelism, or with actual hardware throughput measurements. The gap between expert-call savings and wall-clock savings remains unmeasured and may be negative due to dispatch irregularity. The improvement over random allocation, while consistent, is modest in magnitude and its statistical significance has not been formally established.

We recommend the following next steps for any group pursuing this direction:

1. Replicate the core finding in a tiny transformer with a single MoE FFN layer on a small but real text corpus.
2. Measure both expert-call-normalized validation loss and actual tokens-per-second on target hardware.
3. Sweep the extra-budget fraction and compare additional uncertainty signals beyond entropy and margin.
4. Evaluate whether elastic CPT budgets produce models that are better at fixed-budget inference, or whether elastic budgets are also needed at inference time to realize the gains.

The decision from this run is `promising_continue`: local evidence justifies scaled CPT validation, but final scientific closure requires transformer-scale evidence with hardware dispatch measurements.

---

## Referenced Artifacts

| Artifact | Description |
|---|---|
| `run_notes.md` | Full research run notes including prior evidence review, experimental design, results, and interpretation |
| `scripts/elastic_expert_budget_toy.py` | NumPy toy MoE classifier implementation with all five routing policies |
| `metrics/smoke.json` | Smoke test output (1 seed, 5+5 steps, batch 32) |
| `metrics/elastic_expert_budget_toy_calibrated.json` | Primary calibrated results (12 seeds, 260+340 steps, batch 384) |
| `logs/smoke.log` | Smoke test execution log |
| `logs/calibrated_run.log` | Calibrated run execution log with `/usr/bin/time -v` telemetry |
| `logs/paired_analysis.log` | Paired delta comparisons across seeds |
| `.omx/project_decision.json` | Project decision record with key metrics, validation config, and rationale |
| `papers/.../claim_ledger.json` | Claim ledger (empty at time of draft generation) |
| `papers/.../evidence_bundle.json` | Evidence bundle linking to project and run IDs |
| `papers/.../paper_manifest.json` | Paper generation manifest with writer provider metadata |
