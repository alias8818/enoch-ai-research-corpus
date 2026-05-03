# Audio Room Measurement Planner: A Lightweight Dependency-Free CLI for Small-Room Acoustic Measurement Planning

> **AI Provenance Notice:** This draft was generated entirely by an automated AI research system from project artifacts (run notes, decision JSON, test logs, and generated outputs). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is asserted.

---

## Abstract

We present a lightweight, dependency-free command-line tool for generating structured acoustic measurement plans for small listening rooms. Given room dimensions, a listener position, and a target reverberation time (RT60), the planner computes room volume, the first five axial room modes per dimension, an estimated Schroeder frequency, and a nine-point measurement grid covering the listening area. It also produces a Room EQ Wizard (REW)-oriented measurement checklist. The tool is implemented as a single Python script with zero external dependencies beyond the standard library. Smoke testing with three regression tests confirms correct output generation for a single representative input after a serializer correction. No performance benchmarking, hardware validation, or physical measurement verification was performed. The planner is strictly a pre-measurement organizational aid; it does not replace calibrated physical measurements, room treatment design, or ISO 3382-2 compliant reverberation-time reporting.

## Introduction

Acoustic measurement of small listening rooms is a prerequisite for informed equalization, treatment, and speaker placement decisions. Practitioners commonly use tools such as Room EQ Wizard (REW) to capture impulse responses and frequency responses at multiple positions, then interpret the results manually. However, the planning phase—deciding where to measure, what to check before measuring, and what modal behavior to expect—remains largely ad hoc.

Standards such as ISO 3382-2 define rigorous procedures for reverberation-time measurement in ordinary rooms, but they impose apparatus and procedural requirements that informal optimization workflows do not always need to satisfy. A gap exists between the rigor of standardized measurement and the informal planning that precedes a typical home-studio or listening-room measurement session.

This work addresses that gap with a minimal computational tool that:

1. Computes axial room modes from rectangular room dimensions.
2. Estimates the Schroeder frequency boundary between modal and statistical behavior.
3. Generates a reproducible nine-point measurement grid over the listening area.
4. Produces a REW-oriented pre-measurement checklist.

The tool makes no claim to replace physical measurement, calibrated microphone data, or ISO-compliant reporting. It is a planning scaffold only.

## Method

### Input Parameters

The planner accepts the following command-line arguments:

| Parameter | Flag | Description |
|---|---|---|
| Width | `--width` | Room width in meters |
| Length | `--length` | Room length in meters |
| Height | `--height` | Room height in meters |
| Listener position | `--lp` | Three coordinates (x, y, z) in meters |
| Target RT60 | `--rt60` | Desired reverberation time in seconds |
| Output format | `--format` | `markdown` or `json` |
| Output path | `--output` | File path for generated plan |

### Computed Quantities

**Room volume.** Computed as $V = w \times l \times h$.

**Axial room modes.** For a rectangular room, the axial mode frequencies along each dimension are:

$$f_n = \frac{n \cdot c}{2L}$$

where $n$ is the mode index, $c$ is the speed of sound (taken as 343 m/s), and $L$ is the relevant dimension. The planner reports the first five axial modes per dimension. Only axial modes are computed; tangential and oblique modes are excluded.

**Schroeder frequency.** Estimated as:

$$f_s = 2000 \sqrt{\frac{RT60}{V}}$$

This marks the approximate boundary below which individual modes dominate and above which statistical overlap begins. The formula is an approximation; actual modal density crossover depends on damping distribution and boundary conditions not captured by this model.

**Measurement grid.** A nine-point grid is generated over the listening area. The grid covers the listener position and surrounding positions at small offsets, providing spatial sampling for averaging or identifying position-dependent variation.

### Output

The planner produces either Markdown or JSON output containing:

- Room dimensions and computed volume
- Axial mode frequencies (first five per dimension)
- Schroeder frequency estimate
- Nine measurement point coordinates
- Assumptions and warnings
- A REW-oriented checklist (microphone calibration, pre-loop check, gain staging, etc.)

### Implementation

The tool is implemented as a single Python script (`audio_room_measurement_planner.py`) with no external dependencies beyond the Python standard library. It uses only `argparse`, `json`, `math`, and `sys`.

### Testing

Three regression/smoke tests were implemented:

1. Verification that the CLI produces valid JSON output for representative inputs.
2. Verification that the CLI produces valid Markdown output for representative inputs.
3. Verification that computed room volume is included in serialized output.

No edge-case tests, fuzz testing, or property-based testing were performed.

## Results

### Test Outcomes

The initial test run produced one failure: the JSON serializer omitted the computed room volume field. After correcting the serializer to include `room.volume_m3`, all three tests passed.

| Run | Result | Log |
|---|---|---|
| Initial pytest | 1 failure (volume omitted from JSON) | `artifacts/logs/pytest_initial.log` |
| Post-fix pytest | 3 passed in 0.03s | `artifacts/logs/pytest_after_serializer_fix.log` |

The serializer bug and its correction are documented transparently. The initial failure indicates that the volume computation was performed correctly but the serialization path was incomplete—an integration error rather than an algorithmic defect.

### Example Output

For a room of dimensions 3.6 m × 4.8 m × 2.4 m with listener position (1.8, 2.9, 1.15) and target RT60 of 0.4 s, the planner generated:

- **Room volume:** 41.47 m³
- **First five axial modes** for each dimension (width, length, height)
- **Schroeder frequency estimate**
- **Nine measurement points** distributed around the listening position
- **REW checklist** including microphone calibration, gain staging, and pre-loop verification

The full Markdown output is preserved in `artifacts/example_plan.md` and the JSON equivalent in `artifacts/example_plan.json`. Only one input configuration was exercised in smoke testing.

### Performance

Planner runtime for the smoke command was below shell timing resolution in the execution environment. No long-run, stress-test, or multi-configuration benchmarking was performed. Given the trivial computational cost (arithmetic on a handful of scalars), performance is not expected to be a concern for any realistic input, but this expectation is not empirically validated.

## Limitations

This work has several significant limitations:

1. **No physical validation.** The planner generates a measurement plan; it does not perform or validate physical measurements. All acoustic conclusions (modal behavior, treatment needs, equalization targets) require actual measurements with calibrated hardware.

2. **No ISO 3382-2 compliance.** The planner flags the ISO 3382-2 boundary but does not implement or certify compliance with the standard. ISO-compliant reverberation-time reporting requires specific apparatus, source positions, and averaging procedures not addressed here.

3. **Rectangular room assumption.** Axial mode calculations assume a shoebox-shaped room. Non-rectangular geometries, angled walls, or large openings are not handled.

4. **Axial modes only.** Tangential and oblique modes are not computed. In rooms with similar dimensions along multiple axes, these modes can be significant.

5. **No treatment or EQ advice.** The planner does not recommend acoustic treatment, parametric EQ settings, or speaker/subwoofer placement. Such recommendations require measurement data and use-case-specific judgment.

6. **No REW API integration.** While the REW API documentation was consulted to confirm automation feasibility, no live integration was implemented or tested. REW API integration requires a running REW instance with audio hardware, which is not verifiable in a headless environment.

7. **Limited test coverage.** Only three smoke tests were executed on a single input configuration. Edge cases (extreme dimensions, zero or negative inputs, very large rooms, degenerate listener positions) are not covered by automated tests.

8. **No benchmarking.** Runtime was below measurement resolution. No claim is made about performance under unusual conditions.

9. **Schroeder frequency is an estimate.** The formula used is an approximation. Actual modal density crossover depends on damping distribution and boundary conditions not captured by the model.

10. **Single example only.** Only one room configuration was exercised end-to-end. Correctness for arbitrary inputs is not established beyond the three unit tests.

11. **Empty claim ledger.** The project's claim ledger contains no formally registered claims. The decision JSON records a "proceed" / "viable_with_limits" status, but no structured claim-evidence pairs were audited through the claim ledger mechanism.

## Reproducibility Checklist

| Item | Status |
|---|---|
| Source code available | Yes: `scripts/audio_room_measurement_planner.py` |
| Test suite available | Yes: `tests/test_audio_room_measurement_planner.py` |
| Dependencies | None (Python standard library only) |
| Example outputs preserved | Yes: `artifacts/example_plan.md`, `artifacts/example_plan.json` |
| Test logs preserved | Yes: `artifacts/logs/pytest_initial.log`, `artifacts/logs/pytest_after_serializer_fix.log`, `artifacts/logs/pytest_final.log` |
| Exact commands documented | Yes: see run notes |
| Random seeds | Not applicable (no randomness in computation) |
| Hardware environment logged | Yes: `artifacts/logs/environment.log` |
| External data sources documented | Yes: three URLs in decision JSON |
| Version control | Project directory: `<control-plane-projects>/source-record-redacted` |
| Claim ledger | Present but empty (no formal claims registered) |
| Readiness audit | Missing (flagged in review metadata) |

## Conclusion

A lightweight, dependency-free CLI tool for small-room acoustic measurement planning has been implemented and smoke-tested. It computes axial room modes, Schroeder frequency estimates, and a nine-point measurement grid, and produces a REW-oriented checklist. All three automated tests pass after a serializer correction.

The tool is viable as a pre-measurement organizational aid for informal room optimization. It is not viable as a substitute for calibrated physical measurements, room treatment design, or ISO 3382-2 compliant reporting. The boundary between informal planning and certified measurement is clearly flagged in the tool's output.

The evidence base is narrow: three smoke tests on a single input configuration, one example output, and no physical validation. The claim ledger is empty, and the readiness audit signal is missing from the review metadata. The results should be interpreted accordingly.

Recommended next steps include: (a) adding a REW measurement naming and export template to map generated points to captured data, (b) adding optional ingestion of REW-exported CSV/JSON data for post-measurement analysis, (c) adding a standards-aware report mode that distinguishes informal optimization from ISO 3382-2 reverberation-time reporting, and (d) expanding test coverage to edge cases and multiple room configurations.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Planner script | `scripts/audio_room_measurement_planner.py` |
| Test suite | `tests/test_audio_room_measurement_planner.py` |
| Example plan (Markdown) | `artifacts/example_plan.md` |
| Example plan (JSON) | `artifacts/example_plan.json` |
| Evidence summary | `artifacts/research/evidence_summary.md` |
| Run notes | `run_notes.md` |
| Initial test log | `artifacts/logs/pytest_initial.log` |
| Post-fix test log | `artifacts/logs/pytest_after_serializer_fix.log` |
| Final test log | `artifacts/logs/pytest_final.log` |
| Planner smoke log | `artifacts/logs/planner_smoke_after_fix.log` |
| Environment log | `artifacts/logs/environment.log` |
| Project decision JSON | `.omx/project_decision.json` |
| Project metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260502T193448495111+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T193448495111+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T193448495111+0000/paper_manifest.json` |
