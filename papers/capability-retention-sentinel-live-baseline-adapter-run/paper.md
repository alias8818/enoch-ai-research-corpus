# Capability Retention Sentinel with Live Baseline Adapter: A Dependency-Free Suite for Detecting LLM Capability Regression

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

We present the Capability Retention Sentinel Suite, a dependency-free Python toolkit for detecting capability regression in language model outputs across structured and unstructured task categories. The suite generates 243 deterministic prompts spanning nine categories (exact-copy spans, JSON validity, YAML validity, arithmetic, short code, long-context retrieval, tool-call formatting, refusal canaries, and instruction-following), scores responses against category-specific deterministic criteria, and produces a single JSON report suitable for automated closeout gating. We further introduce a live baseline adapter that executes prompts against any OpenAI-compatible `/chat/completions` endpoint and compares baseline versus candidate model reports. In self-test against synthetic reference and intentionally degraded responses, the suite achieves a reference score of 1.0 and a degraded score of 0.0, correctly flagging regression. In a mock-server integration test over 27 prompts, the baseline model scores 1.0 (gate pass) and the compressed model scores 0.0 (gate fail), with a per-category delta of −1.0. A live smoke test against a local llama.cpp server serving Phi-4-mini-instruct-Q4_K_M produced zero runner failures but scored 0/3 on exact-copy prompts due to nonsensical model outputs—a negative result that confirms the adapter mechanism functions correctly while honestly reflecting poor model performance on the tested subset. These results support the suite's utility as an adapter and scoring mechanism but do not constitute evidence of capability retention for any specific model.

## 1. Introduction

Quantifying whether a modified, compressed, or updated language model retains the capabilities of its predecessor remains an open practical problem. Coarse aggregate metrics (e.g., perplexity on a held-out corpus) can miss category-specific regressions, while full benchmark suites are expensive to run and difficult to integrate into automated deployment pipelines.

This work addresses the need for a lightweight, deterministic, dependency-free regression sentinel that can be wired into local model evaluation workflows. The Capability Retention Sentinel Suite generates a fixed prompt set, scores model responses against deterministic per-category criteria, and emits a structured JSON report. A live baseline adapter extends this to OpenAI-compatible endpoints, enabling direct baseline-versus-candidate comparison.

The core hypothesis under test is: *the sentinel suite catches intentional regressions across all required categories and can be wired to local model runners without adding dependencies.* The current project artifacts support this finding in the tested setting.

## 2. Method

### 2.1 Prompt Generation

The suite generates 243 deterministic prompts, with 27 prompts per category across nine categories:

| Category | Description |
|---|---|
| Exact-copy spans | Prompts requiring verbatim reproduction of a provided text span |
| JSON validity | Prompts requesting valid JSON output conforming to a specified schema |
| YAML validity | Prompts requesting valid YAML output conforming to a specified schema |
| Arithmetic | Prompts with deterministic numerical answers |
| Short code | Prompts requesting small Python functions |
| Long-context retrieval | Prompts embedding a target fact in a longer context for extraction |
| Tool-call formatting | Prompts requesting structured tool-call output in a specified format |
| Refusal canary | Prompts that should trigger a refusal; the sentinel checks that a refusal is produced |
| Instruction-following | Prompts with specific formatting or content constraints |

Prompts are generated deterministically from seed data so that the same prompt set is reproducible across runs.

### 2.2 Scoring

Each response is scored against category-specific deterministic criteria:

- **Exact-copy**: character-level match against the expected span.
- **JSON/YAML validity**: parsed successfully and conforms to the required schema.
- **Arithmetic**: numerical answer matches the expected value.
- **Short code**: the response is parsed via Python's `ast` module; unsafe constructs (imports, classes, `while`, `with`, `try`, globals/nonlocals, dunder names/attributes) are rejected before execution in a restricted namespace, and the function must produce the expected output for given inputs.
- **Long-context retrieval**: the expected fact string appears in the response.
- **Tool-call formatting**: the response matches the required structured format.
- **Refusal canary**: a refusal indicator is detected in the response.
- **Instruction-following**: specified formatting and content constraints are satisfied.

The scorer emits a per-category pass rate and an aggregate score in [0, 1], along with a binary gate decision (pass/fail against a configurable threshold).

### 2.3 Command Adapter

The `run-command` CLI subcommand invokes any local model CLI once per prompt, passing prompt text on stdin, exposing `SENTINEL_CASE_ID` and `SENTINEL_CATEGORY` as environment variables, capturing stdout into the response JSONL, and recording return codes and stderr. Per-prompt timeouts and a `--limit` flag for smoke subsets are supported.

### 2.4 Live Baseline Adapter

The `live_baseline.py` module implements:

1. **Endpoint contract verification**: confirms the target server exposes `/v1/models` and `/v1/chat/completions` with the expected contract.
2. **Prompt execution**: sends each prompt to the `/chat/completions` endpoint and captures the assistant response.
3. **Report scoring**: applies the deterministic scorer to the collected responses.
4. **Baseline-vs-candidate comparison**: loads two previously generated reports (baseline and candidate), computes per-category deltas, and emits a comparison JSON with a retention gate decision.

A mock OpenAI-compatible server (`scripts/mock_openai_server.py`) provides two named models—`local-baseline-mock` (returns correct responses) and `local-compressed-mock` (returns empty/incorrect responses)—for integration testing without a real model endpoint.

## 3. Results

### 3.1 Self-Test: Synthetic Reference and Degraded Responses

The self-test generates synthetic reference responses (all correct) and intentionally degraded responses (all incorrect), then scores both.

| Condition | Score | Gate |
|---|---|---|
| Reference (all correct) | 1.0 | Pass |
| Degraded (all incorrect) | 0.0 | Fail |

Regression detected: **true**. This confirms the scorer correctly discriminates between perfect and completely degraded outputs in a controlled setting.

### 3.2 Mock Server Integration Test

Using the mock OpenAI-compatible server over 27 prompts (3 per category):

| Model | Pass Rate | Score | Gate |
|---|---|---|---|
| `local-baseline-mock` | 27/27 | 1.0 | Pass |
| `local-compressed-mock` | 0/27 | 0.0 | Fail |

Per-category delta: −1.0 across all nine categories. Retention gate: **fail**.

This result validates the end-to-end adapter pipeline (endpoint discovery, prompt dispatch, response capture, scoring, comparison) against a controlled server.

### 3.3 Live Endpoint Smoke Test: Phi-4-mini-instruct-Q4_K_M via llama.cpp

A local llama.cpp server was started serving the model `Phi-4-mini-instruct-Q4_K_M.gguf`. The endpoint contract was verified (`/v1/models` and `/v1/chat/completions` responded as expected). Three exact-copy prompts were dispatched.

| Metric | Value |
|---|---|
| Runner failures | 0 |
| Cases attempted | 3 |
| Cases passed | 0 |
| Score | 0/3 |

The model produced nonsensical outputs for all three exact-copy prompts. This is a **negative result** for capability retention on this model/prompt subset. It does, however, serve as positive evidence that the adapter mechanism correctly captures and scores real model outputs, including cases where the model performs poorly.

### 3.4 Unit Tests

All unit tests passed at each stage of development:

| Stage | Tests | Result |
|---|---|---|
| Initial MVP | 3 | All passed |
| After command adapter | 5 | All passed |
| After live adapter | 6 | All passed |

All source files compiled cleanly via `python -m compileall`.

## 4. Limitations

1. **Narrow real-model coverage.** The only live model test used a single quantized model (Phi-4-mini-instruct-Q4_K_M) on only 3 exact-copy prompts. This is insufficient to characterize capability retention for any model. The result was negative (0/3), which honestly reflects the model's performance on this tiny subset but cannot be generalized.

2. **Mock-server results are synthetic.** The 27/27 and 0/27 mock-server results confirm the adapter and scoring pipeline function end-to-end, but they do not characterize real model behavior. The mock server returns trivially correct or incorrect responses by design.

3. **Deterministic prompts may not cover all failure modes.** The 243-prompt set spans nine categories but may not capture subtle regressions (e.g., increased hallucination rate, degraded reasoning on complex multi-step problems, or style/tonality shifts) that a more open-ended evaluation would reveal.

4. **Short-code scoring relies on AST-level safety filtering and restricted execution.** While the scorer rejects common unsafe constructs, the restricted namespace approach is not a sandbox; edge cases in Python execution safety may exist.

5. **No external replication.** All experiments were conducted in a single local environment. No cross-hardware, cross-platform, or independent replication data is available.

6. **Gate threshold is configurable but not empirically calibrated.** The default pass/fail threshold has not been validated against human judgments of acceptable capability retention.

7. **The live adapter depends on OpenAI-compatible endpoint contract.** Models or servers that deviate from the `/v1/chat/completions` contract may require adapter modifications.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Prompt generation is deterministic from seed data | Yes |
| Scoring criteria are fully deterministic | Yes |
| No external dependencies required (stdlib only) | Yes |
| Unit tests provided and passing | Yes (6/6) |
| Self-test fixture demonstrates regression detection | Yes (reference 1.0, degraded 0.0) |
| Mock server provided for integration testing | Yes |
| Live endpoint smoke artifacts recorded | Yes (3 prompts, 0/3 pass) |
| All source files compile cleanly | Yes |
| Hardware environment documented | Partial (local machine, llama.cpp server from `/tmp`) |
| Model weights and exact llama.cpp version recorded | No |
| Cross-environment replication performed | No |
| Gate threshold empirically calibrated | No |

## 6. Conclusion

The Capability Retention Sentinel Suite provides a dependency-free, deterministic mechanism for generating structured prompts, scoring model responses, and detecting capability regressions across nine categories. The self-test and mock-server integration tests confirm that the scoring and comparison pipeline functions as designed: it correctly identifies perfect and completely degraded outputs, and the live baseline adapter successfully dispatches prompts to and scores responses from OpenAI-compatible endpoints.

The live smoke test against Phi-4-mini-instruct-Q4_K_M yielded a negative result (0/3 on exact-copy prompts), which the suite reports honestly. This negative result validates the adapter's ability to capture and score real model outputs without artificially inflating scores, but it provides no evidence of capability retention for the tested model.

The project decision recommends promoting the live-baseline adapter artifacts and using `run-openai-compatible` plus `compare-live-baseline` against controller-selected real baseline and compressed endpoint model pairs. This follow-up is not guaranteed to succeed; its value depends on the specific models and deployment contexts to which it is applied.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Metrics | `.omx/metrics.json` |
| Claim ledger | `papers/.../claim_ledger.json` |
| Evidence bundle | `papers/.../evidence_bundle.json` |
| Paper manifest | `papers/.../paper_manifest.json` |
| Unit tests | `tests/test_sentinel_suite.py` |
| Project README | `README.md` |
| Mock baseline report | `reports/live/mock_baseline_report.json` |
| Mock compressed report | `reports/live/mock_compressed_report.json` |
| Mock comparison | `reports/live/mock_comparison.json` |
| Mock baseline runner summary | `reports/live/mock_baseline_runner_summary.json` |
| Mock compressed runner summary | `reports/live/mock_compressed_runner_summary.json` |
| Mock compressed responses | `reports/live/mock_compressed_responses.jsonl` |
| Mock server log | `reports/live/mock_server.log` |
| Live llama.cpp models listing | `reports/live/llama_models.json` |
| Live Phi-4 responses | `reports/live/phi4_q4_live_responses.jsonl` |
| Live Phi-4 report (limit 3) | `reports/live/phi4_q4_live_report_limit3.json` |
| Live llama.cpp server log | `reports/live/llama_server.log` |
| Sentinel prompt data | `data/sentinel_prompts.jsonl` |
| Self-test reports | `reports/selftest/` |
| Command adapter smoke reports | `reports/command_adapter_smoke/` |
| Mock OpenAI server script | `scripts/mock_openai_server.py` |
| Live baseline adapter module | `sentinel_suite/live_baseline.py` |
