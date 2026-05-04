> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, benchmark outputs, and decision records). The operator who released these artifacts claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact.

---

# The Noisy-Web Distillation Gauntlet: A Synthetic Benchmark for Exposing Source-Awareness Failure Modes in Web Distillation

## Abstract

We present the Noisy-Web Distillation Gauntlet, a dependency-free synthetic benchmark that generates HTML-like pages containing trusted current sources, stale trusted sources, untrusted distractors, boilerplate, advertisements, and prompt-injection-like text. The benchmark evaluates whether a distillation policy can correctly identify and extract information from trustworthy, current sources under controlled noise. We compare two deterministic baselines: a naive latest-mention policy (selecting the most recent dated mention matching the query entity and attribute, regardless of source trust) and a trusted-distiller policy (stripping boilerplate and injection carriers, preferring current trusted sources, falling back to stale trusted sources, and abstaining on unresolved trusted conflicts). Across 10 seeds of 100 queries each (10 distractors per query, 70% conflict rate), the naive latest-mention baseline achieved a mean exact accuracy of 10.1% (SD 2.2%) and a mean unsupported-answer rate of 97.5% (SD 1.4%), while the trusted distiller achieved 100% exact and citation accuracy with zero unsupported answers. These results are scoped to a controlled synthetic setting where trusted and current metadata is available as ground truth; they do not constitute a claim that LLM-based distillers will perform similarly on real web corpora. The benchmark is reproducible, requires no private APIs or manual labeling, and exposes a specific class of noisy-web failure that devastates recency-only policies.

## 1. Introduction

Retrieval-augmented generation (RAG) and web distillation systems must extract factual answers from web pages that vary widely in trustworthiness, recency, and noise. Prior work on the Comprehensive RAG Benchmark (CRAG) frames modern RAG evaluation as factual question answering over dynamic, noisy web and knowledge-graph evidence, reporting that straightforward RAG remains far from fully trustworthy. The CRAG framework provides mock APIs for web and knowledge-graph search and uses rule-based and LLM-based scoring categories that penalize hallucinated or incorrect answers.

A complementary need exists for a compact, fully local, reproducible benchmark that can expose specific failure modes in web distillation without requiring access to private APIs, external model endpoints, or manually labeled datasets. Such a benchmark would serve as a development harness: a gauntlet that stress-tests a distillation policy's ability to handle conflicting sources, stale information, distractors, and adversarial text.

This paper describes the Noisy-Web Distillation Gauntlet, a synthetic benchmark implemented as a single dependency-free Python script. The benchmark generates HTML-like pages with known gold answers and controlled noise, then evaluates deterministic distillation policies against those gold answers. Our primary research question is: can a compact, reproducible noisy-web gauntlet expose failure modes in web/RAG distillation and provide a measurable improvement target without relying on private APIs or manual labeling?

We answer affirmatively, with important scope limitations. The gauntlet reveals that a naive latest-mention policy—selecting the most recent mention matching the query—is catastrophically brittle under recent conflicting web noise, while a source-aware policy that respects trust and recency metadata can eliminate this specific failure class. However, the benchmark operates on synthetic HTML with supplied metadata, and no LLM was evaluated. Closing the gap to real-world distillation performance remains future work.

## 2. Method

### 2.1 Benchmark Design

The benchmark (`src/noisy_web_gauntlet.py`) generates synthetic HTML-like pages for each query. Each query targets a specific entity–attribute pair (e.g., a company's CEO or a product's price). The generated pages include:

- **One trusted current source**: a page containing the correct, current gold answer, marked as trusted and current.
- **Zero or one stale trusted source**: a page containing a previously correct but now outdated answer, marked as trusted but stale.
- **Multiple untrusted distractors**: recent pages containing conflicting values for the same entity–attribute pair, marked as untrusted. The number of distractors is configurable (default 10 in the full run).
- **Boilerplate, advertisements, and comment sections**: noise text embedded in the HTML structure.
- **Prompt-injection-like text**: adversarial strings designed to mimic injection attacks in web content.

The conflict rate (fraction of queries where untrusted distractors actively contradict the gold answer) is configurable. In the full experiment, the conflict rate was set to 0.7.

### 2.2 Entity/Attribute Space

The benchmark uses a fixed vocabulary of 20 entities and 6 attributes per entity, yielding 120 unique entity–attribute combinations. This cardinality constraint directly limits the number of non-duplicate queries. An initial stress run at 200 queries exceeded this limit and produced trusted-current duplicate conflicts, demonstrating why cardinality controls are necessary. The accepted headline run was therefore capped at 100 queries per seed.

### 2.3 Evaluated Policies

Two deterministic baselines are implemented within the benchmark:

1. **naive_latest_mention**: Selects the latest dated mention matching the query entity and attribute, independent of source trust or staleness. This policy never abstains.

2. **trusted_distiller**: Strips boilerplate and injection carriers from pages, prefers current trusted sources, falls back to stale trusted sources only when no current trusted source is available, and abstains when unresolved trusted conflicts exist. This policy has access to the trust and recency metadata supplied by the benchmark.

### 2.4 Metrics

For each policy, the benchmark reports:

- **exact_accuracy**: Fraction of queries where the extracted answer exactly matches the gold answer.
- **citation_accuracy**: Fraction of queries where the cited source is the correct trusted current source.
- **unsupported_rate**: Fraction of queries where the extracted answer is not supported by any trusted source (i.e., the answer is drawn from an untrusted or stale source, or is fabricated).
- **abstain_rate**: Fraction of queries where the policy declines to answer.

### 2.5 Experimental Protocol

The full experiment consisted of 10 independent runs with seeds 1 through 10. Each run generated 100 queries with 10 distractors per query and a conflict rate of 0.7. Results were aggregated across seeds, reporting mean, standard deviation, min, and max for each metric.

A preliminary smoke test (seed 11, 10 queries, 4 distractors) was run to verify pipeline correctness before the full experiment.

### 2.6 Environment

All runs were executed on a Linux host (kernel aarch64, hostname `gx10-efe8`) with 121 GiB total memory and 116 GiB available at run start. An NVIDIA GB10 GPU was visible to the system but remained at 0% utilization throughout; the benchmark is implemented using only the Python standard library and performs no GPU computation. Swap was configured to 0 bytes, consistent with project constraints.

## 3. Results

### 3.1 Smoke Test

The smoke test (10 queries, seed 11, 4 distractors) confirmed pipeline correctness. The naive latest-mention baseline achieved 10% exact accuracy, 10% citation accuracy, and 90% unsupported rate. The trusted distiller achieved 100% on all accuracy metrics with 0% unsupported rate. Both policies had 0% abstain rate.

### 3.2 Full Experiment

Table 1 summarizes the aggregate results across 10 seeds × 100 queries.

**Table 1.** Aggregate metrics across 10 seeds (100 queries each, 10 distractors, 70% conflict rate).

| Metric | naive_latest_mention (mean ± SD) | trusted_distiller (mean ± SD) |
|---|---|---|
| exact_accuracy | 0.101 ± 0.022 | 1.000 ± 0.000 |
| citation_accuracy | 0.025 ± 0.014 | 1.000 ± 0.000 |
| unsupported_rate | 0.975 ± 0.014 | 0.000 ± 0.000 |
| abstain_rate | 0.000 ± 0.000 | 0.000 ± 0.000 |

Naive latest-mention exact accuracy ranged from 0.08 to 0.15 across seeds; citation accuracy ranged from 0.00 to 0.04. The unsupported rate ranged from 0.96 to 1.00. The trusted distiller achieved perfect scores on all accuracy metrics across all 10 seeds, with zero variance.

### 3.3 Interpretation

The naive latest-mention policy is severely degraded by recent conflicting untrusted sources. At a 70% conflict rate with 10 distractors per query, the most recent mention is overwhelmingly likely to originate from an untrusted distractor, yielding a 97.5% unsupported-answer rate and only 10.1% exact accuracy.

The trusted distiller's perfect performance is expected given the benchmark design: every query includes exactly one trusted current source containing the gold answer, and the policy has direct access to trust and recency metadata. This result confirms that the benchmark correctly encodes its intended structure and that the source-aware policy successfully exploits that structure. It does not demonstrate that an LLM-based distiller would achieve comparable performance, since real-world systems must infer trust and recency rather than receiving them as ground truth.

### 3.4 Cardinality Constraint Discovery

The initial 200-query stress run revealed that exceeding the 120 unique entity–attribute combinations produced trusted-current duplicate conflicts, where multiple queries targeting the same entity–attribute pair generated inconsistent gold answers. This finding motivated the reduction to 100 queries per seed and highlights a design constraint: the current entity/value space is too small to support larger query counts without duplication. Results from the stress run are preserved in `results/full/` but are excluded from headline metrics.

## 4. Limitations

1. **Synthetic HTML only.** The generated pages use simplified templates that do not model JavaScript rendering, crawling failures, paywalls, malformed markup, multilingual content, or the full structural complexity of production web pages.

2. **Metadata availability.** The trusted distiller relies on trust and recency metadata supplied directly by the benchmark. Real-world crawls typically lack such metadata and must infer source trustworthiness and content freshness from indirect signals, which is itself an unsolved problem.

3. **No LLM evaluation.** This benchmark evaluates deterministic policies, not LLM-based summarizers or answer extractors. The extent to which LLM distillers exhibit the same failure modes—or can recover from them—remains untested.

4. **Small entity/value space.** The current vocabulary of 20 entities × 6 attributes = 120 unique combinations limits the maximum number of non-duplicate queries. Scaling beyond 100 queries per seed requires expanding this space.

5. **No real-web validation.** The benchmark has not been validated against CRAG-style real or simulated web corpora with human labels. The gap between synthetic and real-world performance is unknown.

6. **Deterministic noise.** The noise patterns (boilerplate, ads, injection-like text) follow fixed templates. Real web noise is more diverse and adversarial.

7. **Zero abstention in both policies.** Neither policy abstained in the full experiment. The trusted distiller's abstention mechanism (for unresolved trusted conflicts) was not exercised because the benchmark guarantees exactly one current trusted source per query. The abstention pathway remains unvalidated at scale.

## 5. Reproducibility Checklist

- **Code availability**: The benchmark is implemented in a single file (`src/noisy_web_gauntlet.py`) using only the Python standard library. No external dependencies are required.
- **Random seed control**: All runs accept a `--seed` argument. Seeds 1–10 were used for the full experiment; seed 11 for the smoke test.
- **Configuration parameters**: Full experiment: `--queries 100`, `--distractors 10`, `--conflict-rate 0.7`. Smoke test: `--queries 10`, `--distractors 4`.
- **Output artifacts**: Per-seed predictions (`results/full100/predictions_seed*_q100.csv`), per-seed datasets (`results/full100/dataset_seed*_q100.jsonl`), smoke-test summary (`results/smoke2/summary_seed11_q10.json`), and aggregate summary (`results/full100/aggregate_summary.json`).
- **Execution logs**: `logs/smoke.log`, `logs/full100_run.log`, `logs/aggregate_full100.log`.
- **Hardware**: CPU-only execution on aarch64 Linux; no GPU required. 121 GiB system memory available.
- **Statistical reporting**: Mean, standard deviation, min, max, and sample size (n=10 seeds) reported for all metrics.
- **Result classification**: These are toy simulation / synthetic benchmark results. No CUDA kernels, no llama.cpp hook prototypes, no production validation runs were performed.

## 6. Conclusion

The Noisy-Web Distillation Gauntlet provides a reproducible, dependency-free benchmark that exposes a specific and severe failure mode in web distillation: when recent untrusted sources conflict with trusted sources, a naive latest-mention policy collapses to approximately 10% exact accuracy and 97.5% unsupported answers. A source-aware policy that respects trust and recency metadata eliminates this failure class entirely in the controlled synthetic setting.

These results are positive but narrowly scoped. The benchmark demonstrates viability as a local development harness for noisy-web distillation failure modes, but it does not establish that LLM-based distillers will perform comparably on real web pages where trust and recency must be inferred rather than supplied. The entity/value space is small, the HTML is synthetic, and no model was evaluated.

The benchmark's primary value is as a measurable improvement target and a diagnostic tool. Future work should expand the entity/value generator, incorporate real HTML fixtures, add metadata-inference variants where trust and freshness are latent, and evaluate LLM summarizers and answer extractors against the same CSV/JSONL evaluation protocol. Integration with CRAG-style real or simulated web corpora would further validate whether the failure modes exposed here generalize to production settings.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Benchmark script | `src/noisy_web_gauntlet.py` |
| Run notes | `run_notes.md` |
| Project decision record | `.omx/project_decision.json` |
| Smoke-test summary | `results/smoke2/summary_seed11_q10.json` |
| Aggregate summary | `results/full100/aggregate_summary.json` |
| Per-seed predictions | `results/full100/predictions_seed*_q100.csv` |
| Per-seed datasets | `results/full100/dataset_seed*_q100.jsonl` |
| Smoke-test log | `logs/smoke.log` |
| Full-run log | `logs/full100_run.log` |
| Aggregate log | `logs/aggregate_full100.log` |
| Stress-run results (excluded from headline) | `results/full/` |
| Claim ledger | `papers/source-record-redacted-20260430T164448343954+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T164448343954+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T164448343954+0000/paper_manifest.json` |
| External reference: CRAG paper | `https://arxiv.org/abs/2406.04744` |
| External reference: CRAG repository | `https://github.com/facebookresearch/CRAG` |
