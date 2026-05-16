# Prefix-Equivalence Targeted Normalizer Uplift

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

We present results from a targeted normalizer uplift intervention applied to a prefix-equivalence canonicalizer for prompt-template caching. The parent baseline canonicalizer achieved a pair F1 of 0.792 and a cache true-hit rate of 0.908 on a synthetic benchmark of 3,000 examples. By introducing a targeted synonym map covering nine observed false-negative paraphrase clusters, the uplift canonicalizer achieved a pair F1 of 0.957 and a cache true-hit rate of 0.980, with the cache false-hit rate remaining at 0.000. The pair F1 improvement of 16.5 percentage points exceeds the pre-registered kill condition of 5 percentage points. These results are limited to the synthetic benchmark and paraphrase clusters present in the project artifacts; external replication on production traffic and broader paraphrase distributions is not established.

---

## 1. Introduction

Prompt-template caching systems depend on canonicalizers that map semantically equivalent prompt prefixes to a shared cache key. When users paraphrase the same intent using different surface forms (e.g., "summarize this" vs. "make a tl;dr for this"), a canonicalizer that fails to collapse these variants produces redundant cache keys, reducing hit rates and increasing compute waste.

The parent project established a template canonicalizer baseline for prefix-equivalence detection. Analysis of that baseline's failure clusters revealed systematic false negatives: paraphrases that shared intent with canonical templates but used out-of-template phrasing. This branch project investigates whether a targeted, rule-based synonym normalizer applied to those specific failure clusters can improve canonicalization quality without introducing false cache hits.

The pre-registered kill condition required the uplift to improve template F1 by at least 5 percentage points while producing zero new false cache hits relative to the parent baseline.

---

## 2. Method

### 2.1 Baseline

The parent template canonicalizer (`template_canonical`) serves as the A/B baseline. It normalizes prompt prefixes through template matching and canonical key assignment. Its metrics were recorded in the parent project artifacts and preserved without modification in this branch.

### 2.2 Targeted Uplift Normalizer

The uplift normalizer (`template_targeted_uplift`) extends the parent canonicalizer with a targeted synonym map (`TARGETED_SYNONYM_MAP`) and a normalization function (`norm_template_targeted`). The synonym map was constructed by inspecting false-negative clusters in the parent baseline's results. Each entry maps an observed out-of-template paraphrase to its canonical equivalent.

The nine targeted paraphrase clusters and their canonical mappings are:

| Paraphrase variant | Canonical target |
|---|---|
| make a tl dr for | summarize |
| distill | summarize |
| scan for | find |
| surface | find |
| assign | categorize |
| bucket | categorize |
| polish | rewrite |
| wordsmith | rewrite |
| use the source to answer / give the answer for | answer from context |

These mappings were selected based on observed parent false negatives and are not claimed to be exhaustive for any real-world paraphrase distribution.

### 2.3 Benchmark Design

The benchmark generates a synthetic corpus of 3,000 prompt-prefix examples organized into clusters, with 6 variants per cluster, using seed 3443677. Each cluster represents a semantically coherent intent. Variants within a cluster include both in-template and out-of-template phrasings. The corpus is stored in `artifacts/data/prefix_equivalence_corpus.jsonl`.

Six canonicalization strategies are evaluated and ranked:

1. `oracle_label` — ground-truth cluster labels (upper bound)
2. `template_targeted_uplift` — the proposed uplift normalizer
3. `template_canonical` — the parent baseline
4. `keyword_signature` — keyword-based signature matching
5. `exact` — exact string matching
6. `lower_punct` — lowercasing and punctuation stripping only

### 2.4 Metrics

- **Pair F1**: F1 score computed over all pairs of examples, where a true positive is a pair correctly identified as equivalent (same canonical key and same oracle label).
- **Cache true-hit rate**: Proportion of equivalent pairs that share the same canonical key (recall of the caching system).
- **Cache false-hit rate**: Proportion of non-equivalent pairs that incorrectly share the same canonical key (false collision rate).
- **Unique keys**: Number of distinct canonical keys produced, where fewer keys (at constant false-hit rate) indicate better collapse of equivalent variants.

### 2.5 Kill Condition

The branch was pre-registered to finalize negative if the targeted uplift improved template pair F1 by fewer than 5 percentage points or introduced any new false cache hits relative to the parent baseline.

---

## 3. Results

### 3.1 Primary Metrics

| Metric | Parent (`template_canonical`) | Uplift (`template_targeted_uplift`) | Delta |
|---|---|---|---|
| Pair F1 | 0.791833 | 0.957332 | +0.165499 |
| Cache true-hit | 0.908333 | 0.980000 | +0.071667 |
| Cache false-hit | 0.000000 | 0.000000 | 0.000000 |
| Unique keys | 275 | 60 | −215 |

The uplift normalizer improved pair F1 by 16.55 percentage points and cache true-hit rate by 7.17 percentage points, while the cache false-hit rate remained at zero. The number of unique canonical keys decreased from 275 to 60, indicating substantially better collapse of equivalent variants.

### 3.2 Strategy Ranking

The six strategies ranked as follows on pair F1:

`oracle_label` > `template_targeted_uplift` > `template_canonical` > `keyword_signature` > `exact` > `lower_punct`

The uplift normalizer occupies the second rank, below the oracle upper bound and above all other methods including the parent baseline.

### 3.3 Kill Condition Assessment

The kill condition passed: pair F1 improved by 16.55 percentage points (exceeding the 5-point threshold), and the cache false-hit rate remained at 0.000 (no new false collisions introduced).

### 3.4 Verification

- Unit tests: 5 of 5 passed (`python3 -m unittest discover -s tests -v`).
- Metrics JSON validated (`python3 -m json.tool artifacts/results/prefix_equivalence_metrics.json`).
- Corpus row count confirmed at 3,000 (`wc -l artifacts/data/prefix_equivalence_corpus.jsonl`).

---

## 4. Limitations

1. **Synthetic benchmark only.** The 3,000-example corpus is synthetically generated with 6 variants per cluster. Real-world prompt distributions exhibit greater lexical diversity, longer prompts, and noisier phrasing. Performance on production traffic is not established.

2. **Targeted rule scope.** The synonym map covers only nine paraphrase clusters observed in the parent baseline's failure modes. Coverage of the full space of user paraphrases is unknown. The map is hand-curated and may not generalize to domains or languages beyond those represented in the benchmark.

3. **No production validation.** These results are from a toy simulation benchmark, not from a deployed caching system serving real requests. Latency impact, memory overhead, and behavior under distribution shift have not been measured.

4. **Single benchmark configuration.** All results use a single seed (3443677), a fixed example count (3,000), and a fixed variant count (6 per cluster). Sensitivity to these parameters has not been tested.

5. **No comparison to learned methods.** The uplift is purely rule-based. Whether learned canonicalizers (e.g., embedding similarity, classifier-based equivalence) would outperform or complement the targeted rules has not been investigated.

6. **False-hit rate floor effect.** The cache false-hit rate of 0.000 in both conditions may reflect the benchmark's structure rather than an intrinsic property of the normalizers. A benchmark with more semantically similar but distinct clusters could reveal false-hit behavior not observed here.

7. **Automated provenance.** This draft and the underlying experiment were produced by an automated research pipeline. No independent human replication has been performed.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Benchmark command documented | Yes: `python3 scripts/prefix_equiv_experiment.py --examples 3000 --variants-per-cluster 6 --seed 3443677` |
| Random seed recorded | Yes: 3443677 |
| Corpus size stated | Yes: 3,000 examples |
| Baseline metrics preserved | Yes: parent artifacts in `artifacts/results/parent_prefix_equivalence_metrics.json` |
| Uplift metrics recorded | Yes: `artifacts/results/prefix_equivalence_metrics.json` |
| Code available | Yes: `scripts/prefix_equiv_experiment.py`, `tests/test_prefix_equiv_experiment.py` |
| Pre-registered kill condition | Yes: ≥5 pp F1 improvement, zero new false cache hits |
| Unit tests passing | Yes: 5/5 |
| JSON validation | Yes |
| External replication | No — not performed |

---

## 6. Conclusion

A targeted synonym-map normalizer applied to nine observed false-negative paraphrase clusters improved prefix-equivalence pair F1 from 0.792 to 0.957 (+16.5 pp) and cache true-hit rate from 0.908 to 0.980 (+7.2 pp) on a synthetic 3,000-example benchmark, with no increase in cache false hits. The pre-registered kill condition was met. These findings support the hypothesis that targeted rule-based normalization can substantially improve canonicalization quality for the specific paraphrase clusters present in the benchmark. The results do not establish generalization to production traffic, broader paraphrase distributions, or domains beyond those represented in the synthetic corpus. External replication and evaluation against learned canonicalization methods remain open.

---

## Referenced Artifacts

### Result files
- `artifacts/results/summary.md`
- `artifacts/results/prefix_equivalence_metrics.json`
- `artifacts/data/prefix_equivalence_corpus.jsonl`
- `artifacts/results/parent_summary.md`
- `artifacts/results/parent_prefix_equivalence_metrics.json`
- `artifacts/data/parent_prefix_equivalence_corpus.jsonl`

### Source and configuration files
- `scripts/prefix_equiv_experiment.py`
- `tests/test_prefix_equiv_experiment.py`
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`
- `run_notes.md`

### Paper pipeline artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
