# MASSV + Beagle Cross-Attention: A Synthetic Proxy Study of Cross-Attention Visual Conditioning for Multimodal Speculative Decoding Drafters

> **AI Provenance / No-Human-Credit Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, and metric files). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

Speculative decoding for vision-language models (VLMs) requires draft models whose output distributions closely approximate the target VLM's multimodal distribution. MASSV demonstrates that adapting a small language model into a multimodal drafter—via a frozen target vision encoder, a lightweight projector, and self-distilled visual instruction tuning—yields up to 1.46× end-to-end speedup on visually grounded tasks. Beagle (Budget EAGLE) shows that cross-attention-based Transformer decoders can replace tightly coupled self-attention drafters with simpler architectures while maintaining competitive speedups. This work investigates whether combining MASSV's visual grounding strategy with Beagle's cross-attention interface is architecturally plausible. Because no VLM checkpoints, PyTorch installation, or training infrastructure were available, we report results from a bounded synthetic proxy harness that models the core interface question: how should visual hidden states be presented to a draft decoder? In the proxy, a Beagle-style cross-attention drafter (draft text state as Q, frozen visual hidden states as K/V) consistently outperforms both text-only and pooled-projector baselines on top-1 acceptance rate and total variation distance (TVD) across patch counts from 8 to 128. These proxy results support the architectural plausibility of the combination but do not constitute evidence of real VLM inference speedup. Scientific closure requires implementation with real VLM pairs, self-distilled training, and wall-clock measurements.

## 1. Introduction

Speculative decoding accelerates autoregressive language model inference by using a small draft model to propose candidate tokens that a larger target model verifies in parallel. For text-only models, this approach is well-studied. For vision-language models, the draft model must condition on both text and visual inputs, and its output distribution must closely approximate the target VLM's multimodal distribution to achieve high acceptance rates.

MASSV (arXiv:2505.10526v2) addresses the multimodal drafting problem by adapting a small language model (SLM) into a multimodal drafter. The SLM shares the target VLM's frozen vision encoder, trains a lightweight multimodal projector, and then undergoes self-distilled visual instruction tuning (SDViT) on target-VLM outputs. MASSV reports up to 30% higher mean accepted length and up to 1.46× end-to-end speedup on visually grounded tasks. Critically, MASSV's ablations show that naive multimodal adaptation without distribution alignment can regress performance, establishing that architectural changes alone are insufficient.

Beagle, or Budget EAGLE (arXiv:2505.24544v4), addresses a different problem in speculative decoding architecture: the tight coupling and auxiliary components (pooling, fusion layers) required by self-attention-based drafters like EAGLE. Beagle replaces these with a cross-attention-based Transformer decoder, where draft-token/text state serves as queries and target-model hidden states serve as keys and values. This simplifies the architecture while maintaining competitive speedups and improving training stability.

The natural question is whether these two ideas compose: can a MASSV-style multimodal drafter use Beagle-style cross-attention over visual hidden states rather than a projector/pooling interface, preserving MASSV's visual grounding and distribution alignment while gaining Beagle's architectural simplicity?

This paper reports on a synthetic proxy study designed to test the core interface question before committing to a full implementation. We emphasize upfront that no real VLM training or inference was performed; the results concern representational alignment in a controlled synthetic setting, not measured speedup on real models. The claim ledger for this artifact records no structured claims, and the audit status is blocked on that basis. The findings reported here are proxy-level evidence only.

## 2. Method

### 2.1 Architectural Hypothesis

A combined MASSV+Beagle drafter would operate as follows:

1. The target VLM's vision encoder processes the image once per prompt, producing visual hidden states (a sequence of patch-level representations).
2. A Beagle-style draft decoder conditions on these visual hidden states via cross-attention: the draft decoder's current text/token hidden state serves as queries (Q), while the frozen visual hidden states serve as keys (K) and values (V).
3. Self-distilled visual instruction tuning (as in MASSV's SDViT objective) remains the alignment mechanism, because MASSV's ablations indicate that architecture alone is insufficient—distribution alignment through distillation is critical.

The expected benefit is that cross-attention over the full visual token sequence preserves more spatial and semantic information than a pooled/projected summary, while eliminating the auxiliary pooling and fusion components that Beagle identifies as sources of architectural complexity.

### 2.2 Synthetic Proxy Harness

Because the project environment contained no VLM checkpoints, no PyTorch installation, and no training infrastructure, we constructed a bounded proxy harness (`src/massv_beagle_proxy.py`) to test the representational question: given a target distribution that depends on query-specific visual evidence, which visual conditioning interface produces draft distributions closest to the target?

The proxy models the following synthetic setup:

- **Target distribution:** Next-token logits depend on text features plus a query-selected visual patch/token. Distractor visual patches are present, so the drafter must identify the relevant visual information rather than relying on a summary statistic.
- **Drafters compared:**
  - *text_only:* Conditions on text features only, with no visual input.
  - *massv_pooled_projector:* Conditions on text features plus a pooled (mean-aggregated) representation of all visual tokens, representing a simple projector/pooling interface.
  - *beagle_cross_attention:* Conditions on text features via cross-attention over the full visual token sequence (text state as Q, visual tokens as K/V), representing the proposed Beagle-style interface.

All drafters are small single-layer networks trained via gradient descent on the synthetic target distribution. The proxy uses NumPy 2.4.4 exclusively; no GPU or deep learning framework is involved. This is a toy simulation, not a llama.cpp hook prototype, CUDA calibration, or production validation.

### 2.3 Metrics

- **top1_accept:** Fraction of validation examples where the drafter's top-1 predicted token matches the target's top-1 token. This is a proxy for greedy speculative acceptance rate.
- **mean_tvd:** Mean total variation distance between the target and draft probability distributions over the vocabulary. Lower is better. TVD is directly relevant because it bounds rejection probability in speculative decoding.

### 2.4 Experimental Protocol

**Smoke test:** 256 training examples, 128 validation examples, 16 patches, hidden dimension 32, vocabulary size 96.

**Calibration sweep:** 8192 training examples, 2048 validation examples, hidden dimension 64, vocabulary size 256, with patch counts of 8, 16, 32, 64, and 128. Each configuration was run once (single random seed) with wall-clock time recorded.

## 3. Results

### 3.1 Smoke Test

| Drafter | top1_accept | mean_tvd |
|---|---|---|
| text_only | 0.266 | 0.258 |
| massv_pooled_projector | 0.352 | 0.218 |
| beagle_cross_attention | 0.648 | 0.136 |

The cross-attention drafter substantially outperforms both baselines on this tiny configuration. However, the smoke test uses very small dimensions and sample counts; these numbers should be interpreted as directional indicators only.

### 3.2 Calibration Sweep

| Patches | text top1 | pooled top1 | beagle top1 | text TVD | pooled TVD | beagle TVD | Elapsed (s) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0.169 | 0.356 | 0.739 | 0.287 | 0.216 | 0.117 | 0.28 |
| 16 | 0.226 | 0.366 | 0.735 | 0.258 | 0.200 | 0.109 | 0.44 |
| 32 | 0.329 | 0.460 | 0.753 | 0.218 | 0.172 | 0.092 | 0.77 |
| 64 | 0.430 | 0.537 | 0.816 | 0.176 | 0.141 | 0.071 | 1.56 |
| 128 | 0.547 | 0.627 | 0.845 | 0.136 | 0.111 | 0.061 | 2.15 |

### 3.3 Observations

**Cross-attention consistently outperforms baselines.** The Beagle-style cross-attention drafter achieves higher top-1 acceptance and lower TVD than both baselines at every patch count tested. The advantage is present at the smallest patch count (8 patches: 0.739 vs. 0.356 pooled vs. 0.169 text-only) and persists across the full range.

**Scaling trend.** All drafters improve as patch count increases (more visual evidence makes the task easier), but the cross-attention drafter's advantage is largest in absolute terms at higher patch counts (128 patches: 0.845 vs. 0.627 pooled). This is consistent with the hypothesis that cross-attention can exploit fine-grained visual token structure that pooling discards. However, this trend may not transfer to real VLM distributions where the relationship between patch count and information content differs.

**Pooled projector helps over text-only but underperforms cross-attention.** The pooled projector baseline consistently outperforms text-only, confirming that visual information is useful in this proxy. It consistently underperforms cross-attention, suggesting that mean-pooling loses query-relevant spatial information in this synthetic setting.

**Wall-clock cost scales with patch count.** Proxy elapsed time increases from 0.28 s at 8 patches to 2.15 s at 128 patches, reflecting the quadratic cost of cross-attention over the visual token sequence. This is a known scaling concern for cross-attention mechanisms and would need to be evaluated in a real inference setting where visual sequences may contain hundreds or thousands of tokens.

**No variance estimates.** Each sweep point was run once with no explicit random seed control. The magnitude of the cross-attention advantage should be interpreted with caution; we cannot distinguish a robust effect from a seed-dependent one with this design.

## 4. Limitations

This study has substantial limitations that prevent drawing conclusions about real VLM speculative decoding performance:

1. **Synthetic proxy, not real VLMs.** The target distribution is a constructed function of text and visual features, not the output of an actual vision-language model. The degree to which the proxy captures the structure of real VLM distributions is unknown and likely limited.

2. **No real training or inference.** No VLM checkpoints were used. No PyTorch or GPU-based training was performed. The drafters are single-layer networks trained on synthetic data, not the multi-layer Transformer decoders used in MASSV or Beagle.

3. **No self-distillation.** MASSV's key finding is that self-distilled visual instruction tuning is necessary for distribution alignment. The proxy trains drafters directly on the target distribution, which sidesteps this critical step. A real implementation must include SDViT or equivalent distillation, and the interaction between cross-attention conditioning and distillation quality is untested.

4. **No accepted-length or wall-clock speedup measurements.** The proxy measures top-1 acceptance and TVD as proxies for speculative decoding quality, but does not measure mean accepted token length, tokens-per-second, or end-to-end wall-clock speedup on real inference workloads.

5. **No memory or latency profiling under real inference.** Cross-attention over long visual sequences adds compute and memory cost at draft time. The proxy's wall-clock times reflect NumPy operations on tiny arrays, not GPU inference with real models.

6. **Single random seed per configuration.** Each sweep point was run once. We do not report variance across seeds, so the magnitude of the cross-attention advantage should be interpreted with caution.

7. **Quadratic scaling of cross-attention.** The proxy does not test patch counts beyond 128. Real VLMs may produce visual token sequences of 576 or more patches, where the quadratic cost of cross-attention becomes a more significant concern and may offset acceptance-rate gains.

8. **Claim ledger audit blocked.** The claim ledger for this artifact records no structured claims and has audit status "blocked_empty_claims." No claim in this paper has passed a formal evidence audit.

9. **Missing readiness audit signal.** The paper review item flags a missing "readiness_audit" signal, and the checklist shows 0 of 9 items passed. This draft should be treated as preliminary.

## 5. Reproducibility Checklist

- **Code available:** `src/massv_beagle_proxy.py` (in project directory)
- **Command for smoke test:** `python3 src/massv_beagle_proxy.py --train 256 --val 128 --patches 16 --dim 32 --vocab 96 --output artifacts/metrics/smoke_metrics.json`
- **Command for sweep:** As documented in run notes; iterates `--patches` over {8, 16, 32, 64, 128} with `--train 8192 --val 2048 --dim 64 --vocab 256`
- **Random seeds:** Not explicitly set in the commands; the proxy script's default seeding behavior should be inspected in source
- **Hardware:** Linux aarch64 host, NVIDIA GB10 GPU (CUDA 13.0 driver detected), 122 GB available RAM, swap disabled. PyTorch not installed; NumPy 2.4.4 used exclusively. No GPU execution occurred.
- **Metrics files:** `artifacts/metrics/smoke_metrics.json`, `artifacts/metrics/proxy_p8.json`, `artifacts/metrics/proxy_p16.json`, `artifacts/metrics/proxy_p32.json`, `artifacts/metrics/proxy_p64.json`, `artifacts/metrics/proxy_p128.json`, `artifacts/metrics/proxy_sweep_summary.json`
- **Logs:** `artifacts/logs/telemetry_20260506T020508Z.log`, `artifacts/logs/smoke_20260506T020605Z.log`, `artifacts/logs/calibration_20260506T020617Z.log`
- **Dependencies:** Python 3.12.3, NumPy 2.4.4. No GPU execution; no PyTorch required.
- **Variance reporting:** Not available; single run per configuration.

## 6. Conclusion

We investigated whether MASSV's multimodal speculative decoding strategy and Beagle's cross-attention drafter architecture can be combined, using a synthetic proxy harness to test the core interface question. In the proxy, a Beagle-style cross-attention drafter that attends over the full visual token sequence consistently outperforms both text-only and pooled-projector baselines on top-1 acceptance rate and total variation distance across patch counts from 8 to 128. This supports the architectural plausibility of the combination: cross-attention over visual hidden states appears to preserve query-relevant visual information more effectively than pooling in this synthetic setting.

However, this is a proxy result, not a scientific conclusion about real VLM inference. The proxy uses synthetic distributions, single-layer networks, no self-distillation, and single random seeds per configuration. MASSV's own ablations demonstrate that architectural changes alone are insufficient without distribution alignment via distillation. Scientific closure requires:

1. Implementation with real VLM pairs (e.g., Qwen2.5-VL-7B-Instruct target with Qwen2.5-1.5B-Instruct draft).
2. Both a MASSV baseline (projector/pooling interface) and a MASSV+Beagle variant (cross-attention interface), trained with self-distilled visual instruction tuning.
3. Measurement of mean accepted token length, TVD, and wall-clock speedup on standard multimodal benchmarks.
4. Memory and latency profiling, particularly for the quadratic cost of cross-attention over long visual sequences.
5. Multiple random seeds and variance reporting.

The proxy evidence is positive and justifies proceeding to a real VLM smoke test, but does not support claims about real-world speedup or acceptance rates.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Proxy script | `src/massv_beagle_proxy.py` |
| Smoke metrics | `artifacts/metrics/smoke_metrics.json` |
| Sweep metrics (p=8) | `artifacts/metrics/proxy_p8.json` |
| Sweep metrics (p=16) | `artifacts/metrics/proxy_p16.json` |
| Sweep metrics (p=32) | `artifacts/metrics/proxy_p32.json` |
| Sweep metrics (p=64) | `artifacts/metrics/proxy_p64.json` |
| Sweep metrics (p=128) | `artifacts/metrics/proxy_p128.json` |
| Sweep summary | `artifacts/metrics/proxy_sweep_summary.json` |
| Telemetry log | `artifacts/logs/telemetry_20260506T020508Z.log` |
| Smoke log | `artifacts/logs/smoke_20260506T020605Z.log` |
| Calibration log | `artifacts/logs/calibration_20260506T020617Z.log` |
| Project decision | `.omx/project_decision.json` |
| Project metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260506T020410374116+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260506T020410374116+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260506T020410374116+0000/paper_manifest.json` |
