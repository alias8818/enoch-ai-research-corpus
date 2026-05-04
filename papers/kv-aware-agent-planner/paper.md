# KV-Aware Admission Planning for Memory-Bound Long-Context LLM Agent Workloads

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision records, metrics JSON, and evidence bundles). The operator who released the artifact claims no personal authorship credit for the writing or the results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

Long-context LLM agent workloads impose substantial KV-cache memory pressure on unified-memory-architecture (UMA) systems where swap is disabled. We evaluate three job-admission strategies—fixed-concurrency, prompt-token-cap, and KV-aware—for scheduling mixed agent calls under a strict memory envelope on an NVIDIA GB10-class machine (~117 GiB available, no swap, earlyoom active). Using a deterministic, reproducible simulation parameterized for a Llama-3-70B-class GQA model profile (327,680 bytes KV per token), we run three 250-job workloads across different random seeds. The KV-aware planner completes 97.6% of submitted jobs (244/250 average) with zero simulated late out-of-memory events, compared to 70.1% for fixed-concurrency and 71.6% for prompt-token-cap. However, KV-aware admission incurs substantially higher queueing latency (mean 150.9 s, P95 1140.6 s) versus fixed-concurrency (mean 14.9 s, P95 58.4 s). These results suggest KV-aware admission is viable as a memory-safety gate for agent dispatch on memory-constrained UMA systems, but it is not a complete performance optimizer. The latency cost demands complementary mechanisms—priority aging, context compaction, and model-tier routing—before production deployment. All results derive from a resource simulation; live inference runtime validation remains necessary.

## Introduction

LLM-based agents routinely issue calls with large prompt contexts, tool-returned context, and generous output token budgets. On systems with unified memory and no swap, the KV cache for such calls can grow to dominate memory consumption, making KV-cache size a first-order scheduling constraint rather than a secondary concern.

The NVIDIA GB10 platform exemplifies this constraint: it provides a large but finite memory pool (~117 GiB available), runs with swap disabled, and operates under earlyoom to protect system stability. When an inference runtime oversubscribes memory, the result is either an out-of-memory kill or uncontrolled degradation of service. A job-admission planner that accounts for KV-cache growth before dispatching a call could prevent such events—but at the cost of increased queueing latency for jobs that cannot be immediately admitted.

This paper evaluates a specific question: can a KV-aware admission planner prevent memory oversubscription for mixed agent workloads while preserving a useful amount of throughput, compared to naive admission strategies?

We compare three strategies:

1. **Fixed-concurrency**: admits up to 8 concurrent jobs without any memory guard.
2. **Prompt-token-cap**: admits jobs based on prompt and tool-context token counts, ignoring output-budget KV growth.
3. **KV-aware**: admits jobs only when model weights, runtime overhead, and the maximum live KV reservation for all admitted jobs fit within a conservative memory envelope.

We implement these as a deterministic, stdlib-only Python simulation and evaluate on three 250-job workloads. We report completed jobs, rejection/OOM counts, throughput, latency, and peak memory utilization.

## Method

### Simulator Design

The simulation artifact (`kv_aware_planner.py`) models a stream of agent LLM calls arriving at a scheduler. Each job is characterized by:

- **Prompt tokens**: tokens in the initial prompt.
- **Tool-context tokens**: tokens injected by tool outputs during the call.
- **Output budget**: maximum tokens the model may generate.
- **Actual output length**: realized output tokens (sampled at job creation).

The simulator processes jobs in arrival order. For each job, the admission policy determines whether to admit it immediately, queue it, or reject it. Admitted jobs occupy memory for their full lifetime (prefill through last output token). Memory is released when the job completes.

### Model Profile

The simulation uses an explicit Llama-3-70B-class GQA approximation with the following parameters:

| Parameter | Value |
|---|---|
| Layers | 80 |
| KV heads | 8 |
| Head dimension | 128 |
| KV dtype | fp16/bf16 (2 bytes) |
| KV bytes per token | 2 × 80 × 8 × 128 × 2 = 327,680 |
| Approximate quantized weights | 42 GiB |
| Runtime overhead | 8 GiB |

The KV bytes-per-token figure of 327,680 (320 KiB) means a single 32,768-token context reserves approximately 10 GiB of KV cache alone. This makes KV cache a dominant memory term for long-context calls.

### Memory Envelope

The safe memory envelope is computed as:

```
safe_envelope = MemAvailable × reserve_fraction
```

where `MemAvailable` ≈ 116–117 GiB (observed during runs) and `reserve_fraction` = 0.82. This yields a safe envelope of approximately 95–96 GiB. The 0.82 reserve fraction accounts for the swap-disabled, earlyoom-active posture of the target platform: the planner must stay conservatively below physical availability because there is no swap to absorb transient overshoot.

### Admission Policies

**Fixed-concurrency.** Admits up to 8 concurrent jobs regardless of memory impact. Jobs that would exceed the concurrency limit are queued. No memory check is performed; if actual memory exceeds physical availability, the simulator records a late OOM event.

**Prompt-token-cap.** Estimates memory usage from prompt + tool-context tokens only, ignoring the KV growth from the output budget. Admits a job if the estimated total (weights + overhead + prompt/tool KV for all live jobs) fits the envelope. This policy captures the common mistake of accounting only for input context.

**KV-aware.** Estimates memory usage from the full maximum KV reservation: prompt tokens + tool-context tokens + output budget for each live job. Admits a job only if weights + overhead + maximum live KV for all admitted and candidate jobs fits the envelope. Jobs that cannot ever fit the envelope (even with no other jobs running) are rejected permanently.

### Workload Generation

Each workload generates 250 jobs with stochastic prompt lengths, tool-context sizes, output budgets, and actual output lengths. An arrival-rate parameter controls inter-arrival spacing. We use three seeds (34, 35, 36) with arrival rate 0.45 to produce three independent workloads.

### Host Environment

All runs executed on an NVIDIA GB10 / aarch64 system running Ubuntu kernel 6.17.0-1014-nvidia. Key posture facts:

- `MemAvailable`: ~116–117 GiB during runs.
- `SwapTotal`: 0 B (swap disabled).
- `earlyoom`: active.
- `nvidia-smi`: reports GB10 present but does not expose UMA memory usage on this platform.

### Execution

The following commands produced the reported artifacts:

```bash
python3 kv_aware_planner.py --jobs 20 --seed 1 --arrival-rate 0.3 --out artifacts/smoke_metrics.json
python3 kv_aware_planner.py --jobs 250 --seed 34 --arrival-rate 0.45 --out artifacts/kv_planner_metrics_seed34.json
python3 kv_aware_planner.py --jobs 250 --seed 35 --arrival-rate 0.45 --out artifacts/kv_planner_metrics_seed35.json
python3 kv_aware_planner.py --jobs 250 --seed 36 --arrival-rate 0.45 --out artifacts/kv_planner_metrics_seed36.json
```

A syntax check (`python3 -m py_compile kv_aware_planner.py`) passed without errors.

## Results

### Aggregate Metrics (3 × 250-job workloads, seeds 34–36)

| Metric | Fixed-concurrency | Prompt-token-cap | KV-aware |
|---|---:|---:|---:|
| Jobs completed | 175.3 | 179.0 | 244.0 |
| Jobs rejected or OOM | 74.7 | 71.0 | 6.0 |
| Throughput (jobs/min) | 16.75 | 8.78 | 6.37 |
| Mean latency (s) | 14.94 | 49.42 | 150.93 |
| P95 latency (s) | 58.36 | 331.88 | 1140.56 |
| Peak actual total (GiB) | 95.87 | 95.88 | 92.95 |
| Peak reserved total (GiB) | 50.00 | 94.65 | 95.89 |
| Makespan (s) | 629.45 | 1245.99 | 2340.48 |

### Completion Rate

The KV-aware planner completes 97.6% of submitted jobs on average (244/250), rejecting only 6 jobs whose maximum KV reservation cannot fit the envelope even in isolation. Fixed-concurrency and prompt-token-cap complete approximately 70.1% and 71.6% of jobs respectively, with the remainder either rejected or suffering simulated late OOM.

### Memory Safety

The KV-aware planner's peak actual total memory (92.95 GiB) stays below the safe envelope (~95–96 GiB), consistent with its admission logic. Fixed-concurrency and prompt-token-cap both reach peak actual totals of ~95.87–95.88 GiB, which is at or above the envelope boundary. Their apparently higher throughput is misleading: many of the "completed" jobs under those policies would have triggered OOM on a real system without swap. The fixed-concurrency planner's peak reserved total of only 50.00 GiB reflects the fact that it performs no memory reservation at all—actual memory grows uncontrolled beyond what the policy tracks.

### Throughput and Latency Trade-off

The KV-aware planner's throughput (6.37 jobs/min) is the lowest of the three strategies, and its mean latency (150.93 s) and P95 latency (1140.56 s) are substantially higher. This is the direct cost of conservative admission: long-context jobs spend significant time queued until sufficient memory is released by completing jobs. The naive planners appear faster only because they drop or OOM the large-context jobs that create the most queueing pressure. The prompt-token-cap planner occupies an intermediate position: its latency is worse than fixed-concurrency but better than KV-aware, yet it still fails to prevent memory overshoot because it ignores output-budget KV growth.

### Prompt-Token-Cap Insufficiency

The prompt-token-cap policy, which ignores output-budget KV growth, still suffers ~71 rejections/OOMs per run and reaches peak actual memory comparable to fixed-concurrency. This confirms that output-budget KV growth is a material contributor to memory pressure and cannot be safely ignored by an admission controller.

## Limitations

1. **Simulation, not live inference.** This study uses a deterministic resource simulation. No live vLLM, llama.cpp, or other inference runtime was benchmarked. The simulator's throughput and latency numbers derive from profile parameters (assumed decode/prefill rates), not from measured GB10 runtime performance. Real inference runtimes exhibit additional complexities—memory fragmentation, batching effects, speculative decoding—that the simulation does not capture.

2. **Unvalidated throughput constants.** The decode and prefill throughput assumptions embedded in the simulator are explicit parameters, not calibrated measurements from the GB10 host. Production deployment requires measuring actual token throughput on the target runtime and hardware.

3. **No semantic quality evaluation.** The simulator treats all completed jobs as equally valuable regardless of context length or output quality. Rejecting or queueing a long-context agent call may have disproportionate semantic impact compared to rejecting a short call. This trade-off was not measured.

4. **Synthetic workload.** Job arrival patterns, prompt lengths, tool-context sizes, and output budgets are generated stochastically. No real private agent traces were available. Production workloads may exhibit different distributions, burst patterns, or correlations between context size and priority.

5. **Single model profile.** Only one model profile (Llama-3-70B-class GQA) was evaluated. Different architectures, quantization levels, or KV sharing strategies would yield different bytes-per-token figures and different admission outcomes.

6. **No priority or aging mechanism.** The current KV-aware planner uses FIFO queuing. Long-context jobs that cannot be admitted may block indefinitely under sustained load. Production systems require priority aging, preemption, or context compaction to prevent starvation.

7. **No context compaction or summarization.** The planner treats each job's token budget as fixed. In practice, agents can summarize or truncate context to reduce KV footprint. Integrating such actions into the admission loop was outside the scope of this study.

8. **Limited seed coverage.** Three seeds provide a narrow view of stochastic variability. Confidence intervals on the reported averages are not computed; the aggregate figures should be interpreted as point estimates from a small sample of workload realizations.

## Reproducibility Checklist

- **Artifact available**: `kv_aware_planner.py` (stdlib-only Python, no external dependencies).
- **Deterministic**: All runs use explicit random seeds (1, 34, 35, 36). Re-running with the same seed and parameters produces identical output.
- **Command log preserved**: `logs/commands.log` records the exact execution environment and commands.
- **Output artifacts**: `artifacts/smoke_metrics.json`, `artifacts/kv_planner_metrics_seed34.json`, `artifacts/kv_planner_metrics_seed35.json`, `artifacts/kv_planner_metrics_seed36.json`, `artifacts/kv_planner_aggregate.json`.
- **Stdout captures**: `logs/kv_planner_seed*.stdout.json`.
- **Host environment documented**: Kernel version, MemAvailable, SwapTotal, earlyoom status recorded in run notes and command log.
- **Model profile explicit**: All KV bytes-per-token calculation steps are documented and verifiable.
- **Syntax check passed**: `python3 -m py_compile kv_aware_planner.py` completed without errors.
- **No external dependencies**: The simulator uses only Python standard library modules.

## Conclusion

KV-cache memory is a first-order scheduling constraint for long-context LLM agent workloads on memory-constrained UMA systems. In a deterministic simulation parameterized for a Llama-3-70B-class model on an NVIDIA GB10-class machine with ~117 GiB available memory and no swap, a KV-aware admission planner that accounts for full output-budget KV growth completes 97.6% of jobs with zero simulated late OOM events, compared to ~70–72% for naive admission strategies. The cost of this safety is substantially increased queueing latency (mean 150.9 s vs. 14.9 s for fixed-concurrency), particularly for long-context calls.

These results support proceeding with a KV-aware planner prototype as a memory-safety and resource-admission gate for agent dispatch. However, the result is bounded: the simulation does not validate live inference runtime behavior, actual throughput, or semantic quality impact. Production deployment requires (1) replaying real agent traces through the KV estimator and comparing predicted peak memory to runtime telemetry, (2) adding priority aging and context-compaction actions to prevent starvation of long-context jobs, and (3) a small live inference smoke test on the target runtime before committing to a full benchmark. The KV-aware planner should be understood as a necessary safety layer, not a sufficient performance optimizer.

---

## Referenced Artifacts

| Artifact | Description |
|---|---|
| `kv_aware_planner.py` | Simulator/planner source (stdlib-only Python) |
| `run_notes.md` | Research run notes with environment, commands, and interpretation |
| `artifacts/smoke_metrics.json` | 20-job smoke test metrics |
| `artifacts/kv_planner_metrics_seed34.json` | 250-job run, seed 34 |
| `artifacts/kv_planner_metrics_seed35.json` | 250-job run, seed 35 |
| `artifacts/kv_planner_metrics_seed36.json` | 250-job run, seed 36 |
| `artifacts/kv_planner_aggregate.json` | Aggregate table across seeds 34–36 |
| `logs/commands.log` | Command and environment capture |
| `logs/kv_planner_seed*.stdout.json` | Stdout captures for main runs |
| `.omx/project_decision.json` | Final decision record with evidence and limitations |
| `papers/.../claim_ledger.json` | Claim ledger (empty claims array; limitation note: model-authored draft) |
| `papers/.../evidence_bundle.json` | Evidence bundle linking to project and run IDs |
| `papers/.../paper_manifest.json` | Paper generation manifest with writer provider metadata |
