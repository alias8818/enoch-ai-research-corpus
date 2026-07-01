# Block Consequence Probes: Leave-One-Block-Out Perturbation for Identifying Answer-Controlling Context Without Model Internals

> **AI provenance notice:** This draft was AI-generated from automated research artifacts (run notes, claim ledger, metrics, and decision JSON). The operator claims no personal authorship credit for the writing or results beyond releasing the artifacts. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has verified the claims herein.

---

## Abstract

We investigate whether a leave-one-block-out perturbation probe can identify which context block in a prompt controls a language model's answer, without access to model internals. The probe removes each context block in turn, re-generates the answer, and flags a block as consequential when its removal changes the normalized output relative to the full-context baseline. In a controlled pilot on 24 synthetic extraction cases with four labeled blocks each, the probe correctly identified the answer-controlling block in all 24 cases (hit rate 1.0 on baseline-correct cases), while removal of irrelevant blocks produced zero answer changes across 72 ablations (irrelevant-block change rate 0.0). These results support the mechanism as a viable first-pass block-dependency diagnostic for explicit extraction prompts under deterministic local generation. The scope is narrow: synthetic labeled blocks, a single quantized local model, atomic one-token answers, and exact-match scoring. We do not claim the probe generalizes to natural documents, multi-hop reasoning, paraphrased facts, or production settings.

## Introduction

Understanding which portion of a prompt drives a language model's output is relevant for retrieval-augmented generation diagnostics, context-window management, and attribution. Internal-model methods such as attention inspection or activation patching require access to model weights and intermediate states, which may be unavailable for served or quantized models. A black-box alternative is perturbation-based probing: alter the input, observe the output change, and attribute consequence to the altered component.

We test a minimal instance of this idea: a **block consequence probe** that performs leave-one-block-out ablation on the prompt context, regenerates the answer after each removal, and scores each block by whether its removal changes the normalized answer relative to the all-blocks baseline. The probe requires no model internals—only generation access.

The research question is narrow and operational: on a controlled extraction task where exactly one of four labeled context blocks contains the answer, does the probe correctly identify that block and correctly ignore the others?

This paper reports results from that controlled pilot. We deliberately limit the scope to synthetic prompts with atomic answers and a single local model, and we discuss the resulting limitations at length.

## Method

### Probe definition

Given a prompt composed of a system instruction, a query referencing a named block, and $k$ labeled context blocks $B_1, \ldots, B_k$, the probe proceeds as follows:

1. **Baseline generation.** Generate the answer $a_{\text{full}}$ from the complete prompt containing all $k$ blocks.
2. **Ablation generations.** For each block $B_i$, generate the answer $a_{-i}$ from the prompt with $B_i$ removed (all other blocks and the instruction retained).
3. **Consequence scoring.** Block $B_i$ is scored as *consequential* if the normalized form of $a_{-i}$ differs from the normalized form of $a_{\text{full}}$.
4. **Hit determination.** The probe succeeds for a case if the gold block (the block the query instructs the model to extract from) is the unique consequential block.

Normalization consists of stripping whitespace and lowercasing, followed by exact string comparison. This is appropriate for the atomic one-token answers used in this pilot but would be insufficient for paraphrased or multi-sentence responses.

### Synthetic case construction

Each case consists of:

- Four labeled context blocks (`A` through `D`), each containing a unique answer token.
- A query instructing the model to report the token found in one designated gold block.
- The expected answer is the unique token in the gold block.

This design ensures a clear ground truth: the gold block is the only block whose content determines the correct answer. The design intentionally maximizes the signal-to-noise ratio for the probe mechanism, which means it also minimizes the ecological validity of the test cases.

### Model and runtime

- **Model:** Phi-4-mini-instruct, quantized to Q4_K_M format (GGUF), served locally.
- **Runtime:** Python `llama_cpp` binding with `n_gpu_layers=-1` (all layers on GPU), `n_ctx=1024`, `temperature=0.0` (deterministic generation).
- **Hardware:** Linux aarch64 host (`gx10-efe8`) with NVIDIA GB10 GPU. Swap disabled. Available memory remained above 122 GB throughout.

### Experimental procedure

Two runs were executed:

1. **Smoke test:** 2 cases (10 generations), verifying harness correctness and memory stability before the larger run.
2. **Main run:** 24 cases. Each case requires 5 generations (1 baseline + 4 ablations), yielding 120 total generation calls.

Telemetry (MemAvailable, SwapTotal, GPU temperature, GPU power) was captured before and after the main run.

### Metrics

- **Baseline extraction accuracy:** Fraction of cases where the full-context generation produces the correct gold-block token.
- **Probe hit rate:** Fraction of baseline-correct cases where the gold block is the unique consequential block.
- **Relevant block change rate:** Fraction of gold-block ablations that change the answer.
- **Irrelevant block change rate:** Fraction of non-gold-block ablations that change the answer.
- **Mean case time:** Wall-clock seconds per case (5 generations).
- **Generation throughput:** Estimated generation calls per second.

## Results

### Smoke test

The 2-case smoke test completed successfully:

- Baseline extraction accuracy: 2/2 (1.0).
- Probe hit rate on baseline-correct cases: 2/2 (1.0).
- Mean case time: 3.659 s/case.
- MemAvailable remained above 122 GB; swap at 0 kB; no memory pressure observed.

The smoke test confirmed harness correctness and system stability before proceeding to the main run.

### Main run

| Metric | Value |
|---|---|
| Cases | 24 |
| Total generation calls | 120 |
| Baseline extraction accuracy | 24/24 (1.0) |
| Probe hit rate (baseline-correct cases) | 24/24 (1.0) |
| Relevant block change rate | 24/24 (1.0) |
| Irrelevant block change rate | 0/72 (0.0) |
| Cases with any irrelevant change | 0/24 (0.0) |
| Mean case time | 3.484 s/case |
| Estimated generation calls/second | 1.435 |
| Model load time | 0.306 s |

The probe achieved perfect hit rate and perfect specificity on this benchmark: every gold-block removal changed the answer, and no non-gold-block removal did. The ceiling effect on both hit rate and specificity means this pilot cannot distinguish the probe's performance from the upper bound of the measurement instrument; it can only confirm that the mechanism works at all under these conditions.

### System telemetry

| Metric | Pre-run | Post-run |
|---|---|---|
| MemAvailable (kB) | 122,339,988 | 122,310,932 |
| SwapTotal / SwapFree (kB) | 0 / 0 | 0 / 0 |
| GPU temperature (°C) | 41 | 52 |
| GPU power (W) | ~11 | ~13 |

Memory consumption was negligible relative to available RAM (delta ≈ 29 MB). GPU temperature rose 11°C and power rose approximately 2 W under sustained generation load. GPU utilization read 0 at telemetry sampling instants, likely reflecting sampling between generation bursts rather than actual idle time. No thermal throttling or memory pressure was observed.

## Limitations

The results are narrow, and the following limitations constrain any generalization:

1. **Synthetic labeled blocks.** The context blocks are explicitly labeled (`A`–`D`) and contain single answer tokens. Natural retrieved documents lack such labels, have overlapping content, and may jointly determine answers. The probe's clean separation between consequential and irrelevant blocks may not hold when blocks share information or when the model draws on multiple blocks to construct its response.

2. **Single model.** Only one model (Phi-4-mini-instruct Q4_K_M) was tested. Different architectures, quantization levels, or training regimes may exhibit different sensitivity to block removal—particularly models with different instruction-following or context-attention behaviors.

3. **Atomic one-token answers with exact-match scoring.** The task requires extracting a single token and scoring is exact string match. This eliminates ambiguity but does not test whether the probe works when answers are paraphrased, multi-sentence, or semantically equivalent but lexically different.

4. **Deterministic generation.** Temperature was set to 0.0. Stochastic generation may introduce variance that makes answer-change detection noisier, potentially requiring statistical thresholds rather than binary comparison.

5. **Short context.** Context length was well within the 1024-token window. Block-consequence signals may degrade when context approaches or exceeds the model's effective attention horizon.

6. **Perturbation cost.** The probe requires $k + 1$ generations per case (one baseline plus one per block). For prompts with many blocks, this linear cost may become prohibitive without candidate prefiltering or batching strategies.

7. **No multi-hop or distributed answers.** In cases where the answer depends on reasoning across multiple blocks, the leave-one-block-out probe may flag multiple blocks as consequential, complicating interpretation.

8. **Controlled extraction only.** The probe was tested only on cases where the query explicitly names the source block. It was not tested on open-ended questions where the model must decide which block is relevant.

9. **Ceiling effects.** Both hit rate and specificity reached 1.0, so this pilot cannot estimate how close to ceiling the probe operates under more challenging conditions. The observed perfect scores are consistent with the task being too easy to stress-test the mechanism.

10. **No cross-block interaction test.** Because each block contains a unique token with no semantic overlap, the pilot does not test whether removing an irrelevant block that shares surface features with the gold block (e.g., similar vocabulary) might cause spurious answer changes.

## Reproducibility Checklist

- **Model identifier:** `lmstudio-community/Phi-4-mini-instruct-GGUF/Phi-4-mini-instruct-Q4_K_M.gguf` (local path: `<local-path-redacted>`)
- **Runtime:** Python `llama_cpp` binding, `n_gpu_layers=-1`, `n_ctx=1024`, `temperature=0.0`
- **Hardware:** Linux aarch64, NVIDIA GB10, swap disabled, >122 GB RAM available
- **Probe harness:** `scripts/block_consequence_probe.py`
- **Random seed:** Deterministic generation (temperature=0.0); no stochastic seed required
- **Number of cases:** 24 (main run), 2 (smoke test)
- **Generations per case:** 5 (1 baseline + 4 ablations)
- **Total generation calls:** 120 (main run)
- **Answer normalization:** Strip whitespace, lowercase, exact string match
- **Raw results:** `results/block_consequence_results.jsonl`
- **Summary metrics:** `results/block_consequence_summary.json`
- **Run log:** `results/logs/block_consequence_run.log`
- **Smoke raw results:** `results/logs/smoke.jsonl`
- **Smoke summary:** `results/metrics/smoke_summary.json`
- **Smoke log:** `results/logs/smoke.log`
- **Decision record:** `.omx/project_decision.json`

## Conclusion

A leave-one-block-out consequence probe correctly identified the answer-controlling context block in all 24 synthetic extraction cases tested, with zero false positives from irrelevant-block removals across 72 ablations. This supports the mechanism as a cheap, black-box block-dependency diagnostic for explicit extraction prompts under deterministic local generation.

However, the result is a controlled pilot, not a validation. The probe succeeded on a task designed to make the signal unambiguous: labeled blocks, atomic answers, exact-match scoring, and a single cooperative model. The ceiling effects (hit rate 1.0, specificity 1.0) mean the pilot confirms viability but cannot characterize the mechanism's robustness under harder conditions. Whether the probe remains reliable under naturalistic conditions—unlabeled retrieved documents, paraphrased or multi-hop answers, semantic equivalence grading, stochastic generation, longer contexts, and diverse models—remains an open question.

The appropriate next step is a broader benchmark with naturalistic document chunks, multiple local models, graded answer equivalence, and longer prompts. Until such validation is completed, the probe should be regarded as a promising but unvalidated first-pass diagnostic, not a production attribution tool.

---

## Referenced artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Probe harness | `scripts/block_consequence_probe.py` |
| Smoke log | `results/logs/smoke.log` |
| Smoke raw results | `results/logs/smoke.jsonl` |
| Smoke summary | `results/metrics/smoke_summary.json` |
| Main run log | `results/logs/block_consequence_run.log` |
| Main raw results | `results/block_consequence_results.jsonl` |
| Main summary | `results/block_consequence_summary.json` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260430T031918369644+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T031918369644+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T031918369644+0000/paper_manifest.json` |
