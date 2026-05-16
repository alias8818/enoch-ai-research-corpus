# In-Place KV-Cache Compaction via Importance Retention in llama.cpp: Mechanism Feasibility and Semantic Divergence

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision records, metrics files, and evidence bundles). The operator who released this artifact claims no personal authorship credit for the writing or results beyond making the artifact available. Readers should treat this document as an unreviewed AI-generated research artifact and evaluate its claims accordingly.

---

## Abstract

We investigate whether the existing KV-cache manipulation primitives in llama.cpp suffice to implement sparse, in-place importance-based cache compaction—retaining a subset of KV cells, renumbering their positions, and continuing autoregressive decoding without copying or defragmenting the retained KV tensor data. A smoke-test harness using a 15M-parameter quantized model demonstrates that the mechanism is viable: cells can be removed via `seq_rm`, retained cells can be shifted to compact positions via `seq_add`, the existing K-shift (RoPE) update graph applies the positional corrections, and subsequent decoding proceeds without error. However, logits produced after in-place compaction diverge substantially from both a full-prefix baseline (RMSE 2.17, max absolute difference 6.55) and a retained-only recomputed reference (RMSE 0.57, max absolute difference 3.35), with top-1 predictions disagreeing in both comparisons. This divergence is expected and fundamental: retained tokens' K/V vectors were computed under the original full-prefix hidden state, and removing other cells after the fact does not retroactively alter those representations. We conclude that in-place KV compaction is mechanically feasible in current llama.cpp but is not a semantically exact compaction transform; it functions as a heuristic cache-compression strategy whose quality impact must be evaluated per-task with a real importance scorer.

## Introduction

Autoregressive transformer inference maintains a growing KV cache that scales linearly with sequence length. For long-context applications, cache memory becomes a dominant resource constraint. One proposed mitigation is importance-based compaction: retain only the KV cells deemed most important and discard the rest, freeing cache slots for continued generation.

An ideal compaction scheme would be both *in-place* (avoiding tensor copies or defragmentation) and *semantically exact* (producing the same logits as if the retained tokens had been the only tokens ever presented to the model). These two properties are in tension. In-place compaction preserves the retained KV vectors as-is, but those vectors were computed under the full prefix context. Recomputing the retained tokens from scratch would yield semantically correct representations but requires a forward pass and defeats the in-place goal.

The llama.cpp inference framework exposes KV-cache manipulation primitives—`seq_rm` for removing cells by position range and `seq_add` for shifting cell positions—that, combined with its existing K-shift (RoPE correction) update graph, appear to provide the building blocks for in-place compaction. This paper asks: do these primitives suffice to implement in-place importance-based KV compaction, and does the resulting compacted cache produce outputs equivalent to a recomputed compacted prompt?

## Method

### Framework and Version

We cloned llama.cpp at commit `05e141a6b34a1535096e2bb7828418df431f7efe` (2026-05-01) and built it with CMake in Release mode (`GGML_NATIVE=OFF`, `GGML_OPENMP=OFF`, `LLAMA_CURL=OFF`, `LLAMA_BUILD_TESTS=ON`). A custom test harness was added at `tests/test-kv-importance-retention.cpp` and integrated via `tests/CMakeLists.txt`. The complete patch is recorded in `artifacts/llama_cpp_kv_importance_research.patch`.

No modifications to llama.cpp's core source code were required; the compaction procedure is composed entirely from the existing public memory API.

### Model

The smoke test uses llama.cpp's built-in tiny test model: `tinyllamas/stories15M-q4_0.gguf` (17.5 MiB, approximately 24.4M parameters, Q4_0 quantization). This model is downloaded automatically by an existing CTest fixture. It was chosen for determinism and fast iteration; it is not representative of production-scale models.

### Experimental Design

Three contexts are constructed from the same model:

1. **Full-prefix baseline.** A 48-token synthetic prompt is decoded normally. This context is never modified and serves as the reference for full-context output.

2. **In-place compacted cache.** The same 48-token prompt is decoded. Then 32 of 48 KV cells are removed using `llama_memory_seq_rm`, and the 16 retained cells (the first 8 as a prefix anchor, plus 8 sparse later positions) are shifted to compact positions 0–15 using `llama_memory_seq_add`. A single additional token is then decoded at position 16, forcing llama.cpp to apply pending K-shift updates through its normal `llama_kv_cache::update` path before computing attention.

3. **Retained-only recompute.** Only the 16 retained tokens (in their original order) are presented as a fresh prompt to a new context. This represents the semantically correct output for a cache containing exactly those tokens.

### Comparison Metrics

After decoding the post-compaction token, we compare the logit vectors:

- **RMSE** between the compacted-cache logits and the recompute reference.
- **Maximum absolute difference** between the same.
- **Top-1 agreement** (whether the highest-logit vocabulary entry is the same).
- The same three metrics comparing compacted-cache logits to the full-prefix baseline.

### Key llama.cpp Mechanisms Exploited

The compaction procedure relies on four existing mechanisms in llama.cpp:

- **`llama_kv_cache::seq_rm`** (`llama-kv-cache.cpp:342`): Removes cells in a specified sequence/position range and updates the cache head pointer for freed slots.
- **`llama_kv_cache::seq_add`** (`llama-kv-cache.cpp:514`): Shifts cell positions by a specified offset, recording per-cell shift metadata.
- **`llama_kv_cache::update`** (`llama-kv-cache.cpp:741`): Before the next decode, builds and computes a K-shift graph that applies RoPE positional corrections to keys whose positions have changed.
- **Attention masking** (`llama-kv-cache.cpp:1505`): Empty cells are skipped (`cells.is_empty(j)`) and only cells belonging to the active sequence are unmasked.

Additionally, the next input position must continue from the memory module's `seq_pos_max + 1` (`llama-batch.cpp:295`), which the compacted cache satisfies after position renumbering.

## Results

### Mechanical Feasibility

The in-place compaction procedure completed without error. After removing 32 cells and shifting 16 retained cells to positions 0–15, the cache correctly reported compact positions, and subsequent decoding at position 16 succeeded. The metric `in_place_sparse_importance_retention_decode_ok` is 1 (true).

No explicit tensor copy or defragmentation was needed. The retained KV data remained at its original memory locations; only metadata (cell position labels and the shift graph) was updated, followed by the existing K-shift RoPE correction pass.

### Logit Divergence

| Comparison | RMSE | Max Abs Difference | Top-1 Agreement |
|---|---|---|---|
| Compacted vs. Retained-only Recompute | 0.5708 | 3.3523 | No |
| Compacted vs. Full-prefix Baseline | 2.1707 | 6.5466 | No |

The compacted cache's logits are closer to the recomputed reference than to the full baseline, which is consistent with the compacted cache containing a subset of the original context. However, top-1 predictions disagree in both comparisons, and the absolute differences are substantial relative to typical logit magnitudes for a small model.

The metric `semantic_equivalence_to_recompute` is 0 (false).

### Resource Usage

The test was conducted on a host with 121 GiB total RAM (116 GiB available, no swap). Each context consumed approximately 23 MiB of host memory. No GPU was used; the test ran entirely on CPU.

## Limitations

1. **Tiny model only.** The 15M-parameter Q4_0 model is far from representative of production-scale transformers. Larger models may exhibit different divergence magnitudes, and backend-specific K-shift or cache-layout issues may arise on CUDA, Metal, or Vulkan backends that were not tested here.

2. **Single prompt, single post-compaction token.** The experiment decodes only one token after compaction. Quality degradation may accumulate over longer generation horizons, or it may stabilize; neither possibility is measured.

3. **No importance scorer.** The retained positions were chosen manually (prefix anchor plus arbitrary sparse positions). A real deployment would require a scoring function (e.g., attention-weight aggregation, perplexity-based selection, or a learned critic), and the quality of compaction depends heavily on which cells are retained.

4. **No perplexity or downstream task evaluation.** Logit RMSE and top-1 disagreement on a single token are coarse proxies for generation quality. Perplexity on a held-out corpus and performance on long-context benchmarks are needed to assess practical utility.

5. **Fundamental semantic limitation.** In-place compaction cannot be semantically exact because retained KV vectors encode information from the full prefix, including tokens that are subsequently removed. This is not a bug in the implementation; it is a property of the approach. Exact compaction would require recomputing retained tokens from scratch (or applying a learned correction), which negates the in-place advantage.

6. **API limitations.** Current llama.cpp public APIs provide range-based removal and position shifts, not a first-class "compact these arbitrary cells by importance" operation. Production use would require a scheduler/scorer layer and guardrails for models or backends where K-shift is unsupported.

7. **Hook-prototype scope.** This experiment composes existing llama.cpp API calls into a compaction procedure; it is a hook-prototype validation of mechanism feasibility, not a production-validated implementation. No CUDA copy calibration or GPU-backend testing was performed. The results should not be assumed to generalize to GPU-accelerated inference paths without separate validation.

## Reproducibility Checklist

- **Code availability:** The test harness source is in `tests/test-kv-importance-retention.cpp`; the patch against llama.cpp is at `artifacts/llama_cpp_kv_importance_research.patch`.
- **Upstream commit:** `05e141a6b34a1535096e2bb7828418df431f7efe`.
- **Model:** `tinyllamas/stories15M-q4_0.gguf`, obtained via llama.cpp's built-in CTest download fixture.
- **Build configuration:** CMake, Release mode, `GGML_NATIVE=OFF`, `GGML_OPENMP=OFF`, `LLAMA_CURL=OFF`, `LLAMA_BUILD_TESTS=ON`.
- **Build command:** `cmake -S external/llama.cpp -B external/llama.cpp/build-research <flags>` followed by `cmake --build <build-dir> --target test-kv-importance-retention -j 8`.
- **Test command:** `ctest -V -R 'test-download-model|test-kv-importance-retention'`.
- **Hardware:** CPU-only; host with 121 GiB RAM, no swap, no GPU.
- **Metrics file:** `results/kv_importance_metrics.json`.
- **Build/test logs:** `logs/cmake_configure.log`, `logs/build_test_kv_importance.log`, `logs/ctest_kv_importance.log`.
- **Determinism:** The tiny model and CPU backend produce deterministic results given fixed inputs; no stochastic sampling was involved.

## Conclusion

In-place KV-cache compaction via importance retention is mechanically feasible in current llama.cpp using only the existing `seq_rm`, `seq_add`, and K-shift update primitives, without modifying the framework's source code. The compacted cache can continue decoding, and no tensor copy or defragmentation is required—only metadata updates and RoPE positional corrections.

However, the resulting logits are not semantically equivalent to those produced by recomputing the retained tokens as a fresh compacted prompt. In our smoke test, top-1 predictions disagreed and RMSE was 0.57 (vs. recompute) and 2.17 (vs. full baseline). This divergence is inherent to the in-place approach: retained KV vectors reflect the full original prefix context and cannot be retroactively altered to simulate the absence of dropped tokens.

The technique is therefore best understood as a heuristic cache-compression strategy rather than an exact compaction transform. Its practical value depends on whether the quality degradation is acceptable for a given application, which must be evaluated through perplexity measurements and downstream task benchmarks with a genuine importance scorer—work that remains outside the scope of this prototype study.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Test harness source | `external/llama.cpp/tests/test-kv-importance-retention.cpp` |
| CMake integration | `external/llama.cpp/tests/CMakeLists.txt` |
| Patch against llama.cpp | `artifacts/llama_cpp_kv_importance_research.patch` |
| Metrics JSON | `results/kv_importance_metrics.json` |
| CMake configure log | `logs/cmake_configure.log` |
| Build log | `logs/build_test_kv_importance.log` |
| Test execution log | `logs/ctest_kv_importance.log` |
| Project decision JSON | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260501T142248454457+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T142248454457+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T142248454457+0000/paper_manifest.json` |
