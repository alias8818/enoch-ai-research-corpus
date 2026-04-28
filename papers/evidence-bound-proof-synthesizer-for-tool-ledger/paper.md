# Evidence-Bound Proof Synthesizer for Tool Ledger

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present an evidence-bound proof synthesizer that automatically derives checker-accepted proof objects and grant envelopes for a proof-carrying tool ledger. The synthesizer extracts permitted fields, witness hashes, expiry bounds, rollback plans, issuer identifiers, nonces, and grant envelopes from task clauses, approved evidence, tool calls, and trace metadata. On a generated benchmark of 400 rows (200 benign, 200 adversarial), the synthesizer emits checker-accepted proofs for all 200 benign rows and refuses all 200 adversarial rows, with zero unauthorized invocations. On a 1,000-row corpus of real local agent transcripts spanning shell commands, file patches, file writes/deletes, and browser navigation, the synthesizer achieves 95.2% checker/trace acceptance (952/1,000) while the remaining 48 refusals are policy-bounded—29 involve denied command tokens and 19 exceed the maximum argument size. Median synthesized proof size exceeds the manual baseline by 9.54%, below the 10% overhead threshold. Mean synthesis latency is 0.0131 ms on generated traces and 0.0097 ms on real transcripts. These results are limited to the tested local transcript corpus and do not constitute validation on external or production-scale deployments.

## 1. Introduction

Autonomous software agents execute tool calls—shell commands, file writes, browser navigation—whose effects on the host system must be constrained to pre-approved scopes. Proof-carrying authorization provides a principled mechanism: each tool call is accompanied by a proof object that a stateless checker validates against approved evidence before execution proceeds. However, constructing these proof objects manually for every tool call in an agent transcript is impractical at scale.

This work investigates whether a deterministic synthesizer can automatically produce checker-accepted proof objects from the evidence already present in task specifications and transcript metadata, without authorizing calls that fall outside approved scopes. The central hypothesis is that structured evidence—permitted fields, witness hashes, expiries, rollback plans, issuers, nonces, and grants—contains sufficient information for automatic proof synthesis, and that the resulting proofs are accepted by the existing stateless checker at rates meeting or exceeding 95% for benign calls while admitting zero adversarial calls.

We report results from a successor project that extends a parent proof-carrying tool ledger MVP with an automatic synthesizer, a transcript ingester for real agent logs, and an exact-command witness mechanism. The project defined a branch-specific kill condition: halt negative if automatic synthesis cannot produce checker-accepted proofs for at least 95% of benign replayed trace/tool calls, or if synthesized proof size exceeds manual proof size by more than 10% median without improving rejection of overbroad or invalid calls. The kill condition was not triggered.

## 2. Method

### 2.1 System Architecture

The system comprises four components inherited or developed within this project:

1. **Stateless Checker** (`proof_ledger/checker.py`): Inherited from the parent MVP. Validates proof objects against approved evidence without maintaining state between calls. Enforces permitted fields, witness hashes, expiry bounds, command-prefix constraints, argument size limits (`max_arg_bytes`), and denied token lists.

2. **Deterministic Synthesizer** (`proof_ledger/synthesizer.py`): The core contribution. Given a `TaskContext` (containing approved evidence, scope, and policy) and a `ToolCall` record, the synthesizer attempts to construct a proof object and grant envelope that the checker will accept. The synthesis strategy is extractive: it derives proof fields directly from evidence rather than generating novel assertions. For shell commands (`admin.run`), the synthesizer first attempts narrow prefix/segment proofs; if these fail, it falls back to an exact `command.sha256` proof only when the command hash appears in the transcript's `approved_command_hashes`. Denied command tokens (`rm -rf`, `sudo`, fork bombs, `mkfs`, `shutdown`) are refused before any fallback path.

3. **Transcript Ingester** (`proof_ledger/transcript_ingester.py`): Normalizes heterogeneous agent log formats into uniform `TranscriptRow` objects with `TaskContext` evidence and `ToolCall` records. Supports:
   - Codex/OMX JSONL function-call events and stderr exec blocks → `admin.run`
   - `apply_patch` custom tool calls → per-path `file.write` (add/update/move) or `file.delete` (delete hunks)
   - Direct file-write-like tools (`write_file`, `create_file`, `edit_file`) → `file.write`
   - URL-bearing browser/fetch/navigation tools → `browser.navigate` with host-bound evidence

4. **Benchmarks**: Two replay benchmarks exercise the synthesizer on distinct corpora (see Section 3).

### 2.2 Exact Command Witness Mechanism

A key design decision concerns the granularity of authorization. Broad command-prefix proofs authorize any command beginning with an approved prefix (e.g., `git `), which is safe for simple cases but insufficient for complex real transcript commands that do not match any approved prefix. The exact command witness mechanism records SHA-256 hashes of approved commands in transcript evidence. The synthesizer falls back to an exact-hash proof only when the command hash is present in `approved_command_hashes`. The checker validates that the proof's command hash matches an approved hash in evidence. This preserves broad-prefix safety for generated/adversarial cases (where no exact hashes are pre-approved) while enabling authorization of complex but legitimate commands observed in real transcripts.

### 2.3 Safety Constraints

The synthesizer enforces several invariants:

- **Denied token refusal**: Commands containing `rm -rf`, `sudo`, fork bombs, `mkfs`, `shutdown` are refused before any proof emission, including exact-hash fallback.
- **Argument size bound**: Calls whose serialized arguments exceed `max_arg_bytes` are refused, preventing emission of proofs the checker must reject.
- **Path scope enforcement**: Evidence scope `.` covers relative file writes within the repository root but does not permit absolute paths or `..` traversal.
- **Segmented command safety**: For `admin.run`, every segment of `&&`/`;`-chained commands must be individually declared and evidence-prefix approved; unsafe pipes, redirection, and command substitution are refused.

## 3. Results

### 3.1 Generated Benchmark

The generated benchmark (`benchmark_synthesizer.py`) replays 50 synthesized workflows producing 400 total rows: 200 benign and 200 adversarial (including overbroad/tampered evidence and invalid calls).

| Metric | Value |
|---|---|
| Benign rows synthesized and checker-accepted | 200/200 |
| Benign rows trace-accepted | 200/200 |
| Adversarial rows refused by synthesizer | 200/200 |
| Unauthorized adversarial calls allowed | 0/200 |
| Boilerplate proofs rejected by checker | 200/200 |
| Mean synthesis latency | 0.0131 ms |
| Median proof size overhead vs. manual baseline | +9.54% |

The 9.54% median proof size overhead is below the 10% negative threshold defined in the kill condition. Zero adversarial calls were authorized, and all boilerplate (empty/minimal) proofs were rejected by the checker.

### 3.2 Real Transcript Benchmark

The real transcript benchmark (`benchmark_real_transcripts.py`) replays 1,000 rows sampled from local Codex/OMX agent session logs, covering shell commands, file patches, file writes/deletes, and browser navigation.

| Metric | Value |
|---|---|
| Total rows ingested | 1,000 |
| Rows synthesized | 952 |
| Checker-accepted | 952 |
| Trace-accepted | 952 |
| Refused before proof emission | 48 |
| Mean synthesis latency | 0.0097 ms |

**Acceptance by tool kind:**

| Tool Kind | Accepted | Total | Acceptance Rate |
|---|---|---|---|
| `admin.run` | 800 | 830 | 96.4% |
| `file.write` | 149 | 167 | 89.2% |
| `file.delete` | 1 | 1 | 100.0% |
| `browser.navigate` | 2 | 2 | 100.0% |

**Refusal breakdown (48 rows):**

| Refusal Reason | Count |
|---|---|
| Denied command tokens | 29 |
| Oversized tool arguments | 19 |

All 48 refusals are policy-bounded: denied tokens are intentionally never overridden, and oversized arguments exceed the checker's `max_arg_bytes` limit. No refusals result from normalization failures or synthesizer bugs.

### 3.3 Parent Checker Regression

The parent checker benchmark (`benchmark.py`) was rerun in the successor project to verify that synthesizer additions did not degrade existing safeguards. The parent benchmark reports zero unauthorized invocations across single-call, trace, and realistic generated suites.

### 3.4 Unit Tests

A total of 38 unit tests pass, covering checker-accepted synthesized proofs, refusal of unsupported adversarial calls, trace grant/proof authorization, proof tightening, transcript ingestion (Codex custom tool calls, multi-file patch splitting, delete patches, direct file writes, URL navigation), segmented command safety, and exact-hash witness validation.

### 3.5 Evolution of Real Transcript Acceptance

The real transcript acceptance rate improved across three development stages:

| Stage | Accepted | Total | Rate | Primary Gap |
|---|---|---|---|---|
| Shell-only ingestion | 179 | 250 | 71.6% | No non-shell tool kinds |
| Non-shell normalization | 672 | 1,000 | 67.2% | Unsupported pipelines, unsafe constructs, prefix mismatches |
| Exact command witnesses | 952 | 1,000 | 95.2% | Denied tokens (29), oversized args (19) |

The apparent decline from 71.6% to 67.2% reflects the transition from a narrow shell-only sample (250 rows) to a larger, noisier mixed-kind corpus (1,000 rows) with stricter refusal of unsupported shell constructs—not checker leakage. The subsequent rise to 95.2% follows the introduction of exact command witnesses.

## 4. Limitations

1. **Transcript corpus scope**: All real transcript rows originate from local Codex/OMX agent sessions on a single machine. The results do not constitute validation on external, multi-user, or production-scale deployments.

2. **Tool kind coverage**: The `browser.navigate` kind accounts for only 2 of 1,000 real transcript rows, and `file.delete` for only 1. Claims about these tool kinds are weakly supported by the current corpus.

3. **Oversized argument refusals**: 19 rows are refused because their serialized arguments exceed `max_arg_bytes`. A chunked or streamed proof shape could potentially address this gap, but no such mechanism has been implemented or tested.

4. **Denied token policy**: The 29 denied-command-token refusals are intentional and policy-bounded. Whether this policy is appropriate for all deployment contexts is an open question not addressed by the current evidence.

5. **No adversarial real-transcript evaluation**: The real transcript corpus contains only benign agent activity. Adversarial robustness is evaluated only on the generated benchmark. The interaction between exact command witnesses and adversarial real-transcript manipulations has not been tested.

6. **Latency measurements**: Synthesis latency (0.0097–0.0131 ms) reflects pure Python computation on small proof objects. These numbers do not account for I/O, serialization overhead, or concurrent load in a production deployment.

7. **Proof size comparison**: The +9.54% median overhead versus manual baseline is measured on the generated benchmark only. Manual baselines for real transcript proofs were not available for comparison.

8. **Single-implementation evidence**: All results come from a single Python implementation. No alternative implementations, formal verification of the checker, or independent code audit has been performed.

## 5. Reproducibility Checklist

- **Source files available**: `proof_ledger/checker.py`, `proof_ledger/synthesizer.py`, `proof_ledger/transcript_ingester.py`, `benchmark_synthesizer.py`, `benchmark_real_transcripts.py`, `benchmark.py`, `tests/test_synthesizer.py`, `tests/test_transcript_ingester.py`
- **Durable result artifacts**: Listed in Section 6 (Referenced Artifacts)
- **Unit test command**: `.venv/bin/python -m pytest -q` → 38 passed
- **Compile check command**: `.venv/bin/python -m py_compile proof_ledger/*.py benchmark.py benchmark_synthesizer.py benchmark_real_transcripts.py` → passed
- **Generated benchmark command**: `.venv/bin/python benchmark_synthesizer.py`
- **Real transcript benchmark command**: `.venv/bin/python benchmark_real_transcripts.py`
- **Parent benchmark command**: `.venv/bin/python benchmark.py`
- **Python environment**: Project-local `.venv` (exact Python version not recorded in artifacts)
- **Randomness control**: The synthesizer is deterministic; generated benchmark workflows are produced by a seeded generator (seed not recorded in artifacts)
- **Hardware**: Local development machine; no GPU or specialized hardware involved

## 6. Conclusion

A deterministic evidence-bound proof synthesizer for a proof-carrying tool ledger produces checker-accepted proofs for 100% of benign generated traces and 95.2% of benign real agent transcript rows, while authorizing zero adversarial calls in either corpus. The median proof size overhead of 9.54% versus manual baselines remains below the 10% threshold. The remaining 4.8% refusal rate on real transcripts is entirely policy-bounded—denied shell tokens and oversized arguments—rather than caused by normalization failures or synthesizer defects.

The introduction of exact command witnesses was the critical mechanism for lifting real transcript acceptance from 67.2% to 95.2%, enabling authorization of complex legitimate commands without weakening broad-prefix safety for adversarial inputs. The transcript ingester's extension beyond shell-only replay to file patches, file writes/deletes, and browser navigation broadened the tool-kind coverage, though the real corpus remains sparse for non-shell kinds.

These findings support the hypothesis that structured evidence in task specifications and transcript metadata is sufficient for automatic proof synthesis within the tested scope. The results are bounded to the local transcript corpus and single implementation tested here. External replication on diverse agent platforms, larger transcript corpora, and production-scale deployments remains necessary before broader claims are warranted.

## 7. Referenced Artifacts

### Result files
- `artifacts/tool_ledger.jsonl`
- `artifacts/benchmark_cases.json`
- `artifacts/benchmark_report.json`
- `artifacts/synthesis_tool_ledger.jsonl`
- `artifacts/synthesized_proofs.jsonl`
- `artifacts/synthesis_benchmark_report.json`
- `artifacts/real_transcript_tool_ledger.jsonl`
- `artifacts/real_transcript_synthesized_proofs.jsonl`
- `artifacts/real_transcript_synthesis_report.json`
- `artifacts/parent_benchmark_stdout.json`

### Source and configuration files
- `proof_ledger/checker.py`
- `proof_ledger/synthesizer.py`
- `proof_ledger/transcript_ingester.py`
- `benchmark_synthesizer.py`
- `benchmark_real_transcripts.py`
- `benchmark.py`
- `tests/test_synthesizer.py`
- `tests/test_transcript_ingester.py`
- `run_notes.md`
- `README.md`

### Decision and metadata files
- `.omx/project_decision.json`
- `.omx/project.json`
- `.omx/metrics.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/paper_manifest.json`
