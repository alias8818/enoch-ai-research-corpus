# Chain-of-Density Evidence Packing for Budgeted Retrieval-Augmented Prompts

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We present Chain-of-Density (CoD) evidence packing, an offline method that compresses retrieved evidence into token-budgeted prompt packs by iteratively extracting high-density support sentences and replacing lower-density spans. In a synthetic benchmark spanning five task types with query perturbations, CoD packing achieved a mean same-budget F1-proxy gain of 0.796 and mean gold-evidence recall gain of 0.743 over vanilla retrieve-then-read, with mean token savings of 0.491 against non-trivial vanilla baselines and a construction latency overhead of 1.191 ms. On a real-data validation using 120 SQuAD v1.1 dev examples with hard lexical distractors, CoD packing gained +0.105 answer EM/F1 and +0.098 faithful citation rate at matched token budgets, at a cost of +2.19 ms construction latency. A notable mixed finding is that CoD consumed more prompt tokens than vanilla on average in the real-data setting, because the vanilla baseline silently skipped oversized raw paragraphs; the stronger supported claim is same-budget quality gain rather than token reduction. External validity remains inconclusive: results have not yet been confirmed with LLM-generated answer scoring or on repository-QA traces.

## 1. Introduction

Retrieve-then-read pipelines for question answering and evidence-grounded generation typically pack raw retrieved chunks into a prompt up to a token budget. When the budget is tight, either chunks are truncated or lower-ranked chunks are dropped entirely, potentially discarding high-density support sentences buried in verbose passages.

Chain-of-Density (CoD) evidence packing addresses this by rewriting the evidence selection step: rather than including or excluding whole chunks, the packer extracts and scores individual support sentences, then iteratively replaces lower-density spans with higher-density alternatives until the token budget is saturated. The output is a compact prompt pack with sentence-level provenance annotations.

This technical report documents the implementation and evaluation of CoD evidence packing against a vanilla top-k chunk baseline. The evaluation proceeds in two stages: a synthetic benchmark across five task types with query perturbations, and a real-data validation on SQuAD v1.1 with hard lexical distractors. We report both positive and negative findings.

## 2. Method

### 2.1 Chain-of-Density Packer

The CoD packer operates in four stages:

1. **Chunk retrieval.** Given a query, retrieve candidate chunks using a standard retriever.
2. **Support sentence extraction and scoring.** Within each retrieved chunk, extract sentences and score them for query-relevance density using a lexical overlap and term-frequency signal.
3. **Iterative density replacement.** Starting from the highest-scoring sentences, fill the token budget. When the budget is exhausted, iteratively compare the lowest-density included sentence against the highest-density excluded sentence; swap if the excluded sentence scores higher and fits within the budget.
4. **Provenance-annotated output.** Emit the selected sentences as a prompt pack, with each sentence annotated by its source chunk identifier and position.

The implementation is dependency-light and runs offline, requiring no model inference for the packing step itself.

### 2.2 Vanilla Baseline

The vanilla baseline retrieves the top-k chunks and concatenates them in rank order, truncating at the token budget. If a chunk exceeds the remaining budget, it is skipped entirely (not truncated). This skip behavior is a design choice that affects the comparison, as discussed in Section 5.

### 2.3 Benchmark Harness

A deterministic benchmark harness was implemented covering five task categories: question answering, citation-heavy answering, contract/form extraction, repository-QA, and long summarization. Each task includes a base query and perturbed variants to test robustness. Metrics logged per example include prompt token count, construction latency (ms), gold-evidence recall, answer F1 proxy, and compression ratio.

### 2.4 SQuAD v1.1 Validation Harness

A separate real-data harness draws examples from the SQuAD v1.1 dev set. For each example, the gold paragraph is presented alongside five hard lexical distractor paragraphs (drawn from other SQuAD entries sharing high token overlap with the query). Both the CoD packer and vanilla baseline construct prompt packs under fixed token budgets. An extractive generated-answer upper bound is scored: the best extractive span in the packed prompt is compared against the gold answer using exact match (EM) and token-level F1. Citation faithfulness is scored by checking whether the generated answer's cited source line overlaps the gold paragraph.

## 3. Results

### 3.1 Synthetic Benchmark

The synthetic benchmark was run over token budgets of 90, 130, 180, 240, 360, 520, and 700. All four unit tests passed prior to the benchmark run.

| Metric | Value |
|---|---|
| Mean same-budget F1-proxy gain | 0.796 |
| Mean same-budget gold-evidence recall gain | 0.743 |
| Mean token savings vs. non-trivial vanilla | 0.491 |
| Mean construction latency delta | +1.191 ms |

The synthetic evidence supports the CoD mechanism: at matched token budgets, CoD packs contain more gold-relevant content and yield higher answer-quality proxies than the vanilla baseline. However, these results derive from controlled synthetic tasks; external validity is not established.

### 3.2 Real SQuAD v1.1 Validation

The SQuAD validation was run on 120 deterministic examples over budgets of 120, 180, 240, 360, and 520 tokens, with 5 hard distractors per example. All unit tests and both benchmark scripts passed verification.

| Metric | Value |
|---|---|
| Answer EM/F1 gain (same budget) | +0.105 |
| Faithful citation rate gain (same budget) | +0.098 |
| Construction latency delta | +2.19 ms |

**Mixed finding on token consumption.** CoD used more prompt tokens than vanilla on average. The reason is that the vanilla baseline skips oversized raw paragraphs entirely when they exceed the remaining budget, resulting in fewer total tokens used. CoD, by extracting sentences, can pack more content into the same budget—but this means it actually uses more of the allocated budget. The stronger supported claim is that CoD yields quality gains at the same budget, not that it reduces token consumption. Equal-quality budget savings are observable only on the coarse budget frontier (i.e., a smaller CoD budget can match a larger vanilla budget's quality).

## 4. Limitations

1. **No LLM-generated answer scoring.** Both the synthetic and SQuAD evaluations use extractive answer upper bounds rather than actual LLM-generated answers. The effect of CoD packing on end-to-end LLM answer quality remains unmeasured.

2. **No repository-QA or multi-hop validation.** The hypothesis has not been tested on repo-QA traces or multi-hop datasets such as HotpotQA, where evidence aggregation across documents may interact differently with sentence-level packing.

3. **Synthetic benchmark generality.** The synthetic benchmark uses constructed task templates; performance on these templates may not transfer to naturally occurring query distributions.

4. **Vanilla baseline skip behavior.** The vanilla baseline skips chunks that exceed the remaining budget rather than truncating them. A truncating vanilla baseline might close part of the quality gap with CoD. This comparison was not conducted.

5. **Distractor hardness.** The SQuAD validation uses five hard lexical distractors per example. Performance may differ with more or fewer distractors, or with semantically similar (rather than lexically similar) distractors.

6. **Packing scorer limitations.** The density scorer uses lexical overlap and term-frequency signals. It does not use semantic embeddings, which may limit its ability to identify relevant sentences with low lexical overlap.

7. **Scale of real-data evaluation.** Only 120 SQuAD examples were evaluated. Statistical significance of the +0.105 and +0.098 gains has not been formally tested.

8. **Single-dataset validation.** All real-data results come from SQuAD v1.1, a single-answer extractive QA dataset. Generalization to abstractive, multi-answer, or open-ended generation tasks is not established.

## 5. Reproducibility Checklist

- **Code availability:** Implementation in `src/chain_density_pack.py`; benchmark harness in `benchmark.py`; SQuAD harness in `real_squad_benchmark.py`; tests in `tests/test_chain_density_pack.py`.
- **Data availability:** SQuAD v1.1 dev set (`data/squad_dev_v1.1.json`) is a public dataset; synthetic benchmark data is generated deterministically by `benchmark.py`.
- **Randomness control:** Both benchmarks are deterministic; no random seeds are required.
- **Budgets tested:** Synthetic: 90, 130, 180, 240, 360, 520, 700. SQuAD: 120, 180, 240, 360, 520.
- **SQuAD configuration:** 120 examples, 5 distractors per example.
- **Unit tests:** 4 tests passing (`python -m unittest discover -s tests -v`).
- **Result files:** `results/benchmark_results.json`, `results/real_squad_benchmark_results.json`, `results/summary.md`.
- **Hardware/environment:** Not recorded in artifacts. Latency figures (1.191 ms, 2.19 ms) are relative and should not be compared across environments.

## 6. Conclusion

Chain-of-Density evidence packing produces prompt packs that contain more gold-relevant content per token than vanilla retrieve-then-read, yielding measurable quality gains at matched budgets in both synthetic and real SQuAD evaluations. The real-data gains are modest (+0.105 answer EM/F1, +0.098 faithful citation) and come with a small latency cost (+2.19 ms). A key negative finding is that CoD does not reliably reduce prompt token consumption relative to a vanilla baseline that skips oversized chunks; the primary benefit is quality improvement at fixed budgets, not token savings.

The current evidence supports the CoD mechanism within the tested settings, but external validity remains inconclusive. Validation against LLM-generated answers, repository-QA traces, and multi-hop datasets is recommended before drawing broader conclusions.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Evidence bundle | `evidence_bundle.json` |
| Claim ledger | `claim_ledger.json` |
| Publication manifest | `publication_manifest.json` |
| CoD packer implementation | `src/chain_density_pack.py` |
| Synthetic benchmark | `benchmark.py` |
| SQuAD benchmark | `real_squad_benchmark.py` |
| Unit tests | `tests/test_chain_density_pack.py` |
| Synthetic benchmark results | `results/benchmark_results.json` |
| SQuAD benchmark results | `results/real_squad_benchmark_results.json` |
| Results summary | `results/summary.md` |
| SQuAD dev data | `data/squad_dev_v1.1.json` |
| Project metrics | `.omx/metrics.json` |
