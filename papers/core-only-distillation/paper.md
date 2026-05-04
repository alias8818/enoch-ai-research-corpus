# Core-Only Distillation: Fact-Masked Supervision Improves Low-Data Planning Accuracy and Factual Humility Under Entity Shift — A Synthetic Benchmark Study

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, and benchmark outputs). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

We investigate whether supervising a student model on strategy-oriented signals (plans, checks, and tool decisions) while masking factual tokens produces measurable improvements in planning accuracy and factual humility under distribution shift. Using a synthetic benchmark with four planning classes and a Naive Bayes student model, we compare core-fact-masked prompts against unmasked (raw-answer-like) prompts under an out-of-distribution entity shift that reverses entity–action correlations present in training. Across 25 random seeds at low training sizes (n = 16, 32), core-fact-masked supervision yields small but statistically distinguishable gains: a paired mean delta of +0.032 in planning accuracy (approximate 95% CI [0.009, 0.054]) and +0.041 in humility F1 (approximate 95% CI [0.003, 0.078]) at n = 16. The humility F1 advantage persists at n = 32 (+0.040, 95% CI [0.020, 0.060]), though the planning accuracy delta narrows to include zero (+0.011, 95% CI [−0.003, 0.025]). All conditions saturate to ceiling performance by n = 128, and a random-masking control frequently approximates core masking, weakening claims about the specificity of the masking policy. These results constitute a bounded, low-data toy signal supporting fact-shortcut removal as a mechanism, but do not constitute evidence that core-only distillation transfers to real language model distillation or complex workflows.

## 1. Introduction

Standard knowledge distillation trains a student model to reproduce the factual outputs of a teacher. This approach risks transferring surface-level factual associations rather than the teacher's decision-making strategies—its plans, verification checks, and tool-selection patterns. If a student learns to associate entity names with actions (e.g., "Acme Corp → LOOKUP"), it may fail systematically when those correlations shift at deployment.

The core-only distillation hypothesis proposes an alternative: supervise the student on strategy-oriented signals while masking factual tokens (entities, numbers, dates, codes), preserving only task verbs and structural cues. The intended effect is twofold: (1) remove factual shortcuts that enable spurious correlation between entity identity and planning action, and (2) encourage a factual humility signal—learning when to abstain or seek external information rather than guess.

This paper reports results from a mechanistic synthetic benchmark designed to test the most bounded version of this hypothesis: does fact-masked/core-only supervision produce a measurable planning and factual-humility signal under factual shortcut shift, compared to unmasked supervision? We deliberately restrict the study to a toy regime (synthetic data, Naive Bayes classifier) to isolate the data-quality and masking mechanism before investing in neural distillation at scale. This is a mechanistic probe of shortcut removal and strategy-label learnability, not a real LLM distillation run.

## 2. Method

### 2.1 Benchmark Design

We constructed a dependency-free synthetic benchmark (`experiments/core_only_distillation.py`) generating four planning classes:

- **CALCULATE**: use a calculator; perform a unit check.
- **LOOKUP**: use retrieval; perform a source-date check.
- **COMPARE**: compare options; perform a criteria check.
- **CLARIFY**: missing required facts; exhibit do-not-guess humility.

Training data intentionally correlates entity names with planning actions. The out-of-distribution (OOD) evaluation split reverses these entity–action correlations, creating a factual shortcut shift: models that rely on entity–action associations from training will systematically misclassify at evaluation.

### 2.2 Conditions

Four supervision conditions were compared:

1. **majority**: Class-prior baseline (predict the most frequent class).
2. **raw_answer_like**: Train and infer on unmasked prompts, allowing factual/entity shortcuts.
3. **random_mask_control**: Mask non-core tokens randomly, controlling for generic masking effects.
4. **core_fact_masked**: Mask entities, numbers, dates, and codes while preserving task verbs and structural cues.

### 2.3 Student Model

A Naive Bayes classifier serves as the student model. This choice deliberately sacrifices neural representational capacity to isolate whether the masking mechanism itself produces learnable strategy signals from the data. It tests data quality and shortcut removal, not neural distillation at scale. A bag-of-words model cannot capture the sequential or contextual reasoning that a transformer-based student might leverage or lose under masking.

### 2.4 Evaluation Metrics

- **Planning accuracy**: Correct classification into the four planning classes on OOD data.
- **Humility F1**: F1 score on the CLARIFY class specifically, measuring the model's ability to recognize when facts are missing and abstain from guessing.

### 2.5 Experimental Protocol

Two runs were conducted:

- **Smoke test**: train_sizes = [16], eval_n = 40, seeds = 2, to validate the pipeline.
- **Full run**: train_sizes = [16, 32, 64, 128, 256], eval_n = 500 per split per seed, 25 seeds.

All runs were CPU-only on a Linux aarch64 host with approximately 117 GB available memory and no swap. No GPU or GB10 calibration was required or performed.

### 2.6 Statistical Analysis

We computed paired seed deltas (core_fact_masked − raw_answer_like) for each metric at each training size, reporting mean, standard deviation, standard error, and approximate 95% confidence intervals across the 25 seeds. Confidence intervals are approximate (mean ± 1.96 × SE) and assume approximate normality of the paired delta distribution.

## 3. Results

### 3.1 OOD Entity-Shift Performance

Table 1 reports mean planning accuracy and humility F1 for the two primary conditions under OOD entity shift.

**Table 1.** OOD entity-shift metrics by training size and condition (25 seeds, eval_n = 500).

| train_n | condition | planning accuracy (mean) | humility F1 (mean) |
|--------:|-----------|------------------------:|-------------------:|
| 16 | raw_answer_like | 0.818 | 0.813 |
| 16 | core_fact_masked | 0.850 | 0.854 |
| 32 | raw_answer_like | 0.935 | 0.926 |
| 32 | core_fact_masked | 0.946 | 0.966 |
| 256 | raw_answer_like | 1.000 | 1.000 |
| 256 | core_fact_masked | 1.000 | 1.000 |

Both conditions converge to ceiling performance by n = 256. The core_fact_masked condition shows a consistent low-data advantage that diminishes as training size increases.

### 3.2 Paired Delta Analysis

Table 2 reports paired deltas (core_fact_masked − raw_answer_like) across seeds.

**Table 2.** Paired seed deltas on OOD evaluation (25 seeds).

| train_n | metric | paired Δ mean | SD | SE | approx. 95% CI |
|--------:|--------|-------------:|------:|------:|---------------:|
| 16 | planning accuracy | +0.032 | 0.058 | 0.012 | [0.009, 0.054] |
| 16 | humility F1 | +0.041 | 0.096 | 0.019 | [0.003, 0.078] |
| 32 | planning accuracy | +0.011 | 0.035 | 0.007 | [−0.003, 0.025] |
| 32 | humility F1 | +0.040 | 0.052 | 0.010 | [0.020, 0.060] |
| 64 | planning accuracy | −0.005 | 0.018 | 0.004 | [−0.013, 0.002] |
| 64 | humility F1 | +0.003 | 0.010 | 0.002 | [−0.001, 0.007] |

At n = 16, both planning accuracy and humility F1 show positive deltas with confidence intervals excluding zero, indicating a statistically distinguishable (though small) advantage for core-fact-masked supervision. At n = 32, the humility F1 advantage remains with the confidence interval excluding zero, but the planning accuracy delta crosses zero and is no longer statistically distinguishable. By n = 64, neither metric shows a significant difference; the planning accuracy delta is slightly negative (−0.005, 95% CI [−0.013, 0.002]).

The humility F1 signal is more robust than the planning accuracy signal across the low-data regime, persisting at n = 32 where the accuracy advantage is no longer significant.

### 3.3 Random Mask Control

The random_mask_control condition was often close to core_fact_masked in performance. This result weakens the claim that the specific core-only masking policy is uniquely responsible for the observed gains; rather, the evidence more strongly supports the general mechanism of shortcut removal through masking, regardless of whether the masking targets factual tokens specifically or randomly. The toy result supports shortcut removal more strongly than a uniquely core-only target format.

### 3.4 Saturation Behavior

All non-majority conditions reach near-ceiling performance by n = 128. The benchmark therefore cannot estimate scaling behavior beyond low-data regimes and provides no evidence about whether core-only masking would help, hurt, or be neutral at larger training sizes in more complex settings. The signal is strictly low-data.

## 4. Limitations

1. **Synthetic data and Naive Bayes student.** The benchmark uses procedurally generated prompts and a bag-of-words classifier. This tests the data-quality and masking mechanism in isolation but does not constitute evidence for or against core-only distillation in real neural language models. A Naive Bayes model cannot capture the sequential or contextual reasoning that a transformer-based student might leverage or lose under masking.

2. **Rapid saturation.** The task saturates by n = 128 training examples, making it impossible to estimate whether the low-data advantage persists, disappears, or reverses at scale. The signal is strictly low-data and the benchmark cannot estimate scaling behavior.

3. **Random masking proximity.** The random_mask_control condition often approximates core_fact_masked, suggesting that the observed gains may stem from generic shortcut disruption rather than from preserving specifically task-relevant cues. This weakens claims about the uniqueness of the core-only masking policy.

4. **No real-model validation.** No fine-tuning of an actual language model was performed. The results support a mechanistic claim about shortcut removal in a controlled setting, not the stronger claim that a distilled cognitive core will transfer to messy real-world workflows.

5. **Narrow distribution shift.** The OOD shift is limited to entity–action correlation reversal. Real deployment shifts may involve vocabulary drift, task distribution change, or novel planning classes not represented in the benchmark.

6. **Limited class structure.** Four planning classes with clear verbal cues may overestimate the learnability of strategy signals. Real planning decisions often lack such explicit markers.

7. **High variance at low n.** At n = 16, the standard deviation of the humility F1 paired delta (0.096) is large relative to the mean (0.041), indicating substantial seed-to-seed variability. The positive mean should be interpreted cautiously.

## 5. Reproducibility Checklist

- **Code availability:** `experiments/core_only_distillation.py` — dependency-free Python script.
- **Random seeds:** 25 seeds per training size; results reported as means and paired deltas across seeds.
- **Hardware:** CPU-only; Linux aarch64, approximately 117 GB RAM, no swap. No GPU required.
- **Software:** Python (version recorded in `logs/environment.log`); no external ML framework dependencies.
- **Data generation:** Synthetic; fully determined by the script. No external datasets.
- **Statistical reporting:** Paired deltas with standard deviations, standard errors, and approximate 95% confidence intervals across 25 seeds.
- **Full logs:** `logs/core_only_distillation_smoke.log`, `logs/core_only_distillation_full.log`, `logs/environment.log`.
- **Raw data:** `results/core_only_distillation/raw_metrics.csv`, `results/core_only_distillation/paired_core_vs_raw.json`, `results/core_only_distillation/example_records.jsonl`.
- **Aggregated summaries:** `results/core_only_distillation/summary.md`, `results/core_only_distillation/summary.json`, `results/core_only_distillation/summary_metrics.csv`.
- **Claim audit status:** The claim ledger for this paper is in `blocked_empty_claims` status; no structured claims have been extracted and the artifact has not passed strict claim/evidence audit.

## 6. Conclusion

Core-fact-masked supervision produces a small but statistically distinguishable improvement in planning accuracy and factual humility under entity-shift distribution shift at very low training sizes (n = 16–32) in a synthetic benchmark with a Naive Bayes student. The humility F1 signal is more robust than the planning accuracy signal, persisting at n = 32 where the accuracy advantage is no longer significant. However, three factors substantially limit the strength of these findings: (1) the effect is confined to a low-data regime and saturates quickly, (2) random masking approximates core masking, supporting shortcut removal generally rather than a uniquely core-only policy, and (3) the synthetic, bag-of-words setting does not test neural distillation.

The evidence supports the bounded claim that removing factual shortcuts from training data can improve strategy-label learnability under distribution shift, particularly for abstention/humility signals. It does not support the stronger claim that core-only distillation will transfer to real language model fine-tuning or complex workflows. The recommended next step is a real small-LM smoke test: collect or synthesize teacher plan/check/tool traces, mask fact spans, fine-tune a tiny student model, and evaluate on held-out workflows with answer correctness separated from planning accuracy and calibrated abstention.

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Experiment script | `experiments/core_only_distillation.py` |
| Smoke test log | `logs/core_only_distillation_smoke.log` |
| Full run log | `logs/core_only_distillation_full.log` |
| Environment log | `logs/environment.log` |
| Summary (Markdown) | `results/core_only_distillation/summary.md` |
| Summary (JSON) | `results/core_only_distillation/summary.json` |
| Summary metrics (CSV) | `results/core_only_distillation/summary_metrics.csv` |
| Raw metrics (CSV) | `results/core_only_distillation/raw_metrics.csv` |
| Paired deltas (JSON) | `results/core_only_distillation/paired_core_vs_raw.json` |
| Example records | `results/core_only_distillation/example_records.jsonl` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260430T110834979580+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T110834979580+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T110834979580+0000/paper_manifest.json` |
