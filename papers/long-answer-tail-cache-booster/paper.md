# Long-Answer Tail Cache Booster: Evaluating RAM Prompt-Cache Reuse for Post-Eviction Continuation in llama-server

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, benchmark results, and server logs). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism. No human reviewer has endorsed this content.

---

## Abstract

We evaluate whether RAM-based prompt/sequence-state caching in `llama-server` can reduce prompt-prefill work when continuing a previously generated long answer after the serving slot has been evicted and reused. Using a single-slot, single-model protocol on an NVIDIA GB10 host with Phi-4-mini-instruct (Q4_K_M), we force slot eviction between a long-answer generation and a tail continuation request, comparing runs with RAM cache disabled (`--cache-ram 0`) versus enabled (`--cache-ram 1024`). Cache-enabled runs consistently reduced the number of prompt tokens requiring evaluation: from 247 to 16 (192-token answer) and from 574 to 343 (512-token answer). Prompt-processing time speedups ranged from 1.41× to 30.72×, though end-to-end wall-clock speedups were modest (1.16–1.20×) because the tail requests generated only 4–16 tokens, making decode time a non-trivial fraction of total latency. A critical finding is that retokenization of previously generated text limited prefix reuse in the 512-token condition: only 231 of 555 saved tokens were matched, indicating that full benefit requires exact token replay or server-managed continuation handles rather than client-supplied text. Results are confined to a single model, single slot, and synthetic workload; generalization to production serving is not established.

## Introduction

In LLM serving, a common operational pattern arises when a client wishes to extend or continue a previously generated long answer. If the original serving slot has since been evicted and reused for another request, the continuation prompt—comprising the original prompt plus the full generated answer plus a continuation suffix—must be prefilled from scratch. For long answers, this prefill cost can be substantial.

The `llama-server` component of llama.cpp implements a RAM prompt cache (`--cache-ram N`) that saves sequence state when a slot is released and can reload the longest matching cached prefix on a subsequent request. This mechanism directly addresses the post-eviction continuation scenario: if the tail continuation request shares a token prefix with a previously cached sequence, the server can skip recomputing that prefix.

This paper evaluates a straightforward question: does this existing cache mechanism materially reduce the cost of continuing a long answer after slot eviction, and what are the constraints on its effectiveness? We treat this as a runtime/cache-product evaluation rather than a model-quality research result, and we are careful to distinguish the prototype-level evidence from what would be required for production validation.

## Method

### Environment

All experiments ran on a single host with the following characteristics:

- **Platform:** Linux (aarch64), NVIDIA GB10
- **Memory:** 121 GiB total, swap disabled (`SwapTotal: 0 kB`), approximately 116 GiB available at start
- **GPU:** NVIDIA GB10, CUDA 13.0, driver 580.x
- **Runtime:** `llama-server` built from local llama.cpp source (exact commit hash not captured)
- **Model:** `Phi-4-mini-instruct-Q4_K_M.gguf` (lmstudio-community distribution)

### Protocol

For each cache setting (disabled, enabled), the benchmark executed the following steps:

1. Start `llama-server` with one slot and context length 4096.
2. **Request A:** Generate a technical note with `n_predict` set to the target answer length (24 for smoke, 192 or 512 for full runs).
3. **Request B:** Submit an unrelated one-token prompt to force single-slot reuse, thereby evicting Request A's slot.
4. **Request A-tail:** Submit a continuation prompt composed of the original prompt A, the generated answer A text, and a continuation suffix; generate 4 tokens (smoke) or 16 tokens (full).
5. Compare tail prompt evaluation work (tokens evaluated, prompt-processing milliseconds) and wall-clock time between cache-disabled and cache-enabled runs.

This protocol constitutes a llama.cpp hook-prototype evaluation: it exercises an existing feature (`--cache-ram`) under controlled conditions rather than implementing a new inference runtime.

### Cache Settings

- **Baseline:** `--cache-ram 0` (RAM cache disabled)
- **Optimized (smoke):** `--cache-ram 512`
- **Optimized (full runs):** `--cache-ram 1024`

### Runs

Three configurations were tested:

| Run | Answer target tokens | Tail generation tokens | Cache RAM (MiB) |
|------|-----:|-----:|-----:|
| smoke | 24 | 4 | 512 |
| full_192 | 192 | 16 | 1024 |
| full_512 | 512 | 16 | 1024 |

### Measurement

The primary metrics are:

- **Tail prompt tokens evaluated:** Number of prompt tokens the server needed to process for the tail request (fewer indicates more prefix reuse).
- **Tail prompt-processing time (ms):** Time spent in prompt evaluation for the tail request.
- **Tail wall-clock time (s):** End-to-end time for the tail request including both prefill and decode.
- **Speedup ratios:** Enabled-to-disabled ratios for prompt-ms and wall time.

Server logs were inspected to confirm whether cache saving and reuse occurred, as opposed to attributing differences to timing noise. Each condition was measured once; no repeated trials or statistical tests were performed.

## Results

### Summary Table

| Run | Cache | A target tokens | Tail prompt tokens evaluated | Tail prompt ms | Tail wall s | Tail wall speedup | Tail prompt-ms speedup |
|------|------|-----:|-----:|-----:|-----:|-----:|-----:|
| smoke | disabled | 24 | 78 | 2.790 | 0.0707 | — | — |
| smoke | enabled | 24 | 11 | 2.264 | 0.0590 | 1.20× | 1.23× |
| full_192 | disabled | 192 | 247 | 3.473 | 0.2467 | — | — |
| full_192 | enabled | 192 | 16 | 2.455 | 0.2105 | 1.17× | 1.41× |
| full_512 | disabled | 512 | 574 | 118.299 | 0.3436 | — | — |
| full_512 | enabled | 512 | 343 | 3.851 | 0.2953 | 1.16× | 30.72× |

### Server Log Confirmation

Server logs provide direct evidence that the observed differences arise from cache behavior rather than timing noise:

**Cache disabled:** Tail requests recomputed the full prompt from scratch:
- `full_192`: `n_tokens = 0 ... task.n_tokens = 247`, `batch.n_tokens = 247`
- `full_512`: `n_tokens = 0 ... task.n_tokens = 574`, `batch.n_tokens = 574`

**Cache enabled — state saving:** The server saved sequence state upon slot release:
- `full_192`: `saving prompt with length 235, total state size = 15.609 MiB`
- `full_512`: `saving prompt with length 555, total state size = 36.863 MiB`

**Cache enabled — state reuse:** The tail request reused a cached prefix:
- `full_192`: tail started at `n_tokens = 231`, evaluated only `batch.n_tokens = 16`
- `full_512`: tail started at `n_tokens = 231`, evaluated `batch.n_tokens = 343` (rather than 574)

### Memory Footprint

Cached state sizes were modest relative to available RAM:
- 235 tokens: 15.609 MiB
- 555 tokens: 36.863 MiB

No memory pressure was observed; `MemAvailable` remained high and swap was disabled throughout. However, these measurements reflect a single-slot workload; memory budget under multi-slot contention was not evaluated.

### Key Observation: Incomplete Prefix Reuse in full_512

In the `full_512` condition, the server saved 555 tokens of state but the tail request only matched a 231-token prefix. This means 324 of the saved tokens were not reused. The likely cause is detokenization/retokenization mismatch: the generated answer text was converted back to a string for the tail prompt, and re-encoding that string via the tokenizer produced a different token sequence than the original generation. This is a significant constraint: client-side text replay does not guarantee token-level prefix matching, and the benefit degrades as the mismatched portion grows.

The `full_192` condition did not exhibit this problem to the same degree: 231 of 235 saved tokens were matched (with the small discrepancy likely attributable to the continuation suffix and prompt boundary effects). The difference between conditions suggests that retokenization divergence accumulates with longer generated text.

### Prompt-ms Speedup Discrepancy

The prompt-processing millisecond speedup for `full_512` (30.72×) is dramatically larger than for `full_192` (1.41×), despite the wall-clock speedups being similar (1.16× vs. 1.17×). This discrepancy arises because the `full_512` baseline incurred a 118.299 ms prompt-processing cost (recomputing 574 tokens from scratch), while the cache-enabled run reduced this to 3.851 ms. However, the wall-clock time includes decode time for the 16 generated tail tokens, which is similar in both conditions and dilutes the prefill savings. The 30.72× prompt-ms speedup is real but should not be interpreted as an end-to-end latency improvement for this workload.

## Limitations

1. **Single model and single-slot local benchmark.** Only Phi-4-mini-instruct (Q4_K_M) was tested on a single GB10 host with one serving slot. Results do not establish behavior under multi-slot contention, larger models, or different quantizations.

2. **Synthetic workload.** The benchmark used a forced single-eviction pattern with deterministic prompt construction. Production workloads involve variable request rates, multiple concurrent slots, and diverse prompt lengths, none of which are represented here.

3. **Modest end-to-end wall speedups.** Wall-clock speedups ranged from 1.16× to 1.20×. This is because the tail requests generated only 4–16 tokens, so decode time constituted a non-trivial fraction of total latency. For longer tail generations, the relative contribution of avoided prefill may differ, but this was not measured.

4. **Retokenization mismatch limits prefix reuse.** The `full_512` run demonstrated that text-level replay of a generated answer does not guarantee token-level prefix matching. Only 231 of 555 saved tokens were reused. Full benefit requires either exact token replay (e.g., a server-side continuation handle that binds to the cached token sequence) or a token-preserving transcript mechanism.

5. **No fleet-level or production trace data.** The frequency and value of long-answer continuation requests after eviction in real serving deployments is unknown. The optimization's utility depends heavily on this workload characteristic.

6. **Single data point per configuration.** Each run condition was measured once. No variance estimates, confidence intervals, or repeated-trial statistics are available. The results should be interpreted as indicative rather than statistically robust.

7. **No eviction policy evaluation.** The cache eviction behavior under memory pressure was not tested. With larger models or more concurrent requests, the RAM budget for cached state may become a binding constraint.

8. **Prototype-level evidence only.** These results are from a llama.cpp hook-prototype evaluation using an existing `--cache-ram` feature. They do not constitute final production validation. The protocol was designed to confirm mechanism viability, not to measure production performance under realistic load.

## Reproducibility Checklist

| Item | Status |
|------|--------|
| Hardware specified | Yes: NVIDIA GB10, aarch64, 121 GiB RAM, swap disabled |
| Software versions specified | Partial: llama.cpp local build, CUDA 13.0, driver 580.x; exact commit hash not captured |
| Model specified | Yes: Phi-4-mini-instruct-Q4_K_M.gguf (lmstudio-community) |
| Benchmark script available | Yes: `scripts/tail_cache_benchmark.py` |
| Raw result data available | Yes: JSON result files per run condition |
| Server logs available | Yes: per-run server logs and evidence excerpt |
| Environment log available | Yes: `logs/environment_probe.log` |
| Random seeds specified | No: not controlled in this prototype |
| Number of trials per condition | 1 per condition |
| Statistical tests performed | No |
| Claim ledger audit status | Blocked: no structured claims were extracted for this artifact |

## Conclusion

RAM prompt/sequence-state caching in `llama-server` can reduce prompt-prefill work for long-answer tail continuations after slot eviction. In our prototype evaluation, cache-enabled runs reduced the number of prompt tokens requiring evaluation from 247 to 16 (full_192) and from 574 to 343 (full_512), with prompt-processing time speedups of 1.41× and 30.72× respectively. End-to-end wall-clock speedups were more modest (1.16–1.20×) due to the short tail-generation lengths in our test.

A critical constraint emerged: text-level replay of previously generated answers does not guarantee token-level prefix matching. In the 512-token condition, retokenization mismatch limited prefix reuse to 231 of 555 saved tokens. Achieving full benefit requires server-side continuation handles or token-preserving transcript paths rather than client-supplied text.

These results support proceeding with targeted prototype development—specifically, exposing continuation handles that bind to cached token/state prefixes and emitting cache-policy metrics (bytes saved, prefix tokens reused, prompt tokens avoided, hit/miss reason)—but do not constitute a standalone model-quality research result. The optimization is a runtime/cache-product feature with clear implementation constraints, and its production value depends on workload characteristics and token-fidelity mechanisms not yet evaluated.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Benchmark script | `scripts/tail_cache_benchmark.py` |
| Summary script | `scripts/summarize_results.py` |
| Aggregate CSV | `results/summary.csv` |
| Smoke results | `results/smoke/results_smoke.json` |
| Full 192 results | `results/full_192/results_full.json` |
| Full 512 results | `results/full_512/results_full.json` |
| Server cache evidence excerpt | `logs/server_cache_evidence_excerpt.log` |
| Environment probe log | `logs/environment_probe.log` |
| Runtime tools log | `logs/runtime_tools.log` |
| llama-cli help log | `logs/llama_cli_help_head.log` |
| llama-cli cache options log | `logs/llama_cli_cache_options.log` |
| llama-cli example options log | `logs/llama_cli_example_options.log` |
| Server logs (per run) | `results/{smoke,full_192,full_512}/server_*.log` |
| Claim ledger | `papers/source-record-redacted-20260429T013048331722+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T013048331722+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T013048331722+0000/paper_manifest.json` |
