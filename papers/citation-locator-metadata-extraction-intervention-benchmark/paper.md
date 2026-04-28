# Citation Locator Metadata Extraction Intervention Benchmark

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether preserving and exploiting citation locator metadata within chunk text can improve evidence retrieval for citation-resolution tasks. Using 300 weak-labeled examples derived from PubMed Central (PMC) natural documents, we compare a stripped-body retrieval baseline against a sequence of oracle-free interventions: preserved-text similarity, parsed-locator boosting, locator-window ranking, locator-local candidate expansion, and citation-neighborhood tie-breaking. On the 161-example typed-locator subset, the best intervention (citation-neighborhood tie-breaking) yields answer exact accuracy of 0.6646, evidence top-1 of 0.5342, and MRR of 0.7318, compared to 0.3478, 0.2919, and 0.5241 for the stripped-body baseline. The evidence top-1 improvement of +0.2423 exceeds the pre-registered +0.10 kill threshold. However, a stratified manual audit of 32 cases reveals 8 intervention regressions alongside 8 intervention wins, and 40% of gold chunks contain multiple locators, limiting the granularity of paragraph-level approaches. Results are based on CPU regex and token-overlap scoring over weak labels; they have not been validated with neural retrieval or human-verified gold annotations. Confidence in the finding is medium and evidence strength is moderate.

## 1. Introduction

Citation resolution in scientific documents requires identifying the specific passage a citation points to within a referenced document. Standard retrieval pipelines often strip citation markers, table references, and figure locators from chunk text before embedding or scoring, on the assumption that such markers are noise. This practice discards structured signals that could disambiguate which passage within a multi-paragraph document is the intended target.

We test the hypothesis that preserving locator metadata (e.g., "see Section 3.2", "Figure 4", "p. 17") in chunk text and exploiting it at ranking time improves evidence retrieval for citation-resolution queries. We evaluate this through a sequence of progressively richer interventions, all oracle-free: they extract locator information from the query and chunk text alone, without access to structured candidate metadata fields.

The experiment uses a pre-registered kill condition: if preserving or parsing locator metadata fails to improve evidence top-1 by at least 10 percentage points over stripped-body retrieval, the branch is terminated. We report results against this threshold on both a typed-locator subset (n=161) and a full weak-label set including noisy numeric-only cross-references (n=300).

## 2. Method

### 2.1 Data

The benchmark uses 300 weak-labeled citation-locator examples derived from PMC natural documents. These were acquired from a parent project's public-PMC weak-label artifacts (`data/pmc_weak_citation_locator.jsonl`) along with mined passage data (`data/pmc_mined_passages.jsonl`) and a manifest (`data/pmc_weak_citation_locator_manifest.json`).

Weak labels associate a citation query with a gold evidence chunk. Each query contains a locator string (e.g., "Table 2", "Section 4.1") and optionally author/year information. The default evaluation filters noisy numeric-only cross-reference labels (e.g., locator "2" without a type prefix), yielding 161 typed-locator examples. A robustness evaluation on all 300 examples is also reported.

### 2.2 Interventions

All interventions hide oracle candidate fields (`author`, `year`, `locator`, `page`, `ref_id`) from the ranking procedure and use only chunk text. The interventions are:

1. **Stripped body similarity (baseline).** Citation/table/figure markers are removed from paragraph text. Ranking uses token overlap between the stripped query and stripped chunk.

2. **Preserved text similarity.** Raw natural paragraph text is used with locators intact. No explicit locator parsing; the locator terms simply participate in token overlap.

3. **Parsed locator intervention.** Locator strings are parsed from the preserved query text. Candidate chunks receive a boost if their text contains a matching locator.

4. **Locator window intervention.** Similar to parsed locator, but restricts the scoring window to text near the matching locator span within the chunk.

5. **Locator-local expansion.** Each preserved paragraph is split into bounded local chunks around extracted locator mentions, using neighboring locator midpoints plus radius and sentence trimming. Expanded chunks are ranked using extracted-locator and local-text overlap. Evaluation is at the parent evidence-id level. This intervention produced an average of 9.32 candidates per example and recovered a query-locator local chunk for 98.14% of gold examples.

6. **Citation-neighborhood tie-breaking.** Built on top of locator-local expansion. Parses author/year strings from the query text and adds a secondary citation-neighborhood cue only when the local chunk already matches the parsed query locator. This guard prevents noisy numeric-only cross-references from being driven by author matches in the absence of a typed locator.

### 2.3 Evaluation Metrics

- **answer_exact:** Fraction of examples where the top-ranked candidate exactly matches the gold answer.
- **evidence_top1:** Fraction of examples where the top-ranked candidate's parent evidence ID matches the gold evidence ID.
- **MRR:** Mean reciprocal rank of the first correct evidence ID in the ranked list.

### 2.4 Stratified Manual Audit

A stratified audit samples cases from four strata: intervention wins (intervention correct, baseline incorrect), intervention regressions (baseline correct, intervention incorrect), shared successes, and shared failures. Each stratum contributes 8 cases, yielding 32 audited rows. Cases are assessed as plausible correct, residual multi-locator collision, or locator-collision/context-mismatch failure.

### 2.5 Implementation

The benchmark is implemented in `scripts/citation_locator_intervention_benchmark.py`. All scoring uses CPU regex and token-overlap computation. No GPU or inference server is required. The script was validated with `python3 -m py_compile` and executed successfully for both the typed-locator and all-xref configurations.

## 3. Results

### 3.1 Typed-Locator Results (n=161)

| Intervention | answer_exact | evidence_top1 | MRR |
|---|---|---|---|
| Stripped body | 0.3478 | 0.2919 | 0.5241 |
| Preserved text | 0.4472 | 0.3727 | 0.6091 |
| Parsed locator | 0.6460 | 0.5280 | 0.7312 |
| Locator window | 0.6211 | 0.5031 | 0.7156 |
| Locator-local expansion | 0.6584 | 0.5280 | 0.7266 |
| Citation-neighborhood tie-breaker | 0.6646 | 0.5342 | 0.7318 |

The citation-neighborhood tie-breaker improves evidence_top1 by +0.2423 over the stripped-body baseline, exceeding the pre-registered +0.10 kill threshold. The largest single gain comes from the transition from preserved text to parsed locator interventions (+0.1553 evidence_top1). The incremental gain from locator-local expansion over parsed locator is +0.0000 on evidence_top1 (both 0.5280) but +0.0124 on answer_exact. The citation-neighborhood tie-breaker adds a further +0.0062 on both answer_exact and evidence_top1 over locator-local expansion, correcting 1 top-1 case with 0 new regressions.

Author/year cues are sparse in the gold data: an author cue is available for 24.22% of typed gold local chunks, and an author-year pair for 20.50%, which explains the modest incremental gain from the tie-breaker.

### 3.2 All-Xref Robustness Results (n=300)

| Intervention | answer_exact | evidence_top1 | MRR |
|---|---|---|---|
| Stripped body | 0.3133 | 0.2700 | 0.5241 |
| Locator-local expansion | 0.5433 | 0.4267 | 0.6470 |
| Citation-neighborhood tie-breaker | 0.5467 | 0.4300 | 0.6498 |

Including noisy numeric-only cross-reference labels reduces absolute performance across all interventions. The tie-breaker delta versus stripped body is +0.1600 on evidence_top1, still above the kill threshold but substantially smaller than on the typed-locator subset. The tie-breaker adds +0.0033 evidence_top1 over locator-local expansion in this setting.

### 3.3 Stratified Audit

The 32-row stratified audit (8 intervention wins, 8 intervention regressions, 8 shared successes, 8 shared failures) yielded the following assessment counts:

- 12 plausible locator-local expansion correct
- 4 plausible citation-neighborhood tie-break correct
- 8 residual multi-locator collisions after local expansion
- 8 locator-collision or context-mismatch failures

The 8 intervention regressions are a notable negative finding: the intervention does not uniformly improve over the baseline. The 8 residual multi-locator collisions reflect the fact that 40.37% of gold chunks mention multiple locators, so paragraph-level and even locator-local chunking can still produce ambiguous matches. The 8 context-mismatch failures indicate cases where the locator matches but the surrounding text is semantically unrelated to the query.

### 3.4 Intermediate Results

For completeness, the locator-window intervention (an earlier design before local expansion) achieved evidence_top1 of 0.5031, a +0.2112 improvement over stripped body. This intermediate result alone exceeded the kill threshold, motivating the subsequent refinement to locator-local expansion.

## 4. Limitations

1. **Weak labels.** The 300 examples are derived from automated PMC mining, not human-verified gold annotations. Label noise may inflate or deflate metrics in ways that are difficult to quantify without a dedicated human annotation effort.

2. **Small scale.** The benchmark contains 300 examples (161 typed-locator). Generalization to other domains, document types, or larger corpora is not established.

3. **Token-overlap scoring only.** All interventions use CPU regex and token-overlap ranking. Results may differ substantially with neural retrieval (dense embedding, cross-encoder re-ranking), and the relative benefit of locator preservation could be larger or smaller in such settings.

4. **No neural or production validation.** These are prototype/simulation results over weak labels, not production pipeline measurements. No GPU, CUDA, or inference server was involved.

5. **Intervention regressions.** The stratified audit identifies 8 cases where the intervention regresses relative to the baseline. The intervention is not uniformly beneficial.

6. **Multi-locator ambiguity.** Approximately 40% of gold chunks contain multiple locator mentions, limiting the granularity achievable with paragraph-level or even locator-local chunk splitting. Finer chunking or full-document citation graph extraction may be needed.

7. **Sparse author/year cues.** Only 24.22% of typed gold local chunks contain an author cue, and 20.50% contain an author-year pair. The citation-neighborhood tie-breaker's contribution is correspondingly limited.

8. **No external replication.** Results have not been replicated on independent datasets or by independent evaluators.

9. **Confidence and evidence strength.** The project decision assigns confidence "medium" and evidence strength "moderate." These assessments reflect the above limitations.

## 5. Reproducibility Checklist

- **Data availability:** Input data files are listed in the artifact manifest (`data/pmc_weak_citation_locator.jsonl`, `data/pmc_mined_passages.jsonl`, `data/pmc_weak_citation_locator_manifest.json`).
- **Code availability:** The benchmark script is `scripts/citation_locator_intervention_benchmark.py`.
- **Compute requirements:** CPU only; no GPU or inference server required.
- **Random seeds:** The benchmark uses deterministic regex and token-overlap scoring; no stochastic components are described in the run notes.
- **Evaluation script validation:** `python3 -m py_compile scripts/citation_locator_intervention_benchmark.py` passed prior to each execution.
- **Result artifacts:** All result files are listed in the artifact manifest and were written by the benchmark script.
- **Audit procedure:** Stratified manual audit of 32 cases is recorded in `results/stratified_manual_audit.jsonl` and `results/stratified_manual_audit_all_xrefs.jsonl`.
- **Pre-registered threshold:** The kill condition (+0.10 evidence_top1 improvement) was specified before the experiment and is documented in `run_notes.md`.

## 6. Conclusion

Preserving and exploiting citation locator metadata in chunk text produces substantial improvements over stripped-body retrieval for citation-resolution queries on PMC weak-labeled data. The best intervention (citation-neighborhood tie-breaking) improves evidence top-1 by +0.2423 on typed-locator examples and +0.1600 on all-xref examples, both exceeding the pre-registered +0.10 threshold. The dominant gain comes from explicit locator parsing and local expansion; the author/year tie-breaker adds a small but consistent positive increment.

However, the improvement is not uniform: 8 of 32 audited cases show intervention regressions, and residual failures from multi-locator collisions and context mismatches remain substantial. The results are limited to CPU token-overlap scoring over 300 weak-labeled examples and have not been validated with neural retrieval or human-verified gold labels. The project decision is to finalize positive with medium confidence and moderate evidence strength, recommending that the benchmark artifacts be used to justify locator-preserving chunking with locator-local expansion and optional citation-neighborhood tie-breaking in the parent citation-resolution pipeline, while acknowledging that remaining failures likely require richer full-document citation/reference graph extraction.

---

## Referenced Artifacts

### Result files
- `results/locator_intervention_eval.json`
- `results/locator_intervention_eval_all_xrefs.json`
- `results/stratified_manual_audit.jsonl`
- `results/stratified_manual_audit_all_xrefs.jsonl`
- `results/intervention_summary.md`
- `results/intervention_summary_all_xrefs.md`

### Source and data files
- `scripts/citation_locator_intervention_benchmark.py`
- `data/pmc_weak_citation_locator.jsonl`
- `data/pmc_mined_passages.jsonl`
- `data/pmc_weak_citation_locator_manifest.json`

### Decision and audit files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `run_notes.md`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
