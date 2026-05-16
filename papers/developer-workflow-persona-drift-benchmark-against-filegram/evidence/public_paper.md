# Developer Workflow Persona Drift Benchmark Against FileGram

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We present a synthetic developer-workflow persona-drift benchmark and compare it against the public FileGram benchmark for file-system behavioral personalization. The developer-workflow benchmark models drift along eight code-specific dimensions—repository choice, workspace layout, branch naming style, editor preference, build tool, debugging loop pattern, PR style, and artifact kind—across four developer personas over 168 synthetic events with 8 explicit drift events. Under three memory strategies (frozen profile, recency window, adaptive profile store), the developer-workflow benchmark yields profile reconstruction accuracies of 0.319, 0.800, and 0.893 respectively, and drift detection F1 scores of 0.130, 0.485, and 0.667. The same three strategies applied to the public FileGram replay (20 profiles, 32 tasks, 640 trajectories, scored via a local FileGramOS-compatible feature extractor) yield attribute accuracies of 0.425, 0.432, and 0.430, with near-zero exact state match. The developer-workflow benchmark thus produces a large separation between stale and adaptive memory strategies, whereas the FileGram public replay under our local scorer shows minimal separation—consistent with FileGram's profile-stable design but limiting cross-benchmark drift comparability. A local telemetry audit over 40 real git repositories confirms that the synthetic drift dimensions map to observable codebase signals, with strong support for four dimensions and moderate support for four others. Confidence in the overall finding is medium, bounded by the synthetic nature of the dataset, the use of a heuristic local scorer rather than FileGram's official LLM judge, and the absence of media-blob resolution in the cross-benchmark comparison.

## 1. Introduction

Personalization systems that track user behavioral traces face the problem of persona drift: user preferences change over time, and a system that fails to detect and adapt to these changes will serve stale recommendations. FileGram (arXiv, April 2026) introduced a benchmark for grounding agent personalization in file-system behavioral traces, covering profile reconstruction, trace disentanglement, persona drift detection, and multimodal grounding across 20 user profiles, 32 tasks, 640 trajectories, and 6 behavioral dimensions. However, FileGram's public task inventory is dominated by analyst, legal, office, and archive workflows rather than software development workflows.

This work asks whether a developer-workflow-specific persona-drift benchmark produces a materially different evaluation surface from FileGram's generic file-system benchmark. If developer workflows introduce drift patterns that are structurally distinct from office-style file management—for example, shifts in build tooling, branch naming conventions, or debugging strategies—then a specialized benchmark may reveal failure modes invisible to a more general benchmark.

We report three evidence layers: (1) a synthetic developer-workflow drift benchmark with deterministic generation and evaluation, (2) an apples-to-apples cross-benchmark comparison using the same three memory strategies on both the developer-workflow traces and the public FileGram assets, and (3) a local git-telemetry realism audit that checks whether the synthetic drift dimensions correspond to observable signals in real repositories.

## 2. Method

### 2.1 Developer-Workflow Persona-Drift Benchmark

The benchmark is implemented as a deterministic synthetic generator and evaluator (`scripts/developer_workflow_persona_drift_benchmark.py`). It models four developer personas, each defined over eight drift dimensions:

- **Repository choice** (`repo`): which codebase the developer works on.
- **Workspace layout** (`workspace`): directory organization preference.
- **Branch naming style** (`branch_style`): convention for git branch names.
- **Editor preference** (`editor`): primary development editor.
- **Build tool** (`build_tool`): preferred build system.
- **Debugging loop pattern** (`debug_loop`): approach to debugging cycles.
- **PR style** (`pr_style`): pull request authoring convention.
- **Artifact kind** (`artifact_kind`): type of artifact produced (source, test, config, etc.).

The generator produces 168 events across 12 phase segments with 8 explicit drift events, where a persona's attribute values change at a phase boundary. The dataset and manifest are stored as `data/developer_workflow_persona_drift.jsonl` and `data/developer_workflow_persona_drift_manifest.json`.

### 2.2 Memory Strategies

Three baseline memory strategies are evaluated:

1. **Frozen profile**: A single profile estimated from the first phase, never updated.
2. **Recency window**: A profile estimated from the most recent *k* events (window size tuned per benchmark).
3. **Adaptive profile store**: A profile that incrementally updates attribute estimates as new events arrive, with a decay mechanism for stale observations.

### 2.3 Evaluation Metrics

- **Profile reconstruction accuracy**: Fraction of persona attributes correctly predicted at each evaluation point.
- **Proactive action accuracy**: Fraction of next-action predictions matching the ground-truth persona.
- **Drift detection F1**: Harmonic mean of precision and recall for detecting whether a drift event occurred at a given phase boundary.
- **Exact state match**: Fraction of evaluation points where the entire attribute vector is correctly predicted.

### 2.4 Cross-Benchmark Comparison

To enable apples-to-apples comparison, `scripts/apples_to_apples_filegram_compare.py` applies the same three memory strategies to both the developer-workflow traces and the public FileGram assets. The FileGram side uses the public Hugging Face dataset (`Choiszt/FileGram`), caching 20 profiles × 32 trajectories = 640 trajectories locally.

The FileGram scorer was upgraded during the project to use a FileGramOS-compatible observable feature extractor (imported from `external/FileGram/bench/filegramos/feature_extraction.py` when available), mapping FileGramOS-style features onto the six FileGram profile dimensions (A: reading, B: production, C: organization, D: iteration/versioning, E: curation/work-rhythm, F: cross-modal). This upgrade replaced an earlier lightweight heuristic proxy that scored only dimensions A/B/C/D/F.

Media-blob resolution is implemented but disabled by default because direct public blob fetching produced HTTP 429 rate-limit errors during the run. The scorer therefore relies on event metadata and content-length features for write-content axes.

### 2.5 Realism Audit

`scripts/developer_realism_audit.py` performs a deterministic local telemetry scan over actual git checkouts, inspecting branch naming, build/test tooling, CI/review configuration files, and recent commit-message style. It compares observed signals against the synthetic benchmark's eight drift dimensions and classifies each dimension as strong, moderate, or weak based on the frequency and consistency of observable evidence.

## 3. Results

### 3.1 Developer-Workflow Benchmark

| Strategy | Profile Reconstruction Accuracy | Proactive Action Accuracy | Drift Detection F1 |
|---|---|---|---|
| Frozen profile | 0.3194 | 0.3171 | 0.1301 |
| Recency window | 0.7995 | 0.7927 | 0.4848 |
| Adaptive profile store | 0.8933 | 0.8902 | 0.6667 |

The expected ranking (adaptive > recency > frozen) holds across all three metrics. The gap between frozen and adaptive strategies is substantial: profile reconstruction accuracy improves by 57.4 percentage points, and drift detection F1 improves by 53.7 points. This confirms that the developer-workflow benchmark is sensitive to memory strategy choice under explicit drift.

### 3.2 Cross-Benchmark Comparison

**Developer-workflow benchmark (attribute accuracy and exact state match):**

| Strategy | Attribute Accuracy | Exact State Match |
|---|---|---|
| Frozen | 0.3194 | 0.2927 |
| Recency | 0.7995 | 0.7195 |
| Adaptive | 0.8933 | 0.8110 |

**FileGram public replay with FileGramOS-compatible extractor (all six dimensions A–F):**

| Strategy | Attribute Accuracy | Exact State Match |
|---|---|---|
| Frozen | 0.4250 | — |
| Recency | 0.4317 | — |
| Adaptive | 0.4296 | 0.0016 |

The FileGram side shows minimal separation between memory strategies (attribute accuracy range: 0.425–0.432), and exact state match is near zero across all strategies. This is consistent with FileGram's profile-stable design: the public trajectories do not contain the kind of explicit persona drift that would differentiate stale from adaptive memory. Drift detection F1 is therefore not meaningful for the FileGram replay under our local scorer.

The earlier lightweight proxy (scoring only A/B/C/D/F) produced attribute accuracies of 0.380 (frozen), 0.399 (recency), and 0.399 (adaptive), with exact state match of 0.000, 0.002, and 0.003 respectively. The FileGramOS-compatible extractor modestly improved absolute scores but did not change the qualitative conclusion.

**Extractor metadata for the FileGramOS run:**

- FileGramOS feature extractor used: true
- Public media blob references seen in cached trajectories: 3,024
- Blob resolution requested: false
- Cached blobs: 0

### 3.3 Realism Audit

| Metric | Value |
|---|---|
| Repositories scanned | 40 |
| Recent commit subjects inspected | 1,691 |
| Local branches inspected | 62 |
| Tracked file samples inspected | 31,413 |

**Dimension support classification:**

| Support Level | Dimensions |
|---|---|
| Strong | repo, workspace, build_tool, artifact_kind |
| Moderate | branch_style, editor, debug_loop, pr_style |
| Weak | none |

All eight synthetic drift dimensions have at least moderate support from real git-telemetry signals. The four strong dimensions (repo, workspace, build_tool, artifact_kind) have direct, high-frequency observables in repository structure and file paths. The four moderate dimensions (branch_style, editor, debug_loop, pr_style) have observable signals but with lower frequency or greater ambiguity—for example, editor preference may only be inferable from `.editorconfig` or IDE metadata rather than from commit history directly.

## 4. Limitations

1. **Synthetic dataset.** The developer-workflow benchmark uses procedurally generated events, not real developer traces. While the realism audit confirms that the drift dimensions correspond to observable signals, the event distributions, drift magnitudes, and inter-dimensional correlations may not reflect real-world developer behavior.

2. **Local heuristic scorer for FileGram.** The cross-benchmark comparison uses a local FileGramOS-compatible feature extractor rather than FileGram's official LLM judge pipeline. The near-zero exact state match on the FileGram side may reflect scorer limitations rather than an intrinsic property of the data. Media-blob resolution was disabled due to HTTP 429 rate limits, further limiting the scorer's access to write-content features.

3. **FileGram drift comparability.** The FileGram public replay appears profile-stable under our local scorer, meaning drift detection F1 cannot be meaningfully computed. This prevents a direct comparison of drift sensitivity across the two benchmarks. The comparison is therefore limited to profile reconstruction accuracy and the qualitative observation that the developer-workflow benchmark produces large strategy separation while FileGram does not under this scorer.

4. **Limited persona and event count.** The developer-workflow benchmark covers 4 personas and 168 events. This is small relative to FileGram's 20 profiles and 640 trajectories. Generalization to a larger, more diverse developer population is not established.

5. **Local-only realism audit.** The telemetry audit scans local git checkouts on a single machine. It does not access hosted issue/PR labels, CI logs, or review metadata from platforms such as GitHub or GitLab. The moderate-support dimensions (branch_style, editor, debug_loop, pr_style) would likely benefit from hosted platform data.

6. **No human evaluation.** The benchmark results are entirely automated. No human subjects were asked whether the predicted profiles or detected drift points correspond to their perceived behavior changes.

7. **Confidence is medium.** The project decision records evidence strength as "strong" but confidence as "medium," reflecting the above caveats. The current project artifacts support the finding in the tested setting, but the finding should not be generalized beyond the tested setting without further validation.

## 5. Reproducibility Checklist

- [x] **Benchmark script available:** `scripts/developer_workflow_persona_drift_benchmark.py` — deterministic, no random seed variation.
- [x] **Cross-benchmark script available:** `scripts/apples_to_apples_filegram_compare.py` — caches FileGram trajectories from Hugging Face.
- [x] **Realism audit script available:** `scripts/developer_realism_audit.py` — deterministic local git scan.
- [x] **Synthetic dataset committed:** `data/developer_workflow_persona_drift.jsonl` and `data/developer_workflow_persona_drift_manifest.json`.
- [x] **Result artifacts committed:** `results/benchmark_results.json`, `results/benchmark_report.md`, `results/apples_to_apples_comparison.json`, `results/apples_to_apples_report.md`, `results/developer_realism_audit.json`, `results/developer_realism_audit.md`.
- [x] **FileGram public cache:** `data/filegram_public_cache/` with cached trajectory events.
- [x] **FileGramOS extractor path documented:** `external/FileGram/bench/filegramos/feature_extraction.py` (cloned from `synvo-ai/FileGram`).
- [x] **Verification commands documented:** All three scripts compile and run with the commands listed in run notes.
- [ ] **Media-blob resolution:** Not reproducible without a Hugging Face cache or rate-limit-free access; disabled by default.
- [ ] **Official FileGram judge pipeline:** Not included; the local scorer is a heuristic proxy, not the published evaluation method.
- [ ] **External replication on different hardware/models:** Not performed.

## 6. Conclusion

We have constructed a developer-workflow persona-drift benchmark that models drift along eight code-specific dimensions and evaluated it under three memory strategies. The benchmark produces a clear and substantial separation between frozen, recency-window, and adaptive memory strategies (profile reconstruction accuracy: 0.319, 0.800, 0.893; drift detection F1: 0.130, 0.485, 0.667), confirming that developer-workflow drift is detectable and that adaptive memory substantially outperforms static profiles.

The apples-to-apples comparison with FileGram's public assets reveals a qualitative difference: under our local FileGramOS-compatible scorer, the FileGram replay shows minimal strategy separation (attribute accuracy: 0.425–0.432), consistent with its profile-stable design. The developer-workflow benchmark thus exercises a different failure mode—drift under changing developer preferences—that is not well-represented in the current FileGram public evaluation.

A local git-telemetry realism audit over 40 repositories confirms that all eight synthetic drift dimensions map to observable real-world signals, with strong support for four dimensions and moderate support for four.

These results support the hypothesis that developer-workflow persona drift constitutes a materially different evaluation surface from generic file-system personalization benchmarks. However, confidence remains medium due to the synthetic dataset, the heuristic nature of the cross-benchmark scorer, the absence of media-blob resolution, and the lack of human evaluation. Future work should calibrate against official FileGram judge labels if those become available, extend the benchmark to more personas and real developer traces, and incorporate hosted platform telemetry for the moderately supported dimensions.

## Referenced Artifacts

### Scripts
- `scripts/developer_workflow_persona_drift_benchmark.py` — synthetic developer-workflow drift benchmark generator and evaluator.
- `scripts/apples_to_apples_filegram_compare.py` — cross-benchmark scorer for developer-workflow and FileGram public replay.
- `scripts/developer_realism_audit.py` — local git-telemetry realism audit.

### Data
- `data/developer_workflow_persona_drift.jsonl` — synthetic developer-workflow event traces.
- `data/developer_workflow_persona_drift_manifest.json` — dataset manifest.
- `data/filegram_public_cache/` — cached FileGram public trajectory events (e.g., `signal/p9_visual_organizer_T-32/events.json`).

### Results
- `results/benchmark_results.json` — developer-workflow benchmark metrics.
- `results/benchmark_report.md` — developer-workflow benchmark report.
- `results/apples_to_apples_comparison.json` — cross-benchmark comparison metrics and extractor metadata.
- `results/apples_to_apples_report.md` — cross-benchmark comparison report.
- `results/developer_realism_audit.json` — realism audit structured results.
- `results/developer_realism_audit.md` — realism audit report.

### Decision and Metadata
- `.omx/project_decision.json` — project decision (finalize_positive, hypothesis supported, confidence medium).
- `.omx/metrics.json` — session metrics.
- `run_notes.md` — detailed run notes across all execution phases.
- `README.md` — reproduction commands and output descriptions.

### External Reference
- `external/FileGram/` — cloned from `synvo-ai/FileGram` public repository; provides `bench/filegramos/feature_extraction.py` used by the FileGramOS-compatible extractor.

### Paper Artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
