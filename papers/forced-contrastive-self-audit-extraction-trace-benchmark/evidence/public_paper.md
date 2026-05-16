# Forced Contrastive Self-Audit Extraction Trace Benchmark: A Harness and Baseline Evaluation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present the Forced Contrastive Self-Audit (FCSA) Extraction Trace Benchmark, a deterministic benchmark harness designed to evaluate whether language models can extract correct answers from structured documents while simultaneously producing a contrastive self-audit trace that justifies the extraction against planted distractor rationales. The benchmark comprises five seed tasks spanning invoice, clinical, meeting-notes, contract, and order domains, each containing gold answers, distractor candidate rationales, and required audit-check fields. We evaluate the harness against Qwen2.5-0.5B-Instruct served locally via a Transformers-backed OpenAI-compatible shim on CUDA. The model achieves a mean score of 0.5075 across five tasks with 3/5 answer correctness, but audit coverage is 0.0 on all tasks: the model never produces the required structured contrastive audit trace. Two distractor-heavy tasks are failed by selection of the distractor. These results establish a lower baseline for the FCSA benchmark and confirm that the harness and scoring pipeline function correctly, but they do not demonstrate that the forced contrastive self-audit mechanism is effective at this model scale. The current project artifacts support this finding in the tested setting.

---

## 1. Introduction

Structured information extraction from documents is a well-studied task, but the reliability of extracted outputs depends on whether models can articulate and defend their reasoning against plausible alternatives. A model that extracts a correct answer without distinguishing it from a planted distractor may appear correct by coincidence rather than by genuine discriminative reasoning.

The Forced Contrastive Self-Audit (FCSA) mechanism addresses this by requiring models to produce, alongside their extraction, a structured audit trace that explicitly contrasts the selected answer against distractor candidates. The hypothesis under test is that forcing such contrastive self-audit improves the discriminability of correct extractions from distractors.

This paper reports the construction of the FCSA benchmark harness, the seed task dataset, the deterministic scoring pipeline, and a baseline evaluation against a small instruct model. The results are mixed: the harness validates successfully and discriminates between good and poor outputs, but the evaluated model fails to produce any audit trace and succumbs to distractors on two of five tasks.

---

## 2. Method

### 2.1 Seed Task Design

Five forced contrastive extraction tasks were created across the following domains:

| Task | Domain | Extraction Target |
|------|--------|-----------------|
| 1 | Invoice | Invoice total |
| 2 | Clinical note | Medication dose |
| 3 | Meeting notes | Action item owner |
| 4 | Contract | Termination clause trigger |
| 5 | Purchase order | Shipping address |

Each task contains:

- A source document with embedded structured information.
- A gold answer.
- One or more planted distractor rationales: plausible but incorrect candidate answers with supporting context designed to mislead shallow extraction.
- Required contrastive self-audit check fields that the model must populate to demonstrate it has considered and rejected the distractor.

Tasks are stored in `data/seed_tasks.jsonl`.

### 2.2 Prompt Generation

The benchmark harness (`src/fcsa_benchmark.py`) renders each task into a deterministic prompt that instructs the model to:

1. Extract the target answer from the document.
2. Identify the distractor candidate(s).
3. Produce a structured contrastive audit trace explaining why the selected answer is correct and the distractor is not.

Rendered prompts are written to `results/prompts.jsonl` for reproducibility.

### 2.3 Scoring

The scoring pipeline evaluates four components per task:

- **Answer correctness** (binary or partial credit): whether the extracted answer matches the gold answer.
- **Evidence support**: whether the model cites supporting evidence from the document.
- **Distractor rejection**: whether the model correctly identifies and rejects the planted distractor.
- **Audit coverage**: whether the model populates all required contrastive self-audit check fields.

Scores are combined into a per-task composite score in [0, 1]. The harness also computes a mean score across all tasks.

### 2.4 Model Serving

A local OpenAI-compatible shim (`scripts/openai_transformers_shim.py`) was implemented using FastAPI and uvicorn, backed by the HuggingFace Transformers library. The shim exposes `/v1/models` and `/v1/chat/completions` endpoints and loads the model from a local cache snapshot.

The evaluated model is **Qwen2.5-0.5B-Instruct** (0.5 billion parameters), loaded from:

```
[redacted-local-hf-cache]/hub/models--Qwen--Qwen2.5-0.5B-Instruct/snapshots/7ae557604adf67be50417f59c2c2f167def9a775
```

The shim was launched on `127.0.0.1:18000` and verified functional before benchmark execution. Runtime dependencies included PyTorch with CUDA 13.0 support, Transformers, Accelerate, FastAPI, and uvicorn.

### 2.5 Output Parsing

An initial run revealed that Qwen2.5-0.5B-Instruct wraps JSON output in markdown code fences, causing parse failures. The runner (`scripts/run_openai_compatible.py`) was updated to tolerate fenced and extraneous JSON objects and to preserve `raw_content` for auditability. This is a practical finding about model output formatting at this scale, not a benchmark design choice.

---

## 3. Results

### 3.1 Sample Validation

Prior to the live model run, the scoring pipeline was validated against two hand-crafted sample outputs:

| Sample | Score |
|--------|-------|
| Good sample | 0.9500 |
| Distractor sample | 0.1071 |
| Mean (n=2) | 0.5285 |

The scoring pipeline discriminates between correct and distractor-selecting outputs as intended.

### 3.2 Qwen2.5-0.5B-Instruct Baseline

The benchmark was executed against the locally served Qwen2.5-0.5B-Instruct model. Results are recorded in `results/model_eval.json`.

| Task | Domain | Score | Answer Correct |
|------|--------|-------|---------------|
| 1 | Invoice | 0.9000 | Yes |
| 2 | Clinical dose | 0.5750 | Yes |
| 3 | Meeting owner | 0.0625 | No |
| 4 | Contract termination | 0.2500 | No |
| 5 | Shipping address | 0.7500 | Yes |

- **Mean score**: 0.5075 (n=5)
- **Answer correctness**: 3/5
- **Audit coverage**: 0.0 on all five tasks

### 3.3 Key Observations

1. **Answer extraction partially works**: The model extracts the correct answer on 3 of 5 tasks, achieving high scores on the invoice (0.90) and shipping address (0.75) tasks where the target information is relatively unambiguous in the document.

2. **Audit coverage is uniformly zero**: The model never produces the required structured contrastive audit trace on any task. This is the most salient negative finding. The forced contrastive self-audit mechanism, as currently prompted, is not elicited by a 0.5B-parameter instruct model.

3. **Distractor susceptibility**: On two tasks (meeting owner at 0.0625, contract termination at 0.25), the model selects the planted distractor. These are the distractor-heavy tasks where the contrastive audit trace would be most necessary.

4. **JSON formatting**: The model wraps structured JSON output in markdown fences, requiring post-hoc parsing tolerance. This is a practical engineering concern for benchmark deployment at this model scale.

### 3.4 Test Suite Validation

All automated tests pass:

- `python -m py_compile` succeeds for `src/fcsa_benchmark.py`, `scripts/run_openai_compatible.py`, and `scripts/openai_transformers_shim.py`.
- `python -m pytest -q`: 6 passed in 0.01s.

---

## 4. Limitations

1. **Single small model**: Results are reported only for Qwen2.5-0.5B-Instruct. This is a 0.5B-parameter model, which is substantially smaller than contemporary production-grade instruct models. Whether larger models produce non-zero audit coverage is unknown from these artifacts.

2. **Five seed tasks only**: The benchmark comprises five hand-crafted tasks. This is insufficient for drawing general conclusions about model behavior across domains, document types, or distractor configurations.

3. **Zero audit coverage**: The central mechanism under test—forced contrastive self-audit—was not successfully elicited in any task. The hypothesis that forcing contrastive self-audit improves extraction discriminability is neither confirmed nor refuted by these results; it is simply untested at this model scale because the model does not comply with the audit instruction.

4. **No comparison conditions**: No ablation is reported (e.g., the same model without the forced audit instruction). It is therefore unclear whether the audit instruction helps, hurts, or is simply ignored.

5. **Local prototype infrastructure**: The model was served via a project-local OpenAI-compatible shim, not a production inference server. Latency, throughput, and serving stability were not measured. The shim was stopped after the run and is not persistently available.

6. **No external replication**: All experiments were conducted in a single local environment. No cross-hardware or cross-environment replication is present in the artifacts.

7. **Scoring rubric calibration**: The scoring weights and rubric were defined during harness construction and have not been independently calibrated or validated against human judgments of audit quality.

8. **Deterministic but not randomized**: Prompt rendering is deterministic, which aids reproducibility but means no variance estimates are available from repeated runs.

---

## 5. Reproducibility Checklist

| Item | Status |
|------|--------|
| Benchmark harness source code | Available: `src/fcsa_benchmark.py` |
| Seed task dataset | Available: `data/seed_tasks.jsonl` |
| Rendered prompts | Available: `results/prompts.jsonl` |
| Model outputs (raw) | Available: `results/model_outputs.jsonl` (includes `raw_content`) |
| Evaluation scores | Available: `results/model_eval.json` |
| Sample evaluation scores | Available: `results/sample_eval.json` |
| Sample outputs | Available: `samples/sample_outputs.jsonl` |
| Runner script | Available: `scripts/run_openai_compatible.py` |
| Model serving shim | Available: `scripts/openai_transformers_shim.py` |
| Test suite | Available: `tests/test_fcsa_benchmark.py` (6 tests, all passing) |
| Model identifier | Qwen2.5-0.5B-Instruct (HuggingFace cache snapshot `7ae557604adf67be50417f59c2c2f167def9a775`) |
| Python environment | Project-local `.venv` with PyTorch CUDA 13.0, Transformers, Accelerate, FastAPI, uvicorn, pytest |
| Random seed | Not applicable (deterministic prompt rendering, single model run) |
| Hardware | Local CUDA GPU (specific device not recorded in artifacts) |
| Number of runs | 1 run per task (no repeated trials) |

---

## 6. Conclusion

The Forced Contrastive Self-Audit Extraction Trace Benchmark harness has been constructed, validated, and exercised against Qwen2.5-0.5B-Instruct. The harness and scoring pipeline function as designed: they correctly discriminate between good and distractor-selecting outputs in sample validation, and they produce interpretable per-task scores in live evaluation.

The baseline results are mixed. The model extracts correct answers on 3 of 5 tasks but achieves zero audit coverage across all tasks and falls to distractors on 2 of 5 tasks. The forced contrastive self-audit mechanism is not elicited by this model at this scale. Whether the mechanism is effective with larger models, different prompting strategies, or fine-tuned audit rubrics remains an open question.

The current project artifacts support the finding that the benchmark harness is functional and produces meaningful score differentiation in the tested setting. They do not support claims about the general effectiveness of forced contrastive self-audit as an extraction reliability mechanism. The recommended next step is to use the recorded Qwen2.5-0.5B baseline to compare against a stronger cached instruct model or to calibrate the audit rubric before drawing further conclusions.

---

## Referenced Artifacts

### Result files
- `results/model_eval.json` — Qwen2.5-0.5B-Instruct evaluation scores
- `results/model_outputs.jsonl` — Raw model outputs with `raw_content` preserved
- `results/sample_eval.json` — Sample validation scores
- `results/prompts.jsonl` — Rendered deterministic prompts

### Source and script files
- `src/fcsa_benchmark.py` — Benchmark harness: prompt rendering and scoring
- `scripts/run_openai_compatible.py` — Runner for OpenAI-compatible endpoints
- `scripts/openai_transformers_shim.py` — Local Transformers-backed OpenAI-compatible shim
- `tests/test_fcsa_benchmark.py` — Test suite (6 tests)
- `data/seed_tasks.jsonl` — Five seed tasks with gold answers and distractors
- `samples/sample_outputs.jsonl` — Hand-crafted sample outputs for scoring validation

### Project metadata and decision files
- `.omx/project_decision.json` — Project decision: `finalize_positive`, hypothesis: `supported`
- `.omx/metrics.json` — Session metrics
- `run_notes.md` — Detailed execution log
- `README.md` — Project usage documentation

### Paper artifacts
- `papers/.../evidence_bundle.json` — Evidence bundle with decision, run notes, and file manifest
- `papers/.../claim_ledger.json` — Claim audit with confidence levels and wording constraints
- `papers/.../paper_manifest.json` — Paper artifact manifest
