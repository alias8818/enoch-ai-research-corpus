# Answer-Shape Prompt Planner: Budget-Aware Prompt Packing Guided by Predicted Answer Structure

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We present Answer-Shape Prompt Planner, a method that predicts the structural shape of a desired answer (e.g., JSON object, bullet list, citation-supported paragraph) and uses that prediction to rank and pack retrieved document chunks into a fixed-token-budget prompt. Across four progressively realistic evaluation tiers—synthetic oracle-proxy scoring, synthetic generated-answer scoring with query paraphrases, non-synthetic SQuAD/Wikipedia retrieval with a deterministic extractive reader, and live local-LLM inference with Qwen2.5-0.5B and Qwen2.5-1.5B—the planner consistently achieves higher answer quality than a uniform truncation baseline at the same or lower token budget. The strongest live-model result (Qwen2.5-1.5B, 14 tasks) shows a +36.31-point answer-quality gain with 6.80% fewer prompt tokens. However, JSON exact match remains at 0.0000 for both planner and baseline across all live-LLM runs, citation support is modest (0.2143 vs. 0.0714), and planner construction latency is higher than the baseline. These mixed-format results indicate that answer-shape-aware packing improves evidence selection but does not by itself enforce output format compliance. The current project artifacts support this finding in the tested setting; the method is not validated on larger models, broader corpora, or production workloads.

---

## 1. Introduction

Retrieval-augmented generation (RAG) systems typically pack retrieved document chunks into a language-model prompt under a token budget, most commonly by truncating the ranked list uniformly once the budget is exhausted. This approach ignores the structural requirements of the intended answer: a JSON extraction task benefits from chunks containing field names and typed values, while a citation-supported paragraph task benefits from chunks with attributable claims. A packing strategy that accounts for the predicted answer shape could allocate the token budget more effectively, retaining higher-evidence chunks relevant to the expected output structure.

We investigate the following hypothesis: *prompt packing that is informed by the predicted answer shape yields higher answer quality at equal or lower token cost than uniform truncation.* We test this hypothesis through a dependency-free offline implementation and a sequence of four evaluation tiers of increasing realism, culminating in live inference with locally served language models on SQuAD-derived retrieval tasks.

The contributions of this work are:

1. A simple, deterministic answer-shape prediction and shape-aware chunk-ranking/packing algorithm with no external dependencies.
2. A progressive evaluation methodology spanning oracle-proxy metrics, generated-answer scoring, deterministic extractive reading, and live LLM inference.
3. Empirical evidence that answer-shape-aware packing improves answer quality across all four tiers, alongside honest reporting of cases where the method does not improve format compliance.

---

## 2. Method

### 2.1 Answer-Shape Prediction

The planner accepts or predicts one of several answer shapes: `json_object`, `bullet_list`, `citation_paragraph`, `repo_qa`, and `contract_extraction`. Shape prediction uses query-derived heuristics (keyword matching and structural cues in the query text). The predicted shape determines which salience features weight chunk and sentence selection.

### 2.2 Shape-Aware Chunk Ranking

Given a query $q$, a set of retrieved chunks $C = \{c_1, \ldots, c_n\}$, and a predicted answer shape $s$, the planner computes a ranking score for each chunk as:

$$\text{score}(c_i) = \alpha \cdot \text{query\_term\_overlap}(c_i, q) + (1 - \alpha) \cdot \text{shape\_salience}(c_i, s)$$

where `query_term_overlap` measures the fraction of query-derived terms present in the chunk, and `shape_salience` assigns higher weight to chunks containing structural markers relevant to shape $s$ (e.g., curly braces and key-value patterns for `json_object`, attribution phrases for `citation_paragraph`). The parameter $\alpha$ balances query relevance against shape relevance.

An earlier version of the packer used gold-label `required_terms` for ranking, which constituted an oracle leak. This was removed; the current implementation derives ranking terms solely from the query via `query_terms()`, and a regression test confirms that gold answer values are not included as ranking terms.

### 2.3 Budget-Constrained Packing

Chunks are sorted by descending score and packed into the prompt until the declared token budget is reached. Partial chunks are truncated at sentence boundaries when possible. The resulting prompt is prefixed with shape-specific instructions (e.g., "Respond in valid JSON with fields X, Y, Z" for `json_object`).

### 2.4 Baseline: Uniform Truncation

The uniform truncation baseline ranks chunks by query-term overlap alone (no shape salience) and packs them in order until the budget is exhausted. This represents a standard RAG packing strategy.

---

## 3. Results

We report results across four evaluation tiers. Each tier increases realism by replacing oracle signals with generated outputs and by moving from synthetic corpora to public data with live model inference.

### 3.1 Tier 1: Offline Synthetic Benchmark (Oracle-Proxy Scoring)

The initial benchmark used five deterministic synthetic cases (JSON extraction, bullet summary, citation answer, repo-QA, contract extraction) with an evidence-retention F1 proxy as the quality metric. This tier measures how well the planner preserves required evidence, not actual answer quality.

| Metric | Planner | Uniform | Delta |
|--------|---------|---------|-------|
| Mean answer-F1 proxy | 0.8333 | 0.2300 | +60.33 |
| Mean prompt tokens | 122.6 | 156.0 | −21.41% |
| Equal-or-better-quality token saving | 49.40% | — | — |
| Mean construction latency | 0.365 ms | 0.151 ms | +0.214 ms |

The planner retained substantially more required evidence with fewer tokens. However, the F1 proxy is an oracle metric computed against gold evidence labels, not against model-generated answers.

### 3.2 Tier 2: Synthetic Answer-Quality Benchmark (Generated Answers)

To move beyond oracle proxies, a second benchmark fed packed prompts into a shape-aware extractive reader that produces actual answer text. The benchmark swept across five budgets and 15 query paraphrases, scoring field exact match, fact F1, and citation support.

| Metric | Planner | Uniform | Delta |
|--------|---------|---------|-------|
| Declared-budget answer quality | 0.7022 | 0.2300 | +47.22 |
| Declared-budget prompt tokens | 130.93 | 156.0 | −16.07% |
| Budget-sweep mean answer quality | 0.7264 | 0.1840 | +54.24 |
| Predicted-shape planner mean quality | 0.7371 | — | — |

The predicted-shape planner (which does not receive the true shape) achieved 0.7371, close to the expected-shape planner's 0.7264, suggesting the simple shape predictor did not collapse under the included paraphrases. Evidence remains moderate because the reader is deterministic and extractive, and the corpus is synthetic.

### 3.3 Tier 3: Non-Synthetic RAG Benchmark (SQuAD, Deterministic Reader)

A real-data benchmark was constructed from SQuAD dev v1.1 Wikipedia contexts with 10 retrieval tasks, scored by JSON exact match, field F1, citation support, prompt tokens, and latency. The answerer was a deterministic extractive reader (no LLM).

| Metric | Planner | Uniform | Delta |
|--------|---------|---------|-------|
| Answer quality | 0.8833 | 0.0000 | +88.33 |
| Prompt tokens | 120.50 | 131.00 | −8.02% |
| Field F1 | 0.9333 | 0.0000 | +93.33 |
| JSON exact match | 0.0000 | 0.0000 | 0.00 |
| Citation support | 0.9000 | 0.1000 | +80.00 |
| Total latency | 0.294 ms | 0.123 ms | +0.171 ms |

The planner achieved a large quality gain, but the uniform baseline scoring 0.0000 on this slice indicates an extreme difficulty mismatch for unshaped packing. JSON exact match was 0.0000 for both methods, showing that even correct evidence selection does not guarantee format compliance from an extractive reader.

### 3.4 Tier 4: Live LLM Inference (Qwen2.5-0.5B-Instruct)

The benchmark harness was extended with an OpenAI-compatible `/chat/completions` hook. Qwen2.5-0.5B-Instruct was served locally via vLLM on 14 SQuAD/Wikipedia tasks.

| Metric | Planner | Uniform | Delta |
|--------|---------|---------|-------|
| Answer quality | 0.0595 | 0.0000 | +5.95 |
| Prompt tokens | 120.50 | 129.29 | −6.80% |
| Field F1 | 0.0952 | 0.0000 | +9.52 |
| JSON exact match | 0.0000 | 0.0000 | 0.00 |
| Citation support | 0.0714 | 0.0714 | 0.00 |
| Total latency | 385.49 ms | 401.38 ms | −15.89 ms |
| Answer latency p50 / p95 | 363.71 / 941.23 ms | — | — |
| Completion throughput | 165.56 tok/s | — | — |
| GPU utilization | 96% | — | — |
| Server RSS / PSS | 3582 / 3239 MB | — | — |

This run barely cleared the ≥5-point quality-gain threshold. Absolute answer quality was low, and citation support was identical for both methods. The small model's limited instruction-following capacity is a likely confound.

### 3.5 Tier 4 (continued): Live LLM Inference (Qwen2.5-1.5B-Instruct)

To disambiguate model-capacity effects from packing effects, the same benchmark was run with Qwen2.5-1.5B-Instruct served via vLLM (`--max-model-len 2048`, `--gpu-memory-utilization 0.35`) on the same 14-task slice.

| Metric | Planner | Uniform | Delta |
|--------|---------|---------|-------|
| Answer quality | 0.3690 | 0.0060 | +36.31 |
| Prompt tokens | 120.50 | 129.29 | −6.80% |
| Field F1 | 0.5476 | 0.0119 | +53.57 |
| JSON exact match | 0.0000 | 0.0000 | 0.00 |
| Citation support | 0.2143 | 0.0714 | +14.29 |
| Total latency | 780.70 ms | 725.96 ms | +54.74 ms |
| Answer latency p50 / p95 | 658.66 / 1962.24 ms | — | — |
| Completion throughput | 55.75 tok/s | — | — |
| GPU utilization | 95% | — | — |
| Server RSS / PSS | 3800 / 3457 MB | — | — |

The stronger model produced a substantially larger quality gain (+36.31 points) with the same 6.80% token reduction. Field F1 improved from 0.0119 to 0.5476, and citation support improved from 0.0714 to 0.2143. However, JSON exact match remained at 0.0000 for both methods, and the planner's total latency was 54.74 ms higher than the baseline.

### 3.6 Summary Across Tiers

| Tier | Planner Quality | Uniform Quality | Quality Delta | Token Reduction |
|------|----------------|----------------|---------------|-----------------|
| Synthetic oracle-proxy | 0.8333 | 0.2300 | +60.33 | 21.41% |
| Synthetic generated-answer | 0.7022 | 0.2300 | +47.22 | 16.07% |
| SQuAD deterministic | 0.8833 | 0.0000 | +88.33 | 8.02% |
| SQuAD Qwen2.5-0.5B | 0.0595 | 0.0000 | +5.95 | 6.80% |
| SQuAD Qwen2.5-1.5B | 0.3690 | 0.0060 | +36.31 | 6.80% |

The quality gain is consistent in direction across all tiers but shrinks in absolute magnitude as evaluation realism increases. Token reduction is consistent but modest (6.80–21.41%), decreasing as the evaluation moves to real data and live models.

---

## 4. Limitations

1. **Small and narrow task slices.** All live-LLM evaluations used 10–14 tasks derived from SQuAD dev v1.1 Wikipedia contexts. This sample is too small to support generalization to broader RAG workloads, domains, or query distributions.

2. **JSON exact match is zero across all live-LLM runs.** Neither the planner nor the baseline achieved any JSON exact match with live models. This indicates that answer-shape-aware packing improves evidence selection but does not by itself enforce output format compliance. Format control may require complementary techniques (constrained decoding, format-specific prompting, or fine-tuning).

3. **Citation support remains low.** Even with the 1.5B model, planner citation support was only 0.2143. The planner selects more citation-relevant evidence, but the model frequently fails to format citations correctly.

4. **Modest token reduction in realistic settings.** Token savings ranged from 6.80% to 8.02% on real-data benchmarks, compared to 16–21% on synthetic benchmarks. The real-data tasks may have shorter or more homogeneous retrieved chunks, leaving less room for shape-aware reallocation.

5. **Planner construction latency overhead.** The planner adds ranking and packing overhead (0.214 ms in the synthetic benchmark; 54.74 ms additional total latency in the 1.5B live run). While small relative to LLM inference latency, this overhead is consistently positive and may matter in latency-sensitive deployments.

6. **Model scale ceiling.** The largest model tested was Qwen2.5-1.5B-Instruct. Behavior at larger model scales (7B, 14B, 70B+) is unknown. It is plausible that stronger instruction-following would amplify the planner's gains or render shape-aware packing less necessary.

7. **Deterministic extractive reader inflates Tier 3 gains.** The 88.33-point quality gain in the deterministic SQuAD benchmark reflects the extractive reader's dependence on evidence ordering and selection rather than model reasoning. This tier should be interpreted as a packing-quality signal, not an answer-quality signal.

8. **Single retrieval corpus.** All non-synthetic results use SQuAD dev v1.1 Wikipedia contexts. Performance on other corpora (legal, medical, code) is untested.

9. **No human evaluation.** All metrics are automated (F1, exact match, citation support). Human preference or usability judgments were not collected.

---

## 5. Reproducibility Checklist

- **Code availability:** The implementation is contained in `src/answer_shape_prompt_planner.py` (dependency-free, Python stdlib only). Benchmark scripts are in `experiments/run_offline_benchmark.py`, `experiments/run_answer_quality_benchmark.py`, and `experiments/run_real_rag_benchmark.py`.
- **Unit tests:** `tests/test_planner.py` (4 tests, all passing as of the final run).
- **Deterministic benchmarks:** All three benchmark scripts produce deterministic results when run without the `--llm-base-url` flag. Commands: `python3 experiments/run_offline_benchmark.py --out results/offline_benchmark.json`; `python3 experiments/run_answer_quality_benchmark.py --out results/answer_quality_benchmark.json`; `python3 experiments/run_real_rag_benchmark.py --out results/real_rag_benchmark.json --max-tasks 12`.
- **Live-LLM benchmarks:** Require a locally served OpenAI-compatible endpoint. The Qwen2.5-1.5B run used vLLM with `--max-model-len 2048 --gpu-memory-utilization 0.35`. Command: `python3 experiments/run_real_rag_benchmark.py --out results/real_rag_benchmark_llm_qwen15b.json --max-tasks 16 --llm-base-url http://127.0.0.1:18001/v1 --llm-model qwen2.5-1.5b-instruct`.
- **Data:** SQuAD dev v1.1 is downloaded and cached automatically at `data/squad-dev-v1.1.json`.
- **Result artifacts:** All benchmark outputs are persisted as JSON and Markdown in the `results/` directory (see Referenced Artifacts).
- **Compilation check:** `python3 -m py_compile` passed for all source and experiment files.
- **Randomness control:** Synthetic benchmarks are deterministic. Live-LLM benchmarks depend on model sampling; exact numerical reproduction requires fixed seeds and model configuration.

---

## 6. Conclusion

Answer-Shape Prompt Planner demonstrates that informing prompt packing with the predicted structural shape of the desired answer consistently improves answer quality over uniform truncation across four evaluation tiers of increasing realism. The strongest live-model evidence (Qwen2.5-1.5B, 14 SQuAD tasks) shows a +36.31-point answer-quality gain with 6.80% fewer prompt tokens. However, the method does not improve JSON exact match (0.0000 for both planner and baseline), citation support remains modest, token savings are small on real data, and planner latency is higher. The current project artifacts support the finding that answer-shape-aware packing improves evidence selection in the tested setting; the method is not validated on larger models, broader corpora, or production workloads. Format control and larger-model scaling should be investigated as a separate follow-on study.

---

## Referenced Artifacts

### Result files
- `results/real_rag_benchmark_llm_qwen15b.md`
- `results/real_rag_benchmark_llm_qwen15b.json`
- `results/answer_quality_benchmark.md`
- `results/answer_quality_benchmark.json`
- `results/offline_benchmark.json`
- `results/real_rag_benchmark_llm_qwen05b.md`
- `results/real_rag_benchmark_llm_qwen05b.json`
- `results/real_rag_benchmark.md`
- `results/real_rag_benchmark.json`
- `results/offline_benchmark.md`

### Source and experiment files
- `src/answer_shape_prompt_planner.py`
- `experiments/run_offline_benchmark.py`
- `experiments/run_answer_quality_benchmark.py`
- `experiments/run_real_rag_benchmark.py`
- `tests/test_planner.py`

### Data
- `data/squad-dev-v1.1.json`

### Project metadata and decision artifacts
- `run_notes.md`
- `README.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`
- `prompts/initial.md`
- `prompts/resume.md`

### Paper-specific artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
