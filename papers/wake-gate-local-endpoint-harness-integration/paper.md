# Wake-Gate Local Endpoint Harness Integration

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, and project decision JSON). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact. It has not been subjected to human peer review.

---

## Abstract

We describe an integration that connects a local OpenAI-compatible model endpoint contract harness to a wake-gate autonomous-project dispatch system. The integration materializes wake-gate queue payloads—`/prepare-project` and `/dispatch` requests—from cached local model artifacts and validates the copied harness against a live llama.cpp backend serving a quantized Phi-4-mini-instruct model. In the tested setting, the contract harness reported successful probes on both the `/models` and `/chat/completions` endpoints (HTTP 200, `ok=true`), and the llama.cpp service was cleanly shut down afterward. A vLLM serving path was prepared and dependency-installed but not separately executed, since the branch success criterion was satisfied by the llama.cpp path. These results are bounded to a single machine, a single model, and a single validation session; no latency or throughput benchmarks were collected, and no external replication has been performed. The current project artifacts support the finding that the harness-wake-gate integration is viable in the tested setting, but generalization to other backends, models, or hardware configurations remains unvalidated.

## 1. Introduction

Autonomous research pipelines require reliable mechanisms to provision, validate, and tear down local model-serving endpoints. A *local model endpoint contract harness* verifies that an OpenAI-compatible server correctly responds to `/models` and `/chat/completions` requests before downstream tasks depend on it. A *wake-gate* system manages the lifecycle of autonomous project runs, including queue-based dispatch of preparation and execution requests.

This report documents an integration effort—*Wake-Gate Local Endpoint Harness Integration*—that connects these two subsystems. The central question is whether the contract harness can be copied into an autonomous wake-gated project workspace, represented as wake-gate queue payloads, and validated against a real cached model backend without requiring credentials or destructive system changes.

The project was executed within the OMX research automation pipeline on 2026-04-13. The recorded project decision is `finalize_positive` with hypothesis status `supported`, evidence strength `strong`, and confidence `high`. However, as the claim ledger for this project explicitly notes, the allowed wording is that "the current project artifacts support this finding in the tested setting," and the finding must not be generalized as proving universal viability.

## 2. Method

### 2.1 Artifact Acquisition

The parent Local Model Endpoint Contract Harness artifacts were acquired from a prior OMX project (`source-record-redacted`). The acquired artifacts included:

- `scripts/local_model_endpoint.py` — the contract harness implementation
- `tests/test_contract_harness.py` — the unit test suite
- Endpoint manifest JSON files and supporting documentation

These artifacts were copied into the current project workspace without modification.

### 2.2 Wake-Gate Integration Builder

A new script, `scripts/build_wake_gate_integration.py`, was created to serve as the integration bridge. This script:

1. Discovers cached HuggingFace model snapshots on the local filesystem.
2. Emits wake-gate `/prepare-project` and `/dispatch` JSON payloads suitable for enqueueing into the wake-gate controller.
3. Materializes an autonomous child project directory containing the endpoint manifests and prompts needed for validation.

### 2.3 Two Serving Paths

Two distinct serving paths were prepared:

**vLLM path.** Queue artifacts were generated for the cached model `Qwen/Qwen2.5-3B-Instruct` (snapshot `aa8e72537993ba99e69dfaafa59ed015b17504d1`). A project-local virtual environment (`.venv`) was created and populated with `vllm`, `transformers`, and `torch` via `uv pip install`. This path was dependency-ready but was not separately started, because the branch success criterion was already satisfied by the llama.cpp path.

**llama.cpp path.** Queue artifacts and an autonomous child project (`autonomous_llama_cpp_endpoint_project/`) were generated for the cached GGUF model `Phi-4-mini-instruct-Q4_K_M.gguf` (from `lmstudio-community`), served via `/mnt/usb/home/jeremy/projects/llama.cpp/build/bin/llama-server`. This path was executed and validated.

### 2.4 Validation Protocol

The contract harness was validated against the llama.cpp backend by:

1. Starting `llama-server` with the cached GGUF model.
2. Registering the endpoint in `.omx/endpoints/wake-gate-llama-cpp-cached.endpoint.json`.
3. Running the contract probe, which issues HTTP requests to `/models` and `/chat/completions` and checks for expected response structure and status codes.
4. Recording the probe result to `artifacts/wake_gate_integration/manual/llama_cpp_probe.json`.
5. Stopping the llama.cpp service and confirming shutdown via `artifacts/wake_gate_integration/manual/llama_cpp_status_after_stop.json` (`alive=false`).

Unit tests were also executed: `python -m unittest tests/test_contract_harness.py` and `.venv/bin/python -m pytest tests -q`, both of which passed. A compile check (`.venv/bin/python -m compileall scripts tests`) completed successfully.

## 3. Results

### 3.1 Contract Harness Validation

The contract probe against the llama.cpp backend returned `ok=true`. Specifically:

- The `/models` endpoint returned HTTP status 200.
- The `/chat/completions` endpoint returned HTTP status 200.
- The probe result was recorded in `artifacts/wake_gate_integration/manual/llama_cpp_probe.json`.

This constitutes a hook-prototype-level validation: a real cached model backend was probed through the contract harness, and both required endpoints responded correctly. No latency or throughput measurements were taken; the probe verifies functional correctness only.

### 3.2 Service Lifecycle

The llama.cpp service was started, probed, and stopped within a single session. The post-stop status check confirmed `alive=false`, indicating no residual helper server process remained from this project.

### 3.3 Unit Test Results

- `python -m unittest tests/test_contract_harness.py` — passed.
- `.venv/bin/python -m pytest tests -q` — 2 passed in 1.46s.
- `.venv/bin/python -m compileall scripts tests` — compiled successfully.

### 3.4 vLLM Path Status

The vLLM serving path was prepared (dependencies installed, queue artifacts generated, endpoint manifest created) but not executed. The branch success criterion was satisfied by the llama.cpp path, so the heavier vLLM backend was not separately started. Whether the vLLM path functions correctly in this integration remains unvalidated by direct execution.

### 3.5 Wake-Gate Queue Payloads

The integration builder successfully generated wake-gate queue payloads for both serving paths:

- **llama.cpp queue:** `artifacts/wake_gate_integration/llama_cpp_queue/prepare_project_request.json` and `dispatch_request.json`
- **vLLM queue:** `artifacts/wake_gate_integration/20260413T090207Z/prepare_project_request.json` and `dispatch_request.json`

These payloads are structurally complete but have not been consumed by a live wake-gate controller dispatch cycle; they were generated and recorded, not dequeued and executed through the full wake-gate pipeline.

## 4. Limitations

1. **Single backend validated.** Only the llama.cpp serving path was executed and probed. The vLLM path was prepared but not run. Whether the integration works with vLLM remains unconfirmed by direct evidence.

2. **Single model.** The live validation used only `Phi-4-mini-instruct-Q4_K_M.gguf`. The `Qwen/Qwen2.5-3B-Instruct` model referenced in the vLLM artifacts was not served or probed.

3. **Single machine and session.** All operations occurred on one machine in one session (session `omx-1776070733914-t1ccqv`, duration approximately 5 minutes). No cross-machine or cross-session replication was performed.

4. **No performance benchmarks.** The contract harness verifies functional correctness (endpoint availability and response structure), not serving performance. Latency, throughput, concurrency, and memory utilization were not measured.

5. **No concurrent access testing.** The probe was conducted in isolation. Behavior under concurrent requests or multiple simultaneous harness validations was not assessed.

6. **Wake-gate dispatch not end-to-end.** The queue payloads were generated but not consumed by a live wake-gate controller. The integration validates payload generation and harness probing, not the full dispatch lifecycle.

7. **Cached model dependency.** The validation relied on pre-cached model files. The integration does not demonstrate model downloading or first-time provisioning.

8. **No external replication.** These results have not been independently reproduced on different hardware or by different operators.

## 5. Reproducibility Checklist

| Item | Status |
|------|--------|
| Model identifier and source specified | Yes: `lmstudio-community/Phi-4-mini-instruct-GGUF/Phi-4-mini-instruct-Q4_K_M.gguf` |
| Model cache path recorded | Yes: `/mnt/usb/home/jeremy/.lmstudio/models/...` |
| Server binary path recorded | Yes: `/mnt/usb/home/jeremy/projects/llama.cpp/build/bin/llama-server` |
| Endpoint manifest preserved | Yes: `.omx/endpoints/wake-gate-llama-cpp-cached.endpoint.json` and `artifacts/wake_gate_integration/manual/cached_llama_cpp_endpoint.json` |
| Contract probe result preserved | Yes: `artifacts/wake_gate_integration/manual/llama_cpp_probe.json` |
| Service shutdown confirmed | Yes: `artifacts/wake_gate_integration/manual/llama_cpp_status_after_stop.json` (`alive=false`) |
| Unit test suite included and passing | Yes: 2 passed in 1.46s |
| Wake-gate queue payloads preserved | Yes: both `prepare_project_request.json` and `dispatch_request.json` for both paths |
| Hardware specification recorded | No: GPU/CPU/RAM details of the host machine are not present in the artifacts |

## 6. Conclusion

The current project artifacts support the finding that a local OpenAI-compatible model endpoint contract harness can be integrated into a wake-gate autonomous-project dispatch system in the tested setting. The integration was validated by probing a live llama.cpp backend serving a cached quantized model, with both `/models` and `/chat/completions` endpoints returning successful responses. The service was cleanly shut down afterward, and the unit test suite passed.

However, several aspects remain unvalidated: the vLLM serving path was prepared but not executed, the wake-gate queue payloads were generated but not consumed by a live controller dispatch cycle, no performance benchmarks were collected, and no external replication has been performed. The project decision recommends using the generated queue payloads to enqueue a concrete autonomous llama.cpp validation run, or to exercise the vLLM artifact if a heavier backend validation is desired. This recommended follow-up is not guaranteed to succeed; it reflects the project's assessment of a logical next step given the current evidence.

## Referenced Artifacts

### Run notes and decisions
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Claim ledger and evidence bundle
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`

### Integration builder
- `scripts/build_wake_gate_integration.py`

### llama.cpp queue artifacts
- `artifacts/wake_gate_integration/llama_cpp_queue/summary.json`
- `artifacts/wake_gate_integration/llama_cpp_queue/dispatch_request.json`
- `artifacts/wake_gate_integration/llama_cpp_queue/prepare_project_request.json`

### vLLM queue artifacts
- `artifacts/wake_gate_integration/20260413T090207Z/summary.json`
- `artifacts/wake_gate_integration/20260413T090207Z/dispatch_request.json`
- `artifacts/wake_gate_integration/20260413T090207Z/prepare_project_request.json`
- `artifacts/wake_gate_integration/20260413T090207Z/cached_vllm_endpoint.json`
- `artifacts/wake_gate_integration/20260413T090207Z/mock_endpoint.json`
- `artifacts/wake_gate_integration/20260413T090207Z/README.md`
- `artifacts/wake_gate_integration/20260413T090207Z/autonomous_project_prompt.md`

### Manual validation artifacts
- `artifacts/wake_gate_integration/manual/llama_cpp_probe.json`
- `artifacts/wake_gate_integration/manual/llama_cpp_stop.json`
- `artifacts/wake_gate_integration/manual/llama_cpp_status_after_stop.json`
- `artifacts/wake_gate_integration/manual/cached_llama_cpp_endpoint.json`

### Builder output
- `artifacts/wake_gate_integration/latest_builder_stdout.json`

### Autonomous child projects
- `autonomous_llama_cpp_endpoint_project/` (run notes, prompts, manifests)
- `autonomous_endpoint_validation_project/` (run notes, prompts, harness script)
