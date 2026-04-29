# Real-Model Negative-Exit Controller on Math and Code Search Traces

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate whether a negative-exit controller—trained to identify and skip candidates unlikely to be correct—can reduce tail latency and expansion count in best-of-N search over language model outputs, while preserving task accuracy. Using a linear controller trained on real-model search traces from Qwen2.5-3B-Instruct (Q4_K_M quantization) served via llama.cpp, we evaluate on 50 tasks (40 GSM8K-style math, 10 MBPP-style code) with 8 candidates per task. At matched 95% task accuracy, the negative-exit controller reduces p95 latency by 0.4034 s (~21.7%) relative to a positive-only baseline, but p95 expansion count remains unchanged at 2.0. Mean latency and mean expansions show small improvements. An earlier 16-task pilot showed no significant difference on any metric. These results support a latency-specific benefit from explicit negative-exit labels at matched accuracy, but do not demonstrate the expansion-tail reduction originally sought. Confidence is medium due to the small held-out set (20 tasks), single model, and single random seed.

---

## 1. Introduction

Best-of-N search over language model outputs is a common strategy for improving task accuracy: generate N candidates, evaluate each, and select the best. The cost of this approach scales linearly with N, and in latency-sensitive settings the tail (p95) cost matters more than the mean. A natural question is whether some candidates can be identified as unlikely to succeed early—before full evaluation—and skipped, reducing both latency and the number of expansions (model evaluations) without sacrificing accuracy.

Prior work on early-exit and speculative decoding has explored related ideas in single-sequence settings. This project investigates a complementary approach: a *negative-exit controller* that operates at the candidate level in a search trace, learning to predict which candidates will fail and exiting them before full evaluation. The controller is trained on labeled search traces where each candidate is marked as correct or incorrect, and at inference time it decides whether to evaluate or skip each candidate.

The central hypothesis is that explicit negative-exit labels allow the controller to prune low-value candidates more effectively than a positive-only baseline (which evaluates candidates in order and stops at the first correct one), yielding reductions in p95 latency and p95 expansion count at matched task accuracy.

A branch kill condition was pre-registered: finalize negative if the real-model trace benchmark shows no p95 expansion or latency reduction at matched task accuracy (within 1 percentage point) versus the positive-only baseline, or if controller savings come only from accuracy loss.

---

## 2. Method

### 2.1 Benchmark Harness

A dependency-free Python benchmark harness (`scripts/real_model_negative_exit_benchmark.py`) was constructed to:

1. Collect candidate traces from an OpenAI-compatible endpoint (llama.cpp server) for GSM8K-style math and MBPP-style code tasks.
2. Label each candidate as correct or incorrect using deterministic answer checking.
3. Train a linear negative-exit controller on labeled traces (train split).
4. Evaluate three strategies on a held-out test split:
   - **Model-order baseline**: evaluate candidates in generation order up to a fixed budget $k$; task success if any of the $k$ candidates is correct.
   - **Positive-only baseline**: evaluate candidates in order, stopping at the first correct candidate; if none found within budget $k$, the task fails.
   - **Negative-exit controller**: for each candidate, the linear controller predicts whether it is likely incorrect; if so, the candidate is skipped (exited) without evaluation. Otherwise, it is evaluated. The controller thus reorders and prunes the candidate list before evaluation.

### 2.2 Controller Training

The negative-exit controller is a linear classifier trained on per-candidate features extracted from the search trace (e.g., generation order, prompt features). The training label is binary: correct (1) or incorrect (0). At inference, the controller's predicted probability of incorrectness is thresholded to make skip/evaluate decisions.

### 2.3 Evaluation Protocol

For each strategy and each budget $k \in \{1, \ldots, 8\}$, we compute:

- **Task accuracy**: fraction of tasks where at least one correct candidate is found within budget $k$.
- **p95 latency**: 95th percentile wall-clock time to task completion (including skipped candidates' overhead).
- **p95 expansions**: 95th percentile number of model evaluations performed.
- **Mean latency** and **mean expansions**: arithmetic means over all test tasks.

The primary comparison is at *matched task accuracy*: we identify the budget $k$ at which each strategy achieves a target accuracy (95%), then compare p95 latency and p95 expansions at that budget.

---

## 3. Results

### 3.1 Pilot Runs and Negative Findings

**Deterministic fixture smoke (10 tasks, 40 candidates).** The harness was validated on synthetic fixtures. Metrics were recorded in `artifacts/mock_smoke_metrics.json`. This confirmed harness correctness but provides no real-model evidence.

**Phi-4-mini attempt.** A Phi-4-mini endpoint was verified and traces were collected, but the model produced unusable malformed outputs with zero oracle accuracy. These traces are retained as acquisition evidence (`artifacts/phi4mini_tiny_metrics.json`) but are excluded from analysis.

**Qwen2.5-3B initial smoke (16 tasks, 4 candidates/task, 64 total candidates).** At matched model-order accuracy of 0.7143, the negative-exit controller showed *no improvement* in p95 expansions (3.0 vs. 3.0) or p95 latency (4.1008 s vs. 4.1008 s) relative to the positive-only baseline. Mean latency was slightly lower (2.5280 s vs. 2.5706 s), but this difference is within noise for 16 tasks. This negative result motivated scaling to a larger benchmark.

### 3.2 Primary Benchmark: Qwen2.5-3B 50×8

**Configuration.** 50 tasks (40 math, 10 code), 8 candidates per task, budgets 1–8. Model: `qwen2.5-3b-instruct-q4_k_m.gguf` served via llama.cpp on port 18085. Train/test split: 30 train, 20 test.

**Trace quality.** 400 candidates total, 245 correct (61.25% candidate-level accuracy), 49/50 tasks with at least one correct candidate (98% oracle task accuracy).

**Matched-accuracy comparison at 95% target.**

| Strategy | Budget $k$ | Task Accuracy | p95 Latency (s) | p95 Expansions | Mean Latency (s) | Mean Expansions |
|---|---|---|---|---|---|---|
| Model-order baseline | 3 | 95% | 4.2002 | 3.0 | — | — |
| Positive-only | 2 | 95% | 1.8558 | 2.0 | — | — |
| Negative-exit | 2 | 95% | 1.4524 | 2.0 | — | — |

**Negative-exit vs. positive-only (both at budget 2, 95% accuracy):**

- p95 latency: 1.4524 s vs. 1.8558 s → **improvement of 0.4034 s (~21.7%)**
- p95 expansions: 2.0 vs. 2.0 → **unchanged**
- Mean latency: improvement of 0.1576 s
- Mean expansions: 1.10 vs. 1.15 → small improvement

**Negative-exit vs. model-order baseline (at 95% accuracy):**

- p95 latency: 1.4524 s vs. 4.2002 s → reduction of 2.7478 s (~65.2%)
- p95 expansions: 2.0 vs. 3.0 → reduction of 1.0 (~33.3%)

The model-order baseline comparison is included for context but is not the primary comparison, since the positive-only baseline already incorporates early stopping and is the more appropriate control.

### 3.3 Summary of Evidence

The larger benchmark supports a p95 latency benefit from the negative-exit controller at matched task accuracy, but does *not* support a p95 expansion benefit. The initial 16-task pilot showed no benefit on any metric. The branch kill condition (no p95 latency or expansion reduction at matched accuracy) is therefore not met, but the evidence is specifically a latency effect, not the expansion-tail effect that was originally targeted.

---

## 4. Limitations

1. **Small held-out set.** The test split contains only 20 tasks. p95 estimates over 20 tasks are noisy; the observed 0.4034 s improvement could shift substantially with more tasks or a different split.

2. **Single model and quantization.** All results are from Qwen2.5-3B-Instruct at Q4_K_M quantization. Generalization to other models, sizes, or quantization levels is untested. The Phi-4-mini attempt failed entirely, illustrating model-specific fragility.

3. **Single random seed.** One data collection seed was used. Variance across seeds is unknown.

4. **p95 expansions unchanged.** The original motivation included reducing the tail number of model evaluations. The negative-exit controller did not achieve this relative to the positive-only baseline at matched accuracy. The benefit is latency-specific, likely arising from skipping the wall-clock time of evaluating predicted-incorrect candidates rather than reducing the count of evaluations that reach the p95 threshold.

5. **Task distribution skew.** The benchmark is 80% math (GSM8K-style) and 20% code (MBPP-style). Results may not generalize to other task mixtures or domains.

6. **Controller simplicity.** The linear controller may be too weak to capture complex patterns in candidate quality. Whether more expressive controllers would yield expansion benefits is an open question.

7. **No external replication.** Results have not been replicated by an independent group or on different hardware.

8. **llama.cpp prototype setting.** The inference server was launched temporarily from `/tmp/enoch_services` for each run and stopped afterward. This is a prototype/hook-prototype setting, not a production deployment. Latency numbers include local server overhead and are not directly comparable to production serving configurations.

---

## 5. Reproducibility Checklist

- **Benchmark harness:** `scripts/real_model_negative_exit_benchmark.py` (dependency-free, OpenAI-compatible endpoint harness)
- **Model:** `qwen2.5-3b-instruct-q4_k_m.gguf` (publicly available GGUF)
- **Inference server:** llama.cpp, launched on port 18085 from `/tmp/enoch_services`
- **Task counts:** 50 tasks (40 math + 10 code), 8 candidates/task, budgets 1–8
- **Train/test split:** 30 train / 20 test
- **Random seed:** single seed (not explicitly recorded in artifacts; see Limitation 3)
- **Primary metrics file:** `artifacts/qwen25_3b_50x8_metrics.json`
- **Trace file:** `artifacts/qwen25_3b_50x8_traces.json`
- **Standard output log:** `artifacts/qwen25_3b_50x8_stdout.txt`
- **Pilot metrics:** `artifacts/qwen25_3b_main_metrics.json` (16-task run)
- **Smoke test metrics:** `artifacts/mock_smoke_metrics.json` (deterministic fixture)
- **Failed model traces:** `artifacts/phi4mini_tiny_metrics.json` (zero oracle accuracy, excluded)
- **Claim audit:** `papers/.../claim_ledger.json`
- **Evidence bundle:** `papers/.../evidence_bundle.json`
- **Project decision:** `.omx/project_decision.json`

---

## 6. Conclusion

A linear negative-exit controller trained on real-model search traces from Qwen2.5-3B-Instruct demonstrates a p95 latency reduction of approximately 21.7% (0.4034 s) relative to a positive-only baseline at matched 95% task accuracy on a 50-task benchmark. However, p95 expansion count is unchanged, and an earlier 16-task pilot showed no significant benefit on any metric. The current project artifacts support a latency-specific finding in the tested setting; they do not demonstrate that the method works universally or that expansion-tail benefits are achievable with this controller class. The result is offered as a positive real-model validation at medium confidence, with the caveat that replication across additional seeds, models, and task distributions is needed to establish robustness.

---

## Referenced Artifacts

### Result and metrics files
- `artifacts/qwen25_3b_50x8_metrics.json` — primary benchmark metrics
- `artifacts/qwen25_3b_50x8_traces.json` — primary benchmark traces
- `artifacts/qwen25_3b_50x8_stdout.txt` — primary benchmark run log
- `artifacts/qwen25_3b_main_metrics.json` — 16-task pilot metrics
- `artifacts/qwen25_3b_main_traces.json` — 16-task pilot traces
- `artifacts/qwen25_3b_main_stdout.txt` — 16-task pilot run log
- `artifacts/qwen25_3b_smoke_metrics.json` — Qwen2.5 smoke metrics
- `artifacts/qwen25_3b_smoke_stdout.txt` — Qwen2.5 smoke run log
- `artifacts/qwen25_3b_smoke_traces.json` — Qwen2.5 smoke traces
- `artifacts/qwen06_smoke_metrics.json` — Qwen0.6 smoke metrics
- `artifacts/qwen06_smoke_stdout.txt` — Qwen0.6 smoke run log
- `artifacts/qwen06_smoke_traces.json` — Qwen0.6 smoke traces
- `artifacts/phi4mini_tiny_metrics.json` — Phi-4-mini metrics (zero oracle accuracy, excluded)
- `artifacts/phi4mini_tiny_stdout.txt` — Phi-4-mini run log
- `artifacts/phi4mini_tiny_traces.json` — Phi-4-mini traces
- `artifacts/mock_smoke_metrics.json` — deterministic fixture smoke metrics
- `artifacts/mock_smoke_stdout.txt` — deterministic fixture smoke run log
- `artifacts/mock_smoke_traces.json` — deterministic fixture smoke traces

### Project and decision files
- `.omx/project_decision.json` — project decision (finalize_positive, supported, medium confidence)
- `.omx/metrics.json` — session metrics
- `.omx/project.json` — project metadata
- `run_notes.md` — chronological run notes
- `RESULTS.md` — results summary
- `scripts/real_model_negative_exit_benchmark.py` — benchmark harness source

### Paper and audit files
- `papers/.../claim_ledger.json` — claim audit with allowed/forbidden wording
- `papers/.../evidence_bundle.json` — evidence bundle
- `papers/.../paper_manifest.json` — paper manifest
