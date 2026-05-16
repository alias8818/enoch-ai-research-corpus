# Dense Mask Distillation from Mixture-of-Experts: A Controlled Mechanistic Study

**AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision records, experiment logs, and metric summaries). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review is asserted or required by this notice.

---

## Abstract

Mixture-of-Experts (MoE) layers achieve conditional computation through input-dependent routing, but deployment requires memory proportional to the total number of experts. We investigate whether the conditional structure encoded by an MoE router can be transferred to a dense student network augmented with input-dependent hidden-unit masks. On a synthetic piecewise nonlinear regression task with four latent domains, we distill a 4-expert MoE teacher (2,708 parameters) into several student architectures under matched parameter budgets. A dense student with router-distilled group masks (2,024 parameters) reduces mean squared error (MSE) to the teacher by 76.2% relative to a parameter-matched ordinary dense MLP (2,020 parameters), and achieves 99.5% router agreement with the teacher. Without the router distillation loss, the same mask architecture achieves only 8.9% router agreement and substantially higher error. These results support the mechanistic viability of router-informed dense mask distillation. However, they are confined to a synthetic regression setting with CPU-only execution, an unoptimized mask implementation that does not demonstrate inference latency gains, and only three random seeds. We do not claim language-model-scale results, inference speedup, or general-domain applicability.

---

## 1. Introduction

Mixture-of-Experts models scale network capacity through conditional computation: a router selects a sparse subset of expert subnetworks per input, enabling total parameter counts that exceed per-example activation counts. This conditional structure is valuable for scaling but creates deployment challenges, as all expert parameters must reside in memory regardless of per-example sparsity.

Knowledge distillation from MoE to dense models is a natural compression strategy. Prior work has explored MoE-to-dense distillation in speech recognition and expert-wise pruning using router hints. A central question is whether the input-dependent routing structure itself carries compressible information that a dense student can exploit, or whether a sufficiently large dense student can absorb MoE behavior through output distillation alone.

We propose a simple mechanism: a dense student augmented with input-dependent hidden-unit masks, where the mask router is trained by distillation from the MoE teacher's router. At inference, the student selects a hard top-1 mask group, activating only a fraction of hidden units—mirroring the conditional activation pattern of the original MoE, but within a single dense weight matrix.

This paper reports a controlled experiment on a synthetic task. The contribution is a mechanistic demonstration that router distillation into dense masks substantially improves distillation fidelity under matched parameter counts, together with an honest accounting of the gaps between this result and practical deployment. We do not claim results at language-model scale, inference speedup, or general applicability.

---

## 2. Method

### 2.1 Task Design

We construct a synthetic piecewise nonlinear regression problem with four latent domains, determined by the signs of input dimensions 0 and 1. Each domain applies a distinct nonlinear function to the input. This design ensures that an MoE with four experts has a natural expert–domain alignment, providing a controlled testbed for whether students can recover conditional structure. The task is intentionally simple: it isolates the mechanism of interest (router-informed masking) from confounds present in real MoE models (overlapping routing, noisy targets, high-dimensional outputs).

### 2.2 Teacher Model

The teacher is a 4-expert MoE with 2,708 total parameters. Each expert is a small MLP. The teacher is trained with two losses:

- **Output MSE loss** against ground-truth targets.
- **Router cross-entropy loss** against domain labels derived from the input sign structure.

This ensures the teacher develops both accurate domain-specific outputs and a well-structured router with clear expert–domain alignment.

### 2.3 Student Architectures

All students are trained by distillation against the teacher's outputs (MSE to teacher predictions). We evaluate five student configurations:

| Model | Parameters | Architecture | Active Hidden Fraction (Eval) |
|---|---:|---|---:|
| `dense_h16` | 340 | Dense MLP, hidden size 16 | 1.00 |
| `dense_h64` | 1,348 | Dense MLP, hidden size 64 | 1.00 |
| `dense_h96` | 2,020 | Dense MLP, hidden size 96 | 1.00 |
| `mask_no_router_loss` | 2,024 | Dense + 4-group mask, output distillation only | 0.25 |
| `mask_router_distilled` | 2,024 | Dense + 4-group mask, output + router distillation | 0.25 |

The mask students share a single dense first-layer weight matrix partitioned into four groups. A learned router selects one group per input via hard top-1 at evaluation time, yielding a theoretical active hidden fraction of 0.25. The `mask_router_distilled` variant adds a cross-entropy loss between the student router's selection and the teacher's top-1 route.

### 2.4 Training Protocol

- **Teacher training:** 80 epochs (primary 3-seed runs) or 120 epochs (calibration run), MSE + router cross-entropy.
- **Student training:** 80 epochs (primary 3-seed runs) or 120 epochs (calibration run), distillation MSE to teacher outputs; router cross-entropy added for `mask_router_distilled`.
- **Random seeds:** 0, 1, 2 for primary runs; seed 0 for calibration and smoke tests.
- **Optimizer and learning rate:** Recorded in the experiment scripts (`scripts/dense_mask_distill.py`).

### 2.5 Implementation Caveat

The current mask evaluation computes the full dense first-layer activation and then applies a hard group mask. This means the measured CPU wall time does not reflect a sparse or group-skipping kernel implementation. The `active_hidden_frac_eval = 0.25` is a theoretical value assuming such an implementation exists. **No inference latency improvement should be attributed to the mask architecture based on these experiments.** This is a representational result, not a deployment-speed result.

---

## 3. Results

### 3.1 Primary Metrics

Results across three seeds, reported as mean ± population standard deviation:

| Model | Params | Active Hidden Frac | MSE to Teacher | MSE to Truth | Router Agreement |
|---|---:|---:|---:|---:|---:|
| teacher | 2,708 | 1.00 | 0.00000 ± 0.00000 | 0.01262 ± 0.00222 | 1.00000 |
| dense_h16 | 340 | 1.00 | 0.27911 ± 0.02968 | 0.29314 ± 0.03072 | n/a |
| dense_h64 | 1,348 | 1.00 | 0.14564 ± 0.01202 | 0.16216 ± 0.01486 | n/a |
| dense_h96 | 2,020 | 1.00 | 0.12951 ± 0.00858 | 0.14587 ± 0.01060 | n/a |
| mask_no_router_loss | 2,024 | 0.25 | 0.04437 ± 0.01049 | 0.05226 ± 0.00825 | 0.08880 |
| mask_router_distilled | 2,024 | 0.25 | 0.03077 ± 0.00268 | 0.03954 ± 0.00330 | 0.99493 |

The teacher's MSE to truth (0.01262) reflects the residual error of a well-trained 4-expert MoE on this task. All student MSE values are measured relative to both teacher outputs and ground truth.

### 3.2 Parameter-Matched Comparison

The primary comparison is between `dense_h96` (2,020 params) and `mask_router_distilled` (2,024 params), which are effectively parameter-matched:

- **Teacher MSE reduction:** 76.2% (0.1295 → 0.0308)
- **Truth MSE reduction:** 72.9% (0.1459 → 0.0395)

The mask student with router distillation substantially outperforms the ordinary dense student at the same parameter budget on both distillation fidelity and ground-truth accuracy. The magnitude of this gap is notable: the parameter-matched dense student remains far from the teacher's own error level, while the router-distilled mask student approaches it much more closely.

### 3.3 Effect of Router Distillation Loss

Comparing the two mask variants reveals the critical role of the router distillation loss:

- `mask_no_router_loss` achieves only 8.9% router agreement with the teacher, and its MSE to teacher (0.0444) is substantially higher than the router-distilled variant (0.0308).
- `mask_router_distilled` achieves 99.5% router agreement, and its MSE to teacher is 30.6% lower than the no-router-loss variant.

Without explicit supervision on which group to activate, the mask student's router fails to recover the teacher's conditional structure, and the representational benefit of masking is diminished. With router distillation, the student closely replicates the teacher's routing decisions and achieves substantially better distillation fidelity. This suggests that the mask architecture's advantage depends on correctly recovering the routing structure, not merely on having maskable groups.

### 3.4 Scaling with Dense Capacity

Increasing dense student capacity from 340 to 2,020 parameters monotonically reduces MSE, but even the largest dense student (`dense_h96`) remains far from the mask student's performance. At the parameter budgets tested, the conditional structure captured by masking provides a representational advantage that pure capacity scaling does not recover. Whether this holds at larger parameter budgets or different capacity ratios is not tested.

### 3.5 Inference Latency

The mask student's measured CPU evaluation time was slower than the dense students, consistent with the implementation caveat: the full dense layer is computed before masking. No latency or throughput improvement was observed. This is an expected negative result given the implementation choice, and it should not be interpreted as evidence against the approach—only as evidence that the current implementation does not realize the theoretical sparsity benefit.

---

## 4. Limitations

1. **Synthetic task only.** The regression problem has clean, discrete latent domains with a known expert–domain alignment. Real MoE models exhibit softer, overlapping routing patterns, and language-model tasks involve high-dimensional, noisy targets. Whether router-distilled masks transfer to these settings is unknown.

2. **Small scale.** The teacher has 2,708 parameters and four experts. Scaling to transformer-scale MoE layers with hundreds of experts and billions of parameters introduces optimization, memory, and routing dynamics not present here. The result is a mechanistic demonstration, not a scalability claim.

3. **No inference speedup demonstrated.** The mask implementation computes dense activations before applying hard masks. The theoretical 0.25 active hidden fraction would require a group-skipping or sparse kernel to realize as latency or energy savings, which was not implemented or measured. This is a representational result, not a deployment result.

4. **CPU-only execution.** Experiments ran on a PyTorch CPU build (torch 2.11.0+cpu). No CUDA or hardware-accelerated inference results were obtained. The host had an NVIDIA GB10 device visible via `nvidia-smi`, but `torch.cuda.is_available()` returned false with the installed wheel, and all computation was CPU-only.

5. **Limited seed count.** Three random seeds provide a preliminary signal sufficient for a local action decision, but are inadequate for publication-grade statistical claims. The population standard deviations reported are descriptive statistics, not inferential. Confidence intervals and hypothesis tests are not reported.

6. **No comparison to alternative compression methods.** The experiment does not compare against structured pruning, low-rank adaptation, or other MoE compression techniques. The observed advantage is relative to a naive dense baseline only. Whether router-distilled masks outperform these alternatives is unknown.

7. **Router agreement metric is task-specific.** The 99.5% router agreement reflects the clean domain structure of the synthetic task. In real MoE models with softer routing distributions, exact route agreement may be neither achievable nor desirable. A more nuanced routing divergence metric would be needed for real-model evaluation.

8. **Claim audit status.** The claim ledger for this artifact is in `blocked_empty_claims` status: no structured claims were extracted for formal evidence auditing. The results reported here are drawn directly from the run notes and decision record and have not passed a formal claim/evidence audit.

---

## 5. Reproducibility Checklist

- **Code available:** `scripts/dense_mask_distill.py` (experiment driver), `scripts/aggregate_results.py` (aggregation script).
- **Dependencies specified:** `requirements.txt` (PyTorch CPU wheel, NumPy).
- **Exact commands recorded:** Full command lines for setup, smoke test, calibration run, and primary 3-seed runs are recorded in `run_notes.md`.
- **Random seeds:** 0, 1, 2 for primary runs; seed 0 for calibration and smoke tests.
- **Hardware environment:** Linux 6.17.0-1014-nvidia-aarch64, NVIDIA GB10 visible but not used, ~122 GB available RAM, maximum RSS ~315 MB (from `/usr/bin/time -v`).
- **Software environment:** Python 3, PyTorch 2.11.0+cpu, NumPy. Virtual environment with CPU-only PyTorch wheel installed from `https://download.pytorch.org/whl/cpu`.
- **Output artifacts:** JSONL per-seed logs, per-seed JSON summaries, aggregated CSV (`results/metrics_full_h96.csv`), aggregated summary JSON (`results/metrics_full_h96_summary.json`), full stdout/stderr logs for all runs.
- **Reproduction steps:** Create virtual environment, install dependencies per `requirements.txt`, run commands as specified in `run_notes.md`. Total wall time for the 3-seed primary run is on the order of minutes on a modern CPU.
- **Threading:** Primary runs used `--threads 16`.

---

## 6. Conclusion

We have shown that a dense student augmented with input-dependent hidden-unit masks, where the mask router is distilled from an MoE teacher's router, substantially outperforms a parameter-matched ordinary dense MLP on a synthetic MoE distillation task. The router distillation loss is critical: without it, the mask student fails to recover the teacher's routing structure (8.9% agreement), and the advantage over a plain dense student, while still present, is substantially diminished. With router distillation, the student achieves 99.5% router agreement and 76.2% lower MSE to the teacher compared to the best dense baseline at matched parameter count.

These findings support the mechanistic viability of router-informed dense mask distillation as a compression strategy that preserves conditional structure. However, the result is confined to a controlled synthetic setting and does not demonstrate inference speedup, language-model performance, or scalability beyond four experts and 2,708 teacher parameters. The negative result on measured inference latency—expected given the unoptimized mask implementation—underscores that representational viability and deployment viability are distinct questions.

The next stage requires: (1) porting the mask-distillation loss to a transformer FFN/MoE layer and distilling from a small open MoE checkpoint; (2) implementing group-skipping inference to test whether the reduced active hidden fraction translates to real latency or energy savings; and (3) comparing against structured pruning and adapter baselines on a language-model validation set. Until such evidence is obtained, the present result should be treated as a promising but preliminary mechanistic demonstration with unknown generalization properties.

---

## Referenced Artifacts

| Artifact | Description |
|---|---|
| `run_notes.md` | Full experiment narrative, commands, environment details, and interpretation |
| `scripts/dense_mask_distill.py` | PyTorch experiment driver |
| `scripts/aggregate_results.py` | Aggregation script (JSONL → CSV + summary JSON) |
| `requirements.txt` | Minimal reproduction dependencies |
| `logs/smoke.log` | Smoke test output |
| `logs/full_seed0.log` | Calibration 120-epoch run log |
| `logs/full_h96_seed0.log` | Primary run, seed 0 |
| `logs/full_h96_seed1.log` | Primary run, seed 1 |
| `logs/full_h96_seed2.log` | Primary run, seed 2 |
| `results/full_h96/summary_full_seed0.json` | Per-seed summary, seed 0 |
| `results/full_h96/summary_full_seed1.json` | Per-seed summary, seed 1 |
| `results/full_h96/summary_full_seed2.json` | Per-seed summary, seed 2 |
| `results/metrics_full_h96.csv` | Aggregated metrics across seeds |
| `results/metrics_full_h96_summary.json` | Aggregated summary JSON |
| `.omx/project_decision.json` | Decision record with primary metrics, limitations, and next steps |
| `papers/.../claim_ledger.json` | Claim ledger (status: `blocked_empty_claims`; no structured claims extracted) |
| `papers/.../evidence_bundle.json` | Evidence bundle (source: `langgraph_control_plane_mvp`) |
