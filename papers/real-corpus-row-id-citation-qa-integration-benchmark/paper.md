# Real-Corpus Row-ID Citation QA Integration Benchmark

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has approved this content.

---

## Abstract

We investigate whether table-aware context packing with row-ID citation surfaces enables instruction-tuned language models to answer table-QA questions while correctly citing the source rows, compared to source-order packing. We construct a benchmark from the public WikiSQL validation set, converting SQL supervision into row-ID citation targets requiring both correct answers and exact row citations in structured JSON output. Across an offline oracle ceiling, Phi-4-mini-instruct (Q4_K_M), and Qwen2.5-7B-Instruct (Q4_K_M) under llama.cpp JSON-schema grammar, table-aware packing yields large answer+citation gains over source-order packing at all tested context budgets (120, 200, 320 lexical tokens). Source-order packing scores 0.000 answer+citation at every budget and reader configuration. Table-aware packing reaches 0.875 answer+citation under the oracle and under schema-constrained Qwen2.5, and 0.250–0.500 under Phi-4-mini depending on budget. However, Qwen2.5 without grammar-constrained decoding produced 0.000 schema validity, and the oracle ceiling itself is 0.875 rather than 1.000 due to a lexical-ranking edge case. The benchmark comprises only 8 cases from a single corpus, and results are limited to two quantized models on local CUDA hardware. These findings support the row-ID citation packing hypothesis in the tested setting but do not establish generalizability.

## 1. Introduction

Table question answering requires models to extract answers from structured data and, increasingly, to cite the specific rows supporting those answers. A practical citation mechanism must expose canonical row identifiers in the model's context and score whether the model's output references the correct rows alongside correct answers.

The central question is whether table-aware context packing—where rows are arranged to retain target rows within a lexical context budget—produces measurable gains in answer correctness and row citation compared to source-order packing, where rows appear in their original sequence and target rows may fall outside the context window.

We report results from a benchmark built on the public WikiSQL validation set, using SQL equality supervision to derive gold row-ID citation targets. We test three reader configurations: an offline oracle, Phi-4-mini-instruct served via llama.cpp, and Qwen2.5-7B-Instruct served via llama.cpp with and without JSON-schema grammar constraints. We measure answer+citation accuracy, row recall, schema validity, and serving latency/utilization.

## 2. Method

### 2.1 Benchmark Construction

The benchmark script (`scripts/real_corpus_rowid_citation_benchmark.py`) downloads and caches the WikiSQL validation parquet from Hugging Face and persists a compact fixture (`data/wikisql_rowid_citation_cases.json`). From this corpus, 8 cases are selected where the gold SQL query uses equality conditions on a single column. For each case, the benchmark derives:

- A **gold answer**: the cell value matching the SQL condition.
- A **gold citation**: the canonical row ID `WSQLxxx.rN` for the row satisfying the SQL condition, where `N` is the row index.

Each case is packed under two linearization strategies from `src/table_linearizer.py`:

- **Source-order packing**: rows appear in their original table order. Target rows may fall outside the lexical context budget.
- **Table-aware packing**: rows are arranged so that target rows are retained within the lexical context budget.

Both packers use the `citation_surface=row_id_only` setting, exposing canonical `citation_id=WSQLxxx.rN` values in the context.

### 2.2 Scoring

A response is scored as correct on **answer+citation** only if:

1. The output is parseable JSON containing `answer` (string) and `citations` (array of strings) fields.
2. The `answer` field contains the expected answer text.
3. The `citations` array includes the exact gold row ID.

**Row recall** measures whether the gold row ID appears in the context provided to the model, independent of the model's output. **Schema validity** measures whether the model's output is parseable JSON with the required fields, regardless of answer or citation correctness.

### 2.3 Context Budgets

Three lexical context token budgets are tested: 120, 200, and 320 tokens. These budgets are intentionally tight to stress the packing mechanism and create conditions where source-order packing may exclude target rows.

### 2.4 Reader Configurations

**Offline oracle.** The oracle directly inspects the packed context to determine whether the gold row is present and whether the answer is recoverable. This establishes a packing-retention ceiling independent of any model's generation capability.

**Phi-4-mini-instruct (Q4_K_M).** Served via llama.cpp (`build-local-cuda`) on local CUDA hardware. The model is prompted to produce JSON output with `answer` and `citations` fields. No grammar constraint is applied; the parser handles Markdown JSON fences.

**Qwen2.5-7B-Instruct (Q4_K_M) — unconstrained.** Served via the same llama.cpp CUDA stack with `--chat-template chatml`. No grammar constraint is applied. This configuration produced malformed JSON and is reported as a negative result.

**Qwen2.5-7B-Instruct (Q4_K_M) — schema-constrained.** Served via llama.cpp with `--chat-template chatml` and `--json-schema-file` grammar enforcing the `{answer: string, citations: string[]}` schema. This configuration produced valid JSON output.

## 3. Results

### 3.1 Offline Oracle Ceiling

| Budget | Packing      | Answer+Citation | Row Recall |
|--------|-------------|-----------------|------------|
| 120    | Source-order | 0.000           | 0.000      |
| 120    | Table-aware  | 0.875           | 0.875      |
| 200    | Source-order | 0.000           | 0.000      |
| 200    | Table-aware  | 0.875           | 0.875      |
| 320    | Source-order | 0.000           | 0.000      |
| 320    | Table-aware  | 0.875           | 0.875      |

Source-order packing retains zero target rows at any budget. Table-aware packing retains 7 of 8 target rows (0.875) at all budgets. The single miss is a lexical-ranking/selection edge case in the WikiSQL fixture, so the benchmark is not saturated even at the oracle level.

### 3.2 Phi-4-mini-instruct

| Budget | Packing      | Answer+Citation | Row Recall | Schema Validity |
|--------|-------------|-----------------|------------|-----------------|
| 120    | Source-order | 0.000           | 0.000      | —               |
| 120    | Table-aware  | 0.250           | 0.875      | 0.875           |
| 200    | Source-order | 0.000           | 0.000      | —               |
| 200    | Table-aware  | 0.375           | 0.875      | 1.000           |
| 320    | Source-order | 0.000           | 0.000      | —               |
| 320    | Table-aware  | 0.500           | 0.875      | 0.875           |

Phi-4-mini shows a clear table-aware gain, increasing with budget from +25.0 to +50.0 points over source-order. However, it does not reach the oracle ceiling of 0.875. Schema validity is imperfect (0.875–1.000), primarily due to Markdown JSON fencing or malformed compact JSON in some outputs. Row recall is 0.875 throughout, confirming that the packing mechanism retains the target rows; the gap between row recall and answer+citation reflects model generation errors rather than packing failures.

**Latency and utilization.** 48 requests; mean latency 378.6 ms, p50 373.6 ms, p95 456.8 ms. Mean GPU utilization 85.0%, p95 95.0%. p95 RSS 1.28 GB. Final UMA `MemAvailable=118669352 kB`, `SwapFree=0 kB`.

### 3.3 Qwen2.5-7B-Instruct — Unconstrained (Negative Result)

| Budget | Packing      | Answer+Citation | Row Recall | Schema Validity |
|--------|-------------|-----------------|------------|-----------------|
| 120    | Source-order | 0.000           | 0.000      | 0.000           |
| 120    | Table-aware  | 0.000           | 0.875      | 0.000           |
| 200    | Source-order | 0.000           | 0.000      | 0.000           |
| 200    | Table-aware  | 0.000           | 0.875      | 0.000           |
| 320    | Source-order | 0.000           | 0.000      | 0.000           |
| 320    | Table-aware  | 0.000           | 0.875      | 0.000           |

Qwen2.5 without grammar constraints produced malformed or degenerate JSON-like text (e.g., `{"answer4": ...}`) under both prompt-only and `response_format=json_object` attempts. Schema validity was 0.000 across all conditions. This is a serving/decoding configuration failure rather than a packing failure: table-aware packing still retained 0.875 row recall, but the model could not emit parseable JSON.

**Latency and utilization.** 48 requests; mean latency 1304.2 ms, p50 1019.8 ms, p95 2494.1 ms. Mean GPU utilization 88.2%, p95 96.0%. p95 RSS 982 MB. Final UMA `MemAvailable=117039204 kB`, `SwapFree=0 kB`.

### 3.4 Qwen2.5-7B-Instruct — Schema-Constrained

| Budget | Packing      | Answer+Citation | Row Recall | Schema Validity |
|--------|-------------|-----------------|------------|-----------------|
| 120    | Source-order | 0.000           | 0.000      | 1.000           |
| 120    | Table-aware  | 0.875           | 0.875      | 1.000           |
| 200    | Source-order | 0.000           | 0.000      | 1.000           |
| 200    | Table-aware  | 0.875           | 0.875      | 1.000           |
| 320    | Source-order | 0.000           | 0.000      | 1.000           |
| 320    | Table-aware  | 0.875           | 0.875      | 1.000           |

With llama.cpp JSON-schema grammar enforcement, Qwen2.5 achieves 1.000 schema validity and matches the oracle ceiling of 0.875 answer+citation at all budgets. The +87.5 point gain over source-order is consistent across all three budgets.

**Latency and utilization.** 48 requests in 33.22 s wall-clock (~1.45 requests/s); mean latency 690.3 ms, p50 630.4 ms, p95 1489.2 ms. Mean GPU utilization 89.7%, p95 95.0%. p95 RSS 1.61 GB. Final UMA `MemAvailable=116187580 kB`, `SwapFree=0 kB`.

### 3.5 Summary of Gains

| Reader              | Max Answer+Citation (Table-Aware) | Source-Order | Gain (points) |
|---------------------|-----------------------------------|-------------|---------------|
| Oracle              | 0.875                             | 0.000       | +87.5         |
| Phi-4-mini          | 0.500 (budget 320)                | 0.000       | +50.0         |
| Qwen2.5 (unconstr.) | 0.000                             | 0.000       | 0.0           |
| Qwen2.5 (schema)    | 0.875                             | 0.000       | +87.5         |

## 4. Limitations

1. **Small benchmark size.** Only 8 cases from the WikiSQL validation set are used. Statistical power is limited, and results may not generalize to the full WikiSQL corpus or other table-QA datasets.

2. **Single corpus.** All cases derive from WikiSQL, which uses relatively simple equality-condition SQL queries. Performance on more complex SQL (aggregations, joins, multi-condition queries) is untested.

3. **Oracle ceiling not saturated.** The oracle itself achieves only 0.875 answer+citation due to a lexical-ranking edge case. The benchmark does not test whether table-aware packing can achieve perfect recall on a saturated fixture.

4. **Model coverage.** Only two quantized GGUF models (Phi-4-mini-instruct Q4_K_M and Qwen2.5-7B-Instruct Q4_K_M) are tested. Results may differ for full-precision models, larger models, or models from different families.

5. **Grammar constraint dependency.** Qwen2.5 required llama.cpp JSON-schema grammar enforcement to produce valid output. Without this constraint, it scored 0.000 schema validity. This raises questions about whether the citation gains reflect packing quality or serving-stack configuration. The Phi-4-mini results (which did not require grammar constraints) partially address this concern, but Phi-4-mini did not reach the oracle ceiling.

6. **Hardware specificity.** All runs were conducted on a single local CUDA machine with unified memory architecture (UMA). Latency and utilization metrics are not portable to other hardware configurations.

7. **No comparison to alternative citation methods.** The benchmark tests only the `row_id_only` citation surface. Other citation mechanisms (e.g., cell-level citations, natural language attributions) are not evaluated.

8. **Tight context budgets.** The budgets (120–320 tokens) are intentionally constrained. At larger budgets, source-order packing may retain target rows, potentially reducing or eliminating the table-aware advantage.

## 5. Reproducibility Checklist

- **Benchmark script:** `scripts/real_corpus_rowid_citation_benchmark.py`
- **Table linearizer:** `src/table_linearizer.py`
- **Cached fixture:** `data/wikisql_rowid_citation_cases.json`
- **Source corpus:** WikiSQL validation parquet, cached at `data/cache/wikisql_validation.parquet`
- **Models:** `lmstudio-community/Phi-4-mini-instruct-Q4_K_M.gguf`, `bartowski/Qwen2.5-7B-Instruct-Q4_K_M.gguf`
- **Serving stack:** llama.cpp `build-local-cuda` with `--chat-template chatml`; schema-constrained runs add `--json-schema-file`
- **Python validation:** `.venv/bin/python -m py_compile scripts/*.py src/*.py` passed
- **Helper server lifecycle:** llama.cpp server started, `/v1/models` verified, server stopped before yielding; `pgrep` confirmed no residual processes
- **All result files persisted** (see Referenced Artifacts)

## 6. Conclusion

Table-aware context packing with row-ID citation surfaces produces substantial answer+citation gains over source-order packing on the tested WikiSQL row-ID citation benchmark. Source-order packing scored 0.000 answer+citation at every budget and reader configuration because target rows were excluded from the context window. Table-aware packing retained 0.875 row recall and, when the reader emitted valid JSON, achieved up to 0.875 answer+citation (matching the oracle ceiling under schema-constrained Qwen2.5) or 0.250–0.500 (under unconstrained Phi-4-mini).

The Qwen2.5 unconstrained failure (0.000 schema validity despite 0.875 row recall) is a negative result that highlights the dependency of citation QA on reliable structured output generation. Grammar-constrained decoding resolved this failure, but introduces an additional serving requirement.

These findings support the row-ID citation packing hypothesis in the tested setting. However, the small benchmark size (8 cases), single corpus, limited model coverage, and grammar-constraint dependency substantially bound the strength of the conclusion. Replication on larger corpora with additional models and serving configurations is necessary before drawing broader claims.

## Referenced Artifacts

### Project-local source files
- `scripts/real_corpus_rowid_citation_benchmark.py`
- `src/table_linearizer.py`
- `data/wikisql_rowid_citation_cases.json`
- `data/cache/wikisql_validation.parquet`
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Oracle result files
- `results/real_corpus_rowid_citation_summary_oracle.md`

### Phi-4-mini result files
- `results/real_corpus_rowid_citation_summary_phi.md`
- `results/phi_real_corpus_benchmark_metrics.json`
- `results/real_corpus_phi_time.txt`

### Qwen2.5 unconstrained result files
- `results/real_corpus_rowid_citation_summary_qwen.md`
- `results/real_corpus_rowid_citation_results_qwen.json`
- `results/qwen_real_corpus_benchmark_metrics.json`
- `results/qwen_real_corpus_server_monitor.jsonl`
- `results/real_corpus_qwen_time.txt`
- `results/real_corpus_qwen_stdout.json`
- `results/qwen_models.json`

### Qwen2.5 schema-constrained result files
- `results/real_corpus_rowid_citation_summary_qwen_schema.md`
- `results/real_corpus_rowid_citation_results_qwen_schema.json`
- `results/qwen_schema_real_corpus_benchmark_metrics.json`
- `results/qwen_schema_real_corpus_server_monitor.jsonl`
- `results/real_corpus_qwen_schema_time.txt`
- `results/real_corpus_qwen_schema_stdout.json`
- `results/qwen_schema_llama_server.log`
- `results/qwen_schema_llama_stdout.log`
- `results/qwen_schema_models.json`
- `results/qwen_schema_simple_test.json`

### Paper and audit artifacts
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
