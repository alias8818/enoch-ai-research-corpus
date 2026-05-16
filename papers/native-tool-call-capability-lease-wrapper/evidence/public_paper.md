# Capability Lease Wrappers for Least-Privilege Enforcement in Native Tool-Call Runtimes

> **AI Provenance / No-Human-Credit Notice:** This draft was generated automatically from structured research artifacts (run notes, decision records, benchmark metrics, evidence bundles). No human claims authorship credit for the writing or the experimental results beyond releasing the artifacts. Readers should treat this document as an unreviewed AI-generated research artifact. The operator makes no representation that this draft has undergone human peer review, scientific validation, or editorial oversight.

---

## Abstract

Native tool-call interfaces in language-model runtimes allow models to invoke external tools directly, but typically provide no mechanism to constrain *which* tool invocations are permitted, with *what arguments*, or for *how long*. We propose and prototype a capability lease wrapper that mediates every tool dispatch through a lease object binding the tool name, an unguessable nonce, an expiry time, a call budget, and an argument policy (required/allowed keys, literal constraints, string-length bounds, path-root constraints), with an HMAC signature for local tamper detection. The model-visible tool arguments carry only an opaque `_lease` handle; the host-side dispatcher verifies the lease against a registry before invoking the real tool. In a local Python dispatcher harness, the wrapper correctly blocked all six adversarial scenarios (missing lease, wrong tool, path escape, nonce mismatch, revoked lease, budget exhaustion) without reaching the underlying tool, while an unwrapped baseline reached the underlying tool in every case. Median added dispatch overhead was 0.0069 ms over 20,000 iterations (wrapped p95: 0.0073 ms). These results support local viability of the mechanism; production claims require integration with an actual native tool-call host runtime, which was not tested.

## Introduction

Language-model runtimes increasingly expose native tool-call interfaces that let models invoke external functions during inference. While convenient, this creates a privilege escalation surface: a model that can call a tool can, in principle, call it with any arguments the tool accepts, any number of times, at any point in the session. Existing mitigations—prompt-level instructions, output filtering, or tool-level permission checks—operate either too late (after execution) or too coarsely (all-or-nothing access).

Capability-based security offers a principled alternative: grant a principal a *capability*—an unforgeable, attenuable token—that encodes precisely what actions are permitted. We adapt this idea to tool-call runtimes by introducing a *capability lease*: a short-lived, nonce-bound, budgeted, argument-scoped token that the host issues and the dispatcher must verify before any tool execution proceeds.

The central hypothesis is that a native-tool-call runtime can enforce least-privilege access by wrapping each tool dispatch in such a lease, with the model-visible arguments carrying only an opaque handle and the host-side dispatcher performing all verification. This paper reports on a dependency-free Python prototype that tests this hypothesis in a local dispatcher harness. The scope is deliberately narrow: we seek to establish whether the mechanism is locally viable—correct in its blocking semantics and acceptable in its overhead—before investing in integration with a production runtime.

## Method

### Lease Structure

Each lease record contains the following fields:

- **tool**: the specific tool name the lease authorizes.
- **nonce**: a cryptographically unguessable value binding the lease to a particular issuance.
- **expiry**: a timestamp after which the lease is invalid.
- **max_calls**: the maximum number of times the lease may be exercised.
- **arg_policy**: a dictionary specifying required keys, allowed keys, literal value constraints, maximum string lengths, and path-root constraints for tool arguments.
- **hmac**: an HMAC signature over the serialized record, computed with a process-local secret, to detect tampering with the registry.

The model-visible tool arguments include only an opaque `_lease` handle containing the lease `id` and `nonce`. The host-side dispatcher resolves the handle against a lease registry, verifies the HMAC, checks expiry and budget, enforces the argument policy, and only then invokes the underlying tool.

### Prototype Implementation

The prototype (`src/capability_lease.py`) is a dependency-free Python module implementing:

1. A `LeaseManager` that issues, revokes, and looks up leases, and maintains the HMAC-signed registry.
2. An argument policy checker that validates tool arguments against the lease's `arg_policy` before dispatch.
3. A `WrappedDispatcher` that intercepts tool calls, verifies the lease, enforces the argument policy, and either executes or rejects the call.
4. An `UnwrappedDispatcher` that passes calls through directly, serving as a baseline.

No external dependencies are required; the module uses only the Python standard library.

### Evaluation Design

The evaluation comprises three components:

1. **Unit tests** (8 tests in `tests/test_capability_lease.py`) covering lease issuance, revocation, expiry, budget enforcement, argument policy, and HMAC integrity.
2. **Adversarial replay** (in `experiments/run_lease_eval.py`) that replays six attack scenarios against both the wrapped and unwrapped dispatchers:
   - Missing lease handle
   - Wrong tool name
   - Path-escape argument (attempting to traverse outside the permitted root)
   - Nonce mismatch
   - Revoked lease
   - Budget exhaustion (second call after first consumes the budget)
3. **Microbenchmark** (20,000 iterations) measuring dispatch latency for both wrapped and unwrapped paths, reporting median and p95 overhead.

### Environment

The experiments were run on a local machine. The environment probe log (`artifacts/logs/env_probe.log`) records the Python version, kernel, and available memory. No GPU or CUDA calibration was involved; this is a pure Python function-dispatch benchmark, not a networked or hardware-accelerated measurement.

## Results

### Unit Tests

All 8 unit tests passed, covering lease creation, revocation, expiry, call budget, argument policy enforcement, and HMAC tamper detection.

### Adversarial Replay

| Scenario | Wrapped Result | Underlying Tool Reached? | Baseline Result | Underlying Tool Reached? |
|---|---|---|---|---|
| Missing lease | Blocked | No | Executed | Yes |
| Wrong tool | Blocked | No | Executed | Yes |
| Path escape | Blocked | No | Executed | Yes |
| Nonce mismatch | Blocked | No | Executed | Yes |
| Revoked lease | Blocked | No | Executed | Yes |
| Budget exhaustion | Blocked | No | Executed | Yes |

The wrapped dispatcher blocked all six adversarial scenarios without the underlying tool being invoked. The unwrapped baseline reached the underlying tool in all six cases. The `wrapped_expected_status_match` and `blocked_scenarios_without_underlying_execution` flags were both `True`. The `budget_second_call_blocked` flag was `True`.

### Microbenchmark

Over 20,000 iterations of a single-tool dispatch:

| Metric | Value |
|---|---|
| Baseline median dispatch | 0.000224 ms |
| Wrapped median dispatch | 0.007120 ms |
| Median added overhead | 0.006896 ms |
| Wrapped p95 dispatch | 0.007264 ms |

The median added overhead of approximately 0.007 ms is well below 1 ms. However, this measures only Python function-call overhead in a local process; it does not include network latency, serialization costs, or the overhead of a real tool-call host runtime. The figure should be interpreted as an order-of-magnitude indicator for the local dispatch path, not as a production performance prediction.

## Limitations

1. **Local prototype only.** This is a dispatcher harness, not a live integration with a production native-tool-call API. Whether the lease wrapper behaves identically against an actual host runtime (with its own dispatch pipeline, serialization, and error handling) remains untested.

2. **Benchmark scope.** The microbenchmark measures Python function-dispatch overhead on a single machine. It does not account for network round-trips, inter-process communication, or the latency profile of a real tool-call infrastructure. The sub-0.01 ms overhead figure should not be generalized to production deployments.

3. **Lease issuance policy is unspecified.** The prototype demonstrates that a lease, once issued, can be enforced. It does not address which component should issue leases, how prompts or tool schemas expose the required `_lease` fields to model calls, or how lease parameters are determined. These are product-level design decisions outside the scope of this prototype.

4. **Single-process HMAC.** The HMAC signature protects against local registry tampering within a single process using a process-local secret. A distributed or multi-process deployment would require shared-key rotation or a central lease service, neither of which is implemented here.

5. **Delegated agents.** Lease propagation across multi-turn, multi-agent workflows—where one agent delegates tool access to another—was not tested and may require additional protocol design.

6. **No real-model integration.** The prototype does not test how a language model would populate the `_lease` handle in practice, nor whether model behavior changes when lease-enforced constraints are present.

7. **Claim audit incomplete.** The claim ledger for this paper contains no formally registered claims at the time of draft generation. The paper review checklist shows 0 of 9 items resolved. The results reported here are drawn directly from the run notes and project decision record and have not undergone independent verification or formal claim registration.

## Reproducibility Checklist

- **Code availability:** Prototype source (`src/capability_lease.py`), test suite (`tests/test_capability_lease.py`), and evaluation script (`experiments/run_lease_eval.py`) are present in the project directory.
- **Exact commands:** All commands executed are recorded in the run notes and decision JSON:
  - `python3 -m unittest discover -s tests -v`
  - `python3 -m py_compile src/capability_lease.py experiments/run_lease_eval.py`
  - `python3 experiments/run_lease_eval.py --iterations 20000 --out artifacts/metrics/lease_eval_metrics_20k.json`
- **Environment:** Recorded in `artifacts/logs/env_probe.log` (Python version, kernel, memory).
- **Metrics:** Raw metrics in `artifacts/metrics/lease_eval_metrics_20k.json`.
- **Logs:** Unit test output in `artifacts/logs/unittest_smoke.log`; evaluation smoke test in `artifacts/logs/lease_eval_smoke.log`; final verification in `artifacts/logs/final_verify.log`.
- **Randomness:** Nonce generation uses Python's `secrets` module; adversarial replay scenarios are deterministic. No random seeds are required for reproducibility of the blocking behavior. Microbenchmark timings are subject to system load and should be interpreted as order-of-magnitude indicators.
- **Dependencies:** The prototype is dependency-free (standard library only).
- **Bytecode compilation:** Both `src/capability_lease.py` and `experiments/run_lease_eval.py` passed `py_compile` verification.

## Conclusion

A dependency-free capability lease wrapper successfully enforced tool-specific, nonce-bound, expiring, budgeted, and argument-scoped constraints on native tool calls in a local Python dispatcher harness. All six adversarial scenarios were blocked before underlying tool execution, while the unwrapped baseline reached the underlying tool in every case. Median added dispatch overhead was under 0.01 ms over 20,000 iterations.

These results support the local viability of the mechanism: the lease wrapper correctly prevents unauthorized tool invocations at negligible local overhead. However, the prototype operates entirely within a single-process Python harness. Production validation requires integration with an actual native tool-call host/runtime surface, cross-process or distributed lease management, and real-model prompt/schema ergonomics for lease handle propagation. No further local-only experimentation is likely to change the prototype-level conclusion; the remaining questions are inherently integration-dependent.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Research plan | `research_plan.md` |
| Prototype source | `src/capability_lease.py` |
| Test suite | `tests/test_capability_lease.py` |
| Evaluation script | `experiments/run_lease_eval.py` |
| Environment probe log | `artifacts/logs/env_probe.log` |
| Unit test log | `artifacts/logs/unittest_smoke.log` |
| Evaluation smoke log | `artifacts/logs/lease_eval_smoke.log` |
| Final verification log | `artifacts/logs/final_verify.log` |
| Metrics (20k iterations) | `artifacts/metrics/lease_eval_metrics_20k.json` |
| Run notes | `run_notes.md` |
| Project decision record | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260430T205518607063+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T205518607063+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T205518607063+0000/paper_manifest.json` |
