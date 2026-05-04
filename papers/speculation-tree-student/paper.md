# Spine-Preserving Speculation Trees from Lightweight Student Models

**AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, experimental logs, and telemetry). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

Speculative decoding accelerates autoregressive generation by verifying draft tokens against a teacher model in a single forward pass. Tree-structured drafts can improve acceptance rates over linear chains by hedging against student errors, but naive breadth-first allocation can sacrifice the depth that yields the highest-value accepted tokens. We investigate whether a lightweight student model can construct effective speculative token trees under a fixed node budget. In a controlled experiment using a synthetic order-2 Markov teacher (32-token vocabulary) and an n-gram student, we compare five draft-construction policies across low-, mixed-, and high-entropy next-token distributions. A *spine-preserving* tree policy—which maintains a deep top-1 draft chain and allocates remaining budget to high-probability side branches—yields a macro-average improvement of 7.40% in accepted greedy tokens per verification call over a top-1 chain baseline and reduces zero-accept rounds by 11.71 percentage points. A pure best-first tree, by contrast, underperforms the chain on mean accepted tokens despite achieving lower zero-accept rates, indicating that unconstrained breadth sacrifices valuable depth. These results are obtained under a synthetic Markov teacher with an acceptance-count proxy rather than wall-clock latency; real-model validation is required before drawing deployment conclusions.

## Introduction

Speculative decoding reduces the latency of autoregressive inference by having a cheap draft model propose candidate tokens that a teacher model verifies in a single forward pass. When the draft is correct, multiple tokens are emitted at once; when it is wrong, the teacher corrects at the first divergence point. The expected speedup depends on the number of tokens accepted per verification call and the relative cost of drafting versus verification.

Linear (chain) drafts extend a single top-1 sequence from the student. Tree-structured drafts allocate the node budget across multiple branches, allowing the teacher to accept whichever prefix matches. Prior work has explored multi-head draft architectures and adaptive tree structures that argue fixed draft topologies can be suboptimal under a node budget.

This work asks: can a lightweight student—too cheap to run multiple decoding heads—still construct useful speculative trees? The key tension is between *depth* (a long correct chain yields many accepted tokens) and *breadth* (side branches hedge against student errors). We propose and evaluate a *spine-preserving tree* policy: the student first builds a top-1 chain to maximum depth, then spends remaining node budget on high-probability side branches at positions where the student's confidence is low or the distribution is flat.

We evaluate this question in a controlled setting: a synthetic order-2 Markov teacher with a 32-token vocabulary and three entropy profiles, paired with an n-gram student trained on teacher samples. This design isolates the algorithmic question of tree construction from confounds of real-model infrastructure (KV-cache management, tree attention, GPU kernel overhead). We report results as accepted greedy tokens per verification call, not wall-clock speedup.

## Method

### Teacher Model

The teacher is a synthetic order-2 Markov decoder over a vocabulary of 32 tokens. Three entropy profiles control the next-token distribution:

- **Low entropy:** peaked distributions; the teacher is highly predictable.
- **Mixed entropy:** moderate entropy; some positions are peaked, others are flat.
- **High entropy:** flat distributions; the teacher is hard to predict.

The teacher is deterministic under greedy decoding: given a context, the top-1 token is unambiguous.

### Student Model

The student is an n-gram model (order 2, matching the teacher's Markov order) trained on 2,500 sequences of length 64 sampled from the teacher. The student estimates conditional probabilities $P(t \mid c)$ for each token $t$ given context $c$. No neural network is used; the student is intentionally minimal to test whether a cheap model can provide useful tree-structure signals.

### Draft Policies

All policies operate under a fixed node budget $B = 15$ and maximum depth $D = 8$. The branch factor $k = 4$ limits how many children any node may have.

1. **chain_top1:** Top-1 student chain of depth $\min(B, D)$. Uses all budget on a single sequence.
2. **static_width2:** Breadth-first tree with width 2 at each level, up to depth and budget limits.
3. **student_best_first:** Pure probability-prioritized tree. Nodes are expanded in order of the student's estimated probability of the path from root, regardless of depth.
4. **student_spine_tree:** Preserve a top-1 chain (the "spine") to maximum depth, then allocate remaining budget to high-probability side branches at positions along the spine where the student's top-1 confidence is low.
5. **oracle_\*:** Upper-bound policies that use the teacher's true probabilities for tree construction. These are not achievable by any real student but bound the best possible performance.

### Verification

Given a draft tree, the teacher performs greedy verification: it walks the tree from the root, accepting each node whose token matches the teacher's greedy output for that context, and stops at the first mismatch. The metric is the number of accepted tokens per verification call. This is an *algorithmic acceptance proxy*, not a wall-clock measurement. It does not account for tree-attention implementation cost, KV-cache overhead, or parallel verification latency.

### Experimental Protocol

For each entropy profile, we:

1. Sample 2,500 training sequences (length 64) from the teacher.
2. Train the n-gram student on these sequences.
3. Evaluate on 5,000 held-out contexts.
4. Construct draft trees under each policy with budget 15, max depth 8, branch factor 4.
5. Record mean accepted tokens and zero-accept rate (fraction of verification calls where no draft token is accepted).

A smoke test (100 eval contexts, budget 7, max depth 5) confirmed harness correctness before full runs.

## Results

### Main Comparison

| Profile | Chain mean accepted | Spine-tree mean accepted | Lift vs chain | Chain zero-accept | Spine zero-accept |
|---|---:|---:|---:|---:|---:|
| Mixed entropy | 5.7436 | 6.0800 | +5.86% | 14.72% | 3.84% |
| Low entropy | 7.7568 | 7.7822 | +0.33% | 3.04% | 2.48% |
| High entropy | 3.1744 | 3.6830 | +16.02% | 28.26% | 4.58% |

The spine-preserving tree outperforms the top-1 chain across all three entropy profiles. The improvement is largest in the high-entropy regime (+16.02%), where the chain suffers frequent zero-accept rounds (28.26%) that the spine tree reduces to 4.58%. In the low-entropy regime, the chain is already near-optimal (the teacher is highly predictable), so the tree provides marginal benefit (+0.33%).

Macro-average lift of `student_spine_tree` over `chain_top1`: **+7.40%** accepted tokens per verify. Macro-average absolute zero-accept reduction: **11.71 percentage points**.

No confidence intervals or standard deviations were computed over the 5,000 evaluation contexts; the reported means should be interpreted accordingly, and the precision of the claimed lifts is uncertain.

### Negative Result: Pure Best-First Tree

The `student_best_first` policy, which expands nodes purely by probability priority without preserving a spine, produced *lower* mean accepted tokens than the chain despite achieving a lower zero-accept rate. This is an important negative sub-result: spending all nodes on breadth sacrifices the long high-value spine. A tree that hedges broadly but lacks depth cannot recover the multi-token acceptance that a correct deep chain provides. This finding contradicts the intuition that broader trees are uniformly better and suggests that tree structure must be constrained to preserve depth.

### Static Width-2 Tree

The `static_width2` policy performed between the chain and the spine tree, confirming that some tree structure helps but that the specific allocation strategy matters. A fixed-width tree does not adapt its branching to the student's confidence profile.

### Oracle Upper Bounds

Oracle policies (using teacher probabilities) substantially outperform all student policies, confirming that the student's imperfect probability estimates leave meaningful headroom. This gap is largest in the high-entropy profile where the student's n-gram estimates are least accurate.

## Limitations

1. **Synthetic teacher only.** The Markov teacher with a 32-token vocabulary does not represent the token distribution, error modes, or context-dependence of production LLMs. The student's n-gram architecture is also far simpler than even the smallest neural draft models used in practice. Whether these results transfer to real language models is unknown.

2. **Acceptance proxy, not wall-clock speedup.** The metric—accepted greedy tokens per verification call—omits the costs of tree attention, KV-cache management, and GPU kernel overhead. In a real system, the overhead of verifying a tree versus a chain may partially or fully offset the acceptance gains. Whether the spine tree yields net wall-clock improvement is an open question.

3. **No real tokenizer or vocabulary.** The 32-token vocabulary is orders of magnitude smaller than production tokenizers (32K–128K tokens). Vocabulary size affects the student's calibration and the branching structure of the draft tree.

4. **Greedy verification only.** The teacher verifies greedily (top-1 match). Sampling-based verification, which is common in speculative decoding, may change the relative advantage of tree versus chain drafts.

5. **Fixed budget and depth.** Results are reported for budget 15 and max depth 8. The optimal budget allocation likely depends on the teacher's entropy profile and the student's accuracy, neither of which we sweep comprehensively.

6. **No ablation of student quality.** The n-gram student is the only student tested. A more capable student (e.g., a small neural model) might reduce the advantage of tree structures by producing more accurate chains, or might amplify the advantage by providing better-calibrated branching signals.

7. **Single Markov order.** The teacher and student both use order 2. Real LLMs have effectively unbounded context; the student's ability to estimate useful tree structure from longer contexts is untested.

8. **No random seed fixation.** The harness uses Python's default random state; exact reproducibility of the reported numbers is not guaranteed. This is a methodological gap.

9. **No variance reporting.** Means are reported over 5,000 evaluation contexts per profile without confidence intervals or standard deviations. This weakens the precision of the claimed lifts and makes statistical significance assessment impossible.

## Reproducibility Checklist

- **Code available:** `scripts/spec_tree_student_experiment.py` (harness), `scripts/summarize_results.py` (summary helper).
- **Random seeds:** Not fixed. Reproducibility of exact numeric results is not guaranteed. This is a known gap.
- **Data generation:** All data is synthetic (Markov teacher samples). No external datasets are required.
- **Hyperparameters:** Vocab = 32, order = 2, train sequences = 2,500, seq len = 64, eval contexts = 5,000, budget = 15, max depth = 8, branch-k = 4.
- **Hardware:** Linux aarch64, kernel 6.17.0-1014-nvidia, Python 3.12.3, 128 GB RAM. Max RSS per run ≈ 18.9 MB. No GPU required.
- **Result files:** `artifacts/results/smoke.json`, `artifacts/results/mixed_entropy_budget15_spine.json`, `artifacts/results/low_entropy_budget15_spine.json`, `artifacts/results/high_entropy_budget15_spine.json`, `artifacts/results/summary.json`.
- **Log files:** `artifacts/logs/smoke.log`, `artifacts/logs/mixed_entropy_budget15_spine.log`, `artifacts/logs/low_entropy_budget15_spine.log`, `artifacts/logs/high_entropy_budget15_spine.log`, `artifacts/logs/summary.log`, `artifacts/logs/telemetry_before.log`, `artifacts/logs/telemetry_after.log`.
- **Statistical reporting:** Means over 5,000 evaluation contexts per profile. No confidence intervals or standard deviations reported; this is a gap.
- **Evidence classification:** Results are from a toy simulation (synthetic Markov teacher, n-gram student, acceptance-count proxy). This is not a llama.cpp hook-prototype result, not a CUDA copy calibration, and not a final production validation.

## Conclusion

In a controlled Markov-teacher setting, a spine-preserving speculation tree—where a lightweight student maintains a deep top-1 draft chain and allocates remaining node budget to high-probability side branches—improves accepted tokens per verification call by a macro-average of 7.40% over a top-1 chain, with the largest gains in high-entropy regimes (+16.02%). The policy also reduces zero-accept rounds by 11.71 percentage points on average. A pure best-first tree underperforms the chain on mean accepted tokens, demonstrating that unconstrained breadth sacrifices valuable depth.

These results support the hypothesis that the effective tree structure for speculative decoding is not "maximize breadth" but rather "preserve depth, hedge at uncertainty." However, the evidence is confined to a synthetic Markov teacher with an acceptance-count proxy and no variance estimates. The critical next step is validation against a real causal language model teacher and a cheap neural or n-gram drafter, measuring wall-clock tokens per second and acceptance rates on natural language prompts. Until such validation is performed, the spine-tree policy should be considered a promising prototype, not a deployment-ready technique.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Experiment harness | `scripts/spec_tree_student_experiment.py` |
| Summary helper | `scripts/summarize_results.py` |
| Smoke result | `artifacts/results/smoke.json` |
| Mixed entropy result | `artifacts/results/mixed_entropy_budget15_spine.json` |
| Low entropy result | `artifacts/results/low_entropy_budget15_spine.json` |
| High entropy result | `artifacts/results/high_entropy_budget15_spine.json` |
| Summary results | `artifacts/results/summary.json` |
| Smoke log | `artifacts/logs/smoke.log` |
| Mixed entropy log | `artifacts/logs/mixed_entropy_budget15_spine.log` |
| Low entropy log | `artifacts/logs/low_entropy_budget15_spine.log` |
| High entropy log | `artifacts/logs/high_entropy_budget15_spine.log` |
| Summary log | `artifacts/logs/summary.log` |
| Telemetry (before) | `artifacts/logs/telemetry_before.log` |
| Telemetry (after) | `artifacts/logs/telemetry_after.log` |
| Claim ledger | `papers/source-record-redacted-20260502T090419832744+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T090419832744+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T090419832744+0000/paper_manifest.json` |
