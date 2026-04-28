# Agent App Store With Repro Sandboxes: A Toy Validation of Permission-Manifested Skill Packaging and Sandbox Guardrails

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We present a toy-scale validation of a local-first agent skill marketplace design in which each skill entry ships with deterministic metadata, an explicit permission manifest, and a sandboxed install-and-test harness. A mini marketplace of 10 valid skill fixtures and 4 adversarial invalid fixtures was constructed and exercised by an automated smoke harness. The valid-skill install pass rate was 1.0 (10/10), and the adversarial rejection rate was 1.0 (4/4), with zero guardrail failures across four rejection classes: undeclared permissions, nondeterminism, timeout, and failing deterministic tests. These results support the mechanism at toy scale but do not establish external validity: the harness relies on static policy markers and Python-level isolation rather than OS-level syscall or network enforcement, and no real-world third-party agent skills were tested. The project decision is `finalize_positive` with `supported` hypothesis status, bounded to the tested setting.

## 1. Introduction

As autonomous agents become more capable, the need for shareable, composable skill modules grows. However, installing an untrusted skill into an agent's runtime introduces risks: the skill may access undeclared resources, behave nondeterministically, exceed resource budgets, or simply produce incorrect outputs. A marketplace that enforces reproducible sandbox validation at install time could mitigate these risks by requiring each skill to declare its capabilities and pass a deterministic test before acceptance.

This report describes a bounded toy experiment that tests whether such a mechanism can produce measurable, reproducible install-time signals. The central question is: *can a local-first marketplace harness, given deterministic skill metadata and explicit permission manifests, reliably accept valid skills and reject invalid ones across multiple failure classes?*

The experiment does not attempt to prove the mechanism at production scale or under adversarial conditions beyond the four classes tested. It aims only to determine whether the mechanism produces a clear, measurable signal in a controlled toy setting.

## 2. Method

### 2.1 Marketplace Structure

A mini local-first marketplace was constructed containing 10 valid skill entries. Each skill directory includes:

- **`skill.json`**: Deterministic metadata specifying the skill entrypoint, test command, and expected stdout.
- **`permissions.json`**: Explicit capability manifest declaring boolean claims for `network`, `filesystem`, and `env` access.
- **`runner.py`**: The skill payload implementing the declared behavior.
- **`README.md`**: Human-readable description.

The 10 valid skills are: `slugify`, `json_sort`, `word_count`, `reverse_lines`, `sha256`, `csv_sum`, `template_fill`, `regex_extract`, `markdown_title`, and `permission_echo`. All valid skills declare permissions consistent with their implementations and produce deterministic output matching their declared expected stdout.

### 2.2 Adversarial Fixtures

Four invalid skill fixtures were added to a separate invalid lane:

| Fixture | Violation | Expected Rejection Class |
|---|---|---|
| `invalid_undeclared_permission` | Imports `socket` while manifest declares `network: false` | Permission-policy violation |
| `invalid_nondeterministic` | Emits `time.time_ns()` producing varying stdout | Nondeterminism detection |
| `invalid_timeout` | Sleeps beyond the sandbox timeout threshold | Timeout |
| `invalid_failing_test` | Deterministic output does not match declared expected stdout | Failing deterministic test |

### 2.3 Sandbox Harness

The automated smoke harness (`scripts/run_marketplace_smoke.py`) performs the following for each skill:

1. Validates `skill.json` and `permissions.json` manifest shape.
2. Stages the skill in an isolated temporary install root.
3. Executes the declared test command with a restricted environment.
4. Compares actual stdout against declared expected stdout.
5. For the invalid lane, classifies the rejection reason and checks it matches the expected guardrail class.

The harness fails the overall run if any valid skill fails, any invalid skill is accepted, or any invalid skill is rejected for the wrong guardrail class.

### 2.4 Fixture Generation

All fixtures are generated deterministically by `scripts/create_mini_marketplace.py`, ensuring reproducibility of the marketplace index and skill payloads.

## 3. Results

### 3.1 Initial Valid-Only Run

The first smoke test (valid skills only) produced:

| Metric | Value |
|---|---|
| Skills tested | 10 |
| Passed | 10 |
| Failed | 0 |
| Reproducible install pass rate | 1.0 |
| Wall-clock time | ~0.224 s |
| Skills/sec | ~44.6 |
| p50 install+test latency | ~28.1 ms |
| p95 install+test latency | ~28.7 ms |
| Max RSS | 14,988 KB |

A UMA-aware memory sample from `/proc/meminfo` was captured, including `MemAvailable`, `SwapFree`, `HugePages_Free`, and `Hugepagesize`.

### 3.2 Adversarial Validation Run

After adding the invalid lane, the combined run produced:

| Metric | Value |
|---|---|
| Valid skills tested | 10 |
| Valid passed | 10 |
| Valid failed | 0 |
| Reproducible valid install pass rate | 1.0 |
| Invalid skills tested | 4 |
| Invalid rejected with expected class | 4 |
| Invalid accepted | 0 |
| Invalid wrong rejection class | 0 |
| Invalid rejection rate | 1.0 |
| Guardrail failures | 0 |
| Wall-clock time | ~1.47 s |

The wall-clock time is dominated by the 1-second timeout fixture. Excluding that fixture, the remaining operations complete in sub-second time.

### 3.3 Per-Class Rejection Detail

- **Permission-policy violation**: The harness detected the `socket` import via static permission-policy scan and rejected the skill before execution.
- **Nondeterminism**: Repeated deterministic test runs produced different stdout across invocations, triggering rejection.
- **Timeout**: The skill exceeded the sandbox timeout threshold and was rejected with a timeout diagnostic.
- **Failing deterministic test**: The skill's actual stdout did not match the declared expected stdout, triggering rejection.

All four rejections were classified into the expected guardrail class with zero misclassifications.

## 4. Limitations

This experiment is a toy-scale validation and carries several important limitations:

1. **Static policy markers, not OS-level enforcement.** The permission manifest uses boolean declarations checked by static analysis (e.g., scanning for `socket` imports). No OS-level syscall filtering, network namespace isolation, seccomp policies, or container-based sandboxing is applied. A skill could circumvent the static check by obfuscating its access pattern (e.g., using `ctypes` or dynamic imports).

2. **Python-level isolation only.** Skills are staged in temporary directories with restricted environment variables, but there is no process-level or kernel-level isolation. Resource limits beyond the timeout threshold are not enforced.

3. **No real-world third-party skills.** All 14 fixtures were authored as part of the experiment. The behavior of messy, real-world agent skills—complex dependency chains, side effects, implicit state—was not tested.

4. **Small fixture count.** Ten valid and four invalid fixtures constitute a minimal test surface. Statistical claims about pass rates at this scale are weak.

5. **Single execution environment.** All runs were executed on a single machine with a single Python version. Cross-platform, cross-runtime, or multi-user behavior was not assessed.

6. **Nondeterminism detection is shallow.** The harness detects nondeterminism by running the test twice and comparing stdout. A skill that is nondeterministic only under rare conditions or only after many invocations would not be caught.

7. **No measurement of the harness's own failure modes.** The experiment does not test what happens when the harness itself is buggy, when the manifest schema changes, or when the test runner encounters an internal error.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Fixture generation script available | Yes (`scripts/create_mini_marketplace.py`) |
| Smoke harness script available | Yes (`scripts/run_marketplace_smoke.py`) |
| Result file persisted | Yes (`results/marketplace_smoke.json`) |
| Marketplace index reproducible | Yes (deterministic generation) |
| Skill manifests and payloads versioned | Yes (in `marketplace/` directory tree) |
| Invalid fixtures documented | Yes (in `marketplace/invalid/` directory tree) |
| Execution commands recorded | Yes (in `run_notes.md`) |
| Hardware/runtime environment specified | Partial — Max RSS and `/proc/meminfo` captured; full system specs not recorded |
| External dependencies | Python 3 standard library only; no third-party packages |

## 6. Conclusion

A local-first agent skill marketplace design with deterministic metadata, explicit permission manifests, and sandboxed install-time validation produced a clear positive signal in a toy-scale experiment. The harness accepted all 10 valid skills (install pass rate 1.0) and correctly rejected all 4 adversarial invalid skills (rejection rate 1.0, zero guardrail failures, zero misclassifications) across four distinct violation classes.

These results support the mechanism within the tested setting but do not establish that it generalizes to real-world third-party skills, OS-level adversarial conditions, or production-scale workloads. The primary remaining risk is external validity: static permission markers and Python-level isolation are insufficient against determined adversaries or complex real-world skill behaviors.

The project decision is `finalize_positive` with `supported` hypothesis status. The recommended next step, if pursued, would target OS-level sandbox enforcement (syscall filtering, network namespaces, seccomp) against real third-party skills. Absent that, the current toy validation is treated as complete within its bounded scope.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Metrics | `.omx/metrics.json` |
| Evidence bundle | `papers/source-record-redacted/evidence_bundle.json` |
| Claim ledger | `papers/source-record-redacted/claim_ledger.json` |
| Paper manifest | `papers/source-record-redacted/paper_manifest.json` |
| Smoke test results | `results/marketplace_smoke.json` |
| Marketplace index | `marketplace/index.json` |
| Invalid marketplace index | `marketplace/invalid_index.json` |
| Fixture generation script | `scripts/create_mini_marketplace.py` |
| Smoke harness script | `scripts/run_marketplace_smoke.py` |
| Project README | `README.md` |
