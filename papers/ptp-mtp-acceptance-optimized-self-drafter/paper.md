# Acceptance-Optimized Self-Drafting for Parallel and Multi-Token Prediction Speculative Decoding

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (synthetic simulation outputs, literature survey notes, and decision logs). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

Speculative decoding with parallel token prediction (PTP) and multi-token prediction (MTP) drafters is conventionally trained to minimize token-level divergence (e.g., KL or cross-entropy) between draft and target distributions. However, the quantity that directly governs wall-clock speedup is the expected acceptance length per verification step, not distributional divergence alone. We investigate whether directly optimizing for acceptance length—rather than KL divergence—yields systematically better draft configurations. Using a calibrated synthetic simulator that models bounded-capacity drafters against Zipf-like target distributions, we compare KL-minimizing and acceptance-maximizing configuration selectors. Under constrained tail capacity, the acceptance selector wins in all 60 calibrated trials (mean expected token gain over KL selector: 0.124 tokens/step; mean estimated speedup gain: 10.5%). Under a less constrained smoke setting, the two selectors frequently agree, yielding negligible differences (1/12 wins). These results support the viability of acceptance-optimized drafting as a prototype direction but do not constitute real-model validation. The simulation validates the optimization shape—the fact that acceptance and KL objectives can diverge under capacity constraints—but not the magnitude of the effect in deployed systems. Full scientific closure requires target-model benchmarks with wall-clock throughput measurement.

## Introduction

Speculative decoding accelerates autoregressive language model inference by drafting multiple tokens in a single forward pass and verifying them against the target model in parallel. The speedup depends on how many draft tokens the verifier accepts per step—the *acceptance length*—and on the relative cost of drafting versus verification.

Recent work has introduced two families of multi-token drafters. Parallel Token Prediction (PTP) jointly predicts multiple dependent future tokens in one model call, reporting over four accepted tokens per speculative step on Spec-Bench for Vicuna-7B. Multi-Token Prediction (MTP) adds auxiliary future-token heads to the target model and is explicitly positioned as a speculative decoding foundation. Serving systems such as vLLM's P-EAGLE are already integrating parallel MTP drafting slots with practical kernel and metadata support.

Conventional drafter training minimizes token-level KL divergence or cross-entropy between draft and target distributions. This is a reasonable proxy but not the true objective: acceptance length depends on the *overlap* between draft and target distributions at the token level, which is captured by the total variation distance rather than KL. Recent work on acceptance-oriented losses reports 8–10% average acceptance-length gains over KL-based training across draft architectures and targets. Randomized drafting theory demonstrates that acceptance probability and tokens-per-second can be optimized from distribution overlap and draft probability. Acceptance has also been shown to vary by domain, motivating domain-aware speculation budgets.

This paper asks: when a bounded-capacity drafter must trade off tail coverage against top-token fidelity, does selecting or training for acceptance length directly outperform selecting for KL divergence? We approach this question through synthetic simulation, literature evidence, and a concrete prototype design, and we report honestly where evidence is insufficient.

## Method

### Synthetic Simulation Design

The simulator (`scripts/acceptance_sim.py`) does not emulate a full transformer. It isolates the decision rule central to the research question: given a target distribution and a family of bounded-capacity draft distributions, which selection criterion yields higher expected acceptance?

**Target distribution.** A Zipf-like token distribution with mild perturbation, approximating the token probability structure of a large language model.

**Draft distribution.** A bounded-capacity PTP/MTP-style drafter: detailed probability allocation for top tokens plus a crude uniform tail bucket. This models an auxiliary head with limited capacity that cannot represent the full target tail.

**Selectors compared.**

1. **KL selector:** chooses the drafter configuration minimizing KL(p ‖ q), where p is the target distribution and q is the draft distribution.
2. **Acceptance selector:** chooses the configuration maximizing expected emitted tokens per verification step.

**Acceptance computation.** For single-token speculative verification, acceptance probability equals Σ min(pᵢ, qᵢ) = 1 − TV(p, q), where TV is total variation distance. Multi-token draft length is estimated via an independent per-position prefix acceptance approximation: the expected accepted prefix length plus one bonus token from the verifier.

**Experimental conditions.**

- *Smoke run:* 12 trials, vocabulary size 512 (default), with default (less constrained) tail capacity.
- *Calibrated run:* 60 trials, vocabulary size 256, with constrained tail capacity to amplify the regime where KL and acceptance objectives diverge.

### Environment

All simulations ran on a Linux aarch64 host (kernel on `gx10-efe8`) with Python 3.12.3. An NVIDIA GB10 GPU was detected but 0% utilized; simulations were CPU-only. Available memory at telemetry time was approximately 121.9 GB with no swap configured. No CUDA kernels were involved; this was purely a CPU-based synthetic computation. No llama.cpp hook-prototypes, CUDA copy calibrations, or production validation steps were performed.

## Results

### Smoke Run (12 trials, vocab 512, default capacity)

| Metric | Value |
|---|---|
| Acceptance objective wins | 1 / 12 |
| Win rate | 0.083 |
| Mean expected token gain vs. KL | 0.0028 |
| Mean speedup gain vs. KL | 0.0024 |
| Max expected token gain vs. KL | 0.033 |

In the smoke setting, KL and acceptance selectors chose the same configuration in 11 of 12 trials. The single win for the acceptance selector yielded a marginal gain. This is expected: when drafter capacity is sufficient relative to vocabulary size, the two objectives are largely aligned, and the selectors converge.

### Calibrated Run (60 trials, vocab 256, constrained tail)

| Metric | Value |
|---|---|
| Acceptance objective wins | 60 / 60 |
| Win rate | 1.0 |
| Mean expected token gain vs. KL | 0.124 |
| Median expected token gain vs. KL | 0.128 |
| Mean speedup gain vs. KL | 0.105 |
| Max expected token gain vs. KL | 0.149 |
| Min expected token gain vs. KL | 0.083 |

Under constrained tail capacity, the acceptance selector consistently outperformed the KL selector across all 60 trials. The mean gain of 0.124 tokens per verification step translates to an estimated 10.5% speedup improvement. The minimum gain (0.083 tokens) indicates the advantage persists across all sampled configurations, not only in extreme cases.

### Interpretation

The divergence between smoke and calibrated results is informative. When drafter capacity is generous relative to the target distribution's effective support, KL minimization and acceptance maximization produce similar configurations. The advantage of direct acceptance optimization emerges specifically when the drafter must allocate limited capacity across tokens—precisely the regime relevant to practical MTP/PTP auxiliary heads with constrained parameter budgets.

However, these are synthetic results. The simulator assumes independent per-position acceptance, a Zipf-like target, and a specific capacity-constrained draft family. Real transformer distributions, position-dependent correlations, and verification semantics may alter the magnitude and even the direction of the effect. The 10.5% figure should be understood as a signal that the optimization shape is real under the simulated conditions, not as a prediction of real-system gains.

## Limitations

1. **No real-model evaluation.** The results derive entirely from a synthetic simulator. No target model, drafter checkpoint, or serving backend was evaluated. The simulation validates the optimization shape—the fact that acceptance and KL objectives can diverge under capacity constraints—but not the magnitude of the effect in real systems.

2. **Simplifying assumptions.** The simulator uses independent per-position acceptance, ignoring position-dependent correlations in real draft sequences. Real speculative verification rejects at the first mismatching position, so correlations between positions matter. The Zipf-like target distribution is a rough approximation of real language model output distributions.

3. **Vocabulary and capacity settings.** The calibrated run used vocabulary size 256 and a specific tail-capacity constraint. Real vocabularies are typically 32K–128K. The relationship between capacity constraint severity and the acceptance-vs-KL gap at production scale is unknown.

4. **No wall-clock measurement.** Speedup estimates are derived from expected token gains, not measured end-to-end latency. Drafter overhead, verification cost, kernel efficiency, and memory pressure all affect real throughput and may erode or amplify the estimated gains.

5. **Domain dependence.** Acceptance dynamics are known to vary by domain. The simulator does not model domain-specific acceptance profiles, though the literature motivates domain-aware speculation budgets.

6. **Incomplete scope.** The Notion page associated with this project was not accessible during the run; unpublished constraints there could alter the project scope.

7. **Claim audit status.** The project's claim ledger contains no structured claims and is marked `blocked_empty_claims`. This draft should not be treated as having passed a strict claim/evidence audit until claims reference public evidence files.

8. **Mixed smoke result.** The smoke run showed only 1/12 wins for the acceptance objective. While the calibrated run showed 60/60, this sensitivity to capacity assumptions means the result is conditional on the drafter being in a capacity-constrained regime. Whether real MTP/PTP auxiliary heads fall into this regime is an open empirical question.

## Reproducibility Checklist

- [x] **Code available:** `scripts/acceptance_sim.py` in project directory.
- [x] **Command-line arguments documented:** `--trials`, `--vocab`, `--out` flags recorded in run notes.
- [ ] **Fixed random seed:** Not explicitly set in recorded commands. Reproducers should set a fixed seed for exact numeric reproduction. This is a gap.
- [x] **Raw metrics files:** `metrics/smoke_acceptance_sim.json` and `metrics/acceptance_sim_60.json`.
- [x] **Execution logs:** `logs/smoke_acceptance_sim.log`, `logs/acceptance_sim_60.log`.
- [x] **Environment telemetry:** `logs/environment_telemetry.log` (kernel, Python version, GPU, memory).
- [x] **Decision artifact:** `.omx/project_decision.json` with full evidence bundle and blockers.
- [ ] **Real-model checkpoints:** Not evaluated; no model weights were downloaded or run.
- [ ] **Benchmark prompts:** Not used; simulation uses synthetic distributions only.
- [ ] **Wall-clock latency measurements:** Not performed; speedup estimates are derived, not measured.

## Conclusion

We presented evidence that directly optimizing speculative decoding drafters for acceptance length—rather than KL divergence—can yield meaningful gains when draft capacity is constrained relative to the target distribution. Synthetic simulation under a calibrated constrained-tail regime showed consistent advantages for the acceptance selector (60/60 trials, mean 10.5% estimated speedup gain), while an unconstrained smoke run showed negligible difference (1/12 trials), confirming that the advantage is capacity-dependent rather than universal.

These findings are consistent with recent literature reporting 8–10% acceptance-length improvements from acceptance-oriented losses and with theoretical results on the relationship between distribution overlap and acceptance probability. However, the evidence remains at the synthetic simulation level. The result should be interpreted as supporting a prototype direction, not as a validated optimization for deployed systems.

A concrete prototype path exists: start from an existing target model with MTP/PTP-compatible auxiliary heads or a lightweight self-draft module; calibrate per-position acceptance on a small prompt set; train with a hybrid objective (KL for stability in early phases, acceptance surrogate in late phases); and validate with wall-clock throughput against an autoregressive baseline. The proposed GB10 experiment protocol—smoke with 10–20 prompts at draft lengths 1–4, followed by calibrated throughput measurement—provides a minimal viable next step.

The central claim is narrow and conditional: acceptance-optimized drafting is worth prototyping, with the magnitude of real-system gains still unknown.

---

## Referenced Artifacts

| Artifact | Path | Description |
|---|---|---|
| Run notes | `run_notes.md` | Full research log, literature survey, experiment design, and interpretation |
| Simulation script | `scripts/acceptance_sim.py` | Synthetic acceptance comparison simulator |
| Smoke metrics | `metrics/smoke_acceptance_sim.json` | 12-trial smoke run results |
| Calibrated metrics | `metrics/acceptance_sim_60.json` | 60-trial calibrated run results |
| Smoke log | `logs/smoke_acceptance_sim.log` | Execution log for smoke run |
| Calibrated log | `logs/acceptance_sim_60.log` | Execution log for calibrated run |
| Environment telemetry | `logs/environment_telemetry.log` | Host, kernel, GPU, memory details |
| Project decision | `.omx/project_decision.json` | Final decision with evidence bundle and blockers |
| Project metadata | `.omx/project.json` | Project configuration |
| Session metrics | `.omx/metrics.json` | Turn and token usage summary |
| Claim ledger | `papers/.../claim_ledger.json` | Empty claims; audit status: blocked |
| Evidence bundle | `papers/.../evidence_bundle.json` | Source and run identifiers only |
| Paper manifest | `papers/.../paper_manifest.json` | Generation metadata |
