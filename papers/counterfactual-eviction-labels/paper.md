# Counterfactual Eviction Labels for KV-Cache Retention: A Viability Study on Synthetic Recall Traces

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision logs, metrics files, and benchmark outputs). The operator who released this artifact claims no personal authorship credit for the writing or scientific results. Readers should treat this document as an unreviewed AI-generated research artifact and evaluate its claims accordingly.

---

## Abstract

We investigate whether offline counterfactual labels—computed by masking candidate KV-cache blocks from attention and measuring the resulting increase in answer-token negative log-likelihood—can identify causally important cache blocks for future output. On synthetic key-value recall traces with 48 fact blocks per case, counterfactual labels ranked the answer-critical block first in all 32 test cases (mean delta percentile 1.000, mean NLL margin over median block +9.24, std 3.33). At a 10% retention budget, counterfactual labels achieved 1.000 target recall, compared to 0.906 for attention-mass ranking, 0.156 for recency, and 0.156 for random selection. However, attention-mass ranking already achieved 1.000 recall at a 20% budget, indicating that on this exact-copy recall task the counterfactual signal's advantage is confined to tight budgets. The method requires O(candidate blocks) additional forward passes per trace, making it suitable only as an offline teacher signal for distillation, not as an online eviction policy. We discuss these limitations and outline conditions under which counterfactual labels may provide greater marginal value over cheaper baselines.

## Introduction

Autoregressive language models with key-value (KV) caches face growing memory pressure as context lengths increase. Production systems employ eviction policies that discard cache blocks deemed unlikely to be needed for future generation. Common heuristics include recency (evict the oldest blocks), accumulated attention mass (evict blocks receiving little attention during prefill), and hybrid strategies combining protected windows with attention-based scoring.

A fundamental limitation of these heuristics is that they measure past or current attention patterns rather than predicting future causal importance. A block that received modest attention during prefill may be critical for answering a downstream question, while a heavily attended block may be irrelevant to the actual output. Recent work in production KV-cache management has begun to frame eviction as a prediction problem. Apple's KVP framework proposes learning to rank tokens by predicted future usefulness, and NVIDIA TensorRT-LLM exposes priority and duration controls for KV retention that presuppose some scoring mechanism. OpenVINO documents current attention-score and block-wise eviction alongside the accuracy/memory tradeoff inherent in these decisions.

This raises the question: can we construct high-quality supervision labels that identify which cache blocks are causally necessary for correct future output? If so, these labels could serve as a teacher signal for training a cheap online scorer that approximates counterfactual importance from features available at prefill or decode time.

We test a concrete labeling procedure: for a completed prompt-and-answer trace, mask one candidate fact block from attention, recompute the answer-token negative log-likelihood (NLL), and assign that block a label equal to the NLL increase relative to the unmasked baseline. A large positive delta indicates that the masked block was causally important for producing the correct answer.

We evaluate these labels on controlled synthetic recall traces using distilgpt2, comparing against attention-mass, recency, and random baselines at 10%, 20%, and 30% retention budgets. Our results show that counterfactual labels are a viable teacher signal on this task, but we emphasize that scientific closure for real workloads requires harder benchmarks and a trained online scorer.

## Method

### Counterfactual Labeling Procedure

For each completed prompt-and-answer trace, we:

1. Run one full forward pass and record the answer-token NLL as the baseline.
2. For each candidate KV block (in our setting, each fact line), run one forward pass with that block's key positions masked from attention, and record the resulting answer-token NLL.
3. Assign each block a counterfactual label: `masked_answer_nll - full_answer_nll`.

A positive label indicates that removing the block worsened the model's ability to predict the correct answer. Blocks with larger labels are more causally important for the answer.

This procedure approximates KV eviction by masking candidate key positions from future attention in a full causal forward pass. It is a label-generation method, not a production serving patch. The relationship between these masking-based labels and actual cache-eviction outcomes—where blocks are removed from the cache before or during decode, potentially affecting KV-compression behavior in subsequent layers—remains to be validated.

### Synthetic Recall Task

We construct synthetic key-value recall prompts. Each case consists of a list of fact lines of the form `CODE### -> value-string`, followed by a question querying one specific code. For example:

```
CODE017 -> purple-river-1234
CODE032 -> blue-mountain-5678
...
Question: value for CODE017? Answer: purple-river-1234
```

Each fact line is treated as a candidate KV block. The queried fact is the target block; all other facts are distractors. This design ensures a known ground truth for which block is answer-critical, but it also makes the task relatively easy: the answer is a verbatim copy of a context span, which allows attention-mass heuristics to perform well.

### Baseline Ranking Methods

We compare counterfactual labels against three baseline ranking methods:

- **Attention mass:** Rank blocks by the total attention weight the answer token assigns to each block's key positions during the full forward pass.
- **Recency:** Rank blocks by position, with later positions considered more recent (and thus more likely to be retained).
- **Random:** Deterministic random ordering as a lower bound.

For each method, we compute target recall at retention budgets of 10%, 20%, and 30% of blocks.

### Implementation and Experimental Configuration

The experiment is implemented in `scripts/counterfactual_eviction_labels.py`. The script generates synthetic cases, runs full and counterfactual forward passes, computes labels and baseline scores, and writes structured JSON results.

We ran three configurations:

1. **Smoke test** (`sshleifer/tiny-gpt2`, 2 cases × 8 facts): Dependency and runtime check. This model is intentionally weak and produced flat/noisy labels; results serve as a sanity check on the pipeline rather than scientific evidence.

2. **Calibration** (`distilgpt2`, 6 cases × 20 facts): Verification that the positive signal reproduces on the target model at small scale.

3. **Main run** (`distilgpt2`, 32 cases × 48 facts): Primary evaluation. This produced 1,536 counterfactual block masks plus 32 baseline forward passes.

All runs used CUDA on an NVIDIA GB10 GPU. The environment reused an existing virtualenv containing `torch 2.11.0+cu130` and `transformers 5.7.0`; no additional package installation was required.

## Results

### Main Run Metrics

The main run (32 cases × 48 fact blocks) completed in 29.70 seconds of evaluation time, achieving 52.80 forward passes per second. System memory remained abundant throughout (MemAvailable ≈ 114.7 GiB at completion; swap disabled). GPU utilization was 94% at run end. The GB10 GPU reported memory fields as `[N/A]` via `nvidia-smi`, so GPU memory consumption could not be recorded.

### Counterfactual Label Quality

The answer-critical (target) fact block received the highest counterfactual NLL delta in all 32 cases:

| Metric | Value |
|--------|-------|
| Mean target delta percentile | 1.000 |
| Mean NLL margin over median block | +9.24 (std 3.33) |
| Target top-ranked | 32/32 |

The standard deviation of 3.33 NLL across cases indicates some variability in the magnitude of the counterfactual effect, though the ordinal ranking of the target block was consistent.

### Target Recall at Retention Budgets

| Method | Top-10% Recall | Top-20% Recall | Top-30% Recall |
|--------|---------------|---------------|---------------|
| Counterfactual labels | 1.000 | 1.000 | 1.000 |
| Attention mass | 0.906 | 1.000 | 1.000 |
| Recency | 0.156 | 0.281 | 0.344 |
| Random | 0.156 | 0.219 | 0.219 |

Counterfactual labels achieved perfect target recall at all budgets. Attention mass achieved perfect recall at 20% and 30% but missed the target in approximately 9.4% of cases at the 10% budget (3 of 32 cases). Recency and random baselines performed poorly, as expected given that the target fact's position is uniformly distributed among the 48 fact lines.

The key comparison is between counterfactual labels and attention mass at the 10% budget: counterfactual labels offer a 9.4 percentage-point advantage. Whether this advantage is practically significant depends on the cost one is willing to pay for it (see Limitations).

### Relationship Between Counterfactual Labels and Attention Mass

The mean Spearman rank correlation between counterfactual labels and attention mass across all blocks was −0.024 (std 0.261). This near-zero correlation indicates that the counterfactual label is not merely a monotone transformation of aggregate attention. Although both methods frequently identify the target block, they rank the remaining (distractor) blocks differently. The counterfactual signal provides a causal rather than correlational basis for retention decisions, but on this task the practical consequence of this difference is modest: both methods find the target, and the distractor rankings do not affect target recall.

### Calibration Run

The calibration run (6 cases × 20 facts) reproduced the positive signal: target counterfactual percentile was 1.000 and top-10% target recall was 1.000, consistent with the main run. This provides some evidence that the result is not an artifact of a particular random seed or case configuration, though the sample size is small.

### Smoke Test

The `sshleifer/tiny-gpt2` smoke test produced flat/noisy labels, consistent with that model's known limitations. This run confirmed that the pipeline executed without errors and that label quality depends on model capacity. It does not constitute scientific evidence about the labeling method itself.

## Limitations

### Synthetic Exact-Copy Recall Task

The synthetic task requires the model to reproduce a value string that appears verbatim in the context. This makes answer-token attention mass a strong baseline: the model can largely solve the task by attending to the token sequence it must copy. On harder tasks where the answer requires reasoning over multiple blocks, non-lexical inference, or synthesis of information not directly present in any single block, attention-mass heuristics may degrade more substantially, and the counterfactual label's advantage may grow. However, we have not yet demonstrated this empirically. The current result establishes viability on an easy task; it does not establish utility on hard tasks.

### Forward-Pass Approximation of Eviction

Our method approximates KV eviction by masking key positions from attention during a full forward pass. A production KV-cache eviction system would operate differently: it would remove blocks from the cache before or during decode, potentially affecting the KV-compression behavior of subsequent layers and the dynamics of autoregressive generation. The gap between masking-based labels and actual cache-eviction outcomes is unknown and represents an important open question.

### Computational Cost

Counterfactual label generation requires one additional forward pass per candidate block per trace. The main run used 1,536 counterfactual forwards for 32 short examples. For long contexts with thousands of candidate blocks, this cost becomes substantial. The method is therefore positioned as an offline teacher signal for dataset construction and distillation, not as an online serving-time eviction policy. Whether a cheap online scorer trained on these labels can approach their quality is an open question.

### Model Scale

All experiments used distilgpt2, a small model (approximately 82M parameters). Whether counterfactual labels retain their discriminative quality at larger model scales and on more complex distributions of evidence remains to be tested. The NLL margin of +9.24 may compress or expand at scale; we have no data to extrapolate.

### Single-Answer-Token Evaluation

Our labels are computed from the NLL of a single answer token (or a short answer span). For open-ended generation tasks where quality is measured over many tokens, the relationship between single-token NLL deltas and overall output quality is less direct. A block that modestly affects many tokens might receive a smaller per-token label than one that dramatically affects a single token, even if the aggregate output impact is larger.

### Limited Statistical Power

The main run comprises 32 cases. While the target block was top-ranked in all 32 cases, confidence intervals around the recall rates are non-trivial at this sample size. A binomial 95% confidence interval on the observed 1.000 recall at 10% budget extends down to approximately 0.891, meaning we cannot rule out a non-trivial failure rate on larger samples.

## Reproducibility Checklist

- **Code:** `scripts/counterfactual_eviction_labels.py` (included in project directory).
- **Model:** `distilgpt2` (publicly available via Hugging Face).
- **Environment:** `torch 2.11.0+cu130`, `transformers 5.7.0`, CUDA, NVIDIA GB10.
- **Random seeds:** Deterministic random baseline used; full seed specification available in script.
- **Main result file:** `results/main_distilgpt2_32x48.json`.
- **Metrics summary:** `results/metrics_summary.json`.
- **Calibration result:** `results/calibration_distilgpt2_6x20.json`.
- **Smoke result:** `results/smoke_tiny_gpt2.json`.
- **Logs:** `logs/smoke_tiny_gpt2.log`, `logs/calibration_distilgpt2_6x20.log`, `logs/main_distilgpt2_32x48.log`.
- **Run notes:** `run_notes.md`.
- **Decision record:** `.omx/project_decision.json`.
- **Hardware:** NVIDIA GB10, host with ≥114 GiB available RAM, swap disabled.
- **Runtime:** 29.70 s for main evaluation (1,568 total forward passes).
- **GPU memory:** Not recorded (GB10 reports `[N/A]` for memory fields via `nvidia-smi`).

## Conclusion

Offline counterfactual eviction labels—computed by masking candidate KV blocks and measuring answer-token NLL increases—provide a viable teacher signal for identifying causally important cache blocks. On synthetic key-value recall traces with 48 distractor facts, counterfactual labels ranked the answer-critical block first in all 32 test cases and achieved perfect target recall at a 10% retention budget, outperforming attention-mass ranking (0.906 at 10%), recency (0.156), and random selection (0.156).

However, the practical significance of this result is bounded by three factors. First, attention-mass ranking already achieves near-perfect recall on this exact-copy task (1.000 at 20%), limiting the marginal value of counterfactual labels to tight retention budgets. Second, the O(candidate blocks) cost of label generation restricts the method to offline dataset construction rather than online serving. Third, the synthetic recall setting does not exercise the regimes where cheap heuristics are most likely to fail—non-lexical reasoning, multi-hop inference, and long-context tasks where the answer-critical evidence is not a direct copy of a queried key.

The path forward is distillation: training a cheap online scorer from features available at prefill or decode time (KV vectors, positions, attention summaries, segment metadata) using counterfactual labels as supervision. If such a scorer can approach counterfactual-label quality on harder benchmarks where attention heuristics degrade, the label-generation cost may be justified. If it cannot, the method should be abandoned. We regard the current result as a promising viability signal for this distillation branch, not as scientific closure for real workloads.

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Run notes | `run_notes.md` |
| Source references | `sources.md` |
| Experiment script | `scripts/counterfactual_eviction_labels.py` |
| Metrics summary | `results/metrics_summary.json` |
| Smoke test result | `results/smoke_tiny_gpt2.json` |
| Calibration result | `results/calibration_distilgpt2_6x20.json` |
| Main result | `results/main_distilgpt2_32x48.json` |
| Smoke log | `logs/smoke_tiny_gpt2.log` |
| Calibration log | `logs/calibration_distilgpt2_6x20.log` |
| Main log | `logs/main_distilgpt2_32x48.log` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T140348585489+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T140348585489+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T140348585489+0000/paper_manifest.json` |
