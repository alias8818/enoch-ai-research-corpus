# Skill Preflight Gate Integration: Redirecting Vague Execution-Mode Prompts to Planning Before Durable State Seeding

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, benchmark logs, and test outputs). The operator who released this artifact claims no personal authorship credit for the writing or experimental results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Execution-mode keyword triggers in the OMX (oh-my-codex) framework—such as `$autopilot`, `$ralph`, `$team`, and `$ultrawork`—activate skills and seed durable execution state immediately upon detection. When a prompt is vague (e.g., `$autopilot fix it`), this immediate activation commits to an execution mode without prior planning, even though the framework already contains a preflight gate function (`applyRalplanGate()`) designed to redirect such cases to a planning skill (`$ralplan`). This paper documents a local integration shim that wires the existing preflight gate into the native skill activation seam, evaluates its behavior through automated tests and a throughput benchmark, and assesses remaining risks for upstream integration. In the integrated shim, vague prompts redirect to `$ralplan` while well-specified prompts pass through and `$cancel` bypasses the gate. A benchmark of 50,000 prompt evaluations completed in 137.4 ms (~363,870 ops/s). However, the proposed patch targets compiled JavaScript rather than the original TypeScript source (which was absent from the published package), and upstream closure requires source-level integration and the full native-hook regression suite. The result is classified as viable at the prototype level but not production-validated.

## Introduction

The OMX framework provides keyword-triggered skill activation as a core interaction mechanism. When a user issues a prompt containing a recognized skill keyword (e.g., `$autopilot`), the system activates the corresponding skill and seeds a durable execution state (`initialized_mode`). This design prioritizes responsiveness: the user's intent is interpreted and acted upon without an intermediate planning step.

A known tension exists when prompts contain execution-mode keywords but lack sufficient specification for durable execution. For example, `$autopilot fix it` activates the `autopilot` skill and sets `initialized_mode: autopilot`, yet the prompt provides no actionable target for the autopilot mode. The framework already includes `applyRalplanGate()`, a function that detects such cases and recommends redirection to `$ralplan` (a planning-phase skill). However, at the time of this study, `applyRalplanGate()` is not wired into the native skill activation path. The gate's output is computed but not consumed: the skill activates on the original keyword regardless of the gate's recommendation.

This paper investigates whether integrating the existing preflight gate at the skill activation seam produces the desired routing behavior—redirecting vague execution prompts to planning while preserving direct activation for well-specified prompts—without introducing new dependencies or significant runtime overhead. The investigation is limited to a local integration shim operating against the installed OMX package; it does not constitute a merged upstream change.

## Method

### Environment

All experiments were conducted on a single machine with the following software stack:

| Component | Version |
|---|---|
| Node.js | v22.22.1 |
| npm | 10.9.4 |
| OMX (oh-my-codex) | v0.15.2 |
| Codex CLI | 0.128.0 |
| Python | 3.12.3 |

System memory during the run: `MemAvailable` reported 116–122 GiB; `SwapTotal: 0 kB`. No swap activity was observed. These conditions reflect a resource-rich single-machine environment and may not generalize to constrained deployments.

### Implementation

The integration shim (`scripts/skill_preflight_gate.mjs`) imports the installed OMX module `dist/hooks/keyword-detector.js` and defines a function `preflightSkillActivationText()` that invokes the existing `applyRalplanGate()` before skill activation proceeds. The shim does not introduce new dependencies; it calls a function already present in the installed OMX package.

A test suite (`tests/skill_preflight_gate.test.mjs`) asserts three behaviors:

1. **Vague prompt gating:** A prompt containing an execution-mode keyword without sufficient specification (e.g., `$autopilot fix it`) is redirected to `$ralplan`.
2. **Well-specified prompt pass-through:** A prompt containing an execution-mode keyword with concrete instructions (e.g., `$autopilot update src/hooks/keyword-detector.ts and run npm test`) retains the original skill activation.
3. **Cancel bypass:** The `$cancel` keyword bypasses the preflight gate and remains `cancel`.

A benchmark script (`scripts/skill_preflight_benchmark.mjs`) evaluates preflight-gate throughput over 50,000 iterations.

### Procedure

Three commands were executed:

1. **Smoke test:** `node scripts/skill_preflight_gate.mjs` — compares baseline `recordSkillActivation()` behavior against integrated preflight behavior, logging structured JSON output.
2. **Automated test suite:** `/usr/bin/time -v node --test tests/skill_preflight_gate.test.mjs` — runs the three assertions above with resource measurement.
3. **Throughput benchmark:** `/usr/bin/time -v node scripts/skill_preflight_benchmark.mjs 50000` — measures preflight-only evaluation rate.

All outputs were captured to artifact log files (see Referenced Artifacts).

## Results

### Baseline Gap Reproduced

Under the unmodified OMX skill activation path, the prompt `$autopilot fix it` activates the `autopilot` skill and sets `initialized_mode: autopilot`. Simultaneously, `applyRalplanGate()` reports `gateApplied: true`, `gatedKeywords: ["autopilot"]`, and replacement `keywords: ["ralplan"]`. This confirms the gap: the gate detects the need for redirection but its output is not consumed by the activation path. The gate fires but has no effect on the skill that is activated.

### Integrated Shim Behavior

With the preflight gate wired into the activation seam:

| Prompt | Integrated Skill | Phase / Mode |
|---|---|---|
| `$autopilot fix it` | `ralplan` | `planning` / `initialized_mode: ralplan` |
| `$autopilot update src/hooks/keyword-detector.ts and run npm test` | `autopilot` | (unchanged) |
| `$cancel` | `cancel` | (bypasses gate) |

The shim redirects vague execution prompts to planning while preserving well-specified activation and cancel bypass. These results are from the local shim only; they have not been validated in the OMX runtime itself.

### Automated Test Results

The test suite reported 3 tests, 3 passed, exit status 0. Resource usage for the test run:

- Wall time: 0.09 seconds
- Max RSS: 60,180 kB
- Swaps: 0

### Throughput Benchmark

Over 50,000 preflight-gate evaluations:

| Metric | Value |
|---|---|
| Elapsed time | 137.412 ms |
| Operations per second | ~363,870 |
| Max RSS (from `/usr/bin/time`) | 69,156 kB |

The per-evaluation overhead of the preflight gate is approximately 2.7 µs. This is small relative to typical LLM inference latencies (which are orders of magnitude larger), though the benchmark measures only the gate evaluation in isolation, not the full activation path or any downstream LLM call.

## Limitations

Several limitations constrain the generality of these results:

1. **Compiled-JS patch, not source-level.** The published OMX npm package includes compiled `dist/` files and partial `src/`, but the TypeScript source corresponding to `dist/hooks/keyword-detector.js` was not present in the package. The proposed integration patch (`artifacts/proposed_integration_patch.diff`) targets the compiled JavaScript. A proper upstream contribution must patch the original TypeScript source and rebuild. The compiled-JS patch demonstrates the integration point but is not directly mergeable.

2. **Local shim, not production integration.** The shim operates on the installed package's exports. It validates that the desired behavior is achievable at the prototype level but does not constitute a merged, regression-tested change to OMX itself. Final production closure requires applying the source patch in the OMX repository and running the full native-hook regression suite, which was not available in this environment.

3. **Multi-skill invocation semantics untested.** Prompts containing multiple explicit skill invocations (e.g., `$ralplan $team $ralph`) may interact with the gate in ways not covered by the current three-assertion test suite. Upstream integration should add dedicated regression tests for multi-skill invocations to ensure planning-preservation semantics still win when multiple keywords are present.

4. **Follow-up shortcut double-gating risk.** Runtime follow-up shortcuts depend on `priorSkill` and planning artifact state. If the preflight gate is applied without awareness of prior planning completion, a follow-up prompt could be incorrectly re-gated to `$ralplan`. The upstream integration must pass `priorSkill` and planning state options from existing session state exactly once to avoid double-gating. This risk is identified but not empirically evaluated.

5. **Single-machine evaluation.** All measurements were taken on one machine with abundant memory (116–122 GiB available). Performance characteristics may differ under memory pressure, different Node.js versions, or different hardware.

6. **No end-to-end session validation.** The tests verify skill-keyword routing logic in isolation. They do not validate that the redirected `$ralplan` skill produces a planning artifact that correctly feeds back into subsequent execution-mode activation. This session-level flow remains unvalidated.

7. **Vagueness classification depends on `applyRalplanGate()` heuristics.** The boundary between "vague" and "well-specified" prompts is determined by the existing gate function, whose internal heuristics were not audited in this study. The two test cases (one vague, one well-specified) demonstrate that the shim preserves the gate's existing classification, but they do not characterize the full decision boundary.

## Reproducibility Checklist

- [x] **Software versions specified:** Node.js v22.22.1, npm 10.9.4, OMX v0.15.2, Codex CLI 0.128.0, Python 3.12.3.
- [x] **Hardware context reported:** Memory available 116–122 GiB, no swap.
- [x] **Commands listed verbatim:** All three run commands are documented in the Method section and run notes.
- [x] **Output artifacts preserved with checksums:** All log, metric, and diff artifacts are listed with SHA-256 hashes in the decision JSON and Referenced Artifacts section.
- [x] **Test exit status reported:** Exit status 0, 3/3 tests pass.
- [x] **Benchmark parameters stated:** 50,000 iterations, elapsed time and ops/s reported.
- [x] **Negative results and risks documented:** Compiled-JS patch limitation, multi-skill gap, double-gating risk, single-machine scope, no end-to-end validation, vagueness boundary uncharacterized.
- [ ] **Upstream regression suite run:** Not available in this environment; required for production closure.
- [ ] **TypeScript source patch applied:** Not possible from published package alone; required for upstream merge.

## Conclusion

The existing OMX `applyRalplanGate()` function can be integrated at the native skill activation seam to redirect vague execution-mode prompts to planning before durable execution state is seeded. A local integration shim demonstrates the desired behavior—vague prompts route to `$ralplan`, well-specified prompts pass through, and `$cancel` bypasses the gate—with no new dependencies and low per-evaluation overhead (~363,870 ops/s, ~2.7 µs per evaluation). Automated tests confirm the three core routing behaviors.

However, this result is a prototype validation, not a production integration. The patch targets compiled JavaScript because the corresponding TypeScript source was not available in the published package. Upstream closure requires a source-level patch, the full OMX native-hook regression suite, and additional coverage for multi-skill invocations and follow-up shortcut semantics. The double-gating risk in session-level flows is identified but not empirically evaluated. The vagueness-classification boundary of `applyRalplanGate()` is taken as-is without independent audit. The finding is classified as viable positive with high confidence for the isolated routing logic, but production readiness depends on upstream integration work that falls outside the scope of this study.

## Referenced Artifacts

| Artifact | Path | SHA-256 |
|---|---|---|
| Run notes | `run_notes.md` | `c04b1d877dfc48e928b4249c6fdce71ef8ab199af8737626aba412249657458a` |
| Integration shim | `scripts/skill_preflight_gate.mjs` | `5c346d142d6187a217157c12aa03055549b938c668922d3f85e9e5e6e071b433` |
| Benchmark script | `scripts/skill_preflight_benchmark.mjs` | `106d1e01bf58f66b8c115b246ef395a47c9eae757f853e3f56153381b02abcdc` |
| Test suite | `tests/skill_preflight_gate.test.mjs` | `31db1aa68cc071a6ffe13ababbeb69bb9e327ffe21f1ecf852c35f59295885e8` |
| Integration notes | `artifacts/integration_notes.md` | `5628e6ba4de3613c239636d5d4f57b9c08e1c5ab2f23e712671ac98f85788978` |
| Proposed patch | `artifacts/proposed_integration_patch.diff` | `c7061bae23d27532f2a3ab68ad3c6a2b9a3d12622ef67a898fd162bdef6f930f` |
| Smoke log | `artifacts/logs/skill_preflight_gate_smoke.json` | `ba9411a734d5968f7508116b7d404bf4f26e7b252e8c3e4bf098501a992efbb5` |
| Test output log | `artifacts/logs/node_test_skill_preflight_gate.log` | `355d574ad1b62694bbda4b6f104caa8aaf41b795de22b7d99402e4e3fc3be1cc` |
| Test time log | `artifacts/logs/node_test_skill_preflight_gate.time.log` | `fc75b0ba71ebe58372fa2f6c7fefaa73cbda5694534133909c361711316f8d0c` |
| Benchmark time log | `artifacts/logs/skill_preflight_gate_benchmark.time.log` | `9354da63c9fa33f087d20d708adff7996cb9964960be8cacd84d713106ba306c` |
| Test metrics | `artifacts/metrics/skill_preflight_gate_test_metrics.json` | `47cc791a172db5170076db4c36c765af50b07aad1c5c0a0a6bc61ab1b15b7a1b` |
| Benchmark metrics | `artifacts/metrics/skill_preflight_gate_benchmark.json` | `bdee69ea76a485f2be0bac8468a8a43adcde05ed7f4515f6f3dc305f9ab074c8` |
| Project decision | `.omx/project_decision.json` | (in project directory) |
| Claim ledger | `papers/.../claim_ledger.json` | (in paper directory) |
| Evidence bundle | `papers/.../evidence_bundle.json` | (in paper directory) |
| Paper manifest | `papers/.../paper_manifest.json` | (in paper directory) |
