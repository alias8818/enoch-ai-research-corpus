# Real RYS Wall-Clock Throughput for Budget-Pruned Representation Seeding

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

We report wall-clock throughput measurements for budget-pruned representation seeding, a method that reduces the candidate interval set in transformer block scanning from exhaustive contiguous enumeration to a calibrated ~5% subset. On gpt2-medium with 10 text probes under CUDA float16, the calibrated budget-pruned candidate set (17 of 300 intervals, a 94.33% reduction) preserved full recall of all 45 blind winners identified by exhaustive search and reduced total scan time from 3.336 s to 0.203 s, yielding a 16.42× wall-clock speedup. Scoring-only speedup was 17.41×. These results are from a single warm-GPU run on one model and probe suite; broader replication is needed before generalizing.

## 1. Introduction

Transformer model analysis often requires scanning contiguous block intervals—subsets of sequential transformer layers—to identify intervals that maximize some scoring criterion. Exhaustive enumeration of all contiguous intervals in a model with $L$ layers produces $L(L+1)/2$ candidates, which grows quadratically and can become a throughput bottleneck for larger models or repeated evaluation.

Budget-pruned representation seeding addresses this bottleneck by using representation-level signals to pre-select a small candidate interval set, ideally preserving the high-scoring intervals ("winners") found by exhaustive search while dramatically reducing the number of forward passes required. Prior work in this project lineage established a calibrated 5% budget-pruned seed report for gpt2-medium and verified its recall against blind winners. The present branch asks whether this interval reduction translates into a real, end-to-end wall-clock speedup on the same model, probe set, and scoring harness—or whether overheads erode the theoretical gain.

The branch-specific kill condition was: finalize negative if scanning only the calibrated 5% candidate set does not produce a meaningful end-to-end wall-clock speedup over exhaustive contiguous block scanning on the same gpt2-medium probe harness, or if the speedup only appears by changing model, task, or scoring semantics between arms.

## 2. Method

### 2.1 Representation Seeding and Budget Pruning

Representation seeding uses activation-level statistics collected from a model to rank contiguous transformer-block intervals by their likelihood of containing high-scoring regions. Budget pruning then retains only the top fraction of these ranked intervals—here, approximately 5%—as the candidate set for full scoring. The calibration and seed-report generation were performed in the parent project; this branch inherits the calibrated seed report artifact (`results/gpt2_medium_seed_report_budget_pruned_calibrated.json`) without modification.

### 2.2 Wall-Clock Throughput Benchmark

A shared-harness benchmark (`scripts/benchmark_hf_block_scan_throughput.py`) was implemented to ensure that the two experimental arms differ only in their interval set:

- **Exhaustive arm:** Scores all 300 contiguous intervals of gpt2-medium (24 layers; intervals of length 1 through 24).
- **Budget-pruned arm:** Scores only the 17 intervals specified by the calibrated seed report.

Both arms share the same loaded model, tokenizer, probe set, scoring function, device, and dtype. Each arm includes its own baseline forward pass (to account for model-load and warm-up effects) followed by interval-scoring forward passes. The benchmark records per-arm wall-clock time after model load.

### 2.3 Recall Verification

A separate recall evaluation (`scripts/evaluate_seed_recall.py`) compares the budget-pruned candidate set against the blind winners from exhaustive search. The blind winners were computed independently in the parent project and stored in `results/gpt2_medium_block_winners.json`. The recall check verifies that no high-scoring interval is missed by the pruned set.

## 3. Results

### 3.1 Wall-Clock Throughput

All measurements were collected on gpt2-medium, 10 probes, CUDA float16, with 2 warmup intervals per arm and top-k = 20.

| Arm | Intervals scanned | Total scan time (s) | Interval reduction |
|---|---|---|---|
| Exhaustive | 300 | 3.336 | — |
| Budget-pruned | 17 | 0.203 | 94.33% |

- **Total scan speedup:** 16.42×
- **Scoring-only speedup:** 17.41×

The scoring-only speedup (which excludes the shared baseline forward pass) is close to the theoretical interval-count ratio of 300/17 ≈ 17.65×, indicating that per-interval scoring cost is approximately uniform and that overhead from the pruning step itself is negligible in this configuration.

### 3.2 Recall Preservation

| Metric | Value |
|---|---|
| Blind winner count | 45 |
| Full recall | 1.0 |
| Top-budget recall | 1.0 |
| Budget size | 17 |
| Missed winner count | 0 |

The budget-pruned candidate set recovered all 45 blind winners identified by exhaustive search. No high-scoring interval was missed.

### 3.3 Interpretation Relative to Kill Condition

The branch kill condition was not supported. On the same model, task, and scoring harness, the calibrated 5% representation-pruned candidate set preserved blind-winner recall and produced a real end-to-end wall-clock speedup close to the theoretical interval-count reduction.

## 4. Limitations

1. **Single model and probe suite.** All results are from gpt2-medium with 10 text probes. Generalization to other model families, sizes, or probe distributions is not established by the present artifacts.

2. **Single warm-GPU run.** The benchmark was executed once on a warm GPU. No cold-start timing, no repeated-trial variance estimation, and no multi-GPU or multi-machine replication were performed. Wall-clock numbers should be interpreted as point estimates, not as stable averages with confidence intervals.

3. **Prototype benchmark, not production validation.** The benchmark script is a research prototype exercising HuggingFace Transformers forward passes. It does not represent an optimized production inference pipeline, and results may differ under different serving frameworks, batch sizes, or concurrency regimes.

4. **Recall is specific to the blind-winner definition.** The 45 blind winners and the recall metric depend on the scoring function and top-k threshold used. Changing the scoring criterion or the definition of a "winner" could alter recall rates.

5. **No comparison to alternative pruning strategies.** This study compares only exhaustive search vs. one specific budget-pruned seed report. Random subsampling, uniform spacing, or other pruning heuristics were not evaluated, so the advantage of representation seeding over simpler pruning baselines is not measured here.

6. **Quadratic scaling not directly tested.** The 300-interval search space for gpt2-medium (24 layers) is modest. The practical benefit of budget pruning should increase with model depth, but this was not demonstrated empirically in the present artifacts.

## 5. Reproducibility Checklist

- **Model:** gpt2-medium (HuggingFace Transformers)
- **Device and dtype:** CUDA, float16
- **Probe set:** `data/probes.jsonl` (10 probes)
- **Seed report:** `results/gpt2_medium_seed_report_budget_pruned_calibrated.json`
- **Blind winners:** `results/gpt2_medium_block_winners.json`
- **Benchmark script:** `scripts/benchmark_hf_block_scan_throughput.py`
- **Recall script:** `scripts/evaluate_seed_recall.py`
- **Benchmark invocation:**
  ```
  .venv/bin/python scripts/benchmark_hf_block_scan_throughput.py \
    --model gpt2-medium \
    --probes data/probes.jsonl \
    --seed-report results/gpt2_medium_seed_report_budget_pruned_calibrated.json \
    --out results/gpt2_medium_wall_clock_throughput.json \
    --device cuda --dtype float16 \
    --warmup-intervals 2 --top-k 20
  ```
- **Recall invocation:**
  ```
  .venv/bin/python scripts/evaluate_seed_recall.py \
    --seed-report results/gpt2_medium_seed_report_budget_pruned_calibrated.json \
    --winners results/gpt2_medium_block_winners.json \
    --out results/gpt2_medium_block_winner_eval_budget_pruned_calibrated_rerun.json
  ```
- **Dependencies:** torch, transformers, numpy (installed via uv into a project-local .venv)
- **HF cache:** Local HuggingFace cache directory (HF_HOME and TRANSFORMERS_CACHE set explicitly)
- **Raw result files:** See Referenced Artifacts section below

## 6. Conclusion

On gpt2-medium with 10 probes under CUDA float16, budget-pruned representation seeding reduced the scanned interval set from 300 to 17 (94.33% reduction) while preserving full recall of all 45 blind winners. The corresponding wall-clock speedup was 16.42× for total scan time and 17.41× for scoring-only time. These findings support the utility of representation-seeded pruning for accelerating transformer block interval search in the tested setting. The main caveats are the single-model, single-run experimental design and the absence of comparison to simpler pruning baselines. Replication on additional model families, repeated timing runs with variance estimation, and comparison to alternative pruning strategies are recommended as follow-up work.

---

## Referenced Artifacts

### Result files
- `results/gpt2_medium_wall_clock_summary.json` — compact throughput summary
- `results/gpt2_medium_wall_clock_throughput.json` — raw per-arm wall-clock timing and top scored records
- `results/gpt2_medium_block_winner_eval_budget_pruned_calibrated_rerun.json` — recall verification (current directory)
- `results/gpt2_medium_budget_pruned_calibration.json` — calibration data
- `results/gpt2_medium_block_winner_eval_budget_pruned_calibrated.json` — original recall evaluation
- `results/gpt2_medium_block_winners.json` — blind winners from exhaustive search
- `results/gpt2_medium_seed_report_budget_pruned_calibrated.json` — calibrated 5% seed report

### Source and infrastructure files
- `scripts/benchmark_hf_block_scan_throughput.py` — shared-harness wall-clock benchmark
- `scripts/evaluate_seed_recall.py` — recall evaluation script
- `scripts/representation_seed.py` — representation seeding implementation
- `scripts/calibrate_multi_real_models.py` — multi-model calibration
- `scripts/compare_seed_reports.py` — seed report comparison utility
- `tests/test_representation_seed.py` — unit tests
- `data/probes.jsonl` — probe set (10 probes)
- `run_notes.md` — execution log and interpretation
- `.omx/project_decision.json` — project decision (finalize_positive)
- `.omx/metrics.json` — session metrics
- `.omx/project.json` — project metadata

### Paper audit artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
