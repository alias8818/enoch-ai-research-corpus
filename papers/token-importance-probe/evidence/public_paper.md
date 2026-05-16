# Token Importance Probe: Black-Box Leave-One-Out Logprob Deltas Identify Causal Input Tokens in Synthetic Dictionary Lookup

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, and metric files). The operator who released these artifacts claims no personal authorship credit for the writing or the experimental results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact.

---

## Abstract

We investigate whether a purely black-box, leave-one-token-out probe—requiring only next-token log probabilities from a locally hosted language model—can identify which input tokens causally drive the model's answer. Using synthetic dictionary-lookup prompts with known causal token roles (query key, dictionary key, dictionary value, distractors), we measure importance as the log-probability drop on the expected first answer token when a candidate input token is replaced. On Qwen2.5-3B-Instruct (Q4_K_M), the probe achieves 8/8 baseline answer accuracy, a 7.10-nat mean gap between target-token and distractor-token ablation damage, and places the answer value in the top-3 importance ranks in 7/8 cases. On Qwen2.5-0.5B-Instruct (Q4_K_M), baseline accuracy is lower (6/8), the target–distractor gap is 3.28 nats, and the answer value ranks first by logprob damage in all 8 cases despite the weaker model. These results suggest the probe is viable as a local, model-agnostic diagnostic for simple factual-lookup contexts, though faithfulness on longer natural-language reasoning remains untested. Several confounds—including distribution-shift contamination, a top-logprob floor approximation, and the small sample of 8 cases per model—limit the strength of the conclusions.

---

## 1. Introduction

Understanding which input tokens drive a language model's output is important for interpretability, debugging, and trust. Existing approaches—attention visualization, gradient-based attribution, and activation patching—require access to model internals. In many practical deployments, only an inference API exposing generated-token log probabilities is available.

We ask: can a black-box probe that perturbs the input and observes the change in next-token log probabilities reliably distinguish causal input tokens from irrelevant distractors?

We study this question in a controlled setting: synthetic dictionary-lookup prompts where the causal roles of individual tokens are known by construction. This eliminates the attribution ground-truth problem and allows direct evaluation of the probe's discriminative power. The trade-off is ecological validity: a controlled synthetic task may not reflect the probe's behavior on natural-language inputs.

---

## 2. Method

### 2.1 Probe Design

The probe implements a leave-one-token-out ablation strategy around `llama.cpp` chat completions:

1. **Prompt construction.** Build synthetic dictionary-lookup prompts of the form `Lookup <key> =` with a small dictionary containing one matching row and distractor rows. Each prompt contains tokens with known causal roles:
   - `query_key_target`: the queried key in the lookup instruction.
   - `dict_key_target`: the matching key in the dictionary.
   - `dict_value_target`: the answer value in the matching row.
   - Distractor keys and values from non-matching rows.

2. **Baseline scoring.** Submit the intact prompt to the model and record the log probability of the expected first answer token from the `logprobs` field returned by the OpenAI-compatible `llama-server` endpoint.

3. **Ablation.** Replace one candidate input token occurrence with `____` and rescore the same expected answer token.

4. **Importance score.** Define importance as `baseline_logprob − ablated_logprob`. Larger positive values indicate that removing the token made the known answer less likely.

The probe requires only generated-token log probabilities—no attention matrices, hidden states, or gradients.

### 2.2 Models and Infrastructure

| Item | Detail |
|------|--------|
| Model A | Qwen2.5-0.5B-Instruct, quantized Q4_K_M (GGUF) |
| Model B | Qwen2.5-3B-Instruct, quantized Q4_K_M (GGUF) |
| Inference engine | `llama-server` (llama.cpp build) |
| Hardware | NVIDIA GPU (GB10-class), ~121 GB system RAM, swap disabled |
| Context window | 2048 tokens |
| GPU layers | All 99 layers offloaded (`--ngl 99`) |
| Top-logprobs | 20 per position |
| Cases per model | 8 |

### 2.3 Ablation Floor Approximation

When the expected answer token was absent from the returned top-20 log probabilities for an ablated prompt, the script assigned a conservative floor value of `min_top_logprob − 1` rather than querying the full vocabulary. This underestimates the damage for strongly suppressed tokens and may compress the dynamic range of importance scores for the most impactful ablations. The effect is directional: it biases the probe toward underestimating the target–distractor gap, making the reported discrimination gaps conservative lower bounds on the true gaps.

### 2.4 Scope of Scoring

Only the first answer token is scored. The dictionary values were intentionally chosen as single-token color words to make first-token scoring sufficient for this benchmark. Multi-token answers would require scoring a sequence of conditional log probabilities, which this probe does not implement.

### 2.5 Classification of Evidence

This experiment constitutes a llama.cpp hook-prototype result: the probe wraps a locally hosted inference server via its OpenAI-compatible API, uses no model internals, and was run on a small synthetic benchmark (8 cases per model). It is not a production validation, nor was it evaluated on natural-language tasks.

---

## 3. Results

### 3.1 Baseline Answer Accuracy

| Model | Baseline Accuracy (8 cases) |
|-------|---------------------------:|
| Qwen2.5-0.5B-Instruct-Q4_K_M | 0.75 (6/8) |
| Qwen2.5-3B-Instruct-Q4_K_M | 1.00 (8/8) |

The 0.5B model failed on 2 of 8 lookup cases at baseline, meaning the expected answer token was not the model's top prediction even before any ablation. This weakens the probe's signal for those cases, since the importance score measures damage to a token the model was not reliably predicting.

### 3.2 Target–Distractor Discrimination

| Model | Target–Distractor Mean Delta Gap (nats) |
|-------|---------------------------------------:|
| Qwen2.5-0.5B-Instruct-Q4_K_M | 3.278 |
| Qwen2.5-3B-Instruct-Q4_K_M | 7.098 |

Both models show a positive gap: ablating tokens with known causal roles damages the expected answer more than ablating distractors. The gap is substantially larger for the 3B model, consistent with its higher baseline accuracy and presumably sharper internal representations.

### 3.3 Role-Level Importance Breakdown

Mean importance (logprob delta in nats) by token role:

| Token Role | 0.5B | 3B |
|------------|-----:|----:|
| `dict_value_target` | 5.58 | 8.46 |
| `query_key_target` | 2.55 | 12.21 |
| `dict_key_target` | 0.88 | 1.48 |
| Distractors (mean) | −0.28 | 0.29 |

Several observations warrant attention:

- **0.5B model:** The dictionary value (the answer itself present in the prompt) causes the largest damage when ablated, followed by the query key. Distractor ablations show a slightly negative mean importance (−0.28 nats), meaning removing distractors slightly *increased* the expected answer's log probability on average. This direction is consistent with a plausible coherence effect—fewer distractors reduce competition—but the magnitude is small.

- **3B model:** The query key causes the largest damage (12.21 nats), substantially exceeding the dictionary value (8.46 nats). This role-ordering reversal between model sizes may reflect different internal strategies: the 3B model may rely more heavily on the query–key match operation, while the 0.5B model may depend more on directly recognizing the value in context. This interpretation is speculative; the experiment was not designed to isolate mechanism differences.

- **Mixed distractor signal for 3B.** Distractor ablations for the 3B model show a small positive mean (0.29 nats), indicating slight damage rather than benefit. This is the wrong direction for a clean probe and suggests contamination from distribution shift: replacing a distractor token with `____` changes the prompt's statistical properties in a way that slightly harms the expected answer, even though the distractor token is causally irrelevant.

### 3.4 Ranking Performance

| Model | Causal Tokens in Top-3 (mean) | Answer-Value Rank@3 |
|-------|------------------------------:|---------------------:|
| Qwen2.5-0.5B-Instruct-Q4_K_M | 2.75 / 3 | 1.000 |
| Qwen2.5-3B-Instruct-Q4_K_M | 2.25 / 3 | 0.875 |

The 0.5B model places the answer value at rank 1 in all 8 cases by expected-token logprob damage, despite its lower baseline accuracy. The 3B model achieves rank@3 of 0.875 (7/8 cases with the answer value in the top 3), with a slightly lower mean count of causal tokens in the top 3 (2.25 vs. 2.75). This apparent inversion—where the smaller model ranks the answer value more consistently—may be an artifact of the small sample size (8 cases) and the different role-level importance profiles. No statistical test was applied; the difference may not be significant.

### 3.5 Latency and Resource Usage

| Model | Mean Request Latency | CUDA Memory | Peak GPU Util. |
|-------|---------------------:|------------:|---------------:|
| Qwen2.5-0.5B-Instruct-Q4_K_M | 0.0265 s | ~697 MiB | ~30% |
| Qwen2.5-3B-Instruct-Q4_K_M | 0.0461 s | ~2,207 MiB | 52–59% |

System RAM remained ample throughout: starting at ~121.6 GB available, ending at ~120.3 GB (0.5B run) and ~118.8 GB (3B run). Swap was disabled (SwapTotal: 0 kB). For the 3B model, server-side timings near run end showed prompt eval at roughly 0.5–1.7 ms/token (depending on prompt length) and decode at roughly 9.3 ms/token (~107 tokens/s for 2-token completions).

---

## 4. Limitations

1. **Synthetic task only.** The probe is evaluated exclusively on controlled dictionary-lookup prompts with single-token answers. Whether the same logprob-delta scores faithfully reflect causal importance in longer, natural-language reasoning contexts is unknown. The synthetic setting provides ground truth but sacrifices ecological validity.

2. **Deletion sensitivity ≠ causal contribution.** Replacing a token with `____` changes the prompt's distributional properties beyond merely "removing information." A high importance score may partly reflect sensitivity to prompt editing (distribution shift) rather than pure causal contribution. The 3B model's positive distractor mean (0.29 nats) is direct evidence of this confound. Distinguishing causal contribution from distribution shift requires additional controls (e.g., masking vs. insertion vs. synonym substitution), which were not implemented here.

3. **Top-logprob floor approximation.** When the expected token falls outside the top-20 log probabilities after ablation, the script uses `min_top_logprob − 1` as a floor. This underestimates true damage for strongly suppressed tokens and compresses the upper range of importance scores. While this biases the reported gaps conservatively (downward), it also means the absolute importance values are not directly comparable to what a full-vocabulary logprob query would yield.

4. **First-token-only scoring.** Only the first answer token is scored. Multi-token answers would require scoring a sequence of conditional log probabilities, which this probe does not implement. The benchmark values were intentionally single-token color words to sidestep this limitation.

5. **Small sample size.** Only 8 cases per model were evaluated. The reported metrics—including the 0.5B model's higher answer-value ranking despite lower accuracy, and the role-ordering reversal between model sizes—may not be stable across larger samples. No confidence intervals or statistical tests were computed.

6. **Quantization effects.** Both models were run in Q4_K_M quantization. The impact of quantization on logprob fidelity and, consequently, on importance scores has not been isolated. Quantization may introduce systematic biases in logprob values that affect the probe's discrimination.

7. **No random seeds recorded.** The prompts are deterministic synthetic constructions, so this does not affect reproducibility of the prompt set. However, any stochasticity in the inference server (e.g., sampling parameters) was not controlled via explicit seeds.

8. **Single replacement strategy.** Only one replacement token (`____`) was tested. The choice of replacement may affect the magnitude and even the sign of importance scores. Other replacement strategies (e.g., deletion, random token, [MASK]) were not evaluated.

---

## 5. Reproducibility Checklist

| Item | Status |
|------|--------|
| Probe implementation available | Yes: `scripts/run_token_importance_probe.py` |
| Model files specified | Yes: Qwen2.5-0.5B-Instruct-Q4_K_M.gguf, qwen2.5-3b-instruct-q4_k_m.gguf |
| Inference engine specified | Yes: llama.cpp `llama-server` (build path recorded in run notes) |
| Server launch parameters recorded | Yes: `--port`, `--ctx 2048`, `--ngl 99`, `--top-logprobs 20` |
| Number of cases specified | Yes: 8 per model |
| Random seeds | Not recorded; prompts are deterministic synthetic constructions |
| Hardware specified | Yes: NVIDIA GPU (GB10-class), ~121 GB RAM, swap disabled |
| Raw ablation records available | Yes: `ablation_records.jsonl` and `.csv` per model |
| Baseline records available | Yes: `baseline_records.json` per model |
| Environment log available | Yes: `artifacts/logs/env_probe.log` |
| GPU monitoring available | Yes: `nvidia_smi.csv` per model |
| Server logs available | Yes: `llama_server.log` per model |
| Combined metrics available | Yes: `artifacts/metrics/token_importance_summary.json` |
| Statistical tests | Not performed |

---

## 6. Conclusion

A black-box leave-one-token-out probe using only next-token log probabilities can distinguish causal input tokens from distractors in synthetic dictionary-lookup prompts. On Qwen2.5-3B-Instruct, the probe achieves a 7.10-nat target–distractor discrimination gap and places the answer value in the top-3 importance ranks in 7/8 cases. On Qwen2.5-0.5B-Instruct, the gap is 3.28 nats and the answer value ranks first in all cases by logprob damage, though baseline accuracy is only 75%.

The positive result is confined to a controlled synthetic task with short prompts and single-token answers. Several confounds temper the conclusion: the 3B model's distractor ablations show a small positive mean importance (0.29 nats), indicating distribution-shift contamination; the top-logprob floor approximation compresses the upper range of importance scores; and the sample of 8 cases per model is too small to support robust statistical claims. The probe's faithfulness on natural-language contexts, its susceptibility to distribution-shift confounds, and the effect of the floor approximation all remain open questions.

The most useful next steps are: (1) adding exact arbitrary-continuation logprob scoring to eliminate the floor approximation, (2) evaluating on real retrieval or QA prompts with labeled evidence spans, and (3) comparing deletion, masking, and insertion controls to quantify distribution-shift sensitivity.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Run notes | `run_notes.md` |
| Probe implementation | `scripts/run_token_importance_probe.py` |
| Combined metrics | `artifacts/metrics/token_importance_summary.json` |
| 0.5B summary | `artifacts/token_importance_probe/qwen_0p5b/summary.json` |
| 0.5B ablation records (JSONL) | `artifacts/token_importance_probe/qwen_0p5b/ablation_records.jsonl` |
| 0.5B ablation records (CSV) | `artifacts/token_importance_probe/qwen_0p5b/ablation_records.csv` |
| 0.5B baseline records | `artifacts/token_importance_probe/qwen_0p5b/baseline_records.json` |
| 0.5B server log | `artifacts/token_importance_probe/qwen_0p5b/logs/llama_server.log` |
| 0.5B GPU monitor | `artifacts/token_importance_probe/qwen_0p5b/logs/nvidia_smi.csv` |
| 3B summary | `artifacts/token_importance_probe/qwen_3b/summary.json` |
| 3B ablation records (JSONL) | `artifacts/token_importance_probe/qwen_3b/ablation_records.jsonl` |
| 3B ablation records (CSV) | `artifacts/token_importance_probe/qwen_3b/ablation_records.csv` |
| 3B baseline records | `artifacts/token_importance_probe/qwen_3b/baseline_records.json` |
| 3B server log | `artifacts/token_importance_probe/qwen_3b/logs/llama_server.log` |
| 3B GPU monitor | `artifacts/token_importance_probe/qwen_3b/logs/nvidia_smi.csv` |
| Environment log | `artifacts/logs/env_probe.log` |
| 0.5B run log | `artifacts/logs/token_importance_probe_run.log` |
| 3B run log | `artifacts/logs/token_importance_probe_qwen3b_run.log` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T042048500155+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T042048500155+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T042048500155+0000/paper_manifest.json` |
