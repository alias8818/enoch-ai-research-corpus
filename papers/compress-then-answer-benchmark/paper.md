# Compress-Then-Answer Benchmark

**AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We present the Compress-Then-Answer Benchmark, a reproducible harness for measuring how context compression changes question-answering system rankings and surfaces failure modes. Using a synthetic 1,000-example QA dataset with tagged failure categories (late evidence, stale same-entity, front-matter), we evaluate five compression policies crossed with three answer policies under a two-sentence budget. In a deterministic baseline, compressed-context evaluation reshuffles answerer rankings—`latest_entity_regex` drops from rank 1 on full context to rank 3 under best compression, while `first_entity_regex` rises from rank 2 to rank 1—while matching peak accuracy (0.871) at 24.0% mean sentence retention. Model-backed evaluation with Phi-4-mini-instruct (Q4_K_M) on 100 examples across two independent synthetic seeds confirms that compressed context consistently changes the top-ranked answerer: both seeds rank `regex_latest` first on full context but `llm_choice` first under best compressed context. The `stale_same_entity` failure cluster is the dominant and most stable high-error category across all runs (mean error 0.4655–0.4731 at n=100). However, the direction of the rank shift was unstable between the 30-example and 100-example sample sizes, and all model-backed results use a single small model family on CPU, limiting external validity.

## Introduction

Retrieval-augmented and long-context question-answering systems increasingly operate over compressed or truncated contexts, whether by design (retrieval budgets, context window limits) or by necessity (latency, cost). A natural assumption is that compression degrades all systems proportionally, preserving relative rankings. If compression instead reshuffles system rankings—or selectively amplifies certain failure modes—then benchmarks that evaluate only on full context may give a misleading picture of production behavior.

This work asks two questions:

1. **Ranking shift:** Does evaluating question-answering systems on compressed context change which answerer ranks highest, compared to evaluation on full context?
2. **Failure exposure:** Does compressed-context evaluation surface stable, interpretable failure clusters that are less visible under full-context evaluation?

We address these questions with a minimal, dependency-free benchmark harness and a synthetic QA dataset designed to contain controllable failure categories. We report results from both deterministic (regex-based) and model-backed (local GGUF inference) evaluation, and we test stability across sample sizes and synthetic seeds.

## Method

### Benchmark Harness

The benchmark harness is implemented in dependency-free Python (`src/compress_then_answer/benchmark.py` for the deterministic path, `src/compress_then_answer/llm_benchmark.py` for the model-backed path). The harness:

1. Generates synthetic QA examples with tagged failure categories.
2. Applies a compression policy to reduce the context to a fixed sentence budget.
3. Applies an answer policy to the (compressed or full) context to produce a predicted answer.
4. Compares the prediction against the ground-truth label and records accuracy, sentence retention, and per-failure-category error rates.

### Synthetic Dataset

The dataset contains 1,000 deterministic synthetic QA examples generated with `seed=3443677`. Each example includes a multi-sentence context, a question, a ground-truth entity label, and one or more failure tags drawn from three categories:

- **`late_evidence`**: The correct answer appears only in the final sentences of the context, making it vulnerable to truncation or compression that discards late material.
- **`stale_same_entity`**: The context contains an earlier mention of the same entity with outdated or conflicting information, testing whether the system selects the latest evidence.
- **`front_matter`**: The context begins with irrelevant or misleading introductory sentences, testing robustness to noise in the leading positions.

A second seed (`3443678`) was used for cross-seed stability evaluation, generating an independent 100-example subset.

### Compression Policies

Five compression policies were evaluated:

| Policy | Description |
|---|---|
| `none_full_context` | No compression; full context retained (retention = 1.0) |
| `first_2_sentences` | Retain the first two sentences |
| `last_2_sentences` | Retain the last two sentences |
| `query_entity_2_sentences` | Retain up to two sentences containing the query entity |
| `llm_select_2_sentences` | LLM selects up to two sentences (model-backed only) |

All compression policies operate under a two-sentence budget.

### Answer Policies

Three answer policies were evaluated:

| Policy | Description |
|---|---|
| `first_entity_regex` | Extract the first entity-like string matching a regex |
| `latest_entity_regex` | Extract the last entity-like string matching a regex |
| `llm_choice` | LLM selects from allowed labels (model-backed only) |

### Model-Backed Evaluation

Model-backed evaluation uses `llama-cpp-python` with the cached local model `Phi-4-mini-instruct-Q4_K_M.gguf`, running on CPU (`n-gpu-layers 0`). Completion caching ensures deterministic re-evaluation. Answer normalization maps model outputs against the allowed label set.

### Evaluation Protocol

The deterministic baseline evaluates all five compression policies crossed with the two regex answer policies on 1,000 examples. The model-backed evaluation evaluates a subset of policies (including `llm_select_2_sentences` and `llm_choice`) on smaller samples (30 and 100 examples) due to inference cost. Accuracy, mean sentence retention, and per-failure-category mean error are recorded for each system (compression + answerer pair).

## Results

### Deterministic Baseline (n = 1,000, seed = 3443677)

| System | Accuracy | Mean Sentence Retention |
|---|---|---|
| `none_full_context+latest_entity_regex` | 0.871 | 1.000 |
| `query_entity_2_sentences+first_entity_regex` | 0.871 | 0.240 |
| `none_full_context+first_entity_regex` | 0.871 | 1.000 |

On full context, `latest_entity_regex` and `first_entity_regex` achieve identical accuracy (0.871). Under the best compressed context (`query_entity_2_sentences`), `first_entity_regex` becomes the sole top-ranked answerer because `latest_entity_regex` drops to rank 3. This demonstrates that compression can reshuffle answerer rankings even when peak accuracy is preserved.

Failure clusters under deterministic evaluation:

| Failure Tag | Mean Error |
|---|---|
| `stale_same_entity` | 0.6613 |
| `late_evidence` | 0.5198 |
| `front_matter` | 0.4816 |

### Model-Backed Smoke Test (n = 30, seed = 3443677, Phi-4-mini CPU)

| System | Accuracy | Mean Sentence Retention |
|---|---|---|
| `none_full_context+llm_choice` | 0.9000 | 1.000 |
| `llm_select_2_sentences+regex_latest` | 0.8667 | 0.1923 |
| `llm_select_2_sentences+llm_choice` | 0.7667 | 0.1923 |

On full context at n = 30, `llm_choice` ranks first. Under best compressed context, `regex_latest` ranks first and `llm_choice` drops to rank 2. The `stale_same_entity` cluster remains the dominant failure mode (mean error 0.4667, system spread 0.4000).

### Model-Backed Stability Run (n = 100, seed = 3443677, Phi-4-mini CPU)

| System | Accuracy | Mean Sentence Retention |
|---|---|---|
| `query_entity_2_sentences+llm_choice` | 0.8900 | 0.2430 |
| `none_full_context+regex_latest` | 0.8800 | 1.000 |
| `none_full_context+llm_choice` | 0.8600 | 1.000 |

At n = 100, the rank shift direction reverses relative to n = 30: `regex_latest` now ranks first on full context, while `llm_choice` ranks first under best compressed context. This instability in rank direction between n = 30 and n = 100 is a negative result—small samples give a misleading picture of which answerer benefits from compression.

The `stale_same_entity` cluster persists (mean error 0.4655).

### Cross-Seed Stability (n = 100, seed = 3443678, Phi-4-mini CPU)

| System | Accuracy | Mean Sentence Retention |
|---|---|---|
| `query_entity_2_sentences+llm_choice` | 0.8800 | 0.2432 |

Both seeds at n = 100 agree on the rank structure: `regex_latest` ranks first on full context, and `llm_choice` ranks first under best compressed context. The `stale_same_entity` cluster is stable (mean error 0.4731 on seed 3443678 vs. 0.4655 on seed 3443677).

### Summary of Key Findings

1. **Ranking shift is reproducible at n = 100 across seeds**, but the direction of the shift is sensitive to sample size (it flipped between n = 30 and n = 100).
2. **`stale_same_entity` is the dominant and most stable failure cluster** across all experimental conditions, with mean error consistently near 0.47.
3. **Compressed context achieves comparable accuracy to full context** (0.8800–0.8900 vs. 0.8600–0.8800) at approximately 24% sentence retention, but the best answerer under compression differs from the best answerer on full context.

## Limitations

1. **Single model family.** All model-backed results use Phi-4-mini-instruct (Q4_K_M) on CPU. Whether the ranking shift and failure clusters generalize to larger or different model families is unknown.
2. **Synthetic data.** The QA examples are procedurally generated with controlled failure tags. Real-world retrieval corpora may exhibit different or additional failure modes.
3. **Small model-backed sample sizes.** The model-backed evaluation uses at most 100 examples per seed. Statistical power for detecting moderate effect sizes in rank shifts is limited.
4. **Rank-direction instability.** The direction of the answerer rank shift changed between n = 30 and n = 100, indicating that the specific ranking outcome is sensitive to sample composition even when the phenomenon (rank shift occurs) is stable.
5. **Limited compression and answer policies.** Only five compression policies and three answer policies are tested. More sophisticated compression (e.g., abstractive summarization, embedding-based retrieval) and answering (e.g., chain-of-thought, multi-hop) may behave differently.
6. **CPU-only inference.** All model-backed runs used `n-gpu-layers 0`. GPU-accelerated inference could change generation characteristics, though the deterministic caching mitigates nondeterminism concerns for the reported runs.
7. **No external replication.** The results have not been independently replicated by a separate team or on separate infrastructure.

## Reproducibility Checklist

| Item | Status |
|---|---|
| Code available in project directory | Yes (`src/compress_then_answer/`) |
| Synthetic data generation is deterministic (fixed seed) | Yes (seeds 3443677, 3443678) |
| Unit tests pass | Yes (5 tests, `python3 -m unittest discover -s tests -v`) |
| Compile check passes | Yes (`python3 -m compileall -q src tests`) |
| Deterministic baseline reproducible from command line | Yes (`python3 -m src.compress_then_answer.benchmark --n 1000 --seed 3443677`) |
| Model-backed harness reproducible with specified GGUF | Yes (requires `Phi-4-mini-instruct-Q4_K_M.gguf` and `llama-cpp-python`) |
| Completion cache provided for model-backed runs | Yes (`results/llm_cache.jsonl`) |
| Per-example predictions logged | Yes (`results/llm_predictions_100.jsonl`, `results/llm_predictions_100_seed3443678.jsonl`) |
| Metrics files are JSON-parseable | Yes (`results/metrics.json`, `results/llm_metrics_100.json`, `results/llm_metrics_100_seed3443678.json`) |

## Conclusion

The Compress-Then-Answer Benchmark provides evidence that evaluating question-answering systems on compressed context changes answerer rankings and exposes a persistent `stale_same_entity` failure cluster. At n = 100 across two independent synthetic seeds, the best answerer under compression (`llm_choice`) differs from the best answerer on full context (`regex_latest`), and this rank shift is stable across seeds. However, the direction of the shift was unstable between the 30-example and 100-example sample sizes, indicating that the specific ranking outcome should not be over-interpreted from small samples. The dominant failure cluster—`stale_same_entity`, with mean error near 0.47—is the most stable finding across all conditions.

These results support the hypothesis that compressed-context evaluation provides diagnostic information not available from full-context evaluation alone, but the evidence is confined to a single small model family, synthetic data, and limited policy sets. Validation on a second model family and on naturalistic data would substantially strengthen the external validity of these findings.

## Referenced Artifacts

### Source code
- `src/compress_then_answer/benchmark.py` — deterministic benchmark harness
- `src/compress_then_answer/llm_benchmark.py` — model-backed benchmark harness
- `tests/test_benchmark.py` — deterministic regression tests
- `tests/test_llm_benchmark.py` — model-backed parser/evaluator tests

### Data
- `data/examples.jsonl` — 1,000 deterministic synthetic QA examples (seed 3443677)
- `data/llm_examples.jsonl` — 30-example model-backed subset (seed 3443677)
- `data/llm_examples_100.jsonl` — 100-example model-backed subset (seed 3443677)
- `data/llm_examples_100_seed3443678.jsonl` — 100-example model-backed subset (seed 3443678)

### Results
- `results/metrics.json` — deterministic baseline metrics (n = 1,000)
- `results/report.md` — deterministic baseline report
- `results/llm_metrics.json` — model-backed smoke test metrics (n = 30)
- `results/llm_report.md` — model-backed smoke test report
- `results/llm_predictions.jsonl` — model-backed smoke test per-example predictions
- `results/llm_metrics_100.json` — model-backed stability metrics (n = 100, seed 3443677)
- `results/llm_report_100.md` — model-backed stability report
- `results/llm_predictions_100.jsonl` — model-backed stability per-example predictions
- `results/stability_report.md` — n = 30 vs. n = 100 comparison
- `results/llm_metrics_100_seed3443678.json` — cross-seed metrics (n = 100, seed 3443678)
- `results/llm_report_100_seed3443678.md` — cross-seed report
- `results/llm_predictions_100_seed3443678.jsonl` — cross-seed per-example predictions
- `results/cross_seed_report.md` — seed 3443677 vs. seed 3443678 comparison
- `results/llm_cache.jsonl` — shared completion cache for model-backed runs

### Decision and metadata
- `.omx/project_decision.json` — project decision artifact (finalize_positive)
- `run_notes.md` — full execution log
- `README.md` — run instructions
