# Skill-to-Dataset Compiler: Deterministic Provenance-Rich Weak Supervision from Codex Skill Files

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metrics, and logs). The operator who released these artifacts claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We present a deterministic compiler that transforms Codex `SKILL.md` files into a validated, provenance-annotated JSONL dataset intended for skill-routing and skill-card tasks. The compiler recursively discovers skill files, extracts structured fields (title, description, use conditions, exclusion conditions, checklists), and emits four record types: `route_positive`, `skill_card`, `procedure_summary`, and `route_negative`. Every record carries full provenance including source path, SHA-256 hash, and the extracted evidence span. In a full local compilation over 40 source skills, the compiler produced 122 records with zero validation errors, 122 unique identifiers, and complete provenance coverage, completing in 0.06 seconds wall time with 18,528 KB peak RSS. The compiler has no external dependencies beyond the Python 3 standard library. While the compilation path is demonstrated to be practical, fast, and auditable, the semantic quality of the generated labels for model training remains unvalidated. Negative routing examples are sparse (2 of 40 skills yielded parseable exclusions), and the Markdown parser is regex-based, which may limit robustness on heterogeneous skill formats. The formal claim ledger for this artifact contains no audit-approved claims; all statements herein should be read as prototype-level observations rather than validated research claims.

## Introduction

Skill-routing—the task of selecting which skill an agent should invoke given a user request—is a prerequisite for reliable multi-skill agent systems. Training or evaluating routing models requires labeled datasets mapping requests to skills, ideally with both positive and negative examples and with metadata describing each skill's scope and procedures.

Manual annotation of such datasets is expensive and difficult to keep in sync with evolving skill definitions. An alternative is to derive weak supervision labels directly from the skill specification files themselves, which already contain structured information about when a skill should and should not be used, what steps it follows, and how it is described.

This work investigates whether a local, dependency-free compiler can turn Codex `SKILL.md` files into a concrete dataset with provenance, validation, and useful weak labels without requiring private services or manual annotation. We do not claim that the resulting labels are sufficient for high-quality model training without further curation; rather, we demonstrate that the source-to-JSONL compilation path is practical, auditable, and deterministic, providing a foundation on which curation and evaluation can be built.

The research question, as recorded in the run notes, is: *Can a local compiler turn Codex `SKILL.md` files into a concrete dataset with provenance, validation, and useful weak labels without private services or manual annotation?* The prototype evidence supports a qualified affirmative for the compilation path, while leaving the training-value question open.

## Method

### Compiler Design

The compiler is implemented as a single Python script (`scripts/skill_to_dataset.py`) with no dependencies beyond the Python 3 standard library. It performs the following steps:

1. **Recursive discovery.** Given one or more root directories, the compiler recursively finds all files named `SKILL.md`.

2. **Field extraction.** For each skill file, the compiler extracts:
   - Title (from the first heading)
   - First descriptive paragraph
   - `Use when` conditions
   - `Do not use when` conditions (exclusion criteria)
   - Bullets and checklists

3. **Record emission.** The compiler emits JSONL records of four types:
   - `route_positive` — maps a user request or evidence span to the skill to use, derived from the `Use when` section and descriptive text.
   - `skill_card` — a normalized metadata card for the skill (title, description, conditions).
   - `procedure_summary` — checklist or step sequences derived from bullet evidence in the skill file.
   - `route_negative` — negative routing examples derived from explicit `Do not use when` sections, when present.

4. **Provenance attachment.** Every record includes: `skill_id`, the source file path, a SHA-256 hash of the source file, and the specific evidence span from which the record was derived.

5. **Validation.** Before declaring success, the compiler validates that:
   - All instructions are non-empty.
   - All record IDs are unique.
   - All records carry provenance fields.

### Parsing Approach

The current parser uses regular expressions over raw Markdown text. This approach is simple and sufficient for the locally available skill files, which follow a relatively consistent format. A Markdown AST parser could be substituted if precision on more heterogeneous formats becomes necessary. The regex-based approach is an acknowledged limitation rather than a design choice we defend as sufficient.

### Experimental Procedure

Two compilation runs were performed on a single local machine:

- **Smoke test:** Compilation limited to 3 source skills under a single root (`$HOME/.codex/skills`), with metrics output.
- **Full local compile:** Compilation over all discoverable skills under two root directories (`$HOME/.codex/skills` and `$HOME/.codex/plugins/cache`), with metrics output.

Both runs were executed with `/usr/bin/time -v` for wall time and peak RSS measurement. A separate JSONL sanity counter verified record counts, ID uniqueness, and provenance coverage. Memory telemetry was collected from `/proc/meminfo`.

Unit tests were executed via `python3 -m unittest -v tests/test_skill_to_dataset.py`.

These are local prototype compilation runs, not production benchmarks or CUDA calibrations. The results characterize the compiler's behavior on a specific local corpus, not its performance at scale or on arbitrary skill formats.

## Results

### Smoke Test (3 source skills)

| Metric | Value |
|---|---|
| Source skills | 3 |
| Records produced | 10 |
| Validation errors | 0 |
| Max RSS | 18,380 KB |
| Wall time | 0.02 s |

### Full Local Compile (40 source skills)

| Metric | Value |
|---|---|
| Source skills | 40 |
| Records produced | 122 |
| Validation errors | 0 |
| Unique IDs | 122 / 122 |
| All records have provenance | true |
| Max RSS | 18,528 KB |
| Wall time | 0.06 s |

**Records by type:**

| Record type | Count |
|---|---|
| `route_positive` | 40 |
| `skill_card` | 40 |
| `procedure_summary` | 40 |
| `route_negative` | 2 |

The distribution reflects the structure of the source skills: every skill yields one record of each of the first three types, but only 2 of 40 skills contain explicit, parseable `Do not use when` sections, limiting negative examples to just 2 records (1.6% of the total). This imbalance is a property of the source corpus, not a compiler defect, but it materially constrains the dataset's utility for training a router that must learn when *not* to select a skill.

### Resource Usage

The compiler's memory footprint is modest (peak RSS ~18.5 MB) and wall time is sub-second for 40 skills. The host system reported 127,535,908 KB total memory, 122,625,060 KB available, with no swap configured. Memory pressure was negligible for this workload. These figures characterize a local prototype compilation on a well-provisioned machine; they do not constitute a production-scale benchmark.

### Validation

All unit tests passed. Both the smoke test and full compile completed with zero validation errors. The sanity counter confirmed that all 122 records have unique IDs and complete provenance. Structural validity of the output is established; semantic validity is not.

### Claim Ledger Status

The formal claim ledger for this paper (`claim_ledger.json`) contains zero audit-approved claims and carries the audit status `blocked_empty_claims`. The ledger's own limitations note states: *"This artifact must not pass strict claim/evidence audit until claims reference public evidence files."* Readers should interpret all quantitative results above as prototype observations recorded in run logs, not as claims that have passed formal audit.

## Limitations

1. **Semantic label quality is unvalidated.** The compiler produces structurally valid, provenance-rich records, but whether these records constitute high-quality training data for a routing model has not been assessed by human review or by an LLM-based judge against held-out requests. The project decision records confidence as "high for compilation path, medium for training value." This distinction is important: we can state with confidence that the compiler runs correctly on the tested corpus; we cannot state that its outputs are fit for model training.

2. **Negative examples are sparse.** Only 2 of 40 local skills contain explicit `Do not use when` sections in a parseable form. The compiled dataset is heavily skewed toward positive routing examples (40:2 ratio), which limits its direct utility for training a router that must also learn when *not* to select a skill.

3. **Procedure summaries may require filtering.** Bullet-derived `procedure_summary` records are useful for documentation and evaluation, but their suitability for training depends on whether the extracted steps are semantically coherent and complete. Some bullet lists may be formatting artifacts rather than genuine procedural steps.

4. **Regex-based parsing limits robustness.** The Markdown parser uses regular expressions rather than an AST, which may fail or produce incorrect extractions on skill files with non-standard formatting, nested structures, or unusual heading hierarchies. Hardening would require a Markdown AST parser if precision on heterogeneous formats becomes important.

5. **No request paraphrase diversity.** Each `route_positive` record is derived directly from the skill's own descriptive text. A training dataset would benefit from paraphrased or diversified request formulations mapping to the same skill, which the current compiler does not generate.

6. **Scale is limited to local artifacts.** The 40-skill, 122-record dataset is a prototype-scale result. Performance and correctness at orders-of-magnitude larger scale have not been tested.

7. **No held-out evaluation.** The compiled records have not been evaluated against held-out requests or compared to any baseline, so no claim about downstream task performance can be made.

8. **Single-corpus result.** All skills were drawn from a single local installation. Reproduction on a different skill corpus has not been performed.

## Reproducibility Checklist

- [x] Compiler source code is available at `scripts/skill_to_dataset.py`.
- [x] Unit test source is available at `tests/test_skill_to_dataset.py`.
- [x] Full command lines for smoke test and full compile are recorded in run notes.
- [x] Resource measurement used `/usr/bin/time -v` for wall time and max RSS.
- [x] Output datasets are saved: `results/smoke.jsonl`, `results/local_skills_dataset.jsonl`.
- [x] Metrics files are saved: `results/smoke_metrics.json`, `results/local_skills_metrics.json`.
- [x] All log files are preserved (unit test, smoke run, full run, sanity check, memory telemetry, sample records).
- [x] No external dependencies beyond Python 3 standard library.
- [x] Provenance fields (source path, SHA-256, evidence span) are attached to every record.
- [ ] Human review of semantic label quality has **not** been performed.
- [ ] Held-out evaluation of compiled records for model training has **not** been performed.
- [ ] Reproduction on a different skill corpus has **not** been performed.
- [ ] Formal claim audit has **not** been passed (claim ledger is empty; audit status: `blocked_empty_claims`).

## Conclusion

We have demonstrated a deterministic, dependency-free compiler that transforms Codex `SKILL.md` files into a validated, provenance-annotated JSONL dataset. On a local corpus of 40 skills, the compiler produced 122 records with zero validation errors, complete provenance coverage, and sub-second wall time at modest memory cost. The compilation path—discovery, extraction, record emission, provenance attachment, and validation—is practical, fast, and auditable.

However, the compiler addresses only the mechanical step of turning structured skill files into labeled records. It does not address whether those records are semantically sufficient for model training. Negative routing examples are sparse due to the structure of the source skills (2 of 40), procedure summaries may require filtering, and the regex-based parser may need hardening for more heterogeneous formats. The formal claim ledger remains empty, reflecting the fact that these results have not yet been distilled into audit-approved claims referencing public evidence.

The results support proceeding with curation and evaluation—particularly human or LLM-judge review of semantic quality, request paraphrase generation for diversity, and Markdown AST parsing for robustness—but do not warrant claims about training utility without such steps. The project decision of "viable prototype / proceed with curation caveat" accurately captures the current state: the compilation path works; the training-value question remains open.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Compiler | `scripts/skill_to_dataset.py` |
| Unit tests | `tests/test_skill_to_dataset.py` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260430T160618346714+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T160618346714+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T160618346714+0000/paper_manifest.json` |
| Smoke dataset | `results/smoke.jsonl` |
| Smoke metrics | `results/smoke_metrics.json` |
| Full dataset | `results/local_skills_dataset.jsonl` |
| Full metrics | `results/local_skills_metrics.json` |
| Unit test log | `logs/unit-test.log` |
| Smoke run log | `logs/smoke-run.log` |
| Full run log | `logs/full-run.log` |
| Dataset sanity log | `logs/dataset-sanity.log` |
| Memory telemetry log | `logs/memory-telemetry.log` |
| Sample records log | `logs/sample-records.log` |
