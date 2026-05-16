# Verifier-Feature Acceptance Classifier for Adaptive Speculative Decoding Depth

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts (simulation logs, feature-signal probes, decision records). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated the claims herein.

---

## Abstract

Speculative decoding accelerates autoregressive inference by verifying draft tokens against a target model in a single forward pass. Fixed draft depths are suboptimal because acceptance rates vary across contexts. We investigate whether verifier-side (target-model) acceptance features can drive an adaptive draft-length policy that increases accepted draft tokens per verifier call over a fixed-depth baseline without degrading output distribution quality. In a controlled Markov-language speculative decoding simulator with exact rejection sampling, an online classifier using verifier feedback (Beta-posterior acceptance probabilities updated after a 400-call burn-in) increased accepted draft tokens per verifier call by 17.8% over a fixed K=4 baseline while preserving the target distribution (total variation distance 0.016–0.022). An oracle upper bound using full target-side information achieved a 25.6% improvement, confirming headroom for richer verifier features. However, the throughput gain came at the cost of a 59.0% increase in wasted draft compute (rejected draft tokens per accepted token), revealing a tradeoff: maximizing accepted tokens per call incentivizes longer drafts that increase wasted FLOPs. A draft-entropy heuristic reduced waste by 19.5% but decreased accepted tokens per call by 41.0%. A feature-signal probe on 80,000 proposal labels confirmed that verifier-side acceptance probability is substantially more predictive of acceptance outcomes (AUC 0.979) than draft-only confidence signals (AUC 0.580). These results are limited to a toy Markov simulation and do not constitute validation on a real language model or hardware platform. We conclude that verifier-feature acceptance classification is a viable direction but that practical policies must optimize a hardware-aware cost model rather than accepted tokens per call alone.

## 1. Introduction

Speculative decoding reduces the latency of autoregressive inference by having a small draft model propose candidate tokens that a larger target model verifies in a single forward pass. The number of draft tokens proposed before each verification call—the draft depth K—is typically fixed. This is suboptimal because acceptance rates depend on local context: when the draft model closely approximates the target, longer drafts yield more accepted tokens per verification; when the approximation is poor, shorter drafts avoid wasting draft compute on tokens that will be rejected.

Prior work has recognized this limitation. PEARL proposes adaptive draft lengths and reports speedups over vanilla speculative decoding. AdaEDL motivates adaptive early stopping by noting that static draft lengths perform poorly under high acceptance-count variance, reporting 10–57% improvements. SVIP observes that oracle draft length varies significantly and uses draft entropy for dynamic length selection, achieving up to 17–22% speedups. Online Speculative Decoding and OnlineSPEC frame verification feedback as a no-extra-cost signal for online adaptation.

A common thread in this prior work is the use of draft-side features (e.g., draft entropy, draft confidence) to predict acceptance and adapt the draft depth. However, the verifier (target model) already computes the information needed to assess acceptance probability—specifically, the target token probabilities at each draft position. This verifier-side signal is available at no additional compute cost after each verification call and should, in principle, be far more informative about future acceptance than draft-side heuristics.

This paper investigates the hypothesis that a classifier trained on verifier-side acceptance features can drive an adaptive draft-length policy that improves accepted draft tokens per verifier call over a fixed-depth baseline, without changing output quality. We conduct this investigation in a controlled setting—a dependency-free Markov-language speculative decoding simulator—to establish initial viability before committing to a full LLM implementation.

Our contributions are:

1. A controlled simulation demonstrating that an online verifier-feedback classifier improves accepted draft tokens per verifier call by 17.8% over fixed K=4, with an oracle upper bound of 25.6%.
2. A feature-signal probe quantifying the predictive gap between verifier-side and draft-side acceptance features (AUC 0.979 vs. 0.580).
3. An honest characterization of the throughput–waste tradeoff: the same policy that increases accepted tokens per call also increases wasted draft compute by 59.0%, indicating that practical deployment requires hardware-aware optimization rather than optimization of accepted tokens per call alone.

## 2. Method

### 2.1 Simulator Design

We implemented a dependency-free Markov-language speculative decoding simulator that performs exact rejection sampling with residual token sampling on rejection. The simulator models a draft–target pair as Markov chains over a shared vocabulary, with the target chain defining the true distribution and the draft chain defining the proposal distribution. Exact rejection sampling guarantees that the output distribution matches the target distribution by construction, regardless of the draft policy.

### 2.2 Policies Compared

Four draft-length policies were evaluated:

- **fixed_k4.** Fixed draft depth K=4. This is the baseline.
- **draft_entropy_adaptive.** A draft-only heuristic that selects K from {1, 2, 4, 7, 8} based on draft token entropy/confidence. This represents the draft-side adaptive approach used in prior work.
- **online_verifier_feature_classifier.** An online classifier that maintains a Beta posterior over acceptance probabilities for each candidate draft length, updated from verifier acceptance labels after a 400-call burn-in period. During burn-in, the policy defaults to K=4. After burn-in, it selects K from {1, 2, 4, 7, 8} to maximize expected accepted tokens per verifier call. This is the primary experimental condition.
- **oracle_target_feature_upper_bound.** An oracle policy with access to the true target–draft probability overlap at each position, selecting K to maximize accepted tokens per call. This represents the theoretical upper bound on verifier-feature-driven adaptation.

### 2.3 Feature-Signal Probe

A separate probe generated 80,000 proposal labels from the same Markov-pair generator and evaluated the predictive quality of six acceptance scores:

- **draft_token_prob.** Draft model probability assigned to the proposed token.
- **draft_state_max_prob.** Maximum probability in the draft model's next-token distribution.
- **neg_draft_entropy.** Negative entropy of the draft model's next-token distribution (a confidence measure).
- **target_token_prob.** Target model probability assigned to the proposed token.
- **verifier_state_overlap.** Overlap between target and draft next-token distributions.
- **verifier_token_accept_prob.** True acceptance probability derived from target and draft probabilities.

For each score, we computed the area under the ROC curve (AUC) and the Brier score (with rescaled Brier for calibration assessment).

### 2.4 Experimental Protocol

The main experiment ran 16 independent seeds, each generating 8,000 tokens via exact speculative rejection sampling. Metrics were aggregated across seeds. Quality was verified by comparing the unigram distribution of target-only sampling against speculative sampling, measured by total variation distance over three 50,000-token checks.

The feature-signal probe ran once on 80,000 proposal labels.

### 2.5 Environment

Experiments were conducted on a host running Linux 6.17.0-1014-nvidia (aarch64) with 121 GiB RAM and an NVIDIA GB10 GPU (idle during experiments; no GPU computation was used). Swap was intentionally disabled. Python 3.12.3 was used. No ML frameworks (PyTorch, Transformers, scikit-learn, NumPy) were installed; the simulator and probe are pure-Python with no external dependencies.

## 3. Results

### 3.1 Main Experiment: Accepted Tokens per Verifier Call

Table 1 summarizes the primary metrics across 16 seeds (8,000 tokens each).

**Table 1.** Speculative decoding metrics by policy (16 seeds, 8,000 tokens/seed).

| Policy | Accepted tokens / verifier call | Δ vs fixed K=4 | Wasted draft / accepted | Wasted Δ vs fixed | Mean K |
|---|---:|---:|---:|---:|---:|
| fixed_k4 | 2.198 | 0.0% | 0.821 | 0.0% | 4.000 |
| draft_entropy_adaptive | 1.296 | −41.0% | 0.661 | −19.5% | 2.156 |
| online_verifier_feature_classifier | 2.590 | +17.8% | 1.304 | +59.0% | 5.966 |
| oracle_target_feature_upper_bound | 2.761 | +25.6% | 1.422 | +73.4% | 6.686 |

The online verifier-feature classifier achieved the primary success criterion (≥15% improvement in accepted tokens per verifier call), with a 17.8% gain over fixed K=4. The oracle upper bound confirms substantial headroom (25.6%), suggesting that richer verifier features beyond the online Beta posterior could yield further gains.

However, the throughput improvement came with a significant cost: wasted draft compute (rejected draft tokens per accepted token) increased by 59.0%. The policy achieved its gains primarily by selecting longer drafts (mean K=5.966 vs. K=4 for the baseline), which increases the expected number of accepted tokens per call but also increases the number of wasted tokens when rejection occurs early in the draft sequence.

The draft-entropy adaptive policy illustrates the opposite tradeoff: it reduced wasted compute by 19.5% but at the cost of a 41.0% reduction in accepted tokens per call, as it selected shorter drafts (mean K=2.156) that were too conservative.

Neither adaptive policy simultaneously improved throughput and reduced waste relative to the fixed baseline.

### 3.2 Quality Verification

The total variation distance between the unigram distribution of target-only sampling and speculative sampling was 0.016–0.022 across three 50,000-token checks. This is consistent with finite-sample noise for an algorithm that samples residual tokens on rejection and preserves the target distribution by construction. No quality degradation was observed.

### 3.3 Feature-Signal Probe

Table 2 reports the predictive quality of draft-side versus verifier-side acceptance scores on 80,000 proposal labels.

**Table 2.** Feature-signal probe results (80,000 proposal labels).

| Score | AUC | Brier / rescaled Brier |
|---|---:|---:|
| draft_token_prob | 0.437 | 0.648 |
| draft_state_max_prob | 0.510 | 0.476 |
| neg_draft_entropy | 0.580 | 0.484 |
| target_token_prob | 0.851 | 0.625 |
| verifier_state_overlap | 0.671 | 0.163 |
| verifier_token_accept_prob | 0.979 | 0.049 |

Draft-only scores performed poorly as acceptance predictors. The best draft-side score (neg_draft_entropy) achieved AUC 0.580—barely above chance. Draft_token_prob was below chance (AUC 0.437), indicating that high draft probability is a poor proxy for target acceptance in this setting.

Verifier-side scores were substantially more predictive. Target_token_prob achieved AUC 0.851, and the true verifier token acceptance probability achieved AUC 0.979 with a Brier score of 0.049, indicating near-perfect calibration. Verifier_state_overlap (AUC 0.671) was also more predictive than any draft-side score.

These results support the premise that verifier-side features carry substantially more information about acceptance outcomes than draft-side heuristics in this controlled Markov setting. The degree to which this gap persists in real transformer-based LLMs remains an open question.

## 4. Limitations

1. **Toy simulation only.** All results come from a Markov-language simulator, not a real language model. The simulator models verifier features as probability-derived signals rather than actual hidden activations. The degree to which these findings transfer to transformer-based LLMs with real hidden states, attention patterns, and vocabulary distributions is unknown.

2. **No hardware cost model.** Accepted tokens per verifier call is a proxy for throughput, not a direct measurement. Real throughput depends on target verification cost as a function of K, draft cost as a function of K, kernel overhead, batching effects, sequence length, and the draft/target FLOP ratio. The 17.8% improvement in accepted tokens per call does not translate directly to a 17.8% improvement in tokens per second.

3. **Waste–throughput tradeoff unresolved.** The online classifier increased wasted draft compute by 59.0%. Whether this waste is acceptable depends on the relative cost of draft FLOPs versus target FLOPs, which varies by hardware and model configuration. The secondary success criterion of ≥20% reduction in wasted draft compute was not met.

4. **Burn-in period.** The online classifier requires 400 verification calls before adaptation begins. During this period, it defaults to fixed K=4. The sensitivity of results to this burn-in length was not evaluated.

5. **Single Markov-pair configuration.** The draft–target agreement level in the simulator determines baseline acceptance rates. Results may differ substantially at higher or lower agreement levels. Only one configuration was tested.

6. **No real LLM features.** The probe evaluates probability-derived signals, not hidden-state features (e.g., norm, margin, attention entropy) that would be available in a real transformer implementation. The predictive power of such features is untested.

7. **No direct comparison to prior adaptive methods.** The simulation does not implement PEARL, AdaEDL, or SVIP policies directly, so we cannot compare verifier-feature adaptation to these prior methods on equal footing.

8. **Claim audit incomplete.** The structured claim ledger for this artifact contains no extracted claims and its audit status is blocked. The quantitative results reported here are drawn directly from simulation output files and the project decision record, but have not passed a formal claim-evidence audit.

## 5. Reproducibility Checklist

- **Code availability:** The main simulation script and feature probe are dependency-free pure Python. No external packages are required.
- **Random seeds:** 16 independent seeds were used for the main experiment. Per-seed metrics are recorded in `results/spec_acceptance_classifier/per_seed_metrics.csv`.
- **Hardware:** Experiments ran on aarch64 Linux 6.17.0-1014-nvidia, 121 GiB RAM, NVIDIA GB10 GPU (idle; no GPU computation used), swap disabled.
- **Software:** Python 3.12.3, no ML frameworks installed.
- **Aggregate metrics:** `results/spec_acceptance_classifier/summary.json`
- **Per-seed metrics:** `results/spec_acceptance_classifier/per_seed_metrics.csv`
- **Feature probe results:** `results/spec_acceptance_classifier/feature_signal_probe.json`
- **Execution logs:** `logs/spec_acceptance_classifier_sim.log`, `logs/feature_signal_probe.log`
- **System probe:** `.omx/system_probe.log`
- **Exact commands:** Recorded in run notes (see Referenced Artifacts).

## 6. Conclusion

We presented evidence from a controlled Markov-language simulation that verifier-side acceptance features can drive an adaptive speculative decoding depth policy, improving accepted draft tokens per verifier call by 17.8% over a fixed K=4 baseline while preserving the target output distribution. An oracle upper bound of 25.6% confirms headroom for richer verifier features. A feature-signal probe demonstrated that verifier-side acceptance probability (AUC 0.979) is substantially more predictive of acceptance outcomes than draft-side heuristics (AUC 0.580), supporting the premise that verifier feedback is an underutilized signal for draft-depth adaptation.

However, the results also reveal a tradeoff that tempers this conclusion: the throughput-oriented adaptive policy increased wasted draft compute by 59.0%, as it achieved its gains primarily by selecting longer drafts. The draft-entropy heuristic reduced waste but at a severe throughput cost (−41.0% accepted tokens per call). Neither policy simultaneously improved throughput and reduced waste. This indicates that practical deployment cannot optimize accepted tokens per verifier call in isolation; it must optimize a hardware-aware objective that accounts for the relative cost of draft FLOPs, target FLOPs, and verification overhead.

These findings are limited to a toy simulation and do not constitute validation on a real language model or hardware platform. The next stage of validation should implement verifier-feature logging in an actual speculative decoding stack, train a classifier on real target logits and hidden-state features, and evaluate a hardware-cost-aware depth policy against fixed and draft-heuristic baselines on mixed chat/code/tool prompts, measuring end-to-end tokens per second as the primary metric.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| System probe log | `.omx/system_probe.log` |
| Main simulation script | `scripts/spec_acceptance_classifier_sim.py` |
| Feature probe script | `scripts/feature_signal_probe.py` |
| Aggregate summary | `results/spec_acceptance_classifier/summary.json` |
| Per-seed metrics | `results/spec_acceptance_classifier/per_seed_metrics.csv` |
| Feature signal probe results | `results/spec_acceptance_classifier/feature_signal_probe.json` |
| Main experiment log | `logs/spec_acceptance_classifier_sim.log` |
| Feature probe log | `logs/feature_signal_probe.log` |
| Project decision record | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260428T205012644113+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260428T205012644113+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260428T205012644113+0000/paper_manifest.json` |
