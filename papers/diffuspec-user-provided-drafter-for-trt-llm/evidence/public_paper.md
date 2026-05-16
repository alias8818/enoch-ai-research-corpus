# DiffuSpec: Feasibility of User-Provided Diffusion-Style Drafters for Speculative Decoding in TensorRT-LLM

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, evidence bundles, claim ledgers, and source code inspection). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

Speculative decoding accelerates autoregressive language model inference by drafting candidate token sequences verified in a single target-model forward pass. Diffusion-based drafting methods such as DFlash generate draft tokens via block-diffusion rather than left-to-right autoregression, potentially improving draft diversity and acceptance rates. This paper investigates whether NVIDIA's TensorRT-LLM can accommodate a user-provided diffusion-style drafter through its existing speculative decoding API. We conduct a static and contract-level feasibility study: we verify that the `UserProvidedDecodingConfig` API accepts arbitrary `Drafter` subclasses implementing `prepare_draft_tokens()`, and we demonstrate a minimal adapter that converts a diffusion-style lattice into the linear draft token sequence the framework expects. A smoke test with synthetic token IDs confirms the adapter produces well-formed output conforming to the `Drafter` interface contract. However, no end-to-end inference runs, throughput measurements, or acceptance-rate benchmarks were performed. The API integration path exists and is architecturally viable, but performance characteristics remain undetermined. We further observe that TensorRT-LLM already contains a native DFlash integration with hidden-state conditioning, which is likely preferable for hidden-state-dependent drafters. The claim ledger for this artifact recorded no structured claims, and the audit status is accordingly blocked; the findings here should be interpreted as preliminary feasibility evidence rather than validated performance claims.

## Introduction

Speculative decoding reduces the latency of autoregressive language model serving by proposing multiple candidate tokens per step and verifying them in a batched forward pass through the target model. The degree of speedup depends on the acceptance rate—the fraction of draft tokens that match the target model's distribution—and the cost of draft generation relative to the verification pass.

Conventional speculative decoding uses a smaller autoregressive model or n-gram methods as the drafter. More recently, diffusion-based approaches such as DFlash have been proposed, in which a block-diffusion model generates draft tokens in parallel rather than sequentially. DFlash supports integration with serving frameworks including vLLM and SGLang, and its draft models are publicly available. This raises the question of whether such non-autoregressive drafters can also be integrated into NVIDIA's TensorRT-LLM serving framework.

TensorRT-LLM supports multiple speculative decoding strategies, including Eagle3, MTP, PARD, n-gram, draft-target decoding, and a native DFlash integration. It also exposes a `UserProvidedDecodingConfig` that accepts an arbitrary Python object implementing the `Drafter` abstract base class. This paper asks: **Can a diffusion-style drafter be integrated into TensorRT-LLM via the user-provided drafter API, and what are the architectural constraints?**

We do not present performance results. Instead, we present a feasibility analysis grounded in API inspection, source code review, and a minimal contract smoke test. We identify the integration path, its constraints, and the format mismatch between the diffusion drafter's native output (a lattice or set of parallel token blocks) and the linear token sequence expected by the framework's speculative decoding loop.

## Method

### Environment

All work was conducted on the following platform:

| Component | Value |
|---|---|
| OS | Linux 6.17.0-1014-nvidia (aarch64), Ubuntu |
| GPU | NVIDIA GB10 |
| Driver | 580.159.03 |
| CUDA | 13.0 |
| Python | 3.12.3 |
| RAM | 121 GB (no swap configured) |
| GPU State | Idle: 0% utilization, 40°C, 11W |

### Source Acquisition

Two repositories were cloned:

1. **TensorRT-LLM** at commit `a753934d6445b32b7175a97eb32de06ee3319a94`, providing the speculative decoding framework, API definitions, and native drafter implementations.
2. **DFlash** at commit `ac132a654b155693bf8caefe8d8299fcbc05ba7b`, providing the reference diffusion-based drafter implementation and its vLLM/SGLang integration examples.

The DFlash clone produced a non-fatal warning (`fatal: 'README.md' is not a directory`), but the repository was checked out successfully.

### API Analysis

We inspected the TensorRT-LLM speculative decoding API by examining the following source files:

- **`tensorrt_llm/_torch/speculative/drafter.py`**: Defines the `Drafter` abstract base class with the `prepare_draft_tokens()` method contract. This is the interface that user-provided drafters must implement.
- **`tensorrt_llm/llmapi/llm_args.py`**: Defines `UserProvidedDecodingConfig`, a dataclass accepting a `drafter` field of type `object`, documented as a `Drafter` instance implementing `prepare_draft_tokens()`. The `max_draft_len` field specifies the number of drafter layers (i.e., the length of the linear draft sequence).
- **`tensorrt_llm/_torch/speculative/utils.py`**: Contains `get_spec_drafter()`, which returns `spec_config.drafter` directly when the configuration is a `UserProvidedDecodingConfig`, confirming the user's `Drafter` object is passed through to the decoding loop without framework-level transformation.
- **`tensorrt_llm/_torch/speculative/dflash.py`**: Contains the native DFlash integration with a dedicated `DFlashDecodingConfig`. This native path uses hidden-state conditioning via `prepare_1st_drafter_inputs()`, feeding target model hidden states into the drafter.
- **`tensorrt_llm/_torch/speculative/interface.py`**: Contains `is_external_drafter()` and related predicates that control code paths for user-provided drafters versus built-in strategies.
- **`tensorrt_llm/_torch/speculative/spec_tree_manager.py`**: Manages the speculative token tree, including auxiliary buffers (`tokens_gather_idx_for_drafter_model`, `spec_dec_packed_mask_for_drafter_model`, `hidden_states_read_indices_offset_for_drafter_model`) used by the drafter model's attention layers.

### Adapter Design

The core integration challenge is a format mismatch: diffusion-based drafters produce token candidates in a lattice or parallel-block structure, while TensorRT-LLM's speculative decoding loop (for the user-provided path) expects a linear left-to-right sequence of draft tokens. We designed a minimal adapter (`DiffuSpecUserDrafterAdapter`) that:

1. Accepts a diffusion drafter producing a lattice of candidate token sequences.
2. Selects a single path through the lattice (e.g., greedy or top-1 selection at each diffusion step).
3. Presents the selected path as a linear draft token sequence to the `prepare_draft_tokens()` interface.

This adapter is a proof-of-concept for the API contract. It is not optimized and makes no claim about the quality of the selected path relative to the full lattice.

### Validation Procedure

We performed two levels of validation:

1. **Static smoke test**: All adapter source files passed `py_compile` without errors, confirming syntactic validity.
2. **Contract smoke test**: The adapter was instantiated and `prepare_draft_tokens()` was called with synthetic inputs, verifying that the output conforms to the expected format—a list of draft token lists, one per sequence in the batch.

No full model loading, inference, or benchmarking was performed. The smoke test uses synthetic token IDs, not output from an actual language model or diffusion drafter.

## Results

### API Feasibility

The `UserProvidedDecodingConfig` in TensorRT-LLM directly supports user-provided drafters. The documented usage pattern is:

```python
speculative_config = UserProvidedDecodingConfig(
    max_draft_len=3, drafter=MyDrafter()
)
llm = LLM("/path/to/target_model", speculative_config=speculative_config)
```

The `Drafter` abstract base class requires implementation of `prepare_draft_tokens()`, which returns draft tokens for the current decoding step. The framework handles verification, acceptance, and KV-cache management internally.

The `get_spec_drafter()` utility function returns `spec_config.drafter` directly for user-provided configurations, confirming that the user's `Drafter` object is passed through to the decoding loop without framework-level transformation or validation beyond type checking in the configuration layer.

The `is_external_drafter()` predicate in `interface.py` is used throughout the codebase to gate code paths specific to user-provided drafters, including decisions about overlap scheduling, chain drafter usage, and attention metadata preparation. This indicates the user-provided drafter path is a supported and maintained feature, not an afterthought.

### Smoke Test Outcome

The contract smoke test produced:

```python
{'smoke': 'pass', 'drafts': [[12, 13, 14, 15], [21, 22, 23, 24]]}
```

This confirms that the adapter produces well-formed draft token lists: two sequences, each with four draft tokens, consistent with the `Drafter` interface contract. This is a toy result using synthetic token IDs. It validates the adapter's conformance to the API contract but provides no evidence about draft quality, acceptance rates, or end-to-end integration correctness.

### Native DFlash Integration

TensorRT-LLM already contains a native DFlash integration (`tensorrt_llm/_torch/speculative/dflash.py`) with a dedicated `DFlashDecodingConfig` exposed in the public API (`tensorrt_llm/llmapi/__init__.py`). This native path supports hidden-state conditioning from the target model via `prepare_1st_drafter_inputs()`, which feeds target model hidden states into the drafter's first layer. This enables higher-quality drafts than token-only conditioning, since the drafter can leverage the target model's internal representations rather than only the sampled token sequence.

The user-provided `Drafter.prepare_draft_tokens()` interface does not expose target model hidden states to the drafter. This is a fundamental architectural limitation of the user-provided path for any drafter that benefits from hidden-state conditioning.

### Claim Audit Status

The claim ledger for this artifact recorded zero structured claims, and its audit status is `blocked_empty_claims`. The ledger's own limitations note states: "This artifact must not pass strict claim/evidence audit until claims reference public evidence files." Accordingly, the findings in this paper should be treated as preliminary feasibility observations rather than audited, evidence-backed claims.

### Summary of Validated and Unvalidated Items

| Item | Status |
|---|---|
| TensorRT-LLM supports user-provided drafters via `UserProvidedDecodingConfig` | Validated (API inspection + smoke test) |
| A diffusion lattice can be converted to a linear draft token sequence at the API level | Validated (adapter smoke test with synthetic data) |
| The adapter integrates correctly with a live TensorRT-LLM inference pipeline | Not tested |
| DiffuSpec improves throughput over non-speculative decoding | Not tested |
| DiffuSpec achieves competitive acceptance rates vs. autoregressive drafters | Not tested |
| Hidden-state-conditioned DFlash drafters should use native integration | Inferred from API structure; not empirically validated |

## Limitations

1. **No end-to-end inference validation.** The smoke test verifies the API contract with synthetic data but does not confirm that the adapter functions correctly within a live TensorRT-LLM inference loop. Integration issues—such as tensor device placement, batch size handling, KV-cache alignment, and dtype compatibility—may arise in practice and are not addressed by this study.

2. **No performance measurements.** We report no throughput (tokens/second), acceptance rate, or wall-clock latency numbers. The feasibility of the API path does not imply that the resulting system is fast. The overhead of lattice-to-sequence conversion, the suboptimality of selecting a single path from a diffusion lattice, and the lack of hidden-state conditioning in the user-provided path may all degrade performance relative to native speculative decoding methods. Any performance claims would require benchmarking that was not conducted.

3. **Lattice-to-linear conversion is lossy.** A diffusion drafter's potential advantage lies in its ability to propose multiple candidate token blocks in parallel. Converting this to a single linear sequence discards the lattice structure and may reduce acceptance rates compared to tree-structured verification (as used by Eagle3's dynamic tree mode). The `UserProvidedDecodingConfig` supports a `max_draft_len` parameter for linear drafting but does not natively expose tree-structured draft verification to user-provided drafters. Whether this loss is acceptable in practice is an empirical question we do not answer.

4. **Hidden-state conditioning is unavailable via the user-provided path.** The `Drafter.prepare_draft_tokens()` interface provides token-level context but does not pass target model hidden states. Drafters that benefit from hidden-state conditioning (e.g., DFlash, Eagle) will likely perform better through their dedicated native integrations (`DFlashDecodingConfig`, `Eagle3DecodingConfig`) than through the generic user-provided path. This is an architectural inference from the API structure, not an empirically validated claim.

5. **Single hardware configuration.** All tests were run on an NVIDIA GB10 (aarch64) with CUDA 13.0. Results may differ on other GPU architectures, in multi-GPU configurations, or under different driver versions.

6. **No comparison to native DFlash integration.** We did not benchmark the user-provided adapter path against TensorRT-LLM's native DFlash integration, so we cannot quantify any performance gap. The native path may be strictly superior for DFlash-type drafters.

7. **Empty claim ledger.** The automated claim audit recorded no structured claims for this artifact, and the audit status is blocked. This paper therefore does not meet the standard for evidence-backed claim validation, and its findings should be treated accordingly.

## Reproducibility Checklist

- [x] Source code for the adapter is available at `scripts/diffuspec_user_drafter_adapter.py`
- [x] TensorRT-LLM commit hash recorded: `a753934d6445b32b7175a97eb32de06ee3319a94`
- [x] DFlash commit hash recorded: `ac132a654b155693bf8caefe8d8299fcbc05ba7b`
- [x] Hardware and software environment fully specified (GPU model, driver, CUDA, OS, Python, RAM)
- [x] Smoke test command and output recorded verbatim in run notes
- [x] All validated and unvalidated items explicitly enumerated
- [ ] Full inference benchmark scripts provided (not available; benchmarks not performed)
- [ ] Random seeds specified for reproducible benchmark runs (not applicable; no benchmarks)
- [ ] Acceptance rate and throughput metrics reported with confidence intervals (not available)
- [ ] Claim ledger contains audit-approved claims (empty; audit status: blocked)

## Conclusion

TensorRT-LLM's `UserProvidedDecodingConfig` provides a viable API path for integrating diffusion-style speculative drafters. A minimal adapter can convert a diffusion lattice into the linear draft token sequence expected by the framework, and a contract smoke test with synthetic token IDs confirms the interface is satisfiable. However, this feasibility result is narrow: no end-to-end inference runs, throughput measurements, or acceptance-rate benchmarks were performed, and the claim ledger for this artifact is empty and audit-blocked.

The user-provided path has a fundamental architectural limitation: it does not expose target model hidden states to the drafter. This constrains draft quality for conditionally-generated drafters such as DFlash. We recommend two distinct integration strategies depending on the drafter type:

1. **Token-only drafters** (e.g., n-gram-like or unconditional diffusion drafters): The `UserProvidedDecodingConfig` path with a lattice-to-linear adapter is architecturally feasible. Performance impact is unknown and requires benchmarking.

2. **Hidden-state-conditioned drafters** (e.g., DFlash): TensorRT-LLM's native `DFlashDecodingConfig` integration is likely preferable, as it provides access to target model hidden states and avoids the lossy lattice-to-linear conversion. This recommendation is based on API structure analysis, not empirical comparison.

The critical next step is to select a concrete target model and drafter pair, run baseline (non-speculative) and speculative inference on the GB10 platform, and measure tokens/second and acceptance length. Only with these measurements can the practical value of the DiffuSpec approach be assessed. Until such evidence is produced and subjected to claim audit, the findings here remain at the level of API feasibility, not validated performance.

---

## Referenced Artifacts

| Artifact | Location | Description |
|---|---|---|
| Run notes | `run_notes.md` | Full session log with environment, source acquisition, smoke test output |
| Project decision | `.omx/project_decision.json` | Feasibility decision with confidence levels and validated/unvalidated items |
| Session metrics | `.omx/metrics.json` | Turn counts and token usage for the research session |
| Claim ledger | `papers/.../claim_ledger.json` | Empty claims; audit status: `blocked_empty_claims` |
| Evidence bundle | `papers/.../evidence_bundle.json` | Source, project, and run identifiers |
| Paper manifest | `papers/.../paper_manifest.json` | Generation metadata and writer provider info |
| Adapter script | `scripts/diffuspec_user_drafter_adapter.py` | Minimal DiffuSpec-to-TRT-LLM Drafter adapter implementation |
| Research result | `research_result.md` | Detailed research findings (referenced by project decision) |
| TensorRT-LLM source | `external/TensorRT-LLM` at `a753934d` | Framework source with speculative decoding API |
| DFlash source | `external/dflash` at `ac132a65` | Reference diffusion drafter implementation |
