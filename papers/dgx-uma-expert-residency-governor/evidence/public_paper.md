# DGX Spark UMA Expert Residency Governor: A MemAvailable-Based Admission Controller for Unified Memory Systems

> **AI provenance / no-human-credit note:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, and benchmark logs). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

NVIDIA DGX Spark (GB10) systems employ a unified memory architecture (UMA) in which the GPU and CPU share a single 128 GB LPDDR5x DRAM pool. This design invalidates the conventional approach of using `nvidia-smi` framebuffer (FB) memory accounting to decide how many model expert shards or caches may safely remain resident. On the GB10, `nvidia-smi` reports memory usage as "Not Supported," and `cudaMemGetInfo` understates allocatable memory because it does not account for reclaimable OS memory. We investigate whether a Linux OS-level memory availability signal—`/proc/meminfo` `MemAvailable`—combined with an `earlyoom`-aware reserve policy, can serve as the primary capacity gate for an expert residency governor. On a single local DGX Spark host, we validate that: (1) `MemAvailable` tracks allocation pressure under managed-memory allocations of 256 MiB and 2 GiB; (2) a prototype governor produces correct admit/shed decisions for parameterized expert sizes of 8 GiB (admit) and 200 GiB (block); and (3) GPU utilization telemetry (SM occupancy, power, temperature) is obtainable via `nvidia-smi dmon` despite FB and BAR1 memory fields remaining unavailable. These results derive from short smoke tests and calibrations only; no real mixture-of-experts model was loaded, and no long-run stability test was performed. Confidence in the approach is medium-high, pending validation against representative MoE workloads.

## 1. Introduction

Mixture-of-experts (MoE) models benefit from keeping frequently routed expert shards resident in fast memory to avoid repeated load latency. On discrete-GPU systems, residency decisions are typically governed by VRAM availability reported through `nvidia-smi` or `cudaMemGetInfo`. The NVIDIA DGX Spark (GB10) platform departs from this model: its 128 GB LPDDR5x DRAM (273 GB/s peak bandwidth, 4266 MHz, 256-bit interface) is shared between CPU and GPU via address translation services (ATS), forming a unified memory architecture.

This architectural difference creates a practical problem. The standard GPU memory accounting interfaces either report nothing—`nvidia-smi` returns "Not Supported" on DGX Spark, which NVIDIA support confirms is expected for UMA systems—or report conservatively, as the DGX Spark Porting Guide warns that `cudaMemGetInfo` does not account for reclaimable OS memory. An expert residency governor that relies on these signals will either fail to operate or will systematically under-admit experts, wasting available capacity.

The present work asks: can a residency governor for DGX Spark use Linux OS-level memory availability as its primary capacity signal, and what auxiliary signals are needed to make safe admission decisions? We report results from a short empirical investigation on a local GB10 host, including CUDA managed-memory smoke tests, a cuBLAS throughput calibration, and a prototype governor implementation. We distinguish carefully between these prototype-stage results and production validation, which has not been performed.

## 2. Method

### 2.1 Platform

All experiments were conducted on a single DGX Spark host with the following characteristics:

| Property | Value |
|---|---|
| Kernel | Linux 6.17.0-1014-nvidia, aarch64 |
| CPU | 20 ARM cores (Cortex-X925 + Cortex-A725 clusters) |
| GPU | NVIDIA GB10, driver 580.159.03, CUDA 13.0 |
| Physical DRAM | 127,535,908 kB (~121.6 GiB) LPDDR5x |
| `nvidia-smi` memory usage | Not Supported |
| `earlyoom` | Active, configured `-m 4 -r 60` |
| Swap (observed) | 134,217,724 kB (~128 GiB) |

The swap observation is notable: the intended GB10 posture is swap-disabled, but the local host had swap enabled. This discrepancy is discussed in §5.

### 2.2 UMA Attribute Probe

A CUDA smoke test (`scripts/gb10_uma_smoke.cu`) queried four device attributes and performed managed-memory allocations of 256 MiB and 2 GiB, recording `MemAvailable` from `/proc/meminfo` before and after each allocation. The attributes queried were: `concurrentManagedAccess`, `pageableMemoryAccess`, `pageableMemoryAccessUsesHostPageTables`, and `hostNativeAtomicSupported`. These correspond to the CUDA Programming Guide's decision pattern for identifying unified-memory systems with host page-table hardware coherency.

### 2.3 Throughput Calibration

A cuBLAS GEMM smoke test (`scripts/gb10_cublas_smoke.cu`) executed 1000 repetitions of a 4096×4096 FP32 matrix multiply, measuring wall-clock runtime and computing throughput in TFLOP/s. Concurrent `nvidia-smi dmon` sampling at 1-second intervals captured SM utilization, power, and temperature. This calibration served two purposes: verifying that the GPU compute path is functional and confirming that utilization telemetry is obtainable on the UMA host.

### 2.4 Governor Policy

The prototype governor (`scripts/uma_residency_governor.py`) implements the following policy:

```
reserve = max(configured_reserve_gib, MemTotal × earlyoom_floor_pct) × safety_factor
usable_for_residency = MemAvailable − reserve
max_resident_experts = floor(usable_for_residency / expert_size)
admit_next = (usable_for_residency >= expert_size)
```

Default parameters: base reserve 16 GiB, earlyoom floor 6% of MemTotal, safety factor 1.10. The governor was tested with two expert-size configurations: 8 GiB (expected admit) and 200 GiB (expected block). The policy intentionally ignores swap for admission decisions, even when swap is present, because swapping violates the intended GB10 memory posture and would introduce unpredictable latency.

## 3. Results

### 3.1 UMA Attributes and Managed-Memory Allocation

The GB10 device reported the following CUDA attributes:

| Attribute | Value |
|---|---|
| `concurrentManagedAccess` | 1 |
| `pageableMemoryAccess` | 1 |
| `pageableMemoryAccessUsesHostPageTables` | 1 |
| `hostNativeAtomicSupported` | 1 |

These values confirm full unified-memory support with host page-table hardware coherency, consistent with the CUDA Programming Guide's UMA decision pattern. Both the 256 MiB and 2 GiB managed allocations completed successfully, and `MemAvailable` decreased consistently with allocation pressure. This confirms that the OS-level memory availability signal tracks managed-memory allocation on this UMA system.

### 3.2 Throughput and Utilization

The cuBLAS calibration produced:

| Metric | Value |
|---|---|
| Runtime (n=4096, 1000 reps) | 7.481 s |
| FP32 throughput | 18.372 TFLOP/s |
| Peak SM utilization | 96% |
| Peak power | 93 W |
| Peak temperature | 57 °C |

`nvidia-smi dmon` successfully reported SM utilization, power, and temperature. FB memory and BAR1 memory fields were unavailable (reported as `-`), consistent with the UMA architecture where framebuffer accounting is not exposed through this interface. This confirms that GPU utilization telemetry is accessible even though memory telemetry is not.

### 3.3 Governor Decisions

With initial `MemAvailable` of approximately 115.4 GiB:

**8 GiB expert, 16 GiB base reserve:**

| Metric | Value |
|---|---|
| Computed reserve | 17.6 GiB (max(16, 121.6 × 0.06) × 1.10) |
| Usable for residency | 97.81 GiB |
| Max resident experts | 12 |
| `admit_next` | true |

**200 GiB expert, 16 GiB base reserve:**

| Metric | Value |
|---|---|
| `admit_next` | false |
| Negative-case assertion | Passed |

The governor correctly admitted the 8 GiB expert and blocked the 200 GiB expert, confirming that the policy logic handles both positive and negative cases. However, these are parameterized inputs, not real expert memory footprints derived from an actual model.

## 4. Limitations

1. **No representative MoE workload.** Expert size was a command-line parameter, not derived from a real model. Production thresholds for reserve size, earlyoom floor percentage, and safety factor require calibration against actual expert memory footprints and their spike patterns during inference. The observed "12 resident experts" figure applies only to the synthetic 8 GiB parameterization.

2. **No long-run stability test.** Experiments consisted of short smoke tests and calibrations lasting seconds to minutes. Sustained inference under residency pressure—tracking `MemAvailable` drift, OOM events, and expert reload latency over hours—was not performed. Memory fragmentation, kernel-level reclaim behavior under sustained pressure, and the interaction between `earlyoom` and the governor's reserve policy remain untested.

3. **Swap posture mismatch.** The local host reported ~128 GiB of swap despite the intended GB10 posture of swap-disabled operation. The governor was designed to ignore swap for admission decisions, and it did. However, the host configuration discrepancy means the observed `MemAvailable` behavior may differ from a swap-disabled production environment, where memory pressure would trigger OOM killing earlier rather than swapping. The presence of swap may have inflated `MemAvailable` readings relative to the no-swap configuration.

4. **Single-host sample.** All observations come from one DGX Spark unit. Variability across units, firmware versions, or driver revisions was not characterized.

5. **`cudaMemGetInfo` not independently benchmarked.** The NVIDIA Porting Guide warns that `cudaMemGetInfo` understates allocatable UMA memory, but we did not independently quantify the gap between `cudaMemGetInfo` output and actual allocatable capacity on this host. This gap is cited from official documentation rather than measured.

6. **Performance gate not implemented.** The two-layer governor design proposes a performance gate (inference latency, tokens/s, eviction/reload time) alongside the capacity gate. Only the capacity gate was implemented and tested. Whether keeping experts resident actually improves end-to-end inference performance on this platform remains unvalidated.

7. **Claim audit status.** The claim ledger for this artifact is in `blocked_empty_claims` status, meaning no structured claims have passed formal evidence audit. The findings reported here should be interpreted as prototype-stage observations rather than audit-approved claims.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Hardware specified | Yes: DGX Spark / GB10, aarch64, 128 GiB LPDDR5x |
| Driver/CUDA version specified | Yes: driver 580.159.03, CUDA 13.0 |
| Kernel version specified | Yes: 6.17.0-1014-nvidia |
| `earlyoom` configuration recorded | Yes: `-m 4 -r 60` |
| Swap state documented | Yes: ~128 GiB observed (noted as mismatch with intended posture) |
| Source files available | Yes: `scripts/uma_residency_governor.py`, `scripts/gb10_uma_smoke.cu`, `scripts/gb10_cublas_smoke.cu` |
| Build commands documented | Yes: nvcc commands with `-O2 -std=c++17` flags recorded |
| Run commands documented | Yes: parameterized commands for each test |
| Raw logs preserved | Yes: 7 log files in `logs/` directory |
| Metrics extracted | Yes: `metrics/research_metrics.json` |
| Decision rationale recorded | Yes: `.omx/project_decision.json` |
| Random seeds | Not applicable (no stochastic components in tests) |
| Third-party dependencies | CUDA toolkit, cuBLAS, Python 3 (standard library only in governor) |
| Multi-host replication | No: single host only |
| Long-run stability | No: smoke tests and calibrations only |

## 6. Conclusion

On the DGX Spark / GB10 unified-memory platform, `nvidia-smi` FB memory reporting is unavailable and `cudaMemGetInfo` is an unreliable capacity signal for expert residency decisions. Linux `MemAvailable`, combined with an `earlyoom`-aware reserve policy, provides a viable primary signal for a residency governor. A prototype governor correctly admits and blocks parameterized experts under this policy, and GPU utilization telemetry (SM occupancy, power, temperature) remains accessible through `nvidia-smi dmon`.

These findings are based on short smoke tests and calibrations on a single host. The approach has not been validated against a real mixture-of-experts model, and production deployment requires: (1) tuning reserve parameters against representative MoE memory traces; (2) implementing the proposed performance gate to evaluate whether residency actually improves inference latency and throughput; (3) confirming the swap-disabled host posture and re-validating `MemAvailable` behavior under that configuration; and (4) long-run stability testing under sustained inference load. Until these steps are completed, the medium-high confidence assigned to this result should be interpreted as indicating a promising direction that remains short of production validation.

---

## Referenced Artifacts

| Artifact | Description |
|---|---|
| `run_notes.md` | Primary research log with observations, interpretation, and reproduction commands |
| `scripts/uma_residency_governor.py` | Prototype governor: MemAvailable/earlyoom-based admit/shed logic |
| `scripts/gb10_uma_smoke.cu` | CUDA managed-memory allocation smoke test and UMA attribute probe |
| `scripts/gb10_cublas_smoke.cu` | cuBLAS GEMM throughput/utilization calibration |
| `metrics/research_metrics.json` | Extracted quantitative metrics from the run |
| `.omx/project_decision.json` | Machine-readable decision record with evidence references and key metrics |
| `logs/local_smoke_20260505T210503Z.log` | Host telemetry smoke output |
| `logs/gb10_uma_smoke_256m_20260505T210558Z.log` | 256 MiB managed allocation log |
| `logs/gb10_uma_smoke_2g_20260505T210608Z.log` | 2 GiB managed allocation log |
| `logs/gb10_cublas_smoke_long_20260505T210722Z.log` | cuBLAS calibration runtime log |
| `logs/nvidia_dmon_cublas_long_20260505T210722Z.log` | `nvidia-smi dmon` telemetry during cuBLAS run |
| `logs/uma_residency_governor_20260505T210805Z.json` | Governor admit decision output (8 GiB expert) |
| `logs/uma_residency_governor_block_20260505T210811Z.json` | Governor block decision output (200 GiB expert) |
| `papers/.../claim_ledger.json` | Claim ledger (status: `blocked_empty_claims`) |
| `papers/.../evidence_bundle.json` | Evidence bundle (source: `langgraph_control_plane_mvp`) |
| `papers/.../paper_manifest.json` | Paper generation manifest |
