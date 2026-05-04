# Token-Conditioned MLP Thinning: Per-Token Sparse Masks for Feed-Forward Network Compression

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision logs, metric files, and claim ledgers). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether transformer feed-forward network (FFN) layers can be thinned using masks conditioned solely on the current token identity, preserving model quality more effectively than global or random thinning at equivalent retained widths. On a controlled synthetic next-token prediction task with a small causal transformer (2 layers, *d*=96, *d*<sub>ff</sub>=384), we calibrate per-token FFN activation magnitudes and construct three equal-budget mask strategies: token-conditioned top-*k*, global top-*k*, and random per-token. Across three random seeds at 25% retained FFN width, token-conditioned masks yield a mean loss increase of 0.0146 over the dense baseline, compared to 0.1101 for global top-*k* and 0.1378 for random per-token masks—approximately 7.5× and 9.4× lower degradation, respectively. At 12.5% retained width, the advantage narrows but remains approximately 4.5× and 5.0×. However, a naïve grouped-gather CPU implementation of the sparse FFN path achieves only ~6.3% of dense throughput at 25% retention, as Python-level grouping overhead dominates at this scale. These results support the algorithmic viability of token-conditioned FFN sparsity for quality preservation, but do not establish deployment-speed viability, which would require fused GPU kernels. All experiments use a synthetic deterministic task and CPU-only PyTorch; generalization to pretrained language models on natural text remains untested.

## Introduction

Transformer FFN layers consume a large fraction of inference compute. Structured sparsity methods that zero out or skip FFN channels can reduce this cost, but the choice of *which* channels to retain matters for quality. Global pruning strategies select a single shared mask across all inputs, while mixture-of-experts and conditional-computation approaches route dynamically based on input representations.

We ask a simpler question: if the only conditioning signal is the current token id—available at no additional compute cost—can we construct per-token FFN masks that preserve quality substantially better than global or random masks at the same sparsity budget?

This approach has an appealing property: token ids are discrete, bounded, and already computed before the FFN fires, so a lookup into a precomputed mask table is essentially free. The question is whether token identity alone carries enough information about which FFN channels matter.

We evaluate this idea on a small causal transformer trained on a deterministic synthetic next-token task, comparing three mask strategies at 50%, 25%, and 12.5% retained FFN width. We report quality (loss degradation) and throughput (tokens per second) for a naïve grouped-gather implementation. We are careful to distinguish the algorithmic quality finding—which is positive—from the deployment-speed finding, which is negative under our implementation conditions.

## Method

### Task and Model

We train a tiny causal transformer language model on a deterministic synthetic next-token prediction task. The model uses the following hyperparameters for the final experiment:

- Model dimension (*d*): 96
- FFN dimension (*d*<sub>ff</sub>): 384
- Layers: 2
- Attention heads: 4
- Sequence length: 32
- Batch size: 48
- Training steps: 150

The synthetic task is deterministic: each input token maps to a unique correct next token, ensuring the model can achieve near-zero loss when fully trained. This design maximizes the signal from token identity but limits ecological validity, as natural language exhibits contextual ambiguity that a single token id cannot resolve.

### Calibration

After training, we run 16 calibration batches through the dense model and record, for each token id, the mean absolute activation of each FFN intermediate channel. This produces a calibration matrix *C* ∈ ℝ<sup>|V| × d<sub>ff</sub></sup> where *C*<sub>t,j</sub> is the mean magnitude of channel *j* when token *t* is the input to the FFN.

### Mask Construction

Given a retention fraction *r* ∈ {0.5, 0.25, 0.125}, we construct three mask types, each retaining exactly ⌊*r* · *d*<sub>ff</sub>⌋ channels per token:

1. **token_topk**: For each token *t*, retain the top-*k* channels by calibrated magnitude *C*<sub>t,·</sub>. This yields a distinct mask per token.

2. **global_topk**: Compute the mean magnitude per channel across all tokens, then retain the top-*k* channels globally. Every token uses the same mask.

3. **random_token**: For each token *t*, randomly select *k* channels. This controls for the effect of having per-token masks without using calibration information.

All three strategies share the same per-token retention budget, isolating the effect of *which* channels are selected.

### Evaluation

We evaluate each masked model on 20 held-out batches, computing cross-entropy loss and perplexity. We also measure throughput (tokens per second) for the dense baseline and for a grouped-gather implementation of the token_topk path, which computes only the selected FFN channels per token using index gathering.

### Experimental Protocol

We run three seeds (123, 456, 789) and report means. A smoke test (2 steps, *d*=32, *d*<sub>ff</sub>=64) and a calibration run (80 steps, *d*=64, *d*<sub>ff</sub>=192) preceded the final runs to validate the pipeline. The smoke test and calibration run confirmed correct metric computation and reasonable convergence behavior before committing to the full three-seed protocol.

## Results

### Quality: Loss Degradation

The dense baseline achieves a mean loss of 0.002053 (perplexity 1.002055) across seeds, confirming the synthetic task is well-learned.

Table 1 reports the mean loss increase (Δloss) relative to the dense baseline for each mask strategy and retention fraction. Lower values indicate better quality preservation.

**Table 1:** Mean Δloss vs. dense baseline across three seeds.

| Retained FFN fraction | token_topk | global_topk | random_token |
|----------------------:|-----------:|------------:|-------------:|
| 50%                   | 0.000915   | 0.018508    | 0.022916     |
| 25%                   | 0.014616   | 0.110115    | 0.137801     |
| 12.5%                 | 0.063769   | 0.285678    | 0.320616     |

Token-conditioned masks consistently outperform both baselines. At 25% retention, token_topk Δloss is 7.5× lower than global_topk and 9.4× lower than random_token. At 12.5% retention, the advantage narrows but remains substantial at approximately 4.5× and 5.0×, respectively.

The global_topk strategy outperforms random_token at all sparsity levels, confirming that calibration information helps even when masks are not token-specific. However, the additional gain from per-token specialization is the dominant effect.

### Throughput

Table 2 reports mean throughput for the dense baseline and the token_topk grouped-gather path.

**Table 2:** Mean throughput (tokens/s) across three seeds.

| Configuration              | Throughput (tokens/s) | Fraction of dense |
|---------------------------|----------------------:|------------------:|
| Dense baseline             | 225,837               | 100%              |
| token_topk gather @ 50%    | 14,351                | 6.4%              |
| token_topk gather @ 25%    | 14,181                | 6.3%              |
| token_topk gather @ 12.5%  | 15,396                | 6.8%              |

The grouped-gather implementation is substantially slower than the dense baseline across all retention fractions. Python-level index construction, per-token gather/scatter operations, and the absence of kernel fusion produce overhead that overwhelms the reduction in floating-point operations. Notably, throughput does not meaningfully improve as the retained fraction decreases, confirming that the bottleneck is implementation overhead rather than arithmetic volume.

This is a negative result for the deployment-speed hypothesis under the current implementation: the naïve gathered path is not a viable speedup strategy on CPU at this model scale.

### Resource Usage

Maximum resident set size per seed was 384–386 MB. The host reported ~122 GB available memory. No swap was configured. Experiments ran on a Linux aarch64 host with an NVIDIA GB10 GPU visible to the driver (driver version 580.142), but the installed PyTorch wheel (2.11.0+cpu) provided only CPU execution; no CUDA timing was obtained.

## Limitations

1. **Synthetic task only.** The model is trained on a deterministic synthetic next-token task with a small vocabulary. Whether token-conditioned masks preserve quality on natural language with a real pretrained model is unknown. The synthetic task may overstate the information content of token identity, since token-to-next-token mappings are deterministic and unambiguous.

2. **CPU-only execution.** All timing was performed on CPU with a CPU-only PyTorch wheel. No GPU kernel timing was obtained, despite the host having an NVIDIA GB10. The throughput results reflect Python/CPU overhead and do not predict GPU performance with fused kernels.

3. **Naïve implementation.** The grouped-gather path uses unoptimized Python-level index construction and per-token gather/scatter. A fused CUDA kernel or block-sparse/tiled implementation could yield substantially different throughput characteristics. The current results support only the *algorithmic quality* claim, not a *speedup* claim.

4. **Token-id conditioning only.** Masks are keyed exclusively by token id. Tokens that share the same surface form but appear in different contexts receive the same mask. Whether a cheap contextual router (e.g., a small linear projection of the hidden state) would outperform token-id lookup on open-domain language is untested.

5. **Small model scale.** The model has 2 layers, 96-dimensional embeddings, and 384 FFN channels. Scaling behavior—both quality and the calibration stability of per-token masks—is unknown.

6. **Single architecture.** Only one transformer configuration was tested. The relative advantage of token-conditioned masks may depend on FFN width ratio, layer depth, and attention head configuration.

7. **No comparison to learned routing.** Mixture-of-experts and other learned routing methods were not included as baselines. Token-conditioned masks may be complementary to or dominated by such approaches.

8. **No per-seed variance reporting.** While three seeds were run and per-seed metric files are available as artifacts, standard errors across seeds are not reported in the decision log. The mean values should be interpreted accordingly.

## Reproducibility Checklist

- **Code available:** `experiments/token_conditioned_mlp_thinning.py`
- **Seeds reported:** 123, 456, 789
- **Hyperparameters fully specified:** Yes (see Method section and command lines in run notes).
- **Hardware specified:** Linux aarch64, NVIDIA GB10 (driver 580.142), PyTorch 2.11.0+cpu. All timing performed on CPU only.
- **Metrics logged:** Per-seed JSON files and aggregate metrics JSON are available as artifacts.
- **Statistical variability:** Three seeds reported; standard errors are not reported in the decision log but raw per-seed values are available in the per-seed metric files.
- **Negative results reported:** Yes—throughput degradation is fully reported; the grouped-gather implementation is slower than dense at all retention fractions.
- **Calibration procedure documented:** Yes—16 calibration batches, mean absolute activation per token per channel.
- **Dependencies:** Python 3, PyTorch 2.11.0+cpu, NumPy, psutil.
- **Implementation type:** Toy simulation on a synthetic task; not a production validation or real-model benchmark.

## Conclusion

Token-conditioned FFN masks—where the set of retained intermediate channels is selected per token based on calibrated activation magnitudes—preserve model quality substantially better than global or random masks at the same sparsity budget on a controlled synthetic task. At 25% retained FFN width, token-conditioned masks incur only 0.015 mean Δloss compared to 0.110 for global top-*k* and 0.138 for random per-token masks.

However, these results do not constitute a practical speedup method. A naïve grouped-gather CPU implementation runs at only ~6% of dense throughput, with overhead dominating any arithmetic savings. Whether token-conditioned sparsity can be translated into wall-clock gains depends on the availability of fused, hardware-aware sparse kernels—a direction we were unable to validate due to the CPU-only PyTorch installation.

The core finding is that token identity alone carries significant information about which FFN channels are important, at least in the controlled setting studied here. Whether this holds for pretrained language models on natural text, and whether it can be made efficient, are the critical open questions. Specifically: (1) validation on a real pretrained LM layer with natural-token calibration and evaluation, (2) implementation of fused token-grouped FFN kernels on GPU or mapping of masks to block-sparse/tile-friendly groups, and (3) comparison of token-id conditioning versus a cheap contextual router to test whether token id alone suffices for open-domain language.

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Experiment script | `experiments/token_conditioned_mlp_thinning.py` |
| Smoke test metrics | `results/smoke_metrics.json` |
| Smoke test log | `logs/smoke.log` |
| Calibration metrics | `results/calibration_metrics.json` |
| Calibration log | `logs/calibration.log` |
| Final seed 123 metrics | `results/final_seed_123.json` |
| Final seed 456 metrics | `results/final_seed_456.json` |
| Final seed 789 metrics | `results/final_seed_789.json` |
| Aggregate metrics | `results/aggregate_metrics.json` |
| Final multi-seed log | `logs/final_multiseed.log` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260430T173848324346+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T173848324346+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T173848324346+0000/paper_manifest.json` |
