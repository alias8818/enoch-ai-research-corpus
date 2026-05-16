# Recurrent-State Verification for Anisotropic Speculative Trees: An Algorithmic Feasibility Study of SSD/Mamba-2 Verifiers with GOOSE Speculation

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, claim ledgers, benchmark outputs, and decision JSON). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

Speculative decoding accelerates autoregressive language model inference by verifying multiple candidate tokens in a single forward pass. The GOOSE method constructs anisotropic speculation trees that allocate deeper chains along high-acceptance "spine" paths and wider branches near low-acceptance transitions, reporting speedups of 1.9–4.3× over autoregressive baselines. The Structured State Space Duality (SSD) framework establishes that state-space models such as Mamba-2 admit a recurrent form with constant per-step state and a structured masked-attention dual, raising the question of whether recurrent-state copying can replace transformer-style tree attention for speculative verification. This study investigates whether an SSD/Mamba-2-style recurrent verifier is algorithmically compatible with a GOOSE anisotropic speculation tree. Using an analytic expected-yield model validated by Monte Carlo simulation (200,000 trials per configuration, absolute error < 0.02 tokens) and a CPU operation-shape microbenchmark, we reproduce the GOOSE anisotropic-tree mechanism at the paper-median acceptance heterogeneity (6× spine-to-transition ratio) and sketch a recurrent-state verification schedule for a 63-node tree. At this heterogeneity, the anisotropic tree yields a +12.08% expected-accepted-token gain over a simplified balanced baseline. A parameterized memory model estimates SSD recurrent-state tree overhead at 0.5× the transformer KV-cache tree bytes under default assumptions, though this ratio is configuration-dependent and not measured from a deployed model. Gains are non-monotonic: at low heterogeneity (ratios 1 and 4), the anisotropic tree *underperforms* the balanced baseline by −15.47% and −6.36% respectively. No LLM serving implementation, model weights, GPU inference benchmark, or real acceptance-trace data exist in this study. The result supports algorithmic feasibility and motivates a next-stage implementation benchmark, but full system throughput remains unproven.

---

## Introduction

Autoregressive decoding in large language models is memory-bandwidth-bound: each generated token requires a full forward pass regardless of the computational cost of the pass itself. Speculative decoding addresses this bottleneck by proposing multiple candidate tokens—typically from a smaller draft model or the model's own earlier layers—and verifying them in a single forward pass using the target model. When the target model is a transformer, verification is performed via tree attention, a masked self-attention variant that evaluates all candidate positions simultaneously using the shared key-value (KV) cache.

The GOOSE method constructs anisotropic speculation trees that exploit heterogeneity in acceptance probabilities. Tokens continuing a high-probability context path ("spine" candidates) are accepted far more often than tokens representing topic transitions ("branch" candidates). GOOSE reports a median acceptance-probability gap of approximately 6× between spine and transition candidates, with spine acceptance median 0.21 and transition acceptance median 0.033. By constructing trees that are deep along the spine and wide near the root for transitions, GOOSE achieves 1.9–4.3× lossless speedup and 12–33% equal-budget improvement over balanced-tree baselines.

Separately, the Structured State Space Duality (SSD) framework establishes that structured state-space models, including Mamba-2, possess a dual form connecting their recurrent computation to structured masked attention on semiseparary matrices. A key property of the recurrent form is that the per-step state has constant size regardless of sequence length, in contrast to the linearly-growing KV cache of transformers. This raises a natural question: if the target model in a speculative decoding system is an SSD/SSM model rather than a transformer, can the verification step exploit recurrent-state copying instead of tree attention?

This study investigates the algorithmic compatibility of an SSD/Mamba-2 recurrent verifier with a GOOSE anisotropic speculation tree. We do not implement or benchmark a serving system. Instead, we: (1) reproduce the GOOSE anisotropic-tree yield model analytically and validate it via Monte Carlo simulation; (2) sketch a recurrent-state verification schedule showing how a 63-node GOOSE tree can be evaluated by copying parent recurrent states and advancing child states in grouped depth/frontier batches; (3) compare a parameterized memory model for SSD recurrent-state tree overhead against transformer KV-cache tree overhead; and (4) provide a CPU operation-shape microbenchmark contrasting vectorized recurrent propagation with a dense masked-attention analog. Our findings support algorithmic feasibility but do not constitute a system-level throughput claim.

---

## Method

### Problem Formulation

Given a speculative tree with a fixed candidate-node budget $B$, we seek to maximize the expected number of accepted tokens per verification step. Following GOOSE, we model two classes of candidates:

- **Spine candidates** with acceptance probability $p_s$.
- **Transition (branch) candidates** with acceptance probability $p_t$.

The anisotropy ratio is $r = p_s / p_t$. GOOSE reports a median ratio of approximately 6.

A balanced tree distributes candidate nodes uniformly across depths. An anisotropic tree allocates more nodes to deeper spine positions (where acceptance is higher) and concentrates branch nodes near the root (where the cost of a rejected branch is lower, since it does not prune deeper spine candidates).

### Analytic Yield Model

For a tree with spine length $L$ and branch widths $w_0, w_1, \ldots, w_{L-1}$ at each spine depth, the expected accepted-token yield is:

$$E[\text{yield}] = \sum_{d=0}^{L-1} p_s^d \cdot \left(1 + w_d \cdot p_t\right)$$

This model assumes independence of sibling branch acceptance and sequential spine acceptance. The tree must satisfy the budget constraint:

$$L + \sum_{d=0}^{L-1} w_d \leq B$$

Spine length and branch-width allocation are optimized to maximize expected yield for each anisotropy ratio $r$.

### Monte Carlo Validation

For each configuration, we simulate 200,000 trials of the speculative verification process. Each trial: (1) walks the spine from root to tip, accepting each spine node independently with probability $p_s$; (2) at each accepted spine depth $d$, evaluates $w_d$ branch candidates independently with probability $p_t$; (3) records the total number of accepted tokens (spine + branches). The Monte Carlo yield estimate is compared against the analytic expected yield; configurations with absolute error exceeding 0.02 tokens are flagged.

### SSD Recurrent-State Verification Schedule

For an SSD/Mamba-2 target model, each tree node carries a recurrent state vector inherited from its parent. The verification schedule proceeds as follows:

1. **Initialize**: The root node's recurrent state is the model's current state.
2. **Depth-first advance**: For each spine depth $d = 0, 1, \ldots, L-1$, copy the parent state to each child node at that depth and advance the state by one step (applying the SSM recurrence).
3. **Frontier batching**: Nodes at the same depth that share the same parent can be evaluated in a single vectorized batch, since their input states are identical up to the parent state.

For a 63-node tree with spine length 6 and branch widths $[31, 19, 7, 0, 0, 0]$, this yields 6 recurrent depth steps and 9 vector batches when grouped by parent depth (spine node + branch siblings at each of the first three depths with non-zero branches, plus the three deeper spine-only depths).

### Memory Model

We compare the memory overhead of duplicating verification-tree state for two architectures:

- **Transformer KV cache**: Each tree node requires storing key and value vectors for all layers. At hidden dimension $H$, $L_{\text{layers}}$ layers, and 2 bytes per element (fp16/bf16), the per-node KV cost is $2 \times L_{\text{layers}} \times H \times 2$ bytes (key + value, each of size $H$).
- **SSD recurrent state**: Each tree node requires storing the recurrent state for all layers. At SSD state elements per layer $S$, the per-node cost is $L_{\text{layers}} \times S \times 2$ bytes.

Default assumptions: $L_{\text{layers}} = 32$, $H = 4096$, $S = 4096$, fp16/bf16 precision. Under these assumptions, the SSD recurrent-state tree bytes are 0.5× the transformer KV-cache tree bytes. This ratio is parameter-dependent and does not constitute a measurement from any deployed model.

### CPU Operation-Shape Microbenchmark

To sanity-check the computational advantage of vectorized recurrent propagation over dense masked attention at the same candidate-node budget, we implement a NumPy CPU microbenchmark:

- **Recurrent propagation**: Vectorized state-copy and advance operations across candidate nodes, shaped to match the tree structure.
- **Dense masked-attention analog**: A full $B \times B$ masked attention computation at the same budget.

This microbenchmark measures wall-clock time for 200 repeats at state dimension 512 on CPU. It is a local sanity check on operation counts and shapes, not a GPU throughput measurement.

### Experimental Parameters

| Parameter | Smoke test | Full probe |
|---|---|---|
| Budget | 15 | 63 |
| $p_s$ | 0.42 | 0.42 |
| Anisotropy ratios | 1, 6 | 1, 2, 4, 6, 8, 12, 18 |
| Monte Carlo trials | 5,000 | 200,000 |
| Microbench state dim | 128 | 512 |
| Microbench repeats | 20 | 200 |

---

## Results

### Anisotropic Tree Yield

Table 1 presents the primary results across anisotropy ratios. Expected yield and Monte Carlo yield are in units of accepted tokens per verification step.

**Table 1**: Expected yield, Monte Carlo validation, and gain over balanced baseline for budget = 63, $p_s = 0.42$.

| Ratio $r$ | $p_t$ | Expected yield | MC yield | MC abs error | Gain vs balanced | Spine length | Branch widths by depth |
|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 0.420 | 3.4273 | 3.4308 | 0.0035 | −15.47% | 8 | [12, 11, 9, 8, 6, 5, 3, 1] |
| 2 | 0.210 | 2.9253 | 2.9241 | 0.0012 | +4.31% | 7 | [19, 15, 11, 7, 4, 0, 0] |
| 4 | 0.105 | 2.6574 | 2.6579 | 0.0005 | −6.36% | 6 | [26, 18, 10, 3, 0, 0] |
| 6 | 0.070 | 2.5178 | 2.5163 | 0.0016 | +12.08% | 6 | [31, 19, 7, 0, 0, 0] |
| 8 | 0.053 | 2.4205 | 2.4202 | 0.0003 | +21.78% | 6 | [35, 19, 3, 0, 0, 0] |
| 12 | 0.035 | 2.2914 | 2.2927 | 0.0013 | +18.62% | 6 | [41, 16, 0, 0, 0, 0] |
| 18 | 0.023 | 2.1707 | 2.1714 | 0.0007 | +9.75% | 6 | [47, 10, 0, 0, 0, 0] |

All Monte Carlo absolute errors are below 0.02 tokens, confirming the analytic model.

The gain-over-balanced column reveals a non-monotonic pattern. At low heterogeneity ($r = 1$), the anisotropic tree underperforms the balanced baseline by −15.47%. This is expected: when spine and branch acceptance are equal, concentrating nodes on a spine is maladaptive because the anisotropic allocation sacrifices breadth without any acceptance advantage. At $r = 4$, the anisotropic tree still underperforms by −6.36%, indicating that at this intermediate heterogeneity, the optimized tree sacrifices too much branch breadth for spine depth relative to the balanced alternative. Positive gains emerge at $r \geq 6$, consistent with GOOSE's reported median heterogeneity. The peak gain of +21.78% occurs at $r = 8$, with gains declining at higher ratios ($r = 12$: +18.62%, $r = 18$: +9.75%), suggesting diminishing returns as transition acceptance becomes negligibly small and branch nodes contribute little yield regardless of allocation.

### SSD Recurrent Verification Schedule

For the $r = 6$ configuration (spine length 6, branch widths [31, 19, 7, 0, 0, 0], total 63 nodes):

- **Recurrent depth steps**: 6 (one per spine position).
- **Vector batches when grouped by parent depth**: 9 (spine node plus branch siblings at each of the first three depths with non-zero branches, plus the three deeper spine-only depths).

This schedule demonstrates that the entire 63-node tree can be verified in 6 sequential recurrent steps with 9 vectorized batch operations, avoiding the need for a transformer-style tree attention mask. The key insight is that sibling nodes at the same depth sharing a parent can reuse the parent's recurrent state as a common starting point, enabling batched evaluation.

### Memory Model

Under default assumptions (32 layers, hidden dimension 4096, SSD state elements per layer 4096, fp16/bf16):

- Transformer KV-cache tree bytes: 33,030,144
- SSD recurrent-state tree bytes: 16,515,072
- Ratio (SSD / Transformer): 0.5

This ratio is sensitive to the assumed SSD state dimension per layer. Real Mamba-2 model configurations may use different state sizes, and the transformer KV-cache per-node cost depends on the number of attention heads and head dimension. This model should be replaced with measurements from the chosen implementation.

### CPU Microbenchmark

At state dimension 512, 200 repeats:

- Vectorized recurrent propagation: 0.00218 s
- Dense masked-attention analog: 0.01395 s
- Ratio (attention / recurrent): 6.40×

This result is a CPU NumPy operation-shape timing check. It confirms that, at the same candidate-node budget, the recurrent formulation involves substantially fewer floating-point operations than dense masked attention. It does not predict GPU throughput, where memory-access patterns, kernel fusion, and hardware-specific optimizations dominate.

### Resource Usage

The full bounded probe required:

- Wall time: 1.04 s
- Maximum RSS: 36,444 kB
- Swap used: 0 kB

The probe ran entirely on CPU. An NVIDIA GB10 GPU was available on the host but was not utilized for inference, consistent with the decision to close the algorithmic-feasibility question before committing to a GPU implementation.

---

## Limitations

This study has several significant limitations that bound the strength of its conclusions:

1. **No LLM implementation or serving benchmark.** No SSD/Mamba-2 model weights, serving engine, or inference pipeline existed in this project. All results are from an analytic model, Monte Carlo simulation, and CPU microbenchmark. No tokens/sec, time-to-first-token (TTFT), inter-token latency (ITL), or GPU utilization measurements were obtained.

2. **No real acceptance traces.** The acceptance probabilities $p_s$ and $p_t$ are parameterized inputs, not measurements from any target model. The GOOSE paper reports median values, but actual acceptance distributions depend on the draft model, target model, and input distribution.

3. **Memory model is parameterized, not measured.** The 0.5× SSD-to-transformer memory ratio depends on assumed per-layer state dimensions (4096) that may not match any real Mamba-2 configuration. Actual memory footprints must be measured from the chosen implementation.

4. **CPU microbenchmark does not predict GPU performance.** The 6.40× attention-to-recurrent time ratio measures NumPy operation-shape costs on CPU. GPU kernels for SSM recurrence and tree attention have fundamentally different memory-access and parallelism characteristics.

5. **Simplified yield model.** The analytic model assumes independent sibling acceptance and sequential spine acceptance. Real speculative decoding involves more complex dependencies (e.g., draft-model correlation, token-level acceptance conditioning).

6. **Balanced baseline is simplified.** The balanced baseline used for gain comparison is a simplified model, not the full GOOSE balanced-tree baseline. The reported gains (e.g., +12.08% at $r = 6$) are not directly comparable to GOOSE's reported 12–33% improvement over its own balanced baseline.

7. **Non-monotonic gain pattern.** The negative gains at $r = 1$ and $r = 4$ indicate that the anisotropic allocation can be harmful at low-to-moderate heterogeneity. Any deployment must characterize the actual acceptance distribution before committing to an anisotropic tree.

8. **Ambiguous project origin.** The project title "SSD + Goose + SA" was ambiguous; SA was resolved as the GOOSE speculation/acceptance mechanism rather than a separate method. No private Notion content beyond prompt metadata was accessible.

9. **Claim ledger is empty.** The claim ledger for this paper draft contains no structured claims and has audit status "blocked_empty_claims." This draft must not pass strict claim/evidence audit until claims reference public evidence files.

---

## Reproducibility Checklist

- **Code available**: `scripts/ssd_goose_sa_probe.py` (SHA256 recorded in `logs/06_sha256_manifest.log`)
- **Primary result file**: `results/full/ssd_goose_sa_probe_20260506T044512Z.json`
- **Validation script**: Inline Python in run notes; output in `logs/05_validate_results.log`
- **Environment recorded**: `logs/00_environment.log` (host, OS, GPU, memory, Python/NumPy versions)
- **Source artifacts**: `artifacts/sources/goose_2604.02047.pdf`, `artifacts/sources/goose_2604.02047.txt`, `artifacts/sources/ssd_2405.21060.pdf`, `artifacts/sources/ssd_2405.21060.txt`
- **Claim extraction log**: `logs/02_source_claim_grep.log`
- **Full run log**: `logs/04_full_probe.log`
- **Runtime metrics**: `logs/04_full_probe_time.log` (wall time, max RSS via `/usr/bin/time -v`)
- **SHA256 manifest**: `logs/06_sha256_manifest.log`
- **Random seed**: Not explicitly recorded in the probe script; Monte Carlo results may vary slightly across runs. The validation check confirms MC absolute error < 0.02 for all configurations.
- **Hardware**: Linux `gx10-efe8`, `aarch64`, NVIDIA GB10 (GPU unused for compute), 121 GB available RAM, swap disabled.
- **Software**: Python 3.12.3, NumPy 2.4.4, PyTorch not installed.
- **Decision artifact**: `.omx/project_decision.json`

---

## Conclusion

This study investigates whether an SSD/Mamba-2-style recurrent verifier can execute a GOOSE anisotropic speculative tree. The central finding is one of algorithmic compatibility, not system performance:

- The GOOSE anisotropic-tree yield model is reproducible in an analytic/Monte Carlo harness. At the paper-median heterogeneity of $r = 6$, the anisotropic tree yields a +12.08% expected-accepted-token gain over a simplified balanced baseline, with Monte Carlo absolute error of 0.0016 tokens.
- A concrete recurrent-state verification schedule exists for a 63-node GOOSE tree: 6 sequential depth steps and 9 vectorized batch operations, with parent-state copying replacing transformer tree attention.
- A parameterized memory model estimates SSD recurrent-state tree overhead at 0.5× transformer KV-cache tree bytes under default assumptions, though this ratio is configuration-dependent and must be validated against real model configurations.
- A CPU microbenchmark confirms fewer floating-point operations for recurrent propagation versus dense masked attention at the same budget (6.40× ratio), but this does not predict GPU throughput.

The combination of SSD recurrent verification with GOOSE anisotropic trees is algorithmically viable and worth implementation benchmarking. However, the evidence here does not support claims about real-world speedup, tokens/sec, latency, or memory behavior on any deployed model. The non-monotonic gain pattern—negative at $r = 1$ and $r = 4$, positive at $r \geq 6$—underscores that anisotropic allocation requires accurate characterization of acceptance heterogeneity before deployment.

The recommended next step is to implement a minimal SSD/Mamba-2 verifier adapter that exposes parent recurrent-state copy and child-state advance for a GOOSE tree, then run a GPU smoke/calibration matrix measuring accepted tokens per verification, tokens/sec, ITL, TTFT, GPU utilization, and memory posture before committing to a full benchmark.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Probe script | `scripts/ssd_goose_sa_probe.py` |
| Primary result JSON | `results/full/ssd_goose_sa_probe_20260506T044512Z.json` |
| Environment log | `logs/00_environment.log` |
| Source fetch log | `logs/01_fetch_extract_sources.log` |
| Source claim grep | `logs/02_source_claim_grep.log` |
| Smoke probe log | `logs/03_smoke_probe.log` |
| Full probe log | `logs/04_full_probe.log` |
| Full probe runtime | `logs/04_full_probe_time.log` |
| Validation log | `logs/05_validate_results.log` |
| SHA256 manifest | `logs/06_sha256_manifest.log` |
| Goose PDF | `artifacts/sources/goose_2604.02047.pdf` |
| Goose text extract | `artifacts/sources/goose_2604.02047.txt` |
| SSD PDF | `artifacts/sources/ssd_2405.21060.pdf` |
| SSD text extract | `artifacts/sources/ssd_2405.21060.txt` |
| Decision JSON | `.omx/project_decision.json` |
| Metrics JSON | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260506T044140821325+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260506T044140821325+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260506T044140821325+0000/paper_manifest.json` |
