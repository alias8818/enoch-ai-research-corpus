# Dual-Trace Memory Encoder: Compact Scene Anchors for Temporal Recall in Synthetic Memory Benchmarks

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present the Dual-Trace Memory Encoder, a memory-writing strategy that augments fact-only records with compact scene-anchor cues to improve temporal and contextual recall. In a deterministic synthetic writer-swap benchmark, an initial dual-trace writer achieved a +48.6 percentage-point accuracy gain over a fact-only baseline (77.7% vs. 29.1%) but violated a storage-overhead constraint (+108.8% overhead vs. the ≤10% target). A compressed variant that retains event facts plus a single scene cue anchor while eliminating duplicate scene fields and shortening source codes achieved a +41.2 percentage-point mean gain over fact-only across 10 seeds (3.1 pp stdev) at +5.5% mean storage overhead (0.2 pp stdev), satisfying both the ≥15-point accuracy-lift and ≤10% storage-overhead thresholds. A volume-matched fact-only control matched the baseline (29.1%), indicating the gain derives from the scene-anchor structure rather than memory volume alone. These results are confined to a synthetic, deterministic benchmark harness; external validity on real agent memory traces remains untested.

## 1. Introduction

Autonomous coding agents that operate across multiple sessions face a temporal recall problem: facts recorded in earlier sessions must be retrievable in later sessions, yet conventional fact-only memory records lack the contextual and temporal cues that queries often target. When a user asks "what changed after the refactoring step?" or "which version introduced the bug?", a flat fact store provides no scene-level anchor to match against such temporally grounded queries.

The Dual-Trace Memory Encoder proposes that each memory record carry two traces: the event fact itself and a compact scene-anchor cue encoding the situational context in which the fact was recorded. The hypothesis is that scene anchors improve retrieval accuracy on temporal, update-tracking, and aggregation questions without imposing prohibitive storage overhead.

This report documents a controlled writer-swap experiment: the memory writer is varied (fact-only, volume-matched fact-only, uncompressed dual-trace, compressed dual-trace) while the retrieval, search, and answer-extraction components remain fixed. The experiment is synthetic and deterministic; it tests mechanism viability rather than real-world performance.

## 2. Method

### 2.1 Benchmark Design

A minimal local benchmark harness (`scripts/dual_trace_memory_benchmark.py`) was constructed to isolate the effect of the memory writer. The harness generates synthetic multi-session event sequences, writes memory records using one of four writer conditions, then evaluates retrieval accuracy on three question categories: temporal ordering, update tracking, and aggregation.

The four writer conditions are:

1. **Fact-only**: Records contain only the event fact fields.
2. **Volume-matched fact-only**: Fact-only records padded to match the character count of the uncompressed dual-trace condition, controlling for memory volume.
3. **Uncompressed dual-trace**: Records contain event fact fields plus full scene fields (source, session context, temporal markers).
4. **Compressed dual-trace**: Records contain event fact fields plus a single scene cue anchor; duplicate scene fields are removed and the source identifier is shortened to a one-character code.

Retrieval (search and ranking) and answer extraction are identical across all conditions. Only the writer varies.

### 2.2 Success Criteria

Two thresholds were defined prior to the compressed iteration:

- **Accuracy lift**: ≥15 percentage points over the fact-only baseline.
- **Storage overhead**: ≤10% increase in total stored characters relative to the fact-only condition.

Both criteria must be satisfied simultaneously.

### 2.3 Evaluation Protocol

Single-seed evaluation used seed 343. Multi-seed evaluation used seeds 340 through 349 (10 seeds). For each seed, the harness generates the same event sequences deterministically, writes records under each condition, runs retrieval, and computes accuracy as the fraction of questions answered correctly. Storage overhead is computed as the percentage increase in total stored characters relative to the fact-only condition for the same seed.

## 3. Results

### 3.1 Uncompressed Dual-Trace (Initial Iteration)

| Condition | Accuracy (seed 343) | Storage Overhead |
|---|---|---|
| Fact-only | 29.1% | baseline |
| Volume-matched fact-only | 29.1% | matched to uncompressed dual-trace |
| Uncompressed dual-trace | 77.7% | +108.8% |

The uncompressed dual-trace writer produced a +48.6 percentage-point accuracy gain over fact-only. The volume-matched fact-only control scored identically to the plain fact-only baseline (29.1%), ruling out memory volume as the source of the gain. However, the +108.8% storage overhead far exceeded the ≤10% constraint. The evidence at this stage was therefore **mixed**: the scene-anchor mechanism improved recall substantially, but compactness was unresolved.

Multi-seed results (seeds 340–349) for the uncompressed variant showed a mean gain of +48.4 percentage points (stdev 2.7 pp), consistent with the single-seed finding.

### 3.2 Compressed Dual-Trace (Second Iteration)

| Condition | Accuracy (seed 343) | Storage Overhead |
|---|---|---|
| Fact-only | 29.1% | baseline |
| Volume-matched fact-only | 29.1% | matched to uncompressed dual-trace |
| Compressed dual-trace | 68.2% | +5.4% |

The compressed dual-trace writer achieved a +39.1 percentage-point gain at +5.4% storage overhead on seed 343.

| Metric | Mean (10 seeds) | Stdev |
|---|---|---|
| Accuracy gain (compressed dual − fact-only) | +41.2 pp | 3.1 pp |
| Storage overhead | +5.5% | 0.2% |

Across 10 seeds, the compressed dual-trace writer satisfied both success criteria: the mean accuracy gain of +41.2 pp exceeded the 15-point threshold, and the mean storage overhead of +5.5% remained within the 10% budget. Storage overhead was stable across seeds (0.2 pp stdev).

### 3.3 Accuracy–Compression Tradeoff

Compression reduced the accuracy gain from +48.6 pp (uncompressed) to +39.1 pp (seed 343), a cost of approximately 9.5 percentage points. This tradeoff brought storage overhead from +108.8% down to +5.4%, a roughly 20× reduction in overhead for a ~20% relative reduction in accuracy gain. Whether this tradeoff is favorable depends on deployment constraints; under the stated criteria, the compressed variant is the only condition that satisfies both thresholds simultaneously.

## 4. Limitations

1. **Synthetic benchmark only.** The harness generates deterministic synthetic event sequences and questions. No real coding-agent memory traces, real user queries, or production retrieval systems were tested. External validity is unknown.

2. **Single benchmark harness.** All results come from one script (`scripts/dual_trace_memory_benchmark.py`) with a fixed retrieval and answer-extraction pipeline. The observed gains may be sensitive to the specific question types (temporal, update-tracking, aggregation) and may not generalize to other query distributions.

3. **No real-world storage system.** Storage overhead is measured in character count of written records. Actual storage costs in a production vector database or key-value store may differ due to indexing, compression at the storage layer, or embedding dimension changes.

4. **Moderate confidence.** The project decision records confidence as "medium" and evidence strength as "moderate." The hypothesis is supported in the tested setting but has not been validated externally.

5. **Uncompressed variant failed the storage constraint.** The initial dual-trace design, while achieving higher accuracy, was infeasible under the storage budget. The compressed variant resolves this but at reduced accuracy. The Pareto frontier between accuracy and storage has not been fully characterized.

6. **No ablation of individual compression choices.** The compressed writer simultaneously removes duplicate scene fields and shortens source codes. The relative contribution of each compression step to the accuracy–overhead tradeoff was not measured.

7. **Deterministic evaluation.** The benchmark is fully deterministic given a seed. While this aids reproducibility, it means the variance across seeds reflects only the effect of seed-dependent event generation, not stochastic retrieval or model inference noise.

## 5. Reproducibility Checklist

- **Code available:** `scripts/dual_trace_memory_benchmark.py` (compiles cleanly per `py_compile` verification).
- **Deterministic:** Given a seed, the benchmark produces identical results across runs.
- **Seeds reported:** Single seed 343; multi-seed range 340–349.
- **Metrics defined:** Accuracy = fraction of questions answered correctly; storage overhead = percentage increase in total stored characters vs. fact-only.
- **Success criteria pre-registered:** ≥15 pp accuracy gain and ≤10% storage overhead, defined before the compressed iteration.
- **Negative/mixed results reported:** The uncompressed dual-trace condition violated the storage constraint; this is reported explicitly.
- **Volume control included:** Volume-matched fact-only condition isolates the scene-anchor mechanism from raw memory volume.
- **Result files:** `results/dual_trace_memory_benchmark.json` (single-seed), `results/dual_trace_memory_benchmark_multiseed.json` (10-seed), `results/dual_trace_memory_benchmark.md` (summary report).

## 6. Conclusion

The Dual-Trace Memory Encoder's compressed-scene variant achieved a +41.2 percentage-point mean accuracy gain over a fact-only baseline at +5.5% mean storage overhead in a deterministic synthetic writer-swap benchmark across 10 seeds, satisfying both pre-registered success criteria. A volume-matched control confirmed that the gain derives from the scene-anchor structure rather than increased memory volume. The uncompressed variant achieved higher accuracy (+48.6 pp) but at prohibitive storage cost (+108.8% overhead), illustrating a clear accuracy–compression tradeoff.

These findings support the viability of the scene-anchor mechanism within the tested synthetic setting. The primary remaining risk is external validity: the benchmark is deterministic and synthetic, and the next scientifically distinct validation step would test the compressed writer on real coding-agent memory traces. Until such validation is performed, the results should be interpreted as mechanism-level evidence rather than a deployment-ready claim.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Benchmark script | `scripts/dual_trace_memory_benchmark.py` |
| Single-seed results | `results/dual_trace_memory_benchmark.json` |
| Multi-seed results | `results/dual_trace_memory_benchmark_multiseed.json` |
| Benchmark report | `results/dual_trace_memory_benchmark.md` |
| Project decision | `.omx/project_decision.json` |
| Evidence bundle | `papers/source-record-redacted/evidence_bundle.json` |
| Claim ledger | `papers/source-record-redacted/claim_ledger.json` |
| Publication manifest | `papers/source-record-redacted/publication/publication_manifest.json` |
| Metrics | `.omx/metrics.json` |
