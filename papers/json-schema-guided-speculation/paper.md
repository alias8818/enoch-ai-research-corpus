# JSON-Schema Guided Speculation: Character-Level Upper-Bound Analysis of Deterministic Span Elision for Structured-Output Decoding

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, evidence bundles, claim ledgers, benchmark outputs, and decision records). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

Structured JSON outputs from large language models contain a fraction of schema-implied syntax—property names, punctuation, and fixed literals—that is fully determined by the active JSON Schema and requires no model inference. We investigate whether a decoder can exploit this determinism to skip or speculatively batch guaranteed-accept tokens, reducing the number of target-model forward passes. We compile a practical subset of JSON Schema into canonical JSON emissions annotated as schema-forced versus model-choice spans, and measure the forced-character fraction across six schema archetypes (1,000 samples each) using a dependency-free, character-level prototype. The forced fraction ranges from 0.783 (rigid tool-call schema, upper-bound elision speedup 4.63×) to 0.035 (mostly free-text schema, upper-bound speedup 1.04×), with an overall mean forced fraction of 0.453. A speculative-decoding proxy with verification window γ = 16 yields estimated speedups from 2.43× (rigid) to 1.02× (free-text). These results are character-level upper bounds from a toy simulation; real speedups will be lower due to tokenizer merge effects, grammar-state overhead, and engine integration costs. The approach appears viable as a narrow systems optimization for rigid structured-output schemas but offers negligible benefit for schemas dominated by unconstrained natural-language fields.

## Introduction

Constrained decoding ensures that language model outputs conform to a specified grammar or schema, typically by masking the token distribution at each step to exclude invalid continuations. This guarantee comes at a cost: every token position, even those where the grammar uniquely determines the next token, still requires a full forward pass through the target model.

Speculative decoding accelerates autoregressive inference by having a lightweight draft model propose token sequences that the target model verifies in parallel. When the draft is accepted, multiple tokens are emitted per target forward pass. However, speculative decoding typically relies on a separate draft model and does not exploit structural knowledge from the output schema itself.

We observe that for many structured-output workloads—particularly function calls, classification records, and extraction schemas—a substantial fraction of the output is not merely constrained but *determined* by the schema. Property names, colons, commas, braces, and constant values follow from the schema grammar state alone. If the decoder can identify these uniquely determined positions, it can accept them without consulting the target model, or batch them as guaranteed-accept drafts within a speculative verification window.

This paper asks: **what fraction of structured JSON output characters are schema-determined, and how does this fraction vary across schema archetypes?** We answer this with a character-level prototype that compiles JSON Schema into forced-span annotations, providing upper-bound estimates for the potential speedup from schema-guided speculation or token elision. We stress that these are opportunity-size measurements, not realized wall-clock speedups.

## Method

### Schema Compilation

We implement a dependency-free prototype (`schema_guided_speculation.py`) that compiles a practical subset of JSON Schema into a canonical JSON emission model. The supported schema features are:

- **Objects**: required properties with ordered keys, optional properties
- **Arrays**: items with min/max items constraints, including fixed-length arrays
- **Primitives**: `string`, `number`, `integer`, `boolean`
- **Constants**: `const` and `enum` with a single value

The compiler produces a sequence of emission events, each annotated as either **schema-forced** (the next character is uniquely determined by the grammar state) or **model-choice** (the model must select among multiple valid continuations).

### Forced-Span Annotation

For each emission event, the prototype determines whether the grammar state admits exactly one valid continuation. If so, the character is marked forced; otherwise, it is marked as a model-choice point. This classification is exact at the character level for the supported schema subset.

### Schema Archetypes

We define six schema archetypes spanning a range of structural rigidity:

| Archetype | Description |
|---|---|
| `rigid_tool_call` | Function call with fixed property names, enum-typed method, short string arguments |
| `classification_record` | Record with several enum/const fields and a few free-text fields |
| `invoice_extraction` | Extraction of structured invoice data with numeric fields and short strings |
| `ui_tree_shallow` | Shallow UI component tree with typed nodes and text content |
| `reasoning_answer` | Chain-of-thought reasoning with a long free-text field and a short typed answer |
| `mostly_free_text` | Document with minimal structure and a large unconstrained text body |

### Metrics

For each archetype, we generate 1,000 random valid JSON instances conforming to the schema and compute:

- **Mean characters**: average output length in characters.
- **Forced fraction**: fraction of characters that are schema-determined.
- **Elide upper speedup**: theoretical maximum speedup if all forced characters are accepted without target-model invocation, computed as `1 / (1 − forced_fraction)`.
- **γ = 16 verify proxy**: estimated speedup under speculative decoding with a verification window of 16 tokens, where forced spans are batched as guaranteed-accept drafts. This partially accounts for the overhead of verification passes and partial acceptance.

The elide upper speedup is a character-level proxy that assumes forced characters map one-to-one to tokens and that elision has zero overhead. The γ = 16 proxy partially accounts for batching overhead but remains a character-level approximation. Both are upper bounds.

### Validation

All metrics were validated with a separate validation script (`validate_metrics.py`) that checks JSON parseability, schema conformance, and metric consistency. The prototype and validation script both pass Python compilation checks.

### Experimental Classification

The prototype is a **toy simulation**: it measures the opportunity for token elision at the character level without running an actual LLM target model. It is not a llama.cpp hook prototype, not a CUDA copy calibration, and not a final production validation. The results characterize the *size* of the deterministic-span opportunity, not the *realized* speedup from any particular implementation.

## Results

### Forced-Fraction and Speedup Estimates

| Schema Archetype | Mean Chars | Forced Fraction | Elide Upper Speedup | γ = 16 Verify Proxy |
|---|---:|---:|---:|---:|
| `rigid_tool_call` | 86.8 | 0.783 | 4.63× | 2.43× |
| `classification_record` | 82.2 | 0.682 | 3.15× | 2.05× |
| `invoice_extraction` | 186.0 | 0.629 | 2.70× | 1.58× |
| `ui_tree_shallow` | 156.3 | 0.467 | 1.88× | 1.34× |
| `reasoning_answer` | 232.0 | 0.121 | 1.14× | 1.08× |
| `mostly_free_text` | 995.0 | 0.035 | 1.04× | 1.02× |

Across all archetypes, the overall mean forced fraction is 0.453, yielding an overall mean elide upper speedup of 2.42×.

### Key Observations

**Rigid schemas show substantial forced fractions.** The `rigid_tool_call` archetype, dominated by fixed property names, punctuation, and single-value enums, has 78.3% of its characters schema-determined. Even under the more conservative γ = 16 proxy, the estimated speedup is 2.43×.

**Speedup degrades sharply as free-text content increases.** The `reasoning_answer` archetype (12.1% forced) and `mostly_free_text` archetype (3.5% forced) show negligible speedup potential. Schema-guided speculation provides essentially no benefit when the output is dominated by unconstrained natural language.

**The gap between elide upper bound and γ = 16 proxy is significant.** For the `rigid_tool_call` archetype, the elide upper bound is 4.63× but the γ = 16 proxy is only 2.43×. This gap reflects the cost of verification passes and the fact that not all forced spans can be batched into a single verification window. Real implementations will likely fall below even the γ = 16 proxy due to tokenizer effects and integration overhead.

**The opportunity is concentrated in syntax, not semantics.** Inspection of the forced spans reveals that the majority of forced characters come from JSON syntax (`{`, `}`, `:`, `,`, `[`, `]`), required property names, and `const`/single-value `enum` literals. Model-choice points occur primarily at string content, numeric values, and multi-value enums.

**The overall mean is misleading.** The overall mean forced fraction of 0.453 averages across archetypes with very different characteristics. In practice, the applicability of schema-guided speculation depends entirely on the specific schema in use. For the two most rigid archetypes, the opportunity is material; for the two least rigid, it is negligible.

## Limitations

1. **Character-level proxy, not tokenizer-level.** The prototype operates at the character level and does not account for tokenizer merge behavior. A multi-character forced span (e.g., `"property_name":`) may tokenize into a single token or span multiple tokens depending on the tokenizer. If a forced character sequence crosses a token boundary in a way that merges with a model-choice token, the elision opportunity may be smaller or larger than the character-level estimate. Real speedup requires tokenizer-aware analysis.

2. **No target model integration.** The prototype does not run an actual LLM. It measures the *opportunity* for token elision, not the *realized* speedup. Integration with an inference engine (llama.cpp, vLLM/XGrammar, SGLang) is necessary to measure actual wall-clock improvement. No llama.cpp hook-prototype, CUDA copy calibration, or production validation results exist for this project.

3. **Grammar-state overhead not measured.** Maintaining and advancing the JSON Schema grammar state at each decode step incurs computational cost. For schemas with deep nesting or many properties, this overhead may partially offset the savings from token elision.

4. **Limited JSON Schema coverage.** The prototype supports a practical subset of JSON Schema: objects, arrays, strings, numbers, booleans, `const`, `enum`, and fixed-length arrays. Unsupported features include `$ref`/`$defs`, `patternProperties`, `additionalProperties`, `oneOf`/`anyOf`/`allOf`, `if`/`then`/`else`, and `pattern`-constrained strings. Extending coverage would change forced fractions, potentially in either direction.

5. **Random sampling may not reflect real distributions.** The 1,000 samples per archetype are generated from uniform random distributions over valid values. Real-world workloads may have different string-length distributions, different nesting depths, or different field usage patterns that alter the forced fraction.

6. **KV cache and batching effects not modeled.** In production inference, token elision changes the KV cache access pattern and may interact with continuous batching. These effects are not captured by the character-level proxy.

7. **γ = 16 proxy is an approximation.** The speculative verification proxy assumes a fixed window size and perfect acceptance of forced spans within the window. Real speculative decoding has variable acceptance rates and overheads not captured here.

8. **No random seed control.** The prototype uses Python's default random module without specifying a seed. Exact numerical reproducibility of individual samples is not guaranteed, though the aggregate statistics are expected to be stable at 1,000 samples per archetype.

9. **Claim audit status is blocked.** The project's claim ledger records zero structured claims and an audit status of `blocked_empty_claims`. The metrics and observations reported here have not passed a formal claim/evidence audit.

## Reproducibility Checklist

| Item | Status |
|---|---|
| Prototype source available | Yes: `src/schema_guided_speculation.py` (dependency-free Python) |
| Validation script available | Yes: `scripts/validate_metrics.py` |
| Benchmark command documented | Yes: `python3 src/schema_guided_speculation.py --samples 1000 --out results/schema_guided_speculation_metrics.json` |
| Validation command documented | Yes: `python3 scripts/validate_metrics.py results/schema_guided_speculation_metrics.json` |
| Compilation check passed | Yes: both scripts pass `py_compile` |
| Random seed specified | No: uses Python default random; exact reproducibility not guaranteed |
| Output artifacts preserved | Yes: `results/schema_guided_speculation_metrics.json`, benchmark and validation logs |
| Hardware requirements | None for the character-level prototype: standard Python 3, no GPU |
| External dependencies | None for the prototype |
| Claim/evidence audit passed | No: claim ledger is `blocked_empty_claims` with zero claims |

## Conclusion

JSON Schema can guide speculation or target-step elision for deterministic structured-output spans, but the opportunity is highly schema-dependent and the results reported here are character-level upper bounds, not realized speedups. For rigid schemas such as tool/function calls, where 78% of output characters are schema-determined, the character-level upper bound on speedup is 4.63× (2.43× under a speculative verification proxy). For schemas dominated by free-text fields, the opportunity is negligible (≤4% forced fraction, ≤1.04× speedup).

The strongest implementation path is tokenizer-aware singleton-token elision inside an existing constrained decoder, with speculative verification windows as a fallback for deterministic spans longer than one token. The character-level results reported here are upper-bound proxies from a toy simulation; real speedups will be lower and must be measured through integration with a model tokenizer and an inference engine. We assess the approach as viable but narrow—applicable primarily to rigid structured-output workloads—and recommend next steps focus on llama.cpp grammar or vLLM/XGrammar integration with local small LLMs on rigid tool-call schemas, with careful measurement of grammar-state overhead and tokenizer merge effects.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Prototype source | `src/schema_guided_speculation.py` |
| Validation script | `scripts/validate_metrics.py` |
| Metrics output | `results/schema_guided_speculation_metrics.json` |
| Literature notes | `results/literature_notes.md` |
| Benchmark log | `logs/benchmark_1000.log` |
| Summary log | `logs/summary_1000.log` |
| Validation log | `logs/validate_metrics.log` |
| Compile log | `logs/py_compile.log` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260429T151648285254+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T151648285254+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T151648285254+0000/paper_manifest.json` |
