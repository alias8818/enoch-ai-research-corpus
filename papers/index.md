# Paper index

Count: 379

This index distinguishes metadata-file presence from strict claim/evidence audit status. Current corpus state is 379/379 packaging/provenance lint pass and 3/379 strict claim/evidence audit pass.

## Highlighted artifacts

These launch highlights are a curated inspection set, not a peer-review ranking. The `why it matters` summaries are bounded pointers into generated artifacts; use each paper's evidence bundle, claim ledger, and strict-audit status before treating a claim as established.

| Title | Public ID | Why it matters | Bounds |
|---|---|---|---|
| [Evidence-Bound Proof Synthesizer for Tool Ledger](evidence-bound-proof-synthesizer-for-tool-ledger/paper.md) | `enoch-paper-0098` | This is one of the strongest artifacts because it pushes beyond ordinary agent logging: it proposes automatically synthesized proof objects for tool calls, derived from task evidence and trace metadata. | Local transcript corpus and generated traces only; not production-scale validation. |
| [vLLM Attention-Sink Retention 3B Continuous-Serving Stress Campaign](vllm-attention-sink-retention-3b-continuous-serving-stress-campaign/paper.md) | `enoch-paper-0159` | Canonical inspection path: a bounded continuous-serving artifact with concrete latency, error, output-divergence, limitations, evidence bundle, and claim ledger links. | Single model, single hardware environment, limited trials, no semantic output-quality validation, and not independently replicated. |
| [DFlash Code-Generation Quality Guard](dflash-code-generation-quality-guard/paper.md) | `enoch-paper-0006` | A marketable systems result: speculative decoding is exciting, but code generation quality is the scary failure mode. This artifact tests speedups behind explicit quality kill conditions. | Small local benchmark subsets and hardware/backend compatibility constraints. |
| [DFlash vLLM/SGLang Throughput Shootout](dflash-vllm-sglang-throughput-shootout/paper.md) | `enoch-paper-0001` | This is a clean performance headline for the corpus: a local GB10 serving benchmark with positive vLLM results and negative SGLang compatibility evidence reported transparently. | Single GB10 GPU, one target/draft model pair, modest sample sizes; SGLang path blocked by SM121 kernel compatibility. |
| [FlashAttention-4 Kernel Pipelining for sm_121](flashattention-4-kernel-pipelining-for-sm_121-fa4-sm121/paper.md) | `enoch-paper-0029` | This is one of the more technically novel artifacts: it explores whether GB10/SM121 TMA paths can support FlashAttention-4-style pipelined attention kernels. | Kernel scaffold and microbenchmark evidence, not a production FA4 implementation. |
| [Open-Weight Integrity Twin Agent Sweep](open-weight-integrity-twin-agent-sweep/paper.md) | `enoch-paper-0033` | This is a strong ‘why this matters’ artifact: it looks for evaluator-surface tampering and public-vs-trusted score gaps in local open-weight models. | Limited model family/scale coverage and deliberately bounded workspace tasks. |
| [Router-Distilled Triton MLP Full-Model Integration](router-distilled-triton-mlp-full-model-integration/paper.md) | `enoch-paper-0024` | A concrete kernel-and-model integration artifact: not just an idea about sparse routing, but a routed MLP wired into a decoder-layer prefill path. | Single GB10 hardware configuration and prefill-focused tests; decode/generalization unproven. |
| [Resource-Bounded Agent Kernel](resource-bounded-agent-kernel/paper.md) | `enoch-paper-0040` | This directly reinforces the system thesis: autonomous agents need OS-style resource governance, not just prompts and logs. | Harness validation, not production kernel certification. |
| [Adversarial Channel Router](adversarial-channel-router/paper.md) | `enoch-paper-0044` | A highly sellable agent-safety direction: typed, authenticated channel envelopes to stop adversarial payloads from leaking across planner/tool/output channels. | Bounded local harnesses; needs broader integration with live multi-agent runtimes. |
| [Agent Identity Rotation](agent-identity-rotation/paper.md) | `enoch-paper-0042` | This is a crisp agent-security concept: planner, executor, and committer roles sign action envelopes so authority is explicit and replay-resistant. | Synthetic adversarial corpus within a deterministic local harness; live multi-agent integration remains untested. |
| [Value-per-Joule Broker Online Canary](value-per-joule-broker-online-canary-on-gb10-endpoints/paper.md) | `enoch-paper-0012` | This is easy to explain and relevant to anyone running local AI: route by successful-output value per joule, not just model size or confidence. | Small models, single host, short-duration canary. |
| [Memory Pressure Admission Gate](memory-pressure-admission-gate-live-serving-validation/paper.md) | `enoch-paper-0115` | A practical serving-control result that matches the Enoch worldview: protect the lane before requests create pathological pressure. | Single stack, one quantized model, 16-request deterministic workload; peak RSS increased slightly. |
| [Cache Churn Alarm vLLM Adapter Benchmark](cache-churn-alarm-vllm-adapter-benchmark/paper.md) | `enoch-paper-0120` | This is a nuanced artifact: it does not oversell latency, but it finds a concrete memory-pressure control signal for suppressing optional speculative branches. | Single model/configuration and isolated A/B runs; p95 latency did not improve. |

## Full artifact index

| Title | Public ID | Evidence bundle present | Claim ledger file present | Claim count | Strict audit pass | Missing result refs |
|---|---|---:|---:|---:|---:|---:|
| [Acceptance-Length CUDA Graph Bank](acceptance-length-cuda-graph-bank/paper.md) | `enoch-paper-0367` | yes | yes | 0 | false | 0 |
| [Adapter-Projected GaLore 192-Step Decoupled-Refresh MMLU Eval](adapter-projected-galore-192-step-decoupled-refresh-mmlu-eval/paper.md) | `enoch-paper-0099` | yes | yes | 2 | false | 20 |
| [Adaptive Boundary Colorization Gate](adaptive-boundary-colorization-gate/paper.md) | `enoch-paper-0089` | yes | yes | 2 | false | 20 |
| [Adaptive Budget-Aware LIM Reserve Sampler](adaptive-budget-aware-lim-reserve-sampler/paper.md) | `enoch-paper-0062` | yes | yes | 2 | false | 20 |
| [Adaptive Claim-First Top-K Router](adaptive-claim-first-top-k-router/paper.md) | `enoch-paper-0003` | yes | yes | 2 | false | 7 |
| [Adaptive Evidence Packer RAG Integration](adaptive-evidence-packer-rag-integration/paper.md) | `enoch-paper-0078` | yes | yes | 2 | false | 13 |
| [Adaptive Landmark Reweighter](adaptive-landmark-reweighter/paper.md) | `enoch-paper-0331` | yes | yes | 0 | false | 0 |
| [Adaptive Prefix Splitter Inference Integration](adaptive-prefix-splitter-inference-integration/paper.md) | `enoch-paper-0073` | yes | yes | 2 | false | 3 |
| [Adversarial Channel Router](adversarial-channel-router/paper.md) | `enoch-paper-0044` | yes | yes | 2 | false | 6 |
| [Agent App Store With Repro Sandboxes](agent-app-store-with-repro-sandboxes/paper.md) | `enoch-paper-0043` | yes | yes | 2 | false | 1 |
| [Agent Budget Parliament](agent-budget-parliament/paper.md) | `enoch-paper-0166` | yes | yes | 0 | false | 0 |
| [Agent Identity Rotation](agent-identity-rotation/paper.md) | `enoch-paper-0042` | yes | yes | 2 | false | 7 |
| [Agent Runner Black Box Integration Benchmark](agent-runner-black-box-integration-benchmark/paper.md) | `enoch-paper-0235` | yes | yes | 0 | false | 0 |
| [Agentic Benchmark Autogenerator](agentic-benchmark-autogenerator/paper.md) | `enoch-paper-0178` | yes | yes | 0 | false | 0 |
| [AGENTS.md Linter Task-Lift Validation](agents.md-linter-task-lift-validation/paper.md) | `enoch-paper-0215` | yes | yes | 0 | false | 0 |
| [Answer-Shape Prompt Planner](answer-shape-prompt-planner/paper.md) | `enoch-paper-0008` | yes | yes | 2 | false | 10 |
| [Anti-Collapse Expert Immune System](anti-collapse-expert-immune-system/paper.md) | `enoch-paper-0122` | yes | yes | 0 | false | 0 |
| [Anti-Encyclopedia Curriculum](anti-encyclopedia-curriculum/paper.md) | `enoch-paper-0300` | yes | yes | 0 | false | 0 |
| [Applicability-Gated Abstention Calibration Policy](applicability-gated-abstention-calibration-policy/paper.md) | `enoch-paper-0061` | yes | yes | 2 | false | 15 |
| [Aretē: Hierarchical Multi-Virtue Reward Architecture for RL](aret-hierarchical-multi-virtue-reward-architecture-for-rl/paper.md) | `enoch-paper-0028` | yes | yes | 2 | false | 20 |
| [Asymmetric K/V Adapter Training](asymmetric-k-v-adapter-training/paper.md) | `enoch-paper-0274` | yes | yes | 0 | false | 0 |
| [Async Selective KV Lease Backend Prototype](async-selective-kv-lease-backend-prototype/paper.md) | `enoch-paper-0247` | yes | yes | 0 | false | 0 |
| [Attention Budget Controller](attention-budget-controller/paper.md) | `enoch-paper-0183` | yes | yes | 0 | false | 0 |
| [Attention-Loss Shadow Estimator](attention-loss-shadow-estimator/paper.md) | `enoch-paper-0091` | yes | yes | 2 | false | 20 |
| [Attention-MLP Joint Pruner](attention-mlp-joint-pruner/paper.md) | `enoch-paper-0344` | yes | yes | 0 | false | 0 |
| [Attention Sink Preserving Prune](attention-sink-preserving-prune/paper.md) | `enoch-paper-0299` | yes | yes | 0 | false | 0 |
| [Attention-Sink Rescue Pool](attention-sink-rescue-pool/paper.md) | `enoch-paper-0322` | yes | yes | 0 | false | 0 |
| [Audio Room Measurement Planner](audio-room-measurement-planner/paper.md) | `enoch-paper-0134` | yes | yes | 0 | false | 0 |
| [Autonomous Project Manager Kernel](autonomous-project-manager-kernel/paper.md) | `enoch-paper-0348` | yes | yes | 0 | false | 0 |
| [Backend-Switched Verifier Pretraining](backend-switched-verifier-pretraining/paper.md) | `enoch-paper-0269` | yes | yes | 0 | false | 0 |
| [Batched Reader QETS Mixed-Domain Scaling Validation](batched-reader-qets-mixed-domain-scaling-validation/paper.md) | `enoch-paper-0090` | yes | yes | 2 | false | 14 |
| [Batched vLLM Speculation-Cost Governor Integration](batched-vllm-speculation-cost-governor-integration/paper.md) | `enoch-paper-0079` | yes | yes | 2 | false | 20 |
| [Benchmark Explorer Agent](benchmark-explorer-agent/paper.md) | `enoch-paper-0133` | yes | yes | 0 | false | 0 |
| [Benchmark Health Ledger](benchmark-health-ledger/paper.md) | `enoch-paper-0046` | yes | yes | 2 | false | 4 |
| [Benchmark Qwen3 Non-Uniform REAP Manual-FP8 Scoring](benchmark-qwen3-non-uniform-reap-manual-fp8-scoring/paper.md) | `enoch-paper-0017` | yes | yes | 2 | false | 18 |
| [BFI-DFlash: Bonus Feature Imputation](bfi-dflash-bonus-feature-imputation/paper.md) | `enoch-paper-0167` | yes | yes | 0 | false | 0 |
| [Blackboard With Proof Obligations](blackboard-with-proof-obligations/paper.md) | `enoch-paper-0177` | yes | yes | 0 | false | 0 |
| [Block Consequence Probes](block-consequence-probes/paper.md) | `enoch-paper-0349` | yes | yes | 0 | false | 0 |
| [Bonsai-Up Logprob-Margin Safeguard Deployment Benchmark](bonsai-up-logprob-margin-safeguard-deployment-benchmark/paper.md) | `enoch-paper-0036` | yes | yes | 2 | false | 9 |
| [Branch-Shared KV Fragments](branch-shared-kv-fragments/paper.md) | `enoch-paper-0316` | yes | yes | 0 | false | 0 |
| [Byte-Memory Pointer Decoder for Fragile Spans](byte-memory-pointer-decoder-for-fragile-spans/paper.md) | `enoch-paper-0016` | yes | yes | 2 | false | 7 |
| [Cache Churn Alarm vLLM Adapter Benchmark](cache-churn-alarm-vllm-adapter-benchmark/paper.md) | `enoch-paper-0120` | yes | yes | 2 | false | 20 |
| [Cache Quantization Awareness Training](cache-quantization-awareness-training/paper.md) | `enoch-paper-0278` | yes | yes | 0 | false | 0 |
| [Cache Reentry Production Endpoint Validation](cache-reentry-production-endpoint-validation/paper.md) | `enoch-paper-0013` | yes | yes | 2 | false | 9 |
| [Calibrated Citation Governance Benchmark](calibrated-citation-governance-benchmark/paper.md) | `enoch-paper-0206` | yes | yes | 0 | false | 0 |
| [Calibration Regret Map](calibration-regret-map/paper.md) | `enoch-paper-0161` | yes | yes | 0 | false | 0 |
| [Canoe Route Risk Planner](canoe-route-risk-planner/paper.md) | `enoch-paper-0139` | yes | yes | 0 | false | 0 |
| [Capability Retention Sentinel Live Baseline Adapter Run](capability-retention-sentinel-live-baseline-adapter-run/paper.md) | `enoch-paper-0027` | yes | yes | 2 | false | 0 |
| [Capable Planner Segment-Firewall Validation](capable-planner-segment-firewall-validation/paper.md) | `enoch-paper-0093` | yes | yes | 3 | false | 4 |
| [CENF Full-PDF Citation Accuracy Benchmark](cenf-full-pdf-citation-accuracy-benchmark/paper.md) | `enoch-paper-0207` | yes | yes | 0 | false | 0 |
| [CeRA: Capacity-Enhanced Rank Adaptation via SiLU-Gated Parallel Adapter](cera-capacity-enhanced-rank-adaptation-via-silu-gated-parallel-adapter/paper.md) | `enoch-paper-0258` | yes | yes | 0 | false | 0 |
| [Chain-of-Density Evidence Pack](chain-of-density-evidence-pack/paper.md) | `enoch-paper-0116` | yes | yes | 2 | false | 3 |
| [Cheap Factual Correction After Local Sycophancy Rejection](cheap-factual-correction-after-local-sycophancy-rejection/paper.md) | `enoch-paper-0105` | yes | yes | 2 | false | 1 |
| [Chunk-Margin Pruner](chunk-margin-pruner/paper.md) | `enoch-paper-0032` | yes | yes | 2 | false | 20 |
| [CI-Log Cost-Gated Failure Signature Sentinel](ci-log-cost-gated-failure-signature-sentinel/paper.md) | `enoch-paper-0208` | yes | yes | 0 | false | 0 |
| [Citation-Focused Section Ordering](citation-focused-section-ordering/paper.md) | `enoch-paper-0051` | yes | yes | 2 | false | 9 |
| [Citation Locator Metadata Extraction Intervention Benchmark](citation-locator-metadata-extraction-intervention-benchmark/paper.md) | `enoch-paper-0067` | yes | yes | 2 | false | 6 |
| [Citation-Mode Speculation](citation-mode-speculation/paper.md) | `enoch-paper-0317` | yes | yes | 0 | false | 0 |
| [Citation Span Robustness Tuning](citation-span-robustness-tuning/paper.md) | `enoch-paper-0281` | yes | yes | 0 | false | 0 |
| [Clean-Core Agent Harness](clean-core-agent-harness/paper.md) | `enoch-paper-0170` | yes | yes | 0 | false | 0 |
| [CMC-DFlash: Conditional Marginal Coupling for DFlash](cmc-dflash-conditional-marginal-coupling-for-dflash/paper.md) | `enoch-paper-0173` | yes | yes | 0 | false | 0 |
| [Codebase Cartographer Real-Repo Validation](codebase-cartographer-real-repo-validation/paper.md) | `enoch-paper-0211` | yes | yes | 0 | false | 0 |
| [Coder-Only Dense Shrinker](coder-only-dense-shrinker/paper.md) | `enoch-paper-0352` | yes | yes | 0 | false | 0 |
| [Cognitive Core Eval Suite](cognitive-core-eval-suite/paper.md) | `enoch-paper-0301` | yes | yes | 0 | false | 0 |
| [Commit-Level Critic](commit-level-critic/paper.md) | `enoch-paper-0045` | yes | yes | 2 | false | 20 |
| [Compiler Error Curriculum Real-Workflow Scale Validation](compiler-error-curriculum-real-workflow-scale-validation/paper.md) | `enoch-paper-0209` | yes | yes | 0 | false | 0 |
| [Compiler Flag Search Agent](compiler-flag-search-agent/paper.md) | `enoch-paper-0136` | yes | yes | 0 | false | 0 |
| [Compress-Then-Answer Benchmark](compress-then-answer-benchmark/paper.md) | `enoch-paper-0014` | yes | yes | 2 | false | 14 |
| [Compression-Aware MicroLM](compression-aware-microlm/paper.md) | `enoch-paper-0295` | yes | yes | 0 | false | 0 |
| [Compression Gap Penalty](compression-gap-penalty/paper.md) | `enoch-paper-0154` | yes | yes | 0 | false | 0 |
| [Compression Overhead Estimator](compression-overhead-estimator/paper.md) | `enoch-paper-0351` | yes | yes | 0 | false | 0 |
| [Confidence-Triggered Reread Training](confidence-triggered-reread-training/paper.md) | `enoch-paper-0293` | yes | yes | 0 | false | 0 |
| [Configuration Entropy Reducer](configuration-entropy-reducer/paper.md) | `enoch-paper-0144` | yes | yes | 0 | false | 0 |
| [Consent Receipt Engine](consent-receipt-engine/paper.md) | `enoch-paper-0194` | yes | yes | 0 | false | 0 |
| [Contention-Aware Single-Medium Backend Broker Benchmark](contention-aware-single-medium-backend-broker-benchmark/paper.md) | `enoch-paper-0057` | yes | yes | 2 | false | 20 |
| [Context Budget Dropout](context-budget-dropout/paper.md) | `enoch-paper-0273` | yes | yes | 0 | false | 0 |
| [Context Capital Allocator](context-capital-allocator/paper.md) | `enoch-paper-0188` | yes | yes | 0 | false | 0 |
| [Context Digest Auxiliary Reconstruction](context-digest-auxiliary-reconstruction/paper.md) | `enoch-paper-0135` | yes | yes | 0 | false | 0 |
| [Context Overflow Real LLM Reader Validation](context-overflow-real-llm-reader-validation/paper.md) | `enoch-paper-0010` | yes | yes | 2 | false | 13 |
| [Context Provenance Firewall](context-provenance-firewall/paper.md) | `enoch-paper-0353` | yes | yes | 0 | false | 0 |
| [Context Rehydration Multi-Model Validation](context-rehydration-multi-model-validation/paper.md) | `enoch-paper-0112` | yes | yes | 2 | false | 18 |
| [Context Rehydration Student](context-rehydration-student/paper.md) | `enoch-paper-0288` | yes | yes | 0 | false | 0 |
| [Context Reuse Clusterer Local Serving Harness](context-reuse-clusterer-local-serving-harness/paper.md) | `enoch-paper-0030` | yes | yes | 2 | false | 15 |
| [Context-Role Pruning](context-role-pruning/paper.md) | `enoch-paper-0337` | yes | yes | 0 | false | 0 |
| [Context Skeleton Distillation](context-skeleton-distillation/paper.md) | `enoch-paper-0287` | yes | yes | 0 | false | 0 |
| [Continuous-Phase Memory Bench](continuous-phase-memory-bench/paper.md) | `enoch-paper-0264` | yes | yes | 0 | false | 0 |
| [Contrastive Chunk Ordering Loss](contrastive-chunk-ordering-loss/paper.md) | `enoch-paper-0298` | yes | yes | 0 | false | 0 |
| [Controlled Supabase Lifecycle Drill](controlled-supabase-lifecycle-drill/paper.md) | `enoch-paper-0497` | yes | yes | 0 | false | 0 |
| [Controller-Integrated Uncertainty Heatmap Ranker](controller-integrated-uncertainty-heatmap-ranker/paper.md) | `enoch-paper-0240` | yes | yes | 0 | false | 0 |
| [Core-Only Distillation](core-only-distillation/paper.md) | `enoch-paper-0175` | yes | yes | 0 | false | 0 |
| [Council-Gated Memory Promotion](council-gated-memory-promotion/paper.md) | `enoch-paper-0193` | yes | yes | 0 | false | 0 |
| [Counterexample Bank Targeted Mini-SFT Validation](counterexample-bank-targeted-mini-sft-validation/paper.md) | `enoch-paper-0118` | yes | yes | 2 | false | 3 |
| [Counterfactual Eviction Labels](counterfactual-eviction-labels/paper.md) | `enoch-paper-0156` | yes | yes | 0 | false | 0 |
| [Coverage-Guided Security Patch Red Team Real-Repo Benchmark](coverage-guided-security-patch-red-team-real-repo-benchmark/paper.md) | `enoch-paper-0229` | yes | yes | 0 | false | 0 |
| [CPU-Offload Stress Harness Real-Server Scaleup](cpu-offload-stress-harness-real-server-scaleup/paper.md) | `enoch-paper-0119` | yes | yes | 2 | false | 20 |
| [CUAD Cross-Model Legal Answer Quality Replication](cuad-cross-model-legal-answer-quality-replication/paper.md) | `enoch-paper-0063` | yes | yes | 2 | false | 10 |
| [CUAD Dense Retriever Productionization with Cached Vector Index](cuad-dense-retriever-productionization-with-cached-vector-index/paper.md) | `enoch-paper-0054` | yes | yes | 2 | false | 10 |
| [Data Center Airflow Toy Twin](data-center-airflow-toy-twin/paper.md) | `enoch-paper-0131` | yes | yes | 0 | false | 0 |
| [Dataset Genealogy Index - Successor Branch](dataset-genealogy-index---successor-branch/paper.md) | `enoch-paper-0212` | yes | yes | 0 | false | 0 |
| [Deadline-Guarded Speculation Live Serving Validation](deadline-guarded-speculation-live-serving-validation/paper.md) | `enoch-paper-0080` | yes | yes | 2 | false | 20 |
| [Delegation Simulator](delegation-simulator/paper.md) | `enoch-paper-0332` | yes | yes | 0 | false | 0 |
| [Delta-Prefill Alignment Loss](delta-prefill-alignment-loss/paper.md) | `enoch-paper-0297` | yes | yes | 0 | false | 0 |
| [Demo Position Lottery](demo-position-lottery/paper.md) | `enoch-paper-0117` | yes | yes | 2 | false | 4 |
| [Denoised Rejection Replay](denoised-rejection-replay/paper.md) | `enoch-paper-0305` | yes | yes | 0 | false | 0 |
| [Dense Mask Distillation from MoE](dense-mask-distillation-from-moe/paper.md) | `enoch-paper-0164` | yes | yes | 0 | false | 0 |
| [Dense Prune Harness Benchmark](dense-prune-harness-benchmark/paper.md) | `enoch-paper-0163` | yes | yes | 0 | false | 0 |
| [Dense Router Retrofit](dense-router-retrofit/paper.md) | `enoch-paper-0203` | yes | yes | 0 | false | 0 |
| [Dense-to-MoE Upcycling Retrofit](dense-to-moe-upcycling-retrofit/paper.md) | `enoch-paper-0227` | yes | yes | 0 | false | 0 |
| [Dense-to-Sparse Curriculum](dense-to-sparse-curriculum/paper.md) | `enoch-paper-0187` | yes | yes | 0 | false | 0 |
| [Developer Workflow Persona Drift Benchmark Against FileGram](developer-workflow-persona-drift-benchmark-against-filegram/paper.md) | `enoch-paper-0005` | yes | yes | 2 | false | 6 |
| [DFlash Code-Generation Quality Guard](dflash-code-generation-quality-guard/paper.md) | `enoch-paper-0006` | yes | yes | 2 | false | 20 |
| [DFlash GB10 Transformers Smoke](dflash-gb10-transformers-smoke/paper.md) | `enoch-paper-0038` | yes | yes | 2 | false | 7 |
| [DFlash vLLM/SGLang Throughput Shootout](dflash-vllm-sglang-throughput-shootout/paper.md) | `enoch-paper-0001` | yes | yes | 2 | false | 20 |
| [DFlash vs Existing Spec-Dec Baseline Harness](dflash-vs-existing-spec-dec-baseline-harness/paper.md) | `enoch-paper-0020` | yes | yes | 2 | false | 20 |
| [DGX UMA Expert Residency Governor](dgx-uma-expert-residency-governor/paper.md) | `enoch-paper-0358` | yes | yes | 0 | false | 0 |
| [Diff Hygiene Budgeter Real-Repo Validation](diff-hygiene-budgeter-real-repo-validation/paper.md) | `enoch-paper-0217` | yes | yes | 0 | false | 0 |
| [Difficulty-Aware Mask Bank - Successor Branch](difficulty-aware-mask-bank---successor-branch/paper.md) | `enoch-paper-0026` | yes | yes | 2 | false | 20 |
| [DiffuSpec User-Provided Drafter for TRT-LLM](diffuspec-user-provided-drafter-for-trt-llm/paper.md) | `enoch-paper-0368` | yes | yes | 0 | false | 0 |
| [Document-Field Importance LLM Generation Validation](document-field-importance-llm-generation-validation/paper.md) | `enoch-paper-0034` | yes | yes | 2 | false | 1 |
| [Domain-Gated Speculative Waste Minimizer](domain-gated-speculative-waste-minimizer/paper.md) | `enoch-paper-0162` | yes | yes | 0 | false | 0 |
| [Draft Candidate Reordering](draft-candidate-reordering/paper.md) | `enoch-paper-0311` | yes | yes | 0 | false | 0 |
| [Draft Length Predictor Tuning](draft-length-predictor-tuning/paper.md) | `enoch-paper-0277` | yes | yes | 0 | false | 0 |
| [Draft Token Value Distill](draft-token-value-distill/paper.md) | `enoch-paper-0158` | yes | yes | 0 | false | 0 |
| [Draft-Value Router](draft-value-router/paper.md) | `enoch-paper-0037` | yes | yes | 2 | false | 14 |
| [Dual-Trace Memory Encoder](dual-trace-memory-encoder/paper.md) | `enoch-paper-0103` | yes | yes | 2 | false | 3 |
| [Dynamic Window Fine-Tune](dynamic-window-fine-tune/paper.md) | `enoch-paper-0151` | yes | yes | 0 | false | 0 |
| [EAGLE-3 Bigger Drafter Pareto Sweep](eagle-3-bigger-drafter-pareto-sweep/paper.md) | `enoch-paper-0202` | yes | yes | 0 | false | 0 |
| [EasySpec Target-Internal Early-Exit Drafter](easyspec-target-internal-early-exit-drafter/paper.md) | `enoch-paper-0359` | yes | yes | 0 | false | 0 |
| [Elastic Expert Budget During CPT](elastic-expert-budget-during-cpt/paper.md) | `enoch-paper-0123` | yes | yes | 0 | false | 0 |
| [Energy-Aware Small Model Distill](energy-aware-small-model-distill/paper.md) | `enoch-paper-0283` | yes | yes | 0 | false | 0 |
| [Engine-Level Prefix Cache Cohort Scheduler](engine-level-prefix-cache-cohort-scheduler/paper.md) | `enoch-paper-0035` | yes | yes | 2 | false | 20 |
| [Enoch DAG Scheduler Shadow Router](enoch-dag-scheduler-shadow-router/paper.md) | `enoch-paper-0256` | yes | yes | 0 | false | 0 |
| [Enoch Experiment Lifecycle Gate Integration](enoch-experiment-lifecycle-gate-integration/paper.md) | `enoch-paper-0219` | yes | yes | 0 | false | 0 |
| [Entity-Neighborhood Windower](entity-neighborhood-windower/paper.md) | `enoch-paper-0009` | yes | yes | 2 | false | 3 |
| [Evidence-Bound Proof Synthesizer for Tool Ledger](evidence-bound-proof-synthesizer-for-tool-ledger/paper.md) | `enoch-paper-0098` | yes | yes | 2 | false | 10 |
| [Evidence-First Answerability Cutoff Integration Benchmark](evidence-first-answerability-cutoff-integration-benchmark/paper.md) | `enoch-paper-0056` | yes | yes | 2 | false | 20 |
| [Evidence-First Context Ladder Prompt Layout Ablation](evidence-first-context-ladder-prompt-layout-ablation/paper.md) | `enoch-paper-0070` | yes | yes | 2 | false | 15 |
| [Evidence Recall Auxiliary Head](evidence-recall-auxiliary-head/paper.md) | `enoch-paper-0155` | yes | yes | 0 | false | 0 |
| [Evidence Recall Mini-Teacher](evidence-recall-mini-teacher/paper.md) | `enoch-paper-0296` | yes | yes | 0 | false | 0 |
| [Evidence Span Boundary Loss](evidence-span-boundary-loss/paper.md) | `enoch-paper-0285` | yes | yes | 0 | false | 0 |
| [Executive/Worker Model Split](executive-worker-model-split/paper.md) | `enoch-paper-0171` | yes | yes | 0 | false | 0 |
| [Experiment Autopsy Agent](experiment-autopsy-agent/paper.md) | `enoch-paper-0142` | yes | yes | 0 | false | 0 |
| [Expert Upcycling for Verification Models](expert-upcycling-for-verification-models/paper.md) | `enoch-paper-0130` | yes | yes | 0 | false | 0 |
| [Fact Frequency Flattener](fact-frequency-flattener/paper.md) | `enoch-paper-0197` | yes | yes | 0 | false | 0 |
| [Field Importance Multi-Task Tuning](field-importance-multi-task-tuning/paper.md) | `enoch-paper-0121` | yes | yes | 0 | false | 0 |
| [Fieldwise Recall Probe Real-Trace Multi-Model Validation](fieldwise-recall-probe-real-trace-multi-model-validation/paper.md) | `enoch-paper-0085` | yes | yes | 2 | false | 17 |
| [File-Delta Personalization Tuning](file-delta-personalization-tuning/paper.md) | `enoch-paper-0184` | yes | yes | 0 | false | 0 |
| [Firmware Diff Explainer](firmware-diff-explainer/paper.md) | `enoch-paper-0149` | yes | yes | 0 | false | 0 |
| [FlashAttention-4 Kernel Pipelining for sm_121 (FA4-sm121)](flashattention-4-kernel-pipelining-for-sm_121-fa4-sm121/paper.md) | `enoch-paper-0029` | yes | yes | 2 | false | 20 |
| [Forced Contrastive Self-Audit Extraction Trace Benchmark](forced-contrastive-self-audit-extraction-trace-benchmark/paper.md) | `enoch-paper-0019` | yes | yes | 2 | false | 4 |
| [Frozen Prompt Archive Real Workflow Integration](frozen-prompt-archive-real-workflow-integration/paper.md) | `enoch-paper-0205` | yes | yes | 0 | false | 0 |
| [Garbage Token Tax](garbage-token-tax/paper.md) | `enoch-paper-0182` | yes | yes | 0 | false | 0 |
| [GB10 Dense Router Retrofit Strict Audit Bundle](gb10-dense-router-retrofit-strict-audit-bundle/paper.md) | `enoch-paper-0160` | yes | yes | 5 | true | 0 |
| [GB10 Expert-Upcycling Reproduction Harness](gb10-expert-upcycling-reproduction-harness/paper.md) | `enoch-paper-0222` | yes | yes | 0 | false | 0 |
| [GB10 Joule Router Live Calibration Adapter](gb10-joule-router-live-calibration-adapter/paper.md) | `enoch-paper-0031` | yes | yes | 2 | false | 10 |
| [GB10 Local Server Utility Swap Broker Validation](gb10-local-server-utility-swap-broker-validation/paper.md) | `enoch-paper-0083` | yes | yes | 2 | false | 20 |
| [Generalized Codex Tool Policy Event Rollout](generalized-codex-tool-policy-event-rollout/paper.md) | `enoch-paper-0224` | yes | yes | 0 | false | 0 |
| [GGUF LoRA GPU Switch Benchmark on Non-MoE Models](gguf-lora-gpu-switch-benchmark-on-non-moe-models/paper.md) | `enoch-paper-0252` | yes | yes | 0 | false | 0 |
| [Ghost-Route Policy Evaluator](ghost-route-policy-evaluator/paper.md) | `enoch-paper-0262` | yes | yes | 0 | false | 0 |
| [Goal Shard Manager](goal-shard-manager/paper.md) | `enoch-paper-0190` | yes | yes | 0 | false | 0 |
| [Goose-SA Anisotropic Tree](goose-sa-anisotropic-tree/paper.md) | `enoch-paper-0362` | yes | yes | 0 | false | 0 |
| [Half-Life Planning](half-life-planning/paper.md) | `enoch-paper-0499` | yes | yes | 0 | false | 0 |
| [Harness Shadow Mode Labeled Replay Prototype](harness-shadow-mode-labeled-replay-prototype/paper.md) | `enoch-paper-0500` | yes | yes | 0 | false | 0 |
| [Head Importance Self-Labeling](head-importance-self-labeling/paper.md) | `enoch-paper-0159` | yes | yes | 0 | false | 0 |
| [Home Lab Agent Orchestrator](home-lab-agent-orchestrator/paper.md) | `enoch-paper-0041` | yes | yes | 2 | false | 8 |
| [Hot-Cold Tensor Paging](hot-cold-tensor-paging/paper.md) | `enoch-paper-0039` | yes | yes | 2 | false | 20 |
| [Human-Checked Acceptance Trace Validation](human-checked-acceptance-trace-validation/paper.md) | `enoch-paper-0111` | yes | yes | 2 | false | 7 |
| [Human Interruptibility Score](human-interruptibility-score/paper.md) | `enoch-paper-0354` | yes | yes | 0 | false | 0 |
| [HumanEval MBPP Counterexample-Harvest Verifier Transfer](humaneval-mbpp-counterexample-harvest-verifier-transfer/paper.md) | `enoch-paper-0104` | yes | yes | 2 | false | 4 |
| [Hypothesis Ledger Admission Gate A/B Trial](hypothesis-ledger-admission-gate-a-b-trial/paper.md) | `enoch-paper-0216` | yes | yes | 0 | false | 0 |
| [Interactive Trust-Tier Side-Effect Trace Benchmark](interactive-trust-tier-side-effect-trace-benchmark/paper.md) | `enoch-paper-0165` | yes | yes | 0 | false | 0 |
| [Intercept-Aware KV Checkpointing for Tool Calls - Successor Branch](intercept-aware-kv-checkpointing-for-tool-calls---successor-branch/paper.md) | `enoch-paper-0021` | yes | yes | 2 | false | 20 |
| [JSON-Schema Guided Speculation](json-schema-guided-speculation/paper.md) | `enoch-paper-0319` | yes | yes | 0 | false | 0 |
| [Junction Adapter Broader RYS Benchmark](junction-adapter-broader-rys-benchmark/paper.md) | `enoch-paper-0101` | yes | yes | 2 | false | 11 |
| [K-First Approximation Switch](k-first-approximation-switch/paper.md) | `enoch-paper-0307` | yes | yes | 0 | false | 0 |
| [Knowledge Deletion Fine-Tune](knowledge-deletion-fine-tune/paper.md) | `enoch-paper-0302` | yes | yes | 0 | false | 0 |
| [KV-Aware Agent Planner](kv-aware-agent-planner/paper.md) | `enoch-paper-0189` | yes | yes | 0 | false | 0 |
| [KV Eviction Gold Labels](kv-eviction-gold-labels/paper.md) | `enoch-paper-0015` | yes | yes | 2 | false | 12 |
| [KV-Pressure Adaptive Speculation Governor for >32k Context](kv-pressure-adaptive-speculation-governor-for-32k-context/paper.md) | `enoch-paper-0360` | yes | yes | 0 | false | 0 |
| [KV-Saliency Student](kv-saliency-student/paper.md) | `enoch-paper-0284` | yes | yes | 0 | false | 0 |
| [KV Spill Top-3 Learned Reranker](kv-spill-top-3-learned-reranker/paper.md) | `enoch-paper-0255` | yes | yes | 0 | false | 0 |
| [Lab Notebook Diff Engine](lab-notebook-diff-engine/paper.md) | `enoch-paper-0338` | yes | yes | 0 | false | 0 |
| [Lab Protocol Lockfile Multi-Turn Tool-Calling Replay](lab-protocol-lockfile-multi-turn-tool-calling-replay/paper.md) | `enoch-paper-0228` | yes | yes | 0 | false | 0 |
| [Latency-to-Value Scheduler Real Model Tier Validation](latency-to-value-scheduler-real-model-tier-validation/paper.md) | `enoch-paper-0220` | yes | yes | 0 | false | 0 |
| [Layer-Asymmetric Cache Budget](layer-asymmetric-cache-budget/paper.md) | `enoch-paper-0323` | yes | yes | 0 | false | 0 |
| [Layer Skip under Memory Pressure](layer-skip-under-memory-pressure/paper.md) | `enoch-paper-0286` | yes | yes | 0 | false | 0 |
| [Layerwise Calibration Observer for Dense](layerwise-calibration-observer-for-dense/paper.md) | `enoch-paper-0343` | yes | yes | 0 | false | 0 |
| [llama.cpp GGUF hot-warm-cold mmap instrumentation](llama.cpp-gguf-hot-warm-cold-mmap-instrumentation/paper.md) | `enoch-paper-0254` | yes | yes | 0 | false | 0 |
| [llama.cpp In-Place KV Compaction for Importance Retention](llama.cpp-in-place-kv-compaction-for-importance-retention/paper.md) | `enoch-paper-0250` | yes | yes | 0 | false | 0 |
| [LLM-Backed Log-to-Patch Memory Benchmark](llm-backed-log-to-patch-memory-benchmark/paper.md) | `enoch-paper-0225` | yes | yes | 0 | false | 0 |
| [LLM-Backed Summary Drift Corpus Validation](llm-backed-summary-drift-corpus-validation/paper.md) | `enoch-paper-0303` | yes | yes | 0 | false | 0 |
| [LLM Code Navigation Context-Packer Evaluation](llm-code-navigation-context-packer-evaluation/paper.md) | `enoch-paper-0086` | yes | yes | 2 | false | 5 |
| [LLM Evidence-Survival QA Validation](llm-evidence-survival-qa-validation/paper.md) | `enoch-paper-0053` | yes | yes | 2 | false | 20 |
| [LLM MCP Mutation Proxy Benchmark](llm-mcp-mutation-proxy-benchmark/paper.md) | `enoch-paper-0218` | yes | yes | 0 | false | 0 |
| [Load-Balancer-Free Symmetry Breaker](load-balancer-free-symmetry-breaker/paper.md) | `enoch-paper-0127` | yes | yes | 0 | false | 0 |
| [Locality-Switched Windowing](locality-switched-windowing/paper.md) | `enoch-paper-0321` | yes | yes | 0 | false | 0 |
| [Log Compression With Causal Handles](log-compression-with-causal-handles/paper.md) | `enoch-paper-0143` | yes | yes | 0 | false | 0 |
| [Long-Answer Tail Cache Booster](long-answer-tail-cache-booster/paper.md) | `enoch-paper-0312` | yes | yes | 0 | false | 0 |
| [Long-Context KV-Pressure Speculation Governor](long-context-kv-pressure-speculation-governor/paper.md) | `enoch-paper-0375` | yes | yes | 0 | false | 0 |
| [Long Context Trash Compactor](long-context-trash-compactor/paper.md) | `enoch-paper-0347` | yes | yes | 0 | false | 0 |
| [Long-Horizon Canary Tasks](long-horizon-canary-tasks/paper.md) | `enoch-paper-0333` | yes | yes | 0 | false | 0 |
| [Long-Tail Entity Boost Mix](long-tail-entity-boost-mix/paper.md) | `enoch-paper-0064` | yes | yes | 2 | false | 20 |
| [Long-to-Short Compression Training](long-to-short-compression-training/paper.md) | `enoch-paper-0280` | yes | yes | 0 | false | 0 |
| [Lookahead + SuffixDecoding + Code Trace Cache](lookahead-suffixdecoding-code-trace-cache/paper.md) | `enoch-paper-0371` | yes | yes | 0 | false | 0 |
| [Lookahead + SuffixDecoding for Code/Agent Loops](lookahead-suffixdecoding-for-code-agent-loops/paper.md) | `enoch-paper-0374` | yes | yes | 0 | false | 0 |
| [Lookup-Aware Toolformer Toy](lookup-aware-toolformer-toy/paper.md) | `enoch-paper-0179` | yes | yes | 0 | false | 0 |
| [Lost-in-Middle Reversal Curriculum](lost-in-middle-reversal-curriculum/paper.md) | `enoch-paper-0291` | yes | yes | 0 | false | 0 |
| [Lost-Middle Rescue Student](lost-middle-rescue-student/paper.md) | `enoch-paper-0294` | yes | yes | 0 | false | 0 |
| [Low-Rank KV Compensation Adapter](low-rank-kv-compensation-adapter/paper.md) | `enoch-paper-0275` | yes | yes | 0 | false | 0 |
| [Low-Rank Patch After Prune](low-rank-patch-after-prune/paper.md) | `enoch-paper-0196` | yes | yes | 0 | false | 0 |
| [MASSV + Beagle Cross-Attention](massv-beagle-cross-attention/paper.md) | `enoch-paper-0366` | yes | yes | 0 | false | 0 |
| [Memorization/Reasoning Probe Split](memorization-reasoning-probe-split/paper.md) | `enoch-paper-0342` | yes | yes | 0 | false | 0 |
| [Memory Pressure Admission Gate Live Serving Validation](memory-pressure-admission-gate-live-serving-validation/paper.md) | `enoch-paper-0115` | yes | yes | 2 | false | 6 |
| [Memory Pressure Replay Logs](memory-pressure-replay-logs/paper.md) | `enoch-paper-0065` | yes | yes | 2 | false | 20 |
| [Memory Quarantine Queue Real-LLM Workflow Benchmark](memory-quarantine-queue-real-llm-workflow-benchmark/paper.md) | `enoch-paper-0230` | yes | yes | 0 | false | 0 |
| [Memory Topology Arena](memory-topology-arena/paper.md) | `enoch-paper-0261` | yes | yes | 0 | false | 0 |
| [Minimum Curriculum Search](minimum-curriculum-search/paper.md) | `enoch-paper-0350` | yes | yes | 0 | false | 0 |
| [Multi-Model Real-Span Boundary Corruption Benchmark](multi-model-real-span-boundary-corruption-benchmark/paper.md) | `enoch-paper-0081` | yes | yes | 2 | false | 6 |
| [Multi-Objective Throughput Reward](multi-objective-throughput-reward/paper.md) | `enoch-paper-0290` | yes | yes | 0 | false | 0 |
| [Multi-Tenant Cache Fairness Guard](multi-tenant-cache-fairness-guard/paper.md) | `enoch-paper-0309` | yes | yes | 0 | false | 0 |
| [N:M Quant-Prune Joint Search](n-m-quant-prune-joint-search/paper.md) | `enoch-paper-0201` | yes | yes | 0 | false | 0 |
| [Native Tool-Call Capability Lease Wrapper](native-tool-call-capability-lease-wrapper/paper.md) | `enoch-paper-0210` | yes | yes | 0 | false | 0 |
| [Near-Miss Tool Call Dataset](near-miss-tool-call-dataset/paper.md) | `enoch-paper-0066` | yes | yes | 2 | false | 3 |
| [Network Path Curiosity Agent](network-path-curiosity-agent/paper.md) | `enoch-paper-0132` | yes | yes | 0 | false | 0 |
| [Neural Endpoint Segment Order Sensitivity Validation](neural-endpoint-segment-order-sensitivity-validation/paper.md) | `enoch-paper-0113` | yes | yes | 2 | false | 4 |
| [Noisy-Web Distillation Gauntlet](noisy-web-distillation-gauntlet/paper.md) | `enoch-paper-0199` | yes | yes | 0 | false | 0 |
| [Null Result Memory Real-Workflow Replay Benchmark](null-result-memory-real-workflow-replay-benchmark/paper.md) | `enoch-paper-0246` | yes | yes | 0 | false | 0 |
| [OmniDraft Cross-Vocabulary Compatibility Layer](omnidraft-cross-vocabulary-compatibility-layer/paper.md) | `enoch-paper-0369` | yes | yes | 0 | false | 0 |
| [OMX Guarded Trust-Weighted Memory Store Integration](omx-guarded-trust-weighted-memory-store-integration/paper.md) | `enoch-paper-0233` | yes | yes | 0 | false | 0 |
| [OMX Skill Bond Registry Prototype](omx-skill-bond-registry-prototype/paper.md) | `enoch-paper-0234` | yes | yes | 0 | false | 0 |
| [Open-Weight Integrity Twin Agent Sweep](open-weight-integrity-twin-agent-sweep/paper.md) | `enoch-paper-0033` | yes | yes | 2 | false | 0 |
| [OpenAI-Compatible Deployment of Syntax-Preserving RAG Adapter](openai-compatible-deployment-of-syntax-preserving-rag-adapter/paper.md) | `enoch-paper-0055` | yes | yes | 2 | false | 14 |
| [Outcome-Calibrated Real-Trace Safety-Drift Monitor](outcome-calibrated-real-trace-safety-drift-monitor/paper.md) | `enoch-paper-0106` | yes | yes | 2 | false | 10 |
| [Outlier Singleton Protection](outlier-singleton-protection/paper.md) | `enoch-paper-0346` | yes | yes | 0 | false | 0 |
| [Output-Aware Terminal Recovery Reset Gate](output-aware-terminal-recovery-reset-gate/paper.md) | `enoch-paper-0236` | yes | yes | 0 | false | 0 |
| [Pair-Adaptive Draft Waste Calibration Benchmark](pair-adaptive-draft-waste-calibration-benchmark/paper.md) | `enoch-paper-0011` | yes | yes | 2 | false | 6 |
| [Paper Club Swarm Blind Full-Paper Validation](paper-club-swarm-blind-full-paper-validation/paper.md) | `enoch-paper-0185` | yes | yes | 0 | false | 0 |
| [Parametric Memory Budget Meter](parametric-memory-budget-meter/paper.md) | `enoch-paper-0345` | yes | yes | 0 | false | 0 |
| [Partial-Evidence Audited SFT Recall-Preservation Ablation](partial-evidence-audited-sft-recall-preservation-ablation/paper.md) | `enoch-paper-0048` | yes | yes | 2 | false | 20 |
| [Partial-Module RYS](partial-module-rys/paper.md) | `enoch-paper-0100` | yes | yes | 2 | false | 8 |
| [Partition-Aware Cascade Distillation](partition-aware-cascade-distillation/paper.md) | `enoch-paper-0260` | yes | yes | 0 | false | 0 |
| [Partition-Local Confidence Cascade](partition-local-confidence-cascade/paper.md) | `enoch-paper-0259` | yes | yes | 0 | false | 0 |
| [Physical Experiment DOE Agent](physical-experiment-doe-agent/paper.md) | `enoch-paper-0145` | yes | yes | 0 | false | 0 |
| [Plan AST](plan-ast/paper.md) | `enoch-paper-0180` | yes | yes | 0 | false | 0 |
| [Plan Drift Tribunal](plan-drift-tribunal/paper.md) | `enoch-paper-0356` | yes | yes | 0 | false | 0 |
| [Precision-Filtered Evidence Anchors for Distractor-Robust QA](precision-filtered-evidence-anchors-for-distractor-robust-qa/paper.md) | `enoch-paper-0077` | yes | yes | 2 | false | 19 |
| [Prefix-Equivalence Targeted Normalizer Uplift](prefix-equivalence-targeted-normalizer-uplift/paper.md) | `enoch-paper-0007` | yes | yes | 2 | false | 6 |
| [Prefix-Matched Draft Library](prefix-matched-draft-library/paper.md) | `enoch-paper-0318` | yes | yes | 0 | false | 0 |
| [Prefix Reuse Consistency Loss](prefix-reuse-consistency-loss/paper.md) | `enoch-paper-0289` | yes | yes | 0 | false | 0 |
| [Prefix Seeder Serving Adapter Benchmark](prefix-seeder-serving-adapter-benchmark/paper.md) | `enoch-paper-0052` | yes | yes | 2 | false | 20 |
| [Prefix-Share Serving Trace Set](prefix-share-serving-trace-set/paper.md) | `enoch-paper-0071` | yes | yes | 2 | false | 0 |
| [Production Codex OMX Typed Event Recorder](production-codex-omx-typed-event-recorder/paper.md) | `enoch-paper-0244` | yes | yes | 0 | false | 0 |
| [Production End-Task Canonical-First RYS Variant Benchmark](production-end-task-canonical-first-rys-variant-benchmark/paper.md) | `enoch-paper-0018` | yes | yes | 2 | false | 7 |
| [Production RAG KV-Offload Landmark Reliability Scale-Up](production-rag-kv-offload-landmark-reliability-scale-up/paper.md) | `enoch-paper-0049` | yes | yes | 2 | false | 0 |
| [Production Speculative Decoding Counter Validation](production-speculative-decoding-counter-validation/paper.md) | `enoch-paper-0084` | yes | yes | 2 | false | 8 |
| [Project Kill Switch Council](project-kill-switch-council/paper.md) | `enoch-paper-0181` | yes | yes | 0 | false | 0 |
| [Prompt-Compression-Aware Drafters](prompt-compression-aware-drafters/paper.md) | `enoch-paper-0314` | yes | yes | 0 | false | 0 |
| [Proof-Carrying PRs](proof-carrying-prs/paper.md) | `enoch-paper-0339` | yes | yes | 0 | false | 0 |
| [Protocol Compliance Judge](protocol-compliance-judge/paper.md) | `enoch-paper-0141` | yes | yes | 0 | false | 0 |
| [Prune-Then-Upcycle Recovery Loop](prune-then-upcycle-recovery-loop/paper.md) | `enoch-paper-0226` | yes | yes | 0 | false | 0 |
| [PTP/MTP Acceptance-Optimized Self-Drafter](ptp-mtp-acceptance-optimized-self-drafter/paper.md) | `enoch-paper-0357` | yes | yes | 0 | false | 0 |
| [Public FastAPI Typer Compatibility Oracle Validation](public-fastapi-typer-compatibility-oracle-validation/paper.md) | `enoch-paper-0214` | yes | yes | 0 | false | 0 |
| [Q2-to-Q4 Calibration-Regret Block Promotion Runtime Prototype](q2-to-q4-calibration-regret-block-promotion-runtime-prototype/paper.md) | `enoch-paper-0243` | yes | yes | 0 | false | 0 |
| [Quant Spectrum Cross-Model Downstream Validation](quant-spectrum-cross-model-downstream-validation/paper.md) | `enoch-paper-0242` | yes | yes | 0 | false | 0 |
| [Quantization-Aware Expert Upcycling](quantization-aware-expert-upcycling/paper.md) | `enoch-paper-0221` | yes | yes | 0 | false | 0 |
| [Quantization-Aware Saliency](quantization-aware-saliency/paper.md) | `enoch-paper-0186` | yes | yes | 0 | false | 0 |
| [Query Budget Contract Local Server Benchmark](query-budget-contract-local-server-benchmark/paper.md) | `enoch-paper-0087` | yes | yes | 2 | false | 20 |
| [Query-Key Retention Map](query-key-retention-map/paper.md) | `enoch-paper-0326` | yes | yes | 0 | false | 0 |
| [Qwen32B Speculative Workflow Robustness Suite](qwen32b-speculative-workflow-robustness-suite/paper.md) | `enoch-paper-0248` | yes | yes | 0 | false | 0 |
| [Real-Corpus Row-ID Citation QA Integration Benchmark](real-corpus-row-id-citation-qa-integration-benchmark/paper.md) | `enoch-paper-0074` | yes | yes | 2 | false | 20 |
| [Real-Document Retrieval Compression Teacher Validation](real-document-retrieval-compression-teacher-validation/paper.md) | `enoch-paper-0114` | yes | yes | 2 | false | 5 |
| [Real-Mode Stress Regularization](real-mode-stress-regularization/paper.md) | `enoch-paper-0268` | yes | yes | 0 | false | 0 |
| [Real-Model Negative-Exit Controller on Math and Code Search Traces](real-model-negative-exit-controller-on-math-and-code-search-traces/paper.md) | `enoch-paper-0108` | yes | yes | 2 | false | 18 |
| [Real-RAG Answer-Abstention Boundary Benchmark](real-rag-answer-abstention-boundary-benchmark/paper.md) | `enoch-paper-0068` | yes | yes | 2 | false | 6 |
| [Real-Repo Docstring Property Gate Integration](real-repo-docstring-property-gate-integration/paper.md) | `enoch-paper-0213` | yes | yes | 0 | false | 0 |
| [Real RYS Wall-Clock Throughput for Budget-Pruned Representation Seeding](real-rys-wall-clock-throughput-for-budget-pruned-representation-seeding/paper.md) | `enoch-paper-0025` | yes | yes | 2 | false | 7 |
| [Real-Task Context Compression Pareto Validation](real-task-context-compression-pareto-validation/paper.md) | `enoch-paper-0110` | yes | yes | 2 | false | 8 |
| [Real Trace Near-Miss Refusal Adapter Validation](real-trace-near-miss-refusal-adapter-validation/paper.md) | `enoch-paper-0107` | yes | yes | 2 | false | 4 |
| [REAP Dynamic Tree Shaping](reap-dynamic-tree-shaping/paper.md) | `enoch-paper-0373` | yes | yes | 0 | false | 0 |
| [REAP Ragged Loader Real-Checkpoint Integration](reap-ragged-loader-real-checkpoint-integration/paper.md) | `enoch-paper-0102` | yes | yes | 2 | false | 2 |
| [Reasoning-Aware Quant Router Policy V2](reasoning-aware-quant-router-policy-v2/paper.md) | `enoch-paper-0253` | yes | yes | 0 | false | 0 |
| [Recap Token Supervision](recap-token-supervision/paper.md) | `enoch-paper-0279` | yes | yes | 0 | false | 0 |
| [Reduced-Planner Scratchpad Feedback Real Repo-QA Validation](reduced-planner-scratchpad-feedback-real-repo-qa-validation/paper.md) | `enoch-paper-0095` | yes | yes | 2 | false | 18 |
| [Rehydration Guide Student](rehydration-guide-student/paper.md) | `enoch-paper-0157` | yes | yes | 0 | false | 0 |
| [Rejection-Mode Targeted Abstention Refusal Tuning](rejection-mode-targeted-abstention-refusal-tuning/paper.md) | `enoch-paper-0075` | yes | yes | 2 | false | 20 |
| [Rejection-Span Distillation](rejection-span-distillation/paper.md) | `enoch-paper-0327` | yes | yes | 0 | false | 0 |
| [Repo Pulse Index Real-Repo Pilot](repo-pulse-index-real-repo-pilot/paper.md) | `enoch-paper-0237` | yes | yes | 0 | false | 0 |
| [Research Agent Treaty Protocol](research-agent-treaty-protocol/paper.md) | `enoch-paper-0172` | yes | yes | 0 | false | 0 |
| [Research Claim Unit Tests](research-claim-unit-tests/paper.md) | `enoch-paper-0174` | yes | yes | 0 | false | 0 |
| [Research Council Agenda Compiler Weekly Pilot](research-council-agenda-compiler-weekly-pilot/paper.md) | `enoch-paper-0257` | yes | yes | 0 | false | 0 |
| [Residual Conservation Pruner](residual-conservation-pruner/paper.md) | `enoch-paper-0195` | yes | yes | 0 | false | 0 |
| [Residue-Head Teacher Distillation for LBRC](residue-head-teacher-distillation-for-lbrc/paper.md) | `enoch-paper-0059` | yes | yes | 2 | false | 20 |
| [Resource-Bounded Agent Kernel](resource-bounded-agent-kernel/paper.md) | `enoch-paper-0040` | yes | yes | 2 | false | 20 |
| [Retrieval-Aware Evidence Packer Arbitration Benchmark](retrieval-aware-evidence-packer-arbitration-benchmark/paper.md) | `enoch-paper-0097` | yes | yes | 2 | false | 20 |
| [Retrieval-Conditioned Expert Expansion](retrieval-conditioned-expert-expansion/paper.md) | `enoch-paper-0126` | yes | yes | 0 | false | 0 |
| [Retrieval Honesty Loss](retrieval-honesty-loss/paper.md) | `enoch-paper-0341` | yes | yes | 0 | false | 0 |
| [Retrieval-Landmark KV Pins](retrieval-landmark-kv-pins/paper.md) | `enoch-paper-0308` | yes | yes | 0 | false | 0 |
| [Reuse-Fingerprint Student](reuse-fingerprint-student/paper.md) | `enoch-paper-0150` | yes | yes | 0 | false | 0 |
| [Reversible Prune Masks](reversible-prune-masks/paper.md) | `enoch-paper-0335` | yes | yes | 0 | false | 0 |
| [RL/Bandit Entropy-Gated Multi-Policy Speculation Router](rl-bandit-entropy-gated-multi-policy-speculation-router/paper.md) | `enoch-paper-0363` | yes | yes | 0 | false | 0 |
| [Robotic Procedure Verifier](robotic-procedure-verifier/paper.md) | `enoch-paper-0146` | yes | yes | 0 | false | 0 |
| [Rollback Audit and Escrow for Transactional Tool Calls](rollback-audit-and-escrow-for-transactional-tool-calls/paper.md) | `enoch-paper-0239` | yes | yes | 0 | false | 0 |
| [Router-Distilled Triton MLP Full-Model Integration](router-distilled-triton-mlp-full-model-integration/paper.md) | `enoch-paper-0024` | yes | yes | 2 | false | 20 |
| [SA-First Neural Fallback Router](sa-first-neural-fallback-router/paper.md) | `enoch-paper-0364` | yes | yes | 0 | false | 0 |
| [Safety Interlock Synthesizer](safety-interlock-synthesizer/paper.md) | `enoch-paper-0147` | yes | yes | 0 | false | 0 |
| [Salience-Backed Candidate Top-1 KV Prefill Packing Benchmark](salience-backed-candidate-top-1-kv-prefill-packing-benchmark/paper.md) | `enoch-paper-0058` | yes | yes | 2 | false | 12 |
| [Saliency Distillation Targets](saliency-distillation-targets/paper.md) | `enoch-paper-0168` | yes | yes | 0 | false | 0 |
| [Sandbox Risk Oracle Live Harness Calibration](sandbox-risk-oracle-live-harness-calibration/paper.md) | `enoch-paper-0231` | yes | yes | 0 | false | 0 |
| [Scaffold-Only Revision Mode](scaffold-only-revision-mode/paper.md) | `enoch-paper-0270` | yes | yes | 0 | false | 0 |
| [Schema-Anchor Adapter Tuning](schema-anchor-adapter-tuning/paper.md) | `enoch-paper-0152` | yes | yes | 0 | false | 0 |
| [Schema-Drift JSON Corpus](schema-drift-json-corpus/paper.md) | `enoch-paper-0109` | yes | yes | 2 | false | 0 |
| [Schema-Pinned JSON Cache](schema-pinned-json-cache/paper.md) | `enoch-paper-0328` | yes | yes | 0 | false | 0 |
| [Semantic Channel Naming](semantic-channel-naming/paper.md) | `enoch-paper-0355` | yes | yes | 0 | false | 0 |
| [Semantic Overlap Tax Generative LLM Public RAG Benchmark](semantic-overlap-tax-generative-llm-public-rag-benchmark/paper.md) | `enoch-paper-0076` | yes | yes | 2 | false | 12 |
| [Serving-Boundary Context Compression KV Benchmark](serving-boundary-context-compression-kv-benchmark/paper.md) | `enoch-paper-0245` | yes | yes | 0 | false | 0 |
| [Shared-Context Multi-Query Speculation](shared-context-multi-query-speculation/paper.md) | `enoch-paper-0325` | yes | yes | 0 | false | 0 |
| [Shared-Prompt Batcher Local-Server Validation](shared-prompt-batcher-local-server-validation/paper.md) | `enoch-paper-0072` | yes | yes | 2 | false | 15 |
| [Short-Model Long-Task Distillation](short-model-long-task-distillation/paper.md) | `enoch-paper-0272` | yes | yes | 0 | false | 0 |
| [Short-Train Long-Eval Prompt-Robust Tuning](short-train-long-eval-prompt-robust-tuning/paper.md) | `enoch-paper-0088` | yes | yes | 2 | false | 20 |
| [Similarity-Gated Value Quantization](similarity-gated-value-quantization/paper.md) | `enoch-paper-0306` | yes | yes | 0 | false | 0 |
| [Sink Token Stabilization](sink-token-stabilization/paper.md) | `enoch-paper-0153` | yes | yes | 0 | false | 0 |
| [Skill Preflight Gate Integration](skill-preflight-gate-integration/paper.md) | `enoch-paper-0238` | yes | yes | 0 | false | 0 |
| [Skill-to-Dataset Compiler](skill-to-dataset-compiler/paper.md) | `enoch-paper-0191` | yes | yes | 0 | false | 0 |
| [SLO Narrative Compressor](slo-narrative-compressor/paper.md) | `enoch-paper-0140` | yes | yes | 0 | false | 0 |
| [Small-Model Persona Context Orderer Generation Validation](small-model-persona-context-orderer-generation-validation/paper.md) | `enoch-paper-0004` | yes | yes | 2 | false | 6 |
| [SOBD: Survival-Optimized Block Diffusion](sobd-survival-optimized-block-diffusion/paper.md) | `enoch-paper-0169` | yes | yes | 0 | false | 0 |
| [Source-Citation KV Reserve](source-citation-kv-reserve/paper.md) | `enoch-paper-0313` | yes | yes | 0 | false | 0 |
| [Sparse-Value Late Materializer](sparse-value-late-materializer/paper.md) | `enoch-paper-0315` | yes | yes | 0 | false | 0 |
| [Sparse-Verifier Token Check](sparse-verifier-token-check/paper.md) | `enoch-paper-0329` | yes | yes | 0 | false | 0 |
| [Spec Decoder Domain Router](spec-decoder-domain-router/paper.md) | `enoch-paper-0198` | yes | yes | 0 | false | 0 |
| [SpecTr-Style OT Verifier for Multi-Candidate Trees](spectr-style-ot-verifier-for-multi-candidate-trees/paper.md) | `enoch-paper-0370` | yes | yes | 0 | false | 0 |
| [Speculation-Friendly LM Head Tuning](speculation-friendly-lm-head-tuning/paper.md) | `enoch-paper-0276` | yes | yes | 0 | false | 0 |
| [Speculation Tree Student](speculation-tree-student/paper.md) | `enoch-paper-0292` | yes | yes | 0 | false | 0 |
| [SpecVocab Hybrid for EAGLE-3 and DFlash](specvocab-hybrid-for-eagle-3-and-dflash/paper.md) | `enoch-paper-0200` | yes | yes | 0 | false | 0 |
| [SSA-Mamba Retrieval Bridge: Content-Routed SSM Memory for Million-Token Evidence](ssa-mamba-retrieval-bridge-content-routed-ssm-memory-for-million-token-evidence/paper.md) | `enoch-paper-0496` | yes | yes | 5 | true | 0 |
| [SSD + Goose + SA](ssd-goose-sa/paper.md) | `enoch-paper-0372` | yes | yes | 0 | false | 0 |
| [SSD Outcome Cache with Suffix-State Keys](ssd-outcome-cache-with-suffix-state-keys/paper.md) | `enoch-paper-0361` | yes | yes | 0 | false | 0 |
| [Stalled Agent Rescuer](stalled-agent-rescuer/paper.md) | `enoch-paper-0340` | yes | yes | 0 | false | 0 |
| [Strong-Draft Weak-Reviewer Transfer](strong-draft-weak-reviewer-transfer/paper.md) | `enoch-paper-0265` | yes | yes | 0 | false | 0 |
| [Structured Noise Injection Suite](structured-noise-injection-suite/paper.md) | `enoch-paper-0047` | yes | yes | 2 | false | 10 |
| [Sub-8GB Model Zoo Triage](sub-8gb-model-zoo-triage/paper.md) | `enoch-paper-0336` | yes | yes | 0 | false | 0 |
| [Swarm Counterfactual Logger](swarm-counterfactual-logger/paper.md) | `enoch-paper-0334` | yes | yes | 0 | false | 0 |
| [Swarm Heartbeat Bus](swarm-heartbeat-bus/paper.md) | `enoch-paper-0176` | yes | yes | 0 | false | 0 |
| [Sycophancy-Sensitive Escalation](sycophancy-sensitive-escalation/paper.md) | `enoch-paper-0263` | yes | yes | 0 | false | 0 |
| [Synthetic User Load Negotiator](synthetic-user-load-negotiator/paper.md) | `enoch-paper-0138` | yes | yes | 0 | false | 0 |
| [Task-Class Expert Reproduction](task-class-expert-reproduction/paper.md) | `enoch-paper-0125` | yes | yes | 0 | false | 0 |
| [Task-Gated Thinking Retention Controller](task-gated-thinking-retention-controller/paper.md) | `enoch-paper-0249` | yes | yes | 0 | false | 0 |
| [Task-Routed Context Allocation: Extractive Relevance vs Marginal Utility](task-routed-context-allocation-extractive-relevance-vs-marginal-utility/paper.md) | `enoch-paper-0251` | yes | yes | 0 | false | 0 |
| [Temperature-Conditional Acceptance Calibration](temperature-conditional-acceptance-calibration/paper.md) | `enoch-paper-0365` | yes | yes | 0 | false | 0 |
| [Test Rig Self-Maintainer](test-rig-self-maintainer/paper.md) | `enoch-paper-0148` | yes | yes | 0 | false | 0 |
| [Thermal Policy Optimizer](thermal-policy-optimizer/paper.md) | `enoch-paper-0137` | yes | yes | 0 | false | 0 |
| [Thinking-Pattern Bridge Adapter](thinking-pattern-bridge-adapter/paper.md) | `enoch-paper-0267` | yes | yes | 0 | false | 0 |
| [Token-Conditioned MLP Thinning](token-conditioned-mlp-thinning/paper.md) | `enoch-paper-0204` | yes | yes | 0 | false | 0 |
| [Token Importance Probe](token-importance-probe/paper.md) | `enoch-paper-0282` | yes | yes | 0 | false | 0 |
| [Token Rent for Examples](token-rent-for-examples/paper.md) | `enoch-paper-0002` | yes | yes | 2 | false | 20 |
| [Token-Type Importance Labels](token-type-importance-labels/paper.md) | `enoch-paper-0096` | yes | yes | 2 | false | 9 |
| [Tokenized Tiny-LM Duplicate Ratio Ablation](tokenized-tiny-lm-duplicate-ratio-ablation/paper.md) | `enoch-paper-0082` | yes | yes | 2 | false | 9 |
| [Tool-Boundary Non-Speculate Gate](tool-boundary-non-speculate-gate/paper.md) | `enoch-paper-0324` | yes | yes | 0 | false | 0 |
| [Tool Starvation Detector](tool-starvation-detector/paper.md) | `enoch-paper-0498` | yes | yes | 0 | false | 0 |
| [Trace Inspector Warm Session Operator Trial](trace-inspector-warm-session-operator-trial/paper.md) | `enoch-paper-0232` | yes | yes | 0 | false | 0 |
| [Trajectory Rulebook Distillation](trajectory-rulebook-distillation/paper.md) | `enoch-paper-0271` | yes | yes | 0 | false | 0 |
| [Trie-Guided Speculative JSON](trie-guided-speculative-json/paper.md) | `enoch-paper-0330` | yes | yes | 0 | false | 0 |
| [Uncertainty-Coverage Co-Estimator](uncertainty-coverage-co-estimator/paper.md) | `enoch-paper-0266` | yes | yes | 0 | false | 0 |
| [Upcycle Router Cold-Start Benchmark](upcycle-router-cold-start-benchmark/paper.md) | `enoch-paper-0124` | yes | yes | 0 | false | 0 |
| [Upcycle Timing Sweep Law](upcycle-timing-sweep-law/paper.md) | `enoch-paper-0223` | yes | yes | 0 | false | 0 |
| [Upcycled Expert Distillation Collapse](upcycled-expert-distillation-collapse/paper.md) | `enoch-paper-0128` | yes | yes | 0 | false | 0 |
| [Upcycled LoRA Expert Grafting](upcycled-lora-expert-grafting/paper.md) | `enoch-paper-0129` | yes | yes | 0 | false | 0 |
| [UTR Conflict-Update Final-Answer Schema Hardening](utr-conflict-update-final-answer-schema-hardening/paper.md) | `enoch-paper-0092` | yes | yes | 2 | false | 20 |
| [Value-Only Cold Storage](value-only-cold-storage/paper.md) | `enoch-paper-0320` | yes | yes | 0 | false | 0 |
| [Value-per-Joule Broker Online Canary on GB10 Endpoints](value-per-joule-broker-online-canary-on-gb10-endpoints/paper.md) | `enoch-paper-0012` | yes | yes | 2 | false | 13 |
| [Verification-Conditional Cache Restore](verification-conditional-cache-restore/paper.md) | `enoch-paper-0310` | yes | yes | 0 | false | 0 |
| [Verification Failure Clusters](verification-failure-clusters/paper.md) | `enoch-paper-0069` | yes | yes | 2 | false | 6 |
| [Verifier-Feature Acceptance Classifier](verifier-feature-acceptance-classifier/paper.md) | `enoch-paper-0304` | yes | yes | 0 | false | 0 |
| [vLLM Attention-Sink Retention 3B Continuous-Serving Stress Campaign](vllm-attention-sink-retention-3b-continuous-serving-stress-campaign/paper.md) | `enoch-paper-0060` | yes | yes | 5 | true | 0 |
| [VRAM Admission Controller](vram-admission-controller/paper.md) | `enoch-paper-0192` | yes | yes | 0 | false | 0 |
| [Wake-Gate Local Endpoint Harness Integration](wake-gate-local-endpoint-harness-integration/paper.md) | `enoch-paper-0023` | yes | yes | 2 | false | 15 |
| [Weak-Wikipedia Generative Answer Flattening Pilot](weak-wikipedia-generative-answer-flattening-pilot/paper.md) | `enoch-paper-0050` | yes | yes | 2 | false | 3 |
| [Web-State Replay Benchmark for Rewindable Sandboxes](web-state-replay-benchmark-for-rewindable-sandboxes/paper.md) | `enoch-paper-0094` | yes | yes | 2 | false | 2 |
| [Workflow-Aware Verifier Router Benchmark](workflow-aware-verifier-router-benchmark/paper.md) | `enoch-paper-0241` | yes | yes | 0 | false | 0 |
