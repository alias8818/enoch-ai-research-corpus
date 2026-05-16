# Codebase Cartographer Real-Repo Validation: A Python Stdlib-Only Static Cartography Baseline

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We report on the implementation and validation of a Python-stdlib-only static cartography harness applied to a single real public repository. The cartographer extracts file inventories, Python module inventories, symbol tables, import graphs, parse-health telemetry, and throughput and memory metrics without external dependencies. Applied to the `pallets/click` repository (commit `831c8f09`, version 8.3.3, 149 files, 63 Python modules), the harness produced zero parse failures, extracted 1,689 symbols and 387 import edges (116 internal, 271 external), and completed in approximately 0.12 seconds with peak RSS of 28,896 kB. A validation harness confirmed 9 of 9 invariant and spot-check assertions. The target repository's own test suite and build process passed when executed from the correct working directory. An import-resolution defect discovered during the initial full run was corrected and the run repeated. These results establish that a local, dependency-free cartography baseline is feasible and yields structurally useful output on one real repository. However, validation was conducted on a single repository of moderate size, the analysis is Python-focused with no semantic or cross-language parsing, and the import graph is derived from static analysis rather than runtime tracing. Broader scientific closure requires corpus-level evaluation across languages, repository sizes, and project layouts.

## 1. Introduction

Automated codebase cartography—the extraction of structural maps from source repositories—has applications in code navigation, dependency auditing, and architectural understanding. Existing production-grade cartography tools typically depend on language servers, type checkers, or large external dependency chains. This raises the question of whether a minimal, stdlib-only baseline can produce useful structural maps from real repositories without such dependencies.

This paper reports on a single-repository validation experiment. We implemented a Python-stdlib-only cartographer and applied it to the public `pallets/click` repository. We then validated the cartography output against repository invariants and spot checks, and confirmed that the target repository remained buildable and testable after the analysis.

The scope is deliberately narrow. We make no claim about multi-language support, semantic call-graph extraction, type resolution, or architectural narrative generation. The result is a feasibility demonstration and baseline measurement on a single real repository, not a production tool evaluation.

## 2. Method

### 2.1 Cartographer Implementation

The cartographer (`tools/cartographer.py`) was implemented using only the Python standard library. Its analysis pipeline consists of the following stages:

1. **File inventory.** A recursive walk of the target repository tree, classifying files by extension and recording path, hash, and line count for each file.
2. **Python module identification.** Files with `.py` extension are classified as Python modules.
3. **Symbol extraction.** Each Python module is parsed via the `ast` module. Top-level class definitions, function definitions, and async function definitions are extracted by name and line number.
4. **Import graph construction.** Each `import` and `from ... import` statement is recorded as a directed edge. Edges are classified as internal (target resolvable within the repository's own module namespace) or external (target outside the repository).
5. **Module normalization.** Source-layout directories (`src`, `lib`) are stripped from module paths to produce canonical module names matching the package's import namespace. Relative imports are resolved against the enclosing package.
6. **Telemetry.** Peak RSS is recorded via `resource.getrusage`, and elapsed wall-clock time is recorded via `time.perf_counter`.

The harness accepts a `--limit-files` argument for incremental smoke and calibration runs.

### 2.2 Validation Harness

A separate validation script (`tools/validate_cartography.py`) checks cartography output against repository invariants and known structural properties:

- File count consistency between the cartography report and the actual filesystem.
- Parse success rate for all identified Python modules.
- Presence of known modules (`click.core`, `click.testing`).
- Presence of known core symbols (`Command`, `Context`, `Group`).
- Detection of both internal and external import edges.
- Presence of source file hashes and line counts.
- Resolution of relative imports to `click.*` targets.

These checks are narrow spot checks and invariants, not exhaustive correctness verification of the full symbol table or import graph.

### 2.3 Target Repository

The target repository is `pallets/click`, a widely-used Python command-line interface library:

- **URL:** `https://github.com/pallets/click.git`
- **Pinned HEAD:** `831c8f0948af519e45b90801d7430ff25451f972`
- **Commit date:** 2026-04-30
- **Commit subject:** `Add NoSuchCommand exception with suggestions for misspelled commands (#3228)`
- **Version:** 8.3.3 (from `pyproject.toml`)

This repository was selected as a real-world Python project with a standard `src`-layout, moderate size, and a well-known public interface. The selection of a single well-structured repository introduces a favorable bias; less conventional project structures may present different challenges.

### 2.4 Execution Environment

- **Host:** Linux, aarch64
- **GPU:** Reported as NVIDIA GB10, 0% utilization at telemetry time (irrelevant to this CPU-bound workload)
- **MemAvailable:** 122,626,616 kB
- **SwapTotal:** 0 kB
- **OOM protection:** `earlyoom v1.7` binary present

The memory environment is substantially over-provisioned relative to the workload. The zero-swap configuration and earlyoom presence were mission constraints, not findings of this experiment.

### 2.5 Experimental Procedure

The experiment proceeded through the following stages:

1. **Environment verification and self-smoke test.** The cartographer was run on its own project directory (23 files, 1 Python module, 0 parse failures).
2. **Target clone and provenance recording.** The target repository was cloned at the pinned commit.
3. **Incremental calibration runs.** A 20-file smoke run, an 80-file calibration run, and a 100-file Python-inclusive smoke run were executed to verify CLI wiring and Python analysis coverage.
4. **Full cartography run (initial).** The cartographer was run on the complete target tree. This run revealed an import-resolution defect (see Section 4.1).
5. **Bug fix and rerun.** The defect was corrected and the full run was repeated, producing the final cartography output.
6. **Target repository build and test.** The target's own test suite and build process were executed to confirm the repository was not modified or corrupted by the analysis.
7. **Cartography validation.** The validation harness was run against the final cartography output.

## 3. Results

### 3.1 Calibration Runs

| Run | Files | Python Modules | Parse Failures | Symbols | Max RSS (kB) |
|-----|-------|---------------|----------------|---------|-------------|
| Self-smoke (project dir) | 23 | 1 | 0 | — | — |
| 20-file target smoke | 20 | — | 0 | — | — |
| 80-file calibration | 80 | 9 | 0 | 34 | 19,048 |
| 100-file Python-inclusive | 100 | 15 | 0 | 91 | — |

The 20-file smoke run primarily covered documentation and configuration files due to deterministic sorted-order traversal. This confirmed CLI wiring but did not exercise Python analysis depth. The 80-file and 100-file runs progressively validated Python module detection and symbol extraction. These are calibration runs on a single repository and should not be interpreted as benchmarks.

### 3.2 Full Cartography Run

After the import-resolution fix (Section 4.1), the full run produced:

| Metric | Value |
|--------|-------|
| Files scanned | 149 |
| Python modules | 63 |
| Python parse failures | 0 |
| Python symbols | 1,689 |
| Import edges (total) | 387 |
| Import edges (internal) | 116 |
| Import edges (external) | 271 |
| Elapsed time | ~0.123 s |
| Throughput | ~1,209 files/s |
| Max RSS | 28,896 kB |

The memory footprint (28,896 kB peak RSS) is negligible relative to available memory (122,626,616 kB). The zero-swap configuration was maintained throughout. The throughput figure (~1,209 files/s) reflects a small repository processed in a fraction of a second; extrapolation to larger repositories would require separate measurement.

### 3.3 Validation Results

The validation harness passed all 9 of 9 checks:

1. File count matched (149 reported / 149 actual, consistent with ignore policy).
2. All Python modules parsed successfully (63/63).
3. Known module `click.core` present.
4. Known module `click.testing` present.
5. Known symbol `Command` extracted.
6. Known symbol `Context` extracted.
7. Known symbol `Group` extracted.
8. Internal import edges detected.
9. External import edges detected.

Additional checks confirmed the presence of source file hashes, line counts, and resolution of relative imports to `click.*` targets. These are spot checks against a small number of known entities, not exhaustive verification of all 1,689 symbols or all 387 import edges.

### 3.4 Target Repository Integrity

The target repository's own test suite, when executed from the repository root, produced:

- **1492 passed**, 23 skipped, 30,000 deselected, 1 xfailed, in 1.31 s.

The build process produced:

- `click-8.3.3-py3-none-any.whl`
- `click-8.3.3.tar.gz`

Both results confirm that the cartography process did not modify or corrupt the target repository. The initial test run from the project root (rather than the repository root) produced one failure; see Section 4.2.

## 4. Issues Found and Resolved

### 4.1 Source-Layout Module Normalization

The initial full cartography run reported 0 internal import edges. Investigation revealed that the cartographer treated `src/click/*.py` files as belonging to the module namespace `src.click.*`, which did not match the actual import targets used by relative imports within the package. The fix strips common source-root prefixes (`src`, `lib`) from module paths and resolves relative imports against the enclosing package. After this correction, the rerun produced 116 internal edges and 271 external edges, consistent with the expected structure of the `click` package.

This defect is notable because it was only revealed by the full run on a `src`-layout repository. The calibration runs, which covered fewer Python modules, did not surface it. This suggests that calibration on small subsets may not expose layout-specific resolution errors.

### 4.2 Working-Directory-Dependent Test Failure

The initial run of the target repository's test suite from the project root (rather than the repository root) produced one failure in `test_expand_args`, which expected `pyproject.toml` in the current working directory. Rerunning the test suite from `repos/click` (the cloned repository root) resolved the failure. This is a known class of test-environment sensitivity and is not related to the cartography process.

## 5. Limitations

1. **Single-repository validation.** All results pertain to one repository (`pallets/click`) of moderate size (149 files, 63 Python modules). Corpus-level generality across languages, repository sizes, and project layouts is not established. The selected repository has a well-structured `src`-layout and clean public interface; results may not transfer to less conventional project structures.

2. **Python-only analysis.** Non-Python files are inventoried (path, hash, line count) but not deeply parsed. The cartographer provides no semantic analysis for JavaScript, C, Rust, configuration files, or other non-Python artifacts.

3. **Static import graph only.** The import graph is derived from static analysis of `import` and `from ... import` statements. It does not reflect runtime import behavior, conditional imports, dynamic module loading, or call graphs. Import edges represent declared dependencies, not necessarily executed ones.

4. **No type resolution or call graph.** Symbol extraction records names and definition sites but does not resolve types, inheritance hierarchies, or function call relationships.

5. **No architectural narrative.** The cartographer produces structural data (files, modules, symbols, imports) but does not generate human-readable architectural descriptions, ownership inferences, or dependency-risk assessments.

6. **Best-effort import resolution.** Module normalization handles `src` and `lib` layouts and relative imports, but may not correctly resolve all packaging conventions (namespace packages, editable installs, multi-package monorepos). The initial run's zero-internal-edge defect (Section 4.1) illustrates this fragility.

7. **Validation spot checks are narrow.** The 9 validation checks confirm basic structural invariants and a small number of known symbols and modules. They do not constitute exhaustive correctness verification of the full symbol table or import graph. Incorrect or missing symbols or edges that are not among the checked entities would not be detected.

8. **No comparison baseline.** The cartography output has not been compared against any other static analysis tool, language server, or ground-truth annotation. Its accuracy relative to alternative approaches is unknown.

## 6. Reproducibility Checklist

- [x] **Target repository and commit:** `https://github.com/pallets/click.git` at `831c8f0948af519e45b90801d7430ff25451f972` — publicly accessible and pinned.
- [x] **Cartographer source:** `tools/cartographer.py` — Python-stdlib-only, no external dependencies.
- [x] **Validator source:** `tools/validate_cartography.py` — Python-stdlib-only.
- [x] **Full cartography output:** `results/click_full_v2_cartography.json`.
- [x] **Summary metrics:** `results/click_full_v2_summary.json`.
- [x] **Validation metrics:** `metrics/validation_metrics.json`.
- [x] **Research metrics:** `metrics/research_metrics.json`.
- [x] **Execution logs:** `logs/00_environment.log` through `logs/10_final_verification.log`.
- [x] **Decision record:** `.omx/project_decision.json`.
- [x] **Runtime:** Python 3 (stdlib only), Linux aarch64, no GPU required.
- [x] **Memory constraint:** SwapTotal 0 kB; peak RSS 28,896 kB; earlyoom v1.7 active.
- [x] **Determinism:** File traversal is sorted; AST parsing is deterministic; output JSONs are reproducible given the same repository state.
- [ ] **Corpus-level evaluation:** Not performed; single-repository result only.
- [ ] **Cross-language validation:** Not performed; Python-only analysis.
- [ ] **Comparison against alternative tools:** Not performed.

## 7. Conclusion

A Python-stdlib-only static cartography harness was implemented and validated on the real public `pallets/click` repository. The harness produced a complete file inventory, Python module inventory, symbol table (1,689 symbols), and import graph (387 edges) with zero parse failures, in approximately 0.12 seconds and under 29 MB of peak memory. All 9 validation checks passed, and the target repository's own test suite and build process confirmed repository integrity post-analysis. An import-resolution defect discovered during the initial full run was corrected, illustrating both the value of full-repository validation and the fragility of layout-specific module normalization.

These results demonstrate that a minimal, dependency-free cartography baseline is feasible and yields structurally useful output on one real repository. The result is a positive feasibility finding at medium-high confidence, constrained by single-repository validation and Python-only scope. No claim is made about performance or correctness on other repositories, languages, or project layouts.

The next research step should scale the same harness to a small corpus of repositories varying in language, size, and layout, and compare cartography output against known package/module structures or maintainer-labeled architecture documentation. This would begin to establish the generality bounds of the approach, identify failure modes in less conventional project structures, and provide a basis for measuring accuracy against ground truth.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Cartographer harness | `tools/cartographer.py` |
| Validation harness | `tools/validate_cartography.py` |
| Full cartography output | `results/click_full_v2_cartography.json` |
| Summary metrics | `results/click_full_v2_summary.json` |
| Validation metrics | `metrics/validation_metrics.json` |
| Research metrics | `metrics/research_metrics.json` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Environment log | `logs/00_environment.log` |
| Self-smoke log | `logs/01_self_smoke.log` |
| Clone/provenance log | `logs/02_clone_click.log` |
| Target metadata log | `logs/03_pyproject_excerpt.log` |
| Cartography runs log | `logs/04_cartography_runs.log` |
| Cartography rerun log | `logs/05_cartography_rerun_v2.log` |
| Target tests log (project root) | `logs/06_target_repo_tests.log` |
| Target tests log (repo root) | `logs/07_target_repo_tests_repo_root.log` |
| Validation log | `logs/08_validate_cartography.log` |
| Target build log | `logs/09_target_build.log` |
| Final verification log | `logs/10_final_verification.log` |
| Claim ledger | `papers/source-record-redacted-20260430T212818393036+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T212818393036+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T212818393036+0000/paper_manifest.json` |
