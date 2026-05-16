# Real-Task Context Compression Pareto Validation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

We evaluate whether context compression strategies for retrieval-augmented generation (RAG) exhibit budget-dependent Pareto rankings and systematic failure modes when assessed on real-task answer quality rather than context-retention proxies. Using SQuAD v1.1 dev questions paired with Wikipedia distractor paragraphs to form long RAG contexts, we compare five compression families—prefix truncation, random sentence selection, keyword-overlap selection, answer-aware oracle selection, and full context—across four token budgets (96, 192, 384, 768). Deterministic extractive EM/F1 evaluation over 180 examples confirms that (1) Pareto ranking shifts with budget: at 768 tokens, full context overtakes the answer-aware oracle, unlike at tighter budgets; (2) prefix truncation exhibits a durable late-evidence failure mode that persists even at 768 tokens; and (3) answer-aware compression outperforms prefix truncation by +79.2 F1 at 96 tokens, declining to +35.9 F1 at 768 tokens. A stratified 25-row LLM judge sample corroborates the directional findings. Evidence strength is moderate: the LLM judge sample is small, and the evaluation is confined to a single dataset with deterministic metrics. The saved prediction artifacts are prepared for larger-scale LLM or human adjudication.

---

## 1. Introduction

Context compression—reducing the token length of retrieved or provided context before passing it to a language model—is a practical necessity when operating under inference cost or context-window constraints. Prior synthetic-benchmark evaluations have suggested that the relative quality of compression strategies depends on the available token budget, and that naive prefix truncation systematically fails when answer-bearing evidence appears late in the context. However, synthetic benchmarks may not reflect the distribution of evidence positions, distractor quality, or answer types encountered in real retrieval-augmented generation tasks.

This study asks whether the budget-dependent Pareto structure and late-evidence failure mode observed in synthetic settings persist under real-task answer-quality evaluation. We construct a validation harness using SQuAD v1.1 dev questions, augment each with real Wikipedia distractor paragraphs to simulate long RAG contexts, and evaluate compression strategies using extractive answer-quality metrics (exact match and token-level F1) rather than binary context-retention proxies.

The project was governed by a pre-registered branch kill condition: finalize-negative if real-task evaluation shows no Pareto ranking shifts across budgets and no recurring late-evidence failure cluster for prefix truncation; finalize-positive if at least one real dataset shows budget-dependent ranking or the late-evidence cluster persists. The kill condition was not met, yielding a finalize-positive decision with moderate evidence strength.

---

## 2. Method

### 2.1 Task Construction

We assemble RAG-style long contexts from SQuAD v1.1 dev. For each question, the gold answer paragraph is retained and 10 distractor paragraphs (drawn from other SQuAD Wikipedia articles) are appended, producing contexts substantially longer than any single compression budget. This construction preserves real-world properties: genuine lexical overlap between distractors and questions, varied answer types, and non-uniform evidence positioning within the context.

### 2.2 Compression Strategies

Five compression families are evaluated:

1. **Prefix truncation** — Retain the first *B* tokens of the context.
2. **Random sentence selection** — Randomly sample sentences until the token budget is met.
3. **Keyword-overlap selection** — Rank sentences by token overlap with the question and select top sentences within budget.
4. **Answer-aware oracle** — Rank sentences by overlap with the gold answer and select top sentences within budget. This represents an upper bound on retrieval-informed compression.
5. **Full context** — No compression; the entire context is provided (may exceed budget for comparison purposes).

### 2.3 Budgets

Token budgets of 96, 192, 384, and 768 are evaluated. These span the range from aggressively compressed (approximately 1–2 paragraphs) to moderately compressed (several paragraphs).

### 2.4 Evaluation

The primary evaluation uses deterministic extractive answer quality: exact match (EM) and token-level F1 between the model's extracted answer span and the SQuAD gold answer. This measures whether the compressed context still supports correct answer extraction, rather than merely whether the gold paragraph is retained.

A supplementary LLM judge evaluation was conducted on a stratified sample of 25 prediction rows, using Claude CLI with an answer-quality judging prompt. This sample was designed to verify that the deterministic metrics are directionally consistent with a more holistic quality assessment.

### 2.5 Failure Mode Analysis

For prefix truncation, we classify each failure by the position of the gold answer span within the original context: *early* (first third), *middle* (second third), or *late* (final third). This directly tests whether late-evidence failures observed in synthetic benchmarks persist on real RAG contexts.

---

## 3. Results

### 3.1 Budget-Dependent Pareto Ranking

Ranking changes across budgets were observed (`ranking_changes_across_budgets = 1`). At budgets of 96, 192, and 384 tokens, the answer-aware oracle ranked at or near the top. At 768 tokens, full context overtook the answer-aware oracle in ranking. This shift is consistent with a Pareto frontier that depends on the cost–quality tradeoff: when the budget is generous enough to include most relevant content, the overhead of oracle selection provides diminishing returns relative to simply providing the full context.

### 3.2 Late-Evidence Failure Mode

Prefix truncation exhibited a persistent late-evidence failure mode across all budgets:

| Budget | Early | Middle | Late |
|--------|-------|--------|------|
| 96     | 39    | 50     | 54   |
| 768    | —     | —      | 51   |

At 96 tokens, late-position failures (54) exceeded early-position failures (39) by 15 cases. Even at 768 tokens, late evidence remained the top prefix failure category (51 cases). This confirms that the late-evidence failure cluster is not an artifact of synthetic benchmarks but persists on real RAG contexts with naturally distributed evidence positions.

### 3.3 Answer-Aware Compression Advantage

Targeted answer-aware compression substantially outperformed prefix truncation on F1:

| Budget (tokens) | F1 Advantage over Prefix |
|------------------|--------------------------|
| 96               | +79.213                  |
| 192              | +68.519                  |
| 384              | +52.756                  |
| 768              | +35.904                  |

The advantage decreases as the budget increases—consistent with the interpretation that prefix truncation recovers more of the relevant context at larger budgets—but remains substantial even at 768 tokens.

### 3.4 LLM Judge Corroboration

The 25-row stratified LLM judge sample produced mean scores directionally consistent with deterministic metrics:

| Strategy             | LLM Judge Mean |
|----------------------|----------------|
| prefix_truncate      | 0.0            |
| random_sentences     | 0.2            |
| keyword_overlap      | 1.0            |
| answer_aware_oracle  | 1.0            |
| full_context         | 1.0            |

The LLM judge assigned zero mean score to prefix truncation and low scores to random selection, while assigning perfect mean scores to keyword overlap, answer-aware oracle, and full context. This directional agreement supports the deterministic findings, though the sample size is too small for statistical inference.

---

## 4. Limitations

1. **Small LLM judge sample.** Only 25 stratified rows received LLM judging. The primary evaluation relies on deterministic extractive EM/F1, which may not capture all aspects of answer quality (e.g., fluency, completeness of multi-part answers). The full prediction artifact is saved for larger-scale adjudication, but that adjudication has not been conducted.

2. **Single dataset.** All results are from SQuAD v1.1 dev, a single-answer extractive QA dataset. The findings may not generalize to multi-hop QA, summarization, or open-ended generation tasks where answer quality is less amenable to extractive F1 measurement.

3. **Deterministic evaluation only.** The primary metrics are exact match and token-level F1 against gold answer strings. These do not assess whether a compressed context supports semantically correct but lexically divergent answers.

4. **Answer-aware oracle is an upper bound.** The answer-aware oracle uses gold answer information for sentence selection, which is unavailable at inference time. It serves as a ceiling on retrieval-informed compression, not as a deployable strategy. The practical gap between keyword-overlap selection and the oracle is not characterized in detail.

5. **No model-in-the-loop evaluation.** Compression quality is assessed via extractive answer matching against gold spans, not by feeding compressed contexts to a language model and evaluating generated outputs. The interaction between compression artifacts and model behavior (e.g., hallucination under missing context) is not measured.

6. **Fixed distractor count.** All contexts use exactly 10 distractor paragraphs. Real RAG pipelines may retrieve varying numbers of distractors with different relevance distributions.

7. **No cross-dataset replication.** The branch kill condition was evaluated on a single dataset. Replication on additional RAG benchmarks would strengthen the evidence.

---

## 5. Reproducibility Checklist

- **Dataset source:** SQuAD v1.1 dev (`artifacts/squad_dev_v1.1.json`)
- **RAG context assembly:** `artifacts/real_rag_squad_examples.jsonl`
- **Compression and evaluation script:** `scripts/real_task_context_compression_validation.py`
- **Test suite:** `tests/test_real_task_context_compression_validation.py` (3 tests passed)
- **Run parameters:** `--n 180 --seed 34436771 --budgets 96,192,384,768 --distractors 10`
- **Primary output:** `artifacts/real_task_predictions.jsonl`
- **Pareto metrics:** `artifacts/real_task_pareto_metrics.csv`
- **Pareto summary:** `artifacts/real_task_pareto_summary.json`
- **LLM judge input:** `artifacts/llm_judge_sample_input.json`
- **LLM judge output:** `artifacts/claude_llm_judge_sample_output.json`
- **LLM judge comparison:** `artifacts/llm_judge_sample_comparison.json`
- **LLM judge markdown:** `.omx/artifacts/llm-judge-squad-sample-20260417T121503Z.md`
- **Environment setup:**
  ```bash
  uv venv --python /usr/bin/python3 .venv
  uv pip install --python .venv/bin/python pytest
  .venv/bin/python -m pytest tests -q
  .venv/bin/python scripts/real_task_context_compression_validation.py \
    --n 180 --seed 34436771 --budgets 96,192,384,768 --distractors 10 --out artifacts
  ```
- **Random seed:** 34436771
- **Sample size:** 180 examples

---

## 6. Conclusion

Real-task answer-quality evaluation on SQuAD-derived RAG contexts confirms two findings previously observed in synthetic settings: (1) the Pareto ranking of compression strategies shifts with token budget, with full context overtaking answer-aware oracle selection at 768 tokens; and (2) prefix truncation exhibits a durable late-evidence failure mode that persists across all tested budgets. Answer-aware compression provides substantial F1 gains over prefix truncation (+79.2 F1 at 96 tokens, declining to +35.9 at 768 tokens), and keyword-overlap selection achieves comparable scores to the oracle in the LLM judge sample.

These findings are supported by moderate-strength evidence. The deterministic evaluation is comprehensive over 180 examples, but the LLM judge corroboration covers only 25 stratified rows, and the evaluation is confined to a single extractive QA dataset. The saved prediction artifacts (`artifacts/real_task_predictions.jsonl`) are prepared for larger-scale LLM or human adjudication if stronger evidence is required. No additional generic successor branch is recommended; the appropriate follow-up, if pursued, is a scaled adjudication pass on the existing predictions.

---

## Referenced Artifacts

### Result files
- `artifacts/llm_judge_sample_comparison.json`
- `artifacts/claude_llm_judge_sample_output.json`
- `artifacts/llm_judge_sample_input.json`
- `artifacts/real_task_pareto_summary.json`
- `artifacts/real_task_predictions.jsonl`
- `artifacts/real_task_pareto_metrics.csv`
- `artifacts/real_rag_squad_examples.jsonl`
- `artifacts/squad_dev_v1.1.json`

### Source and test files
- `scripts/real_task_context_compression_validation.py`
- `tests/test_real_task_context_compression_validation.py`
- `scripts/__init__.py`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`
- `.omx/artifacts/llm-judge-squad-sample-20260417T121503Z.md`
- `run_notes.md`
- `README.md`

### Paper pipeline artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
