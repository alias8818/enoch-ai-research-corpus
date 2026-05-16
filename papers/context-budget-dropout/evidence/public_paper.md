# Context Budget Dropout: Budget-Robust Context Allocation via Random Effective-Budget Reductions During Tuning

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, benchmark results, and decision records). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate whether a context allocator tuned with random effective-budget reductions—termed *context budget dropout*—remains more robust than a selector tuned only at the nominal full budget when the actual context budget is hard-cut. In a controlled synthetic multi-fact retrieval benchmark with 1,000 generated cases (300 train, 700 held-out test), context budget dropout did not outperform full-budget tuning under fixed chunk-count budgets: both policies achieved identical exact answerability (1.000 at 3 chunks; 0.667 fact recall at 2 chunks, where 3 required slots make exact answerability structurally impossible). However, under tight token-proxy budgets, context budget dropout produced materially higher answerability: +0.091 at 12 tokens (95% CI [+0.071, +0.113]) and +0.217 at 15 tokens (95% CI [+0.190, +0.251]), with the advantage vanishing at 20 tokens and narrowing to +0.009 at 25 tokens (95% CI [+0.003, +0.016]). The improvement arises because dropout training favors shorter, slot-complete evidence earlier in the ordering, reducing failures caused by long or redundant chunks consuming the budget. These results are confined to a synthetic benchmark with handcrafted feature proxies and whitespace token counts; no real LLM reader or production retrieval traces were used. The claim should not be extended beyond this controlled synthetic evidence until validated on real retrieval traces with an LLM- or human-judged reader.

## Introduction

Context allocation for retrieval-augmented systems involves selecting a subset of available evidence to fit within a serving budget, typically measured in tokens. In practice, the effective budget at serving time may differ from the budget assumed during tuning—due to dynamic load, model context window changes, or downstream truncation. A selector optimized only at the nominal full budget may produce orderings that are fragile when the budget is unexpectedly reduced.

The core idea of *context budget dropout* is straightforward: during tuning, the effective budget is randomly reduced below the nominal maximum, exposing the selector to budget-constrained regimes. The hypothesis is that this produces an allocation ordering that degrades gracefully—prioritizing evidence that is both informative and compact—rather than an ordering that is optimal at full budget but collapses under cuts.

This paper reports a controlled test of that hypothesis. We built a deterministic synthetic multi-fact QA/retrieval benchmark where each case contains three required evidence slots, high-lexical-overlap decoy entities, redundant same-slot evidence, and filler. We compared four policies: lexical-only ranking, full-budget-tuned selection, context-budget-dropout-tuned selection, and a hand-robust control. We evaluated under both chunk-count budgets and token-proxy budgets.

The results support a narrower version of the hypothesis than initially hoped. Context budget dropout did not improve over full-budget tuning when budgets are measured as fixed chunk counts—both policies found equally slot-complete orderings. The improvement appears only under token budgets, where the length of selected evidence matters. This distinction is important: chunk-budget robustness and token-budget robustness are different properties, and dropout addresses the latter.

## Method

### Benchmark Design

A synthetic multi-fact retrieval benchmark (`scripts/context_budget_dropout_bench.py`) generates deterministic cases with the following structure:

- **3 required evidence slots**: Each case requires facts from three distinct slots to be answerable.
- **High-lexical decoy entities**: Wrong-entity distractors with high lexical overlap to the query, creating real decoy pressure.
- **Redundant same-slot evidence**: Multiple passages supporting the same slot, differing in length and specificity.
- **Filler passages**: Topically relevant but non-essential text.

Policies observe only text-derived feature proxies (handcrafted, not learned embeddings or model attention scores). Evaluation checks hidden correct-slot coverage: a case is "answerable" if and only if all three required slots are covered by the selected evidence within the budget.

### Policies Compared

| Policy | Description |
|--------|-------------|
| `lexical_only` | Lexical score control; selects by lexical overlap only |
| `full_budget_tuned` | Random-search selector tuned only at the nominal 6-chunk budget |
| `context_budget_dropout` | Same selector family, tuned over effective budgets 2–6 |
| `hand_robust_control` | Manually constructed robust sanity control |

### Evaluation Budgets

Two budget regimes were evaluated:

1. **Chunk-count budgets**: Fixed number of chunks (2, 3, 4, 5, 6). Answerability depends only on whether the selected chunks cover all three required slots; chunk length is irrelevant.
2. **Token-proxy budgets**: Budget measured in whitespace-split token proxy counts (12, 15, 20, 25). Answerability depends on both slot coverage and whether the selected evidence fits within the token limit. Selection is greedy and can be non-monotonic with respect to budget size, as a larger budget may admit an early long chunk that changes the remaining packing path.

### Statistical Method

Paired bootstrap resampling was used to compute 95% confidence intervals for the difference in answerability between context budget dropout and full-budget-tuned policies across the 700 held-out test cases.

### Experimental Configuration

- **Cases generated**: 1,000
- **Train cases**: 300
- **Held-out test cases**: 700
- **Tuning trials**: 650 (random search)
- **Random seed**: 20260501
- **Full run wall time**: 43.28 s, CPU 99%
- **Full run max RSS**: approximately 23,260 KB (see `logs/full_time.log`; the project decision record reports 23,100 KB, a minor discrepancy likely reflecting different measurement points during execution)
- **System memory**: approximately 122 GB available, 0 kB swap; no swaps observed

## Results

### Chunk-Budget Answerability

At a chunk budget of 3 (the minimum for exact answerability given 3 required slots), all non-lexical policies achieved perfect answerability:

| Policy | 3-Chunk Answerability |
|--------|----------------------|
| `context_budget_dropout` | 1.000 |
| `full_budget_tuned` | 1.000 |
| `hand_robust_control` | 1.000 |
| `lexical_only` | 0.000 |

At 2 chunks, exact answerability is structurally impossible (3 required slots, 2 chunks). Both `context_budget_dropout` and `full_budget_tuned` recovered 0.667 fact recall (2 of 3 slots on average), indicating equivalent slot-priority orderings.

Bootstrap for 3-chunk exact answerability: dropout minus full-tuned delta = 0.000, 95% CI [0.000, 0.000]. There is no detectable advantage for dropout under chunk budgets.

The `lexical_only` policy scored 0.000 across all chunk budgets, confirming that the benchmark contains meaningful decoy pressure and that lexical overlap alone is insufficient for this task.

### Token-Budget Answerability

Under token-proxy budgets, context budget dropout showed clear advantages at tight budgets:

| Token Budget | Dropout | Full-Tuned | Delta | 95% CI | n |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 12 | 1.000 | 0.909 | +0.091 | [+0.071, +0.113] | 700 |
| 15 | 0.987 | 0.770 | +0.217 | [+0.190, +0.251] | 700 |
| 20 | 1.000 | 1.000 | 0.000 | [0.000, 0.000] | 700 |
| 25 | 1.000 | 0.991 | +0.009 | [+0.003, +0.016] | 700 |

The largest effect appears at the 15-token budget, where dropout achieves 98.7% answerability versus 77.0% for full-budget tuning—a +21.7 percentage point difference with a confidence interval entirely above zero. At 12 tokens, the effect is smaller but still significant (+9.1 pp). At 20 tokens, both policies saturate at 1.000. At 25 tokens, a small residual difference (+0.9 pp) persists, with a confidence interval that excludes zero.

The `lexical_only` policy scored 0.000 across all token budgets as well.

### Mechanism

The token-budget advantage arises because dropout training, by experiencing reduced budgets during tuning, learns to place shorter, slot-complete evidence earlier in the selection ordering. Full-budget tuning has no pressure to prefer compact evidence and may place long or redundant chunks before shorter slot-essential ones. Under a tight token budget, a single long chunk can consume most of the allocation, leaving insufficient room for remaining required slots.

This mechanism also explains why the chunk-budget result is null: when budget is measured in chunks rather than tokens, the length of individual chunks is irrelevant to whether the budget is satisfied, so preferring shorter evidence confers no advantage.

### Runtime and Resource Usage

The full benchmark run completed in 43.28 seconds of wall time at 99% CPU utilization, with a maximum RSS of approximately 23,260 KB. No swap activity was observed. The benchmark is computationally lightweight.

## Limitations

1. **Synthetic benchmark only.** No real retrieval traces, production data, or human-annotated corpora were used. The cases are procedurally generated with a controlled difficulty structure. Transfer to real-world retrieval distributions is unknown.

2. **No real LLM reader.** Answerability is defined as required-fact containment in the selected evidence. Whether an actual LLM would correctly extract and use those facts under reduced context was not tested.

3. **Whitespace token proxy.** Token counts are based on whitespace splitting, not a model-specific BPE tokenizer. Real token budgets may differ substantially from these proxy counts, and the relative lengths of evidence passages may change under a real tokenizer.

4. **Handcrafted feature proxies.** The policies operate on text-derived features constructed by hand, not learned embeddings or model attention scores. The extent to which results transfer to learned retrieval features is unknown.

5. **Greedy token-budget selection.** The token-budget selection algorithm is greedy and can exhibit non-monotonic behavior: a larger budget may admit an early long chunk that changes the remaining packing path, potentially reducing answerability. This is a property of the selection algorithm, not the tuning method, but it complicates interpretation of token-budget results.

6. **Single benchmark configuration.** Only one difficulty structure (3 required slots, decoys, redundancy) was tested. Performance may differ with more or fewer required slots, different decoy strategies, or different redundancy patterns.

7. **Chunk-budget null result.** Context budget dropout did not improve over full-budget tuning under chunk-count budgets. The method's benefit is specific to length-sensitive budget regimes. This is an honest negative result: the method does not universally improve robustness.

8. **No comparison to explicit length-aware baselines.** The dropout approach was compared against full-budget tuning and lexical control, but not against explicit length-aware selection methods such as Maximal Marginal Relevance or knapsack-based selectors. Whether dropout offers advantages over such methods remains open.

## Reproducibility Checklist

- [x] **Random seed**: 20260501 (fixed and reported).
- [x] **Code**: `scripts/context_budget_dropout_bench.py`; tests in `tests/test_context_budget_dropout_bench.py`.
- [x] **Command for full run**: `/usr/bin/time -v python3 scripts/context_budget_dropout_bench.py --cases 1000 --train-cases 300 --trials 650 --outdir results/full`
- [x] **Regression tests**: `python3 -m pytest -q` → `logs/pytest.log`.
- [x] **Output artifacts**: `results/full/aggregate_results.csv`, `results/full/token_budget_results.csv`, `results/full/summary.json`.
- [x] **Logs**: `logs/full.log`, `logs/full.time.log`, `logs/smoke.log`, `logs/smoke.time.log`, `logs/bootstrap_token_delta.log`, `logs/pytest.log`.
- [x] **Hardware**: System with approximately 122 GB available RAM, 0 kB swap; full run max RSS approximately 23,260 KB; wall time 43.28 s.
- [x] **Statistical method**: Paired bootstrap, 700 test cases, 95% CIs reported.
- [x] **All metrics**: Reported directly from saved CSV and JSON outputs; no manual aggregation.
- [x] **Negative results reported**: Chunk-budget null result and lexical-control failure reported in full.

## Conclusion

Context budget dropout—tuning a context allocator under random effective-budget reductions—does not outperform full-budget tuning when budgets are measured as fixed chunk counts. Both policies achieve identical slot-complete orderings in that regime. This is an honest negative result: the method does not universally improve allocation robustness.

The method does, however, produce materially higher answerability under tight token-proxy budgets, with the largest effect at intermediate budget tightness (+21.7 pp at 15 tokens, 95% CI [+19.0, +25.1]). The mechanism is that dropout training favors shorter, slot-complete evidence earlier in the ordering, reducing failures where long or redundant chunks consume the budget before all required slots are covered. The advantage vanishes when the budget is sufficiently generous (20 tokens) and narrows to a small residual at 25 tokens.

These results are confined to a controlled synthetic benchmark with handcrafted features and whitespace token proxies. The scientific claim should not be extended beyond this controlled setting until validated on real retrieval traces with actual tokenizer budgets and an LLM or human reader judging final answer correctness. Next-stage validation should include: (1) replay on production retrieval traces with actual tokenizer budgets, (2) comparison against explicit length-aware baselines such as MMR or knapsack selectors, and (3) end-to-end evaluation with a reader model.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Benchmark script | `scripts/context_budget_dropout_bench.py` |
| Test suite | `tests/test_context_budget_dropout_bench.py` |
| Pytest log | `logs/pytest.log` |
| Smoke run log | `logs/smoke.log` |
| Smoke time log | `logs/smoke.time.log` |
| Full run log | `logs/full.log` |
| Full time log | `logs/full.time.log` |
| Bootstrap token delta log | `logs/bootstrap_token_delta.log` |
| Chunk-budget results | `results/full/aggregate_results.csv` |
| Token-budget results | `results/full/token_budget_results.csv` |
| Summary JSON | `results/full/summary.json` |
| Project decision JSON | `.omx/project_decision.json` |
| Project metrics | `.omx/metrics.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260501T234318456645+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T234318456645+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T234318456645+0000/paper_manifest.json` |
