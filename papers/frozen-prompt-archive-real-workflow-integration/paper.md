# Frozen Prompt Archive Integration with Real Workflow Artifacts: Drift Detection and Audit Burden Reduction in Autonomous Controller Prompts

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, benchmark metrics, and evidence bundles). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated the claims herein.

---

## Abstract

Autonomous controller systems that manage compute infrastructure via LLM-driven prompts face an under-examined reliability problem: prompt policies embedded in controller configurations drift across deployments and over time without systematic tracking. This paper reports on the integration of a frozen prompt archive mechanism with 803 real local Enoch/OMX workflow projects, scanning 2,537 prompt surfaces and producing 11,719 immutable archive records. The archive detected 2,152 structural drift proxy incidents across six policy categories and identified systematic missing-policy surfaces—most prominently, a GPU utilization policy absent from 928 first-turn controller prompts. By normalizing and hashing policy scaffolds, the archive reduces the audit surface from 148.6 MB across 2,537 source files to 193 unique policy-section versions, a 13.15× reduction. Throughput was 219.9 surfaces/s with p50 latency of 1.13 ms and p95 of 16.6 ms on a single-threaded scan. These results are limited to locally available workflow artifacts rather than a newly instrumented live controller run, and drift labels are structural rather than semantic. The findings demonstrate that naturally occurring prompt-policy drift is measurable, non-trivial in volume, and amenable to systematic audit compression, though the evidence strength applies to local workflow integration specifically and does not constitute a universal benchmark claim.

## Introduction

Autonomous infrastructure controllers increasingly rely on large language model prompts to encode operational policies, mission definitions, resource constraints, and branching logic. As these systems scale across many project deployments, the prompts that govern controller behavior become a hidden configuration surface—one that is typically version-controlled at the project level but rarely audited for cross-project consistency or temporal drift.

The core problem is straightforward: when a controller prompt policy changes in one project but not others, or when a policy section is silently omitted from certain prompt surfaces, the resulting behavioral divergence is difficult to detect without reading every prompt file and log. At the scale of hundreds of projects, manual audit becomes impractical. The run notes for this project record that manual/latest-source audit would require opening 2,537 prompt/log sources and reading 148,585,343 bytes.

A prior toy demonstration established that a frozen prompt archive—capturing immutable snapshots of prompt surfaces with content-addressable hashing—could in principle detect structural drift. The present work integrates that mechanism with real Enoch/OMX workflow artifacts to address three questions:

1. Does naturally occurring prompt-policy drift exist in real autonomous controller deployments, and at what scale?
2. Are there systematic missing-policy surfaces where expected policy sections are absent?
3. Can a frozen archive meaningfully reduce the audit burden compared to reading all source files?

## Method

### Architecture

The frozen prompt archive operates as a single-pass scanner over a directory tree of Enoch/OMX project artifacts. For each project, it identifies prompt surfaces—files and log excerpts containing controller prompts—and records an immutable archive entry containing:

- The full prompt content (hashed for deduplication)
- A normalized scaffold hash, which strips project-specific variable bindings while preserving policy-section structure
- The policy section identifier (e.g., "Decision Contract," "GB10 Autonomous Resource Policy")
- Provenance metadata (source path, surface type, timestamp)

The scanner targets three surface types per project: `prompts/initial.md`, `prompts/resume.md`, and first-turn Enoch stderr prompt logs. The scanner caps each project at the first three Enoch stderr prompt logs to avoid over-weighting noisy reruns.

### Drift Detection

Drift is detected structurally: when the same policy section (identified by category name) yields different normalized scaffold hashes across observations, each distinct hash version constitutes a drift incident. This is a proxy measure—it captures structural variation but does not assess semantic severity. Two prompts with identical scaffold structure but substantively different parameter values would be counted as the same version if normalization strips the differing values; conversely, formatting changes that do not alter semantics would register as drift.

Missing-policy detection flags cases where a policy section expected for a given surface type is absent. Expectations are derived from the union of policy sections observed across all surfaces of that type. This means that if a policy section is universally absent from a surface type, it would not be flagged as missing, making the missing-policy counts conservative lower bounds.

### Benchmark Configuration

Two benchmark runs were executed:

1. **Smoke calibration** (20 projects): validating pipeline correctness and measuring baseline throughput.
2. **Full real-workflow benchmark** (803 projects): scanning the complete local project tree at `/mnt/usb<local-path-redacted>`.

Both runs were executed on a single machine with approximately 122 GB available memory and zero swap. The scanner is single-threaded and Python-based. Unit tests were executed via `python3 -m unittest discover -s scripts -p 'test_*.py'`.

### Artifacts

The implementation and results are captured in the following artifacts:

| Artifact | Size | SHA-256 |
|---|---|---|
| `scripts/frozen_prompt_archive.py` | 5,497 B | `c7e5b5ef7cfc519e7e7249caf9b98fb9c86b62ed5b5534f1789d147c1d9de1ff` |
| `scripts/run_real_workflow_benchmark.py` | 13,041 B | `b213694663d6708e46e4fba1dd851bb4261cba0178d2d514fec1459f60fa402c` |
| `scripts/test_real_workflow_benchmark.py` | 1,779 B | `fcd44f385f045c5a041518b2c96a6fb1a2023c849598acf8de632e414a87aed5` |
| `artifacts/real_workflow_smoke_20/reports/metrics.json` | 9,980 B | `ce2cb4a24ff1145f054b680264ace06ba545c49d2c3146b173c93f71eb88158d` |
| `artifacts/real_workflow_full/reports/metrics.json` | 12,071 B | `fa2e1ff63f414e977e871dd67b04857e067de4313288fabb5b73954ceb83d2e3` |
| `artifacts/real_workflow_full/reports/surfaces.jsonl` | 1,648,281 B | `817751cb8b115bba2084765210bddca1a0ef49583716d727adc0fde99208f56d` |
| `artifacts/real_workflow_full/archive/manifest.jsonl` | 8,288,969 B | `684da5d727ba3d58084834b03a1fe10f9ea06f63d1e18c86f33f5e068ff7f761` |

## Results

### Scale and Throughput

The full benchmark scanned 803 project directories, identifying 2,537 prompt surfaces and producing 11,719 frozen archive records. The manifest is stored as newline-delimited JSON in `artifacts/real_workflow_full/archive/manifest.jsonl`.

| Metric | Smoke (20 projects) | Full (803 projects) |
|---|---|---|
| Projects scanned | 20 | 803 |
| Prompt surfaces | 60 | 2,537 |
| Archive records | 240 | 11,719 |
| Throughput (surfaces/s) | 298.4 | 219.9 |
| Latency p50 | 0.325 ms | 1.129 ms |
| Latency p95 | 14.181 ms | 16.618 ms |
| Elapsed time | — | 11.539 s |
| MemAvailable start (kB) | 122,457,896 | 121,653,304 |
| MemAvailable end (kB) | 122,453,164 | 122,538,344 |
| SwapTotal (kB) | 0 | 0 |

Memory consumption was negligible relative to available capacity, and no swap activity occurred. The throughput decrease from smoke to full run (298.4 → 219.9 surfaces/s) is consistent with increased I/O overhead from a larger directory tree. Memory available at end of the full run (122,538,344 kB) was slightly higher than at start (121,653,304 kB), suggesting no memory leak and possible return of buffers to the available pool.

### Prompt Uniqueness

Across 2,537 surfaces, 2,528 unique full-prompt hashes were observed, indicating near-total uniqueness at the full-prompt level. This is expected: project-specific variable bindings (names, paths, resource limits) ensure that full prompts rarely collide. At the normalized scaffold level, 1,966 unique hashes were observed, reflecting moderate deduplication when project-specific content is stripped.

### Drift Detection

The archive detected 2,152 drift proxy incidents across six policy categories. The distribution reveals qualitatively different drift patterns:

**Low-drift policies** (1 version, no structural drift detected):
- *Successor / Branch Policy*: 1,785 observations, 1 unique version.
- *Mission*: 542 observations, 1 unique version.

**Moderate-drift policies** (2–4 versions, with a dominant version and minority variants):
- *GB10 Autonomous Resource Policy*: 1,785 observations, 2 unique versions. The dominant version accounts for 1,782 observations; a variant accounts for 3.
- *Decision Contract*: 1,988 observations, 4 unique versions. The dominant version accounts for 1,784 observations; three variants account for 167, 36, and 1 observation(s) respectively.

**High-drift policies** (many versions, no single dominant scaffold):
- *Operating constraints*: 542 observations, 182 unique versions. The two most common versions account for 181 observations each, but the remaining 180 versions are unique or near-unique. This reflects the inherently project-specific nature of operating constraints.
- *GB10 GPU Utilization / Performance Policy*: 3 observations, 3 unique versions. Each observation is structurally distinct.

The Decision Contract drift is notable: 4 structural versions across 1,988 observations, with one variant appearing 167 times, suggests a deliberate policy update that propagated to a subset of projects but not all. However, this interpretation has not been confirmed by semantic review.

### Missing-Policy Surfaces

The archive identified systematic absences of expected policy sections:

| Surface Type | Missing Policy | Count |
|---|---|---|
| `enoch_first_turn_stderr_prompt` | GB10 GPU Utilization / Performance Policy | 928 |
| `initial_prompt_file` | GB10 GPU Utilization / Performance Policy | 803 |
| `resume_prompt_file` | GB10 GPU Utilization / Performance Policy | 803 |
| `enoch_first_turn_stderr_prompt` | Mission | 751 |
| `enoch_first_turn_stderr_prompt` | Operating constraints | 751 |
| `initial_prompt_file` | Mission | 622 |
| `initial_prompt_file` | Operating constraints | 622 |
| `resume_prompt_file` | Mission | 622 |
| `resume_prompt_file` | Operating constraints | 622 |
| `enoch_first_turn_stderr_prompt` | GB10 Autonomous Resource Policy | 260 |
| `enoch_first_turn_stderr_prompt` | Successor / Branch Policy | 260 |
| `initial_prompt_file` | GB10 Autonomous Resource Policy | 246 |

The GPU Utilization / Performance Policy is absent from all 803 `initial_prompt_file` and `resume_prompt_file` surfaces, and from 928 of the stderr prompt surfaces. This pattern is consistent with the hypothesis that the policy was introduced partway through the controller's deployment history and was never backfilled into existing prompt templates, though alternative explanations have not been ruled out.

### Audit Burden Reduction

Manual audit of all 2,537 prompt sources would require opening 2,537 files and reading 148,585,343 bytes (approximately 142 MB). The frozen archive compresses the policy-section audit to 193 unique section versions, a 13.15× reduction in the number of distinct policy texts an operator must review. Full-prompt audit remains high-cardinality (2,528 unique full prompts), which is the expected behavior for project-specific prompts; the archive's value for full prompts is preservation and provenance rather than deduplication.

## Limitations

1. **Local artifacts, not live instrumentation.** The benchmark operates on locally available Enoch/OMX workflow artifacts rather than a newly instrumented live controller run. While these artifacts are real workflow outputs with real controller timestamps and logs, they represent a retrospective snapshot rather than a prospective validation.

2. **Structural drift, not semantic drift.** Drift incidents are detected via normalized scaffold hash differences. Two prompts with identical structure but substantively different semantic content (e.g., a resource limit changed from "100 GB" to "10 GB") would be counted as the same scaffold version if the variable-binding normalization strips the differing value. Conversely, formatting changes that do not alter semantics would register as drift. Semantic severity assessment still requires operator review for high-impact policy changes.

3. **Rerun capping.** The scanner caps each project at the first three Enoch stderr prompt logs to avoid over-weighting noisy reruns. This means some prompt surfaces are excluded, and the drift counts are lower bounds rather than complete tallies.

4. **Single-machine, single-threaded execution.** All benchmarks ran on one machine with one thread. Parallelism characteristics and behavior on memory-constrained systems are not characterized.

5. **No semantic review of drift incidents.** The 2,152 drift proxy incidents have not been individually reviewed to classify which represent intentional policy updates, which are accidental regressions, and which are benign formatting changes. The aggregate counts establish that drift exists and is measurable, but do not establish its operational impact.

6. **Missing-policy expectations are derived empirically.** The set of "expected" policy sections is inferred from the union of sections observed across all surfaces of a given type. If a policy section is universally absent from a surface type, it would not be flagged as missing. The missing-policy counts are therefore conservative.

7. **Claim ledger is empty.** The automated claim ledger for this paper draft contains no formally registered claims, only a limitation noting that human claim audit is required. The findings reported here are drawn directly from run notes and benchmark metrics and have not undergone formal claim adjudication.

8. **Confidence is medium.** The project decision record assigns confidence "medium" and evidence strength "strong" for local workflow integration specifically. This does not support generalization beyond the observed Enoch/OMX deployment.

## Reproducibility Checklist

- **Code available:** `scripts/frozen_prompt_archive.py`, `scripts/run_real_workflow_benchmark.py`, `scripts/test_real_workflow_benchmark.py` (SHA-256 hashes recorded in Artifacts table above).
- **Unit tests:** Executed via `python3 -m unittest discover -s scripts -p 'test_*.py'`; log at `artifacts/logs/unit_tests.log`.
- **Benchmark command:** `python3 scripts/run_real_workflow_benchmark.py --root <path> --out <out_dir> --include-logs`.
- **Input data:** Local Enoch/OMX project directory at `/mnt/usb<local-path-redacted>`. This path is operator-specific and not publicly available; the archive manifest (`artifacts/real_workflow_full/archive/manifest.jsonl`) captures the scanned content.
- **Output data:** `artifacts/real_workflow_full/reports/metrics.json`, `artifacts/real_workflow_full/reports/surfaces.jsonl`, `artifacts/real_workflow_full/archive/manifest.jsonl`.
- **Randomness:** The scanner is deterministic; no random seeds are involved.
- **Hardware:** Single machine, ~122 GB RAM, 0 kB swap. CPU details not recorded in artifacts.
- **Software versions:** Python 3 (exact version not recorded in artifacts). OS not recorded.
- **Missing signals:** The paper review item flags a missing `readiness_audit` signal. The checklist progress records 0 of 9 items passed, with 9 pending. This draft has not completed the automated review checklist.

## Conclusion

Integrating a frozen prompt archive with 803 real Enoch/OMX workflow projects demonstrates that naturally occurring prompt-policy drift is measurable, non-trivial in volume, and systematically distributed. The archive detected 2,152 structural drift incidents and identified missing-policy surfaces affecting up to 928 controller prompt instances. By normalizing policy scaffolds, the archive reduces the operator audit burden from 2,537 source files (148.6 MB) to 193 unique policy-section versions—a 13.15× reduction—while preserving full-prompt provenance for forensic review.

These findings support adopting the frozen prompt archive as a controller-side provenance and audit step, consistent with the project decision record's recommendation. However, structural drift detection is a necessary but insufficient condition for operational safety: semantic review labels for high-severity policy drift remain a recommended next step. The gap between the 193 unique policy versions and the 2,152 drift incidents underscores that deduplication and drift detection serve complementary purposes—one compresses the review set, the other surfaces the variance that demands attention.

The evidence is moderate-to-strong for local workflow integration. It does not constitute a universal benchmark claim; the drift patterns and missing-policy surfaces observed here are specific to the Enoch/OMX deployment configuration and its evolution over time. Generalization to other autonomous controller systems would require replication with their respective workflow artifacts.

---

## Referenced Artifacts

| Name | Path | Description |
|---|---|---|
| Run notes | `run_notes.md` | Operator log of benchmark commands, results, and observations |
| Project decision | `.omx/project_decision.json` | Automated decision record: `finalize_positive`, hypothesis `supported`, confidence `medium`, evidence strength `strong` |
| Session metrics | `.omx/metrics.json` | Session token usage and activity timestamps |
| Claim ledger | `papers/.../claim_ledger.json` | Empty claims array; limitation noting human claim audit required |
| Evidence bundle | `papers/.../evidence_bundle.json` | Source and run ID metadata |
| Paper manifest | `papers/.../paper_manifest.json` | Generation timestamp and writer provider metadata |
| Archive script | `scripts/frozen_prompt_archive.py` | Core frozen prompt archive implementation (5,497 B) |
| Benchmark runner | `scripts/run_real_workflow_benchmark.py` | Real-workflow benchmark driver script (13,041 B) |
| Test suite | `scripts/test_real_workflow_benchmark.py` | Unit tests for benchmark pipeline (1,779 B) |
| Smoke metrics | `artifacts/real_workflow_smoke_20/reports/metrics.json` | 20-project calibration run metrics (9,980 B) |
| Full metrics | `artifacts/real_workflow_full/reports/metrics.json` | 803-project full run metrics (12,071 B) |
| Surfaces report | `artifacts/real_workflow_full/reports/surfaces.jsonl` | Per-surface scan results (1,648,281 B) |
| Archive manifest | `artifacts/real_workflow_full/archive/manifest.jsonl` | 11,719 immutable archive records (8,288,969 B) |
| Smoke log | `artifacts/logs/real_workflow_smoke_20.log` | Smoke run stdout/stderr |
| Full run log | `artifacts/logs/real_workflow_full.log` | Full run stdout/stderr |
| Unit test log | `artifacts/logs/unit_tests.log` | Unit test execution log |
