# Metadata-Conditioned Draft Length Prediction for Speculative Decoding: A Trace-Driven Tuning Study

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, evidence bundles, claim ledgers, metrics, and decision logs). The operator who released this artifact claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Speculative decoding accelerates autoregressive inference by drafting tokens on a small model and verifying them in parallel on a larger target model. The draft depth—the number of tokens generated before verification—governs a tradeoff between acceptance efficiency and parallelism. We investigate whether a simple metadata-conditioned mapping from task-domain labels to fixed draft depths can improve throughput and reduce wasted computation relative to a uniform deep-draft baseline, while preserving exact output quality. Using a trace-driven tuning benchmark constructed from 64 real-stack speculative decoding traces (Qwen2.5-0.5B-Instruct drafting for Qwen2.5-3B-Instruct, float32, 16 generated tokens per example), we tune a conservative domain-to-depth predictor subject to an acceptance-rate floor constraint (≥0.99× the accepted-tokens-per-verifier-call of fixed-depth-8). On all-data tuning, the predictor achieves +9.40% measured tokens/sec and −18.88% rejected draft tokens versus fixed-8, with zero output quality mismatches and zero accepted-per-call delta. In 500-seed repeated stratified half-train/half-test cross-validation, the held-out predictor achieves mean +11.99% tokens/sec (p5: +9.29%, p95: +15.06%) and mean −24.10% rejected tokens (p5: −30.24%, p95: −18.65%), at a mean −0.96% accepted-per-call tradeoff. These results support a bounded claim: on this corpus, metadata-conditioned draft-length selection can reduce waste and improve throughput while preserving exact output, but the modest corpus size (64 examples, 8 per domain) limits confidence, and revalidation on 128–256 fresh traces is recommended before production deployment.

---

## Introduction

Speculative decoding reduces the latency of autoregressive language model inference by using a small draft model to propose multiple candidate tokens, which a larger target model then verifies in parallel. The draft depth—the number of tokens the draft model generates before the target model performs a verification pass—is a key control parameter. A depth that is too shallow underutilizes the target model's parallel verification capacity; a depth that is too deep produces many rejected tokens whose computation is wasted.

The optimal draft depth depends on properties of the input. Some domains or task types yield higher acceptance rates and thus benefit from deeper drafts, while others are poorly suited to speculative decoding at all. This suggests that a metadata-conditioned draft-length predictor—one that selects depth based on task-domain or other lightweight features available before inference begins—could outperform any single fixed depth.

This study asks: can a simple group-to-depth mapping, conditioned on metadata labels already available at inference time, improve speculative decoding throughput and reduce wasted computation relative to a uniform deep-draft baseline, while preserving output quality?

We approach this question conservatively. Rather than launching new inference runs, we reuse per-example trace data from a sibling experiment that already measured speculative decoding under multiple fixed depths (2, 4, 6, 8) and a domain-gated policy on 64 real-stack examples. This allows us to tune and evaluate a metadata-conditioned predictor in a trace-driven simulation with exact output-quality verification, at the cost of relying on a modest and previously collected corpus.

---

## Method

### Data Source

The input data consists of per-example speculative decoding traces copied from a sibling project. The source run evaluated speculative decoding with the following configuration:

- **Target/verifier model:** Qwen/Qwen2.5-3B-Instruct
- **Draft model:** Qwen/Qwen2.5-0.5B-Instruct
- **Precision:** float32
- **Examples:** 64 real-stack prompts, 16 generated target tokens each
- **Policies measured per example:** `target_only`, `fixed_2`, `fixed_4`, `fixed_6`, `fixed_8`, `sat_depth_domain_gate`
- **Metadata labels per example:** `domain`, `task_slice`, `waste_reason`

The source run used exact-reference validation: generated token IDs under each policy were compared against the `target_only` reference. The copied per-example CSV preserves these token IDs, enabling a local exact-output quality gate.

### Trace-Driven Simulation

Because the source traces contain per-example measurements for every fixed depth, any depth-assignment policy can be evaluated by looking up each example's metrics under the assigned depth. This is a trace-driven simulation: no new model inference is performed. The advantage is exact reproducibility and the ability to verify output quality; the limitation is that the policy space is restricted to the depths measured in the source traces (2, 4, 6, 8).

### Quality Gate

For every candidate depth assignment, the generated token IDs are verified against the `target_only` reference exactly. Any assignment producing a mismatch is rejected. In the final results, all evaluated policies (including the tuned predictor) produce zero quality mismatches.

### Tuning Procedure

The predictor maps each metadata group (domain, task_slice, or waste_reason) to one of the fixed depths {2, 4, 6, 8}. The tuning objective is:

1. **Maximize** measured tokens/sec (inner-loop throughput).
2. **Subject to:** accepted tokens per verifier call ≥ 0.99 × (accepted tokens per verifier call under `fixed_8`) on the training set.

This constraint ensures the predictor does not sacrifice acceptance efficiency beyond a 1% tolerance relative to the deepest baseline. The constraint is checked per group on the training fold; groups that cannot meet the floor at any depth shallower than 8 are assigned `fixed_8`.

### Evaluation Protocol

Two evaluation modes are reported:

1. **All-data tuning:** The predictor is tuned on all 64 examples and evaluated on the same 64 examples. This represents an upper bound on performance with perfect knowledge of the distribution.

2. **Repeated stratified cross-validation:** 500 random seeds, each with a stratified half-train/half-test split (32 train, 32 test). The predictor is tuned on the train fold and evaluated on the held-out test fold. Mean, 5th percentile, 50th percentile, and 95th percentile of per-seed metrics are reported.

All metrics are reported as percentage deltas relative to the `fixed_8` baseline on the same evaluation set.

### Implementation

The tuning script (`scripts/draft_length_predictor_tuning.py`) is dependency-free (Python standard library only). It parses the per-example CSV, applies the quality gate, enumerates candidate depth assignments per group under the acceptance constraint, and selects the assignment maximizing throughput. Cross-validation is stratified by domain.

---

## Results

### Quality Verification

All fixed-depth baselines and the domain-gate policy produce zero generated-token mismatches versus the `target_only` reference across all 64 examples. The tuned predictor likewise produces zero mismatches in both all-data and cross-validation settings. This confirms that, on this corpus, draft-depth selection does not alter output quality: every evaluated depth yields the same token sequence as target-only autoregressive decoding.

### Fixed-Depth Baselines vs. `fixed_8`

| Policy | Tokens/sec Δ | Rejected tokens Δ | Accepted/verifier Δ |
|---|---|---|---|
| `fixed_2` | +26.17% | −73.37% | −24.33% |
| `fixed_4` | +25.46% | −48.99% | −5.76% |
| `fixed_6` | +11.14% | −23.18% | −1.93% |
| `sat_depth_domain_gate` | +10.77% | −21.33% | −0.20% |

Shallow depths dramatically reduce rejected tokens and improve throughput but at a steep cost in accepted tokens per verifier call. The existing domain-gate policy from the source run achieves a favorable tradeoff close to `fixed_8` in acceptance rate. These baselines establish the tradeoff surface that the tuned predictor navigates.

### All-Data Tuned Predictor

The tuned domain-to-depth mapping (equivalent to task_slice and waste_reason mappings on this corpus due to one-to-one label alignment):

| Domain | Assigned Depth |
|---|---|
| coding | fixed_8 |
| formatting | fixed_8 |
| instruction_following | fixed_4 |
| knowledge | fixed_8 |
| long_context | fixed_6 |
| policy_style | fixed_4 |
| rag_robustness | fixed_8 |
| reasoning | fixed_8 |

Performance vs. `fixed_8`:

| Metric | Delta |
|---|---|
| Tokens/sec | +9.40% |
| Accepted/verifier | 0.00% |
| Rejected tokens | −18.88% |
| Quality mismatches | 0 |

The predictor assigns shallower depths to three domains (instruction_following → fixed_4, long_context → fixed_6, policy_style → fixed_4) where the acceptance rate is sufficiently high to meet the floor constraint, and retains `fixed_8` for the remaining five domains. The zero accepted-per-call delta indicates that the floor constraint is met exactly on the training data for all groups.

### Cross-Validation Results (500 seeds, domain-conditioned)

| Metric | Mean | p5 | p50 | p95 |
|---|---|---|---|---|
| Tokens/sec Δ | +11.99% | +9.29% | +12.00% | +15.06% |
| Rejected tokens Δ | −24.10% | −30.24% | −24.14% | −18.65% |
| Accepted/verifier Δ | −0.96% | −2.33% | −0.79% | 0.00% |
| Quality mismatches | 0 | — | — | — |

The held-out predictor consistently improves throughput and reduces rejected tokens across nearly all random splits. The accepted-per-call tradeoff is small in expectation (−0.96%) but can reach −2.33% in unfavorable splits, reflecting the fact that the 0.99 acceptance floor on training data does not perfectly transfer to held-out data. The 95th percentile of accepted-per-call delta is 0.00%, indicating that many splits incur no acceptance penalty at all. The same metrics hold for `task_slice` and `waste_reason` conditioning because the 64-example source corpus has one-to-one aligned labels across these three features.

---

## Limitations

1. **Corpus size.** The trace corpus contains only 64 examples (8 per domain). This is sufficient to demonstrate viability but insufficient for high-confidence production claims. The cross-validation variance reflects this: the 5th-to-95th percentile range for throughput delta spans +9.29% to +15.06%. Revalidation on 128–256 fresh traces is recommended.

2. **Trace-driven simulation, not live inference.** All results are derived from previously collected per-example traces. No new speculative decoding runs were performed in this project. The policy space is restricted to the four fixed depths measured in the source experiment. Dynamic or adaptive depth policies are not evaluated.

3. **Label alignment.** On this corpus, domain, task_slice, and waste_reason labels are one-to-one aligned, making the three conditioning features equivalent. In a larger corpus with many-to-one mappings, the features may yield different predictors, and this equivalence should not be assumed.

4. **Single model pair.** Results are specific to the Qwen2.5-0.5B/Qwen2.5-3B draft-target pair in float32. The optimal depth assignments and the viability of metadata conditioning may differ for other model pairs, precisions, or generation lengths.

5. **Short generation length.** Each example generates only 16 target tokens. The relative overhead of verification calls is higher for short sequences, and the throughput and acceptance metrics may not transfer directly to longer generations where warmup effects diminish.

6. **Conservative constraint.** The 0.99 acceptance floor was chosen conservatively. A less strict constraint would permit shallower depths and potentially higher throughput at greater acceptance cost. The full tradeoff surface was not exhaustively explored.

7. **No online adaptation.** The predictor is static: it maps metadata to a fixed depth before inference begins. It does not adapt during generation based on observed acceptance rates, which could further improve performance.

8. **Scope of claim.** The predictor is explicitly a throughput/waste tuning controller, not an accepted-tokens-per-call maximizer. The ~1% accepted-per-call tradeoff in held-out evaluation is a deliberate design consequence of the floor constraint, not an artifact.

---

## Reproducibility Checklist

- **Data availability:** The input trace (`data/real_depth_policy_per_example.csv`) and source summary (`data/source_real_depth_summary.json`) are present in the project directory, copied from the sibling project.
- **Code availability:** The tuning script (`scripts/draft_length_predictor_tuning.py`) is dependency-free (Python standard library only) and can be re-executed without GPU or external packages.
- **Random seeds:** 500 cross-validation seeds were used for the final run; the script accepts a `--seeds` argument for reproducibility.
- **Execution logs:** Smoke run log (`logs/smoke_20260502T014607Z.log`) and final run log (`logs/final_20260502T014607Z.log`) are preserved.
- **Metrics artifacts:** `results/smoke_metrics.json` and `results/final_metrics.json` contain the full numeric results.
- **Quality gate:** Exact token-ID matching against `target_only` reference is performed in-script; all evaluated policies pass with zero mismatches.
- **Hardware:** No GPU or live inference was required; all computation is trace-driven on CPU.
- **Stratification:** Cross-validation splits are stratified by domain to preserve class proportions.

---

## Conclusion

On a 64-example real-stack speculative decoding trace corpus (Qwen2.5-0.5B drafting for Qwen2.5-3B, float32, 16 tokens per example), a metadata-conditioned draft-length predictor tuned under a conservative acceptance-rate floor achieves meaningful throughput improvements (+9.40% all-data, +11.99% CV mean) and rejected-token reductions (−18.88% all-data, −24.10% CV mean) relative to a uniform fixed-8 baseline, while preserving exact output quality. The accepted-tokens-per-verifier-call tradeoff is zero on all-data tuning and approximately −1% in held-out cross-validation.

These results support a bounded claim: metadata-conditioned draft-length selection is viable as a conservative throughput and waste-reduction controller for speculative decoding. The predictor is not an accepted-tokens-per-call maximizer; it explicitly trades a small acceptance efficiency margin for throughput and waste reduction.

The primary limitation is corpus size. Before production deployment, the tuned mapping should be revalidated on 128–256 fresh traces, and the `fixed_8` fallback should be retained for any domain or task type that cannot meet the acceptance floor. The trace-driven methodology itself—tuning depth assignments offline from per-example multi-depth traces before deploying them online—is a practical approach that avoids costly online search and can be repeated whenever new trace data becomes available.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Tuning script | `scripts/draft_length_predictor_tuning.py` |
| Input per-example trace | `data/real_depth_policy_per_example.csv` |
| Source run summary | `data/source_real_depth_summary.json` |
| Smoke run log | `logs/smoke_20260502T014607Z.log` |
| Final run log | `logs/final_20260502T014607Z.log` |
| Smoke metrics | `results/smoke_metrics.json` |
| Final metrics | `results/final_metrics.json` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T014248693641+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T014248693641+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T014248693641+0000/paper_manifest.json` |
