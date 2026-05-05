# Context-Role Pruning: Role-Scoped Hard Gates for Multi-Agent Context Compression

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

Multi-agent language model systems assemble prompts from context contributed by multiple roles. When the aggregate context exceeds a token budget, naive truncation or purely lexical retrieval can drop task-critical facts or admit cross-role distractors that share vocabulary with the active query. This paper evaluates a deterministic role-scoped pruning approach that gates context selection by role metadata before applying relevance scoring. In a synthetic benchmark of 500 cases with 120 distractor blocks per case at a 20% token budget, the strict role-gating policy (`role_prune_strict`) achieved oracle recall of 1.000 while compressing retained context to approximately 2.2% of the full context and eliminating all other-role distractor blocks. BM25 lexical retrieval also achieved perfect oracle recall but admitted distractors at increasing rates as the budget grew (0.051 at 10%, 0.121 at 20%, 0.288 at 40%). Positional baselines failed to preserve oracle facts (recall 0.315 for `full_until_budget` at 20% budget). These results are preliminary: the benchmark measures deterministic context retention, not downstream LLM answer quality, and the approach depends on correct role metadata labeling.

## Introduction

In multi-agent orchestration systems, a given agent's prompt is assembled from a mixture of global instructions, shared project context, and role-specific context blocks. As the number of contributing agents grows, the total context volume can exceed practical token budgets. The pruning problem—deciding which context blocks to retain—is nontrivial because distractor blocks from other roles may share lexical overlap with the active agent's query, causing purely retrieval-based selection to admit irrelevant context.

The core hypothesis of this work is that role metadata provides a strong and underused signal for context pruning: when an agent operates under a specific role, context blocks labeled with that role (or with global/shared scope) are far more likely to contain task-critical facts than blocks from other roles, even when the other-role blocks exhibit lexical similarity to the query. A hard role gate—selecting only global, shared, and current-role context before any relevance scoring—should therefore achieve higher precision than free-form retrieval while maintaining recall of critical facts.

This paper presents a deterministic benchmark evaluation of five pruning policies across varying budget ratios and noise levels. The results support the viability of role-scoped hard gating as a context compression strategy, with clear caveats regarding metadata dependence and the absence of downstream LLM evaluation.

## Method

### Pruning Harness

A deterministic pruning harness was implemented in `src/context_role_pruning.py` with a reproducible benchmark driver in `experiments/run_context_role_pruning.py`. Token counts use a regex word-token proxy; absolute token values are approximate, but comparisons are internal and consistent across policies within the same tokenizer proxy.

### Synthetic Case Structure

Each synthetic case contains:

- **Global/shared instructions** seeded with local project markdown, always retained by role-aware policies.
- **Active-role oracle facts**: context blocks labeled with the current agent's role that contain facts the agent must retain to answer its query. These serve as the ground-truth retention target.
- **Same-role background context**: additional blocks under the current role that are not oracle-labeled.
- **Other-role distractor blocks**: context blocks labeled with different roles, constructed with lexical collisions against the active query to challenge purely retrieval-based selection.

### Pruning Policies

Five policies were compared:

1. **`full_until_budget`**: Retain blocks in original document order until the token budget is exhausted.
2. **`tail_until_budget`**: Retain blocks in reverse order until the budget is exhausted.
3. **`bm25`**: Rank all blocks by BM25 lexical relevance to the query and retain the top-scoring blocks within budget.
4. **`role_prune`**: Prioritize global/shared and current-role blocks; fill remaining budget with the highest-scoring cross-role blocks by BM25.
5. **`role_prune_strict`**: Hard gate—retain only global/shared and current-role blocks. No cross-role blocks are admitted regardless of lexical score.

### Metrics

- **Oracle recall**: Fraction of oracle-labeled facts retained after pruning.
- **Distractor retention**: Fraction of other-role distractor blocks retained after pruning.
- **Compression**: Ratio of retained tokens to full-context tokens (lower means more compression).
- **Selection latency**: Wall-clock time for the pruning decision per case.

### Experimental Configuration

Experiments were run at three budget ratios (10%, 20%, 40%) with 500 cases and 120 noise blocks per case. A calibration run at 50 cases and 80 noise blocks preceded the full runs. A smoke test at 5 cases and 20 noise blocks validated the harness. The smoke test used a fixed random seed of 17.

### Platform

All experiments ran on Linux 6.17.0-1014-nvidia (aarch64) with approximately 122 GB available memory. Swap was disabled. Memory consumption was negligible (delta of approximately 224 kB across the full 20% run).

## Results

### Main Comparison at 20% Budget

Table 1 summarizes results for 500 cases, 120 distractor blocks per case, at a 20% token budget.

| Policy | Oracle Recall | Distractor Retention | Compression | Mean Tokens |
|---|---|---|---|---|
| `role_prune_strict` | 1.000 | 0.000 | 0.022 | 656.7 |
| `bm25` | 1.000 | 0.121 | 0.199 | 5928.4 |
| `full_until_budget` | 0.315 | 0.201 | 0.199 | 5922.9 |

**Table 1.** Policy comparison at 500 cases, 120 distractor blocks, 20% budget. `role_prune` and `tail_until_budget` results from the full 500-case run are not separately reported in the available summary data; see the smoke test for qualitative behavior of these policies.

The strict role-gating policy achieved perfect oracle recall while using only 2.2% of the full context and admitting zero distractor blocks. BM25 also achieved perfect oracle recall but used the full 20% budget allocation and admitted approximately 12.1% of distractor blocks. The positional baseline used the full budget but failed to retain most oracle facts (recall 0.315).

### Budget Scaling

Table 2 shows distractor retention for BM25 across budget ratios.

| Budget Ratio | BM25 Distractor Retention | `role_prune_strict` Distractor Retention |
|---|---|---|
| 10% | 0.051 | 0.000 |
| 20% | 0.121 | 0.000 |
| 40% | 0.288 | 0.000 |

**Table 2.** Distractor retention by budget ratio (500 cases, 120 distractor blocks). `role_prune_strict` retained zero distractors at all budgets. BM25 distractor retention increased monotonically with budget, as the larger budget allowed more lexical matches to cross-role blocks.

`role_prune_strict` maintained oracle recall of 1.000 and compression of approximately 0.022 across all three budget ratios, because the global/shared and current-role content constituted only approximately 2.2% of the full context in these synthetic cases. The remaining budget was simply unused under the strict policy.

### Smoke Test Detail

The 5-case smoke test (20 noise blocks, 20% budget, seed 17) confirmed the pattern. Per-case results show that `role_prune_strict` consistently achieved oracle recall of 1.0 with distractor retention of 0.0 across all five cases (active roles: designer, security, verifier, security, executor). BM25 and `role_prune` matched oracle recall but admitted 0.05 distractor retention per case. Positional baselines exhibited oracle recall between 0.0 and 0.667 depending on case.

A notable observation from the smoke test: `role_prune` and `bm25` produced identical results (same blocks, tokens, and metrics per case). This suggests that at the 20% budget level with 20 noise blocks, the role-priority phase of `role_prune` did not alter the selection relative to pure BM25—likely because the budget was large enough to include all role-matched blocks plus some cross-role blocks, making the role-priority ordering irrelevant to the final selection. Whether this equivalence holds at the 500-case scale with 120 noise blocks is not separately reported for `role_prune` in the available summary data.

The `tail_until_budget` policy performed comparably or worse than `full_until_budget` in the smoke test, with mean oracle recall of 0.267 versus 0.400 for `full_until_budget`.

### Selection Latency

At the full 20% run (500 cases, 120 distractor blocks), selection latency was:

- Mean: 7.83 ms
- P95: 13.51 ms
- Max: 14.83 ms

The smoke test (5 cases, 20 distractor blocks) showed lower latencies (mean 1.45 ms, p95 2.64 ms, max 2.74 ms), consistent with the smaller problem size.

## Limitations

1. **Deterministic retention, not downstream quality.** This benchmark measures whether oracle-labeled facts are retained in the pruned context, not whether an LLM produces better answers when given the pruned context versus the full context. A downstream A/B test with an actual language model is needed to confirm that the retained context is sufficient for task completion and that distractor removal improves (or at least does not harm) answer quality.

2. **Synthetic oracle/distractor labels.** The oracle and distractor labels are constructed by the benchmark generator. In real multi-agent systems, the boundary between "critical fact" and "background context" is less clear, and role metadata may be noisy or misapplied.

3. **Metadata dependence.** The strict policy's correctness depends entirely on accurate role labeling. If a task-critical fact is mislabeled under another role, `role_prune_strict` will drop it unless it is promoted to global/shared scope or passed through an explicit dependency edge. This is a real operational risk in systems where role annotations are not rigorously maintained.

4. **No cross-role exception mechanism evaluated.** The strict policy admits no cross-role context. Real systems may require selective cross-role access (e.g., a security reviewer needing a specific design constraint). The benchmark did not test explicit dependency-edge exceptions, though the run notes identify this as a necessary extension.

5. **Approximate tokenization.** Token counts are regex word-token proxies, not model-specific tokenizer outputs. Compression ratios and absolute token counts should be interpreted as approximate; relative comparisons across policies remain valid within the same proxy.

6. **Single benchmark design.** All cases follow the same structural template (global + oracle + same-role background + other-role distractors with lexical collisions). Generalization to other context structures, domains, or noise distributions is not established.

7. **Incomplete policy reporting at scale.** Full 500-case results for `role_prune` and `tail_until_budget` are not separately reported in the available summary data. The smoke test suggests `role_prune` behaves identically to `bm25` at the tested budget/noise configuration, and `tail_until_budget` performs comparably or worse than `full_until_budget`, but these observations at 5 cases do not establish behavior at 500 cases.

8. **Claim ledger status.** The formal claim ledger for this artifact is in `blocked_empty_claims` status, meaning no structured claims have been extracted and audited against evidence files. The results reported here are drawn directly from run notes and result files but have not passed a formal claim/evidence audit.

## Reproducibility Checklist

- [x] **Source code available**: `src/context_role_pruning.py`, `experiments/run_context_role_pruning.py`
- [x] **Unit tests**: `tests/test_context_role_pruning.py`; executed via `python3 -m unittest discover -s tests -v` (log: `logs/tests.log`)
- [x] **Compilation verified**: `python3 -m py_compile` on both source files succeeded
- [x] **Random seed documented**: Seed 17 for smoke test; seeds for calibration and full runs recorded in respective output files
- [x] **Raw result files preserved**: `results/smoke.json`, `results/calibration.json`, `results/full_10pct.json`, `results/full_20pct.json`, `results/full_40pct.json`
- [x] **Summary table preserved**: `results/metrics_summary.md`
- [x] **Execution logs preserved**: `logs/smoke.log`, `logs/full_runs.log`, `logs/tests.log`
- [x] **Platform recorded**: Linux 6.17.0-1014-nvidia aarch64, approximately 122 GB RAM, swap disabled
- [x] **Memory delta recorded**: 122,657,108 kB to 122,657,332 kB across full 20% run
- [x] **Latency statistics recorded**: Mean, p95, max for both smoke and full runs
- [x] **All five policies evaluated on identical cases**: Confirmed in smoke test result file; full-run result files contain per-policy data
- [ ] **Downstream LLM A/B test**: Not conducted; identified as remaining risk
- [ ] **Real-world role metadata validation**: Not conducted
- [ ] **Formal claim/evidence audit passed**: Claim ledger is in `blocked_empty_claims` status

## Conclusion

Role-scoped hard gating (`role_prune_strict`) preserved all oracle facts in a deterministic synthetic benchmark of 500 multi-agent context cases while compressing retained context to approximately 2.2% of the full volume and eliminating all cross-role distractor blocks. Positional truncation baselines failed to preserve oracle facts (recall 0.315 at 20% budget). BM25 lexical retrieval preserved oracle facts but admitted increasing proportions of distractors as the budget grew (5.1% at 10%, 12.1% at 20%, 28.8% at 40%), demonstrating that lexical overlap is an unreliable signal in multi-role contexts where distractors are designed to share vocabulary with the query.

These results support the viability of role-scoped hard gating as a context compression strategy for multi-agent systems, with the important caveat that the approach requires reliable role metadata and an explicit mechanism for cross-role dependency exceptions. The result is classified as a positive preliminary finding: the context-selection behavior is clearly demonstrated, but downstream LLM answer quality remains unevaluated. A production deployment should implement the hard role gate as a first-pass filter, with a controlled exception channel for explicitly declared cross-role dependencies, and should validate end-to-end task performance against an unpruned baseline.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Implementation | `src/context_role_pruning.py` |
| Benchmark driver | `experiments/run_context_role_pruning.py` |
| Unit tests | `tests/test_context_role_pruning.py` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260429T225148388943+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T225148388943+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T225148388943+0000/paper_manifest.json` |
| Smoke results | `results/smoke.json` |
| Calibration results | `results/calibration.json` |
| Full results (10% budget) | `results/full_10pct.json` |
| Full results (20% budget) | `results/full_20pct.json` |
| Full results (40% budget) | `results/full_40pct.json` |
| Metrics summary | `results/metrics_summary.md` |
| Smoke log | `logs/smoke.log` |
| Full runs log | `logs/full_runs.log` |
| Tests log | `logs/tests.log` |
