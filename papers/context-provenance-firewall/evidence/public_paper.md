# Context Provenance Firewall: Provenance-Preserving Prompt Compilation and Source/Sink Authorization for Agent Safety

> **AI Provenance / No-Human-Credit Note:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review is asserted or implied.

---

## Abstract

We present Context Provenance Firewall, a deterministic middleware approach to reducing the blast radius of indirect prompt injection in agent and retrieval-augmented generation (RAG) systems. Rather than attempting to classify or filter malicious content—a strategy that prior security guidance suggests is inherently incomplete—the firewall preserves source provenance metadata throughout prompt assembly, separates trusted instruction-channel content from untrusted evidence-channel content, and enforces source/sink authorization checks before side-effectful actions. In a synthetic evaluation with four deterministic test cases, naive prompt assembly exposed two untrusted instruction-like chunks on the instruction surface, while firewalled assembly exposed zero. The firewall flagged two suspicious untrusted chunks and routed two side-effect actions influenced by untrusted text to a `needs_review` state, while allowing two benign or trusted-origin actions. These results are from synthetic deterministic cases only; no live LLM attack-success measurements were performed. The approach shows promise as a composable middleware layer but is not a complete prompt-injection solution.

## Introduction

Indirect prompt injection—where malicious instructions are embedded in web pages, documents, or other content that an LLM agent retrieves—has been identified as a principal risk for agentic LLM systems. OpenAI describes the risk as growing proportionally with agent access to sensitive data and user-delegated actions. The OWASP Top 10 for LLM Applications ranks prompt injection as LLM01 and flags untrusted plugin/input handling, excessive agency, and sensitive information disclosure as compounding risks.

Recent security guidance from OpenAI (2026) argues that input filtering alone is insufficient: systems should be designed to constrain impact even when manipulation succeeds, using source/sink analysis and safeguards around dangerous actions and data transmission. This insight reframes the problem. Rather than asking whether retrieved content *is* an injection, one can ask whether untrusted content has been allowed to *reach* instruction-channel surfaces or *authorize* side-effect actions—regardless of its content.

We investigate a concrete instantiation of this principle: a small, deterministic "context provenance firewall" that operates at the prompt-assembly layer. The firewall makes three contributions:

1. **Provenance-preserving prompt compilation.** Each context chunk carries structured metadata (trust level, source URI, purpose, SHA-256 hash). The compiler separates trusted instructions from untrusted evidence blocks and records a manifest, preventing untrusted text from silently occupying the instruction surface.

2. **Suspicion flagging without content suppression.** Untrusted chunks exhibiting instruction-like characteristics are flagged but not dropped. Evidence remains available for the model to reason over; it is simply not placed where the model would treat it as policy.

3. **Source/sink action authorization.** Before side-effectful actions (e.g., sending email, making HTTP POST requests, deleting files, executing shell commands), a deterministic check verifies that the action's authorization chain traces to trusted sources. Actions influenced by untrusted retrieval text are routed to a review state rather than executed outright.

We emphasize at the outset: this is a prototype evaluated on synthetic deterministic cases. It does not constitute a complete prompt-injection defense, and no live LLM attack-success measurements are claimed.

## Method

### Design Principles

The firewall is designed around three principles derived from prior security guidance:

- **Provenance over classification.** Rather than attempting to detect malicious content via classifiers or pattern matching, the firewall tracks where content came from and what role it is authorized to play. This aligns with guidance that input filtering is incomplete and that systems should constrain impact even when manipulation succeeds.

- **Separation of channels.** LLM prompts conflate multiple communication channels: system instructions, user requests, retrieved evidence, and tool outputs. The firewall enforces a structural separation between the instruction channel (trusted) and the evidence channel (potentially untrusted).

- **Authorization before action.** Side-effectful operations require a provenance check on both the action type and its arguments. If the authorization chain includes untrusted sources, the action is not blocked outright but is escalated to a review state.

### Implementation

The prototype is implemented in `src/context_firewall.py` as a no-dependency Python module, tested on Python 3.12.3. Key components:

**ContextChunk.** Each chunk of context is represented as a `ContextChunk` object carrying:

- `chunk_id`: unique identifier
- `trust`: trust level (e.g., `trusted`, `untrusted`)
- `source_uri`: provenance of the content
- `purpose`: intended role (`instruction`, `evidence`, `user_request`)
- metadata dictionary
- SHA-256 content hash

**compile_naive().** A baseline assembler that flattens all context chunks into a single prompt string without preserving provenance. This represents the default behavior of most current RAG and agent systems, where retrieved content, system instructions, and user requests are concatenated without structural distinction.

**compile_firewalled().** The provenance-preserving assembler that:

1. Separates chunks by trust level and purpose.
2. Places trusted instructions on the instruction surface.
3. Places untrusted content in delimited evidence blocks, clearly marked as non-instructional.
4. Records a manifest mapping each chunk to its position and role in the assembled prompt.
5. Flags untrusted chunks that exhibit instruction-like characteristics (e.g., imperative verbs, directive phrasing) without removing them.

**authorize_action().** A deterministic source/sink checker for side-effect actions. For a defined set of dangerous action types (`send_email`, `http_post`, `delete_file`, `run_shell`), the function:

1. Traces the provenance of the action request and its arguments.
2. If the authorization chain includes only trusted sources, the action is allowed.
3. If the authorization chain includes untrusted sources, the action is marked `needs_review`.
4. Read-only actions (e.g., drafting an answer) are allowed regardless of source provenance.

### Evaluation Design

The evaluation uses a synthetic test harness (`scripts/evaluate_firewall.py`) with four test cases designed to exercise the firewall's core mechanisms:

1. A benign read-only answer drafted from untrusted web retrieval text.
2. An email send action requested by a trusted user.
3. An email send action influenced by untrusted web text containing directive content.
4. A file deletion action influenced by untrusted retrieval text.

Each case is run through both `compile_naive()` and `compile_firewalled()`, and the assembled prompts are analyzed for: (a) whether untrusted instruction-like content appears on the instruction surface, (b) whether the manifest is preserved, (c) whether suspicious chunks are flagged, and (d) the authorization decision for side-effect actions.

This evaluation is purely structural and deterministic. No LLM is invoked; the metrics reflect the properties of the assembled prompt artifacts and the authorization function's behavior, not model responses.

## Results

### Unit Tests

Four unit smoke tests passed in 0.01 seconds, verifying basic construction, compilation, flagging, and authorization logic. These tests confirm that the implementation's core pathways execute without error on their intended inputs but do not constitute coverage of the full input space.

### Synthetic Evaluation

| Metric | Naive Assembly | Firewalled Assembly |
|--------|---------------|-------------------|
| Untrusted instruction-like chunks on instruction surface | 2 | 0 |
| Manifest preserved for all chunks | No | Yes |
| Suspicious untrusted chunks flagged | N/A | 2 |
| Side-effect actions allowed (benign/trusted) | 4 | 2 |
| Side-effect actions routed to review | 0 | 2 |

**Instruction surface exposure.** In naive assembly, two untrusted chunks containing directive content were placed directly on the instruction surface, where an LLM would treat them as policy. In firewalled assembly, zero untrusted chunks reached the instruction surface; they were confined to delimited evidence blocks. This is a structural result: the firewalled compiler physically prevents untrusted content from occupying the instruction surface by construction, not by detection.

**Suspicion flagging.** The firewall flagged two untrusted chunks as suspicious based on instruction-like characteristics. These chunks were not suppressed—they remained available as evidence—but their placement and metadata prevented them from being interpreted as instructions. The flagging heuristic is intentionally simple and makes no robustness claims; it serves as an advisory signal, not a primary control.

**Action authorization.** Two side-effect actions influenced by untrusted retrieval text (an email send and a file deletion) were routed to `needs_review` status. Two benign actions (a read-only answer draft and a trusted user-requested email) were allowed. Naive assembly permitted all four actions without provenance checks, meaning that in a naive system, the untrusted-influenced email and deletion would have executed without any review gate.

### What Was Not Measured

No live LLM was invoked during evaluation. The metrics reflect the structural properties of the assembled prompts and the deterministic behavior of the authorization function, not actual model behavior under attack. The following critical quantities remain unmeasured:

- **Attack success rate** against the firewalled prompt structure when processed by an actual LLM.
- **False positive rate** on legitimate user-requested actions that happen to reference untrusted sources.
- **Answer utility**—whether confining retrieved content to evidence blocks degrades the quality of model outputs.
- **User-review burden**—the rate at which `needs_review` escalations occur in realistic workloads and whether that rate is operationally sustainable.
- **Model compliance with channel delimiters**—whether LLMs reliably respect the structural separation between instruction and evidence blocks.

## Limitations

1. **Synthetic evaluation only.** The four test cases are deterministic constructions, not a representative sample of real-world prompt-injection attacks. The reduction from 2 to 0 instruction-surface exposures demonstrates the mechanism's structural effect but does not establish its effectiveness against adaptive adversaries or diverse injection strategies. An adaptive adversary aware of the firewall's structure may attempt to exploit the evidence-channel content in ways the structural separation does not prevent.

2. **No live LLM validation.** Because the project directory contained no model harness or credentials, no LLM was called. It remains unknown whether confining untrusted content to evidence blocks is sufficient to prevent an LLM from following embedded instructions, or whether models reliably respect channel delimiters. This is the most significant gap: the firewall controls the *structure* of the prompt, but whether that structural control translates to *behavioral* control depends on model properties that were not measured.

3. **Small case count.** Four synthetic cases provide a proof-of-concept demonstration but no statistical basis for generalization. The results should be interpreted as existence proofs of the mechanism's structural behavior, not as estimates of its operational performance.

4. **Suspicion flagging is secondary and heuristic.** The flagging of instruction-like content in untrusted chunks is intentionally a secondary mechanism. It is not a classifier and makes no robustness claims. The primary control is structural separation and source/sink authorization. Over-reliance on the flagging heuristic would reintroduce the classification problem the firewall is designed to avoid.

5. **Review burden unquantified.** Routing actions to `needs_review` shifts risk to a human reviewer. The rate of such escalations, their false positive fraction, and the sustainability of human review under load are unknown. A system that escalates too many actions to review may be effectively equivalent to a system that blocks those actions, or may create review fatigue that undermines the safety benefit.

6. **Scope of action types.** The prototype defines four dangerous action types (`send_email`, `http_post`, `delete_file`, `run_shell`). Real agent systems may have a broader and more ambiguous action surface. The enumeration of dangerous actions is itself a design decision that requires domain-specific threat modeling.

7. **Trust assignment is assumed, not derived.** The firewall requires that trust levels (`trusted`, `untrusted`) be assigned to context chunks before compilation. The correctness of the firewall's behavior depends entirely on the correctness of these assignments. Mislabeling a malicious chunk as `trusted` would bypass all controls. The firewall does not solve the trust-assignment problem; it assumes it is solved upstream.

8. **Notion page access.** An unauthenticated fetch of the project's Notion page returned only generic Notion shell HTML. No private project body content was available to incorporate beyond the title and initial prompt.

## Reproducibility Checklist

- **Code availability:** `src/context_firewall.py`, `tests/test_context_firewall.py`, `scripts/evaluate_firewall.py` are present in the project directory.
- **Evaluation data:** `results/firewall_eval.json` contains the structured evaluation output.
- **Runtime environment:** Python 3.12.3; no external dependencies. Environment telemetry recorded in `logs/environment.log`.
- **Test execution:** `python3 -m pytest -q` reproduces unit tests; `python3 scripts/evaluate_firewall.py` reproduces the synthetic evaluation.
- **Logs:** `logs/pytest.log`, `logs/evaluate_firewall.log`, `logs/notion_head.log`, `logs/notion_extract.log`, `logs/environment.log`.
- **Determinism:** All results are deterministic given the same input. No random seeds or model calls are involved.
- **External service dependencies:** None for core evaluation. The Notion fetch was an optional exploration and does not affect reproducibility of the reported results.
- **Claim audit status:** The claim ledger (`claim_ledger.json`) records `audit_status: blocked_empty_claims`, indicating that no structured claims were extracted for this artifact. This draft should not be treated as having passed a strict claim/evidence audit.

## Conclusion

A deterministic context provenance firewall that preserves source metadata, separates instruction and evidence channels, and enforces source/sink authorization before side-effectful actions is implementable as lightweight middleware with no external dependencies. In synthetic evaluation, it eliminated untrusted instruction-surface exposure (from 2 to 0 cases out of 4), flagged suspicious content without suppressing it, and routed untrusted-influenced actions to review while allowing benign and trusted actions.

These results are structurally meaningful but narrowly scoped. The approach does not claim to detect all prompt injections, nor does it establish LLM behavioral robustness. Its value is in reducing the blast radius of successful manipulations: even if an injection reaches the model, the untrusted content cannot silently authorize dangerous actions or occupy the instruction surface without explicit architectural violation. However, whether this structural guarantee translates to behavioral safety depends on model properties—specifically, whether LLMs reliably respect channel delimiters—that were not measured in this run.

The recommended next step is integration with a live agent or RAG system and evaluation on a larger indirect-prompt-injection corpus, measuring attack success rate, false positive rate on legitimate actions, citation fidelity, answer utility, and user-review burden. Until such measurements exist, the firewall should be regarded as a promising structural pattern with unvalidated operational effectiveness.

---

## Referenced Artifacts

| Artifact | Path / Location |
|----------|----------------|
| Firewall implementation | `src/context_firewall.py` |
| Unit tests | `tests/test_context_firewall.py` |
| Evaluation script | `scripts/evaluate_firewall.py` |
| Evaluation results | `results/firewall_eval.json` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260430T040248344871+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T040248344871+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T040248344871+0000/paper_manifest.json` |
| Pytest log | `logs/pytest.log` |
| Evaluation log | `logs/evaluate_firewall.log` |
| Environment log | `logs/environment.log` |
| Notion fetch log | `logs/notion_head.log` |
| Notion extract log | `logs/notion_extract.log` |

## External Sources Consulted

- OpenAI, "Prompt Injections." https://openai.com/index/prompt-injections/
- OWASP, "Top 10 for Large Language Model Applications." https://owasp.org/www-project-top-10-for-large-language-model-applications/
- OpenAI, "Designing Agents to Resist Prompt Injection" (2026). https://openai.com/index/designing-agents-to-resist-prompt-injection/
- OpenAI, "Agent Builder Safety." https://platform.openai.com/docs/guides/agent-builder-safety
