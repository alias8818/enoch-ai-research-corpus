# Bonsai-Up Logprob-Margin Safeguard Deployment Benchmark

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is claimed.

---

## Abstract

We evaluate one-shot logprob-margin gating as a deployment safeguard for cheap-model inference, comparing it against a 3× repeated-sampling baseline on 200 rows of GSM8K across two prompt families (arithmetic-structure and question-shape). The logprob-margin gate accepts 20.5% of rows as cheap at a 0.5 percentage-point accuracy loss relative to all-promoted inference, while achieving a 6.3× wall-clock speedup over the 3× repeated-sampling fallback. However, the repeated-sampling baseline accepts roughly twice as many cheap rows (≈39.0–39.5%) with exact static-baseline recovery. The result is positive but narrow: one-shot logprob-margin gating is a viable latency-reduction safeguard when a small accuracy loss and limited cheap-acceptance rate are acceptable, but it does not dominate repeated sampling when exact accuracy recovery and maximum cheap acceptance are required. Confidence in this finding is medium, bounded by the single dataset, single model profile, and 200-row evaluation scope.

## 1. Introduction

Deploying language models under latency and compute constraints often involves routing inputs between a cheap (fast, small) model and a more capable (slow, large) model. A safeguard gate decides which inputs can safely be served by the cheap model without unacceptable accuracy loss. Two broad strategies exist:

1. **Repeated-sampling gates** that draw multiple stochastic completions from the cheap model and accept the cheap answer only when self-consistency exceeds a threshold.
2. **One-shot uncertainty gates** that inspect the logprob distribution of a single cheap completion and accept when the model's confidence exceeds a threshold.

Repeated-sampling gates can recover the full promoted-model baseline but require multiple forward passes per input, incurring latency proportional to the sample count. One-shot logprob-margin gates require only a single forward pass but may accept fewer cheap rows and may not fully recover baseline accuracy.

This work benchmarks one-shot logprob-margin gating against a 3× repeated-sampling reference on GSM8K rows 400–599, using Bonsai cheap-profile GGUF models served by local `llama-server` instances. We report accuracy, cheap-acceptance fraction, recovered static-loss fraction, and wall-clock latency for both strategies across two prompt families.

## 2. Method

### 2.1 Capture Harness

A Python harness (`capture_logprob_margin_benchmark.py`) launches local `llama-server` instances from `/tmp/enoch_llama_services`, verifies model availability via the `/models` endpoint, and issues one deterministic cheap completion per row with `n_probs=10` to capture the top-10 token logprobs at each position. From the returned logprob distribution, the harness derives the following per-row signals:

- **cheap_first_token_margin**: logprob difference between the top-1 and top-2 tokens at the first generated position.
- **cheap_min_token_prob**: minimum top-1 token probability across all generated positions.
- **cheap_mean_token_prob**: mean top-1 token probability across all generated positions.
- **confidence, margin, entropy**: aggregate uncertainty measures computed from the full logprob distribution.
- **self-consistency**: included for compatibility with the repeated-sampling gate evaluation.

Each `llama-server` instance is stopped after its bucket/model group completes, ensuring no cross-bucket interference.

### 2.2 Gate Evaluation

A separate script (`evaluate_uncertainty_gates.py`) sweeps threshold values over the captured signals to find the gate configuration that maximizes accepted cheap fraction while preserving accuracy within a specified tolerance of the all-promoted baseline. The sweep was run with `--max-values-per-signal 8` and an extended sweep with `--max-values-per-signal 6`.

### 2.3 Baseline

The parent repeated-sampling reference draws 3 stochastic completions per row from the same cheap model and accepts the cheap answer when self-consistency exceeds a threshold. This baseline was captured in a prior run and recorded in `parent_repeated_sampling_gate_review.json`.

### 2.4 Deployment Floor Criteria

The branch was configured with a kill condition: the one-shot logprob-margin gate must preserve all-promoted exact-match accuracy within 0.5 percentage points, accept at least 20% cheap outputs, and demonstrate material latency improvement versus the 3× repeated-sampling fallback. Failure to meet all three criteria would terminate the investigation.

## 3. Results

### 3.1 Arithmetic-Structure Family

| Metric | One-Shot Logprob-Margin Gate | 3× Repeated-Sampling Baseline |
|---|---|---|
| All-promoted accuracy | 0.060 | 0.060 |
| All-cheap one-shot accuracy | 0.025 | — |
| Gated accuracy | 0.055 | 0.060 |
| Accepted cheap fraction | 0.205 | ≈0.395 |
| Recovered static-loss fraction | 0.857 | 1.000 |
| Full capture wall time | 198.90 s | ≈1265 s |
| Mean per-request latency | 0.959 s | — |

### 3.2 Question-Shape Family

| Metric | One-Shot Logprob-Margin Gate | 3× Repeated-Sampling Baseline |
|---|---|---|
| All-promoted accuracy | 0.060 | 0.060 |
| All-cheap one-shot accuracy | 0.025 | — |
| Gated accuracy | 0.055 | 0.060 |
| Accepted cheap fraction | 0.205 | ≈0.390 |
| Recovered static-loss fraction | 0.857 | 1.000 |
| Full capture wall time | 200.07 s | ≈1267 s |
| Mean per-request latency | 0.974 s | — |

### 3.3 Summary of Tradeoffs

- **Latency**: One-shot logprob-margin gating is approximately 6.3× faster in wall-clock time than the 3× repeated-sampling fallback (≈199–200 s vs. ≈1265–1267 s per family).
- **Cheap acceptance**: The logprob-margin gate accepts 20.5% of rows as cheap, roughly half the 39.0–39.5% acceptance rate of the repeated-sampling baseline.
- **Accuracy**: The logprob-margin gate incurs a 0.5 percentage-point accuracy loss relative to all-promoted inference (0.055 vs. 0.060), while the repeated-sampling baseline achieves exact recovery.
- **Recovered static-loss fraction**: The logprob-margin gate recovers 85.7% of the accuracy gap between all-cheap and all-promoted inference.

Both families produce identical numerical outcomes on all metrics, suggesting the gate behavior is not sensitive to the prompt-family distinction within this evaluation scope.

### 3.4 Kill Condition Assessment

The predefined deployment floor criteria are met:

1. Accuracy within 0.5 pp of promoted: 0.5 pp loss exactly meets the threshold (borderline).
2. Cheap acceptance ≥ 20%: 20.5% meets the threshold (borderline).
3. Material latency improvement: 6.3× speedup clearly meets the threshold.

The kill condition is not triggered. However, two of three criteria are met at the margin, and the result should be characterized as narrowly positive rather than robustly positive.

## 4. Limitations

1. **Dataset scope**: Results are reported on GSM8K test rows 400–599 (200 rows) only. Generalization to other datasets, domains, or row ranges is not established.

2. **Model scope**: The evaluation uses Bonsai cheap-profile GGUF models. Results may differ for other model families, sizes, or quantization levels.

3. **Absolute accuracy levels**: The all-promoted accuracy of 0.060 is low, reflecting the limited capability of the cheap model on GSM8K. The 0.5 pp accuracy loss (from 0.060 to 0.055) represents a relative accuracy degradation of approximately 8.3%, which is more consequential than the absolute 0.5 pp figure suggests. On a higher-accuracy cheap model, the same gating threshold might yield different tradeoffs.

4. **Borderline criteria**: Two of the three deployment floor criteria are met at or near the threshold boundary (0.5 pp accuracy loss, 20.5% cheap acceptance). Small perturbations in model, data, or threshold selection could push the result below the floor.

5. **Single-seed evaluation**: Only seed 7 was used. Variance across seeds is not characterized.

6. **No external replication**: These results have not been independently replicated on different hardware or by different researchers.

7. **Identical family outcomes**: The arithmetic-structure and question-shape families produced identical numerical outcomes on all reported metrics. This may indicate that the gate is insensitive to prompt structure in this setting, or it may reflect an artifact of the small sample size or shared model behavior. The cause is not determined.

8. **Latency measurement context**: Wall-clock times include server startup and shutdown overhead per bucket. Per-request latency (≈0.96–0.97 s) reflects single-request timing under sequential execution and no concurrent load. Production deployment with persistent servers and concurrent requests may yield different latency profiles.

9. **No production validation**: These are llama.cpp hook-prototype benchmark results, not final production validation. The harness launches and stops `llama-server` instances per bucket, which differs from a persistent-serving deployment.

## 5. Reproducibility Checklist

- **Code**: `scripts/capture_logprob_margin_benchmark.py`, `scripts/evaluate_uncertainty_gates.py`, `scripts/summarize_logprob_margin_benchmark.py`
- **Data**: `data/logprob_margin_benchmark/gsm8k_test_seed7_rows400_599__arithmetic_structure_v1__logprob_margin_rows.jsonl` (200 rows), `data/logprob_margin_benchmark/gsm8k_test_seed7_rows400_599__question_shape_v1__logprob_margin_rows.jsonl` (200 rows)
- **Smoke data**: `data/logprob_margin_benchmark/smoke_arithmetic_logprob_rows.jsonl`
- **Model source**: Bonsai cheap-profile GGUF models (sibling project `source-record-redacted`)
- **Inference backend**: `llama-server` (llama.cpp), launched from `/tmp/enoch_llama_services`
- **Gate sweep parameters**: `--max-values-per-signal 8` (primary), `--max-values-per-signal 6` (extended)
- **Logprob capture**: `n_probs=10`, deterministic (temperature 0) single completion per row
- **Row range**: GSM8K test, seed 7, rows 400–599
- **Families**: `arithmetic_structure_v1`, `question_shape_v1`
- **Validation performed**: JSON parse verification on all result files and both 200-row JSONL captures; in-memory `compile(...)` syntax checks on all scripts; `__pycache__` cleared; no `llama-server` processes remaining after run

## 6. Conclusion

One-shot logprob-margin gating provides a 6.3× wall-clock speedup over 3× repeated sampling on the evaluated GSM8K subset, at the cost of a 0.5 percentage-point accuracy loss and roughly half the cheap-acceptance rate. The method meets the predefined deployment floor criteria, but does so narrowly: the accuracy and acceptance thresholds are met at the boundary, and the gate does not dominate repeated sampling on either accuracy recovery or cheap-acceptance rate.

The finding supports the use of one-shot logprob-margin gating as a deployment safeguard only when the specific tradeoff profile—moderate latency reduction, limited cheap acceptance, small accuracy loss—is acceptable for the application. When exact baseline recovery or maximum cheap acceptance is required, repeated sampling remains the stronger approach.

This result is bounded by the evaluation scope (200 rows, one dataset, one model profile, one seed) and has not been externally replicated. Broader evaluation across datasets, models, and seeds is needed before drawing general conclusions about logprob-margin gating as a deployment safeguard.

---

## Referenced Artifacts

### Result files
- `results/uncertainty_gates/logprob_margin_deployment_review.json`
- `results/uncertainty_gates/gsm8k_test_seed7_rows400_599__arithmetic_structure_v1__logprob_margin_gate_summary.json`
- `results/uncertainty_gates/gsm8k_test_seed7_rows400_599__arithmetic_structure_v1__logprob_margin_extended_gate_summary.json`
- `results/uncertainty_gates/gsm8k_test_seed7_rows400_599__arithmetic_structure_v1__logprob_margin_manifest.json`
- `results/uncertainty_gates/gsm8k_test_seed7_rows400_599__question_shape_v1__logprob_margin_gate_summary.json`
- `results/uncertainty_gates/gsm8k_test_seed7_rows400_599__question_shape_v1__logprob_margin_extended_gate_summary.json`
- `results/uncertainty_gates/gsm8k_test_seed7_rows400_599__question_shape_v1__logprob_margin_manifest.json`
- `results/uncertainty_gates/smoke_arithmetic_logprob_manifest.json`
- `results/uncertainty_gates/parent_repeated_sampling_gate_review.json`

### Data files
- `data/logprob_margin_benchmark/gsm8k_test_seed7_rows400_599__arithmetic_structure_v1__logprob_margin_rows.jsonl`
- `data/logprob_margin_benchmark/gsm8k_test_seed7_rows400_599__question_shape_v1__logprob_margin_rows.jsonl`
- `data/logprob_margin_benchmark/smoke_arithmetic_logprob_rows.jsonl`

### Scripts
- `scripts/capture_logprob_margin_benchmark.py`
- `scripts/evaluate_uncertainty_gates.py`
- `scripts/summarize_logprob_margin_benchmark.py`

### Decision and metadata
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `run_notes.md`

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
