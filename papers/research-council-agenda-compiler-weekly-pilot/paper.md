# Research Council Agenda Compiler: A Deterministic Weekly Pilot with Structured Updates

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, benchmark logs). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact.

---

## Abstract

We present a deterministic agenda compiler that transforms structured weekly research updates into a bounded 60-minute research-council agenda with assigned owners, outcome labels, evidence links, time allocations, and a parking lot for deferred items. On a synthetic gold fixture of 8 weekly update items, the compiler achieves precision 1.0000, recall 1.0000, F1 1.0000, and nDCG 0.9994. An 80,000-row throughput calibration on an ARM-based workstation completed in 0.15 s wall-clock time at 532,842 rows/s with 89,824 KB peak RSS and zero swap usage. These results establish local feasibility but do not constitute production validation: the fixture is synthetic, scoring weights are hand-tuned on a single gold set, and no real historical council data was available. We recommend promotion to a weekly pilot only after evaluation on at least four historical weekly snapshots with aggregate F1 ≥ 0.85 and nDCG ≥ 0.80.

## Introduction

Research councils that meet weekly face a recurring coordination problem: structured updates from multiple contributors must be compiled into a time-bounded agenda that preserves decision priority, assigns ownership, and defers non-critical items. Manual agenda construction is labor-intensive and inconsistent in ordering and time allocation.

Prior guidance on effective meeting agendas emphasizes meeting objectives, desired outcomes, time allocations, owners, supporting materials, and realistic scope (PerformYard). Institutional guidance further stresses early distribution, explicit outcome tracking, and action items with owners and deadlines (UC Berkeley BPM). These principles suggest a schema-driven, deterministic compilation approach: if weekly updates arrive in a structured format, a scoring policy can rank items by outcome type and urgency, enforce a meeting-length budget, and produce a complete agenda with a parking lot for overflow.

This paper reports on a pilot implementation of such a compiler. The central question is whether a lightweight deterministic system can produce agendas that match expert-curated gold labels on a controlled fixture, and whether the computational cost is low enough for weekly deployment on modest hardware. We do not claim production readiness; rather, we report synthetic-feasibility evidence and identify the specific gaps that must be closed before promotion.

## Method

### Schema Design

The compiler ingests weekly research updates as JSONL records. Each record contains fields for item identifier, owner, outcome type, urgency, evidence links, and estimated discussion time. The compiler produces an agenda with the following structure per item:

- **Purpose**: one-line statement of the item's objective
- **Owner**: responsible party
- **Outcome label**: one of `Decide`, `Unblock`, `Triage`, `Assign`, `Review`
- **Timebox**: allocated minutes within the 60-minute meeting budget
- **Evidence links**: supporting materials or pre-read references
- **Due date**: action-item deadline where applicable
- **Parking-lot rationale**: if the item is deferred, a reason for deferral

Outcome types are ordered by council priority: `Decide` and `Unblock` items receive the highest scores and earliest placement, followed by `Triage`, `Assign`, and `Review`.

### Scoring Policy

Each item receives a composite score from a weighted sum of outcome priority, urgency, and evidence availability. The scoring weights are transparent and configurable but were hand-tuned on the single gold fixture. Items are sorted by descending score and greedily added to the agenda until the cumulative timebox reaches the 60-minute budget. Remaining items are placed in the parking lot with a recorded rationale.

### Timebox Constraint

An early design iteration allocated 8 minutes to `Review` and `Assign` items. This caused the 8-item fixture to overflow the 60-minute budget, yielding recall of 0.8333 because one item was forced into the parking lot despite being expected in the agenda. Reducing non-decision timeboxes to 6 minutes preserved all expected items while respecting the meeting length. This adjustment is fixture-specific and may not generalize.

### Evaluation

Evaluation compares the compiled agenda against gold labels in the fixture. Metrics are:

- **Precision**: fraction of agenda items that appear in the gold set
- **Recall**: fraction of gold items that appear in the agenda
- **F1**: harmonic mean of precision and recall
- **nDCG**: normalized discounted cumulative gain, measuring ranking quality relative to the gold ordering

### Throughput Calibration

To assess computational feasibility, the 8-item fixture was repeated 10,000 times to produce an 80,000-row input. The compiler processed this input while `/usr/bin/time -v` recorded wall-clock time, peak RSS, and memory deltas. The calibration was run on an NVIDIA Jetson-based ARM workstation (Linux 6.17.0-1014-nvidia, aarch64, Python 3.12.3) with 121,629,788 KB available memory and 0 KB swap. The `earlyoom` daemon was present at `/usr/bin/earlyoom`.

## Results

### Agenda Quality

On the 8-item gold fixture, the final compiler produced the following agenda order: `W1-D1`, `W1-B1`, `W1-D2`, `W1-R1`, `W1-A1`, `W1-E1`. Evaluation metrics:

| Metric    | Value  |
|-----------|--------|
| Precision | 1.0000 |
| Recall    | 1.0000 |
| F1        | 1.0000 |
| nDCG      | 0.9994 |

There were zero false positives and zero false negatives. The nDCG of 0.9994 (rather than 1.0000) reflects a minor ordering divergence from the gold ranking at a low-priority position.

### Initial Design Failure

The first compiler version achieved recall of 0.8333 because 8-minute timeboxes for `Review` and `Assign` items caused the total agenda duration to exceed 60 minutes, forcing one gold-expected item into the parking lot. This failure was resolved by reducing non-decision timeboxes to 6 minutes. The resolution is specific to this fixture's item mix and may require re-tuning for different input distributions.

### Performance Bug

The initial throughput benchmark exposed a quadratic-time bottleneck in parking-lot membership checks. The implementation used repeated `any(...)` scans over the agenda list to check whether an item was already placed. Replacing this with an `agenda_ids` set reduced the check to O(1) and allowed the 80,000-row calibration to complete promptly.

### Throughput and Memory

| Metric                   | Value          |
|--------------------------|----------------|
| Input rows               | 80,000         |
| Compiler elapsed time    | 0.150138 s     |
| Throughput               | 532,842 rows/s |
| Peak RSS                 | 89,824 KB      |
| Memory-available delta   | 32,412 KB      |
| Swap total / used        | 0 KB           |

The workload is CPU-bound and memory-light. No GPU inference or long-running process was required. The calibration confirms that the compiler is computationally viable for weekly deployment on modest hardware.

## Limitations

1. **Synthetic fixture only.** The gold set contains 8 hand-crafted items. Real council updates may exhibit different distributions of outcome types, urgency levels, and time requirements. The perfect metrics on this fixture are necessary but not sufficient for production claims.

2. **Hand-tuned weights.** Scoring weights were adjusted to match the single gold fixture. Without cross-validation on multiple historical weeks, there is a substantial risk of overfitting to this fixture's characteristics.

3. **Structured-input assumption.** The compiler requires JSONL input with pre-labeled outcome types and time estimates. If source updates arrive as raw prose, an extraction and classification step must be added and separately evaluated.

4. **No real council data.** No historical council agendas, private weekly update streams, or reviewer judgments were available locally. The Notion URL recorded in project metadata was not used as evidence.

5. **Single-machine calibration.** Throughput and memory results reflect one ARM workstation. Performance on different hardware may vary.

6. **Timebox sensitivity.** The 6-minute non-decision timebox that resolved the initial recall failure was chosen to fit this specific fixture. Agendas with more `Review` or `Assign` items may still overflow the 60-minute budget at this setting.

7. **Missing readiness audit.** The review checklist records a missing `readiness_audit` signal, and all 9 checklist items remain in `pending` status. The draft has not undergone human claim audit.

## Reproducibility Checklist

- [x] Source code for the compiler, evaluator, and benchmark is available (`src/agenda_compiler.py`, `src/evaluate_agenda.py`, `src/benchmark_throughput.py`)
- [x] Gold fixture data is available (`data/weekly_research_items.jsonl`)
- [x] Compiled agenda output is available (`outputs/agenda_2026-05-01.json`)
- [x] Evaluation metrics are available (`outputs/eval_metrics.json`)
- [x] Environment probe log is available (`artifacts/logs/environment_probe.log`)
- [x] Compilation, evaluation, and throughput logs are available (`artifacts/logs/compile_after_perf_fix.log`, `artifacts/logs/eval_after_perf_fix.log`, `artifacts/logs/throughput_80k.log`)
- [x] All Python source files pass `py_compile` without errors (`artifacts/logs/py_compile.log`)
- [x] Machine-readable decision JSON is available (`.omx/project_decision.json`)
- [ ] Real historical council data is **not** included (private/unavailable)
- [ ] External validation on non-synthetic inputs has **not** been performed
- [ ] Human claim audit has **not** been completed

## Conclusion

A deterministic scoring-and-packing compiler can transform structured weekly research updates into a time-bounded, evidence-backed council agenda with perfect inclusion metrics on a synthetic gold fixture and sub-second throughput at scale. The pilot result demonstrates technical feasibility and low computational cost. However, the result is confined to a single synthetic fixture with hand-tuned parameters. The initial design's recall failure under a plausible timebox configuration, and the quadratic performance bug discovered during calibration, illustrate that even simple deterministic systems require careful constraint analysis and benchmarking before deployment.

We recommend proceeding to a weekly pilot with real council data only after evaluating the compiler on at least four historical weekly snapshots. Promotion criteria are: aggregate F1 ≥ 0.85, aggregate nDCG ≥ 0.80, and zero omissions of critical `Decide` or `Unblock` items. Until such external validation is completed, the present results should be treated as local feasibility evidence, not as a production readiness claim.

---

## Referenced Artifacts

| Artifact | Description |
|----------|-------------|
| `run_notes.md` | Full run notes including commands, findings, and limitations |
| `data/weekly_research_items.jsonl` | Synthetic/gold weekly update fixture (8 items) |
| `src/agenda_compiler.py` | Deterministic compiler and scoring policy |
| `src/evaluate_agenda.py` | Precision/recall/F1/nDCG evaluator |
| `src/benchmark_throughput.py` | Throughput and memory calibration script |
| `outputs/agenda_2026-05-01.json` | Compiled council agenda output |
| `outputs/eval_metrics.json` | Final evaluation metrics |
| `artifacts/logs/environment_probe.log` | Machine, kernel, Python version, memory, swap probe |
| `artifacts/logs/compile_after_perf_fix.log` | Post-fix compilation smoke log |
| `artifacts/logs/eval_after_perf_fix.log` | Post-fix evaluation log |
| `artifacts/logs/throughput_80k.log` | 80,000-row throughput calibration log |
| `artifacts/logs/py_compile.log` | Python compilation check log |
| `.omx/project_decision.json` | Machine-readable decision with key metrics and blockers |
| `papers/.../claim_ledger.json` | Claim ledger (empty claims; notes model-authored draft requires human audit) |
| `papers/.../evidence_bundle.json` | Evidence bundle linking to project and run IDs |
