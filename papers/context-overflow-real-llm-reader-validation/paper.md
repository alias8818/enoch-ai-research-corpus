# Context Overflow Real LLM Reader Validation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We evaluate whether a local generative language model can serve as an effective reader on a validated natural context-overflow benchmark, where an answer token must be extracted from long-form documents containing natural distractor text. A Qwen2.5-3B-Instruct model achieves 999/1000 exact answer-token accuracy (0.999) on the full 1,000-example dataset, with complete output parseability, outperforming lexical retrieval (0.903), TF-IDF retrieval (0.785), context truncation at 4,096 tokens (0.85), and a boundary-probe baseline at 4,096 tokens (0.95). A smaller Qwen2.5-0.5B-Instruct model achieves only 88/100 accuracy on a 100-example pilot subset, tying TF-IDF retrieval and exhibiting unparseable-output failures on technical distractor text. The single error produced by the 3B model is a generative copy error in which a nearby numeric distractor was substituted for the correct answer token. These results are limited to a single model family (Qwen2.5), a single hardware environment, and a single benchmark dataset; cross-family replication was not performed.

---

## 1. Introduction

Retrieval-augmented and long-context reading systems face a fundamental challenge when the relevant information lies beyond a conventional context window or is embedded within substantial distractor text. Prior work on the context-overflow benchmark established that simple retrieval and truncation strategies exhibit characteristic failure modes: lexical and TF-IDF retrievers miss answers that lack distinctive surface cues, truncation discards answers beyond the cutoff, and even boundary-probe methods that exploit positional heuristics (e.g., final-keyword or tail-position artifacts) achieve imperfect accuracy on natural text.

A natural question is whether a generative language model, applied as a reader over the full document, can overcome these limitations by leveraging learned attention patterns rather than explicit positional heuristics. This study provides empirical evidence on that question using a validated natural context-overflow dataset of 1,000 examples, comparing two parameter scales of the Qwen2.5-Instruct family against previously recorded retrieval and truncation baselines.

The core finding is that a 3B-parameter instruct-tuned generative reader nearly saturates the benchmark at 0.999 accuracy, materially exceeding all non-oracle baselines. However, a 0.5B-parameter reader performs substantially worse, indicating that the capability is scale-dependent and not an automatic consequence of generative decoding. We report these results with their full limitations, including the absence of cross-family replication and the restricted hardware environment.

---

## 2. Method

### 2.1 Benchmark

The evaluation uses the validated natural context-overflow pilot dataset (`context_overflow_natural_pilot_1000.jsonl`), containing 1,000 examples. Each example presents a document with natural distractor text and a target answer token of the form `ANS_XXXXXXXXXX`. Examples are stratified across four positional buckets relative to a context cutoff:

- **answer_before_cutoff**: The answer appears before the cutoff position (400 examples).
- **just_beyond_cutoff_0_64**: The answer appears 0–64 tokens beyond the cutoff (200 examples).
- **beyond_cutoff_65_256**: The answer appears 65–256 tokens beyond the cutoff (200 examples).
- **far_beyond_cutoff_gt256**: The answer appears more than 256 tokens beyond the cutoff (200 examples).

The metric is exact ANS-token accuracy: the model's output must contain the complete correct answer string to be counted as correct. A secondary metric is parseable rate: the fraction of outputs from which an ANS token can be extracted at all.

### 2.2 Reader Implementation

The reader harness (`src/real_llm_reader_validation.py`) supports local Hugging Face Transformers models with CUDA/PyTorch inference. It accepts a model identifier, loads weights in bfloat16, and generates completions with `max_new_tokens=24`. For each example, the harness records:

- Exact ANS-token match (correct/incorrect/unparseable)
- Per-example generation latency
- Process RSS and system memory telemetry
- GPU utilization via nvidia-smi (when available)
- Aggregate model-token throughput (prompt tokens + completion tokens per wall-clock second)

An OpenAI-compatible endpoint path was also implemented but could not be exercised because no local endpoint was available during the experiment.

### 2.3 Baselines

All baselines were computed on the same 1,000-example dataset in a prior project run and are reported from the stored result artifacts. The baselines are:

| Baseline | Description | Accuracy |
|---|---|---|
| Lexical retriever | Exact-match retrieval over the document | 0.903 |
| sklearn char-wb TF-IDF | Character n-gram TF-IDF retrieval | 0.785 |
| truncate_4096 | Truncate context to 4,096 tokens, extract answer | 0.85 |
| boundary_probe_4096 | Probe the boundary region at 4,096 tokens | 0.95 |
| entity-similarity decoy retriever | Entity-similarity retrieval with decoy distractors | 0.0 |
| Oracle / final-keyword / tail | Baselines that exploit the answer's tail-position artifact | 1.0 |

### 2.4 Models

Two models from the Qwen2.5-Instruct family were evaluated:

- **Qwen2.5-0.5B-Instruct**: 0.5 billion parameter instruct-tuned model, loaded from local Hugging Face cache.
- **Qwen2.5-3B-Instruct**: 3 billion parameter instruct-tuned model, loaded from local Hugging Face cache, bfloat16 precision.

### 2.5 Evaluation Protocol

The evaluation proceeded in three stages:

1. **Smoke test** (20 stratified examples): Verify pipeline correctness and output parseability.
2. **Calibrated pilot** (100 stratified examples): Estimate accuracy and identify failure modes before committing to a full run.
3. **Full validation** (1,000 examples): Complete dataset evaluation with durable result artifacts.

The 0.5B model was evaluated through stages 1 and 2 only. The 3B model was evaluated through all three stages.

---

## 3. Results

### 3.1 Qwen2.5-0.5B-Instruct

| Stage | Examples | Exact Accuracy | Parseable Rate | Samples/sec | p50 Latency | p95 Latency | Model Tokens/sec |
|---|---|---|---|---|---|---|---|
| Smoke (20) | 20 | 20/20 (1.000) | — | 4.22 | 0.205s | 0.337s | ~15,460 |
| Pilot (100) | 100 | 88/100 (0.88) | 0.89 | 4.56 | 0.205s | 0.339s | ~17,170 |

On the 100-example pilot, the 0.5B model tied the sklearn char-wb TF-IDF baseline (0.88) and fell below the lexical retriever (0.92) and boundary_probe_4096 (0.95). It exceeded truncate_4096 (0.85) and the entity-similarity decoy retriever (0.0). The 12 failures consisted predominantly of unparseable outputs where the model reproduced technical-kernel strings from the natural distractor text rather than emitting a valid ANS token, plus one case where the model emitted an incorrect ANS decoy token.

The high smoke-test accuracy (20/20) did not generalize to the larger pilot, indicating that the 20-example smoke was insufficient to characterize the 0.5B model's failure rate.

### 3.2 Qwen2.5-3B-Instruct

| Stage | Examples | Exact Accuracy | Parseable Rate | Samples/sec | p50 Latency | p95 Latency | Model Tokens/sec |
|---|---|---|---|---|---|---|---|
| Smoke (20) | 20 | 20/20 (1.000) | 1.0 | 1.04 | 0.925s | 1.441s | ~3,790 |
| Pilot (100) | 100 | 100/100 (1.000) | 1.0 | 1.04 | ~0.93s | ~1.46s | ~3,910 |
| Full (1,000) | 1,000 | 999/1,000 (0.999) | 1.0 | 0.878 | 0.931s | 2.485s | ~4,327 |

On the full 1,000-example dataset, the 3B model achieved 0.999 exact accuracy with a parseable rate of 1.0. Total wall-clock time was 1,169.9 seconds, with 1,139.5 seconds spent on generation. The model processed 4,917,912 prompt tokens and 13,000 completion tokens.

### 3.3 Baseline Comparison (Full 1,000-Example Dataset)

| Method | Accuracy |
|---|---|
| Qwen2.5-3B-Instruct | **0.999** |
| boundary_probe_4096 | 0.95 |
| lexical retriever | 0.903 |
| truncate_4096 | 0.85 |
| sklearn char-wb TF-IDF | 0.785 |
| entity-similarity decoy retriever | 0.0 |
| Oracle / final-keyword / tail | 1.0 |

The 3B generative reader exceeds all non-oracle baselines by a substantial margin. The only baselines that match or exceed it are those that explicitly exploit the answer's tail-position artifact (oracle, final-keyword, tail), which achieve 1.0 by construction.

### 3.4 Accuracy by Positional Bucket (3B, Full Dataset)

| Bucket | Examples | Accuracy |
|---|---|---|
| answer_before_cutoff | 400 | 399/400 (0.9975) |
| just_beyond_cutoff_0_64 | 200 | 200/200 (1.000) |
| beyond_cutoff_65_256 | 200 | 200/200 (1.000) |
| far_beyond_cutoff_gt256 | 200 | 200/200 (1.000) |

The sole error occurred in the `answer_before_cutoff` bucket, where the answer was positioned 32 tokens before the cutoff. This is notable because it is the bucket where truncation-based methods are expected to perform best, yet it is where the generative reader made its only error.

### 3.5 Error Analysis

The single incorrect prediction was on example `nat_cof_000465` (cutoff 1,024, answer offset −32). The correct answer was `ANS_3274281230`, which appeared in a final review memorandum within the document. The model emitted `ANS_3236250595`, which corresponds to a nearby bare numeric technical-token distractor appearing after the correct answer in the text. This is a generative copy/attention error: the model attended to a distractor token in close proximity to the correct answer and substituted it. This is not an unparseable-output failure; the model produced a well-formed but incorrect ANS token.

---

## 4. Limitations

1. **Single model family.** All results are from the Qwen2.5-Instruct family. No second model family (e.g., Phi-3.5-mini, Phi-4-mini, Llama, Mistral) was evaluated. Whether the observed accuracy generalizes across model families remains unknown.

2. **Single hardware environment.** All runs were conducted on a single local machine with CUDA PyTorch and cached Hugging Face model weights. No multi-GPU, multi-node, or cloud-environment replication was performed.

3. **Scale-dependent capability.** The 0.5B model's performance (0.88 on 100 examples, with 11% unparseable outputs) demonstrates that the reading capability is not uniform across parameter scales. The relationship between model scale and context-overflow reading accuracy was not systematically characterized.

4. **Benchmark-specific artifact.** The oracle/final-keyword/tail baselines achieve 1.0 accuracy by exploiting the positional artifact that the answer appears near the document's end. The 3B model's near-perfect accuracy may partially exploit this same artifact through learned attention patterns rather than through genuine long-range comprehension. Disentangling positional-heuristic exploitation from semantic understanding would require a modified benchmark where answer position is decorrelated from document structure.

5. **Limited failure-mode characterization.** With only one error in 1,000 examples, the failure mode of the 3B model is characterized by a single instance. Whether the observed distractor-substitution pattern is representative of the model's broader failure modes cannot be determined from this dataset alone.

6. **No production validation.** These results are from a research-prototype harness running in a single-session local environment. They have not been validated in a production serving configuration with concurrent requests, batching, or distributed inference.

7. **Dataset size.** The benchmark contains 1,000 examples. While sufficient to distinguish the 3B model's accuracy from the strongest non-oracle baseline (0.95) with reasonable statistical power, confidence intervals on the 0.999 estimate are wide at the upper tail (the 95% Clopper–Pearson interval on 999/1000 is approximately [0.994, 1.000]).

8. **Smoke-test insufficiency for 0.5B.** The 0.5B model's 20/20 smoke-test result was misleading; the 100-example pilot revealed a 12% failure rate. This illustrates that small smoke tests can fail to detect meaningful error rates, particularly when failures are concentrated in specific example types.

---

## 5. Reproducibility Checklist

- **Code availability**: `src/real_llm_reader_validation.py` and `src/context_overflow_benchmark.py` are present in the project directory. Compilation was verified via `python -m py_compile`.
- **Data availability**: `data/context_overflow_natural_pilot_1000.jsonl` is present in the project directory.
- **Model identifiers**: Qwen2.5-0.5B-Instruct and Qwen2.5-3B-Instruct, loaded from local Hugging Face cache.
- **Precision**: bfloat16 for all reported runs.
- **Generation parameters**: `max_new_tokens=24`; additional decoding parameters not specified in the available artifacts.
- **Hardware**: Local CUDA PyTorch environment; specific GPU model not recorded in the available run notes.
- **Random seeds**: Not specified in the available artifacts.
- **Result artifacts**: All summary JSON files, prediction JSONL files, and run logs are listed in the artifact manifest below.
- **Baseline provenance**: Baseline results were computed in a parent project run and copied into this branch. Same-subset comparison was used for the 100-example pilot; full-dataset comparison was used for the 1,000-example validation.
- **Statistical testing**: No formal hypothesis tests were conducted. Accuracy differences are reported as point estimates.

---

## 6. Conclusion

A Qwen2.5-3B-Instruct generative reader achieves 0.999 exact answer-token accuracy on a 1,000-example natural context-overflow benchmark, exceeding all non-oracle retrieval and truncation baselines. The single error is attributable to a distractor-substitution attention failure rather than an output-parseability failure. A smaller Qwen2.5-0.5B-Instruct model achieves only 0.88 accuracy on a 100-example subset, with 11% of outputs unparseable, indicating that the reading capability is scale-dependent.

These results support the hypothesis that a sufficiently large instruct-tuned generative model can serve as an effective reader for context-overflow tasks, but they do not establish that this capability generalizes across model families, hardware environments, or benchmark variants where the answer's positional artifact is removed. Cross-family replication (e.g., with Phi-mini or other instruct-tuned models) and evaluation on position-decorrelated benchmarks remain open directions.

---

## Referenced Artifacts

### Result files
- `results/qwen25_3b_full_1000_run.log`
- `results/qwen25_3b_full_1000_summary.json`
- `results/qwen25_3b_full_1000_summary_predictions.jsonl`
- `results/qwen25_3b_smoke_20_summary.json`
- `results/qwen25_3b_pilot_100_summary.json`
- `results/qwen25_0p5b_smoke_20_summary.json`
- `results/qwen25_0p5b_pilot_100_summary.json`
- `results/qwen25_3b_pilot_100_summary_predictions.jsonl`
- `results/qwen25_3b_smoke_20_summary_predictions.jsonl`
- `results/qwen25_0p5b_pilot_100_summary_predictions.jsonl`
- `results/qwen25_0p5b_smoke_20_summary_predictions.jsonl`
- `results/baseline_natural_pilot_1000_summary_predictions.jsonl`
- `results/baseline_natural_pilot_1000_summary.json`

### Source files
- `src/real_llm_reader_validation.py`
- `src/context_overflow_benchmark.py`
- `data/context_overflow_natural_pilot_1000.jsonl`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `run_notes.md`

### Paper artifacts
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
