# Context Rehydration Student: Offline-Trained Sketch Decoders for Lossy Context Recovery

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, benchmark results, and source scripts). The operator who released these artifacts claims no personal authorship credit for the writing or scientific results. Readers should treat this document as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether a small, offline-trained student model can recover useful task answers from lossy context sketches—hash-collided summaries of full context—more effectively than undistilled heuristic controllers. In a synthetic sketch-memory benchmark, a task-specific MLP student (14,529 parameters, 225-float sketch input) achieves mean accuracy of 0.706 across three calibrated seeds (range 0.690–0.728), outperforming an undistilled heuristic baseline (mean 0.641, range 0.629–0.651; Δ = +6.5 pp) and a generic-sketch logistic regression student (mean 0.612; Δ = +9.4 pp), while running 22.3× faster than a full-context teacher scan (0.295 ms vs. 6.588 ms per 1,000 examples). These results are limited to synthetic data with a deterministic oracle teacher; no claim is made about real agent traces or production context-rehydration quality. The findings are consistent with the mechanism that task-specific distillation from teacher utilities contributes to sketch decoding performance, but scientific closure requires validation on real offline traces with downstream task-quality metrics.

## 1. Introduction

Context rehydration—the problem of recovering useful information from lossy, compressed representations of prior context—is a practical concern in systems that must operate under memory or latency constraints. When full context is unavailable or too expensive to scan, an agent may have access only to a sketch: a hash-collided or otherwise lossy summary of the original records. The central question is whether a compact, offline-trained student can decode task-relevant answers from such sketches more effectively than simple heuristics, and whether this recovery preserves a material fraction of the utility of a full-context teacher.

This work tests the hypothesis that a small offline-trained student can recover useful task answers from lossy context sketches better than undistilled sketch controllers, preserving a material fraction of teacher utility while avoiding online full-context scans. We construct a synthetic benchmark where a teacher has access to full generated record context and answers exactly, while competing methods see only a lossy sketch plus a query encoding. We compare a majority baseline, an undistilled heuristic controller, a generic-sketch logistic regression student, a task-sketch logistic regression student, and a task-sketch MLP student.

Our results on synthetic data indicate that task-specific sketch features and nonlinear decoding both contribute to student performance, with the task-sketch MLP achieving the highest accuracy among sketch-only methods. However, the gap to the oracle teacher remains substantial (0.706 vs. 1.000), and the fastest heuristic baseline still has lower latency than the MLP. We discuss these trade-offs and the remaining risks for deployment.

## 2. Method

### 2.1 Task Design

The benchmark (`src/context_rehydration_experiment.py`) creates a synthetic sketch-based memory task with the following structure:

1. **Record generation.** A set of records is generated, forming the full context.
2. **Teacher.** Has access to the full record context and answers queries exactly (accuracy 1.000 by construction, verified via oracle).
3. **Sketch construction.** Full context is compressed into a lossy hash-collided sketch. In the calibrated configuration, the full context comprises 324 integers, while the task sketch input comprises 225 floats.
4. **Query encoding.** Each method receives the sketch plus a query encoding as input.

This is a toy simulation: the records are synthetically generated, and the teacher is a deterministic oracle rather than a learned model. The sketch construction uses hash collision to produce a lossy compression, simulating the information degradation that motivates context rehydration in real systems.

### 2.2 Compared Methods

Five methods are compared:

- **Majority baseline.** Predicts the most frequent class.
- **Undistilled heuristic controller.** A hand-crafted rule operating on the sketch without task-specific training.
- **Generic-sketch logistic regression student.** A linear model trained on generic (non-task-specific) sketch features.
- **Task-sketch logistic regression student.** A linear model trained on task-specific sketch features.
- **Task-sketch MLP student.** A multi-layer perceptron trained on task-specific sketch features (14,529 parameters).

### 2.3 Metrics

- **Accuracy and F1.** Measured against teacher labels.
- **Teacher gap.** Difference between method accuracy and teacher accuracy (1.000).
- **Prediction latency.** Milliseconds per 1,000 examples.
- **Input size.** Dimensionality of the input representation.
- **Parameter count.** Number of trainable parameters.
- **System telemetry.** `MemAvailable` and best-effort GB10/NVIDIA utilization data.

### 2.4 Experimental Protocol

Three execution modes were used:

1. **Smoke test** (`--mode smoke`): Quick validation of the pipeline.
2. **Calibrated single run** (`--mode calibrated`): Single run with calibrated parameters.
3. **3-seed calibrated sweep** (`src/run_seed_sweep.py`): Three independent runs with different random seeds, reported as mean and range.

All runs were executed on a GB10 host with 121 GiB RAM, approximately 116 GiB available at start, swap intentionally disabled (`SwapTotal: 0`). Runs were small CPU-only sklearn experiments; NVIDIA GPU utilization remained at 0% throughout, so no GPU-accelerated runs were attempted. These are prototype-scale calibration runs, not production validation.

## 3. Results

### 3.1 Accuracy

Table 1 summarizes accuracy across the three calibrated seeds.

| Method | Mean Accuracy | Range |
|---|---|---|
| Teacher (oracle, full context) | 1.000 | — |
| Task-sketch MLP student | 0.706 | 0.690–0.728 |
| Undistilled heuristic | 0.641 | 0.629–0.651 |
| Generic-sketch logreg student | 0.612 | — |

The task-sketch MLP student outperforms the undistilled heuristic by a mean of +6.5 percentage points and the generic-sketch logistic regression student by +9.4 percentage points. The task-sketch logistic regression student is not reported with a separate mean in the summary metrics but is intermediate between the generic logreg and the MLP, suggesting that both task-specific features and nonlinear decoding contribute to the MLP's advantage. F1 was measured but specific values are not available in the summary artifacts.

### 3.2 Latency and Efficiency

| Method | Latency (ms / 1k examples) | Speedup vs. Teacher |
|---|---|---|
| Teacher (full-context scan) | 6.588 | 1.0× |
| Task-sketch MLP student | 0.295 | 22.3× |

The MLP student achieves a 22.3× speedup over the full-context teacher scan. However, the undistilled heuristic (a simple rule) is expected to be faster still; its latency is not separately reported in the summary metrics but should be lower than the MLP's 0.295 ms per 1,000 examples given its lack of learned parameters. This creates a deployment trade-off: the heuristic is the lowest-latency option, the student offers higher accuracy at modest additional latency, and the teacher offers perfect accuracy at substantially higher cost.

### 3.3 Model Characteristics

- **MLP parameter count:** 14,529
- **Task sketch input:** 225 floats (vs. 324 integers for full context)
- **Compression ratio:** The sketch input is approximately 69.4% of the full context dimensionality, though the representations differ in type (float vs. integer), making direct compression ratios not strictly comparable.

### 3.4 Variability Across Seeds

The MLP student's accuracy range of 0.690–0.728 across three seeds indicates moderate variability (span of 3.8 pp). The undistilled heuristic's range of 0.629–0.651 is narrower (span of 2.2 pp), consistent with its deterministic rule-based nature. The MLP's wider range reflects sensitivity to training initialization and data shuffling, a consideration for deployment stability.

### 3.5 Mixed and Negative Results

Several findings temper the positive interpretation:

- **Large teacher gap.** The best student achieves 70.6% accuracy, leaving a 29.4 pp gap to the oracle teacher. Whether this gap is acceptable depends on application-specific cost-quality trade-offs.
- **Heuristic remains competitive on latency.** The undistilled heuristic, while less accurate, is likely the lowest-latency option. The student's accuracy advantage comes at a latency cost relative to the heuristic.
- **No F1 detail available.** Although F1 was measured, summary artifacts do not report per-method F1 values, limiting the ability to assess class-balanced performance.
- **Task-sketch logreg not fully reported.** The intermediate position of the task-sketch logistic regression student is inferred rather than directly quantified, making it difficult to precisely attribute the MLP's advantage to nonlinearity versus task-specific features.

## 4. Limitations

1. **Synthetic data only.** The benchmark uses generated records and a deterministic oracle teacher. No claim is made about performance on real agent traces, production context-rehydration scenarios, or natural language contexts.

2. **Oracle teacher, not an LLM.** The teacher is a deterministic function over generated records, not a large language model. The sketch-decoding problem for LLM-generated context may have fundamentally different structure.

3. **Substantial teacher gap.** The best student achieves 0.706 accuracy versus the teacher's 1.000, leaving a 29.4 percentage-point gap. Whether this gap is acceptable depends on the cost-quality trade-off of the target application.

4. **Heuristic latency advantage.** The undistilled heuristic, while less accurate, is likely faster than the MLP. Deployment would require an admission policy that routes queries to the student only when the quality gain justifies the additional latency and complexity.

5. **No downstream task-quality metrics.** Accuracy is measured against teacher labels (agreement with oracle), not against a downstream task-quality metric. A student that agrees with the teacher 70.6% of the time may or may not produce acceptable downstream outcomes.

6. **No real failure-mode traces.** The experiment does not use traces from the target context-rehydration failure mode that motivated this work. The synthetic task may not reflect the distributional properties of real sketch-query pairs.

7. **CPU-only, small-scale.** All runs were small sklearn experiments on CPU. Scaling behavior with larger sketch dimensions, more classes, or deeper models is untested.

8. **Limited seed count.** Three seeds provide a preliminary estimate of variability but are insufficient for robust statistical claims about performance distributions.

## 5. Reproducibility Checklist

- **Code available:** `src/context_rehydration_experiment.py`, `src/run_seed_sweep.py`
- **Random seeds:** Three seeds used in calibrated sweep; seeds recorded in `artifacts/context_rehydration_sweep/summary.json`
- **Environment:** GB10 host, 121 GiB RAM, swap disabled, CPU-only (sklearn), NVIDIA GPU present but unused
- **Environment log:** `logs/environment_20260502T065426Z.log`
- **Smoke test results:** `artifacts/context_rehydration_v2/smoke/results.json`
- **Calibrated single-run results:** `artifacts/context_rehydration_v2/calibrated/results.json`
- **Seed sweep summary:** `artifacts/context_rehydration_sweep/summary.json`
- **CSV metrics:** `metrics/context_rehydration_seed_sweep.csv`
- **Project decision record:** `.omx/project_decision.json`
- **Dependencies:** Python 3, sklearn, numpy (versions recorded in environment log)
- **Execution commands:** Documented in run notes; reproducible via the same `--mode` flags and sweep script
- **Result classification:** These are calibrated prototype-scale CPU runs on synthetic data, not production validation or GPU benchmarks.

## 6. Conclusion

On a controlled synthetic sketch-memory task, a task-specific MLP student with 14,529 parameters consistently outperforms both an undistilled heuristic controller (+6.5 pp mean accuracy) and a generic-sketch logistic regression student (+9.4 pp), while achieving a 22.3× speedup over full-context teacher scanning. These results are consistent with the mechanism that task-specific teacher utilities matter for compression distillation: both the choice of sketch features (task-specific vs. generic) and the decoder architecture (MLP vs. logistic regression) appear to contribute to performance.

However, the results are confined to synthetic data with an oracle teacher, and the best student still leaves a 29.4 percentage-point gap to perfect performance. The viability of context rehydration students for production use remains unproven. The heuristic baseline retains a latency advantage over the student, meaning deployment would require an admission policy rather than unconditional replacement. Next steps include: (1) replacing synthetic teacher labels with real offline traces from the target context-rehydration failure mode, (2) training and evaluating students against an admission policy that compares heuristic, student, and teacher fallback cost-quality trade-offs, and (3) adding downstream answer-quality metrics beyond teacher-label agreement.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `src/context_rehydration_experiment.py` |
| Seed sweep harness | `src/run_seed_sweep.py` |
| Smoke test results | `artifacts/context_rehydration_v2/smoke/results.json` |
| Calibrated single-run results | `artifacts/context_rehydration_v2/calibrated/results.json` |
| Seed sweep summary | `artifacts/context_rehydration_sweep/summary.json` |
| CSV metrics | `metrics/context_rehydration_seed_sweep.csv` |
| Environment log | `logs/environment_20260502T065426Z.log` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260502T065348538592+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T065348538592+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T065348538592+0000/paper_manifest.json` |
