# LLM-Backed Summary Drift Corpus Validation: A Smoke-Test Viability Study

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metrics, and logs). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results beyond releasing the artifact. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We describe a lightweight, dependency-free harness for validating a summary-drift detection corpus using a large language model (LLM) as a batched judge. A synthetic 30-case corpus was constructed from six source documents spanning clinical, finance, legal, science, operations, and education domains. Each source received one faithful summary and four controlled drift variants (entity substitution, number drift, polarity/negation drift, unsupported addition). A deterministic sanity oracle confirmed all 30 gold labels as internally consistent. A batched LLM judge (gpt-5.4-mini, low reasoning effort, single prompt) then classified every case correctly, achieving accuracy 1.000 and drift F1 1.000 on this corpus. While these results demonstrate harness viability at smoke-test scale, the corpus is small, synthetic, and author-labeled; the results do not establish benchmark generality, robustness under distribution shift, or reproducibility across model versions. We report the method, results, and limitations in full.

## Introduction

Detecting factual drift between a source document and its summary is important for applications in clinical reporting, legal compliance, and financial disclosure, where an inaccurate summary can materially alter the meaning of a record. A corpus for training or evaluating drift detectors requires validated labels: each summary must be marked as faithful or as drifting, ideally with the drift type identified. Manual annotation is expensive and slow, and inter-annotator agreement on subtle drift can be low. An alternative is to use a large language model (LLM) as a judge to validate corpus labels at scale.

This work asks a narrow question: can a batched LLM judge correctly classify a small, intentionally constructed summary-drift corpus, and does the approach merit further scaling? We do not claim that a positive answer on 30 synthetic cases proves general reliability. Rather, we treat this as a viability study and report its boundaries honestly.

The contribution is the harness design and the empirical demonstration that, under controlled conditions with unambiguous drift, a single batched LLM call can validate all cases correctly while producing human-readable explanations identifying the changed fact.

## Method

### Corpus Design

Six source documents were authored, one per domain: clinical, finance, legal, science, operations, and education. For each source document, five summaries were generated:

- **1 faithful summary**: accurately reflects the source.
- **4 drift variants**, one per drift class:
  - *Entity substitution*: a named entity is replaced with a different entity of the same type.
  - *Number drift*: a numeric quantity is altered.
  - *Polarity/negation drift*: a statement's polarity is inverted.
  - *Unsupported addition*: a plausible but unsupported claim is inserted.

This yields 30 total cases with a gold distribution of 6 no-drift and 24 drift. The drift variants were designed to be unambiguous: each contains exactly one controlled deviation from the source, making the gold label clear by construction.

### Validation Harness

The validation script (`scripts/summary_drift_validation.py`) is dependency-free Python. It supports two modes:

1. **Deterministic oracle** (`--llm none`): checks that the corpus file is internally consistent (correct number of cases, valid drift-type labels, no duplicate IDs). This serves as a structural sanity check, not a semantic judge. It verifies that the corpus file matches its own schema and that the gold labels are syntactically valid; it does not verify that the drift is semantically present.
2. **LLM judge** (`--llm codex`): batches all 30 cases into a single prompt and submits it to the Codex CLI backend with model `gpt-5.4-mini` at low reasoning effort. The prompt asks the model to classify each case as faithful or drifting and to identify the drift type and the changed fact. The entire corpus is presented in one prompt to avoid per-case startup overhead.

### Execution Environment

- Host: `gx10-efe8`, Linux aarch64, NVIDIA GB10 visible but not used for inference; LLM calls went to remote Codex.
- Swap: disabled (`SwapTotal: 0 kB`).
- Available memory at start: approximately 122,959,364 kB.
- LLM backend: Codex CLI, model `gpt-5.4-mini`, low reasoning, single batched call.
- Timeout: 360 seconds (not reached; the call completed in under 10 seconds).

### Commands

```bash
# Deterministic sanity check
python3 scripts/summary_drift_validation.py \
  --llm none --out results/smoke_deterministic_v2

# LLM-backed validation
/usr/bin/time -f 'elapsed_sec=%e maxrss_kb=%M' \
  python3 scripts/summary_drift_validation.py \
  --llm codex --model gpt-5.4-mini \
  --out results/llm_batch_full --timeout 360
```

## Results

### Deterministic Oracle

The deterministic sanity oracle passed all 30 cases: accuracy 1.000, drift F1 1.000. This confirms the corpus file is structurally valid and labels are internally consistent. It does not confirm semantic correctness of the gold labels; a structurally valid corpus could still contain mislabeled cases.

### LLM Judge

The batched LLM judge classified all 30 cases correctly:

| Metric | Value |
|---|---|
| Accuracy | 1.000 |
| Precision (drift) | 1.000 |
| Recall (drift) | 1.000 |
| Drift F1 | 1.000 |

Per-type accuracy:

| Drift type | Accuracy |
|---|---|
| Faithful (no drift) | 1.000 |
| Entity substitution | 1.000 |
| Number drift | 1.000 |
| Polarity/negation drift | 1.000 |
| Unsupported addition | 1.000 |

The LLM judge returned explanations identifying the specific changed fact in each drift case. For example, in number-drift cases, the explanation named the altered quantity and its original and substituted values.

### Resource Usage

| Metric | Value |
|---|---|
| LLM batch elapsed | 9.98 s |
| Throughput | 3.01 cases/s |
| Wrapper elapsed (incl. startup) | 10.05 s |
| Max RSS | 112,336 KB |

Batching all 30 cases into one prompt avoided per-case Codex CLI startup overhead. The entire validation, including Python startup and CLI invocation, completed in approximately 10 seconds.

## Limitations

These results must be interpreted within their narrow scope:

1. **Small synthetic corpus.** 30 cases from 6 author-written documents do not represent the distribution of real-world summaries. Perfect scores on this corpus are expected given its simplicity and are not evidence of general capability. The drift variants were designed to be unambiguous; real-world drift is often subtle, partial, or ambiguous. Performance on this corpus sets an upper bound on what a judge *can* do under favorable conditions, not a lower bound on what it *will* do on harder data.

2. **Author-generated labels.** Gold labels were produced by the same process that generated the drift variants. There is no independent human annotation, no inter-annotator agreement measure, and no blinded adjudication. The labels are correct by construction but have not been externally validated.

3. **Non-pinned LLM backend.** The Codex CLI with `gpt-5.4-mini` is not a pinned, versioned public model endpoint. Results are not guaranteed reproducible across time or backend changes. No immutable run metadata (e.g., model weights hash, temperature, top-p) was captured beyond what the CLI exposes. The model version and sampling parameters were not recorded.

4. **Single evaluation pass.** Only one LLM judge call was made. There is no measurement of classification stability across repeated calls, temperature settings, or prompt variations. A single perfect pass does not characterize the variance of the judge's output.

5. **No external target corpus.** The original project referenced a Notion page, but the page body was not accessible through the available connector surface. Validation was conducted entirely on the synthetic corpus. No real-world corpus was evaluated.

6. **Claim audit status.** The structured claim ledger for this artifact contains no extracted claims and carries audit status `blocked_empty_claims`. This paper must not be treated as having passed a strict claim/evidence audit until claims reference publicly verifiable evidence files.

7. **Drift classes are controlled and obvious.** Each drift variant contains exactly one deviation. Multi-drift cases, partial drift, and stylistic drift were not tested. The four drift classes do not exhaust the space of possible drift types.

## Reproducibility Checklist

- [x] Corpus generation script available: `scripts/summary_drift_validation.py`
- [x] Deterministic oracle results recorded: `results/smoke_deterministic_v2/metrics.json`
- [x] LLM judge results recorded: `results/llm_batch_full/metrics.json`
- [x] LLM predictions logged: `results/llm_batch_full/llm_predictions.jsonl`
- [x] Generated corpus logged: `results/llm_batch_full/corpus.jsonl`
- [x] LLM prompt captured: `results/llm_batch_full/logs/codex_batch_prompt.txt`
- [x] Execution logs retained: `logs/llm_batch_full.stdout.log`, `logs/llm_batch_full.stderr.log`
- [x] Codex smoke logs retained: `logs/codex_smoke.stdout.log`, `logs/codex_smoke.stderr.log`
- [x] Execution environment described (host, OS, memory, swap)
- [ ] Model version and weights hash pinned — **not available**; Codex CLI does not expose this
- [ ] Temperature and sampling parameters recorded — **not captured** beyond CLI defaults
- [ ] Independent human annotation — **not performed**
- [ ] Repeated-run stability measured — **not performed**
- [ ] Claim/evidence audit passed — **not performed**; claim ledger is empty

## Conclusion

A dependency-free Python harness generated a 30-case summary-drift corpus and a batched LLM judge classified all cases correctly with full per-type accuracy. The approach is viable at smoke-test scale: the harness works, the batched prompt strategy is efficient (3 cases/s), and the judge produces useful explanations identifying the changed fact in each drift case.

However, this study establishes viability only. The corpus is small, synthetic, and author-labeled; the LLM backend is not pinned; no stability or robustness analysis was performed; and the claim ledger carries no audit-approved claims. Any claim of benchmark-level performance or general reliability would be unsupported by the present evidence.

Scaling to hundreds of real summaries with blinded independent annotation, repeated judge passes to measure stability and disagreement, and a pinned model endpoint with recorded sampling parameters remains necessary before the method can be considered validated for general use. The results reported here are consistent with the project decision of `viable_with_limits`: the idea works under controlled conditions, but publishable closure requires substantially more evidence.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Validation script | `scripts/summary_drift_validation.py` |
| Deterministic metrics | `results/smoke_deterministic_v2/metrics.json` |
| LLM batch metrics | `results/llm_batch_full/metrics.json` |
| LLM predictions | `results/llm_batch_full/llm_predictions.jsonl` |
| Generated corpus | `results/llm_batch_full/corpus.jsonl` |
| Codex batch prompt | `results/llm_batch_full/logs/codex_batch_prompt.txt` |
| Codex batch stdout | `results/llm_batch_full/logs/codex_batch.stdout.log` |
| Codex batch stderr | `results/llm_batch_full/logs/codex_batch.stderr.log` |
| Codex smoke stdout | `logs/codex_smoke.stdout.log` |
| Codex smoke stderr | `logs/codex_smoke.stderr.log` |
| Top-level batch stdout | `logs/llm_batch_full.stdout.log` |
| Top-level batch stderr | `logs/llm_batch_full.stderr.log` |
| Deterministic run log | `logs/smoke_deterministic_v2.log` |
| Context snapshot | `.omx/context/summary-drift-corpus-validation-20260428T204024Z.md` |
| Autopilot spec | `.omx/plans/autopilot-spec.md` |
| Autopilot impl plan | `.omx/plans/autopilot-impl.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260428T203948490218+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260428T203948490218+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260428T203948490218+0000/paper_manifest.json` |
