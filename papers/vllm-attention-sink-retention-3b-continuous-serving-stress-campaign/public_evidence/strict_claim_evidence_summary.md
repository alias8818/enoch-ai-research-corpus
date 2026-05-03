# Public strict claim/evidence surrogate

Artifact: `vllm-attention-sink-retention-3b-continuous-serving-stress-campaign`

This file is derived only from public repository-local files: `paper.md` and `evidence_bundle.json`.
It does not recreate or assert possession of the raw result JSON/log/archive files named by the original generated evidence bundle.

Strict audit meaning: traceability only. It is not peer review, scientific correctness, independent replication, statistical power, semantic output quality, or human-written status.

Original raw result refs not present in this public corpus: 20.

## Claims traced

### vllm-sink-001

The calibrated OpenAI-compatible continuous-serving sweep used a patched vLLM 0.19.1 install serving Qwen/Qwen2.5-3B-Instruct with float16, max_model_len=1024, max_num_batched_tokens=4096, max_num_seqs=16, and gpu_memory_utilization=0.50.

Evidence summary: The public evidence bundle run-notes tail records the server configuration and retention policy used for the calibrated sweep.

Not validated: environment_recreation, vLLM patch correctness, model cache integrity.

### vllm-sink-002

Across the four calibrated paired baseline/retention trials, the public bundle reports zero request errors and no retention p95 latency regression over the 10% kill gate; the worst reported p95 delta is +0.30%.

Evidence summary: The run-notes tail lists p95 deltas for n96/c8/out64 trials 1-2, n128/c16/out64, and n256/c16/out128, and states that no calibrated pair triggered the kill gate.

Not validated: statistical_power, independent_replication, scientific_correctness.

### vllm-sink-003

The same public evidence reports non-zero output preview differences in all calibrated pairs: 2/96, 3/96, 7/128, and 17/256, so this artifact does not establish semantic equivalence.

Evidence summary: The run-notes tail explicitly cautions that output preview differences were low but non-zero and that only output previews, not full semantic grading, were compared.

Not validated: semantic_output_quality, human_evaluation, full_output_equivalence.

### vllm-sink-004

The public evidence reports high GPU utilization during calibrated load (90-96% mean, 96% peak), engine RSS around 2.34-2.42 GB, and MemAvailable roughly 54.6-55.6 GB after warmup.

Evidence summary: These resource ranges are stated in the public run-notes tail and repeated in the paper resource-utilization subsection.

Not validated: hardware_generalization, long-duration_memory_leak_behavior.

### vllm-sink-005

The project decision in the public bundle is finalize_positive with hypothesis_status supported, confidence medium, and evidence_strength strong for the latency kill-gate dimension.

Evidence summary: The evidence bundle decision and status_json.project_decision fields carry the same decision/status/confidence/evidence-strength values and a stop reason tied to the latency kill gate.

Not validated: peer_review, external_acceptance, scientific_correctness.
