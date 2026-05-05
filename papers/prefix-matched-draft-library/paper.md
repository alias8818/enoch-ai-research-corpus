# Prefix-Matched Draft Libraries as Model-Free Speculative Decoding Proposers

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated its claims.

---

## Abstract

Speculative decoding accelerates autoregressive language model inference by proposing draft tokens that a target model verifies in parallel. Existing draft proposers typically require a smaller draft model or a trained draft network. We investigate a model-free alternative: a prefix-matched draft library that maps recent token prefixes to previously observed continuation tokens, proposing drafts via exact prefix lookup. In an algorithmic token-stream simulation across extractive-copy, repetitive-synthetic, and generic-prose workloads, we find that prefix-matched drafting achieves up to 13.7× ideal iteration speedup (9.9× net speedup under a 3%-per-draft-token verifier overhead model) on input-grounded extractive tasks, and 3.9× ideal iteration speedup (2.8× net) on deterministic repetitive text. However, for generic prose continuation—whether using a private prompt prefix or a public cross-document library—the method yields at most 1.07× ideal speedup, falling below 1.0× net speedup under plausible verification overhead. These results support prefix-matched draft libraries as a workload-gated accelerator suitable for extractive, template-driven, or repetitive generation, but not as a general-purpose speculative proposer for unrelated prose.

## Introduction

Speculative decoding reduces the latency of autoregressive inference by having a proposer generate candidate tokens that a target model then verifies in a single forward pass, accepting a contiguous prefix of correct tokens and resampling from the rejection distribution at the first mismatch. The accepted token count per iteration replaces the single-token emission of standard autoregressive decoding, yielding speedups proportional to the mean accepted draft length.

Most speculative decoding methods employ a smaller draft model as proposer, incurring the cost of maintaining and running a second model. N-gram-based and model-free proposers offer an alternative: they require no additional model weights and can exploit statistical regularities in the token stream. A natural instance of this idea is a prefix-matched draft library—a lookup structure that, given the most recent *k* tokens, proposes the *v*-token continuation most frequently (or most recently) observed following that prefix in some reference corpus.

The appeal is straightforward: when the desired output repeats text already present in the prompt or session—extractive question answering, code patch echoing, structured template filling, tool-output reproduction—the prefix library should draft nearly the correct continuation once the decoder has produced enough tokens to match a source span. The question is whether this advantage extends to generic open-ended generation, and at what cost in verification overhead when drafts are frequently rejected.

We implement and evaluate a prefix-matched draft library across three workload categories: (1) extractive copying from a source document present in the prompt, (2) deterministic repetitive synthetic text, and (3) generic prose continuation under both private-prompt and public cross-document library configurations. We report ideal iteration speedup and a sensitivity-adjusted net speedup under a verifier-overhead model, and we identify the workload boundary beyond which the method ceases to be beneficial.

## Method

### Prefix-Matched Draft Library Construction

The draft library is a map from *k*-token prefix keys to *v*-token continuation values. Given a tokenized reference corpus, the construction process scans all (*k* + *v*)-length windows, inserting or updating the entry for each prefix key. When a prefix key maps to multiple distinct continuations (because the same prefix appears in different contexts), a retention policy selects which continuation to store. We evaluate two policies:

- **Oldest:** Retain the first continuation observed for each prefix, emulating a first-come-first-served cache.
- **Majority:** Retain the continuation most frequently associated with each prefix, emulating a frequency-based cache.

### Draft Proposal and Verification Simulation

At each decoding step, the proposer examines the most recent *k* tokens emitted by the target. If the prefix key exists in the library, the stored *v*-token continuation is proposed as the draft. The target model is then simulated to verify the draft against the known ground-truth output stream: tokens are accepted sequentially until the first mismatch, at which point the draft is truncated and the iteration completes. If the prefix key is absent, no draft is proposed and the iteration emits a single token (matching the baseline).

The simulation follows the accepted-length convention used in n-gram speculative decoding evaluations: each baseline iteration emits one token, while each speculative iteration emits 1 + (number of accepted draft tokens). The ideal iteration speedup is the ratio of baseline iterations to speculative iterations required to produce the same output.

### Verifier Overhead Model

Speculative decoding incurs verification cost proportional to the draft length. We model net speedup as:

$$S_{\text{net}} = \frac{S_{\text{ideal}}}{1 + \alpha \cdot \bar{v}}$$

where $S_{\text{ideal}}$ is the ideal iteration speedup, $\bar{v}$ is the mean proposed draft length (including zero-length proposals on misses), and $\alpha$ is the fractional verifier overhead per draft token. We report results at $\alpha = 0.03$ (3% overhead per draft token) as a representative value. This model is intentionally simple; real overhead depends on hardware, batch size, and serving-engine implementation.

### Tokenization

The evaluator uses a regex-based word-and-punctuation tokenizer with no subword merging. This choice avoids external dependencies but means that exact numerical speedups will shift under production tokenizers such as BPE or SentencePiece, which produce different vocabulary sizes and prefix distributions.

### Workloads

1. **Gutenberg extractive-copy:** The target output is a span of text copied verbatim from a source document included in the prompt. The draft library is built from the same source document (private library scope). This workload models extractive QA, quote retrieval, and document-grounded summarization.

2. **Synthetic repetitive:** A deterministic synthetic corpus with repeated structural patterns. The draft library is built from the prompt prefix (private scope). This workload models templated output, structured data formatting, and code generation with recurring patterns.

3. **Gutenberg generic continuation (private):** The target output is a continuation of a Gutenberg text, with the draft library built from the preceding prompt tokens only. This workload tests whether intra-document prefix reuse helps open-ended prose.

4. **Gutenberg generic continuation (public cross-document):** The draft library is built from a pool of other Gutenberg documents (train set), and evaluated on held-out documents. This workload tests cross-document generalization of prefix matches.

### Implementation

The evaluator (`scripts/prefix_draft_library_eval.py`) is a standalone Python script with no non-stdlib dependencies. It downloads five Project Gutenberg texts into `data/gutenberg/` and generates a small deterministic repetitive synthetic corpus. Configuration sweeps over prefix length *k* ∈ {2, 3, 5}, draft length *v* ∈ {3, 5, 13}, and retention policy (oldest, majority).

**Important scope note:** This is an algorithmic token-stream simulation. It is not a llama.cpp hook-prototype, not a CUDA copy calibration, and not a production serving-engine benchmark. The simulation verifies drafts against a known ground-truth output stream rather than against a live target model. Real latency speedup requires integration into a serving engine with actual model forward passes.

## Results

### Extractive-Copy Workload

The extractive-copy workload yielded the strongest results. With a private source-prompt library, *k* = 5, *v* = 13, and the oldest retention policy, the hit rate reached 0.986, with a mean of 12.71 accepted draft tokens per speculative iteration. The ideal iteration speedup was 13.71×, and the net speedup under 3% verifier overhead was 9.86×.

This result is consistent with the hypothesis: once the decoder has produced a 5-token prefix that matches a span in the source document, the library almost always proposes the correct continuation, and nearly all 13 draft tokens are accepted.

### Synthetic Repetitive Workload

The repetitive synthetic workload showed moderate but meaningful gains. With *k* = 2, *v* = 13, and the oldest policy, the hit rate was 0.560, with a mean of 2.88 accepted draft tokens. The ideal iteration speedup was 3.88×, and the net speedup was 2.79×.

The lower hit rate reflects the fact that short prefixes in repetitive text are ambiguous—multiple distinct continuations may share the same 2-token prefix—but the majority of proposed drafts still contribute accepted tokens, yielding a net benefit.

### Generic Prose Continuation Workloads

Both generic prose workloads showed negligible or negative net speedup.

**Private prompt prefix library** (*k* = 2, *v* = 3, majority): ideal speedup 1.07×, net speedup 0.98×, mean accepted draft tokens 0.074.

**Public cross-document library** (*k* = 2, *v* = 3, majority): ideal speedup 1.06×, net speedup 0.97×, mean accepted draft tokens 0.063.

In both cases, the hit rate was below 0.56, and the mean accepted draft length was near zero—most proposed drafts were rejected at the first token. The small ideal speedup is overwhelmed by verification overhead, producing net slowdown.

### Effect of Draft Length *v*

Larger *v* improves speedup only when acceptance is high. In the extractive-copy workload, *v* = 13 substantially outperformed *v* = 3 or *v* = 5. In the generic prose workloads, larger *v* hurt net speedup because verification cost grows with *v* while accepted length remains near zero. This asymmetry implies that *v* should be bounded and tuned from live acceptance telemetry rather than set to a fixed large value.

### Effect of Retention Policy

The oldest retention policy outperformed majority in the extractive-copy and repetitive workloads, likely because the first occurrence of a prefix in a coherent document tends to be followed by the same continuation that the target will produce. The majority policy performed better in the generic prose workloads, though the difference was immaterial given the near-zero accepted draft lengths.

### Summary Table

| Workload | Library scope | Best config | Ideal speedup | Net speedup (α=0.03) | Hit rate | Mean accepted tokens |
|---|---|---|---:|---:|---:|---:|
| Gutenberg extractive-copy | Private source prompt | k=5, v=13, oldest | 13.71× | 9.86× | 0.986 | 12.71 |
| Synthetic repetitive | Private prompt prefix | k=2, v=13, oldest | 3.88× | 2.79× | 0.560 | 2.88 |
| Gutenberg generic (private) | Private prompt prefix | k=2, v=3, majority | 1.07× | 0.98× | 0.466 | 0.07 |
| Gutenberg generic (public) | Public cross-document | k=2, v=3, majority | 1.06× | 0.97× | 0.557 | 0.06 |

## Limitations

1. **Algorithmic simulation, not serving-engine integration.** These results are from a token-stream simulation, not from an integrated GPU LLM serving benchmark. Real latency speedup depends on batch scheduling, memory bandwidth, kernel implementation, and the interaction between draft verification and the target model's forward pass. The verifier-overhead model used here is a linear sensitivity parameter, not a measured quantity.

2. **Non-production tokenizer.** The regex word-and-punctuation tokenizer produces different prefix distributions than BPE or SentencePiece tokenizers used in production LLMs. Subword tokenizers typically have larger vocabularies and shorter token sequences for the same text, which may reduce prefix-match hit rates (more distinct prefixes) or increase them (shorter, more repetitive subword patterns). The numerical speedup values reported here should not be taken as predictions of production performance.

3. **Small corpus scale.** The evaluation uses five Project Gutenberg texts and a small synthetic corpus. Scaling to larger libraries introduces memory and lookup-cost concerns not modeled here. Hash-table lookup is O(1) in expectation, but cache behavior and memory footprint at billion-prefix scale remain untested.

4. **Deterministic ground-truth verification.** The simulation verifies drafts against a known output stream, which assumes the target model would produce exactly that output. In practice, the target model's distribution may differ from the reference corpus, and accepted tokens must be resampled from the target's conditional distribution at the rejection point. This simulation elides that resampling cost and distributional mismatch.

5. **Single verifier-overhead parameter.** The 3% per-draft-token overhead is illustrative. Actual overhead varies with hardware, model size, batch size, and whether verification is done via a single forward pass over the draft or token-by-token. The net speedup values are sensitive to this parameter; the qualitative conclusion (positive for extractive, negative for generic prose) is robust across a range of plausible α values, but the crossover point is workload-dependent.

6. **No comparison to model-based drafters.** This study does not compare prefix-matched drafting against small-model or n-gram speculative decoding baselines. The relevant question for deployment is whether a prefix library adds value on top of (or as a fallback for) existing draft proposers, which requires integration-level experimentation.

7. **Claim audit status.** The claim ledger for this artifact recorded no structured claims and an audit status of "blocked_empty_claims." The results presented here are drawn directly from the recorded metrics and run notes but have not passed a formal claim-evidence audit.

## Reproducibility Checklist

- [x] **Source code available:** `scripts/prefix_draft_library_eval.py` (standalone Python, no non-stdlib dependencies)
- [x] **Command log preserved:** `results/logs/prefix_draft_eval.log`
- [x] **Full metrics output:** `results/prefix_draft_eval/metrics.json`
- [x] **Key metrics extracted:** `results/prefix_draft_eval/key_metrics.json`, `results/prefix_draft_eval/key_metrics.csv`
- [x] **Human-readable summary:** `results/prefix_draft_eval/summary.md`
- [x] **Source reference notes:** `results/prefix_draft_eval/source_refs.md`
- [x] **Project decision recorded:** `.omx/project_decision.json`
- [x] **Corpus acquisition specified:** Five Project Gutenberg texts downloaded by the script; synthetic corpus generated deterministically in-code
- [x] **Determinism:** Synthetic corpus and evaluation are deterministic (no random seed required)
- [x] **Configuration sweep documented:** *k* ∈ {2, 3, 5}, *v* ∈ {3, 5, 13}, retention ∈ {oldest, majority}
- [ ] **Production serving-engine integration:** Not performed; identified as follow-on work
- [ ] **Production tokenizer evaluation:** Not performed; identified as limitation
- [ ] **Formal claim-evidence audit:** Not passed; claim ledger recorded blocked_empty_claims status

## Conclusion

Prefix-matched draft libraries are a viable model-free speculative decoding proposer for workloads where the desired output repeats or closely follows text already present in the prompt or session. In extractive-copy settings, the method achieves near-perfect hit rates and substantial iteration speedup (13.7× ideal, 9.9× net under 3% verifier overhead). In repetitive structured text, moderate speedup (3.9× ideal, 2.8× net) is achievable. However, for generic prose continuation—whether using a private prompt-prefix library or a public cross-document library—the method does not overcome verification overhead, producing net slowdown.

The practical implication is that prefix-matched draft libraries should be deployed as a workload-gated mechanism: auto-enabled when live acceptance telemetry indicates mean accepted draft length above a threshold (e.g., > 1.0), and disabled otherwise. Recommended starting parameters are *k* ∈ {3, 5} with *v* capped in the range 5–13, tuned from observed acceptance rates. The method should not be pursued as an always-on generic speculative proposer for unrelated prose.

The recommended next step is integration into a production serving engine with live acceptance telemetry, enabling measurement of real latency speedup and interaction with existing draft-proposing mechanisms.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Evaluation script | `scripts/prefix_draft_library_eval.py` |
| Command log | `results/logs/prefix_draft_eval.log` |
| Full metrics | `results/prefix_draft_eval/metrics.json` |
| Key metrics (JSON) | `results/prefix_draft_eval/key_metrics.json` |
| Key metrics (CSV) | `results/prefix_draft_eval/key_metrics.csv` |
| Human summary | `results/prefix_draft_eval/summary.md` |
| Source references | `results/prefix_draft_eval/source_refs.md` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260429T134456125737+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T134456125737+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T134456125737+0000/paper_manifest.json` |
