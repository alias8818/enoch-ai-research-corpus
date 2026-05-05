# Semantic Channel Naming as a Low-Cost Routing Prior: A Synthetic Benchmark Study

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims. The claim ledger for this paper carries audit status `blocked_empty_claims`, meaning no structured claims have passed formal evidence audit. All findings should be read as preliminary prototype evidence rather than validated scientific claims.

---

## Abstract

We investigate whether encoding task semantics in channel names improves routing accuracy for multi-agent systems relative to opaque or generic identifiers. Using a deterministic synthetic benchmark with 12 agent/channel categories and 120 routing messages per seed, we evaluate five naming conditions under a character n-gram TF-IDF cosine router. Opaque and generic-role identifiers perform at chance (0.083). Compact semantic labels raise ten-seed mean accuracy to 0.253 (SD = 0.038). Alias-rich semantic names further improve to 0.570 (SD = 0.026). However, paraphrase-only messages remain near chance (0.125) even under the alias-rich condition, and misleading semantic names stay at or below chance (ten-seed mean 0.065, SD = 0.024). These results indicate that semantic channel names provide a useful but bounded routing prior: they substantially improve lexical-overlap routing, yet cannot substitute for descriptions, examples, or embedding-based methods when request vocabulary diverges from channel labels. The benchmark is synthetic and uses a simple TF-IDF router; production validation requires live agent traces and more capable routing models.

## Introduction

Multi-agent routing systems must direct incoming messages to the appropriate agent or channel. In practice, routing metadata often relies on opaque identifiers (e.g., `channel_00`) or generic role labels (e.g., `agent_lane_00`) that carry no task-relevant signal. If channel names instead encoded task semantics—for example, `debug_failures` rather than `channel_03`—a simple lexical router could exploit the resulting name–message overlap to improve routing beyond chance.

This idea relates to information-foraging theory, which holds that agents choose paths using proximal cues that indicate likely information value (Pirolli & Card, 1999, *Information Foraging*, Psychological Review 106(4):643–675, DOI 10.1037/0033-295X.106.4.643). It also parallels the design of function-calling APIs in large language model platforms, where tool `name` and `description` fields serve as model-visible routing metadata (OpenAI function-calling documentation, https://platform.openai.com/docs/guides/function-calling).

We test three hypotheses:

1. **Semantic naming helps.** Channel names that encode task semantics should improve routing accuracy over opaque or generic IDs.
2. **The effect depends on correct semantics.** Misleading semantic names should not improve routing, ruling out length or surface-form artifacts.
3. **Names alone are insufficient.** Paraphrased requests that use different vocabulary from the channel name should reveal the limits of name-only routing.

## Method

### Benchmark Design

We constructed a deterministic local proxy benchmark with 12 agent/channel categories. For each seed, we generated 120 routing messages: 96 lexical-overlap tasks (where the message vocabulary substantially overlaps the correct channel's semantic domain) and 24 paraphrase tasks (where the message intent matches a channel but uses different vocabulary). The dataset is synthetic but deterministic and included for inspection and replay.

### Naming Conditions

Five naming conditions were evaluated:

- **opaque_ids**: `channel_00`, `channel_01`, …, `channel_11`
- **generic_role_ids**: `agent_lane_00`, `agent_lane_01`, …, `agent_lane_11`
- **semantic_compact**: Short purpose labels such as `debug_failures`, `billing_payments`
- **semantic_alias_rich**: Purpose labels augmented with common aliases, e.g., `debug_errors_failures_crashes_exceptions`
- **misleading_semantic**: Compact semantic labels intentionally assigned to the wrong channels (the name for channel *i* describes the task domain of channel *j* ≠ *i*)

### Router

We evaluated both word-token and character-n-gram TF-IDF cosine routers. The character n-gram router was designated as the primary metric because it handles morphological variation without external models. For each incoming message, the router computes TF-IDF vectors over the concatenated channel name and message text, then selects the channel with the highest cosine similarity. This is a deliberately cheap baseline router; it does not use pretrained embeddings or language models.

### Evaluation Protocol

- **Single-seed run**: 120 messages, bootstrap 95% confidence intervals resampled over examples.
- **Ten-seed stability check**: Repeated the benchmark with seeds 1–10, reporting mean and standard deviation of accuracy across seeds.
- Accuracy is decomposed into **lexical accuracy** (96 lexical-overlap examples) and **paraphrase accuracy** (24 paraphrase examples).

### Computational Environment

All runs were CPU-only, sub-second per seed, on a machine with 127.5 GB total memory and 122.7 GB available. No GPU was required. Swap was disabled (SwapTotal: 0 kB). No GB10/GPU long run was needed.

## Results

### Single-Seed Results (Character TF-IDF)

| Condition | Overall Acc | 95% Bootstrap CI | Lexical Acc | Paraphrase Acc |
|---|---:|---:|---:|---:|
| opaque_ids | 0.083 | [0.042, 0.142] | 0.083 | 0.083 |
| generic_role_ids | 0.083 | [0.042, 0.142] | 0.083 | 0.083 |
| semantic_compact | 0.225 | [0.150, 0.308] | 0.250 | 0.125 |
| semantic_alias_rich | 0.575 | [0.483, 0.658] | 0.688 | 0.125 |
| misleading_semantic | 0.100 | [0.050, 0.158] | 0.094 | 0.125 |

Opaque and generic-role identifiers perform at chance level for 12 channels (1/12 ≈ 0.083). Compact semantic names roughly triple overall accuracy. Alias-rich names achieve 0.575 overall accuracy, with lexical accuracy reaching 0.688. However, paraphrase accuracy remains at 0.125 across all semantic conditions—only marginally above chance. Misleading semantic names do not improve routing (0.100 overall), confirming that the benefit depends on correct semantic correspondence rather than name length or surface form.

### Ten-Seed Stability Check (Character TF-IDF)

| Condition | Mean Acc | SD Acc | Mean Lexical Acc | Mean Paraphrase Acc |
|---|---:|---:|---:|---:|
| opaque_ids | 0.083 | 0.000 | 0.083 | 0.083 |
| generic_role_ids | 0.083 | 0.000 | 0.083 | 0.083 |
| semantic_compact | 0.253 | 0.038 | 0.290 | 0.108 |
| semantic_alias_rich | 0.570 | 0.026 | 0.681 | 0.125 |
| misleading_semantic | 0.065 | 0.024 | 0.064 | 0.071 |

The ten-seed results confirm the single-seed pattern. Opaque and generic IDs remain at chance with zero variance. Semantic compact names show a mean of 0.253 (SD = 0.038). Alias-rich names show a mean of 0.570 (SD = 0.026), indicating stable improvement. Misleading names drop slightly below chance (0.065, SD = 0.024), suggesting that incorrect semantic cues may actively mislead the router. Paraphrase accuracy remains near or below chance across all conditions.

### Key Observations

1. **Semantic names add recoverable signal.** The gap between opaque IDs (0.083) and alias-rich names (0.570) is large and stable across seeds.
2. **Alias richness matters.** Compact names (0.253) improve over chance, but alias-rich names (0.570) more than double that gain, indicating that covering user/task vocabulary in the channel name substantially helps lexical routing.
3. **Correctness is necessary.** Misleading names perform at or below chance, ruling out the possibility that the improvement is an artifact of name length or token count.
4. **Names alone are insufficient for paraphrase.** Paraphrase accuracy stays near chance (0.108–0.125) even with alias-rich names. When request vocabulary diverges from channel labels, a name-only signal provides negligible guidance.

## Limitations

1. **Synthetic benchmark.** The dataset is generated rather than drawn from production routing traces. Real-world messages may exhibit different lexical distributions, ambiguity patterns, or domain shifts. The benchmark may overestimate or underestimate real-world routing benefits.
2. **Simple router.** The character n-gram TF-IDF cosine router is a deliberately cheap baseline. Results do not directly predict behavior of LLM-based or embedding-based routers, which may handle paraphrase better but at higher cost. Whether semantic names provide additional marginal benefit when combined with such models remains untested.
3. **Small scale.** Twelve channels and 120 messages per seed constitute a toy-scale experiment. Scaling to hundreds of channels may change the relative benefit of semantic naming.
4. **No live-agent validation.** These results demonstrate that semantic names add recoverable signal for a cheap router in a synthetic setting; they do not prove production routing improvement. Final scientific closure requires A/B testing on real agent routing traces or controlled live-agent experiments.
5. **Paraphrase set is small.** Only 24 paraphrase examples per seed are evaluated. The near-chance paraphrase result is consistent but estimated from limited data.
6. **Claim audit incomplete.** The claim ledger for this paper carries audit status `blocked_empty_claims`; no structured claims have been extracted or passed formal evidence audit. Findings should be treated as preliminary prototype evidence.
7. **No external model dependency.** The router uses no pretrained embeddings or language models. Whether semantic names provide additional marginal benefit when combined with such models remains untested.

## Reproducibility Checklist

- **Deterministic generation**: The benchmark script accepts a `--seed` argument and produces identical datasets for a given seed.
- **Code available**: `scripts/semantic_channel_naming_eval.py` (SHA-256: `eb5d30ac61c3d471c6333a1ea6457a1a83e99f0373cdf29fd991ba11c6399a86`).
- **Single-seed reproduction**: `python3 scripts/semantic_channel_naming_eval.py --out results/semantic_channel_naming`
- **Multi-seed reproduction**: `for s in 1 2 3 4 5 6 7 8 9 10; do python3 scripts/semantic_channel_naming_eval.py --seed $s --out results/semantic_channel_naming/seeds/seed_$s; done`
- **Result checksums**: `summary.json` (SHA-256: `b07b029f74e4cb72cbe52f7722e9ace452431fce189aa32c7bd37e3771377ec7`), `multiseed_summary.json` (SHA-256: `2def30fb32257647da3f6efa4f0b24c0e63092c1683785f96fa69226061861d2`).
- **Hardware**: CPU-only; no GPU required. Machine had 127.5 GB RAM, 122.7 GB available, no swap.
- **Statistical method**: Bootstrap 95% confidence intervals over per-example predictions; ten-seed mean and standard deviation for stability.
- **Evidence classification**: Results are from a deterministic synthetic benchmark (toy simulation), not from llama.cpp hook-prototype runs, CUDA copy calibration, or final production validation.

## Conclusion

Semantic channel names provide a meaningful, low-cost routing prior in a synthetic benchmark setting. Alias-rich semantic names raised character TF-IDF routing accuracy from chance (0.083) to a ten-seed mean of 0.570, while compact semantic names reached 0.253. Misleading names confirmed that the benefit depends on semantic correctness, not surface form. However, paraphrase accuracy remained near chance across all conditions, demonstrating that name-only routing fails when request vocabulary diverges from channel labels.

The practical implication is that semantic, alias-rich channel names should be adopted as routing metadata—they are cheap to implement and provide substantial signal for lexical overlap cases—but they must be paired with descriptions, examples, or embedding-based methods to handle paraphrase and synonym variation. Production validation via A/B testing on live agent routing traces remains necessary before claiming scientific closure on real-world impact.

---

## Referenced Artifacts

| Artifact | Path | SHA-256 |
|---|---|---|
| Benchmark script | `scripts/semantic_channel_naming_eval.py` | `eb5d30ac61c3d471c6333a1ea6457a1a83e99f0373cdf29fd991ba11c6399a86` |
| Single-seed results | `results/semantic_channel_naming/summary.json` | `b07b029f74e4cb72cbe52f7722e9ace452431fce189aa32c7bd37e3771377ec7` |
| Multi-seed results | `results/semantic_channel_naming/multiseed_summary.json` | `2def30fb32257647da3f6efa4f0b24c0e63092c1683785f96fa69226061861d2` |
| Per-example predictions | `results/semantic_channel_naming/predictions.csv` | — |
| Generated dataset | `results/semantic_channel_naming/dataset.csv` | — |
| Smoke run log | `logs/semantic_channel_naming_eval.log` | `d625a331bb9bbdcb9e9721a2412447228b8ac83f1e8e9a94ca8adedd7c36d7e9` |
| Memory telemetry | `logs/memory_telemetry.txt` | `7f506ae3d1363be0b3baaf77e599878ebece969cf6230e0dcb2d2e34d5841dfd` |
| Stability run logs | `logs/semantic_channel_naming_seeds/seed_*.log` | — |
| Project decision | `.omx/project_decision.json` | — |
| Run notes | `run_notes.md` | — |
| Claim ledger | `papers/source-record-redacted-20260430T042448341344+0000/claim_ledger.json` | — |
| Evidence bundle | `papers/source-record-redacted-20260430T042448341344+0000/evidence_bundle.json` | — |
| Paper manifest | `papers/source-record-redacted-20260430T042448341344+0000/paper_manifest.json` | — |
