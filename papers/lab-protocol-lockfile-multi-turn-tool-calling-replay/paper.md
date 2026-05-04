# Lab Protocol Lockfile Multi-Turn Tool-Calling Replay

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metrics, and log files). The operator who released these artifacts claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism.

---

## Abstract

We present a dependency-free Python replay harness that verifies whether a multi-turn, tool-calling lab-agent transcript is reproducible and falsifiable using a protocol lockfile. The lockfile encodes canonical SHA-256 event hashes, a rolling chain hash committing to the full transcript order, and tool-call–to–tool-result bindings via `tool_call_id`. Replay is performed against deterministic local mock lab tools (`inventory.lookup`, `plate_reader.read`, `dilution.plan`). In a single-episode, nine-event transcript, the clean lockfile passes verification. A tampered tool-result control fails with three concrete mismatches (semantic content, event hash, chain hash). A shape-drift control with a missing `tool_call_id` fails with five mismatches (missing ID, unmatched pending call, stale event hash, unresolved tool call, stale chain hash). These results support the hypothesis that a protocol lockfile can make a multi-turn tool-calling transcript reproducible enough to distinguish clean replay from both data tampering and conversation-shape drift, but only under local deterministic replay conditions. The result does not validate live model compliance rates under real decoding variance.

## Introduction

Multi-turn tool-calling interactions between language-model agents and laboratory instruments produce transcripts whose integrity is difficult to verify after the fact. If an agent calls `plate_reader.read` and a human later questions whether the reported absorbance was the actual instrument output, there is typically no cryptographic chain linking the tool call to its result and to the surrounding conversation context.

Protocol lockfiles offer a potential solution: by recording each event in a transcript with a canonical hash and linking events into a rolling chain hash, any subsequent modification to a tool result, a conversation turn, or the ordering of events should be detectable. Additionally, tool-call–to–tool-result bindings (via `tool_call_id`) allow structural verification that every assistant tool call received a corresponding result and vice versa.

The research question addressed here is: **Can a protocol lockfile make a multi-turn, tool-calling lab-agent transcript replayable and falsifiable with local evidence, including detection of tool-result drift and conversation/tool-call shape drift?**

This paper reports on a local prototype implementation with negative controls. It does not make claims about live LLM behavior, real instrument integration, or compliance rates under stochastic decoding.

## Method

### Design Overview

A dependency-free Python replay harness was constructed with the following components:

1. **Canonical JSON hashing** (`lab_protocol_replay/canonical.py`): Each transcript event is serialized to a deterministic JSON representation (sorted keys, fixed spacing) and hashed with SHA-256. This ensures that key-order or whitespace variations do not produce spurious hash mismatches.

2. **Rolling chain hash**: Each event's hash incorporates the previous event's chain hash, producing a single final chain hash that commits to the complete ordered transcript. Any reordering, insertion, or deletion of events invalidates the chain.

3. **Tool-call–to–tool-result binding**: Assistant tool-call events carry a `tool_call_id`. The harness verifies that each tool-call event has a matching subsequent tool-result event with the same ID, and that no tool result exists without a corresponding call.

4. **Deterministic mock lab tools** (`lab_protocol_replay/lab_tools.py`): Three mock tools simulate a wet-lab agent's toolkit:
   - `inventory.lookup`
   - `plate_reader.read`
   - `dilution.plan`

   These tools return deterministic outputs for given inputs, enabling exact replay comparison.

5. **Replay runner** (`lab_protocol_replay/runner.py`): Reads a lockfile, replays each event against the mock tools, recomputes event hashes and the chain hash, and reports mismatches.

### Lockfile Format

Each lockfile is a JSON document containing:

- An ordered list of transcript events (role, content, tool calls, tool results).
- Per-event SHA-256 hashes.
- A final chain hash.
- Metadata including tool-call ID bindings.

### Experimental Conditions

Three lockfiles were tested:

| Condition | File | Purpose |
|---|---|---|
| Valid | `protocols/lab_protocol_replay.lock.json` | Clean transcript; should pass |
| Tampered | `protocols/lab_protocol_replay.tampered.lock.json` | Tool-result content altered; should fail |
| Shape-drift | `protocols/lab_protocol_replay.shape_bad.lock.json` | `tool_call_id` removed from one event; should fail |

The tampered and shape-drift conditions serve as negative controls. They were generated by the same lockfile generator (`scripts/make_lockfiles.py`) with targeted modifications applied to the valid lockfile.

### Execution

All commands were run on a single machine (CPU-only; GPU idle at 0% utilization). The replay harness was invoked as:

```
python3 scripts/run_protocol_replay.py <lockfile> --out <result_file>
```

Unit tests were executed via:

```
python3 -m unittest discover -s tests -v
```

Resource usage was captured with `/usr/bin/time -v`. Full command output is preserved in `results/logs/protocol_replay_verify_v2.log`.

## Results

### Valid Replay

The clean lockfile passed all checks:

- **Outcome**: `ok=true`
- **Episodes**: 1
- **Transcript events**: 9
- **Final chain hash**: `6ea0161ac5d940a34cce6bf4c2942067e37ff86c7d83eb7d8f019f7e43126751`

### Tampered Tool-Result Control

The tampered lockfile failed as expected:

- **Outcome**: `ok=false`
- **Mismatch count**: 3
- **Mismatches**: semantic tool-content mismatch, event hash mismatch, chain hash mismatch

The cascade from content alteration through event hash to chain hash demonstrates that a single tool-result modification propagates through the entire verification chain. This is a desirable property for falsification: a local content change cannot be confined to a single event.

### Shape-Drift Control

The shape-drift lockfile (missing `tool_call_id`) failed as expected:

- **Outcome**: `ok=false`
- **Mismatch count**: 5
- **Mismatches**: missing `tool_call_id`, unmatched pending call, stale event hash, unresolved tool call, stale chain hash

The structural violation of a missing binding ID triggers multiple distinct failure modes, providing richer diagnostic information than a simple hash mismatch. The five mismatches span both structural (missing ID, unmatched call, unresolved call) and cryptographic (stale event hash, stale chain hash) categories.

### Unit Tests

All four unit tests passed (`4/4`).

### Resource Usage

| Metric | Value |
|---|---|
| Max RSS range | 17,600 – 18,484 kB |
| Wall-clock per replay/test | ~0.03 – 0.04 s |
| System MemAvailable | 122,493,572 kB |
| SwapTotal | 0 kB |
| GPU utilization | 0% (CPU-only workload) |

The replay harness is lightweight in both memory and time, consistent with a verification-only workload operating on a small transcript. These resource figures characterize the prototype harness only; they should not be extrapolated to production-scale transcripts.

## Limitations

1. **No live LLM or external tool API was invoked.** The transcript is a pre-recorded deterministic sequence, and the mock tools return fixed outputs. This validates lockfile mechanics and drift detection, not model compliance rates under real decoding variance.

2. **Single episode, single transcript.** The valid replay covers one episode with nine events across two user turns and three tool calls. Generalization to longer transcripts, more complex tool-call graphs, or concurrent tool calls is not demonstrated.

3. **Deterministic mock tools only.** Real lab instruments may return non-deterministic outputs (sensor noise, timing-dependent readings). The current scheme assumes exact reproducibility of tool results, which may require tolerance windows or canonicalization for real-world use.

4. **No private Notion page content was accessed** beyond the project metadata supplied in the prompt. No external data sources were consulted.

5. **No adversarial robustness testing.** The tampered and shape-drift controls represent simple, single-point failures. The scheme has not been tested against adversarial lockfile construction, hash collision attacks, or partial-replay attacks.

6. **Confidence assessment: medium-high.** The project decision classifies the evidence as "prototype with negative controls." The hypothesis is supported for local deterministic replay but not yet for live model behavior.

7. **Claim ledger is empty at time of drafting.** The claim ledger associated with this paper contains no formally registered claims, which limits the degree to which specific assertions can be tracked to evidence.

## Reproducibility Checklist

- [x] **Code available**: All source files are listed in the artifact table with SHA-256 hashes.
- [x] **Lockfiles available**: Valid, tampered, and shape-drift lockfiles are included with hashes.
- [x] **Result files available**: Output JSON for all three conditions is preserved with hashes.
- [x] **Command log preserved**: `results/logs/protocol_replay_verify_v2.log`.
- [x] **Telemetry preserved**: `results/logs/telemetry.log`.
- [x] **Unit tests provided**: `tests/test_protocol_replay.py` (4/4 passed).
- [x] **Dependency-free**: No external packages required beyond the Python standard library.
- [x] **Negative controls included**: Tampered and shape-drift lockfiles serve as negative controls.
- [ ] **Live model validation**: Not performed; recommended as future work.
- [ ] **Multi-episode or long-transcript testing**: Not performed.

## Conclusion

A dependency-free Python replay harness demonstrates that a protocol lockfile can make a multi-turn, tool-calling lab-agent transcript reproducible and falsifiable under local deterministic conditions. The clean lockfile passes verification; a tampered tool-result control fails with three cascading mismatches (semantic, event hash, chain hash); and a shape-drift control with a missing `tool_call_id` fails with five distinct mismatches. The rolling chain hash and tool-call binding mechanism together provide both content-integrity and structural-integrity guarantees.

The result is strongest for deterministic replay and governance checks on recorded transcripts. It does not address live model compliance, stochastic tool outputs, or adversarial lockfile construction. The single-episode, nine-event scale limits generalization claims. If stronger scientific closure is needed, a separate live-model benchmark that captures actual assistant tool-call traces under decoding variance and scores compliance against this lockfile schema would be the appropriate next step.

---

## Referenced Artifacts

| Artifact | Path | SHA-256 |
|---|---|---|
| Canonical hashing module | `lab_protocol_replay/canonical.py` | `fc2f51e85c04b510f0fad125c3d92b15e42305ab992fa299c2fa58a16d340c8f` |
| Mock lab tools | `lab_protocol_replay/lab_tools.py` | `46b56dd7472c0d10b99d606e96337e6d897d7f84e6103217de1762abc829b162` |
| Replay runner | `lab_protocol_replay/runner.py` | `ad8e85466d1440e94d4337cf94ce396ff0a58290680db445d767ba70e88a656b` |
| Lockfile generator | `scripts/make_lockfiles.py` | `5e36f0793543cca825e7e13ff1385a6ae71c6748c014b004809d4dcec5f1db1e` |
| Replay entry point | `scripts/run_protocol_replay.py` | `04f7683fdb75ef1795621646484467b5228665bfd80e052ab87c2f3cdab85bc3` |
| Unit tests | `tests/test_protocol_replay.py` | `02b8bf3be74f2347c79e9eee2e62b595669a64f1cd489b7a4c05d1b46887632b` |
| Valid lockfile | `protocols/lab_protocol_replay.lock.json` | `b0bfa3ef0c2d2cbef6765af14c0b3c28e694498416ecb7b0bd3424c789437522` |
| Tampered lockfile | `protocols/lab_protocol_replay.tampered.lock.json` | `0a8b37704021d9cce2a394da343584487d48e90687464d7f8cd493ec9ca84e7d` |
| Shape-drift lockfile | `protocols/lab_protocol_replay.shape_bad.lock.json` | `b58e95f2d9ce9461d2c21ce6bc3b10b4c1225cfcce3b6d2eec492fdb10545719` |
| Valid replay result | `results/valid_replay_result.json` | `095f137f188979c3cde9980580a53db491dcc7f0128e3544de3b5cf54923c8a2` |
| Tampered replay result | `results/tampered_replay_result.json` | `faafb4e04bd492a93bc405ad47ee66f6d750709321ef23a46dff61ac6bdd3596` |
| Shape-drift replay result | `results/shape_bad_replay_result.json` | `3fc25091d2253c45301959112d2cd358d3009f49909772b275a28132c3802a51` |
| Command log | `results/logs/protocol_replay_verify_v2.log` | `461e2b17984878e2bacaf65f5201cbd569b470601fe03f7c7c46295edefba9ea` |
| Telemetry log | `results/logs/telemetry.log` | `572d8e9754e72dc49ba9305b905646db4d2834e5e4ee285536783d200d2e86b3` |
| Run notes | `run_notes.md` | — |
| Project decision | `.omx/project_decision.json` | — |
| Claim ledger | `papers/source-record-redacted-20260501T035848747813+0000/claim_ledger.json` | — |
| Evidence bundle | `papers/source-record-redacted-20260501T035848747813+0000/evidence_bundle.json` | — |
| Paper manifest | `papers/source-record-redacted-20260501T035848747813+0000/paper_manifest.json` | — |
