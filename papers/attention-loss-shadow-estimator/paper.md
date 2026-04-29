# Attention-Loss Shadow Estimator: Block-Level KV Cache Retention via Trained Shadow Loss Prediction

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We present the Attention-Loss Shadow Estimator, a lightweight trainable policy wrapper that predicts which key-value (KV) cache blocks a transformer will need at query time, enabling selective retention under a fixed memory budget without modifying base model weights. The method trains a linear scorer over online block features—position, landmark proximity, query overlap, marker strength, and block length—and uses a hybrid binary/magnitude objective to rank blocks for retention. We evaluate the approach across four experimental stages of increasing fidelity: a synthetic block-level simulator, a replay-label experiment with imported HuggingFace KV manager telemetry, a live-model experiment on SmolLM2-135M-Instruct, and a strengthened live-model experiment on Qwen2.5-0.5B-Instruct with hybrid loss-magnitude training. At equal 50% KV budget on the strongest live-model configuration, the shadow estimator improves logprob preservation by 2.348 points and live-label recall by 21.619 points over simple landmark pinning, while reducing restored KV bytes by 9.6% and p95 latency by 0.8%. At 35% budget, shadow retention matches or exceeds landmark@50 on both logprob preservation and recall while using 30% fewer resident KV bytes. Earlier experimental stages showed larger gains on synthetic metrics but mixed results on the initial live-model configuration, where recall lagged landmark pinning until the hybrid objective and stronger features were introduced. These results support the mechanism under the tested conditions, but all experiments use deterministic synthetic traces rather than external long-context benchmarks, and the model scale is limited to 0.5B parameters. The project decision is `finalize_positive` with medium confidence and moderate evidence strength.

## 1. Introduction

Autoregressive language models serving long-context inputs face a fundamental memory tension: the KV cache grows linearly with sequence length, yet GPU memory is finite. Practical deployments must evict some cached key-value pairs, and the quality cost of eviction depends on which blocks the model will actually attend to at generation time. Simple heuristics—always retain the most recent blocks, or pin a fixed set of "landmark" blocks—provide crude approximations but leave substantial quality on the table when the query depends on mid-context information.

The Attention-Loss Shadow Estimator addresses this by training a small linear model to predict, from online block and query features, which KV blocks are most likely to incur high answer-logprob loss if evicted. The estimator operates as a wrapper around any causal LM: it does not modify base model weights, requires no architectural changes, and can be trained from replay-inferred or live-model eviction labels. At inference time, it scores each block and retains the top-k under the memory budget.

This report documents the method and its empirical evaluation across four stages of increasing fidelity, from a pure synthetic simulator through live-model experiments with real `past_key_values` tensors. We report positive results on the final live-model configuration, mixed results on an earlier live-model stage, and substantial synthetic gains that overestimate real performance. We flag all limitations honestly.

## 2. Method

### 2.1 Problem Formulation

Given a prefill over $B$ blocks, a memory budget $k = \lfloor \alpha B \rfloor$ (where $\alpha \in (0,1]$ is the retention fraction), and an incoming query, the retention policy must select $k$ blocks whose KV entries remain resident. The remaining $B - k$ blocks are evicted (offloaded to CPU or discarded). If a subsequent query requires an evicted block, it must be restored, incurring latency and transfer cost.

### 2.2 Shadow Estimator

The shadow estimator is a linear scorer $s(b, q) = \mathbf{w}^\top \phi(b, q)$ where $\phi(b, q)$ is a feature vector computed from block $b$ and query $q$ without accessing model internals. The features used in the final configuration are:

- **Inverse position** (`inv_position`): $1 / \text{position}(b)$, capturing recency bias without leaking absolute position.
- **Landmark proximity** (`near_landmark`): binary indicator of whether block $b$ is adjacent to a designated landmark block.
- **Rare/numeric query overlap**: count of rare or numeric tokens shared between block $b$ and query $q$.
- **Marker strength**: signal from section-heading or structural markers in block $b$.
- **Block length**: token count of block $b$.

At inference, blocks are ranked by $s(b, q)$ and the top-$k$ are retained.

### 2.3 Training Objectives

Three training objectives were evaluated:

- **Binary**: cross-entropy loss on whether each block is relevant (1) or not (0), based on eviction labels.
- **Magnitude**: regression on the answer-logprob loss incurred by evicting each block.
- **Hybrid**: weighted combination of binary cross-entropy (with positive-class weight `positive_weight=3.5`) and magnitude loss (with weight `magnitude_weight=0.7`). The hybrid objective maintains recall pressure on all relevant blocks while ranking high-loss blocks higher.

The hybrid objective was introduced after the initial live-model experiment revealed that the binary objective under-recovered the relevant block set compared to landmark pinning.

### 2.4 Baseline Policies

- **Recency**: retain the $k$ most recent blocks.
- **Simple landmark**: retain $k$ blocks distributed at fixed intervals (evenly spaced across the sequence).
- **Query overlap**: retain blocks with highest token overlap with the query.
- **Oracle**: retain the $k$ blocks with highest true relevance (from labels).

### 2.5 Label Generation

Block relevance labels are derived via leave-one-block-out ablation: for each block $b$, the model generates an answer with block $b$'s KV entries removed, and the drop in answer logprob relative to the full-context baseline is recorded. Blocks whose removal causes a logprob drop above a threshold are labeled relevant. In the synthetic and replay-label stages, labels come from deterministic simulators; in the live-model stages, labels come from actual model forward passes.

## 3. Results

Results are reported separately for each experimental stage to preserve the progression of evidence fidelity.

### 3.1 Stage 1: Synthetic Block-Level Simulator

**Setup.** A dependency-free Python simulator (`src/shadow_estimator_experiment.py`) with deterministic long-doc QA, multi-turn chat, code-navigation, and grounded-generation traces. 260 training traces, 128 evaluation traces, 192 blocks, 10 queries per trace. Budgets: 0.25–0.70.

**Key results at 50% budget (shadow vs simple landmark):**

| Metric | Shadow | Landmark | Delta |
|---|---|---|---|
| Exact match | — | — | +53.125 pts |
| F1 | — | — | +36.315 pts |
| CPU/offload traffic proxy | — | — | −8.224% |
| Latency proxy | — | — | −21.096% |

**Lower-budget result:** Shadow@25 matched or exceeded landmark@50 quality with 50.0% lower peak KV MB and 4.209% lower latency proxy, but 44.779% higher CPU/offload traffic proxy (more evicted blocks requiring restore).

**Caveat.** These results use synthetic labels and proxy metrics. The attention-proxy baseline was competitive at low budgets. This stage supported continuing to real-model experiments but does not constitute proof of the mechanism.

### 3.2 Stage 2: Replay-Label + HF KV Telemetry

**Setup.** Shadow estimator trained on black-box replay-inferred block labels from an imported replayed-ablation oracle. KV telemetry uses real `past_key_values`-layout tensors through an imported HuggingFace KV manager. 180 training examples, 72 evaluation examples, 48 blocks. Budgets: 0.25–0.65. CUDA available (PyTorch 2.11.0+cu130).

**Key results at 50% budget (shadow vs simple landmark):**

| Metric | Shadow | Landmark | Delta |
|---|---|---|---|
| Exact match | — | — | +23.611 pts |
| Replay-label recall | — | — | +40.278 pts |
| Restored KV bytes | — | — | −100.0% |
| Transfer-time delta | — | — | −0.808% |

**Lower-budget result:** Shadow@25 achieved exact_match=1.0 and replay_label_recall=1.0 with 50.0% fewer resident blocks and restored_kv_bytes=0.

**Caveat.** Label semantics are from deterministic replayed-ablation tasks rather than a live LM scoring harness. KV telemetry uses real torch tensors through the imported HF manager but not model-output caches. This is a meaningful upgrade over synthetic labels but not yet final proof on a live inference stack.

### 3.3 Stage 3: Live-Model PKV Replay (SmolLM2-135M-Instruct)

**Setup.** Live HuggingFace causal-LM replay harness obtaining model-produced `past_key_values`, normalizing Transformers 5 `DynamicCache` layers to legacy `(key, value)` tuples. Leave-one-block-out answer-logprob labels. 18 training examples, 8 evaluation examples, 16 blocks, max 20 tokens per block. Budgets: 0.25–0.75. CUDA on NVIDIA GB10.

**Key results at 50% budget (shadow vs simple landmark):**

| Metric | Shadow | Landmark | Delta |
|---|---|---|---|
| Logprob preservation | 0.995886 | 0.983424 | +1.246 pts |
| Answer-logprob drop | −0.012768 | 0.521963 | −0.534731 |
| Restored KV bytes | 1,382,400 | 1,152,000 | +19.9% |
| Live-label recall | 0.681548 | 0.788095 | −10.655 pts |

**Lower-budget result:** Shadow@25 used 50.0% fewer resident KV bytes (1,843,200 vs 3,686,400) and achieved higher answer-logprob preservation (0.997353 vs 0.983424), but live-label recall was materially lower (0.576190 vs 0.788095) and restored KV bytes were higher (1,958,400 vs 1,152,000).

**Interpretation.** This stage produced mixed evidence. The shadow estimator improved the direct answer-logprob objective and reduced resident KV, but the binary-label feature setup under-recovered the leave-one-block-out relevant set compared with landmark pinning. This did not falsify the mechanism but indicated that stronger features and a better training objective were needed.

### 3.4 Stage 4: Strengthened Live-Model (Qwen2.5-0.5B-Instruct, Hybrid Objective)

**Setup.** Same live-LM harness with non-leaky block/query features (inverse position, landmark proximity, rare/numeric query overlap, marker strength, block length) and hybrid training objective (`positive_weight=3.5`, `magnitude_weight=0.7`). 28 training examples, 12 evaluation examples, 20 blocks, max 24 tokens per block. Budgets: 0.25–0.75. CUDA on NVIDIA GB10. Runtime: 38.03s wall, max RSS 2,794,140 KB, scored-token throughput ~3,080 tok/s.

**Key results at 50% budget (shadow vs simple landmark):**

| Metric | Shadow | Landmark | Delta |
|---|---|---|---|
| Logprob preservation | 0.98622 | 0.96274 | +2.348 pts |
| Live-label recall | 0.625341 | 0.40915 | +21.619 pts |
| Answer-logprob drop | — | — | −1.288495 |
| Restored KV bytes | — | — | −9.615% |
| p95 total latency | — | — | −0.804% |

**Lower-budget success criterion:** Shadow@35 matched or exceeded landmark@50 on logprob preservation and live-label recall while using 30.0% fewer resident KV bytes.

| Metric | Shadow@35 | Landmark@50 |
|---|---|---|
| Logprob preservation | 0.98343 | 0.96274 |
| Live-label recall | 0.507669 | 0.40915 |
| Resident KV bytes | 2,064,384 | 2,949,120 |
| Restored KV bytes | 1,523,712 | 1,152,000 |
| p95 total latency (ms) | 32.24 | — |

**Interpretation.** The strengthened shadow policy recovered live-label recall and preserved the logprob/KV benefits observed in earlier stages. This supports the core wrapper mechanism for this research branch, with the caveat that prompts are deterministic synthetic traces rather than an external long-context benchmark suite.

## 4. Limitations

1. **Synthetic traces.** All experiments use deterministic synthetic retrieval, code, and chat-style traces. No external long-context benchmark (e.g., LongBench, ZeroScrolls) was evaluated. Quality estimates may not transfer to naturalistic distributions.

2. **Small model scale.** The strongest live-model result uses Qwen2.5-0.5B-Instruct (500M parameters). Behavior at 7B, 13B, or 70B scales is unknown. The shadow estimator's feature set and training dynamics may interact differently with larger models.

3. **Limited evaluation set size.** The final live-model experiment uses 12 evaluation examples across 20 blocks. Statistical uncertainty is high. No confidence intervals or significance tests are reported.

4. **No unit tests.** The project has no collected pytest tests. Verification consists of `py_compile` checks and smoke runs only.

5. **Mixed earlier-stage results.** The initial live-model experiment (Stage 3, SmolLM2-135M) showed recall degradation versus landmark pinning. The hybrid objective and stronger features resolved this on Qwen2.5-0.5B, but it is unclear whether the fix is robust across models and tasks.

6. **Restored KV bytes at lower budgets.** While shadow@35 reduces resident KV by 30% versus landmark@50, its restored KV bytes (1,523,712) exceed landmark@50's (1,152,000). This means the latency benefit from reduced residency is partially offset by higher restore traffic in offload-heavy deployments.

7. **Single hardware configuration.** All live-model experiments ran on a single NVIDIA GB10 with UMA memory. Results on discrete-GPU or multi-GPU configurations may differ.

8. **Label leakage risk.** Although non-leaky features were designed for Stage 4, no formal information-leakage audit was performed. Features derived from block content could implicitly encode relevance information that would not be available in a truly online setting.

9. **No comparison to attention-sink or streaming strategies.** The baselines are recency, landmark, and query-overlap. Modern KV cache methods (e.g., attention-sink retention, streaming eviction, H2O) were not compared.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Code available in project | Yes: `src/live_lm_shadow_kv_experiment.py`, `src/shadow_replay_kv_experiment.py`, `src/shadow_estimator_experiment.py`, `src/kv_manager.py`, `src/paged_kv_manager.py`, `src/replayed_ablation_oracle.py`, `src/kv_eviction_gold_mvp.py` |
| Deterministic traces | Yes: all traces are generated by deterministic seed-based generators |
| Model identifiers specified | Yes: `HuggingFaceTB/SmolLM2-135M-Instruct`, `Qwen/Qwen2.5-0.5B-Instruct`, `hf-internal-testing/tiny-random-gpt2` |
| Hardware specified | Yes: NVIDIA GB10, UMA, ~120 GB available |
| Random seeds recorded | Not explicitly in artifacts |
| Full command lines recorded | Yes: in run notes for all stages |
| Raw result data available | Yes: `raw_rows.jsonl`, `summary.json`, `summary.csv`, `block_labels.jsonl` for each run |
| System snapshots recorded | Yes: `artifacts/live_lm_qwen_hybrid_system_snapshot.txt`, `artifacts/replay_kv_system_snapshot.txt`, `artifacts/system_snapshot.txt` |
| Runtime telemetry recorded | Yes: `/usr/bin/time -v` output and script-internal elapsed/throughput for all stages |
| Unit tests | No: pytest collection found 0 tests |
| External benchmark validation | No: only synthetic traces used |

## 6. Conclusion

The Attention-Loss Shadow Estimator demonstrates that a lightweight, base-weight-preserving wrapper can improve KV cache retention quality over simple landmark pinning on live model-output PKV telemetry. On Qwen2.5-0.5B-Instruct with a hybrid training objective, the shadow estimator improves logprob preservation by 2.348 points and live-label recall by 21.619 points at equal 50% KV budget, and achieves equivalent or better quality at 35% budget (30% fewer resident KV bytes). However, these results are bounded by synthetic trace distributions, small evaluation sets, a single model scale, and the absence of comparison to modern streaming KV cache methods. The initial live-model experiment on SmolLM2-135M produced mixed results (recall degradation), which was resolved only after introducing stronger features and a hybrid objective. The project decision is `finalize_positive` with medium confidence and moderate evidence strength. Future work should validate the same policy on external long-context benchmarks and at larger model scales before claiming broader applicability.

---

## Referenced Artifacts

### Source code
- `src/live_lm_shadow_kv_experiment.py`
- `src/shadow_replay_kv_experiment.py`
- `src/shadow_estimator_experiment.py`
- `src/kv_manager.py`
- `src/paged_kv_manager.py`
- `src/replayed_ablation_oracle.py`
- `src/kv_eviction_gold_mvp.py`
- `src/cache_audit.py`

### Decision and metadata
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `run_notes.md`

### Stage 1 (synthetic) results
- `artifacts/main/metrics.csv`
- `artifacts/main/summary.json`
- `artifacts/main_run.log`
- `artifacts/system_snapshot.txt`

### Stage 2 (replay-label + HF KV) results
- `artifacts/replay_kv_smoke/summary.json`
- `artifacts/replay_kv_smoke/raw_rows.jsonl`
- `artifacts/replay_kv_main/summary.json`
- `artifacts/replay_kv_main/summary.csv`
- `artifacts/replay_kv_main/raw_rows.jsonl`
- `artifacts/replay_kv_smoke.log`
- `artifacts/replay_kv_main.log`
- `artifacts/replay_kv_system_snapshot.txt`

### Stage 3 (live-LM SmolLM2) results
- `artifacts/live_lm_smoke/summary.json`
- `artifacts/live_lm_smoke/summary.csv`
- `artifacts/live_lm_smoke/raw_rows.jsonl`
- `artifacts/live_lm_smoke/block_labels.jsonl`
- `artifacts/live_lm_smoke.log`
- `artifacts/live_lm_smol_pilot/summary.json`
- `artifacts/live_lm_smol_pilot/summary.csv`
- `artifacts/live_lm_smol_pilot/raw_rows.jsonl`
- `artifacts/live_lm_smol_pilot/block_labels.jsonl`
- `artifacts/live_lm_smol_pilot.log`
- `artifacts/live_lm_smol_main/summary.json`
- `artifacts/live_lm_smol_main/summary.csv`
- `artifacts/live_lm_smol_main/raw_rows.jsonl`
- `artifacts/live_lm_smol_main/block_labels.jsonl`
- `artifacts/live_lm_smol_main.log`
- `artifacts/live_lm_system_snapshot.txt`

### Stage 4 (live-LM Qwen2.5 hybrid) results
- `artifacts/live_lm_hybrid_smoke/summary.json`
- `artifacts/live_lm_hybrid_smoke/summary.csv`
- `artifacts/live_lm_hybrid_smoke/raw_rows.jsonl`
- `artifacts/live_lm_hybrid_smoke/block_labels.jsonl`
- `artifacts/live_lm_hybrid_smoke.log`
- `artifacts/live_lm_qwen_hybrid_calibration/summary.json`
- `artifacts/live_lm_qwen_hybrid_calibration/summary.csv`
- `artifacts/live_lm_qwen_hybrid_calibration/raw_rows.jsonl`
- `artifacts/live_lm_qwen_hybrid_calibration/block_labels.jsonl`
- `artifacts/live_lm_qwen_hybrid_calibration.log`
- `artifacts/live_lm_qwen_hybrid_main/summary.json`
- `artifacts/live_lm_qwen_hybrid_main/summary.csv`
- `artifacts/live_lm_qwen_hybrid_main/raw_rows.jsonl`
- `artifacts/live_lm_qwen_hybrid_main/block_labels.jsonl`
- `artifacts/live_lm_qwen_hybrid_main.log`
- `artifacts/live_lm_qwen_hybrid_system_snapshot.txt`

### Verification logs
- `artifacts/pytest_after_hybrid.log`
- `artifacts/pytest_install.log`
- `artifacts/torch_cu130_install.log`
- `artifacts/transformers_install.log`
- `artifacts/venv_create.log`

### Claim audit
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
