# Repo Pulse Index: A Pilot Study of Public-Git-History Repository Vitality Scoring

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, logs, and result files). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

We present a pilot study of the Repo Pulse Index (RPI), a lightweight repository vitality score computed exclusively from publicly cloneable git history and file-structure signals. The RPI aggregates four dimensions—recent maintainer activity, sustained commit cadence, a bus-factor proxy derived from unique recent authors, and project hygiene inferred from CI/test/docs/license/packaging file markers—into a single 0–100 score. We implemented the prototype using only standard-library tooling and evaluated it on 8 real public GitHub repositories, split between actively maintained projects and stale/archived controls. Active repositories achieved a mean RPI of 85.55 (N=4), compared to 10.82 for controls (N=4), yielding a 74.74-point mean separation. The highest-scoring repository (click) received an RPI of 99.69, while the lowest (gitflow) received 8.30. These results suggest that a purely local, public-data vitality index is viable as a first-pass signal, though the small, Python-biased sample, heuristic hygiene scoring, and absence of human-labeled validation limit the strength of this conclusion. No statistical significance testing, threshold optimization, or longitudinal validation was performed.

## Introduction

Assessing the vitality and maintenance health of a software repository is a practical concern for dependency selection, risk assessment, and ecosystem monitoring. Existing approaches frequently rely on private platform data (issue response times, CI build outcomes, release cadence) or proprietary scoring systems whose internals are not reproducible. This creates a gap: can a useful vitality signal be derived from data available to anyone who can clone the repository?

We define the Repo Pulse Index (RPI) as a composite score computed from two categories of publicly available evidence:

1. **Git history signals**: commit timestamps (recency and cadence) and unique author email addresses (as a bus-factor proxy).
2. **File-structure signals**: presence of files or directories indicating CI configuration, test suites, documentation, licensing, and packaging infrastructure.

The pilot study reported here tests whether such an index can meaningfully separate active repositories from stale or archived ones using only local git data and file inspection—no API keys, no private data, no platform-specific metadata incorporated into the score.

## Method

### RPI Design

The RPI is a weighted composite of four sub-scores, each normalized to a 0–25 range before summation into a final 0–100 score:

| Sub-score | Signal Source | Description |
|---|---|---|
| Recent Activity | Commit timestamps | Proportion of commits within a recent time window (default: 90 days) relative to total commits. |
| Commit Cadence | Commit timestamps | Regularity of commit intervals over a longer lookback window, penalizing long gaps. |
| Bus-Factor Proxy | Author emails | Count of unique author email addresses in recent commits, mapped to a saturation curve. |
| Project Hygiene | File structure | Heuristic scan for CI config files, test directories, documentation files, license files, and packaging manifests. |

Each sub-score uses a simple deterministic mapping. The implementation is a single Python script (`scripts/repo_pulse_index.py`) using only the standard library and the `git` command-line tool—no external dependencies.

### Repository Selection

We selected 8 public GitHub repositories, divided into two groups:

- **Active sample** (N=4): repositories with recent commits and ongoing maintenance activity.
- **Stale/archived controls** (N=4): repositories with no recent commits, explicitly archived, or clearly abandoned.

The sample is small and biased toward Python-language projects, reflecting the pilot scope. The grouping was determined by experimenter judgment rather than an independently labeled ground truth, which introduces a risk of circularity: the scoring dimensions were chosen because they correlate with the grouping criterion.

### Data Collection

For each repository, we:

1. Cloned the full git history locally.
2. Extracted commit timestamps and author email addresses via `git log`.
3. Scanned the file tree for hygiene markers (e.g., `.github/workflows/`, `tests/`, `README.*`, `LICENSE`, `setup.py`, `pyproject.toml`).
4. Optionally captured GitHub metadata (archival status, stars, etc.) for contextual reference, though this metadata was **not** incorporated into the RPI score itself.

### Computation

The RPI was computed for all 8 repositories in a single batch run. Unit tests were executed before and after the run to confirm implementation correctness. All tests passed.

## Results

### Primary Outcome

The RPI separated active repositories from stale/archived controls with a large descriptive gap:

| Group | Mean RPI | N |
|---|---|---|
| Active sample | 85.55 | 4 |
| Stale/archived controls | 10.82 | 4 |
| **Mean separation** | **74.74** | — |

This separation is descriptive only. No statistical significance test, confidence interval, or effect-size calculation was performed given the sample size of 8.

### Per-Repository Scores

The highest and lowest individual scores were:

| Repository | RPI | Group |
|---|---|---|
| click | 99.69 | Active |
| gitflow | 8.30 | Stale/Archived |

The remaining 6 repositories' scores fall within the ranges implied by the group means above. The full per-repository breakdown is available in the results CSV and JSON artifacts (see Referenced Artifacts).

### Edge Case: Low-Recent-Commit Active Projects

The pilot surfaced an important boundary condition: the repository `encode/httpx`, which is actively maintained but had relatively few recent commits at the time of measurement, received a lower-than-expected RPI. This illustrates a known limitation of recency-weighted scoring—mature, stable projects with infrequent but meaningful updates may be systematically undervalued by the current formulation.

### Test Validation

All unit tests passed before and after the RPI computation run, confirming that the implementation produced consistent, deterministic outputs for the tested inputs.

## Limitations

This pilot has several significant limitations that temper the strength of its conclusions:

1. **Small, language-biased sample.** Eight repositories, predominantly Python, provide no basis for generalization across ecosystems, languages, or repository scales. The observed separation may not hold for larger or more diverse samples.

2. **Noisy bus-factor proxy.** Unique author email addresses are an imperfect measure of contributor diversity. Contributors may use multiple email addresses, and automated commits (e.g., bots, Dependabot) inflate the count without reflecting true human bus-factor risk.

3. **Heuristic hygiene scoring.** The file-structure scan uses fixed filename and directory patterns. This approach is brittle: it misses unconventional layouts and produces false positives or negatives for non-Python projects.

4. **GitHub metadata excluded from score.** Archival status, release cadence, issue/PR responsiveness, and star counts were captured contextually but not yet integrated into the RPI. These signals likely carry independent predictive value.

5. **No human-labeled validation set.** The active-vs-stale grouping was determined by the experimenter's judgment rather than by an independently labeled ground truth. This introduces circularity risk: the scoring dimensions were chosen precisely because they correlate with the grouping criterion.

6. **No calibration or threshold analysis.** The 74.74-point separation is descriptive; no ROC curve, precision/recall analysis, or threshold optimization was performed. The optimal RPI threshold for classifying repositories as active or stale is unknown.

7. **Single time-point measurement.** Each repository was scored at one point in time. Longitudinal stability of the RPI—whether it tracks meaningful changes in maintenance health over time—remains untested.

8. **No statistical significance testing.** With N=8, no meaningful significance test was applied. The reported separation could be consistent with chance variation in a larger population.

## Reproducibility Checklist

| Item | Status | Location |
|---|---|---|
| Implementation source | Available | `scripts/repo_pulse_index.py` |
| Unit tests | Passing | `tests/test_repo_pulse_index.py` |
| Clone logs (active repos) | Available | `artifacts/logs/clone_real_repos.log` |
| Clone logs (controls) | Available | `artifacts/logs/clone_stale_controls.log` |
| GitHub metadata snapshot | Available | `artifacts/logs/github_metadata.log` |
| RPI computation log | Available | `artifacts/logs/run_rpi_with_controls.log` |
| Test rerun log | Available | `artifacts/logs/test_repo_pulse_index_rerun.log` |
| System telemetry | Available | `artifacts/logs/system_telemetry.log` |
| Results (CSV) | Available | `artifacts/results/repo_pulse_index_with_controls.csv` |
| Results (JSON) | Available | `artifacts/results/repo_pulse_index_with_controls.json` |
| Analysis summary | Available | `artifacts/results/analysis_summary.txt` |
| Full research report | Available | `artifacts/results/research_report.md` |
| External dependencies | None beyond Python standard library and `git` CLI | — |
| Deterministic output | Yes (given same repository state) | — |
| Human-labeled validation set | Not available | — |
| Statistical significance tests | Not performed | — |

## Conclusion

The Repo Pulse Index pilot demonstrates that a purely local, public-data vitality score can separate active repositories from stale/archived controls with a large mean separation (74.74 points) in a small, Python-biased sample of 8 repositories. The result is promising but not conclusive. The index's four sub-scores—recent activity, commit cadence, bus-factor proxy, and project hygiene—capture real signals, but each carries known weaknesses, and the absence of human-labeled validation data means the observed separation cannot yet be interpreted as validated predictive accuracy.

The most important next step is a calibration study with 30–100 repositories spanning multiple languages and ecosystems, annotated with human-labeled vitality judgments. Optional integration of GitHub API dimensions (archival status, release cadence, issue/PR responsiveness) may improve discrimination, particularly for edge cases like mature projects with infrequent commits. Until such calibration is performed, the RPI should be treated as an experimental first-pass signal rather than a validated metric.

---

## Referenced Artifacts

All artifacts referenced in this paper reside under project directory `<control-plane-projects>/source-record-redacted`.

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260501T075718408356+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T075718408356+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T075718408356+0000/paper_manifest.json` |
| Implementation | `scripts/repo_pulse_index.py` |
| Tests | `tests/test_repo_pulse_index.py` |
| Research report | `artifacts/results/research_report.md` |
| Results (CSV) | `artifacts/results/repo_pulse_index_with_controls.csv` |
| Results (JSON) | `artifacts/results/repo_pulse_index_with_controls.json` |
| Analysis summary | `artifacts/results/analysis_summary.txt` |
| Clone log (active) | `artifacts/logs/clone_real_repos.log` |
| Clone log (controls) | `artifacts/logs/clone_stale_controls.log` |
| GitHub metadata log | `artifacts/logs/github_metadata.log` |
| RPI run log | `artifacts/logs/run_rpi_with_controls.log` |
| Test rerun log | `artifacts/logs/test_repo_pulse_index_rerun.log` |
| System telemetry log | `artifacts/logs/system_telemetry.log` |
