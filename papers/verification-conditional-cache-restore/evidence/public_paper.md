# Verification-Conditional Cache Restore: A Synthetic Policy Evaluation

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, benchmark outputs, and sweep logs). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

Large-language-model inference over long contexts demands substantial key-value (KV) cache memory. Offloading or compressing KV state reduces on-device footprint but can degrade answer quality when answer-critical spans are affected. We propose Verification-Conditional Cache Restore (VCCR): a policy that keeps most KV state compressed or offloaded, then restores only those spans flagged by an online verifier when answer confidence is low. We evaluate VCCR through a deterministic synthetic benchmark modeling long-document QA as a set of context spans where each answer requires a subset of evidence spans. Across 32 configurations varying compression bit width, verifier sensitivity, and verifier specificity, 8 configurations met the target criterion of ≥30% peak KV reduction at ≤2 F1-quality-loss points. The best low-thrash configuration achieved 83.5% peak KV reduction with 1.38 F1 quality-loss points and a 1.10× latency proxy. However, success was strongly conditional on high verifier sensitivity (≥0.97); at sensitivity 0.70, quality loss ranged from approximately 10.7 to 13.1 F1 points, far outside the success gate. These results validate the policy mechanism in simulation but do not constitute validation under real attention kernels, KV block layouts, or production serving stacks.

---

## Introduction

KV cache memory is a dominant cost in long-context LLM inference. Methods for reducing on-device memory pressure—including KV cache offloading, compression, quantization, and eviction—have received growing attention. However, context-intensive workloads expose accuracy degradation in current offloading methods, partly attributable to unreliable salience heuristics and low-rank key projection artifacts.

The core difficulty is that static or offline salience estimates are noisy: spans deemed unimportant a priori may be answer-critical for a specific query. A policy that compresses or offloads based solely on such priors risks irreversible quality loss on the spans that matter most for the given question.

VCCR addresses this by introducing an online verification gate. Rather than restoring spans based on static salience, the policy starts with KV state compressed or offloaded, probes answer confidence with a verifier or self-check, and restores only those spans the verifier flags as potentially missing. The hypothesis is that this conditional restore can achieve substantial KV footprint reduction while limiting quality loss to a narrow band, provided the verifier has sufficiently high recall on answer-critical evidence.

The target criterion for this study, drawn from the project specification, is: ≥30% lower KV footprint or offload traffic at ≤2 F1-quality-loss points, or equal quality with ≥10% lower latency.

This paper reports results from a synthetic policy simulation only. No real LLM inference, GPU execution, or serving-stack integration was performed. The results characterize the dynamics of the VCCR policy logic under controlled parameter variation; they do not characterize VCCR's behavior under real attention patterns, actual KV block management, or hardware memory hierarchies.

---

## Method

### Policy Definitions

Four policies are compared in a controlled synthetic environment:

1. **full_fp16**: No compression or offloading. Serves as the quality upper bound with full primary KV footprint (4,096 normalized bytes).
2. **uniform_compress**: All spans compressed uniformly at a given bit width, with no online restoration. Peak KV equals the compressed footprint.
3. **static_salience_pin**: A noisy offline salience prior is used to pin a subset of spans in primary memory; no online correction occurs. Peak KV equals the pinned subset plus compressed remainder.
4. **verification_conditional_restore (VCCR)**: All spans start compressed. An online verifier probes answer confidence. Spans flagged by the verifier are restored from secondary storage up to a cap, after which the answer is produced. Peak KV equals the compressed baseline plus restored spans.

### Synthetic Benchmark Model

The benchmark models a long-document QA request as a set of $N$ context spans. Each answer requires $k$ evidence spans drawn from the full set. A compressed span may decode incorrectly with probability determined by compression bit width and case difficulty. The verifier is modeled as a binary classifier with two configurable parameters:

- **Sensitivity** (recall on answer-critical spans): the probability that the verifier flags a span that is genuinely answer-critical.
- **Specificity** (true negative rate on non-critical spans): the probability that the verifier correctly does not flag a non-critical span.

This is a policy-logic simulation. It captures the dynamics of restore decisions, verifier errors, and compression-induced quality loss, but it does not model real attention patterns, KV block layouts, GPU memory hierarchies, PCIe/NVLink transfer costs, or actual token generation.

### Measured Metrics

- **Exact match proxy** and **F1 proxy**: quality measures derived from the span-oracle model.
- **Quality loss vs. full_fp16**: difference in F1 points from the uncompressed upper bound.
- **Peak primary KV bytes**: maximum normalized KV bytes resident in primary memory at any point during a request.
- **Primary KV bytes**: baseline normalized KV bytes (compressed footprint, excluding restores).
- **Restore traffic**: mean number of restored spans per request.
- **Latency proxy**: normalized scalar relative to full_fp16, derived from restore counts.
- **Thrash rate**: fraction of restored spans that were not answer-critical (i.e., unnecessary restores driven by verifier false positives).
- **Verifier miss rate**: fraction of answer-critical spans not flagged by the verifier (i.e., verifier false negatives on critical evidence).

### Experimental Procedure

A smoke test was run first (100 trials, 512 spans) to confirm script correctness and negligible memory risk. A calibrated parameter sweep then covered 32 configurations:

- Compression bits: {2, 3, 4, 6}
- Verifier sensitivity: {0.70, 0.82, 0.90, 0.97}
- Verifier specificity: {0.90, 0.96}

Each configuration ran 20,000 trials over 4,096 spans. The sweep completed in 8.19 seconds wall time with 24,636 kB maximum RSS and zero swap events.

### Environment

- Host: Linux 6.17.0-1014-nvidia, aarch64
- CPU: 20 ARM cores (Cortex-X925 + Cortex-A725)
- Python: 3.12.3
- Available memory: ~116 GiB at start; swap intentionally disabled (SwapTotal: 0 kB)
- All runs were CPU-only; no GPU inference was performed

---

## Results

### Smoke Test

The smoke test (100 trials, 512 spans) completed in approximately 0.04 seconds with 14,900 kB max RSS and zero swap events. VCCR improved F1 from 0.6022 (uniform compression) and 0.7502 (static salience pinning) to 0.8693, at the same peak primary KV bytes as static pinning (116 normalized bytes vs. 512 for full_fp16). This confirmed that the simulation was functional and memory-safe for the larger sweep.

### Parameter Sweep: Success Configurations

Of 32 configurations, 8 met the target criterion of ≥30% peak KV reduction at ≤2 F1-quality-loss points. An additional 2 configurations fell within ≤3 quality-loss points.

The best low-thrash success configuration is summarized in Table 1.

**Table 1.** Best low-thrash success configuration (2-bit compression, verifier sensitivity 0.97, specificity 0.96).

| Metric | Value |
|---|---:|
| VCCR F1 | 0.9862 |
| Uniform compress F1 | 0.5605 |
| Static salience pin F1 | 0.7241 |
| VCCR exact match | 0.9190 |
| Quality loss vs. full_fp16 | 1.38 F1 points |
| Peak KV reduction vs. full_fp16 | 83.52% |
| Primary KV bytes | 512 / 4096 normalized |
| Peak KV bytes | 675 / 4096 normalized |
| Mean restored spans/request | 4.24 |
| Latency proxy | 1.10× |
| Thrash rate | 0.22 |
| Verifier miss rate | 0.026 |

Other success configurations spanned 2-, 3-, 4-, and 6-bit compression, all at verifier sensitivity 0.97. Peak KV reduction across these configurations ranged from 58.5% to 83.5%, with quality loss from 0.87 to 1.38 F1 points. In all success configurations, VCCR substantially outperformed both uniform compression and static salience pinning in absolute F1.

### Parameter Sweep: Failure Evidence

At verifier sensitivity 0.70, VCCR still outperformed uniform compression and static salience pinning in absolute F1, but quality loss versus full_fp16 ranged from approximately 10.7 to 13.1 F1 points—far outside the ≤2-point success gate. The worst observed configuration is summarized in Table 2.

**Table 2.** Worst-case configuration (2-bit compression, verifier sensitivity 0.70, specificity 0.90).

| Metric | Value |
|---|---:|
| VCCR F1 | 0.8692 |
| Quality loss vs. full_fp16 | 13.08 F1 points |
| Thrash rate | 0.583 |
| Verifier miss rate | 0.254 |
| Peak KV reduction vs. full_fp16 | 83.52% |

This confirms that VCCR's viability is conditional on high verifier recall. A low-recall verifier causes the policy to miss answer-critical spans, and the resulting quality loss cannot be compensated by the restore mechanism. The peak KV reduction remains high even in failure cases (because compression is aggressive and few restores occur), but this is meaningless if quality is unacceptable.

### Role of Verifier Specificity

Verifier specificity primarily controlled restore thrash and latency. At sensitivity 0.97, increasing specificity from 0.90 to 0.96 roughly halved the thrash rate in success configurations, with modest effect on quality. Low specificity increases unnecessary restores, raising both traffic and latency without quality benefit. At low sensitivity (0.70), specificity had less practical impact because the dominant failure mode was verifier miss rate rather than thrash.

### Summary of Sensitivity Dependence

The sweep reveals a sharp sensitivity threshold. At sensitivity 0.97, 8 of 8 configurations (across all bit widths and specificities) met the ≤2-point quality-loss gate. At sensitivity 0.90, quality loss exceeded 2 points. At sensitivity 0.70, quality loss exceeded 10 points in all configurations. This suggests that the VCCR policy has a narrow operating envelope: it requires a verifier with very high recall on answer-critical evidence to deliver its promised quality–footprint tradeoff.

---

## Limitations

1. **Synthetic benchmark only.** The simulation models policy dynamics but does not exercise real attention kernels, KV block layouts, GPU memory hierarchies, or actual LLM token generation. The F1 and exact-match proxies are derived from a span-oracle model, not from real model outputs. The results characterize whether the policy logic is internally consistent and potentially viable, not whether it works in practice.

2. **Verifier model is idealized.** The verifier is parameterized as a binary classifier with fixed sensitivity and specificity, independent of span content, compression level, or query context. Real verifiers (e.g., self-check loops, consistency probes, entailment classifiers) may exhibit context-dependent error patterns, calibration drift, or interactions with compression that are not captured here.

3. **No real latency data.** The latency proxy is a normalized scalar derived from restore counts. It does not reflect actual TTFT, decode latency, PCIe/NVLink transfer costs, GPU scheduling effects, or the overhead of running a verifier inference step. The 1.10× latency proxy should not be interpreted as a measured latency overhead.

4. **Compression model is simplified.** Span decode failure probability is a function of bit width and case difficulty in the simulation. Real quantization or offloading may exhibit different or more complex failure modes, including correlated errors across adjacent spans or systematic biases not modeled here.

5. **Single workload type.** Only long-document QA with discrete evidence spans was modeled. Other workload types (summarization, multi-hop reasoning, code generation, agentic tool-use loops) may exhibit different restore dynamics, different verifier feasibility, or different sensitivity to compression-induced errors.

6. **No serving-stack integration.** The experiment does not integrate with TensorRT-LLM, vLLM, LMCache, or any production inference stack. Claims about implementability are based on API documentation review, not empirical integration. Whether the required block-priority, offload, and event APIs can be composed into a working VCCR implementation remains unvalidated.

7. **Conditional viability.** The central result—that VCCR can achieve large KV reduction with small quality loss—holds only when verifier sensitivity is very high (≥0.97 in this simulation). This is a demanding requirement whose feasibility on real workloads remains unvalidated. If real verifiers cannot achieve this recall level on answer-critical evidence, the policy will fail its quality gate despite functioning correctly as a mechanism.

8. **No claim audit passed.** The claim ledger for this artifact is in `blocked_empty_claims` status with no structured claims extracted. The numeric results reported here are drawn directly from the run notes and decision JSON but have not passed a formal claim-evidence audit.

---

## Reproducibility Checklist

- **Source code available:** `scripts/vccr_sim.py` (synthetic benchmark), `scripts/run_vccr_sweep.py` (sweep driver).
- **Deterministic execution:** The benchmark is deterministic given the same input parameters. No external random seeds were set beyond script defaults.
- **Environment recorded:** Full system telemetry captured in `logs/environment.txt` (kernel, CPU, Python version, memory, swap configuration).
- **Resource bounds verified:** Max RSS 24,636 kB for the full sweep; swap disabled and zero swap events observed; wall time 8.19 s for 32 configurations × 20,000 trials.
- **Raw outputs preserved:** Individual run JSON/CSV files in `results/sweep/`; aggregate summary in `results/vccr_sweep_summary.csv`; smoke test metrics in `results/smoke_metrics.json` and `results/smoke_metrics.csv`.
- **Command log preserved:** Exact commands recorded in run notes, including `/usr/bin/time -v` resource wrappers.
- **Decision artifact preserved:** Machine-readable decision in `.omx/project_decision.json` with all numeric evidence fields.
- **External dependencies:** Python 3.12.3 standard library only; no GPU or specialized packages required for the synthetic benchmark.
- **Claim audit status:** Not passed. Claim ledger is empty and blocked. Results should be treated as unevaluated prototype evidence.

---

## Conclusion

Verification-Conditional Cache Restore proposes that KV cache restoration decisions should be gated by online verification rather than static salience alone. In a synthetic policy benchmark across 32 configurations, 8 met the target of ≥30% peak KV reduction at ≤2 F1 quality-loss points. The best configuration achieved 83.5% peak KV reduction with 1.38 F1 quality-loss points and a 1.10× latency proxy, substantially outperforming both uniform compression (F1 0.5605) and static salience pinning (F1 0.7241).

However, this result is conditional on high verifier sensitivity. At sensitivity 0.70, quality loss exceeded 10 F1 points in all tested configurations, despite VCCR still outperforming the non-adaptive baselines in absolute F1. The policy mechanism is validated in simulation, but the critical dependency on verifier recall means that VCCR's practical viability depends on whether real verifiers can achieve ≥0.97 recall on answer-critical evidence in target workloads—a question this study does not answer.

The appropriate next step is integration with a real inference stack that exposes KV block priority, offload, and event controls (e.g., TensorRT-LLM or vLLM with LMCache), and evaluation on labeled long-context QA or extraction benchmarks measuring actual quality, latency, HBM peak, host/offload traffic, and verifier error rates. Early stopping should be applied if verifier recall on answer-critical evidence falls below 0.90 or if restore thrash exceeds the static-pinning traffic envelope.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Synthetic benchmark script | `scripts/vccr_sim.py` |
| Sweep driver script | `scripts/run_vccr_sweep.py` |
| Environment telemetry | `logs/environment.txt` |
| Smoke test log | `logs/smoke_vccr.log` |
| Sweep log | `logs/sweep_vccr.log` |
| Sweep analysis log | `logs/analyze_sweep.log` |
| Smoke metrics (JSON) | `results/smoke_metrics.json` |
| Smoke metrics (CSV) | `results/smoke_metrics.csv` |
| Sweep summary | `results/vccr_sweep_summary.csv` |
| Individual sweep runs | `results/sweep/*.json`, `results/sweep/*.csv` |
| Machine-readable decision | `.omx/project_decision.json` |
| Claim ledger | `papers/.../claim_ledger.json` |
| Evidence bundle | `papers/.../evidence_bundle.json` |
