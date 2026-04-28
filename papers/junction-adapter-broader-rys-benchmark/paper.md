# Junction Adapter Broader RYS Benchmark: Multi-Model Evaluation Under Stricter Overfit Controls

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We report results from a broader multi-model benchmark of junction adapters—residual LoRA-style adapters applied only at junction-neighbor layers around a replayed layer interval—for reducing cross-entropy on locally cached language model corpora. Three model families were evaluated under a branch-specific kill condition requiring at least two model-family cells to achieve ≥5% held-out test cross-entropy (CE) improvement with a train/test CE gain ratio ≤4. After correcting an initial evaluation weakness (non-disjoint corpus splits), the final results under path-disjoint train/eval/test splits show model heterogeneity: GPT-2 achieves 27.19% held-out test CE improvement (gain ratio 1.21) and Qwen2.5-0.5B-Instruct achieves 20.35% (gain ratio 1.35), both passing the kill condition. However, OPT-125M achieves only 3.16% held-out test CE improvement (gain ratio 3.24), falling below the 5% threshold. The branch kill condition is not met because two cells pass, but the heterogeneity across model families tempers the strength of the overall signal. The project decision is `finalize_positive` with medium confidence and moderate evidence strength.

## 1. Introduction

Junction adapters are a parameter-efficient fine-tuning strategy that applies residual low-rank adapters only at the layers immediately adjacent to ("junction-neighbor" of) a replayed layer interval, rather than at every layer. The central hypothesis under test is whether this targeted adapter placement yields meaningful held-out cross-entropy improvements across multiple model families and corpora, with acceptable overfit characteristics as measured by the ratio of training CE gain to test CE gain.

This benchmark extends a prior single-model junction-adapter evaluation to a broader set of cached model families and corpora, with stricter controls designed to detect narrow or overfit signals. A branch-specific kill condition was defined *a priori*: at least two model-family cells must achieve ≥5% held-out test CE improvement with a train/test CE gain ratio ≤4, and the median held-out test CE gain across cells must be ≥5%. Failure of this condition would classify the junction-adapter signal as likely narrow or overfit.

## 2. Method

### 2.1 Junction Adapter Construction

Two benchmark runners were implemented:

**Manual repeated-block runner** (`broader_rys_benchmark.py`): Designed for GPT-2-family models with identifiable repeated transformer blocks. This runner selects a layer interval to replay and wraps only the junction-neighbor layers (those immediately adjacent to the replayed interval) with residual LoRA adapters.

**Generic expanded-ModuleList runner** (`generic_broader_rys_benchmark.py`): An architecture-tolerant variant that handles models with expanded `ModuleList` layer structures (e.g., OPT, Qwen families). It replays a layer interval and similarly wraps only junction-neighbor layers with residual LoRA adapters.

### 2.2 Corpus and Split Policy

Both runners perform broader local corpus discovery from cached text files. The split policy was revised during the benchmark after an initial weakness was identified:

- **Initial policy (first OPT-125M run):** Independent RNG token draws from a shared broader corpus. This was stricter than a train-only overfit check but weaker than path-disjoint splits, as the same underlying text files could contribute tokens to multiple splits.
- **Corrected policy (all final results):** Deterministic path-disjoint train/eval/test corpus splits. Distinct text files are assigned to each split, ensuring no document-level leakage. Split paths are recorded in each cell's dataset metadata.

### 2.3 Metrics

For each model-family cell, the following metrics are computed:

- **Held-out test CE improvement:** Percentage reduction in cross-entropy on the held-out test split after adapter training, relative to the unadapted baseline.
- **Eval CE improvement:** Percentage reduction on the eval split.
- **Train/test CE gain ratio:** Ratio of training-set CE improvement to test-set CE improvement. Values near 1.0 indicate proportional generalization; values well above 1.0 indicate overfitting to training data.

### 2.4 Kill Condition

The branch-specific kill condition requires:

1. At least two model-family cells achieve held-out test CE improvement ≥ 5%.
2. Each passing cell has a train/test CE gain ratio ≤ 4.
3. The median held-out test CE gain across all completed cells is ≥ 5%.

If fewer than two cells pass, or the median gain is below 5%, the broader junction-adapter signal is classified as likely narrow/overfit and the branch is killed.

## 3. Results

### 3.1 Completed Model-Family Cells

All results below use the corrected path-disjoint split policy and were run on CPU.

| Model Family | Runner | Held-Out Test CE Improvement | Eval CE Improvement | Train/Test Gain Ratio | Pass Kill Condition? |
|---|---|---|---|---|---|
| GPT-2 (124M) | Manual repeated-block | 27.19% | 26.82% | 1.2075 | Yes |
| facebook/opt-125m | Generic expanded-ModuleList | 3.16% | — | 3.2401 | No (below 5% threshold) |
| Qwen/Qwen2.5-0.5B-Instruct | Generic expanded-ModuleList | 20.35% | 13.76% | 1.3501 | Yes |

Two of three cells pass the kill condition. The median held-out test CE gain across the three cells is 20.35% (the median of {27.19, 3.16, 20.35}), which exceeds the 5% threshold. The branch kill condition is therefore not met.

### 3.2 Failed Cell: distilgpt2

An attempted distilgpt2 cell failed because the local cache lacked model weights (`pytorch_model.bin` / `model.safetensors`). An `--allow-download` attempt was terminated after several minutes with no observable progress. This cell is excluded from the kill condition evaluation.

### 3.3 Impact of Split Policy Correction on OPT-125M

The OPT-125M cell was initially evaluated under the non-disjoint RNG-draw policy, yielding a held-out test CE improvement of 12.86% with a train/test gain ratio of 1.17. After correction to path-disjoint splits, the held-out test CE improvement dropped to 3.16% with a gain ratio of 3.24. This substantial degradation under stricter evaluation constitutes a negative finding: the initial OPT-125M result was partially inflated by document-level leakage between splits. The corrected result falls below the 5% pass threshold.

### 3.4 Aggregate Summary

The aggregate benchmark summary was recomputed after the split correction and Qwen2.5-0.5B-Instruct addition. The completed cell statuses are: GPT-2 supported, OPT-125M mixed, Qwen2.5-0.5B-Instruct supported.

## 4. Limitations

1. **Small and heterogeneous model coverage.** Only three model families were successfully evaluated (124M, 125M, and 0.5B parameters). The distilgpt2 cell failed due to missing cached weights. Results may not generalize to larger models or different architectures.

2. **CPU-only execution.** All benchmarks ran on CPU with locally cached models and corpora. No GPU results are reported. Training dynamics and optimal hyperparameters may differ on GPU.

3. **Local corpus provenance.** Corpora were discovered from local cached text files. Their content, domain, and size distribution are not standardized benchmarks, limiting comparability with published work.

4. **Model heterogeneity under strict evaluation.** The OPT-125M result shifted from apparently supportive (12.86% test CE gain) to mixed (3.16%) when path-disjoint splits were enforced. This demonstrates that the junction-adapter signal is sensitive to evaluation methodology and varies across model families. The signal cannot be assumed uniform.

5. **No hyperparameter search.** Adapter rank, learning rate, number of training steps, and layer-interval selection were not systematically tuned per model. The reported results may under- or over-represent the achievable signal for any given model.

6. **Automated pipeline provenance.** This benchmark was executed and documented by an automated research pipeline. While all artifacts were verified (compilation, pytest, JSON parsing), no independent human replication has been performed.

7. **No external validation.** Results have not been replicated outside the originating environment. Claims are bounded to the project artifacts listed in the evidence bundle.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Code available in project artifacts | Yes: `scripts/hf_rys_junction_adapter.py`, `scripts/broader_rys_benchmark.py`, `scripts/generic_broader_rys_benchmark.py` |
| Tests available | Yes: `tests/test_hf_rys_junction_adapter.py`, `tests/test_broader_rys_benchmark.py` (6 tests passing) |
| Model identifiers specified | Yes: `gpt2`, `facebook/opt-125m`, `Qwen/Qwen2.5-0.5B-Instruct` |
| Split policy documented | Yes: path-disjoint train/eval/test (corrected from RNG-draw) |
| Metrics JSON artifacts recorded | Yes: see Referenced Artifacts |
| Run logs recorded | Yes: see Referenced Artifacts |
| Aggregate summary recomputed after correction | Yes: `artifacts/broader_rys_benchmark_aggregate_summary.json` |
| Compilation and test verification | Yes: `py_compile` passed; `pytest` 6 passed |
| Hardware specified | Partial: CPU only; specific CPU model not recorded in artifacts |
| Random seeds specified | Partial: deterministic path-disjoint splits; RNG seeds for training not explicitly recorded |
| External replication | No |

## 6. Conclusion

The broader junction-adapter benchmark under stricter overfit controls yields a mixed but net-positive result. Two of three model-family cells (GPT-2 and Qwen2.5-0.5B-Instruct) pass the pre-specified kill condition with substantial held-out test CE improvements (27.19% and 20.35%) and favorable train/test gain ratios (1.21 and 1.35). However, OPT-125M fails the 5% held-out test CE improvement threshold under path-disjoint splits, and its initial apparent success under weaker splits was an artifact of document-level leakage. This heterogeneity across model families is a substantive negative finding: the junction-adapter signal is not uniform and is sensitive to evaluation methodology.

The branch kill condition is not met (two cells pass; median gain 20.35%), supporting a `finalize_positive` decision with medium confidence. Future work should pursue a named full-suite public LM evaluation with standardized benchmarks, GPU execution, systematic hyperparameter search, and broader model coverage rather than additional generic successor branches.

## Referenced Artifacts

### Result files
- `artifacts/broader_rys_benchmark_summary.md`
- `artifacts/broader_rys_benchmark_aggregate_summary.json`
- `artifacts/broader_rys_benchmark_metrics.json`
- `artifacts/broader_rys_benchmark_run.log`
- `artifacts/generic_broader_rys_qwen05b_metrics.json`
- `artifacts/generic_broader_rys_qwen05b_run.log`
- `artifacts/generic_broader_rys_opt125m_cpu_metrics.json`
- `artifacts/generic_broader_rys_opt125m_cpu_run.log`
- `artifacts/generic_broader_rys_opt125m_metrics.json`
- `artifacts/generic_broader_rys_opt125m_run.log`
- `artifacts/broader_rys_benchmark_distilgpt2_run.log`

### Source and test files
- `scripts/hf_rys_junction_adapter.py`
- `scripts/broader_rys_benchmark.py`
- `scripts/generic_broader_rys_benchmark.py`
- `tests/test_hf_rys_junction_adapter.py`
- `tests/test_broader_rys_benchmark.py`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`
- `run_notes.md`

### Paper pipeline artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
