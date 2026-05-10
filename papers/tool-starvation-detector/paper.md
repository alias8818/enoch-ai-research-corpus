# Tool Starvation Detector: A Deterministic Trace-Level Guardrail for Agent Tool-Avoidance Failures

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the Enoch control plane. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No independent human review has been performed on the code, results, or interpretation.

---

## Abstract

Autonomous agents that orchestrate external tools can drift into a failure mode where they express commitment to using a tool (shell execution, filesystem inspection, web retrieval, test running) but never issue the corresponding tool call, substituting further reasoning prose instead. We term this failure mode *tool starvation*. This paper presents a deterministic, dependency-free detector that identifies tool starvation in structured event traces by matching assistant intent language against subsequent tool-call events within a bounded window. The detector was evaluated on six synthetic labeled traces (three positive, three negative) and achieved perfect classification in that fixture set. Four unit tests covering starvation, healthy immediate tool use, advisory-only text, and `tool_calls` field detection all pass. A sanity check on a non-agent runtime log produced no false positives. However, the evaluation is confined to synthetic fixtures and does not establish real-world precision or recall. The claim ledger for this artifact records no structured claims and its audit status is *blocked_empty_claims*, meaning the results have not passed formal claim–evidence audit. We discuss the design, its limitations, and the evidence gap that must be closed before production deployment.

## Introduction

Autonomous agents that orchestrate tool use—shell execution, filesystem inspection, web retrieval, database queries, test runners—are increasingly deployed in production workflows. A recurring operational failure mode is *tool avoidance*: the agent's text output expresses commitment to using a tool ("I'll run the tests," "Let me check the file"), but no corresponding tool call appears in the event stream. The agent substitutes further reasoning prose, and the task degrades into ungrounded speculation.

This failure mode is difficult to detect post hoc because the agent's text remains superficially coherent. Existing governance mechanisms—budget markets, typed evidence requirements, planning constraints—address drift at the planning level but do not directly audit the trace for intent–action divergence at the event level.

We define *tool starvation* as a trace-level condition: an assistant turn contains language committing to tool use, and no tool call appears within a bounded subsequent window. We present a prototype detector, evaluate it on synthetic traces, and characterize the evidence gap that remains before meaningful validation.

## Method

### Detector Design

The detector operates on structured event traces in JSON or JSONL format. It follows a deliberately simple, explainable rule pipeline:

1. **Trace parsing.** Accept common trace shapes: JSONL (one event per line), a JSON list of events, or a JSON object with an `events`, `messages`, `trace`, or `turns` field.

2. **Tool-event identification.** An event is classified as a tool call if its `role`, `type`, or `event` field contains the substring `tool`, `function`, or `command`, or if it contains fields named `tool_calls`, `function_call`, `cmd`, or `tool_name`.

3. **Intent detection.** Assistant-turn text is scanned for regex groups matching five intent categories:
   - Filesystem inspection (e.g., "read the file," "check the directory")
   - Execution (e.g., "run the command," "execute the script")
   - Verification (e.g., "verify the output," "confirm the result")
   - Web/external lookup (e.g., "search for," "look up")
   - Explicit tool/shell/command language (e.g., "use the shell," "call the tool")

4. **Advisory suppression.** Language such as "You can run…" or "One approach would be to…" is suppressed unless the assistant is committing to action via markers like `I'll`, `let me`, `need to`, or `must`.

5. **Starvation finding.** A finding is emitted when an assistant turn expresses committed tool intent and either (a) no tool call appears later in the trace, or (b) the next tool call is more than `--max-gap` non-tool events away (default: 2).

### Output Format

Each finding includes: the event index, the matched intent category, a severity level, a numeric score, and an evidence snippet from the assistant turn. When no findings are produced, the detector reports `no_tool_starvation_detected` along with summary counts of assistant turns and tool events.

### Evaluation Procedure

A synthetic labeled-trace fixture generator (`run_experiment.py`) produces six traces:

| Fixture | Label | Description |
|---------|-------|-------------|
| `starved_no_tool.jsonl` | Positive | Assistant commits to tool use; no tool call follows |
| `starved_delayed_tool.jsonl` | Positive | Tool call appears but exceeds the gap threshold |
| `starved_wrong_tool.jsonl` | Positive | Assistant commits to one tool category; a different category's tool fires |
| `healthy_immediate.jsonl` | Negative | Assistant commits; corresponding tool call fires within gap |
| `healthy_advisory.jsonl` | Negative | Assistant discusses tools advisorially without commitment |
| `healthy_no_intent.jsonl` | Negative | Assistant reasons without mentioning tools |

The evaluator computes accuracy, precision, recall, and per-case true/false positive/negative counts against the labels.

### Environment

Experiments ran on a GB10-class machine: Linux kernel 6.17.0-1014-nvidia, aarch64, Python 3.12.3, approximately 122 GB available memory, no swap (per GB10 constraints), earlyoom active. The detector is CPU-only and I/O-light; no GPU or long-running compute was required.

## Results

### Synthetic Evaluation

From the synthetic labeled fixture set (6 cases):

| Metric | Value |
|--------|-------|
| True positives | 3 |
| True negatives | 3 |
| False positives | 0 |
| False negatives | 0 |
| Accuracy | 1.0 |
| Precision | 1.0 |
| Recall | 1.0 |

These figures reflect perfect classification on the synthetic fixture set. The fixture set is small and was designed to exercise the detector's core discrimination axes (committed intent vs. advisory text, immediate tool use vs. starvation, gap threshold enforcement). It does not represent the distribution or ambiguity of real agent traces. The Clopper–Pearson 95% confidence interval for recall with 3/3 true positives is approximately [0.29, 1.0], illustrating the wide uncertainty around these point estimates.

### Unit Tests

Four unit tests were executed, covering:

1. Starvation detection on a trace with committed intent and no tool call.
2. Healthy classification when a tool call immediately follows intent.
3. Advisory-only text correctly not flagged.
4. Detection via `tool_calls` fields in assistant events.

All four tests passed.

### Real-Trace Sanity Check

The detector was run on this project's own OMX runtime log (`.omx/logs/omx-2026-04-29.jsonl`). That log contained only session lifecycle events—no assistant turns or tool-call events. The detector correctly reported `no_tool_starvation_detected` with `assistant_turns=0`. This is a sanity check confirming that the detector does not false-positive on non-agent event streams, not a validation of its agent-trace behavior.

### Claim Audit Status

The claim ledger for this artifact records `audit_status: blocked_empty_claims` with no structured claims extracted. The ledger explicitly notes that "this artifact must not pass strict claim/evidence audit until claims reference public evidence files." The evidence bundle contains only source, project, and run identifiers with no detailed evidence entries. Readers should interpret the reported metrics as prototype-level observations rather than audited scientific claims.

## Limitations

1. **Synthetic-only evaluation.** The six-case fixture set proves mechanical correctness of the detection pipeline, not real-world operating characteristics. Precision and recall on actual agent traces—where intent language is more varied, advisory boundaries are less clear, and tool-call schemas differ—are unknown and likely lower.

2. **Regex intent matching.** The detector relies on handcrafted regex groups to identify committed tool intent. This approach will miss paraphrases outside the patterns and may false-positive on unusual explanatory or pedagogical text that happens to match commitment markers. A learned intent classifier could improve coverage but would sacrifice the deterministic, dependency-free property.

3. **No root-cause attribution.** The detector identifies divergence between assistant text and tool events. It does not determine whether the failure originates in the model (refusal or inability to generate tool calls), the controller (dropping or misrouting tool-call events), the tool bridge (unavailability or timeout), or the scheduler (preempting tool execution before completion).

4. **Gap threshold sensitivity.** The default `--max-gap` of 2 non-tool events is a heuristic. The optimal threshold depends on the agent's turn structure and the latency of tool execution in a given deployment. No sensitivity analysis across gap values has been performed.

5. **No tool-availability metadata.** The detector does not know whether a tool was actually available to the agent at the time intent was expressed. An agent that commits to a web search in an air-gapped environment may be expressing a planning error rather than a starvation event, and the detector cannot distinguish these cases without external context.

6. **Small fixture set.** Six labeled cases are insufficient to estimate generalization. Confidence intervals on the reported 1.0 metrics are wide (e.g., the Clopper–Pearson 95% interval for recall with 3/3 true positives is approximately [0.29, 1.0]).

7. **Blocked claim audit.** The claim ledger contains no structured claims and has audit status `blocked_empty_claims`. The results reported here have not passed formal claim–evidence audit and should be treated accordingly.

## Reproducibility Checklist

- [x] **Code available.** `tool_starvation_detector.py`, `run_experiment.py`, and `tests/test_detector.py` are present in the project directory.
- [x] **Dependencies specified.** The detector is dependency-free (stdlib only). Python 3.12.3 was used.
- [x] **Fixtures available.** Six synthetic trace fixtures are in `fixtures/`.
- [x] **Evaluation script available.** `run_experiment.py` regenerates `artifacts/synthetic_eval_metrics.json`.
- [x] **Unit tests available.** `tests/test_detector.py`; run via `python3 -m unittest discover -s tests -v`.
- [x] **Environment logged.** `logs/environment_20260429T163844.log` captures kernel, Python version, memory, and earlyoom status.
- [x] **Deterministic.** The detector and evaluator are deterministic given the same inputs and parameters.
- [ ] **Real-world trace corpus.** Not available; this is the primary evidence gap.
- [ ] **Cross-environment validation.** The detector has only been run on one machine (aarch64 Linux, Python 3.12.3).
- [ ] **Claim–evidence audit passed.** The claim ledger is in `blocked_empty_claims` status with no structured claims.

## Conclusion

The Tool Starvation Detector is a trace-level guardrail prototype that identifies a specific and operationally relevant failure mode—assistant intent to use tools without corresponding tool calls—using deterministic, explainable rules. On a six-case synthetic fixture set, it achieves perfect classification, and its unit tests pass. A sanity check on a non-agent runtime log produced no false positives. However, these results establish mechanical correctness only. Real-world precision and recall remain unmeasured, and the regex-based intent matcher will inevitably face paraphrases and edge cases not represented in the synthetic fixtures. The claim ledger for this artifact has not passed audit, and no structured claims have been validated.

The recommended next step is integration into a live agent controller (e.g., the Enoch/LangGraph event stream) as a streaming watchdog on assistant turns, followed by evaluation against a labeled historical trace corpus that includes tool-availability metadata. Only with such a corpus can the detector's thresholds be tuned and its operating characteristics meaningfully characterized.

## Referenced Artifacts

| Artifact | Path / Description |
|----------|--------------------|
| Detector implementation | `tool_starvation_detector.py` |
| Synthetic evaluator | `run_experiment.py` |
| Unit tests | `tests/test_detector.py` |
| Synthetic trace fixtures | `fixtures/` (6 JSONL files) |
| Synthetic evaluation metrics | `artifacts/synthetic_eval_metrics.json` |
| Example detector output (starved trace) | `artifacts/starved_no_tool_detection.json` |
| Detector output on OMX runtime log | `artifacts/current_omx_log_detection.json` |
| Durable research metrics | `.omx/research_metrics.json` |
| Project decision record | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Environment telemetry log | `logs/environment_20260429T163844.log` |
| Synthetic evaluation log | `logs/synthetic_eval_20260429T163818.log` |
| Unit test log | `logs/unit_tests_20260429T163834.log` |
| Claim ledger | `papers/.../claim_ledger.json` |
| Evidence bundle | `papers/.../evidence_bundle.json` |
| Paper manifest | `papers/.../paper_manifest.json` |
