# Garbage Token Tax: Measuring the Latency and Context-Budget Cost of Irrelevant Prompt Material in Local LLM Inference

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, benchmark logs, decision JSON, and metrics). The operator who released these artifacts claims no personal authorship credit for the writing or the experimental results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

We investigate whether irrelevant, low-information prompt material imposes a measurable cost on local LLM inference—a phenomenon we term the "garbage token tax." We define three operational dimensions: compute tax (additional prompt-prefill wall time), memory tax (additional context/KV allocation), and quality tax (loss of task accuracy). Using a Q4_K_M quantized Phi-4-mini-instruct model on an NVIDIA GB10 GPU via llama.cpp CUDA, we benchmark prompt-prefill latency at 64, 512, and 2,048 prompt tokens and run a small QA smoke test (5 arithmetic prompts per condition) with clean versus garbage-prefixed prompts. We find a clear compute tax: marginal prefill cost ranges from approximately 0.16 ms/token (64→512 tokens) to 0.27 ms/token (512→2,048 tokens), and end-to-end QA latency increases by approximately 0.35 s when prepending ~2k garbage tokens. We observe memory tax in the form of CUDA context allocation scaling from 256 MiB (context 2,048) to 512 MiB (context 4,096). However, we do **not** find evidence of a quality tax on this task: garbage-prefixed conditions matched or exceeded clean-condition accuracy, though the sample is too small to support any conclusion about quality effects in either direction. We conclude that the garbage token tax is a viable and measurable systems-level phenomenon on the latency and context-budget axes, but that quality degradation claims require substantially stronger evidence than this run provides.

## Introduction

Practical LLM deployments frequently include prompt material that carries little or no task-relevant information: system boilerplate, retrieved but irrelevant context, repeated conversation history, formatting scaffolding, and other filler. We call such tokens "garbage tokens" and ask whether they impose a measurable tax on inference.

We operationalize the garbage token tax along three dimensions:

1. **Compute tax:** Additional prompt-prefill wall time caused by extra tokens that do not add useful task information.
2. **Memory tax:** Additional context and KV-cache allocation pressure required to carry longer prompts.
3. **Quality tax:** Loss of task accuracy attributable to prepending low-semantic-content material.

The compute and memory taxes are straightforward systems-level predictions: more tokens require more prefill computation and more KV-cache memory. The quality tax is a stronger and more contingent claim: it requires that irrelevant context actively degrades model output, which may depend on model architecture, task difficulty, distractor salience, and answer position.

This study provides initial measurements of all three tax dimensions on a single local inference configuration. We deliberately frame our contributions as narrow and preliminary: we measure one model, one hardware target, one garbage style, and one simple task. Our goal is to establish whether the phenomenon is measurable at all and to characterize which dimensions show clear effects versus which require further investigation.

## Method

### Hardware and Software Environment

All experiments ran on a single machine with the following configuration:

- **Host:** Linux `gx10-efe8`, kernel 6.17.0-1014-nvidia, aarch64
- **GPU:** NVIDIA GB10, CUDA backend as reported by llama.cpp
- **System memory:** MemAvailable remained above 117 GiB throughout all runs; SwapTotal reported as 0 kB (no swap configured)
- **Model:** Phi-4-mini-instruct, Q4_K_M GGUF quantization (`lmstudio-community/Phi-4-mini-instruct-GGUF/Phi-4-mini-instruct-Q4_K_M.gguf`)
- **Inference engine:** llama.cpp, built from `/mnt/usb<local-path-redacted>`, with CUDA offload (`-ngl 99`)

### Prompt-Prefill Benchmark

We used `llama-bench` to measure prompt-prefill time and throughput at three prompt lengths: 64, 512, and 2,048 tokens. Each configuration generated 16 tokens with 3 repetitions. The command was:

```
llama-bench -m <model_path> -ngl 99 -p 64,512,2048 -n 16 -r 3 -o json
```

Wall-clock resource usage was captured via `/usr/bin/time -v`. This benchmark measures systems-level prefill cost with synthetic (non-semantic) prompt tokens, isolating compute tax from any semantic interaction effects. This constitutes a llama.cpp CUDA copy calibration benchmark rather than a production serving measurement.

### QA Smoke Test with Garbage Prefixes

To probe the quality tax, we constructed a small QA harness using 5 simple arithmetic prompts (e.g., "Return only the integer: 17+25="). Each prompt was run under three conditions:

1. **Clean:** The arithmetic prompt alone (mean 17 prompt tokens).
2. **Garbage prefix 512:** Deterministic synthetic garbage text prepended to reach approximately 512 total prompt tokens (mean 542 tokens).
3. **Garbage prefix 2048:** Deterministic synthetic garbage text prepended to reach approximately 2,048 total prompt tokens (mean 2,077 tokens).

The garbage text consisted of token-like but semantically empty material generated by the test script. All runs used temperature 0, seed 1, and single-turn mode (`-st`) to ensure determinism. Correctness was assessed by exact integer match. This constitutes a toy smoke test rather than a robust evaluation harness.

### Memory/Context Observation

CUDA context allocation sizes were recorded from llama.cpp stderr output at context sizes 2,048 and 4,096. Swap activity was monitored via `/usr/bin/time -v` output.

## Results

### Compute Tax: Prompt-Prefill Latency

Table 1 reports prompt-prefill benchmark results.

**Table 1:** Prompt-prefill benchmark, Phi-4-mini-instruct Q4_K_M on NVIDIA GB10 via llama.cpp CUDA. Each row: 3 repetitions, 16 generated tokens.

| Prompt tokens | Avg prefill time (ms) | Avg prefill throughput (tok/s) |
|---:|---:|---:|
| 64 | 21.79 | 2,952 |
| 512 | 94.45 | 5,426 |
| 2,048 | 502.20 | 4,078 |

Marginal prefill cost per additional token:

- **64 → 512 tokens:** +448 tokens, +72.66 ms → **0.162 ms/token**
- **512 → 2,048 tokens:** +1,536 tokens, +407.74 ms → **0.265 ms/token**

The marginal cost per token increases at longer prompt lengths, consistent with the quadratic component of attention computation. Throughput peaks at the intermediate prompt length (512 tokens) and declines at 2,048 tokens, indicating that the per-token overhead of longer sequences is not amortized as effectively at the longer context.

### Compute Tax: End-to-End QA Latency

Table 2 reports end-to-end wall-clock time for the QA smoke test.

**Table 2:** QA smoke test results, 5 arithmetic prompts per condition. Temperature 0, seed 1.

| Condition | Mean prompt tokens | Correct / n | Accuracy | Mean elapsed (s) |
|---|---:|---:|---:|---:|
| Clean | 17 | 4/5 | 80% | 1.528 |
| Garbage prefix 512 | 542 | 5/5 | 100% | 1.693 |
| Garbage prefix 2048 | 2,077 | 5/5 | 100% | 1.874 |

End-to-end latency increased by approximately 0.17 s (clean → garbage 512) and 0.35 s (clean → garbage 2048). These increases are consistent with the prefill benchmark and confirm that garbage tokens impose a measurable compute tax on realistic inference workloads.

### Quality Tax

The QA smoke test did **not** show a quality penalty from prepended garbage. The clean condition achieved 80% accuracy (4/5), while both garbage-prefixed conditions achieved 100% accuracy (5/5). The single clean-condition failure was on the prompt "407 + 519 =", where the model returned 914 instead of 926; both garbage-prefixed versions of the same prompt returned the correct answer 926.

We strongly caution against interpreting this as evidence that garbage tokens *improve* accuracy. With n = 5 per condition, this result is entirely consistent with random variation. The task (two- and three-digit addition) is sufficiently simple that the model may answer correctly regardless of context length. No quality tax effect can be claimed from this data, and no quality benefit can be claimed either.

### Memory Tax

CUDA context allocation, as reported by llama.cpp stderr:

- Context size 2,048: **256 MiB** allocated
- Context size 4,096: **512 MiB** allocated

Context allocation scales linearly with the configured context window in this range. No swap activity was observed in any run (`Swaps: 0`), consistent with the no-swap system configuration and the ample available system memory (>117 GiB). However, on memory-constrained deployments, the doubling of KV-cache allocation from 256 MiB to 512 MiB could become a meaningful constraint on batch size or concurrent request capacity.

## Limitations

This study has several significant limitations that constrain the generality of its conclusions:

1. **Single model and quantization:** Only Phi-4-mini-instruct Q4_K_M was tested. Larger models, different architectures, and full-precision weights may exhibit different tax profiles.

2. **Single hardware target:** All measurements were taken on one NVIDIA GB10 GPU. Different GPU architectures, memory bandwidths, and batch scheduling strategies will change the absolute and relative magnitudes of the compute and memory taxes.

3. **Inadequate quality evaluation:** The quality tax was probed with only 5 simple arithmetic questions per condition. This sample is far too small to detect modest accuracy effects and far too easy to stress the model's attention mechanism. No conclusion about quality tax—positive, negative, or null—is justified from this data alone.

4. **Synthetic garbage style:** The garbage text was deterministic, token-like, and semantically empty. Real application garbage (HTML boilerplate, stack traces, duplicated conversation history, irrelevant RAG chunks, adversarial distractors) may interact differently with the model's attention patterns and could plausibly produce quality effects not observed here.

5. **Single-turn, temperature-zero inference:** All QA runs used temperature 0 and single-turn mode. Multi-turn conversations and stochastic sampling may exhibit different behavior.

6. **No batched inference:** All measurements used single-request inference. Under batched serving, the latency impact of garbage tokens may be amortized differently or may create head-of-line blocking effects not captured here.

7. **No comparison across answer positions:** The arithmetic answer always appeared at the end of the prompt. Garbage tokens placed between the question and the answer position (in contexts where the answer must be extracted from mid-prompt) may produce stronger quality effects.

8. **Software version gap:** The llama.cpp build path is reported, but the exact commit hash was not captured in run notes. This limits bit-exact reproducibility.

9. **No statistical uncertainty quantification:** The benchmark used 3 repetitions; the QA smoke used 5 items per condition. No confidence intervals or significance tests were computed. Given the sample sizes, none would be meaningful for the quality axis.

## Reproducibility Checklist

- **Model specified:** Yes — Phi-4-mini-instruct Q4_K_M GGUF, path and community source identified.
- **Hardware specified:** Yes — NVIDIA GB10, aarch64 host, kernel version reported.
- **Software versions:** Partially — llama.cpp build path reported; exact commit hash not captured. This is a reproducibility gap.
- **Random seeds:** Yes — all QA runs used seed 1 and temperature 0.
- **Benchmark parameters:** Yes — prompt lengths, generation lengths, and repetition counts specified.
- **Raw data available:** Yes — benchmark JSON, QA JSONL, and timing logs are preserved as named artifacts.
- **Analysis code available:** The postprocessing script is inline in run notes; the QA runner script is identified.
- **Statistical uncertainty:** Not reported. The benchmark used 3 repetitions; the QA smoke used 5 items per condition. No confidence intervals or significance tests were computed, and given the sample sizes, none would be meaningful for the quality axis.
- **Claim audit status:** The claim ledger for this run is empty (`audit_status: blocked_empty_claims`). No structured claims were extracted, and the artifact has not passed strict claim/evidence audit.

## Conclusion

The garbage token tax is a real and measurable systems-level phenomenon. On a local Phi-4-mini-instruct Q4_K_M deployment via llama.cpp CUDA on an NVIDIA GB10, we find:

- **Compute tax is confirmed:** Marginal prefill cost ranges from ~0.16 ms/token to ~0.27 ms/token depending on prompt length, and end-to-end QA latency increases by ~0.35 s when ~2k garbage tokens are prepended.
- **Memory tax is confirmed:** CUDA context allocation doubles from 256 MiB to 512 MiB when context window doubles from 2,048 to 4,096 tokens, creating potential batch-size constraints on memory-limited deployments.
- **Quality tax is not supported by this data:** The small arithmetic QA smoke showed no accuracy degradation from garbage prefixes. This null result should not be interpreted as evidence against quality tax; it reflects the inadequacy of the evaluation rather than the absence of the effect.

The garbage token tax is viable as an optimization and research target when framed as a token-cost, latency, and context-budget phenomenon. Claims of quality degradation require a substantially larger evaluation harness with realistic garbage classes (HTML boilerplate, stack traces, duplicated chat history, irrelevant RAG chunks), randomized seeds, diverse task suites, answer-position variants, and at least one stronger model before they can be substantiated.

---

## Referenced Artifacts

| Artifact | Path | Description |
|---|---|---|
| Run notes | `run_notes.md` | Full experimental log and interpretation |
| Decision JSON | `.omx/project_decision.json` | Final project decision and evidence summary |
| Consolidated metrics | `results/garbage_token_tax_metrics.json` | Postprocessed benchmark and QA metrics |
| QA results | `results/qa_garbage_tax_results.json` | Per-case QA rows and corrected parser summary |
| QA runner script | `scripts/run_garbage_token_tax.py` | Deterministic QA/garbage-prefix runner |
| Benchmark log | `logs/bench_phi4_prompt_lengths.json` | llama-bench raw JSON output |
| Benchmark timing | `logs/bench_phi4_prompt_lengths.err` | `/usr/bin/time -v` and CUDA init evidence |
| QA run log | `logs/qa_garbage_tax_run.jsonl` | QA run output |
| QA timing | `logs/qa_garbage_tax_run.time` | QA run resource timing |
| Generated prompts | `prompts/generated/` | Clean and garbage-prefixed prompt files |
| Smoke test output | `logs/cli_smoke2.out`, `logs/cli_smoke2.err` | Single-turn smoke test and CUDA allocation evidence |
| Claim ledger | `papers/.../claim_ledger.json` | Empty claim ledger (audit blocked) |
| Evidence bundle | `papers/.../evidence_bundle.json` | Source metadata only |
| Paper manifest | `papers/.../paper_manifest.json` | Generation metadata |
