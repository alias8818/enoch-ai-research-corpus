# Persona-Conditioned Context Ordering Survives Small-Model Decoding: Evidence from Flan-T5-Base on SQuAD and HotpotQA

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We investigate whether prompt-level evidence-retention gains from persona-conditioned context ordering survive actual small-model decoding—a hypothesis we term "decoding survival." Prior work in the parent project established that a heuristic persona-conditioned packer retains more gold evidence than source-order packing at fixed token budgets. This study validates whether those retention gains translate into measurable answer-quality improvements under greedy decoding. Using `google/flan-t5-base` on 80 SQuAD examples and 80 HotpotQA examples at a 180-token pack budget, persona-conditioned packing yields +61.80 answer-F1 on SQuAD and +19.89 answer-F1 on HotpotQA versus source-order, at token-neutral budgets and with slightly lower median latency. The branch kill condition (≤ +3 F1 delta) was cleared by a wide margin. However, these results are bounded by a single model, a single pack budget, greedy decoding, and small deterministic samples. The current project artifacts support this finding in the tested setting; the result validates the mechanism, not a final optimized ordering system.

---

## 1. Introduction

Retrieval-augmented generation and long-context question answering systems must select and order evidence within fixed token budgets. The order in which evidence fragments appear in the prompt can substantially affect which fragments are retained after truncation and, consequently, what the model can draw upon at decoding time.

A prior project (parent: `source-record-redacted`) demonstrated that a heuristic persona-conditioned context orderer—reordering evidence fragments by relevance to a query persona before packing—retains substantially more gold evidence than naive source-order packing at the same token budget. However, evidence retention is a proxy; the critical question is whether those retention gains survive the decoding process and produce better answers. We term this the **decoding-survival hypothesis**: prompt-level evidence-retention improvements from persona-conditioned ordering translate into measurable answer-quality gains under actual model decoding.

This study replicates the packing strategies from the parent project and evaluates them end-to-end with a local small instruction-tuned model, measuring answer exact match (EM), token-level F1, evidence recall, oracle answerability, latency, throughput, and resource telemetry.

We define a branch kill condition: if persona-conditioned packing yields ≤ +3 answer-F1 points versus source-order at similar token budgets, or if generation repeatedly fails despite retained gold evidence, the decoding-survival hypothesis is rejected. The observed deltas substantially exceed this threshold on both datasets.

---

## 2. Method

### 2.1 Context Orderer

The context orderer (`src/context_orderer.py`) is a heuristic, dependency-free packer inherited from the parent project. Given a set of evidence fragments and a query, it implements two packing strategies:

- **Source-order**: Fragments are packed in their original retrieval order, truncated to the token budget.
- **Persona-conditioned**: Fragments are reordered by lexical relevance to the query persona before packing and truncation.

Both strategies operate under an identical token budget, ensuring that any quality differences arise from ordering rather than budget expansion.

### 2.2 Generation Benchmark

The generation benchmark (`experiments/generation_benchmark.py`) evaluates both packing strategies end-to-end:

1. Pack evidence fragments using source-order or persona-conditioned strategy at the specified token budget.
2. Construct a short-answer prompt from the packed context.
3. Decode with greedy search via `google/flan-t5-base`.
4. Score the decoded answer against gold references using exact match (EM) and token-level F1.
5. Compute kept evidence recall (fraction of gold evidence fragments retained after packing) and oracle answerability F1 (whether the packed context contains sufficient evidence to answer).
6. Record latency (per-sample, p50, p95), throughput (samples/sec, generated tokens/sec), CPU/process memory, UMA `/proc/meminfo`, CUDA allocator usage, and best-effort GPU utilization telemetry.

### 2.3 Datasets

- **SQuAD v1.1 dev**: 80 examples sampled deterministically.
- **HotpotQA dev distractor v1**: 80 examples sampled deterministically.

Both datasets are loaded from local project caches (`data/squad_dev_v1.1.json`, `data/hotpot_dev_distractor_v1.json`).

### 2.4 Model and Decoding

- Model: `google/flan-t5-base` (cached locally).
- Decoding: Greedy search, short-answer generation.
- Pack budget: 180 tokens.
- Framework: Transformers + PyTorch (`torch==2.11.0+cu130`) on CUDA.

### 2.5 Pre-run Verification

Prior to the full benchmark, the following checks were performed:

- Unit tests: `.venv/bin/python -m unittest discover -s tests` → 2 tests passed.
- Compilation: `.venv/bin/python -m py_compile` on all benchmark and source files → passed.
- Smoke test: 1 SQuAD example × 2 strategies on CUDA/GB10 → passed (`artifacts/generation_smoke.json`).
- Calibration: 8-example runs on both datasets → passed.

---

## 3. Results

### 3.1 SQuAD (n = 80)

Table 1 reports the difference (persona-conditioned minus source-order) on SQuAD limit-80.

| Metric | Delta (Persona − Source) |
|---|---|
| Answer F1 | +61.80 |
| Exact Match | +55.00 |
| Kept Evidence Recall | +71.77 |
| Oracle Answerability F1 | +71.25 |
| Token Budget Change | +0.15% |

**Latency and throughput:**

| Metric | Value |
|---|---|
| Throughput | 28.77 samples/sec |
| Generated-token throughput | 174.43 tok/sec |
| p50 latency | 26.21 ms |
| p95 latency | 58.24 ms |
| Avg. latency difference | −5.40 ms (persona faster) |

**Resource telemetry:** Max CUDA allocator usage approximately 526 MB during prior calibration; full-run telemetry persisted in artifacts with UMA `MemAvailable` and process RSS/PSS.

### 3.2 HotpotQA (n = 80)

Table 2 reports the difference (persona-conditioned minus source-order) on HotpotQA limit-80.

| Metric | Delta (Persona − Source) |
|---|---|
| Answer F1 | +19.89 |
| Exact Match | +17.50 |
| Kept Evidence Recall | +33.52 |
| Oracle Answerability F1 | +26.25 |
| Token Budget Change | +0.44% |

**Latency and throughput:**

| Metric | Value |
|---|---|
| Throughput | 24.45 samples/sec |
| Generated-token throughput | 158.31 tok/sec |
| p50 latency | 29.03 ms |
| p95 latency | 65.44 ms |
| Avg. latency difference | −7.42 ms (persona faster) |

### 3.3 Interpretation

The decoding-survival hypothesis is supported in both tested settings. The persona-conditioned packer's evidence-retention gains translate into large answer-quality improvements on SQuAD (+61.80 F1) and material improvements on multi-hop HotpotQA (+19.89 F1). These gains are achieved at token-neutral budgets (+0.15% and +0.44% respectively), confirming that the improvement stems from ordering rather than budget expansion. Latency was slightly lower for persona-packed prompts in both runs, though the magnitude of the latency difference (5–7 ms) is small relative to p95 latency and may not be robust across different hardware or sample distributions.

The substantially larger effect on SQuAD versus HotpotQA is consistent with the task structure: SQuAD questions are typically answerable from a single evidence fragment, so retaining the correct fragment is often sufficient. HotpotQA requires multi-hop reasoning across fragments, and even when more gold evidence is retained, the model must still compose an answer from multiple pieces—a harder decoding task where the simple lexical persona packer provides less targeted assistance.

---

## 4. Limitations

1. **Single model.** Only `google/flan-t5-base` was tested. The decoding-survival effect may differ substantially for causal language models, chat-tuned models, or models of different scale. No claim is made about generalization to other architectures.

2. **Single pack budget.** All experiments used a 180-token budget. The magnitude and even the direction of the effect may change at different budgets (e.g., very large budgets where truncation is rare, or very small budgets where even persona-conditioned packing cannot retain sufficient evidence).

3. **Greedy decoding only.** Sampling-based or beam-search decoding may interact differently with persona-ordered contexts. The current results do not characterize this interaction.

4. **Small, deterministic samples.** 80 examples per dataset is a calibration-scale pilot, not a statistically powered evaluation. The deterministic sampling means no confidence intervals or significance tests are reported. The large effect sizes on SQuAD are unlikely to reverse with more data, but the HotpotQA delta of +19.89 F1 has wider uncertainty.

5. **HotpotQA absolute performance.** While the relative gain on HotpotQA is material, absolute answer quality remains lower than on SQuAD. This is expected given the multi-hop reasoning requirement but limits the practical applicability of the current packer on such tasks without further refinement.

6. **Heuristic packer.** The persona-conditioned orderer uses simple lexical relevance scoring. The result validates the mechanism—that ordering matters for decoding quality—but does not validate any particular optimized ordering system. A learned or more sophisticated ranker may yield different (potentially larger or smaller) effects.

7. **Hardware specificity.** All runs were on a single GB10/CUDA machine. Latency and throughput numbers are hardware-specific and should not be compared across platforms.

8. **No comparison to other ordering baselines.** Only source-order was tested as a baseline. Random-order, reverse-order, or relevance-only (without persona conditioning) baselines were not evaluated, so the specific contribution of persona conditioning versus generic relevance ordering is not isolated.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Code available in project | Yes: `src/context_orderer.py`, `experiments/generation_benchmark.py` |
| Unit tests | 2 tests passing |
| Datasets specified | SQuAD v1.1 dev, HotpotQA dev distractor v1 (local copies) |
| Model specified | `google/flan-t5-base` (HuggingFace cached) |
| Pack budget specified | 180 tokens |
| Decoding strategy specified | Greedy search |
| Sample size specified | 80 per dataset, deterministic |
| Hardware specified | GB10, CUDA, PyTorch 2.11.0+cu130 |
| Result artifacts persisted | Yes (6 JSON files in `artifacts/`) |
| Random seeds | Deterministic sampling; no stochastic decoding |
| Full telemetry recorded | Yes: latency, throughput, CPU/memory, CUDA allocator, UMA meminfo |

---

## 6. Conclusion

Persona-conditioned context ordering produces large and material answer-quality improvements over source-order packing when evaluated end-to-end with `google/flan-t5-base` greedy decoding on SQuAD (+61.80 F1) and HotpotQA (+19.89 F1), at token-neutral budgets and with no latency penalty. The decoding-survival hypothesis is supported in the tested setting: prompt-level evidence-retention gains do survive the decoding process.

These results should be interpreted as a mechanism validation at calibration scale, not as a production-ready system evaluation. The effect is bounded by a single small model, a single token budget, greedy decoding, and 80-example deterministic samples per dataset. The recommended follow-up is same-mechanism replication on a second small chat model and a budget sweep, rather than development of a new generic successor system.

---

## Referenced Artifacts

### Result files
- `artifacts/generation_summary.json`
- `artifacts/generation_benchmark_squad_flan_t5_base_limit80.json`
- `artifacts/generation_benchmark_hotpot_flan_t5_base_limit80.json`
- `artifacts/generation_benchmark_hotpot_flan_t5_base_limit8.json`
- `artifacts/generation_benchmark_flan_t5_base_limit8.json`
- `artifacts/generation_smoke.json`

### Source and configuration files
- `src/context_orderer.py`
- `experiments/generation_benchmark.py`
- `experiments/longdoc_squad_benchmark.py`
- `tests/test_context_orderer.py`
- `data/squad_dev_v1.1.json`
- `data/hotpot_dev_distractor_v1.json`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `run_notes.md`
- `README.md`
- `README.parent.md`

### Paper pipeline artifacts
- `papers/.../evidence_bundle.json`
- `papers/.../claim_ledger.json`
- `papers/.../publication_manifest.json`
