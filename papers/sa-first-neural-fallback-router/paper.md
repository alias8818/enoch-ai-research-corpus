# SA-First Neural Fallback Router: A Learned Gate for Selective Invocation of Expensive Neural Inference

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, benchmark outputs, decision records, and metric files). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate a two-stage routing architecture in which a deterministic static-analysis (SA) layer processes all requests and a small learned gate predicts whether the SA output is unsupported or likely incorrect, conditionally invoking an expensive neural fallback only when needed. On synthetic benchmarks executed on CPU-only hardware (NVIDIA GB10, aarch64, Linux 6.17), the SA-first learned gate achieves 97.26% accuracy while reducing neural invocation cost by 54.2% and latency by 55.1% relative to an always-fallback neural baseline, at the cost of a 1.13 percentage-point accuracy deficit. However, sensitivity analysis across degraded regimes reveals that these savings collapse to approximately 12% when SA coverage is low or confidence signals are noisy, with fallback rates rising to approximately 87%. The architecture is conditionally viable: it delivers material efficiency gains when the SA layer resolves a substantial fraction of requests with calibrated uncertainty, but offers negligible benefit otherwise. All results derive from synthetic benchmarks and have not been validated on production workloads.

---

## Introduction

In many inference-serving systems, a cheap deterministic or static-analysis (SA) path can correctly resolve a subset of requests, while the remainder require expensive neural inference. A natural architecture routes requests through the SA layer first and selectively invokes the neural model only when SA output is uncertain or unsupported. The key design question is what decides whether to fall back.

Simple threshold policies on SA confidence are common but brittle: a fixed threshold may over-fallback on well-calibrated SA outputs or under-fallback on miscalibrated ones. We explore whether a small learned gate, trained on labeled SA outcomes, can improve on threshold routing by predicting whether the SA answer will be wrong or unsupported before committing to the neural path.

This paper reports results from synthetic benchmark experiments evaluating the SA-first learned gate against three baselines: SA-only (no fallback), threshold-based SA fallback, and neural-all (always fallback). We measure accuracy, fallback rate, cost, and latency, and we conduct sensitivity analysis across regimes that vary SA coverage and confidence signal quality.

---

## Method

### Architecture

The SA-first neural fallback router operates in two stages:

1. **SA layer.** A deterministic/static-analysis first path processes every request and emits a set of signals: support, confidence, warning, complexity, novelty, and ambiguity. These signals characterize whether the SA output is likely to be correct and complete.

2. **Learned gate.** A small model (trained on labeled SA outcomes) takes the SA signals as input and predicts whether the SA answer is unsupported or likely wrong. If the gate predicts failure, the request is routed to the neural fallback; otherwise, the SA answer is returned directly.

### Baselines

We compare against three policies:

- **SA only:** Returns the SA answer unconditionally. Cost normalized to 1.0 unit per request.
- **Threshold SA:** Falls back to neural inference when SA confidence falls below a fixed threshold.
- **Neural all:** Always invokes the neural fallback. Cost normalized to 25.0 units per request.

### Experimental Setup

**Environment.** All experiments ran on an NVIDIA GB10 system (aarch64, Linux 6.17, Python 3.12.3) with approximately 121.9 GB available memory, swap disabled (`SwapTotal: 0 kB`), and `earlyoom` active. GPU utilization was 0%; all benchmarks were CPU-only.

**Data.** Synthetic datasets generated with controlled seeds. The base experiment used 6,000 training, 3,000 development, and 12,000 test examples (seed 7). A prior smoke test confirmed script correctness with smaller data (200/100/300, seed 11).

**Sensitivity analysis.** We evaluated three regimes across five seeds each:

- **base:** Default SA coverage and confidence calibration.
- **low_sa_coverage:** Reduced fraction of requests for which SA can produce a supported answer.
- **noisy_confidence:** SA confidence signals corrupted with noise, degrading gate input quality.

**Cost model.** SA-only cost is 1.0 unit per request. Neural fallback cost is 25.0 units per request (reflecting the relative expense of neural inference). A request that falls back incurs both SA and neural cost. Latency follows a similar proportional model: SA-only at 0.200 ms, neural-all at 8.000 ms per request.

**Validation.** An independent validation script (`scripts/validate_research.py`) was run after all experiments to verify artifact consistency.

---

## Results

### Base Regime (Seed 7)

| Policy | Accuracy | Fallback Rate | Mean Cost Units | Mean Latency (ms) |
|---|---:|---:|---:|---:|
| SA only | 0.6330 | 0.0000 | 1.000 | 0.200 |
| Threshold SA | 0.9625 | 0.3979 | 10.550 | 3.304 |
| Neural all | 0.9839 | 1.0000 | 25.000 | 8.000 |
| SA-first learned gate | 0.9726 | 0.4351 | 11.442 | 3.594 |

The learned gate achieves 97.26% accuracy, a 1.01 percentage-point improvement over threshold SA (96.25%) and a 1.13 percentage-point deficit relative to neural-all (98.39%). It invokes the neural fallback on 43.51% of requests, slightly more than threshold SA (39.79%), yielding a modest cost increase of 0.892 units over threshold SA. Relative to neural-all, the learned gate reduces cost by 54.2% and latency by 55.1%.

The SA-only baseline confirms that static analysis alone is insufficient (63.30% accuracy), establishing that fallback is necessary for acceptable quality.

### Sensitivity Analysis

Across five seeds per regime:

| Regime | Mean Gate Accuracy | Min Gate Accuracy | Max Gate Accuracy | Mean Fallback Rate | Mean Cost Reduction vs. Neural-All |
|---|---:|---:|---:|---:|---:|
| base | 0.9735 | 0.962 | 0.980 | 0.4840 | 49.5% |
| low_sa_coverage | 0.9708 | 0.9655 | 0.9754 | 0.8750 | 12.0% |
| noisy_confidence | 0.9734 | 0.9691 | 0.9774 | 0.8768 | 11.8% |

In the base regime, the learned gate maintains high accuracy (mean 97.35%, minimum 96.2%) with a mean fallback rate of 48.4%, yielding approximately 49.5% cost reduction versus neural-all. Gate accuracy is relatively stable across seeds.

In the degraded regimes, gate accuracy remains comparable (mean 97.08% and 97.34%), but the fallback rate rises sharply to approximately 87.5–87.7%, collapsing cost savings to roughly 12%. The gate correctly identifies that SA outputs are unreliable in these regimes and routes most requests to fallback, preserving accuracy but negating the efficiency rationale.

### Negative and Mixed Evidence

Several findings temper the positive interpretation:

1. **The learned gate does not match neural-all accuracy.** The 1.13 percentage-point gap is small in absolute terms but may be unacceptable in domains where near-perfect accuracy is required.

2. **The learned gate is slightly more expensive than threshold SA** in the base regime (11.442 vs. 10.550 cost units), because it falls back on a larger fraction of requests (43.51% vs. 39.79%). The accuracy improvement of 1.01 percentage points over threshold SA comes at a cost premium.

3. **Benefits vanish under poor SA coverage or noisy confidence.** In the `low_sa_coverage` and `noisy_confidence` regimes, the architecture retains its accuracy advantage over SA-only but provides only approximately 12% cost reduction versus neural-all, which is unlikely to justify the operational complexity of maintaining a two-stage system.

4. **Gate accuracy variance.** Even in the base regime, minimum gate accuracy across seeds was 96.2%, suggesting occasional seed-dependent degradation. The sample of five seeds is small, and the true variance may be larger.

---

## Limitations

1. **Synthetic benchmarks only.** All results derive from synthetic data with controlled SA coverage and confidence properties. Scientific closure on a production router requires real request traces labeled with SA outcome and neural fallback outcome. We have not conducted such validation.

2. **Private specification unavailable.** The originating project prompt referenced private Notion content that was not available in the working tree. The operational definition of SA was reconstructed from the project name and local scripts; it may differ from the original intent.

3. **Accuracy–cost tradeoff is domain-dependent.** Whether a 1.13 percentage-point accuracy deficit is acceptable in exchange for 54.2% cost reduction depends on application-specific error tolerance and cost constraints. We do not prescribe a universal threshold.

4. **No production latency measurement.** Latency figures reflect a synthetic proportional model, not measured end-to-end serving latency on real infrastructure with queuing, batching, and network effects.

5. **Limited sensitivity coverage.** We tested two degraded regimes (low SA coverage, noisy confidence). Other failure modes—distribution shift, adversarial inputs, gate overconfidence on out-of-distribution SA signals—were not evaluated.

6. **Small seed count.** Sensitivity analysis used five seeds per regime. This is sufficient to reveal gross trends but inadequate for precise confidence intervals on the reported means.

7. **CPU-only execution.** All benchmarks ran on CPU with zero GPU utilization. Results may not transfer to GPU-accelerated serving environments where the cost ratio between SA and neural inference differs.

8. **Claim audit incomplete.** The structured claim ledger for this artifact was flagged as `blocked_empty_claims` at generation time: no structured claims were extracted for formal evidence linkage. The reported findings should be treated as preliminary until claims are formally registered and audited against the evidence artifacts.

---

## Reproducibility Checklist

- **Code available:** `scripts/run_experiment.py`, `scripts/validate_research.py` (compiled and executed without error).
- **Random seeds reported:** Base run seed 7; smoke test seed 11; sensitivity loop over five seeds per regime.
- **Dataset sizes reported:** Base: 6,000 train / 3,000 dev / 12,000 test. Smoke: 200/100/300.
- **Hardware specified:** NVIDIA GB10, aarch64, Linux 6.17, Python 3.12.3, approximately 121.9 GB RAM, swap disabled, earlyoom active, CPU-only.
- **All metrics reported:** Accuracy, fallback rate, mean cost units, mean latency for all four policies.
- **Sensitivity analysis included:** Three regimes (base, low_sa_coverage, noisy_confidence) across five seeds each.
- **Validation script executed:** `scripts/validate_research.py` ran post-experiment.
- **Output artifacts:** All metric JSON files and log files preserved (see Referenced Artifacts).
- **Claim audit status:** Blocked (empty claims); not yet passed.

---

## Conclusion

The SA-first learned fallback router is conditionally viable. In regimes where static analysis has sufficient coverage and emits calibrated uncertainty signals, the learned gate preserves high accuracy (at or above 97.3%) while avoiding roughly half of neural fallback invocations, yielding cost and latency reductions of approximately 50–55% relative to an always-fallback baseline. This represents a material efficiency gain for workloads that meet these preconditions.

However, the architecture's benefits are not universal. When SA coverage is low or confidence signals are noisy, the gate correctly routes most requests to fallback, preserving accuracy but reducing cost savings to approximately 12%. In such regimes, the operational complexity of maintaining a two-stage system is unlikely to be justified.

The learned gate also does not close the accuracy gap with neural-all inference, retaining a deficit of approximately 1.1 percentage points even in favorable conditions. Deployment decisions must weigh this deficit against the efficiency gains within the specific error tolerance of the target application.

Future work should: (a) collect real workload traces with labeled SA and neural outcomes to validate or refute the synthetic findings; (b) calibrate the fallback acceptance threshold to product-specific risk tolerance; and (c) incorporate an abstention or error taxonomy so that unsupported SA cases are always routed to fallback before the learned gate optimizes residual risk.

---

## Referenced Artifacts

| Artifact | Description |
|---|---|
| `scripts/run_experiment.py` | Main experiment script (training, evaluation, sensitivity loop) |
| `scripts/validate_research.py` | Post-experiment validation script |
| `artifacts/logs/smoke.log` | Smoke test log (seed 11, small data) |
| `artifacts/logs/base_run.log` | Base regime run log (seed 7) |
| `artifacts/logs/sensitivity.log` | Sensitivity analysis log (3 regimes × 5 seeds) |
| `artifacts/metrics/smoke.json` | Smoke test metric output |
| `artifacts/metrics/sa_first_router_base.json` | Base regime metric output |
| `artifacts/metrics/sa_first_router_sensitivity.json` | Sensitivity analysis metric output |
| `.omx/specs/autoresearch-sa-first-neural-fallback-router/result.json` | Structured result specification |
| `run_notes.md` | Operator run notes and interpretation |
| `.omx/project_decision.json` | Decision record with key metrics and limitations |
| `papers/.../claim_ledger.json` | Claim ledger (status: blocked_empty_claims) |
| `papers/.../evidence_bundle.json` | Evidence bundle (source: langgraph_control_plane_mvp) |
| `papers/.../paper_manifest.json` | Paper generation manifest |
