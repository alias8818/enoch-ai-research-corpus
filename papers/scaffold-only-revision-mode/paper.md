# Scaffold-Only Revision Mode: Feasibility of Sentinel-Protected Constrained Repair on Synthetic Fixtures

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metrics, claim ledger, evidence bundle). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We evaluate the feasibility of a "scaffold-only revision" mode: a constrained code repair pass that may edit imports, exported names, CLI adapters, wrappers, and other non-core glue, but must provably leave core algorithm text unchanged. Enforcement relies on `# CORE_START` / `# CORE_END` sentinel markers and SHA-256 hash equality checks over the protected region. In a synthetic benchmark of 36 fixtures spanning 6 tasks, scaffold-only repair recovered all 24 initially-failing scaffold-class fixtures (recovery rate 1.0) while preserving protected core text byte-for-byte across all 36 fixtures (protected-core-unchanged rate 1.0). Six core-wrong negative-control fixtures remained failing after scaffold-only repair (false-repair count 0). These results support the viability of sentinel-protected scaffold-only revision as a safety mechanism for repair scenarios where failures originate in integration glue rather than core algorithm logic. However, the benchmark is synthetic and does not demonstrate that a live language model will produce correct scaffold edits on real failure traces; production utility remains unvalidated.

## Introduction

Automated code repair systems face a fundamental tension: the desire to fix integration and interface errors must be balanced against the risk of silently altering correct algorithm logic. In practice, many code failures—particularly in generated or scaffolded code—arise from incorrect imports, mismatched function signatures, CLI parsing errors, or output formatting mistakes, while the core algorithm implementation is already correct.

Scaffold-only revision mode addresses this tension by constraining the repair pass to non-core "scaffold" regions: imports, exported names, CLI adapters, wrappers, and IO/API glue. The core algorithm, delimited by `# CORE_START` and `# CORE_END` sentinel markers, is protected by a hash gate: any revision that changes the protected region's SHA-256 digest is rejected.

This paper reports on a feasibility evaluation of this mode using a synthetic benchmark harness. We seek to answer two questions:

1. When failures are caused by scaffold defects and the core algorithm is correct, can scaffold-only repair recover test pass rates while preserving the protected core?
2. When failures are caused by core algorithm defects, does scaffold-only repair correctly refuse to produce a passing result (i.e., does it avoid false repairs)?

## Method

### Definitions

**Scaffold-only revision** is defined as a repair mode that may edit any code outside `# CORE_START` / `# CORE_END` sentinel markers but must not alter text within those markers. Enforcement is via SHA-256 hash comparison of the protected region before and after the revision pass.

**Fixture classification:**

- *Scaffold-class fixture*: a code artifact whose core algorithm is correct but whose scaffold (imports, exports, CLI, wrappers, formatting) contains injected defects.
- *Core-wrong fixture*: a code artifact whose core algorithm contains an injected defect, used as a negative control.

### Benchmark Harness

A synthetic benchmark harness (`src/scaffold_revision_harness.py`) was constructed with the following properties:

- **6 tasks**, each with **6 fixtures** (30 scaffold-class + 6 core-wrong = 36 total fixtures).
- Scaffold defects were injected into imports, exported function names, CLI argument parsing, output formatting, and wrapper glue.
- Core defects were injected into algorithm logic within the protected region.
- Each fixture includes a test suite that can pass only when both scaffold and core are correct.

### Revision Procedure

The scaffold-only repair pass operates as follows:

1. Compute SHA-256 hash of the protected region (`# CORE_START` through `# CORE_END`).
2. Apply scaffold-only edits (outside the sentinel boundaries).
3. Recompute SHA-256 hash of the protected region.
4. If hashes differ, reject the revision.
5. Run the fixture's test suite to determine pass/fail.

### Environment

- Total system memory: 121 GiB (measured via `free -h`), with approximately 116 GiB available.
- Swap: disabled (0 B).
- No GPU or UMA stress paths were used; this was not a long inference run.
- Memory availability was recorded from `/proc/meminfo` before and after the experiment run.

### Execution

The experiment was invoked via `run_experiment.sh`. Static verification of the harness source was performed via `python3 -m py_compile`. Logs were captured to `artifacts/logs/scaffold_revision_harness.log` and `artifacts/logs/py_compile.log`.

## Results

### Primary Metrics

| Metric | Value |
|---|---|
| Total fixtures | 36 |
| Tasks | 6 |
| Scaffold-class fixtures | 30 |
| Core-wrong fixtures | 6 |
| Baseline pass count (before repair) | 6 |
| Scaffold fixtures initially failing | 24 |
| Scaffold fixtures passing after repair | 30 |
| Scaffold after-repair pass rate | 1.0 |
| Scaffold recovery rate (among initial failures) | 1.0 |
| Core-wrong false-repair count | 0 |
| Protected-core-unchanged count | 36 |
| Protected-core-unchanged rate | 1.0 |
| Elapsed time | 0.99 s |
| Throughput | 36.3 fixtures/s |

### Memory Stability

| Measurement | Available KiB |
|---|---|
| Before run | 122,510,128 |
| After run | 122,501,832 |

Memory availability remained stable throughout the experiment, with a negligible decrease of 8,296 KiB (~8.1 MiB), consistent with normal process overhead.

### Scaffold Recovery

All 24 scaffold-class fixtures that initially failed were recovered to a passing state by scaffold-only repair. The 6 scaffold-class fixtures that already passed before repair remained passing. No scaffold-class fixture was made worse by the repair pass.

### Core-Wrong Negative Controls

All 6 core-wrong fixtures remained failing after scaffold-only repair. The scaffold-only constraint correctly prevented the repair pass from altering core algorithm logic, and no false repair occurred.

### Protected Region Integrity

SHA-256 hash equality held for all 36 fixtures. The protected core region was preserved byte-for-byte in every case, confirming that the sentinel-based hash gate is an effective enforcement mechanism at the synthetic benchmark level.

## Limitations

1. **Synthetic benchmark only.** The fixtures are procedurally generated with injected defects. Real code failures exhibit more varied and subtle defect patterns. The scaffold repair logic in this harness is deterministic and has direct access to the correct scaffold structure; a live language model would need to infer correct scaffold edits from context, which is a fundamentally harder problem.

2. **No live model evaluation.** This experiment tests the feasibility and enforcement properties of the scaffold-only constraint, not whether a production LLM can produce correct scaffold edits under this constraint. Scientific closure on production utility requires evaluation on real failed outputs with a live-model revision pass operating under the same hash gate.

3. **Limited defect taxonomy.** Injected scaffold defects cover imports, exported names, CLI parsing, output formatting, and wrapper glue. Other scaffold defect categories (e.g., type annotation mismatches, async/sync signature conflicts, dependency version incompatibilities) are not represented.

4. **No Notion page body.** The original project specification was available only as a title and mission statement; the Notion page body was not retrievable during the experiment. The operationalization was derived from the title alone, which may differ from the original intent.

5. **Small scale.** 36 fixtures across 6 tasks is sufficient for a feasibility demonstration but inadequate for statistical generalization. Confidence intervals on the observed 1.0 rates would be wide.

6. **No adversarial evaluation.** The benchmark does not test whether the sentinel markers themselves could be manipulated, or whether the repair pass could achieve a passing test through scaffold edits that circumvent the core algorithm's intended behavior without modifying the protected region.

7. **Deterministic repair logic.** The harness repair pass uses deterministic, rule-based edits with direct knowledge of the correct scaffold structure. This establishes an upper bound on repairability under the scaffold-only constraint but does not reflect the difficulty a stochastic model would face when inferring correct edits from error signals alone.

## Reproducibility Checklist

- [x] Source code for the benchmark harness is included (`src/scaffold_revision_harness.py`).
- [x] Experiment runner script is included (`run_experiment.sh`).
- [x] Raw fixture results are recorded (`artifacts/results/scaffold_revision_results.json`).
- [x] Summary results are recorded (`artifacts/results/summary.md`).
- [x] Execution logs are captured (`artifacts/logs/scaffold_revision_harness.log`).
- [x] Static verification log is captured (`artifacts/logs/py_compile.log`).
- [x] Notion fetch log is captured (`artifacts/logs/notion_head.log`, `artifacts/logs/notion_extract.log`).
- [x] Notion page HTML is captured (`artifacts/logs/notion_page.html`).
- [x] Project decision JSON is recorded (`.omx/project_decision.json`).
- [x] Run notes are recorded (`run_notes.md`).
- [x] Environment details (memory, swap status) are documented in run notes.
- [x] All metric definitions and values are specified in the decision JSON.
- [ ] Real-world trace corpus: not available for this experiment.
- [ ] Live model revision pass: not evaluated.

## Conclusion

Scaffold-only revision mode, enforced by sentinel-delimited protected regions and SHA-256 hash gates, is feasible as a safety mechanism for constrained code repair. In a synthetic benchmark of 36 fixtures, the mode recovered all scaffold-class failures (24/24) while preserving protected core text in every case (36/36) and producing zero false repairs on core-wrong negative controls (0/6). These results establish that the enforcement mechanism works as designed and that scaffold defects in the tested taxonomy are repairable without touching core algorithm code.

However, this is a feasibility result on a synthetic benchmark, not a production validation. The critical open question is whether a live language model, operating under the scaffold-only constraint, can infer and apply correct scaffold edits on real failure traces. The deterministic repair logic in this harness provides an upper bound on repairability; the gap between this upper bound and live-model performance remains unmeasured. We recommend validating the mode on real revision traces or live model outputs with the same protected-region hash gate, using this harness as the acceptance oracle.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Benchmark harness source | `src/scaffold_revision_harness.py` |
| Experiment runner | `run_experiment.sh` |
| Raw fixture results | `artifacts/results/scaffold_revision_results.json` |
| Results summary | `artifacts/results/summary.md` |
| Harness execution log | `artifacts/logs/scaffold_revision_harness.log` |
| Static verification log | `artifacts/logs/py_compile.log` |
| Notion HEAD log | `artifacts/logs/notion_head.log` |
| Notion extract log | `artifacts/logs/notion_extract.log` |
| Notion page HTML | `artifacts/logs/notion_page.html` |
| Project decision JSON | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260501T223248529148+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T223248529148+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T223248529148+0000/paper_manifest.json` |
