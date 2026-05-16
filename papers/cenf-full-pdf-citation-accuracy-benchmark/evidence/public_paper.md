# CENF Full-PDF Citation Accuracy Benchmark

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, benchmark results, and decision JSON). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has verified the claims herein.

---

## Abstract

We present a deterministic, reproducible benchmark for full-PDF citation accuracy applied to a public 80-page literature-review document. The benchmark extracts in-text author-year citation mentions from the body text, extracts bibliography entries from the References section, normalizes both to author-year keys, and scores resolution of mentions against the reference index. On the CENF Numeracy Literature Overview and Review PDF, the benchmark extracted 400 in-text citation mentions (261 unique keys) and 231 bibliography entries (233 unique keys). Of the 400 mentions, 291 resolved to an extracted reference key, yielding a mention resolution rate of 72.75% and a unique-key resolution rate of 67.05%. Manual audit of the most frequent unresolved mentions reveals a heterogeneous population: some correspond to genuinely missing or mismatched bibliography entries, while others are false unresolved cases attributable to parser limitations (multi-author ordering, missing comma before year, pdftotext entry-joining artifacts). The result is therefore a conservative lower-bound feasibility measurement, not a final human-grade citation-error adjudication. The benchmark executes in 0.04 seconds wall-clock time with 14.2 MiB peak RSS on commodity hardware.

---

## Introduction

Citation accuracy—the property that in-text references resolve correctly to bibliography entries—is a basic quality criterion for academic documents. Systematic assessment of citation accuracy across an entire PDF document requires parsing both the body text and the References section, normalizing author-year keys, and matching mentions to entries. Despite the apparent simplicity of this task, real-world PDFs present numerous challenges: inconsistent citation formatting, multi-author entries, text extraction artifacts, and bibliography entries that span line boundaries.

This paper reports on the construction and execution of a small, reproducible, deterministic benchmark for full-PDF citation accuracy. The benchmark is applied to a single public document: the CENF Numeracy Literature Overview and Review, an 80-page PDF containing a literature review with an extensive bibliography. The benchmark is not an LLM citation-generation benchmark; it is a deterministic parser-based measurement of citation/reference consistency within a single document.

The central question is: given a deterministic extraction and normalization pipeline, what fraction of in-text citation mentions resolve to the extracted bibliography, and what are the dominant failure modes for unresolved mentions?

---

## Method

### Data Source

The benchmark operates on a single public PDF:

- **Document:** Research CENF Numeracy Literature Overview and Review
- **Source URL:** `https://husite.nl/cenf/wp-content/uploads/sites/349/2024/05/Research-CENF-Numeracy-Literature-Overview-and-Review.pdf`
- **Local file:** `data/cenf_literature_review.pdf`
- **Format:** PDF 1.5, 80 pages, 2.1 MiB
- **SHA256:** `e9696f1a0f35745693aac3a459c7e313ea720a10aa21425f240ad78171219280`
- **Extracted text:** via `pdftotext -layout`, producing 3,413 lines, 28,267 words, 209,085 bytes (stored as `data/cenf_literature_review.txt`)

### Benchmark Pipeline

The benchmark script (`scripts/citation_benchmark.py`) performs the following steps:

1. **Region splitting.** The extracted text is split into body, References, and annex regions using document heading markers. This yields an estimated 42 body pages and 18 reference pages.

2. **Bibliography extraction.** Entries are extracted from the References region. Each entry is parsed to produce a normalized author-year key. The pipeline extracted 231 reference entries yielding 233 unique reference keys. The slight excess of keys over entries arises from entries that produce multiple normalized keys (e.g., multi-author entries generating keys under different first-author orderings).

3. **Citation mention extraction.** In-text author-year mentions are extracted from all body pages, covering both parenthetical citations (e.g., "(Smith, 2020)") and narrative citations (e.g., "Smith (2020)"). The pipeline extracted 400 citation mentions yielding 261 unique citation keys.

4. **Resolution scoring.** A mention is scored as resolved when its normalized author-year key appears in the reference-key index. This is a strict deterministic match; no fuzzy matching or disambiguation is applied.

5. **Unresolved audit.** Unresolved mentions are tabulated and the most frequent cases are audited manually to classify failure modes.

### Unit Tests

A companion test suite (`scripts/test_citation_benchmark.py`) validates parser components. Unit test results are recorded in `logs/08_unit_tests.log`.

### Resource Measurement

The timed benchmark was executed under `/usr/bin/time -v` on a system with approximately 116 GiB available memory and no swap (consistent with project constraints). Wall-clock time and peak RSS were recorded.

---

## Results

### Primary Metrics

| Metric | Value |
|--------|-------|
| PDF pages | 80 |
| Body pages (estimated) | 42 |
| Reference pages (estimated) | 18 |
| Reference entries extracted | 231 |
| Unique reference keys | 233 |
| Citation mentions extracted | 400 |
| Unique citation keys | 261 |
| Resolved mentions | 291 |
| Unresolved mentions | 109 |
| Mention resolution rate | 72.75% |
| Unique-key resolution rate | 67.05% |

### Runtime and Resource Usage

| Metric | Value |
|--------|-------|
| Wall-clock time | 0.04 s |
| Peak RSS | 14,572 KiB (~14.2 MiB) |
| Available memory | ~116 GiB |
| Swap | 0 KiB (none configured) |

This is a small CPU/text benchmark. The runtime and memory figures are not representative of large-scale or GPU-based workloads; they are reported solely for reproducibility calibration.

### Unresolved Mention Audit

The 109 unresolved mentions are not a homogeneous population. Manual audit of the most frequent unresolved keys (recorded in `results/citation_benchmark_final/top_unresolved_audit.md`) reveals three categories:

1. **Likely missing or secondary bibliography entries.** Keys such as `cockcroft:1982`, `crowther:1959`, `arney:2002`, `barwell:2004`, `faragher:2005`, and `tickly:2000` have no matching author in the extracted references. These are candidate genuine citation/reference mismatches—citations present in the body with no corresponding bibliography entry found by the parser.

2. **Author present but cited year absent.** Keys such as `diez-palomar:2020`, `tout:1997`, `gal:1999`, and `lave:1991` have a matching author in the bibliography but not with the cited year. These may represent edition-year discrepancies or citation errors.

3. **Parser false unresolved.** Keys such as `anderson:2000`, `o campo:2020`, and `coben:2006b` have exact author-year evidence in the extracted reference list but are missed by the resolution step. Root causes include multi-author ordering differences (the first author in the citation is not the first author in the bibliography entry), a missing comma before the year in the bibliography entry, and pdftotext entry-joining artifacts that corrupt the parsed reference key.

The relative proportions of these three categories have not been quantified precisely; doing so would require human bibliographic adjudication across all 109 unresolved mentions. The existence of category 3 confirms that the measured resolution rate is a conservative lower bound.

---

## Limitations

1. **Single-document scope.** The benchmark is applied to one PDF. Generalization to other documents, disciplines, or citation styles is not established.

2. **Deterministic parser, not an LLM benchmark.** This benchmark measures citation/reference consistency under a specific parsing pipeline. It does not evaluate LLM citation generation, retrieval-augmented generation, or any model's ability to produce accurate citations.

3. **Conservative lower-bound resolution rate.** The measured 72.75% mention resolution rate is a lower bound on true citation accuracy for this document. The unresolved population includes confirmed parser false negatives (category 3 above), meaning the true resolution rate is higher than reported. The magnitude of the upward correction is unknown without human adjudication.

4. **Parser limitations.** The normalization and matching logic is intentionally simple (strict author-year key matching). It does not handle: multi-author citation forms where the citing author is not the first-listed bibliography author; bibliography entries with non-standard formatting (e.g., missing comma before year); pdftotext line-joining artifacts; numeric citation styles; or footnote-based citation systems.

5. **No human adjudication.** Converting the 109 unresolved mentions into final publication-grade citation-error labels requires human bibliographic review, which was not performed.

6. **pdftotext dependency.** Text extraction quality depends on `pdftotext -layout`. Different extraction tools or parameters may yield different results.

7. **Region splitting heuristic.** The body/References/annex split relies on heading markers in the extracted text. Documents with ambiguous or non-standard section headings could cause region misassignment.

---

## Reproducibility Checklist

- [x] **Data source specified.** Public URL, local filename, SHA256 hash, and file metadata are recorded.
- [x] **Extraction tool and parameters documented.** `pdftotext -layout` with input and output paths.
- [x] **Benchmark script versioned.** `scripts/citation_benchmark.py` is the deterministic pipeline.
- [x] **Unit tests provided.** `scripts/test_citation_benchmark.py` with log at `logs/08_unit_tests.log`.
- [x] **All outputs archived.** Metrics JSON, mentions CSV, unresolved mentions CSV, references JSON, and top-unresolved audit are in `results/citation_benchmark_final/`.
- [x] **Execution logs preserved.** All command logs from `logs/01_download.log` through `logs/08_unit_tests.log`.
- [x] **Runtime and resource telemetry recorded.** Wall-clock time, peak RSS, available memory, and swap configuration from `logs/07_timed_run_and_telemetry.log`.
- [x] **Deterministic pipeline.** No random seeds or stochastic components; re-execution on the same input with the same tools should produce identical results.
- [ ] **Human adjudication of unresolved mentions.** Not performed; identified as a limitation.
- [ ] **Cross-document validation.** Not performed; single-document study.

---

## Conclusion

A deterministic full-PDF citation accuracy benchmark was constructed and applied to the CENF Numeracy Literature Overview and Review. The benchmark extracted 400 in-text citation mentions and 231 bibliography entries from the full PDF text, resolving 291 mentions (72.75%) to extracted reference keys. The 67.05% unique-key resolution rate and 109 unresolved mentions constitute a conservative lower-bound measurement: audit of the most frequent unresolved cases confirms that some are parser false negatives rather than genuine citation errors, while others correspond to plausible missing or mismatched bibliography entries.

The benchmark is reproducible, executes in under 0.1 seconds on commodity hardware, and produces auditable intermediate artifacts (mention lists, reference indices, unresolved audits). The primary scientific contribution is a positive feasibility result: a simple deterministic pipeline can extract and resolve the majority of author-year citations in a real-world literature-review PDF, and the unresolved remainder can be triaged into actionable categories for human review.

The unresolved rate of 27.25% of mentions underscores that deterministic parsing alone is insufficient for complete citation-error adjudication. Human bibliographic review remains necessary to distinguish genuine citation/reference discrepancies from parser artifacts, and to quantify the true accuracy of the document's citation practice.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Source PDF | `data/cenf_literature_review.pdf` |
| Source PDF SHA256 | `data/cenf_literature_review.sha256` |
| Extracted text | `data/cenf_literature_review.txt` |
| Benchmark script | `scripts/citation_benchmark.py` |
| Unit test script | `scripts/test_citation_benchmark.py` |
| Final metrics | `results/citation_benchmark_final/metrics.json` |
| All mentions | `results/citation_benchmark_final/mentions.csv` |
| Unresolved mentions | `results/citation_benchmark_final/unresolved_mentions.csv` |
| Extracted references | `results/citation_benchmark_final/references.json` |
| Top unresolved audit | `results/citation_benchmark_final/top_unresolved_audit.md` |
| Timed run log | `logs/07_timed_run_and_telemetry.log` |
| Unit test log | `logs/08_unit_tests.log` |
| Download log | `logs/01_download.log` |
| Smoke benchmark log | `logs/02_smoke_benchmark.log` |
| Iteration logs | `logs/03_benchmark_v1.log` – `logs/06_benchmark_final.log` |
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
