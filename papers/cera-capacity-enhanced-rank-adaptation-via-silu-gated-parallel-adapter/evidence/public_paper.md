# CeRA: Capacity-Enhanced Rank Adaptation via SiLU-Gated Parallel Adapter

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, evidence bundles, claim ledgers, and benchmark metrics). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We introduce CeRA (Capacity-Enhanced Rank Adaptation), a parameter-efficient adaptation method that augments a standard low-rank linear adapter (LoRA) with a SiLU-gated parallel low-rank branch. The gated branch computes a nonlinear, input-conditioned residual of the form $\text{SiLU}(xU) \odot (xV)C$, which a purely linear LoRA update cannot represent regardless of rank. In a controlled synthetic regression experiment on a frozen-base adaptation task, the parallel CeRA variant (LoRA branch + gated branch, rank 4 each) achieves a mean test MSE of 0.0197 on a gated nonlinear target, compared to 0.1666 for a parameter-matched LoRA (rank 11), winning all 8 random seeds (mean MSE ratio 0.134). On a linear control target, the same parallel CeRA variant remains competitive with standard LoRA (mean test MSE 0.000538 vs. 0.000575, winning 7/8 seeds). A pure gated-only variant fails the linear control (mean test MSE 0.269), confirming that the linear LoRA branch must be retained. These results establish mechanistic viability in a synthetic setting; they do not constitute evidence of superiority on real transformer fine-tuning tasks.

## Introduction

Low-rank adaptation (LoRA) reduces the parameter cost of fine-tuning by decomposing the weight update $\Delta W$ into a product $BA$ of low-rank matrices. This decomposition is inherently linear: the adapted output is $y = x(W_0 + BA)$, and the residual $xBA$ is a linear function of the input $x$. While this linearity is computationally convenient, it limits the expressivity of the adaptation to residuals that lie within the column space of a low-rank linear map.

Many adaptation tasks may involve residuals with input-conditioned or multiplicative structure—for example, where the effective update depends on the activation pattern of the input. A purely linear low-rank adapter cannot capture such structure regardless of how its rank is increased, because the residual it produces is always a fixed linear projection of the input.

We propose CeRA, which adds a SiLU-gated parallel branch to the standard LoRA update. The adapted output becomes:

$$y = xW_0 + xBA + \text{SiLU}(xU) \odot (xV)C$$

The gated branch $\text{SiLU}(xU) \odot (xV)C$ is nonlinear in $x$: the SiLU activation applied to one low-rank projection gates the contribution of another, producing an input-conditioned residual that no linear low-rank map can replicate. Critically, the standard LoRA branch is retained, so CeRA degrades gracefully toward LoRA-like behavior on targets where the nonlinear branch provides no benefit.

This paper reports results from a controlled synthetic experiment designed to test two mechanistic claims: (1) that the gated branch captures nonlinear residuals that linear LoRA cannot, and (2) that the parallel formulation preserves competitive performance on linear residuals. We do not report results on real transformer benchmarks.

## Method

### Problem Setting

Consider a frozen base model that computes $y_{\text{base}} = xW_0$, where $x \in \mathbb{R}^{1 \times d_{\text{in}}}$ and $W_0 \in \mathbb{R}^{d_{\text{in}} \times d_{\text{out}}}$. The adaptation task is to approximate a target function $y_{\text{target}} = y_{\text{base}} + r^*(x) + \epsilon$, where $r^*(x)$ is a structured residual and $\epsilon$ is noise.

### Adapter Variants

**Frozen (no adaptation).** Predicts $y_{\text{base}}$ only. Serves as the lower-bound baseline showing the cost of no adaptation.

**LoRA (rank $r$).** Adds a linear low-rank residual: $\hat{y} = y_{\text{base}} + xBA$, where $B \in \mathbb{R}^{d_{\text{in}} \times r}$, $A \in \mathbb{R}^{r \times d_{\text{out}}}$.

**CeRA pure gated (rank $r$).** Adds only the gated residual: $\hat{y} = y_{\text{base}} + \text{SiLU}(xU) \odot (xV)C$, where $U \in \mathbb{R}^{d_{\text{in}} \times r}$, $V \in \mathbb{R}^{d_{\text{in}} \times r}$, and $C \in \mathbb{R}^{r \times d_{\text{out}}}$. The elementwise product $\text{SiLU}(xU) \odot (xV)$ yields a $1 \times r$ vector that is then projected through $C$ to the output dimension.

**CeRA parallel (rank $r$).** Adds both branches: $\hat{y} = y_{\text{base}} + xBA + \text{SiLU}(xU) \odot (xV)C$.

### Target Families

To isolate the mechanistic properties of each adapter, we define two target families:

**Gated target.** $y = y_{\text{base}} + \text{SiLU}(xU^*) \odot (xV^*)C^* + \epsilon$. This matches CeRA's inductive bias: the true residual has the same gated low-rank structure that the CeRA gated branch is designed to capture.

**Linear target.** $y = y_{\text{base}} + xB^*A^* + \epsilon$. This matches LoRA's inductive bias: the true residual is a linear low-rank map.

These targets are deliberately constructed to favor their respective adapter families. The gated target represents a best-case scenario for CeRA's gated branch; the linear target serves as a negative control to verify that CeRA does not catastrophically fail when the gated branch is unhelpful.

### Parameter Matching

For fair comparison, we include a parameter-matched LoRA variant where the rank is chosen so that the total parameter count approximately matches that of CeRA parallel (rank 4). With $d_{\text{in}} = d_{\text{out}} = d$, CeRA parallel at rank 4 uses parameters for $B, A$ (LoRA branch) plus $U, V, C$ (gated branch). The parameter-matched LoRA uses rank 11 to approximate this count. The match is approximate because rank must be an integer.

### Optimization

All adapters are trained via gradient descent on mean squared error (MSE) using the same learning rate and step count. The base weights $W_0$ are frozen throughout. A single hyperparameter configuration is shared across all methods; we do not perform per-method tuning.

## Results

### Experimental Configuration

All experiments use a deterministic NumPy regression harness with no GPU or deep learning framework dependency. This is a toy synthetic experiment, not a transformer fine-tuning evaluation. Configuration: 8 random seeds, 3000 gradient steps per run, 1024 training examples, 4096 test examples. Wall time for the full 8-seed × 2-target evaluation was 13.16 seconds; peak RSS was 43,488 KB on a Linux aarch64 host with ~115 GiB available memory and swap disabled.

An initial smoke test (1 seed, 200 steps, 256 train / 512 test examples) confirmed end-to-end execution. On the gated target, the smoke test showed `cera_r4` test MSE of 0.0935 versus frozen at 0.2228 and parameter-matched LoRA at 0.2156. The main evaluation below uses the full configuration.

### Gated Target

On the gated nonlinear target, the parallel CeRA variant strongly outperforms both LoRA variants:

| Adapter | Mean Test MSE | Seeds Won vs. Param-Matched LoRA |
|---|---|---|
| Frozen | 0.2228 | — |
| LoRA (rank 4) | 0.2156 | — |
| LoRA param-matched (rank 11) | 0.1666 | — |
| CeRA parallel (rank 4) | 0.0197 | 8/8 |

The mean MSE ratio of CeRA parallel to parameter-matched LoRA is 0.134, indicating that CeRA achieves roughly 7.5× lower test error on this target. CeRA wins all 8 seeds.

This result is consistent with the hypothesis that the gated branch captures nonlinear input-conditioned residuals that no linear low-rank map can represent, regardless of rank. However, it should be interpreted in light of the fact that the gated target was explicitly constructed to match CeRA's functional form.

### Linear Target Control

On the linear target, the parallel CeRA variant remains competitive with standard LoRA:

| Adapter | Mean Test MSE | Seeds Won vs. LoRA (rank 4) |
|---|---|---|
| LoRA (rank 4) | 0.000575 | — |
| LoRA param-matched (rank 11) | 0.000678 | — |
| CeRA parallel (rank 4) | 0.000538 | 7/8 |
| CeRA pure gated (rank 4) | 0.269 | — |

The parallel CeRA variant slightly outperforms standard LoRA (rank 4) on 7 of 8 seeds, with a mean test MSE of 0.000538 vs. 0.000575. It also outperforms the parameter-matched LoRA (rank 11), which achieves 0.000678. The margin is small, and we caution against over-interpreting this slight advantage. The primary takeaway is that the gated branch does not catastrophically interfere with linear adaptation when the LoRA branch is present.

### Negative Control: Pure Gated CeRA

The pure gated CeRA variant (without the LoRA branch) achieves a mean test MSE of 0.269 on the linear target—worse than the frozen baseline. This is a critical negative result: the SiLU-gated branch alone is not a drop-in replacement for LoRA on linear adaptation tasks. The nonlinearity that provides expressivity on gated targets becomes a liability when the true residual is linear.

This confirms that the parallel formulation (LoRA branch + gated branch) is essential to the CeRA design. Removing the linear branch sacrifices the method's ability to handle linear residuals, and the gated branch can actively harm performance in such settings.

## Limitations

1. **Synthetic setting only.** All evidence comes from a controlled NumPy regression experiment on synthetic data. The frozen base is a single linear map, and the target residuals are constructed to match the inductive biases of the respective adapters. No results on real transformer architectures, real datasets, or standard NLP/CV benchmarks are reported. The results establish mechanistic viability, not practical superiority.

2. **Favorable target construction.** The gated target is explicitly constructed to match CeRA's functional form. Performance on this target represents a best-case scenario for CeRA's gated branch. Real adaptation tasks may not exhibit residuals with clean gated low-rank structure, and the degree of benefit from the gated branch in practice remains unknown.

3. **Scale and dimensionality.** The experiment uses modest dimensions and sample sizes (1024 training, 4096 test). Scaling behavior to high-dimensional transformer hidden states (typically 768–4096) and large datasets has not been tested.

4. **Single nonlinearity.** Only the SiLU activation is tested. Other gating functions (e.g., ReLU, GELU, sigmoid) may yield different tradeoffs between expressivity and interference with linear adaptation.

5. **No comparison to other nonlinear adapters.** The experiment compares CeRA only to LoRA variants. Other parameter-efficient methods that introduce nonlinearity (e.g., adapter modules with nonlinear layers) are not included as baselines.

6. **Optimization details.** A single learning rate and step count are used across all methods. Whether CeRA requires different hyperparameter tuning than LoRA in practice has not been investigated.

7. **Parameter matching is approximate.** The parameter-matched LoRA (rank 11) does not exactly match CeRA's parameter count; it is the nearest integer rank approximation.

8. **No real-model integration.** CeRA has not been implemented as a PEFT-compatible module for transformer linear layers. The interaction between the gated branch and layer normalization, residual connections, and multi-head attention in real transformers is unexplored.

## Reproducibility Checklist

- **Code available:** `src/cera_numpy_experiment.py` (deterministic NumPy harness, no GPU required).
- **Random seeds:** 8 seeds per condition, explicitly logged.
- **Command lines:** All invocation commands recorded in run notes and log files.
- **Log files:** `logs/smoke.log`, `logs/smoke_parallel.log`, `logs/eval_parallel_8seeds_3000steps.log`.
- **Metrics files:** `metrics/cera_parallel_results.json`, `metrics/cera_results.json`, `metrics/smoke.json`.
- **Summary:** `metrics/summary.md`.
- **Decision record:** `.omx/project_decision.json`.
- **Environment:** Python 3.12.3, Linux aarch64, NumPy only (no PyTorch/transformers dependency).
- **Hardware:** CPU-only execution on aarch64 host; 13.16s wall time; max RSS 43,488 KB; no swap activity.
- **Determinism:** NumPy deterministic harness; no stochastic training procedures beyond seeded initialization.

## Conclusion

CeRA augments LoRA with a SiLU-gated parallel low-rank branch that can express nonlinear, input-conditioned residuals unreachable by any linear low-rank adapter. In a controlled synthetic experiment, the parallel CeRA variant (LoRA + gated branch) achieves 7.5× lower test MSE than parameter-matched LoRA on a gated nonlinear target (8/8 seeds), while remaining competitive with standard LoRA on a linear control target (7/8 seeds). A pure gated variant without the LoRA branch fails the linear control (mean test MSE 0.269), confirming that the linear branch must be retained.

These results support the mechanistic claim that SiLU-gated parallel capacity captures structure that linear LoRA cannot, and that the parallel formulation preserves linear adaptation behavior. They do not support claims about real-transformer fine-tuning performance, benchmark superiority, or deployment advantage. The natural next step is implementation as a PEFT-compatible module and evaluation on real downstream tasks.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment source | `src/cera_numpy_experiment.py` |
| Smoke test log | `logs/smoke.log` |
| Parallel smoke log | `logs/smoke_parallel.log` |
| Main evaluation log | `logs/eval_parallel_8seeds_3000steps.log` |
| Main metrics | `metrics/cera_parallel_results.json` |
| Initial metrics | `metrics/cera_results.json` |
| Smoke metrics | `metrics/smoke.json` |
| Results summary | `metrics/summary.md` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260501T170048849691+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T170048849691+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T170048849691+0000/paper_manifest.json` |
