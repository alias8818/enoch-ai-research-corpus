# Cache Reentry Production Endpoint Validation: Answer-Contract Prompting Improves Tool-Use Accuracy on a vLLM-Served Qwen2.5-3B-Instruct Endpoint

> **AI Provenance / No-Human-Credit Note:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We report empirical results from validating an answer-contract prompt adapter for tool-use scenarios against a production-grade vLLM OpenAI-compatible endpoint. A prior experiment using a local HuggingFace Transformers shim with Qwen2.5-0.5B-Instruct found that a no-debug transcript prompt yielded 0% exact-match accuracy on a 1,000-example tool-serving benchmark, while an answer-contract prompt yielded 100%. This study reproduces that finding on a vLLM-served Qwen2.5-3B-Instruct endpoint: the transcript prompt scores 0.0 exact pass on 100 sampled examples (all failures classified as wrong_answer), while the answer-contract prompt scores 1.0 exact pass on the same 100 examples and sustains 1.0 exact pass across all 1,000 examples. These results are bounded by the specific model, endpoint configuration, and benchmark dataset tested. Notably, the vLLM endpoint was run without native function-call parsing enabled (`--omit-tools` mode), so the results validate the answer-contract serving adapter on vLLM but do not characterize vLLM's native tool-call parser behavior.

---

## 1. Introduction

When large language models are deployed behind OpenAI-compatible serving endpoints, tool-use accuracy depends not only on model capability but also on how tool schemas and conversation history are presented in the prompt. A prior project (the "parent" project, project ID `source-record-redacted`) established a benchmark harness and 1,000-example dataset for evaluating tool-serving accuracy across five scenarios. In that parent project, a local HuggingFace Transformers shim running Qwen2.5-0.5B-Instruct demonstrated a stark contrast between two prompt styles:

- **Transcript prompt**: presents the tool-use conversation as a raw transcript of user messages, assistant responses, and tool results, without instructing the model on the expected answer format.
- **Answer-contract prompt**: augments the transcript with an explicit instruction specifying the expected answer format and contract, guiding the model to produce structured, parseable outputs.

The parent project found that the transcript prompt yielded 0% exact-match accuracy while the answer-contract prompt yielded 100% on the same 100-example sample. The present study asks whether this result generalizes to a production-grade serving configuration: specifically, a vLLM 0.19.0 OpenAI-compatible endpoint serving the larger Qwen2.5-3B-Instruct model.

---

## 2. Method

### 2.1 Benchmark Harness

The benchmark harness (`src/tool_serving_benchmark.py`) was copied from the parent project into this branch. It evaluates an OpenAI-compatible chat completions endpoint against a 1,000-example dataset spanning five tool-use scenarios. Each example consists of a multi-turn conversation involving tool calls and tool results, with a ground-truth final answer. The harness sends the conversation to the endpoint, extracts the model's final answer, and compares it against the ground truth using exact-match scoring.

The harness supports two prompt styles:

- **Transcript**: The conversation history (including tool-result messages) is sent as-is, with no additional formatting instructions beyond the standard chat message roles.
- **Answer-contract**: The same conversation history is sent, but the system or user message includes an explicit answer-contract instruction specifying the expected output format and the requirement to produce a final answer matching the ground-truth schema.

Both prompt styles were run with `--no-debug-json` (no debug labels injected into the prompt) and `--omit-tools` (the OpenAI `tools` schema is excluded from the API request, though tool-result messages are preserved in the conversation history).

### 2.2 Endpoint Configuration

A vLLM 0.19.0 server was launched as a production-style OpenAI-compatible endpoint with the following configuration:

- **Model**: `Qwen/Qwen2.5-3B-Instruct` (served as `qwen2.5-3b-instruct`)
- **Host**: `127.0.0.1:18090`
- **Max model length**: 4096 tokens
- **GPU memory utilization**: 0.70
- **Tool-call parser**: Not enabled (the endpoint was not launched with `--enable-auto-tool-choice` or `--tool-call-parser`)

The vLLM server rejected `tool_choice=auto` in this configuration, which motivated the `--omit-tools` benchmark mode. This mode preserves the semantic content of tool-result messages while omitting the `tools` parameter from the API request.

### 2.3 Software Environment

- Python virtual environment created with `uv venv --python /usr/bin/python3`
- vLLM 0.19.0 installed via `uv pip install vllm`
- PyTorch pinned to `torch==2.10.0+cu130`, `torchvision==0.25.0+cu130`, `torchaudio==2.10.0+cu130` (initial attempts with CPU-only Torch and with `torch==2.11.0+cu130` failed due to missing `libtorch_cuda.so` and ABI mismatch errors respectively)
- Unit tests: `python3 -m unittest discover -s tests` passed with 6 tests

### 2.4 Experimental Protocol

Three benchmark runs were executed against the vLLM endpoint:

1. **Transcript, 100 examples**: `--limit 100 --prompt-style transcript`
2. **Answer-contract, 100 examples**: `--limit 100 --prompt-style answer_contract`
3. **Answer-contract, full 1,000 examples**: `--prompt-style answer_contract` (no limit)

All runs used `--no-debug-json --omit-tools --max-tokens 64`. The 100-example subset was the same balanced sample across both prompt styles, enabling a direct paired comparison.

---

## 3. Results

### 3.1 Transcript Prompt (100 examples)

| Metric | Value |
|---|---|
| Exact pass rate | 0.0 |
| Total examples | 100 |
| Wrong-answer failures | 100 |
| Other failure types | 0 |

The transcript prompt produced zero correct answers. Every failure was classified as `wrong_answer`, indicating the model generated a response but it did not match the ground truth.

### 3.2 Answer-Contract Prompt (100 examples)

| Metric | Value |
|---|---|
| Exact pass rate | 1.0 |
| Total examples | 100 |
| Wrong-answer failures | 0 |
| Other failure types | 0 |

The answer-contract prompt produced correct answers on all 100 examples across all five scenarios.

### 3.3 Answer-Contract Prompt (1,000 examples)

| Metric | Value |
|---|---|
| Exact pass rate | 1.0 |
| Total examples | 1,000 |
| Wrong-answer failures | 0 |
| Other failure types | 0 |

The answer-contract prompt sustained perfect accuracy on the full benchmark dataset.

### 3.4 Summary

The answer-contract adapter improved exact-match accuracy from 0% to 100% on the 100-example comparison and held at 100% across all 1,000 examples. This reproduces the parent project's finding on a larger model served through a production-grade vLLM endpoint.

---

## 4. Limitations

1. **Single model family**: Only Qwen2.5 models were tested (0.5B-Instruct in the parent project, 3B-Instruct in this study). Generalization to other model families (Llama, Mistral, Gemma, etc.) is not established.

2. **Omitted tool schema**: The vLLM endpoint was not configured with a native function-call parser. The `tools` parameter was omitted from API requests, and tool-result messages were injected as plain chat messages. This validates the answer-contract serving adapter on vLLM but does not characterize vLLM's native tool-call parser behavior. It remains unknown whether the answer-contract adapter would improve over (or interact with) vLLM's native `--enable-auto-tool-choice --tool-call-parser` mode.

3. **Single hardware and software configuration**: Results were obtained on one machine with one CUDA/Torch/vLLM version stack. Replication across different GPU architectures, vLLM versions, or serving frameworks (SGLang, TensorRT-LLM, etc.) has not been performed.

4. **Benchmark scope**: The 1,000-example dataset covers five tool-use scenarios. The extent to which these scenarios represent the diversity of real-world tool-use deployments is not characterized.

5. **Exact-match metric**: The benchmark uses exact-match scoring. This is a strict metric that may overstate failure rates for near-correct outputs and understates failure rates for outputs that match by coincidence. No partial-credit or semantic-similarity evaluation was performed.

6. **Deterministic vs. sampling behavior**: The `--max-tokens 64` setting and the absence of reported temperature/sampling parameters mean the sampling configuration is not fully documented in the run notes. Reproducibility of the exact 0% and 100% figures under different sampling configurations is not guaranteed.

7. **No comparison to native tool-call parsing**: The most significant untested condition is vLLM with `--enable-auto-tool-choice --tool-call-parser` enabled. The answer-contract adapter may be complementary to, redundant with, or in conflict with native tool-call parsing. This is an open question.

8. **Ceiling effect**: The 100% accuracy on the answer-contract condition leaves no room to measure degradation under harder conditions, larger models, or more complex tool schemas. The apparent perfection may reflect benchmark difficulty rather than method capability.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Benchmark harness source | Available: `src/tool_serving_benchmark.py` |
| Unit tests | Available: `tests/test_tool_serving_benchmark.py` (6 tests, passing) |
| Dataset | 1,000-example dataset copied from parent project |
| Model identifier | `Qwen/Qwen2.5-3B-Instruct` (publicly available) |
| vLLM version | 0.19.0 |
| PyTorch version | 2.10.0+cu130 |
| Endpoint launch command | Documented in run notes (see Section 2.2) |
| Benchmark invocation commands | Documented in run notes (see Section 2.4) |
| Raw predictions | Available: JSONL files in `results/` directory |
| Summary files | Available: JSON files in `results/` directory |
| Parent project summaries | Available: `results/parent_qwen2_5_0_5b_instruct_*` |
| Hardware details | Not recorded in artifacts |
| Sampling parameters (temperature, top-p) | Not explicitly recorded in run notes |
| Random seed | Not recorded |

---

## 6. Conclusion

This study provides empirical evidence that an answer-contract prompt adapter improves tool-use exact-match accuracy from 0% to 100% on a 1,000-example benchmark when served through a vLLM 0.19.0 endpoint running Qwen2.5-3B-Instruct. This reproduces a prior finding obtained with a smaller model (Qwen2.5-0.5B-Instruct) on a local Transformers shim, extending it to a production-grade serving configuration with a larger model.

The result is bounded by significant limitations: only one model family was tested, the vLLM endpoint was run without native function-call parsing, and the benchmark uses exact-match scoring on a fixed dataset. The most important open question is whether the answer-contract adapter provides similar improvements when vLLM's native tool-call parser is enabled, or when other serving frameworks and model families are used.

The current project artifacts support the finding that the answer-contract adapter improves accuracy in the tested setting. They do not establish that the method works universally or that the observed 100% accuracy will hold under different conditions.

---

## Referenced Artifacts

### Result files
- `results/vllm_qwen2_5_3b_instruct_answer_contract_full_predictions.jsonl`
- `results/vllm_qwen2_5_3b_instruct_answer_contract_full_summary.json`
- `results/vllm_qwen2_5_3b_instruct_answer_contract_100_predictions.jsonl`
- `results/vllm_qwen2_5_3b_instruct_answer_contract_100_summary.json`
- `results/vllm_qwen2_5_3b_instruct_transcript_100_predictions.jsonl`
- `results/vllm_qwen2_5_3b_instruct_transcript_100_summary.json`
- `results/parent_qwen2_5_0_5b_instruct_answer_contract_100_summary.json`
- `results/parent_qwen2_5_0_5b_instruct_transcript_100_summary.json`
- `results/mvp_summary.json`

### Source and configuration files
- `src/tool_serving_benchmark.py`
- `tests/test_tool_serving_benchmark.py`
- `scripts_launch_vllm.sh`
- `logs/vllm_qwen2_5_3b_18090.log`
- `logs/vllm_qwen2_5_3b_18090.pid`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `run_notes.md`
- `README.parent.md`

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/publication/publication_manifest.json`
