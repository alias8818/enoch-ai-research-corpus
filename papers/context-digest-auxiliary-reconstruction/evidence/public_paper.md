# Context Digest Auxiliary Reconstruction: Exact Fact Recovery from Compact Evidence-Bearing Digests

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, benchmark results, claim ledger). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review is asserted or required by this notice.

---

## Abstract

We investigate whether a compact context digest can support later reconstruction of exact source-context facts, compared to ordinary truncation or lossy summarization at the same byte budget. Four digest schemes—head truncation, lossy summary, auxiliary tuple index, and hash-guarded tuple index—are evaluated on a deterministic synthetic benchmark requiring exact `(subject, attribute) → value` reconstruction. At a 2048-byte budget over 64-fact corpora (approximately 25.6% compression ratio), the auxiliary tuple index achieves 0.9023 exact/evidence recall versus 0.2523 for head truncation and 0.0 for lossy summary. At 8192 bytes over 1024 facts (approximately 6.4% compression), tuple index recall degrades to 0.2156, still exceeding head truncation (0.0660) and lossy summary (0.0). Hash guarding trades recall for auditability (0.7207 versus 0.9000 at 256 facts / 8192 bytes). No evaluated scheme produces incorrect answers because all schemes abstain when evidence is absent. These results support auxiliary reconstruction only as an evidence-preserving digest design; lossy summaries that omit exact values cannot reconstruct those values by definition. All results derive from a synthetic deterministic benchmark and have not been validated on real agent transcripts.

## Introduction

Long-context systems face recurring pressure to compress or truncate context before feeding it to downstream consumers. Two common strategies—retaining the first N bytes of raw context (head truncation) or producing a lossy natural-language summary—discard information irreversibly. A third possibility is to construct a compact digest that deliberately retains addressable, evidence-bearing atoms sufficient for later exact reconstruction of specific facts.

This work asks: does an auxiliary reconstruction digest retain enough addressable evidence to answer exact fact queries better than ordinary truncation or lossy summaries at the same byte budget? The question is constrained to deterministic, evidence-backed reconstruction rather than model-assisted guessing, and evaluation is conducted on synthetic corpora where ground truth is unambiguous.

The core tension is straightforward: if a digest omits exact values, exact reconstruction of those values is impossible without external information. If a digest retains exact values in a compact, addressable form, reconstruction becomes a lookup problem rather than an inference problem. The empirical question is whether the byte overhead of structuring facts as addressable atoms is repaid in recall relative to naive truncation.

## Method

### Synthetic Corpus Design

Synthetic corpora contain exact source facts of the form `(fact_id, subject, attribute, value, source sentence)`. Queries request exact `(subject, attribute) → value` reconstruction. This design eliminates ambiguity about what constitutes a correct answer and enables deterministic evaluation. It also makes the task easier than reconstruction from real transcripts, a limitation discussed below.

### Metrics

| Metric | Definition |
|---|---|
| `exact_recall` | Fraction of queries for which the exact value is reconstructed |
| `evidence_recall` | Fraction of queries for which the correct source fact ID is recovered |
| `hallucination_rate` | Fraction of answered queries that return a wrong value |
| `compression_ratio` | Digest bytes divided by raw context bytes |

In the reported results, exact recall and evidence recall are equal because the synthetic task ties value correctness to fact-ID correctness.

### Digest Schemes

Four schemes are compared, each receiving the same byte budget:

1. **Head truncation** (`head_truncation`): Retain the first N bytes of raw context. This is the simplest baseline and represents what many context-window-constrained systems do implicitly.

2. **Lossy summary** (`lossy_summary`): Retain a plausible summary of subjects and attributes but omit exact values. This represents the class of natural-language summarization approaches that compress by paraphrasing and eliding detail.

3. **Auxiliary tuple index** (`aux_tuple_index`): Compact `fid|subject|attr|value` tuples sorted for lookup. This is the primary proposed scheme: a structured digest that retains exact values in addressable form.

4. **Hash-guarded tuple index** (`aux_hash_guarded`): Tuple index plus a short source sentence hash per tuple for auditability. This variant tests the cost of adding integrity verification metadata.

### Experimental Configuration

The main benchmark sweeps the following parameters:

- **Seeds:** 0–19 (20 runs per condition)
- **Corpus sizes:** 64, 256, 1024 facts
- **Byte budgets:** 1024, 2048, 4096, 8192
- **Queries per run:** 128

The benchmark script is `scripts/bench_context_digest_reconstruction.py`. Compilation was verified via `python3 -m py_compile`. A smoke test preceded the main run. All results are deterministic given the same seed and parameters.

This is a CPU-only, Python-stdlib benchmark with no GPU, no LLM inference, and no external dependencies. It should be classified as a synthetic deterministic simulation rather than a production validation or model-assisted evaluation.

## Results

### Moderate Compression (64 and 256 Facts)

At compression ratios of approximately 25.6%, the auxiliary tuple index substantially outperforms both baselines:

| Corpus facts | Budget | Compression ratio | Scheme | Exact/evidence recall |
|---:|---:|---:|---|---:|
| 64 | 2048 B | ~25.6% | `aux_tuple_index` | 0.9023 |
| 64 | 2048 B | ~25.6% | `head_truncation` | 0.2523 |
| 64 | 2048 B | ~25.6% | `lossy_summary` | 0.0000 |
| 256 | 8192 B | ~25.6% | `aux_tuple_index` | 0.9000 |
| 256 | 8192 B | ~25.6% | `head_truncation` | 0.2496 |
| 256 | 8192 B | ~25.6% | `lossy_summary` | 0.0000 |

The tuple index achieves roughly 3.6× the recall of head truncation at comparable byte budgets for these corpus sizes. The absolute recall of approximately 0.90 indicates that most facts can be retained and recovered when the byte budget accommodates roughly one-quarter of the raw context.

### Low Compression (1024 Facts)

At 8192 bytes over 1024 facts (approximately 6.4% compression), all schemes degrade substantially, but relative ordering is preserved:

| Scheme | Exact/evidence recall |
|---|---:|
| `aux_tuple_index` | 0.2156 |
| `aux_hash_guarded` | 0.1762 |
| `head_truncation` | 0.0660 |
| `lossy_summary` | 0.0000 |

Reconstruction quality scales with the number of retained fact atoms per byte. The tuple index retains a recall advantage over head truncation (0.2156 vs. 0.0660), but both values are low in absolute terms. The hash-guarded variant falls below the unguarded tuple index because per-tuple hash overhead reduces the number of tuples that fit within the fixed budget.

### Hash Guarding: Recall–Auditability Trade-off

Hash guarding adds integrity verification at the cost of per-tuple overhead:

| Corpus facts | Budget | `aux_tuple_index` recall | `aux_hash_guarded` recall |
|---:|---:|---:|---:|
| 256 | 8192 B | 0.9000 | 0.7207 |

The hash-guarded variant lowers recall by consuming bytes for auditability metadata, but provides an integrity hook for verifying that reconstructed facts match their source sentences. Whether this trade-off is worthwhile depends on application-specific requirements for verifiability.

### Hallucination Rate

No evaluated scheme produced incorrect answers. All schemes abstain when evidence is absent from the digest, yielding a hallucination rate of 0.0 across all conditions. This abstention behavior is a deliberate design constraint of the benchmark rather than an emergent property: the reconstruction logic returns no answer when the digest does not contain a matching entry. Any deployment that replaces abstention with model-assisted guessing would need separate evaluation for hallucination risk.

## Limitations

1. **Synthetic facts are easier than real transcripts.** The benchmark uses structured `(subject, attribute, value)` tuples with no semantic paraphrase, coreference resolution, or multi-hop reasoning required. Real agent transcripts would present substantially harder reconstruction problems. The recall numbers reported here should not be interpreted as predictive of real-world performance.

2. **No model-assisted reconstruction tested.** The evaluation is purely deterministic lookup. It does not assess whether an LLM could reconstruct facts from partial, paraphrased, or implied digest content. This is a separate and important question that this benchmark does not address.

3. **Project intent partially inferred.** The originating Notion page was probed via unauthenticated fetch but returned only a generic shell without page-specific content (see `artifacts/logs/notion_probe.log`, `artifacts/logs/notion_page.html`). The research question was reconstructed from the project title. Project-specific intent that differs from the title-derived question would not be captured here.

4. **No external or private human evidence** was available to validate real-world applicability. The results are self-contained within the synthetic benchmark.

5. **Lossy summary failure is structural, not empirical.** The zero recall of `lossy_summary` follows directly from its design (omitting exact values). This is not a surprising empirical finding but a confirmation that exact reconstruction requires exact values to be retained in some form.

6. **Compression ratio is the primary lever.** The results show that recall degrades predictably as the ratio of budget to corpus size falls. The tuple index advantage is real but bounded: it cannot recover facts that do not fit in the budget.

7. **Only one digest structure tested.** The auxiliary tuple index is a simple, unambiguous encoding. Other structured digest designs (e.g., card-style digests, semantic selectors, hierarchical indices) were not evaluated and may offer different trade-offs.

## Reproducibility Checklist

- **Benchmark script:** `scripts/bench_context_digest_reconstruction.py`
- **Compilation check:** `python3 -m py_compile scripts/bench_context_digest_reconstruction.py` — passed
- **Smoke test command:** `python3 scripts/bench_context_digest_reconstruction.py --smoke --outdir artifacts/results/smoke`
- **Smoke test result:** passed (log at `artifacts/logs/smoke.log`; results at `artifacts/results/smoke/summary.json`, `artifacts/results/smoke/detail.csv`)
- **Main benchmark command:** `python3 scripts/bench_context_digest_reconstruction.py --outdir artifacts/results/main --seeds 0..19 --facts 64 256 1024 --budgets 1024 2048 4096 8192 --queries 128`
- **Determinism:** Synthetic corpora and queries are generated from specified seeds; results are deterministic given the same seed and parameters.
- **Dependencies:** Python 3 standard library only; no external packages, no GPU, no LLM inference required.
- **Peak memory (main run):** 20,560 KB RSS; swap disabled (SwapTotal: 0 kB).
- **Wall time (main run):** approximately 1.04 seconds.
- **Result artifacts:**
  - Smoke: `artifacts/results/smoke/summary.json`, `artifacts/results/smoke/detail.csv`
  - Main: `artifacts/results/main/summary.json`, `artifacts/results/main/detail.csv`
  - Condensed metrics: `artifacts/metrics/research_metrics.json`
  - Logs: `artifacts/logs/smoke.log`, `artifacts/logs/main_benchmark.log`
- **Classification:** Synthetic deterministic simulation; not production validation, not model-assisted evaluation, not CUDA calibration.

## Conclusion

Auxiliary context digests are viable for exact fact reconstruction when they store compact, addressable, evidence-bearing atoms. Under the synthetic exact-fact workload, the tuple digest produced roughly 3.6× the recall of head truncation at comparable byte budgets for 64- and 256-fact corpora, while retaining correct evidence IDs and producing no wrong answers. However, this advantage erodes as compression ratios increase: at approximately 6.4% compression over 1024 facts, tuple index recall falls to 0.2156. Lossy summaries that omit exact values cannot reconstruct those values by definition; any apparent recovery would be unsupported guessing rather than evidence-backed reconstruction.

The design implication is narrow but clear: auxiliary reconstruction should be pursued only as an evidence-preserving digest strategy, not as a lossy natural-language summary reconstruction claim. Two constraints are required: mandatory abstention when evidence is absent from the digest, and mandatory evidence pointers when reconstruction claims are made. Removing either constraint would reintroduce hallucination risk that this benchmark deliberately excludes.

The next useful experiment would replace the synthetic corpus with real agent transcripts and compare compact tuple/card digests, semantic selectors, and model-assisted reconstruction against held-out fact QA. Such an experiment would test whether the structural advantage observed here survives the ambiguity, paraphrase, and multi-hop reasoning demands of real contexts.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Benchmark script | `scripts/bench_context_digest_reconstruction.py` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T130318591241+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T130318591241+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T130318591241+0000/paper_manifest.json` |
| Smoke log | `artifacts/logs/smoke.log` |
| Main benchmark log | `artifacts/logs/main_benchmark.log` |
| Notion probe log | `artifacts/logs/notion_probe.log` |
| Notion page HTML | `artifacts/logs/notion_page.html` |
| Smoke summary | `artifacts/results/smoke/summary.json` |
| Smoke detail | `artifacts/results/smoke/detail.csv` |
| Main summary | `artifacts/results/main/summary.json` |
| Main detail | `artifacts/results/main/detail.csv` |
| Research metrics | `artifacts/metrics/research_metrics.json` |
