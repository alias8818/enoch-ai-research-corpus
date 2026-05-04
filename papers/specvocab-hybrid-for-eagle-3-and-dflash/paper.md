# SpecVocab Hybrid Draft-Head Reduction for EAGLE-3 and DFlash: Feasibility and Limitations

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, and prototype metrics). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

Speculative decoding accelerates large-language-model inference by drafting tokens with a lower-cost model and verifying them against the target. In state-of-the-art drafters such as EAGLE-3 and DFlash, the output embedding (LM-head) projection dominates draft latency when vocabulary sizes are large (e.g., $V = 151{,}936$ for Qwen3-8B). This work investigates whether SpecVocab-style dynamic vocabulary selection—computing approximate logits in a reduced dimension, selecting a top-$k$ candidate subset, and computing exact logits only for those rows—can reduce draft-head cost when integrated into EAGLE-3 and DFlash. We report theoretical cost-model analysis, static code analysis of attachment points, and local NumPy/CPU calibration probes. For Qwen3-8B-scale parameters ($V = 151{,}936$, $d = 4096$, $d' = 256$, $k = 2048$), the hybrid reduces draft-head multiply-accumulate operations by a factor of 13.16× and emitted logit elements by 74.19×. However, a naive CPU/NumPy implementation of the indexed-head path showed no wall-clock speedup (observed ratio 0.90–0.97×), confirming that the theoretical MAC reduction is erased by Python-level gather and top-$k$ overhead without a fused GPU kernel. We identify DFlash as the more promising first integration target due to its block-parallel draft structure, which amortizes ranker overhead across multiple positions. The result is a conditional feasibility finding: the approach is attractive in cost-model terms, but scientific closure requires a trained vocabulary ranker and a fused CUDA/Triton indexed-head kernel, neither of which yet exists in this work.

## Introduction

Speculative decoding improves autoregressive inference throughput by generating draft tokens with a lower-cost model and verifying them in parallel against the target model. Two recent families of drafters have advanced the state of the art:

- **EAGLE-3** uses an autoregressive feature-level draft model that reuses target-model hidden states and emits tokens via a fixed draft vocabulary, mapped to the target vocabulary through index buffers.
- **DFlash** employs a diffusion-style block-parallel draft model that produces an entire block of draft tokens in a single non-causal pass, then verifies the block against the target.

Both approaches share a bottleneck: the LM-head projection from hidden dimension $d$ to vocabulary size $V$. For models with large vocabularies (e.g., Qwen3-8B with $V = 151{,}936$), this single linear layer dominates draft computation time.

SpecVocab addresses this bottleneck by replacing the full $V$-way projection with a two-stage process: (1) approximate ranking via a low-rank projection $W_{\text{down}} \in \mathbb{R}^{d' \times d}$ followed by $W_{\text{vocab}} \in \mathbb{R}^{V \times d'}$, yielding approximate logits for all $V$ tokens; (2) selection of a top-$k$ candidate set $K_t$; and (3) exact logit computation only for the $k$ selected rows of the target LM-head weight matrix $U \in \mathbb{R}^{V \times d}$.

This work asks: can SpecVocab-style dynamic vocabulary selection be integrated into EAGLE-3 and DFlash, and does the resulting cost reduction translate into practical throughput gains? We report theoretical analysis, code-level attachment-point identification, and calibration experiments. The answer is conditionally positive: the arithmetic savings are substantial, but realizing them requires infrastructure (fused GPU kernels, trained rankers) not yet available in this study.

## Method

### Theoretical Cost Model

For a single draft position, the full LM-head projection requires $V \cdot d$ multiply-accumulate operations (MACs). The SpecVocab hybrid replaces this with two stages:

1. **Ranker stage:** $V \cdot d'$ MACs (low-rank approximate logit computation).
2. **Indexed exact stage:** $k \cdot d$ MACs (exact logit computation for top-$k$ candidates only).

The total hybrid cost per position is $V \cdot d' + k \cdot d$, yielding a theoretical MAC reduction factor of:

$$R = \frac{V \cdot d}{V \cdot d' + k \cdot d}$$

For $P$ draft positions (e.g., $P = \text{block\_size} - 1$ in DFlash), the full cost is $P \cdot V \cdot d$ and the hybrid cost is $P \cdot (V \cdot d' + k \cdot d)$, assuming one independent candidate set per position. The reduction factor $R$ is independent of $P$.

Additionally, the number of emitted logit elements per position drops from $V$ to $k$, a reduction factor of $V / k$.

### Attachment-Point Analysis

We analyzed the open-source implementations of DFlash (in `z-lab/dflash`, commit `44947fb`) and EAGLE-3 (in `sgl-project/SpecForge`, commit `d5fb617`) to identify where the LM-head projection occurs and how a SpecVocab hybrid would attach.

**DFlash.** In `specforge/modeling/draft/dflash.py` (lines 320–331), the draft block's hidden states for positions $1$ through $\text{block\_size}-1$ are projected through `target.lm_head(...)` in a single call. This is the primary replacement target: the full LM-head call would be replaced by the ranker + indexed exact-head path. The replacement is localized and does not affect the subsequent target-model verification step.

**EAGLE-3.** In `specforge/modeling/draft/llama3_eagle.py` (lines 1322–1347, 1413–1415), the draft model already supports a `draft_vocab_size` configuration and mapping buffers (`t2d` / `d2t`) between target and draft vocabularies. However, the current draft vocabulary is fixed at configuration time rather than dynamically selected per step. A SpecVocab hybrid would replace the static draft vocabulary with a dynamic top-$k$ candidate set computed per draft step. This introduces a complication: EAGLE-3's autoregressive tree drafting requires candidate subsets across sequential speculative steps, and the overhead of computing top-$k$ per tiny step may not be well-amortized.

### Proposed Hybrid Design

**For DFlash:**

1. For each block-position hidden state $h_{t,i}$ ($i = 1, \ldots, \text{block\_size}-1$), compute approximate logits via $W_{\text{vocab}}(W_{\text{down}}(h_{t,i}))$.
2. Select top-$k$ candidate set $K_{t,i}$ per position.
3. Execute a batched indexed exact LM-head kernel over $(position, candidate)$ rows of $U$.
4. Sample per position from candidate logits.
5. Preserve target verification unchanged, maintaining losslessness.

**For EAGLE-3:**

1. Replace the fixed `draft_vocab_size` projection with the ranker + indexed exact-head path.
2. Compute $K_t = \text{top-}k(W_{\text{vocab}}(W_{\text{down}}(h_t)))$ per draft step.
3. Compute exact logits $U[K_t] \cdot h_t$.
4. Sample from the candidate distribution; map candidate token IDs directly to target vocabulary.
5. Design a cache/reuse policy for candidate sets across sequential speculative steps to mitigate per-step top-$k$ overhead.

### Calibration Probe

We implemented a NumPy-based calibration script (`scripts/specvocab_hybrid_probe.py`) to measure wall-clock times for the full vs. hybrid LM-head paths on CPU. The script uses random matrices as proxies for model weights and hidden states; it does not use trained weights and its recall numbers should not be interpreted as model quality metrics. The probe was run on an NVIDIA GB10 system with CUDA 13.0, approximately 117 GiB available memory, swap disabled, and no PyTorch/Transformers/Triton/CuPy/JAX/MLX stack in the base environment.

## Results

### Theoretical MAC Reduction

Table 1 summarizes the cost-model analysis across parameter configurations.

**Table 1:** Theoretical MAC reduction for SpecVocab hybrid vs. full LM-head projection.

| Configuration | $V$ | $d$ | $d'$ | $k$ | Positions | Full MACs | Hybrid MACs | MAC Reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Smoke test | 8,192 | 512 | 32 | 256 | 4 | 16,777,216 | 1,572,864 | 10.67× |
| Calibration | 32,768 | 1,024 | 64 | 512 | 8 | 268,435,456 | 20,971,520 | 12.80× |
| Qwen3-8B EAGLE-like | 151,936 | 4,096 | 256 | 2,048 | 1 | 622,329,856 | 47,284,224 | 13.16× |
| Qwen3-8B DFlash block=8 | 151,936 | 4,096 | 256 | 2,048 | 7 | 4,356,308,992 | 330,989,568 | 13.16× |
| Qwen3-8B DFlash block=16 | 151,936 | 4,096 | 256 | 2,048 | 15 | 9,334,947,840 | 709,263,360 | 13.16× |

The MAC reduction converges to approximately 13.16× for the Qwen3-8B-scale configuration with $d' = d/16$ and $k = 2048$. The logit element reduction is $V / k = 151{,}936 / 2{,}048 \approx 74.19\times$.

### Observed Wall-Clock Performance (CPU/NumPy)

Table 2 reports the observed wall-clock ratio of full-to-hybrid execution time on CPU using NumPy.

**Table 2:** Observed CPU wall-clock ratio (full time / hybrid time). Values below 1.0 indicate the hybrid was slower.

| Configuration | Theoretical MAC Reduction | Observed Full/Hybrid Ratio |
|---|---:|---:|
| Smoke ($V{=}8{,}192$, $d{=}512$, $d'{=}32$, $k{=}256$, pos=4) | 10.67× | 0.97× |
| Calibration ($V{=}32{,}768$, $d{=}1{,}024$, $d'{=}64$, $k{=}512$, pos=8) | 12.80× | 0.90× |

The hybrid path was **slower** than the full projection in both measured cases. The naive NumPy implementation incurs overhead from: (1) the top-$k$ selection step, (2) Python-level gather operations to extract the candidate rows from $U$, and (3) the indexed matrix multiplication, which cannot leverage optimized BLAS routines as effectively as a full dense matmul. These overheads completely erase the theoretical MAC savings.

The Qwen3-8B-scale configurations were evaluated in cost-model mode only (no wall-clock measurement) because the full PyTorch/Transformers stack was not available in the probe environment.

### Code Analysis Findings

The static code analysis confirms that both DFlash and EAGLE-3 have well-defined, localized LM-head projection points amenable to SpecVocab hybrid replacement:

- DFlash: `target.lm_head(...)` called once over all block draft positions (`dflash.py:320-331`).
- EAGLE-3: Draft logits computed via a fixed `draft_vocab_size` projection with mapping buffers (`llama3_eagle.py:1322-1347, 1413-1415`).

DFlash is the more attractive first target because its block-parallel structure amortizes the ranker overhead across multiple draft positions in a single pass, whereas EAGLE-3's autoregressive tree drafting would require per-step top-$k$ computation with less amortization opportunity.

## Limitations

This work has several significant limitations that prevent drawing conclusions about practical throughput gains:

1. **No fused GPU kernel.** The central negative result is that a naive CPU/NumPy implementation of the indexed-head path is slower than the full projection. The SpecVocab paper itself emphasizes that a custom CUDA/Triton/CUTLASS kernel for the indexed matmul + top-$k$ path is essential. We have not implemented such a kernel, and the theoretical MAC reduction cannot be claimed as a practical speedup without it.

2. **No trained vocabulary ranker.** The calibration probe uses random untrained matrices for $W_{\text{down}}$ and $W_{\text{vocab}}$. The recall of the top-$k$ candidate set under random projections is not informative about recall under trained projections. A trained ranker, jointly optimized with the draft model via distillation from the target's full output distribution, is required before any quality or acceptance-rate claims can be made.

3. **No end-to-end inference benchmark.** No full model inference runs were performed. The environment lacked PyTorch, Transformers, Triton, and other ML frameworks. All Qwen3-8B-scale results are cost-model estimates, not measurements.

4. **Single-rank assumption per position.** The cost model assumes one independent candidate set $K_{t,i}$ per draft position. If candidate sets must be shared or cached across positions (e.g., for EAGLE-3's tree drafting), the cost model may overestimate savings.

5. **No acceptance-rate modeling.** Reducing the candidate set to $k$ tokens necessarily truncates the tail of the draft distribution. If the true next token falls outside $K_t$, the draft is guaranteed to be rejected at that position. The relationship between $k$, ranker quality, and acceptance rate has not been characterized in this work.

6. **Hardware-specific calibration.** The CPU calibration was performed on a single GB10 system. Results may differ substantially on GPU, on other hardware, or with different BLAS/library configurations.

7. **Random seed not controlled.** The prototype script does not specify a random seed; wall-clock measurements may vary across runs, though the qualitative finding (hybrid slower than full on CPU/NumPy) is expected to be robust given the magnitude of the overheads involved.

## Reproducibility Checklist

- **Hardware:** NVIDIA GB10, CUDA 13.0 driver stack, approximately 117 GiB available RAM, swap disabled.
- **Software:** Python with NumPy; no PyTorch/Transformers/Triton/CuPy/JAX/MLX in base environment.
- **Reference repositories:** `z-lab/dflash` at commit `44947fb`; `sgl-project/SpecForge` at commit `d5fb617`.
- **Prototype script:** `scripts/specvocab_hybrid_probe.py` — NumPy-based calibration probe with random matrices.
- **Prototype output:** `artifacts/specvocab_hybrid_probe.json` — structured metrics from the probe.
- **Logs:** `logs/specvocab_hybrid_probe.log`, `logs/env_smoke.log`, `logs/post_probe_telemetry.log`, `logs/dflash_lm_head_lines.log`, `logs/eagle3_lm_head_lines.log`, `logs/vocab_code_grep.log`, `logs/specvocab_algorithm_excerpt.log`, `logs/paper_relevant_excerpts.txt`.
- **Paper references:** `refs/specvocab.txt`, `refs/dflash.txt`, `refs/eagle3.txt` (converted from downloaded PDFs).
- **Random seed:** Not specified in the probe script; results may vary across runs.
- **Claimed speedups:** All speedup figures in this paper are theoretical (cost-model) unless explicitly labeled as observed wall-clock measurements. The only wall-clock measurements (0.97× and 0.90×) show the hybrid is slower, not faster, on CPU/NumPy.

## Conclusion

We have shown that SpecVocab-style dynamic vocabulary selection has clear, localized attachment points in both EAGLE-3 and DFlash, and that for Qwen3-8B-scale parameters ($V = 151{,}936$, $d = 4096$, $d' = d/16$, $k = 2048$), the hybrid reduces draft-head MACs by 13.16× and emitted logit elements by 74.19×. DFlash is the more promising first integration target because its block-parallel draft structure amortizes ranker overhead across multiple positions.

However, this is a feasibility and cost-model result, not a throughput result. The naive CPU implementation is slower than the baseline, and the gap between theoretical MAC reduction and practical wall-clock performance remains unclosed. Scientific closure requires three elements not present in this work: (1) a fused CUDA/Triton batched indexed LM-head kernel, (2) a trained vocabulary ranker distilled from the target model, and (3) end-to-end inference benchmarks measuring acceptance rate, tokens per second, and losslessness. Until these are demonstrated, the 13.16× MAC reduction should be understood as an upper bound on potential savings, not a predicted speedup.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Project decision JSON | `.omx/project_decision.json` |
| Prototype script | `scripts/specvocab_hybrid_probe.py` |
| Prototype metrics | `artifacts/specvocab_hybrid_probe.json` |
| Prototype log | `logs/specvocab_hybrid_probe.log` |
| Environment smoke log | `logs/env_smoke.log` |
| Post-probe telemetry | `logs/post_probe_telemetry.log` |
| DFlash LM-head code excerpt | `logs/dflash_lm_head_lines.log` |
| EAGLE-3 LM-head code excerpt | `logs/eagle3_lm_head_lines.log` |
| Vocabulary code grep results | `logs/vocab_code_grep.log` |
| SpecVocab algorithm excerpt | `logs/specvocab_algorithm_excerpt.log` |
| Paper relevant excerpts | `logs/paper_relevant_excerpts.txt` |
| SpecVocab paper (text) | `refs/specvocab.txt` |
| DFlash paper (text) | `refs/dflash.txt` |
| EAGLE-3 paper (text) | `refs/eagle3.txt` |
| DFlash repository | `refs/dflash` (commit `44947fb`) |
| SpecForge repository | `refs/specforge` (commit `d5fb617`) |
| Run notes | `run_notes.md` |
