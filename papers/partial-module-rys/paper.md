# Partial-Module Repeat-Your-Submodule: Decomposing Layer Repeats into Submodule Repeats for Quality Preservation in Transformer Language Models

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has approved this document.

---

## Abstract

We investigate whether repeating individual submodules (attention or MLP) within a transformer layer is less damaging to model quality than repeating the entire layer block—a strategy we term Partial-Module Repeat-Your-Submodule (RYS). Using a custom GPT-2 execution runner that selectively repeats attention-only, MLP-only, or full-block submodules at target layers, we measure probe negative log-likelihood (NLL) across two experimental phases. In an initial 10-probe single-layer sweep, attention-only repeats consistently produced smaller NLL degradation than full-layer repeats, and one configuration (attention-only at layer 2) appeared to slightly improve over baseline (ΔNLL = −0.0130). However, a 60-prompt validation of that configuration showed the improvement did not replicate (ΔNLL = +0.0045, near-neutral). The central finding is a harm-reduction result: attention-only repeats at layer 2 reduced the full-layer-repeat NLL penalty by approximately 96% while incurring roughly half the block-equivalent depth overhead. Current evidence supports partial attention repeats as a quality-preserving alternative to full-layer repeats, but does not support claiming reliable improvement over the unmodified baseline. All experiments use GPT-2 (124M) with locally cached probe sets; results on larger models remain untested.

## 1. Introduction

Layer repetition—executing a transformer layer more than once during a single forward pass—has been explored as a mechanism for increasing effective depth without adding parameters. Prior work in the parent RYS project (project `source-record-redacted`'s validated parent `source-record-redacted`) established that full-layer repeats in GPT-2 generally degrade probe NLL, falsifying naive tail-prune and full-layer-repeat candidates.

This project asks a more granular question: if repeating an entire transformer block is harmful, can the harm be reduced by repeating only a submodule of that block? Transformer layers decompose naturally into attention and feed-forward (MLP) submodules with residual connections. These submodules serve different computational roles—attention mediates token-to-token information flow, while the MLP performs per-token nonlinear transformations. Repeating only one submodule preserves the other's original execution path, potentially allowing the repeated submodule to refine its computation without the compounding error introduced by repeating both.

We test four repeat configurations at selected layers: full-block repeat, attention-only repeat, MLP-only repeat, and attention+MLL partial repeat. We report results from two experimental phases: an initial 10-probe sweep across all GPT-2 layers, and a 60-prompt focused validation of the most promising configuration.

## 2. Method

### 2.1 Partial-Module Execution Runner

We implemented `scripts/partial_module_rys_benchmark.py`, a GPT-2/DistilGPT-2-style execution runner that processes the native transformer layer order but can insert an extra execution of a target layer's submodule at a specified position. The runner supports four repeat modes at any target layer $l$:

- **Full-block repeat**: The entire transformer block at layer $l$ (attention + MLP + layer norms + residual connections) is executed twice consecutively.
- **Attention-only repeat**: Only the attention submodule (including its input layer norm and residual addition) at layer $l$ is executed twice; the MLP submodule executes once.
- **MLP-only repeat**: Only the MLP submodule (including its input layer norm and residual addition) at layer $l$ is executed twice; the attention submodule executes once.
- **Attention+MLP partial repeat**: Both submodules are repeated, but each is repeated independently (attention twice, then MLP twice), rather than repeating the composed block.

The baseline path executes each layer exactly once with no modifications. Identity equivalence was verified by confirming that baseline logits from the partial-module runner match native HuggingFace GPT-2 logits exactly (identity_max_abs_logit_diff = 0.0).

### 2.2 Probe-NLL Benchmark

Model quality is measured via average negative log-likelihood (NLL) and derived perplexity (PPL = exp(NLL)) over a set of text prompts. Lower NLL indicates better model performance under the language modeling objective.

Two probe sets were used:
- **10-probe set** (`data/probes.jsonl`): 10 broad-coverage prompts inherited from the parent RYS benchmark.
- **60-prompt extended set** (`data/probes_extended_60.jsonl`): 60 deterministic prompts spanning factual knowledge, reasoning, mathematics, code generation, creative writing, multilingual text, longform content, and edge cases. This set was constructed locally to avoid external dataset dependencies.

All evaluations use a maximum sequence length of 96 tokens.

### 2.3 Block-Equivalent Latency

To compare computational overhead fairly, we report block-equivalent latency as a multiplier relative to the baseline. A full-block repeat at one layer adds one block-equivalent unit of depth (1.083× for GPT-2's 12 layers, i.e., 13/12). A single-submodule repeat adds approximately half a block-equivalent unit (1.042×, i.e., 12.5/12), since attention and MLP each constitute roughly half of a transformer block's computation.

## 3. Results

### 3.1 Initial 10-Probe Sweep: Layer-5 Target

The first experiment targeted layer 5, the mid-stack layer identified in the parent RYS project. Results on the 10-probe set:

| Configuration | NLL | ΔNLL | PPL | Block-Equiv Latency |
|---|---|---|---|---|
| Baseline GPT-2 | 4.3704 | — | 79.08 | 1.000× |
| Full layer-5 repeat | 4.5089 | +0.1384 | 90.81 | 1.083× |
| Attention-only layer-5 repeat | 4.4407 | +0.0703 | 85.76 | 1.042× |
| MLP-only layer-5 repeat | 4.4879 | +0.1174 | 88.94 | 1.042× |

All repeat configurations degraded NLL relative to baseline. However, the attention-only repeat incurred only 51% of the full-block NLL penalty while using approximately 50% of the added block-equivalent depth. The MLP-only repeat was closer to the full-block penalty, suggesting that MLP repetition is more disruptive than attention repetition at this layer.

### 3.2 All-Layer Single-Layer Sweep (10 Probes)

A sweep across all 12 GPT-2 layers revealed layer-dependent patterns:

- **Best non-baseline result**: Attention-only repeat at layer 2 produced NLL 4.3574, ΔNLL = −0.0130, PPL 78.05, at block-equivalent latency 1.042×. This was the only configuration that appeared to improve over baseline.
- **Attention-only repeats** were consistently closer to baseline than corresponding full-layer repeats across most layers.
- **All full-layer repeats** worsened NLL on this probe set.
- **MLP-only repeats** were generally worse than attention-only repeats at the same layer.
- **Layer 0 repeats** (both MLP and full-block) catastrophically degraded NLL, consistent with layer 0 serving a foundational role in GPT-2's residual stream.

### 3.3 60-Prompt Validation: Layer-2 Attention-Only Repeat

Given the apparent improvement at layer 2, we conducted a focused validation using the 60-prompt extended set:

| Configuration | NLL | ΔNLL | PPL | Block-Equiv Latency |
|---|---|---|---|---|
| Baseline GPT-2 | 4.2716 | — | 71.63 | 1.000× |
| Full layer-2 repeat | 4.3838 | +0.1122 | 80.22 | 1.083× |
| Attention-only layer-2 repeat | 4.2761 | +0.0045 | 71.95 | 1.042× |
| MLP-only layer-2 repeat | 4.3714 | +0.0999 | 79.25 | 1.042× |
| Attention+MLP partial repeat | 4.3838 | +0.1122 | 80.22 | 1.083× |

The attention-only layer-2 repeat did **not** replicate the baseline-beating signal observed in the 10-probe set. The ΔNLL shifted from −0.0130 (10 probes) to +0.0045 (60 prompts), a change from a small improvement to near-neutral/slight degradation. This reversal is consistent with the 10-probe result being within noise bounds for that sample size.

However, the harm-reduction finding is robust: the attention-only repeat reduced the full-layer-repeat NLL penalty by approximately 96% (from +0.1122 to +0.0045) while incurring roughly half the block-equivalent depth overhead. The attention+MLP partial repeat matched the full-block repeat exactly (ΔNLL = +0.1122 in both cases), confirming that independently repeating both submodules is equivalent to repeating the full block—i.e., the harm is not an artifact of block composition order but accumulates from repeating both computational paths.

### 3.4 Attempted Broader Validation

An attempt to validate on GPT-2-medium (24 layers) was made with a bounded 180-second online/cache-fill window, but the process timed out before producing results. No GPT-2-medium data are available.

## 4. Limitations

1. **Single model scale.** All results are from GPT-2 (124M, 12 layers). Whether the harm-reduction pattern generalizes to larger models (GPT-2-medium, GPT-2-large, GPT-2-xl) or different architectures is unknown. The GPT-2-medium validation attempt timed out without producing results.

2. **Probe-set sensitivity.** The apparent baseline-beating signal at layer 2 (ΔNLL = −0.0130 on 10 probes) did not replicate on 60 prompts (ΔNLL = +0.0045). This demonstrates that small probe sets can produce misleading signals, and even the 60-prompt set may not be sufficient to resolve effects at the ±0.01 NLL scale.

3. **NLL as sole metric.** Quality is measured only via NLL/PPL on short prompts (max 96 tokens). Downstream task performance, generation quality, and longer-context behavior are not evaluated.

4. **No training or fine-tuning.** All experiments use the pretrained GPT-2 weights without any adaptation. The results reflect zero-shot insertion of repeats; models fine-tuned with repeat-augmented forward passes might behave differently.

5. **Block-equivalent latency is approximate.** The 1.042× and 1.083× multipliers assume attention and MLP contribute equally to block compute. Actual FLOP ratios vary by model configuration and hardware.

6. **Single repeat only.** Each experiment inserts exactly one extra execution of the target submodule. Multiple repeats, interleaved repeats, or repeats at multiple layers simultaneously are not tested.

7. **No statistical significance testing.** Results are reported as raw NLL differences without confidence intervals or hypothesis tests, making it difficult to distinguish signal from noise at small effect sizes.

## 5. Reproducibility Checklist

- **Model identifier:** `gpt2` (HuggingFace Transformers, 124M parameters, 12 layers)
- **Code:** `scripts/partial_module_rys_benchmark.py`
- **Tests:** `tests/test_partial_module_rys_benchmark.py` (3/3 passing)
- **Identity verification:** `identity_max_abs_logit_diff = 0.0` confirmed for baseline path
- **Probe sets:** `data/probes.jsonl` (10 prompts), `data/probes_extended_60.jsonl` (60 prompts)
- **Execution environment:** Python 3 with PyTorch (CUDA 13.0), Transformers, NumPy; project `.venv`
- **Command (layer-5 target, 10 probes):**
  ```
  python scripts/partial_module_rys_benchmark.py --local-files-only --models gpt2 --probe-limit 12 --max-length 96 --target-layers 5 --out results/partial_module_rys_benchmark.json --summary-md results/partial_module_rys_benchmark_summary.md
  ```
- **Command (all-layer sweep, 10 probes):**
  ```
  python scripts/partial_module_rys_benchmark.py --local-files-only --models gpt2 --probe-limit 12 --max-length 96 --sweep-single-layers --out results/partial_module_rys_single_layer_sweep.json --summary-md results/partial_module_rys_single_layer_sweep_summary.md
  ```
- **Command (layer-2 validation, 60 prompts):**
  ```
  python scripts/partial_module_rys_benchmark.py --local-files-only --models gpt2 --probes data/probes_extended_60.jsonl --probe-limit 60 --max-length 96 --target-layers 2 --out results/partial_module_rys_layer2_extended60.json --summary-md results/partial_module_rys_layer2_extended60_summary.md
  ```
- **Randomness controls:** Deterministic probe sets; no stochastic sampling in NLL computation. Model weights loaded deterministically from local cache.
- **Hardware:** Local machine with CUDA-capable GPU; exact hardware not recorded in artifacts.

## 6. Conclusion

We evaluated partial-module layer repetition as a refinement of full-layer repeat strategies in GPT-2. The primary finding is a harm-reduction result: repeating only the attention submodule at a target layer preserves model quality substantially better than repeating the full block, reducing the NLL penalty by approximately 96% at layer 2 while incurring roughly half the computational overhead. This pattern was consistent across both the 10-probe sweep and the 60-prompt validation.

A secondary finding is cautionary: an apparent baseline-beating signal from attention-only repetition at layer 2 (ΔNLL = −0.0130 on 10 probes) did not replicate on the larger 60-prompt set (ΔNLL = +0.0045). This falsification underscores the risk of drawing positive conclusions from small probe sets and tempers the interpretation of the harm-reduction result—while attention-only repeats are clearly less damaging than full-layer repeats, they do not reliably improve over the unmodified baseline.

The attention+MLP partial repeat matching the full-block repeat exactly confirms that the harm from full-layer repetition is compositional: it arises from repeating both submodules, not from the specific ordering or interaction of the repeated computations.

These results support archiving partial-module attention repeats as a quality-preserving alternative to full-layer repeats for depth-augmentation strategies, but not as a reliable baseline-improving mechanism. Future work should test this pattern on larger models, broader probe sets with statistical significance testing, and with fine-tuning to adapt weights to the modified forward pass.

## Referenced Artifacts

### Run notes and decision
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Source code and tests
- `scripts/partial_module_rys_benchmark.py`
- `tests/test_partial_module_rys_benchmark.py`

### Probe data
- `data/probes.jsonl`
- `data/probes_extended_60.jsonl`

### Result files
- `results/partial_module_rys_benchmark.json`
- `results/partial_module_rys_benchmark_summary.md`
- `results/partial_module_rys_single_layer_sweep.json`
- `results/partial_module_rys_single_layer_sweep_summary.md`
- `results/partial_module_rys_layer2_extended60.json`
- `results/partial_module_rys_layer2_extended60_summary.md`
- `results/partial_module_rys_layer2_validation_analysis.json`
- `results/partial_module_rys_layer2_validation_analysis.md`

### Paper and audit artifacts
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
