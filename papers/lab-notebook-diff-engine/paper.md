# Lab Notebook Diff Engine: A Dependency-Free Semantic Diff Prototype for Scientific Notebook Revisions

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, evidence bundles, claim ledgers, benchmark results, and decision JSON). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We describe a lightweight, dependency-free semantic diff engine that compares revisions of Markdown and Jupyter lab notebooks by extracting and comparing domain-specific facts—sections, measurements, tags, dates, attachments, bullet items, and paragraph notes—rather than raw text lines. On a controlled synthetic fixture of 8 gold-labeled high-signal changes, the engine achieves precision 1.0, recall 1.0, and F1 1.0. A scaling smoke test comparing documents up to 478,776 bytes completes in a median of 0.168 s (approximately 2.85 MB/s) with negligible memory impact on a machine with over 122 GB available RAM. These results demonstrate local feasibility of the approach but do not establish production-level accuracy: the evaluation is synthetic and small, the parser is regex/rule-based and does not handle tables, chemical formulas, image contents, or robust unit conversion, and no real lab notebook corpus was available for validation. The structured claim ledger for this artifact remains in a blocked-empty state, meaning no formal claims have passed audit. We discuss the design, a repeated-section identity bug discovered during scaling, the fix via hierarchical heading paths, and the remaining limitations that must be addressed before external validity can be claimed.

## Introduction

Scientific lab notebooks—whether maintained as Markdown files, Jupyter notebooks, or structured documents—accumulate revisions over the course of experiments. Standard diff tools (e.g., `diff`, Git line-level diffs) operate on raw text and report line-level additions, deletions, and modifications. For scientific notebooks, this output is often low-signal: a single measurement update may be buried among hundreds of formatting or boilerplate changes, and the diff does not distinguish a measurement delta from a tag addition or a protocol edit.

The research question motivating this work is: *Can a lightweight local diff engine produce more useful lab-notebook revision evidence than raw line diffs by surfacing domain facts such as measurement changes, protocol edits, tags, conclusions, and attachments?*

We approach this by building a prototype engine that extracts structured, notebook-aware facts from each revision, assigns each fact a stable semantic identity, and then compares the two fact sets to emit structured JSON changes with measurement deltas and high-signal summaries. The engine is dependency-free (pure Python, no external packages) and operates locally, making it potentially suitable for environments where data privacy or air-gapped operation is required.

This paper reports the design, implementation, evaluation on controlled fixtures, scaling behavior, a bug discovered during scaling, and the honest limitations of the current prototype. We are explicit about what the evidence supports and what it does not.

## Method

### Fact Extraction

The engine parses Markdown and Jupyter (`.ipynb`) notebook files and extracts the following fact types:

- **Sections**: Identified by Markdown headings. Each section is assigned a hierarchical path (e.g., `day 1 > results`) to disambiguate repeated section names across the document.
- **Measurements**: Key-value pairs recognized by regex patterns covering common scientific notations (activity, yield, pH, time, etc.).
- **Tags**: Labels or metadata tags attached to notebook entries.
- **Dates**: Date annotations within the notebook.
- **Attachments**: File paths or references to attached resources.
- **Bullets**: Protocol steps, procedure items, or other bulleted content.
- **Paragraph notes**: Free-text paragraph blocks treated as atomic note units.

### Semantic Identity and Comparison

Each extracted fact is assigned a stable semantic identity based on its type, hierarchical section path, and key (where applicable). Two facts from different revisions are considered the *same fact* if and only if their semantic identities match. The engine then classifies each fact as:

- **Added**: Present in the new revision but not the old.
- **Removed**: Present in the old revision but not the new.
- **Modified**: Present in both revisions with the same identity but different values.

For modified measurements, the engine computes and reports the numeric delta.

### Output Format

The diff output is a structured JSON object containing:

- A list of changes, each annotated with fact type, identity, old value, new value, and (for measurements) the delta.
- A high-signal summary highlighting measurement changes, tag additions/removals, attachment changes, and hypothesis/conclusion edits.

### Implementation

The engine is implemented in a single Python file (`src/lab_notebook_diff.py`) with no external dependencies. An evaluation harness (`src/evaluate_engine.py`) computes precision, recall, and F1 against gold-labeled changes, and runs scaling smoke tests by repeating fixture content. Unit tests reside in `src/test_lab_notebook_diff.py`.

### Bug Discovery and Fix

During scaling tests, a bug was discovered: repeated notebook sections (e.g., multiple "results" sections under different days) collapsed into a single identity because the initial implementation used only the leaf heading name as the identity key. This was fixed by switching to hierarchical heading paths (e.g., `day 1 > results` vs. `day 2 > results`). A regression test (`test_repeated_sections_do_not_collapse`) was added to prevent re-introduction. This bug illustrates the kind of structural ambiguity that can arise in real notebooks and that synthetic fixtures may not initially expose.

## Results

### Gold-Label Evaluation

On the controlled synthetic fixture containing 8 gold-labeled high-signal domain changes (measurement deltas, tag additions, attachment changes), the engine achieved:

| Metric | Value |
|---|---|
| Gold labels | 8 |
| True positives | 8 |
| False positives | 0 |
| False negatives | 0 |
| Precision | 1.0 |
| Recall | 1.0 |
| F1 | 1.0 |
| Sample elapsed time | 0.000424 s |

These numbers reflect performance on a small, controlled, synthetic fixture. They establish that the engine can correctly identify the labeled change types under ideal conditions but do not establish accuracy on real, noisy, or adversarial lab notebook revisions. A perfect score on 8 items is weak evidence of general correctness; it is consistent with both correct behavior and with a fixture that happens to exercise only the cases the engine handles well.

### Scaling Smoke Test

The evaluation harness repeated fixture content to generate progressively larger inputs:

| Bytes compared | Change count | Fact counts (old, new) | Repeats | Median time (s) | Throughput (MB/s) |
|---|---|---|---|---|---|
| 950 | 20 | 22, 23 | 1 | 0.000367 | 2.59 |
| 9,536 | 200 | 220, 230 | 10 | 0.00311 | 3.07 |
| 95,576 | 2,000 | 2,200, 2,300 | 100 | 0.0317 | 3.02 |
| 478,776 | 10,000 | 11,000, 11,500 | 500 | 0.168 | 2.85 |

Throughput remains approximately constant at roughly 2.8–3.1 MB/s across the tested range, suggesting roughly linear scaling with document size. However, the scaling test generates larger inputs by repeating fixture content, which may not represent the structural diversity of real large notebooks. The throughput figures should be interpreted as rough indicators on synthetic data, not as predictions for real-world performance.

Memory impact was negligible on the test machine: MemAvailable decreased from 122,617,296 KiB to 122,587,088 KiB (a delta of approximately 30 MB) during evaluation. The machine had over 122 GB RAM and no swap (SwapTotal: 0 kB). The `earlyoom` daemon was active during testing. Performance and memory behavior on resource-constrained machines (e.g., laptops with 8–16 GB RAM) were not tested.

### Jupyter Notebook Support

The engine produced a structured diff for Jupyter (`.ipynb`) fixtures (`results/ipynb_diff.json`), confirming that the extraction pipeline extends to the notebook JSON format. However, no separate gold-label evaluation was conducted for Jupyter-specific changes, so correctness on Jupyter inputs remains unevaluated beyond visual inspection of the output.

### Unit Tests

Three unit tests passed, including the regression test for repeated section identity (`test_repeated_sections_do_not_collapse`). The small number of tests means coverage is limited.

### Claim Ledger Status

The structured claim ledger for this artifact is in a `blocked_empty_claims` state: no formal claims were extracted or audited. The ledger notes that the artifact must not pass strict claim/evidence audit until claims reference public evidence files. This means the results reported here have not been through a formal internal claim-audit process and should be read accordingly.

## Limitations

1. **Synthetic and small evaluation.** The gold fixture contains only 8 labeled changes. This proves feasibility—the engine can correctly identify the targeted change types under controlled conditions—but does not establish production accuracy on real lab notebooks, which may contain ambiguous formatting, unconventional notation, or change types not represented in the fixture. A perfect F1 on 8 items is weak statistical evidence.

2. **Regex/rule-based extraction.** The parser relies on pattern matching and does not understand tables, chemical formulas, image contents beyond attachment paths, OCR text, or free-form unit conversions. Any fact not matching the current regex patterns will be missed or misclassified. The set of recognized measurement patterns is necessarily incomplete.

3. **Duplicate sibling headings.** While the hierarchical heading path fix resolves repeated sections at different hierarchy levels (e.g., `day 1 > results` vs. `day 2 > results`), duplicate sibling headings with identical titles at the same level may still collide, producing incorrect identity assignments.

4. **No real-corpus validation.** No Notion API or private notebook corpus was available during this run. Integration with Notion or other notebook platforms, and real-user acceptance testing, were not performed. External validity is unknown.

5. **Memory environment.** The test machine had over 122 GB RAM with no swap. Performance and memory behavior on resource-constrained machines (e.g., laptops with 8–16 GB RAM) were not tested and may differ substantially.

6. **Scaling test methodology.** The scaling smoke test generates larger inputs by repeating fixture content, which may not represent the structural diversity of real large notebooks. The throughput figures should be interpreted as rough upper bounds on synthetic data, not as predictions for real-world performance.

7. **Claim audit gap.** The claim ledger is in a blocked-empty state, meaning no structured claims have been formally audited against evidence. The results in this paper have not passed internal claim-audit review.

8. **Jupyter evaluation gap.** While Jupyter notebook parsing produces output, no gold-label evaluation was performed for Jupyter-specific changes, so correctness on that format is unquantified.

## Reproducibility Checklist

- **Source code available:** `src/lab_notebook_diff.py`, `src/evaluate_engine.py`, `src/test_lab_notebook_diff.py`
- **Test fixtures available:** `data/sample_old.md`, `data/sample_new.md`, `data/sample_old.ipynb`, `data/sample_new.ipynb`, `data/gold_changes.json`
- **Output artifacts available:** `results/sample_diff.json`, `results/ipynb_diff.json`, `results/metrics.json`
- **Decision record available:** `.omx/project_decision.json`
- **Execution logs available:** `logs/001_py_compile.log` through `logs/007_environment.log`
- **Dependencies:** None (pure Python 3, no external packages)
- **Commands for reproduction:**
  1. `python3 -m py_compile src/lab_notebook_diff.py src/evaluate_engine.py`
  2. `python3 src/lab_notebook_diff.py data/sample_old.md data/sample_new.md --pretty --unified`
  3. `python3 src/evaluate_engine.py`
  4. `python3 -m unittest discover -s src -p 'test_*.py' -v`
- **Environment details recorded:** `logs/007_environment.log` (kernel version, MemAvailable, SwapTotal, earlyoom configuration)
- **Randomness:** No random seeds were used; the engine is deterministic.
- **Claim ledger status:** `blocked_empty_claims` — no formal claims have been audited.

## Conclusion

A dependency-free semantic diff engine for Markdown and Jupyter lab notebooks has been implemented and evaluated on controlled synthetic fixtures. The engine extracts domain-specific facts (sections, measurements, tags, dates, attachments, bullets, paragraphs), compares them by stable semantic identity, and emits structured JSON changes with measurement deltas and high-signal summaries. On 8 gold-labeled changes, it achieves perfect precision and recall; on synthetic scaling tests up to approximately 479 KB, it processes at roughly 2.85 MB/s with negligible memory impact on a high-RAM machine.

These results establish local feasibility: a small, dependency-free engine can produce more reviewable revision evidence than raw line diffs for structured scientific notebooks under controlled conditions. However, the evaluation is synthetic and small (8 gold labels), the parser has known coverage gaps (tables, chemical formulas, unit conversion, image contents), no real lab notebook corpus was tested, and the claim ledger remains in a blocked-empty state. The prototype should be considered a viability demonstration, not a production-validated tool.

Recommended next steps include: (1) evaluation on 20–50 anonymized real lab notebook revision pairs with human-labeled important changes; (2) addition of table parsing and unit normalization; (3) an HTML/Markdown reviewer report renderer; and (4) Notion export/API integration only after real-corpus signal is confirmed.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Engine source | `src/lab_notebook_diff.py` |
| Evaluation harness | `src/evaluate_engine.py` |
| Unit tests | `src/test_lab_notebook_diff.py` |
| Markdown fixtures | `data/sample_old.md`, `data/sample_new.md` |
| Jupyter fixtures | `data/sample_old.ipynb`, `data/sample_new.ipynb` |
| Gold labels | `data/gold_changes.json` |
| Sample semantic diff | `results/sample_diff.json` |
| Jupyter semantic diff | `results/ipynb_diff.json` |
| Metrics | `results/metrics.json` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260429T230248449297+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T230248449297+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T230248449297+0000/paper_manifest.json` |
| Compile log (initial) | `logs/001_py_compile.log` |
| Sample diff stdout | `logs/002_sample_diff_stdout.json` |
| Evaluation log (initial) | `logs/003_evaluate.log` |
| Compile log (post-fix) | `logs/004_py_compile_after_section_path.log` |
| Evaluation log (post-fix) | `logs/005_evaluate_section_path.log` |
| Unit test log | `logs/006_unittest.log` |
| Environment log | `logs/007_environment.log` |
