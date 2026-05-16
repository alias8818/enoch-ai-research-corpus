# Evidence-First Context Ladder Prompt Layout Ablation

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We ablate the prompt layout of context-ladder retrieval-augmented generation, holding the selection of ladder items constant while varying their ordering within the prompt. Two layout variants—evidence-first (fine-grained chunks placed before summaries) and summary-demoted (chunks first, summaries explicitly labeled as background)—are compared against a summary-leading baseline on a 12-item repository question-answering benchmark using Qwen2.5-3B-Instruct. Evidence-first ordering yields positive mean F1 deltas at all three tested token budgets (+0.299 at 600, +0.060 at 900, +0.226 at 1200), with a win/tie/loss record of 14/17/5 across budget–query pairs. Summary-demoted ordering shows a mixed pattern (+0.154, −0.089, +0.175) and a weaker win/tie/loss of 14/13/9. Deterministic extractive evaluation confirms that all layouts produce identical evidence recall and F1, isolating the observed differences to generative model behavior. These results are limited to a single small model, one seed, and 12 items; they should not be generalized without further replication.

## 1. Introduction

Retrieval-augmented generation (RAG) systems typically assemble prompts by concatenating retrieved context items before a query. When the context includes both coarse summaries and fine-grained evidence chunks, the default convention is to place summaries first—providing the model with a high-level frame before details. However, autoregressive language models allocate disproportionate attention to early tokens, and summary-leading layouts may encourage the model to anchor on summary-level abstractions rather than grounding its answer in specific evidence.

This study investigates whether reordering the *same* selected context items—placing fine-grained evidence chunks before summaries—improves answer quality without altering the retrieval or selection pipeline. The key constraint is that selection remains identical across conditions; only the spatial layout of items within the prompt changes. This isolates the effect of prompt ordering from any confound introduced by different evidence being available to the model.

We test two layout interventions against a summary-leading baseline:

1. **Evidence-first**: identical ladder items, chunks before summaries.
2. **Summary-demoted**: identical ladder items, chunks first, with prompt text explicitly labeling summaries as background context.

Our evaluation uses a local repository question-answering (repo-QA) benchmark with both deterministic (extractive) and generative (LLM) evaluation paths, enabling us to separate ordering effects on retrieval quality from ordering effects on generation quality.

## 2. Method

### 2.1 Context Ladder Layout Variants

The parent project provides a context-ladder system that selects a ranked set of context items—both summary-level and chunk-level—for a given query. We introduce three layout policies that consume the same selected item set:

- **Summary-leading (baseline)**: Summaries are placed first in the prompt, followed by fine-grained chunks. This is the default layout from the parent system.
- **Evidence-first**: The selected item set is reordered so that all fine-grained chunks appear before all summaries. Item membership and token count are preserved; only the serial position of items changes.
- **Summary-demoted**: As with evidence-first, chunks precede summaries, but an additional prompt annotation labels the summary sections as "background context," explicitly signaling their subordinate role.

### 2.2 Verification of Layout Isolation

To confirm that layout variants differ only in ordering and not in content, we implemented regression tests (`tests/test_context_ladder.py`) that verify:

- Evidence-first prompts contain exactly the same items as summary-leading prompts for the same query and budget.
- Token counts are preserved across layout variants.
- Summary-demoted prompts include the expected demotion annotation.

All six regression tests passed.

### 2.3 Evaluation Protocol

We employ a two-track evaluation:

**Deterministic (extractive) track.** An extractive reader computes evidence recall and F1 directly from the selected item set, without any generative model. Because the item set is identical across layouts, this track serves as a control: any difference in generative performance must arise from model behavior, not from retrieval quality.

**Generative (LLM) track.** A local language model generates free-text answers conditioned on the laid-out prompt. Generated answers are evaluated against reference answers using token-overlap F1.

### 2.4 Benchmark Configuration

| Parameter | Value |
|---|---|
| Model | Qwen/Qwen2.5-3B-Instruct |
| Random seed | 344 |
| Benchmark items | 12 repo-QA questions |
| Token budgets | 600, 900, 1200 |
| Layouts | summary-leading, evidence-first, summary-demoted |
| Total generations | 144 (3 layouts × 3 budgets × 12 items × 1 seed) |

## 3. Results

### 3.1 Deterministic Control

All three layouts produced identical evidence recall and F1 scores on the deterministic extractive track. This confirms that the layout manipulation does not alter the information available to the reader; any downstream difference is attributable to the generative model's sensitivity to token ordering.

### 3.2 Generative Evaluation: Evidence-First vs. Summary-Leading

Mean generated-answer F1 deltas (evidence-first minus summary-leading) at each budget:

| Budget | F1 Delta | Direction |
|---|---|---|
| 600 | +0.299 | Positive |
| 900 | +0.060 | Positive |
| 1200 | +0.226 | Positive |

Across all 36 budget–query pairs (3 budgets × 12 items), evidence-first won 14, tied 17, and lost 5 against the summary-leading baseline.

The positive deltas at all three budgets indicate that evidence-first ordering consistently improves generative answer quality relative to the summary-leading baseline under these test conditions. The largest improvement occurs at the tightest budget (600), where the model has the least room for summary material and benefits most from early evidence exposure.

### 3.3 Generative Evaluation: Summary-Demoted vs. Summary-Leading

Mean generated-answer F1 deltas (summary-demoted minus summary-leading):

| Budget | F1 Delta | Direction |
|---|---|---|
| 600 | +0.154 | Positive |
| 900 | −0.089 | Negative |
| 1200 | +0.175 | Positive |

Win/tie/loss record: 14/13/9.

Summary-demoted layout shows a mixed pattern. It improves at budgets 600 and 1200 but degrades at budget 900. The negative delta at budget 900 suggests that the explicit demotion annotation can interfere with the model's use of summary context at intermediate context sizes, producing less reliable behavior than the simpler evidence-first reordering.

### 3.4 Performance Characteristics

The full LLM generation run completed in approximately 200.1 seconds for 144 generations after cached model load. Pre- and post-run UMA memory readings indicated approximately 116 GiB available. Idle GPU utilization samples registered 0%, which is too coarse to establish whether the GPU was saturated during generation; this measurement limitation prevents any claim about compute efficiency.

## 4. Limitations

1. **Single model.** All generative results are from Qwen2.5-3B-Instruct. Whether evidence-first ordering helps, harms, or is neutral for larger models or models from different families is unknown.
2. **Single seed.** Only seed 344 was used. Variance across seeds has not been characterized, so the reported F1 deltas should be treated as point estimates, not as stable population means.
3. **Small benchmark.** The 12-item repo-QA benchmark is narrow. Results may not extend to other domains, question types, or repository structures.
4. **Token-overlap F1.** Generated answers are evaluated with token-overlap F1, which captures lexical similarity but not semantic correctness, faithfulness, or hallucination rates. Evidence-first ordering could improve F1 while increasing hallucination; this possibility was not tested.
5. **No human evaluation.** Answer quality was assessed automatically. Human preference or correctness judgments may differ from F1 rankings.
6. **GPU utilization unmeasured.** The 0% idle-sample utilization is too coarse to support any claim about computational cost or saturation.
7. **Summary-demoted instability.** The negative F1 delta at budget 900 for summary-demoted layout indicates that explicit demotion annotations can produce unpredictable effects depending on context size. This variant should not be adopted as a default without further investigation.
8. **No cross-repository replication.** All items come from a single repository. The effect of evidence-first ordering on other codebases or document collections is untested.

## 5. Reproducibility Checklist

- **Code available**: Layout variant implementations are in `src/context_ladder.py`; benchmark harness in `src/repo_qa_llm_benchmark.py` and `src/repo_qa_benchmark.py`.
- **Tests**: `tests/test_context_ladder.py` (6 passing regression tests verifying layout isolation).
- **Model specified**: Qwen/Qwen2.5-3B-Instruct.
- **Seed specified**: 344.
- **Benchmark items**: 12 repo-QA items (see `results/ablation_llm/repo_qa_llm_results.json`).
- **Budgets specified**: 600, 900, 1200 tokens.
- **Deterministic control**: `results/ablation_deterministic/repo_qa_summary.md` and `results/ablation_deterministic/repo_qa_results.json`.
- **Generative results**: `results/ablation_llm/repo_qa_llm_results.json` and `results/ablation_llm/repo_qa_llm_summary.md`.
- **Analysis**: `results/ablation_analysis.md`.
- **Calibration logs**: `results/pre_llm_calibration.txt`, `results/post_llm_calibration.txt`.
- **Parent baseline**: `results/parent_baseline_/` directory contains the original summary-leading baseline results for comparison.
- **Pilot run**: `results/ablation_llm_pilot/` contains an earlier pilot run with the same model and benchmark.

## 6. Conclusion

Reordering context-ladder items to place fine-grained evidence before summaries improves mean generated-answer F1 over a summary-leading baseline at all three tested token budgets in a 12-item repo-QA benchmark with Qwen2.5-3B-Instruct. The effect is consistent in direction (+0.060 to +0.299 F1) and favorable in pairwise comparison (14 wins, 17 ties, 5 losses). The simpler evidence-first reordering outperforms the more aggressive summary-demoted variant, which shows an unstable pattern including a negative delta at one budget.

These findings support adopting evidence-first layout as the default prompt ordering for context-ladder systems, subject to the substantial limitations of this study: a single small model, one random seed, 12 benchmark items, and token-overlap F1 as the sole quality metric. Validation on additional models, seeds, repositories, and evaluation dimensions (faithfulness, hallucination rate, human judgment) is necessary before the result can be considered robust.

## Referenced Artifacts

### Result files
- `results/ablation_analysis.md`
- `results/ablation_llm/repo_qa_llm_results.json`
- `results/ablation_llm/repo_qa_llm_summary.md`
- `results/ablation_llm_pilot/repo_qa_llm_results.json`
- `results/ablation_llm_pilot/repo_qa_llm_summary.md`
- `results/ablation_deterministic/repo_qa_results.json`
- `results/ablation_deterministic/repo_qa_summary.md`
- `results/post_llm_calibration.txt`
- `results/pre_llm_calibration.txt`
- `results/parent_baseline_/repo_qa_llm_results.json`
- `results/parent_baseline_/repo_qa_llm_summary.md`
- `results/parent_baseline_/repo_qa_results.json`
- `results/parent_baseline_/repo_qa_summary.md`
- `results/parent_baseline_/benchmark_results.json`
- `results/parent_baseline_/benchmark_summary.md`

### Source and configuration files
- `src/context_ladder.py`
- `src/repo_qa_llm_benchmark.py`
- `src/repo_qa_benchmark.py`
- `src/synthetic_benchmark.py`
- `tests/test_context_ladder.py`
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `prompts/initial.md`
- `prompts/resume.md`

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
