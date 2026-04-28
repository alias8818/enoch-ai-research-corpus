# Real-RAG Answer-Abstention Boundary Benchmark: A Pilot Study of Answer-vs-Abstain Failures on Real Documents with a Local Instruction Model

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Retrieval-augmented generation (RAG) systems must decide when to answer and when to abstain, yet the boundary conditions under which small instruction-tuned models fail to abstain remain underspecified. We report a 32-example pilot benchmark constructed from SQuAD v2 development-set documents, covering four boundary types: plain supported questions, missing-evidence (unanswerable) questions, wrong-document retrieval distractors, and long-context needle-in-a-haystack cases. Using a locally cached HuggingFaceTB/SmolLM2-1.7B-Instruct model on CUDA with direct Transformers inference, we observe that plain supported accuracy (0.625) substantially exceeds boundary accuracy (0.250). Missing-evidence and wrong-document conditions each produced 6/8 false non-abstaining answers; long-context needles produced 3/8 over-abstentions and 3/8 wrong answers. These results suggest that the answer-abstention boundary failures previously observed in synthetic settings persist with real Wikipedia-derived contexts and a live local model, though the evidence remains limited to a single small model and a 32-example pilot. The project decision is `finalize_positive` with hypothesis status `supported`, confidence `medium`, and evidence strength `moderate`.

## 1. Introduction

A core requirement for deployed RAG systems is appropriate answer abstention: the model should decline to answer when the retrieved context does not support a response. Prior synthetic MVP work identified systematic failures at the answer-abstention boundary, but it remained unclear whether these failures were artifacts of synthetic template construction or genuine phenomena observable with real documents and live model inference.

This study investigates whether answer-abstention boundary failures survive the transition from synthetic to real-document settings. We construct a small but structured pilot benchmark from SQuAD v2 development data, covering four boundary types that stress different facets of the answer-vs-abstain decision. We evaluate a single small instruction-tuned model under local CUDA inference and report per-category accuracy, false-answer rates, and over-abstention rates.

The central question is: does the boundary split—where supported questions are answered correctly at a higher rate than boundary questions requiring abstention—persist with real documents and a live model? The branch-specific kill condition specified that the pilot should be finalized negative if no measurable boundary failures were observed beyond ordinary QA errors, or if the boundary split did not change abstention/error patterns relative to supported real-document QA.

## 2. Method

### 2.1 Benchmark Construction

We acquired real documents from the SQuAD v2 development set (`data/squad_dev_v2.0.json`) and constructed a 32-example RAG boundary pilot (`data/real_rag_boundary_pilot.jsonl`) with the following category breakdown:

| Category | Count | Description |
|---|---|---|
| Plain supported | 8 | Questions answerable from the provided context |
| Missing-evidence | 8 | SQuAD-impossible (unanswerable) questions paired with context that lacks the answer |
| Wrong-document distractor | 8 | Questions paired with a retrieved document from a different SQuAD article |
| Long-context needle | 8 | Answerable questions embedded in long contexts with real distractor paragraphs from other articles |

This design ensures at least two distinct boundary types (missing-evidence and wrong-document) as required by the kill condition, plus a long-context condition that tests whether extended context degrades the abstention decision.

### 2.2 Model and Inference

We used the locally cached `HuggingFaceTB/SmolLM2-1.7B-Instruct` model with direct HuggingFace Transformers inference on CUDA. An initial probe for reusable local endpoints (Ollama on port 11434 and an OpenAI-compatible endpoint on port 8000) found neither available, so the benchmark proceeded with direct model inference without a helper server.

### 2.3 Scoring

Answer and abstention behavior was scored using exact-match and substring-match heuristics. Predictions were classified as correct answers, false (non-abstaining incorrect) answers, or abstentions. The scoring heuristic does not include human judgment or semantic equivalence assessment.

### 2.4 Calibration

A smoke test and throughput calibration run was executed first (`results/smoke/`), followed by the full pilot. This calibration verified that the inference pipeline produced well-formed outputs and established baseline latency and throughput measurements before the full evaluation.

## 3. Results

### 3.1 Accuracy by Category

| Category | Accuracy | False Answers | Over-Abstentions | Wrong Answers |
|---|---|---|---|---|
| Plain supported | 0.625 (5/8) | — | — | 3/8 |
| Missing-evidence | 0.250 (2/8) | 6/8 | — | — |
| Wrong-document distractor | 0.250 (2/8) | 6/8 | — | — |
| Long-context needle | 0.250 (2/8) | — | 3/8 | 3/8 |

Plain supported accuracy (0.625) exceeds boundary accuracy (0.250) by 37.5 percentage points. The two primary boundary categories—missing-evidence and wrong-document distractors—each produced 6/8 false non-abstaining answers, indicating a strong tendency to generate unsupported responses rather than abstain. Long-context needles exhibited a mixed failure pattern: 3/8 over-abstentions (the model declined to answer despite the answer being present) and 3/8 wrong answers, suggesting that extended context degrades both the answer and abstention decisions.

### 3.2 Throughput and Resource Measurements

| Metric | Value |
|---|---|
| Total generation wall time | 7.47 s |
| Total generated tokens | 214 |
| Overall generation throughput | 28.66 tokens/s |
| p50 per-example latency | 0.13 s |
| p95 per-example latency | 0.51 s |

Per-example resource snapshots (including `/proc/meminfo`, process RSS, and GPU utilization samples) are recorded in the metrics and prediction JSON files.

### 3.3 Verification

The benchmark script (`scripts/real_rag_boundary_benchmark.py`) passed `python -m py_compile` verification after the run.

## 4. Limitations

1. **Sample size.** The pilot contains only 32 examples (8 per category). Per-category estimates are therefore highly uncertain; a binomial proportion of 0.250 from 8 trials has a 95% confidence interval of approximately [0.07, 0.59].

2. **Single model.** Only SmolLM2-1.7B-Instruct was evaluated. The observed boundary failures may be specific to this model's size, training data, or instruction-tuning procedure. No claim can be made about whether stronger or larger models exhibit similar patterns.

3. **Single data source.** All documents derive from SQuAD v2 Wikipedia articles. Boundary behavior may differ for other domains, document structures, or retrieval corpora.

4. **Heuristic scoring.** Exact-match and substring-match heuristics do not capture semantic equivalence. Some model outputs scored as incorrect may be semantically valid, and some scored as correct may be superficially matching without genuine comprehension. Human evaluation was not performed.

5. **No retrieval system.** The benchmark supplies pre-constructed (question, context) pairs rather than running a live retriever. The wrong-document and long-context conditions simulate retrieval failures but do not test an end-to-end RAG pipeline.

6. **No comparison to synthetic MVP.** While the run notes state that the synthetic boundary signal "survives," no direct numerical comparison between synthetic and real-document results is available in the artifacts. The claim of persistence is qualitative.

7. **Confidence is medium.** The project decision assigns medium confidence and moderate evidence strength, reflecting the preliminary nature of the pilot. The recommended next action is to scale the benchmark to more examples and at least one stronger model before making publication-grade claims.

## 5. Reproducibility Checklist

- **Benchmark script:** `scripts/real_rag_boundary_benchmark.py` (verified compilable)
- **Input data:** `data/squad_dev_v2.0.json` (SQuAD v2 dev set), `data/real_rag_boundary_pilot.jsonl` (32-example pilot)
- **Model:** `HuggingFaceTB/SmolLM2-1.7B-Instruct` (publicly available on HuggingFace)
- **Inference backend:** Direct HuggingFace Transformers on CUDA (no server dependency)
- **Smoke/calibration results:** `results/smoke/summary.md`, `results/smoke/real_rag_metrics.json`, `results/smoke/real_rag_predictions.jsonl`
- **Full pilot results:** `results/summary.md`, `results/real_rag_metrics.json`, `results/real_rag_predictions.jsonl`
- **Scoring method:** Exact-match and substring-match heuristics (documented in benchmark script)
- **Hardware:** CUDA GPU (specific model not recorded in artifacts; per-example GPU utilization snapshots are in prediction JSON)
- **Random seed:** Not specified in artifacts; exact numerical replication may vary

## 6. Conclusion

A 32-example real-document RAG boundary pilot using SmolLM2-1.7B-Instruct on CUDA shows that the answer-abstention boundary split persists beyond synthetic settings: plain supported accuracy (0.625) substantially exceeds boundary accuracy (0.250). Missing-evidence and wrong-document conditions produce high rates of false non-abstaining answers (6/8 each), while long-context needles exhibit mixed over-abstention and wrong-answer failures. These findings are consistent with the hypothesis that small instruction-tuned models systematically fail at the answer-abstention boundary when presented with real documents, but the evidence is limited by small sample size, a single model, a single corpus, and heuristic scoring. The project decision recommends scaling to more examples and at least one stronger model before drawing broader conclusions.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Project metrics | `.omx/metrics.json` |
| Benchmark script | `scripts/real_rag_boundary_benchmark.py` |
| Pilot input data | `data/real_rag_boundary_pilot.jsonl` |
| SQuAD v2 dev source | `data/squad_dev_v2.0.json` |
| Pilot summary | `results/summary.md` |
| Pilot metrics | `results/real_rag_metrics.json` |
| Pilot predictions | `results/real_rag_predictions.jsonl` |
| Smoke summary | `results/smoke/summary.md` |
| Smoke metrics | `results/smoke/real_rag_metrics.json` |
| Smoke predictions | `results/smoke/real_rag_predictions.jsonl` |
| Evidence bundle | `papers/source-record-redacted/evidence_bundle.json` |
| Claim ledger | `papers/source-record-redacted/claim_ledger.json` |
| Publication manifest | `papers/source-record-redacted/publication/publication_manifest.json` |
