# Asymmetric Key/Value Adapter Rank Allocation: A Mechanistic Study in Synthetic Frozen Attention

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts (run notes, decision JSON, experiment logs, and result files). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review is asserted or implied.

---

## Abstract

Low-rank adapter (LoRA) methods typically assign a single rank hyperparameter uniformly across all targeted attention projections. This study investigates whether allocating adapter rank asymmetrically between key ($W_k$) and value ($W_v$) projections—while holding total trainable parameters constant—can improve adaptation quality when the target adaptation itself has asymmetric intrinsic rank structure. We construct a controlled synthetic setting: a frozen single-head attention block is trained via low-rank residuals on $W_k$ and $W_v$ to imitate teachers with known adaptation structure (value-only rank-4, key-only rank-4, and mixed rank-1 key / rank-3 value). Across three teacher tasks and seven rank configurations at equal parameter budget, the task-matched asymmetric split consistently and substantially outperforms the symmetric K2/V2 baseline, with mean validation MSE reductions of multiple orders of magnitude. However, the optimal split is task-dependent: no single K/V ratio dominates across tasks. These results support asymmetric K/V rank allocation as a task-conditioned design choice, not as a universal rule. The evidence is limited to a single synthetic attention layer and does not demonstrate improvement in real pretrained-transformer fine-tuning.

## Introduction

Low-rank adaptation (LoRA) freezes pretrained model weights and injects trainable low-rank matrix pairs into targeted linear projections, achieving significant reductions in trainable parameters and optimizer memory with no inference-time latency after adapter merging. Standard practice exposes a single adapter rank hyperparameter applied uniformly across all targeted modules—typically the query, key, and value projections of attention layers.

An implicit assumption of uniform rank allocation is that the intrinsic dimensionality of the required adaptation is similar across projections. However, key and value projections serve distinct computational roles: keys govern attention routing (which tokens are attended to), while values govern content mixing (what information is carried through). If a downstream task primarily requires rerouting attention patterns, the key-side adaptation may have higher intrinsic rank than the value-side adaptation, and vice versa for tasks that primarily require output content remapping.

Prior work on adapter asymmetry has studied asymmetry between the two LoRA factors ($A$ vs. $B$) within a single projection, rather than asymmetry between different projection types. The question of whether the rank budget should be distributed differently between key and value projections remains open.

This work asks: **Can an asymmetric K/V rank allocation outperform a symmetric allocation at the same trainable-parameter budget, and if so, under what conditions?**

To isolate mechanism from confounds present in full-model fine-tuning, we adopt a synthetic experimental design: a single frozen attention head is trained to match teachers with known, controlled adaptation structure. This allows us to determine whether the training loop can recover an asymmetric adaptation when given the appropriate rank budget, and whether a mismatched symmetric allocation imposes a measurable cost. We emphasize upfront that this is a mechanistic probe in a toy setting, not a validation of the approach on real pretrained models.

## Method

### Experimental Design

We construct a synthetic, frozen single-head attention block and train only low-rank residual adapters on $W_k$ and $W_v$ to imitate teacher models with known hidden adaptation structure. The base attention block parameters are frozen; only the LoRA-style low-rank residuals are trainable. This is a toy simulation designed to test whether rank-matching is sufficient and necessary for recovery of a known adaptation, absent the confounds of multi-layer interactions, real data distributions, and nonlinear cross-layer effects.

### Teacher Tasks

Three teacher configurations define the target adaptation, each with a total intrinsic rank of 4:

1. **value_only_teacher**: The true teacher update is rank-4 on $W_v$ only (zero rank on $W_k$). This represents tasks where adaptation is purely content-remapping.
2. **key_only_teacher**: The true teacher update is rank-4 on $W_k$ only (zero rank on $W_v$). This represents tasks where adaptation is purely attention-rerouting.
3. **mixed_k1_v3_teacher**: The true teacher update is rank-1 on $W_k$ and rank-3 on $W_v$. This represents tasks with mixed adaptation structure.

### Student Configurations

At an equal trainable-parameter budget (total adapter rank = 4), five rank allocations are compared:

| Configuration | Key rank | Value rank | Total rank |
|---|---|---|---|
| K4/V0 | 4 | 0 | 4 |
| K3/V1 | 3 | 1 | 4 |
| K2/V2 | 2 | 2 | 4 |
| K1/V3 | 1 | 3 | 4 |
| K0/V4 | 0 | 4 | 4 |

A K4/V4 configuration (total rank 8, double the parameter budget) is included as a capacity sanity check to confirm the training loop can converge when sufficient rank is available. A frozen baseline (K0/V0, no adapters) is also measured.

### Training Details

- **Optimizer**: AdamW
- **Batch size**: 256
- **Training steps**: 800
- **Validation batches**: 8
- **Seeds**: 3 per configuration per task (63 total experimental conditions)
- **Validation metric**: Output MSE against the teacher

A bug was encountered and patched during the main run: PyTorch optimizers reject an empty parameter list, causing zero-rank configurations (K0/V0 boundary cases) to fail. The script was patched to skip optimizer creation and stepping when no trainable parameters exist. The patch was verified via a repeat smoke test before the main run.

### Hardware and Environment

- **GPU**: NVIDIA GB10
- **Platform**: Ubuntu aarch64
- **CUDA driver**: 580 / CUDA 13.0
- **PyTorch**: 2.11.0+cu130
- **Available memory**: ~116 GiB (swap disabled intentionally)
- **Throughput**: ~11M–19M tokens/s for equal-budget configs during the main loop; calibration mode measured ~3.30M tokens/s for K1/V3
- **GPU utilization**: 50–80% during main-loop polling; 20% during calibration; 0% at idle (42°C post-run)

A smoke-first, then-calibrate, then-main protocol was followed per GB10 operational constraints. Calibration was capped at 50 steps by the script (despite a 100-step request flag), which was accepted as sufficient for throughput estimation.

## Results

### Main Results

Mean validation MSE over 3 seeds for each task and rank configuration:

| Task | Best equal-budget split | Best MSE | Symmetric K2/V2 MSE | Frozen baseline MSE |
|---|---|---|---|---|
| value_only_teacher | K0/V4 | 3.05 × 10⁻¹⁴ | 1.99 × 10⁻¹ | 5.50 × 10⁻¹ |
| key_only_teacher | K4/V0 | 7.78 × 10⁻¹⁴ | 1.60 × 10⁻¹ | 3.12 × 10⁻¹ |
| mixed_k1_v3_teacher | K1/V3 | 8.03 × 10⁻¹³ | 4.04 × 10⁻¹ | 2.12 |

The K4/V4 over-provisioned sanity check reached near-zero MSE for all three tasks, confirming that the training loop and optimization landscape are sound when sufficient rank is available.

### Interpretation

For each teacher task, the rank allocation that matches the teacher's intrinsic K/V rank profile achieves near-zero MSE, while the symmetric K2/V2 allocation performs substantially worse—by multiple orders of magnitude in MSE. Specifically:

- When adaptation is value-side only (value_only_teacher), allocating all rank budget to value (K0/V4) recovers the teacher; symmetric K2/V2 wastes half the budget on key rank that cannot contribute to the adaptation, leaving value rank insufficient.
- When adaptation is key-side only (key_only_teacher), the pattern reverses: K4/V0 dominates; K2/V2 wastes budget on value rank.
- When adaptation is mixed (mixed_k1_v3_teacher), the exact asymmetric split K1/V3 matches the teacher's rank profile and outperforms K2/V2.

These results establish that **the optimal K/V rank split is task-conditioned**. There is no universal best allocation: the best split follows the intrinsic rank profile of the target adaptation.

### Negative and Mixed Observations

The results also carry a clear negative implication: any fixed K/V ratio (including the symmetric default) will be suboptimal for tasks whose adaptation structure does not match that ratio. The symmetric K2/V2 split, while better than the frozen baseline in all cases, is far from optimal in every task tested. A practitioner who deploys a fixed asymmetric split (e.g., always favoring value rank) would similarly fail on key-dominant tasks. The data reject the hypothesis of a universal optimal K/V split.

## Limitations

1. **Synthetic, single-layer setting.** The experiment deliberately isolates mechanism in one frozen synthetic attention layer. This proves that asymmetric rank allocation *can* work in principle, but does not demonstrate improvement in real pretrained-transformer fine-tuning with multi-layer, multi-head attention, nonlinear interactions between layers, or real data distributions. The gap between this toy simulation and production validation is substantial.

2. **Known teacher structure.** The student configurations are evaluated against teachers with known rank structure. In practice, the intrinsic K/V rank profile of a real downstream task is unknown a priori, making the optimal allocation a hyperparameter to be searched—potentially at nontrivial cost.

3. **Single-head attention.** Real transformers use multi-head attention with per-head key and value projections. The interaction between rank allocation and head structure is not addressed.

4. **No downstream task evaluation.** The metric is output MSE against a teacher, not a downstream task metric (e.g., accuracy, BLEU, perplexity). The relationship between MSE reduction and downstream quality is not established.

5. **Small scale.** The experiment involves a tiny synthetic model. Scaling behavior—whether the observed effects persist, amplify, or diminish at practical model sizes—is unknown.

6. **Rejection of universal split.** The results explicitly reject the existence of a single best K/V ratio. Any practical deployment requires task-specific tuning or heuristics for rank allocation, which partially offsets the simplicity gain that motivates uniform rank in the first place.

7. **Seed count.** Three seeds per condition provide a directional signal but limited statistical power. Confidence intervals are not reported and the variance structure across seeds is not analyzed in depth.

## Reproducibility Checklist

- **Code**: `src/asym_kv_adapter_experiment.py`, `src/summarize_results.py`, `src/plot_results.py`
- **Raw results**: `artifacts/main_results.jsonl` (63 rows: 3 tasks × 7 configs × 3 seeds)
- **Aggregated results**: `artifacts/summary.txt`, `artifacts/summary.csv`, `artifacts/best_rank4.csv`
- **Visualization**: `artifacts/rank_allocation_mse.png`
- **Run logs**: `logs/smoke_20260501_190219.log`, `logs/calibrate_20260501_190254.log`, `logs/main_20260501_190254.log`, `logs/smoke_after_patch.log`, `logs/mem_after_main.log`, `logs/nvidia_smi_after_main.log`
- **System probe**: `.omx/system_probe.log`
- **Smoke test results**: `artifacts/smoke_results.jsonl`, `artifacts/smoke_results_after_patch.jsonl`
- **Calibration results**: `artifacts/calibration_results.jsonl`
- **Hardware**: NVIDIA GB10, Ubuntu aarch64, CUDA 580/13.0, PyTorch 2.11.0+cu130
- **Random seeds**: 3 per condition (explicit in raw results file)
- **Known bug and patch**: Zero-rank configurations fail with unpatched PyTorch optimizer; patch skips optimizer creation when parameter list is empty. Patch verified via repeat smoke test.
- **Dependencies**: `torch`, `numpy`, `matplotlib`, `pandas` (installed via pip in venv)
- **Operational protocol**: Smoke → calibration → main run (GB10 constraint)

## Conclusion

This study provides mechanistic evidence that asymmetric rank allocation between key and value adapter projections can substantially outperform symmetric allocation when the target adaptation has asymmetric intrinsic K/V rank structure. In a controlled synthetic attention setting, matching the adapter rank profile to the task's adaptation profile yields near-zero MSE, while symmetric allocation wastes budget on the wrong projection and leaves the correct one under-parameterized—resulting in MSE values orders of magnitude higher.

Crucially, the results also provide a negative finding: **there is no universal optimal K/V split**. The best allocation is task-conditioned, depending on whether the adaptation is routing-dominant (favoring key rank), content-dominant (favoring value rank), or mixed. This constrains any practical deployment: asymmetric K/V rank allocation should be treated as a task-conditioned hyperparameter, not a fixed design rule.

Final scientific closure requires validation in real pretrained-transformer fine-tuning with independently configurable K/V ranks, evaluated on downstream tasks spanning routing-heavy and content-remapping-heavy regimes. A concrete next step would be a small pretrained-transformer K/V rank sweep on at least two task families—one routing-heavy, one content-remapping-heavy—under matched trainable-parameter budgets (e.g., K0/V8, K2/V6, K4/V4, K6/V2, K8/V0, with Q/O held constant or disabled).

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| System probe | `.omx/system_probe.log` |
| Main results (raw) | `artifacts/main_results.jsonl` |
| Summary (text) | `artifacts/summary.txt` |
| Summary (CSV) | `artifacts/summary.csv` |
| Best rank-4 configs | `artifacts/best_rank4.csv` |
| MSE plot | `artifacts/rank_allocation_mse.png` |
| Smoke results | `artifacts/smoke_results.jsonl`, `artifacts/smoke_results_after_patch.jsonl` |
| Calibration results | `artifacts/calibration_results.jsonl` |
| Smoke log | `logs/smoke_20260501_190219.log` |
| Calibration log | `logs/calibrate_20260501_190229.log` |
| Main run log | `logs/main_20260501_190254.log` |
| Post-patch smoke log | `logs/smoke_after_patch.log` |
| Memory log | `logs/mem_after_main.log` |
| GPU log | `logs/nvidia_smi_after_main.log` |
| Experiment source | `src/asym_kv_adapter_experiment.py` |
| Summary source | `src/summarize_results.py` |
| Plot source | `src/plot_results.py` |
| Claim ledger | `papers/source-record-redacted-20260501T235948852683+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T235948852683+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T235948852683+0000/paper_manifest.json` |
