# Short-Model Long-Task Distillation: Can Compact State Transitions Enable Horizon Extrapolation?

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, benchmark metrics). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated these claims.

---

## Abstract

We investigate whether a model trained on short-horizon examples can correctly execute tasks far exceeding its training horizon when distillation supplies compact local state transitions rather than opaque final-answer labels. Using a deterministic modular-arithmetic benchmark (modulus 97, operations `add`, `sub`, `mul`), we compare three distillation surfaces: (1) direct final-answer distillation via a linear classifier, (2) learned transition distillation via a decision tree on teacher-generated local state transitions, and (3) a compiled finite-state transition table. Training examples use sequence length 16; evaluation extends to length 1024 (a 64× extrapolation factor). Direct final-answer distillation remains at chance accuracy (~1.0%) across all evaluation horizons, including the training horizon. Both transition-based approaches achieve exact accuracy (1.000) at all evaluated lengths, including length 1024. The compiled transition table requires 56,454 bytes and processes 11,555 length-1024 examples per second on CPU. These results are confined to a synthetic deterministic domain with a known state schema; they do not demonstrate automatic latent-state discovery or transfer to natural-language agent tasks.

---

## Introduction

A practical challenge in deploying compact models for long-horizon tasks is that training data and context windows are typically short, while deployment demands may involve task horizons far exceeding those seen during training. If a small model must execute a multi-step procedure lasting thousands of steps, but was only ever trained on traces tens of steps long, can it generalize?

One approach is to distill the final answer: train the student to predict the correct output given the input specification. This approach is opaque—it provides no mechanism by which the student can internally simulate the intermediate computation. An alternative is to distill the *process*: expose the student to the teacher's local state transitions, so that the student can roll forward step by step, regardless of total horizon length.

This work tests a specific instantiation of that hypothesis on a controlled synthetic benchmark where the ground-truth computation is a deterministic modular arithmetic reduction. This choice makes correctness unambiguous and the state space finite and small, allowing a clean separation of outcomes.

The contribution is a clear bifurcation of results: final-answer-only distillation fails completely on this benchmark (remaining at chance even at the training horizon), while transition-based distillation succeeds exactly and extrapolates to 64× the training horizon. The negative result for final-answer distillation and the dependency on a known state schema are equally important parts of the finding.

---

## Method

### Benchmark Design

The task substrate is modular arithmetic over a finite field. Each task instance is a sequence of operations drawn from `{add, sub, mul}`, each paired with an integer operand, applied sequentially to an accumulator initialized to zero. The final answer is the terminal residue modulo M, where M = 97. This yields 97 possible output classes.

Key properties of this benchmark:

- **Deterministic:** The same operation sequence always yields the same final residue.
- **Finite state space:** The accumulator takes exactly 97 distinct values, making the state transition relation compact and enumerable.
- **Horizon-independent transitions:** The local transition `(prev_state, op, value) → next_state` is the same regardless of sequence length.

### Training and Evaluation Horizons

Training examples use sequence length 16. Evaluation horizons are 16, 64, 256, and 1024. The maximum extrapolation factor is 1024 / 16 = 64.

### Distillation Surfaces

Three distillation approaches are compared:

**1. Direct Final-Answer Distillation.** A `HashingVectorizer` converts the full operation string into a feature vector, and an `SGDClassifier` (log loss, linear model) is trained to predict the final residue class from the string representation alone. The student never observes intermediate states.

**2. Learned Transition Distillation.** The teacher generates local transition triples `(prev_state, op, value) → next_state` from short-horizon traces. A decision tree classifier is trained on these triples to predict `next_state`. At evaluation time, the student rolls out the decision tree step by step, feeding each predicted state back as the input to the next step.

**3. Compiled Transition-Table Distillation.** The same teacher-generated transition relation is stored as a lookup table (finite-state automaton). At evaluation time, the table is queried deterministically for each step. This represents the limiting case where the transition function is exact and requires no learning.

### Implementation and Execution

The experiment is implemented as a single Python script (`scripts/short_model_long_task_distillation.py`) using scikit-learn 1.8.0. Two execution modes were used:

- **Smoke mode:** Quick validation run.
- **Full mode:** Complete benchmark with all evaluation horizons.

The full run was executed on `Linux-6.17.0-1014-nvidia-aarch64` (NVIDIA GB10 platform), Python 3.12.3, with swap intentionally disabled. The experiment is CPU/sklearn-bound; no GPU computation was used. Script syntax was verified via `python3 -m py_compile`.

---

## Results

### Accuracy by Evaluation Horizon

| Eval Length | Direct Final-Label Acc | Learned Transition Acc | Table Transition Acc |
|---:|---:|---:|---:|
| 16 | 0.008 | 1.000 | 1.000 |
| 64 | 0.012 | 1.000 | 1.000 |
| 256 | 0.014 | 1.000 | 1.000 |
| 1024 | 0.009 | 1.000 | 1.000 |

Random chance for 97 classes is 1/97 ≈ 0.0103. Direct final-answer accuracy remains near chance at all horizons, including the training horizon of 16. Both transition-based methods achieve perfect accuracy at all horizons, including the 64× extrapolation to length 1024.

The direct classifier's failure at the training horizon itself (0.008 at length 16) is notable: the linear model trained on hashed operation strings does not learn the underlying algorithm even within the training distribution, suggesting that the final-answer distillation surface provides insufficient signal for this class of procedural tasks.

### Resource and Timing Metrics

| Metric | Value |
|---|---|
| Full run wall time | 30.42 s |
| Max RSS | 699,008 kB |
| MemAvailable (start / end) | 122,379,064 / 122,092,600 kB |
| Swap (total / free) | 0 / 0 kB |
| GPU utilization | 0% (11.22–11.27 W idle) |

Memory consumption was modest relative to available RAM. The experiment is entirely CPU-bound; GPU telemetry is recorded only for completeness.

### Distilled Artifact Properties

| Artifact | Size / Entries | Build Time |
|---|---|---|
| Transition table | 28,227 entries / 56,454 bytes | 0.0022 s |
| Decision tree | (sklearn internal) | 0.0667 s |
| Direct classifier | (sklearn internal) | 1.9603 s |

The compiled transition table is the most compact and fastest-to-build artifact. The decision tree is slower to train but still sub-second. The direct classifier is the slowest to train despite being the simplest model, likely due to the high-dimensional hashed feature space.

### Throughput

| Eval Length | Table Examples/s |
|---:|---:|
| 16 | 613,103.5 |
| 64 | 175,396.6 |
| 256 | 45,500.9 |
| 1024 | 11,554.7 |

Throughput decreases approximately linearly with sequence length, consistent with per-step table lookup cost being constant and the number of steps scaling linearly.

---

## Limitations

1. **Synthetic domain only.** The benchmark is deterministic modular arithmetic with a known, small, finite state space. This is not evidence that transition distillation works for natural-language agent tasks, stochastic environments, or tasks with large or continuous state spaces. The result should be understood as a boundary condition on a toy substrate, not as a demonstration of practical applicability.

2. **Known state schema.** The experiment relies on the teacher exposing the correct compact latent state (the accumulator residue). Automatic discovery of the right state representation from raw traces is not tested. In real applications, identifying the compact state schema may constitute the primary difficulty.

3. **Decision tree vs. table.** The learned decision tree achieves exact accuracy on this benchmark, but its structure may not scale gracefully to larger state spaces. The compiled table is the practical distilled artifact here; the decision tree result confirms that a learned model *can* capture the transition, but does not establish that it will remain compact or exact in other domains.

4. **No natural-language or agent-task validation.** The hypothesis is stated in terms of "short models" and "long tasks," but the evidence is confined to a toy arithmetic domain. Extrapolation to LLM-based agents requires a materially different benchmark with real teacher traces and an explicit state schema.

5. **Deterministic environment.** All transitions are noiseless. The effect of stochastic state transitions or partial observability on transition distillation quality is untested.

6. **Single modulus.** Only M = 97 was tested. The relationship between state space size, table compactness, and distillation quality across varying M is not characterized.

7. **Single model class per distillation surface.** The direct classifier is a linear model; the learned transition model is a decision tree. Other model architectures (e.g., neural networks) were not tested, and the negative result for direct distillation may be architecture-dependent.

---

## Reproducibility Checklist

- [x] **Experiment script available:** `scripts/short_model_long_task_distillation.py`
- [x] **Script syntax-verified:** `python3 -m py_compile` passed
- [x] **Smoke and full run logs preserved:** `artifacts/logs/smoke.log`, `artifacts/logs/full.log`
- [x] **Metrics CSV files preserved:** `artifacts/metrics/smoke_metrics.csv`, `artifacts/metrics/full_metrics.csv`
- [x] **Results JSON files preserved:** `artifacts/metrics/smoke_results.json`, `artifacts/metrics/full_results.json`
- [x] **Run notes preserved:** `run_notes.md`
- [x] **Decision JSON preserved:** `.omx/project_decision.json`
- [x] **Platform recorded:** Linux-6.17.0-1014-nvidia-aarch64, Python 3.12.3, scikit-learn 1.8.0
- [x] **Memory telemetry recorded:** MemAvailable and RSS at start/end
- [x] **GPU telemetry recorded:** NVIDIA GB10, 0% utilization (CPU-bound experiment)
- [x] **Wall time recorded:** 30.42 s for full run
- [x] **Random seed behavior:** Deterministic benchmark; scikit-learn default seeding

---

## Conclusion

On a synthetic modular-arithmetic benchmark, distilling a teacher's local state transitions enables a short-horizon student to execute tasks 64× longer than its training horizon with exact accuracy, while direct final-answer distillation remains at chance. The compiled transition table (56,454 bytes, 28,227 entries) is the clearest viable artifact: it is exact, compact, and processes 11,555 length-1024 examples per second on CPU.

The positive result is tightly constrained: it holds when the teacher can expose a compact, correct latent state and the transition relation is horizon-independent. The negative result for final-answer distillation is equally clear and raises the concern that training on input–output pairs alone may be insufficient for learning algorithmic procedures, even at the training horizon.

Scientific closure for natural-language agent tasks requires a follow-on experiment with real LLM teacher traces, an explicit (possibly learned) state schema, and tasks where the compact state representation is not supplied by the experimenter. The present result establishes a boundary condition: when compact state transitions are available, horizon extrapolation is straightforward; when they are not, even short-horizon generalization may fail.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `scripts/short_model_long_task_distillation.py` |
| Full run log | `artifacts/logs/full.log` |
| Smoke run log | `artifacts/logs/smoke.log` |
| Full metrics CSV | `artifacts/metrics/full_metrics.csv` |
| Smoke metrics CSV | `artifacts/metrics/smoke_metrics.csv` |
| Full results JSON | `artifacts/metrics/full_results.json` |
| Smoke results JSON | `artifacts/metrics/smoke_results.json` |
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260501T231048537328+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T231048537328+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T231048537328+0000/paper_manifest.json` |
| Project Notion page | `https://www.notion.so/Short-Model-Long-Task-Distillation-source-record-redacted` |
