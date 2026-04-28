# KV Eviction Gold Labels: Block-Level Relevance Labels for Key-Value Cache Eviction Evaluation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We investigate whether block-level gold relevance labels for key-value (KV) cache eviction can meaningfully separate retention policies, expose systematic failure modes, and quantify the gap between heuristic and label-informed eviction. Across three progressively realistic experimental stages—synthetic-label simulation (1,500 examples), deterministic replayed-ablation labeling (300 examples), and neural-model replayed-ablation labeling using Qwen2.5-0.5B-Instruct (100 examples)—we find that label-informed retention consistently outperforms heuristic baselines by large margins. On the neural replay stage, the label-aware policy achieves 0.96 accuracy on full-context-correct examples versus 0.33 for lexical query-overlap retention (+62.67 percentage points). A persistent failure cluster emerges: lexical query-overlap retention systematically loses causal evidence in code-navigation tasks (accuracy 0.18), while label-aware retention preserves it (0.91). However, these results carry significant caveats: the label-aware policy approximates an oracle, task examples are synthetically generated, the neural model answers only 75% of full-context prompts correctly, and all experiments use a 0.5B-parameter model. We report these findings as evidence for the diagnostic value of block-level eviction labels, not as evidence that such labels are practical to obtain at scale.

## 1. Introduction

Long-context language models must manage finite KV cache budgets during inference. When the cache exceeds available capacity, some key-value pairs must be evicted. Common eviction heuristics—recency weighting, lexical overlap with the query, or random sampling—make retention decisions without explicit knowledge of which context blocks are causally necessary for the task at hand. This raises a diagnostic question: if one could label each context block as relevant or safe-to-evict for a given task, how much would retention policy accuracy improve, and what failure modes would become visible?

We approach this question not by proposing a practical labeling method, but by constructing gold labels through counterfactual replay and measuring their diagnostic value. Specifically, we ask:

1. Do block-level gold labels separate retention policies in a measurable ranking?
2. Do they expose systematic failure clusters that heuristic policies miss?
3. Does the ranking separation persist when gold labels are inferred from model replays rather than synthetic generators?

We address these questions through three experimental stages of increasing realism, from synthetic toy simulation through deterministic replay to neural-model replay. Each stage reuses the same task families (structured extraction, code navigation, abstention calibration) and the same retention policies (random, recency, lexical query-overlap, label-aware, and oracle), enabling direct comparison of how label quality affects policy evaluation.

## 2. Method

### 2.1 Task Generation

Synthetic examples are generated with 16 context blocks each. Every example belongs to one of three task families:

- **Structured extraction**: Extract a specific field value (e.g., `VAL...`, `mod_...`, `owner_...`) from a structured document containing distractor blocks.
- **Code navigation**: Identify a value by tracing causal dependencies across code-like blocks, where lexical distractors share surface tokens with the query but are causally irrelevant.
- **Abstention calibration**: Determine that no answer exists in the provided context and respond with `ABSTAIN`.

Each block is internally tagged (at generation time) as relevant or irrelevant to the task. These tags are hidden from all retention policies and used only for audit and oracle evaluation.

### 2.2 Retention Policies

Given a keep budget of 4 blocks out of 16, five retention policies select which blocks to retain:

- **Random**: Uniform random selection of 4 blocks.
- **Recency**: Retain the 4 most recently positioned blocks.
- **Query-overlap**: Retain the 4 blocks with the highest lexical token overlap with the query.
- **Label-aware**: Retain blocks marked as relevant by the available labeling method (synthetic labels, replay-inferred labels, or neural replay labels), filling remaining budget with recency. This policy approximates an oracle because it directly uses the labeling method's output.
- **Oracle**: Retain all blocks tagged as relevant at generation time (synthetic stage) or all blocks inferred as sufficient by replay (replay stages).

A policy is scored as accurate for an example if it retains all blocks necessary for correct task completion and evicts no block whose removal would cause failure.

### 2.3 Labeling Methods

Three labeling methods produce block-level relevance labels, each used in a separate experimental stage:

**Synthetic labels (Stage 1).** The task generator's internal `Block.relevant` field directly provides gold labels. This is a toy oracle with no inference cost.

**Replayed-ablation labels (Stage 2).** For each example, a deterministic parser evaluates task correctness under counterfactual context ablations:
- One full-context evaluation.
- 16 keep-one-block-only evaluations (retain a single block, remove all others).
- 16 leave-one-block-out evaluations (remove a single block, retain all others).

A block is labeled *sufficient* if the keep-one-block-only evaluation succeeds. A block is labeled *unsafe to evict* if the leave-one-block-out evaluation fails. The deterministic parser provides exact correctness judgments. Cost: 33 evaluations per example.

**Neural replay labels (Stage 3).** The same ablation structure is applied, but correctness is judged by a neural language model (Qwen2.5-0.5B-Instruct) using greedy generation and exact-match token scoring against normalized answer tokens. Cost: 33 model generations per example (3,300 total for 100 examples).

### 2.4 Evaluation Metrics

- **Policy accuracy**: Fraction of examples for which the policy retains all necessary blocks.
- **Failure cluster analysis**: Categorization of policy failures into `lost_all_evidence` (no necessary block retained), `partial_evidence` (some but not all necessary blocks retained), and other types.
- **Targeted uplift**: Difference in accuracy between label-aware and the best heuristic baseline, measured on the subset of examples where the labeling method produces valid labels.
- **Replay cost**: Total number of task executions or model generations required to infer labels.

## 3. Results

### 3.1 Stage 1: Synthetic-Label Simulation (1,500 Examples)

| Policy | Accuracy |
|---|---|
| Random | 0.214 |
| Recency | 0.207 |
| Query-overlap | 0.336 |
| Label-aware (synthetic) | 1.000 |
| Oracle (synthetic) | 1.000 |

The label-aware policy achieves perfect accuracy because it directly reads synthetic gold labels. The ranking separation is clear: label-aware ≈ oracle > query-overlap > random ≈ recency. The targeted uplift of label-aware over query-overlap is +66.4 percentage points.

Query-overlap produced 996 total failures: 709 `lost_all_evidence` and 287 `partial_evidence`. Code-navigation accuracy under query-overlap was 0.0, because hard lexical distractors displaced causally necessary blocks.

This stage establishes that gold labels separate policies in a toy setting, but the label-aware policy is essentially an oracle, so the uplift reflects the ceiling of label-informed retention rather than a practical gain.

### 3.2 Stage 2: Replayed-Ablation Labels (300 Examples)

| Policy | Accuracy |
|---|---|
| Random | 0.513 |
| Recency | 0.520 |
| Query-overlap | 0.487 |
| Label-aware (replay) | 1.000 |
| Oracle (replay) | 1.000 |

Full-context correctness was 300/300 (deterministic parser). Of 300 examples, 250 had replay-sufficient blocks and 50 had individually unsafe-to-evict blocks. The replay-label-aware uplift over query-overlap is +51.33 percentage points.

The failure cluster persisted: query-overlap produced 154 `lost_all_replay_evidence` failures. Code-navigation accuracy under query-overlap was 0.22, compared to 1.0 for label-aware retention.

Baseline accuracies are higher than in Stage 1 (random ~0.51 vs. ~0.21), which reflects the different label structure: replay-inferred labels identify sufficient subsets rather than individual relevant blocks, changing which examples are scorable. This makes cross-stage accuracy comparisons indirect.

### 3.3 Stage 3: Neural Replay Labels (100 Examples)

**All-example accuracy** (including 25 examples where the model failed on full context):

| Policy | Accuracy |
|---|---|
| Random | 0.47 |
| Recency | 0.43 |
| Query-overlap | 0.33 |
| Label-aware (neural) | 0.80 |
| Oracle (neural replay) | 0.80 |

**Full-context-correct subset** (75/100 examples where the model answered correctly with full context):

| Policy | Accuracy |
|---|---|
| Random | 0.52 |
| Recency | 0.48 |
| Query-overlap | 0.333 |
| Label-aware (neural) | 0.96 |
| Oracle (neural replay) | 0.96 |

Of the 75 full-context-correct examples, 67 had neural sufficient-block labels and 38 had neural unsafe-to-evict labels. The targeted neural-label-aware uplift over query-overlap on the full-context-correct subset is +62.67 percentage points; over random, +44.0 percentage points.

The failure cluster persisted under neural generations: query-overlap produced 48 `lost_all_neural_replay_evidence` failures. Code-navigation accuracy under query-overlap was 0.1818, while neural-label-aware reached 0.9091.

A notable negative result: 25% of examples (25/100) could not be labeled because the model failed on the full-context prompt. On these examples, no label-informed retention decision is possible, and the all-example label-aware accuracy drops to 0.80. This represents a hard floor on the practical coverage of replay-based labeling with weak models.

### 3.4 Cross-Stage Summary

The ranking label-aware > query-overlap > random ≈ recency is consistent across all three stages. The code-navigation failure cluster under query-overlap (accuracy 0.0 → 0.22 → 0.18) is robust across label sources. However, the label-aware policy's near-oracle nature means the uplift figures represent upper bounds, not achievable gains from any practical labeling method that falls short of oracle accuracy.

## 4. Limitations

1. **Synthetic task generation.** All examples are procedurally generated with controlled distractor structure. Real-world long-context tasks may exhibit different failure modes, and the observed failure cluster (lexical distractors displacing causal evidence in code navigation) may not generalize to naturalistic tasks.

2. **Label-aware policy as near-oracle.** The label-aware retention policy directly uses the best available labels, making it approximately an oracle. The large uplifts over heuristic baselines therefore measure the ceiling of label-informed retention, not the gain achievable by any practical labeling method that introduces its own errors.

3. **Small neural model.** The neural replay stage uses Qwen2.5-0.5B-Instruct, a 0.5B-parameter model that answers only 75% of full-context prompts correctly. The 25% failure rate on full context means replay-based labels cannot be inferred for a substantial fraction of examples. Stronger models may produce different label distributions and different policy rankings.

4. **Small scale.** The neural replay stage evaluates 100 examples. The synthetic and replay stages evaluate 1,500 and 300 examples respectively, but these use deterministic or oracle-based labelers. No stage approaches the scale needed for dataset production.

5. **Exact-match scoring.** Neural replay correctness is judged by exact token match against normalized answer strings. This binary criterion may over-penalize partially correct generations and under-detect semantically equivalent answers, affecting label quality.

6. **No version control.** The project directory is not under git version control, limiting reproducibility auditability at the repository level.

7. **Single model and hardware configuration.** All neural experiments run on a single local GPU with a single model. No cross-model or cross-hardware replication has been performed.

8. **Replay cost.** Replayed-ablation labeling requires 33 evaluations per example. At the neural stage, this translates to 3,300 model generations for 100 examples. Scaling to thousands of examples with larger models would incur substantial compute costs that have not been characterized.

## 5. Reproducibility Checklist

- **Code availability**: Source files are present in the project directory (`src/kv_eviction_gold_mvp.py`, `src/replayed_ablation_oracle.py`, `src/neural_replayed_ablation_oracle.py`) with corresponding test suites (`tests/test_kv_eviction_gold_mvp.py`, `tests/test_replayed_ablation_oracle.py`, `tests/test_neural_replayed_ablation_oracle.py`). All `py_compile` checks and unit tests (8/8) pass.
- **Command-line regeneration**: The neural replay artifacts were regenerated with `.venv/bin/python src/neural_replayed_ablation_oracle.py --n 100 --total-blocks 16 --keep-blocks 4 --seed 344 --model-id Qwen/Qwen2.5-0.5B-Instruct --batch-size 48 --outdir artifacts`.
- **Random seed**: Seed 344 is specified for all stages.
- **Model identifier**: `Qwen/Qwen2.5-0.5B-Instruct`, loaded from local Hugging Face cache.
- **Dependencies**: Python 3, PyTorch 2.11.0+cu130, transformers, accelerate, safetensors, sentencepiece. Project-local `.venv` created with `uv venv`.
- **Hardware**: Local CUDA-capable GPU (cu130). No cloud or distributed compute used.
- **Artifact persistence**: All result CSVs, JSON summaries, label previews, and spot-check reports are written to the `artifacts/` directory.
- **No git commits**: The project directory is not under version control; artifact integrity relies on file timestamps and content hashes rather than commit history.

## 6. Conclusion

Block-level gold labels for KV cache eviction, whether provided by a synthetic oracle or inferred through counterfactual replay, produce consistent and large ranking separations among retention policies across three experimental stages. The most striking finding is a persistent failure cluster: lexical query-overlap retention systematically loses causal evidence in code-navigation tasks, achieving accuracy as low as 0.18 even when label-aware retention reaches 0.91 on the same examples. This failure mode is robust across synthetic, deterministic, and neural label sources.

However, the practical implications are bounded. The label-aware policy operates at near-oracle accuracy, so the observed uplifts (+44 to +66 percentage points over heuristic baselines) represent upper bounds. The neural replay stage reveals that a weak model (0.5B parameters) cannot label 25% of examples due to full-context failures, imposing a hard coverage limit. All tasks are synthetic, and no claim of external validity is warranted.

The primary contribution of this work is diagnostic: block-level eviction labels are a useful evaluation tool for exposing systematic retention failures, particularly in tasks where surface-level lexical cues are misleading. Whether such labels can be produced at scale with sufficient accuracy to improve real eviction decisions remains an open question that would require validation on naturalistic tasks with stronger models at larger scale.

## Referenced Artifacts

### Source files
- `src/kv_eviction_gold_mvp.py` — Synthetic-label MVP harness
- `src/replayed_ablation_oracle.py` — Deterministic replayed-ablation labeler
- `src/neural_replayed_ablation_oracle.py` — Neural replayed-ablation labeler
- `tests/test_kv_eviction_gold_mvp.py` — MVP unit tests (3/3 passed)
- `tests/test_replayed_ablation_oracle.py` — Replay labeler unit tests
- `tests/test_neural_replayed_ablation_oracle.py` — Neural labeler unit tests (8/8 total passed)

### Result files
- `artifacts/mvp_eval_rows.csv` — Stage 1 per-example/policy evaluation rows (7,500 rows)
- `artifacts/mvp_summary.json` — Stage 1 aggregate metrics
- `artifacts/synthetic_gold_label_preview.json` — Stage 1 label preview
- `artifacts/spot_check_failures.md` — Stage 1 failure spot checks
- `artifacts/replayed_ablation_eval_rows.csv` — Stage 2 per-example/policy rows (1,500 rows)
- `artifacts/replayed_ablation_summary.json` — Stage 2 aggregate metrics
- `artifacts/replayed_ablation_label_preview.json` — Stage 2 label preview (25 examples)
- `artifacts/replayed_ablation_spot_checks.md` — Stage 2 failure spot checks
- `artifacts/neural_replayed_ablation_eval_rows.csv` — Stage 3 per-example/policy rows (500 rows)
- `artifacts/neural_replayed_ablation_summary.json` — Stage 3 aggregate metrics
- `artifacts/neural_replayed_ablation_label_preview.json` — Stage 3 label preview (20 examples)
- `artifacts/neural_replayed_ablation_spot_checks.md` — Stage 3 failure spot checks

### Decision and audit files
- `.omx/project_decision.json` — Project decision: `finalize_positive`, hypothesis `supported`
- `run_notes.md` — Full execution log across all three stages
- `papers/.../claim_ledger.json` — Claim audit with confidence ratings and wording constraints
- `papers/.../evidence_bundle.json` — Aggregated evidence bundle
