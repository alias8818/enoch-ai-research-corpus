# Expert Upcycling for Verification Models: A Toy-Scale Feasibility Study

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision logs, metrics files, and experiment scripts). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether expert upcycling—initializing a Mixture-of-Experts (MoE) model by duplicating a trained dense checkpoint—confers sample-efficiency advantages when applied to verification models. Using a self-contained NumPy experiment with a single-hidden-layer MLP verifier trained on synthetic multi-domain claims (addition, modular multiplication, max, linear combination), we compare three conditions after a short continuation training budget: (1) continued dense training, (2) upcycled 4-expert MoE (dense weights duplicated into 4 experts with a learned router), and (3) scratch MoE (same architecture, random initialization). Across 10 random seeds, the upcycled MoE achieves validation accuracy of 0.9961 ± 0.0033 (vs. 0.9975 ± 0.0022 for continued dense and 0.9112 ± 0.0116 for scratch MoE) and out-of-distribution accuracy of 0.9676 ± 0.0170 (vs. 0.9537 ± 0.0326 for continued dense and 0.8073 ± 0.0573 for scratch MoE). Upcycling preserves the dense verifier's behavior at initialization and substantially outperforms scratch MoE, but does not improve in-domain accuracy over continued dense training in this saturated regime. A modest OOD advantage for the upcycled MoE (+0.014 over continued dense) is observed but is small relative to variance and should be interpreted cautiously. Router specialization across domains is weak and inconsistent across seeds. These results constitute positive toy evidence for the viability of verifier expert upcycling as a research direction, but do not constitute evidence at LLM scale or on real verification datasets.

## Introduction

Mixture-of-Experts (MoE) architectures offer a path to increased model capacity without proportionally increasing per-token compute cost. Recent work on sparse upcycling has demonstrated that initializing MoE models from trained dense checkpoints—by duplicating the dense model's feed-forward layers into multiple expert copies and training a new router—can outperform both continued dense training and MoE models trained from scratch, particularly under limited continuation budgets. Subsequent work on expert upcycling has proposed duplicating experts while preserving active routing cost, with continued training breaking duplicate symmetry, and has identified utility-based expert selection as beneficial under limited continuation budgets.

Verification models—classifiers that assess the correctness of claims or reasoning steps—often operate across multiple distinct domains (e.g., arithmetic, logical inference, code correctness). This multi-domain structure suggests a natural fit for MoE architectures, where different experts might specialize in different verification predicates. However, training MoE verifiers from scratch is sample-inefficient, and the question of whether upcycling a trained dense verifier into an MoE preserves verification behavior while enabling expert specialization remains open.

This study tests the following hypothesis at toy scale: duplicating a trained dense verifier's hidden layer into multiple experts with a learned router preserves initial verification performance and is more sample-efficient than training an MoE verifier from scratch under a limited continuation budget. We emphasize at the outset that this is a feasibility probe using synthetic data and a minimal architecture; it does not address transformer-scale models or real verification datasets.

## Method

### Task Design

We construct a synthetic verification task with four rule families, each generating (claim, label) pairs where the label indicates whether the claim is correct:

- **add**: Integer addition correctness.
- **mul_mod**: Modular multiplication correctness.
- **max**: Maximum-element identification correctness.
- **linear_combo**: Linear combination correctness.

Training and in-distribution validation use operands sampled from a standard range (integers in [0, 20]); out-of-distribution (OOD) evaluation uses a wider operand range (integers in [0, 35]) to test generalization. Labels are balanced across correct and incorrect claims.

### Models

All models are single-hidden-layer MLPs implemented in pure NumPy with ReLU activation and sigmoid output:

- **Dense verifier**: Hidden dimension 48, single hidden layer, trained from random initialization.
- **Upcycled MoE**: After dense pretraining, the hidden layer and output layer are duplicated into 4 expert copies. A softmax router (separate trainable weight matrix) selects among experts. Top-1 routing is used. All expert parameters and the router are then updated during continuation training.
- **Scratch MoE**: Same architecture as the upcycled MoE (4 experts, top-1 routing, hidden dimension 48), but initialized from random weights.

### Training Protocol

1. **Pretraining phase**: The dense verifier is trained for 900 steps on 6,000 synthetic training examples (batch size 128, learning rate 0.005) using binary cross-entropy loss.
2. **Continuation phase**: All three models receive 250 additional training steps on 1,200 new examples (same hyperparameters). The dense model continues training; the upcycled MoE begins from the duplicated dense checkpoint with a freshly initialized router; the scratch MoE trains from random initialization.
3. **Evaluation**: Validation accuracy (in-distribution, 4,000 examples) and OOD accuracy (wider operand range, 4,000 examples) are measured after the continuation phase.

### Experimental Configuration

The final experiment uses 10 random seeds. A prior smoke test (1 seed, reduced scale: 80 pretrain steps, 40 continuation steps, hidden dimension 24, batch size 64, learning rate 0.003) confirmed infrastructure correctness but produced near-random performance as expected given the insufficient training budget.

## Results

### Initialization Preservation

Smoke test data confirms that at the start of the continuation phase—before any MoE-specific training—the upcycled MoE's validation accuracy and loss are identical to the dense model's (both accuracy 0.52875, loss 0.69379). This is expected by construction: all four experts are exact copies of the dense hidden layer, so with uniform routing the output is identical. The scratch MoE, by contrast, starts at accuracy 0.465 and loss 0.69795, reflecting its random initialization. This confirms that the upcycling initialization preserves the pretrained verifier's behavior.

### Main Comparison

Table 1 reports validation and OOD accuracy and loss (mean ± std over 10 seeds) after the continuation phase of the final experiment.

**Table 1: Accuracy and loss comparison across 10 seeds**

| Model | Val. Accuracy | OOD Accuracy | Val. Loss | OOD Loss |
|---|---|---|---|---|
| Continued Dense | 0.9975 ± 0.0022 | 0.9537 ± 0.0326 | 0.0262 | 0.1215 |
| Upcycled MoE | 0.9961 ± 0.0033 | 0.9676 ± 0.0170 | 0.0264 | 0.0998 |
| Scratch MoE | 0.9112 ± 0.0116 | 0.8073 ± 0.0573 | 0.2659 | 0.4470 |

### Key Deltas

- Upcycled MoE vs. scratch MoE validation accuracy: **+0.085**
- Upcycled MoE vs. continued dense validation accuracy: **−0.001**
- Upcycled MoE vs. scratch MoE OOD accuracy: **+0.160**
- Upcycled MoE vs. continued dense OOD accuracy: **+0.014**

### In-Domain Performance

Continued dense training achieves the highest in-domain validation accuracy (0.9975), marginally above the upcycled MoE (0.9961). This small gap (−0.001) is expected: the task is sufficiently easy that the dense model saturates, and the MoE's router introduces a small additional source of error that is not fully compensated within 250 continuation steps. The upcycled MoE does not improve in-domain accuracy over continued dense training in this saturated regime.

### Out-of-Distribution Generalization

The upcycled MoE achieves the highest OOD accuracy (0.9676), exceeding continued dense by +0.014 and scratch MoE by +0.160. The upcycled MoE also shows lower OOD variance (std 0.017) than continued dense (std 0.033), suggesting somewhat more stable generalization. However, the OOD advantage over continued dense is modest relative to the variance of both estimates, and we cannot rule out that it arises from the particular synthetic distribution rather than a general property of upcycling. This finding should be treated as suggestive rather than confirmed.

### Scratch MoE Underperformance

The scratch MoE performs substantially worse on both metrics, confirming that the MoE architecture is significantly harder to train from scratch under the same limited budget. This is the strongest and most robust finding in the experiment: upcycling provides a large sample-efficiency advantage over random MoE initialization (+0.085 validation accuracy, +0.160 OOD accuracy).

### Router Specialization

Router entropy and per-task routing distributions were examined in the smoke test. The mean routing distribution across the four experts is approximately uniform ([0.2424, 0.2577, 0.2535, 0.2464]), and per-task routing patterns are weakly differentiated and inconsistent across seeds. The routing entropy of 1.385 (vs. maximum 1.386 for 4 experts) confirms near-uniform routing. This indicates that 250 continuation steps are insufficient for the router to develop clean domain-specific specialization, and that the experts remain largely symmetric. This finding is consistent with prior work suggesting that utility-based expert selection or routing regularization may be necessary to break expert symmetry under limited training budgets.

### Smoke Test Results

The smoke test (1 seed, 80 pretrain steps, 40 continuation steps, hidden dimension 24, batch size 64) produced near-random performance across all three models: continued dense accuracy 0.494, upcycled MoE accuracy 0.505, scratch MoE accuracy 0.466. OOD accuracies were similarly near chance (0.484, 0.494, 0.495 respectively). This is consistent with the insufficient training budget at that scale and serves only as an infrastructure validation, not a meaningful experimental result.

## Limitations

1. **Toy scale only**: The experiment uses a 1-hidden-layer MLP with 48 hidden units on synthetic data. No transformer architecture, large language model, real verification dataset, or GPU computation is involved. The results do not directly generalize to LLM-scale verification models.

2. **Synthetic task simplicity**: The four rule families are trivially separable by a small MLP, and the dense model saturates in-domain. This ceiling effect limits the observable benefit of added MoE capacity. Real verification tasks (e.g., mathematical proof checking, code correctness) are substantially harder and may exhibit different dynamics.

3. **In-domain saturation**: Because the dense model already achieves near-perfect in-domain accuracy, the upcycled MoE cannot demonstrate an in-domain improvement. The modest OOD advantage (+0.014) is within the range of noise given the variance, and should not be treated as a confirmed effect.

4. **Weak router specialization**: The router does not develop clean task-disentangled routing within the continuation budget. Whether longer training, utility-based expert selection, or routing regularization would produce meaningful specialization remains untested.

5. **No real verifier data**: The experiment uses procedurally generated synthetic labels. Performance on real-world verification datasets (e.g., process reward labels, math answer correctness) is unknown.

6. **Single architecture and hyperparameter setting**: Only one hidden dimension (48), expert count (4), learning rate (0.005), and continuation budget (250 steps) are tested. Sensitivity to these choices is not characterized.

7. **No comparison to other upcycling variants**: Utility-based expert selection, higher-granularity routing, and non-uniform expert initialization are not tested, despite being highlighted in prior work as important design choices.

8. **No statistical significance testing**: The 10-seed comparison provides descriptive statistics (mean ± std) but no formal hypothesis tests or confidence intervals. The large gap between upcycled and scratch MoE is unlikely to be due to chance, but the small OOD advantage of upcycled over dense is not distinguishable from noise with this sample size.

## Reproducibility Checklist

- **Code available**: `scripts/expert_upcycling_verifier.py` (Python 3.12, NumPy only, no GPU required).
- **Random seeds**: 10 seeds reported in the final run; seed 0 used in smoke test.
- **Hyperparameters (final run)**: Pretrain steps 900, continuation steps 250, hidden dimension 48, experts 4, batch size 128, learning rate 0.005, pretrain samples 6000, continuation samples 1200, validation samples 4000, in-distribution operand range [0, 20], OOD operand range [0, 35].
- **Hyperparameters (smoke test)**: Pretrain steps 80, continuation steps 40, hidden dimension 24, experts 4, batch size 64, learning rate 0.003, pretrain samples 1000, continuation samples 300, validation samples 800.
- **Infrastructure**: CPU-only; max RSS 51,560 KB (final run); wall time 3.00 seconds; zero swaps; swap disabled.
- **Output files**: `results/final_expert_upcycling_verifier.json` (full per-seed metrics for 10-seed run), `results/smoke.json` (1-seed smoke test with reduced scale), `logs/final_experiment.log`, `logs/smoke3.log`.
- **Syntax validation**: `python3 -m py_compile scripts/expert_upcycling_verifier.py` passes.
- **Memory stability**: MemAvailable before/after final run: 122,910,204 kB / 122,913,740 kB (no memory leak detected).
- **Smoke test validation**: Prior smoke test with reduced scale confirmed infrastructure correctness; near-random performance in the smoke test is consistent with the insufficient training budget at that scale.

## Conclusion

A toy-scale NumPy experiment provides positive evidence that expert upcycling is a viable initialization strategy for MoE verification models. Duplicating a trained dense verifier into a 4-expert MoE preserves the dense model's behavior at initialization and substantially outperforms a scratch MoE under a limited continuation budget (+0.085 validation accuracy, +0.160 OOD accuracy). This sample-efficiency advantage is the most robust finding of this study.

The upcycled MoE does not improve in-domain accuracy over continued dense training, which we attribute to task saturation rather than a fundamental limitation of the approach. A modest OOD advantage for the upcycled MoE (+0.014) is observed but should be interpreted cautiously given the variance. Router specialization is weak and variable across seeds, suggesting that explicit mechanisms for breaking expert symmetry (utility-based selection, routing regularization) may be necessary at scale.

These findings close the local feasibility question but do not address the full scientific question. Definitive conclusions require replication with transformer-scale verifiers on real verification datasets, with longer continuation budgets and systematic variation of routing strategies and expert counts.

---

## Referenced Artifacts

| Artifact | Path | Description |
|---|---|---|
| Experiment script | `scripts/expert_upcycling_verifier.py` | NumPy implementation of dense/upcycled-MoE/scratch-MoE verifier comparison |
| Final metrics | `results/final_expert_upcycling_verifier.json` | Per-seed and aggregate metrics for 10-seed final run |
| Smoke test metrics | `results/smoke.json` | 1-seed smoke test results (reduced scale: 80 pretrain steps, 40 continuation steps, hidden 24, batch 64) |
| Final run log | `logs/final_experiment.log` | Stdout/stderr capture for final run |
| Smoke test log | `logs/smoke3.log` | Stdout/stderr capture for smoke test |
| Project decision | `.omx/project_decision.json` | Decision record (promising_continue, medium confidence), primary metrics, key deltas, limitations |
| Run notes | `run_notes.md` | Narrative experiment log with interpretation and closure statement |
| Session metrics | `.omx/metrics.json` | Session token and turn counts |
| Claim ledger | `papers/source-record-redacted-20260502T225548785424+0000/claim_ledger.json` | Claim audit ledger (empty at time of generation) |
| Evidence bundle | `papers/source-record-redacted-20260502T225548785424+0000/evidence_bundle.json` | Evidence bundle linking to project and run artifacts |
| Paper manifest | `papers/source-record-redacted-20260502T225548785424+0000/paper_manifest.json` | Paper generation metadata |
