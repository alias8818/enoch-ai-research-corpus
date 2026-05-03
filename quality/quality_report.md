# Corpus public audit reports

Packaging/provenance lint: 159 / 159 pass
Strict claim/evidence audit: 1 / 159 pass
Scientific correctness, replication, peer review, statistical power, semantic output quality, and citation accuracy: not validated.

This compatibility report deliberately shows both counts on the first screen. The packaging/provenance lint checks artifact packaging, provenance language, placeholder/overclaim patterns, and presence of evidence/claim metadata files. It does not validate strict claim/evidence auditability.

## Packaging/provenance lint validated

- `ai_provenance_notice_present`
- `no_placeholder_citation_patterns`
- `no_unsupported_human_authorship_claim`
- `no_unsupported_peer_review_claim`
- `evidence_bundle_present`
- `claim_ledger_present`

## Not validated by packaging/provenance lint

- `peer_review`
- `scientific_correctness`
- `external_replication`
- `statistical_power`
- `semantic_output_quality`
- `citation_accuracy`
- `strict_claim_evidence_audit`

## Strict claim/evidence audit

Strict claim/evidence passed: 1 / 159
Status: `blocked_audit_gaps`
Gap summary: Claim ledgers are empty or result_file references are not publicly present; packaging/provenance lint must not be read as deep claim audit.

| Paper | Packaging/provenance lint pass | Packaging issues |
|---|---:|---|
| `adapter-projected-galore-192-step-decoupled-refresh-mmlu-eval` | True | {} |
| `adaptive-boundary-colorization-gate` | True | {} |
| `adaptive-budget-aware-lim-reserve-sampler` | True | {} |
| `adaptive-claim-first-top-k-router` | True | {} |
| `adaptive-evidence-packer-rag-integration` | True | {} |
| `adaptive-prefix-splitter-inference-integration` | True | {} |
| `adversarial-channel-router` | True | {} |
| `agent-app-store-with-repro-sandboxes` | True | {} |
| `agent-identity-rotation` | True | {} |
| `answer-shape-prompt-planner` | True | {} |
| `anti-collapse-expert-immune-system` | True | {} |
| `applicability-gated-abstention-calibration-policy` | True | {} |
| `aret-hierarchical-multi-virtue-reward-architecture-for-rl` | True | {} |
| `attention-loss-shadow-estimator` | True | {} |
| `audio-room-measurement-planner` | True | {} |
| `batched-reader-qets-mixed-domain-scaling-validation` | True | {} |
| `batched-vllm-speculation-cost-governor-integration` | True | {} |
| `benchmark-explorer-agent` | True | {} |
| `benchmark-health-ledger` | True | {} |
| `benchmark-qwen3-non-uniform-reap-manual-fp8-scoring` | True | {} |
| `benchmark-qwen3-non-uniform-reap-manual-fp8-scoring-b7a5f924e4` | True | {} |
| `bonsai-up-logprob-margin-safeguard-deployment-benchmark` | True | {} |
| `byte-memory-pointer-decoder-for-fragile-spans` | True | {} |
| `cache-churn-alarm-vllm-adapter-benchmark` | True | {} |
| `cache-reentry-production-endpoint-validation` | True | {} |
| `canoe-route-risk-planner` | True | {} |
| `capability-retention-sentinel-live-baseline-adapter-run` | True | {} |
| `capable-planner-segment-firewall-validation` | True | {} |
| `chain-of-density-evidence-pack` | True | {} |
| `cheap-factual-correction-after-local-sycophancy-rejection` | True | {} |
| `chunk-margin-pruner` | True | {} |
| `citation-focused-section-ordering` | True | {} |
| `citation-locator-metadata-extraction-intervention-benchmark` | True | {} |
| `commit-level-critic` | True | {} |
| `compiler-flag-search-agent` | True | {} |
| `compress-then-answer-benchmark` | True | {} |
| `compression-gap-penalty` | True | {} |
| `configuration-entropy-reducer` | True | {} |
| `contention-aware-single-medium-backend-broker-benchmark` | True | {} |
| `context-digest-auxiliary-reconstruction` | True | {} |
| `context-overflow-real-llm-reader-validation` | True | {} |
| `context-rehydration-multi-model-validation` | True | {} |
| `context-reuse-clusterer-local-serving-harness` | True | {} |
| `counterexample-bank-targeted-mini-sft-validation` | True | {} |
| `counterfactual-eviction-labels` | True | {} |
| `cpu-offload-stress-harness-real-server-scaleup` | True | {} |
| `cuad-cross-model-legal-answer-quality-replication` | True | {} |
| `cuad-dense-retriever-productionization-with-cached-vector-index` | True | {} |
| `data-center-airflow-toy-twin` | True | {} |
| `deadline-guarded-speculation-live-serving-validation` | True | {} |
| `demo-position-lottery` | True | {} |
| `developer-workflow-persona-drift-benchmark-against-filegram` | True | {} |
| `dflash-code-generation-quality-guard` | True | {} |
| `dflash-gb10-transformers-smoke` | True | {} |
| `dflash-vllm-sglang-throughput-shootout` | True | {} |
| `dflash-vs-existing-spec-dec-baseline-harness` | True | {} |
| `difficulty-aware-mask-bank---successor-branch` | True | {} |
| `document-field-importance-llm-generation-validation` | True | {} |
| `draft-token-value-distill` | True | {} |
| `draft-value-router` | True | {} |
| `dual-trace-memory-encoder` | True | {} |
| `dynamic-window-fine-tune` | True | {} |
| `elastic-expert-budget-during-cpt` | True | {} |
| `engine-level-prefix-cache-cohort-scheduler` | True | {} |
| `entity-neighborhood-windower` | True | {} |
| `evidence-bound-proof-synthesizer-for-tool-ledger` | True | {} |
| `evidence-first-answerability-cutoff-integration-benchmark` | True | {} |
| `evidence-first-context-ladder-prompt-layout-ablation` | True | {} |
| `evidence-recall-auxiliary-head` | True | {} |
| `experiment-autopsy-agent` | True | {} |
| `expert-upcycling-for-verification-models` | True | {} |
| `field-importance-multi-task-tuning` | True | {} |
| `fieldwise-recall-probe-real-trace-multi-model-validation` | True | {} |
| `firmware-diff-explainer` | True | {} |
| `flashattention-4-kernel-pipelining-for-sm_121-fa4-sm121` | True | {} |
| `forced-contrastive-self-audit-extraction-trace-benchmark` | True | {} |
| `gb10-joule-router-live-calibration-adapter` | True | {} |
| `gb10-local-server-utility-swap-broker-validation` | True | {} |
| `head-importance-self-labeling` | True | {} |
| `home-lab-agent-orchestrator` | True | {} |
| `hot-cold-tensor-paging` | True | {} |
| `human-checked-acceptance-trace-validation` | True | {} |
| `humaneval-mbpp-counterexample-harvest-verifier-transfer` | True | {} |
| `intercept-aware-kv-checkpointing-for-tool-calls---successor-branch` | True | {} |
| `junction-adapter-broader-rys-benchmark` | True | {} |
| `kv-eviction-gold-labels` | True | {} |
| `llm-code-navigation-context-packer-evaluation` | True | {} |
| `llm-evidence-survival-qa-validation` | True | {} |
| `load-balancer-free-symmetry-breaker` | True | {} |
| `log-compression-with-causal-handles` | True | {} |
| `long-tail-entity-boost-mix` | True | {} |
| `memory-pressure-admission-gate-live-serving-validation` | True | {} |
| `memory-pressure-replay-logs` | True | {} |
| `multi-model-real-span-boundary-corruption-benchmark` | True | {} |
| `near-miss-tool-call-dataset` | True | {} |
| `network-path-curiosity-agent` | True | {} |
| `neural-endpoint-segment-order-sensitivity-validation` | True | {} |
| `open-weight-integrity-twin-agent-sweep` | True | {} |
| `openai-compatible-deployment-of-syntax-preserving-rag-adapter` | True | {} |
| `outcome-calibrated-real-trace-safety-drift-monitor` | True | {} |
| `pair-adaptive-draft-waste-calibration-benchmark` | True | {} |
| `partial-evidence-audited-sft-recall-preservation-ablation` | True | {} |
| `partial-module-rys` | True | {} |
| `physical-experiment-doe-agent` | True | {} |
| `precision-filtered-evidence-anchors-for-distractor-robust-qa` | True | {} |
| `prefix-equivalence-targeted-normalizer-uplift` | True | {} |
| `prefix-seeder-serving-adapter-benchmark` | True | {} |
| `prefix-share-serving-trace-set` | True | {} |
| `production-end-task-canonical-first-rys-variant-benchmark` | True | {} |
| `production-rag-kv-offload-landmark-reliability-scale-up` | True | {} |
| `production-speculative-decoding-counter-validation` | True | {} |
| `protocol-compliance-judge` | True | {} |
| `query-budget-contract-local-server-benchmark` | True | {} |
| `real-corpus-row-id-citation-qa-integration-benchmark` | True | {} |
| `real-document-retrieval-compression-teacher-validation` | True | {} |
| `real-model-negative-exit-controller-on-math-and-code-search-traces` | True | {} |
| `real-rag-answer-abstention-boundary-benchmark` | True | {} |
| `real-rys-wall-clock-throughput-for-budget-pruned-representation-seeding` | True | {} |
| `real-task-context-compression-pareto-validation` | True | {} |
| `real-trace-near-miss-refusal-adapter-validation` | True | {} |
| `reap-ragged-loader-real-checkpoint-integration` | True | {} |
| `reduced-planner-scratchpad-feedback-real-repo-qa-validation` | True | {} |
| `rehydration-guide-student` | True | {} |
| `rejection-mode-targeted-abstention-refusal-tuning` | True | {} |
| `residue-head-teacher-distillation-for-lbrc` | True | {} |
| `resource-bounded-agent-kernel` | True | {} |
| `retrieval-aware-evidence-packer-arbitration-benchmark` | True | {} |
| `retrieval-conditioned-expert-expansion` | True | {} |
| `reuse-fingerprint-student` | True | {} |
| `robotic-procedure-verifier` | True | {} |
| `router-distilled-triton-mlp-full-model-integration` | True | {} |
| `safety-interlock-synthesizer` | True | {} |
| `salience-backed-candidate-top-1-kv-prefill-packing-benchmark` | True | {} |
| `schema-anchor-adapter-tuning` | True | {} |
| `schema-drift-json-corpus` | True | {} |
| `semantic-overlap-tax-generative-llm-public-rag-benchmark` | True | {} |
| `shared-prompt-batcher-local-server-validation` | True | {} |
| `short-train-long-eval-prompt-robust-tuning` | True | {} |
| `sink-token-stabilization` | True | {} |
| `slo-narrative-compressor` | True | {} |
| `small-model-persona-context-orderer-generation-validation` | True | {} |
| `structured-noise-injection-suite` | True | {} |
| `synthetic-user-load-negotiator` | True | {} |
| `task-class-expert-reproduction` | True | {} |
| `test-rig-self-maintainer` | True | {} |
| `thermal-policy-optimizer` | True | {} |
| `token-rent-for-examples` | True | {} |
| `token-type-importance-labels` | True | {} |
| `tokenized-tiny-lm-duplicate-ratio-ablation` | True | {} |
| `upcycle-router-cold-start-benchmark` | True | {} |
| `upcycled-expert-distillation-collapse` | True | {} |
| `upcycled-lora-expert-grafting` | True | {} |
| `utr-conflict-update-final-answer-schema-hardening` | True | {} |
| `value-per-joule-broker-online-canary-on-gb10-endpoints` | True | {} |
| `verification-failure-clusters` | True | {} |
| `vllm-attention-sink-retention-3b-continuous-serving-stress-campaign` | True | {} |
| `wake-gate-local-endpoint-harness-integration` | True | {} |
| `weak-wikipedia-generative-answer-flattening-pilot` | True | {} |
| `web-state-replay-benchmark-for-rewindable-sandboxes` | True | {} |
