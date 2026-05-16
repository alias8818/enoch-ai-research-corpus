# llama.cpp GGUF mmap Hot-Warm-Cold Page Residency Instrumentation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, evidence bundles, claim ledgers, and benchmark outputs). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated these claims.

---

## Abstract

We present a lightweight, Linux-specific instrumentation patch for llama.cpp's GGUF memory-mapped file path that classifies mapped pages into four residency categories—hot, warm, cold, and evicted-initial—using `mincore(2)`. The patch emits aggregate page-count JSONL events at three lifecycle points (post-mmap, post-fragment-unmap, pre-munmap) and introduces an opt-in `LLAMA_MMAP_HOTNESS_NO_POPULATE` environment variable to suppress llama.cpp's default `MAP_POPULATE` prefetch, which otherwise collapses the observable residency distribution. In calibration runs with a 15M-parameter Q4_0 GGUF model on an aarch64 host with 127.5 GB RAM, three conditions produced distinct, expected residency profiles: (1) after advisory page-cache eviction, 3,889 of 4,481 tensor pages were cold at post-fragment-unmap and transitioned to warm by pre-munmap; (2) with a warm page cache, all tensor pages were hot throughout; (3) with default `MAP_POPULATE`, all pages were hot immediately despite prior eviction. The instrumentation is aggregate and page-level; per-tensor attribution and cross-platform portability remain open. Results are from a single small-model calibration on one host and have not been validated at production model scale.

## 1 Introduction

llama.cpp loads GGUF model files via `mmap(2)`, mapping the file into the process address space and relying on the operating system page cache to service page faults on demand. On Linux, the default build passes `MAP_POPULATE` to pre-fault all mapped pages, eliminating demand-paging latency but also making it impossible to observe which pages were already resident versus which were faulted in during inference. This distinction matters for understanding cold-start latency, page-cache competition under memory pressure, and the interaction between model loading and system-level eviction policies.

We investigate whether a minimal, local instrumentation patch can capture page residency state at key points in the mmap lifecycle and classify pages into categories reflecting their residency history:

- **Hot**: resident both at the baseline (immediately after mmap) and at the current sampling point.
- **Warm**: not resident at baseline but resident at the current sampling point (demand-faulted in).
- **Cold**: not resident at the current sampling point.
- **Evicted-initial**: resident at baseline but not at the current sampling point (evicted between observations).

This paper reports the design, implementation, and calibration results of such a patch, evaluated under three controlled conditions on a single small model. The results are hook-prototype calibration evidence, not production-validated findings.

## 2 Method

### 2.1 Instrumentation Design

The patch modifies a single source file (`llama-mmap.cpp`) in a local fork of llama.cpp at commit `c3c15053925746c74fc2aaf6b864bd66665393c4`. The instrumentation is activated by setting the environment variable `LLAMA_MMAP_HOTNESS_LOG` to an absolute path for JSONL output. When enabled:

1. **Baseline capture.** Immediately after `mmap(2)` returns, `mincore(2)` is called on the full mapping to record which pages are resident. This snapshot serves as the baseline for hot/evicted-initial classification.

2. **Event emission.** JSONL records are emitted at three lifecycle stages:
   - `post_mmap`: after the initial mmap and baseline `mincore` call.
   - `post_unmap_fragment`: after llama.cpp unmaps non-tensor fragments (the region of the GGUF file containing metadata but not tensor data).
   - `pre_munmap`: at mapping teardown, before `munmap(2)`.

3. **Page classification.** At each sampling point, `mincore(2)` is called on currently mapped fragments. Pages are classified relative to the baseline:
   - Pages resident at both baseline and current sample: `hot_pages`.
   - Pages not resident at baseline but resident at current sample: `warm_pages`.
   - Pages not resident at current sample: `cold_pages`.
   - Pages resident at baseline but not at current sample: `evicted_initial_pages`.

4. **No-populate switch.** Setting `LLAMA_MMAP_HOTNESS_NO_POPULATE=1` suppresses the `MAP_POPULATE` flag on Linux. Without this switch, llama.cpp's default behavior pre-faults all pages at mmap time, making nearly every page hot immediately and obscuring cold-to-warm transitions.

Only aggregate page counts are emitted per event, not per-page bitmaps. This limits output size but precludes per-page or per-tensor analysis from the JSONL alone.

### 2.2 Page-Cache Eviction Helper

A helper script (`scripts/evict_file.py`) uses `os.posix_fadvise(..., POSIX_FADV_DONTNEED)` to request that the kernel evict clean pages for a specified file from the page cache. This is an advisory operation; it does not guarantee complete eviction and does not require root privileges.

### 2.3 Experimental Conditions

Three conditions were tested using `llama-bench` with a 15M-parameter Q4_0 GGUF model (`stories15M-q4_0.gguf`, SHA256: `66967fbece6dbe97886593fdbb73589584927e29119ec31f08090732d1861739`):

| Condition | Eviction before run | `NO_POPULATE` | `MAP_POPULATE` |
|-----------|-------------------|---------------|----------------|
| Cold-ish  | Yes (`POSIX_FADV_DONTNEED`) | Yes | No |
| Warm      | No                | Yes           | No             |
| Populate  | Yes (`POSIX_FADV_DONTNEED`) | No            | Yes (default)  |

Benchmark command shape:

```
LLAMA_MMAP_HOTNESS_LOG=$PWD/metrics/hotness_bench_<condition>.jsonl \
LLAMA_MMAP_HOTNESS_NO_POPULATE=1 \
/usr/bin/time -v external/llama.cpp/build/bin/llama-bench \
  -m models/stories15M-q4_0.gguf -p 8 -n 4 -r 1 -t 4 -ngl 0 --no-warmup -o jsonl
```

The `LLAMA_MMAP_HOTNESS_NO_POPULATE=1` line was omitted for the populate condition. Each condition was run once (1 repetition, no warmup), prioritizing calibration over statistical robustness.

### 2.4 Host Environment

- Architecture: aarch64 (Linux)
- MemTotal: ~127.5 GB
- MemAvailable before runs: ~120.6 GB
- SwapTotal: 0
- earlyoom running with configuration `-m 4 -r 60`
- Build flags: `LLAMA_CURL=OFF`, `GGML_NATIVE=OFF`, `GGML_CUDA=OFF`, `GGML_OPENMP=ON`

The host had ample free memory throughout; no OS-level memory pressure was present. Results under memory pressure are not characterized.

## 3 Results

### 3.1 Cold-ish Condition (Post-Eviction, No Populate)

After advisory eviction via `POSIX_FADV_DONTNEED`, the page cache did not fully release the file: 769 of 4,658 mapped pages were still resident at `post_mmap`. After llama.cpp unmapped non-tensor fragments, 592 of 4,481 tensor-mapped pages were hot and 3,889 were cold.

By `pre_munmap`, all 3,889 previously cold pages had transitioned to warm (demand-faulted during inference), with 0 cold pages remaining. No pages were classified as evicted-initial at any stage.

| Stage | Mapped pages | Hot | Warm | Cold | Evicted-initial |
|-------|-------------|-----|------|------|-----------------|
| post_mmap | 4,658 | 769 | 0 | 3,889 | 0 |
| post_unmap_fragment | 4,481 | 592 | 0 | 3,889 | 0 |
| pre_munmap | 4,481 | 592 | 3,889 | 0 | 0 |

Resource usage (from `/usr/bin/time -v`): elapsed 0.04 s, max RSS 33,652 KB, 6 major faults, 4,326 minor faults, 37,264 file system inputs, exit status 0.

Throughput: 637.30 tok/s (prompt, 8 tokens), 1,528.35 tok/s (generation, 4 tokens).

### 3.2 Warm Condition (No Eviction, No Populate)

With the file already resident in the page cache from a prior access, all 4,658 pages were hot at `post_mmap`. This profile persisted through all stages.

| Stage | Mapped pages | Hot | Warm | Cold | Evicted-initial |
|-------|-------------|-----|------|------|-----------------|
| post_mmap | 4,658 | 4,658 | 0 | 0 | 0 |
| post_unmap_fragment | 4,481 | 4,481 | 0 | 0 | 0 |
| pre_munmap | 4,481 | 4,481 | 0 | 0 | 0 |

Resource usage: elapsed 0.03 s, max RSS 33,744 KB, 0 major faults, 4,288 minor faults, 0 file system inputs, exit status 0.

Throughput: 2,324.83 tok/s (prompt), 1,442.86 tok/s (generation).

### 3.3 Default MAP_POPULATE Condition (Post-Eviction, Populate Enabled)

Despite prior eviction, `MAP_POPULATE` caused all 4,658 pages to be resident immediately at `post_mmap`. The cold-to-warm transition observed in the cold-ish condition is entirely hidden by this prefetch.

| Stage | Mapped pages | Hot | Warm | Cold | Evicted-initial |
|-------|-------------|-----|------|------|-----------------|
| post_mmap | 4,658 | 4,658 | 0 | 0 | 0 |
| post_unmap_fragment | 4,481 | 4,481 | 0 | 0 | 0 |
| pre_munmap | 4,481 | 4,481 | 0 | 0 | 0 |

Resource usage: elapsed 0.05 s, max RSS 38,088 KB, 0 major faults, 4,118 minor faults, 37,264 file system inputs, exit status 0.

The populate condition's file system input count (37,264) matches the cold-ish condition's, consistent with `MAP_POPULATE` reading all pages at mmap time rather than on demand.

### 3.4 Comparative Summary

The three conditions produce clearly distinguishable residency profiles. The cold-ish condition is the only one where cold pages are observed at `post_unmap_fragment` and where a cold-to-warm transition occurs. The warm and populate conditions are indistinguishable in their page residency profiles despite different pre-run cache states, confirming that `MAP_POPULATE` collapses the observable distinction.

The prompt throughput difference between cold-ish (637.30 tok/s) and warm (2,324.83 tok/s) conditions—approximately a 3.6× ratio—is consistent with demand-fault overhead for cold pages. However, the benchmark is too short (8 prompt tokens, 4 generation tokens, 1 repetition) for this ratio to be treated as a stable measurement. The generation throughput shows a smaller and reversed difference (1,528.35 vs. 1,442.86 tok/s), which may reflect measurement noise at this scale.

## 4 Limitations

1. **Single small model, single host.** All results come from a 15M-parameter Q4_0 model (~18 MB) on one aarch64 host with abundant RAM. Behavior under memory pressure, with large models (tens of GB), or on different architectures is not characterized.

2. **Advisory eviction is incomplete.** `POSIX_FADV_DONTNEED` is advisory. In the cold-ish condition, 769 of 4,658 pages (16.5%) remained resident after eviction. The "cold-ish" label is deliberate; a truly cold startup cannot be guaranteed with this mechanism.

3. **Aggregate page counts only.** The instrumentation emits total page counts per residency category per event. Per-tensor attribution would require joining mmap page ranges to `llama_model_loader` tensor offset and name metadata, which the current patch does not do.

4. **Linux-specific.** `mincore(2)` is Linux-specific. Windows and macOS would require different APIs or would need to report the instrumentation as unsupported.

5. **`mincore(2)` staleness.** The Linux man page notes that `mincore` may return stale information about page residency. The results should be interpreted as approximate snapshots, not as precise real-time state.

6. **Short benchmark, unstable throughput.** The benchmark configuration (8 prompt tokens, 4 generation tokens, 1 repetition) prioritizes fast calibration over throughput stability. The reported tok/s values are indicative, not statistically robust.

7. **No memory pressure tested.** With ~120 GB available RAM and an ~18 MB model, no page-cache competition or eviction pressure occurred. The evicted-initial category was never observed in these runs; its behavior under pressure remains unvalidated.

8. **Not upstream-ready.** This is a local research patch. The llama.cpp upstream `AGENTS.md` explicitly warns against AI-generated pull requests; no PR or commit was made.

9. **No repeated trials.** Each condition was run once. Variance across runs has not been characterized.

## 5 Reproducibility Checklist

- **Source code**: Local fork of `llama.cpp` at commit `c3c15053925746c74fc2aaf6b864bd66665393c4`. Patch file: `artifacts/llama_mmap_hotness_instrumentation.patch`.
- **Model file**: `stories15M-q4_0.gguf`, SHA256 `66967fbece6dbe97886593fdbb73589584927e29119ec31f08090732d1861739`, downloaded from `https://huggingface.co/ggml-org/models/resolve/main/tinyllamas/stories15M-q4_0.gguf`.
- **Build commands**: cmake with `LLAMA_CURL=OFF`, `GGML_NATIVE=OFF`, `GGML_CUDA=OFF`, `GGML_OPENMP=ON`. Full commands documented in run notes.
- **Environment variables**: `LLAMA_MMAP_HOTNESS_LOG` (absolute path for JSONL output), `LLAMA_MMAP_HOTNESS_NO_POPULATE=1` (for cold-ish and warm conditions; omitted for populate condition).
- **Eviction mechanism**: `scripts/evict_file.py` using `POSIX_FADV_DONTNEED`.
- **Host details**: Linux aarch64, 127.5 GB RAM, 0 swap, earlyoom active. Full memory posture captured in `metrics/mem_before_runs.txt` and `metrics/mem_after_bench.txt`.
- **Raw outputs**: All JSONL hotness logs, stdout/stderr/time logs, and summary JSON preserved under `metrics/` and `artifacts/logs/`.
- **Randomness**: Benchmark used `-r 1` (1 repetition) and `--no-warmup`. No GPU randomness (`-ngl 0`). OpenMP was enabled; thread scheduling may introduce minor non-determinism in wall-clock times but should not affect page residency counts.
- **Result classification**: These are llama.cpp hook-prototype calibration results on a toy-scale model, not production-validated findings.

## 6 Conclusion

A minimal Linux-only patch to llama.cpp's mmap path can instrument GGUF page residency using `mincore(2)` and classify pages into hot, warm, cold, and evicted-initial categories. In calibration runs with a small model, three controlled conditions produced distinct, expected residency profiles, confirming that the instrumentation captures meaningful state transitions. The default `MAP_POPULATE` behavior in llama.cpp collapses the observable residency distribution; the `LLAMA_MMAP_HOTNESS_NO_POPULATE` switch is necessary for demand-fault attribution.

The current implementation is limited to aggregate page counts on Linux, has not been tested under memory pressure or with large models, and is not suitable for upstream submission in its present form. Per-tensor attribution would require joining mmap offsets to tensor metadata. The evicted-initial category, while implemented, was never observed in these runs due to the absence of memory pressure. Despite these limitations, the approach provides a viable local diagnostic for understanding page-cache interactions during GGUF model loading and inference, and the calibration evidence supports further investigation at production model scale under realistic memory conditions.

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Instrumentation patch | `artifacts/llama_mmap_hotness_instrumentation.patch` |
| Cold hotness JSONL | `metrics/hotness_bench_cold.jsonl` |
| Warm hotness JSONL | `metrics/hotness_bench_warm.jsonl` |
| Populate hotness JSONL | `metrics/hotness_bench_populate.jsonl` |
| Cold benchmark stdout | `artifacts/logs/bench_cold.stdout.jsonl` |
| Cold benchmark stderr/time | `artifacts/logs/bench_cold.stderr.log` |
| Warm benchmark stdout | `artifacts/logs/bench_warm.stdout.jsonl` |
| Warm benchmark stderr/time | `artifacts/logs/bench_warm.stderr.log` |
| Populate benchmark stdout | `artifacts/logs/bench_populate.stdout.jsonl` |
| Populate benchmark stderr/time | `artifacts/logs/bench_populate.stderr.log` |
| Consolidated summary | `metrics/summary.json` |
| Memory posture (before) | `metrics/mem_before_runs.txt` |
| Memory posture (after) | `metrics/mem_after_bench.txt` |
| Eviction helper script | `scripts/evict_file.py` |
| Project decision JSON | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260501T160041613105+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T160041613105+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T160041613105+0000/paper_manifest.json` |
| llama.cpp source (local fork) | `external/llama.cpp` at `c3c15053925746c74fc2aaf6b864bd66665393c4` |
