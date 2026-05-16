# Context-Derived N-Gram Trie Speculative Decoding

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, benchmark outputs, decision records). The operator who released this artifact claims no personal authorship credit for the writing or experimental results. Readers should treat this document as an unreviewed AI-generated research artifact and evaluate its claims accordingly.

---

## Abstract

Speculative decoding accelerates autoregressive language model inference by drafting candidate token sequences and verifying them in a single forward pass, but conventional approaches require a separate neural draft model that consumes additional GPU VRAM—a binding constraint for local and consumer-hardware deployments. We investigate replacing the neural draft model with a lightweight n-gram trie constructed dynamically from the already-seen context window. The trie exploits local repetition in structured domains (code, documentation) to propose continuations at negligible memory cost. In proxy benchmarks—a continuation-oracle matching test and greedy verification against distilgpt2—the context-derived trie achieves mean accepted draft lengths of 2.0–2.4 tokens per step on local Python stdlib and system documentation corpora, with first-token acceptance rates of 0.43–0.48. A synthetic repetition control confirms the mechanism recovers repeated continuations perfectly (8.0 accepted tokens/step, 1.0 acceptance rate). However, these results are proxy-only: they do not measure end-to-end wall-clock speedup, GPU utilization, KV-cache costs, or output equivalence under production speculative sampling. A tiny-GPT-2 stress test produced zero acceptance even on the synthetic control, an unexplained anomaly that tempers confidence in the generality of the approach. We report the proxy evidence honestly, document its limitations, and specify the additional evidence required to validate the approach.

## Introduction

Speculative decoding reduces the latency of autoregressive generation by proposing short token sequences (drafts) that a target model verifies in a single batched forward pass. When the target accepts draft tokens, multiple positions advance per forward call, amortizing the per-token cost of the verifier. The technique's effectiveness depends on two factors: the acceptance rate of drafted tokens and the cost of producing drafts.

Standard speculative decoding uses a smaller neural network as the draft model. This draft model must be loaded alongside the target, consuming VRAM that could otherwise support longer contexts or larger targets. For deployments on consumer GPUs where VRAM is the primary constraint, the draft model's memory footprint can make speculative decoding infeasible even when it would improve throughput.

We investigate an alternative: constructing an n-gram trie over the tokens already present in the context window and using it as the draft mechanism. The key observation is that many generation workloads—particularly code completion, documentation generation, and other structured text—exhibit strong local repetition. Function signatures, import blocks, boilerplate patterns, and repeated API calls all create n-gram continuations that a trie can recover exactly, without any neural computation or additional model weights.

This approach offers several potential advantages:

- **Zero draft-model VRAM.** The trie occupies main memory (RAM), not GPU VRAM, leaving the full GPU memory budget for the target model and KV cache.
- **Negligible draft latency.** Trie lookups are O(1) per token, orders of magnitude faster than a neural forward pass.
- **Dynamic adaptation.** The trie is rebuilt or updated from the current context, so it automatically captures domain-specific repetition without fine-tuning.

The central question is whether the acceptance rates achievable with n-gram trie drafts are sufficient to yield net speedup in a real speculative decoding loop, given that verification overhead and rejection costs partially offset gains from accepted tokens. This paper reports proxy evidence bearing on that question and honestly characterizes what remains unknown.

## Method

### N-Gram Trie Construction

Given a context window of tokens $c_1, c_2, \ldots, c_T$, we construct a suffix trie recording all n-gram continuations observed in the context for $n$ up to a maximum order $N$ (default $N = 8$). For each unique $(n-1)$-gram prefix $(c_{i-n+2}, \ldots, c_i)$, the trie stores the set of observed continuation tokens $c_{i+1}$ and their frequencies.

### Draft Generation

At generation step $t$, the draft procedure:

1. Identifies the longest suffix of the current context $(c_{t-k+1}, \ldots, c_t)$ that matches a prefix in the trie, for $k$ up to $N-1$.
2. Selects the most frequent continuation token from the matched trie node.
3. Appends the selected token to the draft and advances the trie walk to the child node.
4. Repeats steps 2–3 until reaching a maximum draft length $D$ (default $D = 8$), a trie leaf, or a node with no children.

The draft is then submitted to the target model for verification.

### Trie Update

After each verification step, accepted tokens are appended to the context and the trie is updated incrementally in O(1) per new token by inserting the new n-gram entries.

### Benchmark Design

Because integrating the trie into a production speculative decoding loop requires non-trivial engineering (KV-cache management, batched verification, speculative sampling), we evaluated the approach through two proxy benchmarks that isolate the draft quality question from the systems-level integration question. These are explicitly not end-to-end speculative decoding measurements.

**Continuation-oracle proxy.** This benchmark builds the trie from a context window of observed text, then drafts tokens and compares them against the held-out continuation of the same text. This measures an upper bound on acceptance: if the trie's draft matches what was actually written, any target model that would have produced the same text would accept the draft. It does not account for the target model's actual token distribution. This benchmark is a toy simulation—it involves no neural model at all.

**Greedy target-model proxy.** This benchmark builds the trie from the same context, drafts tokens, then checks each drafted token against the target model's greedy next-token prediction given the prefix plus all previously accepted draft tokens. This provides a more realistic acceptance estimate, though it still uses greedy decoding rather than the sampling-based acceptance criterion of full speculative decoding. This benchmark is a hook-prototype-level evaluation—it uses a real model (distilgpt2) but in a simplified, non-production setting on CPU.

Both benchmarks use local corpora (Python stdlib source files, system documentation pages, and a synthetic repetition control) to avoid network dependence.

### Tokenizers Tested

We evaluated with two tokenizers: a simple regex-based word-level tokenizer and the GPT-2 BPE tokenizer, to assess sensitivity to tokenization granularity. The primary reported results use GPT-2 tokenization; the regex-tokenizer results are available in the referenced artifacts.

### Corpora

Three corpora were used:

- **local_python_stdlib:** Python standard library source files from the host system.
- **local_system_docs:** System documentation pages from the host system.
- **synthetic_repetition_control:** Deliberately constructed text with exact repetition, serving as a positive control to verify the trie mechanism works when repetition is present.

## Results

### Continuation-Oracle Proxy (GPT-2 Tokenization)

| Corpus | Docs | Mean Accepted Tokens/Step | First-Token Accept Rate | Draft Precision | Ideal Tokens/Target Call |
|---|---:|---:|---:|---:|---:|
| Python stdlib | 30 | 2.014 | 0.481 | 0.305 | 3.014 |
| System docs | 30 | 2.055 | 0.445 | 0.317 | 3.055 |
| Synthetic repetition | 2 | 8.000 | 1.000 | 1.000 | 9.000 |

The "ideal tokens/target call" column represents the total tokens advanced per verification forward pass (accepted draft tokens plus one verified token), assuming all draft tokens are verified in a single batch.

On real corpora, the trie achieves approximately 2.0 accepted tokens per drafting step, with first-token acceptance rates near 0.45–0.48. Draft precision (fraction of drafted tokens that match the continuation) is approximately 0.30–0.32, reflecting that many drafts are partially correct before diverging.

The synthetic repetition control confirms the mechanism works as intended: on text constructed with deliberate repetition, the trie recovers continuations perfectly.

### Greedy Target-Model Proxy (distilgpt2)

| Corpus | Docs | Positions | Mean Accepted Tokens/Step | First-Token Accept Rate | Draft Precision | Ideal Tokens/Target Call |
|---|---:|---:|---:|---:|---:|---:|
| Python stdlib | 10 | 320 | 2.263 | 0.444 | 0.392 | 3.263 |
| System docs | 10 | 320 | 2.384 | 0.428 | 0.450 | 3.384 |
| Synthetic repetition | 2 | 64 | 8.000 | 1.000 | 1.000 | 9.000 |

Against distilgpt2's greedy decoding, acceptance rates are comparable to the continuation oracle, with mean accepted tokens per step of 2.26–2.38 and first-token acceptance of 0.43–0.44. Draft precision is modestly higher (0.39–0.45), suggesting that the target model's greedy distribution partially aligns with the trie's frequency-based selection.

### Tiny-GPT-2 Stress Test

The tiny-GPT-2 greedy benchmark accepted zero tokens across all corpora, including the synthetic repetition control. Because distilgpt2 accepted the synthetic control perfectly and accepted non-trivial numbers of draft tokens on real corpora, we interpret the tiny-GPT-2 result as a pathology of that particular model configuration (likely related to its very limited capacity and idiosyncratic token distributions) rather than as evidence against the trie drafting mechanism itself. This interpretation should be treated with caution: it rests on a single alternative model rather than a systematic ablation, and the zero-acceptance result on the synthetic control—which the trie should match exactly—remains unexplained.

### Regex Tokenizer Results

The continuation-oracle benchmark was also run with a regex word-level tokenizer. The raw metrics are available in the referenced artifacts (`results/local_regex_metrics.json`). The regex tokenizer results are not reported in the main tables because the GPT-2 tokenizer is more representative of production tokenization, but the artifacts are included for completeness.

### Summary of Proxy Evidence

The proxy benchmarks provide moderate evidence that context-derived n-gram tries can produce drafts with non-trivial acceptance rates on structured, repetitive corpora. Mean accepted draft lengths of 2.0–2.4 tokens per step, if sustained in a real speculative decoding loop, could yield throughput improvements. However, these results are proxy-only and do not constitute validation of the approach in a production setting. The tiny-GPT-2 anomaly further tempers confidence in the generality of the mechanism across model architectures.

## Limitations

This work has substantial limitations that must be stated clearly.

**Proxy-only evaluation.** Neither benchmark measures end-to-end wall-clock speedup. The continuation-oracle proxy measures an upper bound on acceptance that may not be achievable by any real target model. The greedy target-model proxy uses distilgpt2, a small model with limited representativeness, and evaluates greedy acceptance rather than the sampling-based acceptance criterion used in production speculative decoding. Neither benchmark accounts for:

- Wall-clock latency of trie construction, lookup, and update in a serving loop
- GPU utilization and kernel overhead for batched verification
- KV-cache management costs when accepting variable-length drafts
- The effect of speculative sampling (non-greedy acceptance) on acceptance rates
- Output equivalence and quality preservation versus non-speculative decoding

**Corpus representativeness.** The benchmarks use local Python stdlib files and system documentation—domains with high local repetition. Acceptance rates on more diverse or creative text (narrative, conversation, reasoning) are unknown and may be substantially lower. The original hypothesis specified ≥50% first-token acceptance on code tasks; the observed rates of 0.43–0.48 fall short of this threshold.

**Small model target.** Distilgpt2 is not a representative target for the use case motivating this work (large models on consumer GPUs). Acceptance rates may differ significantly with larger, more capable target models whose distributions are less aligned with simple frequency-based drafting.

**Tokenization sensitivity.** Results are reported for two tokenizers, but the interaction between tokenization granularity and trie effectiveness is not fully characterized. Subword tokenizers like GPT-2 BPE may fragment repeated patterns across token boundaries, reducing trie hit rates compared to word-level or character-level tokenization.

**Tiny-GPT-2 anomaly.** The zero-acceptance result with tiny-GPT-2, including on the synthetic control, is unexplained and raises questions about the generality of the approach across model architectures and sizes. Our interpretation of this as a model pathology is plausible but not rigorously established. A single counter-model is insufficient to either confirm or dismiss the anomaly.

**No memory profiling.** The hypothesis specified trie RAM < 100 MB. We did not measure actual trie memory consumption in these benchmarks. The trie's memory footprint depends on context length, vocabulary size, and n-gram order, and may exceed 100 MB on very long contexts.

**No hybrid evaluation.** The approach may be most effective as a complement to neural drafting (e.g., using the trie when it has high-confidence continuations and falling back to a neural draft otherwise). We did not evaluate hybrid strategies.

**No production validation.** No CUDA copy calibration or final production validation has been performed. All results are from toy simulation (continuation oracle) and hook-prototype (greedy target model) benchmarks running on CPU.

## Reproducibility Checklist

- **Code availability:** Benchmark scripts are located at `scripts/context_ngram_trie_benchmark.py` and `scripts/target_greedy_acceptance.py` within the project directory.
- **Command-line invocations:** All commands used to produce the reported results are documented in the run notes and reproduced in the Method section of this paper.
- **Input data:** Benchmarks use local Python stdlib files, system documentation, and synthetic repetition controls. No external data download is required. Corpus composition depends on the host system's installed Python stdlib and documentation.
- **Output artifacts:** Raw metric files are at `results/local_regex_metrics.json`, `results/local_gpt2_metrics.json`, `results/tiny_gpt2_greedy_acceptance.json`, and `results/distilgpt2_greedy_acceptance_wide.json`.
- **Randomness:** The synthetic repetition control is deterministic. Local corpus selection depends on the host system's installed Python stdlib and documentation. Results may vary across systems.
- **Hardware:** Benchmarks ran on CPU (machine target: gb10). No GPU was used for these proxy evaluations.
- **Model versions:** distilgpt2 (HuggingFace default), sshleifer/tiny-gpt2 (HuggingFace default).
- **Decision artifacts:** `.enoch/project_decision.json` and `.omx/project_decision.json` record the decision to continue with medium confidence and moderate evidence strength.
- **Evidence level classification:** Continuation-oracle benchmarks are toy simulations (no neural model). Greedy target-model benchmarks are hook-prototype evaluations (real model, simplified setting, CPU only). No CUDA copy calibration or final production validation has been performed.

## Conclusion

We have presented and evaluated a context-derived n-gram trie as a zero-VRAM draft mechanism for speculative decoding. Proxy benchmarks on structured, repetitive corpora show mean accepted draft lengths of 2.0–2.4 tokens per step against both a continuation oracle and distilgpt2's greedy decoding, with first-token acceptance rates of 0.43–0.48. A synthetic repetition control confirms the mechanism recovers repeated continuations exactly. However, a tiny-GPT-2 stress test produced zero acceptance even on the synthetic control, an unexplained anomaly that limits confidence in the mechanism's generality.

These results provide moderate evidence that the approach is viable on repetitive domains, but they are insufficient to conclude that the method achieves net wall-clock speedup in production use. The observed first-token acceptance rates fall below the originally hypothesized 50% threshold for code tasks, and the proxy benchmarks do not measure the systems-level costs (verification overhead, KV-cache management, GPU utilization) that determine whether accepted draft tokens translate to throughput improvement.

The honest assessment is that the core mechanism—context-derived n-gram trie drafting—shows enough promise to warrant further investigation but has not yet been validated in the setting where it would need to deliver value: an optimized speculative decoding loop with a meaningful target model, measuring wall-clock tokens per second, acceptance length distributions, memory consumption, and output equivalence against non-speculative decoding. The unexplained tiny-GPT-2 anomaly further underscores the need for evaluation across a broader range of model architectures and sizes before practical claims can be made.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Continuation-oracle metrics (regex tokenizer) | `results/local_regex_metrics.json` |
| Continuation-oracle metrics (GPT-2 tokenizer) | `results/local_gpt2_metrics.json` |
| Tiny-GPT-2 greedy acceptance | `results/tiny_gpt2_greedy_acceptance.json` |
| Distilgpt2 greedy acceptance | `results/distilgpt2_greedy_acceptance_wide.json` |
| Project decision (enoch) | `.enoch/project_decision.json` |
| Project decision (omx) | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260511T201550943499+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260511T201550943499+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260511T201550943499+0000/paper_manifest.json` |
| Benchmark script (continuation oracle) | `scripts/context_ngram_trie_benchmark.py` |
| Benchmark script (greedy target) | `scripts/target_greedy_acceptance.py` |
| Smoke benchmark log | `logs/smoke_benchmark.log` |
| Local regex benchmark log | `logs/local_regex_benchmark.log` |
| Local GPT-2 benchmark log | `logs/local_gpt2_benchmark.log` |
| Tiny-GPT-2 acceptance log | `logs/tiny_gpt2_greedy_acceptance.log` |
| Distilgpt2 acceptance log | `logs/distilgpt2_greedy_acceptance_wide.log` |
