```markdown
# Non-Uniform MoE Checkpoint Loading for REAP-Compressed Models: A Preflight Integration Prototype

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We present a prototype integration for loading non-uniform (ragged) Mixture-of-Experts checkpoints produced by REAP (Resource-Efficient Architecture Pruning) compression. The prototype—comprising a manifest parser, a topology mutator, and a preflight planner—can infer per-layer expert counts from Hugging Face safetensors index metadata, classify architecture support conservatively, and emit safe configuration overrides for pre-load model topology mutation. In a sweep of 30 publicly available Cerebras REAP checkpoints, 17 were classified as supported (ModuleList-style MoE architectures) and 13 were conservatively rejected (fused or unrecognized expert tensor layouts). Critically, all 30 public checkpoints proved to be uniform by layer (ragged: false), meaning no truly non-uniform checkpoint was available for end-to-end validation. The loader feasibility hypothesis is therefore only partially supported: metadata-driven load planning works for supported architectures, but end-to-end loading of a genuinely ragged checkpoint remains inconclusive rather than falsified.

## 1. Introduction

REAP (Resource-Efficient Architecture Pruning) is a compression method that prunes individual experts from Mixture-of-Experts (MoE) language models, potentially producing checkpoints where different transformer layers retain different numbers of experts. We refer to such checkpoints as *ragged* or *non-uniform*, in contrast to *uniform* checkpoints where every MoE layer has the same expert count.

Standard Hugging Face model loading assumes a fixed expert count per layer, typically read from a single `num_experts` field in `config.json`. When a REAP-compressed model has been pruned non-uniformly, this single-scalar configuration is insufficient: the model's `ModuleList` sizes and router `Linear` heads must be resized on a per-layer basis before the state dict can be loaded without shape mismatches.

This work addresses the question: *can a loader be built that consumes real REAP checkpoint metadata, infers per-layer expert counts, and prepares a compatible model topology for weight loading?* We report on a prototype implementation and its evaluation against all 30 publicly available Cerebras REAP checkpoints on Hugging Face.

## 2. Method

### 2.1 Manifest Inference

The `manifest.py` module infers per-layer expert IDs and counts from Hugging Face state-dict key patterns without downloading weight shards. Given a `model.safetensors.index.json`, it parses tensor keys of the form `model.layers.N.mlp.experts.E.*` to extract the set of expert indices present at each layer. This produces a per-layer expert count map suitable for topology mutation.

### 2.2 Topology Mutation

The `topology.py` module mutates a `ModuleList`-based Hugging Face MoE model instance to match per-layer expert counts. For each MoE layer, it:

1. Truncates the expert `ModuleList` to the target count.
2. Resizes the router `Linear` head (output dimension) to match the new expert count.

This mutation must occur before `load_state_dict` is called, so that the model's parameter shapes align with the checkpoint's tensor shapes.

### 2.3 Preflight Planner

The `integration.py` module is a real-checkpoint preflight planner that:

1. Reads `config.json` and `model.safetensors.index.json` from a local Hugging Face snapshot.
2. Infers per-layer expert counts from actual checkpoint keys.
3. Classifies architecture support conservatively—only known ModuleList-style MoE architectures (Qwen, GLM-style) are marked as supported.
4. Verifies that expert IDs are contiguous and zero-based.
5. Emits safe configuration overrides (`num_experts=max`, plus `ragged_expert_counts`) for pre-load topology mutation.

Architectures with fused expert tensors or unrecognized expert tensor layouts are explicitly rejected rather than loaded unsafely.

### 2.4 Conservative Rejection Policy

Fused expert tensor architectures (where expert weights are concatenated into a single tensor rather than stored as separate `ModuleList` entries) are intentionally rejected. Correct loading of such architectures requires architecture-specific slicing logic that was not implemented in this prototype. This is a deliberate safety choice: failing loudly on an unsupported architecture is preferable to silently loading misaligned weights.

## 3. Results

### 3.1 Unit Tests

Four unit tests were executed covering manifest key inference, HF index manifest loading, supported ragged Qwen-style metadata, and conservative fused-architecture rejection. All four passed.

### 3.2 Topology Smoke Test

A topology smoke test was run against a small Qwen-like PyTorch stand-in model using a CUDA PyTorch 2.11.0 environment. The test verified that `ModuleList` truncation and router `Linear` resizing produce a model whose parameter shapes match the expected ragged configuration. Result: passed.

### 3.3 Real Checkpoint Preflight

A preflight analysis was executed on the public checkpoint `cerebras-Qwen3-Coder-REAP-25B-A3B`. The output artifact (`qwen3_25b_preflight.json`) recorded:

- **supported**: true
- **architecture**: `Qwen3MoeForCausalLM`
- **model_type**: `qwen3_moe`
- **expert layers**: 48
- **experts per layer**: 103
- **contiguous expert IDs**: true
- **ragged**: false

This confirms the preflight planner can successfully parse and classify a real public REAP checkpoint, although this particular checkpoint is uniform.

### 3.4 Collection Sweep

A compact sweep over all 30 public REAP metadata snapshots produced the following summary:

| Metric | Count |
|---|---|
| Checkpoints checked | 30 |
| Supported architectures | 17 |
| Unsupported architectures | 13 |
| Ragged (non-uniform) checkpoints | 0 |

The 13 unsupported entries included architectures with no recognized expert tensors: DeepseekV3, DeepseekV3.2, GLM lite, Kimi Linear, MiniMax M2, and Step3.5. These were conservatively rejected rather than guessed.

### 3.5 Negative Finding: Absence of Ragged Checkpoints

The central negative result is that all 30 publicly available Cerebras REAP checkpoints are uniform by layer. No truly ragged (non-uniform) checkpoint exists in the current public collection. This means the core use case—loading a checkpoint where different layers have different expert counts—could not be validated end-to-end against a real ragged checkpoint. The loader's behavior on genuinely ragged data remains inconclusive.

## 4. Limitations

1. **No ragged checkpoint available for validation.** The absence of any public non-uniform REAP checkpoint means end-to-end loading of a ragged checkpoint is untested. The prototype's topology mutation logic is verified only against synthetic/stand-in models and uniform real checkpoints.

2. **Fused architectures unsupported.** Models that store expert weights as fused tensors (rather than separate `ModuleList` entries) are conservatively rejected. This includes several major architectures present in the public REAP collection (DeepseekV3/V3.2, MiniMax M2, Step3.5, among others).

3. **Metadata-only validation.** The preflight planner operates on `config.json` and `model.safetensors.index.json` metadata. Full weight shard downloading and actual `load_state_dict` execution against a ragged topology-mutated model were not performed.

4. **Contiguous zero-based expert ID assumption.** The prototype assumes expert IDs are contiguous and zero-based within each layer. If a future ragged checkpoint uses sparse or non-zero-based expert IDs, additional remapping logic would be required.

5. **Single upstream source.** The REAP implementation and checkpoints are from CerebrasResearch only. Generalization to other MoE compression methods or checkpoint formats is not addressed.

6. **No inference quality evaluation.** Even if a ragged checkpoint were successfully loaded, this work does not evaluate whether the loaded model produces correct inference outputs. Shape compatibility does not guarantee semantic correctness.

## 5. Reproducibility Checklist

- **Source code**: Prototype implementation in `ragged_moe_loader/` (`manifest.py`, `topology.py`, `integration.py`, `__init__.py`, `__main__.py`).
- **Test suite**: `tests/test_manifest.py`, `tests/test_integration.py` (4 tests, all passing).
- **Verification scripts**: `scripts/verify_topology.py`, `scripts/verify_real_checkpoint_integration.py`, `scripts/probe_reap_collection.py`.
- **Upstream source**: `external/reap/` cloned from `https://github.com/CerebrasResearch/reap`.
- **HF probe data**: `hf_probe/reap_collection_summary.json` and per-model metadata directories.
- **Result artifacts**: `artifacts/real_checkpoint_integration/reap_collection_preflight_compact.json`, `artifacts/real_checkpoint_integration/qwen3_25b_preflight.json`.
- **Python environment**: `uv venv --python /usr/bin/python3 .venv` with `pytest` and `safetensors` installed; topology smoke test used sibling CUDA PyTorch 2.11.0 environment.
- **Execution commands**:
  - `.venv/bin/python -m pytest -q tests` → 4 passed
  - `scripts/verify_topology.py` → topology smoke test passed
  - `scripts/verify_real_checkpoint_integration.py hf_probe/cerebras-Qwen3-Coder-REAP-25B-A3B --out artifacts/real_checkpoint_integration/qwen3_25b_preflight.json` → exit 0, supported=true

## 6. Conclusion

We have implemented and evaluated a prototype non-uniform MoE checkpoint loader for REAP-compressed models. The prototype successfully parses real Hugging Face checkpoint metadata, classifies architecture support, and produces load plans for 17 of 30 public REAP checkpoints. However, the critical validation—loading a genuinely ragged checkpoint—could not be performed because no such checkpoint exists in the current public REAP collection (0 of 30 are ragged). The hypothesis that a ragged loader is feasible for ModuleList-style MoE architectures is partially supported at the prototype level, but end-to-end validation remains inconclusive.

The project decision is `finalize_positive` with hypothesis status `mixed` and confidence `medium`. The recommended next action is to use the preflight integration path when a true non-uniform REAP checkpoint becomes available, or to explicitly target one of the currently unsupported fused architectures in a separate topology-mapping effort.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim audit | `papers/.../claim_audit.json` |
| Evidence bundle | `papers/.../evidence_bundle.json` |
| Collection preflight sweep | `artifacts/real_checkpoint_integration/reap_collection_preflight_compact.json` |
| Qwen3 25B preflight | `artifacts/real_checkpoint_integration/qwen3_25b_preflight.json` |
| HF collection summary | `hf_probe/reap_collection_summary.json` |
| Manifest module | `ragged_moe_loader/manifest.py` |
| Topology module | `ragged_moe_loader/topology.py` |
| Integration module | `ragged_moe_loader/integration.py` |
| Integration tests | `tests/test_integration.py` |
| Manifest tests | `tests/test_manifest.py` |
| Topology verification script | `scripts/verify_topology.py` |
| Real checkpoint verification script | `scripts/verify_real_checkpoint_integration.py` |
| Collection probe script | `scripts/probe_reap_collection.py` |
```
