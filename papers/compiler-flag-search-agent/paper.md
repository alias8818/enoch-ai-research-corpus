# Compiler Flag Search Agent: Checksum-Gated Autonomous Flag Selection on aarch64

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, and benchmark logs). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and evaluate its claims against the referenced primary evidence.

---

## Abstract

We describe a minimal, dependency-free local agent that autonomously enumerates compiler flag combinations, compiles a benchmark workload, executes repeated timings, and ranks candidates by median runtime while rejecting those that produce incorrect output. The agent uses a strict checksum equivalence gate: any candidate whose output diverges from an `-O0` baseline is discarded. On an aarch64 (Cortex-X925 / Cortex-A725) host with GCC 13.3.0 and Clang 18.1.3, the agent evaluated up to 30 flag candidates per run across four experimental phases (smoke, GCC calibration, Clang calibration, and a broader throughput sweep). The best valid GCC candidate (`-O3 -mcpu=native -flto`) achieved a 5.20× speedup over the `-O0` baseline; the best valid Clang candidate (`-O3`) achieved 6.01×. Candidates involving `-Ofast` were consistently rejected due to checksum mismatch, demonstrating that the correctness gate catches unsafe fast-math transformations. All runs completed with low memory footprint and zero swap usage. These results establish local feasibility of autonomous, correctness-gated compiler flag search as a prototype, but do not demonstrate workload-general compiler superiority. The search policy remains simple enumeration rather than Bayesian or learned optimization, and timing methodology lacks CPU isolation and formal confidence intervals.

## Introduction

Selecting compiler optimization flags for a given workload and target machine is a practical optimization problem that typically relies on developer intuition, default settings, or manual benchmarking. Automated approaches exist but often require external dependencies, complex infrastructure, or acceptance of potentially unsafe transformations.

This work investigates a narrower question: can a minimal, stdlib-only local agent compile, run, validate, and rank compiler flag combinations without human-provided dependencies, while leaving sufficient evidence to assess viability? The agent enforces strict output correctness via checksum comparison against an `-O0` baseline, ensuring that only flag combinations preserving bit-exact output are considered valid.

We report results from a prototype implementation running on an aarch64 system with 20 ARM cores, using both GCC and Clang. The goal is not to establish general compiler performance claims, but to determine whether the autonomous search-and-validate loop is feasible, produces trustworthy rankings, and operates within the memory and time constraints of the target host.

## Method

### Benchmark Workload

The agent uses a synthetic C workload (`benchmarks/kernel_mix.c`) consisting of deterministic mixed scalar and vector operations that produce a checksum output. The workload is intentionally simple: it serves as a vehicle for testing the search harness, not as a representative proxy for real applications.

### Search Harness

The harness (`src/flag_search_agent.py`) is implemented in pure Python standard library with no external dependencies. Its loop for each candidate flag combination is:

1. **Compile** the benchmark with the candidate flags using the selected compiler.
2. **Execute** the compiled binary for a configurable number of iterations (`--iters`), repeated for a configurable number of repetitions (`--reps`).
3. **Validate** the output checksum against the `-O0` baseline. Candidates producing any checksum mismatch are rejected.
4. **Record** compile time, per-repetition run times, median runtime, binary size, and memory snapshots as JSONL evidence.

A separate summarization script (`src/summarize_results.py`) aggregates JSONL logs into a structured summary.

### Correctness Gate

The checksum gate compares the stdout of each candidate binary against the stdout of the same benchmark compiled at `-O0`. Any divergence—whether from floating-point reassociation, vectorization-induced reordering, or other `-Ofast`-class transformations—results in rejection. This is a strict equivalence criterion; workloads with tolerance-based validation would likely accept different (and potentially faster) candidates.

### Experimental Phases

Four phases were executed sequentially:

| Phase | Compiler | Mode | Limit | Iters | Reps | Purpose |
|---|---|---|---|---|---|---|
| Smoke | GCC | smoke | 8 | 40 | 7 | Basic functionality check |
| GCC Calibration | GCC | calibrate | 10 | 2000 | 7 | Ranked comparison of hand-picked candidates |
| Clang Calibration | Clang | calibrate | 10 | 2000 | 7 | Same for Clang |
| GCC Throughput | GCC | full | 30 | 1000 | 5 | Search mechanics and throughput measurement |

The `--limit` parameter bounds the number of candidates evaluated. The calibration phases used hand-picked flag combinations of interest; the throughput phase used a broader enumeration ordered by optimization level.

### Environment

All experiments ran on a single aarch64 host (Linux, `gx10-efe8`) with 20 ARM cores (Cortex-X925 and Cortex-A725), GCC 13.3.0, and Clang 18.1.3. Available memory at start was approximately 122 GB with zero swap configured. The harness monitored `MemAvailable` before each candidate evaluation.

### Timing Methodology

Each candidate's runtime is reported as the median across repetitions, where each repetition itself is the total time for the configured number of iterations. This provides some noise reduction but does not include CPU core isolation, frequency pinning, or formal statistical confidence intervals. The timing is wall-clock via Python's standard timing facilities.

## Results

### Smoke Test

The smoke test evaluated 5 candidates in 0.35 seconds (max RSS 27,920 KB, zero swaps). All 5 candidates passed the checksum gate. The best candidate was GCC `-O2` with a median runtime of 0.002262 s, yielding a 5.47× speedup over the `-O0` baseline. This confirmed basic harness functionality.

### GCC Calibration

The GCC calibration evaluated 10 candidates in 7.20 seconds (max RSS 32,916 KB, zero swaps). Of these, 7 passed the checksum gate and 3 were rejected:

- **Rejected:** `-Ofast`, `-Ofast -mcpu=native`, `-Ofast -mcpu=native -funroll-loops`
- **Rejection reason:** Checksum mismatch versus the strict `-O0` baseline.

The best valid candidate was GCC `-O3 -mcpu=native -flto` with a median runtime of 0.058587 s (5.20× speedup over baseline).

### Clang Calibration

The Clang calibration evaluated 10 candidates in 7.09 seconds (max RSS 96,492 KB, zero swaps). As with GCC, 7 candidates passed and 3 were rejected for the same `-Ofast`-class checksum mismatches.

The best valid candidate was Clang `-O3` with a median runtime of 0.050597 s (6.01× speedup over baseline). The compiled binary was 70,752 bytes.

### GCC Throughput Sweep

The broader enumeration evaluated 30 candidates in 17.03 seconds (max RSS 32,200 KB, zero swaps), yielding an approximate throughput of 1.76 candidates per second (each candidate requiring compilation plus 5 timed executions at 1000 iterations). All 30 candidates in this enumeration slice passed the checksum gate.

The best candidate in this slice was GCC `-O1 -mcpu=native -fno-tree-vectorize` at 4.03× versus baseline. However, because the first 30 candidates in the enumeration are ordered by optimization level, this slice did not include the `-O2`/`-O3` combinations that won the calibrated runs. The throughput sweep primarily demonstrates search mechanics and throughput rather than identifying the globally best candidate.

### Memory Behavior

All four phases completed with low RSS (maximum observed: 96,492 KB for the Clang calibration) and zero swap operations, consistent with the host's zero-swap memory posture. The harness's `MemAvailable` checks did not trigger any skips or aborts.

### Summary of Key Results

| Phase | Candidates | Valid | Rejected | Best Valid Flags | Speedup vs `-O0` |
|---|---|---|---|---|---|
| Smoke (GCC) | 5 | 5 | 0 | `-O2` | 5.47× |
| Calibrate (GCC) | 10 | 7 | 3 | `-O3 -mcpu=native -flto` | 5.20× |
| Calibrate (Clang) | 10 | 7 | 3 | `-O3` | 6.01× |
| Full (GCC, first 30) | 30 | 30 | 0 | `-O1 -mcpu=native -fno-tree-vectorize` | 4.03× |

The discrepancy between the smoke-test speedup (5.47×) and the calibration speedup (5.20×) for GCC reflects the different iteration counts and repetition counts between phases, which affect timing resolution and noise. Direct cross-phase speedup comparisons should be made cautiously.

## Limitations

1. **Synthetic benchmark.** The workload (`kernel_mix.c`) is a constructed microbenchmark, not a real application. Speedups observed here do not generalize to other workloads, and the ranking of flag combinations may differ substantially for production code.

2. **Simple search policy.** The current agent uses enumeration of hand-picked or ordered candidates. It does not employ Bayesian optimization, genetic search, learned policies, or any adaptive strategy. Scaling to large flag spaces would require a more sophisticated search policy.

3. **Timing methodology.** Medians over repeated runs provide some noise reduction but fall short of rigorous benchmarking practice. No CPU core isolation, frequency pinning, or statistical confidence intervals were applied. The reported speedups should be treated as indicative rather than precise.

4. **Strict checksum equivalence.** The correctness gate requires bit-exact output matching the `-O0` baseline. This is conservative: it rejects `-Ofast` and related flags that may produce numerically different but practically acceptable results. Workloads with tolerance-based validation criteria would likely find different optimal candidates.

5. **Single-host evaluation.** All results are from one aarch64 host with specific core microarchitectures and compiler versions. Portability of the observed rankings is unknown.

6. **Enumeration ordering bias.** The throughput sweep's first-30 enumeration is ordered by optimization level, which means it does not explore the full flag space uniformly. The best candidate found in that sweep is not the best candidate overall.

7. **No cross-validation with real workloads.** The agent has not been tested against any real compilation target. Whether the checksum gate and ranking survive on production codebases remains an open question.

## Reproducibility Checklist

- **Source code available:** `benchmarks/kernel_mix.c`, `src/flag_search_agent.py`, `src/summarize_results.py` are present in the project directory.
- **Command lines recorded:** Exact command lines for all four phases are documented in the run notes.
- **Environment logged:** `logs/environment_20260502T192434Z.log` records host, CPU, compiler versions, and memory state.
- **Raw evidence preserved:** JSONL logs for all phases (`smoke`, `calibrate_gcc`, `calibrate_clang`, `full_gcc30`) are available with per-candidate compile times, run times, checksums, and memory snapshots.
- **System metrics preserved:** `/usr/bin/time -v` output logs for all phases record wall-clock time, max RSS, and swap counts.
- **Summarized results:** `artifacts/result_summary.json` and `artifacts/run_metrics.json` provide aggregated views.
- **Decision rationale:** `.omx/project_decision.json` records the viability decision, confidence level, observed constraints, and limitations.
- **Random seeds:** The benchmark workload is deterministic; no random seeds are involved.
- **Compiler versions specified:** GCC 13.3.0 (Ubuntu), Clang 18.1.3 (1ubuntu1).
- **Hardware specified:** aarch64, Cortex-X925 + Cortex-A725, 20 cores, ~122 GB RAM, zero swap.
- **Caveat:** CPU isolation and frequency pinning were not applied, so exact timing reproduction on different runs or hosts may vary.

## Conclusion

A stdlib-only local compiler flag search harness successfully compiled, executed, checksum-validated, and ranked GCC and Clang flag candidates on an aarch64 host. The agent found speedups of 5.20× (GCC, `-O3 -mcpu=native -flto`) and 6.01× (Clang, `-O3`) over the `-O0` baseline while correctly rejecting `-Ofast`-class candidates that violated strict checksum equivalence. The search completed with low memory usage and zero swap, and achieved a throughput of approximately 1.76 candidates per second in the broader enumeration phase.

These results establish that autonomous, correctness-gated compiler flag search is viable as a local prototype research tool on this class of host. They do not establish that the observed speedups generalize beyond the synthetic benchmark, that the search policy scales efficiently to large flag spaces, or that the timing methodology yields statistically rigorous rankings. The strict checksum gate, while effective at catching unsafe transformations, is conservative and may exclude practically acceptable flag combinations.

If this line of work continues, the most useful next step would be a two-stage search policy: a short successive-halving pass over a broad flag space to identify promising regions, followed by a longer confirmation pass on the top candidates with formal confidence intervals and optional CPU affinity. Broader scientific closure would require evaluation on real target workloads with domain-appropriate acceptance criteria for numerical equivalence.

---

## Referenced Artifacts

All artifacts reside under the project directory `<control-plane-projects>/source-record-redacted/`.

| Artifact | Path | Description |
|---|---|---|
| Run notes | `run_notes.md` | Narrative record of commands, results, and interpretation |
| Project decision | `.omx/project_decision.json` | Viability decision, confidence, constraints, best result |
| Environment log | `logs/environment_20260502T192434Z.log` | Host, CPU, compiler, and memory state at run time |
| Smoke test JSONL | `logs/smoke_20260502T192552Z.jsonl` | Per-candidate evidence from smoke phase |
| Smoke test time | `logs/smoke_20260502T192552Z.out` | `/usr/bin/time -v` output for smoke phase |
| GCC calibration JSONL | `logs/calibrate_gcc_20260502T192603Z.jsonl` | Per-candidate evidence from GCC calibration |
| GCC calibration time | `logs/calibrate_gcc_20260502T192603Z.out` | `/usr/bin/time -v` output for GCC calibration |
| Clang calibration JSONL | `logs/calibrate_clang_20260502T192621Z.jsonl` | Per-candidate evidence from Clang calibration |
| Clang calibration time | `logs/calibrate_clang_20260502T192621Z.out` | `/usr/bin/time -v` output for Clang calibration |
| GCC throughput JSONL | `logs/full_gcc30_20260502T192635Z.jsonl` | Per-candidate evidence from 30-candidate sweep |
| GCC throughput time | `logs/full_gcc30_20260502T192635Z.out` | `/usr/bin/time -v` output for throughput sweep |
| Result summary | `artifacts/result_summary.json` | Aggregated summary across all phases |
| Run metrics | `artifacts/run_metrics.json` | Wall-clock, RSS, and swap metrics per phase |
| Benchmark source | `benchmarks/kernel_mix.c` | Synthetic mixed scalar/vector C workload |
| Agent source | `src/flag_search_agent.py` | Stdlib-only search harness |
| Summarizer source | `src/summarize_results.py` | JSONL-to-summary aggregation script |
| Claim ledger | `papers/source-record-redacted-20260502T192357266375+0000/claim_ledger.json` | Claim audit record (empty at time of generation) |
| Evidence bundle | `papers/source-record-redacted-20260502T192357266375+0000/evidence_bundle.json` | Source and run ID linkage |
| Paper manifest | `papers/source-record-redacted-20260502T192357266375+0000/paper_manifest.json` | Generation metadata |
