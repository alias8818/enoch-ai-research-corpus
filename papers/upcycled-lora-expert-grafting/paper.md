# Upcycled LoRA Expert Grafting: A Synthetic Proof-of-Mechanism Study

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has verified these claims.

---

## Abstract

We investigate whether independently trained LoRA-style low-rank adapters can be upcycled into frozen experts and grafted behind a small learned router, as an alternative to naive weight-averaging adapter merging. In a controlled synthetic classification setting with a frozen random feature extractor and two conflicting domains, we train rank-2 LoRA deltas per task, freeze them as experts, and learn only a linear softmax router over their logits. Across 10 random seeds, the grafted-router configuration achieves mean accuracy of 92.64% (σ = 0.36%), compared to 76.98% for averaged adapter merging, 77.28% for a single multitask rank-2 LoRA, and 77.26% for a single multitask rank-4 LoRA. An oracle domain-expert selector achieves 93.59%, yielding a mean gap of 0.95 percentage points between grafted routing and perfect selection. The router learns domain assignments with 97.82% mean accuracy. These results constitute a positive proof-of-mechanism in a simplified setting. They do not establish viability on pretrained transformers, real language tasks, token-level routing, or production inference engines.

---

## Introduction

Low-rank adaptation methods produce small delta weight matrices that modify a frozen base model for a target task. When multiple such adapters are trained independently for different tasks, a practical question arises: how should they be combined at inference time?

The simplest approach—averaging or linearly merging adapter weights—risks destructive interference between task-specialized directions. An alternative is to retain adapters as separate experts and route inputs to the appropriate one, analogous to mixture-of-experts architectures but constructed from existing LoRA checkpoints rather than trained end-to-end.

We term this approach *upcycled LoRA expert grafting*: freezing independently trained LoRA deltas as distinct experts and learning a lightweight router that selects among them at inference time. This study provides a minimal, controlled test of the core mechanism. We do not address the full complexity of transformer-based language models, token-level routing, or production deployment. Rather, we ask: in a setting where naive merging is known to fail due to task conflict, does a learned router over frozen experts recover task-specialized performance?

---

## Method

### Problem Setting

We construct a synthetic classification environment with the following components:

1. **Frozen random feature extractor.** A fixed random projection maps input vectors to a hidden representation of dimension $h = 64$. The projection is not trained.
2. **Frozen base classifier head.** A fixed linear head maps hidden representations to class logits. This head is shared across domains and is not trained.
3. **Two conflicting synthetic domains.** Each domain has its own input distribution and label structure, designed so that a single shared adapter cannot simultaneously serve both domains well.

### Adapter Training

For each domain $d \in \{1, 2\}$, we train a rank-2 LoRA-style delta matrix:

$$\Delta_d = B_d A_d$$

where $A_d \in \mathbb{R}^{r \times h}$ and $B_d \in \mathbb{R}^{h \times r}$ with $r = 2$ and $h = 64$. The base model parameters remain frozen throughout. Each adapter is trained on its domain's data alone for 350 steps with learning rate 0.2.

### Expert Grafting and Router Training

After training, both $\Delta_1$ and $\Delta_2$ are frozen. A small linear softmax router is then trained over the frozen experts' logit outputs on a mixed-domain training set. The router takes the base model's hidden representation as input and outputs a distribution over experts. Only the router parameters are updated during this phase, for 250 steps with learning rate 0.2.

At inference, the router selects the expert whose logits are used for the final prediction.

### Baselines

We compare against five configurations:

- **No adapter.** The frozen base model alone, with no adaptation.
- **Averaged adapter merge.** The element-wise average of $\Delta_1$ and $\Delta_2$ applied to the base model.
- **Single multitask rank-2 LoRA.** A single rank-2 adapter trained on mixed-domain data from scratch.
- **Single multitask rank-4 LoRA.** A single rank-4 adapter trained on mixed-domain data from scratch (double the capacity of the per-task adapters).
- **Oracle domain expert.** Perfect domain identification routing each input to its correct expert.

### Implementation

The experiment is implemented in NumPy without deep learning framework dependencies (`experiments/lora_grafting_synthetic.py`). All runs execute on CPU. Per-seed wall time is approximately 0.83–0.91 seconds with peak RSS of approximately 58 MB. The host reports an NVIDIA GB10 GPU via `nvidia-smi`, but this GPU was not used; the experiment is CPU-only.

---

## Results

### Aggregate Metrics (10 Seeds)

All metrics are computed on held-out mixed-domain test sets of 2,000 examples per seed, with training sets of 4,000 examples per seed.

| Configuration | Mean Accuracy | Std. Dev. | Min | Max |
|---|---:|---:|---:|---:|
| No adapter | 0.5017 | 0.0617 | 0.3972 | 0.6032 |
| Averaged adapter merge | 0.7698 | 0.0084 | 0.7565 | 0.7853 |
| Single multitask rank-2 LoRA | 0.7728 | 0.0087 | 0.7622 | 0.7887 |
| Single multitask rank-4 LoRA | 0.7726 | 0.0088 | 0.7620 | 0.7887 |
| **Grafted frozen experts + router** | **0.9264** | **0.0036** | **0.9217** | **0.9323** |
| Oracle domain expert | 0.9359 | 0.0047 | 0.9293 | 0.9425 |

### Key Comparisons

- **Graft vs. averaged merge:** +15.66 percentage points mean accuracy (σ = 0.63 pp).
- **Graft vs. oracle:** −0.95 percentage points mean accuracy (σ = 0.26 pp).
- **Router domain-match rate:** 97.82% mean (σ = 0.20 pp).

### Observations

The averaged adapter merge, single multitask rank-2 LoRA, and single multitask rank-4 LoRA perform nearly identically (within ~0.3 pp of each other), suggesting that the two domains are sufficiently conflicting that neither increased rank nor weight averaging resolves the interference. Doubling the rank from 2 to 4 in the multitask setting provides no measurable benefit, indicating that the bottleneck is task conflict rather than adapter capacity.

The grafted-router configuration recovers most of the oracle performance, with a mean gap of 0.95 pp. The router's 97.82% domain-match rate indicates that the hidden representation carries sufficient domain-discriminative signal for routing, and the linear router learns this mapping reliably.

The no-adapter baseline's high variance (σ = 6.17 pp) reflects the random feature extractor's sensitivity to seed-dependent alignment with the two domain structures. This variance collapses once any adaptation is applied, as expected.

The remaining 0.95 pp gap between grafted routing and oracle is attributable to the 2.18% router domain-mismatch rate: misrouted examples receive the wrong expert's logits and are classified incorrectly at a higher rate. Whether this gap can be closed with more expressive routers, entropy regularization, or top-k routing remains untested.

---

## Limitations

This study has substantial limitations that constrain the generality of its conclusions:

1. **Synthetic setting only.** The feature extractor is a frozen random projection, not a pretrained transformer. The tasks are synthetic classification problems, not real language understanding tasks. The degree to which these results transfer to real PEFT checkpoints on pretrained models is unknown.

2. **Two-domain, example-level routing.** The experiment uses exactly two domains with example-level routing (one expert per input). Real deployment scenarios may involve many more experts, token-level routing, or ambiguous domain boundaries. The router's 2.18% domain-mismatch rate, while small in this setting, may grow substantially with more experts or less separable domains.

3. **No latency or memory profiling.** We do not measure the inference cost of maintaining multiple expert adapters and a router in a real transformer runtime. The memory overhead of storing $N$ frozen LoRA deltas scales linearly with $N$, and the routing computation adds per-example overhead that is not characterized here.

4. **No adapter compatibility validation.** All adapters are trained against the same frozen base model. The method's behavior when adapters target different base checkpoints (e.g., different fine-tuning stages) is not tested.

5. **No entropy regularization or fallback mechanisms.** The linear softmax router has no mechanism for expressing uncertainty or falling back to the base model. In ambiguous cases, a more sophisticated router with top-k routing, entropy thresholds, or expert dropout may be necessary.

6. **Small scale.** Hidden dimension 64, rank 2, two tasks, and a few thousand training examples constitute a minimal test. Scaling behavior with respect to hidden dimension, rank, number of experts, or dataset size is not characterized.

7. **No statistical hypothesis testing.** We report means and standard deviations across 10 seeds but do not compute confidence intervals or perform formal hypothesis tests. The effect sizes are large enough that informal comparison is suggestive, but rigorous statistical claims are not made.

---

## Reproducibility Checklist

- **Code available:** `experiments/lora_grafting_synthetic.py` (self-contained NumPy script; no GPU or deep learning framework required).
- **Random seeds reported:** Seeds 0–9; per-seed metrics stored in `results/metrics_seed_{0..9}.json`.
- **Aggregate metrics:** `results/aggregate_metrics.json`.
- **Corrected smoke test:** `results/smoke_metrics2.json`. An initial smoke test (`results/smoke_metrics.json`) is retained as diagnostic evidence of an earlier accuracy-accounting bug that was corrected before the calibrated run.
- **Execution log:** `logs/calibrated_multiseed_20260502T184832.log`.
- **Hardware:** CPU-only execution on a host reporting an NVIDIA GB10 GPU (unused). SwapTotal: 0 KiB. MemAvailable before run: ~122,864 MB; after run: ~122,807 MB. Per-seed max RSS: ~58 MB. Per-seed wall time: 0.83–0.91 sec (by `/usr/bin/time`); script-internal mean duration: 0.790 sec.
- **Hyperparameters:** `--train-n 4000 --test-n 2000 --hidden 64 --rank 2 --expert-steps 350 --router-steps 250 --lr 0.2 --router-lr 0.2`.
- **Statistical method:** 10-seed mean and standard deviation; no confidence intervals or hypothesis tests computed.

---

## Conclusion

In a controlled synthetic classification setting with two conflicting domains, upcycled LoRA expert grafting—freezing independently trained LoRA deltas as experts and learning a lightweight linear router over their outputs—substantially outperforms naive adapter averaging (+15.66 pp mean accuracy) and approaches oracle expert selection (−0.95 pp mean gap). The router learns domain assignments with 97.82% accuracy, confirming that the frozen base model's representations carry sufficient domain-discriminative signal for routing in this setting.

These results constitute a positive proof-of-mechanism but do not establish viability for practical use. The core finding—that preserving adapter specialization through routing outperforms destructive weight averaging—is supported by the present evidence only in a simplified synthetic setting with two domains, a random feature extractor, and example-level routing. Scientific closure requires validation on pretrained transformers with real or realistic LoRA adapters, characterization of scaling behavior with more experts, measurement of inference overhead in production runtimes, and evaluation under domain ambiguity. The evidence supports proceeding to a real-model experiment but does not warrant claims about production deployment or generalization to language models.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `experiments/lora_grafting_synthetic.py` |
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Corrected smoke metrics | `results/smoke_metrics2.json` |
| Diagnostic smoke metrics (pre-fix) | `results/smoke_metrics.json` |
| Per-seed metrics (seeds 0–9) | `results/metrics_seed_{0..9}.json` |
| Aggregate metrics | `results/aggregate_metrics.json` |
| Calibrated multi-seed log | `logs/calibrated_multiseed_20260502T184832.log` |
| Claim ledger | `papers/source-record-redacted-20260502T234551405823+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T234551405823+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T234551405823+0000/paper_manifest.json` |
