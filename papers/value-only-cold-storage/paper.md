# Value-Only Cold Storage: Selective Value Fetching with Resident Key Sketches for Sparse Long-Context Retrieval

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts (run logs, synthetic harness outputs, decision records, and metric files). The operator who released this artifact claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this document as an unreviewed AI-generated research artifact and evaluate its claims against the referenced evidence bundles. No human reviewer has endorsed this document.

---

## Abstract

Long-context language model inference requires maintaining large key-value (KV) caches in accelerator memory. We investigate **Value-Only Cold Storage (VOCS)**, a strategy that retains lightweight key sketches in fast memory while offloading value vectors to host memory, then selectively fetches only the highest-scoring value pages at decode time. Using a synthetic attention-level harness (not a downstream model benchmark), we compare VOCS against landmark-plus-recent pinning across four workload patterns: single-needle retrieval, mixed recent-and-global access, multi-needle retrieval, and diffuse summarization. At a budget of 16 hot pages per query with 32-dimensional key sketches, VOCS achieves mean cosine similarity to full attention of 0.945 on single-needle retrieval (baseline: −0.000) and 0.964 on mixed recent-and-global access (baseline: 0.152). However, VOCS yields cosine similarity of 0.073 on diffuse summarization and 0.083 on multi-needle retrieval at the same budget, where sparse value fetch captures only 3.3% of attention mass. A byte model for a Llama-3-8B-like 128k-context configuration estimates the VOCS resident footprint at 2.06 GiB (12.9% of the 16.0 GiB full KV), with 64 MiB of value fetch traffic per decode token. These results indicate narrow viability: VOCS is a candidate mechanism for sparse retrieval and needle-style long-context tasks, but it is not a general-purpose KV cache replacement and fails structurally on context-intensive workloads at the tested budgets.

## Introduction

Autoregressive decoding over long contexts requires maintaining large KV caches in accelerator memory. For a Llama-3-8B-class model serving 128k tokens, the KV cache alone can reach approximately 16 GiB in fp16, creating severe memory pressure. Several lines of work address this problem through compression and offloading.

Asymmetric quantization of keys and values recognizes that keys and values exhibit different sensitivity profiles. Query-aware page selection retains page-level key metadata to load only the most critical KV pages from host memory. Speculative prefetching of essential KV entries aims to hide offload latency. Prompt-observation-window compression identifies salient tokens to retain. Recent evaluation of KV cache offloading on context-intensive tasks, however, reports significant quality degradation, identifying low-rank key projection and unreliable landmark selection as failure modes.

These findings motivate a structural question: if keys are necessary for identifying *which* tokens matter, but values constitute the bulk of the memory footprint, can we retain keys (or compact key sketches) in fast memory while offloading values, then selectively restore only the value pages that the resident keys indicate are important?

We call this strategy **Value-Only Cold Storage (VOCS)**. The mechanism comprises three components:

1. **Resident key sketch.** A low-dimensional random projection of each page's key vectors remains in fast memory, consuming a small fraction of the full KV footprint.
2. **Cold value storage.** Full value vectors reside in host memory, organized in fixed-size pages.
3. **Selective value fetch.** At each decode step, the resident key sketch scores all pages against the current query; only the top-scoring value pages are fetched and reassembled into the attention computation.

This paper reports synthetic attention-level evidence for VOCS. We do not claim downstream model accuracy. We isolate the core mechanism—whether a key sketch can select value pages whose weighted sum approximates full attention—and characterize the conditions under which it succeeds or fails.

## Method

### Harness Design

We implemented a synthetic attention-level harness (`scripts/value_only_cold_storage_sim.py`) that generates random key, value, and query vectors and evaluates how well each policy approximates the full-attention output vector. The harness does not invoke a language model, tokenizer, or GPU kernel; it operates at the level of abstract attention computation to isolate the page-selection mechanism. This constitutes toy-simulation-level evidence, not a production or real-model validation.

**Vector generation.** Keys, values, and queries are drawn from standard normal distributions. Page size is fixed at 16 tokens. Key sketch dimension is 32, produced via random projection of the full key vectors.

**Policies compared:**

1. **Landmark** (`landmark`): Pins the first pages and the most recent pages; only pinned pages contribute exact key-value pairs to attention. This represents a simple baseline that retains positional anchors and recent context.

2. **VOCS exact-key oracle** (`vocs_exact_key_oracle`): Full key vectors remain resident; values are fetched only for the top-scoring pages as ranked by exact key-query dot products. This represents an upper bound on VOCS selection quality, assuming perfect key residency.

3. **VOCS sketch** (`vocs_sketch`): A 32-dimensional random-projection sketch of key vectors remains resident; values are fetched for the top-scoring pages as ranked by sketch-query scores. This is the practical VOCS mechanism.

**Workloads.** Four synthetic workload patterns simulate different attention distributions:

- **single_needle:** One answer-critical old token receives dominant attention weight, standing in for needle-in-a-haystack retrieval.
- **recent_and_global:** A mixture of early/global and recent critical tokens, representing tasks that need both long-range and local information.
- **multi_needle:** Several relevant old tokens each receive moderate attention, simulating multi-hop or multi-detail retrieval.
- **diffuse_summary:** Deliberately broad attention distribution, standing in for context-intensive extraction or summarization where many prompt tokens contribute.

**Primary configuration.** Top 16 pages per query, 16-token pages, 32-dimensional key sketch.

### Byte Model

To ground the mechanism in realistic memory figures, we estimate footprints for a Llama-3-8B-like model serving 128k context (32 layers, 8 KV heads, head dimension 128, fp16 KV):

- **Full KV:** 16.0 GiB.
- **Landmark top-64 equivalent resident KV:** 0.125 GiB (0.78% of full).
- **VOCS with exact resident keys + top-64 value pages:** 8.06 GiB (50.4% of full), dominated by the full key tensor.
- **VOCS with 32-dim key sketch + top-64 value pages:** 2.06 GiB (12.9% of full), an 87.1% resident-footprint reduction.
- **Value fetch traffic at top-64:** 64 MiB per decode token. On a 900 GB/s coherent memory link, the raw transfer lower bound is approximately 71 ns. Real kernel overhead, page-fault costs, and memory controller behavior require implementation measurement; this figure should not be treated as a latency prediction.

### Execution Environment

All runs executed on an NVIDIA GB10 host (`gx10-efe8`), Linux aarch64, 121 GiB RAM, swap disabled. The harness is pure NumPy; no GPU acceleration was used. This is a CPU-only synthetic simulation, not a CUDA copy calibration or production validation.

## Results

### Primary Comparison

Table 1 reports the primary comparison at top-16 pages per query, 16-token pages, 32-dimensional key sketch.

**Table 1.** Cosine similarity to full-attention output and attention mass captured, by workload and policy.

| Workload | Policy | Mean cosine | p05 cosine | Attention mass selected |
|---|---|---|---|---|
| single_needle | landmark | −0.000 | −0.132 | 0.007 |
| single_needle | VOCS sketch | 0.945 | 0.637 | 0.790 |
| single_needle | VOCS exact-key oracle | 1.000 | 1.000 | 0.796 |
| recent_and_global | landmark | 0.152 | −0.138 | 0.123 |
| recent_and_global | VOCS sketch | 0.964 | 0.752 | 0.826 |
| diffuse_summary | landmark | 0.176 | 0.111 | 0.031 |
| diffuse_summary | VOCS sketch | 0.073 | −0.072 | 0.033 |
| multi_needle | VOCS sketch | 0.083 | −0.068 | 0.033 |

### Sparse Retrieval: VOCS Outperforms Landmark Pinning

On **single_needle** retrieval, landmark pinning achieves mean cosine of −0.000, effectively missing the old answer token entirely (attention mass captured: 0.007). VOCS sketch achieves mean cosine of 0.945 with attention mass 0.790. The exact-key oracle (cosine 1.000, mass 0.796) confirms that the remaining gap is attributable to sketch approximation error rather than the page-selection budget itself.

On **recent_and_global** access, landmark pinning achieves mean cosine of 0.152, capturing only the recent portion of the attention pattern (mass 0.123). VOCS sketch reaches 0.964 (mass 0.826), indicating that the key sketch successfully identifies both global and recent value pages.

### Diffuse and Multi-Detail Workloads: VOCS Fails

On **diffuse_summary**, both landmark (cosine 0.176) and VOCS sketch (cosine 0.073) perform poorly. The attention mass captured by VOCS sketch is only 0.033, meaning that 16 hot pages are fundamentally insufficient when the attention distribution is broad. VOCS sketch is slightly *worse* than landmark pinning here, likely because landmark pinning at least retains recent tokens that contribute some mass, while sketch-based selection spreads its limited budget across pages that individually score highly but collectively miss the bulk of the distribution.

On **multi_needle**, VOCS sketch achieves cosine 0.083 with attention mass 0.033, again indicating that the hot-page budget is too small when multiple scattered tokens are relevant.

### Resource Usage

The 8k-token calibration run completed in 3.02 seconds, producing 60 result rows. The 32k-token scaling run completed in 10.99 seconds with maximum RSS of 250,904 KB. Available memory remained at approximately 116 GiB throughout; no memory pressure was observed. Swap was disabled as intended. These figures characterize the synthetic harness only and do not predict production inference performance.

## Limitations

1. **Synthetic attention only.** The harness evaluates whether a key sketch can select value pages whose weighted sum approximates full attention. It does not measure downstream model accuracy, perplexity, or task-specific metrics. Real attention distributions in trained models may differ substantially from the synthetic patterns tested here. This is toy-simulation-level evidence, not a real-model benchmark.

2. **No GPU kernels or page migration.** The harness does not exercise real GPU kernels, managed-memory page migration, CUDA-UVM page faults, or tokenizer/model-specific attention distributions. The byte-model estimates of fetch traffic and latency are lower bounds; real overhead depends on kernel implementation, page-fault costs, and memory controller behavior.

3. **Fixed page budget and sketch dimension.** Results are reported for top-16 pages and 32-dimensional sketches. The failure on diffuse and multi-needle workloads may be addressable with larger budgets, but the trade-off between budget and resident footprint was not exhaustively characterized. The positive results on sparse workloads also require sensitivity analysis across budgets.

4. **No latency measurement.** The synthetic harness measures approximation quality, not decode-time latency. Real VOCS implementations must contend with the latency of value page fetches, which may dominate decode time if cache-hit rates are low or page-fault paths are slow.

5. **Random key/value distributions.** Real model KV caches exhibit structure (e.g., attention head specialization, layer-dependent rank). Random vectors may over- or under-estimate the discriminability that key sketches can achieve in practice.

6. **Single hardware configuration.** All runs executed on one GB10 host. Coherent memory bandwidth and page-fault behavior will differ across platforms.

7. **Empty claim ledger.** The claim ledger for this artifact is in a blocked state with no structured claims extracted. The findings reported here have not passed a strict claim/evidence audit and should be read accordingly.

## Reproducibility Checklist

- **Code available:** `scripts/value_only_cold_storage_sim.py` (harness), `scripts/summarize_vocs.py` (summarizer).
- **Primary metrics:** `results/metrics/vocs_calibrate_v2.json` (60 result rows, 8k-token calibration).
- **Scaling metrics:** `results/metrics/vocs_long_32768.json` (32k-token scaling run).
- **Summary metrics:** `results/metrics/summary.json`.
- **Run logs:** `results/logs/vocs_smoke_v2.log`, `results/logs/vocs_calibrate_v2.log`, `results/logs/vocs_long_32768.log`, `results/logs/vocs_summary.log`.
- **Dependencies:** Python 3, NumPy, psutil. No GPU required.
- **Hardware:** NVIDIA GB10 host (`gx10-efe8`), Linux aarch64, 121 GiB RAM, swap disabled.
- **Random seeds:** Not fixed in the reported runs; exact numerical replication may vary. The relative ordering and magnitude of effects are reported as stable across repeated runs per the run notes, but this has not been formally quantified.
- **Configuration:** Top-16 pages, 16-token pages, 32-dim key sketch, standard-normal vector generation.
- **Evidence level:** Synthetic attention-level toy simulation. Not a CUDA copy calibration, not a llama.cpp hook prototype, not a production validation.

## Conclusion

Value-Only Cold Storage is a mechanism for reducing the resident KV cache footprint by retaining compact key sketches in fast memory and selectively fetching value pages from host memory. Synthetic attention-level evidence shows that this mechanism is effective for sparse retrieval workloads: at a budget of 16 hot pages with 32-dimensional key sketches, VOCS achieves cosine similarity of 0.945–0.964 to full attention on single-needle and mixed recent-and-global patterns, compared to −0.000–0.152 for landmark pinning. The estimated resident footprint for a Llama-3-8B-like 128k-context model is 2.06 GiB (12.9% of full KV), an 87.1% reduction.

However, VOCS fails on diffuse summarization (cosine 0.073) and multi-needle workloads (cosine 0.083) at the same budget, where sparse value fetch captures only 3.3% of attention mass. This is not a tuning artifact but a structural limitation: when many tokens contribute meaningfully to the output, no mechanism that selects a small fraction of value pages can approximate full attention.

VOCS should therefore be considered narrowly viable. It is a candidate mechanism for sparse retrieval, repo-QA, and needle-style long-context tasks where the answer depends on a small number of old tokens. It should not be promoted as a general-purpose KV cache replacement or applied to context-intensive structured extraction without an adaptive fallback to a larger hot-value budget or full attention. The next step is a real-model prototype in a paged-KV inference stack, instrumented for downstream quality (exact-match, F1), decode latency, value fetch volume, cache-hit rate, and memory traffic on coherent CPU/GPU systems.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Harness script | `scripts/value_only_cold_storage_sim.py` |
| Summarizer script | `scripts/summarize_vocs.py` |
| Primary metrics (8k calibration) | `results/metrics/vocs_calibrate_v2.json` |
| Scaling metrics (32k) | `results/metrics/vocs_long_32768.json` |
| Summary metrics | `results/metrics/summary.json` |
| Smoke test log | `results/logs/vocs_smoke_v2.log` |
| Calibration log | `results/logs/vocs_calibrate_v2.log` |
| Long scaling log | `results/logs/vocs_long_32768.log` |
| Summary log | `results/logs/vocs_summary.log` |
| Project decision record | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260429T153848424678+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T153848424678+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T153848424678+0000/paper_manifest.json` |
