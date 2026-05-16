# Home Lab Agent Orchestrator: Dry-Run Safety Governance and Evidence Reduction for Local LLM-Based Homelab Incident Diagnosis

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has approved this content.

---

## Abstract

We present a bounded experimental study of a policy-gated agent architecture for homelab infrastructure incident diagnosis. The architecture combines a strict dry-run safety gate that blocks all unsafe or confirmation-required actions with a deterministic evidence-reduction pipeline that preprocesses high-entropy log observations before presentation to a local language model. Across a progressive series of smoke evaluations on synthetic homelab incidents (Proxmox/ZFS, Frigate, Unraid Docker, LAN DHCP), we observe that the dry-run gate maintained a 1.0 unsafe-action block rate under all tested conditions, including when a real local LLM (Phi-4-mini-instruct, Q4_K_M, served via llama.cpp on GB10 hardware) proposed unsafe remediation actions. However, the same real model's diagnosis accuracy collapsed from 1.0 on clean and moderately noisy logs to 0.0–0.25 on high-entropy messy log bundles. A deterministic evidence-reduction pass—scoring log lines by diagnosis-signal terms, retaining high-signal lines per chunk, and emitting compact evidence packets—recovered diagnosis accuracy to 1.0 on both direct and service-backed evaluation paths while preserving the perfect unsafe-action block rate. These results are bounded to four synthetic incident fixtures, a single small quantized model, and GB10-class hardware; they do not establish that the method generalizes to real captured homelab logs, larger models, or production deployments.

---

## 1. Introduction

Home lab operators managing heterogeneous infrastructure (hypervisors, NVRs, container hosts, network appliances) face recurring incident diagnosis tasks that are time-consuming when performed manually. Language-model-based agent architectures offer a potential automation path, but any agent that proposes infrastructure mutations (restarts, reboots, pool scrubs, container recreations) without human confirmation poses a safety risk. The central tension is between diagnostic utility and operational safety.

This study investigates two mechanisms intended to address this tension:

1. **A strict dry-run policy gate** (`DryRunPolicy`) that intercepts all proposed actions, classifies them as safe or unsafe/confirmation-required, and blocks unsafe actions before execution.
2. **A deterministic evidence-reduction pipeline** that compresses high-entropy log observations into bounded evidence packets before model inference, aiming to preserve diagnostic signal while reducing prompt length and noise-induced errors.

We evaluate these mechanisms through a progressive series of smoke evaluations, starting from deterministic rule-based baselines and advancing through a real local LLM endpoint, high-entropy log stress tests, and evidence-reduction recovery experiments. The study is deliberately bounded: all incidents are synthetic fixtures, the model is a single small quantized checkpoint, and no real homelab services or captured logs are involved.

---

## 2. Method

### 2.1 Incident Scenarios

Four synthetic homelab incident fixtures are defined in `harness/scenarios.py`:

| Scenario | Domain | Root Cause |
|---|---|---|
| Proxmox/ZFS | Hypervisor/storage | ZFS pool degradation |
| Frigate | NVR | Camera feed processing failure |
| Unraid Docker | Container host | Container restart loop |
| LAN DHCP | Network | DHCP scope exhaustion |

Each scenario carries typed incident metadata, a set of expected diagnosis tags, and a classification of which proposed actions are unsafe (e.g., pool scrub, container recreation, host reboot) versus safe (e.g., read-only status checks, log collection, note-taking).

### 2.2 Orchestrator and Dry-Run Policy Gate

The orchestrator (`harness/orchestrator.py`) implements a transparent rule-based diagnosis layer that maps observed symptoms to diagnoses. All proposed actions—whether from rules or from a model loop—pass through `DryRunPolicy`, which:

- Classifies each action as safe or unsafe/confirmation-required.
- Blocks all unsafe actions unconditionally.
- Logs blocked actions for post-hoc review.
- Never executes any mutation against real or fake infrastructure.

This gate is invariant across all evaluation lanes.

### 2.3 Model Loop Architecture

The model-in-the-loop path (`harness/model_loop.py`) constructs a structured prompt containing the incident observations, the allowed diagnosis taxonomy, and action constraints, then submits it to an OpenAI-compatible chat completions endpoint. The model returns a JSON payload with a diagnosis string and a list of proposed actions. Malformed JSON responses are handled by recovering any valid diagnosis substring while quarantining unparsed actions to `unknown_requires_human_triage`.

The OpenAI-compatible client (`harness/openai_compatible.py`) supports configurable endpoint timeouts, `max_tokens` caps, and JSON response-format hints to prevent real models from running until client timeout.

### 2.4 Evidence Reduction Pipeline

The evidence reducer (`harness/evidence_reduction.py`) processes high-entropy log observations before model inference:

1. **Chunking**: Log lines are divided into fixed-size chunks.
2. **Scoring**: Each line is scored by the count of exact diagnosis-signal terms from the allowed taxonomy.
3. **Selection**: High-signal lines are retained per chunk; low-signal lines are discarded.
4. **Summary emission**: Candidate-evidence score summaries and the strongest exact-term candidate are emitted as a compact evidence packet.

The reducer is deterministic: given the same input log bundle and taxonomy, it always produces the same reduced output. When the model returns an unknown or malformed diagnosis, the reducer's strongest candidate is used as a deterministic fallback.

### 2.5 Noisy and Messy Log Generators

Two levels of log perturbation are implemented:

- **Noisy logs** (`harness/noisy_logs.py`): Add irrelevant service chatter and a generic destructive reboot distractor plus benign note-taking action to the base incident observations.
- **Messy logs** (`harness/messy_logs.py`): Generate 100+ line high-entropy bundles per scenario with timestamped service chatter, sparse correlated evidence, red herrings (e.g., unrelated service warnings, rotated-log noise), scenario-specific distractors, and extra unsafe distractor actions.

### 2.6 Fake Homelab Services

`harness/fake_services.py` exposes read-only HTTP endpoints mimicking Proxmox, Frigate, Unraid, and router status and log interfaces:

- `/health`, `/services`, `/services/{scenario}/status`, `/services/{scenario}/logs`
- Supports `log_profile="messy"` mode for high-entropy log delivery over HTTP.

A containerized execution script (`scripts/run_container_fake_services.sh`) enables repeatable Docker-based fake-service runs.

### 2.7 Evaluation Lanes

The benchmark (`harness/run_eval.py`) evaluates the following comparison lanes:

| Lane | Diagnosis Source | Log Profile | Service Path |
|---|---|---|---|
| `clean_rule` | Rule-based | Clean | Direct |
| `noisy_rule` | Rule-based | Noisy | Direct |
| `noisy_openai_compatible_model_loop` | Model | Noisy | Direct |
| `service_backed_openai_model_loop` | Model | Clean | HTTP fake services |
| `messy_openai_compatible_model_loop` | Model | Messy | Direct |
| `messy_service_backed_openai_model_loop` | Model | Messy | HTTP fake services |
| `reduced_messy_openai_compatible_model_loop` | Model + reducer | Messy | Direct |
| `reduced_messy_service_backed_openai_model_loop` | Model + reducer | Messy | HTTP fake services |

Metrics recorded per lane: diagnosis accuracy, unsafe-action block rate, average tag recall, samples per second, and (for service-backed lanes) p50/p95 service latency.

---

## 3. Results

### 3.1 Deterministic Baseline (Rule-Based)

The rule-based orchestrator achieved perfect scores on clean and noisy synthetic incidents:

| Lane | Diagnosis Accuracy | Unsafe-Action Block Rate | Avg Tag Recall |
|---|---|---|---|
| `clean_rule` | 1.0 | 1.0 | 1.0 |
| `noisy_rule` | 1.0 | 1.0 | 1.0 |

These results are expected: the rule-based layer was designed to match the synthetic fixtures. They serve as a ceiling reference for model-loop lanes.

### 3.2 Toy Model Loop (In-Process Deterministic Stand-In)

The initial `ToyTriageModel`—a deterministic in-process stand-in that intentionally proposed an unsafe generic remediation—confirmed that the dry-run gate blocks unsafe model-proposed actions:

| Lane | Diagnosis Accuracy | Unsafe-Action Block Rate | Avg Tag Recall |
|---|---|---|---|
| `noisy_toy_model_loop` | 1.0 | 1.0 | 0.5 |

The reduced tag recall (0.5 vs 1.0) reflects the toy model's limited action proposal vocabulary, not a safety failure.

### 3.3 OpenAI-Compatible HTTP Endpoint (Fake Endpoint)

Replacing the in-process toy model with an HTTP client traversing a project-local fake OpenAI-compatible endpoint preserved all metrics:

| Lane | Diagnosis Accuracy | Unsafe-Action Block Rate | Samples/Sec |
|---|---|---|---|
| `noisy_openai_compatible_model_loop` | 1.0 | 1.0 | 7.70 |

### 3.4 Service-Backed Evaluation (In-Process and Containerized)

Adding fake homelab HTTP service boundaries maintained diagnosis and safety metrics while introducing measurable service latency:

| Configuration | Diagnosis Accuracy | Unsafe-Action Block Rate | Samples/Sec | p50 Latency | p95 Latency |
|---|---|---|---|---|---|
| In-process fake services | 1.0 | 1.0 | 943.72 | 0.338 ms | 0.577 ms |
| Containerized fake services | 1.0 | 1.0 | 647.41 | 0.604 ms | 0.694 ms |

Containerized execution reduced throughput by ~31% and increased latency by ~79% at p50, consistent with Docker networking overhead. Process max RSS was 24,064 KB; load average (1 min) was 0.177.

### 3.5 Real Local LLM (Phi-4-mini-instruct via llama.cpp on GB10)

Connecting the harness to a real cached local model (Phi-4-mini-instruct-Q4_K_M, 2.4 GB, served via llama.cpp on GB10 hardware) yielded correct diagnoses on clean, noisy, and service-backed clean lanes:

| Lane | Diagnosis Accuracy | Unsafe-Action Block Rate | Samples/Sec |
|---|---|---|---|
| `clean_rule` | 1.0 | 1.0 | — |
| `noisy_rule` | 1.0 | 1.0 | — |
| `noisy_openai_compatible_model_loop` | 1.0 | 1.0 | 0.612 |
| `service_backed_openai_model_loop` | 1.0 | 1.0 | 0.620 |

The model proposed several unsafe/remediation-shaped actions; all were blocked by the dry-run gate. Generation throughput was approximately 70–76 tokens/sec. Resource snapshot: process max RSS 31,156 KB, load average (1 min) 1.285, MemAvailable 117,873,872 KB, SwapFree 0 KB.

### 3.6 High-Entropy Messy Log Stress Test (Negative Result)

When the real local model was presented with 100+ line high-entropy messy log bundles, **diagnosis accuracy collapsed**:

| Lane | Diagnosis Accuracy | Unsafe-Action Block Rate | Samples/Sec |
|---|---|---|---|
| `messy_openai_compatible_model_loop` (direct) | **0.0** | 1.0 | 0.181 |
| `messy_service_backed_openai_model_loop` (service-backed) | **0.25** | 1.0 | 0.152 |

The dry-run gate remained robust (1.0 block rate), but the model failed to identify correct diagnoses in 3–4 of 4 scenarios. Raw messy prompts were approximately 3.6k tokens. The service-backed lane partially recovered one case (accuracy 0.25 vs 0.0), possibly due to slight differences in observation formatting through the HTTP service boundary. This is a negative result: a small quantized local model cannot reliably diagnose incidents from high-entropy log presentations without preprocessing.

### 3.7 Evidence Reduction Recovery

Applying the deterministic evidence-reduction pipeline before model inference recovered diagnosis accuracy on messy logs:

| Lane | Diagnosis Accuracy | Unsafe-Action Block Rate | Samples/Sec | p50 Latency | p95 Latency |
|---|---|---|---|---|---|
| Raw messy direct | 0.25 | 1.0 | 0.1607 | — | — |
| **Reduced messy direct** | **1.0** | **1.0** | **0.3422** | — | — |
| Raw messy service-backed | 0.25 | 1.0 | 0.1598 | 0.987 ms | 2.951 ms |
| **Reduced messy service-backed** | **1.0** | **1.0** | **0.3415** | 0.975 ms | 2.767 ms |

Evidence reduction compressed prompts from ~3.6k tokens to ~0.9k–1.2k tokens and approximately doubled throughput (0.16 → 0.34 samples/sec), consistent with reduced prompt evaluation cost. Clean, noisy, and service non-messy baselines remained at diagnosis accuracy 1.0 and unsafe-action block rate 1.0.

The 12 regression tests in `test_harness.py` all passed after the evidence-reduction implementation.

---

## 4. Limitations

1. **Synthetic incidents only.** All four scenarios are hand-crafted fixtures with known root causes and structured observations. No real captured homelab logs were tested. Diagnosis accuracy on genuine production logs with unknown failure modes remains unestablished.

2. **Single small quantized model.** Only Phi-4-mini-instruct-Q4_K_M (2.4 GB) was tested. Larger or differently trained models may exhibit different accuracy/noise-sensitivity profiles. The evidence-reduction recovery may not be necessary for models with longer effective context or stronger instruction-following.

3. **Single hardware configuration.** All real-model runs were conducted on GB10-class hardware with llama.cpp serving. Throughput and latency numbers are not portable to other accelerators or serving stacks.

4. **Deterministic evidence reduction is taxonomy-dependent.** The reducer scores lines by exact matches to allowed-diagnosis signal terms. It will not surface evidence for failure modes outside the predefined taxonomy. In production, the taxonomy would need to be extended or made adaptive, which reintroduces the risk of missed diagnoses.

5. **Toy model and fake endpoint lanes are not model evaluations.** The in-process `ToyTriageModel` and project-local fake OpenAI-compatible endpoint lanes verify harness plumbing and safety-gate behavior, not model capability. Their perfect scores should not be interpreted as evidence of model competence.

6. **No live service validation.** Fake homelab services expose static, deterministic responses. Real Proxmox, Frigate, Unraid, and router APIs would present variable response times, authentication, error states, and schema drift that are not represented here.

7. **Safety gate is conservative by design.** The `DryRunPolicy` blocks all actions classified as unsafe or confirmation-required. This prevents harm but also prevents any autonomous remediation. The architecture as tested is a diagnostic assistant, not an autonomous operator.

8. **Tag recall reduction.** The model-loop lanes consistently show avg_tag_recall of 0.5 on noisy/messy inputs, indicating that the model proposes fewer distinct action tags than the rule-based baseline. This may reflect prompt constraints or model conservatism rather than a deficiency, but it limits the action space available for human review.

9. **No comparison against human operators.** The manual baseline estimate (105 minutes) and agent estimate (25 minutes, later 72 minutes) are rough projections, not measured human-subject data. Time-saved claims are illustrative, not empirical.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Code available in project directory | Yes: `harness/` modules, `test_harness.py`, `scripts/` |
| Synthetic scenario definitions provided | Yes: `harness/scenarios.py` (4 fixtures) |
| Deterministic evidence reducer specified | Yes: `harness/evidence_reduction.py` |
| Model loop with OpenAI-compatible client | Yes: `harness/model_loop.py`, `harness/openai_compatible.py` |
| Fake homelab service endpoints | Yes: `harness/fake_services.py` |
| Noisy and messy log generators | Yes: `harness/noisy_logs.py`, `harness/messy_logs.py` |
| Benchmark runner with JSON output | Yes: `harness/run_eval.py` |
| Regression test suite | Yes: `test_harness.py` (12 tests, all passing) |
| Result JSON files recorded | Yes: 8 files in `results/` |
| Real-model endpoint reproducibility | Partial: requires cached GGUF model + llama.cpp server; model path and server launch documented in run notes |
| Hardware specification | GB10-class, 20 CPUs visible to Docker, ~118 GB available memory |
| Random seeds / determinism | Rule-based and reducer lanes are deterministic; real-model outputs may vary across runs |
| External dependencies | Python 3, pytest, Docker (for containerized fake services), llama.cpp (for real-model lane) |

---

## 6. Conclusion

This bounded study provides evidence that a strict dry-run policy gate can reliably block unsafe actions proposed by a local language model across clean, noisy, and high-entropy log conditions, with an unsafe-action block rate of 1.0 in all tested lanes. However, the same gate does not solve the diagnosis accuracy problem: a small quantized local model (Phi-4-mini-instruct-Q4_K_M) achieved 1.0 diagnosis accuracy on clean and moderately noisy synthetic logs but collapsed to 0.0–0.25 accuracy on high-entropy messy log bundles. A deterministic evidence-reduction pipeline recovered accuracy to 1.0 on both direct and service-backed evaluation paths, approximately halving prompt token count and doubling throughput in the process.

These findings are specific to four synthetic incident fixtures, a single model checkpoint, and GB10-class hardware. The evidence-reduction mechanism depends on a predefined diagnosis taxonomy and has not been tested against real captured homelab logs or failure modes outside the taxonomy. The project decision recommends finalizing this bounded experiment positive and continuing only if real captured homelab logs become available for replay validation.

---

## Referenced Artifacts

### Result files
- `results/summary.md`
- `results/smoke_eval.json`
- `results/smoke_eval_evidence_reduced_real_phi.json`
- `results/smoke_eval_evidence_reduced_fake.json`
- `results/smoke_eval_messy_real_phi.json`
- `results/smoke_eval_messy_fake.json`
- `results/smoke_eval_real_phi.json`
- `results/smoke_eval_container_services.json`

### Source and configuration files
- `harness/scenarios.py` — incident fixture definitions
- `harness/orchestrator.py` — rule-based diagnosis and DryRunPolicy gate
- `harness/model_loop.py` — model-in-the-loop agent with malformed-JSON fallback
- `harness/openai_compatible.py` — OpenAI-compatible HTTP client and fake endpoint
- `harness/evidence_reduction.py` — deterministic chunked evidence reducer
- `harness/noisy_logs.py` — noisy log bundle generator
- `harness/messy_logs.py` — high-entropy messy log bundle generator
- `harness/fake_services.py` — fake homelab HTTP service endpoints
- `harness/run_eval.py` — benchmark runner with multi-lane comparison
- `test_harness.py` — regression test suite (12 tests)
- `scripts/run_container_fake_services.sh` — containerized fake-service execution

### Decision and metadata files
- `.omx/project_decision.json` — project decision (finalize_positive)
- `.omx/metrics.json` — session metrics
- `run_notes.md` — detailed execution log
- `papers/source-record-redacted/claim_ledger.json` — claim audit
- `papers/source-record-redacted/evidence_bundle.json` — evidence bundle
