# Thermal Policy Optimization via User-Space Concurrency Control on an ARM-Based GPU System

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, and benchmark logs). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

We investigate whether a lightweight, user-space thermal policy can optimize local workload throughput on an NVIDIA GB10-class ARM system while respecting a thermal cap, using only local telemetry and without modifying fan curves, power limits, cpufreq governors, or GPU clocks. A dependency-free Python harness controls CPU-bound SHA-256 workload concurrency and compares a naive AIMD (Additive-Increase Multiplicative-Decrease) thermal controller against fixed-concurrency baselines. On a 20-core Cortex-X925/Cortex-A725 system with an 80 °C thermal cap, the naive AIMD controller was safe (0% samples over cap, maximum 71.7 °C) but conservative, achieving 19.35M ops/s at an average of 4 active workers. Fixed concurrency at 6 workers yielded 29.94M ops/s at a maximum of 73.3 °C with 0% cap violations—a 54.8% throughput improvement over AIMD while remaining within the thermal envelope. However, fixed concurrency at 7 and 8 workers violated the cap in 92% of samples, revealing a narrow and nonlinear thermal boundary between 6 and 7 workers. These results are bounded by short (25 s) validation windows and a synthetic CPU-bound workload; long-run steady-state behavior and applicability to inference or mixed CPU/GPU workloads remain unvalidated.

## Introduction

Thermal management in high-performance computing systems is conventionally handled at the firmware or kernel level through fan curves, dynamic voltage and frequency scaling (DVFS), and power capping. In some deployment contexts—particularly edge and workstation environments—users may lack privileged access to these mechanisms while still needing to maximize throughput within safe thermal limits.

This work examines whether a lightweight thermal policy can optimize local GB10-class workload throughput while respecting a thermal cap, using only local telemetry and no privileged thermal or fan controls. The motivating observation is that user-space process concurrency is a readily controllable variable that directly influences thermal output. If the relationship between concurrency and temperature is sufficiently predictable, a policy that selects the appropriate concurrency level could deliver near-optimal throughput without system-level modifications.

We report results from a single-machine experiment on an NVIDIA GB10-based ARM system. The findings are positive but bounded: a calibrated fixed-concurrency policy substantially outperforms a naive adaptive controller, but the thermal boundary is narrow and sharply nonlinear, and the result is specific to the tested workload, duration, and hardware instance.

## Method

### Platform

Experiments were conducted on a single host (`gx10-efe8`, Linux aarch64) with the following characteristics:

- **GPU:** NVIDIA GB10, idle temperature approximately 39 °C at probe time.
- **CPU:** 20 ARM cores across Cortex-X925 and Cortex-A725 clusters, performance governor.
- **Memory:** ~116 GiB available (MemAvailable), swap disabled (SwapTotal: 0 kB).
- **Thermal zones:** Readable via `/sys/class/thermal`; ACPI critical trip point at 104.8 °C.

The experiment thermal cap was set to 80 °C, with a safety stop at 98 °C, providing an 18 °C margin below the hardware critical trip point. No fan curves, power limits, cpufreq governors, or GPU clocks were modified at any point.

### Harness

We implemented `thermal_policy_experiment.py`, a dependency-free Python harness that:

1. **Samples telemetry** at approximately 1 Hz: ACPI and hwmon thermal zones, `/proc/meminfo` (MemAvailable, SwapTotal), `/proc/stat` (CPU utilization), and optional `nvidia-smi` GPU telemetry (temperature, power draw, utilization, clocks, memory).
2. **Runs a CPU-bound SHA-256 multiprocessing workload** using Python's `hashlib` and `multiprocessing` modules.
3. **Treats active worker count as the policy control variable**, with no modification to any system-level thermal mechanism.
4. **Supports two policy modes**: fixed concurrency (a constant number of workers) and a naive AIMD thermal controller that additively increases workers when temperature is below cap and multiplicatively decreases when temperature approaches or exceeds cap.
5. **Writes per-second telemetry CSVs and JSON summaries** for post-hoc analysis.

### Experimental Protocol

The experiment proceeded in four phases:

**Smoke test (8 s, cap 48 °C, max 20 workers).** Verified harness correctness and telemetry collection at a low thermal cap before longer runs.

**Calibration (10 s, cap 70 °C, max 20 workers).** Ran fixed-concurrency sweeps at 1, 2, 5, 10, and 20 workers to characterize the thermal response curve. Calibration revealed nonlinear behavior: fixed_5 remained below 66 °C, while fixed_10 reached 86.6 °C and fixed_20 reached 92.6 °C within approximately 11 seconds.

**Main experiment (25 s, cap 80 °C, max 20 workers).** Compared fixed_20 (unconstrained) against the AIMD thermal controller.

**Validation (25 s, cap 80 °C, max 20 workers).** Tested fixed concurrency levels of 5, 6, 7, and 8 workers to identify the safe throughput boundary.

### Metrics

- **Throughput:** SHA-256 operations per second (ops/s), aggregated over the 25 s trial.
- **Maximum observed temperature:** Peak temperature across all thermal zone samples during the trial.
- **Cap violation rate:** Percentage of per-second samples where any thermal zone reading equaled or exceeded 80 °C.
- **Average active workers:** Mean number of workers during the trial (equals the fixed concurrency for fixed policies; varies for AIMD).

## Results

### Main Comparison

Table 1 summarizes the main experiment results comparing unconstrained concurrency (fixed_20) against the naive AIMD thermal controller.

**Table 1.** Main experiment: unconstrained vs. AIMD thermal policy (25 s, cap 80 °C).

| Policy | Ops/s | Max temp (°C) | Samples ≥ 80 °C | Avg workers |
|---|---:|---:|---:|---:|
| fixed_20 | 71,142,631 | 94.8 | 91.7% | 20.0 |
| aimd_thermal | 19,345,208 | 71.7 | 0.0% | 4.0 |

Unconstrained execution at 20 workers delivered the highest raw throughput (71.14M ops/s) but violated the 80 °C cap in 91.7% of samples, reaching a maximum of 94.8 °C—only 10 °C below the critical trip point. The AIMD controller was safe (0% violations, max 71.7 °C) but settled at an average of only 4 active workers, yielding 19.35M ops/s. The AIMD controller's conservatism stems from its cold-start behavior: it begins at low concurrency and increases additively, but any thermal approach triggers multiplicative decrease, preventing it from reaching the empirically safe concurrency band identified during calibration.

### Validation: Fixed Concurrency Boundary

Table 2 presents the validation sweep across fixed concurrency levels.

**Table 2.** Validation sweep: fixed concurrency levels 5–8 (25 s, cap 80 °C).

| Policy | Ops/s | Max temp (°C) | Samples ≥ 80 °C | Avg workers |
|---|---:|---:|---:|---:|
| fixed_5 | 24,819,894 | 74.7 | 0.0% | 5.0 |
| fixed_6 | 29,943,395 | 73.3 | 0.0% | 6.0 |
| fixed_7 | 34,883,789 | 91.7 | 92.0% | 7.0 |
| fixed_8 | 39,661,430 | 92.3 | 92.0% | 8.0 |

The thermal boundary is sharply nonlinear. Fixed_6 was the highest safe concurrency: 29.94M ops/s, 73.3 °C maximum, and 0% cap violations. Adding a single worker (fixed_7) caused the maximum temperature to jump from 73.3 °C to 91.7 °C, with 92% of samples exceeding the 80 °C cap. Fixed_8 exhibited nearly identical violation rates and peak temperatures.

This discontinuity suggests that 7 workers engages a second CPU cluster or thermal domain with substantially different dissipation characteristics, consistent with the heterogeneous Cortex-X925 / Cortex-A725 topology. However, this interpretation is inferred from the thermal data and core topology; no per-cluster instrumentation was performed to confirm it directly.

### Throughput Comparison Under Cap

Among policies that respected the 80 °C cap, fixed_6 delivered 54.8% higher throughput than the naive AIMD controller (29.94M vs. 19.35M ops/s). Fixed_5 was also safe but delivered 17.0% less throughput than fixed_6 (24.82M vs. 29.94M ops/s). The AIMD controller's average of 4 active workers indicates it never reached even the fixed_5 throughput level, suggesting its additive-increase step size or multiplicative-decrease aggressiveness are poorly tuned for this thermal regime.

### Calibration Observations

The 10 s calibration phase revealed the nonlinear thermal response that motivated the validation sweep. At fixed_5, the system remained below 66 °C throughout calibration. At fixed_10, temperature reached 86.6 °C within approximately 11 seconds. At fixed_20, temperature reached 92.6 °C in the same interval. The jump from sub-66 °C at 5 workers to 86.6 °C at 10 workers foreshadowed the sharp boundary observed in the validation phase between 6 and 7 workers.

### Negative and Mixed Results

Several findings qualify the positive result:

- **AIMD underperformance.** The naive AIMD controller, despite being safe, achieved only 27.2% of the throughput of the best safe fixed policy. Its reactive nature and cold-start conservatism make it unsuitable as-is for this thermal regime.
- **Narrow safe operating band.** Only two fixed-concurrency levels (5 and 6) were safe under the 80 °C cap. The transition from safe to unsafe occurs over a single worker increment.
- **Unconstrained throughput remains higher.** Fixed_20 delivered 2.37× the throughput of fixed_6. The thermal cap imposes a substantial throughput cost relative to unconstrained operation.
- **Anomalous temperature ordering.** Fixed_6 (73.3 °C max) reported a lower peak temperature than fixed_5 (74.7 °C max), which is unexpected under a monotonic thermal model. This may reflect measurement variance, thermal transient timing, or scheduling differences across the heterogeneous core clusters. The difference is small (1.4 °C) and does not alter the safety classification of either policy, but it underscores that per-second sampling at 1 Hz may miss transient peaks.

## Limitations

1. **Synthetic workload.** The workload is CPU-bound SHA-256 hashing, not an LLM inference server or mixed CPU/GPU pipeline. Thermal dynamics and throughput trade-offs may differ substantially for GPU-bound or mixed workloads. The GPU remained near idle throughout all trials; GPU thermal interaction under load is uncharacterized.

2. **Short validation windows.** All trials lasted 25 seconds. This duration was sufficient to observe thermal steady-state for the tested workload on this hardware, but it does not establish long-run behavior, thermal cycling effects, or response to ambient temperature variation.

3. **Single machine.** Results are from one GB10 host. Component variation, cooling configuration, and ambient conditions may shift the safe concurrency boundary. The sharpness of the observed boundary (0% vs. 92% violation between 6 and 7 workers) makes this a particular concern: even small hardware or environmental differences could move the boundary.

4. **Limited control surface.** The optimizer controls only user-space worker concurrency. It does not manipulate fan curves, power limits, cpufreq governors, or GPU clocks, all of which are standard thermal management mechanisms. The results demonstrate what is achievable within these constraints, not the full potential of thermal policy optimization.

5. **Unretrieved project context.** The provided Notion URL returned HTTP 404 from the research environment. No private project-specific success criteria beyond the prompt metadata were available.

6. **Nonlinear boundary fragility.** The sharp transition between safe (fixed_6) and unsafe (fixed_7) concurrency means that small perturbations—ambient temperature changes, background processes, or workload phase shifts—could push a fixed_6 configuration into cap violation. A production policy would need continuous monitoring and adaptive backoff.

7. **No per-cluster instrumentation.** The hypothesized explanation for the nonlinear boundary—engagement of a second CPU cluster at 7 workers—is consistent with the heterogeneous core topology but was not directly confirmed through per-cluster frequency, utilization, or thermal monitoring.

8. **AIMD tuning not explored.** The naive AIMD controller used a single parameterization. Different additive-increase step sizes, multiplicative-decrease factors, or temperature thresholds might yield better performance. The comparison here is between one specific AIMD configuration and fixed policies, not between adaptive and fixed approaches in general.

9. **Sampling rate.** Telemetry was sampled at approximately 1 Hz. Sub-second thermal transients—particularly during the ramp-up phase when workers are spawned—may not be captured. The reported maximum temperatures and cap violation rates should be interpreted as lower bounds on the true values.

## Reproducibility Checklist

- **Hardware specified:** Yes — NVIDIA GB10, 20 ARM cores (Cortex-X925 + Cortex-A725), ~116 GiB RAM, Linux aarch64, host `gx10-efe8`.
- **Software specified:** Yes — dependency-free Python 3 harness; no external packages beyond standard library (`hashlib`, `multiprocessing`, `json`, `csv`, `pathlib`, `dataclasses`).
- **Thermal environment documented:** Yes — ACPI critical trip 104.8 °C; experiment cap 80 °C; safety stop 98 °C; performance governor; swap disabled.
- **Random seeds:** Not applicable — SHA-256 workload is deterministic; AIMD policy is reactive to telemetry (no stochastic elements).
- **Complete command log:** Yes — all commands recorded in run notes, including inline Python invocations.
- **Raw data available:** Yes — per-second telemetry CSVs and JSON summaries for all phases (smoke, calibration, experiment, validation).
- **Analysis code available:** Yes — `thermal_policy_experiment.py` (harness) and `summarize_research.py` (analysis).
- **Negative results reported:** Yes — AIMD underperformance and fixed_7/fixed_8 cap violations are reported.
- **Duration and sample counts stated:** Yes — 25 s trials, approximately 25 samples per trial at 1 Hz sampling.
- **Result classification:** These are local benchmark results on real hardware (GB10 ARM workstation), not toy simulations, not CUDA copy calibrations, and not production validation. They represent a single-machine, short-duration prototype evaluation.

## Conclusion

A user-space thermal policy optimizer that controls worker concurrency is viable on the tested GB10-class ARM system, but the result is bounded. The naive AIMD controller was safe but excessively conservative, failing to exploit the calibrated safe concurrency band. A calibrated fixed-concurrency policy at 6 workers delivered 54.8% higher throughput than AIMD while maintaining 0% cap violations and a 6.7 °C margin below the 80 °C cap.

However, the thermal boundary is sharply nonlinear: a single additional worker (7 vs. 6) caused cap violation rates to jump from 0% to 92%, with peak temperatures exceeding 91 °C. This discontinuity, likely related to the heterogeneous core topology, means that fixed policies are fragile and that any production controller must incorporate continuous monitoring with adaptive backoff.

The primary open questions are whether these findings generalize to longer durations, different ambient conditions, GPU-bound inference workloads, and other hardware configurations. The recommended next step is to implement a calibrated guarded controller that initializes at the highest safe calibrated concurrency and probes upward only when thermal headroom and low positive temperature slope permit, validated over longer runs with real inference throughput (tokens/s) as the objective metric.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Experiment harness | `thermal_policy_experiment.py` |
| Summary script | `summarize_research.py` |
| Research summary (JSON) | `artifacts/research_summary.json` |
| Policy results (CSV) | `artifacts/policy_results.csv` |
| Experiment summary | `artifacts/experiment_summary.json` |
| Hardware probe log | `logs/hardware_probe.log` |
| Thermal trip points log | `logs/thermal_trip_points.log` |
| Smoke run log | `logs/smoke_stdout.json` |
| Calibration run log | `logs/calibration_stdout.json` |
| Experiment run log | `logs/experiment_stdout.json` |
| Validation logs (fixed 5–8) | `logs/fixed5_validation_stdout.json` through `logs/fixed8_validation_stdout.json` |
| Summary run log | `logs/summary_stdout.json` |
| Telemetry CSVs (smoke) | `logs/smoke_fixed1.csv` |
| Telemetry CSVs (calibration) | `logs/calibrate_fixed1.csv`, `logs/calibrate_fixed2.csv`, `logs/calibrate_fixed5.csv`, `logs/calibrate_fixed10.csv`, `logs/calibrate_fixed20.csv` |
| Telemetry CSVs (experiment) | `logs/experiment_fixed20.csv`, `logs/experiment_aimd_thermal.csv` |
| Telemetry CSVs (validation) | `logs/validation_fixed5.csv`, `logs/validation_fixed6.csv`, `logs/validation_fixed7.csv`, `logs/validation_fixed8.csv` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T190748654504+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T190748654504+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T190748654504+0000/paper_manifest.json` |
