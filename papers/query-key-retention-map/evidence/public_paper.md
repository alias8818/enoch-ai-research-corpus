# Query-Key Retention Map: Evaluating Query-Key Geometry as a Signal for KV-Cache Retention

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, and metric files). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

We investigate whether a lightweight query-key retention map—a method that scores cached key vectors by their maximum cosine similarity to calibration query vectors observed from early context—can identify future attention-relevant KV-cache entries more effectively than simple baselines. Using a teacher-forced evaluation on GPT-2-family models, we measure the fraction of future attention mass retained under several selection policies at KV budgets of 12.5%, 25%, and 50%. The pure query-key map policy captures measurable signal, retaining 0.559 attention mass at 12.5% budget on GPT-2 versus 0.127 for random selection and 0.445 for a history-attention baseline. However, it consistently underperforms a recency-plus-attention-sink baseline across all budgets tested. A hybrid policy combining the query-key map with mandatory attention-sink and recency reservations outperforms the recency-sink baseline at 25% and 50% budgets on both DistilGPT-2 and GPT-2, but trails it at 12.5%. A substantial gap to the oracle upper bound remains at all budgets. These results indicate that query-key geometry carries useful but insufficient signal for standalone KV-cache retention; it may serve as a complementary feature when combined with sink and recency reservations.

## Introduction

Autoregressive language models must manage growing key-value (KV) caches during long-context generation. Several eviction and compression strategies have been proposed. StreamingLLM demonstrates that retaining initial "attention sink" tokens plus a rolling recency window is sufficient for streaming inference. H2O and related heavy-hitter approaches retain tokens that have accumulated high attention scores over prior steps. SnapKV and similar methods use observed prompt attention structure to guide KV compression.

These approaches share a common limitation: they rely on either positional heuristics (sink + recent) or retrospective attention statistics. Neither directly leverages the geometric relationship between query vectors and key vectors—the quantity that determines attention weights under scaled dot-product attention.

We ask: can a simple query-key retention map, constructed from calibration queries observed in early context, predict which cached keys will receive future attention? Specifically, for each cached key, we compute its maximum cosine similarity to a set of query prototypes derived from early tokens, and retain the highest-scoring keys within a given budget. This requires no access to future queries or future attention weights.

We evaluate this approach on GPT-2-family models using an offline attention-mass-retention metric. Our results are mixed. The query-key map contains real predictive signal but is not strong enough to serve as a standalone retention policy. A hybrid combining the map with mandatory sink and recent tokens shows more promise, outperforming the recency-sink baseline at moderate budgets but not at the tightest budget. These are toy-scale, proxy-metric results and should not be taken as evidence of production viability.

## Method

### Setup

We load causal GPT-2-family models in teacher-forced mode and extract per-layer, per-head query and key vectors from the model's attention projections. For each future token position, we evaluate how well different retention policies preserve the attention distribution that the full model would assign over prior tokens.

### Calibration

Early context tokens serve as calibration queries. We collect query vectors from these positions and treat them as prototypes representing the query manifold the model tends to produce. No future query information is used. The calibration window is fixed and does not update as generation proceeds.

### Retention Policies

At each future token position, given a KV budget (fraction of available prior tokens to retain), we compare six selection policies:

1. **random**: Deterministic random selection of keys within the budget. Serves as a lower bound.
2. **recency_sink**: Mandatory retention of the first four tokens (attention sinks) plus the most recent tokens up to the budget. Mirrors the StreamingLLM strategy.
3. **history_attention**: Online heavy-hitter approximation using cumulative prior attention weights. Mirrors the H2O strategy.
4. **qk_map**: Retain keys with the highest maximum cosine similarity to the calibration query prototypes.
5. **qk_map_sink_recent**: The qk_map policy with mandatory reservation of the first four sink tokens and the last four recent tokens, filling the remaining budget from the qk_map ranking.
6. **oracle_attention**: Select keys by the current future attention weights. This is an impossible upper bound (requires future information) but establishes the maximum achievable retention for a given budget.

### Metric

The primary metric is **future attention mass retained**: the fraction of the full-model attention distribution over prior tokens that falls on the retained subset. A policy that retains the most-attended tokens achieves a score near 1.0; a policy retaining irrelevant tokens approaches the budget fraction (equivalent to random). This is an offline proxy metric; it does not directly measure perplexity, generation quality, or decode throughput.

### Budgets

We evaluate at three KV budgets: 12.5%, 25%, and 50% of available prior tokens.

### Models

We test on three GPT-2-family models of increasing size:

- **sshleifer/tiny-gpt2**: A minimal distillation used as a smoke test.
- **distilgpt2**: The DistilGPT-2 model.
- **gpt2**: The standard GPT-2 (124M parameter) model.

All runs were conducted on CPU with PyTorch 2.11.0 and Transformers 5.7.0. These are toy-scale experiments; results may not transfer to modern long-context LLMs.

## Results

### Smoke Test: sshleifer/tiny-gpt2

The tiny model exhibited nearly uniform attention across prior tokens. All policies retained approximately the budget fraction, with no meaningful differentiation between them. This serves as a useful negative control: the metric does not fabricate policy differences when attention is unstructured.

| Budget | random | recency_sink | qk_map | qk_map_sink_recent | oracle |
|-------:|-------:|-------:|-------:|-------:|-------:|
| 12.5% | 0.1333 | 0.1333 | 0.1333 | 0.1333 | 0.1334 |
| 25%   | 0.2570 | 0.2570 | 0.2570 | 0.2570 | 0.2571 |
| 50%   | 0.5046 | 0.5046 | 0.5046 | 0.5046 | 0.5047 |

### DistilGPT-2

| Budget | random | history_attention | recency_sink | qk_map | qk_map_sink_recent | oracle |
|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| 12.5% | 0.1366 | 0.4053 | 0.6162 | 0.5140 | 0.5927 | 0.7875 |
| 25%   | 0.2615 | 0.4832 | 0.7512 | 0.6478 | 0.7644 | 0.8728 |
| 50%   | 0.5078 | 0.6075 | 0.8570 | 0.7841 | 0.8865 | 0.9470 |

### GPT-2

| Budget | random | history_attention | recency_sink | qk_map | qk_map_sink_recent | oracle |
|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| 12.5% | 0.1270 | 0.4452 | 0.6440 | 0.5589 | 0.6231 | 0.8071 |
| 25%   | 0.2547 | 0.5160 | 0.7699 | 0.6760 | 0.7837 | 0.8862 |
| 50%   | 0.4971 | 0.6338 | 0.8718 | 0.7996 | 0.8961 | 0.9535 |

### Key Observations

**The query-key map contains measurable predictive signal.** On GPT-2 at 12.5% budget, qk_map retains 0.559 attention mass versus 0.127 for random and 0.445 for history_attention. This is a 4.4× improvement over random and a 1.26× improvement over the history-attention baseline. The signal persists across budgets and both non-trivial models.

**Pure qk_map underperforms recency_sink at all budgets.** On GPT-2, recency_sink retains 0.644 at 12.5% budget versus qk_map's 0.559. The gap narrows at higher budgets (0.872 vs. 0.800 at 50%) but does not close. This is a negative result for the standalone policy: the simple heuristic of keeping sink and recent tokens is more effective than query-key geometry alone.

**The hybrid qk_map_sink_recent is the strongest non-oracle policy at moderate budgets.** On GPT-2 at 25% budget, the hybrid retains 0.784 attention mass, exceeding recency_sink's 0.770. At 50%, the margin widens (0.896 vs. 0.872). On DistilGPT-2, the same pattern holds: 0.764 vs. 0.751 at 25%, and 0.887 vs. 0.857 at 50%.

**The hybrid trails recency_sink at the tightest budget.** At 12.5% budget on GPT-2, qk_map_sink_recent retains 0.623 versus recency_sink's 0.644. The mandatory sink+recent reservations consume 8 of the retained slots, leaving very few slots for the qk_map to fill, which limits its contribution at small budgets.

**The oracle gap remains large.** Even the best non-oracle policy (qk_map_sink_recent at 50% budget on GPT-2) retains only 0.896 attention mass versus the oracle's 0.954. At 12.5%, the gap is 0.623 vs. 0.807. This indicates substantial room for improvement in predicting future attention relevance.

## Limitations

1. **Proxy metric, not end-task quality.** We measure attention mass retained, not perplexity, generation quality, or downstream task performance. Attention mass is a necessary but not sufficient condition for maintaining model quality; the relationship between retained attention mass and output degradation is not established here.

2. **Small, hand-written evaluation contexts.** The test contexts are small hand-written probes, not a broad benchmark. Results may not generalize to diverse or naturally occurring long contexts.

3. **GPT-2-family models only.** All experiments use GPT-2-architecture models with multi-head attention (MHA). Modern long-context LLMs typically use grouped-query attention (GQA) or multi-query attention (MQA), which change the key-value sharing structure and may alter the query-key geometry signal.

4. **Fixed early calibration window.** The calibration queries come from a fixed early portion of the context. A production system would need to update query prototypes online as generation proceeds, and the effectiveness of such updating is not evaluated.

5. **CPU-only, small-scale runs.** Experiments were conducted on CPU with models up to 124M parameters. No wall-clock decode throughput measurements were taken, and the computational overhead of the qk_map scoring is not profiled in a realistic serving setting.

6. **No comparison to compression-based methods.** We compare against eviction policies but not against KV-cache compression methods (e.g., quantization, token merging) that may achieve different quality-efficiency tradeoffs.

7. **Claim audit status is blocked.** The claim ledger for this artifact contains no structured claims and is flagged as `blocked_empty_claims`. The results reported here have not passed a formal claim-evidence audit.

## Reproducibility Checklist

- **Code availability**: The experiment script is located at `experiments/qk_retention_map.py` within the project directory.
- **Dependency versions**: Python 3.12.3, PyTorch 2.11.0+cu130, Transformers 5.7.0, NumPy 2.4.4. Installation log at `logs/install-python-stack.log`.
- **Model identifiers**: `sshleifer/tiny-gpt2`, `distilgpt2`, `gpt2` (from Hugging Face Transformers).
- **Hardware**: CPU-only execution. No swap configured (SwapTotal: 0 B). Available memory approximately 122.7 GB. Peak RSS: 816 MB (tiny-gpt2), 1.29 GB (distilgpt2), 1.52 GB (gpt2).
- **Random seeds**: The random policy uses deterministic selection; full seed specification should be confirmed from the experiment script.
- **Raw metrics**: Available as JSON files at `results/qk_retention_metrics_tiny.json`, `results/qk_retention_metrics_distilgpt2.json`, and `results/qk_retention_metrics_gpt2.json`.
- **Execution logs**: `logs/qk_retention_tiny_20260429T182128Z.log`, `logs/qk_retention_distilgpt2_20260429T182138Z.log`, `logs/qk_retention_gpt2_20260429T182147Z.log`.
- **Result classification**: These are toy-scale, teacher-forced simulation results on small GPT-2-family models. They are not production validation, not CUDA kernel benchmarks, and not end-task quality measurements.

## Conclusion

We evaluated a query-key retention map that scores cached keys by their cosine similarity to calibration query vectors from early context. The approach captures measurable signal for predicting future attention relevance: on GPT-2, it substantially outperforms random selection and the history-attention baseline. However, as a standalone policy, it consistently underperforms the simple recency-plus-sink heuristic—a negative result. A hybrid policy that combines the query-key map with mandatory sink and recent reservations outperforms the recency-sink baseline at 25% and 50% KV budgets on both DistilGPT-2 and GPT-2, but trails at the tightest 12.5% budget.

These results support a qualified conclusion: query-key geometry is a viable complementary feature for KV-cache retention when combined with positional reservations, but it is not sufficient to replace them. The substantial gap to the oracle selector at all budgets indicates that static calibration queries capture only a fraction of the information needed for optimal retention. Future work should evaluate online-updated query prototypes and measure perplexity and generation quality on a public long-context corpus before any systems-level implementation.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `experiments/qk_retention_map.py` |
| Dependency install log | `logs/install-python-stack.log` |
| Tiny-GPT-2 run log | `logs/qk_retention_tiny_20260429T182128Z.log` |
| DistilGPT-2 run log | `logs/qk_retention_distilgpt2_20260429T182138Z.log` |
| GPT-2 run log | `logs/qk_retention_gpt2_20260429T182147Z.log` |
| Tiny-GPT-2 metrics | `results/qk_retention_metrics_tiny.json` |
| DistilGPT-2 metrics | `results/qk_retention_metrics_distilgpt2.json` |
| GPT-2 metrics | `results/qk_retention_metrics_gpt2.json` |
| Project decision | `.omx/project_decision.json` |
| Project run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260429T181046098414+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T181046098414+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T181046098414+0000/paper_manifest.json` |
