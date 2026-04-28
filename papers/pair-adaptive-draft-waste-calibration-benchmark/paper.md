# Pair-Adaptive Draft Waste Calibration Benchmark

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

Speculative decoding systems attribute draft-token waste to multiple failure reasons (e.g., vocabulary mismatch, context divergence, length mismatch). Calibrating the relative importance of these reasons typically relies on either fixed synthetic priors or weights transferred from a different draft/target model pair. This paper evaluates whether a pair-adaptive calibration approach—learning per-pair reason weights from a small number of real speculative-decoding traces—recovers pair-specific reason rankings more accurately than non-adaptive baselines. Using a repeated stratified train/heldout benchmark across two real draft/target pairs with 500 random seeds, pair-adaptive calibration at k=4 traces per reason achieved mean Kendall τ = 0.790, mean top-3 overlap = 2.429/3, and mean MAE = 0.036. The best non-adaptive ranking baseline (fixed synthetic prior) yielded τ = −0.137 and top-3 overlap = 0.864/3; the best non-adaptive MAE baseline (full cross-pair real transfer) yielded MAE = 0.134. These results support the hypothesis that small pair-local trace samples recover pair-specific reason rankings substantially better than fixed or transferred weights, though the evaluation is limited to two model pairs and generalization remains unvalidated.

---

## 1. Introduction

Speculative decoding accelerates autoregressive inference by having a smaller draft model propose candidate tokens that a larger target model verifies in parallel. When the target model rejects draft tokens, the resulting waste can be attributed to distinct failure reasons. Understanding the relative contribution of each reason is valuable for prioritizing improvements to the draft model or the speculation strategy.

A central question is how to calibrate the weights assigned to each waste reason for a given draft/target pair. Three natural strategies present themselves: (1) use a fixed synthetic prior derived from analytical or heuristic arguments; (2) transfer weights estimated from one pair to another; or (3) learn pair-specific weights from real traces collected for the pair of interest. The third strategy—pair-adaptive calibration—requires collecting trace data, raising a sample-efficiency question: how many real traces per reason are needed before pair-adaptive weights outperform non-adaptive alternatives?

This paper reports a controlled benchmark evaluation of pair-adaptive calibration against non-adaptive baselines. The benchmark uses repeated stratified train/heldout splits on real speculative-decoding traces from two draft/target pairs, evaluating ranking agreement (Kendall τ), top-reason overlap, and mean absolute error (MAE) at multiple sample sizes. A pre-registered kill condition specified that the approach would be abandoned at k=4 traces per reason if pair-adaptive calibration failed to beat the best non-adaptive baseline by at least +0.25 Kendall τ or +1.0 top-3 overlap while also failing to reduce MAE.

---

## 2. Method

### 2.1 Problem Formulation

Let a draft/target pair produce speculative-decoding traces. Each trace records the waste reason for rejected draft tokens. The calibration task is to estimate a weight vector **w** over waste reasons that best explains the observed waste distribution. The quality of an estimated weight vector is assessed by three metrics computed against a held-out reference:

1. **Kendall τ**: Rank correlation between estimated and reference reason importance rankings.
2. **Top-3 overlap**: Count of reasons appearing in both the top-3 of the estimated and reference rankings (range 0–3).
3. **MAE**: Mean absolute error between estimated and reference weight vectors.

### 2.2 Calibration Methods Compared

The benchmark compares the following methods:

- **Pair-adaptive (small-sample)**: Learns per-pair reason weights from k real traces sampled from the same draft/target pair, using stratified train/heldout splits. Evaluated at k ∈ {2, 4, 8} traces per reason.
- **Fixed synthetic prior**: A non-adaptive baseline using analytically or heuristically derived weights that do not depend on real trace data from the specific pair.
- **Cross-pair real transfer**: A non-adaptive baseline that uses weights estimated from the full real-trace dataset of a different draft/target pair, transferred without adaptation.

### 2.3 Benchmark Design

The benchmark is implemented in `scripts/pair_adaptive_calibration_benchmark.py`, a dependency-free Python script. The design is as follows:

- **Data**: Real speculative-decoding traces from two draft/target pairs inherited from the parent project. One pair uses a standard configuration; the other involves Qwen1.5-3B as the draft model.
- **Evaluation protocol**: Repeated stratified train/heldout splits. For each seed, k traces per reason are sampled for training, and the remaining traces form the heldout reference.
- **Seeds**: 500 random seeds per (pair, k) configuration.
- **Metrics**: Kendall τ, top-3 overlap, and MAE, computed per split and then averaged across seeds and pairs.

### 2.4 Kill Condition

A branch-specific kill condition was defined prior to running the benchmark: at k=4 traces per reason, the pair-adaptive approach would be abandoned if it failed to beat the best non-adaptive baseline by at least +0.25 Kendall τ or +1.0 top-3 overlap **and** failed to reduce MAE. This condition ensures that the approach is only pursued if it provides a practically meaningful improvement across multiple metrics simultaneously.

---

## 3. Results

### 3.1 Primary Results at k=4

Table 1 summarizes the key results at k=4 traces per reason, averaged across both real draft/target pairs and 500 random seeds.

| Method | Mean Kendall τ | Mean Top-3 Overlap | Mean MAE |
|---|---|---|---|
| Pair-adaptive (k=4) | 0.790 | 2.429/3 | 0.036 |
| Fixed synthetic prior | −0.137 | 0.864/3 | — |
| Cross-pair real transfer | — | — | 0.134 |

*Table 1: Calibration quality at k=4 traces per reason. The fixed synthetic prior is the best non-adaptive baseline for ranking metrics (τ, top-3 overlap); cross-pair real transfer is the best non-adaptive baseline for MAE. Dashes indicate the baseline was not the strongest for that metric.*

### 3.2 Pair-Adaptive Margins Over Best Baselines

At k=4, the pair-adaptive method's margins over the best non-adaptive baselines are:

- Kendall τ improvement: +0.927
- Top-3 overlap improvement: +1.565
- MAE improvement: +0.098

All three margins exceed the kill-condition thresholds (+0.25 τ, +1.0 top-3 overlap, MAE reduction). The kill condition was therefore **not triggered**.

### 3.3 Negative Baseline Results

The fixed synthetic prior's negative Kendall τ (−0.137) indicates that its reason ranking is effectively uncorrelated with—or slightly inversely correlated to—the true pair-specific ranking. This is a notable negative result: a carefully constructed synthetic prior provides no useful ranking information for these pairs. Similarly, cross-pair real transfer yields MAE = 0.134, which is nearly four times the pair-adaptive MAE of 0.036, indicating that weights from one pair are a poor proxy for another pair's waste distribution.

### 3.4 Results at Other k Values

The benchmark was also run at k=2 and k=8. The full results are recorded in `results/pair_adaptive_calibration/summary_by_method.csv` and `results/pair_adaptive_calibration/split_metrics.jsonl`. The k=4 result was designated as the primary evaluation point because it represents a practical compromise between sample cost and calibration quality.

---

## 4. Limitations

1. **Two-pair evaluation scope.** The benchmark evaluates only two real draft/target pairs. While the results are consistent across both pairs, generalization to other model families, size ratios, or domains is not established. The claim that pair-adaptive calibration outperforms non-adaptive baselines is supported only in the tested setting.

2. **No production deployment validation.** These results come from a statistical benchmark using repeated train/heldout splits on pre-collected traces. They do not demonstrate that pair-adaptive calibration improves end-to-end speculative decoding throughput or latency in a live serving system.

3. **No external replication.** The benchmark was executed once within a single automated pipeline run. Independent replication by a different team or on different infrastructure has not been performed.

4. **Limited model diversity.** One of the two pairs uses Qwen1.5-3B as the draft model; the other pair's configuration is inherited from the parent project. Results may not extend to substantially different draft/target architectures or size ratios.

5. **Synthetic prior construction.** The fixed synthetic prior's poor performance (τ = −0.137) may reflect limitations in the specific prior used rather than a fundamental limitation of all synthetic approaches. Other synthetic priors might perform differently.

6. **Automated provenance.** This draft and the underlying benchmark were generated and executed by an automated pipeline. While the code and data artifacts are available for inspection, no human independently verified the benchmark execution or metric computations prior to this draft.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Benchmark script available | Yes: `scripts/pair_adaptive_calibration_benchmark.py` |
| Random seeds documented | Yes: 500 seeds, invoked via `--seeds 500` |
| Input data artifacts available | Yes: parent real-trace data in `parent_artifacts/` |
| Output metrics persisted | Yes: `results/pair_adaptive_calibration/` (6 files) |
| Kill condition pre-registered | Yes: defined in benchmark report prior to execution |
| Hardware environment specified | No: execution environment details not recorded in artifacts |
| Software dependencies specified | Partially: script is dependency-free (stdlib only); Python version not recorded |
| Statistical variance reported | Partially: mean metrics across seeds reported; per-seed variance in `split_metrics.jsonl` |
| External replication performed | No |

---

## 6. Conclusion

This paper reports evidence that pair-adaptive calibration—learning per-pair reason weights from as few as k=4 real speculative-decoding traces per reason—substantially outperforms non-adaptive baselines on two real draft/target pairs. At k=4, pair-adaptive calibration achieved mean Kendall τ = 0.790 versus −0.137 for the best non-adaptive ranking baseline, and mean MAE = 0.036 versus 0.134 for the best non-adaptive MAE baseline. The pre-registered kill condition was not triggered.

The negative baseline results are themselves informative: fixed synthetic priors provided no useful ranking signal for these pairs, and cross-pair weight transfer introduced substantial error. These findings suggest that waste-reason distributions are sufficiently pair-specific that even small amounts of pair-local data are preferable to generic or transferred alternatives.

The primary limitation is the two-pair evaluation scope. The project decision recommends that future work validate the same k=4 per-reason protocol on additional draft/target pairs rather than extending the current branch. Whether these margins hold across diverse model families, size ratios, and serving conditions remains an open question.

---

## Referenced Artifacts

### Result files
- `results/pair_adaptive_calibration/summary.json`
- `results/pair_adaptive_calibration/benchmark_report.md`
- `results/pair_adaptive_calibration/summary_by_method.csv`
- `results/pair_adaptive_calibration/split_metrics.jsonl`
- `results/pair_adaptive_calibration/sample_estimates.jsonl`
- `results/pair_adaptive_calibration/run_stdout.json`

### Source and data files
- `scripts/pair_adaptive_calibration_benchmark.py`
- `parent_artifacts/summary.json`
- `parent_artifacts/stability/cross_pair_stability_report.md`
- `parent_artifacts/stability/cross_pair_stability.json`
- `parent_artifacts/real_traces_qwen15_3b/real_trace_report.md`
- `parent_artifacts/real_traces_qwen15_3b/real_trace_summary.json`
- `parent_artifacts/real_traces_qwen15_3b/real_speculative_traces.jsonl`
- `parent_artifacts/real_traces/real_trace_report.md`
- `parent_artifacts/real_traces/real_trace_summary.json`

### Decision and audit files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `run_notes.md`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
