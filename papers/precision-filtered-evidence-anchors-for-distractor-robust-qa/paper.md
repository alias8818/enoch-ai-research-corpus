# Precision-Filtered Evidence Anchors for Distractor-Robust QA

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present precision-filtered evidence anchors, a sentence-level selection method for retrieval-augmented question answering that suppresses distractor, provisional, and negated value-bearing sentences before anchor packing, admitting only sentences carrying final-review or assignment evidence cues. On a synthetic distractor benchmark evaluated with Qwen2.5 0.5B (Q4_K_M) across three prompt budgets (140, 180, 220 tokens) and three paraphrase types (original, code_direct, semantic), precision-filtered anchors outperformed vanilla top-k retrieval at every budget (F1 0.7778 vs 0.0069 at budget 140; 0.7500 vs 0.3750 at budget 180; 0.7778 vs 0.7292 at budget 220) and on the previously failing code_direct paraphrase type (0.6111 vs 0.4514). The current project artifacts support this finding in the tested setting. Confidence is assessed as medium and evidence strength as moderate, bounded by the synthetic and templated nature of the benchmark, the single small model evaluated, and the absence of external corpus validation.

## Introduction

Retrieval-augmented generation (RAG) systems for question answering face a persistent challenge: retrieved evidence passages frequently contain distractor sentences that are superficially answer-shaped—provisional values, negated claims, or competing assignments—yet do not reflect the final resolved answer. When such sentences are exposed to the generative model, small models in particular tend to copy the most prominent value-shaped span regardless of its evidential status, degrading answer accuracy.

Prior anchor-packing approaches attempt to compress retrieved evidence into budget-constrained prompt windows while preserving answer-relevant content. However, the parent implementation of anchor packing in this project's lineage retained low-precision distractor sentences alongside genuine answer-bearing ones. The resulting prompts exposed the generative model to competing value claims, causing systematic failures on paraphrase types (notably code_direct) where the distractor structure closely mirrored the query surface form.

We hypothesize that the parent failure was not a retrieval or retention problem but a precision problem: the anchor packer admitted sentences with provisional, negated, or otherwise non-final value cues, and the generative model preferentially copied those distractors. Precision-filtered evidence anchors address this by applying a sentence-level filter before packing that suppresses distractor, provisional, and negated value sentences, admitting only sentences bearing final-review or assignment evidence cues.

This report documents the implementation, evaluation, and limitations of precision-filtered evidence anchors on a synthetic distractor benchmark with Qwen2.5 0.5B.

## Method

### Precision-Filtered Anchor Packing

The precision-filtered anchor packing procedure operates in two stages:

1. **Distractor detection and redaction.** Each sentence in the retrieved evidence pool is classified by its evidential status. Sentences containing provisional-value markers (e.g., "tentatively assigned", "proposed value"), negated-value markers (e.g., "not the final value", "rejected assignment"), or distractor cues indicating a non-final competing answer are flagged for suppression. Reusable detection and redaction helpers implement this classification.

2. **Budget-constrained anchor packing.** Surviving sentences—those carrying final-review or assignment evidence cues—are packed into the prompt window subject to a token budget. The packing order prioritizes sentences with the strongest final-assignment signals.

The implementation resides in `src/evidence_anchor_packer.py`, which exports `precision_filtered_anchor_pack` and the distractor detection/redaction helpers. The parent anchor packing method (without precision filtering) is retained for comparison.

### Benchmark Harness

The generative QA benchmark (`src/generative_qa_benchmark.py`) evaluates three conditions side-by-side:

- **Vanilla top-k:** Standard retrieval with top-k sentence selection, no anchor packing.
- **Parent anchors:** The prior anchor packing method without distractor filtering.
- **Precision-filtered anchors:** The proposed method.

Each condition is evaluated across three prompt token budgets (140, 180, 220) and three paraphrase types (original, code_direct, semantic), yielding a 3×3×3 design (3 conditions × 3 budgets × 3 paraphrase types) over 24 question items.

### Branch Kill Condition

The method was subject to a pre-registered kill condition: precision-filtered anchors would be deemed non-robust if the generative sweep failed to beat vanilla top-k at every budget, or if it still lost materially on the code_direct paraphrase type. Both conditions were cleared (see Results).

## Results

### Offline Retention Sweep

An offline 120-item sweep at budgets 140, 180, and 220 confirmed that precision-filtered anchor packing preserved answer and evidence retention while consuming approximately 48–53 prompt tokens. Results are recorded in `results/offline_precision_filtered/`.

### Generative QA Benchmark

The Qwen2.5 0.5B (Q4_K_M GGUF) generative sweep over 24 items produced the following F1 scores:

| Budget | Vanilla Top-k | Precision-Filtered | Difference |
|--------|--------------|-------------------|------------|
| 140    | 0.0069       | 0.7778            | +0.7709    |
| 180    | 0.3750       | 0.7500            | +0.3750    |
| 220    | 0.7292       | 0.7778            | +0.0486    |

Precision-filtered anchors outperformed vanilla at every budget. The largest margin appears at the tightest budget (140 tokens), where vanilla retrieval collapses (F1 0.0069) while precision-filtered anchors retain strong performance (F1 0.7778). The margin narrows at budget 220 as vanilla retrieval improves with more context, but precision-filtered anchors maintain a small advantage.

### Code_Direct Paraphrase Results

On the code_direct paraphrase type, which was the failure mode for the parent anchor method:

| Method                | F1     |
|-----------------------|--------|
| Vanilla Top-k         | 0.4514 |
| Precision-Filtered     | 0.6111 |

Precision-filtered anchors beat vanilla by +0.1597 F1 on code_direct paraphrases, clearing the second branch kill condition.

### Performance Characteristics

The full generative run completed in 23.30 seconds wall time with maximum RSS of 969,800 KB. Mean per-request model latency for precision-filtered anchors was:

| Budget | Mean Latency (ms) |
|--------|-------------------|
| 140    | 26.29             |
| 180    | 21.91             |
| 220    | 22.67             |

### Regression Tests

All 7 regression tests passed, covering provisional-value distractor suppression and precision packer budget/retention behavior.

### Interpretation

The parent anchor packing method's failure on code_direct paraphrases was not caused by insufficient evidence retention. Rather, it was caused by low-precision exposure of competing answer-shaped values. Precision filtering addresses this root cause by removing copyable distractors and retaining only the final reviewed value claim. The current project artifacts support this finding in the tested setting.

## Limitations

1. **Synthetic and templated benchmark.** The 24-item generative benchmark and 120-item offline sweep use a synthetic distractor corpus with templated structure. Performance on less templated, naturally occurring QA corpora is unknown and may differ substantially.

2. **Single small model.** All generative results use Qwen2.5 0.5B (Q4_K_M quantization). Whether precision-filtered anchors help, harm, or are neutral for larger or differently architected models has not been tested.

3. **Narrow paraphrase coverage.** Three paraphrase types (original, code_direct, semantic) may not represent the full range of query surface-form variation encountered in production settings.

4. **No external corpus validation.** The project decision explicitly recommends testing on a less templated external QA corpus as a next step; this has not been done.

5. **Moderate evidence strength, medium confidence.** The project's own assessment rates evidence strength as moderate and confidence as medium. These ratings reflect the bounded scope of the evaluation.

6. **Parent anchor comparison incomplete.** The run notes report precision-filtered vs. vanilla comparisons in detail but do not report full parent-anchor F1 scores at each budget and paraphrase type, limiting direct comparison of the two anchor methods.

7. **Automated pipeline provenance.** The experimental design, execution, and decision were produced by an automated research pipeline. While regression tests passed and results are internally consistent, independent replication has not been performed.

## Reproducibility Checklist

- **Model:** Qwen2.5 0.5B Instruct, Q4_K_M quantization (GGUF format), symlinked at `models/qwen2.5-0.5b-instruct-q4_k_m.gguf`.
- **Inference runtime:** llama.cpp (local), as indicated by the generative benchmark harness and GGUF model format.
- **Benchmark items:** 24 generative items across 3 paraphrase types; 120 offline items.
- **Budgets:** 140, 180, 220 prompt tokens.
- **Paraphrase types:** original, code_direct, semantic.
- **Conditions:** vanilla top-k, parent anchors, precision-filtered anchors.
- **Metric:** F1 score (token-level or exact-match, as computed by the benchmark harness).
- **Hardware:** Single machine; max RSS 969,800 KB; wall time 23.30s for full generative run.
- **Source files:** `src/evidence_anchor_packer.py`, `src/generative_qa_benchmark.py`, `tests/test_evidence_anchor_packer.py`.
- **Result files:** See Referenced Artifacts section.
- **Random seeds:** Not specified in available artifacts; this is a gap for exact reproducibility.
- **Software environment:** Python virtual environment (`.venv`); specific package versions not recorded in available artifacts.

## Conclusion

Precision-filtered evidence anchors, which suppress distractor, provisional, and negated value sentences before budget-constrained anchor packing, outperformed vanilla top-k retrieval on a synthetic distractor benchmark at all tested prompt budgets and on the code_direct paraphrase type that previously defeated the parent anchor method. The result supports the hypothesis that the parent method's failure was a precision problem rather than a retention problem. However, these findings are bounded by the synthetic and templated nature of the benchmark, the single small model evaluated, and the absence of external corpus validation. The recommended next step is to test precision-filtered anchors on a less templated external QA corpus to assess generalization. This draft should not be treated as a validated or peer-reviewed publication.

---

## Referenced Artifacts

### Run Notes and Decision
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`

### Claim Ledger and Evidence Bundle
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`

### Source Code
- `src/evidence_anchor_packer.py`
- `src/generative_qa_benchmark.py`
- `src/__init__.py`
- `tests/test_evidence_anchor_packer.py`

### Model
- `models/qwen2.5-0.5b-instruct-q4_k_m.gguf`

### Offline Precision-Filtered Results
- `results/offline_precision_filtered_run.log`
- `results/offline_precision_filtered/summary.md`
- `results/offline_precision_filtered/benchmark_summary.json`
- `results/offline_precision_filtered/benchmark_rows.jsonl`

### Generative Precision-Filtered Results
- `results/generative_qwen_24_precision_filtered_run.log`
- `results/generative_qwen_24_precision_filtered/generative_summary.md`
- `results/generative_qwen_24_precision_filtered/generative_summary_by_paraphrase.json`
- `results/generative_qwen_24_precision_filtered/generative_summary_by_budget.json`
- `results/generative_qwen_24_precision_filtered/generative_rows.jsonl`

### Generative Smoke Test Results (v1 and v2)
- `results/generative_smoke_run.log`
- `results/generative_smoke/generative_summary.md`
- `results/generative_smoke/generative_summary_by_paraphrase.json`
- `results/generative_smoke/generative_summary_by_budget.json`
- `results/generative_smoke/generative_rows.jsonl`
- `results/generative_smoke_v2_run.log`
- `results/generative_smoke_v2/generative_summary.md`
- `results/generative_smoke_v2/generative_summary_by_paraphrase.json`
- `results/generative_smoke_v2/generative_summary_by_budget.json`
- `results/generative_smoke_v2/generative_rows.jsonl`

### Publication Manifest
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/README.md`
