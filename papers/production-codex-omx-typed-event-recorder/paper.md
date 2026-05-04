# Production Codex OMX Typed Event Recorder: A Local Hook Plugin for Typed Event Persistence and Replay

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, metrics, and log evidence). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We present the design, implementation, and local validation of a typed event recorder implemented as an Oh-My-Codex (OMX) hook plugin. The recorder consumes OMX hook envelopes, validates and classifies them against a typed schema, and persists them as newline-delimited JSON (NDJSON) with append-only semantics. In local prototype testing on an ARM64 Linux host, the plugin passed OMX discovery and synthetic dispatch, recording 12 hook events across lifecycle and tool classes. A 1000-event throughput calibration achieved approximately 14,400 events per second for append and 4.35 ms for full replay. The prototype is not yet integrated upstream and carries known limitations around rotation, backpressure, and a bootstrap ordering dependency on pre-compiled output. We report these results with appropriate caveats regarding their scope.

## Introduction

Automated coding agents produce streams of lifecycle and tool-use events during session execution. Persisting these events in a typed, queryable form supports debugging, auditing, and post-hoc analysis. The Oh-My-Codex (OMX) hook system provides an extension point—`onHookEvent(event, sdk)`—that allows plugins to observe events as they occur, without modifying the OMX runtime itself.

This work investigates whether a typed event recorder can be implemented entirely as an OMX hook plugin, using only the public hook API, and whether such a recorder meets basic correctness and throughput requirements for local use. We do not address upstream integration, distributed collection, or long-running production workloads in this prototype.

The contributions of this work are:

1. A TypeScript type contract and runtime validator for OMX hook envelopes.
2. An append-only NDJSON recorder with context sanitization, event classification, and severity mapping.
3. An OMX hook plugin (`typed-event-recorder.mjs`) that wires the recorder into the OMX event stream.
4. Empirical calibration of append throughput and replay latency on a single host.

## Method

### Type Contract

The type contract (`src/types.ts`) defines a `TypedRecorderEvent` structure that wraps the OMX hook envelope with additional fields: a unique event ID (including a nonce), a timestamp, a severity classification, an event class (e.g., `lifecycle` or `tool`), and a sanitized context payload. Event IDs are unique by construction but are not deterministic content hashes.

### Recorder

The recorder (`src/recorder.ts`) performs the following steps for each incoming event:

1. **Validation**: Runtime type-checking of the incoming hook envelope against the type contract.
2. **Context sanitization**: Removal or redaction of fields not intended for persistent storage.
3. **Classification**: Mapping the event to a class (`lifecycle`, `tool`, or extensible future classes) and a severity level.
4. **Append-only persistence**: Serializing the typed event as a single NDJSON line and appending to a configured output file.
5. **Replay**: Reading the NDJSON file, validating each line against the type contract, and producing summary statistics.

### OMX Hook Plugin

The plugin (`.omx/hooks/typed-event-recorder.mjs`) implements the OMX hook interface via `onHookEvent(event, sdk)`. On each invocation, it delegates to the recorder. The plugin is discovered and invoked by the OMX hook system automatically; no modification to OMX source code is required.

### CLI

A small CLI (`src/cli.ts`) supports recording individual events and replaying summaries from persisted NDJSON files.

### Test and Calibration

- **Unit tests** (`test/recorder.test.ts`): Three `node:test` cases covering validation, normalization, and append/replay correctness.
- **Smoke test** (`scripts/smoke.mjs`): Direct API call persisting one event and replaying it.
- **OMX validation**: `omx hooks validate` confirming plugin discovery and shape compliance.
- **OMX synthetic dispatch**: `omx hooks test` dispatching synthetic events through the hook system to the plugin.
- **Throughput calibration** (`scripts/bench.mjs`): 1000 sequential append operations followed by full replay, measuring wall-clock elapsed time.

### Host Environment

All experiments ran on Linux `gx10-efe8` 6.17.0-1014-nvidia, aarch64, with 127.5 GB total memory and approximately 122.4 GB available at observation time. Swap is disabled (SwapTotal: 0 kB). The workload was intentionally small; no long-running memory or stability test was performed.

## Results

### Build and Unit Tests

The TypeScript project compiled and all three unit tests passed. The build step (`tsc`) produced the `dist/` directory required by the OMX hook plugin.

### Direct API Smoke Test

One event was persisted via the direct recorder API and successfully replayed. The output was written to `.omx/events/smoke-typed-events.ndjson`.

### OMX Plugin Validation and Dispatch

After the initial build, `omx hooks validate` reported `✓ typed-event-recorder.mjs`. The synthetic dispatch via `omx hooks test` reported `typed-event-recorder: ok`.

The hook event stream summary after the final dispatch contained 12 events:

| Class      | Count |
|------------|-------|
| lifecycle  | 2     |
| tool       | 10    |

All 12 events were classified as severity `info`. The summary JSON is recorded in `.omx/logs/typed-events-summary-final2.json` and the full event stream in `.omx/events/typed-events.ndjson`.

### Throughput Calibration

The 1000-event calibration produced the following measurements:

| Metric                | Value          |
|-----------------------|----------------|
| Events appended       | 1000           |
| Append elapsed        | 69.45 ms       |
| Append throughput     | ~14,400 evt/s  |
| Events replayed       | 1000           |
| Replay elapsed        | 4.35 ms        |

These results are from a single calibration run on an otherwise idle host. No statistical replication was performed, so these figures should be treated as indicative rather than rigorous benchmarks. The calibration output is in `.omx/events/bench-typed-events.ndjson` and `.omx/logs/bench.log`.

### Bootstrap Ordering Failure

Before the first TypeScript build, the OMX hook system attempted to invoke the plugin. Because `.omx/hooks/typed-event-recorder.mjs` imported `../../dist/src/index.js`, which did not yet exist, those early invocations failed. After `npm test` built `dist/`, all subsequent invocations succeeded. This is a packaging and deployment concern rather than a correctness bug, but it represents a real operational hazard for any workflow that installs hook plugins before their first build.

## Limitations

1. **Local prototype only.** This implementation is project-local and has not been submitted to or integrated with the upstream `oh-my-codex` repository.

2. **No long-running validation.** The experiments consist of a smoke test, a single synthetic dispatch (12 events), and a 1000-event calibration. No sustained workload, memory leak test, or multi-session durability test was performed.

3. **No rotation or retention policy.** The append-only NDJSON file grows without bound. Production use requires rotation, retention limits, and backpressure/error-policy decisions.

4. **No schema publishing.** The type contract is local to this project. External consumers would require a published and versioned JSON Schema.

5. **Non-deterministic event IDs.** Event IDs include a nonce for uniqueness but are not content-addressable. This precludes deduplication by content hash.

6. **Bootstrap dependency on pre-built output.** The plugin imports from `dist/`, which must exist before the OMX hook system invokes the plugin. Production packaging should ship compiled plugin code or a self-contained bundle.

7. **Single-host, single-calibration-run throughput figures.** The ~14,400 evt/s figure is not statistically characterized and may vary with host load, event payload size, and I/O subsystem behavior.

8. **No access to the originating Notion specification.** The private Notion page referenced in the project metadata was not accessed; the only available specification was the prompt and project metadata.

## Reproducibility Checklist

- [x] Source code available in project directory (`<control-plane-projects>/source-record-redacted`)
- [x] Build command documented: `npm test` (compiles TypeScript and runs tests)
- [x] Unit test results logged: `.omx/logs/npm-test-final.log` (3/3 passed)
- [x] Smoke test results logged: `.omx/logs/smoke.log`
- [x] OMX validation results logged: `.omx/logs/omx-hooks-validate-final.log`
- [x] OMX dispatch results logged: `.omx/logs/omx-hooks-test-final.log`
- [x] Event stream persisted: `.omx/events/typed-events.ndjson`
- [x] Event summary persisted: `.omx/logs/typed-events-summary-final2.json`
- [x] Throughput calibration logged: `.omx/logs/bench.log`
- [x] Calibration output persisted: `.omx/events/bench-typed-events.ndjson`
- [x] Decision JSON recorded: `.omx/project_decision.json`
- [x] Host environment described (kernel, architecture, memory, swap)
- [ ] Statistical replication of throughput figures (not performed)
- [ ] Long-running stability test (not performed)
- [ ] Cross-platform or cross-host replication (not performed)

## Conclusion

A typed event recorder can be implemented as an OMX hook plugin without modifying the OMX runtime. Local validation confirms that the plugin is discovered, invoked, and persists events correctly through both direct API calls and the OMX hook dispatch path. A 1000-event throughput calibration suggests append rates on the order of 14,000 events per second on the test host, with sub-5 ms replay of 1000 events.

These results support the assessment of a viable local prototype with high confidence for local OMX hook event recording and medium confidence for production rollout. The gap between local viability and production readiness is defined by the absence of rotation, backpressure, schema publishing, long-running stability data, and upstream integration. The bootstrap ordering dependency—where the plugin fails if invoked before its first build—must also be resolved before any deployment that installs hook plugins prior to compilation.

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Type contract | `src/types.ts` |
| Recorder implementation | `src/recorder.ts` |
| CLI | `src/cli.ts` |
| OMX hook plugin | `.omx/hooks/typed-event-recorder.mjs` |
| Unit tests | `test/recorder.test.ts` |
| Smoke test script | `scripts/smoke.mjs` |
| Calibration script | `scripts/bench.mjs` |
| Build/test log | `.omx/logs/npm-test-final.log` |
| Smoke test log | `.omx/logs/smoke.log` |
| OMX validate log | `.omx/logs/omx-hooks-validate-final.log` |
| OMX dispatch log | `.omx/logs/omx-hooks-test-final.log` |
| Event stream summary | `.omx/logs/typed-events-summary-final2.json` |
| Persisted events (dispatch) | `.omx/events/typed-events.ndjson` |
| Persisted events (smoke) | `.omx/events/smoke-typed-events.ndjson` |
| Calibration log | `.omx/logs/bench.log` |
| Persisted events (calibration) | `.omx/events/bench-typed-events.ndjson` |
| Decision JSON | `.omx/project_decision.json` |
| Metrics JSON | `artifacts/metrics.json` |
| Command log index | `commands.md` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260501T113016046336+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T113016046336+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T113016046336+0000/paper_manifest.json` |
