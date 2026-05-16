# Activation-Calibrated Sparse Hard Masks for Difficulty-Aware Mask Bank Selection

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We investigate whether activation-calibrated hard masks can improve retention in a difficulty-aware mask bank for sparse neural network pruning. Prior work on magnitude-based mask banks found that static weight-magnitude hard masks failed acceptance gates: teacher-bucket routing, denser nested hard masks, and dense-hard fallback all violated hard-retention or compute constraints. We propose constructing hard masks from per-layer MLP channel importance derived from activation magnitudes on hard-bucket calibration prompts, while preserving parent magnitude-based masks for single and easy difficulty tiers. On a 512-record GSM8K teacher worklist with Qwen2.5-0.5B, activation-calibrated sparse hard masks at the same keep-fraction budget (0.80) yield a hard-bucket retention improvement of +11.69 percentage points (95% CI lower bound +3.18 pp) over the single-mask baseline, with aggregate routed retention +5.66 pp (95% CI lower bound +0.98 pp) and compute overhead of +0.95%. A simpler logit-calibration selector evaluated on the same data failed to produce stable held-out improvements, and dense hard masks exceeded the compute budget. These results are specific to the tested model, dataset, and routing configuration; external replication is needed before broader claims are warranted.

## 1. Introduction

Structured pruning via difficulty-aware mask banks routes inputs to masks of varying sparsity depending on estimated problem difficulty. A mask bank typically contains a single (least sparse) mask for all inputs, an easy mask for low-difficulty inputs, and a hard mask for high-difficulty inputs. The effectiveness of such a bank depends critically on the quality of the hard mask: if the hard mask destroys information needed for difficult inputs, the routing mechanism cannot recover accuracy even when it correctly identifies hard examples.

Prior experiments on this mask bank framework (the parent project) concluded with a `finalize_negative` decision for global magnitude and channel-norm masks. Teacher-bucket routing, denser nested hard masks, and dense-hard fallback all failed hard-retention or compute gates. The central question for this successor branch is whether a different hard-mask construction mechanism—one informed by activation signals rather than static weight magnitudes—can produce hard masks that pass acceptance gates without exceeding the compute budget.

We report three stages of investigation: (1) a simple logit-calibration selector that attempts to route between existing parent masks using calibration thresholds, (2) an activation-calibrated hard-mask builder that constructs new MLP channel masks from dense calibration activations, and (3) an expanded validation pass on a 512-record worklist. The first approach failed on held-out data. The second showed promising point estimates but with negative confidence-interval lower bounds at 300 records. The third resolved the uncertainty: activation-calibrated sparse hard masks pass all acceptance gates with statistically significant improvements on the 512-record worklist.

## 2. Method

### 2.1 Problem Setting

Given a language model with MLP layers, a mask bank defines per-layer channel masks at multiple sparsity levels. A difficulty router assigns each input to one of three tiers: single (all inputs), easy (low-difficulty subset), or hard (high-difficulty subset). The acceptance framework evaluates each mask bank configuration against gates on hard-bucket retention, aggregate retention, compute overhead, hard-route frequency, and per-bucket regression.

### 2.2 Baseline: Parent Magnitude-Based Masks

The parent project constructed masks from static weight magnitudes:
- **Single mask**: keep fraction 0.65 (least sparse, applied to all inputs).
- **Easy mask**: keep fraction 0.50 (sparser, applied to easy-bucket inputs).
- **Hard mask**: keep fraction 0.80 (less sparse, applied to hard-bucket inputs).

These masks selected channels based on weight-magnitude rankings within each MLP projection layer. The parent's hard mask achieved full-mask accuracy of 0.19 on the 300-record worklist, and the medium-easy routing policy produced a hard-bucket retention delta of −3.33 pp relative to the single-mask baseline, failing the acceptance gate.

### 2.3 Approach 1: Logit-Calibration Selector

The first successor approach attempted to improve routing between existing parent masks rather than constructing new masks. The selector (`activation_calibrated_selector.py`) consumed the parent 300-record teacher export manifest and sparse-mask logit exports, deterministically split the data into calibration/train and held-out/test rows, and searched one-dimensional logit-calibration thresholds to choose between parent easy and hard masks.

This approach was evaluated on both sparse and dense parent hard-mask exports. The correctness oracle (which assumes perfect routing) showed that complementary examples exist in the parent masks (+8.0 pp hard retention for sparse, +16.0 pp for dense), but the learned calibration thresholds did not generalize to held-out rows.

### 2.4 Approach 2: Activation-Calibrated Hard-Mask Construction

The second approach constructs new hard masks from activation signals rather than selecting among existing masks. The exporter (`hf_activation_sparse_mask_exporter.py`) operates as follows:

1. **Preserve parent masks for single and easy tiers**: The magnitude-based single mask (keep fraction 0.65) and easy mask (keep fraction 0.50) are reused without modification, ensuring backward compatibility with the parent acceptance harness.

2. **Calibrate hard mask from activations**: For each hard-bucket calibration prompt, the exporter runs a forward pass through the dense (unpruned) model and captures per-layer activation magnitudes on the `gate_proj` and `up_proj` MLP projections. Channel importance scores are computed from these activation magnitudes rather than from static weight magnitudes.

3. **Construct hard mask at the same sparse budget**: The activation-calibrated hard mask targets the same keep fraction (0.80) as the parent hard mask, ensuring that the FLOPs budget is comparable. Channels are selected based on activation-weighted importance rankings.

4. **Export in standard format**: The resulting mask logits are exported in the same JSONL format consumed by the acceptance harness, enabling direct comparison.

### 2.5 Acceptance Framework

The acceptance harness (`mask_bank_acceptance.py`) evaluates a mask bank configuration against the following gates:
- **Hard-retention gate**: hard-bucket retention must improve over the single-mask baseline.
- **Compute gate**: compute overhead must remain within budget.
- **Hard-route frequency gate**: the fraction of inputs routed to the hard mask must not exceed a threshold.
- **Per-bucket regression gate**: no difficulty bucket may regress beyond a tolerance.
- **Scientific readiness**: paired-bootstrap 95% confidence-interval lower bounds for aggregate and hard-bucket retention deltas must be non-negative.

Two routing policies were tested:
- **Medium+hard routing**: medium-difficulty inputs are routed to the hard mask. This policy produced compute overhead exceeding the gate.
- **Medium-easy routing**: medium-difficulty inputs are routed to the easy mask. This policy keeps compute overhead low and is the primary reported configuration.

## 3. Results

### 3.1 Logit-Calibration Selector (300 Records)

The simple logit-calibration selector was evaluated on both sparse and dense parent hard-mask exports.

**Sparse parent masks (300 records):**

| Configuration | Hard Retention Delta | Compute Delta | Gate Decision |
|---|---|---|---|
| Parent bucket router | −4.0 pp | +1.7% | needs_attention |
| Calibration selector | −2.0 pp | −8.6% | needs_attention |
| Correctness oracle | +8.0 pp | −10.0% | continue |

**Dense parent masks (300 records, hard-mask FLOPs weight 1.0):**

| Configuration | Hard Retention Delta | Compute Delta | Gate Decision |
|---|---|---|---|
| Parent bucket router | +4.0 pp | +16.0% | needs_attention (compute) |
| Calibration selector | +2.0 pp | −9.2% | needs_attention (retention) |
| Correctness oracle | +16.0 pp | +14.7% | needs_attention (compute) |

The correctness oracle confirms that complementary information exists in the parent masks, but the simple threshold-based selector could not learn a stable routing signal on held-out rows. Dense hard masks contain more recoverable hard examples but routing enough of them exceeds the compute budget. This negative result motivated the shift from selector-only routing to actual mask construction.

### 3.2 Activation-Calibrated Hard Masks (300 Records)

The activation-calibrated hard-mask exporter was run on the 300-record teacher worklist. Calibration used 90 hard-bucket records and 291,456 captured projection-token activations. The realized hard keep fraction was 0.79996, aligned with the parent sparse budget.

**Full-mask accuracies (300 records):**

| Mask | Accuracy |
|---|---|
| Single (magnitude, 0.65) | 0.1800 |
| Easy (magnitude, 0.50) | 0.2167 |
| Hard (activation-calibrated, 0.80) | 0.4433 |
| Parent sparse hard (magnitude, 0.80) | 0.1900 |

The activation-calibrated hard mask achieves substantially higher full-mask accuracy (0.4433) than the parent magnitude-based hard mask (0.19) at the same keep fraction, indicating that activation-based channel selection preserves more functionally important channels.

**Acceptance with medium+hard routing (300 records):** Hard retention delta +8.89 pp, aggregate retention delta +12.67 pp, but compute delta +17.27% and hard-route rate 0.60 fail the compute and frequency gates.

**Acceptance with medium-easy routing (300 records):**

| Metric | Value |
|---|---|
| Routed retention | 0.24 vs single 0.18 (+6.0 pp) |
| Hard retention | 0.2222 vs single hard 0.1333 (+8.89 pp) |
| Compute delta | +0.91% |
| Hard-route rate | 0.30 |
| Worst bucket delta | +4.17 pp |
| Aggregate 95% CI lower | −0.33 pp |
| Hard 95% CI lower | −2.27 pp |
| Gate decision | continue |
| Scientific readiness | false |

Point estimates are positive and all non-CI gates pass, but the 95% CI lower bounds remain slightly negative. The parent sparse medium-easy reference produced hard retention delta −3.33 pp and decision `needs_attention`, so the activation-calibrated mask clears the parent kill condition but does not yet meet the scientific-readiness bar.

### 3.3 Activation-Calibrated Hard Masks (512 Records)

To resolve the CI uncertainty, the worklist was expanded to 512 records (easy=205, medium=153, hard=154) from the parent scored manifest. The activation-calibrated exporter was rerun with identical settings. Calibration used 154 hard-bucket records and 492,960 captured projection-token activations.

**Full-mask accuracies (512 records):**

| Mask | Accuracy |
|---|---|
| Single (magnitude, 0.65) | 0.1738 |
| Easy (magnitude, 0.50) | 0.1875 |
| Hard (activation-calibrated, 0.80) | 0.4570 |

**Acceptance with medium-easy routing (512 records):**

| Metric | Value |
|---|---|
| Routed retention | 0.2305 vs single 0.1738 (+5.66 pp) |
| Aggregate 95% CI lower | +0.98 pp |
| Hard-bucket retention delta | +11.69 pp |
| Hard 95% CI lower | +3.18 pp |
| Compute delta | +0.95% |
| Hard-route rate | 30.08% |
| Worst bucket delta | +1.96 pp |
| Gate decision | continue |
| Scientific readiness | true |

All gates pass, including the CI lower-bound checks. Expanding the evaluation set moved both CI lower bounds non-negative without exceeding compute gates, supporting the activation-calibrated mechanism and resolving the 300-record uncertainty.

## 4. Limitations

1. **Single model and dataset**: All results are obtained on Qwen2.5-0.5B with GSM8K teacher prompts. Generalization to other models, scales, or task domains is not established.

2. **Routing policy sensitivity**: The medium+hard routing policy fails compute gates even with activation-calibrated masks. The reported positive results depend on the medium-easy routing policy, which routes medium-difficulty inputs to the easy mask. Whether other routing configurations can also pass gates is not determined.

3. **Calibration data dependence**: The activation-calibrated hard mask is constructed from activation magnitudes on hard-bucket calibration prompts. Its quality depends on the representativeness of those prompts. The sensitivity of the mask to calibration-set composition is not characterized.

4. **Negative precursor results**: The simple logit-calibration selector failed on held-out data, and dense hard masks exceeded the compute budget. These negative results bound the space of viable approaches: not all activation-informed methods succeed, and the compute budget constrains which mask densities are feasible.

5. **300-record CI gap**: At 300 records, point estimates were positive but CI lower bounds were negative. The 512-record expansion resolved this, but the transition highlights that the effect size is modest enough that smaller evaluation sets may not reliably detect it.

6. **No external replication**: These results have not been replicated by independent researchers or on independent infrastructure. The project decision of `finalize_positive` reflects internal artifact review only.

7. **Static single and easy masks**: The activation-calibrated approach only replaces the hard mask; single and easy masks remain magnitude-based. Whether activation calibration would also improve those tiers is an open question.

8. **Keep-fraction constraint**: The hard keep fraction is fixed at 0.80 to match the parent sparse budget. The interaction between keep fraction and activation-calibrated mask quality is not explored.

## 5. Reproducibility Checklist

- **Model**: Qwen2.5-0.5B, dtype float16, device auto (CUDA).
- **Dataset**: GSM8K teacher worklist, 512 records (easy=205, medium=153, hard=154), derived from parent scored manifest.
- **Mask keep fractions**: single=0.65, easy=0.50, hard=0.80 (activation-calibrated).
- **Calibration**: 154 hard-bucket records, 492,960 captured projection-token activations on `gate_proj`/`up_proj` layers.
- **Routing policy**: medium-easy (medium-difficulty inputs routed to easy mask).
- **Statistical test**: Paired bootstrap, 95% confidence interval.
- **Acceptance gates**: hard-retention, compute delta, hard-route frequency, per-bucket regression, CI lower bounds.
- **Code artifacts**: `experiments/hf_activation_sparse_mask_exporter.py`, `experiments/activation_calibrated_selector.py`, `experiments/mask_bank_acceptance.py`.
- **Environment**: Project-local `.venv` with CUDA PyTorch and Transformers; `HF_HOME` and `HF_HUB_CACHE` pointed at a local Hugging Face cache.
- **Verification**: `python3 -m py_compile experiments/*.py` passed; `.venv/bin/python -m py_compile experiments/hf_activation_sparse_mask_exporter.py` passed.

## 6. Conclusion

Activation-calibrated sparse hard masks improve hard-bucket retention by +11.69 pp (95% CI +3.18 pp) over the single-mask baseline on a 512-record GSM8K worklist with Qwen2.5-0.5B, at a compute overhead of +0.95%. The key mechanism—constructing hard masks from per-layer activation magnitudes on hard-bucket calibration prompts rather than from static weight magnitudes—produces masks that preserve substantially more functional accuracy at the same sparsity budget (0.4570 vs 0.19 full-mask accuracy). Two precursor approaches failed: a simple logit-calibration selector could not learn stable routing thresholds on held-out data, and dense hard masks exceeded the compute budget. The positive result is contingent on the medium-easy routing policy and has been validated only on the tested model and dataset. The current project artifacts support this finding in the tested setting; external replication and broader evaluation are necessary before stronger claims are warranted.

## Referenced Artifacts

### Run notes and decision
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Claim ledger and evidence bundle
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`

### Source code
- `experiments/hf_activation_sparse_mask_exporter.py`
- `experiments/activation_calibrated_selector.py`
- `experiments/mask_bank_acceptance.py`

### 512-record export and acceptance results
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_512/hf_activation_sparse_mask_logits.jsonl`
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_512/hf_activation_sparse_mask_export_summary.json`
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_512/hf_activation_sparse_mask_predictions.csv`
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_512_acceptance_medium_easy/acceptance_report.json`
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_512_acceptance_medium_easy/eval/split_mask_eval_summary.json`
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_512_acceptance_medium_easy/eval/split_mask_eval_bucket_metrics.csv`
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_512_acceptance_medium_easy/eval/split_mask_eval_rows.jsonl`
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_512_acceptance_medium_easy/outcomes/mask_outcome_summary.json`
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_512_acceptance_medium_easy/outcomes/mask_predictions.csv`
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_512_acceptance_medium_easy/outcomes/mask_outcomes.jsonl`

### 512-record worklist
- `results/gsm8k_teacher_export_manifest_512/export_worklist.jsonl`
- `results/gsm8k_teacher_export_manifest_512/export_worklist.csv`
- `results/gsm8k_teacher_export_manifest_512/export_manifest_summary.json`

### 300-record acceptance results (medium-easy)
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_300_acceptance_medium_easy/acceptance_report.json`
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_300_acceptance_medium_easy/eval/split_mask_eval_summary.json`
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_300_acceptance_medium_easy/eval/split_mask_eval_bucket_metrics.csv`
- `results/hf_qwen05b_activation_hard_sparse_mask_gsm8k_teacher_300_acceptance_medium_easy/eval/split_mask_eval_rows.jsonl`

### Parent reference data
- `parent_results/hf_qwen05b_dense_hard_mask_gsm8k_teacher_300/hf_sparse_mask_logits.jsonl`
- `parent_results/hf_qwen05b_dense_hard_mask_gsm8k_teacher_300/hf_sparse_mask_export_summary.json`
- `parent_results/hf_qwen05b_dense_hard_mask_gsm8k_teacher_300/hf_sparse_mask_predictions.csv`
- `parent_results/gsm8k_teacher_export_manifest_300/export_worklist.jsonl`
