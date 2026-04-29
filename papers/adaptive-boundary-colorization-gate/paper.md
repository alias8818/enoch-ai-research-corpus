# Adaptive Boundary Colorization Gate: A Deterministic Routing Strategy for Prompt Boundary Colorization

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has approved this content.

---

## Abstract

We present a deterministic, model-free adaptive gate for prompt boundary colorization that routes between vanilla and colorized prompt packing based on inspectable signals of answer-contract sufficiency and late-evidence risk. In pilot experiments on technical-document structured extraction and SQuAD extractive QA, the gate preserves the strong gains of fixed boundary colorization under tight budgets and late-evidence conditions while eliminating a known regression at higher budgets where colorized packing destructively over-compresses. At budget 480 on technical-doc extraction, the gate routes entirely to vanilla, recovering field recall to 0.8333 (matching vanilla) versus 0.625 for fixed colorization. At budget 160 on SQuAD late-answer stress, the gate routes entirely to colorized, matching fixed colorization's +65.62 F1-point advantage over vanilla. At mid-budget open-domain retrieval (budget 220), the gate routes conservatively (46/50 vanilla), tying vanilla performance and avoiding fixed colorization's evidence-recall loss of 6 points, at the cost of forgoing a small +0.67 F1 gain. These results are limited to the tested datasets, budgets, and model (DistilBERT); confidence is medium and external replication is not yet established.

## 1. Introduction

Prompt boundary colorization is a prompt-packing strategy that marks evidence-span boundaries with structural tokens, enabling downstream models to locate answer-bearing passages more efficiently under token budgets. Prior work on the parent project ("Prompt Boundary Colorization") demonstrated that fixed colorization yields substantial gains when evidence is late-arriving or budgets are tight, but introduces regressions at higher budgets where the structural tokens consume space that vanilla packing would otherwise fill with additional raw context.

This creates a routing problem: for any given query, budget, and evidence corpus, should the system apply boundary colorization or fall back to vanilla packing? A fixed strategy is suboptimal because the crossover point depends on task-specific factors—whether the answer contract is already reachable in the raw prompt, whether evidence appears late in the chunk ordering, and whether the query targets structured fields or free-text spans.

We investigate a deterministic, model-free adaptive gate that makes this routing decision using inspectable signals derived from the prompt, query, and evidence corpus before packing. The gate is intentionally conservative: it routes to colorization only when the raw prompt appears unlikely to contain the answer contract, and defaults to vanilla otherwise. This design prioritizes avoiding destructive over-compression over capturing marginal token savings.

## 2. Method

### 2.1 Gate Design

The adaptive boundary colorization gate (`src/adaptive_boundary_gate.py`) is a deterministic, model-free function that selects between `vanilla_budget` and `colorized_budget` packing strategies. It does not require a learned model or external API call. The gate computes a set of inspectable signals and applies a fixed decision rule.

**Input signals:**

1. **Budget**: The total token budget available for the prompt.
2. **Top-chunk best query-matching sentence prefix ratio**: The fraction of the best-matching sentence in the top-ranked chunk that overlaps with query terms, indicating how directly the leading evidence addresses the query.
3. **Raw query-term hits**: The number of query terms found in the vanilla (uncolorized) prompt, measuring raw coverage.
4. **Structured-query detection**: Whether the query targets specific schema fields (e.g., field names in a technical document), which typically benefits from boundary markers.
5. **Numeric/endpoint cues**: Whether the query requests specific numeric values or endpoint-like answers, which are often late-arriving in chunk orderings.
6. **Field-cue group coverage**: The fraction of expected field-cue groups present in the vanilla prompt, indicating whether the answer contract is already reachable without structural markers.

**Decision rule:**

If the raw prompt appears to contain the answer contract—indicated by sufficient query-term hits, adequate field-cue coverage, and no strong late-evidence risk signals—the gate selects vanilla packing. Otherwise, it selects colorized packing. The rule is conservative: ambiguous cases default to vanilla to avoid the more costly failure mode of destructive colorized selection when vanilla is already adequate.

### 2.2 Implementation Notes

The current implementation builds both candidate prompts (vanilla and colorized) for diagnostic simplicity before selecting one, resulting in a gate construction latency of approximately 2.1–2.7 ms. This latency can be reduced by computing only the feature signals first and lazily constructing the chosen prompt, but this optimization is deferred.

### 2.3 Benchmark Integration

Both parent benchmark harnesses (technical-doc extraction and SQuAD QA) were patched to include an `adaptive_gate` method with row-level gate diagnostics. Regression tests were added for late-evidence routing and raw-contract fallback scenarios.

## 3. Results

### 3.1 Technical-Document Structured Extraction

The technical-doc benchmark evaluates structured field extraction from technical documents under varying token budgets. Each budget sweep processes an 80-row pack. Results are CPU-only prompt packing evaluations.

| Budget | Gate Routing | Field Recall (Adaptive) | Field Recall (Vanilla) | Field Recall (Fixed Colorized) | Mean Tokens (Adaptive) |
|--------|-------------|------------------------|----------------------|-------------------------------|----------------------|
| 160    | 100% colorized | 0.2708             | 0.0000               | 0.2708                        | 91.44                |
| 240    | 100% colorized | 0.4792             | 0.0000               | 0.4792                        | 126.00               |
| 320    | 100% colorized | 0.5417             | 0.0000               | 0.5417                        | 198.69               |
| 480    | 100% vanilla   | 0.8333             | 0.8333               | 0.6250                        | —                    |

At budgets 160–320, the gate correctly identifies that vanilla packing cannot reach the answer contract (field recall 0.0000) and routes entirely to colorization, matching fixed colorization's gains. At budget 480, the gate detects that the raw prompt already contains the answer contract and routes entirely to vanilla, eliminating the fixed-colorization regression (field recall drops from 0.8333 to 0.6250; evidence recall drops from 0.7917 to 0.5938 under fixed colorization).

### 3.2 SQuAD Extractive QA

SQuAD experiments use a cached local DistilBERT extractive QA model offline. Pilot throughput was 18.2–23.1 model calls/sec wall-clock; process RSS/PSS was approximately 1.0 GiB.

#### 3.2.1 Late-Answer Stress (Budget 160)

This regime tests questions where the answer span appears late in the evidence ordering, making it vulnerable to budget truncation.

| Strategy       | F1     | Citation | Kept-Evidence Recall | Prompt Tokens |
|----------------|--------|----------|---------------------|---------------|
| Vanilla        | —      | —        | —                   | 160           |
| Fixed Colorized| —      | —        | —                   | ~139.74       |
| Adaptive Gate  | Matched fixed colorized | Matched fixed colorized | Matched fixed colorized | ~12.55% fewer than vanilla |

The gate routed all 50 tasks to colorized. Relative to vanilla, the adaptive gate achieved +65.62 F1 points, +68 citation points, and +84 kept-evidence recall points, with 12.55% fewer prompt tokens. It matched fixed colorization exactly, as expected when the gate correctly identifies universal late-evidence risk.

#### 3.2.2 Open-Domain Retrieval (Budget 160)

| Strategy       | F1 Advantage vs Vanilla | Citation Advantage | Evidence-Recall Advantage | Mean Tokens |
|----------------|------------------------|--------------------|--------------------------|-------------|
| Fixed Colorized| —                      | —                  | —                        | 139.74      |
| Adaptive Gate  | +4.30                  | +6                 | +8                       | 153.28      |

The gate mixed 15 colorized and 35 vanilla selections. It beat vanilla on all three metrics and beat fixed colorized by +1.02 F1 points, but used more tokens (153.28 vs 139.74) because it preserved vanilla packing when the raw prompt appeared sufficient. This token overhead is a direct consequence of the conservative routing policy.

#### 3.2.3 Open-Domain Retrieval (Budget 220)

The gate routed 46 tasks to vanilla and 4 to colorized. It tied vanilla on F1, citation, and evidence recall, avoiding fixed colorization's evidence-recall loss of 6 points. However, it also gave up fixed colorization's small +0.67 F1 pilot gain. The parent project's 80-example run had previously shown colorized losing at budget 220, so this conservative routing is consistent with avoiding a known failure mode, but it should be viewed as a precision-over-token-savings trade-off rather than an unqualified improvement.

### 3.3 Gate Construction Overhead

Technical-doc benchmark sweeps (80 rows each) completed in approximately 0.10–0.12 seconds wall-clock. Gate construction latency per call was 2.1–2.7 ms, attributable to building both candidate prompts for diagnostic purposes. Lazy construction of only the selected prompt would reduce this overhead.

## 4. Limitations

1. **Conservative routing at mid-budget retrieval.** The gate's conservative default-to-vanilla policy may leave small F1 or token-saving gains on the table at mid-budget open-domain retrieval settings (as observed at budget 220, where a +0.67 F1 gain from fixed colorization was foregone). Whether this trade-off is optimal depends on the relative cost of false-positive colorized routing (destructive over-compression) versus false-negative vanilla routing (missed marginal gains).

2. **Limited dataset and model coverage.** Results are reported only for SQuAD dev-v1.1 (extractive QA) and a technical-document structured extraction benchmark, using DistilBERT as the downstream model. Generalization to other datasets, domains, models, or languages is not established.

3. **Pilot-scale sample sizes.** SQuAD experiments used 50-task pilot subsets. Statistical significance at these sample sizes is not guaranteed, and point estimates may not hold at larger scale.

4. **Gate latency.** The current implementation builds both candidate prompts before selecting, incurring 2.1–2.7 ms overhead per gate call. This is a prototype design choice, not an inherent cost of the method.

5. **No external replication.** All experiments were conducted within a single automated research pipeline on a single machine. No independent replication has been performed.

6. **Heuristic signal design.** The gate's input signals and decision threshold are hand-designed heuristics. They have not been optimized or validated beyond the tested regimes, and may not transfer to substantially different query or corpus distributions.

7. **Budget discretization.** Experiments cover budgets 160, 220, 240, 320, and 480. Behavior at intermediate or very large budgets is not characterized.

## 5. Reproducibility Checklist

- **Source code:** `src/adaptive_boundary_gate.py`, `src/boundary_colorization.py`, `src/evidence_span_carpentry.py`
- **Benchmark harnesses:** `benchmarks/real_squad_qa.py`, `benchmarks/boundary_colorization_benchmark.py`, `benchmarks/run_budget_sweep.py`, `benchmarks/technical_doc_extraction.py`
- **Test suite:** `tests/test_boundary_colorization.py` (5 tests passing)
- **Compilation check:** All source and benchmark modules pass `python -m py_compile`
- **Data:** `data/squad-dev-v1.1.json` (SQuAD dev set)
- **Model:** Cached local DistilBERT extractive QA model (offline, no server dependency)
- **Result files:** See Referenced Artifacts section for complete manifest
- **Environment:** Python virtual environment at `.venv`; process RSS/PSS ~1.0 GiB; MemAvailable ~120.9 GiB; SwapFree 0
- **Randomness:** Gate is deterministic; SQuAD model inference is deterministic given cached model
- **Hardware:** Single machine; technical-doc benchmarks are CPU-only; SQuAD benchmarks use CPU-based DistilBERT inference

## 6. Conclusion

We have presented a deterministic, model-free adaptive gate for prompt boundary colorization that routes between vanilla and colorized prompt packing based on inspectable signals of answer-contract sufficiency and late-evidence risk. In the tested settings, the gate preserves the strong gains of fixed colorization under tight budgets and late-evidence conditions (e.g., +65.62 F1 points over vanilla at SQuAD budget 160 stress) while eliminating the known regression at higher budgets where colorized packing destructively over-compresses (e.g., field recall 0.8333 vs 0.625 at technical-doc budget 480). The primary trade-off is conservative routing at mid-budget open-domain retrieval, where the gate may forgo small marginal gains to avoid the more costly failure mode. These results are limited to the tested datasets, budgets, and model; confidence is medium and external replication is not yet established. The project decision recommends finalizing this branch as a supported deterministic adaptive gate, with follow-up work on gate latency optimization and larger-scale held-out retrieval evaluation.

---

## Referenced Artifacts

### Source files
- `src/adaptive_boundary_gate.py`
- `src/boundary_colorization.py`
- `src/evidence_span_carpentry.py`

### Benchmark harnesses
- `benchmarks/real_squad_qa.py`
- `benchmarks/boundary_colorization_benchmark.py`
- `benchmarks/run_budget_sweep.py`
- `benchmarks/technical_doc_extraction.py`

### Test files
- `tests/test_boundary_colorization.py`

### Result files
- `results/adaptive_gate_selection_counts.json`
- `results/adaptive_squad_summary.json`
- `results/adaptive_technical_doc_summary.json`
- `results/adaptive_squad_retrieval_budget220.log`
- `results/adaptive_squad_retrieval_budget220/summary.json`
- `results/adaptive_squad_retrieval_budget220/benchmark_rows.csv`
- `results/adaptive_squad_retrieval_budget160.log`
- `results/adaptive_squad_retrieval_budget160/summary.json`
- `results/adaptive_squad_retrieval_budget160/benchmark_rows.csv`
- `results/adaptive_squad_stress_budget160.log`
- `results/adaptive_squad_stress_budget160/summary.json`
- `results/adaptive_squad_stress_budget160/benchmark_rows.csv`
- `results/adaptive_technical_doc_budget240/summary.json`
- `results/adaptive_technical_doc_budget240.log`
- `results/adaptive_technical_doc_budget240/benchmark_rows.csv`
- `results/adaptive_technical_doc_budget160.log`
- `results/adaptive_technical_doc_budget160/summary.json`
- `results/adaptive_technical_doc_budget160/benchmark_rows.csv`
- `results/adaptive_technical_doc_budget320.log`
- `results/adaptive_technical_doc_budget320/summary.json`

### Decision and metadata artifacts
- `.omx/project_decision.json`
- `.omx/metrics.json`
- `.omx/project.json`
- `run_notes.md`
- `prompts/initial.md`
- `prompts/resume.md`

### Paper artifacts
- `papers/source-record-redacted/evidence_bundle.json`
- `papers/source-record-redacted/claim_ledger.json`
- `papers/source-record-redacted/paper_manifest.json`
- `papers/source-record-redacted/README.md`
