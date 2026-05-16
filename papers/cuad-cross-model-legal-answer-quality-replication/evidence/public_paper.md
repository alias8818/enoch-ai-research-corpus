# CUAD Cross-Model Legal Answer Quality Replication: Adaptive Indexed Packing Under Varying Retrieval Conditions

> **AI Provenance Notice.** This draft was generated entirely by AI from automated research artifacts (run notes, evidence bundles, claim ledgers, and benchmark outputs) produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We report a cross-model replication study of adaptive indexed packing for legal question answering on the CUAD dataset. The parent project demonstrated that adaptive indexed packing—constructing prompts with indexed clause headers and budget-constrained segment selection—improved downstream LLM answer quality over vanilla flat-prompt construction when using Qwen2.5-7B-Instruct with forced-gold retrieval. This replication substitutes Phi-4-mini-instruct (3.84B parameters, Q4_K_M quantization) as the answerer model. Under forced-gold retrieval isolation (n=30), indexed packing yielded +12.26 F1 points and +35.0 answer-span-retention points over vanilla packing at identical budgets, clearing the pre-registered cross-model threshold. Under pure BM25 retrieval, results were mixed: top-3 retrieval found 0/30 gold contracts and the F1 delta was +1.85 (below threshold), while top-10 retrieval found 4/30 gold contracts and the F1 delta was +5.04 (above threshold) but with zero substring hits in both conditions. The overall hypothesis status is mixed: cross-model answer-quality transfer is reproduced under controlled retrieval, but retrieval recall remains the binding bottleneck under realistic retrieval conditions. Confidence is medium; evidence strength is strong within the tested setting.

---

## 1. Introduction

Long-context legal question answering requires selecting relevant contract segments from documents that frequently exceed model context windows. Adaptive indexed packing addresses this by constructing prompts that include indexed clause headers and budget-constrained segment selection, as opposed to vanilla flat-prompt construction that naively truncates or concatenates retrieved passages.

The parent project (Qwen2.5-7B-Instruct, n=100, forced-gold retrieval) demonstrated that indexed packing improves downstream answer quality. A natural question is whether this improvement transfers across answerer models or is an artifact of the specific model's instruction-following behavior. This replication study addresses that question by substituting a materially different local answerer—Phi-4-mini-instruct—while holding the packing logic, dataset, and evaluation pipeline constant.

A secondary question concerns the interaction between packing strategy and retrieval quality. The parent project used forced-gold retrieval (injecting the gold contract into the retrieved set), which isolates the packing effect but overestimates realistic retrieval conditions. This study additionally tests pure BM25 retrieval at top-3 and top-10 to characterize where retrieval recall, rather than prompt construction, becomes the binding constraint.

---

## 2. Method

### 2.1 Adaptive Indexed Packing

The packing method (implemented in `src/evidence_quilt.py`) constructs two prompt variants for each question–contract pair:

- **Vanilla packing**: Concatenates retrieved contract segments in retrieval rank order, truncated to the token budget.
- **Indexed packing**: Prepends indexed clause headers (e.g., "Section 3.1: Termination") to each segment and selects segments to maximize coverage under the same token budget, using the adaptive indexed-packing algorithm.

Both variants operate under identical token budgets (512 and 1024 tokens) and receive the same retrieved segments as input. The comparison therefore isolates the effect of prompt structure on downstream answer quality.

### 2.2 Benchmark Harness

The benchmark harness (`scripts/run_cuad_llm_answer_quality_benchmark.py`) was acquired from the parent project and verified via unit tests (`tests/test_evidence_quilt.py`, 4 tests passed) and compilation checks prior to execution.

### 2.3 Answerer Model

The cross-model replication answerer is Phi-4-mini-instruct-Q4_K_M (3.84B parameters, 131k training context metadata), served via llama.cpp server with the following configuration:

- Host: 127.0.0.1, Port: 8088
- Context length: 4096, GPU layers: 99, Batch size: 1024, Micro-batch: 256
- Flash attention enabled, memory mapping disabled
- Maximum answer tokens: 96, Request timeout: 180s

The server endpoint was verified via `/v1/models` before each benchmark run and stopped between runs.

### 2.4 Dataset

The CUAD dataset (CUADv1.json) contains 510 contracts with 1,545 eligible long-contract/deep-answer examples. For each experimental condition, n=30 examples were sampled. Average contract length was approximately 7,956 tokens (p95: 25,583 tokens).

### 2.5 Retrieval Conditions

Three retrieval conditions were tested:

1. **Forced-gold retrieval**: The gold contract is injected into the top-k=3 retrieved set, guaranteeing that answer-relevant content is available to both packers. This isolates the packing effect.
2. **Pure BM25 top-3**: Standard BM25 retrieval without forced gold. Top-3 retrieved contracts per question.
3. **Pure BM25 top-10**: Standard BM25 retrieval without forced gold. Top-10 retrieved contracts per question.

### 2.6 Evaluation Metrics

- **LLM F1**: Token-level F1 between the model's answer and the gold answer span.
- **Substring hit**: Binary indicator of whether the gold answer span appears as a substring in the model's output.
- **Answer-span retention**: Proportion of examples where the model's output retains meaningful overlap with the gold answer span.
- **Prompt construction latency**: Wall-clock time to construct the prompt (p95 reported).
- **LLM request latency and throughput**: p95 latency and mean token throughput per request.

### 2.7 Kill Condition

The branch-specific kill condition required that, after running at least one materially different local answerer on ≥30 native CUAD examples, adaptive indexed packing improve downstream LLM answer quality by at least +2.0 F1 points or +5.0 substring-hit points versus vanilla under the same budget/retrieval setting. Failure of all locally available non-credentialed answerers to run after concrete serving attempts would also trigger finalization as negative.

---

## 3. Results

### 3.1 Forced-Gold Retrieval (n=30, budgets 512 and 1024)

Under forced-gold retrieval, indexed packing substantially outperformed vanilla packing:

| Metric | Indexed | Vanilla | Delta |
|---|---|---|---|
| LLM F1 | 0.1614 | 0.0388 | +12.26 |
| Substring hit | 0.0333 | 0.0 | +3.33 |
| Answer-span retention | 0.35 | 0.0 | +35.0 |

This clears the pre-registered kill threshold on F1 (+2.0 points) for a second, materially different local answerer.

Prompt construction remained fast with no budget overruns: indexed p95 23.09 ms, vanilla p95 15.78 ms. LLM request latency was higher for indexed prompts (p95 2,093.70 ms, mean throughput 989.27 tok/s/request) than vanilla (p95 1,712.62 ms, mean throughput 2,226.93 tok/s/request), consistent with indexed prompts providing more structured context that the model processes more slowly.

Runtime: 160.03 s. GPU utilization rose from 0% to 95%; power from 13.85 W to 51.58 W; temperature from 58 °C to 72 °C.

### 3.2 Pure BM25 Top-3 Retrieval (n=30, budgets 512 and 1024)

Pure BM25 top-3 retrieved the gold contract for 0 of 30 sampled examples. Both indexed and vanilla answer-span retention were 0.0.

| Metric | Indexed | Vanilla | Delta |
|---|---|---|---|
| LLM F1 | 0.0561 | 0.0376 | +1.85 |
| Substring hit | 0.0 | 0.0 | 0.0 |
| Answer-span retention | 0.0 | 0.0 | 0.0 |

The +1.85 F1 delta does not clear the kill threshold. This result is best interpreted as retrieval-starved and inconclusive for answer-quality transfer rather than as evidence of packer failure: when the gold contract is absent from the retrieved set, neither packer can provide answer-relevant content.

Runtime: 154.04 s. GPU utilization 0% → 95%; power 12.12 W → 45.53 W; temperature 44 °C → 67 °C.

### 3.3 Pure BM25 Top-10 Retrieval (n=30, budgets 512 and 1024)

Pure BM25 top-10 retrieved the gold contract for 4 of 30 sampled examples. However, fixed budgets still produced 0.0 answer-span retention for both packers.

| Metric | Indexed | Vanilla | Delta |
|---|---|---|---|
| LLM F1 | 0.0880 | 0.0376 | +5.04 |
| Substring hit | 0.0 | 0.0 | 0.0 |
| Answer-span retention | 0.0 | 0.0 | 0.0 |

The +5.04 F1 delta clears the threshold, but zero substring hits and zero answer-span retention weaken the direct-span evidence. This supports a retrieval-generalization signal only weakly: indexed packing produces higher token-level overlap with gold answers even when exact spans are not recovered.

Runtime: 149.30 s. GPU utilization 0% → 95%; power 14.73 W → 48.80 W; temperature 62 °C → 73 °C.

### 3.4 Smoke Test (n=3, BM25-only, budget 512)

An initial smoke test with n=3 confirmed the pipeline executed end-to-end. Indexed F1 was 0.0556 versus vanilla 0.0, with no exact substring hits. This run validated the harness but is too small for inference.

---

## 4. Limitations

1. **Sample size.** All Phi-4-mini experiments used n=30 sampled examples. The parent Qwen2.5 run used n=100. Statistical power at n=30 is limited, and the F1 and substring-hit deltas should be interpreted with appropriate caution.

2. **Single cross-model answerer.** Only one additional answerer (Phi-4-mini-instruct) was tested beyond the parent Qwen2.5-7B-Instruct. The cross-model transfer finding is limited to these two models. Neither model is a legal-domain specialist; no cached legal-domain models were available in the local environment.

3. **Quantization effects.** Both models were run in Q4_K_M quantization. The effect of indexed packing may differ at higher precision or with larger models, but this was not tested.

4. **Retrieval bottleneck.** Pure BM25 retrieval is a poor retriever for CUAD's question style (top-3 found 0/30 gold contracts; top-10 found 4/30). The forced-gold retrieval condition isolates the packing effect but does not reflect realistic deployment. The mixed results under BM25 retrieval indicate that retrieval recall, not prompt packing, is the binding constraint in realistic settings.

5. **No external validation.** Results are limited to the local hardware and software environment described. No external replication has been performed.

6. **Answer-span retention metric.** The answer-span retention metric (0.35 vs. 0.0 in the forced-gold condition) captures a meaningful but coarse-grained notion of answer quality. The specific scoring methodology should be inspected in `src/evidence_quilt.py` before drawing strong conclusions.

7. **Budget constraints.** Budgets of 512 and 1024 tokens are small relative to the average contract length (~7,956 tokens, p95 ~25,583 tokens). Results may differ at larger budgets where vanilla packing can include more context.

8. **Automated provenance.** This draft and the underlying experiments were produced by an automated research pipeline. No human experimenter made real-time adjustments or qualitative judgments during execution.

---

## 5. Reproducibility Checklist

| Item | Status | Detail |
|---|---|---|
| Code available | Yes | `src/evidence_quilt.py`, `scripts/run_cuad_llm_answer_quality_benchmark.py`, `scripts/run_cuad_contract_latency_benchmark.py` |
| Unit tests | Passed | `tests/test_evidence_quilt.py` (4 tests) |
| Model specified | Yes | Phi-4-mini-instruct-Q4_K_M.gguf, 3.84B parameters |
| Server configuration recorded | Yes | llama-server command with all flags recorded in run notes |
| Dataset specified | Yes | CUADv1.json, 510 contracts, 1,545 eligible examples |
| Sample size reported | Yes | n=30 per condition (smoke: n=3) |
| Budgets reported | Yes | 512 and 1024 tokens |
| Retrieval conditions reported | Yes | Forced-gold top-3, pure BM25 top-3, pure BM25 top-10 |
| Metrics defined | Yes | LLM F1, substring hit, answer-span retention, latency, throughput |
| Kill condition pre-registered | Yes | +2.0 F1 or +5.0 substring-hit vs vanilla, ≥30 examples |
| Hardware monitored | Yes | GPU utilization, power, temperature recorded per run |
| Result artifacts stored | Yes | Summary JSON and row CSV per condition |
| Claim ledger audited | Yes | `claim_ledger.json` with confidence levels and forbidden wording |
| External replication | Not performed | Results are local to the tested environment |

---

## 6. Conclusion

This cross-model replication study produces a mixed result. Under forced-gold retrieval, adaptive indexed packing improves Phi-4-mini answer quality by +12.26 F1 points and +35.0 answer-span-retention points over vanilla packing, reproducing the parent project's finding with a materially different answerer model. This confirms that the indexed-packing benefit is not specific to Qwen2.5-7B-Instruct.

Under pure BM25 retrieval, the picture is less clear. At top-3, retrieval found zero gold contracts and the F1 delta was +1.85 (below threshold). At top-10, retrieval found 4/30 gold contracts and the F1 delta was +5.04 (above threshold), but substring hits remained zero in both conditions. The remaining bottleneck is retrieval recall rather than prompt construction: when the gold contract is absent or insufficiently represented in the retrieved set, no packing strategy can recover answer-relevant content.

The project decision is to finalize this branch as positive/mixed. If future work is pursued, it should target retrieval quality directly (e.g., category-aware or query-expanded BM25, or legal-specialized dense retrievers) rather than further cross-model packing replication.

---

## Referenced Artifacts

### Run notes and decision
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`

### Claim ledger and evidence bundle
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`

### Source code and tests
- `src/evidence_quilt.py`
- `scripts/run_cuad_llm_answer_quality_benchmark.py`
- `scripts/run_cuad_contract_latency_benchmark.py`
- `tests/test_evidence_quilt.py`

### Dataset
- `external/cuad/data/CUADv1.json`
- `external/cuad/data/train_separate_questions.json`
- `external/cuad/data/test.json`

### Result files — Forced-gold retrieval (Phi-4-mini, n=30)
- `artifacts/cuad_llm_phi4_goldforced_n30/cuad_llm_answer_quality_summary.json`
- `artifacts/cuad_llm_phi4_goldforced_n30/cuad_llm_answer_quality_rows.csv`

### Result files — Pure BM25 top-3 (Phi-4-mini, n=30)
- `artifacts/cuad_llm_phi4_bm25_n30/cuad_llm_answer_quality_summary.json`
- `artifacts/cuad_llm_phi4_bm25_n30/cuad_llm_answer_quality_rows.csv`

### Result files — Pure BM25 top-10 (Phi-4-mini, n=30)
- `artifacts/cuad_llm_phi4_bm25_top10_n30/cuad_llm_answer_quality_summary.json`
- `artifacts/cuad_llm_phi4_bm25_top10_n30/cuad_llm_answer_quality_rows.csv`

### Result files — Smoke test (Phi-4-mini, n=3)
- `artifacts/cuad_llm_phi4_bm25_smoke/cuad_llm_answer_quality_summary.json`
- `artifacts/cuad_llm_phi4_bm25_smoke/cuad_llm_answer_quality_rows.csv`

### Result files — Parent Qwen2.5 baseline (n=100, copied)
- `artifacts/cuad_llm_qwen25_n100/cuad_llm_answer_quality_summary.json`
- `artifacts/cuad_llm_qwen25_n100/cuad_llm_answer_quality_rows.csv`

### Prompts
- `prompts/initial.md`
- `prompts/resume.md`
