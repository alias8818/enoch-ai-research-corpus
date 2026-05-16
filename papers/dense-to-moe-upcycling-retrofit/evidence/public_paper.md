# Dense-to-MoE Upcycling Retrofit: A Local Prototype Study of Functional Continuity and Post-Upcycle Specialization

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Mixture-of-Experts (MoE) upcycling—converting a dense model checkpoint into a sparse MoE model by copying feed-forward weights into multiple experts—has been proposed as a compute-efficient path to sparse models. We implement and evaluate the core retrofit mechanics in a controlled NumPy-only prototype: a 2-layer dense MLP trained on a heterogeneous piecewise regression task with four latent regimes is upcycled into a top-1 routed 4-expert MoE model. We verify three properties: (1) exact functional continuity at conversion (maximum absolute output difference = 0.0 across all runs), (2) consistent post-upcycle quality improvement over continued dense training under matched epoch budgets (mean MoE/dense MSE ratio = 0.339 across five seeds, all five runs favoring MoE), and (3) emergent expert specialization measured by latent-region routing purity (0.988–0.996). These results establish the retrofit mechanism as locally viable but do not constitute LLM-scale validation. We discuss the gap between this toy-regime evidence and the requirements for closing the question at transformer scale.

## 1. Introduction

Sparse Mixture-of-Experts models offer the possibility of scaling model capacity without proportionally scaling per-token compute. A natural question is whether an existing dense checkpoint can be retrofitted into an MoE architecture without losing the knowledge encoded in its weights, and whether subsequent training can leverage expert specialization to outperform continued dense training under the same budget.

Prior work has studied this question at increasing scale. Komatsuzaki et al. (arXiv:2212.05055) proposed sparse upcycling for T5 and ViT, reporting that upcycled models outperform both dense counterparts and sparse-from-scratch baselines under fixed compute budgets. He et al. (arXiv:2410.07524) extended the approach to billion-parameter LLMs, identifying practical considerations including virtual-group initialization, weight scaling, and softmax-then-topK routing. Liew et al. (arXiv:2502.03009) found scaling-law interactions that limit upcycling efficiency at large training budgets. Nakamura et al. (arXiv:2502.19261) argued that naive copied experts learn slowly due to weight symmetry and proposed partial reinitialization. Chu et al. (arXiv:2604.13508) targeted the same symmetry problem via cluster-aware initialization from dense activations.

The present study does not attempt to replicate or extend these LLM-scale results. Instead, it asks a narrower, mechanistic question: in a fully controlled setting where the ground-truth task structure is known, does the upcycling retrofit preserve functional continuity at conversion, and does symmetry-broken expert training yield measurable specialization and quality gains? We implement the retrofit in a minimal NumPy prototype to isolate the mechanism from confounds introduced by large-scale training infrastructure, model architectures, and data pipelines.

## 2. Method

### 2.1 Task

We construct a heterogeneous piecewise regression problem with four latent regimes. Each input sample is drawn from a region associated with one regime, and the target is a deterministic function of the input with regime-specific parameters. This design ensures that (a) the task benefits from specialization, and (b) routing purity can be measured against known ground-truth regime labels.

### 2.2 Dense Pretraining

A 2-layer MLP is trained on the regression task for a fixed number of epochs (40 in the calibration configuration) using standard gradient descent. This produces a dense checkpoint that serves as the starting point for upcycling.

### 2.3 Upcycling Retrofit

The dense MLP is converted into a 4-expert MoE model via the following procedure:

1. **Expert initialization.** Each expert's feed-forward weights are initialized as an exact copy of the dense model's corresponding layer weights. This yields $E = 4$ identical experts.

2. **Router initialization.** A top-1 routing network is initialized to assign each input token to exactly one expert.

3. **Continuity verification.** Because all experts are identical copies, the MoE model's output is exactly equal to the dense model's output regardless of routing decisions. We verify this by computing the maximum absolute difference between dense and MoE outputs over the test set.

4. **Symmetry breaking.** Tiny perturbations ($\sigma = 10^{-3}$) are added to expert weights to break the symmetry that would otherwise prevent differentiation.

5. **Post-upcycle training.** Experts are trained on tokens routed to them via nearest-centroid assignment. The dense model is also continued for the same number of epochs to serve as the baseline.

### 2.4 Evaluation Metrics

- **Exact-copy continuity:** Maximum absolute difference between dense and MoE outputs at conversion, before symmetry breaking. Expected: 0.0.
- **Test MSE:** Mean squared error on a held-out test set, measured after dense pretraining, after dense continuation, and after MoE upcycling and training.
- **MoE/dense MSE ratio:** Ratio of final MoE test MSE to final dense-continued test MSE. Values below 1.0 favor MoE.
- **Routing entropy fraction:** Normalized entropy of the expert assignment distribution. A value near 1.0 indicates balanced routing across experts.
- **Latent-region routing purity:** Fraction of tokens routed to the expert whose dominant regime matches the token's ground-truth regime. Values near 1.0 indicate that experts have specialized to latent regimes.

### 2.5 Experimental Configurations

Three configurations were run:

- **Smoke test:** Quick validation of the pipeline with default hyperparameters.
- **Calibration run:** Full run with 12,000 training samples, 3,000 test samples, 40 dense epochs, and 16 retrofit epochs.
- **Five-seed sweep:** Five repetitions of the calibration configuration with seeds 1–5 to assess variability.

All experiments were executed on a GB10-class aarch64 Linux host (Linux 6.17.0, 121 GiB RAM, swap disabled, earlyoom active). The prototype is NumPy-only; no GPU was used despite an NVIDIA GB10 being present, as PyTorch was not installed in the environment. This is a toy simulation, not a llama.cpp hook-prototype, CUDA copy calibration, or production validation.

## 3. Results

### 3.1 Exact-Copy Continuity

Across all runs—smoke test, calibration, and all five seed-sweep repetitions—the maximum absolute difference between the dense model output and the upcycled MoE output at conversion was **0.0**. This confirms that the copy-based retrofit preserves functional continuity exactly, as expected from the construction: identical experts produce identical outputs regardless of routing.

### 3.2 Post-Upcycle Quality

| Configuration | Dense Pretrain MSE | Dense Continued MSE | MoE Final MSE | MoE/Dense Ratio | MoE Improvement from Initial |
|---|---|---|---|---|---|
| Smoke | 0.4248 | 0.4002 | 0.1810 | 0.4522 | — |
| Calibration | 0.0907 | 0.0818 | 0.0209 | 0.2553 | 76.89% |

In both configurations, the upcycled MoE model substantially outperformed continued dense training under the same epoch budget. The calibration run showed the MoE achieving 74.5% lower MSE than dense continuation. The MoE initial test MSE after tiny noise perturbation was 0.0904, nearly identical to the dense pretrain MSE of 0.0907, confirming that the symmetry-breaking perturbation introduced negligible immediate quality degradation.

### 3.3 Seed Sweep Variability

All five seed-sweep runs confirmed the same pattern:

- **Continuity:** 5/5 runs preserved exact-copy continuity (max abs diff = 0.0).
- **MoE superiority:** 5/5 MoE runs beat dense continuation.
- **Mean MoE/dense MSE ratio:** 0.3386.
- **Worst MoE/dense MSE ratio:** 0.3759.
- **Latent-region routing purity range:** 0.9883–0.9963.

The consistency across seeds suggests the result is not an artifact of a single initialization, though the sample size of five is modest and the standard deviation was not reported in the artifacts.

### 3.4 Routing Behavior

Routing entropy fraction was 0.9995 (smoke) and 0.9998 (calibration), indicating nearly uniform load across experts. Latent-region routing purity exceeded 0.988 in all runs, indicating that the router learned to assign tokens to the expert corresponding to their ground-truth regime with high accuracy.

### 3.5 Resource Usage

The calibration run's maximum RSS was 40,204 KB as measured by `/usr/bin/time -v`, with 0 swaps on a host with 121 GiB RAM and swap disabled. The prototype processed approximately 2,494,795 samples per second during the paired retrofit comparison phase. These figures reflect the lightweight NumPy-only implementation and are not indicative of LLM-scale resource requirements.

## 4. Limitations

This study has several substantial limitations that must be stated explicitly.

**Toy task only.** The piecewise regression task is a synthetic, low-dimensional problem with known latent structure. It is designed to favor expert specialization. Real-world tasks—particularly language modeling—have far more complex, overlapping, and ambiguous regime structure. The degree to which upcycling benefits transfer to such tasks is unknown from this evidence alone.

**Small model scale.** The prototype uses a 2-layer MLP. Transformer architectures introduce additional complexity: multi-head attention, layer normalization, residual connections, and the interaction between MoE layers and dense attention layers. The retrofit mechanics may behave differently in these settings.

**No LLM evaluation.** No perplexity, downstream task accuracy, or other LLM-relevant metrics were measured. No real training corpus was used. The claim "upcycling works" is supported only for the specific synthetic task studied here.

**Epoch-matched, not compute-matched.** The comparison holds epoch count constant between MoE and dense continuation. Because the MoE model activates fewer parameters per token, per-epoch compute differs. A fully fair comparison would match total FLOPs, which was not done here.

**Routing oracle advantage.** The nearest-centroid routing used during post-upcycle training has access to ground-truth regime labels for centroid computation. In a real setting, the router must learn assignments from data without such supervision. The high routing purity observed here may overestimate what an unsupervised router can achieve.

**Modest seed count.** Five seeds provide a preliminary indication of robustness but are insufficient for strong statistical claims about variance.

**No comparison to from-scratch MoE.** The study compares upcycled MoE to continued dense training but does not compare to an MoE trained from scratch with the same architecture and budget. Prior literature suggests this comparison is important.

**Task designed to favor the method.** The heterogeneous piecewise regression task was explicitly constructed with four latent regimes matching the four experts. This is a best-case scenario for MoE specialization. Tasks without such clean latent structure may show substantially weaker benefits.

## 5. Reproducibility Checklist

- **Code available:** `src/dense_to_moe_upcycling.py` (NumPy-only, no GPU required).
- **Exact commands documented:** Smoke test, calibration, and seed-sweep commands are recorded in run notes (see Referenced Artifacts).
- **Random seeds reported:** Seeds 1–5 for the sweep; default seed for smoke and calibration.
- **Hardware specified:** GB10-class aarch64 Linux, 121 GiB RAM, Linux 6.17.0-1014-nvidia-aarch64, swap disabled, earlyoom active.
- **Software dependencies:** Python 3, NumPy. No PyTorch, no CUDA, no GPU used.
- **Output artifacts:** JSON metrics files for smoke, calibration, and each seed (see Referenced Artifacts).
- **Verification steps:** `py_compile` passed; JSON assertions for continuity and MoE superiority passed.
- **Resource telemetry:** `nvidia-smi`, `/proc/meminfo`, `/usr/bin/time -v` outputs recorded.
- **Evidence level:** Toy simulation (NumPy-only 2-layer MLP on synthetic data). Not a llama.cpp hook-prototype, not a CUDA copy calibration, not a production validation.

## 6. Conclusion

We have demonstrated that dense-to-MoE upcycling retrofit preserves exact functional continuity at conversion and, in a controlled synthetic setting with heterogeneous latent structure, consistently yields post-upcycle quality improvements over continued dense training. Across five random seeds, the upcycled MoE model achieved a mean MSE ratio of 0.339 relative to dense continuation, with routing purity exceeding 0.988.

These results establish the retrofit mechanism as locally viable: the copy-then-perturb procedure works as intended, experts specialize to latent regimes, and the sparse model outperforms the dense baseline on a task designed to benefit from specialization. However, this is a proof-of-mechanics result, not a claim about LLM-scale performance. The gap between a 2-layer MLP on a four-regime synthetic task and a transformer language model on natural text is substantial. The task was explicitly constructed to favor the method, the routing benefited from ground-truth label access, and the comparison was epoch-matched rather than compute-matched.

Closing the question at LLM scale requires: (1) selecting a concrete target checkpoint, (2) implementing MoE FFN layer replacement within that model's architecture, (3) selecting and fetching a representative training corpus, (4) running continued training and evaluation with perplexity and downstream task metrics, and (5) comparing naive upcycling, symmetry-broken upcycling, and cluster-aware upcycling variants. We recommend this targeted transformer validation as the next experimental phase, contingent on the availability of a specific checkpoint and evaluation budget.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Prototype source | `src/dense_to_moe_upcycling.py` |
| Smoke test metrics | `artifacts/smoke_metrics.json` |
| Calibration metrics | `artifacts/calibration_metrics.json` |
| Seed sweep summary | `artifacts/seed_sweep_summary.json` |
| Seed sweep individual runs | `artifacts/seed_{1..5}_metrics.json` |
| Smoke log | `logs/smoke.log` |
| Calibration log | `logs/calibration.log` |
| Calibration time log | `logs/calibration_time.log` |
| Seed sweep log | `logs/seed_sweep.log` |
| Project decision record | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260501T034808609981+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T034808609981+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T034808609981+0000/paper_manifest.json` |
| Project directory | `<control-plane-projects>/source-record-redacted` |
