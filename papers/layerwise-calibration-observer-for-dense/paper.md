# Layerwise Calibration Observer for Dense Neural Networks

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review is claimed or implied.

---

## Abstract

We present a layerwise calibration observer for dense neural networks, comprising per-hidden-layer ridge regression probes with independent temperature scaling calibration. The observer reports layerwise Expected Calibration Error (ECE), Negative Log-Likelihood (NLL), and Brier score under clean and distribution-shifted conditions. In a synthetic dense MLP benchmark across five random seeds, temperature calibration reduced hidden-layer probe ECE by approximately 0.23–0.25 on average. The best clean observer (layer 3) achieved mean calibrated ECE of 0.0060 ± 0.0024; the best shifted observer (layer 2) achieved 0.0120 ± 0.0046. Hidden-layer probes retained classification accuracy of 0.967–0.981 under both conditions. Per-layer metrics revealed inter-layer variation in calibration sensitivity to distribution shift. These results support prototype viability as a lightweight diagnostic instrument, though generalization beyond the synthetic benchmark is unvalidated. The claim ledger for this artifact remains in blocked audit status with no structured claims extracted, and the evidence bundle contains only minimal provenance metadata; readers should weigh the reported numbers accordingly.

## Introduction

Neural network calibration—the agreement between predicted confidence and observed accuracy—is a prerequisite for reliable decision-making in deployed systems. Post-hoc calibration methods such as temperature scaling and Platt scaling are typically applied to the final output layer. However, miscalibration may originate at or propagate through intermediate layers, and a single output-level calibration correction can obscure layer-specific dynamics relevant to monitoring, drift detection, or targeted intervention.

A *layerwise calibration observer* is an external diagnostic module that attaches lightweight linear probes to each hidden layer, calibrates each probe independently, and tracks per-layer calibration metrics. The design is intentionally non-invasive: it operates on cached activations without modifying the host network, and it requires only ridge regression and a scalar temperature per layer.

This paper reports a NumPy-based prototype validation on a synthetic dense MLP. We evaluate three questions: (1) whether hidden-layer activations support calibrated linear readouts, (2) whether per-layer calibration metrics reveal meaningful inter-layer variation, and (3) whether clean-vs-shifted metric comparisons expose detectable calibration drift. We do not claim production validation or generalization to large-scale models; the experiment is scoped to a small synthetic benchmark with CPU-only execution.

## Method

### Observer Architecture

The layerwise calibration observer comprises three stages:

**Activation capture.** Forward passes through the host dense MLP are intercepted at each hidden layer. Activation vectors $h_l(x)$ for layer $l$ are cached alongside input labels. The host network is a dense MLP with four hidden layers (indexed 0–3) plus a final logit layer, trained on a synthetic classification task.

**Linear readout probes.** For each hidden layer $l$, a ridge regression probe $W_l$ maps activations $h_l(x)$ to one-hot label vectors. Probes are fit on a training split with a fixed regularization parameter. Probe outputs are converted to class probabilities via softmax.

**Temperature calibration.** For each layer probe, a scalar temperature $T_l$ is optimized on a held-out validation split to minimize NLL of the probe's softmax output, following the standard post-hoc temperature scaling protocol. The temperature is optimized on clean validation data and then applied to both clean and shifted evaluation.

### Evaluation Metrics

Per-layer metrics include:

- **Accuracy:** Fraction of correctly classified examples.
- **Expected Calibration Error (ECE):** Binned absolute difference between confidence and accuracy (15 bins).
- **Negative Log-Likelihood (NLL):** Cross-entropy of the calibrated probe output.
- **Brier score:** Mean squared error between predicted probabilities and one-hot labels.

Each metric is computed under two conditions:

- **Clean:** Validation data drawn from the training distribution.
- **Shifted:** Validation data drawn from a distribution-shifted variant of the same task.

### Drift Signal

The observer computes calibration drift as the difference between shifted and clean metrics for each layer. A layer whose calibration degrades substantially under shift may indicate representation sensitivity to the applied distribution shift.

### Experimental Protocol

1. Train the dense MLP on the training split.
2. Extract activations from all hidden layers and the final logit layer on training, clean validation, and shifted validation data.
3. Fit ridge regression probes per layer on training activations.
4. Optimize per-layer temperatures on clean validation data.
5. Evaluate calibrated and uncalibrated probes on both clean and shifted validation data.
6. Repeat across five random seeds (7, 11, 23, 37, 51) and aggregate.

The implementation uses only NumPy (no PyTorch, scikit-learn, or other ML frameworks). All runs were executed on a Linux aarch64 host with an NVIDIA GB10 GPU present but unused, as the experiment was intentionally dependency-light.

## Results

### Aggregate Performance Across Seeds

Table 1 summarizes the best-performing observer layers by mean calibrated ECE, aggregated over five seeds.

**Table 1.** Best observer layers by mean calibrated ECE (5 seeds).

| Condition | Best Layer | Cal. ECE (mean ± SD) | Uncal. ECE (mean) | ECE Improvement | Probe Acc. (mean ± SD) |
|-----------|-----------|----------------------|-------------------|-----------------|------------------------|
| Clean     | layer 3   | 0.0060 ± 0.0024      | 0.2511            | 0.2451          | 0.980 ± 0.003          |
| Shifted   | layer 2   | 0.0120 ± 0.0046      | 0.2434            | 0.2314          | 0.968 ± 0.006          |

Temperature calibration produced substantial ECE reductions at every hidden layer. Uncalibrated hidden-layer probes exhibited ECE values of approximately 0.24–0.25, consistent with uncalibrated softmax outputs from linear probes on high-dimensional activations. After temperature scaling, calibrated ECE dropped to 0.006–0.012 at the best-performing layers.

The standard deviations across seeds (0.0024 clean, 0.0046 shifted) indicate that calibrated ECE is reasonably stable but not negligible in variability, particularly under distribution shift.

### Final Logit Layer

The final logit layer was already relatively well-calibrated compared to raw hidden-layer probes, but still benefited from temperature scaling:

**Table 2.** Final logit layer calibration.

| Condition | Uncal. ECE | Cal. ECE | Improvement |
|-----------|-----------|----------|-------------|
| Clean     | 0.0109    | 0.0079   | 0.0030      |
| Shifted   | 0.0228    | 0.0144   | 0.0084      |

The smaller absolute improvement at the final layer is expected: end-to-end cross-entropy training implicitly encourages some calibration alignment at the output.

### Hidden-Layer Probe Accuracy

Hidden-layer probes maintained high classification accuracy across all layers:

- Clean accuracy means: 0.980–0.981 across layers.
- Shifted accuracy means: 0.967–0.971 across layers.

The modest accuracy drop under shift (approximately 1.0–1.3 percentage points) confirms that hidden representations retain discriminative information under the tested distribution shift, though the shift is detectable through both accuracy and calibration metrics.

### NLL Improvement

NLL improvements were consistent with ECE improvements.

Best clean observer (layer 3):

- Uncalibrated NLL: 0.3369
- Calibrated NLL: 0.0613
- Improvement: 0.2756

Best shifted observer (layer 2):

- Uncalibrated NLL: 0.3521
- Calibrated NLL: 0.0984
- Improvement: 0.2536

### Computational Cost

Mean training throughput was approximately 794,943 examples per second on CPU (NumPy, small dense MLP). Peak RSS for the seed-7 run was 57,532 kB with no swap activity. Available memory remained above 117 GiB throughout. These figures reflect the lightweight nature of the prototype and should not be interpreted as representative of production-scale throughput on larger models or GPU-accelerated pipelines.

### Inter-Layer Variation

Per-layer calibration metrics revealed materially different calibration behavior across layers. The best clean observer was layer 3 (deepest hidden layer), while the best shifted observer was layer 2. This asymmetry suggests that different layers exhibit different sensitivities to distribution shift, consistent with the hypothesis that calibration drift is layer-dependent rather than uniform. However, with only four hidden layers and a single shift type, the generality of this observation is limited.

### Negative and Mixed Observations

Several aspects of the results warrant cautious interpretation:

- **Calibrated ECE under shift remains higher than under clean conditions** (0.012 vs. 0.006 at best layers), indicating that temperature scaling optimized on clean data does not fully compensate for distribution shift.
- **The best shifted observer is not the deepest layer**, which contrasts with the clean condition where the deepest hidden layer performed best. The reason for this inversion is not established by the current experiments.
- **Uncalibrated ECE values (~0.24–0.25) are high across all hidden layers**, suggesting that raw linear probe outputs are poorly calibrated by default. The observer's utility depends on the calibration step; without it, layerwise probes would be unreliable as confidence indicators.

## Limitations

1. **Synthetic benchmark only.** The host network is a small dense MLP on a synthetic classification task. No results are reported for production-scale dense transformers, convolutional architectures, or real-world datasets. Generalization to these settings is unknown and should not be assumed.

2. **Post-hoc, offline protocol.** The observer uses post-hoc ridge probes and temperature scaling fitted on pre-collected activations. It does not test online streaming calibration, incremental probe updates, or causal intervention based on observed drift signals.

3. **Single shift type.** Only one distribution shift variant was tested. Behavior under diverse shift types (covariate shift, label shift, subpopulation shift) was not evaluated.

4. **No GPU utilization.** The experiment was CPU-only by design. Activation capture overhead in GPU-accelerated training or inference pipelines was not measured.

5. **Linear probe capacity.** Ridge regression probes are linear. If hidden representations are not linearly separable with respect to task labels, probe accuracy may be insufficient for reliable calibration observation. This was not observed in the synthetic benchmark but may arise in more complex models.

6. **Temperature optimization stability.** Temperature scaling was optimized via scalar search on clean validation data. Transferability of these temperatures to shifted data—and their stability across noisier settings—was adequate in this benchmark but is not guaranteed generally.

7. **No comparison to alternative methods.** The study compares temperature scaling to uncalibrated probes but does not compare against Platt scaling, isotonic regression, ensemble temperature scaling, or other drift detection approaches.

8. **Claim audit status.** The claim ledger for this artifact is in blocked status with no structured claims extracted. The evidence bundle contains only minimal provenance metadata. The reported results should be treated as prototype-level observations pending formal claim-evidence audit.

## Reproducibility Checklist

- **Code availability:** Source files `src/layerwise_calibration_observer.py` and `src/aggregate_runs.py` are present in the project directory.
- **Random seeds:** Five seeds explicitly recorded: 7, 11, 23, 37, 51.
- **Environment:** Linux aarch64, NVIDIA GB10 present (GPU unused), NumPy-only implementation. No PyTorch, scikit-learn, or other ML framework dependencies.
- **Memory telemetry:** Peak RSS and available memory logged via `/usr/bin/time -v` in `logs/02_full_seed7.log`. Peak RSS: 57,532 kB; no swap activity.
- **Per-run artifacts:** `metrics_by_layer.csv`, `calibration_drift.csv`, `training_history.csv`, and `summary.json` for each seed in `artifacts/full_seed*/`.
- **Aggregate artifacts:** `artifacts/aggregate/aggregate_metrics.csv` and `artifacts/aggregate/aggregate_summary.json`.
- **Verification:** Fresh smoke run with assertions (accuracy > 0.8, calibrated ECE < uncalibrated ECE) passed; recorded in `logs/04_verification.log`.
- **Decision record:** `.omx/project_decision.json` contains the structured claim, evidence references, and stated limitations.
- **Claim ledger status:** Blocked (empty claims). The claim ledger at `papers/.../claim_ledger.json` records `audit_status: blocked_empty_claims` with no structured claims extracted. This paper draft should not be treated as having passed claim-evidence audit.

## Conclusion

A lightweight layerwise calibration observer—comprising per-layer ridge regression probes and temperature scaling—produces well-calibrated hidden-layer readouts and detectable calibration drift signals in a synthetic dense MLP benchmark. Across five random seeds, temperature calibration reduced hidden-layer ECE by approximately 0.23–0.25 on average, and hidden-layer probes retained accuracy of at least 0.967 even under distribution shift. Per-layer metrics revealed inter-layer variation in calibration behavior, with the best clean observer (layer 3) and best shifted observer (layer 2) differing, consistent with layer-dependent calibration dynamics.

These results establish prototype viability but do not constitute production validation. The claim ledger remains in blocked audit status, and the evidence bundle contains only minimal provenance metadata. Critical next steps are: (1) porting the observer to a target dense model's activation capture path, (2) evaluating the protocol on real validation and test data with domain-specific acceptance thresholds, and (3) testing under diverse distribution shift types. Until such validation is completed, the observer should be regarded as a promising but unvalidated diagnostic prototype.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260430T011848408685+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T011848408685+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T011848408685+0000/paper_manifest.json` |
| Observer source | `src/layerwise_calibration_observer.py` |
| Aggregation source | `src/aggregate_runs.py` |
| Environment smoke log | `logs/00_env_smoke.log` |
| Smoke experiment log | `logs/01_smoke.log` |
| Full seed-7 run log | `logs/02_full_seed7.log` |
| Replicates and aggregate log | `logs/03_replicates_and_aggregate.log` |
| Verification log | `logs/04_verification.log` |
| Per-seed metrics | `artifacts/full_seed{7,11,23,37,51}/metrics_by_layer.csv` |
| Per-seed calibration drift | `artifacts/full_seed{7,11,23,37,51}/calibration_drift.csv` |
| Per-seed training history | `artifacts/full_seed{7,11,23,37,51}/training_history.csv` |
| Per-seed summary | `artifacts/full_seed{7,11,23,37,51}/summary.json` |
| Aggregate metrics | `artifacts/aggregate/aggregate_metrics.csv` |
| Aggregate summary | `artifacts/aggregate/aggregate_summary.json` |
