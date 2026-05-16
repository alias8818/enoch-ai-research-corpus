# Fieldwise Recall Probe: Real-Trace Multi-Model Validation

> **AI Provenance Notice.** This draft was generated entirely by AI from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

We investigate whether field-aware context selection—targeting specific document fields such as title, body, table, footnote, appendix, and code—yields measurable recall accuracy improvements over body-only or title-only pruning when answering questions grounded in real project trace data. Using 24 composite examples derived from parent project artifacts (run notes, source files, reports, and JSON metadata), we compare four context-selection strategies (full context, body-only pruning, keyword-line retrieval, and field-aware targeted selection) across three model stacks: a deterministic substring oracle, SmolLM2-135M-Instruct, and Qwen2.5-0.5B-Instruct. Field-aware selection produces accuracy uplifts of 66.67 percentage points (deterministic), 25.00 pp (SmolLM2-135M), and 33.33 pp (Qwen2.5-0.5B) over body-only pruning. All three stacks exceed the pre-specified 5 pp uplift threshold. However, the dataset is small (24 examples), absolute LLM accuracy remains low (25% and 41.7% for the two local models), and results are confined to a single project's trace artifacts and sub-billion-parameter models. The current project artifacts support this finding in the tested setting; this does not prove the method works universally.

## 1. Introduction

Retrieval-augmented generation and long-context language model pipelines routinely face a context-pruning problem: not all retrieved content is equally relevant, and including irrelevant context can degrade answer quality while consuming compute budget. A common baseline is body-only or title-only pruning, which retains the main textual content of a document but discards peripheral fields such as tables, footnotes, appendices, and code blocks.

The fieldwise recall probe methodology tests whether a context selector that is aware of document field structure can recover answer-relevant evidence that body-only pruning would discard. Prior work within this project lineage established the probe on synthetic documents; the present study replaces fabricated documents with real parent project trace data and extends validation to two additional local language model stacks.

The central question is: does field-aware context selection provide a consistent accuracy uplift over body-only pruning on real (non-fabricated) trace data, across multiple model stacks, at a magnitude exceeding a pre-registered 5 percentage-point threshold?

## 2. Method

### 2.1 Real-Trace Dataset Construction

The harness (`scripts/real_trace_multimodel_probe.py`) builds composite QA records from parent project artifacts including `run_notes.md`, source files, reports, JSON metadata, and summary artifacts. Every gold answer is a substring of a parent trace snippet; the only synthetic component is the grouping of real snippets into balanced fieldwise records.

The resulting dataset contains 24 grounded examples, with 4 examples per field across six fields: `title`, `body`, `table`, `footnote`, `appendix`, and `code`. Source provenance and answer pools are recorded in `item_pools.json`.

### 2.2 Context-Selection Strategies

Four baselines are compared:

1. **Full context**: The entire document is provided without pruning.
2. **Body-only pruning**: Only the body field is retained; all other fields are discarded.
3. **Keyword-line retrieval**: Lines containing query keywords are extracted regardless of field.
4. **Field-aware targeted selection**: The selector identifies which field(s) are likely to contain the answer and retains only those fields.

### 2.3 Model Stacks

Three model stacks are evaluated:

1. **Deterministic substring oracle**: A non-LLM control that checks whether the gold answer appears as a substring in the provided context. This isolates the effect of context selection from model capability.
2. **SmolLM2-135M-Instruct** (`HuggingFaceTB/SmolLM2-135M-Instruct`): A 135M-parameter instruction-tuned model, served via local Transformers with cached weights.
3. **Qwen2.5-0.5B-Instruct** (`Qwen/Qwen2.5-0.5B-Instruct`): A 0.5B-parameter instruction-tuned model, served via local Transformers with cached weights.

### 2.4 Scoring Protocol

Accuracy is computed as the fraction of examples for which the model's output contains the gold answer as a substring (strict match). Uplift is the difference in accuracy (in percentage points) between field-aware targeted selection and body-only pruning for the same model stack.

### 2.5 Kill Condition

The branch-specific kill condition was pre-registered: finalize negative if real traces fail to show any consistent field-aware uplift over body/title-only pruning across at least two local model stacks (minimum +5 pp on fewer than half of tested model/split pairs), or if the apparent signal is explained solely by fabricated identifiers absent from real traces.

## 3. Results

### 3.1 Accuracy and Uplift

The grounded accuracy metrics from the full run are as follows:

| Model Stack | Body-Only Acc | Field-Aware Acc | Uplift (pp) |
|---|---|---|---|
| Deterministic oracle | 33.33% | 100.00% | +66.67 |
| SmolLM2-135M-Instruct | 0.00% | 25.00% | +25.00 |
| Qwen2.5-0.5B-Instruct | 8.33% | 41.67% | +33.33 |

All three stacks exceed the +5 pp uplift threshold. The deterministic oracle result confirms that the gold answers are present in the field-aware context but absent from the body-only context for a substantial fraction of examples, establishing that the uplift is attributable to context selection rather than model capability.

### 3.2 Absolute Accuracy

Despite the consistent uplift, absolute accuracy for the two local LLMs remains low. SmolLM2-135M-Instruct achieves only 25% even with field-aware context; Qwen2.5-0.5B-Instruct reaches 41.67%. The body-only condition yields 0% and 8.33% respectively. These low baselines mean that the uplift, while real, operates over a range where model generation quality is a significant bottleneck.

### 3.3 Resource Usage

The full run completed in 18.76 seconds wall-clock time with 119% CPU utilization and a maximum RSS of 3,043,396 KB. Per-metric telemetry recorded p95 latency, samples/s, output tokens/s, CPU percent, process RSS, UMA `MemAvailable`, `SwapFree`, HugeTLB status, Torch CUDA allocator stats, sampled GPU utilization, and power draw. On the GB10 platform, nvidia-smi memory was not used as available-memory evidence.

### 3.4 Prediction Volume

The full run produced 288 predictions (24 examples × 4 baselines × 3 model stacks), recorded in `predictions.csv`. Summary metrics are recorded as 12 strict-JSON rows in `summary.json`.

### 3.5 Kill Condition Assessment

The branch-specific kill condition is not met. Field-aware context beat body/title-only pruning by more than 5 percentage points for both local LLMs and for the deterministic control on real parent traces. The signal does not depend on fabricated identifiers.

## 4. Limitations

1. **Small dataset.** The evaluation uses only 24 composite real-trace examples. This is sufficient for the queued successor validation purpose but does not constitute a production-scale benchmark. Statistical power to detect small effect sizes is limited.

2. **Low absolute LLM accuracy.** Both tested models are sub-billion-parameter instruction-tuned models. Their absolute accuracy remains low even under the best context condition, making it difficult to assess whether the observed uplift would persist, shrink, or grow with more capable models.

3. **Single project domain.** All trace data derives from a single parent project's artifacts. Generalization to other domains, document types, or trace structures is not established.

4. **Narrow model coverage.** Only two local LLM stacks were tested. Results may differ for larger models, different serving stacks (e.g., llama.cpp, vLLM), or closed-api models.

5. **Synthetic grouping.** While gold answers are grounded in real trace snippets, the grouping of those snippets into balanced fieldwise records is synthetic. This balancing may over-represent fields that are under-represented in natural document distributions.

6. **Substring matching.** The scoring protocol uses substring containment rather than semantic equivalence or normalized extraction. This may undercount correct answers phrased differently from the gold string and overcount partially overlapping outputs.

7. **No external replication.** Results have not been replicated by independent researchers or on different hardware.

8. **Hardware specificity.** Resource telemetry is specific to the GB10 platform with its UMA memory architecture. nvidia-smi memory was not available as evidence on this platform.

## 5. Reproducibility Checklist

- **Code availability**: The probe harness is at `scripts/real_trace_multimodel_probe.py`. Compilation was verified via `python3 -m py_compile`.
- **Environment**: Python virtual environment created with `uv venv --python /usr/bin/python3 .venv`; CUDA PyTorch, Transformers, Accelerate, and Psutil installed project-locally.
- **Smoke test command**: `.venv/bin/python scripts/real_trace_multimodel_probe.py --per-field 2 --models HuggingFaceTB/SmolLM2-135M-Instruct Qwen/Qwen2.5-0.5B-Instruct --batch-size 4 --out artifacts/real_trace_multimodel_smoke`
- **Full run command**: `/usr/bin/time -v .venv/bin/python scripts/real_trace_multimodel_probe.py --per-field 4 --models HuggingFaceTB/SmolLM2-135M-Instruct Qwen/Qwen2.5-0.5B-Instruct --baselines full_context body_only_prune keyword_line_retrieval field_aware_targeted_fix --batch-size 4 --out artifacts/real_trace_multimodel`
- **Validation assertions**: Strict JSON load plus assertions for 24 examples, 12 summary rows, 288 prediction rows, parent-trace provenance, and ≥5 pp field-aware uplift over body-only for deterministic and both local LLM stacks.
- **Model identifiers**: `HuggingFaceTB/SmolLM2-135M-Instruct`, `Qwen/Qwen2.5-0.5B-Instruct` (cached locally).
- **Randomness control**: Deterministic oracle is fully deterministic. LLM generation parameters are not specified in the available artifacts; this is a gap in reproducibility documentation.
- **Resource evidence**: `/usr/bin/time -v` output captured in `time_stderr.log`; per-metric telemetry in `metadata.json`.

## 6. Conclusion

Field-aware context selection produces consistent accuracy uplifts over body-only pruning on real project trace data across three model stacks, including two sub-billion-parameter local LLMs. The uplifts (25–67 pp) exceed the pre-registered 5 pp threshold, and the deterministic oracle confirms that the mechanism is context-availability rather than model capability. However, the evidence is bounded: the dataset is small, absolute LLM accuracy is low, model and domain coverage are narrow, and no external replication exists. The current project artifacts support this finding in the tested setting. The project decision recommends archiving these real-trace multi-model artifacts and only initiating a new project if a larger public corpus and stronger serving-stack benchmark are explicitly selected.

## Referenced Artifacts

### Result files
- `artifacts/real_trace_multimodel/summary.json` — 12 strict-JSON metric rows
- `artifacts/real_trace_multimodel/time_stderr.log` — `/usr/bin/time -v` resource evidence
- `artifacts/real_trace_multimodel/run_stdout.json` — captured command output
- `artifacts/real_trace_multimodel/report.md` — human-readable result summary
- `artifacts/real_trace_multimodel/metadata.json` — model, baseline, throughput, CPU/RSS, UMA meminfo, accelerator telemetry
- `artifacts/real_trace_multimodel/predictions.csv` — 288 prediction rows
- `artifacts/real_trace_multimodel/item_pools.json` — source provenance and answer pools
- `artifacts/real_trace_multimodel/trace_examples.jsonl` — 24 grounded examples

### Smoke-test artifacts
- `artifacts/real_trace_multimodel_smoke/report.md`
- `artifacts/real_trace_multimodel_smoke/metadata.json`
- `artifacts/real_trace_multimodel_smoke/predictions.csv`
- `artifacts/real_trace_multimodel_smoke/summary.json`
- `artifacts/real_trace_multimodel_smoke/item_pools.json`
- `artifacts/real_trace_multimodel_smoke/trace_examples.jsonl`

### Example-generation artifacts
- `artifacts/real_trace_multimodel_examples/metadata.json`
- `artifacts/real_trace_multimodel_examples/item_pools.json`
- `artifacts/real_trace_multimodel_examples/trace_examples.jsonl`

### Project and pipeline artifacts
- `.omx/project_decision.json` — finalize_positive decision, hypothesis supported, confidence medium
- `.omx/metrics.json` — session metrics
- `run_notes.md` — execution log and scientific state
- `scripts/real_trace_multimodel_probe.py` — probe harness
- `scripts/llm_fieldwise_probe.py` — LLM fieldwise probe script
- `scripts/fieldwise_recall_probe.py` — fieldwise recall probe script
- `.omx/project.json` — project configuration
- `prompts/resume.md`, `prompts/initial.md` — session prompts

### Paper pipeline artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/README.md`
