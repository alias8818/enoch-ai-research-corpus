# Benchmark Health Ledger: Structured Governance for Benchmark Selection Quality and Risk

> **AI Provenance Notice.** This draft was generated automatically from research artifacts produced by the OMX automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate whether a structured benchmark health ledger—a dependency-light scorer that models benchmark contamination, fragility, cost, staleness, accessibility, and relevance as live fields—can improve benchmark selection quality while reducing aggregate health risk relative to a relevance-only baseline. Three experimental stages were conducted: a toy smoke test with hand-authored risk priors, a live-evidence replay against 39 historical benchmark-selection decisions drawn from neighboring research projects, and an uncertainty-penalized held-out validation split. The uncertainty-penalized ledger improved held-out NDCG@3 by +0.0068 and reduced health risk@3 by −0.0300 relative to actual agent choices, while increasing evidence coverage (+0.0334) and reducing locally unvalidated top-3 recommendations (−0.20 per decision). However, the penalty also reduced NDCG@3 by −0.0217 relative to the unpenalized ledger and slightly increased risk (+0.0053), and a separate quality metric (observed historical quality@3) declined from 0.5967 to 0.5334 in the live replay. These mixed-positive results support the benchmark-health-ledger mechanism at moderate evidence strength while exposing a real tradeoff between validation strictness and selection-quality gains. The oracle is derived from local project outcomes rather than independent labels, and all experiments are CPU-only replay studies without model inference. Confidence is assessed as medium.

---

## 1. Introduction

Benchmark selection in language-model evaluation is typically driven by relevance and popularity, with limited systematic attention to benchmark health properties such as contamination exposure, staleness, fragility, and cost risk. A benchmark that is widely cited may nonetheless carry high contamination risk, be stale relative to current model capabilities, or be fragile to small distributional shifts. Selecting benchmarks without accounting for these health dimensions can produce misleading evaluation conclusions.

We explore a simple governance mechanism: a benchmark health ledger that maintains live fields for contamination, fragility, cost, staleness, accessibility, and relevance, and that adjusts benchmark rankings by health-adjusted relevance rather than relevance alone. The central hypothesis is that even a simple structured ledger can alter benchmark selection order in useful ways—improving selection quality while lowering aggregate health and cost risk.

This paper reports results from three experimental stages of increasing fidelity: (1) a toy smoke test with hand-authored priors, (2) a live-evidence replay using risk estimates derived from 1,347 benchmark mentions in neighboring research project logs, and (3) an uncertainty-penalized held-out validation that discounts benchmarks with low local evidence coverage. The evidence supports the mechanism at moderate strength, but with identifiable tradeoffs that bound the strength of the claim.

---

## 2. Method

### 2.1 Benchmark Health Ledger

The ledger is implemented as a CSV-backed scorer (`src/benchmark_health_ledger.py`) with the following per-benchmark fields:

- **Relevance**: task-domain relevance score.
- **Contamination risk**: estimated data-contamination exposure.
- **Fragility**: sensitivity to small input distributional shifts.
- **Cost risk**: computational or access cost of running the benchmark.
- **Staleness**: age relative to known release dates, sourced from `SOURCES.md`.
- **Accessibility**: availability of benchmark data and tooling.

The health-ledger policy score is computed as relevance adjusted by a weighted aggregate of health risk fields, where the weighting reflects a configurable risk tolerance.

### 2.2 Baseline

The manual baseline selects benchmarks by relevance and popularity only, without health-risk adjustment. This approximates common practice in research-agent benchmark selection.

### 2.3 Oracle Utility

A separate oracle utility provides ground-truth benchmark quality rankings. In the smoke test, this oracle is hand-authored. In the live replay, the oracle is inferred from historical project outcomes and live health risk. We acknowledge that this oracle is not independently labeled and constitutes a source of uncertainty.

### 2.4 Live Evidence Ingestion

The live-evidence replay harness (`src/live_evidence_replay.py`) scans neighboring Enoch research project logs (excluding the current project to avoid self-confirmation), extracts benchmark mentions, and recomputes risk priors from observed exposure, age, risk cues, and project decisions. This replaces the hand-authored toy priors with field-derived estimates.

### 2.5 Uncertainty Penalty

An evidence-coverage field is computed from log-scaled project coverage and mention coverage. The uncertainty-penalized ledger score discounts the health-ledger score for low evidence coverage, with stronger discount under lower risk tolerance. This addresses the risk that the ledger over-ranks benchmarks that are fresh but locally unvalidated.

### 2.6 Held-Out Validation Split

A deterministic held-out-project split is applied: projects sorted by index, with every fourth project (index mod 4 = 0) held out. Benchmark risks and coverage are recomputed from training projects only before replaying held-out decisions. This yields 10 held-out projects from 39 replayed decisions, with 1,218 training mentions and 129 held-out mentions.

---

## 3. Results

### 3.1 Toy Smoke Test

The smoke test seeded 12 common coding, KV-retrieval, and data benchmarks with hand-authored risk priors and evaluated 4 benchmark-selection scenarios.

| Metric | Manual Baseline | Health Ledger | Delta |
|---|---|---|---|
| Mean NDCG@3 | 0.9377 | 0.9717 | +0.0340 |
| Mean Health Risk@3 | 0.4426 | 0.4236 | −0.0190 |
| Mean Cost Risk@3 | 0.5050 | 0.4733 | −0.0317 |
| Oracle Overlap@3 | 0.8333 | 0.9167 | +0.0834 |

The smoke test produced a measurable signal at negligible computational cost (wall-clock ~0.0006 s, max RSS 20,184 KB). However, risk priors are hand-authored and the oracle is toy, so this stage provides only weak initial evidence.

### 3.2 Live-Evidence Replay

The live replay ingested 1,347 benchmark mentions from neighboring research projects and replayed 39 historical benchmark-selection decisions.

| Metric | Actual Agent Choices | Health Ledger Replay | Delta |
|---|---|---|---|
| Mean NDCG@3 | 0.9385 | 0.9986 | +0.0600 |
| Mean Health Risk@3 | 0.4449 | 0.3883 | −0.0565 |
| Oracle Overlap@3 | 0.7863 | 1.0000 | +0.2137 |
| Mean Observed Quality@3 | 0.5967 | 0.5334 | −0.0633 |

The ledger improved NDCG@3 and reduced health risk, but **observed historical quality@3 declined by −0.0633**. This negative result indicates that the ledger sometimes recommends fresher, lower-risk benchmarks with less local outcome evidence, which is a genuine limitation rather than a measurement artifact.

### 3.3 Uncertainty-Penalized Held-Out Validation

Held-out validation compared three policies against actual agent choices on 10 held-out projects:

| Metric | Actual Agent | Unpenalized Ledger | Penalized Ledger |
|---|---|---|---|
| Mean NDCG@3 | 0.9625 | 0.9910 | 0.9693 |
| Mean Health Risk@3 | 0.4425 | 0.4072 | 0.4125 |
| Evidence Coverage | — | — | +0.0334 vs unpenalized |
| Unvalidated Top-3 (per decision) | — | — | −0.20 vs unpenalized |

Penalized ledger vs actual agent: **+0.0068 NDCG@3, −0.0300 health risk@3**.

Penalized ledger vs unpenalized ledger: **−0.0217 NDCG@3, +0.0053 health risk@3**, but better evidence coverage and fewer unvalidated top-3 recommendations.

The uncertainty penalty thus produces a mixed-positive result: it preserves the ledger's improvement over the actual agent baseline while reducing the over-ranking of locally unvalidated benchmarks, but at the cost of surrendering some of the unpenalized ledger's gains.

### 3.4 Computational Cost

All experiments were CPU-only. No model inference, GPU workload, or helper server was used.

| Stage | Wall-Clock | CPU Time | Max RSS |
|---|---|---|---|
| Smoke test | ~0.0006 s | ~0.0006 s | 20,184 KB |
| Live replay | 43.2850 s | 43.2777 s | 24,756 KB |
| Held-out validation | 43.2931 s | 43.2869 s | 25,116 KB |

---

## 4. Limitations

1. **Oracle provenance.** The oracle utility is inferred from local project outcomes and risk cues, not from independently labeled benchmark-selection decisions. This introduces circularity risk: the oracle may favor benchmarks that appear frequently in the same project logs that supply the evidence.

2. **Negative quality result.** The live replay showed a decline in observed historical quality@3 (0.5967 → 0.5334), indicating that the ledger's preference for fresher, lower-risk benchmarks can come at the expense of locally validated quality.

3. **Uncertainty-penalized tradeoff.** The penalized ledger surrenders NDCG@3 (−0.0217) and slightly increases risk (+0.0053) relative to the unpenalized ledger. This tradeoff is real and not resolved by the current experiments.

4. **Held-out split determinism.** The held-out split uses a fixed deterministic rule (sorted project index mod 4). A different split could yield different deltas.

5. **Scope of evidence.** All evidence is drawn from a single local research environment (Ench testing ground projects). External replication has not been performed.

6. **No model inference or GPU workloads.** The ledger is a CPU-only scoring mechanism. Its behavior under real model-evaluation workloads (where cost and fragility estimates would be grounded in actual compute) is untested.

7. **Risk priors origin.** The smoke-test priors are hand-authored. The live-replay priors are log-derived. Neither source provides independently validated ground truth for benchmark health.

8. **Small held-out sample.** Only 10 held-out projects (39 total decisions) contribute to the validation. Statistical power is limited.

---

## 5. Reproducibility Checklist

- **Source code**: `src/benchmark_health_ledger.py`, `src/live_evidence_replay.py` — both pass `py_compile` and execute to completion.
- **Input data**: `data/benchmark_ledger.csv`, `data/live_benchmark_ledger.csv`, `data/live_benchmark_evidence.json`, `data/research_log_decisions.jsonl`, `data/heldout_train_benchmark_ledger.csv`, `data/heldout_validation_split.json`.
- **Output data**: `results/smoke_selection_metrics.csv`, `results/smoke_summary.json`, `results/live_replay_metrics.csv`, `results/live_replay_summary.json`.
- **Deterministic split**: Held-out projects selected by sorted index mod 4 = 0.
- **Verification**: Acceptance booleans in `results/live_replay_summary.json` are true for: live evidence ingestion, held-out validation completion, uncertainty penalty presence, held-out NDCG improvement vs actual, held-out risk reduction vs actual, evidence-coverage improvement vs unpenalized, and unvalidated-top3 reduction vs unpenalized.
- **Environment**: CPU-only; no GPU, no model inference, no helper servers. Max RSS ≤ 25,116 KB.
- **Randomness**: No stochastic sampling reported; scoring is deterministic given fixed inputs.

---

## 6. Conclusion

A structured benchmark health ledger can materially alter benchmark selection order toward lower observed health risk while improving selection quality relative to a relevance-only baseline. This finding is supported at moderate evidence strength across three experimental stages: a toy smoke test, a live-evidence replay, and an uncertainty-penalized held-out validation. The held-out validation shows that the penalized ledger improves NDCG@3 (+0.0068) and reduces health risk@3 (−0.0300) relative to actual agent choices, while reducing over-ranking of locally unvalidated benchmarks.

However, the evidence is bounded by several factors: the oracle is log-derived rather than independently labeled, observed historical quality@3 declined in the live replay, and the uncertainty penalty exposes a real tradeoff between validation strictness and selection-quality gains. The most valuable follow-up, if this line of work continues, would be to calibrate uncertainty penalties against independent benchmark labels rather than local log-derived oracles.

---

## Referenced Artifacts

### Source files
- `src/benchmark_health_ledger.py`
- `src/live_evidence_replay.py`

### Data files
- `data/benchmark_ledger.csv`
- `data/live_benchmark_ledger.csv`
- `data/live_benchmark_evidence.json`
- `data/research_log_decisions.jsonl`
- `data/heldout_train_benchmark_ledger.csv`
- `data/heldout_validation_split.json`

### Result files
- `results/smoke_selection_metrics.csv`
- `results/smoke_summary.json`
- `results/live_replay_metrics.csv`
- `results/live_replay_summary.json`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `run_notes.md`
- `SOURCES.md`

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
