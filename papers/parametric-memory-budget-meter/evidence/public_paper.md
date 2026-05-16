# Parametric Memory Budget Meter for GB10/UMA Inference Planning

> **AI provenance notice.** This draft was AI-generated from automated research artifacts (run logs, telemetry, CUDA calibration probes, unit tests, and decision records). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We describe a parametric memory-budget meter that estimates whether a transformer inference workload fits within available unified memory on NVIDIA GB10-class UMA hosts. The meter computes total memory demand from model architecture parameters—parameter count, weight precision, layer count, hidden size, attention and KV head counts, sequence length, batch size, and KV precision—plus allocator overhead, OS reserve, and a safety margin. It compares the estimate against `/proc/meminfo` `MemAvailable`, deliberately excluding swap capacity and `nvidia-smi` GPU-memory accounting; on the GB10, `nvidia-smi` reports memory usage as "Not Supported," removing it as a budget source. We validate the telemetry path with CUDA managed-memory allocation probes that touch memory from both CPU and GPU, confirming that `MemAvailable` deltas are consistent with requested allocation sizes at coarse granularity. Unit tests lock the core estimation formulas. On the test host (121.63 GiB total, 0 swap, earlyoom active), the meter classifies a 70B Q4 model at 131K context as fitting (98.55 GiB required, 18.51 GiB remaining) and a 200B Q4 model at 32K context as not fitting (137.20 GiB required, 20.14 GiB deficit). The approach is viable as a conservative preflight planning gate. It does not replace engine-specific profiling, and its overhead defaults require tuning against real inference traces. The structured claim ledger for this artifact remains in a blocked-empty state; the claims below have not passed formal claim/evidence audit.

## Introduction

Unified Memory Architecture (UMA) platforms such as the NVIDIA GB10 expose a single physical memory pool shared between CPU and GPU. This design simplifies memory management for application developers but complicates capacity planning for large transformer inference workloads. The most common tool for GPU-side budget estimation, `nvidia-smi`, reports memory usage as "Not Supported" on the GB10, eliminating a standard capacity-planning signal.

The Linux kernel's `/proc/meminfo` field `MemAvailable` provides an estimate of memory available for user-space allocation without swapping. On a UMA system with zero swap, this field reflects the true shared pool. Combined with the earlyoom daemon's configuration—active with a 4% minimum threshold and 60-second report interval on our host—these OS-level signals offer a potential basis for preflight capacity checks.

We investigate whether a parametric estimator, driven by model architecture parameters and conservative overhead margins, can produce a reliable fit/no-fit decision against `MemAvailable` for transformer inference on UMA hosts. The estimator must account for weights, KV cache, activations, allocator overhead, OS reserve, and a safety margin below the earlyoom kill threshold. We do not attempt to replace engine-specific profiling; rather, we ask whether a conservative parametric gate can catch obvious misfits before a long inference run begins.

## Method

### Memory Budget Estimation

The meter (`src/memory_budget_meter.py`) computes total required memory as the sum of six components:

1. **Weights.** Parameter count × weight precision (bits) / 8.
2. **KV cache.** Per-layer KV cache size, computed as `2 × kv_heads × head_dim × seq_len × kv_bits / 8`, summed across layers and batch size. The value `head_dim` is derived as `hidden_size / attention_heads`.
3. **Activations.** A per-layer activation estimate scaled by batch size and hidden size, summed across layers.
4. **Allocator overhead.** A multiplicative factor (default 1.10×) applied to the sum of weights, KV cache, and activations, accounting for CUDA allocator fragmentation and internal bookkeeping.
5. **OS reserve.** A fixed reservation (default 2.0 GiB) for kernel and system processes, informed by the earlyoom minimum threshold.
6. **Safety margin.** A multiplicative factor (default 1.05×) applied to the total, providing headroom below the earlyoom kill threshold.

The fit decision compares total required memory against `MemAvailable` at invocation time. A secondary output reports the maximum sequence length achievable under the same parameter assumptions, derived by solving the KV cache equation for `seq_len` given remaining capacity.

The default overhead factors (1.10× allocator, 1.05× safety, 2.0 GiB OS reserve) are deliberately conservative. They have not been calibrated against real inference engine traces and may over- or under-estimate actual overhead for specific engines, quantization formats, or execution strategies.

### Telemetry Collection

The telemetry script (`scripts/collect_telemetry.py`) records:

- `/proc/meminfo` fields (MemTotal, MemAvailable, SwapTotal, and others)
- `nvidia-smi` output (confirming "Not Supported" for memory usage on this device)
- earlyoom process status and command-line arguments

### UMA Calibration Probes

The CUDA probe (`scripts/uma_probe.cu`) allocates managed memory of a specified size, touches every page from both CPU and GPU, and records:

- Effective touch throughput (MiB/s)
- `MemAvailable` before and after allocation and touch

Three probe configurations were executed:

| Label | Allocation | Touch count | Result file |
|---|---|---|---|
| Smoke | 256 MiB × 1 | 1 | `results/uma_smoke_256m.json` |
| Calibration A | 512 MiB × 2 | 2 | `results/uma_cal_512m_x2.json` |
| Calibration B | 1024 MiB × 2 | 2 | `results/uma_cal_1024m_x2.json` |

These are CUDA managed-memory prototype probes, not production validation. They test whether UMA allocations touched by both CPU and GPU are visible through `/proc/meminfo` and whether `MemAvailable` deltas are consistent with requested sizes at coarse granularity.

### Unit Tests

The test suite (`scripts/test_memory_budget_meter.py`) exercises the core estimation formulas with known inputs and expected outputs, verifying weight computation, KV cache sizing, overhead application, and fit classification.

## Results

### Environment

| Property | Value |
|---|---|
| Kernel | Linux 6.17.0-1014-nvidia-aarch64 |
| GPU | NVIDIA GB10 |
| `nvidia-smi` memory usage | Not Supported |
| MemTotal | 121.63 GiB |
| MemAvailable (at telemetry) | 116.53 GiB |
| SwapTotal | 0 bytes |
| earlyoom | Active (`-m 4 -r 60`) |

### UMA Calibration

| Probe | Touch throughput (MiB/s) | MemAvailable drop (GiB) | Notes |
|---|---:|---:|---|
| 256 MiB × 1 | 760 | Not reliably measurable | Small sample; `MemAvailable` fluctuated upward due to kernel cache reclaim noise. Liveness check only. |
| 512 MiB × 2 | 2,540 | Consistent with 1 GiB request | Calibration passed. |
| 1024 MiB × 2 | 3,616 | 2.28 | Close to the 2 GiB request plus system noise/overhead. |

The 1024 MiB × 2 probe shows a `MemAvailable` drop of 2.28 GiB against a 2 GiB allocation, a 14% overhead. This is consistent with expected kernel bookkeeping and page table costs for managed memory on UMA, though we cannot rule out contributions from concurrent system activity. The 256 MiB smoke test is too small for reliable `MemAvailable` delta measurement; `MemAvailable` fluctuated upward during this probe due to normal kernel cache reclaim, confirming that small-allocation deltas are dominated by noise. This probe serves only as a liveness check confirming that managed allocations are visible through `/proc/meminfo`.

### Meter Examples

**Example 1: 70B Q4, 131K context.**

| Parameter | Value |
|---|---|
| Parameters | 70B |
| Weight precision | 4-bit |
| Layers | 80 |
| Hidden size | 8,192 |
| Attention heads | 64 |
| KV heads | 8 |
| Batch | 1 |
| Sequence length | 131,072 |

| Metric | Value |
|---|---|
| Total required | 98.55 GiB |
| Available | 117.06 GiB |
| Remaining | 18.51 GiB |
| Fits | Yes |
| Derived max sequence length | 176,668 tokens |

**Example 2: 200B Q4, 32K context.**

| Parameter | Value |
|---|---|
| Parameters | 200B |
| Weight precision | 4-bit |
| Layers | 120 |
| Hidden size | 12,288 |
| Attention heads | 96 |
| KV heads | 8 |
| Batch | 1 |
| Sequence length | 32,768 |

| Metric | Value |
|---|---|
| Total required | 137.20 GiB |
| Available | 117.06 GiB |
| Deficit | 20.14 GiB |
| Fits | No |

The meter classifies both cases as expected: the 70B model fits with margin, while the 200B model exceeds available capacity. These are parametric estimates, not measurements of actual inference runs. The "fits" judgment depends on the accuracy of the overhead defaults and the stability of `MemAvailable` between the meter's snapshot and the inference run's actual allocation.

### Unit Tests

All unit tests passed. The test suite locks the core formulas for weight computation, KV cache sizing, overhead application, and fit classification. Full output is recorded in `logs/unit_tests.log`. Unit tests verify the arithmetic of the estimator; they do not validate the overhead defaults against real engine behavior.

## Limitations

1. **Architecture inputs required.** The meter requires explicit model architecture parameters (layer count, hidden size, head counts, etc.). It does not resolve these from a model name or checkpoint. A metadata resolver would improve usability but was outside the scope of this work.

2. **Engine-specific overhead is approximate.** Runtime memory consumption varies by inference engine, quantization format, CUDA graph capture strategy, prefill vs. decode memory profiles, and KV cache quantization. The meter's default allocator overhead (1.10×) and safety margin (1.05×) are deliberately conservative but unvalidated against real engine traces. They may overestimate overhead for well-optimized engines or underestimate it for engines with high internal fragmentation.

3. **Synthetic probes validate telemetry, not specific runtimes.** The CUDA managed-memory probes confirm that UMA allocations touched by both CPU and GPU are visible through `/proc/meminfo` on this GB10 host. They do not certify that a specific model binary will load without additional engine overhead beyond what the meter estimates. The probes are calibration tools, not production validation.

4. **`MemAvailable` is a noisy snapshot.** The kernel's `MemAvailable` estimate includes reclaimable caches and is inherently noisy. The meter reads it once at invocation time; concurrent system activity can reduce available memory before the inference run begins. The safety margin partially addresses this but cannot guarantee against all races. The 256 MiB smoke test demonstrated that `MemAvailable` deltas for small allocations are unreliable due to kernel cache reclaim noise.

5. **Single-host validation.** All calibration and meter results come from one GB10 host with 121.63 GiB total memory, Linux kernel 6.17.0-1014-nvidia-aarch64, and a specific earlyoom configuration. Behavior on other UMA devices, memory sizes, kernel versions, or earlyoom settings may differ. We have no evidence of generalization beyond this host.

6. **Claim audit status.** The structured claim ledger for this artifact is in a "blocked_empty_claims" state: no formal claims were extracted for audit. The results reported here have not passed a structured claim/evidence audit and should be interpreted accordingly.

7. **Mixed calibration signal at small sizes.** The 256 MiB probe showed `MemAvailable` fluctuating upward rather than downward, illustrating that the telemetry path is unreliable for small allocations. The meter's accuracy depends on the workload consuming a substantial fraction of total memory, where the signal-to-noise ratio of `MemAvailable` is favorable.

## Reproducibility Checklist

- **Source code:** `src/memory_budget_meter.py`, `scripts/collect_telemetry.py`, `scripts/uma_probe.cu`, `scripts/test_memory_budget_meter.py`
- **Build system:** `Makefile` (invoked via `make all`)
- **Primary run log:** `logs/run_20260430T015346Z.log`
- **Unit test log:** `logs/unit_tests.log`
- **Telemetry artifacts:** `results/telemetry.json`, `results/telemetry.stdout.json`
- **Calibration artifacts:** `results/uma_smoke_256m.json`, `results/uma_cal_512m_x2.json`, `results/uma_cal_1024m_x2.json`
- **Meter output artifacts:** `results/meter_70b_q4_131k.json`, `results/meter_200b_q4_32k.json`
- **Aggregated metrics:** `results/metrics.json`
- **Decision record:** `.omx/project_decision.json`
- **Claim ledger:** `papers/source-record-redacted-20260430T015148482807+0000/claim_ledger.json` (status: blocked_empty_claims)
- **Evidence bundle:** `papers/source-record-redacted-20260430T015148482807+0000/evidence_bundle.json`
- **Hardware:** NVIDIA GB10, aarch64, 121.63 GiB UMA, Linux 6.17.0-1014-nvidia
- **Software dependencies:** Python 3, CUDA toolkit (for `uma_probe.cu` compilation), earlyoom
- **Reproduction steps:** `make all` → run `collect_telemetry.py` → run `uma_probe` at each calibration size → run `memory_budget_meter.py` with desired model parameters → run unit tests via `python3 -m unittest -v scripts/test_memory_budget_meter.py`

## Conclusion

A parametric memory-budget meter using `/proc/meminfo` `MemAvailable` and earlyoom posture is viable as a conservative preflight planning gate for transformer inference on GB10/UMA hosts where `nvidia-smi` memory accounting is unavailable. CUDA managed-memory calibration probes confirm that UMA allocations are visible through the OS telemetry path, with measured overhead (2.28 GiB `MemAvailable` drop for a 2 GiB allocation) consistent with kernel bookkeeping costs. The meter correctly classifies a 70B Q4 model as fitting and a 200B Q4 model as not fitting on a 121.63 GiB host. However, the approach has significant caveats: the overhead defaults are unvalidated against real inference engines, `MemAvailable` is noisy for small allocations and is only a snapshot, and all results come from a single host. The approach is not a replacement for engine-specific profiling. The recommended next step is to integrate the meter as a preflight gate that emits a JSON artifact before each GB10 inference run and fails fast when the fit decision is negative or remaining margin is insufficient relative to the earlyoom threshold, then tune the overhead factors from observed inference traces.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Meter implementation | `src/memory_budget_meter.py` |
| Telemetry collector | `scripts/collect_telemetry.py` |
| CUDA UMA probe source | `scripts/uma_probe.cu` |
| Unit tests | `scripts/test_memory_budget_meter.py` |
| Primary run log | `logs/run_20260430T015346Z.log` |
| Unit test log | `logs/unit_tests.log` |
| Telemetry JSON | `results/telemetry.json` |
| Telemetry stdout | `results/telemetry.stdout.json` |
| Smoke probe result | `results/uma_smoke_256m.json` |
| Calibration probe 512M × 2 | `results/uma_cal_512m_x2.json` |
| Calibration probe 1024M × 2 | `results/uma_cal_1024m_x2.json` |
| Meter output (70B Q4, 131K) | `results/meter_70b_q4_131k.json` |
| Meter output (200B Q4, 32K) | `results/meter_200b_q4_32k.json` |
| Aggregated metrics | `results/metrics.json` |
| Project decision record | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260430T015148482807+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T015148482807+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T015148482807+0000/paper_manifest.json` |
