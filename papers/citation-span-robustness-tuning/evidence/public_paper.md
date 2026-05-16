# Citation Span Robustness Tuning: Clause-Aware Span Resolution over a Sentence-Level Baseline

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, benchmark outputs, and logs). The operator claims no personal authorship credit for the writing or results beyond releasing the artifacts. Readers should treat this document as an unreviewed AI-generated research artifact. No human review or endorsement is claimed or implied.

---

## Abstract

We evaluate whether a lightweight, clause-aware citation span resolver can improve robustness over a sentence-level baseline for assigning citation markers to the text spans they support. Using a deterministic synthetic benchmark of 192 examples spanning 408 citation labels across eight perturbation categories, we compare a naive sentence-boundary baseline against a tuned delimiter-based clause segmenter. On the held-out split (65 examples), the clause-aware resolver achieves character-level F1 of 1.0000 and exact match of 1.0000, compared to the baseline's 0.8809 character-level F1 and 0.7174 exact match—deltas of +0.1191 and +0.2826 respectively. These results are provisional: the benchmark is entirely synthetic and may overestimate real-world performance. We report the experiment design, parameter selection, per-split metrics, and known limitations in full.

## Introduction

Citation markers in scientific text frequently appear mid-sentence, at clause boundaries, or within complex syntactic structures such as semicolon-separated clauses, colon-initiated lists, and parenthetical asides. A common baseline for identifying the text span a citation supports is to assign the entire enclosing sentence. This approach is simple but systematically over-extends spans when citations modify only a clause or sub-sentential unit.

The research question addressed here is: *Can clause-aware citation span extraction, tuned on perturbed synthetic citation cases, improve held-out exact span recovery and character-level F1 versus a sentence-level baseline?*

This work is scoped to a controlled, locally reproducible benchmark. No external annotated corpus or human annotation was available. The original project Notion page was not accessible via public web fetch (HTTP 404), so all data and evaluation are synthetic. We treat this as a proof-of-concept study whose generalization to real scientific text remains an open follow-up question.

## Method

### Benchmark Construction

A deterministic synthetic benchmark was generated programmatically with gold citation-to-span labels and common formatting perturbations. The benchmark comprises:

- **192 examples** containing **408 citation labels** total.
- **Three splits:** train (84 examples), validation (43 examples), holdout (65 examples).
- **Eight perturbation categories:**
  1. `and_two_clauses` — two clauses joined by "and" with a citation on one.
  2. `colon_list` — colon-initiated list items with per-item citations.
  3. `nested_parenthetical` — citations inside parenthetical asides.
  4. `range_three` — three-clause ranges with citations on subsets.
  5. `semicolon_two_clauses` — semicolon-delimited clauses with distinct citations.
  6. `sentence_boundary` — citations at sentence boundaries where sentence-level spans are ambiguous.
  7. `shared_cluster` — multiple citations sharing a cluster span.
  8. `single_sentence_two_clauses` — two clauses within one sentence, each with its own citation.

Each example includes a gold span (character-level start and end indices) for every citation marker. Perturbations are designed to stress cases where sentence-level resolution is insufficient.

### Baseline Resolver

The baseline assigns each citation marker to the full sentence in which it appears, using standard sentence-boundary detection (period, question mark, exclamation mark followed by whitespace and an uppercase letter). This represents the simplest reasonable approach and establishes a lower bound on performance.

### Clause-Aware Resolver

The tuned resolver segments text into clause-level units using a configurable delimiter set and a backward character window. Given a citation marker position, the resolver:

1. Scans backward from the marker up to `max_back_chars` characters.
2. Splits the retrieved context on any delimiter in the configured set.
3. Returns the clause segment containing the citation marker as the predicted span.

Parameter tuning was performed on the validation split via grid search over delimiter combinations and `max_back_chars` values.

### Best Parameters

The selected configuration from validation:

| Parameter | Value |
|---|---|
| Delimiters | `.`, `?`, `!`, `;`, `, while `, `, but `, ` and ` |
| `max_back_chars` | 220 |
| `include_colon_prefix` | `false` |

### Evaluation Metrics

- **Character-level F1:** Overlap between predicted and gold spans measured at character granularity.
- **Exact match:** Binary indicator of whether the predicted span exactly equals the gold span (character-level identity).

Both metrics are computed per-citation-label and then averaged across each split.

### Execution Environment

- Python 3.12.3
- CPU-only deterministic experiment (no GPU required)
- Available memory: 115 GiB RAM, 0 B swap
- Single execution run; no stochastic training or random seeds involved beyond synthetic data generation.

## Results

### Per-Split Metrics

| Split | Resolver | Char-F1 | Exact Match | Δ Char-F1 | Δ Exact Match |
|---|---|---|---|---|---|
| Validation | Baseline | 0.8712 | 0.7000 | — | — |
| Validation | Tuned | 1.0000 | 1.0000 | +0.1288 | +0.3000 |
| Holdout | Baseline | 0.8809 | 0.7174 | — | — |
| Holdout | Tuned | 1.0000 | 1.0000 | +0.1191 | +0.2826 |

The clause-aware resolver achieves perfect recovery on both validation and holdout splits. The baseline's errors concentrate in categories where the citation scope is a proper sub-clause of the enclosing sentence: `and_two_clauses`, `semicolon_two_clauses`, `single_sentence_two_clauses`, and `colon_list` cases where the sentence-level span over-extends beyond the relevant clause.

### Error Analysis of Baseline

The baseline's character-level F1 of approximately 0.88 on holdout indicates that, on average, sentence-level spans capture most but not all of the correct characters. The exact match rate of approximately 0.72 confirms that roughly 28% of citation labels have gold spans that are strict sub-spans of the enclosing sentence. These failures are systematic rather than random: they arise from the structural categories designed into the benchmark.

### Tuned Resolver Performance

The tuned resolver's perfect scores on both validation and holdout indicate that, within the scope of the eight perturbation categories and the delimiter set explored, the clause segmentation logic is sufficient to recover gold spans exactly. This is a strong result but must be interpreted in context (see Limitations).

## Limitations

1. **Synthetic benchmark.** All examples are programmatically generated. The perturbation categories, while motivated by common citation formatting patterns, may not represent the full diversity of real scientific text. Perfect scores on this benchmark do not guarantee comparable performance on naturally occurring citation spans.

2. **Category coverage.** The eight categories do not include quotation marks, em-dashes, footnotes, author-year citation styles, or deeply nested syntactic structures. The delimiter set may be insufficient for these cases.

3. **No human annotation.** Gold spans reflect the synthetic generation logic, not human judgments of citation scope. In real text, annotator disagreement on span boundaries is common and the benchmark does not model this variance.

4. **Potential overfitting to perturbation design.** Parameter tuning was performed on the validation split, and the holdout split draws from the same generative process. If the generative process is too narrow, the holdout result may overestimate generalization. The perfect holdout scores should be interpreted as evidence that the resolver handles the designed perturbation types, not as evidence of broad robustness.

5. **Domain specificity.** The benchmark does not cover legal, biomedical, or humanities citation styles, which may use different clause-connecting patterns.

6. **No comparison to parser-based segmenters.** A dependency-parser-backed clause segmenter might achieve similar or better results with different trade-offs (dependency on external NLP models versus rule simplicity). This comparison was out of scope.

7. **Deterministic but narrow.** The experiment is fully deterministic and reproducible, but the narrow scope means the positive result should be treated as *provisional*—a viability signal for the approach, not a validation of production readiness.

## Reproducibility Checklist

- [x] **Code available:** `scripts/citation_span_experiment.py` (single self-contained script).
- [x] **Deterministic execution:** No random seeds; synthetic data generation is deterministic.
- [x] **Full results logged:** `artifacts/results/citation_span_experiment.json`, `artifacts/results/summary.json`.
- [x] **Execution log preserved:** `artifacts/logs/citation_span_experiment.log`.
- [x] **Syntax validation:** `python3 -m py_compile` passed (`artifacts/logs/py_compile.log`).
- [x] **Environment recorded:** Python 3.12.3, 115 GiB RAM, CPU-only.
- [x] **Splits fixed:** Train (84), validation (43), holdout (65)—no cross-validation or shuffling.
- [x] **Parameter selection documented:** Best parameters selected on validation split only; holdout used for final evaluation.
- [x] **Decision artifact:** `.omx/project_decision.json` records the claim, evidence, constraints, risks, and next steps.

## Conclusion

A lightweight, clause-aware citation span resolver with a tuned delimiter set and backward character window substantially outperforms a sentence-level baseline on a controlled synthetic benchmark. On the held-out split, character-level F1 improved from 0.8809 to 1.0000 (+0.1191) and exact match from 0.7174 to 1.0000 (+0.2826). The result is positive and provisional: it demonstrates viability of the approach within the benchmark's scope, but real-world generalization remains an open question. Key follow-up work includes validation on human-annotated citation-span corpora, expansion of perturbation categories (quotation marks, em-dashes, footnotes, author-year styles), and comparison against parser-backed segmenters.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `scripts/citation_span_experiment.py` |
| Full results | `artifacts/results/citation_span_experiment.json` |
| Summary results | `artifacts/results/summary.json` |
| Human-readable report | `artifacts/results/report.md` |
| Execution log | `artifacts/logs/citation_span_experiment.log` |
| Syntax check log | `artifacts/logs/py_compile.log` |
| Memory telemetry | `artifacts/logs/memory_telemetry.log` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T035918500439+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T035918500439+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T035918500439+0000/paper_manifest.json` |
