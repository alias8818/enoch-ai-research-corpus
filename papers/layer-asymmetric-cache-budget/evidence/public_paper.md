# Layer-Asymmetric KV-Cache Budgets Improve Long-Range Retrieval Under Tight Memory Constraints: A Controlled Demonstration

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metrics, and log files). The operator who released these artifacts claims no personal authorship credit for the writing or experimental results. Readers should treat this document as an unreviewed AI-generated research artifact.

---

## Abstract

We investigate whether a fixed total KV-cache memory budget can be allocated more effectively when distributed asymmetrically across transformer layers rather than uniformly. Using a 4-layer causal decoder-only transformer trained on a synthetic delayed-copy task (sequence length 128, copy distance 64 tokens), we compare uniform per-layer sliding-window budgets against same-total asymmetric budgets under dense teacher-forced evaluation. At tight budgets (25.2% and 37.8% of full cache), uniform windows fail to span the 64-token dependency in any layer, collapsing to near-random accuracy (0.12–0.15). Asymmetric budgets that concentrate slots in one or two layers recover 0.68–0.80 absolute accuracy over the matched uniform baseline, with cross-entropy losses reduced by 6.2–8.0 nats. At 50.4% of full cache, both policies saturate at full accuracy, validating the experimental control. The optimal layer-wise shape varies across random seeds, suggesting the supported mechanism is asymmetric budget search itself rather than a single universal schedule. These results are a bounded mechanistic demonstration on a toy architecture and synthetic task; they do not constitute a production inference claim.

## Introduction

Autoregressive transformer inference maintains a growing KV cache whose memory footprint scales with sequence length, model depth, and hidden dimension. Standard implementations allocate equal cache capacity to every layer. When memory is constrained, a common fallback is to apply a uniform sliding-window attention budget—truncating the KV cache identically at each layer.

This uniform allocation is not obviously optimal. Prior work has observed that attention patterns differ systematically across layers: lower layers in large language models often attend broadly while higher layers consolidate onto fewer positions. PyramidKV proposes dynamic layer-wise cache sizing based on attention entropy. SqueezeAttention explicitly argues that uniform per-layer KV allocation is suboptimal and optimizes layer-wise budgets. LAVa targets layer-wise KV eviction with dynamic layer budgets. These approaches share a common intuition: some layers need more cache than others, and a fixed total budget should be distributed accordingly.

The present work asks a minimal, controlled version of this question: for a small transformer on a task with a known long-range dependency, does reallocating the same total number of KV slots from a uniform to an asymmetric per-layer distribution measurably improve next-token prediction quality? We deliberately restrict the experiment to a synthetic setting where the dependency structure is known, the model is small enough to evaluate exhaustively, and the total cache budget is the only variable. This sacrifices generality for mechanistic clarity.

We do not claim a novel method family. The experiment is a bounded evidence check and a concrete reproduction-style demonstration of why layer-asymmetric budgets can matter, complementing the prior work cited above.

## Method

### Task

We use a delayed-copy task over a vocabulary of 8 tokens. Each input sequence of length 128 consists of a 64-token random prefix followed by the same 64-token prefix. The model is trained to predict the copied half, forcing it to retrieve information from 64 positions back. Loss and accuracy are scored only on targets in the copied portion.

### Model

A 4-layer decoder-only transformer with `d_model = 128`, 4 attention heads, and causal masking. The model is small enough to train to convergence quickly and to evaluate under many cache policies without approximation.

### Cache Budget Simulation

We simulate per-layer KV-cache limits via sliding-window attention masks applied during dense teacher-forced evaluation. A per-layer window of `B_l` tokens means layer `l` can attend only to the most recent `B_l` positions. The total cache budget is `sum_l B_l`. All comparisons within a budget group hold this sum constant.

This teacher-forced sliding-window evaluation approximates—but does not exactly replicate—decoding with a per-layer KV cache of size `B_l`. The approximation is close for next-token prediction under greedy decoding but diverges from autoregressive generation with KV-cache eviction, where earlier tokens are permanently discarded. We return to this distinction in the Limitations section.

### Budget Configurations

**Uniform baselines:** `[16,16,16,16]`, `[24,24,24,24]`, `[32,32,32,32]`, `[48,48,48,48]`, `[64,64,64,64]`, `[80,80,80,80]`.

**Asymmetric candidates (same total):**

| Total slots | Asymmetric configurations |
|---:|---|
| 128 | `[80,24,12,12]`, `[12,12,24,80]`, `[16,48,48,16]`, `[48,16,16,48]`, one-long-layer variants |
| 192 | `[96,48,24,24]`, `[24,24,48,96]`, `[32,64,64,32]`, `[72,24,24,72]` |
| 256 | `[112,64,40,40]`, `[40,40,64,112]`, `[48,80,80,48]`, `[96,32,32,96]` |

### Training and Evaluation

Training uses Adam with learning rate 0.001, batch size 256. The main run trains for 2000 steps (seed 344); a replication run trains for 800 steps (seed 345). Evaluation computes loss and accuracy under each cache policy over 12 evaluation batches.

A smoke test (80 steps, batch size 64, 4 evaluation batches) was run first and completed successfully before the main and replication runs.

### Hardware and Environment

Experiments ran on an NVIDIA GB10 system with CUDA 13.0, 121 GiB RAM, swap disabled. Python environment used PyTorch 2.11.0+cu130. GPU utilization stabilized at 95–96% after warmup. Available system memory remained above 118 GiB throughout; no memory pressure was observed. Swap remained disabled (`SwapTotal: 0 kB`) across all runs.

## Results

### Main Run (Seed 344, 2000 Steps)

Training converged to near-zero loss (2.26 × 10⁻⁵) and perfect accuracy (1.0) on the full-attention task.

| Total KV slots | % of full cache | Uniform policy | Uniform loss | Uniform acc | Best asymmetric policy | Asymmetric loss | Asymmetric acc | Loss reduction | Acc improvement |
|---:|---:|---|---:|---:|---|---:|---:|---:|---:|
| 128 | 25.2% | `[32,32,32,32]` | 8.366 | 0.152 | `[80,24,12,12]` | 1.199 | 0.838 | −7.167 | +0.686 |
| 192 | 37.8% | `[48,48,48,48]` | 9.198 | 0.117 | `[96,48,24,24]` | 1.180 | 0.843 | −8.018 | +0.726 |
| 256 | 50.4% | `[64,64,64,64]` | 2.26 × 10⁻⁵ | 1.000 | `[112,64,40,40]` | 2.30 × 10⁻⁵ | 1.000 | saturated | saturated |

At 128 and 192 total slots, every uniform window (32 or 48 tokens per layer) is shorter than the 64-token copy distance. No layer can bridge the dependency, and accuracy collapses to near-random levels. The early-heavy asymmetric policies allocate 80 or 96 slots to layer 0, crossing the dependency threshold in at least one layer and recovering most of the task performance.

At 256 total slots, the uniform `[64,64,64,64]` policy already spans the copy distance in every layer. Both uniform and asymmetric policies achieve full accuracy, confirming that the experimental control (equal total budget) is functioning correctly. The saturation at this budget level is an expected negative result that validates the experimental design: once the uniform budget is sufficient, asymmetric reallocation provides no additional benefit.

### Replication Run (Seed 345, 800 Steps)

Training again converged (loss 1.05 × 10⁻⁴, accuracy 1.0). The core finding replicated: asymmetric budgets substantially outperform uniform budgets at tight totals.

| Total KV slots | % of full cache | Uniform policy | Uniform loss | Uniform acc | Best asymmetric policy | Asymmetric loss | Asymmetric acc | Loss reduction | Acc improvement |
|---:|---:|---|---:|---:|---|---:|---:|---:|---:|
| 128 | 25.2% | `[32,32,32,32]` | 7.336 | 0.151 | `[8,104,8,8]` | 1.097 | 0.829 | −6.240 | +0.679 |
| 192 | 37.8% | `[48,48,48,48]` | 8.011 | 0.122 | `[32,64,64,32]` | 0.457 | 0.924 | −7.555 | +0.802 |
| 256 | 50.4% | `[64,64,64,64]` | 1.14 × 10⁻⁴ | 1.000 | `[112,64,40,40]` | 1.09 × 10⁻⁴ | 1.000 | saturated | saturated |

The winning asymmetric shape differed across seeds: seed 344 favored early-heavy allocations (`[80,24,12,12]`, `[96,48,24,24]`), while seed 345 favored a middle-heavy or single-long-layer pattern (`[8,104,8,8]`, `[32,64,64,32]`). This variation is a substantive finding: it indicates that the supported mechanism is the existence of a beneficial asymmetric allocation for a given trained model, not a single universal layer schedule that transfers across initializations.

### Throughput

Evaluation throughput was approximately 0.70M scored tokens per second across cache policies. Because evaluation uses dense masked attention rather than a patched decode kernel, throughput comparisons are not the primary claim of this work and should not be interpreted as decode-speed benchmarks.

## Limitations

1. **Synthetic task.** Delayed copy is a clean probe for long-range retrieval but does not represent the distribution of dependencies in natural language or code. Whether asymmetric budgets help on real pretrained models and real tasks remains untested.

2. **Teacher-forced evaluation, not decode-time KV eviction.** Sliding-window masks in dense teacher-forced mode approximate per-layer KV budgets but differ from actual autoregressive generation with a KV cache that permanently discards evicted entries. Error accumulation under true decode-time eviction may change the relative rankings of different budget allocations.

3. **Toy model scale.** A 4-layer, 128-dimension model with 4 heads does not capture the layer-wise attention diversity of production-scale transformers. The magnitude and shape of the asymmetric advantage may differ substantially at scale.

4. **No adaptive budget selection.** The experiment evaluates a fixed set of candidate allocations. It does not address how to discover the best asymmetric budget for a given model and task, which is the practical deployment question.

5. **Optimal shape is seed-dependent.** The best-performing asymmetric configuration varied across the two seeds tested. With only two seeds, we cannot characterize the distribution of optimal shapes. The result supports asymmetric budget search as a mechanism, not any particular fixed schedule.

6. **No comparison to existing layer-wise methods.** The experiment does not benchmark against PyramidKV, SqueezeAttention, or LAVa on the same task. The contribution is a controlled existence proof, not a competitive evaluation.

7. **Claim audit status.** The structured claim ledger for this artifact was generated in an empty state (`audit_status: blocked_empty_claims`) and no structured claims were extracted for formal audit. The results reported here are drawn directly from the run notes and decision JSON rather than from a formally audited claim chain. Readers should weigh the evidence accordingly.

## Reproducibility Checklist

- **Code available:** `scripts/layer_asymmetric_cache_budget.py` in project directory `<control-plane-projects>/source-record-redacted`.
- **Random seeds reported:** Main run seed 344; replication seed 345.
- **Hyperparameters specified:** `d_model=128`, 4 layers, 4 heads, sequence length 128, prefix length 64, vocabulary size 8, learning rate 0.001, batch size 256, training steps 2000 (main) and 800 (replication), evaluation batches 12.
- **Hardware specified:** NVIDIA GB10, CUDA 13.0, 121 GiB RAM, swap disabled, PyTorch 2.11.0+cu130.
- **Raw results available:** `artifacts/layer_cache_v8_s2000/results.csv`, `artifacts/layer_cache_v8_s800_seed345/results.csv`, and corresponding `results.json` files.
- **Summary metrics available:** `artifacts/layer_cache_metrics_summary.json`.
- **System probe log:** `.omx/system_probe.log`.
- **Run logs:** `artifacts/logs/smoke_20260429T161908Z.log`, `artifacts/logs/main_v8_s2000_20260429T161933Z.log`, `artifacts/logs/replicate_v8_s800_seed345_20260429T162206Z.log`, `artifacts/logs/summary_20260429T162840Z.log`.
- **Smoke test:** Ran 80 steps with batch size 64 and 4 eval batches before main runs; completed successfully.
- **Memory telemetry:** Available system memory logged before and during training (~118.96 GiB before, ~118.18 GiB near completion); no memory pressure observed.

## Conclusion

In a controlled 4-layer transformer delayed-copy experiment, allocating a fixed total KV-cache budget asymmetrically across layers substantially outperforms uniform per-layer allocation when the budget is tight relative to the task's dependency length. At 25.2% and 37.8% of full cache, asymmetric budgets recovered 0.68–0.80 absolute accuracy over uniform baselines that collapsed to near-random performance. The advantage disappears once the uniform budget is large enough to span the dependency in every layer, consistent with the expected control behavior and confirming that the benefit is specifically tied to budget scarcity relative to dependency distance.

The optimal asymmetric shape varied across random seeds, indicating that the practical mechanism is asymmetric budget search or adaptation rather than a single fixed schedule. This aligns with the motivation behind prior layer-wise cache methods and provides a concrete mechanistic demonstration of why such methods can matter.

These results are a bounded, positive finding under controlled conditions. They do not establish that layer-asymmetric budgets will help in production inference with pretrained models, where attention patterns, task distributions, and decode-time error accumulation differ substantially from this setting. The natural next step is to implement per-layer KV-cache limits in a real inference runtime and evaluate on long-context benchmarks against existing layer-wise compression baselines.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `scripts/layer_asymmetric_cache_budget.py` |
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| System probe log | `.omx/system_probe.log` |
| Smoke test results | `artifacts/layer_cache_smoke/results.json` |
| Main run results (CSV) | `artifacts/layer_cache_v8_s2000/results.csv` |
| Main run results (JSON) | `artifacts/layer_cache_v8_s2000/results.json` |
| Replication results (CSV) | `artifacts/layer_cache_v8_s800_seed345/results.csv` |
| Replication results (JSON) | `artifacts/layer_cache_v8_s800_seed345/results.json` |
| Summary metrics | `artifacts/layer_cache_metrics_summary.json` |
| Smoke run log | `artifacts/logs/smoke_20260429T161908Z.log` |
| Main run log | `artifacts/logs/main_v8_s2000_20260429T161933Z.log` |
| Replication run log | `artifacts/logs/replicate_v8_s800_seed345_20260429T162206Z.log` |
| Summary extraction log | `artifacts/logs/summary_20260429T162840Z.log` |
| Claim ledger | `papers/source-record-redacted-20260429T161618364220+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T161618364220+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T161618364220+0000/paper_manifest.json` |
