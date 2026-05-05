# Citation-Mode Speculation: Mode-Aware Draft Depth Control for Speculative Decoding

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated these claims.

---

## Abstract

Speculative decoding accelerates autoregressive inference by drafting multiple tokens in parallel and verifying them against a larger model. We investigate whether mode-aware draft depth control—reducing speculative draft depth near citation and exact-quote spans while raising it elsewhere—can reduce wasted draft computation without degrading output quality. In a controlled simulator modeling speculative verifier semantics across 50 trials of 1,000 synthetic documents each, the citation-mode policy reduced wasted draft tokens by 21.99% relative to a fixed-depth-5 baseline while preserving exact verification quality. However, the same policy was 1.22% slower than fixed depth 5 in modeled throughput (0.988× relative speedup), trading fewer wasted tokens for more frequent verifier calls. An entropy-proxy policy and an oracle-expected policy both outperformed citation-mode on throughput (1.014× and 1.043× vs. fixed depth 5, respectively) while also reducing waste. These results indicate that citation-aware gating is viable as a waste-reduction policy hook but does not, on its own, improve throughput over a well-tuned fixed depth in the simulated cost model. Validation on a live speculative decoder with real LLM hardware remains necessary before drawing production conclusions.

## Introduction

Speculative decoding reduces the latency of autoregressive inference by using a small draft model to propose multiple candidate tokens, which a larger verifier model then accepts or rejects in a single forward pass. The draft depth—the number of tokens proposed per verification call—is a key parameter: deeper drafts amortize verification cost over more tokens but risk higher rejection rates when the draft model diverges from the verifier.

In grounded generation tasks, certain output spans—citations, exact quotes, and factual claims—carry higher risk of draft-verifier mismatch because the correct continuation is tightly constrained by source material. We hypothesize that reducing draft depth near these high-risk spans and increasing it elsewhere could reduce wasted draft computation (tokens generated but subsequently rejected) without sacrificing accepted-token throughput or output quality.

This paper reports on a simulation-based investigation of this hypothesis. We compare four draft-depth policies—fixed depth, citation-mode gating, entropy-proxy gating, and an oracle-expected policy—within a controlled simulator that models speculative verifier acceptance semantics. We report both positive and negative findings with full transparency about the simulator's limitations relative to real LLM hardware.

## Method

### Simulator Design

We implemented a controlled simulator (`scripts/citation_mode_speculation_sim.py`) that models speculative decoding with exact verifier semantics. The simulator generates synthetic document sequences containing interspersed citation and exact-quote spans, then applies draft-depth policies to determine how many tokens the draft model proposes per verification call. Verification follows standard speculative decoding: the verifier accepts the longest prefix of draft tokens that matches its own distribution, rejecting the remainder.

The simulator does not invoke a real language model. Draft acceptance rates are modeled based on span-type assumptions: citation and exact-quote spans are assigned lower draft-acceptance probabilities, while free-text spans receive higher acceptance probabilities. This abstraction enables controlled comparison of policies but does not capture the full distributional complexity of real LLM outputs, nor does it reflect hardware-specific latency characteristics.

### Draft-Depth Policies

Four policies were evaluated:

1. **Fixed Depth 5 (`fixed_5`)**: Proposes exactly 5 draft tokens per verification call. Serves as the primary baseline.

2. **Citation-Mode (`citation_mode`)**: Reduces draft depth (to a lower fixed value) when the next output position falls within a detected citation or exact-quote span; raises draft depth elsewhere. This is the proposed intervention.

3. **Entropy-Proxy (`entropy_proxy`)**: Adjusts draft depth based on a proxy for token-level entropy, without explicit citation awareness. Serves as an alternative adaptive baseline.

4. **Oracle-Expected (`oracle_expected`)**: Adjusts draft depth using oracle knowledge of expected acceptance rates per span. Represents an upper bound on what mode-aware policies could achieve with perfect information.

### Cost Model

Modeled throughput is computed as `tokens_per_time = output_tokens / (verifier_calls + draft_tokens × draft_cost_factor)`, where `draft_cost_factor` reflects the relative cost of generating a draft token versus running the verifier. The specific cost factor values are embedded in the simulator and represent a single point in the design space; results are sensitive to this parameter, and different hardware configurations could alter the relative ranking of policies.

### Experimental Setup

Each policy was run for 50 independent trials, each processing 1,000 synthetic documents. All policies operated on identical document sequences (mean 98,930.2 tokens per trial), ensuring fair comparison. Metrics were aggregated across trials with standard deviations reported where available.

### Pre-Registered Success Criteria

Success criteria were defined prior to running the full evaluation:

- **Throughput vs. no speculation**: Citation-mode must exceed 1.0× the no-speculation baseline.
- **Throughput vs. fixed depth 5**: Citation-mode must exceed 1.0× the fixed-depth-5 baseline.
- **Waste reduction vs. fixed depth 5**: Citation-mode must reduce wasted draft tokens relative to fixed depth 5.
- **Equal quality**: Output quality must be preserved. In the simulator, this is guaranteed by exact verifier semantics; no real LLM quality measurement was performed.

## Results

### Primary Metrics

| Metric | Citation-Mode | Fixed Depth 5 | Entropy-Proxy | Oracle-Expected |
|---|---|---|---|---|
| Verifier calls (mean) | 41,836.38 | 35,869.26 | 38,691.64 | 36,693.08 |
| Draft tokens (mean) | 115,121.48 | 176,312.74 | 135,619.02 | 142,681.42 |
| Accepted draft tokens (mean) | 57,786.30 | 63,747.70 | 60,955.56 | 62,925.68 |
| Wasted draft tokens (mean) | 57,335.18 | 112,565.04 | 74,663.46 | 79,755.74 |
| Accepted drafts per call (mean) | 1.381 | 1.777 | 1.575 | 1.715 |
| Output tokens per call (mean) | 2.365 | 2.758 | 2.557 | 2.696 |
| Waste ratio (mean) | 0.498 | 0.638 | 0.551 | 0.559 |
| Modeled throughput (mean) | 1.956 | 1.980 | 2.009 | 2.065 |
| Modeled throughput (stdev) | 0.00514 | 0.00609 | 0.00580 | 0.00598 |
| Speedup vs. no speculation | 1.956× | 1.980× | 2.009× | 2.065× |
| Speedup vs. fixed depth 5 | 0.988× | 1.000× | 1.014× | 1.043× |
| Waste reduction vs. fixed depth 5 | 21.99% | 0.00% | 13.77% | 12.45% |

### Success Criteria Outcomes

- **Throughput vs. no speculation**: **Passed.** Citation-mode achieved 1.956× speedup over the no-speculation baseline.
- **Throughput vs. fixed depth 5**: **Failed.** Citation-mode achieved 0.988× the throughput of fixed depth 5, a 1.22% deficit.
- **Waste reduction vs. fixed depth 5**: **Passed.** Citation-mode reduced wasted draft tokens by 21.99%.
- **Equal quality**: **Conditionally preserved.** Exact verifier semantics in the simulator guarantee output equivalence. No real LLM quality benchmark was conducted.

### Interpretation of the Negative Throughput Result

The citation-mode policy reduced draft depth near high-risk spans, which decreased the number of draft tokens generated per call but increased the number of verification calls required (41,836 vs. 35,869 for fixed depth 5, a 16.6% increase). Under the simulator's cost model, the additional verification calls were more expensive than the saved draft tokens, resulting in a net throughput loss of 1.22%. This represents a genuine trade-off: citation-mode gating converts draft-compute waste into verification-call overhead.

The entropy-proxy and oracle-expected policies both achieved modest throughput gains over fixed depth 5 (1.4% and 4.3%, respectively) while also reducing waste (13.77% and 12.45%, respectively). This suggests that smoother adaptive policies may better navigate the draft-depth vs. verification-call trade-off than the binary citation-mode gate. Notably, the oracle-expected policy—despite having perfect information about acceptance rates—achieved only a 4.3% throughput gain, indicating that the room for improvement over fixed depth 5 may be modest under this cost model.

### Waste Reduction Analysis

Citation-mode achieved the largest waste reduction (21.99%) but at the highest cost in verifier calls. The waste ratio (wasted tokens / total draft tokens) dropped from 0.638 (fixed depth 5) to 0.498 (citation-mode), meaning that roughly half of all draft tokens were still wasted even under citation-mode gating. The entropy-proxy and oracle-expected policies achieved intermediate waste reductions with better throughput outcomes, suggesting that the citation-mode policy over-constrains draft depth near citation spans relative to what is optimal for throughput.

## Limitations

1. **Simulator-only evidence.** All results derive from a controlled simulator, not from a live speculative decoder running on real LLM hardware. The simulator's acceptance-rate model, span-type assignments, and cost model are simplifications. Real LLM acceptance rates depend on the specific draft and verifier models, the prompt distribution, and hardware-specific latency characteristics that the simulator does not capture. These results should be treated as toy simulation evidence, not as production validation.

2. **Cost model sensitivity.** The modeled throughput metric depends on the ratio of draft-token cost to verification-call cost. Different hardware configurations (e.g., CPU-bound vs. GPU-bound draft models, memory-bandwidth-limited verification) would alter this ratio and potentially change the relative ranking of policies. The 1.22% throughput deficit of citation-mode is within the range where cost-model assumptions could reverse the conclusion.

3. **No quality measurement on real outputs.** The simulator guarantees output quality by construction (exact verifier semantics). On real LLMs, adaptive draft-depth policies could interact with sampling strategies, temperature, or top-p in ways that affect output distribution. This risk is unmeasured.

4. **Binary citation detection.** The citation-mode policy uses a binary in-span / out-of-span decision. Real citation detection in LLM outputs is noisy; false positives would unnecessarily reduce draft depth, and false negatives would fail to protect high-risk spans. The simulator does not model detection errors.

5. **Single draft-depth configuration.** The simulator tests one pair of draft-depth values (reduced near citations, elevated elsewhere). The optimal depth schedule was not searched, and the oracle-expected results suggest room for improvement with better-tuned depth schedules.

6. **Synthetic document distribution.** The 1,000 documents per trial are synthetically generated with controlled citation/quote frequencies. Real workloads may have different span-type distributions, potentially changing the magnitude or direction of the waste-reduction effect.

7. **No energy or hardware utilization data.** The 21.99% waste reduction translates to fewer FLOPs on draft-model forward passes, but without hardware measurements, the energy savings claim remains theoretical.

8. **Empty claim ledger.** The project's claim ledger (`claim_ledger.json`) contains no structured claims and has audit status `blocked_empty_claims`. This draft should not be treated as having passed a strict claim/evidence audit.

9. **Random seeds not recorded.** Exact numeric reproducibility may be affected by the absence of explicitly recorded random seeds in the available artifacts.

## Reproducibility Checklist

| Item | Status |
|---|---|
| Code availability | Simulator source `scripts/citation_mode_speculation_sim.py` and summarization script `scripts/summarize_results.py` are present in the project directory. |
| Data availability | All result files (`results/smoke_metrics.json`, `results/citation_mode_speculation_metrics.json`, `results/evidence_summary.md`) are present. Input data is synthetic and generated by the simulator. |
| Random seeds | Not explicitly recorded in the available artifacts. Exact numeric reproducibility may require seed specification. |
| Run logs | `logs/smoke-20260429T133347Z.log`, `logs/full-20260429T133424Z.log`, `logs/summary-20260429T133522Z.log` are available. |
| Decision record | `.omx/project_decision.json` contains the full decision, metrics, and success criteria. |
| Validation performed | JSON validation on `.omx/project_decision.json` and `results/citation_mode_speculation_metrics.json`; Python syntax check on both scripts. |
| Hardware requirements | Simulation runs are not hardware-dependent; no GPU or specific hardware configuration is required to reproduce these simulator results. |
| Statistical reporting | 50 trials per condition; means and one standard deviation reported for modeled throughput. No confidence intervals or hypothesis tests were computed. |
| Claim audit | Not passed. Claim ledger is empty with status `blocked_empty_claims`. |

## Conclusion

Citation-mode speculation—reducing draft depth near citation and exact-quote spans while raising it elsewhere—reduces wasted draft computation by 21.99% relative to a fixed-depth-5 baseline in a controlled simulator. However, this waste reduction comes at the cost of 1.22% lower modeled throughput, because the policy increases verification-call frequency more than it saves draft computation under the simulator's cost model.

The entropy-proxy and oracle-expected policies both outperformed citation-mode on throughput while also reducing waste, suggesting that smoother, entropy-informed adaptation may be preferable to binary citation gating as a standalone policy. The most promising path forward may be a hybrid approach that uses citation detection as one signal within a broader adaptive draft-depth controller, rather than as the sole gating mechanism.

These findings are simulator-only and have not been validated on a live speculative decoder with real LLM hardware. The throughput ranking of policies is sensitive to the cost model's draft-to-verification cost ratio, which varies across hardware configurations. We recommend implementing a lightweight lexical citation/exact-span risk hook in an existing speculative decoder as a draft-length cap, then conducting A/B tests across grounded QA, mixed chat, code-editing, and tool-output workloads with full hardware-level measurement before drawing production conclusions. If citation gating only shifts waste into more verifier calls without quality or energy benefits on real hardware, the approach should be abandoned for this use case.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Simulator script | `scripts/citation_mode_speculation_sim.py` |
| Summarization script | `scripts/summarize_results.py` |
| Smoke test metrics | `results/smoke_metrics.json` |
| Full run metrics | `results/citation_mode_speculation_metrics.json` |
| Evidence summary | `results/evidence_summary.md` |
| Project decision record | `.omx/project_decision.json` |
| Smoke run log | `logs/smoke-20260429T133347Z.log` |
| Full run log | `logs/full-20260429T133424Z.log` |
| Summary run log | `logs/summary-20260429T133522Z.log` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260429T132948325662+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T132948325662+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T132948325662+0000/paper_manifest.json` |
