# Sub-8 GiB GGUF Model Zoo Triage on NVIDIA GB10: Feasibility, Throughput, and Toolchain Caveats

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, benchmark logs, claim ledger, evidence bundle). The operator who released these artifacts claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We report on a structured triage of 11 candidate sub-8 GiB GGUF-format language model artifacts for local deployment on the NVIDIA GB10 platform (aarch64, CUDA 13 driver stack, ~121 GiB system RAM). Two representative quantized models—SmolLM3-3B Q4_K_M (1.78 GiB) and Qwen3.5-4B Q4_K_M (2.55 GiB)—were downloaded and subjected to local smoke-testing via `llama-cpp-python`. Qwen3.5-4B Q4_K_M passed a CPU-backend throughput benchmark at 21.82 tokens/s with a post-load RSS of approximately 2.78 GiB. SmolLM3-3B Q4_K_M failed during chat-template parsing and is held pending a newer `llama.cpp` build or template patch. An attempt to rebuild `llama-cpp-python` with CUDA acceleration failed during CMake compiler detection on the aarch64 CUDA toolchain; all throughput figures therefore reflect CPU-only inference. GPU memory monitoring via `nvidia-smi` is not supported on GB10, necessitating RSS-based and `MemAvailable`-delta memory accounting. We conclude that a sub-8 GiB GGUF model zoo is viable with caveats, and recommend Qwen3.5-4B Q4_K_M (Apache-2.0) as the seed model, pending resolution of GPU acceleration and license verification for redistribution. The claim ledger for this artifact is currently empty, meaning no structured claims have passed audit; readers should treat all findings as preliminary prototype evidence.

---

## Introduction

The proliferation of quantized large language model (LLM) artifacts in GGUF format has made local inference on constrained hardware increasingly practical. However, systematic triage of candidate models—accounting for file size, license, local smoke-test viability, and platform-specific toolchain limitations—remains under-documented for emerging accelerator platforms.

The NVIDIA GB10 is an aarch64-based system shipping with a CUDA 13 driver stack and approximately 121 GiB of system RAM. Two platform-specific characteristics complicate standard deployment validation. First, `nvidia-smi` does not expose per-process or total VRAM metrics in the standard fashion on GB10, precluding direct GPU memory-budget validation. Second, the aarch64 CUDA toolchain presents build-time challenges for common inference frameworks, as we demonstrate empirically.

This study performs a structured triage of 11 candidate GGUF repositories with artifacts under 8 GiB, downloads two representative models, and evaluates local inference viability on the GB10 platform. We report both positive and negative results—including a failed CUDA build and a chat-template incompatibility—to provide an honest assessment of current deployment readiness. Only 2 of 11 candidates were locally validated; the remaining 9 were triaged by metadata alone.

---

## Method

### Platform

All experiments were conducted on a single NVIDIA GB10 node running Ubuntu 24.04.4 LTS (aarch64) with the CUDA 13 driver stack. The system reported approximately 121 GiB total RAM and approximately 116 GiB `MemAvailable` at session start. Swap was disabled (`SwapTotal: 0`), meaning any memory overcommit would result in OOM kills rather than swap-mediated degradation.

### Tooling

A Python virtual environment was provisioned with `huggingface_hub`, `psutil`, `tabulate`, and `llama-cpp-python` (pre-built wheel, CPU backend). The `uv` and `hf` CLI tools were available for package and model management. Notably, `torch` and `transformers` were not installed and were not used; all inference was conducted through `llama-cpp-python`. Exact version pins for installed packages were not recorded in the run notes, which constitutes a reproducibility gap.

### Candidate Selection

Eleven GGUF repositories were identified via Hugging Face metadata queries. Candidate repositories were selected to span multiple model families, size tiers, and license regimes:

| # | Repository | Notes |
|---|-----------|-------|
| 1 | unsloth/Qwen3.5-4B-GGUF | Apache-2.0 |
| 2 | unsloth/Qwen3-4B-GGUF | — |
| 3 | MaziyarPanahi/Qwen3-4B-Instruct-2507-GGUF | — |
| 4 | lmstudio-community/gemma-3-4b-it-GGUF | License-gated |
| 5 | unsloth/gemma-3n-E4B-it-GGUF | License-gated |
| 6 | MaziyarPanahi/Phi-4-mini-instruct-GGUF | — |
| 7 | bartowski/Llama-3.2-3B-Instruct-GGUF | License-gated |
| 8 | ggml-org/SmolLM3-3B-GGUF | Apache-2.0 |
| 9 | MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF | — |
| 10 | bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF | Reasoner lane |
| 11 | unsloth/Qwen3-VL-8B-Instruct-GGUF | — |

Representative GGUF files under the 8 GiB threshold were recorded for each repository. Full metadata is preserved in `data/hf_candidate_metadata.json`.

### Download and Smoke-Test Protocol

Two models were selected for download and local validation:

1. **SmolLM3-3B Q4_K_M** (`SmolLM3-Q4_K_M.gguf`, 1.78 GiB) — selected for its small size and Apache-2.0 license.
2. **Qwen3.5-4B Q4_K_M** (`Qwen3.5-4B-Q4_K_M.gguf`, 2.55 GiB) — selected as a mid-range candidate with permissive licensing.

Smoke-testing consisted of loading each model via `llama-cpp-python` and running a short generation prompt. Throughput was measured in tokens per second. Memory usage was assessed via process RSS (captured with `psutil`) and system-level `MemAvailable` deltas. No swap was available, so RSS values represent committed physical memory. Exact prompt text and context-length settings are preserved in the benchmark log files but were not extracted into this report.

### Attempted CUDA Acceleration

A rebuild of `llama-cpp-python` with CUDA support was attempted using `CMAKE_ARGS="-DGGML_CUDA=on"` and a no-cache reinstall. The build log was captured for diagnosis.

---

## Results

### Qwen3.5-4B Q4_K_M: Passed

Qwen3.5-4B Q4_K_M loaded successfully and produced coherent output. Measured throughput on the CPU backend was **21.82 tokens/s**. Post-load RSS was **2,989,072,384 bytes (~2.78 GiB)**, with total process memory footprint (including `llama-cpp-python` overhead) reaching approximately 3.0 GiB. Given 116 GiB of available RAM at session start, this represents a modest memory budget even for concurrent multi-model scenarios.

This throughput figure is from a single run; no statistical variation across multiple runs was recorded.

### SmolLM3-3B Q4_K_M: Held

SmolLM3-3B Q4_K_M failed during initialization due to an embedded chat-template parsing error in the current `llama-cpp-python` runtime. The model file itself is structurally valid; the failure is attributable to a chat-template format not yet supported by the installed `llama.cpp` version. This model is marked **HOLD** pending either a newer `llama.cpp` build or a manual template patch.

### CUDA Build: Failed

The CUDA-accelerated rebuild of `llama-cpp-python` failed during the CMake compiler detection phase. The build log indicates that the aarch64 CUDA toolchain on GB10 did not satisfy the compiler detection requirements of the `llama.cpp` CMake configuration. This is a toolchain integration issue, not a model viability issue. All reported throughput figures are therefore **CPU-backend only**. GPU-accelerated throughput on GB10 remains unmeasured.

### Memory Monitoring Limitation

`nvidia-smi` on GB10 reports memory usage as "Not Supported." This precludes direct VRAM measurement. Memory judgments throughout this study rely on process RSS and `MemAvailable` deltas, which capture system RAM usage but not GPU memory allocation. If GPU acceleration were functional, VRAM consumption would need to be inferred indirectly or measured through framework-level APIs.

### Summary Decision

The automated decision system classified the project outcome as **viable_with_caveats** with **medium-high confidence**. The primary recommendation is to seed the model zoo with Qwen3.5-4B Q4_K_M, maintain license-gated lanes for Gemma and Llama family models, and reserve a reasoner lane for DeepSeek-R1-Distill-Qwen-7B. No blockers were identified, but four caveats were recorded (see Limitations).

---

## Limitations

1. **CPU-only throughput.** All throughput measurements reflect the `llama-cpp-python` CPU backend on aarch64. GPU-accelerated throughput on GB10 remains unmeasured due to the failed CUDA build. Actual GPU-accelerated performance may differ substantially—likely favorably—in both throughput and memory residency. The CPU-only result of 21.82 tok/s should not be taken as representative of GB10's full capability.

2. **Single-model smoke test.** Only one of two downloaded models (Qwen3.5-4B) passed smoke-testing. The remaining 9 candidates were triaged via metadata only and were not locally validated. Their runtime behavior, chat-template compatibility, and actual memory footprints remain unknown.

3. **VRAM opacity.** The inability to query GPU memory via `nvidia-smi` means we cannot verify whether GPU-resident inference would fit within GB10's VRAM budget for any candidate model. RSS-based memory accounting captures only system RAM.

4. **License uncertainty.** Several candidate repositories do not expose license tags in their Hugging Face metadata. Base model licenses (e.g., Gemma terms, Llama community license) must be individually verified before any redistribution of derived GGUF artifacts.

5. **Static environment.** Experiments were conducted on a single GB10 node with a specific software stack (Ubuntu 24.04.4, CUDA 13, specific `llama-cpp-python` wheel version). Results may not generalize to other architectures, driver versions, or `llama.cpp` builds.

6. **No quality evaluation.** This triage assesses loadability and throughput only. No evaluation of output quality, factual accuracy, instruction-following capability, or safety was performed.

7. **Swap disabled.** With swap disabled, the system provides no memory-overcommit buffer. Models that nominally fit in RAM may still cause OOM under concurrent load or with large context windows, a scenario not tested here.

8. **Single-run throughput.** The 21.82 tok/s figure is from a single benchmark execution. No multi-run statistics (mean, variance, confidence intervals) are available. Run-to-run variation on this platform is uncharacterized.

9. **Incomplete package version recording.** Exact version pins for `llama-cpp-python` and other installed packages were not captured in the run notes, which limits bit-exact reproducibility.

10. **Empty claim ledger.** The claim ledger for this artifact contains no structured claims and its audit status is `blocked_empty_claims`. No claim in this paper has passed formal evidence audit. All findings should be treated as preliminary prototype evidence rather than audited results.

---

## Reproducibility Checklist

| Item | Status |
|------|--------|
| Platform described (hardware, OS, arch, CUDA version) | Yes |
| Software versions recorded (Python packages, llama-cpp-python) | Partial — package names recorded; exact version pins not in run notes |
| Candidate list with repositories | Yes (11 repos) |
| Downloaded model files named with sizes | Yes (2 of 11) |
| Benchmark command and parameters documented | Partial — logs preserved; exact prompt and context-length settings in bench logs |
| Throughput metric with unit | Yes (21.82 tok/s, single run) |
| Memory metric with methodology | Yes (RSS via psutil; MemAvailable deltas) |
| Negative results reported (CUDA build failure, SmolLM3 template failure) | Yes |
| Raw logs preserved and referenced | Yes |
| Decision JSON preserved | Yes |
| Random seeds specified | No (not applicable to this benchmark protocol) |
| Statistical variation reported (e.g., multiple runs) | No — single-run throughput reported |
| Claim ledger populated and audited | No — claim ledger is empty; audit status blocked |

---

## Conclusion

A sub-8 GiB GGUF model zoo is viable on the NVIDIA GB10 platform with important caveats. Qwen3.5-4B Q4_K_M (2.55 GiB, Apache-2.0) passes local smoke-testing at 21.82 tokens/s on the CPU backend with a post-load RSS of approximately 2.78 GiB, well within the system's 121 GiB RAM budget. However, two significant toolchain gaps remain unresolved: CUDA-accelerated `llama-cpp-python` could not be built on the aarch64 CUDA 13 toolchain, and GPU memory monitoring via `nvidia-smi` is not supported on GB10. These gaps mean that GPU-accelerated inference—the primary use case for an accelerator-class system—remains unvalidated.

SmolLM3-3B Q4_K_M, while attractive in size and licensing, is blocked by a chat-template incompatibility that requires either a newer `llama.cpp` runtime or a template patch. The remaining 9 candidates were triaged by metadata only and require local validation before inclusion.

We recommend seeding the zoo with Qwen3.5-4B Q4_K_M, maintaining license-gated lanes for Gemma and Llama family models, and reserving a reasoner lane for DeepSeek-R1-Distill-Qwen-7B. Resolution of the CUDA build failure and VRAM measurement limitations should be prioritized before any production deployment assessment. Multi-run benchmarking with statistical characterization, output quality evaluation, and population of the claim ledger with audit-approved claims are necessary before these findings can be considered validated.

---

## Referenced Artifacts

| Artifact | Path / Key | Description |
|----------|-----------|-------------|
| Run notes | `run_notes.md` | Session log with environment observations, actions, and outcomes |
| Decision JSON | `.omx/project_decision.json` | Machine-readable triage decision, recommendation, caveats |
| Candidate metadata | `data/hf_candidate_metadata.json` | Hugging Face metadata for 11 candidate GGUF repositories |
| Environment probe | `logs/env_probe.log` | Host, memory, GPU, and tool availability probe output |
| Qwen3.5-4B benchmark | `logs/bench_qwen35_4b_q4.log` | Throughput benchmark log for Qwen3.5-4B Q4_K_M |
| Qwen3.5-4B benchmark (T=20) | `logs/bench_qwen35_4b_q4_t20.log` | Alternate temperature benchmark log |
| SmolLM3 retry log | `logs/bench_smollm3_q4_retry.log` | Smoke-test failure log for SmolLM3 Q4_K_M |
| CUDA build log | `logs/reinstall_llama_cpp_cuda_nocache.log` | Failed CUDA rebuild log for llama-cpp-python |
| Triage report | `model_zoo_triage.md` | Consolidated model zoo triage report |
| Project metrics | `.omx/metrics.json` | Session token and turn metrics |
| Claim ledger | `papers/.../claim_ledger.json` | Empty claim ledger; audit status: blocked_empty_claims |
| Evidence bundle | `papers/.../evidence_bundle.json` | Minimal evidence bundle (source, project, run IDs only) |
| Paper manifest | `papers/.../paper_manifest.json` | Generation metadata and writer provider info |
