# Web-State Replay Benchmark for Rewindable Sandboxes

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present a web-state replay benchmark for evaluating rewindable sandboxes that must capture, redact, and deterministically replay multi-step browser sessions involving authentication state. The benchmark exercises a five-event sequence—HTTP redirect, CSRF token acquisition, cookie-based login, authenticated request, and auth-refresh with re-authentication—against a local deterministic HTTP server. In the tested setting, all five network checkpoints pass on replay, all configured secret-bearing values (cookies, headers, query parameters, and body tokens) are redacted to deterministic digest markers, and per-event trace storage remains well below a 64 KiB/event budget (observed maximum: 5,249 bytes; mean: 4,322 bytes). Replay speedup over recording is approximately 260×. These results are obtained from a synthetic local server environment and have not been validated against captured multi-domain web-agent traces or production browser automation harnesses. Confidence in the finding is medium and evidence strength is moderate, reflecting the gap between local synthetic validation and real-world deployment.

## 1. Introduction

Rewindable sandboxes for web agents require the ability to record a browser session's observable state, persist that recording in a form safe for storage and sharing (i.e., with secrets redacted), and later replay the session deterministically from the redacted trace. Prior work on the parent `rewindable_tool_sandbox` established browser-state replay with cookie and header redaction. However, realistic web sessions involve a broader class of secret-bearing values: CSRF tokens in query parameters and HTML form bodies, session identifiers embedded in URLs, refresh tokens in JSON responses, and multi-step authentication flows with intermediate redirects.

This work extends the redaction surface and introduces a structured benchmark that exercises these realistic web-state patterns. The central question is whether a multi-step web session can be replayed deterministically after redacting secret-bearing values across cookies, headers, query parameters, and response bodies, while remaining within a practical storage budget. A branch-specific kill condition was defined: if the local multi-step session could not be replayed deterministically with secrets redacted, or if trace storage exceeded 64 KiB per event, the approach would be abandoned.

## 2. Method

### 2.1 Redaction Extension

The existing browser-state redaction in `src/rewindable_tool_sandbox/sandbox.py` was extended to cover:

- **Sensitive query parameters:** Parameter names matching `csrf`, `session`, `token`, `refresh`, and similar patterns are detected in recorded URLs. Their values are replaced with deterministic digest markers (hash-based placeholders) rather than raw secret strings.
- **HTML/JSON body token assignments:** Common patterns for token assignment in response bodies (e.g., `"csrf_token": "..."`, `<input name="csrf" value="...">`) are identified and their values replaced with the same digest marker scheme.

The digest marker approach ensures that the same secret value always maps to the same marker, preserving request-matching semantics during replay without exposing the original secret.

### 2.2 Benchmark Design

The benchmark (`benchmark_realistic_web_state.py`) implements a deterministic local HTTP server that serves a fixed five-step web session:

1. **Redirect:** The initial request returns an HTTP 302 redirect.
2. **CSRF form:** The redirected URL serves an HTML page containing a CSRF token in both a query parameter and a form body field.
3. **Login with cookies:** A POST request with the CSRF token returns `Set-Cookie` headers establishing session cookies.
4. **Authenticated request:** A request carrying the session cookies accesses a protected resource.
5. **Auth refresh:** The session cookie expires; a refresh token in the response body is used to obtain a new session, followed by a second authenticated request.

Each step produces a browser event and a network checkpoint. The benchmark records the full session, redacts secrets, then replays from the redacted trace and verifies that each checkpoint matches.

### 2.3 Evaluation Criteria

The benchmark evaluates three properties:

1. **Replay correctness:** All network checkpoints must pass on replay (redirect, CSRF, cookie login, authenticated request, auth refresh).
2. **Secret redaction:** All configured secret-bearing values across cookies, headers, query parameters, and body fields must be redacted (`redacted=True` for each).
3. **Storage budget:** Per-event trace size must not exceed 64 KiB (65,536 bytes), an arbitrary but concrete MVP budget.

## 3. Results

### 3.1 Replay Correctness

All five network checkpoints passed on replay. The redirect, CSRF acquisition, cookie-based login, authenticated request, and auth-refresh steps all produced matching responses when replayed from the redacted trace.

### 3.2 Secret Redaction

All configured secrets were confirmed redacted (`redacted=True`). This includes:

- CSRF tokens in query parameters and HTML body fields
- Session cookie values
- Refresh token values in JSON response bodies
- Authorization header values

No raw secret values persisted in the stored trace.

### 3.3 Storage Budget

| Metric | Value |
|---|---|
| Total trace size | 36,007 bytes |
| Number of browser events | 5 |
| Number of network checkpoints | 5 |
| Average event size | 4,322 bytes |
| Maximum event size | 5,249 bytes |
| MVP budget per event | 65,536 bytes |

The maximum observed event size (5,249 bytes) is approximately 8% of the 64 KiB budget. The total trace for the five-event session is 36,007 bytes.

### 3.4 Replay Speedup

| Metric | Value |
|---|---|
| Recording duration | 0.018469 seconds |
| Replay duration | 0.00007099 seconds |
| Replay speedup | 260.15× |

Replay is substantially faster than recording, as expected: replay serves responses from the stored trace without network latency or server-side computation.

### 3.5 Regression Verification

All verification steps passed:

- Unit tests: `python3 -m unittest discover -s tests -v`
- Benchmark execution: `python3 benchmark_realistic_web_state.py`
- Compilation check: `python3 -m py_compile` on all benchmark and source files

## 4. Limitations

1. **Synthetic environment only.** The benchmark runs against a local deterministic HTTP server. It has not been validated against captured web-agent traces from real websites, multi-domain sessions, or browser automation harnesses (e.g., Playwright). The observed metrics may not generalize to production web sessions with variable latency, dynamic content, or non-deterministic server behavior.

2. **Redirect representation.** HTTP redirects are represented through the final `urllib` response checkpoint rather than as separate intermediate 302 responses. A production browser integration should log each redirect hop individually. The current benchmark may miss redirect-chain edge cases.

3. **Pattern-based body redaction.** Body redaction relies on pattern matching for known token-assignment formats (e.g., `"csrf_token": "..."`, `<input name="csrf" value="...">`). This approach will miss secrets in unfamiliar formats and may produce false positives on similarly structured non-secret data. An explicit configurable redaction policy is needed before running on arbitrary real web pages.

4. **Limited secret taxonomy.** The redaction covers a fixed set of parameter names (`csrf`, `session`, `token`, `refresh`, etc.). Real web applications use diverse naming conventions for secrets, and the current taxonomy is not exhaustive.

5. **Single-session scope.** The benchmark evaluates one five-step session. It does not test concurrent sessions, session interleaving, or state contamination between independent replay runs.

6. **No cross-domain validation.** All requests target the same local server origin. Cross-origin cookie scoping, CORS headers, and third-party authentication flows are not exercised.

7. **Confidence and evidence strength.** The project decision assigns medium confidence and moderate evidence strength, reflecting the gap between the current synthetic validation and real-world deployment conditions.

## 5. Reproducibility Checklist

- [x] **Benchmark script available:** `benchmark_realistic_web_state.py` in the project directory.
- [x] **Source code available:** `src/rewindable_tool_sandbox/sandbox.py` contains the redaction and replay implementation.
- [x] **Test suite available:** `tests/test_sandbox.py` includes regression coverage for URL/body redaction and replay request matching.
- [x] **Trace artifact available:** `artifacts/realistic_web_state_trace.json` contains the full recorded and redacted trace.
- [x] **Summary artifact available:** `artifacts/realistic_web_state_summary.json` contains aggregated benchmark metrics.
- [x] **Compilation verified:** All Python source and benchmark files pass `py_compile`.
- [x] **Unit tests pass:** `python3 -m unittest discover -s tests -v` completes successfully.
- [ ] **External replication:** Not yet performed. The benchmark has only been run in the project's local environment.
- [ ] **Multi-domain validation:** Not yet performed. Only a single local server origin is tested.
- [ ] **Production browser harness validation:** Not yet performed. The benchmark uses `urllib` rather than a browser automation framework.

## 6. Conclusion

The web-state replay benchmark demonstrates that a multi-step web session involving redirects, CSRF tokens, cookie-based authentication, and auth refresh can be replayed deterministically from a redacted trace in a synthetic local environment. All configured secrets are redacted, and per-event storage remains well within the 64 KiB budget. Replay speedup is approximately 260× over recording.

These results support the viability of the approach within the tested setting but do not establish generalizability to production web sessions. The three principal gaps—synthetic-only validation, pattern-based rather than policy-based redaction, and single-redirect-hop representation—define the minimum scope of work required before the benchmark can inform production deployment decisions. The recommended next step is to promote this benchmark into the parent replay harness and validate it against captured multi-domain web-agent traces with an explicit configurable redaction policy.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Evidence bundle | `papers/.../evidence_bundle.json` |
| Claim ledger | `papers/.../claim_ledger.json` |
| Publication manifest | `papers/.../paper_manifest.json` |
| Benchmark script | `benchmark_realistic_web_state.py` |
| Sandbox source | `src/rewindable_tool_sandbox/sandbox.py` |
| Test suite | `tests/test_sandbox.py` |
| Trace artifact | `artifacts/realistic_web_state_trace.json` |
| Summary artifact | `artifacts/realistic_web_state_summary.json` |
| Metrics | `.omx/metrics.json` |
