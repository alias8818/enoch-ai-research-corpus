# Attention Sink Preserving Prune: A Synthetic Study of Prefix-Sink Retention in KV-Cache Pruning

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, and decision JSON). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

KV-cache pruning reduces memory and compute during autoregressive transformer inference. A widely observed phenomenon is that early-sequence "attention sink" tokens receive disproportionate attention mass, motivating pruning policies that reserve a small prefix of such tokens alongside recent tokens. This paper evaluates a sink-plus-recency pruning policy against a recency-only baseline using a controlled numpy-based attention trace simulator. We find that prefix-sink preservation improves output fidelity when sink tokens carry low-norm, anchor-like value representations, but can substantially degrade output approximation when sink values are random or high-variance—despite consistently retaining more attention mass. At moderate sink strengths (sink boost = 4) and tight budgets (budget = 32 out of 2048), random sink values caused KL divergence to increase by 143.6% relative to recency-only, while low-norm sink values reduced KL by 84.6%. These results indicate that attention mass alone is an insufficient criterion for sink preservation; value-space behavior must also be considered. All findings are limited to synthetic simulations and require validation on real transformer models.

## 1 Introduction

During autoregressive inference, the key-value (KV) cache grows linearly with sequence length, creating memory pressure that motivates cache pruning. The simplest pruning strategy retains only the most recent $K$ tokens (recency-only). However, empirical observations in large language models show that certain early-sequence positions—termed "attention sinks"—consistently receive high attention scores across queries and layers. This has led to proposals that a fixed prefix of sink tokens should be preserved alongside recent tokens.

The intuition is straightforward: if a small set of prefix tokens captures a large fraction of attention mass, retaining them should better approximate the full-attention output. Yet this reasoning conflates two distinct questions: (1) does retaining sink tokens preserve more *attention mass*, and (2) does preserving more attention mass translate to better *output approximation*? The value vectors associated with sink positions mediate the relationship between attention mass and output quality. If sink values are low-norm or semantically neutral (acting as anchors), retaining them is beneficial. If sink values are high-variance or carry misleading semantic content, the retained mass may actively harm output fidelity.

This study uses a controlled numpy simulation to disentangle these factors. We compare four equal-budget pruning policies—recency-only, sink-plus-recency, random, and oracle top-mass—across varying sink strengths and cache budgets, measuring retained attention mass, relative L2 output error, and KL divergence of a projected next-token distribution. We further isolate the role of sink value norms by running a low-norm sink-value variant.

## 2 Method

### 2.1 Simulator Design

We implemented a numpy-only attention trace simulator (`scripts/asp_prune_experiment.py`) that computes full attention over a synthetic sequence of length $N = 2048$. The simulator generates:

- **Key and query vectors** of dimension $d = 64$, drawn i.i.d. from a standard normal distribution.
- **Value vectors** of dimension $d_v = 64$, drawn i.i.d. from a standard normal distribution (default), or scaled by a factor of 0.1 in the low-norm variant.
- **Attention logits** computed as $Q K^\top / \sqrt{d}$, augmented with a configurable prefix sink bias applied to the first $S = 4$ positions and a mild recency bias applied to recent positions.

For each configuration, 50 random seeds are used to generate independent sequences and query sets ($Q = 256$ queries per seed). This is a toy simulation: no learned weight matrices, no multi-head or multi-layer structure, and no real token embeddings are involved.

### 2.2 Pruning Policies

All policies operate under an equal budget $K$, retaining exactly $K$ of $N$ KV positions:

- **recency_only**: Retain the last $K$ positions.
- **sink_plus_recency**: Retain the first $S$ sink positions plus the last $K - S$ positions.
- **random**: Retain $K$ uniformly random positions.
- **oracle_top_mass**: Offline upper bound; retain the $K$ positions with highest total attention mass across all queries.

After pruning, attention weights are renormalized over the retained positions.

### 2.3 Experimental Conditions

Two main conditions were tested:

1. **Random sink values** (default): Value vectors drawn from $\mathcal{N}(0, I)$.
2. **Low-norm sink values** (`sink_value_scale = 0.1`): Sink-position value vectors scaled by 0.1, simulating anchor-like behavior.

In both conditions, non-sink value vectors remain at default scale.

### 2.4 Parameters

| Parameter | Values |
|---|---|
| Sequence length ($N$) | 2048 |
| Query count | 256 |
| Key/query dimension | 64 |
| Value dimension | 64 |
| Sink count ($S$) | 4 |
| Budget ($K$) | 32, 64, 128, 256 |
| Sink boost | 0, 1, 2, 4, 6, 8 |
| Recency boost | 1.0 |
| Seeds | 50 |

### 2.5 Metrics

- **Retained full-attention mass**: Fraction of the full-attention mass falling on retained positions (higher is better).
- **Relative L2 error**: $\|o_{\text{pruned}} - o_{\text{full}}\|_2 / \|o_{\text{full}}\|_2$ (lower is better).
- **KL divergence**: KL divergence of a synthetic projected next-token distribution between pruned and full attention (lower is better).

Improvement percentages are computed as the relative reduction in error or KL of sink-plus-recency over recency-only. Negative values indicate degradation.

## 3 Results

### 3.1 Random Sink Values

With default (random, full-norm) sink values, the relationship between sink preservation and output quality is non-monotonic and budget-dependent.

**Budget 32, sink boost 4:** Sink-plus-recency retained more attention mass than recency-only ($\Delta = +0.054$), yet output error *increased*: relative L2 error worsened by 50.7% and KL divergence worsened by 143.6%. Despite capturing more mass, the random sink values injected noise that dominated the output at this tight budget.

**Budget 32, sink boost 8:** At higher sink strength, the mass advantage grew ($\Delta = +0.728$), and output quality improved: L2 error reduced by 66.7% and KL divergence reduced by 90.1%. The overwhelming attention mass on sink positions meant that omitting them was catastrophic, and the random sink values were tolerable because the attention distribution was already heavily concentrated.

At intermediate sink boosts (1, 2, 6), the results showed a transition zone where the benefit of mass retention was partially offset by value noise, yielding mixed or marginal improvements.

### 3.2 Low-Norm Sink Values

When sink-position value vectors were scaled to 0.1 of their default norm, sink preservation was consistently beneficial.

**Budget 32, sink boost 4:** Retained mass improvement was identical ($\Delta = +0.054$, since attention mass depends on key/query interactions, not values), but output quality improved substantially: L2 error reduced by 62.4% and KL divergence reduced by 84.6%.

**Budget 32, sink boost 8:** L2 error reduced by 92.6% and KL divergence reduced by 99.4%.

The contrast with the random-value condition at boost 4 is stark: the same attention mass retention that *harmed* output with random sink values *helped* output with low-norm sink values. This confirms that the value-space behavior of sink positions, not just their attention mass, determines whether prefix preservation is beneficial.

### 3.3 Budget Scaling

Larger budgets (64, 128, 256) reduced the absolute magnitude of both benefits and harms, as expected: with more positions retained, the marginal impact of any fixed set of sink positions diminishes. The directional findings (benefit under low-norm, harm under random at moderate boost) persisted at budget 64 but were attenuated at budget 128 and above.

### 3.4 Oracle and Random Baselines

The oracle top-mass policy consistently outperformed all other policies, confirming that attention-mass-informed selection provides an upper bound. The random policy consistently underperformed recency-only, confirming that recency bias provides a meaningful prior for KV-cache pruning.

### 3.5 Summary of Key Contrasts

| Condition | Budget | Sink Boost | Mass $\Delta$ | L2 Reduction (%) | KL Reduction (%) |
|---|---|---|---|---|---|
| Random sink values | 32 | 4 | +0.054 | −50.7 | −143.6 |
| Random sink values | 32 | 8 | +0.728 | +66.7 | +90.1 |
| Low-norm sink values | 32 | 4 | +0.054 | +62.4 | +84.6 |
| Low-norm sink values | 32 | 8 | +0.728 | +92.6 | +99.4 |

Positive reduction percentages indicate improvement over recency-only; negative percentages indicate degradation.

## 4 Limitations

1. **Synthetic simulation only.** All experiments use a numpy simulator with random key/query/value vectors and injected attention biases. No real transformer model, real attention patterns, or real token distributions were tested. The extent to which real-model sink tokens resemble the "low-norm anchor" or "random high-variance" conditions is unknown.

2. **No perplexity or downstream task evaluation.** The KL divergence metric is computed over a synthetic projected distribution, not over actual model vocabularies or downstream tasks.

3. **Simplified attention structure.** The simulator uses single-head, single-layer attention with i.i.d. random projections. Real transformers exhibit multi-head, multi-layer structure with learned key/query/value matrices that may produce qualitatively different sink behavior.

4. **Fixed sink count and position.** The study assumes sink tokens occupy a fixed prefix of length $S = 4$. Real-model sink positions may not be strictly prefix-aligned, and the optimal number of preserved sinks may vary by layer, head, and input.

5. **Binary value-norm condition.** The experiment contrasts only two value-norm scales (1.0 and 0.1). The space of possible value behaviors (correlated values, position-dependent norms, semantic content) is not explored.

6. **No adaptive policy evaluation.** The findings suggest that adaptive sink preservation (conditioned on both attention mass and value sensitivity) would be preferable, but no such adaptive policy was implemented or tested.

7. **Claim audit status.** The claim ledger for this artifact was flagged as `blocked_empty_claims` at generation time, meaning no structured claims were extracted and the paper has not passed a strict claim/evidence audit. The numerical results reported here are drawn directly from the project decision JSON and run notes, but have not undergone independent verification.

## 5 Reproducibility Checklist

- **Code availability:** The simulator (`scripts/asp_prune_experiment.py`) and summary script (`scripts/summarize_results.py`) are present in the project directory.
- **Random seeds:** 50 seeds per condition; seeds are set deterministically in the simulator.
- **Hardware:** NVIDIA GB10, Linux aarch64; no GPU used (numpy-only).
- **Software:** Python 3, numpy 2.4.4, psutil 7.2.2. No torch or transformers dependency.
- **Memory:** Max RSS ~53 MiB; MemAvailable ~117 GiB throughout; no swap (SwapTotal = 0 by design).
- **Execution time:** ~16.9 s (random sink values), ~17.5 s (low-norm sink values) per main experiment.
- **Output artifacts:** All result JSON files, CSVs, and logs are present in the project directory (see Referenced Artifacts).
- **Smoke test:** Passed (16 rows, ~39 MiB RSS).
- **Evidence type:** Toy numpy simulation. No llama.cpp hook-prototype, CUDA copy calibration, or production validation was performed.

## 6 Conclusion

This synthetic study demonstrates that prefix-sink-preserving KV-cache pruning is conditionally viable: it improves output approximation over recency-only pruning when sink tokens function as low-norm semantic anchors, but can substantially degrade output when sink values are random or high-variance, even when more attention mass is retained. The key finding is that attention mass alone is an insufficient criterion for deciding which positions to preserve in a pruned KV cache; the value-space behavior of those positions must also be considered.

At tight budgets and moderate sink strengths—the regime most relevant to aggressive pruning—the difference between benefit and harm is determined entirely by sink-value properties that are invisible to attention-mass metrics. This suggests that practical sink-preserving pruning policies should either (a) validate that sink positions exhibit anchor-like value behavior for the target model, or (b) incorporate value/output sensitivity into the retention decision rather than relying on attention mass alone.

These conclusions are based solely on synthetic simulations. Validation on real transformer models with accessible KV caches, measuring next-token KL or perplexity over long contexts, is necessary before any deployment recommendation. The comparison should include recency-only, fixed sink-plus-recency, adaptive sensitivity-plus-recency, and oracle/top-attention policies.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Simulator script | `scripts/asp_prune_experiment.py` |
| Summary script | `scripts/summarize_results.py` |
| Smoke test results | `results/smoke_asp_prune.json` |
| Random sink-value main results | `results/main_asp_prune_seq2048_q256_seeds50.json` |
| Random sink-value aggregate CSV | `results/main_aggregate.csv` |
| Random sink-value improvements CSV | `results/main_improvements.csv` |
| Low-norm sink-value main results | `results/main_sink_value_scale_0p1_seq2048_q256_seeds50.json` |
| Low-norm sink-value improvements CSV | `results/main_sink_value_scale_0p1_seq2048_q256_seeds50_improvements.csv` |
| Evidence report | `results/evidence_report.md` |
| Smoke test log | `logs/smoke_asp_prune.log` |
| Random sink-value main log | `logs/main_asp_prune_seq2048_q256_seeds50.log` |
| Low-norm sink-value main log | `logs/main_sink_value_scale_0p1_seq2048_q256_seeds50.log` |
| Project decision JSON | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260430T044618429549+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T044618429549+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T044618429549+0000/paper_manifest.json` |
