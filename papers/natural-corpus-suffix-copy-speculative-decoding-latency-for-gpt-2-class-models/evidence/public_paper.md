# Suffix-Copy Speculative Decoding for GPT-2-Class Models: A Bounded Mechanism Study on Wikitext-2

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by an autonomous research pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No independent human review has been performed on the code, results, or interpretation.

---

## Abstract

We evaluate a simple speculative decoding draft policy—ordered suffix-copy—that proposes candidate tokens by copying continuations following earlier occurrences of the current token suffix within the prompt and already-generated context. On GB10 hardware using Hugging Face Transformers eager inference, exact greedy decoding for `gpt2` (124M) and `distilgpt2` (82M) on Wikitext-2 prompts is accelerated by this policy versus standard KV-cache greedy decoding. Suffix-copy speculative decoding preserved exact baseline outputs on every prompt across all runs (640/640 sequences, 61,440 total tokens) and achieved 1.87× speedup for GPT-2 with minimum suffix length 2, 1.73× under a stricter minimum suffix length 4 ablation, and 2.50× for distilgpt2. Shuffled-copy controls remained within 1.006×–1.029× of baseline, indicating the speedup derives from ordered suffix matching rather than batching overhead or timing artifacts. These results support the mechanism within a narrowly bounded scope: Wikitext-2 only, two small GPT-2-class checkpoints, greedy decoding only, one hardware/software stack, and a Python implementation with non-production cache rollback via `copy.deepcopy`. The evidence does not establish whether the mechanism generalizes to broader corpora, larger models, non-greedy decoding, or production serving runtimes.

## Introduction

Speculative decoding accelerates autoregressive language model inference by proposing draft token sequences that a verifier model accepts or rejects in a single forward pass. Prior approaches have focused on training smaller draft models or using n-gram retrieval as draft sources. A simpler possibility remains largely unexplored: when a language model encounters a token suffix that has appeared earlier in the context, the model's greedy continuation may follow the earlier text, making suffix-copy a natural and zero-cost draft policy.

Natural text exhibits substantial repetition. In Wikitext-2, passages frequently contain repeated phrases, named entities, and syntactic patterns. If a model's greedy decoding tends to follow earlier continuations when the local context matches, then copying tokens from prior matching suffixes could provide high-acceptance draft sequences without any auxiliary model or retrieval index.

This study tests a narrowly scoped hypothesis: on Wikitext-2 prompts, an ordered suffix-copy speculative draft policy accelerates exact greedy decoding for GPT-2-class models compared to standard KV-cache greedy decoding, while a shuffled-copy control remains near baseline. We do not claim general applicability beyond the specific conditions tested. The project decision for this run was "finalize_negative"—the evidence constitutes a useful signal supporting the mechanism within its bounded scope, but does not meet the bar for a publication-ready broad claim.

## Method

### Implementation

We implemented `scripts/suffix_copy_spec_decode_eval.py`, a single-file evaluation harness built on Hugging Face Transformers. The implementation uses eager (non-compiled) model inference with standard KV-cache prefill and decode. This is a prototype evaluation harness, not a production serving system.

### Models

We test two GPT-2-class checkpoints: `gpt2` (124M parameters) and `distilgpt2` (82M parameters), loaded from Hugging Face Hub with default weights and no fine-tuning.

### Corpus and Prompting

We draw prompts from Wikitext-2 raw natural text, sampling from test, validation, and train splits after filtering for long passages. Each prompt consists of 192 GPT-2 BPE tokens. We generate 96 greedy tokens per prompt.

### Baseline

The baseline is standard greedy decoding with KV cache: one verifier forward pass per generated token after prefill. This is the standard autoregressive decode path in Hugging Face Transformers.

### Suffix-Copy Speculative Policy

Given the current generated context, the policy searches for an earlier occurrence of the current token suffix (the last *k* tokens, where *k* ranges between `min-suffix` and `max-suffix`). When a match is found, the policy drafts up to `max-draft` (8) following tokens from the matched position. The verifier model then evaluates the draft in a single forward pass, accepting only tokens that match its greedy argmax. On the first mismatch, the verifier emits its own greedy token and the draft is truncated. Because the verifier always emits its greedy token on rejection, the output sequence is exactly identical to standard greedy decoding.

### Shuffled-Copy Control

To distinguish the effect of ordered suffix matching from generic batching or verification overhead, we run a control condition that uses the same speculative machinery but shuffles the copied draft tokens before verification. If speedup were due to batching effects or measurement artifacts rather than meaningful draft content, the shuffled control would show comparable gains.

### Cache Rollback

On draft rejection, the KV cache must be rolled back to the state before the draft was processed. Our implementation uses Python's `copy.deepcopy` for cache rollback, which is correct but not production-efficient. This is a known limitation: the rollback cost partially offsets the speedup from accepted drafts, and a production implementation would use in-place cache truncation or ring-buffer management.

### Timing Protocol

We perform a warmup phase before measured prompts. For each prompt, the order of baseline, suffix-copy, and shuffled-copy conditions is randomized. CUDA synchronization is placed around timed decode spans. We use a fixed seed (20260516) for reproducibility.

### Run Configurations

| Configuration | Model | Prompts | Prompt tokens | Gen tokens | Max draft | Min suffix | Max suffix |
|---|---|---:|---:|---:|---:|---:|---:|
| GPT-2 min-suffix-2 | gpt2 | 256 | 192 | 96 | 8 | 2 | 16 |
| GPT-2 min-suffix-4 | gpt2 | 256 | 192 | 96 | 8 | 4 | 16 |
| distilgpt2 min-suffix-2 | distilgpt2 | 128 | 192 | 96 | 8 | 2 | 16 |

The min-suffix-4 ablation tests whether requiring longer suffix matches (and thus higher-confidence matches) changes the speedup–acceptance tradeoff.

## Results

### Aggregate Metrics

| Configuration | Prompts | Tokens generated | Exact match rate | Baseline tok/s | Suffix-copy tok/s | Control tok/s | Suffix-copy speedup | Control speedup | Acceptance rate | Mean verifier calls (suffix / baseline) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GPT-2 min-suffix-2 | 256 | 24,576 | 256/256 (100%) | 287.98 | 538.68 | 289.83 | 1.871× | 1.006× | 55.39% | 47.94 vs 97.00 |
| GPT-2 min-suffix-4 | 256 | 24,576 | 256/256 (100%) | 287.26 | 496.63 | 289.59 | 1.729× | 1.008× | 77.21% | 52.98 vs 97.00 |
| distilgpt2 min-suffix-2 | 128 | 12,288 | 128/128 (100%) | 469.12 | 1,171.79 | 482.73 | 2.498× | 1.029× | 75.48% | 34.10 vs 97.00 |

All 640 generated sequences (61,440 total tokens) exactly matched the corresponding baseline greedy output, confirming that the speculative verification path preserves output identity.

### Per-Prompt Speedup Distribution

| Configuration | Prompts where suffix-copy faster | Median per-prompt speedup | 5th percentile | 95th percentile |
|---|---:|---:|---:|---:|
| GPT-2 min-suffix-2 | 256/256 | 1.875× | 1.221× | 3.380× |
| GPT-2 min-suffix-4 | 255/256 | 1.724× | 1.114× | 3.197× |
| distilgpt2 min-suffix-2 | 128/128 | 2.774× | 1.450× | 4.238× |

Suffix-copy was faster than baseline on 639/640 prompts. The single slower prompt in the GPT-2 min-suffix-4 run indicates that the `copy.deepcopy` rollback cost can occasionally exceed the benefit when acceptance is low for a given prompt.

### Ablation: Minimum Suffix Length

Increasing the minimum suffix match length from 2 to 4 raised the per-draft acceptance rate from 55.39% to 77.21%, as longer suffix matches provide more reliable continuations. However, the aggregate speedup decreased from 1.871× to 1.729× because the stricter match requirement reduced the number of draft opportunities, increasing mean verifier calls from 47.94 to 52.98 (out of 97 baseline calls). The net effect is a speedup–coverage tradeoff: higher acceptance per draft but fewer drafts attempted. This tradeoff merits further investigation with a fuller ablation over both minimum suffix length and maximum draft length.

### Control Condition

Shuffled-copy speedups were 1.006×, 1.008×, and 1.029× across the three configurations—statistically indistinguishable from baseline. This confirms that the measured speedup in the ordered suffix-copy condition is attributable to meaningful draft content rather than batching overhead, measurement bias, or generic multi-token verification effects.

### Negative and Mixed Observations

Several findings qualify the positive speedup results:

1. **One prompt slower under suffix-copy.** In the GPT-2 min-suffix-4 configuration, one of 256 prompts was slower with suffix-copy than baseline, likely due to high rollback overhead on a prompt with few accepted drafts.

2. **Higher acceptance does not guarantee higher speedup.** The min-suffix-4 ablation achieved a higher acceptance rate (77.21% vs 55.39%) but lower aggregate speedup (1.729× vs 1.871×), because the stricter matching criterion reduced draft frequency enough to offset the per-draft quality improvement.

3. **Acceptance rate well below 100%.** Even the best acceptance rate (77.21% for GPT-2 min-suffix-4) means roughly one in four drafted tokens is rejected, incurring rollback cost. The 55.39% acceptance rate for GPT-2 min-suffix-2 means nearly half of drafted tokens are rejected, though the higher draft frequency still yields better aggregate speedup.

## Limitations

This study has substantial scope limitations that prevent generalization of the results:

1. **Single corpus.** Only Wikitext-2 was tested. Wikitext-2 is a curated encyclopedia-derived corpus with known repetitive structure. Performance on code, conversational text, scientific literature, or other domains is unknown.

2. **Two small checkpoints.** Only `gpt2` (124M) and `distilgpt2` (82M) were tested. Behavior in GPT-2-medium, GPT-2-large, or modern decoder-only architectures is untested. Larger models may exhibit different suffix-recurrence patterns and acceptance rates.

3. **Greedy decoding only.** All runs used exact greedy decoding. The mechanism's interaction with temperature sampling, top-p, top-k, or beam search was not evaluated. Speculative decoding with sampling requires draft and verifier distribution matching, which suffix-copy does not provide.

4. **Single hardware/software stack.** All measurements were taken on a single GB10 machine using Hugging Face Transformers eager inference. Results may differ substantially on GPU-serving runtimes (e.g., TensorRT-LLM, vLLM), compiled inference, or different hardware.

5. **Non-production cache rollback.** Cache rollback uses `copy.deepcopy`, which is correct but adds overhead proportional to cache size. A production implementation would use in-place cache truncation or ring-buffer management, potentially improving speedups or changing the speedup–rollback tradeoff.

6. **Limited token budget.** A total of 61,440 generated tokens across all runs provides moderate statistical power for the tested conditions but does not characterize tail behavior or rare failure modes.

7. **No long-context evaluation.** All prompts were 192 tokens with 96 generated tokens. Behavior on longer contexts (thousands of tokens) where suffix recurrence may be more or less prevalent is unknown.

8. **Incomplete ablation space.** Max draft length was fixed at 8 and max suffix length at 16. The effect of varying these parameters on speedup and acceptance was not systematically tested beyond the min-suffix ablation.

9. **Claim ledger audit blocked.** The claim ledger for this artifact contains no structured claims and its audit status is "blocked_empty_claims." The results reported here are grounded in the run notes and output files but have not passed a formal claim/evidence audit.

## Reproducibility Checklist

- **Code:** `scripts/suffix_copy_spec_decode_eval.py` (single-file evaluation harness)
- **Models:** `gpt2` and `distilgpt2` from Hugging Face Hub (default weights, no fine-tuning)
- **Corpus:** Wikitext-2 raw, sampled from test/validation/train splits after length filtering
- **Seed:** 20260516 (fixed for all primary runs)
- **Prompt length:** 192 GPT-2 BPE tokens
- **Generation length:** 96 greedy tokens per prompt
- **Max draft tokens:** 8
- **Min suffix length:** 2 (primary) and 4 (ablation)
- **Max suffix length:** 16
- **Number of prompts:** 256 (GPT-2 runs), 128 (distilgpt2 run)
- **Hardware:** GB10
- **Framework:** Hugging Face Transformers, eager inference (no compilation)
- **Timing:** CUDA synchronization around decode spans; randomized condition order per prompt; warmup before measurement
- **Output files:** `results/gpt2_wikitext_suffixcopy_primary.json`, `results/gpt2_wikitext_suffixcopy_min4_ablation.json`, `results/distilgpt2_wikitext_suffixcopy_primary.json`
- **Log files:** `logs/gpt2_wikitext_suffixcopy_primary.log`, `logs/gpt2_wikitext_suffixcopy_min4_ablation.log`, `logs/distilgpt2_wikitext_suffixcopy_primary.log`
- **Exactness verification:** Every generated sequence compared token-by-token against baseline greedy output; 640/640 matches across all runs

## Conclusion

Ordered suffix-copy speculative decoding produces substantial and consistent speedups for greedy decoding of GPT-2-class models on Wikitext-2 prompts: 1.87× for GPT-2 (min-suffix-2), 1.73× under stricter suffix matching (min-suffix-4), and 2.50× for distilgpt2. The mechanism is supported by three converging indicators: (1) 100% exact output preservation across all 640 prompts, (2) shuffled-copy controls within 1.006×–1.029× of baseline, and (3) per-prompt speedup distributions consistently above 1.0× (639/640 prompts faster).

However, this evidence establishes only a bounded mechanism result. The scope is limited to one corpus, two small checkpoints, greedy decoding, one hardware stack, and a non-production implementation. The min-suffix-4 ablation revealed that higher per-draft acceptance does not automatically translate to higher aggregate speedup, illustrating a coverage–quality tradeoff that requires further characterization. Whether suffix-copy speculative decoding provides comparable benefits under broader conditions—larger models, diverse corpora, sampling-based decoding, optimized serving runtimes, and long-context settings—remains an open question. A follow-up study with optimized cache rollback, additional corpora, and larger model checkpoints would be required to determine whether this mechanism warrants adoption in production inference systems.

## Referenced Artifacts

| Artifact | Path / Identifier |
|---|---|
| Evaluation script | `scripts/suffix_copy_spec_decode_eval.py` |
| GPT-2 primary results | `results/gpt2_wikitext_suffixcopy_primary.json` |
| GPT-2 min-suffix-4 ablation results | `results/gpt2_wikitext_suffixcopy_min4_ablation.json` |
| distilgpt2 primary results | `results/distilgpt2_wikitext_suffixcopy_primary.json` |
| GPT-2 primary log | `logs/gpt2_wikitext_suffixcopy_primary.log` |
| GPT-2 ablation log | `logs/gpt2_wikitext_suffixcopy_min4_ablation.log` |
| distilgpt2 primary log | `logs/distilgpt2_wikitext_suffixcopy_primary.log` |
| Run notes | `run_notes.md` |
| Project decision (enoch) | `.enoch/project_decision.json` |
| Project decision (omx) | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260516T140123282740+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260516T140123282740+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260516T140123282740+0000/paper_manifest.json` |
| Project ID | `source-record-redacted` |
| Run ID | `source-record-redacted-20260516T140123282740+0000` |
