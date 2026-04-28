# Agent Identity Rotation: Signed-Envelope Privilege Separation for Local Agent Workflows

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present Agent Identity Rotation, a mechanism that enforces privilege separation among planner, executor, and committer agent roles through HMAC-SHA256-signed action envelopes with nonce-based replay protection. In a bounded local-harness evaluation, the policy blocked 12 of 12 adversarial privilege-escalation attempts across real local operations (file writes, command execution, git commits, delegated handoffs, symlink escapes, and serialized tool-call tampering) while allowing 7 of 7 legitimate workflow steps with zero false denies. An unrestricted baseline accepted all 12 adversarial operations. A persisted append-only audit log with independent signatures and hash chaining produced 22 verifiable entries. These results support the hypothesis that identity-separated signed envelopes can prevent cross-role privilege escalation in a local-first control-plane slice. However, the evaluation remains confined to a synthetic adversarial corpus within a deterministic harness; integration with live multi-agent runtimes and LLM-generated workflows remains untested.

## 1. Introduction

Autonomous agent systems that plan, execute, and commit changes to shared workspaces face a fundamental privilege-separation problem: a compromised or misdirected planning step should not be able to directly execute filesystem writes or commit code, and an executor should not be able to escalate to commit privileges. Traditional access-control mechanisms operate at the process or user level and do not map cleanly onto the logical role boundaries within an agent control plane.

Agent Identity Rotation addresses this by assigning distinct cryptographic identities to each agent role—planner, executor, and committer—and requiring that every action be submitted as a signed envelope specifying the actor, the action type, and a nonce. The harness validates the signature against the claimed role, checks that the action type falls within that role's capability set, and rejects any cross-role escalation, signature tampering, or replayed envelope.

This paper reports the design, incremental implementation, and bounded evaluation of this mechanism across three stages: (1) an in-memory toy harness, (2) a local-operation harness gating real filesystem writes, command execution, and git commits, and (3) an expansion adding persisted audit logging, symlink hardening, delegated-agent handoffs, and a broader adversarial corpus. We report both positive and negative findings with full transparency about the scope limitations of the evaluation.

## 2. Method

### 2.1 Role Identity Model

Three roles are defined with non-overlapping capability sets:

- **Planner**: may only issue `plan` actions and `delegate_task` handoffs with bounded recipient role, allowed actions, and optional path prefix constraints.
- **Executor**: may issue `write_file` (workspace-relative, symlink-refusing) and `run_command` (restricted to a no-shell allowlist: `git`, `python3`).
- **Committer**: may only issue `git_commit`, which performs `git add .`, `git commit`, and `rev-parse` within a workspace repository.

Each role holds a distinct HMAC-SHA256 key. Action envelopes contain the actor identity, action type, parameters, and a nonce; the envelope is signed with the actor's key.

### 2.2 Signed-Envelope Protocol

Every action is submitted as a signed envelope. The harness validates:

1. **Signature integrity**: The envelope HMAC matches the claimed actor's key.
2. **Role capability**: The action type is permitted for the claimed role.
3. **Nonce freshness**: The nonce has not been previously observed (replay protection).
4. **Workspace confinement**: File writes resolve to workspace-relative paths; symlink final paths and components are refused, with `O_NOFOLLOW` used when available.
5. **Command allowlisting**: `run_command` actions are restricted to the configured allowlist without shell expansion.

Denied actions are recorded in the audit log with their (invalid) envelope data preserved as evidence.

### 2.3 Persisted Audit Log

Accepted and denied events are written to a durable JSONL audit log. Each entry contains:

- A chained hash linking to the previous entry.
- An independent HMAC signature derived from a key separate from all role keys.
- The full action envelope (or tampered envelope for denied entries).

An independent verifier checks entry signatures, hash chain continuity, sequence ordering, and the validity of accepted-envelope signatures. Denied entries with bad envelopes are counted separately and remain valid audit evidence.

### 2.4 Implementation

The implementation is a Python 3 stdlib-only harness (`src/identity_rotation.py`) with two layers:

- `AgentOSHarness`: the original in-memory toy harness for longitudinal comparison.
- `LocalOperationHarness`: the extended harness gating real local effects.

The evaluation script (`run_identity_eval.py`) compares the governed harness against an unrestricted manual/control-plane baseline that accepts all actions without role or signature checks.

## 3. Results

### 3.1 Toy Harness (In-Memory)

The initial evaluation used the `AgentOSHarness` with synthetic in-memory actions:

| Metric | Policy | Baseline |
|---|---|---|
| Legitimate actions allowed | 3/3 | 3/3 |
| Privilege escalations blocked | 6/6 | 0/6 |
| Signature tamper blocked | Yes | N/A |
| Replay blocked | Yes | N/A |
| False denies | 0 | 0 |
| Wall-clock time | ~0.00015 s | — |

The toy harness demonstrated that signed envelopes prevent the specific cross-role escalation patterns that an unrestricted baseline accepts. However, this result is confined to in-memory actions with no real side effects.

### 3.2 Local-Operation Harness

The `LocalOperationHarness` was evaluated with real local operations:

| Metric | Policy | Baseline |
|---|---|---|
| Legitimate operations allowed | 5/5 | 5/5 |
| Adversarial operations blocked | 8/8 | 0/8 |
| False denies | 0 | 0 |
| Tamper blocked | Yes | N/A |
| Replay blocked | Yes | N/A |
| Wall-clock time | ~0.0371 s | — |
| Per-action latency (mean) | ~2.78 ms | — |
| Per-action latency (p50) | ~0.012 ms | — |
| Per-action latency (p95) | ~8.52 ms | — |

Legitimate operations included `plan`, `git init`, `write_file`, `python3 src/app.py`, and `git_commit`. Adversarial operations included cross-role write/command/commit attempts, executor self-commit, committer write/command, path traversal, and shell escape. The policy blocked all eight; the baseline blocked none.

### 3.3 Persisted Audit and Expanded Adversarial Corpus

After adding the persisted audit log, symlink hardening, delegated-agent handoffs, and expanded adversarial cases:

| Metric | Value |
|---|---|
| Combined policy prevention rate | 1.0 (12/12) |
| Combined baseline prevention rate | 0.0 (0/12) |
| Legitimate operations allowed | 7/7 |
| Adversarial operations blocked | 12/12 |
| False denies | 0 |
| Audit log entries | 22 |
| Audit log denied entries | 13 |
| Bad-envelope signature captured | 1 |
| Audit log verification | Passed |
| Failed-operation recovery | Yes |
| Wall-clock time | ~0.0385 s |

The 12 adversarial operations span: cross-role escalation (write, command, commit), executor self-commit, committer write/command, path traversal, shell escape, symlink escape, serialized tool-call tampering, and delegated-handoff boundary violation. The audit log's independent verifier confirmed hash chain integrity, signature validity, and correct classification of accepted versus denied entries.

### 3.4 Unit Tests

14 unit tests passed, covering: legitimate toy workflow, cross-role denial (toy), signature tamper denial, replay denial, real local writes, real command execution, real git commit, cross-role operation denial, workspace escape denial, unallowlisted shell denial, persisted audit verification, serialized tool-call tampering, symlink/path escape denial, delegated handoff bounds, and failed-operation recovery.

### 3.5 Resource Utilization

The evaluation is CPU-only. No GPU or model inference endpoint is involved. The `identity_rotation_eval.json` artifact records RSS, loadavg, MemAvailable, SwapFree, samples/sec, and steps/sec. Per-action latency is dominated by real subprocess/git effects rather than policy overhead.

## 4. Limitations

1. **Synthetic adversarial corpus**: The 12 adversarial operations are hand-crafted for the harness. They do not represent the distribution of attacks that would arise from LLM-generated workflows, prompt injection, or adversarial tool-call sequences in a live multi-agent runtime.

2. **Deterministic harness**: The policy enforcement path is deterministic and single-threaded. Concurrent access, race conditions on symlink creation, and TOCTOU vulnerabilities in workspace path resolution are not exercised under realistic concurrency.

3. **No live runtime integration**: The mechanism has not been wired into an actual multi-agent framework (e.g., a Codex/OMX tool gateway). Behavior under real tool-call serialization, multi-step repair workflows, and delegated-agent handoffs in production settings is unknown.

4. **No LLM-generated workflow coverage**: All test actions are programmatically constructed. The mechanism's behavior when actions are generated by language models with ambiguous intent, partial failures, or recovery patterns has not been evaluated.

5. **Local-only scope**: The harness gates local operations on a single machine. Network-based escalation, remote agent delegation, and distributed audit log integrity are out of scope.

6. **HMAC key management**: Role keys are held in-process. Key rotation, compromise recovery, and secure key provisioning for long-running or distributed deployments are not addressed.

7. **Audit log durability**: The JSONL audit log is written to local disk. Write-ahead logging, crash recovery, and tamper-evident storage beyond hash chaining are not implemented.

8. **No external replication**: All results are from a single execution environment. No independent replication has been performed.

9. **Perfect prevention rate is a corpus artifact**: The 12/12 prevention rate reflects the composition of the synthetic corpus, not a guarantee against novel attack vectors.

## 5. Reproducibility Checklist

- **Source code**: `src/identity_rotation.py`, `run_identity_eval.py`, `tests/test_identity_rotation.py`, `src/__init__.py`
- **Evaluation command**: `./run_identity_eval.py`
- **Test command**: `python3 -m unittest discover -s tests -v`
- **Compilation check**: `python3 -m py_compile src/identity_rotation.py run_identity_eval.py tests/test_identity_rotation.py`
- **Dependencies**: Python 3 standard library only; no external packages required
- **Result artifacts**: `artifacts/identity_rotation_eval.json`, `artifacts/identity_rotation_audit.jsonl`
- **Workspace artifacts**: `artifacts/local_workflow_workspace/` (contains `recovery.txt`, `src/app.py`, `delegated/out.txt`, `link_to_outside.txt`)
- **Symlink test artifact**: `artifacts/outside_symlink_target.txt`
- **Git proof**: `artifacts/local_workflow_workspace` contains commits `Record signed local workflow` and `Recover after failed operation`
- **Hardware**: CPU-only; no GPU or model inference required
- **Environment notes**: `identity_rotation_eval.json` records RSS, loadavg, MemAvailable, SwapFree

## 6. Conclusion

Agent Identity Rotation provides a mechanism for enforcing privilege separation among planner, executor, and committer agent roles through cryptographically signed action envelopes. In a bounded local-harness evaluation with a synthetic adversarial corpus, the policy blocked all 12 privilege-escalation attempts while allowing all 7 legitimate workflow steps with zero false denies. A persisted append-only audit log with independent signature verification produced 22 verifiable entries capturing both accepted and denied actions. These results support the hypothesis that identity-separated signed envelopes can prevent cross-role privilege escalation in a local-first control-plane slice.

The evidence strength is classified as strong within the tested setting, but the result is bounded by significant limitations: the adversarial corpus is synthetic, the harness is deterministic and single-threaded, no live multi-agent runtime integration has been performed, and no LLM-generated workflows have been tested. The project decision recommends finalizing this bounded local harness result and pursuing a separate follow-on only for a concrete real-runtime integration target. Readers should not interpret the perfect prevention rate as a guarantee against novel attack vectors outside the tested corpus.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Evidence bundle | `papers/source-record-redacted/evidence_bundle.json` |
| Claim ledger | `papers/source-record-redacted/claim_ledger.json` |
| Project decision | `.omx/project_decision.json` |
| Metrics | `.omx/metrics.json` |
| Publication manifest | `papers/source-record-redacted/publication/publication_manifest.json` |
| Evaluation results | `artifacts/identity_rotation_eval.json` |
| Audit log | `artifacts/identity_rotation_audit.jsonl` |
| Harness source | `src/identity_rotation.py` |
| Evaluation script | `run_identity_eval.py` |
| Test suite | `tests/test_identity_rotation.py` |
| Workspace recovery proof | `artifacts/local_workflow_workspace/recovery.txt` |
| Workspace app proof | `artifacts/local_workflow_workspace/src/app.py` |
| Delegated output | `artifacts/local_workflow_workspace/delegated/out.txt` |
| Symlink test link | `artifacts/local_workflow_workspace/link_to_outside.txt` |
| Symlink test target | `artifacts/outside_symlink_target.txt` |
