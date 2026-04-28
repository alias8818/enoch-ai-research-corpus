# Tokenized Tiny-LM Duplicate Ratio Ablation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has approved this document.

---

## Abstract

We investigate whether the duplicate-ratio crowd-out signal—previously observed in a learned key/value classifier—survives the transition to tokenized autoregressive language model pretraining under a fixed token budget. We conduct two ablation stages: first a bigram causal LM trained only at the value position (a deliberately minimal prototype), and second a full-sequence tokenized causal GRU that optimizes next-token cross-entropy across all positions. In a controlled synthetic corpus of templated records (`<bos> color KEY VALUE <eos>`), we sweep five deduplication policies across five duplicate ratios (4 seeds each, 100 runs per stage). At 15× duplication, the full-sequence GRU shows saturated public/anchor evaluation across all policies (spread ≈0.001) while duplicate-heavy evaluation strongly separates policies (spread ≈0.585). Refill-based policies (cap2_rare_refill, exact_dedup_rare_refill) recover near-perfect duplicate-heavy accuracy (≥0.997), whereas no-refill policies remain near chance on crowded-out facts (0.121–0.142). Targeted crowded-fact injection on the raw 15× stream improves duplicate-heavy accuracy by ≈0.586 absolute. The kill condition for this branch is not met. These results are limited to a small GRU on a templated synthetic corpus; generalization to production-scale transformers on natural language remains untested.

## 1. Introduction

When pretraining data contains heavily duplicated documents, the effective token budget available for learning rare facts is reduced—a phenomenon we term *duplicate crowd-out*. Prior work in a parent project demonstrated this signal in a learned key/value classifier operating on structured records, but left open the question of whether the same signal persists under tokenized autoregressive language model pretraining, where the model must learn associations through sequential next-token prediction rather than direct feature–label mapping.

The central hypothesis under test is: under a fixed token/document budget, duplicate-heavy tokenized autoregressive pretraining will saturate an anchor/public evaluation slice while duplicate-heavy or rare/crowded slices still reveal policy separation at high duplicate ratios. A kill condition was pre-registered: if duplicate-heavy spread falls below 5 percentage points at high duplicate ratios *and* targeted crowded-fact injection uplifts accuracy by less than 5 points, the hypothesis would be treated as unsupported.

This report presents evidence from two experimental stages of increasing realism—a bigram value-position LM and a full-sequence causal GRU—both trained on a synthetic templated corpus with controlled duplicate ratios and deduplication policies.

## 2. Method

### 2.1 Synthetic Corpus and Policy Harness

The synthetic corpus consists of templated text records of the form `<bos> color KEY VALUE <eos>`, where KEY is drawn from a universe of 10,000 unique identifiers and VALUE is the associated fact. An anchor subset of 800 keys is designated as "public" (high-frequency) evaluation items; the remaining keys populate the "duplicate-heavy" evaluation slice.

Five deduplication policies are applied to the raw document stream before training:

1. **raw_stream**: No deduplication; duplicates pass through unchanged.
2. **exact_dedup_no_refill**: Exact duplicate removal with no replacement; the freed budget is lost.
3. **cap2_no_refill**: Each document capped at 2 occurrences; no replacement.
4. **cap2_rare_refill**: Cap at 2 occurrences; freed budget refilled with previously unseen (rare) documents.
5. **exact_dedup_rare_refill**: Exact deduplication; freed budget refilled with rare documents.

Duplicate ratios of 1×, 3×, 5×, 10×, and 15× are tested, controlling how many times anchor documents are repeated relative to unique documents.

### 2.2 Stage 1: Bigram Value-Position LM

The first pilot implements a tokenized causal bigram LM. Training optimizes next-token cross-entropy *only at the VALUE position*, making this model architecturally close to an associative key–value lookup despite being framed as autoregressive. This stage serves as a minimal proof-of-concept rather than a realistic language model.

**Parameters:** Fixed token budget; 4 seeds × 5 duplicate ratios × 5 policies = 100 runs.

### 2.3 Stage 2: Full-Sequence Causal GRU LM

The second stage implements a tokenized full-sequence causal GRU. Unlike the bigram pilot, training optimizes next-token cross-entropy across *all* positions in the sequence (`<bos> color KEY VALUE <eos>`), and evaluation predicts VALUE after conditioning on the full prefix `<bos> color KEY`. This architecture requires the model to maintain hidden state across the key portion of the sequence before generating the value, making it a more realistic (though still compact) autoregressive LM.

**Hyperparameters:** budget=12,000 documents, anchor_count=800, universe_size=10,000, epochs=30, d_model=64, hidden_size=96, batch_size=512.

**Sweep:** 4 seeds × 5 duplicate ratios × 5 policies = 100 runs. Total training tokens: 139,200,000.

### 2.4 Evaluation Metrics

- **public_eval_acc**: Accuracy on anchor/public keys (expected to saturate at high duplication regardless of policy).
- **duplicate_heavy_eval_acc**: Accuracy on duplicate-heavy keys (expected to separate policies).
- **crowded_out_acc**: Accuracy specifically on facts that were crowded out of the training set.
- **seen_coverage**: Fraction of the universe encountered during training.
- **public_spread / duplicate_heavy_spread**: Range (max − min) of the corresponding accuracy across policies, measuring policy separation.

### 2.5 Targeted Crowded-Fact Injection

As an additional diagnostic, we measure the accuracy improvement from injecting targeted crowded facts into the raw 15× stream, testing whether the observed deficit is remediable by explicit supplementation.

## 3. Results

### 3.1 Stage 1: Bigram Value-Position LM

At 15× duplication, the bigram LM showed complete public saturation (public_spread = 0.0) and modest duplicate-heavy policy separation (duplicate_heavy_spread ≈ 0.128). The 15× policy-level results were:

| Policy | duplicate_heavy_eval_acc | seen_coverage | unique_docs |
|---|---|---|---|
| raw_stream | ≈0.439 | 0.333 | 80 |
| exact_dedup_no_refill | ≈0.439 | 0.333 | 80 |
| cap2_no_refill | ≈0.439 | 0.333 | 80 |
| cap2_rare_refill | ≈0.559 | 0.483 | 1,120 |
| exact_dedup_rare_refill | ≈0.567 | 0.491 | 1,200 |

Targeted crowded-fact injection on raw 15× improved duplicate-heavy accuracy by ≈0.283 absolute, clearing the ≥5-point threshold.

The no-refill policies are indistinguishable from raw_stream in this bigram setting, and the refill policies show only moderate improvement. The bigram architecture's limited sequential conditioning likely constrains the observable policy separation.

### 3.2 Stage 2: Full-Sequence Causal GRU LM

At 15× duplication, the full-sequence GRU showed near-complete public saturation (public_spread ≈ 0.001) and strong duplicate-heavy policy separation (duplicate_heavy_spread ≈ 0.585). The 15× policy-level results were:

| Policy | duplicate_heavy_eval_acc | crowded_out_acc | seen_coverage | unique_docs |
|---|---|---|---|---|
| raw_stream | ≈0.414 | ≈0.121 | 0.333 | 800 |
| cap2_no_refill | ≈0.419 | ≈0.129 | 0.333 | 800 |
| exact_dedup_no_refill | ≈0.428 | ≈0.142 | 0.333 | 800 |
| cap2_rare_refill | ≈0.997 | ≈0.995 | 1.000 | 10,000 |
| exact_dedup_rare_refill | ≈0.999 | ≈0.999 | 1.000 | 10,000 |

Key observations:

1. **No-refill policies are near chance on crowded-out facts** (0.121–0.142), confirming that the model fails to learn facts it never encounters.
2. **Refill policies achieve near-perfect accuracy** (≥0.997 on both duplicate-heavy and crowded-out metrics), demonstrating that replacing duplicate tokens with rare documents fully recovers learning.
3. **Public evaluation is saturated across all policies** (spread ≈ 0.001), confirming that high-frequency anchor facts are learned regardless of deduplication policy.
4. **Targeted crowded-fact injection on raw 15× improved duplicate-heavy accuracy by ≈0.586 absolute**, well above the 5-point pre-registered threshold.

The kill condition (duplicate-heavy spread < 0.05 *and* injection uplift < 0.05) is not met at either stage.

### 3.3 Computational Telemetry

**Stage 1 (bigram LM):** Wall-clock ≈17.3 s; total tokens ≈516,800; throughput ≈29,822 tokens/s including evaluation; CUDA max allocated ≈703 MB; device: NVIDIA GB10, PyTorch 2.11.0+cu130.

**Stage 2 (GRU LM):** Wall-clock ≈424 s; total tokens ≈139.2 M; throughput ≈328k tokens/s including evaluation; CUDA max allocated ≈386 MB; GPU utilization ≈95%, temperature ≈67°C, power ≈42.7 W; device: NVIDIA GB10, PyTorch 2.11.0+cu130.

## 4. Limitations

1. **Synthetic templated corpus.** All experiments use records of the form `<bos> color KEY VALUE <eos>`. Natural language exhibits far richer structure, longer-range dependencies, and more diverse duplication patterns. Whether the crowd-out signal generalizes to natural-language pretraining remains untested.

2. **Small model scale.** The GRU LM uses d_model=64, hidden_size=96—orders of magnitude below production language models. The model has sufficient capacity to memorize the full universe when all documents are seen (as demonstrated by refill policies reaching ≈1.0 accuracy), but the dynamics of capacity-constrained learning at scale may differ.

3. **Bigram pilot is near-associative.** The Stage 1 bigram LM, while tokenized and autoregressive in framing, optimizes only the value position and is architecturally close to a key/value lookup. Its results are included for completeness but should not be treated as realistic language-model evidence.

4. **Single hardware configuration.** All runs were executed on a single NVIDIA GB10. No cross-platform or multi-GPU validation was performed.

5. **No comparison to production deduplication pipelines.** The five policies tested are simplified abstractions. Real-world deduplication involves fuzzy matching, near-duplicate detection, and quality-based filtering that may interact with the crowd-out signal in ways not captured here.

6. **Fixed hyperparameters.** The sweep varies only duplicate ratio, policy, and seed. Learning rate, model depth, sequence length, and other hyperparameters are held fixed. Their interaction with the crowd-out signal is unknown.

7. **No natural-language or benchmark evaluation.** Downstream task performance (e.g., perplexity on held-out text, question answering, or factual recall benchmarks) was not measured.

## 5. Reproducibility Checklist

- **Code availability:** Training and evaluation scripts are present in the project directory:
  - `scripts/full_sequence_tiny_lm_duplicate_ablation.py` (Stage 2)
  - `scripts/tokenized_tiny_lm_duplicate_ablation.py` (Stage 1)
  - `scripts/duplicate_pretrain_ablation.py` (shared corpus/policy harness)
- **Result data:** Per-run metrics CSVs and summary JSONs are persisted for both stages (see Referenced Artifacts).
- **Random seeds:** 4 seeds per condition; seeds are recorded in per_run_metrics.csv.
- **Hyperparameters:** All stated in Section 2.3 (Stage 2) and implicit in Stage 1 run artifacts.
- **Hardware:** NVIDIA GB10, PyTorch 2.11.0+cu130, CUDA 13.0.
- **Verification:** `python -m py_compile` passes for all three scripts; per_run_metrics.csv contains 100 data rows plus header for each stage; summary.json reports `kill_condition_met=false` and `supported_signal=true`.
- **Pre-registered kill condition:** Stated in run_notes.md; evaluated against observed data; not met.

## 6. Conclusion

Under a fixed token budget on a synthetic templated corpus, the duplicate crowd-out signal persists through the transition from a learned key/value classifier to a tokenized autoregressive language model. In a full-sequence causal GRU trained on 139.2 M tokens, high duplication (15×) saturates public/anchor evaluation across all policies while producing strong policy separation on duplicate-heavy facts (spread ≈0.585). Refill-based deduplication policies recover near-perfect accuracy on crowded-out facts; no-refill policies leave crowded-out facts near chance. Targeted injection of crowded facts into the raw stream produces a 0.586 absolute accuracy improvement, confirming that the deficit is attributable to missing exposure rather than capacity or optimization failure.

These findings are bounded by the synthetic corpus, small model scale, and single-hardware configuration. The pre-registered kill condition for this branch was not met, and the project decision is to finalize positive. Whether the same crowd-out dynamics hold for production-scale transformers on natural-language data with realistic deduplication pipelines remains an open question.

---

## Referenced Artifacts

### Result files
- `results/full_sequence_tiny_lm_duplicate_ablation/summary.json`
- `results/full_sequence_tiny_lm_duplicate_ablation/run.log`
- `results/full_sequence_tiny_lm_duplicate_ablation/per_run_metrics.csv`
- `results/full_sequence_tiny_lm_duplicate_ablation_debug/summary.json`
- `results/full_sequence_tiny_lm_duplicate_ablation_debug/per_run_metrics.csv`
- `results/tokenized_tiny_lm_duplicate_ablation/summary.json`
- `results/tokenized_tiny_lm_duplicate_ablation/per_run_metrics.csv`
- `results/tokenized_tiny_lm_duplicate_ablation_smoke/summary.json`
- `results/tokenized_tiny_lm_duplicate_ablation_smoke/per_run_metrics.csv`

### Source scripts
- `scripts/full_sequence_tiny_lm_duplicate_ablation.py`
- `scripts/tokenized_tiny_lm_duplicate_ablation.py`
- `scripts/duplicate_pretrain_ablation.py`

### Decision and metadata
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `run_notes.md`
- `prompts/initial.md`
- `prompts/resume.md`

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
