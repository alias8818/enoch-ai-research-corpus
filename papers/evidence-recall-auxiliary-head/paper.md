# Evidence Recall Auxiliary Head: Resolving Answer-Only Supervision Ambiguity via Direct Evidence Localization

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether an auxiliary evidence-recall head can improve both evidence localization and answer accuracy in retrieval settings where answer-only supervision is ambiguous. In a controlled synthetic task with 16 key/value slots and intentionally repeated answer values (creating distractor evidence), we compare models trained with and without an auxiliary cross-entropy loss on the true evidence slot. Across 10 random seeds with 2,048 validation examples each, the auxiliary loss at weight 0.3 improves answer accuracy from 0.775 ± 0.025 to 0.983 ± 0.007 and evidence accuracy from 0.699 ± 0.031 to 0.975 ± 0.010 (paired *p* < 5 × 10⁻¹⁰ for both). These results support the hypothesis that direct evidence-slot supervision resolves underdetermination in answer-only training. However, this finding is currently limited to a synthetic NumPy dot-product retrieval model; generalization to production transformer-based RAG systems remains unestablished.

---

## 1. Introduction

In retrieval-augmented generation (RAG) and related settings, models are typically supervised on answer correctness alone. When multiple context items yield the same answer value, answer-only loss provides no signal distinguishing the true evidence from distractors sharing the answer. This underdetermination can cause attention to distribute incorrectly across evidence and distractor slots, degrading both attribution quality and downstream answer accuracy.

We propose an auxiliary evidence-recall head that directly supervises the attention distribution on the true evidence slot via cross-entropy loss, jointly trained with the answer loss. The core hypothesis is: *when answer labels underdetermine which context item justified the answer, direct evidence-slot supervision resolves the ambiguity and produces better retrieval alignment and answer accuracy*.

We test this hypothesis in a minimal controlled setting—a synthetic differentiable retrieval task implemented in NumPy—where the ambiguity is injected by design. This paper reports the experimental results, their statistical strength, and the substantial limitations that constrain what can be concluded.

---

## 2. Method

### 2.1 Task Design

Each example consists of 16 key/value slots. One query key is provided. The target answer is the value at the slot whose key matches the query. Values are intentionally repeated across slots, with at least one distractor slot containing the same answer value as the true evidence slot. This design guarantees that answer-only supervision cannot distinguish the true evidence from value-matched distractors.

### 2.2 Model

The model is a small NumPy dot-product retrieval head with separate query and key embeddings. Answer probability is computed as attention mass aggregated by value class. The auxiliary evidence head applies the same attention distribution but is supervised with cross-entropy on the true evidence slot index.

### 2.3 Training Configuration

- Training examples per seed: 512
- Validation examples per seed: 2,048
- Training epochs: 80
- Random seeds: 10 (seeds 0–9)
- Auxiliary loss weights tested: 0.0, 0.1, 0.3, 1.0
- Total loss: L = L_answer + λ · L_evidence, where λ is the auxiliary weight

### 2.4 Metrics

- **Answer accuracy**: proportion of validation examples where the model's predicted answer matches the target.
- **Evidence accuracy**: proportion of validation examples where the slot with highest attention mass is the true evidence slot.
- **Evidence mass**: mean attention mass assigned to the true evidence slot (a softer measure of localization quality).
- **Target answer mass**: mean attention mass on all slots sharing the target answer value (including distractors), recorded in the decision ledger as an additional diagnostic.

### 2.5 Statistical Analysis

We report mean ± standard deviation across 10 seeds. For the primary comparison (aux weight 0.3 vs. baseline 0.0), we compute paired differences per seed and report two-sided paired *t*-test *p*-values.

---

## 3. Results

### 3.1 Main Results

| Aux weight (λ) | Answer acc (mean ± sd) | Evidence acc (mean ± sd) | Evidence mass (mean ± sd) |
|---:|---:|---:|---:|
| 0.0 | 0.7747 ± 0.0246 | 0.6994 ± 0.0310 | 0.6514 ± 0.0252 |
| 0.1 | 0.9281 ± 0.0125 | 0.8965 ± 0.0190 | 0.8267 ± 0.0160 |
| 0.3 | 0.9828 ± 0.0074 | 0.9746 ± 0.0096 | 0.9142 ± 0.0141 |
| 1.0 | 0.9937 ± 0.0051 | 0.9878 ± 0.0081 | 0.9672 ± 0.0076 |

All three metrics improve monotonically with increasing auxiliary weight. The improvement is substantial even at λ = 0.1 and approaches ceiling at λ = 1.0. Standard deviations decrease with increasing auxiliary weight, suggesting the auxiliary loss also reduces run-to-run variability.

### 3.2 Paired Comparison: λ = 0.3 vs. λ = 0.0

| Metric | Mean paired Δ | Paired *t* *p*-value |
|---|---:|---:|
| Answer accuracy | +0.2081 | 4.15 × 10⁻¹⁰ |
| Evidence accuracy | +0.2752 | 2.10 × 10⁻¹⁰ |
| Evidence mass | +0.2629 | 7.24 × 10⁻¹¹ |

Paired improvements were positive for every seed (10/10), with no exceptions. The *p*-values are far below conventional significance thresholds, though we note that the very small *p*-values partly reflect the large effect size relative to low within-condition variance rather than a large sample.

### 3.3 Target Answer Mass

The decision ledger records target answer mass (attention mass on all slots sharing the target answer value, including distractors). At λ = 0.3, target answer mass is 0.9297 ± 0.0117, compared to 0.7145 ± 0.0212 at baseline. This confirms that the auxiliary loss not only concentrates attention on the true evidence slot but also improves aggregation over the correct answer value as a whole.

### 3.4 Negative and Mixed Observations

No negative results were observed in this synthetic setting: all seeds and all auxiliary weights showed improvement over baseline. This uniformity is itself a limitation—it suggests the task may be too easy or too well-controlled to reveal failure modes that would appear in more realistic settings. The absence of any seed where the auxiliary loss hurt performance should not be taken as evidence that such failure modes cannot exist.

---

## 4. Limitations

1. **Synthetic task only.** The experiment uses a minimal NumPy dot-product retrieval head on a synthetic task with 16 slots, discrete key matching, and controlled value repetition. This is a toy simulation designed to isolate the mechanism, not a validation on real data or real models. No llama.cpp hook-prototype, CUDA copy calibration, or production validation was performed.

2. **No transformer or LLM integration.** The model has no transformer layers, no tokenization, no multi-hop reasoning, and no natural language. Whether the auxiliary evidence loss transfers to transformer-based RAG systems with learned retrieval is unknown.

3. **Single true evidence slot assumed.** The task and loss assume exactly one ground-truth evidence slot per example. Multi-hop evidence (where multiple slots jointly support the answer) and noisy or ambiguous evidence labels are untested.

4. **No calibration or hallucination measurement.** We measure accuracy and attention mass but do not evaluate calibration (reliability of confidence), hallucination rate, or support attribution precision/recall in a real retrieval setting.

5. **Scale and distribution.** The task has 16 slots, small vocabulary, and 512 training examples. The distribution of key/value repetitions is synthetic and may not reflect the statistics of real retrieval corpora.

6. **Auxiliary weight selection.** We test four weights (0.0, 0.1, 0.3, 1.0) but do not perform a systematic hyperparameter search. The apparent monotonic improvement may not hold in settings where the evidence loss conflicts more strongly with the answer loss.

7. **No GPU utilization calibration.** The experiment is CPU-only (max RSS 46,936 kB, 27.04 s wall time on an NVIDIA GB10 host). No CUDA copy calibration or GPU benchmarking was performed or needed for this experiment.

8. **Claim audit incomplete.** The claim ledger for this draft contains no formally audited claims. The limitation "Model-authored draft; human claim audit required" is noted in the ledger. All reported findings should be treated as provisional pending independent verification.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Code available | `scripts/evidence_recall_aux_head.py` (local artifact) |
| Random seeds reported | Yes: seeds 0–9 |
| Hyperparameters reported | Yes: aux weights {0.0, 0.1, 0.3, 1.0}, 80 epochs, 512 train / 2048 val |
| Hardware reported | NVIDIA GB10 host, CUDA 13.0 driver; experiment CPU-only |
| Memory footprint reported | Max RSS 46,936 kB; swap disabled (0 kB total) |
| Wall time reported | 27.04 s for full 10-seed × 4-weight run |
| Statistical tests reported | Paired two-sided *t*-tests with exact *p*-values |
| Raw results available | `artifacts/evidence_recall_results.json` (local artifact) |
| Smoke test available | `artifacts/evidence_recall_smoke.json` (local artifact) |
| Environment log available | `artifacts/logs/environment_probe.log` (local artifact) |
| Validation checks | `py_compile` and `json.tool` passed on script and output files |
| Claim audit | Not yet performed; claim ledger empty at time of drafting |

---

## 6. Conclusion

In a controlled synthetic retrieval task where answer-only supervision is ambiguous due to repeated values, an auxiliary evidence-recall loss substantially improves both evidence localization and answer accuracy. At auxiliary weight 0.3, answer accuracy improves from 0.775 to 0.983 and evidence accuracy from 0.699 to 0.975, with paired *p*-values below 10⁻⁹ across 10 seeds. The improvement is consistent across all seeds with no exceptions.

These results support the hypothesis that direct evidence-slot supervision resolves underdetermination in answer-only training. However, the evidence is confined to a toy NumPy retrieval model on a synthetic task. The uniformity of positive results across all seeds and conditions, while statistically strong, also indicates that the task may not be sufficiently challenging to reveal failure modes present in more realistic settings.

Scientific closure for real systems requires: (1) evaluation on evidence-labeled QA/RAG datasets with trusted support spans, (2) integration into a transformer/RAG model as a separate recall or citation head, (3) measurement of support attribution precision/recall, calibration, and hallucination rate, and (4) ablations for noisy and multi-hop evidence labels.

The result is promising enough to justify a next-stage prototype on a small real evidence-labeled dataset, but it does not yet establish production value.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Experiment script | `scripts/evidence_recall_aux_head.py` |
| Environment probe log | `artifacts/logs/environment_probe.log` |
| Smoke test log | `artifacts/logs/evidence_recall_smoke.log` |
| Smoke test results | `artifacts/evidence_recall_smoke.json` |
| Full run log | `artifacts/logs/evidence_recall_full.log` |
| Full run results | `artifacts/evidence_recall_results.json` |
| Summary log | `artifacts/logs/evidence_recall_summary.log` |
| Project decision ledger | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260502T143048579794+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T143048579794+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T143048579794+0000/paper_manifest.json` |
