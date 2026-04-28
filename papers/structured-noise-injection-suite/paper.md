# Structured Noise Injection Suite: A Benchmark for Exposing Source-Selection Failures in Retrieval-Augmented Generation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We present the Structured Noise Injection Suite, a synthetic benchmark designed to expose source-selection failures in retrieval-augmented generation (RAG) systems. The suite generates answerable question–document pairs where documents are contaminated with structured distractors—duplicate tables, irrelevant code blocks, and distractor appendices—that remain answerable but penalize brittle source-selection heuristics. In deterministic baseline experiments on 1,500 examples (1,200 noisy, 300 clean), all four readers achieved 100% accuracy on the clean slice, producing no ranking separation, while the noisy slice yielded a Kendall distance of 0.800 and accuracy ranging from 25.4% (code-confused reader) to 100% (title-aware reader). A subsequent 120-example balanced validation on Qwen2.5-0.5B-Instruct confirmed that structured-noise failure modes transfer beyond deterministic toy readers: the model scored 70.8% on clean examples but only 52.1% on noisy examples under a minimal prompt policy. A source-guarded prompt policy improved noisy accuracy to 56.2% (+4.17 points), with the strongest gains on duplicate-table and distractor-appendix buckets, while the all-noise bucket remained unchanged at 33.3%, indicating a persistent failure cluster not addressable by prompt engineering alone. These results are bounded by the use of synthetic documents, a single small language model, and a 120-example validation slice; external validity remains uncertain.

---

## 1. Introduction

Retrieval-augmented generation systems typically assume that retrieved documents are relevant and that the generative model will attend to the correct source. In practice, retrieved context frequently contains irrelevant or misleading content—duplicate information, tangential code, or extraneous appendices—that can cause models to select wrong sources even when the correct answer is present.

Standard evaluation on clean or public-like benchmarks may fail to expose these source-selection failures, because clean documents do not stress-test the model's ability to discriminate among competing information sources within a single context window. A system that achieves high accuracy on clean data may nonetheless exhibit brittle behavior when confronted with structured noise.

We investigate whether a synthetically generated benchmark with controlled structured noise can (1) separate systems that are indistinguishable on clean data, (2) reveal specific failure clusters tied to noise types, and (3) provide actionable intervention targets. We report results from two experimental phases: deterministic baseline evaluation on 1,500 examples, and real-model validation on a 120-example balanced slice using Qwen2.5-0.5B-Instruct.

---

## 2. Method

### 2.1 Benchmark Generation

The Structured Noise Injection Suite generates answerable question–document pairs over mini-documents containing Markdown tables with numeric values. Each example consists of a question targeting a specific cell value, a clean document containing the correct answer, and a noisy variant incorporating one or more structured distractors.

Four noise types are defined:

- **Duplicate table:** A second table with conflicting values for the same query target, testing whether the reader selects the correct table.
- **Irrelevant code:** A code block inserted into the document that does not contain the answer, testing whether the reader is confused by code-like formatting.
- **Distractor appendix:** An appendix section with plausible but incorrect values, testing whether the reader privileges main-body content over appendices.
- **All noise:** A combination of all three distractor types in a single document, representing the hardest condition.

The generator produces 1,500 total examples: 300 clean/public-like examples and 1,200 noisy examples distributed across the four noise buckets (300 per bucket). Each example includes a ground-truth answer label for exact-match evaluation.

### 2.2 Deterministic Baseline Readers

Four deterministic readers simulate different source-selection strategies:

- **Title-aware / prompt-policy reader:** Selects the answer from the table whose title matches the question context. Represents an optimal heuristic.
- **First-table bias reader:** Always selects from the first table encountered. Vulnerable to duplicate-table noise.
- **Last-table bias reader:** Always selects from the last table encountered. Vulnerable to duplicate-table noise in the opposite direction.
- **Code-confused reader:** Attempts to extract answers from code blocks when present. Vulnerable to irrelevant-code noise.

These readers are not language models; they implement fixed heuristics to isolate specific failure modes and establish that the benchmark can separate strategies.

### 2.3 Real-Model Evaluation Adapter

A Hugging Face Transformers adapter (`src/llm_adapter_eval.py`) was implemented to evaluate real language model behavior on the same examples. The adapter supports:

- Balanced slice selection across noise types
- Two prompt policies: **minimal** (answer-only instruction) and **source_guarded** (instruction to identify the authoritative source before answering)
- Exact-value extraction scoring and distractor-selection detection
- Throughput measurement and resource logging (process RSS/PSS, CUDA memory, GPU utilization)

The model evaluated is Qwen2.5-0.5B-Instruct, run in-process on CUDA (GB10 platform).

### 2.4 Evaluation Metrics

- **Exact-match accuracy:** Fraction of predictions exactly matching the ground-truth answer.
- **Kendall distance:** Distance between system rankings on clean vs. noisy slices, measuring ranking change.
- **Failure cluster counts:** Number of examples where the model selects a distractor value, broken down by noise type.
- **Throughput:** Predictions per second and tokens per second.

---

## 3. Results

### 3.1 Deterministic Baseline (1,500 Examples, 7,500 Predictions)

On the clean/public-like slice (300 examples), all four deterministic readers achieved 100% accuracy, producing no ranking separation. On the noisy slice (1,200 examples), accuracy diverged substantially:

| Reader | Noisy Accuracy |
|---|---|
| Title-aware / prompt-policy | 100.0% |
| First-table bias | 50.3% |
| Last-table bias | 50.2% |
| Code-confused | 25.4% |

The Kendall distance between clean-slice and noisy-slice rankings was 0.800, indicating a major ranking change. The prompt-policy reader improved over the first-table baseline by 49.67 percentage points on noisy examples.

Failure clusters on noisy examples:

| Noise Type | Failure Count |
|---|---|
| All-noise distractors | 893 |
| Duplicate-table distractors | 598 |
| Irrelevant-code distractors | 299 |
| Appendix distractors | 299 |

Deterministic evaluation completed 7,500 predictions in 0.0661s (113,439 predictions/s; p50 latency 0.0092ms, p95 0.0148ms) on CPU only.

### 3.2 Real-Model Validation (Qwen2.5-0.5B-Instruct, 120-Example Balanced Slice)

A 120-example balanced slice (24 clean + 24 per noise type) was evaluated under two prompt policies, yielding 240 total predictions.

**Accuracy by condition:**

| Condition | Minimal Prompt | Source-Guarded Prompt | Delta |
|---|---|---|---|
| Clean | 0.708 | — | — |
| Noisy overall | 0.521 | 0.562 | +0.041 |
| Duplicate tables | 0.458 | 0.500 | +0.042 |
| Distractor appendices | 0.708 | 0.833 | +0.125 |
| Irrelevant code | — | — | — |
| All noise | 0.333 | 0.333 | 0.000 |

The source-guarded policy produced measurable gains on duplicate-table and distractor-appendix buckets. The all-noise bucket showed no improvement (0.333 under both policies), indicating a persistent source-selection failure cluster that prompt engineering alone does not resolve.

**Failure cluster distribution (real LLM):**

| Distractor Type | Count |
|---|---|
| All-noise | 28 |
| Duplicate-table | 10 |
| Irrelevant-code | 10 |
| Appendix | 5 |

The all-noise bucket accounts for the plurality of failures (28 of 53 total distractor selections), consistent with the deterministic baseline finding that combined noise is the hardest condition.

**Performance and resources:**

- Total evaluation time: 13.066s
- Throughput: 18.368 predictions/s, 8,344.44 prompt+generated tokens/s
- Latency: p50 = 0.052s, p95 = 0.0653s
- Process RSS: 1,867.5 MB; PSS: 1,855.5 MB
- CUDA allocated: 997.7 MB; reserved: 1,054.9 MB
- End GPU utilization: 82%

### 3.3 Mixed and Negative Findings

Several findings qualify the positive results:

1. **Clean-slice insensitivity is a feature, not a bug, for deterministic readers but a concern for LLMs.** The real model scored only 70.8% on clean examples, indicating that even the clean condition is non-trivial for a 0.5B-parameter model. The clean–noisy gap (0.708 vs. 0.521) confirms noise sensitivity but also reflects baseline capability limitations.

2. **The all-noise bucket is resistant to prompt-policy intervention.** Under both minimal and source-guarded prompts, accuracy remained at 0.333. This suggests that when multiple distractor types co-occur, the model's source-selection mechanism fails in a way that simple prompt instructions cannot correct.

3. **The source-guarded improvement is modest in absolute terms.** The +4.17-point gain on noisy overall accuracy, while consistent across two noise types, leaves substantial room between the current performance (56.2%) and the deterministic upper bound (100%).

4. **Irrelevant-code results are not separately reported for the real model** in the available artifacts at the per-bucket level beyond the failure cluster count (10 distractor selections), limiting granular interpretation of this noise type.

---

## 4. Limitations

1. **Synthetic documents only.** All examples are generated from templates with Markdown tables and controlled distractors. Real-world documents exhibit greater lexical and structural diversity. The extent to which these findings transfer to naturally occurring noisy retrieval contexts is unknown.

2. **Single small model.** Real-model validation was conducted exclusively on Qwen2.5-0.5B-Instruct, a 0.5-billion-parameter instruction-tuned model. Larger or differently trained models may exhibit different failure profiles. No claim is made about behavior of models not tested.

3. **Small validation slice.** The real-model evaluation used 120 examples (24 per condition). While sufficient to detect the direction of effect, confidence intervals around the reported accuracies are wide, and small-sample variability cannot be excluded as a partial explanation of the observed differences.

4. **Exact-match scoring only.** Evaluation uses exact string matching against ground-truth values. Partially correct or numerically close answers receive no credit, which may understate model capability on some examples while overstating it on others where the model guesses correctly from a distractor.

5. **No comparison to existing benchmarks.** The relationship between performance on this suite and performance on established RAG or reading-comprehension benchmarks has not been established.

6. **Deterministic readers are toy baselines.** The four deterministic readers implement fixed heuristics and do not represent realistic system architectures. Their role is to confirm that the benchmark can separate strategies, not to serve as competitive baselines.

7. **No cross-model replication.** The finding that structured-noise failure modes transfer from deterministic readers to a real LLM is based on a single model. Replication on additional models is required before generalizing this claim.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Benchmark generation code available | Yes: `src/structured_noise_suite.py` |
| LLM evaluation adapter available | Yes: `src/llm_adapter_eval.py` |
| Generated examples archived | Yes: `data/structured_noise_examples.jsonl` (1,500 examples), `data/spot_check_examples.jsonl` (10 examples) |
| Deterministic baseline predictions archived | Yes: `results/baseline_predictions.csv` (7,500 predictions) |
| Real-model predictions archived | Yes: `results/llm_qwen05b_120/predictions.csv` (240 predictions) |
| Summary statistics archived | Yes: `results/summary.json`, `results/summary.md`, `results/llm_qwen05b_120/summary.json`, `results/llm_qwen05b_120/summary.md` |
| Smoke test results archived | Yes: `results/llm_qwen05b_smoke/` (5-example calibration) |
| Run log archived | Yes: `results/llm_qwen05b_120_run.log` |
| Unit tests pass | Yes: 3 passed (2 import-time warnings from native packages) |
| Source compilation verified | Yes: `py_compile` passed for both source files |
| Model identifier specified | Yes: `Qwen/Qwen2.5-0.5B-Instruct` |
| Hardware specified | Yes: GB10 CUDA platform; CUDA allocated 997.7 MB |
| Random seeds documented | Not present in artifacts |
| Hyperparameters documented | Partially: prompt policies specified; generation parameters not detailed in available artifacts |

---

## 6. Conclusion

The Structured Noise Injection Suite demonstrates that synthetic structured noise can separate source-selection strategies that are indistinguishable on clean data. In deterministic baselines, the clean slice produced no ranking separation (all readers at 100%), while the noisy slice yielded a Kendall distance of 0.800 and accuracy ranging from 25.4% to 100%. Real-model validation on Qwen2.5-0.5B-Instruct confirmed that these failure modes transfer beyond toy readers: noisy accuracy dropped from 70.8% (clean) to 52.1% (minimal prompt), and a source-guarded prompt policy recovered only 4.17 points, with the all-noise condition remaining unchanged at 33.3%.

These findings support the hypothesis that structured noise benchmarks can reveal brittle source-selection behavior hidden by clean evaluation, and that some failure clusters (particularly combined distractor conditions) are resistant to prompt-level intervention. However, the evidence is bounded by synthetic documents, a single small model, and a 120-example validation slice. The current project artifacts support this finding in the tested setting; external replication on larger models and naturally occurring documents is necessary before broader claims are warranted.

---

## Referenced Artifacts

### Source code
- `src/structured_noise_suite.py` — generator, Markdown table parser, deterministic baseline readers, evaluator, summary writers
- `src/llm_adapter_eval.py` — CUDA/Transformers LLM evaluation adapter with balanced slicing, dual prompt policies, scoring, and resource logging
- `tests/test_structured_noise_suite.py` — smoke/regression tests

### Data
- `data/structured_noise_examples.jsonl` — 1,500 generated examples (1,200 noisy, 300 clean)
- `data/spot_check_examples.jsonl` — 10 examples for manual inspection

### Deterministic baseline results
- `results/baseline_predictions.csv` — 7,500 per-system predictions
- `results/summary.json` — aggregate deterministic metrics
- `results/summary.md` — aggregate deterministic summary

### Real-model results
- `results/llm_qwen05b_120/predictions.csv` — 240 predictions (120 examples × 2 prompt policies)
- `results/llm_qwen05b_120/summary.json` — aggregate real-model metrics
- `results/llm_qwen05b_120/summary.md` — aggregate real-model summary
- `results/llm_qwen05b_120_run.log` — raw progress log
- `results/llm_qwen05b_smoke/predictions.csv` — 5-example smoke test predictions
- `results/llm_qwen05b_smoke/summary.json` — smoke test metrics
- `results/llm_qwen05b_smoke/summary.md` — smoke test summary

### Project metadata and decisions
- `.omx/project_decision.json` — finalize_positive decision with supporting rationale
- `.omx/metrics.json` — session metrics
- `run_notes.md` — full execution log and interpretation

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
