# Coder-Only Dense Shrinker: Deterministic Code-Aware Context Compaction for Coding Agents

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, benchmark metrics, system logs, and ablation results). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

We describe a deterministic, model-free context shrinker that reduces large code contexts to compact representations while retaining task-relevant facts for coding agents. The algorithm ranks file, definition, and paragraph chunks by a composite of query-token overlap and code-salience signals—`def`/`class` declarations, assertions, error/bug markers, and identifier matches—then emits selected chunks in source order under a character budget. It requires no language model calls, no embedding index, and no external dependencies. On a 1000-task synthetic coding-regression benchmark where the relevant target file is positioned amid noisy code-like files, the dense shrinker retains all gold facts at all tested budgets (800–3200 characters, approximately 6–24% of original context), while both first-N and head/tail truncation retain zero facts at the tightest budget. Wall-clock time for the full evaluation (1000 tasks × 4 budgets × 3 shrinker variants) is 2.39 seconds, with p95 per-task latency of 0.545 ms and peak RSS of 60,980 KB. An adversarial ablation across four query styles (full, symbol-only, generic, misleading-symbol) shows that the shrinker's success on this benchmark is driven by code-salience markers in the target chunks rather than by query relevance, confirming that the benchmark is structurally favorable to the approach. This constitutes a positive prototype result, not a production validation. Scientific closure requires evaluation on non-synthetic repositories with downstream agent repair accuracy as the success metric.

## Introduction

Coding agents operating on large repositories must contend with context window limits. The simplest strategy—truncating the context to the first N characters or splitting between head and tail—risks discarding the very code most relevant to the task. More sophisticated alternatives exist: embedding-based retrieval, repository-map summarization, and LLM-mediated context selection. These introduce model dependencies, latency, infrastructure complexity, and nondeterminism.

We investigate whether a purely deterministic, code-aware ranking scheme can serve as a lightweight shrinker: one that requires no model calls, no vector index, and no network service, yet retains the facts a coding agent needs to complete a regression-fix task. The working hypothesis is that code contexts carry structural and lexical signals—function definitions, class declarations, assertion patterns, error markers, bug annotations—that correlate with task relevance when combined with query-token overlap.

This paper reports on a prototype implementation evaluated on a synthetic benchmark. We report the results as they stand, including the structural advantage the benchmark confers on code-salience ranking, and we identify the specific gaps that must be closed before the approach can be considered validated for production use. We do not claim that the approach solves semantic or deeply indirect evidence discovery.

## Method

### Algorithm

The dense shrinker operates in three phases:

1. **Chunking.** The input context is split into chunks at file boundaries, then at definition boundaries (`def`, `class`), and finally at paragraph boundaries. Each chunk preserves its source position for later reassembly.

2. **Scoring.** Each chunk receives a composite score from two additive signals:
   - **Query-token overlap:** The fraction of query tokens (lowercased, split on whitespace and punctuation) that appear in the chunk text.
   - **Code salience:** A count-valued signal that increments for the presence of `def` or `class` declarations, assertion statements (`assert`), error/bug markers such as bug labels, error labels, regression labels, and exact identifier matches extracted from the query.

   The final score is the sum of query-token overlap and code-salience weight.

3. **Selection and emission.** Chunks are selected in descending score order until the cumulative character count reaches the budget. Selected chunks are then emitted in original source order to preserve code readability and structural coherence.

The algorithm is fully deterministic: given identical input context, query, and budget, it always produces the same output. It invokes no language model, no embedding model, and no network service.

### Baselines

Two deterministic truncation baselines were implemented for comparison:

- **first_n:** Retain the first N characters of the concatenated context.
- **head_tail:** Retain the first N/2 and last N/2 characters of the concatenated context.

Both baselines are deterministic and require no model calls.

### Benchmark Design

The synthetic coding-regression benchmark generates tasks as follows:

- Each task constructs a context containing multiple code-like files.
- The relevant target file (containing the regression/bug) is placed in the **middle** of the context, ensuring that both `first_n` and `head_tail` truncation exclude it at tight budgets.
- A query string describes the regression in natural language and/or code symbols.
- Gold facts are the chunks from the target file that contain the bug/regression information.

This design is intentionally favorable to code-salience ranking: the target chunks contain `BUG`, `regression`, `assert`, and related markers that receive high code-salience scores regardless of query style. This favorability is a feature of the benchmark, not a hidden confound—it is explicitly reported and tested via the ablation probe.

### Ablation Probe

An adversarial probe re-evaluated 200 tasks at 800 and 1200 characters with four query styles:

- **full_query:** The original task description.
- **symbol_only:** Only code symbols extracted from the query.
- **generic:** A vague query with no task-specific tokens.
- **misleading_symbol:** A query containing symbols from non-target files.

This probe tests whether the shrinker's success depends on query quality or is primarily driven by code-salience signals in the target chunks.

### Hardware and Environment

All runs executed on a Linux `aarch64` system (kernel reported as `Linux gx10-efe8`) with 20 CPUs, approximately 127 GB RAM, and no swap configured (`SwapTotal: 0 kB`). Python 3 was used with no external packages beyond the standard library. System details were captured in `logs/system_smoke.log`.

### Commands Executed

The following commands produced the reported results:

```bash
python3 scripts/dense_shrinker.py --tasks 20 --budgets 800 1200 2000 \
  --out results/dense_shrinker_metrics.json

python3 scripts/dense_shrinker.py --tasks 1000 --budgets 800 1200 2000 3200 \
  --out results/dense_shrinker_metrics_1000.json

python3 scripts/adversarial_probe.py

python3 -m py_compile scripts/dense_shrinker.py scripts/adversarial_probe.py
```

The 1000-task calibration run was timed with `/usr/bin/time -v`.

## Results

### Main Benchmark (1000 Tasks)

The shrinker was evaluated at four character budgets: 800, 1200, 2000, and 3200. The original context size per task was approximately 13,300 characters, making the 800-character budget approximately 6% of the original context.

| Budget (chars) | Compression Ratio | `first_n` Mean Recall | `head_tail` Mean Recall | `dense_query_rank` Mean Recall | `dense_query_rank` Perfect Tasks |
|---|---|---|---|---|---|
| 800 | 0.06 | 0.0000 | 0.0000 | 1.0000 | 1000/1000 |
| 1200 | 0.09 | — | — | 1.0000 | 1000/1000 |
| 2000 | 0.15 | — | — | 1.0000 | 1000/1000 |
| 3200 | 0.24 | — | — | 1.0000 | 1000/1000 |

At the 800-character budget, both truncation baselines achieve zero mean fact recall and zero perfect tasks. The dense shrinker achieves perfect recall on all 1000 tasks at all tested budgets. Baseline metrics at budgets above 800 characters were recorded in the metrics files but are not the primary comparison point; the critical contrast is at the tightest budget where truncation fails completely and the dense shrinker succeeds completely.

The perfect recall across all budgets indicates that the gold-fact chunks are consistently the highest-scoring chunks under the algorithm's scoring function, and that they fit within even the smallest budget tested.

### Latency and Resource Usage

| Metric | Value |
|---|---|
| Wall time (1000 tasks × 4 budgets × 3 shrinkers) | 2.39 s |
| CPU utilization | 99% |
| Max RSS | 60,980 KB |
| p95 per-task latency (`dense_query_rank`) | 0.545 ms |
| Memory available before run | ~122.65 GB |
| Memory available after run | ~122.62 GB |
| Swap total | 0 KB (none configured) |

The shrinker is lightweight in both time and memory. The memory delta over the full run (~38 MB decrease in available memory, consistent with OS buffer behavior rather than application allocation) and sub-millisecond p95 per-task latency are consistent with a deterministic algorithm that avoids allocation hotspots and model inference overhead.

### Ablation Results

The adversarial probe evaluated 200 tasks at 800 and 1200 characters across four query styles:

| Query Style | Budget 800 Mean Recall | Budget 1200 Mean Recall |
|---|---|---|
| full_query | 1.0000 | 1.0000 |
| symbol_only | 1.0000 | 1.0000 |
| generic | 1.0000 | 1.0000 |
| misleading_symbol | 1.0000 | 1.0000 |

The dense shrinker retains all gold facts across all query styles, including generic and misleading queries. This result confirms that the shrinker's success on this benchmark is driven by code-salience signals in the target chunks (BUG, regression, assertion markers) rather than by query relevance. This finding has a dual interpretation:

- **Strength:** The shrinker is robust to poor, vague, or misleading queries on this benchmark.
- **Limitation:** The benchmark does not test scenarios where the target lacks distinctive code-salience markers, meaning the approach's behavior on harder, more realistic tasks remains unknown.

### Claim Audit Status

The claim ledger for this artifact records an audit status of `blocked_empty_claims`: no structured claims were extracted for formal claim/evidence auditing. The empirical results reported here are drawn directly from the run notes, metrics files, and decision JSON, but they have not passed a formal claim/evidence audit pipeline. Readers should weight the results accordingly.

## Limitations

1. **Synthetic benchmark with structural favorability.** The benchmark places bug/regression markers (`BUG`, `regression`, `assert`) in target chunks, which receive high code-salience scores regardless of query content. Real repositories may contain subtle bugs without such markers, or may distribute relevant evidence across multiple files without distinctive lexical signals. The perfect recall results should not be extrapolated to such settings without empirical validation.

2. **No downstream agent evaluation.** Fact retention is an oracle metric: it measures whether the gold chunks appear in the shrunk context, not whether a coding agent can successfully repair the bug using only the shrunk context. A shrinker that retains all facts but presents them in a confusing order, or omits necessary scaffolding (imports, type definitions, configuration), may not improve agent success rates. This is the most significant gap in the current evaluation.

3. **Lexical matching only.** The algorithm relies on token overlap and code-salience keywords. It cannot discover semantically relevant code that uses different terminology, nor can it follow call-graph or data-flow dependencies. Tasks requiring indirect reasoning (e.g., "find where the configuration value that causes this timeout is set") are outside the algorithm's capability.

4. **Interpretation uncertainty.** The original project specification (Notion page) was not accessible from local artifacts. The tested interpretation—"coder-only" means no LLM, no external dependencies, deterministic code-aware compaction—may not capture the project's private intent. Results apply only to the interpretation tested.

5. **Single hardware configuration.** All results come from one machine (aarch64, 20 CPUs, 127 GB RAM, no swap). Performance on resource-constrained environments is not characterized, though the low RSS (61 MB) and sub-millisecond latency suggest reasonable portability.

6. **No comparison to retrieval baselines.** The study compares against truncation only. Embedding-based retrieval, repository-map summarization, and LLM-based context selection were not evaluated and may outperform the dense shrinker on harder benchmarks—particularly those requiring semantic rather than lexical matching.

7. **No real-repository validation.** The benchmark is entirely synthetic. No validation on open-source repositories with real bug reports and test suites has been conducted.

## Reproducibility Checklist

- [x] **Algorithm fully specified.** The scoring function and selection procedure are described in the Method section and implemented in `scripts/dense_shrinker.py`.
- [x] **Deterministic.** Given identical inputs, the algorithm produces identical outputs. No random seeds are involved.
- [x] **No external dependencies.** The implementation uses only the Python standard library.
- [x] **Benchmark generation specified.** The synthetic benchmark is generated by `scripts/dense_shrinker.py` with the `--tasks` and `--budgets` flags.
- [x] **Hardware documented.** System details recorded in `logs/system_smoke.log`: Linux aarch64, 20 CPUs, ~127 GB RAM, no swap.
- [x] **Commands recorded.** All invocation commands are listed in the run notes and reproduced in the Method section.
- [x] **Metrics files available.** `results/dense_shrinker_metrics.json`, `results/dense_shrinker_metrics_1000.json`, `results/adversarial_probe.json`.
- [x] **Logs available.** `logs/dense_shrinker_run.log`, `logs/dense_shrinker_1000.log`, `logs/system_smoke.log`, `logs/adversarial_probe.log`.
- [ ] **Independent reproduction not confirmed.** Results have been produced by one automated pipeline on one machine. No third-party reproduction has been attempted.
- [ ] **Real-repository evaluation not performed.** The benchmark is synthetic; no validation on open-source repositories has been conducted.
- [ ] **Formal claim audit not passed.** The claim ledger records `blocked_empty_claims`; no structured claims have been extracted or audited against evidence files.

## Conclusion

A deterministic, coder-only context shrinker that combines query-token overlap with code-salience ranking achieves perfect fact retention on a 1000-task synthetic coding-regression benchmark at budgets as low as 6% of the original context, where both first-N and head/tail truncation retain zero facts. The algorithm requires no model calls, no external dependencies, and incurs sub-millisecond p95 latency per task with 61 MB peak RSS.

However, the ablation results reveal that this success is substantially driven by code-salience markers (BUG, regression, assertion) present in the synthetic target chunks, not by query relevance. The benchmark is structurally favorable to the approach. The result is a positive prototype finding: it establishes that a zero-dependency deterministic shrinker is viable when task-relevant code carries distinctive lexical or structural markers. It does not establish that the approach works when relevant evidence lacks such markers, when evidence is distributed across files, or when the success metric is downstream agent repair accuracy rather than oracle fact retention.

The necessary next steps are: (1) evaluation on real repositories with hidden target files and pytest-based repair tasks, (2) comparison against embedding retrieval and repository-map baselines, and (3) measurement of downstream coder pass rate from shrunk contexts. Until these steps are completed, the result should be treated as a prototype validation on a favorable synthetic benchmark, not as evidence of production readiness.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Shrinker implementation | `scripts/dense_shrinker.py` |
| Ablation probe script | `scripts/adversarial_probe.py` |
| Smoke metrics (20 tasks) | `results/dense_shrinker_metrics.json` |
| Calibration metrics (1000 tasks) | `results/dense_shrinker_metrics_1000.json` |
| Ablation metrics | `results/adversarial_probe.json` |
| Smoke run log | `logs/dense_shrinker_run.log` |
| Calibration run log | `logs/dense_shrinker_1000.log` |
| System information log | `logs/system_smoke.log` |
| Ablation run log | `logs/adversarial_probe.log` |
| Project decision record | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260430T035148351261+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T035148351261+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T035148351261+0000/paper_manifest.json` |
