# Task-Routed Context Allocation: Extractive Relevance vs Marginal Utility

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run logs, decision records, benchmark outputs). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

When a language model's context window cannot accommodate every candidate chunk, the selection policy determines which evidence is available for generation. We investigate whether context allocation should be driven by extractive query relevance (lexical similarity) or by marginal utility for the task (coverage of distinct evidence slots required to answer). In a controlled synthetic benchmark of 1,000 multi-fact retrieval tasks with hard chunk budgets, we compare four policies: BM25 extractive relevance, a task-routed marginal-utility proxy, an oracle marginal-utility upper bound, and random selection. At budget 3 with 4 distractors per task, BM25 achieves an answerable rate of 0.000 (mean fact recall 0.155), while the task-routed proxy achieves 0.465 (mean fact recall 0.767). A paired bootstrap test yields a delta of 0.465 with 95% CI [0.434, 0.495] (n = 1,000). The oracle upper bound reaches 0.794. BM25's failure stems from spending budget on lexically overlapping distractors (mean 2.535 distractors selected at budget 3). These results support the claim that extractive relevance and marginal utility are not equivalent under context budgets, but generalization to real corpora and downstream generation quality remains unvalidated.

---

## 1 Introduction

Retrieval-augmented generation systems typically select context by ranking chunks against a query using lexical or embedding similarity. This approach implicitly assumes that the most relevant-seeming chunks are the most useful for answering. However, when the context budget is tight and answer facts are distributed across multiple chunks, a policy that maximizes lexical overlap may fill the budget with redundant or distracting content while missing required evidence.

The distinction between *extractive relevance* (how well a chunk matches the query text) and *marginal utility* (how much a new chunk improves the system's ability to complete the task) is consequential. A chunk that repeats query terms but contributes no new answer facts has high extractive relevance but zero marginal utility. Conversely, a chunk that contains a novel required fact but shares few query terms has low extractive relevance but high marginal utility.

This work operationalizes the question as follows: under a hard chunk budget, does the selected context contain all atomic facts required to answer the task? We construct a deterministic synthetic benchmark and compare four allocation policies. We report results honestly, including the substantial gap between the task-routed proxy and the oracle upper bound, and we do not claim these results extend beyond the controlled setting.

---

## 2 Method

### 2.1 Benchmark Design

We implemented `scripts/evaluate_context_allocation.py`, a dependency-free deterministic benchmark generator and evaluator. Each generated task comprises:

- **A route label** drawn from three categories: `owner_flag`, `escalation_region`, or `full_recovery`.
- **A natural-language query** describing the task.
- **Required atomic facts** distributed across separate signal chunks, each containing a distinct fact necessary to fully answer the task.
- **Distractor chunks** with high lexical overlap with the query but containing no answer facts.
- **Unrelated background chunks** with neither lexical overlap nor answer facts.

The benchmark is designed so that answering a task requires *all* required facts; partial recall is insufficient for full answerability. This design choice isolates the coverage problem: a policy that retrieves some but not all required facts receives no answerability credit, though partial credit is captured by the mean fact recall metric.

### 2.2 Policies

Four allocation policies are compared under identical chunk budgets:

1. **`extractive_bm25`**: Okapi BM25 ranking over query text and chunk text. Selects the top-$k$ chunks by score. This policy represents the standard extractive-relevance approach.

2. **`task_routed_mu_proxy`**: A label-free route/slot greedy allocator. This policy rewards selection of chunks that fill new route-relevant evidence slots, using BM25 only as a tie-breaker when multiple chunks fill the same slot. It does not access ground-truth fact labels. The heuristic encodes the intuition that marginal utility comes from covering distinct evidence dimensions rather than re-covering already-served dimensions.

3. **`oracle_marginal_utility`**: Greedy selection with access to required-fact labels. This represents an upper bound on what marginal-utility allocation can achieve and is not deployable without label access. It serves to quantify the gap between the proxy and the best achievable utility-driven selection.

4. **`random`**: Uniform random chunk selection, serving as a floor baseline.

### 2.3 Metrics

- **`answerable_rate`**: Fraction of tasks where the selected context contains *all* required facts. This is a strict binary metric per task.
- **`mean_fact_recall`**: Average fraction of required facts present in the selected context, allowing partial credit.
- **`mean_selected_distractors`**: Average number of distractor chunks included in the selected context, measuring wasted budget.

### 2.4 Experimental Configuration

**Full run.** 1,000 tasks, seed 17, 4 distractors per task, budgets {1, 2, 3, 4, 5}, all four policies.

**Sensitivity run.** 1,000 tasks per condition, seed 23, distractor counts {0, 1, 2, 4, 6}, budgets {3, 4, 5}, all four policies.

**Smoke test.** 24 tasks, seed 17, 4 distractors, budgets {1, 2, 3, 4, 5}, for pipeline validation prior to the full run.

### 2.5 Statistical Testing

We report paired bootstrap confidence intervals for the difference in answerable rate between `task_routed_mu_proxy` and `extractive_bm25` at budget 3, using 1,000 task-level paired observations. The pairing is natural: both policies face the same tasks and chunk pools, so the comparison is within-task.

---

## 3 Results

### 3.1 Full Run (1,000 tasks, 4 distractors/task)

Table 1 presents results for budgets 3 and 4. Budgets 1, 2, and 5 are omitted from the table for brevity; budget 5 results are discussed in the sensitivity analysis.

**Table 1.** Answerable rate, mean fact recall, and mean selected distractors by policy and budget (1,000 tasks, 4 distractors/task).

| Budget | Policy | Answerable Rate | Mean Fact Recall | Mean Selected Distractors |
|---:|---|---:|---:|---:|
| 3 | `random` | 0.009 | 0.248 | — |
| 3 | `extractive_bm25` | 0.000 | 0.155 | 2.535 |
| 3 | `task_routed_mu_proxy` | 0.465 | 0.767 | 0.535 |
| 3 | `oracle_marginal_utility` | 0.794 | 0.918 | 0.000 |
| 4 | `extractive_bm25` | 0.000 | 0.420 | 2.741 |
| 4 | `task_routed_mu_proxy` | 0.794 | 0.918 | 1.000 |

At budget 3, BM25 achieves an answerable rate of 0.000 despite non-trivial fact recall (0.155), indicating it retrieves some required facts but never all of them. The task-routed proxy achieves an answerable rate of 0.465, a substantial improvement. The paired bootstrap test for the difference in answerable rate (`task_routed_mu_proxy` minus `extractive_bm25`) yields:

- Delta: 0.465
- 95% CI: [0.434, 0.495]
- n = 1,000 paired observations

The confidence interval is entirely positive, indicating a statistically reliable improvement under this benchmark's conditions.

BM25's poor answerability is explained by its distractor selection: at budget 3, it selects an average of 2.535 distractor chunks out of 3 slots, leaving only approximately 0.465 slots for signal chunks on average. The task-routed proxy selects only 0.535 distractors on average at the same budget.

At budget 4, the task-routed proxy's answerable rate rises to 0.794, matching the oracle's budget-3 performance. BM25 remains at 0.000 answerable even at budget 4, though its mean fact recall improves to 0.420. This asymmetry underscores that additional budget alone does not fix a policy that systematically misallocates slots to distractors.

The random baseline at budget 3 (answerable rate 0.009, fact recall 0.248) confirms that the task-routed proxy's improvement is not attributable to chance. Notably, BM25's fact recall (0.155) falls below random selection, indicating that BM25's lexical bias is actively counterproductive in this setting: it preferentially selects distractors over signal chunks.

### 3.2 Sensitivity to Distractor Pressure

The sensitivity sweep varies distractor count from 0 to 6:

- **0 distractors.** BM25 eventually succeeds when the budget is large enough (budget 5, answerable rate 1.000). However, at budget 3, BM25 still achieves answerable rate 0.000 because lexical relevance does not enforce coverage of all needed slots—multiple signal chunks may share query terms, and BM25 does not prioritize diversity across slots.
- **1–2 distractors.** The task-routed proxy remains near the oracle upper bound, as route slots are relatively unambiguous and the proxy's heuristic aligns well with the task structure.
- **4–6 distractors.** BM25 increasingly spends budget on red herrings. At 4 distractors/task and budget 3, BM25 selects 2.575 distractors on average and is never fully answerable. The task-routed proxy degrades somewhat but continues to materially outperform BM25.

The sensitivity analysis reveals that the task-routed proxy's advantage is robust across distractor pressures but is most pronounced when distractor pressure is high—precisely the regime where extractive relevance is most misleading.

### 3.3 Resource Usage

The benchmark is CPU-light and memory-safe. All runs executed on a single CPU with no GPU, no network calls, and no external API dependencies:

- **Smoke test:** 24 tasks, 0.08 s wall time, 16,816 KB max RSS.
- **Full run:** 1,000 tasks × 5 budgets × 4 policies, 2.23 s wall time, 30,288 KB max RSS.
- **Sensitivity runs:** 1.11–1.65 s per run, 25,428–27,888 KB max RSS.

No swap activity was observed. Available system memory remained above 121 GB throughout all runs. These measurements confirm the benchmark is deterministic, lightweight, and reproducible on any standard workstation.

---

## 4 Limitations

1. **Synthetic benchmark.** The tasks are generated, not drawn from real retrieval corpora. The benchmark proves a mechanism and provides a regression harness; it does not establish field performance on noisy, ambiguous, or adversarial real-world data. The route categories (`owner_flag`, `escalation_region`, `full_recovery`) are handcrafted and may not correspond to natural task structure in production systems.

2. **Oracle upper bound.** The `oracle_marginal_utility` policy uses hidden required-fact labels and is not deployable. The gap between the task-routed proxy (0.465) and the oracle (0.794) at budget 3 indicates substantial room for improvement in utility estimation. The proxy captures roughly 59% of the oracle's answerable rate at this budget.

3. **Handcrafted heuristics.** The task-routed proxy uses handcrafted route/slot heuristics. A deployable system would require learned or schema-derived utility estimates, and the proxy's performance may not transfer to domains where route/slot structure is less clean or less identifiable.

4. **Containment-based evaluation.** Answerability is measured by required-fact containment in the selected context, not by an LLM generation judge. This choice ensures determinism and reproducibility but omits downstream generation failures (e.g., an LLM that fails to use available facts, or one that hallucinates answers from partial evidence). A complete evaluation would measure end-to-end answer correctness.

5. **Incomplete distractor data for the random baseline.** The random baseline's distractor selection counts are not reported in the available artifacts, though its answerable rate (0.009) and fact recall (0.248) confirm it serves as a floor.

6. **Limited randomization.** Results are reported for one primary configuration (seed 17, 4 distractors) and one sensitivity sweep (seed 23). Robustness across additional random seeds and task distributions is not established.

7. **No real-corpus or LLM-in-the-loop validation.** The decision record explicitly classifies this as a "positive controlled result" requiring "next-stage real-corpus/LLM evaluation." The finding should not be claimed as externally validated for production retrieval without further evidence.

---

## 5 Reproducibility Checklist

| Item | Status |
|---|---|
| Benchmark script | `scripts/evaluate_context_allocation.py` (dependency-free, deterministic, seeded) |
| Random seeds | Full run: seed 17; Sensitivity: seed 23; Smoke: seed 17 |
| Full run command | `python3 scripts/evaluate_context_allocation.py --tasks 1000 --seed 17 --distractors 4 --budgets 1 2 3 4 5 --outdir results/full` |
| Sensitivity command | Iterates distractors in {0,1,2,4,6} with seed 23; see `run_notes.md` for full command |
| Output artifacts | `results/full/summary.json`, `results/full/aggregate_results.csv`, `results/sensitivity_summary.csv` |
| Logs | `logs/smoke.log`, `logs/full.log`, `logs/sensitivity.log` |
| Hardware | CPU-only; max RSS 30,288 KB; wall time 2.23 s for full run; no GPU required |
| Determinism | Seeded; no GPU, no network, no external API calls; no non-deterministic libraries |
| Dependencies | None beyond Python standard library (per design) |
| Statistical test | Paired bootstrap, 1,000 observations, 95% CI reported |

---

## 6 Conclusion

In a controlled synthetic benchmark of 1,000 multi-fact retrieval tasks, task-routed marginal-utility allocation substantially outperforms extractive BM25 relevance under fixed context budgets. At budget 3 with 4 distractors per task, the task-routed proxy achieves an answerable rate of 0.465 versus BM25's 0.000 (paired bootstrap delta 0.465, 95% CI [0.434, 0.495]). The mechanism is clear: BM25 fills the budget with lexically overlapping distractors (mean 2.535 out of 3 slots), while the task-routed proxy diversifies across evidence slots.

These results demonstrate that extractive relevance and marginal utility are not equivalent under context budgets. However, the task-routed proxy remains well below the oracle upper bound (0.794 at budget 3), and all results are confined to a synthetic setting with handcrafted heuristics and containment-based evaluation. The finding is viable for next-stage investigation—including replay on real retrieval traces, replacement of handcrafted heuristics with learned utility estimators, and measurement of downstream LLM answer quality—but should not be claimed as externally validated for production retrieval without further evidence.

---

## Referenced Artifacts

| Artifact | Path / Key |
|---|---|
| Benchmark script | `scripts/evaluate_context_allocation.py` |
| Full run log | `logs/full.log` |
| Smoke test log | `logs/smoke.log` |
| Sensitivity run log | `logs/sensitivity.log` |
| Full run summary | `results/full/summary.json` |
| Full run aggregate results | `results/full/aggregate_results.csv` |
| Sensitivity summary | `results/sensitivity_summary.csv` |
| Project decision record | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260501T143348468384+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T143348468384+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T143348468384+0000/paper_manifest.json` |
| Project directory | `<control-plane-projects>/source-record-redacted` |
| Project ID | `source-record-redacted` |
| Run ID | `source-record-redacted-20260501T143348468384+0000` |
