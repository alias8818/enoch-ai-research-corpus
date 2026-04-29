# Adaptive Prefix Splitter Inference Integration

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present an integration study of an adaptive prefix-splitting prompt packing strategy into a retrieval-augmented inference pipeline. The adaptive prefix splitter selects and truncates retrieved document chunks based on prefix overlap and budget constraints, replacing a baseline similarity-only packer that includes all top-k chunks up to a token budget. In an integration benchmark over 60 real-document question-answering cases (260 chunks, 850-token budget), the adaptive prefix splitter preserved measured answer quality identically to the similarity-only baseline (mean token F1 0.536 vs. 0.536; substring match 0.900 vs. 0.900) while reducing mean prompt tokens from 817.4 to 217.9 (73.34% reduction), mean kept chunks from 7.97 to 2.53, and mean total retrieval/packing/inference latency from 22.359 ms to 6.491 ms. These results were obtained using a deterministic extractive inference shim rather than a live language model; model-backed quality validation is deferred to the parent project's existing CUDA/Qwen benchmark. The current project artifacts support this finding in the tested setting, but generalization to other corpora, models, or hardware configurations remains unvalidated.

---

## 1. Introduction

Retrieval-augmented generation (RAG) pipelines typically retrieve a set of document chunks by similarity, pack them into a prompt up to a token budget, and pass the prompt to a language model. A common inefficiency arises when multiple retrieved chunks share substantial prefix content: the prompt then contains redundant text, consuming token budget without adding new information. The adaptive prefix splitter addresses this by detecting prefix overlap among retrieved chunks and truncating redundant prefixes, thereby fitting more distinct content within the same budget.

This study integrates the previously validated adaptive prefix splitter into a concrete retrieval-to-inference pipeline and evaluates whether the integration preserves answer quality while reducing prompt tokens and latency compared to a similarity-only baseline. The branch-level kill condition was defined in advance: finalize negative if the integrated path cannot preserve answer quality while reducing prompt tokens or latency on the local real-document QA distribution.

---

## 2. Method

### 2.1 Pipeline Architecture

The integration wrapper (`src/inference_retrieval_integration.py`) implements a retrieval → prompt packing → inference → metric-sink pipeline with two configurable packing strategies:

- **similarity_only**: Packs the top-k retrieved chunks into the prompt in similarity-ranked order, respecting the token budget, without any deduplication.
- **prefix_split_adaptive**: Applies the adaptive prefix splitter, which detects prefix overlap among retrieved chunks, truncates redundant prefixes, and packs the deduplicated content within the token budget.

Both strategies share the same retrieval front-end and inference back-end. The pipeline records the following metrics per query: selected/evidence chunk identifiers, prompt token count, number of kept chunks, adaptive stop reason (for the prefix splitter), packer latency, generation latency, total latency, and generated token count.

The generator boundary is exposed as a replaceable interface, allowing substitution of the deterministic extractive shim used in this benchmark with a live model-backed generator.

### 2.2 Evaluation Harness

The evaluation harness (`src/run_integration_monitoring.py`) constructs a local real-document QA corpus, runs both packing strategies through the integrated pipeline, and scores outputs using two metrics:

- **Token F1**: Token-level F1 overlap between the generated answer and the expected answer span.
- **Substring match**: Binary indicator of whether the expected answer span appears as an exact substring of the generated answer.

The harness also captures CPU load, process memory, system memory availability, swap status, and GPU utilization snapshots.

### 2.3 Benchmark Configuration

- Cases: 60 real-document QA pairs
- Corpus chunks: 260
- Token budget: 850 tokens
- Inference: Deterministic extractive shim (no live language model invocation)

---

## 3. Results

### 3.1 Answer Quality

The adaptive prefix splitter preserved answer quality identically to the similarity-only baseline across both metrics:

| Metric | similarity_only | prefix_split_adaptive |
|---|---|---|
| Mean token F1 | 0.536 | 0.536 |
| Substring match | 0.900 | 0.900 |

No degradation in measured answer quality was observed under the tested conditions.

### 3.2 Prompt Efficiency

| Metric | similarity_only | prefix_split_adaptive | Delta |
|---|---|---|---|
| Mean prompt tokens | 817.4 | 217.9 | −599.5 (−73.34%) |
| Mean kept chunks | 7.97 | 2.53 | −5.44 |

The adaptive prefix splitter reduced mean prompt tokens by 73.34% and mean kept chunks by approximately 68%, indicating substantial redundancy in the similarity-only packing for this corpus.

### 3.3 Latency

| Metric | similarity_only | prefix_split_adaptive | Delta |
|---|---|---|---|
| Mean total latency (ms) | 22.359 | 6.491 | −15.868 |

The reduction in total latency reflects the decreased prompt construction and inference-shim processing costs associated with the smaller prompt. These latency figures encompass retrieval, packing, and the extractive inference shim; they do not include live model generation time.

### 3.4 Resource Utilization

- CPU 1-minute load: ~0.19 → ~0.26 (low throughout)
- Process max RSS: ~22.8 MB
- System MemAvailable: ~122.5 GB
- SwapFree: 0
- GPU utilization: 0% (by design; the extractive shim does not invoke GPU computation)

The integration benchmark was intentionally designed to avoid GPU dependency. The parent project contains separate live CUDA/Qwen generated-answer validation results.

### 3.5 Verification

All unit tests and compilation checks passed:

- `PYTHONPATH=src python -m unittest discover -s tests -v`
- `PYTHONPATH=src python -m py_compile src/*.py`
- `PYTHONPATH=src python src/run_integration_monitoring.py --outdir results/integration_monitoring --max-cases 60 --budget 850`

---

## 4. Limitations

1. **Extractive inference shim only.** The integration benchmark uses a deterministic extractive generator rather than a live language model. Answer quality metrics (token F1, substring match) reflect extractive matching, not the generative quality that a live model would produce. Model-backed deployment should reuse the same generator boundary and metric schema, but quality preservation under live model generation must be validated separately. The parent project's CUDA/Qwen results provide a model-backed quality baseline for the prefix splitter itself, but not for this specific integration wrapper.

2. **Single corpus and budget.** Results are reported for one local real-document QA corpus (60 cases, 260 chunks) at a single token budget (850 tokens). Performance may differ on other corpora, chunk distributions, query types, or budget settings.

3. **No live model latency data.** The reported latency reduction (−15.868 ms) reflects packing and extractive-shim overhead only. In a production pipeline with a live model, the absolute latency savings from a smaller prompt may be larger (due to reduced model inference time on shorter inputs) or may be dominated by model latency, making the packing-stage savings proportionally smaller.

4. **No GPU utilization.** The benchmark was run without GPU computation. Resource utilization figures do not reflect a production deployment profile.

5. **No external replication.** Results have not been replicated on different hardware, by independent operators, or on public benchmark datasets.

6. **Automated artifact origin.** This draft and the underlying project artifacts were produced by an automated research pipeline. No human has reviewed or endorsed the results for public release.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Source code for integration wrapper available | Yes: `src/inference_retrieval_integration.py` |
| Source code for evaluation harness available | Yes: `src/run_integration_monitoring.py` |
| Unit tests available | Yes: `tests/test_inference_retrieval_integration.py`, `tests/test_prefix_splitter.py` |
| Benchmark command documented | Yes: see Section 3.5 |
| Result artifacts persisted | Yes: CSV, JSON, Markdown summaries in `results/integration_monitoring/` |
| Token budget specified | Yes: 850 tokens |
| Corpus size specified | Yes: 60 cases, 260 chunks |
| Random seeds or determinism statement | Deterministic extractive shim; no stochastic model component in this benchmark |
| Hardware environment described | Partial: CPU load, RSS, MemAvailable, SwapFree, GPU 0% reported; exact CPU model not recorded in artifacts |
| Software dependencies listed | Not explicitly enumerated in artifacts; code is dependency-free for the extractive shim |

---

## 6. Conclusion

The integration of an adaptive prefix splitter into a retrieval-augmented inference pipeline preserved measured answer quality while reducing prompt tokens by 73.34% and mean total pipeline latency by 15.868 ms on a local real-document QA benchmark of 60 cases. The branch-level kill condition (finalize negative if quality is not preserved alongside efficiency gains) was not met, and the project decision was recorded as finalize_positive with high confidence.

These findings are bounded to the tested setting: a single corpus, a single token budget, and a deterministic extractive inference shim. The project decision recommends adopting the integrated pipeline's generator boundary and metric schema in the target inference service, using the parent project's live-model validation results as the model-backed quality baseline. Whether the observed efficiency gains transfer to live model-backed generation, other corpora, or production hardware remains to be validated.

---

## Referenced Artifacts

### Result files
- `results/integration_monitoring/summary.md`
- `results/integration_monitoring/summary.json`
- `results/integration_monitoring/integration_eval_rows.csv`

### Source files
- `src/inference_retrieval_integration.py`
- `src/run_integration_monitoring.py`
- `src/run_real_doc_experiment.py`
- `src/run_offline_experiment.py`
- `tests/test_inference_retrieval_integration.py`
- `tests/test_prefix_splitter.py`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `run_notes.md`

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/README.md`
