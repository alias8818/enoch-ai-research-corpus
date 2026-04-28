# Entity-Neighborhood Windower: Entity-Guided Evidence Packing for Retrieval-Augmented Prompts

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present Entity-Neighborhood Windower (ENW), a prompt-construction method that selects evidence for retrieval-augmented generation by expanding around entity seeds rather than ranking isolated text chunks. In a vanilla retrieve-then-read pipeline, the top-$k$ scored sentences are packed into the prompt regardless of whether they form a coherent evidence neighborhood. ENW instead identifies entity mentions shared between the query and candidate sentences, seeds windows around those entities, and expands along local sentence adjacency and cross-document citation links. We evaluate ENW against a vanilla top-$k$ baseline across three progressively harder suites: 60 synthetic single-document tasks, 120 mixed single- and cross-document tasks with paraphrased queries, and 80 real tasks drawn from the public CUAD commercial-contract dataset. On the real CUAD suite at a 2048-token budget, ENW achieves 0.526 answer F1 and 0.638 evidence recall versus 0.392 and 0.438 for vanilla, and among solved tasks requires 24.6% fewer mean minimum prompt tokens. However, the token-reduction advantage does not appear on synthetic or semi-synthetic suites, and ENW incurs approximately 3× higher prompt-construction latency on real documents. These results support the hypothesis that entity-neighborhood packing improves same-budget answer quality on real contract text, but generality beyond commercial contracts and the latency–quality trade-off remain open questions.

---

## 1. Introduction

Retrieval-augmented generation (RAG) systems typically select evidence by scoring text chunks against a query and packing the top-$k$ results into the prompt. This approach treats each chunk independently: two adjacent sentences that jointly establish a contractual obligation may be split across the chunk boundary, and a cross-document citation that locates the controlling authority may fall below the scoring threshold even though the entity it mentions is central to the query.

Entity-Neighborhood Windower addresses this by organizing evidence selection around entity mentions rather than chunk-level relevance scores. The intuition is that if a query mentions "Acme Corp." and a sentence in Document A mentions "Acme Corp." while citing an agreement defined in Document B, the sentence in Document B that defines that agreement should be included even if its surface similarity to the query is low. ENW implements this by seeding windows at entity-mention hits and expanding along sentence adjacency and cross-document entity/citation links.

This paper reports results from a three-stage evaluation: (1) synthetic single-document tasks, (2) semi-synthetic cross-document tasks with paraphrased queries and distractors, and (3) real CUAD commercial-contract QA tasks. The evaluation measures answer F1 proxy, evidence recall, exact-answer visibility, minimum successful prompt tokens, and prompt-construction latency under fixed token budgets.

---

## 2. Method

### 2.1 Vanilla Retrieve-Then-Read Baseline

The baseline scores each sentence in the candidate pool against the query using a combined query/content relevance score, selects the top-$k$ sentences by score, and packs them into the prompt in score order until the token budget is exhausted.

### 2.2 Entity-Neighborhood Windower

ENW operates in three phases:

1. **Entity seeding.** Extract entity mentions from the query. Score all candidate sentences against the query. Identify sentences that both score above a threshold and contain at least one entity also present in the query. These become seed sentences.

2. **Neighborhood expansion.** From each seed sentence, expand outward along sentence adjacency within the same document, adding neighboring sentences to the window. Expansion continues until the window reaches a local boundary or the incremental score contribution falls below a threshold.

3. **Cross-document propagation.** When a high-scoring sentence contains a bridge entity (an entity, citation, or agreement name that links to another document), ENW follows that link and seeds a new window in the target document around the linked entity. This propagation step is the primary mechanism by which ENW recovers evidence that vanilla top-$k$ scoring would miss.

4. **Budget-constrained packing.** Collected windows are merged, deduplicated, and packed into the prompt in order of descending seed score until the token budget is exhausted.

### 2.3 Implementation

Both packers are implemented in pure Python in a single benchmark script (`experiments/entity_neighborhood_benchmark.py`). No external ML models or GPU resources are used; scoring is based on term-overlap and entity-match heuristics. Sentence segmentation uses a rule-based splitter for synthetic/semi-synthetic text and an extended rule-based splitter for real CUAD contract text.

---

## 3. Experimental Setup

### 3.1 Task Suites

**Original synthetic suite (60 tasks).** Deterministic synthetic tasks spanning five families: contract clause extraction, case-law reasoning, repository QA, form field extraction, and citation-heavy QA. Each task provides a query, a set of candidate sentences with gold answer spans, and gold evidence sentences. Single-document only; no paraphrasing.

**Mixed semi-synthetic suite (120 tasks).** Combines the 60 original tasks with 60 hard linked-evidence tasks. Hard tasks separate the target entity, the locator clause or citation, and the answer-bearing authority across two documents. Questions are paraphrased versions of the original templates. Distractor sentences mention the target entity but not the controlling linked clause.

**Real CUAD suite (80 tasks).** Drawn from the public CUAD dataset (The Atticus Project), which contains real commercial contracts with expert-labeled clause answers and questions. The loader converts CUAD QA items into sentence-level evidence tasks using answer character offsets. Questions use deterministic paraphrases of the published CUAD clause-review questions.

### 3.2 Metrics

- **Answer F1 proxy:** token-level F1 between the gold answer and the answer text visible in the packed prompt. This measures whether the packed evidence contains the information needed to produce the correct answer, not whether an LLM actually produces it.
- **Evidence recall:** fraction of gold evidence sentences included in the packed prompt.
- **Exact-answer visibility:** count of tasks where the gold answer string appears verbatim in the packed prompt.
- **Minimum successful prompt tokens:** the smallest token budget at which a task is "solved" (gold answer visible), measured per task and averaged over solved tasks.
- **Prompt-construction latency:** wall-clock time for the packing algorithm, measured per task.

### 3.3 Budgets

- Synthetic and mixed suites: 120, 180, 260, 360 tokens.
- Real CUAD suite: 256, 512, 1024, 1536, 2048 tokens.

### 3.4 Success Criteria

The project defined two success bars:

1. **Quality gain:** ENW achieves at least +5 F1 points over vanilla at the same token budget.
2. **Token reduction:** ENW achieves at least 15% fewer mean minimum successful prompt tokens among solved tasks.

---

## 4. Results

### 4.1 Original Synthetic Suite

| Budget | ENW F1 | Vanilla F1 | ENW Recall | Vanilla Recall |
|--------|--------|------------|------------|----------------|
| 120    | 1.000  | 0.934      | 1.000      | 0.933          |
| 180    | 1.000  | 0.989      | 1.000      | 0.989          |
| 260    | 1.000  | 1.000      | 1.000      | 1.000          |
| 360    | 1.000  | 1.000      | 1.000      | 1.000          |

At 120 tokens, ENW leads by +6.6 F1 points, clearing the quality-gain criterion. At higher budgets both methods converge to perfect scores on these simple single-document tasks.

Mean minimum successful prompt tokens: 115.65 (ENW) vs. 122.63 (vanilla), a 5.7% reduction. The 15% token-reduction criterion is **not met** on this suite.

Packing latency: sub-millisecond for both methods; ENW approximately 0.4 ms slower per task.

### 4.2 Mixed Semi-Synthetic Suite

| Budget | ENW F1 | Vanilla F1 | ENW Recall | Vanilla Recall |
|--------|--------|------------|------------|----------------|
| 120    | —      | —          | —          | —              |
| 360    | 0.900  | 0.644      | 0.925      | 0.769          |

On the hard linked-evidence subset at 360 tokens, ENW solved 48/60 exact-answer tasks versus 17/60 for vanilla. At 120 tokens on hard tasks, ENW solved 24/60 versus 4/60 for vanilla. The quality-gain criterion is strongly supported on cross-document, paraphrased tasks.

Mean minimum successful prompt tokens among solved tasks: 167.6 (ENW) vs. 146.9 (vanilla). ENW requires *more* tokens on average, partly because vanilla fails many hard tasks entirely (they are excluded from the "solved" average for vanilla, biasing its average downward toward easier tasks). The token-reduction criterion remains **not supported** on this suite.

Packing latency at 360 tokens: ~0.84 ms (ENW) vs. ~0.36 ms (vanilla).

### 4.3 Real CUAD Suite

| Budget | ENW F1 | Vanilla F1 | ENW Recall | Vanilla Recall | ENW Exact | Vanilla Exact |
|--------|--------|------------|------------|----------------|-----------|---------------|
| 256    | —      | —          | —          | —              | —         | —             |
| 512    | —      | —          | —          | —              | —         | —             |
| 1024   | —      | —          | —          | —              | —         | —             |
| 1536   | —      | —          | —          | —              | —         | —             |
| 2048   | 0.526  | 0.392      | 0.638      | 0.438          | 41/80     | 30/80         |

At 2048 tokens, ENW leads by +13.4 F1 points and +20.0 recall points. Exact-answer visibility improves from 30/80 to 41/80 tasks.

Among solved tasks, mean minimum successful prompt tokens: 690.3 (ENW) vs. 915.7 (vanilla), a **24.6% reduction**. This clears the 15% token-reduction criterion on the real suite.

Packing latency at 2048 tokens: ~15.6 ms (ENW) vs. ~5.5 ms (vanilla). ENW is approximately 3× slower on real documents due to the larger candidate pools and cross-document propagation overhead.

### 4.4 Summary of Criteria

| Criterion | Synthetic | Semi-Synthetic | Real CUAD |
|-----------|-----------|----------------|-----------|
| +5 F1 at same budget | ✓ (+6.6 at 120 tok) | ✓ (+25.6 at 360 tok) | ✓ (+13.4 at 2048 tok) |
| ≥15% token reduction | ✗ (5.7%) | ✗ (−13.9%) | ✓ (24.6%) |

The quality-gain criterion is met on all three suites. The token-reduction criterion is met only on the real CUAD suite, where it is driven by ENW's ability to solve harder tasks at lower budgets rather than by compressing already-solvable tasks.

---

## 5. Limitations

1. **Domain breadth.** All real-document results come from CUAD commercial contracts. Case law, regulatory text, and non-legal domains are untested. The project decision recommends a separate case-law/model-answer validation as optional follow-on work.

2. **Answer F1 proxy, not end-to-end generation quality.** The metrics measure whether gold answer text is *visible* in the packed prompt, not whether an LLM actually produces the correct answer when given that prompt. End-to-end generation evaluation with a specific model is outside the scope of this study.

3. **Small real-task sample.** The CUAD evaluation uses 80 tasks. This is sufficient to observe directional effects but insufficient for tight confidence intervals on absolute metric values.

4. **Token-reduction inconsistency.** The 15% token-reduction criterion is not met on synthetic or semi-synthetic suites. On the mixed suite, the apparent failure is partly an artifact of the "solved-tasks-only" averaging (vanilla solves fewer hard tasks, so its average is computed over easier, lower-token tasks). Nevertheless, the claim that ENW consistently reduces prompt tokens is not supported across all evaluated settings.

5. **Latency overhead.** ENW incurs approximately 3× higher prompt-construction latency on real documents (15.6 ms vs. 5.5 ms). While still sub–20 ms and likely negligible relative to LLM inference time, this overhead may matter in high-throughput or latency-sensitive deployments.

6. **Heuristic scoring.** Both packers use term-overlap and entity-match heuristics rather than learned neural retrievers. The relative gains of ENW may change if a dense retriever is substituted for the scoring function.

7. **No human evaluation.** Answer correctness, evidence sufficiency, and prompt coherence have not been assessed by human annotators.

8. **Deterministic paraphrases only.** The paraphrased questions in the semi-synthetic and CUAD suites are generated by deterministic rules, not by natural variation from multiple annotators.

---

## 6. Reproducibility Checklist

- **Code availability:** `experiments/entity_neighborhood_benchmark.py` — single-file pure-Python benchmark harness.
- **Data availability:** `data/cuad/data.zip` — public CUAD archive from The Atticus Project GitHub.
- **Result files:** `results/entity_neighborhood_benchmark.json` (synthetic + mixed), `results/cuad_real_benchmark.json` (real CUAD).
- **Verification commands:**
  - `python3 -m py_compile experiments/entity_neighborhood_benchmark.py`
  - `python3 experiments/entity_neighborhood_benchmark.py --out results/entity_neighborhood_benchmark.json --suite mixed --n-per-family 12 --budgets 120,180,260,360`
  - `python3 experiments/entity_neighborhood_benchmark.py --out results/cuad_real_benchmark.json --suite cuad_real --real-limit 80 --budgets 256,512,1024,1536,2048`
  - Smoke check: `python3 experiments/entity_neighborhood_benchmark.py --out /tmp/mixed_check.json --suite mixed --n-per-family 2 --budgets 120,360`
- **Determinism:** All tasks and scoring are deterministic; re-running the above commands should reproduce the reported row counts (960 rows for mixed, 800 rows for CUAD) and metric means.
- **Hardware:** No GPU required. All experiments run on CPU with sub-second wall-clock time per task.
- **Software dependencies:** Python 3 standard library only (no external packages beyond the CUAD data archive).

---

## 7. Conclusion

Entity-Neighborhood Windower improves same-budget answer quality over a vanilla top-$k$ baseline across synthetic, semi-synthetic, and real contract-QA tasks. On the public CUAD dataset, ENW achieves +13.4 F1 points and +20.0 recall points at 2048 tokens, and requires 24.6% fewer mean minimum prompt tokens among solved tasks. These gains are consistent with the hypothesis that entity-guided neighborhood expansion recovers cross-document evidence that independent chunk scoring misses.

However, the results carry important caveats. The token-reduction advantage does not appear on simpler synthetic tasks, where both methods converge at moderate budgets. ENW's latency is approximately 3× higher on real documents. The evaluation measures answer visibility rather than end-to-end generation quality, and the real-task sample is limited to 80 CUAD items from a single contract domain.

The current project artifacts support the finding that entity-neighborhood packing improves evidence quality at fixed token budgets on real commercial-contract text. Whether these gains generalize to case law, regulatory text, or non-legal domains, and whether they survive substitution of neural retrievers for heuristic scoring, remain open questions.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Benchmark script | `experiments/entity_neighborhood_benchmark.py` |
| Synthetic + mixed results | `results/entity_neighborhood_benchmark.json` |
| Real CUAD results | `results/cuad_real_benchmark.json` |
| Results summary | `results/summary.md` |
| CUAD data archive | `data/cuad/data.zip` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Evidence bundle | `papers/source-record-redacted/evidence_bundle.json` |
| Claim ledger | `papers/source-record-redacted/claim_ledger.json` |
| Publication manifest | `papers/source-record-redacted/publication/publication_manifest.json` |
| Source module | `src/enw/__init__.py` |
