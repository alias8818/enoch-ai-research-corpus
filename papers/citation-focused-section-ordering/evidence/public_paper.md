# Citation-Focused Section Ordering: Re-evaluating Section Reordering Under Citation Fidelity Objectives

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We report a citation-focused reanalysis of section-order search, a method that reorders retrieved document sections before concatenation into a language model prompt. In a prior evaluation under an answer-F1-per-token objective, section-order search did not produce meaningful improvements. Under a citation-fidelity objective—measuring whether the model cites the correct evidence sections—the same mechanism yields material gains. On 288 paired comparisons from scaled Qwen LLM rows, section-order search improves citation F1 by +0.1478 (95% bootstrap CI [+0.0931, +0.2063]), citation recall by +0.1658 (95% CI [+0.1102, +0.2214]), and exact citation-set match by +0.1875, while reducing both overcitation and undercitation. Generated answer F1 does not decrease (delta +0.0407, 95% CI [−0.0108, +0.0904]), and prompt-token overhead is +1.24 estimated tokens. These results are limited to a single model family, a single benchmark configuration, and an automated pipeline without external replication. The current project artifacts support this finding in the tested setting; they do not demonstrate universal applicability.

---

## 1. Introduction

Retrieval-augmented generation (RAG) systems assemble prompts by concatenating retrieved document sections before presenting them to a language model. The order in which sections appear in the prompt can affect model behavior, but the dominant evaluation objective has been answer quality per token. A parent project evaluated section-order search under that objective and found insufficient improvement to justify adoption.

However, many RAG deployments care about citation fidelity—whether the model attributes its answer to the correct evidence sections—as much as or more than marginal answer-quality gains. Misattribution, overcitation (citing irrelevant sections), and undercitation (failing to cite required evidence) are distinct failure modes that answer-F1 does not capture. This branch project re-evaluates the same section-order search mechanism under a citation-fidelity objective, using the parent project's scaled LLM rows as input data.

The central question is: does section-order search, which was not strong enough for answer-F1-per-token improvement, materially improve citation fidelity without degrading answer quality or imposing large prompt overhead?

---

## 2. Method

### 2.1 Section-Order Search

The section-order search mechanism (implemented in `src/section_order_packer.py`) reorders retrieved document sections according to a search over possible permutations before concatenating them into the prompt. The parent project's harness (`experiments/benchmark_section_order.py`, `experiments/llm_smoke_benchmark.py`) generates paired LLM calls: one using source-order concatenation (the baseline, where sections appear in retrieval rank order) and one using the searched ordering.

### 2.2 Citation-Focused Analysis

A dependency-free analysis script (`experiments/citation_focused_analysis.py`) was added to compute citation-specific metrics from the parent project's scaled LLM rows. This script computes:

- **Citation F1, precision, and recall**: Whether the model's cited section identifiers match the ground-truth required citation set.
- **Exact citation-set match**: The fraction of examples where the model's citation set exactly equals the required set.
- **Overcitation and undercitation rates**: The fraction of examples where the model cites extra sections (overcitation) or omits required sections (undercitation).
- **Generated answer F1**: Token-level F1 between the model's generated answer and the reference answer, serving as an answer-quality guardrail.
- **Prompt-token overhead**: The estimated change in prompt token count between conditions.
- **JSON parse rate**: Whether the model's output was valid JSON.

Paired bootstrap confidence intervals (95%) are computed for the primary deltas.

### 2.3 Success and Kill Criteria

Pre-registered branch-specific criteria were defined before reanalysis:

- **Success gate**: Citation F1 improvement ≥ +0.05 and citation recall improvement ≥ +0.10 versus source-order concat.
- **Guardrails**: Generated answer F1 must not drop by more than −0.02; prompt-token overhead must stay below +5 estimated tokens on average; JSON parse rate must remain comparable.
- **Kill condition**: Finalize negative if citation F1 gain < +0.03, citation recall gain < +0.05, or if citation gains are achieved only with material answer-quality loss (> −0.02 generated F1) or large prompt-token overhead (> +10 estimated tokens).

---

## 3. Results

### 3.1 Experimental Configuration

The analysis uses 576 LLM calls from the parent project's scaled Qwen run, yielding 288 paired comparisons (section-order search vs. source-order concat). The underlying model is a Qwen-family model served via llama.cpp; the benchmark data is derived from SQuAD dev v1.1.

### 3.2 Citation Fidelity Metrics

| Metric | Delta (Search − Source-Order) | 95% Bootstrap CI |
|---|---|---|
| Citation F1 | +0.1478 | [+0.0931, +0.2063] |
| Citation recall | +0.1658 | [+0.1102, +0.2214] |
| Citation precision | +0.1024 | [+0.0406, +0.1622] |
| Exact citation-set match | +0.1875 | — |

All three citation fidelity metrics show positive deltas with confidence intervals excluding zero. The exact citation-set match improvement of +0.1875 indicates that section-order search causes the model to produce the precisely correct citation set substantially more often.

### 3.3 Overcitation and Undercitation

- Overcitation rate delta: −0.0677 (section-order search reduces overcitation).
- Undercitation rate delta: −0.1658 (section-order search reduces undercitation).

The gains are not attributable to indiscriminate citation spam; both overcitation and undercitation decrease, with the larger improvement in undercitation.

### 3.4 Answer-Quality Guardrail

- Generated answer F1 delta: +0.0407 (95% CI [−0.0108, +0.0904]).

The point estimate is positive and the confidence interval includes zero but does not extend below −0.02. The pre-registered guardrail (answer F1 must not drop by more than −0.02) is not violated. There is no evidence of answer-quality degradation; if anything, there is a modest positive trend, though the CI includes zero.

### 3.5 Overhead and Robustness

- Prompt-token overhead: +1.24 estimated tokens on average (below the +5 success guardrail and well below the +10 kill threshold).
- JSON parse-rate delta: 0.0 (no change in output format robustness).

### 3.6 Criterion Evaluation

The success gate passed: citation F1 gain (+0.1478) exceeds +0.05, and citation recall gain (+0.1658) exceeds +0.10. The kill condition did not trigger: citation F1 gain exceeds +0.03, citation recall gain exceeds +0.05, answer F1 did not drop by more than −0.02, and prompt-token overhead is well below +10.

---

## 4. Limitations

1. **Single model family.** All results come from a Qwen-family model served via llama.cpp. Generalization to other model families, sizes, or serving backends is not established.

2. **Single benchmark configuration.** The evaluation uses SQuAD dev v1.1 as the underlying question-answer source. Performance on other domains (legal, medical, multi-hop) is unknown.

3. **Automated pipeline without external replication.** The entire experiment was conducted within an automated research pipeline. No independent replication by external researchers has been performed.

4. **Parent project's negative result.** The same section-order search mechanism did not produce meaningful answer-F1-per-token improvement in the parent project. The positive finding here is specific to the citation-fidelity objective. The method should not be adopted for answer-quality improvement; the project decision explicitly recommends treating answer-F1-per-token improvement as unsupported.

5. **Confidence is medium, evidence strength is moderate.** The project decision records confidence as "medium" and evidence strength as "moderate." These assessments reflect the limited scope of the evaluation and the absence of external validation.

6. **Estimated token counts.** Prompt-token overhead is reported as estimated tokens rather than exact measured tokens. The estimates are sufficient for the guardrail checks but may differ from exact counts under different tokenizers.

7. **No ablation of search strategy.** The analysis compares search ordering to source-order concatenation but does not isolate which aspects of the search (e.g., recency bias, relevance re-ranking) drive the citation improvement.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Code available in project artifacts | Yes: `src/section_order_packer.py`, `experiments/citation_focused_analysis.py`, `experiments/benchmark_section_order.py`, `experiments/llm_smoke_benchmark.py` |
| Unit tests pass | Yes: 2 tests passed via `python3 -m unittest discover -s tests -v` |
| All scripts compile | Yes: `py_compile` passed for all four Python files |
| Input data specified | Yes: `data/squad_dev_v1.1.json`, `results/parent_qwen_scaled/llm_smoke_rows.csv` |
| Output artifacts recorded | Yes: `results/citation_focus/citation_focus_summary.json`, `results/citation_focus/citation_focus_grouped_deltas.csv` |
| Pre-registered criteria | Yes: documented in `run_notes.md` before reanalysis |
| Confidence intervals reported | Yes: 95% paired bootstrap CIs for primary metrics |
| Negative parent-project result disclosed | Yes: answer-F1-per-token improvement unsupported |
| External replication | No: not performed |
| Human review of this draft | No: this is an unreviewed AI-generated artifact |

---

## 6. Conclusion

Section-order search, which did not produce meaningful improvements under an answer-F1-per-token objective, materially improves citation fidelity when evaluated under a citation-focused objective. On 288 paired comparisons from scaled Qwen LLM rows, citation F1 improves by +0.1478, citation recall by +0.1658, and exact citation-set match by +0.1875, with concurrent reductions in both overcitation and undercitation. Answer quality is not degraded (answer F1 delta +0.0407, 95% CI [−0.0108, +0.0904]), and prompt-token overhead is negligible (+1.24 estimated tokens).

These findings are bounded: they apply to one model family, one benchmark, and one automated pipeline. The project decision recommends adopting section-order search only for citation-fidelity-sensitive QA/RAG settings, while treating answer-F1-per-token improvement as unsupported. External replication across additional models, domains, and evaluation frameworks is necessary before broader claims can be justified.

---

## Referenced Artifacts

### Result files
- `results/citation_focus/citation_focus_summary.json`
- `results/citation_focus/citation_focus_grouped_deltas.csv`
- `results/parent_qwen_scaled/llm_smoke_rows.csv`
- `results/parent_qwen_scaled/llm_smoke_summary.json`
- `results/parent_qwen_scaled/llm_smoke_telemetry.json`
- `results/parent_qwen_scaled/llm_smoke_raw_responses.json`
- `results/parent_qwen_scaled/llama_server_scaled.log`
- `results/parent_qwen_scaled/llama_server_tail.log`

### Source and analysis files
- `src/section_order_packer.py`
- `experiments/citation_focused_analysis.py`
- `experiments/benchmark_section_order.py`
- `experiments/llm_smoke_benchmark.py`
- `tests/test_section_order_packer.py`
- `data/squad_dev_v1.1.json`

### Decision and provenance files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`
- `run_notes.md`
- `artifacts/parent_README.md`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
