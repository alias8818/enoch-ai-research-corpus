# LLM Code Navigation Context-Packer Evaluation: Import-Neighborhood vs. Lexical RAG Contexts for Code Navigation with a Small Instruction Model

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifacts. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We evaluate two context-packing strategies—lexical RAG and import-neighborhood—for providing code navigation context to a small instruction-tuned language model (Qwen2.5-3B-Instruct). Using a 150-example stratified slice of long-form code navigation queries over the vllm repository, plus 60 no-answer probes, we measure strict and tolerant accuracy, abstention rates, and calibration. Import-neighborhood context yields directionally higher accuracy across all metrics: +12.0 percentage points strict file-line accuracy, +29.3 points ±2-line accuracy, +25.3 points signature-plus-path accuracy, and +9.3 points exact-signature accuracy over lexical RAG. However, import-neighborhood context also produces substantially worse calibration, false-answering 36.7% of no-answer probes (versus 1.7% for lexical RAG) and achieving a worse Brier score (0.535 vs. 0.401). Absolute accuracy remains low for both packers, indicating that a 3B-parameter model struggles to extract and copy exact code navigation answers even when the target is present in context. These results support the hypothesis that import-neighborhood packing improves answer accuracy in the tested setting, but the calibration degradation represents a significant trade-off. Confidence in this finding is medium; external replication with stronger models and additional repositories is needed before drawing broader conclusions.

---

## 1. Introduction

Code navigation—locating the definition site of a function, class, or symbol given a reference in source code—is a common developer task and a potential application of language models. A typical approach retrieves relevant code context and presents it to a model, which then predicts the target location. The quality of the retrieved context is a primary determinant of answer quality.

Two natural context-packing strategies are:

1. **Lexical RAG**: Retrieve code fragments by lexical similarity (e.g., BM25 or embedding-based search) between the query and source text.
2. **Import-neighborhood**: Retrieve code fragments by following import relationships—gathering the definition sites of imported symbols and the base classes of subclasses, exploiting the structural dependencies that code navigation queries typically target.

The hypothesis under evaluation is that import-neighborhood context provides more relevant signal for code navigation queries than lexical RAG context, leading to higher answer accuracy when consumed by an LLM. This report presents a controlled comparison of these two packers using a single local model, a fixed evaluation slice, and multiple accuracy and calibration metrics.

---

## 2. Method

### 2.1 Evaluation Harness

We implemented `scripts/llm_context_packer_eval.py`, a Python harness that:

1. Loads the stratified evaluation slice from `data/long_form_code_nav_pilot.jsonl`.
2. For each example, rebuilds two context windows: one using lexical RAG retrieval and one using import-neighborhood retrieval. Both packers draw from the same repository source.
3. Prompts the model to answer from context only, requesting the target file path, line number, and function/class signature.
4. Scores each prediction against the weak label using four accuracy metrics (strict file-line, ±2-line tolerant, signature-plus-path, exact signature) and records abstention and calibration outcomes.
5. For no-answer probes (queries with no valid target in the repository), records whether the model correctly abstains or falsely produces an answer.
6. Performs gold spot checks by verifying a stratified subset of weak labels against the actual repository source.

### 2.2 Context Construction

Both packers retrieve up to `top-k=8` code fragments, truncated to a maximum of 18,000 characters and 8,192 input tokens. The lexical RAG packer ranks fragments by text similarity to the query. The import-neighborhood packer ranks fragments by structural proximity: definition sites of imported symbols, base-class definitions for subclass queries, and call-site context for imported call-site queries.

### 2.3 Model and Inference

We use `Qwen/Qwen2.5-3B-Instruct`, a 3-billion-parameter instruction-tuned model, loaded locally via Hugging Face Transformers with CUDA. Generation is constrained to a maximum of 48 new tokens. Batch size is 8. The model is instructed to answer only from the provided context and to abstain if the answer is not present.

### 2.4 Evaluation Metrics

- **Strict file-line accuracy**: The predicted file path and line number exactly match the label.
- **±2-line accuracy**: The predicted file path matches and the predicted line is within ±2 lines of the label.
- **Signature-plus-path accuracy**: The predicted function/class signature and file path match the label (line number may differ).
- **Exact signature accuracy**: The predicted signature exactly matches the label signature.
- **Answerable abstention rate**: Fraction of answerable queries where the model abstains.
- **No-answer abstention rate**: Fraction of no-answer probes where the model correctly abstains.
- **False answer rate on no-answer probes**: Fraction of no-answer probes where the model produces a non-abstention answer.
- **Brier score**: Mean squared error of the model's confidence estimates against the binary correctness outcome, measuring calibration.

---

## 3. Results

### 3.1 Aggregate Metrics

Table 1 reports aggregate metrics across the 150 answerable examples and 60 no-answer probes.

**Table 1.** LLM answer-generation metrics by context packer.

| Packer | Strict file-line acc | ±2-line acc | Signature+path acc | Exact signature acc | Answerable abstain | No-answer abstain | False answer (no-answer) | Brier |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Lexical RAG | 2.7% | 4.0% | 2.0% | 1.3% | 58.7% | 98.3% | 1.7% | 0.401 |
| Import-neighborhood | 14.7% | 33.3% | 27.3% | 10.7% | 31.3% | 63.3% | 36.7% | 0.535 |

Import-neighborhood context yields directionally higher accuracy on every accuracy metric. The largest gains appear in ±2-line accuracy (+29.3 points) and signature-plus-path accuracy (+25.3 points), suggesting that the model frequently identifies the correct region and signature but imprecisely locates the exact line.

### 3.2 Accuracy by Query Type

Table 2 reports exact-signature accuracy broken down by query type.

**Table 2.** Exact-signature accuracy by query type.

| Query type | Lexical RAG | Import-neighborhood |
|---|---:|---:|
| Import-definition | 0.0% | 14.0% |
| Subclass-base | 2.8% | 22.2% |
| Imported call-sites | 1.6% | 1.6% |

Import-neighborhood substantially outperforms lexical RAG on import-definition and subclass-base queries, which align with the structural retrieval logic of the packer. Imported call-sites remain difficult for both packers (1.6% exact signature each), suggesting that neither context strategy provides sufficient signal for this query type at the 3B model scale.

### 3.3 Calibration and Abstention

The two packers exhibit markedly different abstention and calibration profiles. Lexical RAG is conservative: it abstains on 58.7% of answerable queries but false-answers only 1.7% of no-answer probes, yielding a Brier score of 0.401. Import-neighborhood is less conservative: it abstains on only 31.3% of answerable queries but false-answers 36.7% of no-answer probes, yielding a worse Brier score of 0.535.

This represents a clear accuracy–calibration trade-off: import-neighborhood context encourages the model to attempt more answers (benefiting accuracy when the target is present) but also to produce confident wrong answers when no valid target exists.

### 3.4 Gold Spot Checks

We verified 30 stratified weak labels against the vllm repository source. All 30 labels had the requested `def` or `class` near the labelled target line, confirming that the weak labels are not systematically misaligned with the source. No weak-label kill condition was triggered.

### 3.5 Runtime and Resource Characteristics

- Wall-clock time: 890.33 seconds for 420 total queries (2 packers × 210 probes).
- Throughput: 0.472 packer-items/s, 2,149 total tokens/s.
- Per-generation latency (batch-normalized): p50 1.97 s, p95 2.18 s.
- GPU utilization: 95% (sampled via `nvidia-smi`).

---

## 4. Limitations

1. **Single small model.** All results are from Qwen2.5-3B-Instruct. Larger or differently-trained models may exhibit different accuracy–calibration trade-offs. The low absolute accuracy may be primarily a model-capability limitation rather than a context-packer limitation.

2. **Single repository.** The evaluation uses only the vllm repository. Import-neighborhood structure may vary substantially across codebases with different import patterns, languages, or project sizes.

3. **Weak labels.** Although 30/30 gold spot checks passed, the full label set has not been manually verified. Remaining label noise could affect both accuracy measurement and model behavior.

4. **No production validation.** This evaluation is a local prototype harness run on a single GPU. It has not been validated in a production deployment, under concurrent load, or across multiple hardware configurations.

5. **Calibration degradation.** The import-neighborhood packer's 36.7% false-answer rate on no-answer probes and worse Brier score represent a significant practical concern. A deployed system using import-neighborhood context would need additional safeguards against hallucinated navigation targets.

6. **Limited query-type coverage.** Imported call-site queries remain near floor for both packers. The evaluation does not address whether any context strategy can adequately serve this query type.

7. **Deterministic extractor comparison absent.** The run notes indicate that absolute LLM accuracy is "much lower than the deterministic extractor," but the deterministic extractor metrics are not included in the current artifact set, so no quantitative comparison is reported here.

8. **No cross-model or cross-repository replication.** The findings are bounded to the tested setting. Whether the directional accuracy advantage of import-neighborhood persists across models and repositories remains an open question.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Evaluation harness script | Available: `scripts/llm_context_packer_eval.py` |
| Input dataset | Available: `data/long_form_code_nav_pilot.jsonl` |
| Model identifier | Specified: `Qwen/Qwen2.5-3B-Instruct` (Hugging Face snapshot `aa8e72537993ba99e69dfaafa59ed015b17504d1`) |
| Hyperparameters documented | Yes: top-k=8, max-input-tokens=8192, max-context-chars=18000, max-new-tokens=48, batch-size=8 |
| Aggregate metrics JSON | Available: `data/llm_context_packer_eval.json` |
| Row-level predictions | Available: `data/llm_context_packer_predictions.jsonl` (420 rows) |
| Gold spot-check results | Recorded in `data/llm_context_packer_eval.json` |
| Captured stdout reports | Available in `artifacts/` directory (5 files) |
| Python syntax verification | Passed: `python3 -m py_compile` on harness script |
| JSON validity verification | Passed: `python3 -m json.tool` on metrics JSON |
| Row count verification | Passed: 420 rows as expected |
| Hardware specified | Partial: GPU utilization sampled; specific GPU model not recorded in artifacts |
| Random seeds | Not recorded in available artifacts |

---

## 6. Conclusion

In the tested setting—a 3B-parameter instruction model answering code navigation queries over the vllm repository—import-neighborhood context packing provides directionally higher accuracy than lexical RAG context across all measured accuracy metrics, with the largest gains on import-definition and subclass-base query types. However, import-neighborhood context also produces substantially worse calibration, with a 36.7% false-answer rate on no-answer probes and a Brier score of 0.535 versus 0.401 for lexical RAG. Absolute accuracy remains low for both packers, suggesting that model capability is a binding constraint at this scale.

The current project artifacts support the finding that import-neighborhood packing improves answer accuracy in the tested setting. This does not establish that the method works universally or that the accuracy gain is worth the calibration cost in deployment. The project decision recommends using the saved evaluation artifacts to guide stronger-model or calibration work only if a separate, concrete benchmark is explicitly desired. External replication with larger models, additional repositories, and explicit calibration mitigation strategies is needed before drawing broader conclusions.

---

## Referenced Artifacts

### Run notes and decision
- `run_notes.md` — Execution log, metrics tables, interpretation, and verification steps
- `.omx/project_decision.json` — Project decision (finalize_positive), hypothesis status (supported), confidence (medium)
- `.omx/metrics.json` — Session metrics

### Evaluation harness and data
- `scripts/llm_context_packer_eval.py` — LLM answerer evaluation harness
- `data/long_form_code_nav_pilot.jsonl` — Input dataset (150 answerable + 60 no-answer)
- `data/llm_context_packer_eval.json` — Aggregate metrics, gold spot-check results, resource telemetry
- `data/llm_context_packer_predictions.jsonl` — 420 row-level predictions (2 packers × 210 probes)

### Parent project artifacts
- `scripts/code_rag_answer_eval.py` — Parent extractive evaluation script
- `scripts/long_form_nav_pilot.py` — Parent pilot script
- `data/parent_code_rag_answer_eval.json` — Parent extractive evaluation metrics
- `data/parent_code_rag_answer_predictions.jsonl` — Parent extractive predictions

### Captured stdout reports
- `artifacts/llm_context_packer_eval_stdout.json`
- `artifacts/llm_context_packer_eval_qwen3b_batch_smoke_stdout.json`
- `artifacts/llm_context_packer_eval_qwen3b_smoke_stdout.json`
- `artifacts/llm_context_packer_eval_smoke2_stdout.json`
- `artifacts/llm_context_packer_eval_smoke_stdout.json`

### Paper and audit artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
