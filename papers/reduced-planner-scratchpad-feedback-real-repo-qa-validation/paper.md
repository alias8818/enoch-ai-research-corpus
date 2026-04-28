# Reduced-Planner Scratchpad Feedback for Real-Repository QA: A Validation Study

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We evaluate a reduced-planner scratchpad feedback mechanism for question-answering and information extraction over real repository source code. The approach replaces a conventional verbose planner with a query-only 6-token hidden planner whose first-pass output is amortized across grouped downstream questions via a feedback scratchpad. In live experiments using Qwen2.5-7B (GGUF, local inference) against the llama.cpp repository, the amortized reduced planner matched or exceeded the answer quality of vanilla baselines using 190- and 260-token planner contexts while reducing all-in prompt-like token consumption by 18.9–58.2%, depending on the baseline and feedback budget. On a harder paired-evidence benchmark requiring two source facts per answer, amortized feedback improved equal-budget F1 by up to +24.7 points and evidence recall by up to +65.6 points. However, at tighter baseline budgets (90/130 tokens), fixed planner overhead prevented net all-in savings despite comparable quality, and saturated single-fact conditions were less informative. Results are limited to a single model and repository; confidence is assessed as medium.

## 1. Introduction

Large-language-model (LLM) agents that answer questions over code repositories typically allocate substantial prompt tokens to planning or reasoning scratchpads. These scratchpads help the model organize retrieval and reasoning but consume context window capacity that could otherwise support source material. A natural question arises: can the planner component be compressed—replacing a verbose planning prompt with a minimal query-only planner—without degrading answer quality, and can the savings be amplified by amortizing a single first-pass plan across multiple related questions?

This study tests the following hypothesis: a query-only, 6-token hidden planner preserves equal answer quality while reducing all-in prompt-like tokens by at least 15% on real-repository QA/extraction tasks, with the strongest savings when one first-pass planner call is amortized across multiple related questions. A corresponding kill condition was pre-registered: finalize negative if a real-repo pilot with at least 20 live QA/extraction trials shows no cost-normalized equal-quality match with ≥15% all-in token savings for either per-question or amortized planner accounting, or if gains appear only on saturated or low-quality baselines that do not exercise retrieval.

The experiments use a live OpenAI-compatible inference harness operating on actual local repository files with deterministic answer labels derived from source and documentation, rather than synthetic templates. Two benchmark configurations are reported: an atomic single-fact QA run and a harder paired-evidence run requiring two source facts per answer.

## 2. Method

### 2.1 Reduced-Planner Scratchpad Feedback

The method replaces a conventional planner prompt (190 or 260 tokens of planning instructions and context) with a query-only 6-token hidden planner. The planner emits a compact query representation that is injected into a feedback scratchpad appended to downstream question prompts. Two accounting modes are evaluated:

- **Per-question planning**: each question receives its own planner call, incurring the full planner overhead per question.
- **Amortized planning**: one first-pass planner call covers a group of related questions targeting the same source file, distributing the planner overhead across all questions in the group.

The feedback scratchpad carries the planner output into each downstream question prompt, allowing the model to benefit from structured retrieval guidance without re-planning.

### 2.2 Benchmark Harness

The benchmark harness (`scripts/real_repo_qa_feedback_benchmark.py`) constructs QA/extraction labels from actual local repository files. Source files from the target repository are grouped, and questions are generated with deterministic ground-truth answers derived from the source code and documentation. The harness supports configurable feedback budgets and planner modes.

Two benchmark configurations were run:

1. **Atomic real-repo QA**: 24 cases across 8 source-file groups, yielding 288 answer trials. Each case targets a single source fact.
2. **Hard paired-evidence QA**: 16 paired cases across 8 groups, yielding 192 answer trials. Each case requires two source facts per answer, increasing retrieval difficulty.

### 2.3 Baselines and Conditions

Vanilla baselines use full-length planner prompts (190-token and 260-token variants) with no feedback scratchpad. The reduced-planner conditions use the 6-token hidden planner with feedback budgets of 90 and 130 tokens. All-in prompt-like token counts include planner tokens, feedback scratchpad tokens, and question/context tokens, providing a total cost metric for each condition.

### 2.4 Model and Infrastructure

All runs used Qwen2.5-7B in GGUF format, served via a local `llama-server` instance with OpenAI-compatible API. The target repository was a local clone of llama.cpp. Compilation verification (`python3 -m py_compile`) was performed on all benchmark scripts before live execution. A smoke test (4 cases, 24 trials) confirmed server operation and cleanup before the main experiments.

## 3. Results

### 3.1 Atomic Real-Repository QA

The atomic run completed 24 cases across 8 source-file groups with 288 answer trials.

**Amortized reduced planner vs. vanilla baselines (feedback budget = 90 tokens):**

| Comparison | Vanilla F1 | Reduced F1 | All-in Token Delta |
|---|---|---|---|
| Amortized 6-token planner vs. vanilla 190-token | Matched | Matched | −38.6% |
| Amortized 6-token planner vs. vanilla 260-token | Matched | Matched | −58.2% |

Per-question planning also met the ≥15% all-in savings gate against the 190-token and 260-token vanilla baselines.

**Negative finding at tight baselines:** At the tighter 90-token and 130-token vanilla baselines, the fixed overhead of the planner component prevented net all-in token savings, even though answer quality was equal or near-equal. The reduced planner's 6-token output does not compensate for the additional feedback scratchpad overhead when the baseline itself is already compact.

### 3.2 Hard Paired-Evidence QA

The paired-evidence run completed 16 paired cases across 8 groups with 192 answer trials, requiring two source facts per answer.

**Equal-budget F1 improvements (amortized feedback vs. no feedback):**

| Feedback Budget | F1 Improvement | Evidence-Recall Improvement |
|---|---|---|
| 90 tokens | +24.7 points | +62.5 points |
| 130 tokens | +10.2 points | +65.6 points |

**Cost-normalized quality matches meeting the success gate:**

| Comparison | Vanilla F1 | Amortized Feedback F1 | All-in Token Delta |
|---|---|---|---|
| Vanilla 190 vs. amortized feedback 90 | 0.953 | 0.969 | −18.9% |
| Vanilla 260 vs. amortized feedback 130 | 0.974 | 0.984 | −31.0% |

Per-question feedback also met the ≥15% savings gate for the 190-token and 260-token baselines, though amortization yielded lower all-in costs.

### 3.3 Inference Performance and Resource Utilization

Qwen2.5-7B live answer calls averaged approximately 39–42 completion tokens per second across both runs.

| Metric | Atomic Run | Paired-Evidence Run |
|---|---|---|
| CPU mean | ~5.56% | ~5.55% |
| GPU mean | ~95.8% | ~95.7% |
| RSS range | 0.75–2.07 GB | 0.76–1.81 GB |
| MemAvailable after run | 115.6 GB | 115.9 GB |

No helper `llama-server` process remained after completion, confirming clean process teardown.

## 4. Limitations

1. **Single model.** All results are obtained with Qwen2.5-7B (GGUF). Behavior may differ for other model families, sizes, or quantization levels.
2. **Single repository.** The target repository is llama.cpp. Results may not generalize to repositories with different structure, language distribution, or documentation density.
3. **Medium confidence.** The project decision assigns medium confidence and strong evidence strength within the tested setting, but external replication has not been performed.
4. **Tight-baseline failure mode.** The reduced planner does not yield all-in token savings against compact (90/130-token) vanilla baselines because fixed planner overhead dominates at those budgets. This limits the applicability of the method to settings where vanilla planner prompts are already minimal.
5. **Saturated single-fact conditions.** Single-fact QA cases where the baseline already achieves near-ceiling performance are less informative about the mechanism's benefit, even though they show cost savings against larger vanilla contexts.
6. **No human evaluation.** Answer quality is measured via automated F1 and evidence-recall metrics against deterministic labels. Human preference or correctness judgments are not available.
7. **Automated artifact origin.** This draft and the underlying experiments were produced by an automated research pipeline. The results have not undergone independent human peer review.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Benchmark script available | Yes: `scripts/real_repo_qa_feedback_benchmark.py` |
| Compilation verification performed | Yes: `py_compile` passed before live runs |
| Smoke test performed | Yes: 4 cases / 24 trials |
| Model specified | Yes: Qwen2.5-7B GGUF |
| Target repository specified | Yes: llama.cpp (local clone) |
| Number of trials reported | Yes: 288 (atomic), 192 (paired) |
| Number of source-file groups reported | Yes: 8 |
| All-in token accounting defined | Yes: planner + feedback + question/context |
| Pre-registered hypothesis and kill condition | Yes: ≥15% all-in savings at equal quality |
| Negative results reported | Yes: tight-baseline failure mode |
| Process cleanup verified | Yes: no residual `llama-server` |
| Resource utilization reported | Yes: CPU, GPU, RSS, MemAvailable |
| Result CSVs available | Yes: `live_trial_results.csv` for each run |
| Scratchpad logs available | Yes: `scratchpads.json` for each run |
| Server logs available | Yes: `llama_server.log` for each run |
| Case definitions available | Yes: `cases.json` for each run |
| External replication performed | No |

## 6. Conclusion

The reduced query-only 6-token hidden planner with amortized feedback scratchpad met the pre-registered success criterion of ≥15% all-in prompt-like token savings at equal or better answer quality against 190-token and 260-token vanilla planner baselines. The effect is strongest when the vanilla baseline requires larger context to recover multiple source facts and when the first-pass plan is amortized across related questions. On the harder paired-evidence benchmark, amortized feedback substantially improved both F1 and evidence recall at equal feedback budgets, confirming that the mechanism provides genuine retrieval guidance rather than merely reducing cost.

However, the method does not yield net savings against compact baselines where fixed planner overhead dominates, and saturated single-fact conditions provide limited signal about the mechanism's benefit. These boundary conditions constrain the applicability of the approach.

The current project artifacts support the finding in the tested setting. Replication on a second large repository and additional model is recommended as follow-up work, but is not guaranteed to produce identical results.

## Referenced Artifacts

### Run notes and decision
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Benchmark scripts
- `scripts/real_repo_qa_feedback_benchmark.py`
- `scripts/parent_live_inference_feedback_benchmark.py`
- `scripts/scratchpad_context_benchmark.py`

### Smoke test results
- `results/real_repo_qwen7b_smoke/llama_server.log`
- `results/real_repo_qwen7b_smoke/live_report.md`
- `results/real_repo_qwen7b_smoke/live_summary.json`
- `results/real_repo_qwen7b_smoke/scratchpads.json`
- `results/real_repo_qwen7b_smoke/live_trial_results.csv`
- `results/real_repo_qwen7b_smoke/cases.json`

### Atomic real-repo results
- `results/real_repo_qwen7b_reduced_planner/llama_server.log`
- `results/real_repo_qwen7b_reduced_planner/live_report.md`
- `results/real_repo_qwen7b_reduced_planner/live_summary.json`
- `results/real_repo_qwen7b_reduced_planner/scratchpads.json`
- `results/real_repo_qwen7b_reduced_planner/live_trial_results.csv`
- `results/real_repo_qwen7b_reduced_planner/cases.json`

### Hard paired-evidence results
- `results/real_repo_qwen7b_pair_hard/llama_server.log`
- `results/real_repo_qwen7b_pair_hard/live_report.md`
- `results/real_repo_qwen7b_pair_hard/live_summary.json`
- `results/real_repo_qwen7b_pair_hard/scratchpads.json`
- `results/real_repo_qwen7b_pair_hard/live_trial_results.csv`
- `results/real_repo_qwen7b_pair_hard/cases.json`

### Paper and audit artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/claim_audit.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
