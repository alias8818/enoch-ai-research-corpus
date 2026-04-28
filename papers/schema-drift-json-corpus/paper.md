# Schema-Drift JSON Corpus: A Diagnostic Benchmark for Structured-Output Failure Modes Under Schema Mutation

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We present the Schema-Drift JSON Corpus, a 2,000-example synthetic benchmark designed to expose structured-output failure modes that stable-schema evaluation hides. The corpus applies controlled schema mutations—field renames, nested renames, value-format changes, optional-branch additions, and branch flattening—to canonical JSON schemas and records both the drifted schema and drift-operation labels. In deterministic baseline evaluation, a stable-schema slice yields ceiling performance across all controlled systems (1.0 strict leaf accuracy), while the drift slice separates them (canonical-only 0.449, top-level alias 0.869, nested alias 0.929, targeted repair 1.000), producing a +55.06 strict-leaf-point uplift for targeted repair over the canonical-only baseline. In live-model evaluation using three locally-served GGUF instruction models (Phi-4-mini, Qwen2.5-3B, Qwen3-0.6B) via llama.cpp, the drift corpus exposes model-specific failure clusters—particularly Phi-4-mini's branch-flatten weakness (0.048 strict leaf accuracy)—that aggregate metrics obscure. However, model rankings did not change between the stable and drift slices across any tested pair, so the corpus is not yet supported as a rank-flipping benchmark. The current project artifacts support the finding that schema-drift evaluation provides actionable failure-coverage and intervention-targeting signal in the tested setting, with moderate evidence strength and medium confidence.

## 1. Introduction

Structured JSON output from language models is increasingly deployed in production pipelines, yet standard evaluation typically measures adherence to a fixed, stable schema. When downstream schemas evolve—through field renames, added optional branches, or format changes—models may fail in ways invisible to stable-schema benchmarks. This raises a diagnostic question: can a corpus of schema-mutated JSON tasks expose failure modes that stable-schema evaluation hides, and can targeted drift-repair strategies yield measurable uplift?

We report results from the Schema-Drift JSON Corpus project, which constructed a reproducible synthetic benchmark and evaluated it against both deterministic controlled baselines and three locally-served instruction models. The central hypothesis is that schema-drift evaluation exposes separable failure modes and enables targeted intervention, not that it reliably reorders model rankings. The evidence supports this hypothesis as a diagnostic finding, with the important negative result that no rank flip occurred between stable and drift slices in the tested cohort.

## 2. Method

### 2.1 Corpus Generation

The corpus generator (`scripts/generate_schema_drift_corpus.py`) produces synthetic JSON-output records. Each record contains:

- A canonical schema defining the expected output structure.
- A requested drifted schema, derived by applying one or more drift operations to the canonical schema.
- An expected answer conforming to the drifted schema.
- Drift operation labels (e.g., `field_rename`, `nested_field_rename`, `value_format`, `optional_branch_added`, `branch_flatten`).

The generator was run with `--n 2000 --seed 3443677`, producing `data/schema_drift_corpus.jsonl`. The resulting drift-type distribution is:

| Drift Type | Count |
|---|---|
| field_rename | 2,000 |
| nested_field_rename | 985 |
| value_format | 602 |
| optional_branch_added | 397 |
| branch_flatten | 205 |

Note that individual examples may carry multiple drift labels, so counts exceed 2,000 in aggregate.

### 2.2 Evaluation Harness

The evaluator (`scripts/evaluate_schema_drift.py`) scores predictions against either the requested drifted schema or the canonical stable schema, using strict leaf accuracy (exact match at every leaf path) and exact match (full JSON equality). It supports:

- **Controlled deterministic baselines**: `canonical_only`, `top_level_alias`, `nested_alias`, `targeted_repair`—simulated systems that implement progressively more sophisticated drift-handling strategies.
- **Live model predictions**: JSONL input with `id`, `system`/`model`, and a prediction field (fenced or raw JSON), scored via the same leaf-accuracy metric.

The `--prediction-target` flag selects whether predictions are scored against the drifted schema (`drift`, default) or the canonical schema (`canonical`).

### 2.3 Prediction Collection

An OpenAI-compatible collector (`scripts/collect_openai_predictions.py`) queries local endpoints for `/v1/models` and `/chat/completions`, supporting both schema-in-prompt and prompt-only modes, as well as `--json-mode` for endpoints supporting OpenAI JSON response format. Predictions are written as JSONL for evaluation.

### 2.4 Models and Serving

Three cached local GGUF models were served sequentially via `llama.cpp`'s `llama-server` from a neutral `/tmp/schema_drift_services` directory:

1. **Phi-4-mini-instruct** (Q4_K_M quantization)
2. **Qwen2.5-3B-instruct** (Q4_K_M quantization)
3. **Qwen3-0.6B** (Q4_K_M quantization)

Each model was verified via `/v1/models` before collection and the server was stopped before proceeding. These are llama.cpp hook-prototype results, not production-validated deployments.

## 3. Results

### 3.1 Deterministic Baseline Evaluation

On the stable-schema slice, all four controlled systems achieved 1.0 strict leaf accuracy, providing no separation. On the drift slice:

| System | Strict Leaf Accuracy |
|---|---|
| canonical_only | 0.449 |
| top_level_alias | 0.869 |
| nested_alias | 0.929 |
| targeted_repair | 1.000 |

The targeted-repair system achieved a +55.06 strict-leaf-point uplift over the canonical-only baseline. This confirms that the drift slice separates systems that the stable slice cannot distinguish, at least for controlled deterministic baselines.

### 3.2 Live-Model Smoke Test (25 Examples, Phi-4-mini)

An initial 25-example smoke test compared two prompting strategies on Phi-4-mini:

| Strategy | Strict Leaf Accuracy | Exact Match |
|---|---|---|
| schema_prompt | 0.7285 | 0.48 |
| prompt_only | 0.0000 | — |

The prompt-only strategy produced no parseable or schema-adherent JSON on this drift slice, yielding floor performance. Drift-type weak spots under schema prompting were:

| Drift Type | Strict Leaf Accuracy |
|---|---|
| branch_flatten | 0.2292 |
| value_format | 0.5354 |
| optional_branch_added | 0.6190 |
| nested_field_rename | 0.6991 |

### 3.3 Two-Model Comparison (200 Examples)

| Slice | Phi-4-mini | Qwen2.5-3B | Rank |
|---|---|---|---|
| Drift (requested schema) | 0.5285 | 0.9497 | Qwen2.5-3B > Phi-4-mini |
| Stable (canonical schema) | 0.1294 | 0.9944 | Qwen2.5-3B > Phi-4-mini |

Rank changed between stable and drift: **False**.

Notably, Phi-4-mini's stable-schema performance (0.1294) was substantially lower than its drift-schema performance (0.5285), suggesting the canonical-schema prompt configuration degenerated for this model rather than that drift was easier.

### 3.4 Three-Model Comparison (200 Examples)

| Slice | Phi-4-mini | Qwen2.5-3B | Qwen3-0.6B | Rank |
|---|---|---|---|---|
| Drift (requested schema) | 0.5285 | 0.9497 | 0.7535 | Qwen2.5-3B > Qwen3-0.6B > Phi-4-mini |
| Stable (canonical schema) | 0.1294 | 0.9944 | 0.5849 | Qwen2.5-3B > Qwen3-0.6B > Phi-4-mini |

Rank changed between stable and drift: **False**.

Model-specific failure clusters exposed by the drift corpus:

- **Phi-4-mini**: Severe branch-flatten weakness (0.048 strict leaf accuracy), moderate weakness on optional_branch_added (0.330) and nested_field_rename (0.479).
- **Qwen3-0.6B**: Mid-tier performance with materially higher extra-path rate than Qwen2.5-3B.
- **Qwen2.5-3B**: High strict leaf accuracy but low exact match (0.63) due to optional/extra-field behavior—producing structurally compliant but non-identical outputs.

### 3.5 Summary of Key Negative Result

Across all live-model comparisons, the model ranking did not change between the stable and drift evaluation slices. The corpus is therefore not supported as a rank-flipping benchmark for this three-local-GGUF cohort. Its demonstrated value is diagnostic: it exposes failure clusters that aggregate metrics obscure.

## 4. Limitations

1. **Small and non-representative model cohort.** Only three small, locally-cached Q4_K_M GGUF models were tested. Results may not generalize to larger models, different quantizations, or cloud-hosted APIs.

2. **Limited example count.** Live-model evaluation used 200 examples per model per slice. Statistical power for rank-change detection is low at this scale.

3. **Prompt configuration confound.** Phi-4-mini's canonical-schema prompt degenerated (0.1294 strict leaf accuracy), making the stable-vs-drift comparison for this model difficult to interpret as a pure schema-drift effect rather than a prompt-engineering artifact.

4. **Synthetic corpus.** The corpus is procedurally generated from a fixed seed. It does not reflect real-world schema evolution patterns, domain-specific constraints, or the distribution of drift types encountered in production systems.

5. **Single-seed reproducibility.** All results use seed 3443677. Sensitivity to seed choice has not been tested.

6. **No external replication.** All experiments were conducted in a single local environment. No independent replication has been performed.

7. **Deterministic baselines are simulated, not learned.** The controlled systems (canonical_only, top_level_alias, etc.) implement hand-coded drift-handling strategies. Their separation properties do not directly predict how learned systems would behave.

8. **llama.cpp hook-prototype, not production validation.** Model serving used llama.cpp's `llama-server` with sequentially-started local processes. This is a prototype serving configuration, not a production-validated inference stack.

9. **No claim of universal effectiveness.** The current project artifacts support the finding in the tested setting only. The method is not proven to work universally.

## 5. Reproducibility Checklist

- **Corpus generation command**: `python3 scripts/generate_schema_drift_corpus.py --n 2000 --seed 3443677`
- **Deterministic evaluation command**: `python3 scripts/evaluate_schema_drift.py --corpus data/schema_drift_corpus.jsonl --out reports/evaluation_summary.json`
- **Live-model evaluation command (drift)**: `python3 scripts/evaluate_schema_drift.py --corpus data/schema_drift_corpus.jsonl --limit 200 --predictions <prediction_jsonl> --out reports/live_model_drift_comparison_3models_200.json`
- **Live-model evaluation command (stable)**: `python3 scripts/evaluate_schema_drift.py --corpus data/schema_drift_corpus.jsonl --limit 200 --prediction-target canonical --predictions <prediction_jsonl> --out reports/live_model_stable_comparison_3models_200.json`
- **Unit tests**: `python3 -m unittest discover -s tests -v` (3 tests, all passing)
- **Syntax check**: `python3 -m py_compile scripts/*.py` (passed)
- **Dependencies**: Python 3 stdlib only; no pytest or external packages required
- **Seed**: 3443677
- **Corpus size**: 2,000 examples
- **Live evaluation subset**: 200 examples per model per slice
- **Models**: Phi-4-mini-instruct-Q4_K_M, Qwen2.5-3B-instruct-Q4_K_M, Qwen3-0.6B-Q4_K_M (all GGUF, served via llama.cpp)
- **Server cleanup verified**: `ss -ltnp | grep -E '1808[012]'` returned no listeners after shutdown

## 6. Conclusion

The Schema-Drift JSON Corpus provides a reproducible 2,000-example diagnostic benchmark that exposes structured-output failure modes invisible to stable-schema evaluation. Deterministic baselines demonstrate that the drift slice separates systems the stable slice cannot (+55.06 strict-leaf-point uplift for targeted repair over canonical-only). Live-model evaluation across three locally-served GGUF instruction models confirms that the corpus exposes model-specific failure clusters—particularly Phi-4-mini's severe branch-flatten weakness (0.048 strict leaf) and Qwen2.5-3B's exact-match degradation from extra-field behavior. However, model rankings did not change between stable and drift slices in any tested comparison, so the corpus is not supported as a rank-flipping benchmark for this cohort. The project decision is `finalize_positive` with medium confidence and moderate evidence strength: the corpus meets its success criterion as a failure-coverage and intervention-targeting tool, and further benchmark-hardening work (stronger prompt controls, larger model families, broader drift-type coverage) would constitute a separate project.

## Referenced Artifacts

### Project-local source files
- `scripts/generate_schema_drift_corpus.py` — corpus generator
- `scripts/evaluate_schema_drift.py` — evaluation harness with deterministic and prediction-adapter scoring
- `scripts/collect_openai_predictions.py` — OpenAI-compatible prediction collector
- `tests/test_schema_drift_harness.py` — stdlib regression tests (3 tests)
- `README.md` — reproduction and interpretation documentation

### Data files
- `data/schema_drift_corpus.jsonl` — 2,000-example corpus (seed 3443677)
- `data/prediction_adapter_fixture.jsonl` — 100-example adapter validation fixture
- `data/phi4mini_drift_schema_t0_predictions_200.jsonl`
- `data/phi4mini_stable_schema_t0_predictions_200.jsonl`
- `data/qwen2_5_3b_drift_schema_t0_predictions_200.jsonl`
- `data/qwen2_5_3b_stable_schema_t0_predictions_200.jsonl`
- `data/qwen3_0_6b_drift_schema_t0_predictions_200.jsonl`
- `data/qwen3_0_6b_stable_schema_t0_predictions_200.jsonl`

### Report files
- `reports/corpus_summary.json` — drift-type counts
- `reports/evaluation_summary.json` — deterministic baseline evaluation
- `reports/prediction_adapter_evaluation.json` — adapter fixture evaluation
- `reports/local_endpoint_probe.json` — endpoint availability probe
- `reports/phi4mini_prompt_comparison_25.json` — 25-example smoke test
- `reports/local_phi4mini_run_summary.json` — smoke test summary
- `reports/live_model_drift_comparison_200.json` — two-model drift evaluation
- `reports/live_model_stable_comparison_200.json` — two-model stable evaluation
- `reports/live_model_rank_comparison_200.json` — two-model rank comparison
- `reports/live_model_drift_comparison_3models_200.json` — three-model drift evaluation
- `reports/live_model_stable_comparison_3models_200.json` — three-model stable evaluation
- `reports/live_model_rank_comparison_3models_200.json` — three-model rank comparison

### Decision and metadata files
- `.omx/project_decision.json` — project decision (finalize_positive)
- `.omx/metrics.json` — session metrics
- `run_notes.md` — full execution log
- `papers/.../claim_ledger.json` — audited claims and allowed/forbidden wording
- `papers/.../evidence_bundle.json` — structured evidence summary
