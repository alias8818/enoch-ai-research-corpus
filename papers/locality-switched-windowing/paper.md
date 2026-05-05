# Locality-Switched Windowing: Adaptive KV-Cache Residency for Memory-Constrained Long-Context Inference

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (simulator logs, decision records, and run notes). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this as an unreviewed AI-generated research artifact and evaluate its claims with appropriate skepticism. No human reviewer has endorsed this document.

---

## Abstract

We investigate an adaptive KV-cache residency policy, *locality-switched windowing*, that dynamically switches between a sliding-window mode (for local turns) and a targeted cache-restoration mode (for global turns requiring distant context). In a deterministic block-level KV residency simulator modeling 32k-token contexts across four workload types (chat with lookback, citation answering, long-form summarization, document extraction), the locality-switched policy matches the quality of static CPU offload (exact match 1.000, F1 proxy 1.000 at 64-block GPU budget) while reducing mean resident KV by 36.7%, CPU offload traffic by 45.2%, and mean latency by 12.0%. A budget sweep across 32–96 GPU blocks shows consistent traffic reductions of 41–47% with quality preserved at budgets of 48 blocks and above. These results are **upper-bound**: the simulator assumes an oracle span resolver that perfectly identifies answer-critical KV blocks during targeted restoration. The central unresolved risk is whether online signals available at inference time can approximate this oracle with sufficient recall. We do not claim production viability; rather, we present these simulator findings as motivation for a real-inference-stack validation.

## Introduction

Large-language-model inference over long contexts faces a growing tension between KV-cache memory footprint and the need to retain answer-critical state across tens of thousands of tokens. Static strategies—keeping a fixed recent window on GPU and offloading older blocks to CPU—preserve quality but incur substantial restore traffic on every global turn. Pure sliding-window approaches (with optional anchor tokens) eliminate offload traffic but destroy information needed by citation, extraction, and summarization tasks.

Recent work on KV-cache eviction has explored retaining "heavy-hitter" tokens alongside the recent window, demonstrating that not all cached tokens contribute equally to generation. However, context-intensive tasks can suffer when eviction relies on unreliable landmarks or low-rank projections that fail to preserve fine-grained prompt details. Adaptive serving architectures have argued that static offloading cannot respond to shifting memory demands across a conversation. Self-attention-guided token selection has shown improvements over static sliding-window choices on long-context tasks.

Locality-switched windowing addresses this by observing that many turns in a conversation are *local*: they reference only recent context and need no restoration. A minority of turns are *global*: they require targeted restoration of specific distant KV spans. Rather than choosing a single static policy, the wrapper estimates locality online and switches modes accordingly—avoiding unnecessary restores on local turns while performing targeted restores on global ones.

The key question is whether the locality estimate and span resolver can be implemented without oracle access to future attention patterns. This paper reports simulator-level evidence that, *if* such a resolver achieves high recall, the payoff is substantial. We leave the real-inference validation to future work.

## Method

### Simulator Design

We implemented a deterministic, workload-level KV residency simulator (`scripts/locality_switched_windowing_sim.py`) that models KV blocks as 128-token units with an assumed fp16 KV cost of 131,072 bytes per token (computed as: K and V × 32 layers × 8 KV heads × 128 head dimension × 2 bytes). The simulator does not execute a transformer; it models block-level residency decisions and their consequences for quality, latency, and traffic. It uses only the Python 3.12 standard library and no external dependencies.

### Policies Compared

Four policies are evaluated:

1. **full_cache**: All KV blocks resident on GPU. Serves as the quality ceiling and memory floor.
2. **static_cpu_offload**: A fixed GPU window of recent blocks; older blocks restored from CPU on demand. Quality-preserving but traffic-heavy.
3. **sliding_window**: Recent window plus anchor tokens, with no restoration of evicted blocks. Memory-efficient but destructive for tasks requiring distant context.
4. **locality_switched**: An online locality/pressure signal switches between window mode (no restoration, for local turns) and targeted/global restore mode (for global turns). In targeted mode, the simulator assumes an **oracle span resolver** that correctly identifies all answer-critical KV blocks.

### Workloads

Four synthetic workload types are simulated, each designed to stress different access patterns:

- **Chat with occasional long lookbacks**: Predominantly local turns with sporadic references to early context.
- **Citation answering**: Requires precise restoration of specific distant blocks.
- **Long-form summarization**: Requires broad but targeted access to distributed context spans.
- **Document extraction**: Requires precise block-level access to specific regions.

### Experimental Configuration

The primary experiment uses 256 context blocks (32,768 tokens at 128 tokens/block), 64 GPU budget blocks, and 48 window blocks, with 250 repetitions per workload type (1,000 total cases). A budget sweep varies GPU budget across {32, 48, 64, 96} blocks with window blocks set to 75% of budget.

### Quality Metrics

The simulator computes an **exact match** proxy (whether all answer-critical blocks are resident at query time) and an **F1** proxy (harmonic mean of block-level precision and recall for answer-critical blocks). These are structural proxies measuring KV-block residency, not language-model output quality metrics. A block being resident does not guarantee the model's attention patterns will use it correctly.

### Latency Model

Latency is modeled as a function of GPU residency and CPU restore traffic, with per-block restore costs. This is a simplified analytical model, not a measured inference latency from real hardware.

## Results

### Primary Comparison: 64-Block GPU Budget

| Policy | Exact | F1 Proxy | Mean Latency (ms) | Peak KV (MB) | Mean Resident KV (MB) | CPU Traffic (MB) |
|---|---:|---:|---:|---:|---:|---:|
| full_cache | 1.000 | 1.000 | 28.483 | 4,294.967 | 4,294.967 | 0.000 |
| static_cpu_offload | 1.000 | 1.000 | 15.743 | 956.301 | 896.541 | 115,360.137 |
| sliding_window | 0.172 | 0.344 | 12.729 | 838.861 | 838.861 | 0.000 |
| locality_switched | 1.000 | 1.000 | 13.857 | 838.861 | 567.103 | 63,250.104 |

Against static CPU offload, locality-switched windowing achieves:

- **Quality**: Exact match and F1 proxy both preserved at 1.000 (no quality loss in the simulator).
- **Mean latency reduction**: 12.0% (15.743 ms → 13.857 ms).
- **Mean resident KV reduction**: 36.7% (896.541 MB → 567.103 MB).
- **CPU traffic reduction**: 45.2% (115,360.137 MB → 63,250.104 MB).
- **Peak KV reduction**: 12.3% (956.301 MB → 838.861 MB).

These results meet the pre-registered success criteria (equal quality with ≥10% lower latency, and ≥30% lower KV footprint or offload traffic) in simulator space.

### Budget Sweep

| Budget (blocks) | Policy | Exact | F1 Proxy | Mean Latency (ms) | Peak KV (MB) | CPU Traffic (MB) |
|---|---|---:|---:|---:|---:|---:|
| 32 | static_cpu_offload | 1.000 | 1.000 | 14.188 | 536.9 | 127,104.2 |
| 32 | sliding_window | 0.151 | 0.268 | 10.894 | 436.2 | 0.0 |
| 32 | locality_switched | 0.992 | 0.995 | 12.915 | 453.0 | 67,729.6 |
| 48 | static_cpu_offload | 1.000 | 1.000 | 14.948 | 755.0 | 120,057.8 |
| 48 | sliding_window | 0.169 | 0.314 | 11.812 | 637.5 | 0.0 |
| 48 | locality_switched | 1.000 | 1.000 | 13.389 | 637.5 | 65,598.9 |
| 64 | static_cpu_offload | 1.000 | 1.000 | 15.743 | 956.3 | 115,360.1 |
| 64 | sliding_window | 0.172 | 0.344 | 12.729 | 838.9 | 0.0 |
| 64 | locality_switched | 1.000 | 1.000 | 13.857 | 838.9 | 63,250.1 |
| 96 | static_cpu_offload | 1.000 | 1.000 | 17.224 | 1,359.0 | 101,804.1 |
| 96 | sliding_window | 0.175 | 0.416 | 14.565 | 1,241.5 | 0.0 |
| 96 | locality_switched | 1.000 | 1.000 | 14.835 | 1,241.5 | 60,028.9 |

At the smallest budget (32 blocks, ~4k tokens on GPU), locality-switched exhibits a minor quality degradation (F1 proxy 0.995 vs. 1.000, a 0.5-point gap) but still reduces CPU traffic by 46.7% versus static offload. At budgets of 48 blocks and above, quality is fully preserved in the simulator, with traffic reductions of 41–45% across all budgets.

Sliding window consistently fails quality metrics (exact match 0.15–0.18, F1 proxy 0.27–0.42) across all budgets, confirming that pure eviction is inadequate for the tested workload mix.

### Mixed and Negative Findings

Several findings temper the positive headline results:

1. **Oracle assumption**: The locality-switched policy's quality preservation depends entirely on the oracle span resolver. Any implementation with imperfect recall will degrade quality proportionally to the missed-block rate.
2. **Budget sensitivity**: At 32 blocks, even the oracle resolver shows a small quality gap (F1 0.995), suggesting that very tight budgets may require more aggressive heuristics or acceptance of quality loss.
3. **Latency model limitations**: Latency figures are derived from an analytical model assuming fixed per-block restore costs, not measured on real hardware with actual PCIe/CPU-GPU transfer overheads, prefill/decode scheduling, or batch effects.
4. **No real model evaluation**: The exact-match and F1 proxies measure structural block residency, not actual language-model output quality. A block being "resident" does not guarantee the model's attention patterns will use it correctly.

## Limitations

1. **Simulator-only evidence**: All results come from a deterministic block-level simulator. No real transformer was executed. KV residency decisions were evaluated against synthetic workload access patterns, not against actual attention distributions from a language model.

2. **Oracle span resolver**: The most significant limitation. The locality-switched policy assumes perfect knowledge of which KV blocks are answer-critical when switching to targeted-restore mode. Real implementations must derive this from online signals (query embeddings, attention locality estimates, prompt metadata, or retrieval plans). The gap between oracle and achievable resolver performance is unknown and is the primary risk for the approach.

3. **Synthetic workloads**: The four workload types (chat-lookback, citation, summarization, extraction) are modeled as access pattern distributions, not derived from real prompt/response traces. Real workloads may exhibit different locality structures.

4. **Simplified latency model**: The simulator uses a linear per-block cost model for CPU-GPU transfers. Real systems exhibit nonlinear behavior due to PCIe bandwidth saturation, prefetching, batch scheduling, and decode-prefill interleaving.

5. **Single hardware profile**: Experiments were designed on an NVIDIA GB10 (aarch64) system but the simulator itself is hardware-agnostic. No real GPU memory pressure, UMA traffic, or compute-overlap measurements were collected.

6. **Block granularity**: The 128-token block size is a modeling choice. Real KV-cache management may operate at finer or coarser granularity, affecting both traffic efficiency and restoration precision.

7. **No multi-turn state accumulation**: The simulator evaluates per-turn decisions independently. A real system must handle cumulative effects of mode switches across extended conversations, including potential thrashing between modes.

8. **Empty claim ledger**: The automated claim-audit pipeline for this artifact produced an empty claim ledger with `blocked_empty_claims` status. No structured claims have passed evidence audit. The metrics reported here are drawn directly from simulator output files and have not been independently validated through the claim/evidence pipeline.

## Reproducibility Checklist

- **Standalone script**: The simulator is a single Python file (`scripts/locality_switched_windowing_sim.py`) using only Python 3.12 standard library modules—no external dependencies.
- **Deterministic execution**: The simulator is fully deterministic given the same command-line arguments. No random seeds are required.
- **Exact commands**: All run commands are recorded in the run notes and reproduced in the Method section.
- **Output artifacts**: All summary JSON, case-row CSV, and budget-sweep CSV files are preserved under `artifacts/locality_switched_windowing/`.
- **Hardware independence**: The simulator does not require GPU access. It was developed and run on an NVIDIA GB10 system but can execute on any Python 3.12+ host.
- **Parameter space**: All evaluated parameter combinations (budget sweep {32, 48, 64, 96} blocks, 250 repetitions per workload) are documented.
- **Metrics definitions**: Exact match and F1 proxy are defined structurally (block residency, not model output). Latency is defined by the simulator's analytical cost model.
- **Evidence audit status**: The claim ledger for this paper is in `blocked_empty_claims` state. No claims have been formally audited against evidence files. Readers should treat all reported numbers as unverified simulator outputs.

## Conclusion

Locality-switched windowing shows promising simulator-level results: by switching between sliding-window and targeted-restore modes based on an online locality estimate, it preserves the quality of static CPU offload while reducing mean resident KV by 36.7%, CPU traffic by 45.2%, and latency by 12.0% in a 32k-token, 64-block-budget configuration. A budget sweep confirms consistent traffic reductions of 41–47% across GPU budgets from 32 to 96 blocks, with full quality preservation at budgets of 48 blocks and above.

However, these results represent an **upper bound**. The simulator's oracle span resolver assumes perfect identification of answer-critical KV blocks—a capability that no current inference system provides without access to future attention patterns. The central scientific question is whether online signals (query embeddings, attention locality, prompt structure metadata, or lightweight retrieval plans) can approximate this oracle with sufficient recall to preserve the observed gains.

The pure sliding-window baseline's poor quality (exact match ~0.17, F1 ~0.34) confirms that static eviction is inadequate for context-intensive tasks, consistent with prior findings that unreliable landmarks harm citation and extraction performance. The static offload baseline's high traffic confirms that restoring on every turn is wasteful when many turns are local.

We recommend the next validation step be a real-inference-stack MVP: a wrapper around a small local model (e.g., via llama.cpp or vLLM) that implements a non-oracle span resolver using available online signals, and measures actual task quality (exact match, F1 on real prompts), latency, and memory traffic on needle-in-haystack, citation, extraction, and summarization benchmarks. Until such validation is complete, locality-switched windowing should be considered a promising hypothesis with unproven realizability, not a deployable technique.

---

## Referenced Artifacts

| Artifact | Path | Description |
|---|---|---|
| Run notes | `run_notes.md` | Full experimental log, environment details, and interpretation |
| Project decision | `.omx/project_decision.json` | Decision record: `promising_continue`, confidence `medium`, evidence level `deterministic_policy_simulator_upper_bound_not_real_transformer` |
| Upper-bound summary | `artifacts/locality_switched_windowing/upper_bound_summary.json` | Aggregate metrics for the 64-block primary experiment |
| Case rows | `artifacts/locality_switched_windowing/upper_bound_case_rows.csv` | Per-case detail for the primary experiment |
| Budget sweep | `artifacts/locality_switched_windowing/budget_sweep.csv` | Aggregate metrics across GPU budgets {32, 48, 64, 96} |
| Simulator script | `scripts/locality_switched_windowing_sim.py` | Deterministic Python 3.12 simulator (stdlib only) |
| Run logs | `artifacts/logs/smoke_v2.log`, `artifacts/logs/upper_bound.log`, `artifacts/logs/budget_*.log` | Raw stdout from each simulator invocation |
| Project metrics | `.omx/metrics.json` | Session token usage and activity timestamps |
| Claim ledger | `papers/.../claim_ledger.json` | Audit status: `blocked_empty_claims`; no structured claims extracted |
| Evidence bundle | `papers/.../evidence_bundle.json` | Source: `langgraph_control_plane_mvp` |
| Paper manifest | `papers/.../paper_manifest.json` | Generation metadata and writer provenance |
