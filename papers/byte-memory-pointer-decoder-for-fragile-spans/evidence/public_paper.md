# Byte-Memory Pointer Decoder for Fragile Spans

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

Subword tokenizers systematically fragment certain byte sequences—numeric literals, file paths, code identifiers, and punctuation-heavy strings—into tokens that small language models struggle to reproduce verbatim. We investigate whether a pointer/cross-attention decoder that attends to an explicit byte-memory buffer of detected fragile spans can recover exact-copy performance without receiving current-byte generation-slot labels at inference time. In a controlled toy benchmark on a tiny causal transformer (vocab size 180, 720 training examples, 90 test examples), the byte-memory pointer decoder achieves 0.644 exact-match accuracy and 0.910 byte accuracy, compared to 0.000 and 0.665 for a same-run BPE-only baseline and 0.000 and 0.626 for a parent non-oracle byte-memory prefix approach. Pointer position accuracy on supervised memory positions reaches 0.921. Per-category exact-match ranges from 1.000 (numeric) to 0.267 (punctuation-dense), revealing substantial heterogeneity. Latency overhead is 1.127× relative to BPE-only. These results are limited to synthetic data, a single small model, CPU execution, and training with position supervision derived from gold byte matches. External replication on real-world data and larger models is necessary before drawing broader conclusions.

---

## 1. Introduction

Byte-pair encoding (BPE) and related subword tokenizers fragment input sequences into variable-length tokens whose boundaries rarely align with spans that require verbatim reproduction. Certain categories of text—numeric strings, file paths, code identifiers, multilingual tokens, and punctuation-heavy sequences—are particularly susceptible to fragmentation. We refer to these as *fragile spans*: substrings whose tokenization destroys the structural regularities a model would need to reconstruct them exactly.

A prior investigation in the same project lineage tested a naive non-oracle causal byte-memory prefix, which prepends detected fragile-span bytes to the token sequence before the decoder processes it. That approach failed: it scored exact-match 0.000, byte accuracy 0.626 (below the BPE-only baseline of 0.644), and loss 0.827 (above the BPE-only 0.772), with a latency ratio of 1.024×. Simply exposing byte content in a causal prefix does not, by itself, teach a small decoder to copy those bytes at the correct generation positions.

This report investigates a successor hypothesis: that explicit addressable byte-memory pointers—implemented as cross-attention from decoder hidden states to a byte-memory buffer, combined with a learned pointer gate that mixes pointer logits with vocabulary logits—are materially different from a naive causal prefix and can recover held-out fragile-span copying. A critical design constraint is that generation positions receive no current-byte generation-slot labels or direct current-byte priors; the decoder must learn to attend to the correct memory position and emit the pointed-to byte autonomously.

We describe the method, report benchmark results from a controlled toy experiment, and discuss the substantial limitations that constrain interpretation.

---

## 2. Method

### 2.1 Byte-Memory Pointer Decoder Architecture

The decoder is a small causal transformer that incorporates three modifications relative to a standard BPE-only language model:

1. **Byte-memory buffer.** Detected fragile-span bytes are stored in a flat memory buffer. Each memory position holds a byte-level embedding derived from the byte value.

2. **Cross-attention to byte memory.** At each decoder layer, a cross-attention head attends from the decoder hidden state to all byte-memory positions. The attention output is concatenated with the standard self-attention output and projected back to the model dimension.

3. **Pointer gate and scatter-add logits.** A scalar gate $g \in [0, 1]$ is computed from the decoder hidden state. The cross-attention distribution over memory positions is interpreted as a pointer distribution. For each memory position $j$ attending with weight $\alpha_j$, the byte value $b_j$ at that position contributes $g \cdot \alpha_j$ to the logit for byte token $b_j$ in the output vocabulary, via scatter-add. The remaining $(1 - g)$ weight scales the standard vocabulary logits. The final logit for token $t$ is:

$$\text{logit}(t) = (1 - g) \cdot \text{logit}_{\text{vocab}}(t) + g \cdot \sum_{j: b_j = t} \alpha_j$$

### 2.2 Training Signal

During training, pointer targets are derived from gold byte matches: when the gold output byte at a generation position matches a byte in the memory buffer, the target pointer position is the index of that matching byte in memory. This constitutes a form of position supervision that is available only when gold bytes are known and align with memory contents. At inference time, no gold information is available; the decoder must rely entirely on its learned attention and gating.

### 2.3 Constraint: No Current-Byte Generation-Slot Labels

A deliberate design constraint forbids providing the current target byte as an input at generation positions. The first generation input is always a BOS token, not the current target byte. This ensures the decoder cannot solve the task by simply reading the answer from its input and must instead learn to retrieve it from the byte-memory buffer via pointer attention.

---

## 3. Experimental Setup

### 3.1 Benchmark Configuration

| Parameter | Value |
|---|---|
| Training examples | 720 |
| Test examples | 90 |
| Random seed | 3433677 |
| Training epochs | 8 |
| Batch size | 24 |
| Vocabulary size | 180 |
| Device | CPU |
| PyTorch version | 2.11.0+cu130 |

### 3.2 Baselines

Two baselines are compared:

- **BPE-only baseline:** The same tiny causal transformer without byte-memory cross-attention or pointer mechanisms, trained and evaluated in the same run.
- **Parent non-oracle byte-memory prefix:** A prior approach from the parent project that prepends detected fragile-span bytes as a causal prefix before the token sequence, without cross-attention or pointer mechanisms. Its reported metrics (exact-match 0.000, byte accuracy 0.626, loss 0.827, latency ratio 1.024× vs BPE-only) serve as an external reference.

### 3.3 Data

The benchmark uses synthetic fragile-span examples spanning six categories: numeric, code, path, noisy multilingual, mixed-case ID, and punctuation-dense. The fragile-span detector achieves precision 1.000, recall 1.000, and F1 1.000 on this synthetic data, meaning detection is effectively perfect and does not introduce confounding retrieval errors.

### 3.4 Metrics

- **Exact-match accuracy:** Fraction of test examples where the full fragile span is reproduced without any byte error.
- **Byte accuracy:** Fraction of individual bytes correctly predicted, averaged over all generation positions.
- **Mean cross-entropy loss:** Average loss over test examples.
- **Mean latency:** Wall-clock time per example during autoregressive generation (CPU).
- **Pointer position accuracy:** Fraction of supervised memory positions where the pointer distribution's argmax matches the gold pointer target.

### 3.5 Verification

Fifteen unit tests passed, including regression tests verifying that: (a) byte-memory positions are present in the input, (b) pointer targets exist for training, (c) the first generation input is BOS rather than the current target byte, and (d) benchmark artifacts and metrics are created. Compilation with `compileall` succeeded.

---

## 4. Results

### 4.1 Main Comparison

| Metric | BPE-only | Pointer Decoder | Delta |
|---|---|---|---|
| Exact-match accuracy | 0.000 | 0.644 | +0.644 |
| Byte accuracy | 0.665 | 0.910 | +0.245 |
| Mean loss | 0.749 | 0.104 | −0.645 |
| Mean latency (ms/example) | 124.908 | 140.778 | +15.869 |
| Latency ratio | 1.000 | 1.127 | +0.127 |

The pointer decoder achieves non-trivial exact-match accuracy (0.644) where the BPE-only baseline achieves zero, and improves byte accuracy by 24.5 percentage points. Loss decreases by 0.645. Latency increases by 15.9 ms per example, a 12.7% overhead.

### 4.2 Comparison to Parent Non-Oracle Prefix

Relative to the parent project's non-oracle byte-memory prefix (exact-match 0.000, byte accuracy 0.626, loss 0.827), the pointer decoder improves exact-match by +0.644, byte accuracy by +0.284, and loss by −0.723. The naive prefix approach was strictly worse than BPE-only on both byte accuracy and loss; the pointer approach reverses this failure.

### 4.3 Pointer Position Accuracy

On supervised memory positions where gold bytes match memory bytes, the pointer distribution's argmax matches the gold target with accuracy 0.921. This indicates the cross-attention mechanism learns to localize the correct memory position with high reliability when the target byte exists in memory.

### 4.4 Per-Category Breakdown

| Category | Exact-Match |
|---|---|
| Numeric | 1.000 |
| Code | 0.933 |
| Path | 0.667 |
| Noisy multilingual | 0.600 |
| Mixed-case ID | 0.400 |
| Punctuation-dense | 0.267 |

Performance varies dramatically across categories. Numeric and code spans are nearly perfectly copied. Path spans achieve two-thirds exact-match. Noisy multilingual, mixed-case ID, and punctuation-dense spans remain substantially harder, with punctuation-dense spans achieving only 0.267 exact-match—less than half the overall average.

---

## 5. Limitations

1. **Synthetic data only.** All training and test examples are synthetically generated. The fragile-span detector achieves perfect precision and recall on this data, which is unlikely to hold on real-world text. The distribution of fragile-span categories and their difficulty may not reflect production workloads.

2. **Tiny model and vocabulary.** The benchmark uses a single small causal transformer with a vocabulary of 180 tokens. Results may not transfer to larger models with richer vocabularies where BPE fragmentation patterns differ.

3. **Position supervision during training.** Pointer targets are derived from gold byte matches, providing the model with position supervision that is unavailable at inference time. The gap between training supervision and inference conditions represents a form of exposure bias whose impact has not been quantified.

4. **No duplicate or reordered memory stress test.** The current benchmark does not evaluate scenarios where the byte-memory buffer contains duplicate byte values (creating ambiguous pointer targets) or where memory positions are reordered relative to training distribution. These scenarios are expected to be harder and remain untested.

5. **CPU-only latency measurement.** All latency measurements are taken on CPU. GPU latency characteristics may differ substantially, and the 1.127× overhead ratio may not hold on accelerated hardware.

6. **Single seed and single hyperparameter configuration.** Only one random seed (3433677) and one hyperparameter setting (8 epochs, batch size 24, vocab size 180) are reported. Variance across seeds and sensitivity to hyperparameters are unknown.

7. **Category-specific weaknesses.** Punctuation-dense spans (0.267 exact-match) and mixed-case IDs (0.400) remain substantially below the overall average. The method in its current form does not solve fragile-span copying uniformly.

8. **No real-world validation.** No evaluation on actual code repositories, configuration files, log data, or natural text with naturally occurring fragile spans has been performed.

---

## 6. Reproducibility Checklist

| Item | Status |
|---|---|
| Code available in project directory | Yes (`src/pointer_decoder_probe.py`, `src/benchmark_byte_assist.py`, and supporting modules) |
| Unit tests with regression coverage | Yes (15 tests, including pointer-specific constraints) |
| Random seed specified | Yes (3433677) |
| Training hyperparameters documented | Yes (epochs 8, batch size 24, vocab size 180, train count 720, test count 90) |
| Hardware and software environment documented | Yes (CPU, PyTorch 2.11.0+cu130, Python 3, `uv` package manager) |
| Prediction artifacts saved | Yes (JSONL prediction files for both pointer decoder and BPE-only) |
| Tokenizer artifacts saved | Yes (`pointer_mini_bpe_tokenizer.json`) |
| Train/test split artifacts saved | Yes (`train_pointer_examples.jsonl`, `test_pointer_examples.jsonl`) |
| Metrics files saved | Yes (`metrics/pointer_decoder_probe_metrics.json`, `metrics/byte_assist_mvp_metrics.json`) |
| External dataset dependencies | None (synthetic data generated in-code) |
| Multi-seed variance reported | No |
| GPU results reported | No (CPU only) |

---

## 7. Conclusion

In a controlled toy benchmark on a tiny causal transformer with synthetic fragile-span data, a byte-memory pointer decoder with cross-attention and a learned pointer gate achieves 0.644 exact-match accuracy and 0.910 byte accuracy, substantially outperforming both a BPE-only baseline (0.000 / 0.665) and a prior non-oracle byte-memory prefix approach (0.000 / 0.626). These results support the hypothesis that explicit addressable byte-memory pointers are functionally distinct from a naive causal byte-memory prefix and can recover fragile-span copying without current-byte generation-slot labels.

However, the evidence is bounded by significant limitations: synthetic data, a single small model, position supervision during training, untested memory ambiguity scenarios, CPU-only measurement, and pronounced category-specific weaknesses (punctuation-dense exact-match of 0.267). The current project artifacts support this finding in the tested setting; they do not establish that the method works universally or at scale.

The recommended next step is to stress-test the pointer decoder on duplicate/reordered byte memories and harder real code/config snippets before considering larger model integration. External replication on real-world data with naturally occurring fragile spans and imperfect detection is necessary to assess practical applicability.

---

## Referenced Artifacts

### Result files
- `artifacts/pointer_decoder_probe/pointer_decoder_predictions.jsonl`
- `artifacts/pointer_decoder_probe/bpe_only_predictions.jsonl`
- `artifacts/pointer_decoder_probe/pointer_mini_bpe_tokenizer.json`
- `artifacts/pointer_decoder_probe/test_pointer_examples.jsonl`
- `artifacts/pointer_decoder_probe/train_pointer_examples.jsonl`
- `artifacts/byte_assist_mvp/detector_predictions.jsonl`
- `artifacts/byte_assist_mvp/synthetic_fragile_spans.jsonl`

### Source and test files
- `src/pointer_decoder_probe.py`
- `src/benchmark_byte_assist.py`
- `src/torch_transformer_lm_probe.py`
- `src/trainable_copy_probe.py`
- `src/autoregressive_tokenizer_probe.py`
- `tests/test_pointer_decoder_probe.py`
- `tests/test_byte_assist_parent.py`

### Metrics and decision files
- `metrics/pointer_decoder_probe_metrics.json`
- `metrics/byte_assist_mvp_metrics.json`
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `run_notes.md`

### Paper-specific artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
