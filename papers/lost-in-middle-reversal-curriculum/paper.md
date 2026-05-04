# Lost-in-Middle Reversal Curriculum: Position-Targeted Training Shifts Retrieval Accuracy in Synthetic Key-Value Retrieval

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, evaluation logs, claim ledger). The operator who released the artifacts claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Large language models exhibit a "lost-in-the-middle" effect, retrieving information from the edges of a context more reliably than from its interior. We investigate whether a hard-to-easy reversal curriculum—training first on middle-position targets and expanding outward—can reduce this retrieval trough on a controlled synthetic key-value task. Four curricula were compared: uniform sampling, a conventional edge-first (easy-to-hard) curriculum, the proposed middle-reversal curriculum, and a static middle-biased control. In high-sample evaluation (17,408 examples per four-position bin), the middle-reversal curriculum improved middle-bin accuracy by +1.78 percentage points over uniform training (0.154 vs. 0.136, *z* ≈ 4.72). However, overall accuracy was essentially unchanged (+0.07 pp), and edge accuracy decreased by −1.48 pp (*z* ≈ −4.03). A static middle-biased control confirmed extreme position-dependent specialization (middle accuracy 0.260, edge accuracy 0.040) at the cost of overall accuracy (0.119). These results establish that position-targeted curricula can reshape the positional retrieval profile in a synthetic setting, but the effect is a redistribution rather than a net improvement. The tradeoff between middle and edge accuracy remains unresolved without additional balancing mechanisms.

## Introduction

The "lost-in-the-middle" phenomenon describes the empirical observation that language models retrieve information from the beginning and end of a context window more reliably than from its interior. This positional bias is consequential for retrieval-augmented generation and long-context applications where relevant information may appear anywhere in the input.

Curriculum learning—ordering training examples from easy to hard—has been studied extensively, but its interaction with positional retrieval bias is less explored. A natural easy-to-hard curriculum for positional retrieval would start with edge positions (where models already perform better) and anneal toward uniform coverage. The question motivating this work is whether the reverse—a hard-to-easy curriculum that prioritizes middle positions first—can counteract the lost-in-the-middle trough.

We study this question in a minimal synthetic setting: a key-value retrieval task where the target position is directly controllable, allowing precise measurement of positional accuracy without confounds from semantic variation. We compare four position-sampling strategies and evaluate their effect on per-position retrieval accuracy.

The central finding is that the reversal curriculum does shift accuracy toward the middle, but this shift comes at the expense of edge accuracy rather than representing a net improvement in retrieval capability. This is a narrower result than a cure for the lost-in-the-middle effect, but it establishes that position sampling during training is a functional lever on the retrieval profile.

## Method

### Task Definition

The input sequence is structured as `[CLS, query_key, key_0, value_0, key_1, value_1, ..., key_N, value_N]`. The model must predict the value paired with `query_key`. The position of the target key-value pair is a controlled variable. Accuracy is the fraction of correct value predictions.

This synthetic formulation eliminates semantic variation, attention-pattern diversity, and real-world noise, providing a controlled testbed for measuring positional retrieval bias. The tradeoff is reduced external validity, which we discuss in Limitations.

### Position Bins

For a sequence with 16 key-value pairs, positions are grouped into three regions:

- **Edge**: the four positions at each end of the sequence (positions 0–3 and 12–15)
- **Near-edge**: the four positions adjacent to the edge region on each side
- **Middle**: the four central positions

Each bin contains 8 positions total (4 from each half of the sequence), and each position is evaluated with 4,352 examples, yielding 17,408 examples per bin in the high-sample evaluation.

### Curricula

Four position-sampling strategies were tested:

1. **Uniform**: Target position sampled uniformly at random from all positions. Baseline condition.

2. **Edge curriculum (easy-to-hard)**: Training begins with edge-biased position sampling and anneals toward uniform sampling over the course of training. This represents a conventional curriculum that starts with easier (edge) examples.

3. **Middle reversal (hard-to-easy)**: Training begins with middle-biased position sampling and expands outward with uniform exploration. This is the proposed reversal curriculum, exposing the model to the hardest positions first.

4. **Middle static**: Always middle-biased sampling. Included as a sanity check to confirm that position sampling can shape the retrieval profile and to measure the extent of specialization and forgetting.

### Training Configuration

The primary experiment used the following configuration:

- **Sequence parameters**: 16 key-value pairs, 64 unique keys, 32 unique values
- **Training**: 1,800 steps, batch size 256, learning rate 0.001
- **Evaluation**: 256 evaluation batches (4,352 examples per position; 17,408 examples per four-position bin)
- **Framework**: PyTorch 2.11.0 (CPU-only build), running on CPU despite GPU hardware detection
- **Memory**: Peak RSS 549,996 KB; swap disabled (confirmed 0 swaps)

An earlier pilot with harder parameters (900 steps, different pair/key/val counts) was also conducted and is referenced for qualitative consistency.

### Statistical Method

Differences between curricula are assessed via normal-approximation two-proportion z-tests, using the per-bin sample counts. This is appropriate given the large sample sizes (17,408 per bin) but assumes independence across evaluation examples. Crucially, these tests reflect evaluation-sample noise only; they do not account for variance across training runs (see Limitations).

## Results

### Primary Evaluation

| Curriculum | Overall | Edge | Near-edge | Middle | Min position | Argmin |
|---|---:|---:|---:|---:|---:|---:|
| Uniform | 0.1391 | 0.1422 | 0.1403 | 0.1360 | 0.1234 | 6 |
| Edge curriculum | 0.1377 | 0.1372 | 0.1383 | 0.1406 | 0.1314 | 2 |
| Middle reversal | 0.1398 | 0.1274 | 0.1308 | 0.1538 | 0.1119 | 0 |
| Middle static | 0.1190 | 0.0402 | 0.0630 | 0.2601 | 0.0354 | 0 |

### Middle-Bin Accuracy

The middle-reversal curriculum achieved a middle-bin accuracy of 0.1538 compared to 0.1360 for uniform training, an absolute improvement of +0.0178 (1.78 percentage points). Under normal approximation, this difference yields *z* ≈ 4.72, indicating that the middle-bin improvement is unlikely to be due to evaluation-sample noise alone.

The edge curriculum also showed a small middle-bin improvement over uniform (+0.0047), but this was substantially smaller than the reversal curriculum's gain.

### Edge-Bin Accuracy

The middle-reversal curriculum reduced edge-bin accuracy to 0.1274 from 0.1422 (uniform), a decrease of −0.0148 (*z* ≈ −4.03). This indicates that the middle-bin gain came at the expense of edge performance, not from an overall improvement in retrieval capability.

### Overall Accuracy

Overall accuracy was nearly identical across the three non-degenerate curricula: 0.1391 (uniform), 0.1377 (edge), 0.1398 (middle reversal). The middle-reversal curriculum's overall advantage of +0.0007 is negligible and not practically meaningful. The edge curriculum's slight overall deficit of −0.0013 is similarly negligible.

### Static Middle-Biased Control

The middle-static curriculum produced extreme specialization: middle-bin accuracy of 0.2601 (nearly double the uniform baseline) but edge accuracy of only 0.0402 (a collapse to near-chance levels for some positions). Overall accuracy dropped to 0.1190. This confirms that position sampling is a strong lever on the retrieval profile but demonstrates that unidirectional bias produces severe tradeoffs and overall degradation.

### Earlier Pilot (Harder Setting)

An earlier pilot with different parameters (900 steps, different pair/key/val counts) showed the same qualitative pattern at lower absolute accuracy levels: middle-reversal middle accuracy 0.0638 vs. uniform 0.0521; middle-static middle 0.1465 with edge collapse to 0.0072. The consistency of the pattern across two configurations lends qualitative support to the finding, though the pilot used fewer evaluation samples and different hyperparameters, so quantitative comparison is not meaningful.

## Limitations

1. **Synthetic task only.** The key-value retrieval task eliminates semantic variation, attention-pattern diversity, and real-world noise. Whether these curriculum effects transfer to natural-language retrieval tasks is unknown. The synthetic setting may overestimate the controllability of positional bias relative to real-world conditions.

2. **Single training seed.** All results come from a single training run per curriculum. Random initialization, data ordering, and optimization stochasticity could affect the magnitude and possibly the direction of effects. The z-tests reflect evaluation-sample noise only, not training-run variance. Multi-seed replication is needed before drawing firm conclusions about effect sizes.

3. **Small model, CPU-only training.** The model was trained on CPU with a CPU-only PyTorch build. The scale of the model and the training regime are far from production settings. GPU hardware was detected but not utilized. Whether the observed effects persist at larger scale is unknown.

4. **Redistribution, not improvement.** The primary finding is that the reversal curriculum redistributes accuracy from edges to middle rather than improving overall retrieval. This is a narrower result than a cure for the lost-in-the-middle effect. The practical value of a pure redistribution depends on whether middle accuracy is disproportionately important in a given application.

5. **No adaptive balancing.** The curricula tested use fixed annealing schedules. An adaptive approach that equalizes per-position validation error might achieve middle improvement without edge degradation, but this was not tested.

6. **Short sequences.** With only 16 key-value pairs, the "middle" of the sequence is not far from the edges. The lost-in-the-middle effect may be more pronounced and the curriculum effect may differ qualitatively at longer context lengths.

7. **No comparison to architectural interventions.** Positional bias can also be addressed through architectural changes (e.g., positional encoding modifications, attention pattern constraints). The relative efficacy of curriculum-based versus architectural approaches is not addressed.

8. **Low absolute accuracy.** All curricula achieve overall accuracy near 0.14, which is low even for a 32-way classification task. This may reflect undertraining, model capacity limitations, or task difficulty under the chosen hyperparameters. The curriculum effects are measured on top of a poorly-performing baseline, which may limit the generality of the findings.

## Reproducibility Checklist

| Item | Status |
|---|---|
| Training code available | `scripts/lost_middle_curriculum.py` |
| Evaluation code available | `scripts/eval_saved_models.py` |
| Primary metrics file | `results/easy_1800/eval_b256.json` |
| Training JSONL logs | `results/easy_1800/train_*.jsonl` |
| Console/time logs | `logs/easy_1800.console.log`, `logs/easy_1800.eval256.log` |
| Pilot metrics | `results/full_900/metrics.json` |
| Random seeds | **Not explicitly set or reported** — this is a reproducibility gap |
| Hardware | CPU-only PyTorch 2.11.0; GPU present but unused |
| Peak memory | 549,996 KB RSS; swap disabled, confirmed 0 swaps |
| Exact commands | Recorded in run notes |
| Package versions | `torch==2.11.0+cpu`, `numpy`, `psutil` |
| Evaluation sample counts | 4,352 per position; 17,408 per four-position bin |
| Number of training seeds | 1 per curriculum — insufficient for variance estimation |

## Conclusion

A hard-to-easy middle-reversal curriculum improves middle-position retrieval accuracy on a synthetic key-value task by +1.78 percentage points over uniform training, a statistically significant effect under evaluation-sample noise (*z* ≈ 4.72). However, this improvement is offset by a −1.48 percentage point decrease in edge accuracy (*z* ≈ −4.03), leaving overall accuracy essentially unchanged (+0.07 pp). The static middle-biased control confirms that position sampling is a strong lever on the retrieval profile but produces severe edge collapse and overall degradation when applied without balance.

These results support the narrow claim that middle-first reversal sampling can raise middle-position retrieval accuracy in a controlled synthetic setting. They do not support the stronger claim that this curriculum improves aggregate retrieval or resolves the edge–middle accuracy tradeoff. The effect is best characterized as a redistribution of positional accuracy rather than a net improvement.

A viable next step would be to run 3–5 seeds per curriculum with an adaptive loss or two-phase schedule that explicitly rebalances edge accuracy after middle-first training. A meaningful success criterion would be: middle accuracy significantly above uniform while overall and edge accuracy remain non-inferior within 1 percentage point. Without such balancing, the reversal curriculum alone does not resolve the lost-in-the-middle effect.

## Referenced Artifacts

| Artifact | Path / Identifier |
|---|---|
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Training script | `scripts/lost_middle_curriculum.py` |
| Evaluation script | `scripts/eval_saved_models.py` |
| Primary evaluation metrics | `results/easy_1800/eval_b256.json` |
| Training JSONL logs | `results/easy_1800/train_*.jsonl` |
| Console log (training) | `logs/easy_1800.console.log` |
| Console log (evaluation) | `logs/easy_1800.eval256.log` |
| Pilot metrics | `results/full_900/metrics.json` |
| Project metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260502T083148497803+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T083148497803+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T083148497803+0000/paper_manifest.json` |
