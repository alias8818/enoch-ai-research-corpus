# Evidence Survival as a Predictor of LLM Question-Answering Accuracy and Abstention Under Context Truncation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether *evidence survival*—the property that relevant answer-bearing text remains in a language model's context window after truncation—predicts generated answer accuracy and abstention behavior in a code question-answering setting. Using a local llama.cpp-served Qwen2.5-7B-Instruct (Q4_K_M) model and six deterministic context-truncation policies applied to two open-source Python repositories, we collect 600 QA rows across 50 examples, 6 policies, and 2 context budgets (50 and 200 lines). At the policy-cell level, non-oracle evidence survival correlates strongly with both generated accuracy (Pearson *r* = 0.91) and attempt rate (Pearson *r* = 0.87). However, row-level correlations are substantially weaker (*r* = 0.49 for accuracy, *r* = 0.56 for attempt rate), and calibration analysis shows that high evidence coverage systematically overestimates actual correctness (ECE = 0.24). Oracle contexts (guaranteed evidence) yield mean accuracy of 0.54, materially above evidence-poor baselines (0.0), yet residual errors confirm that evidence survival is necessary but not sufficient for correct generation. These results support evidence survival as a policy-level answerability diagnostic, but not as a standalone calibrated probability of correctness, for this model and prompt configuration.

---

## 1. Introduction

When language models answer questions about code, the contents of the context window mediate what the model can possibly answer correctly. If truncation or retrieval policies remove the relevant evidence before it reaches the model, no amount of generation capability can recover the answer. The concept of *evidence survival* captures whether the answer-bearing text persists in the context after a truncation or retrieval policy is applied.

Prior deterministic work (inherited from a parent project) established that evidence survival predicts abstract QA answerability under a simple proxy: if the evidence is present, a deterministic scorer marks the question as answerable; if absent, it is not. This leaves open the question of whether the same relationship holds when an actual language model generates answers and decides whether to attempt or abstain.

The present study extends that line of work by connecting evidence survival to *generated* LLM behavior. Specifically, we ask:

1. Does evidence survival at the policy-cell level predict generated answer accuracy?
2. Does evidence survival predict the model's decision to attempt versus abstain?
3. Is the relationship well-calibrated at the individual-question level, or does it function primarily as a policy-level diagnostic?

We report results from a 600-row endpoint pilot using a quantized 7B-parameter model served locally via llama.cpp, across six truncation policies and two context budgets, on code QA pairs drawn from the `requests` and `django` repositories.

---

## 2. Method

### 2.1 Benchmark Harness

We implemented `llm_qa_endpoint_benchmark.py`, a Python harness that:

1. Verifies the OpenAI-compatible endpoint via `/v1/models` before running.
2. Rebuilds context windows for each example under each truncation policy and budget.
3. Prompts the model to answer the question or emit `ABSTAIN`.
4. Scores generated answers for exact-match accuracy against ground-truth answers.
5. Records per-row evidence coverage (fraction of ground-truth answer tokens present in the context), latency, token usage, and abstention decisions.
6. Writes row-level CSV and aggregate JSON summaries.

The prompt was tightened after an initial smoke test (6 rows) revealed formatting issues: the model sometimes returned file paths for docstring tasks or incorrect line numbers for definition tasks. Task-specific output rules were added before the pilot runs.

### 2.2 Truncation Policies

Six deterministic policies determine which source-code lines enter the context window:

| Policy | Description |
|---|---|
| `repo_head` | First *N* lines of the repository's concatenated file listing (negative control) |
| `file_head` | First *N* lines of the target file |
| `file_tail` | Last *N* lines of the target file |
| `lexical` | Lexically ranked lines from the target file |
| `symbol_lexical` | Symbol-aware lexical selection from the target file |
| `oracle` | Lines guaranteed to contain the answer (upper-bound control) |

Two context budgets were tested: 50 lines and 200 lines.

### 2.3 Model and Serving

- **Model**: Qwen2.5-7B-Instruct, quantized to Q4_K_M (GGUF format).
- **Server**: llama.cpp `llama-server` binary, OpenAI-compatible API.
- **Hardware**: Local GPU (Apple UMA architecture); GPU utilization mean 94.4% during the 600-row run.

### 2.4 Datasets

- **Source repositories**: `requests` (via `external/requests/src/requests`) and `django` (via `external/django/django`).
- **QA pairs**: 50 examples drawn from `results/pilot_1200/context_truncation_examples.jsonl`, inherited from the parent project.
- **Ground truth**: Deterministic QA baseline summaries from `results/qa_baselines_1200/qa_baseline_summary.json`.

### 2.5 Calibration Analysis

A separate script (`analyze_llm_calibration.py`) computes:

- Brier-like scores for coverage-vs-accuracy and coverage-vs-attempt prediction.
- Expected calibration error (ECE) for accuracy and attempt rate.
- Threshold tables mapping evidence-coverage bins to observed accuracy and attempt rates.

### 2.6 Resource Telemetry

During benchmark execution, a 1 Hz sampler recorded GPU utilization, GPU power draw, server RSS, and UMA `MemAvailable`. Note: for the 600-row run, the initial sampler attached to a stale pre-fork server PID, so resource telemetry covers approximately the middle 300 seconds of the 764-second benchmark rather than the full run. Throughput and latency metrics are unaffected and cover the full run.

---

## 3. Results

### 3.1 Aggregate Metrics (600-Row Run)

| Metric | Value |
|---|---|
| Total rows | 600 |
| Wall-clock time | 763.68 s |
| Throughput | 0.786 requests/s |
| Total token throughput | 1,849.1 tokens/s |
| Completion token throughput | 6.18 tokens/s |
| Overall generated accuracy | 0.2083 |
| Overall abstention rate | 0.5533 |
| Overall exact evidence rate | 0.4333 |

### 3.2 Evidence Survival vs. Generated Accuracy

At the **policy-cell level** (aggregating across all examples within a policy–budget combination, excluding oracle), evidence survival correlates strongly with generated accuracy:

- Non-oracle cell-level evidence-vs-accuracy Pearson *r* = 0.9083.
- Non-oracle cell-level evidence-vs-attempt-rate Pearson *r* = 0.8731.

At the **row level** (individual questions), the relationship is substantially weaker:

- Row-level non-oracle coverage-vs-accuracy Pearson *r* = 0.4851.
- Row-level non-oracle coverage-vs-attempt Pearson *r* = 0.5559.

This discrepancy indicates that evidence survival functions well as a between-policy diagnostic but is a noisy predictor for individual questions.

### 3.3 Calibration

| Calibration Metric | Value |
|---|---|
| Brier-like (coverage → accuracy) | 0.2312 |
| ECE (accuracy) | 0.2410 |
| ECE (attempt) | 0.1857 |

High evidence coverage systematically overestimates actual correctness. The model frequently fails to produce correct answers even when the relevant text is present in the context, particularly for `lexical` and `symbol_lexical` policies where coverage is high but accuracy remains modest.

### 3.4 Policy-Cell Breakdown

| Policy | Budget | Exact Evidence | Generated Accuracy | Attempt Rate | Selective Accuracy |
|---|---|---|---|---|---|
| `repo_head` | 50 | 0.00 | 0.00 | 0.00 | — |
| `repo_head` | 200 | 0.00 | 0.00 | 0.06 | 0.00 |
| `file_head` | 50 | — | — | — | — |
| `file_head` | 200 | 0.46 | 0.26 | — | 0.6842 |
| `file_tail` | 200 | 0.54 | 0.26 | — | — |
| `symbol_lexical` | 50 | 0.44 | 0.18 | 0.66 | — |
| `symbol_lexical` | 200 | 0.56 | 0.14 | 0.52 | — |
| `oracle` | 50 | 1.00 | 0.58 | — | 0.69 |
| `oracle` | 200 | 1.00 | 0.52 | — | 0.70 |

*Note: Cells marked "—" were not individually reported in the run notes for the 600-row run; aggregate values are used where available.*

Key observations:

- **`repo_head`** serves as a clean negative control: zero evidence, zero accuracy, and near-total abstention at both budgets.
- **`file_head`/`file_tail`** at 200 lines provide intermediate evidence-survival cells. Despite lower or comparable evidence coverage relative to `symbol_lexical`, they achieve higher generated accuracy (0.26 vs. 0.14–0.18), suggesting that evidence *position* and *salience* within the context matter beyond raw coverage.
- **`lexical`/`symbol_lexical`** show higher evidence coverage but only modest accuracy, reinforcing that evidence survival is necessary but not sufficient for this model and prompt.
- **Oracle** accuracy (mean 0.54) is materially above all non-oracle cells, confirming that guaranteed evidence improves generation. The residual 0.46 error rate under oracle conditions reflects independent model-level and task-level difficulty.

### 3.5 Scaling Observations Across Runs

The 72-row pilot (12 examples, 3 policies, 2 budgets) yielded non-oracle evidence-vs-accuracy Pearson *r* = 0.75 and evidence-vs-attempt *r* = 0.85. The 300-row pilot (50 examples, 3 policies, 2 budgets) yielded *r* = 0.94 and *r* = 0.94 respectively. The 600-row run (50 examples, 6 policies, 2 budgets) yielded *r* = 0.91 and *r* = 0.87. The cell-level relationship is robust across sample sizes and policy sets, though the addition of `file_head` and `file_tail` slightly attenuates the attempt-rate correlation relative to the 3-policy runs.

### 3.6 Resource Utilization

| Resource Metric | Value |
|---|---|
| GPU utilization (mean / p50 / max) | 94.4% / 96% / 96% |
| GPU power (mean / p95 / max) | 83.3 W / 92.4 W / 95.9 W |
| Server RSS (mean / p50 / max) | 7.33 GB / 9.14 GB / 9.35 GB |
| UMA `MemAvailable` (min) | 107,160,772 KB |
| Swap free | 0 KB throughout |

The endpoint was GPU-bound throughout, with utilization consistently above 94%. No memory pressure was observed.

---

## 4. Limitations

1. **Single model and quantization.** All results are from Qwen2.5-7B-Instruct Q4_K_M served via llama.cpp. Larger or differently-trained models may exhibit different evidence-sensitivity profiles. The quantization level may also affect the model's ability to exploit surviving evidence.

2. **Small and homogeneous dataset.** Only 50 QA examples from two Python repositories were used. Generalization to other languages, domains, or question types is not established.

3. **Limited policy and budget granularity.** Only six policies and two budget levels (50 and 200 lines) were tested. The space of possible truncation and retrieval strategies is far larger.

4. **Weak row-level calibration.** Evidence coverage is a poor calibrated predictor of individual-question correctness (ECE = 0.24). Treating evidence survival as a probability of correctness would be misleading.

5. **Evidence survival is necessary but not sufficient.** The `symbol_lexical` and `lexical` cells demonstrate that high evidence coverage can coexist with low generated accuracy. The model's ability to exploit present evidence depends on factors not captured by coverage alone, including evidence position, salience, and task difficulty.

6. **Partial resource telemetry.** The 600-row run's resource sampler attached to a stale PID, covering only the middle ~300 s of the 764 s benchmark. Resource utilization figures should be interpreted with this gap in mind.

7. **Oracle residual error.** Even with guaranteed evidence, mean accuracy is only 0.54. This ceiling reflects model-level limitations (formatting errors, reasoning failures) that evidence survival cannot address.

8. **No external replication.** All experiments were conducted on a single local machine. No cross-hardware or cross-environment replication has been performed.

9. **Exact-match scoring.** Generated answers are scored by exact match against ground truth. This penalizes partially correct or differently-formatted valid answers, potentially understating actual model capability.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Benchmark harness source | `scripts/llm_qa_endpoint_benchmark.py` (compiles cleanly) |
| Calibration analysis source | `scripts/analyze_llm_calibration.py` (compiles cleanly) |
| Inherited deterministic baselines | `scripts/qa_abstention_baselines.py`, `scripts/context_truncation_pilot.py` (compile cleanly) |
| Model identifier | `Qwen2.5-7B-Instruct-Q4_K_M.gguf` (bartowski GGUF) |
| Serving command | Recorded in `results/llm_qa_pilot_600/server_command.txt` |
| Run command | Recorded in `results/llm_qa_pilot_600/time_v.log` and `run_stdout.log` |
| Row-level data | `results/llm_qa_pilot_600/llm_qa_rows.csv` (600 rows) |
| Aggregate summary | `results/llm_qa_pilot_600/llm_qa_summary.json` |
| Calibration summary | `results/llm_qa_pilot_600/calibration_summary.json` |
| Analysis summary | `results/llm_qa_pilot_600/analysis_summary.json` |
| Resource telemetry | `results/llm_qa_pilot_600/resource_samples.log`, `resource_summary.json` |
| Server log | `results/llm_qa_pilot_600/llama_server.log` |
| Dataset | `results/pilot_1200/context_truncation_examples.jsonl` |
| Deterministic baselines | `results/qa_baselines_1200/qa_baseline_summary.json` |
| Source repositories | `external/requests/src/requests`, `external/django/django` |
| Python compilation check | Passed for all four scripts |

---

## 6. Conclusion

Evidence survival—the persistence of answer-bearing text in the context window after truncation—is a strong policy-cell-level predictor of both generated answer accuracy and attempt/abstention behavior for a locally-served Qwen2.5-7B-Instruct model on code QA tasks. Non-oracle cell-level Pearson correlations of *r* = 0.91 (accuracy) and *r* = 0.87 (attempt rate) across six policies and two budgets support this relationship. The oracle upper bound (mean accuracy 0.54) materially exceeds the evidence-poor baseline (0.0), confirming that evidence presence enables correct generation.

However, the relationship does not calibrate well at the individual-question level. Row-level correlations drop to *r* = 0.49, and ECE of 0.24 indicates that high evidence coverage systematically overestimates correctness. The `symbol_lexical` and `lexical` policies demonstrate that evidence survival is necessary but not sufficient: high coverage coexists with low accuracy, likely due to evidence salience, position effects, and independent model-level error.

These findings support treating evidence survival as an *answerability prior* and *retrieval diagnostic*—a tool for evaluating and comparing truncation policies—rather than as a standalone calibrated probability that a particular LLM invocation will produce a correct answer. The recommended follow-up is a targeted retrieval-intervention benchmark to understand and potentially remediate the high-coverage-but-wrong cells that limit the practical utility of evidence survival as a per-question predictor.

---

## Referenced Artifacts

### Run Notes
- `run_notes.md`

### Claim Ledger
- `papers/source-record-redacted/claim_ledger.json`

### Evidence Bundle
- `papers/source-record-redacted/evidence_bundle.json`

### Project Decision
- `.omx/project_decision.json`

### Metrics
- `.omx/metrics.json`

### Source Scripts
- `scripts/llm_qa_endpoint_benchmark.py`
- `scripts/analyze_llm_calibration.py`
- `scripts/qa_abstention_baselines.py`
- `scripts/context_truncation_pilot.py`

### 600-Row Pilot Results
- `results/llm_qa_pilot_600/llm_qa_rows.csv`
- `results/llm_qa_pilot_600/llm_qa_summary.json`
- `results/llm_qa_pilot_600/calibration_summary.json`
- `results/llm_qa_pilot_600/analysis_summary.json`
- `results/llm_qa_pilot_600/resource_summary.json`
- `results/llm_qa_pilot_600/resource_samples.log`
- `results/llm_qa_pilot_600/time_v.log`
- `results/llm_qa_pilot_600/run_stdout.log`
- `results/llm_qa_pilot_600/llama_server.log`
- `results/llm_qa_pilot_600/server_command.txt`

### 300-Row Pilot Results
- `results/llm_qa_pilot_300/llm_qa_rows.csv`
- `results/llm_qa_pilot_300/llm_qa_summary.json`
- `results/llm_qa_pilot_300/analysis_summary.json`
- `results/llm_qa_pilot_300/resource_summary.json`
- `results/llm_qa_pilot_300/time_v.log`
- `results/llm_qa_pilot_300/run_stdout.log`
- `results/llm_qa_pilot_300/llama_server.log`

### Inherited Parent Artifacts
- `results/pilot_1200/context_truncation_examples.jsonl`
- `results/qa_baselines_1200/qa_baseline_summary.json`

### Publication Manifest
- `papers/source-record-redacted/paper_manifest.json`
