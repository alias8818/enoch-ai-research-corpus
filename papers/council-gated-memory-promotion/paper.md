# Council-Gated Memory Promotion: A Multi-Criterion Gate for Reducing False Durable Memories in Synthetic Evaluation

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, simulation outputs, paired statistics). The operator who released this artifact claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact and evaluate its claims accordingly.

---

## Abstract

Durable memory systems for autonomous agents must decide which candidate memories to promote to long-term storage. Simple threshold policies either over-promote—contaminating memory with false entries—or under-promote, losing useful information. We propose a *council-gated* promotion policy requiring three independent checks (evidence, utility, and skeptic gates) before a candidate memory is promoted. In a synthetic simulation across 50 random seeds and three adversarial contamination rates (0.00, 0.18, 0.35), the council gate achieved the highest mean quality score at all rates, with statistically significant improvements over a single-threshold baseline at low and moderate adversarial rates (quality delta +24.80, p ≈ 0.00005 at rate 0.00; +13.06, p ≈ 0.00005 at rate 0.18). At the highest adversarial rate (0.35), the advantage was directionally positive but not statistically significant (+5.72, p ≈ 0.062). The council gate exhibited lower precision, lower recall, and lower F1 than the single-threshold baseline in all conditions, trading standard classification performance for fewer false promotions and reduced memory budget. These results are limited to synthetic data with thresholds calibrated on the same distribution and do not constitute production validation.

## Introduction

Autonomous agents that maintain durable memory face a fundamental gating problem: not every candidate observation or inference deserves promotion to long-term storage. Promoting too many candidates introduces false or misleading entries that persist and degrade downstream reasoning. Promoting too few sacrifices useful knowledge. This trade-off is sharpened when agents operate in environments with adversarial inputs, unreliable sources, or internally generated overconfident inferences.

Common approaches to memory gating employ single-criterion thresholds on confidence or utility scores. While simple and interpretable, such thresholds are vulnerable to systematic failure modes: a single high-confidence but uncorroborated claim may pass, or a genuinely useful but modestly scored observation may be rejected.

We investigate whether a *council* of independent gates, each evaluating a distinct aspect of candidate quality, can improve the outcome of memory promotion decisions. The council gate requires concurrence across three checks:

1. **Evidence gate**: Is the source reliable? Is there corroboration? Are contradictions low?
2. **Utility gate**: Is the candidate sufficiently useful and novel?
3. **Skeptic gate**: Does the candidate avoid patterns of overconfidence with low reliability, and are contradictions low?

This design rests on the intuition that different failure modes are caught by different criteria; requiring agreement reduces false promotions at the cost of some true positives.

We evaluate the council gate against three baselines—promote-all, single-threshold, and conservative-threshold—in a controlled synthetic simulation. We deliberately choose a quality metric that penalizes false durable memories heavily, reflecting the view that contamination in long-term storage is more damaging than lost recall. We report results honestly, including the finding that the council gate underperforms the single-threshold baseline on precision, recall, and F1, and that its quality advantage weakens and loses statistical significance under high adversarial pressure.

## Method

### Simulation Design

We implemented a dependency-free Python simulator (`scripts/council_memory_sim.py`) that generates synthetic memory candidates with the following latent attributes:

- **Truth**: whether the candidate is factually correct
- **Utility**: how useful the candidate would be if promoted
- **Novelty**: whether the candidate provides new information
- **Source reliability**: the trustworthiness of the source
- **Corroborating support**: degree of independent confirmation
- **Contradictions**: count of conflicting evidence
- **Adversarial overconfidence**: whether the candidate exhibits a pattern of high confidence with low reliability

The adversarial rate parameter controls the proportion of candidates that are intentionally misleading or overconfident.

### Policies

Four promotion policies were evaluated:

1. **promote_all**: Every candidate is promoted. This establishes an upper bound on recall and a lower bound on quality under any penalty for false promotions.

2. **single_threshold**: A single composite score threshold determines promotion. This represents a standard baseline approach.

3. **conservative_threshold**: A stricter single threshold that promotes very few candidates, minimizing false positives at the cost of recall.

4. **council_gated**: Promotion requires passage of all three independent gates:
   - *Evidence gate*: reliable source AND corroboration AND low contradictions
   - *Utility gate*: sufficiently useful AND sufficiently novel
   - *Skeptic gate*: low contradictions AND no overconfident/low-reliability pattern

### Quality Metric

The primary metric encodes an explicit policy preference:

```
quality_score = useful_true_promoted − 1.8 × false_promoted − 0.002 × estimated_review_cost
```

This metric penalizes false durable memories at 1.8× the value of a useful true promotion and assigns a small but nonzero cost to review effort. The coefficient 1.8 reflects the judgment that a false persistent memory is substantially more harmful than a missed useful one. If this weighting does not match a deployment's priorities, the ranking of policies may change.

### Experimental Conditions

- **Candidates per seed**: 5,000
- **Seeds**: 50 per condition
- **Adversarial rates**: 0.00, 0.18, 0.35
- **Total candidate evaluations**: 750,000 (3 rates × 50 seeds × 5,000 candidates)

### Statistical Analysis

Paired council-minus-single-threshold quality deltas were computed across the 50 seeds per condition. Bootstrap 95% confidence intervals (resampling the 50 paired differences) and sign-permutation p-values were calculated using `scripts/analyze_results.py`.

### Environment

All runs executed on a Linux system with approximately 117 GB available RAM and no swap. Each 250,000-candidate condition (50 seeds × 5,000 candidates) consumed approximately 18.9 MB max RSS and 1.6 seconds wall time. This was a lightweight CPU simulation; no GPU inference, llama.cpp hook prototypes, CUDA copy calibration, or production throughput measurement was involved.

## Results

### Overview

Tables 1a–1c present mean results across 50 seeds for each adversarial rate.

**Table 1a.** Mean results, adversarial rate = 0.00

| Policy | Quality | Precision | Recall (useful-true) | F1 | False promoted | Memory budget |
|---|---:|---:|---:|---:|---:|---:|
| council_gated | 539.24 | 0.882 | 0.711 | 0.787 | 100.48 | 0.170 |
| single_threshold | 514.44 | 0.918 | 0.783 | 0.845 | 167.90 | 0.410 |
| conservative_threshold | 340.02 | 0.969 | 0.359 | 0.524 | 16.12 | 0.103 |
| promote_all | −2258.21 | 0.633 | 1.000 | 0.775 | 1835.24 | 1.000 |

**Table 1b.** Mean results, adversarial rate = 0.18

| Policy | Quality | Precision | Recall (useful-true) | F1 | False promoted | Memory budget |
|---|---:|---:|---:|---:|---:|---:|
| council_gated | 432.92 | 0.880 | 0.688 | 0.772 | 83.50 | 0.139 |
| single_threshold | 419.86 | 0.917 | 0.767 | 0.835 | 140.78 | 0.339 |
| conservative_threshold | 275.97 | 0.968 | 0.348 | 0.512 | 13.54 | 0.084 |
| promote_all | −3303.42 | 0.535 | 1.000 | 0.697 | 2324.88 | 1.000 |

**Table 1c.** Mean results, adversarial rate = 0.35

| Policy | Quality | Precision | Recall (useful-true) | F1 | False promoted | Memory budget |
|---|---:|---:|---:|---:|---:|---:|
| council_gated | 338.90 | 0.882 | 0.662 | 0.756 | 65.42 | 0.110 |
| single_threshold | 333.18 | 0.915 | 0.748 | 0.823 | 114.90 | 0.272 |
| conservative_threshold | 217.03 | 0.968 | 0.335 | 0.497 | 10.74 | 0.067 |
| promote_all | −4303.46 | 0.441 | 1.000 | 0.612 | 2794.02 | 1.000 |

### Paired Comparisons: Council vs. Single-Threshold

**Table 2.** Paired quality deltas (council − single_threshold), 50 seed pairs per condition

| Adversarial rate | Mean delta | 95% Bootstrap CI | Sign-permutation p |
|---|---:|---|---:|
| 0.00 | +24.80 | [17.36, 32.14] | ≈0.00005 |
| 0.18 | +13.06 | [7.79, 18.31] | ≈0.00005 |
| 0.35 | +5.72 | [0.01, 11.69] | ≈0.062 |

At adversarial rates 0.00 and 0.18, the council gate's quality advantage is statistically significant by the sign-permutation test. At rate 0.35, the advantage is directionally positive but does not reach the p < 0.05 threshold; the lower bound of the bootstrap confidence interval barely excludes zero (0.01).

### Key Observations

1. **promote_all is nonviable** under any adversarial rate. Perfect recall is overwhelmed by massive false-promotion penalties, yielding strongly negative quality scores that worsen with increasing adversarial pressure (−2258 at rate 0.00 to −4303 at rate 0.35).

2. **conservative_threshold** achieves the highest precision (~0.968) across all rates but at severe recall cost (~0.34–0.36), resulting in the lowest quality scores among the non-trivial policies.

3. **single_threshold** outperforms council_gated on precision (0.915–0.918 vs. 0.880–0.882), recall (0.748–0.783 vs. 0.662–0.711), and F1 (0.823–0.845 vs. 0.756–0.787). However, it promotes 1.4–1.8× more false memories and consumes 2.0–2.9× more memory budget.

4. **council_gated** achieves the best quality score by reducing false promotions and memory budget, but at the cost of lower recall and F1. This trade-off is favorable only when the quality metric's penalty weighting aligns with deployment priorities.

5. **The council advantage attenuates with adversarial pressure.** The quality delta shrinks from +24.80 to +5.72 as the adversarial rate increases from 0.00 to 0.35, and statistical significance is lost at the highest rate. This suggests the council gate's advantage is most pronounced in low-to-moderate contamination regimes and may not hold under severe adversarial conditions.

## Limitations

1. **Synthetic data only.** All results derive from a synthetic generator with hand-specified attribute distributions and correlations. No real agent memory traces, LangGraph evaluations, or production telemetry were available. The extent to which the synthetic distribution matches real memory candidate streams is unknown, and the results may not generalize.

2. **Threshold calibration on the evaluation distribution.** Council gate thresholds were tuned during smoke testing on the same synthetic distribution used for evaluation. A rigorous evaluation would pre-register thresholds on a training partition and evaluate on held-out data, or validate on qualitatively different distributions. The current results may overestimate the council gate's advantage relative to a setting with pre-registered thresholds.

3. **Quality metric subjectivity.** The quality metric encodes a specific policy preference (false memories cost 1.8× a useful true promotion; review cost is small). If a deployment values recall or F1 more than contamination resistance, single_threshold is the superior policy. The quality metric is not an objective ground-truth measure of memory system goodness; it is a normative choice.

4. **No downstream task evaluation.** The simulation measures promotion-level metrics but does not evaluate whether promoted memories actually improve downstream agent performance on tasks. The ultimate value of a memory gate depends on end-to-end task outcomes, which were not measured.

5. **Limited adversarial model.** The adversarial generator represents one particular failure mode (overconfident, low-reliability candidates). Other attack vectors—gradual corruption, coordinated injection, or exploitation of gate logic—are not modeled.

6. **No real-system integration.** The council gate has not been implemented within an actual agent memory pipeline. Latency, computational overhead, and interaction with existing memory retrieval subsystems are uncharacterized.

7. **Mixed negative result at high adversarial pressure.** The loss of statistical significance at adversarial rate 0.35 (p ≈ 0.062) is a genuine negative finding. It is possible that under more extreme contamination, the council gate offers no meaningful advantage over a simpler baseline.

## Reproducibility Checklist

- **Simulator source**: `scripts/council_memory_sim.py` (dependency-free Python)
- **Analysis source**: `scripts/analyze_results.py`
- **Random seeds**: Base seed 1000 for full runs; seed 1 for smoke tests. 50 seeds per condition.
- **Raw result CSVs**: `results/synthetic_v1_adv_0.00/policy_results.csv`, `results/synthetic_v1_adv_0.18/policy_results.csv`, `results/synthetic_v1_adv_0.35/policy_results.csv`
- **Summary JSONs**: `results/synthetic_v1_adv_0.00/summary.json`, `results/synthetic_v1_adv_0.18/summary.json`, `results/synthetic_v1_adv_0.35/summary.json`
- **Paired statistics**: `results/synthetic_v1_adv_0.00/paired_stats.json`, `results/synthetic_v1_adv_0.18/paired_stats.json`, `results/synthetic_v1_adv_0.35/paired_stats.json`
- **Run logs**: `logs/full_runs.log`, `logs/smoke.log`, `logs/smoke2.log`, `logs/paired_stats_0.00.log`, `logs/paired_stats_0.18.log`, `logs/paired_stats_0.35.log`
- **Decision record**: `.omx/project_decision.json`
- **Environment**: Linux, ~117 GB available RAM, no swap, Python 3, no GPU required
- **Reproduction command**: See run notes for the exact `for` loop over adversarial rates with `--candidates 5000 --seeds 50 --seed 1000`
- **Claim audit status**: The claim ledger for this paper is currently in `blocked_empty_claims` state with no structured claims extracted. This artifact should not be treated as having passed strict claim/evidence audit.

## Conclusion

A council-gated memory promotion policy—requiring concurrent passage of evidence, utility, and skeptic gates—can reduce false durable memory promotions and memory budget consumption relative to a single-threshold baseline, yielding a higher quality score under a metric that heavily penalizes false memories. In synthetic evaluation across three adversarial rates, the council gate achieved the best mean quality score in all conditions, with statistically significant improvements at low and moderate adversarial rates.

However, this advantage comes with honest trade-offs and caveats. The council gate has lower precision, recall, and F1 than the single-threshold baseline. Its quality advantage weakens and loses statistical significance under high adversarial pressure (rate 0.35, p ≈ 0.062). The result is sensitive to the choice of quality metric; under a metric that values recall or F1 more strongly, the single-threshold policy would be preferred. All findings are limited to synthetic data with thresholds calibrated on the same distribution, and the claim ledger has not passed audit.

The council-gated approach is viable as a contamination-control mechanism for durable memory systems where compactness and low false-promotion rates are prioritized over maximum recall. Scientific closure for production deployment requires validation on real agent memory traces with pre-registered thresholds and downstream task evaluation.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Simulator | `scripts/council_memory_sim.py` |
| Analysis script | `scripts/analyze_results.py` |
| Full run log | `logs/full_runs.log` |
| Smoke test logs | `logs/smoke.log`, `logs/smoke2.log` |
| Paired stats logs | `logs/paired_stats_0.00.log`, `logs/paired_stats_0.18.log`, `logs/paired_stats_0.35.log` |
| Policy result CSVs | `results/synthetic_v1_adv_0.00/policy_results.csv`, `results/synthetic_v1_adv_0.18/policy_results.csv`, `results/synthetic_v1_adv_0.35/policy_results.csv` |
| Summary JSONs | `results/synthetic_v1_adv_0.00/summary.json`, `results/synthetic_v1_adv_0.18/summary.json`, `results/synthetic_v1_adv_0.35/summary.json` |
| Paired stats JSONs | `results/synthetic_v1_adv_0.00/paired_stats.json`, `results/synthetic_v1_adv_0.18/paired_stats.json`, `results/synthetic_v1_adv_0.35/paired_stats.json` |
| Project decision | `.omx/project_decision.json` |
| Project metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260430T144448696224+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T144448696224+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T144448696224+0000/paper_manifest.json` |
