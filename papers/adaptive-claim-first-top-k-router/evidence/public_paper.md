# Adaptive Claim-First Top-K Router

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We present an adaptive routing method that selects between dense claim-first prompt packing and top-k budgeted packing based on task-shape signals. The router is designed to retain the answer-quality gains of dense claim-first prompting on supported task shapes while reducing the token bloat and packing latency that arise when claim-first is applied indiscriminately. In a scaled LongBench evaluation using Qwen-0.5B, the adaptive router achieves F1 scores of 0.2381 (budget 320) and 0.2783 (budget 640), exceeding both a plain top-k baseline (0.1725 and 0.2152) and an always-dense claim-first baseline (0.2265 and 0.2513). Mean model-input tokens under the adaptive router fall 2.0–2.6% below the always-dense baseline. These results are specific to the tested LongBench grid and model; the routing rules are hand-fit to the parent dataset, and confidence in generalizability remains medium. The project decision is `finalize_positive` with hypothesis status `supported`.

## 1. Introduction

Retrieval-augmented generation (RAG) systems face a fundamental packing trade-off: including more retrieved context can improve answer quality but increases prompt length, inference cost, and latency. The claim-first prompt skeleton approach prioritizes retrieved chunks that directly support claimed answer structures, yielding quality improvements on certain task shapes but at the cost of increased token usage when applied uniformly.

This work investigates whether a simple adaptive router—selecting between dense claim-first packing and top-k budgeted packing on a per-query basis—can recover most of the quality gains of always-dense claim-first while materially reducing token consumption. The branch-level kill condition specified that the adaptive router must (a) recover at least most of dense claim-first's quality gains on helpful task shapes and (b) materially reduce prompt token bloat versus always-dense, or else the approach would be abandoned as adding complexity without benefit.

The hypothesis is supported in the tested setting: adaptive routing improves generated-answer F1 over both baselines while reducing token usage relative to always-dense claim-first. However, the routing rules are hand-fit, and broader validation remains incomplete.

## 2. Method

### 2.1 Adaptive Claim-First Top-K Router

The `AdaptiveClaimFirstTopKRouter` (implemented in `src/claim_first/packers.py`) inspects task-type hints when available and routes each query to one of two packing strategies:

- **Dense claim-first:** Packs retrieved chunks using the claim-first prompt skeleton, which prioritizes chunks that directly support the answer structure. This strategy tends to produce higher-quality outputs on task shapes where claim-first was observed to help in prior experiments, but at higher token cost.
- **Top-k budgeted packing:** Selects the top-k chunks within a token budget without claim-first structuring. This strategy is more token-efficient but may miss structural advantages on certain query types.

The routing decision is based on explicit task-shape rules derived from analysis of the parent project's scaled LongBench run. When task-type hints are unavailable, the router defaults to top-k budgeted packing.

### 2.2 Benchmark Harness

The `llm_eval` and offline benchmark harnesses were updated to include the adaptive strategy and to pass task-type hints when available. This enables head-to-head comparison of adaptive, always-dense, and top-k strategies under identical evaluation conditions.

## 3. Results

### 3.1 Verification and Smoke Tests

Unit tests for adaptive dense/top-k routing passed (9 of 9). An offline synthetic benchmark was executed (`results/adaptive_offline/benchmark_summary.json`), confirming basic packing behavior.

A LongBench smoke/calibration run produced 20 evaluation rows in 2.686 seconds (7.446 rows/sec, mean output tokens/sec 98.209). This served as a calibration step rather than a definitive quality measurement.

### 3.2 Scaled LongBench Grid

The primary evaluation used a scaled LongBench grid with the Qwen-0.5B model, producing 320 evaluation rows in 113.348 seconds (2.823 rows/sec, mean output tokens/sec 103.704). Peak CUDA allocation was 1.096 GB; process RSS was 1.91 GB; system MemAvailable was approximately 119.7 GiB.

**Budget 320:**

| Strategy | F1 | Mean Model Tokens |
|---|---|---|
| Adaptive | 0.2381 | 424.3 |
| Always-dense | 0.2265 | 432.8 |
| Top-k | 0.1725 | 407.3 |

**Budget 640:**

| Strategy | F1 | Mean Model Tokens |
|---|---|---|
| Adaptive | 0.2783 | 664.0 |
| Always-dense | 0.2513 | 682.0 |
| Top-k | 661.3 | 0.2152 |

*Correction — the top-k entry for budget 640: F1 = 0.2152, mean model tokens = 661.3.*

The adaptive router achieves the highest F1 at both budgets. Relative to always-dense claim-first, the adaptive router reduces mean model-input tokens by approximately 2.0% (budget 320: 424.3 vs. 432.8) and 2.6% (budget 640: 664.0 vs. 682.0). Relative to plain top-k, the adaptive router uses modestly more tokens (4.2% at budget 320, 0.4% at budget 640) but achieves substantially higher F1 (+38.0% and +29.4% relative improvement over top-k at budgets 320 and 640, respectively).

Pack latency under the adaptive router is reported as sharply lower than classic claim-first, though quantitative latency figures are not recorded in the available artifacts.

### 3.3 Negative and Mixed Observations

- The adaptive router does not repair the inherited behavior whereby top-k packing can exceed nominal model budgets when the first chunk alone exceeds the budget. The adaptive router mitigates this by routing some queries away from top-k, but the underlying issue persists.
- Token savings of 2.0–2.6% versus always-dense are modest. Whether this reduction is practically significant depends on deployment cost models not evaluated here.
- The F1 scores overall are low (0.17–0.28 range), consistent with the use of a 0.5B-parameter model on LongBench tasks. The relative improvements may not hold at larger model scales.

## 4. Limitations

1. **Hand-fit routing rules.** The task-shape routing logic was derived from the same parent scaled LongBench dataset. There is a risk of overfitting to that specific data distribution. Held-out LongBench slices and alternative benchmark suites were not evaluated.

2. **Single model scale.** All results use Qwen-0.5B. Whether the adaptive router's advantages persist with larger models (which may exhibit different sensitivity to prompt structure) is unknown.

3. **No external replication.** The experiments were conducted within a single automated pipeline run. No independent replication has been performed.

4. **Incomplete latency characterization.** Pack latency is described as "sharply lower" versus classic claim-first, but no quantitative latency measurements appear in the recorded artifacts.

5. **Inherited budget overflow.** The top-k packer can exceed its nominal token budget when the first retrieved chunk alone exceeds the budget. The adaptive router does not fix this inherited behavior.

6. **Modest token savings.** The 2.0–2.6% reduction in mean model-input tokens versus always-dense may be insufficient to justify the added routing complexity in some deployment contexts.

7. **Confidence is medium.** The project decision assigns medium confidence to the supported hypothesis, reflecting the above gaps.

## 5. Reproducibility Checklist

- **Code:** `src/claim_first/packers.py` (AdaptiveClaimFirstTopKRouter), `src/claim_first/benchmark.py`, `src/claim_first/llm_eval.py`
- **Tests:** `tests/test_packers.py` (9 passed)
- **Model:** Qwen-0.5B (local, CUDA)
- **Benchmark data:** LongBench (acquired from parent project)
- **Offline synthetic benchmark:** `results/adaptive_offline/benchmark_summary.json`, `results/adaptive_offline/benchmark_rows.csv`
- **Smoke/calibration run:** `results/adaptive_llm_smoke/llm_eval_summary.json`, `results/adaptive_llm_smoke/llm_eval_rows.csv`
- **Scaled grid run:** `results/adaptive_qwen05_longbench_scaled/llm_eval_summary.json`, `results/adaptive_qwen05_longbench_scaled/llm_eval_rows.csv`, `results/adaptive_qwen05_longbench_scaled/interpretation.md`
- **Hardware context:** CUDA max allocated 1.096 GB, process RSS 1.91 GB, MemAvailable ~119.7 GiB
- **Random seeds:** Not recorded in available artifacts; exact numerical replication may vary.

## 6. Conclusion

The adaptive claim-first top-k router improves generated-answer F1 over both plain top-k and always-dense claim-first packing on the evaluated LongBench grid with Qwen-0.5B, while reducing mean model-input tokens by 2.0–2.6% relative to the always-dense baseline. The branch-level kill condition was not triggered: the adaptive router recovers the quality gains of dense claim-first and reduces token bloat, distinguishing it from a trivially equivalent top-k strategy.

These findings are bounded by significant limitations. The routing rules are hand-fit to the parent dataset, validation is confined to a single small model, and no held-out or external replication has been performed. The project decision of `finalize_positive` with medium confidence reflects that the hypothesis is supported in the tested setting but requires additional validation before production use. The recommended next step is to evaluate the same adaptive policy on a larger cached model or a held-out LongBench slice.

---

## Referenced Artifacts

### Result files
- `results/adaptive_qwen05_longbench_scaled/interpretation.md`
- `results/adaptive_qwen05_longbench_scaled/llm_eval_summary.json`
- `results/adaptive_qwen05_longbench_scaled/llm_eval_rows.csv`
- `results/adaptive_llm_smoke/llm_eval_summary.json`
- `results/adaptive_llm_smoke/llm_eval_rows.csv`
- `results/adaptive_offline/benchmark_summary.json`
- `results/adaptive_offline/benchmark_rows.csv`

### Source and configuration files
- `src/claim_first/packers.py`
- `src/claim_first/benchmark.py`
- `src/claim_first/llm_eval.py`
- `src/claim_first/__init__.py`
- `tests/test_packers.py`
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
