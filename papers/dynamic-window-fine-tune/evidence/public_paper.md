# Dynamic Window Fine-Tune: A Synthetic Proxy Study of Context-Budget Robustness

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metrics files). The operator who released this artifact claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

We investigate whether training models with variable context windows—*dynamic window fine-tuning*—improves robustness when inference-time context budgets are tightened. Using a controlled synthetic binary-classification benchmark with an intentionally structured shortcut (strong late-context feature, weak early-context evidence), we compare a fixed full-window training baseline against a dynamic-window treatment that samples prefix budgets during training. In a 16-seed experiment with an elastic-net logistic regression proxy (10,000 training examples, 6,000 test examples per seed), dynamic-window training improved accuracy by 6.1–7.0 percentage points at tight budgets (8, 16, 32 tokens) while degrading full-budget (64-token) accuracy by 0.19 percentage points. The accuracy drop from full to minimum budget was reduced by 6.3 percentage points. However, these gains depended on sparsity regularization that creates capacity pressure toward shortcut selection; low-regularization sweeps produced only 0–2.5 percentage-point improvements. This study is limited to a synthetic linear model and does not demonstrate transfer to transformer architectures, real tasks, or production workloads. The result supports continued investigation at the next experimental stage but does not establish practical utility.

## Introduction

When language models are fine-tuned with full context windows but deployed under constrained context budgets—due to cost, latency, or input truncation—behavior can degrade sharply. A model that has learned to rely on features appearing late in the context may lose access to those features at reduced budgets, with no fallback to earlier, weaker signals.

Dynamic window fine-tuning addresses this by training with variable context windows: during each training step, a prefix budget is sampled and only the first *k* tokens are presented. The hypothesis is that this exposure teaches the model to rely on signals distributed across context positions rather than concentrating on late-position shortcuts, producing behavior that degrades more gracefully when inference budgets tighten.

This work tests that hypothesis in a minimal controlled setting. We construct a synthetic benchmark where early positions carry weak label evidence and late positions carry a strong shortcut, then compare fixed full-window training against dynamic-window training using a sparse logistic regression proxy. The experiment is deliberately narrow: it establishes whether the mechanism produces the predicted effect in a setting where the failure mode is guaranteed to exist, before investing in transformer-scale experiments.

We emphasize at the outset that this is a toy simulation using a linear model, not a transformer fine-tune. The results are suggestive but do not directly predict behavior in neural settings.

## Method

### Benchmark Design

We designed a 64-token synthetic binary classification task with the following structure:

- **Positions 0–7 (early):** Contain weak label-correlated evidence, available at all context budgets.
- **Positions 56–63 (late):** Contain a strong shortcut feature, available only at the full budget of 64 tokens.

This structure guarantees that a model trained exclusively at full budget can achieve high accuracy by relying on the late shortcut, but will suffer substantial degradation when the budget is reduced below 56 tokens and the shortcut becomes inaccessible.

### Training Conditions

**Fixed full-window baseline (`fixed_full`):** Trains with the complete 64-token context at every step.

**Dynamic-window treatment (`dynamic`):** At each training step, a prefix budget is sampled from {8, 16, 32, 64} with probabilities {0.55, 0.25, 0.15, 0.05}. Only the first *k* tokens are presented, where *k* is the sampled budget. The distribution is heavily weighted toward tight budgets to maximize exposure to early-context-only regimes.

### Model

We use `SGDClassifier` (scikit-learn) with log loss, `alpha=5e-4`, and `l1_ratio=0.5` (elastic-net regularization). The L1 component creates sparsity pressure that induces a capacity-constrained feature-selection regime: the model cannot simply memorize all positions and must allocate its limited effective capacity. This pressure is necessary for the fixed-window baseline to meaningfully over-select the late shortcut, creating the failure mode the dynamic-window treatment aims to mitigate.

This linear proxy was chosen because the project environment lacked PyTorch/CUDA installations, and blocking on GPU framework setup was deemed unnecessary for a smoke-stage decision. The proxy models a capacity-limited learner that must choose which features to retain—an analogy to, but not a demonstration of, the behavior of a neural model under parameter or attention capacity constraints.

### Evaluation

Models are evaluated at each of the four budgets (8, 16, 32, 64) by truncating the test context to the corresponding prefix length. We report accuracy and compute the difference (dynamic minus fixed) at each budget, as well as the accuracy drop from budget 64 to budget 8 for each condition.

### Experimental Protocol

- **Seeds:** 16
- **Training examples per seed:** 10,000
- **Test examples per seed:** 6,000
- **Epochs:** 8
- **Environment:** Python 3.12.3, CPU-only (NumPy/scikit-learn), ~122 GB available memory, no swap, no GPU utilization.

A preliminary sweep over schedule and regularization settings was conducted (6 seeds) before the confirmatory 16-seed run. The sweep identified that tight-budget-heavy training distributions combined with stronger sparsity (`l1_ratio=0.5`) produced the largest gains; low-regularization runs yielded only 0–2.5 percentage-point improvements.

## Results

### Main Comparison

Accuracy difference (dynamic minus fixed) at each context budget, averaged over 16 seeds:

| Context Budget | Dynamic − Fixed Accuracy |
|---:|---:|
| 8 | +0.0613 |
| 16 | +0.0647 |
| 32 | +0.0704 |
| 64 | −0.0019 |

Dynamic-window training improved accuracy at all reduced budgets, with gains ranging from 6.1 to 7.0 percentage points. At full budget (64 tokens), the dynamic condition showed a small accuracy deficit of 0.19 percentage points.

### Budget Sensitivity

| Metric | Fixed Full-Window | Dynamic Window |
|---|---:|---:|
| Accuracy drop (64 → 8) | 0.3111 | 0.2478 |
| Drop reduction | — | 0.0632 |

The dynamic-window condition reduced the accuracy degradation from full to minimum budget by 6.3 percentage points (from 31.1% to 24.8%), indicating flatter degradation under budget compression.

### Sweep Findings

Initial sweeps with weaker regularization produced substantially smaller gains (0–2.5 percentage points). The interaction between dynamic window training and sparsity pressure suggests that the method is most effective when the learner faces capacity constraints that would otherwise drive it toward high-quality late-context shortcuts. Without such pressure, the model can simply retain all features and the dynamic-window treatment provides marginal benefit. This interaction is an important negative qualifier: dynamic windows alone were insufficient in this linear proxy.

### Resource Usage

The final 16-seed run completed in 1.50 seconds wall time on CPU. Memory and GPU telemetry logs confirm the run was CPU-bound with no GPU utilization and no swap activity.

## Limitations

1. **Synthetic linear proxy, not a neural model.** The experiment uses an elastic-net logistic regression, not a transformer or LLM. The capacity/shortcut-selection failure mode is engineered via L1 sparsity rather than emerging from attention patterns or representation learning. Results do not directly predict behavior in neural fine-tuning.

2. **Engineered shortcut structure.** The benchmark deliberately places a strong shortcut at late positions and weak evidence at early positions. Real tasks may not exhibit this structure, or may distribute information more uniformly, reducing the potential benefit of dynamic-window training.

3. **Dependence on regularization.** Positive results required specific sparsity pressure (`l1_ratio=0.5`). Without this pressure, gains were small (0–2.5 points). The interaction between dynamic windows and model capacity in transformer settings may differ substantially and has not been characterized.

4. **Narrow evaluation scope.** The study evaluates only classification accuracy under prefix truncation. It does not assess RAG robustness, long-context question answering, structured output fidelity, generation quality, training stability, memory overhead, latency, or any other practical deployment metric.

5. **No transformer validation.** Scientific closure requires demonstration in a neural model (e.g., tiny transformer or LoRA fine-tune) on at least one real task with explicit context-budget evaluation. This study does not provide that.

6. **Budget distribution sensitivity.** The training budget distribution {0.55, 0.25, 0.15, 0.05} was hand-tuned during the sweep. The sensitivity of results to this distribution has not been systematically characterized.

7. **Small seed count for sweep.** The preliminary sweep used only 6 seeds; the confirmatory run used 16. While the direction of effect is consistent, variance estimates from 16 seeds remain noisy for small effect sizes.

## Reproducibility Checklist

- [x] **Experiment script provided:** `src/dynamic_window_experiment.py`
- [x] **Sweep script provided:** `src/sweep_dynamic_windows.py`
- [x] **Raw metrics available:** `results/final_metrics.json`, `results/final_metrics.csv`
- [x] **Sweep metrics available:** `results/sweep_metrics.json`
- [x] **Execution logs preserved:** `logs/smoke.log`, `logs/sweep.log`, `logs/final_run.log`
- [x] **Resource telemetry preserved:** `logs/final_run.time.log`, `logs/memory_after.log`, `logs/gpu_after.log`
- [x] **Decision record preserved:** `.omx/project_decision.json`
- [x] **Random seeds:** 16 independent seeds; seed handling is in the experiment script.
- [x] **Software environment:** Python 3.12.3, NumPy, scikit-learn (CPU-only).
- [x] **Hardware environment:** CPU-only run; no GPU; ~122 GB RAM available; no swap.
- [ ] **External package versions pinned:** Not recorded in artifacts; reproducers should note scikit-learn and NumPy versions.
- [ ] **Docker/container spec:** Not provided.

## Conclusion

Dynamic window fine-tuning improved accuracy by 6.1–7.0 percentage points at tight context budgets in a controlled synthetic benchmark, while incurring only a 0.19 percentage-point cost at full budget. The accuracy drop from full to minimum budget was reduced by 6.3 percentage points. These results meet the pre-specified smoke-test criterion of ≥5 percentage-point gain at tight budgets.

However, the gains are contingent on sparsity-induced capacity pressure that forces shortcut selection—a condition that may or may not analogize to transformer fine-tuning. Low-regularization sweeps showed that dynamic windows alone produced only marginal improvements (0–2.5 points) in this proxy, indicating that the method's benefit is not unconditional. The study is further limited to a linear model on a synthetic task with an engineered shortcut structure. It does not demonstrate that dynamic window fine-tuning transfers to neural architectures, real-world tasks, or practical deployment scenarios.

The appropriate interpretation is that the mechanism (variable context windows during training) produces the predicted effect in a minimal setting where the failure mode is guaranteed to exist. This justifies continued investigation at the next experimental stage—specifically, a tiny transformer or LoRA fine-tune on a real task with explicit context-budget evaluation—but does not yet support claims about practical utility or general applicability.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Experiment script | `src/dynamic_window_experiment.py` |
| Sweep script | `src/sweep_dynamic_windows.py` |
| Final metrics (JSON) | `results/final_metrics.json` |
| Final metrics (CSV) | `results/final_metrics.csv` |
| Sweep metrics | `results/sweep_metrics.json` |
| Smoke log | `logs/smoke.log` |
| Sweep log | `logs/sweep.log` |
| Final run log | `logs/final_run.log` |
| Final run time/resource log | `logs/final_run.time.log` |
| Post-run memory telemetry | `logs/memory_after.log` |
| Post-run GPU telemetry | `logs/gpu_after.log` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T151948640475+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T151948640475+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T151948640475+0000/paper_manifest.json` |
