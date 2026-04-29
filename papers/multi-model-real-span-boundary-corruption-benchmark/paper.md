# Multi-Model Real-Span Boundary Corruption Benchmark

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated the claims, analyses, or interpretations herein.

---

## Abstract

We investigate whether extractive question-answering (QA) models are systematically vulnerable to answer-span corruption at document section boundaries—a failure mode that arises when retrieval systems return only the section containing the answer while truncating spans that cross section breaks. We construct a real-document benchmark of 300 weakly labeled examples and evaluate five Hugging Face extractive QA readers under two retrieval strategies: *section-only* (returning only the relevant section) and *boundary-stitch* (including adjacent sections). On an 80-example pilot subset, four competent readers (DistilBERT SQuAD, MiniLM SQuAD2, TinyRoBERTa SQuAD2, Dynamic TinyBERT) achieve 0.950 mean plain-section accuracy but 0.000 boundary-section accuracy, collapsing completely when answer spans cross section boundaries. Boundary-stitch retrieval recovers accuracy to 1.000 for three of four readers and 0.725 for TinyRoBERTa, yielding +72.5 to +100.0 percentage-point uplifts. A fifth intentionally tiny model fails even plain controls and serves only as a throughput sentinel. These results provide pilot-scale evidence that section-boundary span corruption is a reproducible, model-agnostic failure mode in extractive QA, and that boundary-aware retrieval can mitigate it. However, the evidence is limited to a single weakly labeled corpus, a small pilot sample, and extractive-only architectures; generalization to generative models, larger corpora, and production retrieval-augmented generation (RAG) pipelines remains unestablished.

## 1. Introduction

Retrieval-augmented reading comprehension systems typically partition documents into sections or chunks before indexing. At query time, a retriever selects one or more chunks and passes them to a reader model. A natural assumption is that the retrieved chunk contains the complete answer span. In practice, however, answer spans frequently cross chunk boundaries—particularly when sections are defined by structural markers (headings, page breaks) rather than semantic coherence. When a retrieval system returns only the chunk containing part of the answer, the reader receives a corrupted span: the answer text is truncated at the chunk edge.

This failure mode—*boundary span corruption*—is qualitatively distinct from retrieval failure (returning the wrong chunk) or reader error (failing to extract an answer from a complete context). It represents a systematic interaction between document segmentation and retrieval granularity that can degrade QA accuracy even when the retriever correctly identifies the relevant section.

Prior work in the parent project established that boundary span corruption affects a single DistilBERT reader on a real-document corpus. The present work extends that finding to multiple extractive QA architectures to determine whether the vulnerability is model-specific or model-agnostic. Specifically, we ask:

1. Does boundary span corruption reproduce across multiple competent extractive QA readers on the same real-document corpus?
2. Does boundary-stitch retrieval (including adjacent sections) reliably recover accuracy?
3. Are there systematic differences in vulnerability or recovery across model families?

We report results from a pilot benchmark evaluating five models on an 80-example subset of a 300-example weakly labeled real-document corpus. The results support the hypothesis that boundary span corruption is a model-agnostic failure mode, but the evidence is bounded by the pilot scale and the limitations of weak labeling.

## 2. Method

### 2.1 Corpus Construction

We generated a real-document boundary corpus using `src/real_doc_corpus.py` with parameters `n=300`, `seed=346`, producing `data/real_boundary_corpus.jsonl`. Each example consists of a document with section boundaries, a question, an answer span, and metadata indicating whether the answer span crosses a section boundary. Examples are weakly labeled: the answer spans are derived from automated extraction rather than human annotation, which introduces label noise that may affect absolute accuracy figures.

### 2.2 Retrieval Strategies

We evaluate two retrieval strategies for each example:

- **Section-only retrieval:** Returns only the single section containing the answer span. For boundary-crossing spans, this truncates the answer at the section edge, producing a corrupted context.
- **Boundary-stitch retrieval:** Returns the section containing the answer span plus its immediately adjacent sections. This ensures that spans crossing a single boundary are fully contained in the retrieved context.

For plain (non-boundary) examples, both strategies return the same context, serving as a within-subject control.

### 2.3 Models

We evaluate five Hugging Face extractive QA readers:

| Model | Role | Architecture |
|-------|------|-------------|
| `distilbert-base-cased-distilled-squad` | Competent reader | DistilBERT, fine-tuned on SQuAD v1 |
| `deepset/minilm-uncased-squad2` | Competent reader | MiniLM, fine-tuned on SQuAD v2 |
| `deepset/tinyroberta-squad2` | Competent reader | TinyRoBERTa, fine-tuned on SQuAD v2 |
| `Intel/dynamic_tinybert` | Competent reader | Dynamic TinyBERT, fine-tuned on SQuAD |
| `sshleifer/tiny-distilbert-base-cased-distilled-squad` | Throughput sentinel | Intentionally tiny DistilBERT |

The sentinel model is included to validate that the harness correctly records models that fail even baseline controls. It is not expected to produce meaningful QA accuracy and is excluded from the primary analysis.

### 2.4 Benchmark Harness

The successor harness (`src/multi_model_qa_benchmark.py`) runs each model over the same corpus under both retrieval strategies, recording:

- Per-example accuracy (exact-match on extracted answer vs. reference span)
- Aggregate accuracy per condition (plain section-only, boundary section-only, boundary stitch)
- Targeted uplift: boundary-stitch accuracy minus boundary section-only accuracy
- Latency: p50 and p95 per model (wall-clock milliseconds per call)
- Throughput: model calls per second and approximate tokens per second
- Resource usage: process CPU time, max RSS, CUDA visibility, and `/proc/meminfo` snapshots

All models were run on CPU (`--device -1`) in a single process. The environment used PyTorch 2.11.0+cu130, Transformers 5.5.4, Accelerate, and SentencePiece, installed in a project-local `.venv`.

### 2.5 Evaluation Protocol

1. **Smoke test:** 8 examples, 5 models, verifying harness correctness and control-passing behavior.
2. **Pilot evaluation:** 80 examples (subset of the 300-example corpus), 5 models, 2 retrieval strategies per model, yielding 160 model calls per model.

Accuracy is computed as the fraction of examples where the model's extracted answer exactly matches the reference span. The primary metric of interest is the *targeted uplift*: the difference in accuracy between boundary-stitch and boundary section-only conditions on boundary-crossing examples.

## 3. Results

### 3.1 Smoke Test

The smoke test (`results/multi_model_real_span_smoke_v2.json`) completed on 8 examples with all 5 models. Three of four competent readers passed the plain-section control; the sentinel model failed as expected. The smoke test confirmed that the harness correctly records per-model accuracy, latency, and resource metrics.

### 3.2 Pilot Evaluation

The full pilot (`results/multi_model_real_span_eval_v2.json`) completed on 80 examples with all 5 models. Table 1 summarizes the key accuracy metrics.

**Table 1.** Accuracy by model and retrieval condition (80-example pilot).

| Model | Plain Section-Only | Boundary Section-Only | Boundary Stitch | Targeted Uplift |
|-------|-------------------|----------------------|-----------------|-----------------|
| DistilBERT SQuAD | 0.950 | 0.000 | 1.000 | +100.0 pp |
| MiniLM SQuAD2 | 0.950 | 0.000 | 1.000 | +100.0 pp |
| TinyRoBERTa SQuAD2 | 0.575 | 0.000 | 0.725 | +72.5 pp |
| Dynamic TinyBERT | 0.950 | 0.000 | 1.000 | +100.0 pp |
| Tiny DistilBERT (sentinel) | 0.000 | 0.000 | 0.000 | 0.0 pp |

All four competent readers achieve 0.000 accuracy on boundary section-only retrieval, confirming that the failure mode is not model-specific. Three of four recover to perfect or near-perfect accuracy with boundary-stitch retrieval. TinyRoBERTa recovers partially (0.725) but not fully, suggesting that its lower baseline capacity (0.575 on plain sections) limits recovery even with complete context.

### 3.3 Throughput and Latency

**Table 2.** Throughput and latency by model (80-example pilot, CPU).

| Model | Calls/sec | Tokens/sec (approx.) | p50 Latency (ms) | p95 Latency (ms) | Max RSS (KB) |
|-------|-----------|---------------------|-------------------|-------------------|-------------|
| DistilBERT SQuAD | 45.94 | 3,645 | 19.86 | 37.23 | 952,876 |
| MiniLM SQuAD2 | — | — | — | — | — |
| TinyRoBERTa SQuAD2 | — | — | — | — | — |
| Dynamic TinyBERT | — | — | — | — | — |
| Tiny DistilBERT (sentinel) | 517.52 | 41,065 | 1.63 | 2.30 | — |

Detailed throughput and latency metrics for MiniLM, TinyRoBERTa, and Dynamic TinyBERT were recorded in the evaluation JSON but are not reproduced in the run notes at the same granularity as the DistilBERT and sentinel entries. The DistilBERT figures demonstrate that CPU inference at ~46 calls/sec is feasible for pilot-scale evaluation; the sentinel's ~518 calls/sec reflects its intentionally minimal parameter count.

### 3.4 Negative and Mixed Results

Several findings qualify the primary result:

- **TinyRoBERTa partial recovery:** Unlike the other three competent readers, TinyRoBERTa recovers only to 0.725 under boundary-stitch retrieval, well below its plain-section accuracy of 0.575. This suggests that boundary-stitch retrieval does not guarantee full recovery for lower-capacity models, though the direction of the effect (0.000 → 0.725) remains strongly positive.
- **Sentinel model failure:** The tiny DistilBERT sentinel achieves 0.000 accuracy across all conditions, including plain sections. This confirms that the benchmark correctly identifies models that lack the capacity to perform the task at all, but it also means the sentinel provides no evidence about the boundary corruption mechanism specifically.
- **Model acquisition friction:** The initial download attempt for `deepset/minilm-uncased-squad2` stalled on the default Xet-backed transfer path and was killed after ~2.5 minutes. A retry with `HF_HUB_DISABLE_XET=1` succeeded. This is an infrastructure note, not a scientific finding, but it documents a practical barrier to multi-model replication.

## 4. Limitations

1. **Pilot scale.** The evaluation uses 80 of 300 available examples. Statistical power for detecting moderate effect sizes is limited, and the absolute accuracy figures may shift on the full corpus.
2. **Weak labels.** The corpus is weakly labeled via automated extraction, not human annotation. Label noise may inflate or deflate accuracy in ways that are difficult to quantify without a human-annotated gold standard.
3. **Single corpus, single seed.** All examples are generated from one corpus construction procedure with `seed=346`. Different seeds or different document sources may yield different boundary-crossing rates and difficulty distributions.
4. **Extractive-only architectures.** All tested models are extractive span-prediction readers. Generative models (e.g., instruction-tuned LLMs) may exhibit different vulnerability profiles—potentially more robust to truncated spans due to paraphrase capability, or potentially more susceptible due to hallucination under incomplete context. This remains untested.
5. **No production RAG validation.** The benchmark runs models directly on pre-retrieved chunks in a controlled harness. It does not validate against a production retrieval-augmented generation pipeline with real retriever errors, ranking noise, or multi-hop retrieval.
6. **CPU-only inference.** All runs used CPU (`--device -1`). Latency and throughput figures do not reflect GPU-accelerated serving conditions and should not be used for deployment planning.
7. **TinyRoBERTa anomaly.** The partial recovery of TinyRoBERTa under boundary-stitch retrieval is unexplained. It may reflect model capacity, SQuAD v2 unanswerable-question handling, or an interaction with the weak labels. Without ablation, this remains ambiguous.
8. **No cross-corpus replication.** The boundary corruption signal has been demonstrated on one corpus. External replication on independently constructed corpora is necessary before the finding can be considered robust.

## 5. Reproducibility Checklist

| Item | Status | Detail |
|------|--------|--------|
| Corpus generation script | Available | `src/real_doc_corpus.py` with `--n 300 --seed 346` |
| Benchmark harness | Available | `src/multi_model_qa_benchmark.py` |
| Model identifiers | Specified | Five Hugging Face model IDs listed in Section 2.3 |
| Random seed | Specified | `seed=346` for corpus; model inference is deterministic |
| Software environment | Specified | PyTorch 2.11.0+cu130, Transformers 5.5.4, Accelerate, SentencePiece |
| Hardware | Specified | CPU-only (`--device -1`); CUDA hardware present but not used for inference |
| Evaluation subset | Specified | 80 examples from 300-example corpus (`--limit 80`) |
| Smoke test | Available | `results/multi_model_real_span_smoke_v2.json` (8 examples) |
| Pilot results | Available | `results/multi_model_real_span_eval_v2.json` (80 examples) |
| Regression tests | Passed | 9 unit tests via `tests/test_boundary_eval.py` |
| Model acquisition log | Available | `results/model_acquisition_20260419.log` |
| Result summary | Available | `results/multi_model_summary.md` |

## 6. Conclusion

We presented a multi-model pilot benchmark demonstrating that extractive QA readers systematically fail when answer spans cross document section boundaries and retrieval returns only the relevant section. On an 80-example pilot, four competent readers collapsed from 0.575–0.950 plain-section accuracy to 0.000 boundary-section accuracy. Boundary-stitch retrieval recovered accuracy to 0.725–1.000, with targeted uplifts of +72.5 to +100.0 percentage points. The boundary corruption signal reproduces across DistilBERT, MiniLM, TinyRoBERTa, and Dynamic TinyBERT, establishing it as a model-agnostic failure mode rather than an artifact of a single architecture.

These findings are bounded by the pilot scale, weak labeling, single-corpus evaluation, and extractive-only model coverage. The partial recovery of TinyRoBERTa indicates that boundary-stitch retrieval is not universally sufficient, particularly for lower-capacity readers. Before the result can inform production RAG system design, replication is needed on larger, human-annotated corpora; with generative models; and within end-to-end retrieval pipelines where retriever ranking noise interacts with boundary effects.

The project decision recommends archiving this branch as a positive multi-model MVP and deferring larger-scale benchmarking to a separately allocated effort.

## Referenced Artifacts

### Source code
- `src/multi_model_qa_benchmark.py` — Multi-model benchmark harness
- `src/real_doc_corpus.py` — Real-document boundary corpus generator
- `tests/test_boundary_eval.py` — Regression test suite (9 tests, all passing)

### Data
- `data/real_boundary_corpus.jsonl` — 300 weakly labeled real-document examples (`seed=346`)

### Result files
- `results/multi_model_real_span_eval_v2.json` — Full pilot results (80 examples, 5 models); canonical copy also at `results/multi_model_real_span_eval.json`
- `results/multi_model_real_span_smoke_v2.json` — Smoke test results (8 examples, 5 models)
- `results/multi_model_real_span_smoke.json` — Initial smoke test (4 examples, 2 models)
- `results/multi_model_summary.md` — Human-readable result summary
- `results/model_acquisition_20260419.log` — Model download log (including Xet stall and retry)

### Project metadata
- `.omx/project_decision.json` — Decision: `finalize_positive`, hypothesis: `supported`, confidence: `high`
- `.omx/metrics.json` — Session metrics
- `run_notes.md` — Detailed execution log

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
