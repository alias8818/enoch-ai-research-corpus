# Knowledge Deletion via Targeted Fine-Tuning with Retained-Fact Rehearsal: A Controlled Synthetic Study

---

**AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, result files, and claim ledger). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact and evaluate its claims accordingly.

---

## Abstract

We investigate whether a small fine-tuning pass can selectively delete memorized facts from a neural language model while preserving non-deleted facts. Using a controlled synthetic QA task with known ground truth, we train a tiny causal Transformer to memorize 64 entity-to-code facts, then apply a deletion fine-tune that maps 16 selected facts to an abstention token (`UNKNOWN`) while rehearsing the remaining 48 retained facts on their original answers. Across three random seeds, deleted facts shift from 100% gold-answer accuracy before deletion to 100% `UNKNOWN` on seen prompt templates and a mean of 98.96% `UNKNOWN` on held-out paraphrase templates, while retained facts remain at 100% gold accuracy across all conditions. One seed (seed 2) exhibited a single held-out paraphrase failure, yielding 96.88% deletion accuracy on that partition. These results are positive within the controlled synthetic setting but are obtained on one-token facts with a tiny model; they do not demonstrate weight-level erasure, adversarial robustness, or applicability to real pretrained language models.

## Introduction

Selective removal of memorized knowledge from trained neural language models is relevant to privacy compliance, safety, and model maintenance. Prior work has proposed gradient-ascent unlearning and localized model editing, but evaluating whether deletion has genuinely occurred—rather than being superficially suppressed under tested prompts—remains a difficult verification problem.

We adopt a reductionist approach: rather than attempting deletion in a large pretrained model where ground-truth memorization is unknown, we construct a controlled synthetic environment in which every fact is known, the model's initial memorization is verified, and deletion success can be measured exactly. Specifically, we ask: *can a second fine-tuning pass, which trains deleted-fact prompts toward an abstention token while rehearsing retained facts, reliably overwrite selected memorized facts without collateral damage to non-deleted knowledge?*

This study provides a positive answer in the synthetic setting. We are explicit, however, about the substantial gap between this controlled demonstration and the requirements of practical knowledge deletion from pretrained models.

## Method

### Task Design

We construct a synthetic QA task with 64 entity-to-single-token-code mappings. Each fact can be queried through multiple prompt templates. Templates are partitioned into two sets:

- **Seen templates**: used during both the memorization phase and the deletion fine-tuning phase.
- **Held-out paraphrase templates**: used only during evaluation, not during deletion fine-tuning, to test whether deletion generalizes beyond the exact training prompts.

### Memorization Phase

A tiny causal Transformer is trained from scratch on all 64 facts using the seen templates. Training continues until the model achieves 100% gold-answer accuracy on all facts. This phase establishes a known memorization baseline.

### Deletion Fine-Tuning Phase

16 of the 64 facts are designated for deletion. The deletion fine-tune uses the same seen templates but with modified targets:

- **Deleted facts**: the target is changed from the original code to the token `UNKNOWN`.
- **Retained facts**: the target remains the original correct code. This rehearsal is intended to prevent catastrophic forgetting of non-deleted knowledge during the deletion fine-tune.

### Evaluation

We measure accuracy under four conditions post-deletion:

1. **Seen deleted-fact `UNKNOWN` accuracy**: fraction of deleted-fact seen prompts where the model outputs `UNKNOWN`.
2. **Seen retained-fact gold accuracy**: fraction of retained-fact seen prompts where the model outputs the original correct code.
3. **Held-out paraphrase deleted-fact `UNKNOWN` accuracy**: same as (1) but on held-out paraphrase templates not used during deletion fine-tuning.
4. **Held-out paraphrase retained-fact gold accuracy**: same as (2) but on held-out paraphrase templates.

Pre-deletion, we verify that the model achieves 100% gold-answer accuracy on all facts, including those designated for deletion.

### Experimental Protocol

A smoke test (16 facts, 4 deleted, seed 0) was executed first to validate the pipeline. The full experiment uses 64 facts, 16 deleted, across 3 random seeds (0, 1, 2). All runs were executed on an NVIDIA GB10 GPU with CUDA. Swap was disabled by host policy; memory was monitored via `MemAvailable` telemetry.

## Results

### Smoke Test

The smoke test (16 facts, 4 deleted, seed 0) confirmed the pipeline was functional:

| Metric | Value |
|--------|-------|
| Pre-deletion deleted-fact gold accuracy | 1.000 |
| Post-deletion seen deleted-fact `UNKNOWN` accuracy | 1.000 |
| Post-deletion seen retained-fact gold accuracy | 1.000 |

### Full Run: Seen Templates

Across all three seeds, deletion fine-tuning achieved perfect behavioral deletion on seen templates with no observed collateral damage to retained facts:

| Metric | Mean across seeds |
|--------|-------------------|
| Pre-deletion seen deleted-fact gold accuracy | 1.000 |
| Post-deletion seen deleted-fact `UNKNOWN` accuracy | 1.000 |
| Post-deletion seen retained-fact gold accuracy | 1.000 |

### Full Run: Held-Out Paraphrase Templates

Generalization to held-out paraphrase templates was near-perfect for deletion and perfect for retention:

| Metric | Mean across seeds |
|--------|-------------------|
| Post-deletion held-out paraphrase deleted-fact `UNKNOWN` accuracy | 0.9896 |
| Post-deletion held-out paraphrase retained-fact gold accuracy | 1.000 |

### Per-Seed Breakdown

| Seed | Held-out deleted `UNKNOWN` acc | Held-out retained gold acc | Memorize time (s) | Delete finetune time (s) |
|------|-------------------------------|----------------------------|-------------------|--------------------------|
| 0 | 1.0000 | 1.0000 | 2.56 | 1.91 |
| 1 | 1.0000 | 1.0000 | 3.47 | 2.90 |
| 2 | 0.9688 | 1.0000 | 2.72 | 1.94 |

Seed 2 showed a single held-out paraphrase prompt where a deleted fact was not mapped to `UNKNOWN`, yielding 96.88% accuracy on that partition. This represents one failure out of 32 held-out deleted-fact evaluations for that seed (16 facts × 2 held-out templates). This failure indicates that generalization of deletion to unseen paraphrases is not always perfect, even in this simple synthetic setting.

### Resource Usage

- Device: NVIDIA GB10 (CUDA)
- System `MemAvailable` at start: 116.67 GiB; at finish: 115.60 GiB
- Torch CUDA reserved at finish: 58.0 MiB
- GPU utilization at finish: 41%, temperature 40°C, power 17.05 W
- Swap: disabled by host policy; `MemAvailable` remained above 115 GiB throughout

## Limitations

1. **Synthetic, one-token facts.** The facts in this experiment are simple entity-to-single-token-code mappings. Real-world factual knowledge in pretrained language models is distributed across many parameters and tokens. Deletion difficulty is substantially lower in this controlled setting than it would be in a pretrained model.

2. **Behavioral deletion only.** We measure whether the model outputs `UNKNOWN` when queried; we do not verify that the original fact is irreversibly removed from the weights. The knowledge may persist in a form recoverable under different prompting strategies, probing classifiers, or weight inspection.

3. **Non-adversarial evaluation.** Held-out paraphrase templates test a limited form of generalization but are not adversarial. Resistance to jailbreak-style prompts, few-shot extraction, or trained probing classifiers is not assessed.

4. **Tiny model trained from scratch.** The model used is a small causal Transformer trained from scratch on a narrow fact set. Findings may not transfer to large pretrained models where facts are entangled with broader linguistic and world knowledge.

5. **Abstention target is a single token.** The deletion target `UNKNOWN` is a simple abstention signal. Production systems may require calibrated uncertainty estimates, nuanced refusal text, or policy-governed responses.

6. **No comparison to baselines.** This study does not compare deletion fine-tuning against alternative approaches such as gradient-ascent unlearning, localized model editing (e.g., ROME/MEMIT-style methods), or inference-time filtering. Relative efficacy and tradeoffs remain unknown.

7. **Limited paraphrase diversity.** The held-out paraphrase templates, while not seen during deletion fine-tuning, are drawn from a small template set and may not represent the diversity of prompts a real adversary could construct.

8. **No privacy or safety review.** This experiment uses synthetic facts with no connection to real personal data. Application to privacy-sensitive deletion targets would require additional review.

## Reproducibility Checklist

- **Experiment script**: `scripts/kd_finetune_experiment.py`
- **Frozen dependencies**: `artifacts/requirements_freeze.txt`
- **Command manifest**: `artifacts/commands.json`
- **Smoke test log**: `logs/smoke_20260430T055448Z.log`
- **Full run log**: `logs/full_20260430T055455Z.log`
- **Smoke summary results**: `results/kd_finetune_smoke/smoke_summary.json`
- **Full summary results**: `results/kd_finetune_full/full_summary.json`
- **Per-seed predictions**: `results/kd_finetune_full/full_seed0_rows.json`, `results/kd_finetune_full/full_seed1_rows.json`, `results/kd_finetune_full/full_seed2_rows.json`
- **Training metrics**: `results/kd_finetune_full/full_train_metrics.jsonl`
- **Hardware**: NVIDIA GB10, CUDA, swap disabled by host policy
- **Random seeds**: 0, 1, 2 (full run); 0 (smoke test)
- **Fact counts**: 64 total / 16 deleted (full run); 16 total / 4 deleted (smoke test)
- **Claim ledger status**: `blocked_empty_claims` — no structured claims were extracted for this artifact; the claim/evidence audit has not been passed

## Conclusion

In a controlled synthetic setting, deletion fine-tuning with retained-fact rehearsal successfully overwrites selected memorized facts to an abstention token while preserving non-deleted facts. Across three seeds, seen-template deletion accuracy was 100%, held-out-paraphrase deletion accuracy was 98.96% (mean), and retained-fact accuracy was 100% in all conditions. The single per-seed failure (seed 2, 96.88% held-out deletion accuracy) demonstrates that generalization to unseen paraphrases is not always perfect, even in this simple setting.

These results establish that the deletion-fine-tuning-with-rehearsal mechanism is viable at the level of a controlled synthetic smoke test for one-token factual knowledge. The distance between this demonstration and reliable knowledge deletion in real pretrained language models remains large. Scientific closure requires replication with larger pretrained models, real factual benchmarks, adversarial prompt evaluation, weight-level erasure verification, and comparison to existing unlearning and model-editing baselines.

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Experiment script | `scripts/kd_finetune_experiment.py` |
| Requirements freeze | `artifacts/requirements_freeze.txt` |
| Command manifest | `artifacts/commands.json` |
| Smoke test log | `logs/smoke_20260430T055448Z.log` |
| Full run log | `logs/full_20260430T055455Z.log` |
| Smoke summary | `results/kd_finetune_smoke/smoke_summary.json` |
| Full summary | `results/kd_finetune_full/full_summary.json` |
| Seed 0 predictions | `results/kd_finetune_full/full_seed0_rows.json` |
| Seed 1 predictions | `results/kd_finetune_full/full_seed1_rows.json` |
| Seed 2 predictions | `results/kd_finetune_full/full_seed2_rows.json` |
| Training metrics | `results/kd_finetune_full/full_train_metrics.jsonl` |
| Claim ledger | `papers/source-record-redacted-20260430T055148404374+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T055148404374+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T055148404374+0000/paper_manifest.json` |
