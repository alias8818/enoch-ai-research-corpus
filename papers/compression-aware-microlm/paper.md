# Compression-Aware Tokenization for Micro Language Models: A Bounded Viability Study

> **AI provenance notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metric files, evidence bundles). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether compression-aware byte-pair encoding (BPE) tokenization improves byte-normalized validation loss for very small language models. Using an add-alpha n-gram micro language model over a BPE-tokenized byte stream, we measure validation bits per original byte (bpb) across n-gram orders 2–5 and merge counts 0–256 on the Tiny Shakespeare corpus. Compression-aware tokenization yields substantial improvements for context-constrained models: a 19.8% bpb reduction at order 2 (256 merges) and an 8.8% reduction at order 3 (32 merges). However, the benefit vanishes at higher n-gram orders: order-4 and order-5 byte-token baselines match or exceed all compression-aware variants. The token-count compression from BPE (down to 0.51 tokens/byte at 256 merges) reliably shortens sequences, but the resulting vocabulary expansion and context sparsity negate the advantage once the model has sufficient local context. These results bound the viability of compression-aware tokenization to settings with explicit context or compute bottlenecks and motivate parameter-matched neural micro-model follow-ups.

## Introduction

Standard language model evaluation reports loss in nats or bits per token. When tokenizers differ, this metric conflates tokenization quality with model quality. A natural alternative is bits per original byte (bpb), which normalizes across tokenization schemes and measures the end-to-end compression achieved by the tokenizer–model pipeline.

Compression-aware tokenization—where merge rules are selected to maximize token-count savings on the training data—produces shorter token sequences. If a language model could exploit these shorter sequences without penalty, bpb should improve. However, shorter sequences come at a cost: larger vocabularies, sparser n-gram contexts, and more parameters to estimate from limited data. Whether the net effect is positive depends on the model's capacity to absorb the expanded vocabulary against its context window.

We study this trade-off in the simplest setting that exposes it: an add-alpha n-gram language model over byte-pair-encoded text, evaluated on held-out data as bits per original byte. This micro-model setup is not a claim about neural language models; it is a controlled probe of the tokenization–context interaction. The n-gram model was chosen precisely because it makes the context–vocabulary trade-off legible: every additional merge entry inflates the conditioning vocabulary $|V|$ in the smoothing denominator, and every additional n-gram context either gains sufficient count or remains sparse.

The central finding is a bounded one: compression-aware tokenization helps when the model is context-starved but hurts or has no effect when the model has adequate local context. This boundary condition is the primary contribution.

## Method

### Tokenizer

We implement a greedy BPE-style tokenizer. Starting from a byte-level vocabulary of 256 entries, merge candidates are scored by the token-count savings they produce on the training split. The merge with the highest savings is applied, and the process repeats for a specified number of merge steps. Merge counts tested: 0 (byte baseline), 32, 64, 128, 256.

The merge selection is deterministic: at each step, the pair yielding the greatest reduction in total token count on the training data is chosen. No frequency threshold or regularization is applied.

### Language Model

The language model is an add-alpha (Laplace-smoothed) n-gram model. Given a token stream produced by the tokenizer, the model estimates conditional probabilities:

$$P(t_i \mid t_{i-n+1}, \ldots, t_{i-1}) = \frac{c(t_{i-n+1}, \ldots, t_i) + \alpha}{c(t_{i-n+1}, \ldots, t_{i-1}) + \alpha \cdot |V|}$$

where $|V|$ is the vocabulary size (256 + number of merges) and $\alpha$ is a fixed smoothing parameter. We sweep n-gram orders 2 through 5.

The add-alpha smoother was chosen for simplicity and determinism. It makes the vocabulary-size penalty explicit: as $|V|$ grows with additional BPE merges, the smoothing mass in the denominator increases, diluting probability mass for observed n-grams. This mechanism directly encodes the trade-off under study.

### Evaluation Metric

The primary metric is validation bits per original byte (bpb). For a validation sequence of $B$ original bytes tokenized into $T$ tokens, bpb is:

$$\text{bpb} = \frac{-\sum_{i=1}^{T} \log_2 P(t_i \mid \text{context})}{B}$$

This measures the total predictive coding cost normalized by the original byte count, making it comparable across tokenization schemes. A model that achieves lower bpb is, by definition, a better compressor of the original byte stream.

Secondary metrics include token compression ratio (tokens per byte), n-gram table entry count, peak RSS, and swap telemetry.

### Dataset

We use the Tiny Shakespeare corpus. The first 200,000 bytes form the training split; the next 50,000 bytes form the validation split. This is a small, domain-homogeneous English literary text. The choice was deliberate: a small corpus makes the data-sparsity effects of vocabulary expansion more visible, which is precisely the regime where the trade-off under study is most legible.

### Experimental Protocol

Three runs were executed:

1. **Smoke test** (20K train / 5K val bytes, order 4, merges 0/16/32) to verify pipeline correctness and resource safety.
2. **Main decision run** (200K train / 50K val bytes, order 5, merges 0/32/64/128/256).
3. **Order sweep** (200K train / 50K val bytes, orders 2–5, merges 0/32/64/128/256 for each order).

All runs were executed on Linux 6.17.0-1014-nvidia-aarch64, Python 3.12.3, with swap disabled (SwapTotal: 0 KiB). The experiment script is a single-file Python program with no external ML dependencies beyond the standard library.

## Results

### Token Compression

BPE merges reliably reduced the token-to-byte ratio on the validation set:

| Merges | Tokens/Byte |
|-------:|------------:|
| 0      | 1.00000     |
| 32     | 0.74392     |
| 64     | 0.66880     |
| 128    | 0.58974     |
| 256    | 0.51180     |

At 256 merges, the validation sequence is roughly half the length of the byte-level original. This compression is monotonic and substantial: every doubling of merge count yields a meaningful reduction in tokens per byte.

### Bits per Original Byte by N-gram Order

| Order | Best Merges | Baseline bpb | Best bpb  | Relative Change |
|------:|------------:|-------------:|----------:|---------------:|
| 2     | 256         | 3.6589       | 2.9344    | −19.80%        |
| 3     | 32          | 2.9557       | 2.6957    | −8.80%         |
| 4     | 0           | 2.6379       | 2.6379    | 0.00%          |
| 5     | 0           | 2.7465       | 2.7465    | 0.00%          |

At order 2, the best configuration uses the maximum number of merges (256), achieving a 19.8% bpb reduction. At order 3, the optimum shifts to only 32 merges, yielding an 8.8% improvement. At orders 4 and 5, no merge count improves upon the byte-level baseline.

The shift in optimal merge count from order 2 to order 3 is notable: at order 3, increasing merges beyond 32 degrades bpb, even though token compression continues to improve. This indicates that the vocabulary expansion penalty begins to dominate the sequence-shortening benefit at a lower merge count when the model has more context.

### N-gram Table Size

The n-gram entry count grows with both order and merge count. Selected values from the decision record:

- Order 2, 256 merges (best): 15,371 entries
- Order 3, 32 merges (best): 23,391 entries
- Order 4, 0 merges (baseline): 34,098 entries
- Order 5, 0 merges (baseline): 89,487 entries

At higher orders, the baseline already has a large n-gram table; adding merges inflates it further without predictive payoff. The order-5 baseline alone requires 89,487 n-gram entries—more than five times the order-2 best configuration—reflecting the combinatorial explosion of higher-order contexts even at the byte level.

### Resource Usage

All runs stayed within modest memory bounds, consistent with the constraints of a micro-model experiment:

- Smoke test peak RSS: ~28,800 KiB
- Main order-5 run peak RSS: 92,808 KiB (~91 MiB)
- Order sweep peak RSS: ≤ 90,968 KiB
- Swap usage: 0 KiB throughout (swap disabled)
- MemAvailable: ≥ 122,381,748 KiB throughout
- Total wall-clock time for the main run's five variants: approximately 9.6 seconds

These figures confirm that the experiment is a lightweight prototype/smoke study, not a production-scale benchmark.

### Negative Result: Order 5 Baseline Exceeds Order 4

An incidental observation: the order-5 baseline (2.7465 bpb) is worse than the order-4 baseline (2.6379 bpb). This is consistent with n-gram overfitting at order 5 given the 200K-byte training budget—higher-order contexts are sparser, and the add-alpha smoothing model cannot compensate. This result is not surprising in itself but serves as a sanity check: it confirms that the n-gram model is operating in a regime where data sparsity, not context length, is the binding constraint at order 5.

## Limitations

1. **N-gram model, not neural.** The add-alpha n-gram model has no capacity to generalize across contexts or share statistical strength via distributed representations. A neural micro-transformer might exploit shorter sequences differently, since attention mechanisms can attend over longer ranges and share parameters across vocabulary entries. The results here bound the n-gram regime only.

2. **Single corpus.** Tiny Shakespeare is a small, domain-homogeneous English literary text. Results may not generalize to multilingual, code-mixed, or larger corpora. A corpus with more repetitive byte patterns might yield greater BPE compression, changing the trade-off.

3. **Not strictly parameter-matched.** BPE variants increase the n-gram table entry count (and thus the effective parameter count) while reducing sequence length. The comparison is not a controlled parameter-budget experiment. The bpb metric accounts for sequence length but not for model size. A fairer comparison would hold total parameter count constant across tokenization schemes.

4. **Tokenizer dictionary overhead not charged.** The BPE merge table itself occupies storage that a full compression system would need to transmit. We report bpb as predictive coding cost with a fixed learned tokenizer, not as a self-contained compression ratio. Including the merge table overhead would reduce the apparent benefit of compression-aware tokenization, particularly at high merge counts.

5. **Single train/validation split.** No cross-validation or statistical significance testing was performed. The reported bpb values are point estimates on one split. The magnitude of the observed effects (19.8%, 8.8%) is large enough that sampling noise is unlikely to reverse the direction, but the exact percentages should not be treated as precise.

6. **Order-5 degradation unexplained.** The order-5 baseline performing worse than order-4 is consistent with data sparsity but was not probed with alternative smoothing strategies (e.g., Kneser-Ney, interpolated backoff). Different smoothing might shift the order-4/5 boundary.

7. **Toy simulation scope.** This is a local viability smoke study using an n-gram microLM on a 250K-byte corpus. It is not a final claim about neural LMs, production tokenizers, or large-scale settings. The results should be interpreted as bounding the n-gram regime and motivating—not substituting for—neural micro-model experiments.

## Reproducibility Checklist

- **Code**: `scripts/compression_aware_microlm.py` — single-file Python script, no external ML dependencies beyond standard library.
- **Dataset**: Tiny Shakespeare, publicly available; local path `artifacts/data/tinyshakespeare.txt`.
- **Train/val split**: First 200,000 bytes training, next 50,000 bytes validation.
- **Hyperparameters**: N-gram orders 2–5; merge counts 0, 32, 64, 128, 256; add-alpha smoothing (fixed value as implemented in script).
- **Hardware**: Linux 6.17.0-1014-nvidia-aarch64, Python 3.12.3, swap disabled.
- **Metrics files**: `artifacts/results/smoke_metrics.json`, `artifacts/results/main_metrics.json`, `artifacts/results/order{2,3,4,5}_metrics.json`, `artifacts/results/order_sweep_summary.csv`.
- **Logs**: `artifacts/logs/smoke_20260502T104349Z.log`, `artifacts/logs/main_20260502T104355Z.log`, `artifacts/logs/order_sweep_20260502T104413Z.log`.
- **Randomness**: BPE merge selection is deterministic (greedy by token-count savings). N-gram counting is deterministic. No random seeds are involved.
- **Resource bounds**: Peak RSS ≤ 93 MiB; wall-clock ≤ 10 seconds for the full order sweep.
- **Decision record**: `.omx/project_decision.json` contains the structured decision and best-evidence summary.

## Conclusion

Compression-aware BPE tokenization improves byte-normalized validation loss for extremely context-constrained n-gram micro language models, with a 19.8% bpb reduction at order 2 and an 8.8% reduction at order 3 on Tiny Shakespeare. However, the benefit is bounded: once the n-gram model has sufficient local context (order 4–5 in this setup), the byte-level baseline is as good or better than any compression-aware variant. The token-count savings from BPE are real and substantial (up to 49% sequence shortening at 256 merges), but they do not translate into better predictive coding when the model can already exploit longer byte-level contexts.

The shift in optimal merge count—from 256 at order 2 to 32 at order 3 to 0 at orders 4–5—maps a clear boundary: compression-aware tokenization helps when sequence length is the binding constraint and hurts when vocabulary sparsity is the binding constraint. This boundary is the primary empirical contribution.

The practical implication is that compression-aware tokenization is a targeted tool, not a universal improvement. It is most likely to help in settings where the model faces an explicit context bottleneck—very short context windows, strict compute budgets, or architectures where sequence length is the binding constraint. For models with adequate context, the vocabulary expansion and context sparsity introduced by BPE merges are net negatives in this n-gram regime.

Whether these findings transfer to neural micro-models remains an open question. A neural model with shared embedding parameters and attention-based context aggregation might realize a different trade-off between sequence length and vocabulary size. We recommend equal-parameter, equal-compute neural micro-transformer experiments as the next evidence step.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Experiment script | `scripts/compression_aware_microlm.py` |
| Smoke test metrics | `artifacts/results/smoke_metrics.json` |
| Main decision metrics | `artifacts/results/main_metrics.json` |
| Order-2 metrics | `artifacts/results/order2_metrics.json` |
| Order-3 metrics | `artifacts/results/order3_metrics.json` |
| Order-4 metrics | `artifacts/results/order4_metrics.json` |
| Order-5 metrics | `artifacts/results/order5_metrics.json` |
| Order sweep summary | `artifacts/results/order_sweep_summary.csv` |
| Smoke test log | `artifacts/logs/smoke_20260502T104349Z.log` |
| Main run log | `artifacts/logs/main_20260502T104355Z.log` |
| Order sweep log | `artifacts/logs/order_sweep_20260502T104413Z.log` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T104149170776+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T104149170776+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T104149170776+0000/paper_manifest.json` |
