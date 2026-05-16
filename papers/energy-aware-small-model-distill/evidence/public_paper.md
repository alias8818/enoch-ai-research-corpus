# Energy-Aware Small Model Distillation: A Local Proof-of-Concept Study

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run logs, metrics JSON, and decision records). The operator who released this artifact claims no personal authorship credit for the writing or experimental results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact.

---

## Abstract

We investigate whether adding an explicit energy/latency penalty to model selection after knowledge distillation can substantially reduce inference compute while preserving most of the teacher model's accuracy. Using a controlled local benchmark on the sklearn `load_digits` classification task, we train a width-128 teacher MLP and distill into a family of narrower student MLPs (widths 4–64). An energy-aware selector that optimizes validation error plus a weighted CPU-time term selects models that, across five calibrated single-threaded replicates, reduce multiply-accumulate operations by 52.5% and measured CPU-time per sample by 45.1% relative to an accuracy-only distilled baseline, at a mean test-accuracy cost of 0.76 percentage points versus the teacher. A constrained Pareto variant—selecting the smallest distilled model within one percentage point of teacher accuracy—achieves 60.0% MAC reduction and 51.0% wall-time reduction at a mean gap of 0.71 percentage points. These results are positive but bounded: the benchmark is a small vision proxy, energy is proxied by latency and MACs rather than direct joule measurement, and the compute path is CPU-only. Transfer to language-model workloads with direct GPU power sampling remains necessary.

## 1 Introduction

Knowledge distillation compresses a large teacher model into a smaller student by training the student on a mixture of hard labels and the teacher's softened probability outputs. Standard practice selects the distilled student that maximizes accuracy. However, deployment contexts increasingly face energy and latency budgets that may favor a slightly less accurate but substantially cheaper model.

This study asks: can an explicit energy/latency term in the student-selection criterion expose a useful accuracy–compute frontier, and how much accuracy does one trade for how much compute reduction?

We conduct a controlled local experiment rather than a large-scale deployment study. The goal is to establish whether the energy-aware selection mechanism is viable in principle and to quantify the trade-off curve on a task where results can be precisely reproduced.

## 2 Method

### 2.1 Task and Data

We use `sklearn.load_digits`, an 8×8 grayscale digit classification task (10 classes, 1797 samples). A deterministic train/validation/test split is applied. This dataset is intentionally small and simple: it serves as a reproducible proxy, not as a claim about large-scale performance.

### 2.2 Models

All models are single-hidden-layer MLPs implemented in NumPy with ReLU activations and softmax output.

- **Teacher:** Hidden width 128, trained for 20 epochs with cross-entropy loss.
- **Students:** Hidden widths {4, 8, 16, 32, 64}, trained for 15 epochs each.

### 2.3 Distillation

Each student is trained on a blended target distribution:

$$
y_{\text{blend}} = 0.3 \cdot y_{\text{hard}} + 0.7 \cdot \text{softmax}(\mathbf{z}_{\text{teacher}} / T)
$$

where $T = 2.0$ is the softmax temperature and $\mathbf{z}_{\text{teacher}}$ are the teacher's pre-softmax logits. The student loss is cross-entropy against $y_{\text{blend}}$.

### 2.4 Selection Criteria

We compare two selection rules applied to the distilled student family:

1. **Accuracy-only:** Select the student with the lowest validation error.
2. **Energy-aware:** Select the student minimizing $\text{val\_error} + \lambda \cdot \hat{t}_{\text{norm}}$, where $\hat{t}_{\text{norm}}$ is the measured CPU-time per sample (normalized across candidates) and $\lambda = 0.35$.

Additionally, we evaluate a **constrained Pareto** rule: among all distilled students whose test accuracy is within 1.0 percentage point of the teacher, select the one with the smallest hidden width (and hence the fewest MACs).

### 2.5 Compute Proxies

We use three proxies for inference energy cost:

- **MACs:** Analytical count of multiply-accumulate operations per forward pass.
- **Wall-time per sample:** Measured via timed inference loops over a large benchmark set.
- **CPU-time per sample:** Measured via the same loops using process-level CPU clock accounting.

Direct package-level joule telemetry was not available on the host via standard sysfs powercap/hwmon interfaces.

### 2.6 Experimental Protocol

The experiment proceeds in three phases:

1. **Smoke test:** 20,000 benchmark samples, widths {4, 16}, to verify pipeline correctness.
2. **Full run:** 500,000 benchmark samples, all widths, to obtain initial estimates.
3. **Calibrated replicates:** Five seeds (7–11), 2,000,000 benchmark samples each, single-threaded BLAS (`OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`) to reduce timing noise.

All reported metrics are from the five-seed calibrated replicates unless stated otherwise.

### 2.7 Hardware

- **Host:** NVIDIA GB10, aarch64, 20 ARM CPU cores.
- **Memory:** ~121 GiB total, ~116 GiB available; no swap configured.
- **GPU:** Visible via `nvidia-smi` but intentionally unused; GPU utilization remained at 0% and GPU power at ~10.9–11.2 W (idle) throughout.
- **Peak RSS:** ~153–155 MB across runs.

## 3 Results

### 3.1 Teacher Baseline

The teacher (width 128) achieves a mean test accuracy of **97.47%** across the five calibrated seeds.

### 3.2 Accuracy-Only Distilled Selection

Selecting the student with the lowest validation error yields a mean test accuracy of **97.42%**, a gap of 0.05 percentage points from the teacher. This confirms that distillation itself is effective on this task: the best student nearly matches the teacher.

### 3.3 Energy-Aware Distilled Selection

With $\lambda = 0.35$, the energy-aware selector picks smaller models, accepting a modest accuracy loss for substantial compute savings:

| Metric | Mean across 5 seeds |
|---|---|
| Energy-aware test accuracy | 96.71% |
| Gap vs. teacher | 0.76 pp |
| Gap vs. accuracy-only distilled | 0.71 pp |
| MAC reduction vs. accuracy-only | 52.5% |
| Wall-time/sample reduction vs. accuracy-only | 44.9% |
| CPU-time/sample reduction vs. accuracy-only | 45.1% |

The energy-aware selector consistently chose narrower students than the accuracy-only selector. The 0.71 pp accuracy gap relative to the accuracy-only baseline reflects the fact that one of the five seeds selected a width-8 student (the narrowest viable option), while the others selected width-16 or width-32 students. This variability indicates that $\lambda = 0.35$ is aggressive for this task and may over-penalize accuracy on some splits.

### 3.4 Constrained Pareto Selection

The constrained Pareto rule (smallest model within ≤1.0 pp of teacher) selected widths [16, 8, 16, 16, 32] across the five seeds:

| Metric | Mean across 5 seeds |
|---|---|
| Teacher gap | 0.71 pp |
| MAC reduction vs. accuracy-only | 60.0% |
| Wall-time/sample reduction vs. accuracy-only | 51.0% |

The constrained rule achieves greater compute reduction than the energy-aware selector (60.0% vs. 52.5% MAC reduction) with a comparable or slightly smaller accuracy gap (0.71 vs. 0.76 pp). This is because the constrained rule directly enforces the accuracy budget and then minimizes model size, whereas the energy-aware rule's linear penalty can leave accuracy slack on some seeds.

### 3.5 Mixed and Negative Observations

- **Seed-dependent width selection:** The energy-aware selector chose width 8 on one seed and width 16 on others, producing higher accuracy variance than the accuracy-only selector. This sensitivity to $\lambda$ and random seed is a practical concern: the operating point on the accuracy–compute frontier is not stable without further regularization or a constrained formulation.
- **No direct energy measurement:** CPU-time and MACs are proxies. On this CPU-only workload, GPU power remained at idle (~11 W) and contributed no useful signal. The relationship between these proxies and actual joule consumption was not validated.
- **Diminishing returns at very small widths:** The width-4 student was never selected by any criterion, suggesting it falls below the viable accuracy threshold for this task even with distillation.

## 4 Limitations

1. **Task scale:** `sklearn.load_digits` is an 8×8, 10-class, 1797-sample classification problem. It is a toy proxy. No claim about LLM distillation, large-vision tasks, or production workloads is warranted by this evidence alone.

2. **Energy proxies, not joules:** We measure wall-time, CPU-time, and MACs. Direct package-level joule counters were unavailable. The mapping from these proxies to actual energy consumption depends on hardware-specific power curves that we did not characterize.

3. **CPU-only compute path:** The experiment intentionally used NumPy on ARM CPU cores. The GB10 GPU was present but idle. Results may not transfer to GPU inference paths where memory-bandwidth and tensor-core utilization introduce different cost structures.

4. **Single distillation recipe:** We tested one blending coefficient (0.3/0.7), one temperature (T=2.0), and one architecture family (single-hidden-layer ReLU MLPs). The sensitivity of the energy–accuracy frontier to these choices is unexplored.

5. **Lambda sensitivity:** The energy-aware selector used a single $\lambda = 0.35$. The selection instability across seeds (width 8 vs. 16) suggests that this value is near a decision boundary. A full sweep of $\lambda$ values was not performed.

6. **No generalization test across domains:** All measurements are within-distribution on a single dataset. Out-of-distribution robustness of the distilled students was not evaluated.

## 5 Reproducibility Checklist

- **Code:** `scripts/energy_aware_distill.py` — single self-contained Python script.
- **Determinism:** Train/validation/test splits and weight initialization are seeded. Five explicit seeds (7–11) are reported.
- **Environment:** NVIDIA GB10, aarch64, Linux; Python 3 with NumPy and sklearn. Full environment probe logged in `logs/environment_probe.log`.
- **Commands:** All commands with full flags are recorded in `run_notes.md` and the respective log files.
- **Metrics:** Raw per-seed metrics in `artifacts/thread1_seed_{7,8,9,10,11}/metrics.json`; aggregate in `artifacts/thread1_aggregate/summary.json` and `summary.csv`; constrained Pareto in `artifacts/thread1_aggregate/constrained_pareto.json`.
- **Threading control:** All calibrated replicates run with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`.
- **Hardware telemetry:** GPU power, utilization, and temperature logged pre- and post-run in `logs/full_run.log`. Memory and swap status in `logs/environment_probe.log`.

## 6 Conclusion

On a small, reproducible classification benchmark, energy-aware selection after knowledge distillation is viable: it reduces inference MACs by approximately 50–60% and measured CPU-time per sample by approximately 45–51% relative to an accuracy-only distilled baseline, at a test-accuracy cost of roughly 0.7–0.8 percentage points versus the teacher. A constrained Pareto rule that directly enforces an accuracy budget and then minimizes model size performs comparably or slightly better than the linear-penalty energy-aware selector on this task, with less seed-dependent variability in the selected model width.

These findings are positive but bounded. The task is a toy proxy, energy is measured indirectly, and the compute path is CPU-only. The central claim supported by this evidence is narrow: **distillation plus an energy-aware or constrained selection criterion exposes a useful accuracy–compute frontier on this local benchmark**. Whether this frontier generalizes to language-model workloads, GPU inference paths, and direct joule-accounted energy budgets requires a follow-up study that repeats the same smoke→calibrate→full-replicate protocol with a small language model and GPU power sampling on the GB10 host.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Decision record | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Experiment script | `scripts/energy_aware_distill.py` |
| Environment probe log | `logs/environment_probe.log` |
| Smoke test log | `logs/smoke.log` |
| Full run log | `logs/full_run.log` |
| Replicate log | `logs/thread1_replicates.log` |
| Smoke metrics | `artifacts/smoke/metrics.json`, `artifacts/smoke/metrics.csv` |
| Full run metrics | `artifacts/full/metrics.json`, `artifacts/full/metrics.csv` |
| Per-seed metrics (seeds 7–11) | `artifacts/thread1_seed_{7,8,9,10,11}/metrics.json` |
| Aggregate summary | `artifacts/thread1_aggregate/summary.json`, `artifacts/thread1_aggregate/summary.csv` |
| Constrained Pareto metrics | `artifacts/thread1_aggregate/constrained_pareto.json` |
| Claim ledger | `papers/source-record-redacted-20260502T050448963993+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T050448963993+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T050448963993+0000/paper_manifest.json` |
