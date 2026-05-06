# Strict claim/evidence audit

Strict claim/evidence passed: 2 / 495

This audit is separate from the packaging/provenance lint. It requires non-empty claim ledgers with evidence references and public result-file references, or explicit unavailability metadata.

Status: `blocked_audit_gaps`

## Summary

- Empty claim ledgers: 373 / 495
- Evidence `result_files` references: 2868
- Publicly present result-file references: 18
- Missing result-file references: 2830
- Featured artifacts strict-pass count: 2 / 2

## Validated

- `claim_ledger_schema_parseable`
- `claims_non_empty`
- `claims_reference_evidence`
- `evidence_result_file_refs_public_or_declared_unavailable`

## Not validated

- `scientific_correctness`
- `peer_review`
- `independent_replication`
- `statistical_power`
- `semantic_output_quality`
- `citation_accuracy`

## Rows

| Paper | Strict pass | Claim count | Missing result refs | Issues |
|---|---:|---:|---:|---|
| `acceptance-length-cuda-graph-bank` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `adapter-projected-galore-192-step-decoupled-refresh-mmlu-eval` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `adapter-projected-galore-192-step-decoupled-refresh-mmlu-eval-9a62dd9416` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `adaptive-boundary-colorization-gate` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `adaptive-boundary-colorization-gate-3b59f6774f` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `adaptive-budget-aware-lim-reserve-sampler` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `adaptive-budget-aware-lim-reserve-sampler-2ddbf25384` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `adaptive-claim-first-top-k-router` | False | 0 | 7 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `adaptive-claim-first-top-k-router-d0dc50a98c` | False | 2 | 7 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `adaptive-evidence-packer-rag-integration` | False | 0 | 13 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `adaptive-evidence-packer-rag-integration-2a4e77b31a` | False | 2 | 13 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `adaptive-landmark-reweighter` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `adaptive-prefix-splitter-inference-integration` | False | 0 | 3 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `adaptive-prefix-splitter-inference-integration-6d161ce689` | False | 2 | 3 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `adversarial-channel-router` | False | 0 | 6 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `adversarial-channel-router-e74eea0518` | False | 2 | 6 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `agent-app-store-with-repro-sandboxes` | False | 0 | 1 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `agent-app-store-with-repro-sandboxes-5f40c40e86` | False | 2 | 1 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `agent-budget-parliament` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `agent-identity-rotation` | False | 0 | 7 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `agent-identity-rotation-85bfb941f9` | False | 2 | 7 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `agent-runner-black-box-integration-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `agentic-benchmark-autogenerator` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `agents.md-linter-task-lift-validation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `answer-shape-prompt-planner` | False | 0 | 10 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `answer-shape-prompt-planner-ba167182f1` | False | 2 | 10 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `anti-collapse-expert-immune-system` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `anti-encyclopedia-curriculum` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `applicability-gated-abstention-calibration-policy` | False | 0 | 15 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `applicability-gated-abstention-calibration-policy-52021fb1e7` | False | 2 | 15 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `aret-hierarchical-multi-virtue-reward-architecture-for-rl` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `aret-hierarchical-multi-virtue-reward-architecture-for-rl-cc711c3474` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `asymmetric-k-v-adapter-training` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `async-selective-kv-lease-backend-prototype` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `attention-budget-controller` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `attention-loss-shadow-estimator` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `attention-loss-shadow-estimator-448f1cdd17` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `attention-mlp-joint-pruner` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `attention-sink-preserving-prune` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `attention-sink-rescue-pool` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `audio-room-measurement-planner` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `autonomous-project-manager-kernel` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `backend-switched-verifier-pretraining` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `batched-reader-qets-mixed-domain-scaling-validation` | False | 0 | 14 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `batched-reader-qets-mixed-domain-scaling-validation-1e48547905` | False | 2 | 14 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `batched-vllm-speculation-cost-governor-integration` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `batched-vllm-speculation-cost-governor-integration-6f2deec9e5` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `benchmark-explorer-agent` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `benchmark-health-ledger` | False | 0 | 4 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `benchmark-health-ledger-e3e46df81f` | False | 2 | 4 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `benchmark-qwen3-non-uniform-reap-manual-fp8-scoring` | False | 0 | 18 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `benchmark-qwen3-non-uniform-reap-manual-fp8-scoring-3b0b701050` | False | 2 | 18 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `benchmark-qwen3-non-uniform-reap-manual-fp8-scoring-433ea5b89a` | False | 2 | 18 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `benchmark-qwen3-non-uniform-reap-manual-fp8-scoring-b7a5f924e4` | False | 0 | 18 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `bfi-dflash-bonus-feature-imputation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `blackboard-with-proof-obligations` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `block-consequence-probes` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `bonsai-up-logprob-margin-safeguard-deployment-benchmark` | False | 0 | 9 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `bonsai-up-logprob-margin-safeguard-deployment-benchmark-2310f99ce2` | False | 2 | 9 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `branch-shared-kv-fragments` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `byte-memory-pointer-decoder-for-fragile-spans` | False | 0 | 7 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `byte-memory-pointer-decoder-for-fragile-spans-9e45f48f18` | False | 2 | 7 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `cache-churn-alarm-vllm-adapter-benchmark` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `cache-churn-alarm-vllm-adapter-benchmark-228d4519a8` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `cache-quantization-awareness-training` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `cache-reentry-production-endpoint-validation` | False | 0 | 9 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `cache-reentry-production-endpoint-validation-52f1745344` | False | 2 | 9 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `calibrated-citation-governance-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `calibration-regret-map` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `canoe-route-risk-planner` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `capability-retention-sentinel-live-baseline-adapter-run` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `capability-retention-sentinel-live-baseline-adapter-run-22ad70e0c1` | False | 2 | 0 | ["claims_missing_evidence_refs"] |
| `capable-planner-segment-firewall-validation` | False | 0 | 4 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `capable-planner-segment-firewall-validation-3de5a48185` | False | 3 | 4 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `cenf-full-pdf-citation-accuracy-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `cera-capacity-enhanced-rank-adaptation-via-silu-gated-parallel-adapter` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `chain-of-density-evidence-pack` | False | 0 | 3 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `chain-of-density-evidence-pack-c783196b5f` | False | 2 | 3 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `cheap-factual-correction-after-local-sycophancy-rejection` | False | 0 | 1 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `cheap-factual-correction-after-local-sycophancy-rejection-1886329759` | False | 2 | 1 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `chunk-margin-pruner` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `chunk-margin-pruner-2b55848aba` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `ci-log-cost-gated-failure-signature-sentinel` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `citation-focused-section-ordering` | False | 0 | 9 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `citation-focused-section-ordering-fb43bdffef` | False | 2 | 9 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `citation-locator-metadata-extraction-intervention-benchmark` | False | 0 | 6 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `citation-locator-metadata-extraction-intervention-benchmark-a982006d78` | False | 2 | 6 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `citation-mode-speculation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `citation-span-robustness-tuning` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `clean-core-agent-harness` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `cmc-dflash-conditional-marginal-coupling-for-dflash` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `codebase-cartographer-real-repo-validation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `coder-only-dense-shrinker` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `cognitive-core-eval-suite` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `commit-level-critic` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `commit-level-critic-8b2442c412` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `compiler-error-curriculum-real-workflow-scale-validation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `compiler-flag-search-agent` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `compress-then-answer-benchmark` | False | 0 | 14 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `compress-then-answer-benchmark-c53b7c2a1f` | False | 2 | 14 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `compression-aware-microlm` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `compression-gap-penalty` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `compression-overhead-estimator` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `confidence-triggered-reread-training` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `configuration-entropy-reducer` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `consent-receipt-engine` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `contention-aware-single-medium-backend-broker-benchmark` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `contention-aware-single-medium-backend-broker-benchmark-475e083a27` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `context-budget-dropout` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `context-capital-allocator` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `context-digest-auxiliary-reconstruction` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `context-overflow-real-llm-reader-validation` | False | 0 | 13 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `context-overflow-real-llm-reader-validation-fb8ac0a46b` | False | 2 | 13 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `context-provenance-firewall` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `context-rehydration-multi-model-validation` | False | 0 | 18 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `context-rehydration-multi-model-validation-db1eeb1f24` | False | 2 | 18 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `context-rehydration-student` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `context-reuse-clusterer-local-serving-harness` | False | 0 | 15 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `context-reuse-clusterer-local-serving-harness-3293a9b6dd` | False | 2 | 15 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `context-role-pruning` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `context-skeleton-distillation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `continuous-phase-memory-bench` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `contrastive-chunk-ordering-loss` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `controller-integrated-uncertainty-heatmap-ranker` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `core-only-distillation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `council-gated-memory-promotion` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `counterexample-bank-targeted-mini-sft-validation` | False | 0 | 3 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `counterexample-bank-targeted-mini-sft-validation-e001666b78` | False | 2 | 3 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `counterfactual-eviction-labels` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `coverage-guided-security-patch-red-team-real-repo-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `cpu-offload-stress-harness-real-server-scaleup` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `cpu-offload-stress-harness-real-server-scaleup-7ac6d3d13e` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `cuad-cross-model-legal-answer-quality-replication` | False | 0 | 10 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `cuad-cross-model-legal-answer-quality-replication-964eda1287` | False | 2 | 10 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `cuad-dense-retriever-productionization-with-cached-vector-index` | False | 0 | 10 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `cuad-dense-retriever-productionization-with-cached-vector-index-c25709dd7d` | False | 2 | 10 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `data-center-airflow-toy-twin` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `dataset-genealogy-index---successor-branch` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `deadline-guarded-speculation-live-serving-validation` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `deadline-guarded-speculation-live-serving-validation-be3d57eec2` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `delegation-simulator` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `delta-prefill-alignment-loss` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `demo-position-lottery` | False | 0 | 4 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `demo-position-lottery-dc4b968515` | False | 2 | 4 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `denoised-rejection-replay` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `dense-mask-distillation-from-moe` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `dense-prune-harness-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `dense-router-retrofit` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `dense-to-moe-upcycling-retrofit` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `dense-to-sparse-curriculum` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `developer-workflow-persona-drift-benchmark-against-filegram` | False | 0 | 6 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `developer-workflow-persona-drift-benchmark-against-filegram-4e6de530c8` | False | 2 | 6 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `dflash-code-generation-quality-guard` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `dflash-code-generation-quality-guard-d435059a51` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `dflash-gb10-transformers-smoke` | False | 0 | 7 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `dflash-gb10-transformers-smoke-0b34db2889` | False | 2 | 7 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `dflash-vllm-sglang-throughput-shootout` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `dflash-vllm-sglang-throughput-shootout-acada17226` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `dflash-vs-existing-spec-dec-baseline-harness` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `dflash-vs-existing-spec-dec-baseline-harness-caedfff9e6` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `dgx-uma-expert-residency-governor` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `diff-hygiene-budgeter-real-repo-validation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `difficulty-aware-mask-bank---successor-branch` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `difficulty-aware-mask-bank---successor-branch-652045ba64` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `diffuspec-user-provided-drafter-for-trt-llm` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `document-field-importance-llm-generation-validation` | False | 0 | 1 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `document-field-importance-llm-generation-validation-bb6c85041c` | False | 2 | 1 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `domain-gated-speculative-waste-minimizer` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `draft-candidate-reordering` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `draft-length-predictor-tuning` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `draft-token-value-distill` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `draft-value-router` | False | 0 | 14 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `draft-value-router-8b7bb3b644` | False | 2 | 14 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `dual-trace-memory-encoder` | False | 0 | 3 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `dual-trace-memory-encoder-6bd25ff090` | False | 2 | 3 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `dynamic-window-fine-tune` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `eagle-3-bigger-drafter-pareto-sweep` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `easyspec-target-internal-early-exit-drafter` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `elastic-expert-budget-during-cpt` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `energy-aware-small-model-distill` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `engine-level-prefix-cache-cohort-scheduler` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `engine-level-prefix-cache-cohort-scheduler-810eeb05f0` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `enoch-dag-scheduler-shadow-router` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `enoch-experiment-lifecycle-gate-integration` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `entity-neighborhood-windower` | False | 0 | 3 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `entity-neighborhood-windower-739d77e465` | False | 2 | 3 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `evidence-bound-proof-synthesizer-for-tool-ledger` | False | 0 | 10 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `evidence-bound-proof-synthesizer-for-tool-ledger-4bb53c9047` | False | 2 | 10 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `evidence-first-answerability-cutoff-integration-benchmark` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `evidence-first-answerability-cutoff-integration-benchmark-87cb13bc5f` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `evidence-first-context-ladder-prompt-layout-ablation` | False | 0 | 15 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `evidence-first-context-ladder-prompt-layout-ablation-b1c2c65887` | False | 2 | 15 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `evidence-recall-auxiliary-head` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `evidence-recall-mini-teacher` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `evidence-span-boundary-loss` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `executive-worker-model-split` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `experiment-autopsy-agent` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `expert-upcycling-for-verification-models` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `fact-frequency-flattener` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `field-importance-multi-task-tuning` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `fieldwise-recall-probe-real-trace-multi-model-validation` | False | 0 | 17 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `fieldwise-recall-probe-real-trace-multi-model-validation-3cbaf8e0d7` | False | 2 | 17 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `file-delta-personalization-tuning` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `firmware-diff-explainer` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `flashattention-4-kernel-pipelining-for-sm_121-fa4-sm121` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `flashattention-4-kernel-pipelining-for-sm_121-fa4-sm121-e7971f7338` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `forced-contrastive-self-audit-extraction-trace-benchmark` | False | 0 | 4 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `forced-contrastive-self-audit-extraction-trace-benchmark-6a93b3b661` | False | 2 | 4 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `frozen-prompt-archive-real-workflow-integration` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `garbage-token-tax` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `gb10-dense-router-retrofit-strict-audit-bundle` | True | 5 | 0 | [] |
| `gb10-expert-upcycling-reproduction-harness` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `gb10-joule-router-live-calibration-adapter` | False | 0 | 10 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `gb10-joule-router-live-calibration-adapter-de3ab2c063` | False | 2 | 10 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `gb10-local-server-utility-swap-broker-validation` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `gb10-local-server-utility-swap-broker-validation-798a9fe509` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `generalized-codex-tool-policy-event-rollout` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `gguf-lora-gpu-switch-benchmark-on-non-moe-models` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `ghost-route-policy-evaluator` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `goal-shard-manager` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `goose-sa-anisotropic-tree` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `head-importance-self-labeling` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `home-lab-agent-orchestrator` | False | 0 | 8 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `home-lab-agent-orchestrator-876ea845f9` | False | 2 | 8 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `hot-cold-tensor-paging` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `hot-cold-tensor-paging-bc643f18f8` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `human-checked-acceptance-trace-validation` | False | 0 | 7 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `human-checked-acceptance-trace-validation-8e3ceb5519` | False | 2 | 7 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `human-interruptibility-score` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `humaneval-mbpp-counterexample-harvest-verifier-transfer` | False | 0 | 4 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `humaneval-mbpp-counterexample-harvest-verifier-transfer-2e35d6977f` | False | 2 | 4 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `hypothesis-ledger-admission-gate-a-b-trial` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `interactive-trust-tier-side-effect-trace-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `intercept-aware-kv-checkpointing-for-tool-calls---successor-branch` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `intercept-aware-kv-checkpointing-for-tool-calls---successor-branch-a54ccd2781` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `json-schema-guided-speculation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `junction-adapter-broader-rys-benchmark` | False | 0 | 11 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `junction-adapter-broader-rys-benchmark-4090194b12` | False | 2 | 11 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `k-first-approximation-switch` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `knowledge-deletion-fine-tune` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `kv-aware-agent-planner` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `kv-eviction-gold-labels` | False | 0 | 12 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `kv-eviction-gold-labels-617a0a21e2` | False | 2 | 12 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `kv-pressure-adaptive-speculation-governor-for-32k-context` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `kv-saliency-student` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `kv-spill-top-3-learned-reranker` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `lab-notebook-diff-engine` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `lab-protocol-lockfile-multi-turn-tool-calling-replay` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `latency-to-value-scheduler-real-model-tier-validation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `layer-asymmetric-cache-budget` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `layer-skip-under-memory-pressure` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `layerwise-calibration-observer-for-dense` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `llama.cpp-gguf-hot-warm-cold-mmap-instrumentation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `llama.cpp-in-place-kv-compaction-for-importance-retention` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `llm-backed-log-to-patch-memory-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `llm-backed-summary-drift-corpus-validation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `llm-code-navigation-context-packer-evaluation` | False | 0 | 5 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `llm-code-navigation-context-packer-evaluation-3a30325780` | False | 2 | 5 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `llm-evidence-survival-qa-validation` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `llm-evidence-survival-qa-validation-7369a2c25f` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `llm-mcp-mutation-proxy-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `load-balancer-free-symmetry-breaker` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `locality-switched-windowing` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `log-compression-with-causal-handles` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `long-answer-tail-cache-booster` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `long-context-kv-pressure-speculation-governor` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `long-context-trash-compactor` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `long-horizon-canary-tasks` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `long-tail-entity-boost-mix` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `long-tail-entity-boost-mix-593359d822` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `long-to-short-compression-training` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `lookahead-suffixdecoding-code-trace-cache` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `lookahead-suffixdecoding-for-code-agent-loops` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `lookup-aware-toolformer-toy` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `lost-in-middle-reversal-curriculum` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `lost-middle-rescue-student` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `low-rank-kv-compensation-adapter` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `low-rank-patch-after-prune` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `massv-beagle-cross-attention` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `memorization-reasoning-probe-split` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `memory-pressure-admission-gate-live-serving-validation` | False | 0 | 6 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `memory-pressure-admission-gate-live-serving-validation-c2c4ef0659` | False | 2 | 6 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `memory-pressure-replay-logs` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `memory-pressure-replay-logs-399667d44a` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `memory-quarantine-queue-real-llm-workflow-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `memory-topology-arena` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `minimum-curriculum-search` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `multi-model-real-span-boundary-corruption-benchmark` | False | 0 | 6 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `multi-model-real-span-boundary-corruption-benchmark-3de4e67099` | False | 2 | 6 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `multi-objective-throughput-reward` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `multi-tenant-cache-fairness-guard` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `n-m-quant-prune-joint-search` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `native-tool-call-capability-lease-wrapper` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `near-miss-tool-call-dataset` | False | 0 | 3 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `near-miss-tool-call-dataset-53189437af` | False | 2 | 3 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `network-path-curiosity-agent` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `neural-endpoint-segment-order-sensitivity-validation` | False | 0 | 4 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `neural-endpoint-segment-order-sensitivity-validation-88fd97a900` | False | 2 | 4 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `noisy-web-distillation-gauntlet` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `null-result-memory-real-workflow-replay-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `omnidraft-cross-vocabulary-compatibility-layer` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `omx-guarded-trust-weighted-memory-store-integration` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `omx-skill-bond-registry-prototype` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `open-weight-integrity-twin-agent-sweep` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `open-weight-integrity-twin-agent-sweep-0ccf945b66` | False | 2 | 0 | ["claims_missing_evidence_refs"] |
| `openai-compatible-deployment-of-syntax-preserving-rag-adapter` | False | 0 | 14 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `openai-compatible-deployment-of-syntax-preserving-rag-adapter-f4c3279614` | False | 2 | 14 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `outcome-calibrated-real-trace-safety-drift-monitor` | False | 0 | 10 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `outcome-calibrated-real-trace-safety-drift-monitor-3ba0f94143` | False | 2 | 10 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `outlier-singleton-protection` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `output-aware-terminal-recovery-reset-gate` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `pair-adaptive-draft-waste-calibration-benchmark` | False | 0 | 6 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `pair-adaptive-draft-waste-calibration-benchmark-483f4eaba5` | False | 2 | 6 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `paper-club-swarm-blind-full-paper-validation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `parametric-memory-budget-meter` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `partial-evidence-audited-sft-recall-preservation-ablation` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `partial-evidence-audited-sft-recall-preservation-ablation-6c2fa2a1c9` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `partial-module-rys` | False | 0 | 8 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `partial-module-rys-214ec2d410` | False | 2 | 8 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `partition-aware-cascade-distillation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `partition-local-confidence-cascade` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `physical-experiment-doe-agent` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `plan-ast` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `plan-drift-tribunal` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `precision-filtered-evidence-anchors-for-distractor-robust-qa` | False | 0 | 19 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `precision-filtered-evidence-anchors-for-distractor-robust-qa-f5f7002f1a` | False | 2 | 19 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `prefix-equivalence-targeted-normalizer-uplift` | False | 0 | 6 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `prefix-equivalence-targeted-normalizer-uplift-7aac87ee48` | False | 2 | 6 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `prefix-matched-draft-library` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `prefix-reuse-consistency-loss` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `prefix-seeder-serving-adapter-benchmark` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `prefix-seeder-serving-adapter-benchmark-0dda3ef06c` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `prefix-share-serving-trace-set` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `prefix-share-serving-trace-set-deb949d444` | False | 2 | 0 | ["claims_missing_evidence_refs"] |
| `production-codex-omx-typed-event-recorder` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `production-end-task-canonical-first-rys-variant-benchmark` | False | 0 | 7 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `production-end-task-canonical-first-rys-variant-benchmark-0ed3345070` | False | 2 | 7 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `production-rag-kv-offload-landmark-reliability-scale-up` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `production-rag-kv-offload-landmark-reliability-scale-up-25fe5716f0` | False | 2 | 0 | ["claims_missing_evidence_refs"] |
| `production-speculative-decoding-counter-validation` | False | 0 | 8 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `production-speculative-decoding-counter-validation-508a95f82a` | False | 2 | 8 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `project-kill-switch-council` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `prompt-compression-aware-drafters` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `proof-carrying-prs` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `protocol-compliance-judge` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `prune-then-upcycle-recovery-loop` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `ptp-mtp-acceptance-optimized-self-drafter` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `public-fastapi-typer-compatibility-oracle-validation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `q2-to-q4-calibration-regret-block-promotion-runtime-prototype` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `quant-spectrum-cross-model-downstream-validation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `quantization-aware-expert-upcycling` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `quantization-aware-saliency` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `query-budget-contract-local-server-benchmark` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `query-budget-contract-local-server-benchmark-301a0a4c9e` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `query-key-retention-map` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `qwen32b-speculative-workflow-robustness-suite` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `real-corpus-row-id-citation-qa-integration-benchmark` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `real-corpus-row-id-citation-qa-integration-benchmark-86b43b9fc1` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `real-document-retrieval-compression-teacher-validation` | False | 0 | 5 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `real-document-retrieval-compression-teacher-validation-af518c0527` | False | 2 | 5 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `real-mode-stress-regularization` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `real-model-negative-exit-controller-on-math-and-code-search-traces` | False | 0 | 18 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `real-model-negative-exit-controller-on-math-and-code-search-traces-92c852013c` | False | 2 | 18 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `real-rag-answer-abstention-boundary-benchmark` | False | 0 | 6 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `real-rag-answer-abstention-boundary-benchmark-481ae7871e` | False | 2 | 6 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `real-repo-docstring-property-gate-integration` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `real-rys-wall-clock-throughput-for-budget-pruned-representation-seeding` | False | 0 | 7 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `real-rys-wall-clock-throughput-for-budget-pruned-representation-seeding-1264f736d5` | False | 2 | 7 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `real-task-context-compression-pareto-validation` | False | 0 | 8 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `real-task-context-compression-pareto-validation-a9db9821a9` | False | 2 | 8 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `real-trace-near-miss-refusal-adapter-validation` | False | 0 | 4 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `real-trace-near-miss-refusal-adapter-validation-9afd0f1d27` | False | 2 | 4 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `reap-dynamic-tree-shaping` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `reap-ragged-loader-real-checkpoint-integration` | False | 0 | 2 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `reap-ragged-loader-real-checkpoint-integration-4a35e4aebb` | False | 2 | 2 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `reasoning-aware-quant-router-policy-v2` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `recap-token-supervision` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `reduced-planner-scratchpad-feedback-real-repo-qa-validation` | False | 0 | 18 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `reduced-planner-scratchpad-feedback-real-repo-qa-validation-8a97fc9598` | False | 2 | 18 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `rehydration-guide-student` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `rejection-mode-targeted-abstention-refusal-tuning` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `rejection-mode-targeted-abstention-refusal-tuning-8c1fd3db27` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `rejection-span-distillation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `repo-pulse-index-real-repo-pilot` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `research-agent-treaty-protocol` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `research-claim-unit-tests` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `research-council-agenda-compiler-weekly-pilot` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `residual-conservation-pruner` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `residue-head-teacher-distillation-for-lbrc` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `residue-head-teacher-distillation-for-lbrc-b9f4fd77ce` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `resource-bounded-agent-kernel` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `resource-bounded-agent-kernel-1127e6ebd4` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `retrieval-aware-evidence-packer-arbitration-benchmark` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `retrieval-aware-evidence-packer-arbitration-benchmark-c601be3b27` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `retrieval-conditioned-expert-expansion` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `retrieval-honesty-loss` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `retrieval-landmark-kv-pins` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `reuse-fingerprint-student` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `reversible-prune-masks` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `rl-bandit-entropy-gated-multi-policy-speculation-router` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `robotic-procedure-verifier` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `rollback-audit-and-escrow-for-transactional-tool-calls` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `router-distilled-triton-mlp-full-model-integration` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `router-distilled-triton-mlp-full-model-integration-ab4e1a5044` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `sa-first-neural-fallback-router` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `safety-interlock-synthesizer` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `salience-backed-candidate-top-1-kv-prefill-packing-benchmark` | False | 0 | 12 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `salience-backed-candidate-top-1-kv-prefill-packing-benchmark-5576bc3d18` | False | 2 | 12 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `saliency-distillation-targets` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `sandbox-risk-oracle-live-harness-calibration` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `scaffold-only-revision-mode` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `schema-anchor-adapter-tuning` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `schema-drift-json-corpus` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `schema-drift-json-corpus-d97a28b051` | False | 2 | 0 | ["claims_missing_evidence_refs"] |
| `schema-pinned-json-cache` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `semantic-channel-naming` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `semantic-overlap-tax-generative-llm-public-rag-benchmark` | False | 0 | 12 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `semantic-overlap-tax-generative-llm-public-rag-benchmark-3348c5e036` | False | 2 | 12 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `serving-boundary-context-compression-kv-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `shared-context-multi-query-speculation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `shared-prompt-batcher-local-server-validation` | False | 0 | 15 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `shared-prompt-batcher-local-server-validation-0e58ffd5bd` | False | 2 | 15 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `short-model-long-task-distillation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `short-train-long-eval-prompt-robust-tuning` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `short-train-long-eval-prompt-robust-tuning-55360a96d1` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `similarity-gated-value-quantization` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `sink-token-stabilization` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `skill-preflight-gate-integration` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `skill-to-dataset-compiler` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `slo-narrative-compressor` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `small-model-persona-context-orderer-generation-validation` | False | 0 | 6 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `small-model-persona-context-orderer-generation-validation-5ee3b77220` | False | 2 | 6 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `sobd-survival-optimized-block-diffusion` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `source-citation-kv-reserve` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `sparse-value-late-materializer` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `sparse-verifier-token-check` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `spec-decoder-domain-router` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `spectr-style-ot-verifier-for-multi-candidate-trees` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `speculation-friendly-lm-head-tuning` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `speculation-tree-student` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `specvocab-hybrid-for-eagle-3-and-dflash` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `ssd-goose-sa` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `ssd-outcome-cache-with-suffix-state-keys` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `stalled-agent-rescuer` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `strong-draft-weak-reviewer-transfer` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `structured-noise-injection-suite` | False | 0 | 10 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `structured-noise-injection-suite-e24b2e17ae` | False | 2 | 10 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `sub-8gb-model-zoo-triage` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `swarm-counterfactual-logger` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `swarm-heartbeat-bus` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `sycophancy-sensitive-escalation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `synthetic-user-load-negotiator` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `task-class-expert-reproduction` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `task-gated-thinking-retention-controller` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `task-routed-context-allocation-extractive-relevance-vs-marginal-utility` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `temperature-conditional-acceptance-calibration` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `test-rig-self-maintainer` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `thermal-policy-optimizer` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `thinking-pattern-bridge-adapter` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `token-conditioned-mlp-thinning` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `token-importance-probe` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `token-rent-for-examples` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `token-rent-for-examples-21bc7b6ced` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `token-type-importance-labels` | False | 0 | 9 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `token-type-importance-labels-9d67810608` | False | 2 | 9 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `tokenized-tiny-lm-duplicate-ratio-ablation` | False | 0 | 9 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `tokenized-tiny-lm-duplicate-ratio-ablation-e352f99372` | False | 2 | 9 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `tool-boundary-non-speculate-gate` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `trace-inspector-warm-session-operator-trial` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `trajectory-rulebook-distillation` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `trie-guided-speculative-json` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `uncertainty-coverage-co-estimator` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `upcycle-router-cold-start-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `upcycle-timing-sweep-law` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `upcycled-expert-distillation-collapse` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `upcycled-lora-expert-grafting` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `utr-conflict-update-final-answer-schema-hardening` | False | 0 | 20 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `utr-conflict-update-final-answer-schema-hardening-ee2ec3df1c` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `value-only-cold-storage` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `value-per-joule-broker-online-canary-on-gb10-endpoints` | False | 0 | 13 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `value-per-joule-broker-online-canary-on-gb10-endpoints-7c1e9366d2` | False | 2 | 13 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `verification-conditional-cache-restore` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `verification-failure-clusters` | False | 0 | 6 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `verification-failure-clusters-ec5ecfde87` | False | 2 | 6 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `verifier-feature-acceptance-classifier` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `vllm-attention-sink-retention-3b-continuous-serving-stress-campaign` | True | 5 | 0 | [] |
| `vllm-attention-sink-retention-3b-continuous-serving-stress-campaign-e679db6170` | False | 2 | 20 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `vram-admission-controller` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
| `wake-gate-local-endpoint-harness-integration` | False | 0 | 15 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `wake-gate-local-endpoint-harness-integration-a559f7e6df` | False | 2 | 15 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `weak-wikipedia-generative-answer-flattening-pilot` | False | 0 | 3 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `weak-wikipedia-generative-answer-flattening-pilot-a0927e1c3e` | False | 2 | 3 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `web-state-replay-benchmark-for-rewindable-sandboxes` | False | 0 | 2 | ["claim_ledger_empty_claims", "evidence_result_files_missing_public_artifacts"] |
| `web-state-replay-benchmark-for-rewindable-sandboxes-b07c9b5663` | False | 2 | 2 | ["claims_missing_evidence_refs", "evidence_result_files_missing_public_artifacts"] |
| `workflow-aware-verifier-router-benchmark` | False | 0 | 0 | ["claim_ledger_empty_claims"] |
