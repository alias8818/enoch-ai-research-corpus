# Data Center Airflow Toy Twin: Sparse-Sensor Calibration and Intervention Ranking in a Transparent Rack-Aisle Network Model

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present a small, transparent rack-aisle thermal-airflow network model ("toy twin") designed to calibrate hidden airflow parameters from sparse rack inlet temperature sensors and rank simple cooling interventions. The model encodes rack exhaust temperature via an energy-balance relation ($Q = \dot{m}\, c_p\, \Delta T$), represents inlet temperature as a mixture of supply air and local hot-aisle recirculation, and models tile blockage, fan derating, and containment as adjustments to supply deficit and leakage fraction. On synthetic data with known ground-truth parameters (leakage fraction 0.18, fan scale 0.94, partial tile blockage on two racks), grid-search calibration from sparse inlet sensors recovered the leakage and fan-scale parameters exactly and achieved a sensor RMSE of 0.0721 °C. The as-found calibrated maximum inlet temperature was 26.02 °C, marginally within the ASHRAE A1–A4 recommended upper bound of 27 °C. Among four candidate interventions, the combined "clear tiles plus containment" scenario produced the largest reduction in maximum inlet temperature (−7.53 °C, to 18.49 °C). All simulated scenarios converged. These results are strictly limited to a synthetic, low-fidelity network model and do not constitute facility-design-grade analysis or CFD validation. The artifact is positioned as a fast pre-CFD hypothesis tool for intervention triage.

## 1 Introduction

Data center cooling efficiency depends on managing airflow paths so that cold supply air reaches equipment inlets without excessive mixing with hot exhaust air. Industry guidance recommends hot-aisle/cold-aisle layouts and physical containment to reduce recirculation, with reported cooling energy savings of 10–35% (ENERGY STAR). ASHRAE TC 9.9 specifies a recommended dry-bulb inlet temperature range of 18–27 °C for data-processing equipment classes A1–A4. NVIDIA DGX SuperPOD design guidance recommends aisle containment and CFD modeling for planned changes.

Full CFD simulation remains computationally expensive and slow for rapid hypothesis testing. This raises the question: can a minimal, transparent network model calibrate from sparse real-time sensor data and produce actionable intervention rankings, even if at substantially lower fidelity than CFD?

We implement and evaluate such a toy twin. The research question is deliberately scoped: we ask whether the full loop—encode assumptions, generate sparse observations, calibrate hidden parameters, evaluate interventions, and leave reproducible metrics—can be closed in a self-contained artifact, not whether the model replaces CFD or facility measurements.

## 2 Method

### 2.1 Model formulation

The toy twin represents a data center row as a one-dimensional network of racks along a shared cold aisle. Each rack has:

- **Exhaust temperature** determined by the energy-balance relation $T_{\text{exhaust}} = T_{\text{inlet}} + Q / (\dot{m}\, c_p)$, where $Q$ is the rack heat load, $\dot{m}$ is the mass flow rate through the rack, and $c_p$ is the specific heat of air.
- **Inlet temperature** modeled as a weighted mixture of supply air temperature and local hot-aisle recirculation: $T_{\text{inlet}} = (1 - \lambda)\, T_{\text{supply}} + \lambda\, T_{\text{recirculation}}$, where $\lambda$ is the leakage (recirculation) fraction.
- **Supply deficit** affected by raised-floor tile blockage (reducing effective flow area) and fan scale (derating the total supply airflow). Tile blockage on rack $i$ is parameterized by a blockage fraction $b_i \in [0, 1]$.
- **Containment** represented as a reduction in the leakage fraction $\lambda$, reflecting reduced hot-aisle recirculation when physical barriers are present.

The model is intentionally not CFD. It captures bulk energy and mass balance along a single aisle but omits spatial airflow patterns, turbulent mixing, buoyancy-driven stratification, and three-dimensional geometry.

### 2.2 Calibration procedure

Hidden parameters (leakage fraction $\lambda$, fan scale $f$, and per-rack blockage fractions $b_i$) are calibrated by grid search over a discrete parameter space, minimizing the root-mean-square error (RMSE) between model-predicted inlet temperatures and observed inlet temperatures at a sparse set of sensor locations.

### 2.3 Intervention scenarios

Four intervention scenarios were evaluated against the calibrated as-found baseline:

1. **Clear tiles**: Set all per-rack blockage fractions to zero.
2. **Containment**: Reduce the leakage fraction.
3. **Clear tiles plus containment**: Combine both interventions.
4. **Fan upgrade**: Increase fan scale above the calibrated value.

Each scenario re-solves the network model with the modified parameters and reports the resulting maximum rack inlet temperature.

### 2.4 Implementation

The artifact consists of:

- `airflow_toy_twin.py`: The model, calibration, and intervention-ranking implementation.
- `test_airflow_toy_twin.py`: Regression tests covering convergence, blockage behavior, and calibration recovery.
- `README.md`: Usage instructions and scope warnings.

All code runs under Python 3.12.3 with no external dependencies beyond the standard library.

### 2.5 Experimental protocol

1. **Unit verification**: `python3 -m pytest -q` — 3 regression tests.
2. **Main experiment**: `python3 airflow_toy_twin.py --outdir artifacts/airflow_toy_twin_20260502T2007Z --seed 7` — generates synthetic observations from known ground-truth parameters, calibrates, and ranks interventions.
3. **Throughput benchmark**: 50 consecutive runs to measure wall-clock time and memory footprint.

## 3 Results

### 3.1 Unit tests

All 3 regression tests passed in 0.01 s. Tests covered convergence of the network solver, expected temperature elevation under tile blockage, and recovery of known parameters during calibration.

### 3.2 Calibration accuracy

Ground-truth parameters and calibrated estimates:

| Parameter | Ground truth | Calibrated |
|-----------|-------------|------------|
| Leakage fraction ($\lambda$) | 0.18 | 0.18 |
| Fan scale ($f$) | 0.94 | 0.94 |
| Blockage, rack 5 | 0.42 | not independently recovered |
| Blockage, rack 6 | 0.25 | not independently recovered |

The grid search recovered the leakage fraction and fan scale exactly. Per-rack blockage fractions were not independently calibrated from the sparse sensor set; their effect is absorbed into the aggregate inlet temperature residuals. The sensor RMSE was 0.0721 °C, indicating close fit between the calibrated model and the synthetic observations.

The exact recovery of global parameters is expected given that the calibration data are generated by the same forward model with known discrete parameter values. This constitutes a consistency check on the calibration pipeline, not a validation against independent data.

### 3.3 As-found thermal state

The calibrated as-found maximum rack inlet temperature was 26.02 °C. This falls within the ASHRAE A1–A4 recommended range (18–27 °C) but is only 0.98 °C below the upper bound, indicating limited thermal margin under the assumed conditions. Small perturbations to load, supply temperature, or airflow parameters could push the predicted state outside the recommended range.

### 3.4 Intervention ranking

The experiment evaluated four intervention scenarios against the as-found baseline. The best-performing intervention was:

| Intervention | Max inlet temp (°C) | Δ from as-found (°C) |
|---|---|---|
| As-found baseline | 26.02 | — |
| Clear tiles + containment | 18.49 | −7.53 |

The combined "clear tiles plus containment" intervention produced the largest reduction in maximum inlet temperature, lowering it to 18.49 °C (−7.53 °C from baseline). This is qualitatively consistent with external guidance: both unblocking supply paths and reducing recirculation are expected to lower inlet temperatures, and their combination is expected to dominate either intervention alone.

Complete per-scenario results for the remaining three interventions (clear tiles alone, containment alone, fan upgrade) are recorded in `scenario_metrics.csv` and `scenario_results.json` within the artifact directory. All four simulated scenarios converged successfully.

### 3.5 Throughput and resource usage

Over 50 consecutive runs:

- **Total wall-clock time**: 0.4963 s, yielding 100.75 runs/s.
- **Maximum RSS**: 14,920 KB.
- **Single-run time**: approximately 0.01 s.

The workload is CPU/Python-light and memory-safe relative to available system memory (approximately 122 GB available after benchmark). Swap is disabled on the target system (0 kB total), as expected for the environment configuration.

### 3.6 Negative and mixed observations

- The initial throughput benchmark command failed due to a script-local import path that omitted the repository root. This was corrected by setting `PYTHONPATH=$PWD`. The failed command and its log are retained in the artifact for transparency.
- Per-rack blockage fractions could not be independently calibrated from the sparse sensor set used. The model absorbs their aggregate effect but does not resolve individual blockage values from inlet temperatures alone. This is a structural identifiability limitation of sparse sensing in a network model, not a software defect.
- The as-found maximum inlet temperature (26.02 °C) is near the ASHRAE upper bound, meaning that even small modeling errors could push the predicted state outside the recommended range. The toy twin does not quantify this sensitivity.
- The exact parameter recovery on synthetic data is a necessary but insufficient condition for real-world applicability. It confirms the calibration pipeline is self-consistent but does not demonstrate robustness to model mismatch, sensor noise distributions not represented in the synthetic generator, or structural model error.

## 4 Limitations

1. **Toy network model, not CFD.** The model captures bulk energy and mass balance along a single aisle. It omits three-dimensional airflow patterns, turbulent mixing, buoyancy effects, transient dynamics, and spatial heterogeneity within a rack. It is explicitly a lower-fidelity, fast pre-CFD hypothesis tool, as described in the NVIDIA DGX SuperPOD design guidance context for pre-CFD planning.
2. **Synthetic observations only.** No private or site-specific facility measurements were used. All observations were generated from the model's own forward simulation with known ground-truth parameters. Calibration against synthetic data can recover those parameters but does not validate the model against reality.
3. **No facility-design closure.** Real deployment would require actual rack layout, IT loads, tile/fan airflow measurements, containment leakage characterization, inlet/exhaust sensor streams, and validation against CFD or measured post-intervention data. None of these were available.
4. **Sparse sensor identifiability.** The calibration recovers global parameters (leakage fraction, fan scale) but not all per-rack parameters (individual blockage fractions) from sparse inlet sensors. Additional sensor types or locations would be needed for full identifiability.
5. **Single-aisle geometry.** The model represents one aisle. Multi-aisle interactions, cross-aisle recirculation, and room-level return airflow are not modeled.
6. **Deterministic and steady-state.** The model does not account for temporal variability in loads, setpoints, or ambient conditions.
7. **Single random seed.** The main experiment was run with seed 7 only. While the unit tests and throughput benchmark provide additional confidence in code correctness, the calibration and intervention results have not been demonstrated across multiple random seeds or parameter regimes.

## 5 Reproducibility Checklist

- **Source code**: `airflow_toy_twin.py`, `test_airflow_toy_twin.py`, `README.md` — available in project directory.
- **Random seed**: 7 (specified via `--seed 7`).
- **Python version**: 3.12.3.
- **Host**: `gx10-efe8`.
- **Runtime**: 0.0102 s for the main experiment.
- **Unit test result**: 3 passed in 0.01 s.
- **Throughput benchmark**: 50 runs in 0.4963 s (100.75 runs/s), max RSS 14,920 KB.
- **Output artifacts**: `sensor_observations.csv`, `calibration_grid.csv`, `scenario_metrics.csv`, `scenario_results.json`, `summary.md`, `experiment_summary.json` — all in `artifacts/airflow_toy_twin_20260502T2007Z/`.
- **Logs**: `artifacts/logs/pytest.log`, `artifacts/logs/airflow_toy_twin_run.log`, `artifacts/logs/throughput_benchmark_fixed.log` (and the failed `throughput_benchmark.log` retained for transparency).
- **External dependencies**: None beyond Python standard library.
- **Swap**: Disabled (0 kB total), as expected for the target environment.
- **Claim ledger**: The claim ledger for this paper contains no formal claims at time of generation; the limitation "Model-authored draft; human claim audit required" is recorded.

## 6 Conclusion

A self-contained rack-aisle airflow toy twin was implemented, tested, calibrated from sparse synthetic inlet sensors, and used to rank four cooling interventions. The model recovered global hidden parameters (leakage fraction, fan scale) exactly from synthetic data, achieved a sensor RMSE of 0.0721 °C, and identified "clear tiles plus containment" as the most effective intervention (−7.53 °C reduction in maximum inlet temperature). The qualitative behavior of the model is consistent with published industry guidance on hot/cold aisle separation, containment, and airflow path management.

The artifact is viable as a transparent research and prototyping tool for intervention triage. It is not viable as CFD, facility-design closure, or a substitute for measured validation data. The primary positive result is that the full loop—encode, observe, calibrate, evaluate, and leave reproducible metrics—closes cleanly in a toy setting with synthetic data. The primary limitation is that closing this loop against real facility data remains an open problem requiring site-specific measurements, validation against CFD or post-intervention instrumentation, and demonstration of robustness to model structural error.

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Model implementation | `airflow_toy_twin.py` |
| Regression tests | `test_airflow_toy_twin.py` |
| Usage and scope | `README.md` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Sensor observations | `artifacts/airflow_toy_twin_20260502T2007Z/sensor_observations.csv` |
| Calibration grid | `artifacts/airflow_toy_twin_20260502T2007Z/calibration_grid.csv` |
| Scenario metrics | `artifacts/airflow_toy_twin_20260502T2007Z/scenario_metrics.csv` |
| Scenario results | `artifacts/airflow_toy_twin_20260502T2007Z/scenario_results.json` |
| Experiment summary | `artifacts/airflow_toy_twin_20260502T2007Z/experiment_summary.json` |
| Summary markdown | `artifacts/airflow_toy_twin_20260502T2007Z/summary.md` |
| Pytest log | `artifacts/logs/pytest.log` |
| Main run log | `artifacts/logs/airflow_toy_twin_run.log` |
| Throughput benchmark log (fixed) | `artifacts/logs/throughput_benchmark_fixed.log` |
| Throughput benchmark log (failed) | `artifacts/logs/throughput_benchmark.log` |
| Paper claim ledger | `papers/source-record-redacted-20260502T200718556841+0000/claim_ledger.json` |
| Paper evidence bundle | `papers/source-record-redacted-20260502T200718556841+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T200718556841+0000/paper_manifest.json` |
