# Speculation-Friendly LM Head Tuning: A Controlled Proxy Study

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metrics, and result files). The operator who released the artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

Speculative decoding accelerates autoregressive inference by using a cheaper draft model to propose tokens that a target model verifies in parallel. The token-level acceptance probability depends on the distributional overlap between draft and target. We investigate whether tuning only the target model's output projection (LM head)—while freezing the target's representation body—can increase this overlap without degrading next-token likelihood. In a controlled character-level proxy experiment on Tiny Shakespeare with frozen sparse context features and a fixed 1-gram draft model, we add a draft-alignment term $\lambda \cdot D_{\mathrm{KL}}(q_{\text{draft}} \| p_{\text{target}})$ to the standard cross-entropy objective. Across three random seeds, increasing $\lambda$ from 0 to 0.5 raises the mean token-level acceptance probability $\alpha$ from 0.699 to 0.762 (+9.1% relative) while slightly improving heldout negative log-likelihood. The IID $\gamma{=}4$ tokens-per-verification proxy increases from 2.005 to 2.462 (+22.8% relative). These results are stable across seeds but arise from a character-level frozen-feature proxy, not a transformer-scale finetune, and exclude wall-clock throughput measurements. The findings suggest head-only distribution shaping is feasible in principle; end-to-end validation on real transformer architectures remains necessary.

## 1 Introduction

Speculative decoding reduces the latency of autoregressive inference by having a small draft model propose candidate tokens that a larger target model verifies in a single forward pass. The efficiency gain depends critically on the token-level acceptance probability:

$$\alpha(\mathbf{c}) = \sum_{t} \min\bigl(p_{\text{target}}(t \mid \mathbf{c}),\; q_{\text{draft}}(t \mid \mathbf{c})\bigr)$$

where $\mathbf{c}$ is the context. Higher $\alpha$ yields more accepted tokens per target verification step, improving throughput subject to draft overhead and hardware constraints.

Prior work has explored training draft models to better match a fixed target distribution. A complementary question—addressed here—is whether the *target* model's distribution can be made more speculation-friendly by modifying only its LM head, without retraining the representation body. This is attractive because head-only tuning is comparatively cheap, preserves the target's representations for downstream use, and could be applied as a post-hoc adaptation layer.

The core tension is that pulling the target toward the draft may distort the target's distribution and harm its next-token prediction quality. We test whether a modest alignment term can improve acceptance without such regression.

Because full transformer finetuning is expensive and introduces many confounds, we first test the idea in a controlled proxy setting: a character-level model with frozen sparse features, a single trainable output matrix, and a fixed 1-gram draft. This isolates the question of whether head-only distribution shaping is *feasible in principle* before investing in transformer-scale experiments.

## 2 Method

### 2.1 Problem Formulation

Given a frozen feature extractor $\phi(\mathbf{c})$ mapping context $\mathbf{c}$ to a fixed representation, the target model's distribution is:

$$p_{\text{target}}(t \mid \mathbf{c}) = \text{softmax}\bigl(\mathbf{W} \cdot \phi(\mathbf{c})\bigr)$$

where $\mathbf{W}$ is the only trainable parameter. The draft model $q_{\text{draft}}$ is fixed throughout.

The standard training objective is cross-entropy:

$$\mathcal{L}_{\text{CE}} = -\mathbb{E}_{\mathbf{c}}\left[\log p_{\text{target}}(t^* \mid \mathbf{c})\right]$$

We add a draft-alignment term that pulls the target distribution toward the draft where possible:

$$\mathcal{L}(\lambda) = \mathcal{L}_{\text{CE}} + \lambda \cdot D_{\mathrm{KL}}\bigl(q_{\text{draft}} \| p_{\text{target}}\bigr)$$

The KL divergence $D_{\mathrm{KL}}(q \| p)$ is minimized when $p$ assigns probability wherever $q$ does, which directly increases $\min(p, q)$ and thus $\alpha$. The $\lambda$ parameter controls the strength of alignment. Note that this KL direction ($q$ reference, $p$ approximating) penalizes $p$ for assigning zero probability where $q$ is positive, encouraging coverage of the draft's support.

### 2.2 Experimental Setup

**Dataset.** Tiny Shakespeare (Karpathy char-rnn), a character-level text corpus. This is a toy dataset chosen for fast iteration, not for representativeness of production workloads.

**Frozen target body (proxy).** Fixed sparse character-context features: decayed lag one-hot encodings plus exact recent-bigram features. These features are hand-specified and frozen; they are not learned.

**Tunable target component.** Output projection matrix $\mathbf{W}$ only, trained via the combined objective above.

**Draft model.** A fixed 1-gram character model that conditions only on the immediately preceding character. This is deliberately weak to create a substantial distributional gap between draft and target.

**Evaluation metrics.**

1. **Heldout target NLL**: negative log-likelihood on heldout data, measuring next-character prediction quality.
2. **Token-level acceptance probability** $\alpha = \sum_t \min(p_{\text{target}}(t \mid \mathbf{c}), q_{\text{draft}}(t \mid \mathbf{c}))$, averaged over heldout contexts.
3. **$\gamma{=}4$ tokens-per-verification proxy**: an IID approximation of expected accepted tokens per target verification step assuming 4 draft tokens are proposed, computed from $\alpha$ alone. This proxy *excludes* draft runtime cost and target batching/kernel effects.

**Hyperparameters and seeds.** We sweep $\lambda \in \{0.0, 0.05, 0.10, 0.20, 0.50\}$ and run three seeds (default, 11, 23) per value.

**Resource posture.** All runs executed on a local machine with approximately 116 GiB available RAM. Peak RSS was approximately 266 MB for smoke tests and approximately 2.10 GB for full runs. Swap was intentionally disabled. No major page faults were observed in primary logs.

## 3 Results

### 3.1 Aggregate Results

Table 1 reports mean and standard deviation across three seeds for each $\lambda$ value.

**Table 1.** Aggregate results over 3 seeds.

| $\lambda$ | $\alpha$ mean | $\alpha$ sd | NLL mean | NLL sd | $\gamma{=}4$ proxy | $\Delta\alpha$ | $\Delta$NLL |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 0.698806 | 0.000261 | 2.404159 | 0.000157 | 2.005315 | 0.000000 | 0.000000 |
| 0.05 | 0.706681 | 0.000243 | 2.401395 | 0.000151 | 2.057791 | +0.007875 | −0.002764 |
| 0.10 | 0.714167 | 0.000223 | 2.399457 | 0.000148 | 2.108725 | +0.015362 | −0.004702 |
| 0.20 | 0.728043 | 0.000188 | 2.397341 | 0.000147 | 2.205888 | +0.029238 | −0.006817 |
| 0.50 | 0.762352 | 0.000111 | 2.398420 | 0.000166 | 2.462137 | +0.063546 | −0.005738 |

### 3.2 Acceptance Probability

Token-level acceptance $\alpha$ increases monotonically with $\lambda$, from a baseline of 0.699 to 0.762 at $\lambda = 0.5$, an absolute gain of +0.064 (9.1% relative). The effect is highly stable across seeds: the largest standard deviation is 0.000261 at $\lambda = 0$ and shrinks to 0.000111 at $\lambda = 0.5$.

The $\gamma{=}4$ IID proxy for tokens per target verification increases from 2.005 to 2.462, a 22.8% relative gain. We emphasize that this is a distributional proxy that assumes IID acceptance across draft positions and excludes draft model runtime overhead, target verification batching efficiency, and all hardware-specific effects.

### 3.3 Target Quality

Heldout NLL does not regress at any tested $\lambda$. It slightly *improves* for all $\lambda > 0$, with the best NLL at $\lambda = 0.20$ (2.397, a reduction of 0.007 from baseline). At $\lambda = 0.50$, NLL is 2.398, still marginally better than baseline.

This NLL improvement is likely an artifact of the proxy setting: the draft distribution acts as a regularizer for the limited head model, which has relatively few parameters relative to the feature space. We do not expect this behavior to hold in general. At sufficient $\lambda$, alignment pressure should eventually distort the target distribution and harm NLL. The absence of NLL regression in this experiment may reflect that the tested $\lambda$ range is below that threshold for this particular model capacity and draft strength.

### 3.4 Sensitivity to $\lambda$

The relationship between $\alpha$ and $\lambda$ is approximately linear over the tested range, with no sign of saturation at $\lambda = 0.5$. This suggests further gains in $\alpha$ may be available at higher $\lambda$, though NLL regression becomes more likely. The trade-off frontier between $\alpha$ and NLL was not fully characterized and should be explored in future work, particularly in settings where the free-lunch regime does not hold.

## 4 Limitations

This study has several substantial limitations that constrain the generality of its conclusions:

1. **Character-level frozen-feature proxy.** The target model uses hand-specified sparse features (decayed lag one-hots, recent bigrams) rather than learned transformer representations. The LM head is a single projection matrix, not the complex head of a modern LLM. Results may not transfer to transformer-scale architectures where the head interacts with rich, learned representations.

2. **Toy dataset.** Tiny Shakespeare is a small character-level corpus. Distributional properties (vocabulary size, context dependence, entropy) differ markedly from subword-level LLM pretraining or downstream tasks.

3. **Quality proxy, not task quality.** We measure heldout NLL, not downstream task performance. A small NLL change may or may not correspond to acceptable task-level behavior in a real system.

4. **No wall-clock throughput.** The $\gamma{=}4$ proxy is a purely distributional calculation assuming IID acceptance. It excludes draft model runtime, target verification batching efficiency, kernel launch overhead, and all hardware-specific effects that determine actual speculative decoding speedup.

5. **Fixed, weak draft model.** The 1-gram draft is far weaker than practical draft models (e.g., distilled or smaller transformers). The magnitude and even the direction of the alignment effect may differ with stronger or adaptive draft models.

6. **No exploration of $\lambda$ failure modes.** We did not test $\lambda > 0.5$ or characterize the point at which NLL regression begins. The apparent free lunch (improved $\alpha$ with no NLL cost) may not persist at higher alignment strengths or in richer models.

7. **Single alignment objective.** We use $D_{\mathrm{KL}}(q \| p)$ as the alignment term. Other divergences or directly optimizing $\alpha$ may yield different trade-offs.

8. **No end-to-end speculative decoding validation.** The experiment measures distributional overlap and a derived proxy, not actual speculative decoding with rejection sampling, token tree construction, or real serving infrastructure.

## 5 Reproducibility Checklist

- **Code:** `src/spec_friendly_lm_head.py` (compiles via `python -m py_compile`)
- **Primary metrics files:** `results/full_draft1_metrics.json`, `results/full_draft1_seed11.json`, `results/full_draft1_seed23.json`
- **Aggregate data:** `results/aggregate.csv`
- **Primary logs:** `logs/full_draft1.log`, `logs/full_draft1_seed11.log`, `logs/full_draft1_seed23.log`
- **Smoke test metrics:** `results/smoke_metrics.json`, `results/smoke_draft1_metrics.json`, `results/smoke_bigram_features_metrics.json`
- **Earlier pilot (not part of main analysis):** `results/full_metrics.json`, `logs/full.log` (3-gram draft pilot)
- **Random seeds:** default (unspecified), 11, 23
- **$\lambda$ sweep:** {0.0, 0.05, 0.10, 0.20, 0.50}
- **Draft model:** 1-gram character model (fixed)
- **Dataset:** Tiny Shakespeare, sourced from Karpathy char-rnn public data
- **Hardware:** Local machine, ~116 GiB available RAM, swap disabled; peak RSS ~2.10 GB for full runs
- **Reproduction command:** `python src/spec_friendly_lm_head.py --mode full --draft-ngram 1 --out results/full_draft1_metrics.json` (and variants with `--seed 11`, `--seed 23`)

## 6 Conclusion

In a controlled character-level proxy, adding a draft-alignment KL term to the LM head training objective materially increases speculative decoding acceptance probability without heldout NLL regression. At $\lambda = 0.5$, acceptance rises from 0.699 to 0.762 (+9.1% relative), and the IID $\gamma{=}4$ tokens-per-verification proxy improves by 22.8%. The effect is stable across three random seeds.

However, this result is a feasibility demonstration in a simplified setting, not an end-to-end proof. The proxy uses frozen hand-specified features, a character-level vocabulary, a deliberately weak draft model, and excludes all runtime costs. The absence of NLL regression is likely an artifact of the limited model capacity rather than a general property. Whether head-only tuning can improve real speculative decoding throughput on transformer-scale models—with learned representations, subword vocabularies, practical draft models, and actual hardware—remains an open question.

The natural next step is a frozen-body transformer LM-head or logit-adapter finetune with a fixed draft model, measuring both exact speculative acceptance rates and wall-clock decode throughput on a real serving stack. If the distributional alignment effect transfers, head-only tuning could offer a low-cost post-hoc adaptation to make existing target models more speculation-friendly without modifying their representations.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Harness source | `src/spec_friendly_lm_head.py` |
| Aggregate results | `results/aggregate.csv` |
| Primary metrics (seed default) | `results/full_draft1_metrics.json` |
| Primary metrics (seed 11) | `results/full_draft1_seed11.json` |
| Primary metrics (seed 23) | `results/full_draft1_seed23.json` |
| Primary log (seed default) | `logs/full_draft1.log` |
| Primary log (seed 11) | `logs/full_draft1_seed11.log` |
| Primary log (seed 23) | `logs/full_draft1_seed23.log` |
| Smoke metrics | `results/smoke_metrics.json` |
| Smoke draft-1 metrics | `results/smoke_draft1_metrics.json` |
| Smoke bigram-feature metrics | `results/smoke_bigram_features_metrics.json` |
| Earlier pilot metrics | `results/full_metrics.json` |
| Earlier pilot log | `logs/full.log` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T012618467379+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T012618467379+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T012618467379+0000/paper_manifest.json` |
