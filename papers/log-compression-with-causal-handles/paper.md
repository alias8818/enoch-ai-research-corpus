# Log Compression With Causal Handles

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, claim ledger, benchmark results, and decision records). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this as an unreviewed AI-generated research artifact and evaluate its claims accordingly.

---

## Abstract

We investigate whether agent and tool execution logs can be compressed into *causal handles*—content-addressed identifiers derived from canonical payload signatures and parent-cause references—that preserve causal reconstructability while reducing storage and context-window occupancy. Using a local Python prototype operating on deterministic synthetic DAG-structured agent logs, we evaluate two representations: an exact (lossless) handle encoding and a lossy causal index that retains causal graph structure, component and template metadata, and state-key information while discarding volatile fields and full parameters. The exact handle representation is approximately 1.37× larger than gzip-compressed raw JSONL—a negative result for archival compression, as the high-entropy handles and per-event causal references defeat the dictionary compression that gzip exploits. The lossy causal index compresses to approximately 34% of raw gzip size (approximately 4.9% of raw JSONL) while preserving causal closure and diagnostic class metadata, with zero reconstruction mismatches and zero closure errors across runs of up to 100,000 events. Compression throughput ranges from approximately 125,000 to 146,000 events per second in a single Python process. These results suggest causal handles are viable for causal indexing and context condensation but not for exact archival compression, where traditional compressors remain superior. All results derive from synthetic logs; validation on real agent logs is necessary before drawing stronger conclusions.

## 1. Introduction

Autonomous agent systems produce execution logs recording tool invocations, state reads and writes, causal parent-child relationships, and error events. As agent sessions grow longer, the cost of storing, transmitting, and loading these logs into language-model context windows becomes a practical bottleneck.

The central question of this work is whether agent logs can be compressed into causal handles that preserve the ability to reconstruct causal structure while reducing storage and context size enough to be useful. A causal handle is a content-addressed identifier computed from a canonical payload signature, the handles of parent causes, and a schema tag. If causal identity is preserved, downstream consumers—debuggers, auditors, LLM-based diagnosis agents—can reason about what caused what without retaining every byte of the original log.

We evaluate two design points:

1. **Exact (lossless) causal handles**: an encoding that stores sufficient information to reconstruct original events verbatim.
2. **Lossy causal index**: an encoding that preserves the causal graph, component/template/level metadata, and state-key information, but drops volatile timing fields and full parameters.

Our evaluation uses a synthetic prototype that generates deterministic agent/tool DAG logs. We measure compression ratio relative to raw JSONL and gzip-compressed JSONL, throughput, query latency, and correctness of reconstruction and causal closure retrieval. We report a mixed result: the exact representation fails to beat traditional compression, but the lossy index offers substantial size reduction while preserving causal navigability.

## 2. Method

### 2.1 Synthetic Log Generation

The prototype (`src/causal_log_compression.py`) generates deterministic synthetic agent/tool DAG logs with the following properties:

- **Causal structure**: events have explicit parent-cause references forming a directed acyclic graph.
- **Component and template metadata**: each event carries a component identifier, a template name, and a log level.
- **Parameters**: events include structured parameters with varying content.
- **Volatile fields**: timestamps, duration/span fields, and other timing data that vary across runs.
- **State operations**: events record state reads and writes with key-level metadata.
- **Error events**: occasional error events are injected.

The generator is deterministic: given the same seed, it produces identical logs, enabling reproducible compression experiments. This is a toy simulation; the logs do not originate from a real agent system.

### 2.2 Causal Handle Computation

For each event $e$, a causal handle $h(e)$ is computed as:

$$h(e) = H(\text{canonical\_payload}(e) \,\|\, h(p_1) \,\|\, h(p_2) \,\|\, \ldots \,\|\, \text{schema\_tag})$$

where $H$ is a truncated SHA-256 digest, $p_i$ are parent causes, and $\|$ denotes concatenation. The canonical payload signature is a deterministic serialization of the event's non-volatile, non-causal content. Because parent handles are inputs to child handles, the handle structure is causally closed: altering any ancestor changes all descendant handles.

### 2.3 Representations

**Exact handle representation.** Stores the full handle, all parent handle references, the complete parameter set, and volatile fields. This representation supports bit-exact reconstruction of original events.

**Lossy causal index.** Stores the handle, parent handle references, component/template/level metadata, and state-key information. Drops volatile timing/span fields and full parameter values. This representation supports causal graph traversal and diagnostic class identification but cannot reconstruct full event content.

### 2.4 Verification

The prototype verifies correctness through two checks:

1. **Reconstruction check**: sampling events from the exact representation, reconstructing them, and comparing against the original.
2. **Causal closure check**: for sampled events, retrieving all ancestors via the causal index and verifying that the closure is complete and consistent.

### 2.5 Experimental Protocol

Experiments were run via `scripts/run_log_compression_experiment.sh` with event counts of 1,000; 10,000; 50,000; and 100,000. For each scale, we measured:

- Raw JSONL size and gzip-compressed JSONL size.
- Exact handle representation size (gzip-compressed).
- Causal index size (gzip-compressed).
- Compression throughput (events per second).
- Mean query latency for causal closure retrieval.
- Correctness (reconstruction mismatches and closure errors).

Unit tests were run separately via `python3 -m unittest discover -s tests -v`. All experiments ran on a single Python process on a host with approximately 116 GiB available memory and swap disabled.

## 3. Results

### 3.1 Compression Ratios

| Events | Raw JSONL | Raw gzip | Exact handles gzip | Exact / raw gzip | Causal index gzip | Index / raw gzip |
|-------:|----------:|---------:|-------------------:|-----------------:|------------------:|-----------------:|
| 1,000 | 0.526 MB | 0.077 MB | 0.106 MB | 1.372× | 0.025 MB | 0.329× |
| 10,000 | 5.289 MB | 0.769 MB | 1.058 MB | 1.376× | 0.261 MB | 0.339× |
| 50,000 | 26.543 MB | 3.853 MB | 5.275 MB | 1.369× | 1.310 MB | 0.340× |
| 100,000 | 53.117 MB | 7.712 MB | 10.536 MB | 1.366× | 2.625 MB | 0.340× |

The exact handle representation is consistently approximately 1.37× larger than raw JSONL compressed with gzip. This is a negative result for archival compression: the cryptographic-appearing handles and per-event causal references are high-entropy, defeating the dictionary-based compression that gzip exploits in the original JSONL.

The lossy causal index stabilizes at approximately 34% of raw gzip size (approximately 4.9% of raw JSONL) for runs of 10,000 events and above. The ratio is stable across scales, suggesting the index structure has consistent compressibility characteristics independent of log size in this synthetic regime.

### 3.2 Throughput

| Events | Compression throughput |
|-------:|----------------------:|
| 1,000 | 145,842 ev/s |
| 10,000 | 136,701 ev/s |
| 50,000 | 128,102 ev/s |
| 100,000 | 124,871 ev/s |

Throughput decreases modestly with scale, from approximately 146k ev/s at 1,000 events to approximately 125k ev/s at 100,000 events, likely reflecting increasing hash-chain traversal costs as the causal graph deepens. The throughput remains adequate for online indexing in a single Python process at these synthetic log volumes.

### 3.3 Query Latency

| Events | Mean query latency |
|-------:|------------------:|
| 1,000 | 0.0020 ms |
| 10,000 | 0.0396 ms |
| 50,000 | 1.2915 ms |
| 100,000 | 4.6765 ms |

Query latency grows super-linearly with event count, increasing by roughly an order of magnitude per 10× increase in events. This is consistent with closure-size-dependent traversal costs. At 100,000 events, the mean query latency of approximately 4.7 ms remains practical for interactive debugging but signals that larger histories may require structural mitigation such as memoized closure summaries or segment-level handles.

### 3.4 Correctness

Across all scales, verification found **0 reconstruction mismatches** and **0 causal closure errors**. The exact representation reconstructs original events faithfully, and the causal index correctly supports transitive closure retrieval. Unit tests additionally confirmed that changing a parent cause changes the event handle, validating the causal-closure property of the handle computation.

### 3.5 Memory

The experiment host reported approximately 116 GiB available memory with swap disabled. Peak RSS at 100,000 events was approximately 503 MiB. Memory was not a constraint in these experiments, but the RSS-to-event ratio (approximately 5 KB/event) suggests that substantially larger logs may require streaming or chunked processing.

## 4. Limitations

1. **Synthetic logs only.** The prototype generates deterministic synthetic agent/tool DAGs. Real agent logs (e.g., from production agent sessions) may exhibit different redundancy patterns, causal fanout distributions, and parameter entropy. Compression ratios and throughput on real logs may differ significantly from those reported here.

2. **Lossy index cannot reconstruct full events.** By design, the causal index discards volatile fields and full parameters. It requires a raw-log sidecar for any use case needing complete event content. The index is not a standalone archival format.

3. **Truncated digest collision risk.** The prototype uses truncated SHA-256 handles for compactness. A production system operating in adversarial or high-integrity settings should choose a collision budget explicitly (e.g., 128+ bits or full 256-bit digest) and assess collision probability against the expected event volume.

4. **Query latency scaling.** Mean query latency grows with causal closure size. Histories with large fanout or deep chains may exhibit query times that are impractical without memoized closure summaries or segment-level handles.

5. **Single-compressor comparison.** We compare against gzip only. Modern compressors such as zstd may yield different baseline ratios, potentially changing the relative advantage of the causal index.

6. **No real-world validation.** The scientific closure status of this work is *local synthetic evidence complete; real-log validation needed*. No claims about production performance are warranted.

7. **Claim audit pending.** The claim ledger for this paper contains no formally audited claims at the time of drafting. A human claim audit is noted as a project-level limitation.

## 5. Reproducibility Checklist

- **Source code**: `src/causal_log_compression.py`
- **Experiment runner**: `scripts/run_log_compression_experiment.sh`
- **Metrics summarizer**: `scripts/summarize_metrics.py`
- **Experiment log**: `logs/log_compression_experiment_20260502T174614Z.log`
- **Unit test log**: `logs/unit_tests_20260502T174540Z.log`
- **Metrics summary**: `results/log_compression_ca_handles/summary.json`
- **Run notes**: `run_notes.md`
- **Project decision record**: `.omx/project_decision.json`
- **Log generator**: Deterministic (same seed produces same logs)
- **Compression tool**: gzip (standard system gzip)
- **Hash function**: Truncated SHA-256 (used for prototype compactness; production collision budget should be specified independently)
- **Hardware context**: Single Python process; host with approximately 116 GiB available memory, swap disabled
- **Software dependencies**: Python 3, standard library (hashlib, json, gzip, unittest)
- **Evidence classification**: Local Python prototype on synthetic data; not production validation, not CUDA calibration, not hardware benchmark

## 6. Conclusion

Causal handles provide a principled mechanism for content-addressed, causally closed identification of agent log events. However, the exact (lossless) handle representation does not beat traditional compression for archival storage: it is approximately 1.37× larger than gzip-compressed raw JSONL, because high-entropy handles and per-event causal references resist dictionary compression. This is a negative result for the hypothesis that causal handles can serve as a drop-in compression replacement.

The lossy causal index presents a more promising partial result. At approximately 34% of gzip-compressed raw JSONL (approximately 4.9% of raw JSONL), it preserves causal graph structure, component and template metadata, and state-key information with verified correctness (zero mismatches, zero closure errors across all tested scales). This makes it a viable substrate for causal indexing, debugging, and LLM-context condensation—use cases where full parameter reconstruction is not required but causal navigability is essential.

The recommended production architecture is a dual-store design: raw logs archived with conventional compression (gzip, zstd), supplemented by a separate causal-handle index for retrieval, debugging, and context summarization. This avoids the false promise of exact handle compression while capturing the genuine value of causal identity for downstream reasoning.

Validation on real agent logs, comparison against additional compressors, and resolution of digest-length and query-scaling concerns remain necessary before production deployment.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Source code | `src/causal_log_compression.py` |
| Experiment runner | `scripts/run_log_compression_experiment.sh` |
| Metrics summarizer | `scripts/summarize_metrics.py` |
| Experiment log | `logs/log_compression_experiment_20260502T174614Z.log` |
| Unit test log | `logs/unit_tests_20260502T174540Z.log` |
| Metrics summary | `results/log_compression_ca_handles/summary.json` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Project metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260502T174148781474+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T174148781474+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T174148781474+0000/paper_manifest.json` |
