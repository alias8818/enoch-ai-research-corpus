# Joint Saliency-Guided Budget Allocation Across Attention Heads and MLP Channels

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, evidence bundles, claim ledgers, decision JSON, and benchmark results). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact.

---

## Abstract

We investigate whether jointly allocating a structured pruning budget across attention heads and MLP channels—guided by first-order activation-gradient saliency—yields better loss retention than independent per-subsystem budget splitting. A tiny decoder-only Transformer is trained on a synthetic autoregressive recurrence task, and three pruning methods are compared at target budgets of 10–40%: joint saliency pruning, independent saliency pruning, and joint magnitude pruning. Across three random seeds, joint saliency achieves the lowest mean loss increase at the 30% budget (mean Δloss = 0.036 vs. 0.064 for independent saliency), but degrades substantially at 40% (mean Δloss = 0.180 vs. 0.121 for independent saliency), indicating that the unconstrained joint allocator over-prunes MLP channels at higher budgets. At 10% and 20% budgets, no method demonstrates a clear advantage. Results are limited to a synthetic task on a small randomly initialized model with no fine-tuning recovery and a parameter-count cost proxy rather than measured latency. The evidence is mixed: joint allocation is promising at moderate budgets but requires per-subsystem constraints to prevent pathological allocation at higher pruning fractions.

## Introduction

Structured pruning of Transformer models typically treats attention heads and MLP channels as separate subsystems, each assigned an independent pruning budget. This independence assumption is convenient but potentially suboptimal: the relative importance of attention versus MLP computation may vary across layers and tasks, and a fixed per-subsystem budget cannot reallocate capacity from low-saliency heads to high-saliency MLP channels or vice versa.

Joint budget allocation across subsystems offers a simple alternative: rank all prunable units—heads and channels together—by a shared saliency criterion, then prune the lowest-saliency units until a global parameter budget is met. If attention heads and MLP channels compete for the same capacity, joint allocation should outperform independent splitting by directing the budget toward whichever subsystem benefits more from retained capacity.

This paper presents a controlled but small-scale evaluation of this hypothesis. We compute first-order saliency (activation × gradient magnitude) for attention heads and MLP intermediate channels in a tiny decoder-only Transformer trained on a synthetic autoregressive recurrence. We compare three pruning strategies—joint saliency, independent saliency, and joint magnitude—at four target budgets. The results reveal a nuanced picture: joint saliency is the best method at a 30% budget but becomes the worst at 40%, suggesting that unconstrained joint allocation is unstable without regularization or per-subsystem guardrails.

## Method

### Model and Task

A tiny decoder-only Transformer is trained from random initialization on a synthetic autoregressive recurrence task. The model is trained for 800 gradient steps. Baseline performance (seed 7) after training is loss 2.5837 and token accuracy 0.0930. The low absolute accuracy is expected given the small model and synthetic task; the metric of interest is the *change* in loss and accuracy after pruning relative to each seed's unpruned baseline.

### Saliency Computation

First-order unit saliency is computed as the product of activation magnitude and gradient magnitude for each prunable unit:

- **Attention head saliency:** aggregated over the head's projection dimensions.
- **MLP channel saliency:** aggregated over the intermediate (up-projection) channel dimension.

This yields a scalar importance score per attention head and per MLP intermediate channel, enabling direct comparison across subsystem types.

### Pruning Methods

Three methods are evaluated at target pruning budgets of 10%, 20%, 30%, and 40% of total prunable parameters:

1. **Joint saliency (`joint_saliency`):** All attention heads and MLP channels are ranked together by saliency. Units are pruned from lowest saliency upward until the global parameter budget is met.

2. **Independent saliency (`independent_saliency`):** Attention heads and MLP channels are ranked separately within their subsystems. Each subsystem is pruned independently to meet its proportional share of the target budget.

3. **Joint magnitude (`magnitude_joint`):** Same as joint saliency but using weight magnitude (L2 norm) instead of activation-gradient saliency as the ranking criterion.

### Cost Model

The pruning budget is defined as a fraction of total prunable parameters (attention head parameters + MLP intermediate channel parameters). This is a parameter-count proxy, not a measured latency or throughput cost. Actual cost fractions achieved may differ from targets because attention heads are coarse-grained units: pruning one head removes a fixed block of parameters, making it impossible to hit arbitrary budget targets precisely. This asymmetry particularly affects the independent baseline at low budgets, where the actual cost fraction can undershoot the target.

### Experimental Protocol

Each method–budget combination is evaluated over three random seeds (7, 8, 9). Pruning is applied as a one-shot mask after training with no subsequent fine-tuning or recovery. The primary metrics are Δloss and Δaccuracy relative to the unpruned baseline for each seed. All experiments use CPU-only PyTorch on a GB10 host with approximately 122 GB available RAM and no GPU acceleration.

## Results

### Aggregate Outcomes

Table 1 summarizes mean Δloss, median Δloss, mean Δaccuracy, mean actual cost fraction, and mean units pruned across three seeds for each method–budget combination.

**Table 1: Aggregate pruning results (n = 3 seeds per cell).**

| Budget | Method | Mean Δloss | Median Δloss | Mean Δacc | Actual cost frac. | Heads pruned | MLP ch. pruned |
|--------|--------|-----------|-------------|-----------|-------------------|-------------|----------------|
| 10% | independent_saliency | −0.0002 | −0.0001 | −0.0003 | 0.049 | 0.0 | 25 |
| 10% | joint_saliency | 0.0017 | 0.0004 | −0.0005 | 0.100 | 0.0 | 51 |
| 10% | magnitude_joint | 0.0010 | 0.0018 | −0.0003 | 0.100 | 0.0 | 51 |
| 20% | independent_saliency | 0.0127 | 0.0166 | −0.0011 | 0.162 | 1.0 | 51 |
| 20% | joint_saliency | 0.0128 | 0.0188 | −0.0003 | 0.199 | 0.3 | 91 |
| 20% | magnitude_joint | 0.0079 | 0.0097 | −0.0010 | 0.199 | 0.0 | 102 |
| 30% | independent_saliency | 0.0642 | 0.0392 | −0.0008 | 0.273 | 2.0 | 76 |
| 30% | joint_saliency | 0.0356 | 0.0324 | −0.0009 | 0.299 | 0.7 | 132 |
| 30% | magnitude_joint | 0.0462 | 0.0381 | −0.0015 | 0.299 | 0.3 | 142 |
| 40% | independent_saliency | 0.1209 | 0.0964 | −0.0019 | 0.387 | 3.0 | 102 |
| 40% | joint_saliency | 0.1801 | 0.1361 | −0.0086 | 0.398 | 1.0 | 172 |
| 40% | magnitude_joint | 0.1830 | 0.0686 | −0.0038 | 0.398 | 0.7 | 183 |

### Analysis

**Low budgets (10–20%):** All three methods produce small loss increases. At 10%, independent saliency achieves a negligible mean Δloss of −0.0002 (effectively no degradation), while both joint methods incur small positive Δloss values (0.0017 and 0.0010). However, the actual cost fractions differ substantially: independent saliency achieves only 4.9% actual cost reduction at the 10% target due to the coarse granularity of attention heads, whereas both joint methods achieve approximately 10%. This confound makes strict comparison at 10% difficult. At 20%, magnitude_joint yields the lowest mean Δloss (0.0079), slightly better than both saliency methods (≈0.013). Joint saliency does not demonstrate an advantage at these budgets.

**Moderate budget (30%):** Joint saliency achieves the best mean Δloss of 0.0356, compared to 0.0642 for independent saliency and 0.0462 for magnitude_joint. This represents a 44% reduction in mean loss degradation relative to independent saliency. The joint allocator prunes fewer attention heads (0.7 vs. 2.0) but more MLP channels (132 vs. 76), suggesting that the saliency signal identifies MLP channels as lower-priority at this budget level and that retaining more heads is beneficial.

**High budget (40%):** The advantage reverses sharply. Joint saliency yields the worst mean Δloss (0.1801), substantially worse than independent saliency (0.1209). The joint allocator prunes 172 MLP channels on average (vs. 102 for independent), indicating over-pruning of the MLP subsystem. The accuracy degradation is also largest for joint saliency at this budget (−0.0086 vs. −0.0019). The unconstrained allocator exhausts MLP capacity before pruning enough attention heads, producing a pathological allocation.

**Magnitude vs. saliency:** Joint magnitude pruning is generally intermediate between joint saliency and independent saliency at 20–30%, except at 40% where it ties joint saliency in mean Δloss (0.183 vs. 0.180) but has a much lower median Δloss (0.069 vs. 0.136), suggesting higher variance across seeds. The divergence between mean and median for magnitude_joint at 40% indicates that at least one seed experienced substantially worse degradation than the others.

### Allocation Patterns

The joint allocator consistently favors pruning MLP channels over attention heads across all budgets. At 30%, it prunes 0.7 heads and 132 channels; at 40%, 1.0 head and 172 channels. Independent saliency, by contrast, prunes more heads (2–3) and fewer channels (76–102). The joint allocator's reluctance to prune heads is rational at 30%—where heads appear more salient—but becomes harmful at 40% when the MLP is over-depleted. This pattern suggests that attention head saliency scores are systematically higher than MLP channel saliency scores in this model, causing the joint ranker to deprioritize head pruning even when doing so would be beneficial at higher budgets.

## Limitations

1. **Synthetic task and tiny model.** The experiment uses a small randomly initialized Transformer on a synthetic autoregressive recurrence. No real pretrained language model or natural-language validation set is involved. The saliency landscape and optimal allocation patterns may differ substantially for large pretrained models where attention and MLP roles are more differentiated across layers.

2. **No fine-tuning or recovery.** Pruning is applied as a one-shot mask with no subsequent fine-tuning. In practice, recovery fine-tuning can substantially mitigate pruning degradation, and the relative ranking of methods may change with recovery.

3. **Parameter-count cost proxy.** The budget is defined by parameter fraction, not by measured latency or throughput. Attention heads and MLP channels have different computational profiles (e.g., attention involves sequence-length-dependent computation), so parameter-count budgets may not reflect actual runtime cost savings.

4. **Coarse-grained attention heads.** Attention heads are indivisible pruning units, causing the independent baseline to undershoot target budgets at low fractions (actual cost 4.9% at 10% target). This asymmetry makes strict method comparison at low budgets difficult and introduces a systematic bias whereby independent saliency prunes less than intended at low budgets.

5. **Small seed count and high variance.** Only three seeds are used. The median Δloss values sometimes diverge substantially from means (e.g., magnitude_joint at 40%: mean 0.183, median 0.069), indicating high variance that three seeds cannot adequately characterize. Confidence intervals are not reported and would be wide.

6. **No per-subsystem constraints in joint allocation.** The joint allocator has no guardrails preventing it from pruning all MLP channels while retaining all heads. This lack of constraint is the likely cause of the 40% budget failure mode. A constrained variant was not tested.

7. **Toy simulation scope.** These results constitute toy simulation evidence on a tiny model. They do not constitute production validation, CUDA-level benchmarking, or validation on pretrained language models. Generalization to other architectures, tasks, and scales is not established.

## Reproducibility Checklist

- **Code available:** `scripts/joint_pruner_experiment.py` (experiment implementation), `scripts/summarize_results.py` (aggregation).
- **Seeds reported:** 7, 8, 9.
- **Training steps:** 800 (main experiments), 20 (smoke test).
- **Hardware:** CPU-only PyTorch on a GB10 host; ~122 GB RAM available; swap disabled; no GPU acceleration used. NVIDIA GB10 was present but idle; no CUDA memory accounting was available for the runs.
- **Dependencies:** Python 3, PyTorch (CPU wheel from `https://download.pytorch.org/whl/cpu`).
- **Result files:** `artifacts/main_results.json`, `artifacts/main_seed8.json`, `artifacts/main_seed9.json`, `artifacts/aggregate_results.json`, `artifacts/smoke_results.json`.
- **Logs:** `logs/smoke.log`, `logs/main_800.log`, `logs/main_seed8.log`, `logs/main_seed9.log`.
- **Aggregate table:** `artifacts/aggregate_table.md`.
- **Decision record:** `.omx/project_decision.json`.
- **Claim ledger status:** `blocked_empty_claims` — no structured claims were extracted; this artifact has not passed strict claim/evidence audit.

## Conclusion

Joint saliency-guided allocation of a pruning budget across attention heads and MLP channels shows a measurable advantage over independent per-subsystem budget splitting at a 30% target pruning budget on a tiny synthetic Transformer, reducing mean loss degradation from 0.064 to 0.036. However, the same unconstrained joint allocator fails at 40%, producing a mean loss degradation of 0.180 versus 0.121 for independent splitting, due to pathological over-pruning of MLP channels. At 10% and 20% budgets, no method demonstrates a clear advantage, though confounds from coarse-grained head units complicate comparison at 10%.

These results establish that joint allocation is not uniformly superior to independent splitting. The benefit depends on the budget level and the presence of allocation constraints. A practical joint pruner would likely need per-subsystem minimum-capacity constraints or a regularized allocation objective to prevent the MLP depletion observed at high budgets.

The evidence is sufficient to warrant further investigation on pretrained models with real validation data, measured latency, and recovery fine-tuning, but is not sufficient to claim that joint allocation is generally preferable. The mixed results at different budget levels underscore the importance of evaluating pruning methods across a range of sparsity targets rather than at a single operating point. The project decision record classifies this direction as "promising_with_caveats," with the specific recommendation that continuation should involve a constrained joint allocator evaluated on a pretrained small transformer using a real language-model validation set and measured latency/throughput.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Experiment script | `scripts/joint_pruner_experiment.py` |
| Aggregation script | `scripts/summarize_results.py` |
| Smoke test results | `artifacts/smoke_results.json` |
| Seed 7 results | `artifacts/main_results.json` |
| Seed 8 results | `artifacts/main_seed8.json` |
| Seed 9 results | `artifacts/main_seed9.json` |
| Aggregate results | `artifacts/aggregate_results.json` |
| Aggregate table | `artifacts/aggregate_table.md` |
| Research report | `artifacts/research_report.md` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260430T014048484076+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T014048484076+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T014048484076+0000/paper_manifest.json` |
| Smoke log | `logs/smoke.log` |
| Main log (seed 7) | `logs/main_800.log` |
| Main log (seed 8) | `logs/main_seed8.log` |
| Main log (seed 9) | `logs/main_seed9.log` |
