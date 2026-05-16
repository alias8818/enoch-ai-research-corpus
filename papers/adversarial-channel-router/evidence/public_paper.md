# Adversarial Channel Router: Typed Authenticated Control-Plane Routing Prevents Cross-Channel Contamination from Transcript-Wrapper Prompts

> **AI Provenance Notice:** This draft was generated entirely by AI from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is claimed or implied.

---

## Abstract

We investigate whether typed, authenticated control-plane channel envelopes can prevent cross-channel contamination in multi-channel LLM agent routing, where a transcript-wrapper design that shares conversational context across channels may leak adversarial payloads from one channel into another. We evaluate this question across four tiers of increasing fidelity: a deterministic toy-model smoke test, a dependency-free agent harness simulating lossy summarization and shared scratchpad carryover, an OpenAI-compatible deterministic shim validating the adapter and concurrency pipeline, and a real local small LLM (Qwen2.5-0.5B-Instruct) served via a Transformers-backed OpenAI-compatible endpoint on a GB10 GPU. Across all tiers, typed control-plane routing produced zero cross-channel contamination. Transcript-wrapper routing produced contamination rates of 1.000 (deterministic), 0.2815 (agent harness), 1.000 (shim), and 0.2250 (real LLM). However, the real-LLM tier also revealed that typed prompts incurred a throughput penalty (1.88 vs. 4.63 chat requests/s) due to longer channel-scoped summaries. Sample sizes are small (40 probes in the real-LLM tier), only one model was tested, and the attacker model is simplified. The current project artifacts support the finding that typed authenticated channel envelopes can prevent a class of transcript-wrapper cross-channel contamination in the tested setting, but production workflow validation remains a separate follow-on effort.

## 1. Introduction

Multi-channel LLM agent systems increasingly route user interactions across distinct communication channels such as Discord, Telegram, and email. A common architectural pattern—the transcript-wrapper—shares a single conversational context or scratchpad across all channels, enabling the agent to maintain coherent multi-turn dialogue. However, this design introduces a security risk: adversarial payloads injected via one channel may persist in the shared transcript and be surfaced or acted upon in another channel, constituting cross-channel contamination.

This work examines an alternative architecture—a typed, authenticated control-plane router—that encapsulates each channel in a separate typed envelope with authentication metadata, preventing raw adversarial markers from persisting across channel boundaries. We pose the following hypothesis: typed authenticated channel envelopes prevent cross-channel contamination that occurs under transcript-wrapper routing.

We evaluate this hypothesis through a progressive series of experimental tiers, each increasing in fidelity from deterministic toy models to a real local small LLM, while preserving the same scenario set and scoring contract across tiers. This progressive approach allows us to isolate whether the security mechanism functions correctly in principle (deterministic tiers) and whether it survives the messier, non-deterministic behavior of an actual language model.

## 2. Method

### 2.1 Threat Model

We consider an adversary who can inject prompt-injection payloads into one communication channel (e.g., Discord) containing markers (`LEAK_*` tags) designed to persist in shared agent memory and be reproduced in responses on other channels (e.g., Telegram, email). The security invariant is that a typed control-plane router must not persist or reveal adversarial payloads across channels.

### 2.2 Scenario Generation

All tiers use the same deterministically generated scenario set (seed 7341), producing Discord, Telegram, and email attack messages containing `LEAK_*` markers. Each scenario generates two probes: one for the transcript-wrapper path and one for the typed path, yielding paired contamination observations.

### 2.3 Router Designs

**Transcript-wrapper baseline.** All channel messages are appended to a single shared transcript or scratchpad. The agent processes the full transcript when generating responses, allowing markers from one channel to appear in responses on another channel.

**Typed authenticated control-plane router.** Each message is encapsulated in a typed channel envelope with authentication metadata. The router enforces channel-scoped context: responses are generated using only the context from the requesting channel, and raw markers from other channels are redacted or excluded.

### 2.4 Experimental Tiers

**Tier 1: Deterministic toy-model smoke test.** A sentinel router pair (`SentinelTranscriptRouter`, `SentinelTypedRouter`) directly parses and routes markers without any language model. This tier validates the mechanism in isolation. Configuration: 1000 scenarios, seed 7341.

**Tier 2: Agent harness with lossy summarization.** A `LocalSummaryAgent` simulates lossy summarization, retrieval, and shared assistant scratchpad carryover—modeling the information-loss and persistence properties of a real agent without requiring an LLM runtime. Configuration: 2000 scenarios, seed 7341.

**Tier 3: OpenAI-compatible deterministic shim.** A project-local deterministic OpenAI-compatible server (`openai_compatible_shim.py`) validates the adapter, concurrency, and scoring pipeline. Configuration: 200 scenarios, seed 7341, concurrency 8.

**Tier 4: Real local small LLM.** A Transformers-backed OpenAI-compatible server (`openai_transformers_server.py`) serves `Qwen/Qwen2.5-0.5B-Instruct` on a GB10 GPU in bfloat16. A calibration run (5 scenarios, concurrency 1) precedes the benchmark (20 scenarios, concurrency 4). This tier tests whether a non-deterministic small LLM still leaks under transcript-wrapper prompts while typed prompts remain clean.

### 2.5 Metrics

- **Cross-channel contamination rate:** fraction of probes where a `LEAK_*` marker from one channel appears in the response for another channel.
- **Absolute reduction:** baseline contamination rate minus typed contamination rate.
- **Relative reduction:** absolute reduction divided by baseline contamination rate (undefined when baseline is zero).
- **Throughput:** chat requests per second.
- **Latency:** p50 and p95 per-request latency in milliseconds.
- **Resource utilization:** process RSS/PSS, MemAvailable, GPU utilization (nvidia-smi), SwapFree.

### 2.6 Regression Tests

Five unit tests are maintained across all tiers, verifying: (1) baseline sentinel contamination, (2) typed sentinel isolation, (3) agent-harness transcript-wrapper nontrivial leakage, (4) agent-harness typed isolation, and (5) typed OpenAI prompt redaction of raw `LEAK_*` markers.

## 3. Results

### 3.1 Tier 1: Deterministic Toy-Model Smoke Test

| Metric | Transcript-Wrapper | Typed Control Plane |
|--------|-------------------|-------------------|
| Contamination rate | 2000/2000 = 1.000 | 0/2000 = 0.000 |
| Absolute reduction | — | 1.000 |
| Throughput (samples/s) | 313,184.0 | 766,624.4 |
| p95 latency (ms) | 0.0062 | 0.0031 |
| Max RSS (KB) | 20,432 | — |

The deterministic tier confirms the mechanism works in principle: the sentinel transcript-wrapper always leaks, and the sentinel typed router never leaks. The typed path is also faster in this tier because it avoids the overhead of cross-channel context assembly.

### 3.2 Tier 2: Agent Harness with Lossy Summarization

| Metric | Transcript-Wrapper | Typed Control Plane |
|--------|-------------------|-------------------|
| Contamination rate | 1126/4000 = 0.2815 | 0/4000 = 0.0000 |
| Absolute reduction | — | 0.2815 |
| Throughput (samples/s) | 1,883.4 | 695,610.7 |
| p50 latency (ms) | 0.3992 | 0.0003 |
| p95 latency (ms) | 1.4530 | 0.0036 |
| CPU user time (s) | 3.1852 | 0.0086 |
| RSS/PSS (KB) | ~23,752 / 17,820 | — |

The agent harness introduces lossy summarization, which reduces the transcript-wrapper contamination rate from 1.000 to 0.2815—summarization does not preserve all markers, but it preserves enough to produce nontrivial leakage. The typed path remains at zero contamination. The large throughput difference reflects the agent harness's simulated summarization overhead on the transcript-wrapper path versus the typed path's simpler channel-scoped routing.

### 3.3 Tier 3: OpenAI-Compatible Deterministic Shim

| Metric | Transcript-Wrapper | Typed Control Plane |
|--------|-------------------|-------------------|
| Contamination rate | 400/400 = 1.0000 | 0/400 = 0.0000 |
| Absolute reduction | — | 1.0000 |
| Throughput (req/s) | 562.7 | 586.3 |
| p50 latency (ms) | 2.0090 | 1.9579 |
| p95 latency (ms) | 2.7530 | 2.7761 |
| Max RSS (KB) | 26,316 | — |
| Concurrency | 8 | 8 |

The shim tier validates the OpenAI-compatible adapter and concurrency pipeline. The deterministic shim always reproduces markers in transcript-wrapper mode and never reproduces them in typed mode, confirming the scoring pipeline functions correctly under concurrent load. Throughput and latency are comparable between the two paths at this tier because the shim's response generation is trivial.

### 3.4 Tier 4: Real Local Small LLM (Qwen2.5-0.5B-Instruct)

**Calibration** (5 scenarios, concurrency 1): transcript-wrapper contamination 2/10 = 0.2000; typed contamination 0/10 = 0.0000.

**Benchmark** (20 scenarios, concurrency 4):

| Metric | Transcript-Wrapper | Typed Control Plane |
|--------|-------------------|-------------------|
| Contamination rate | 9/40 = 0.2250 | 0/40 = 0.0000 |
| Absolute reduction | — | 0.2250 |
| Relative reduction | — | 1.0000 |
| Throughput (req/s) | 4.63 | 1.88 |
| p50 latency (ms) | 805.3 | 2,127.5 |
| p95 latency (ms) | 1,191.3 | 2,454.7 |
| Concurrency | 4 | 4 |

GPU utilization averaged 79.86% and peaked at 83% over 44 nvidia-smi samples. Server RSS/PSS was approximately 1,804,268 / 1,791,040 KB; client RSS/PSS approximately 26,180 / 18,014 KB. MemAvailable remained around 119,716,008 KB throughout the run; SwapFree was 0 KB.

The real LLM reproduces the core finding: transcript-wrapper routing leaks cross-channel markers at a measurable rate (22.5%), while typed routing produces zero contamination. However, a notable negative result is that typed prompts were substantially slower (1.88 vs. 4.63 req/s; p50 latency 2,127.5 vs. 805.3 ms). This occurs because the typed control-plane prompts instruct the model to generate longer channel-scoped summaries, increasing generation time even though no markers are leaked.

### 3.5 Summary Across Tiers

| Tier | Transcript-Wrapper Contamination | Typed Contamination | Absolute Reduction |
|------|--------------------------------|--------------------|--------------------|
| Deterministic smoke | 1.000 | 0.000 | 1.000 |
| Agent harness | 0.2815 | 0.0000 | 0.2815 |
| OpenAI shim | 1.0000 | 0.0000 | 1.0000 |
| Real LLM (Qwen 0.5B) | 0.2250 | 0.0000 | 0.2250 |

Typed routing achieved zero contamination in all tiers. Transcript-wrapper contamination varied from 0.2250 to 1.000 depending on the tier's fidelity: deterministic tiers always leak, while tiers with summarization or LLM generation leak at lower but still measurable rates.

## 4. Limitations

1. **Small sample sizes.** The real-LLM benchmark comprised only 40 probes (20 scenarios × 2 paths). The 22.5% contamination rate has a wide confidence interval, and the zero-contamination result for typed routing, while consistent across all tiers, cannot rule out rare leakage events at this sample size.

2. **Single model.** Only Qwen2.5-0.5B-Instruct was tested. Larger or differently-trained models may exhibit different contamination or compliance behaviors. No claim is made about generalization to other models.

3. **Simplified attacker model.** Scenarios use deterministic `LEAK_*` markers rather than natural-language adversarial payloads that might evade redaction through paraphrase, encoding, or steganographic techniques. A more capable adversary could attempt to bypass typed envelopes through indirect prompt injection strategies not modeled here.

4. **Single hardware platform.** All runs were conducted on a GB10 GPU with bfloat16 inference. Results may differ on other hardware, quantization schemes, or serving frameworks.

5. **Throughput penalty.** Typed routing incurred a 2.5× throughput penalty in the real-LLM tier due to longer channel-scoped summary generation. This trade-off between security and latency warrants further investigation, particularly for latency-sensitive applications.

6. **No production workflow validation.** The evidence addresses bounded toy-model, shim, agent-harness, and local small-LLM settings. Production deployments with real user traffic, multi-turn conversations, tool use, and retrieval-augmented generation may introduce contamination vectors not present in these experiments.

7. **Deterministic scenario generation.** All scenarios share the same seed (7341). While this enables controlled comparison across tiers, it limits the diversity of attack patterns tested.

8. **No comparison with alternative mitigations.** This work compares only transcript-wrapper and typed routing. Other approaches—input sanitization, output filtering, per-channel model instances, or sandboxed execution—were not evaluated.

## 5. Reproducibility Checklist

- **Source code:** `src/adversarial_channel_router.py`, `src/openai_compatible_shim.py`, `src/openai_transformers_server.py`
- **Test suite:** `tests/test_adversarial_channel_router.py` (5 tests, all passing)
- **Scenario seed:** 7341 (fixed across all tiers)
- **Model:** `Qwen/Qwen2.5-0.5B-Instruct` (Hugging Face, bfloat16)
- **Hardware:** GB10 GPU; ~122 GB available system memory; no swap
- **Python environment:** System Python 3 for tiers 1–3; project-local `.venv` with CUDA PyTorch/Transformers/FastAPI/Uvicorn for tier 4
- **CLI commands for each tier are recorded in the run notes** (see Referenced Artifacts)
- **Result files:** JSON outputs for each tier are preserved in the `results/` directory
- **GPU polling:** `nvidia-smi` samples recorded in `results/adversarial_channel_router_qwen_gpu_poll.csv`

## 6. Conclusion

We presented evidence from four experimental tiers that typed authenticated control-plane channel envelopes prevent cross-channel contamination in multi-channel LLM agent routing. In all tiers, typed routing produced zero contamination. Transcript-wrapper routing produced measurable contamination ranging from 22.5% (real LLM) to 100% (deterministic), confirming that shared-context architectures leak adversarial payloads across channel boundaries at rates that depend on the fidelity of the routing and generation pipeline.

A significant trade-off emerged in the real-LLM tier: typed routing was 2.5× slower than transcript-wrapper routing due to longer channel-scoped summary generation. This latency cost may be acceptable for security-critical applications but warrants optimization for latency-sensitive deployments.

The current project artifacts support the finding that typed authenticated channel envelopes can prevent a class of transcript-wrapper cross-channel contamination in the tested setting. However, the evidence is bounded by small sample sizes, a single small model, simplified attack patterns, and the absence of production workflow validation. External replication with larger models, more diverse attack strategies, and real-world agent workflows is needed before drawing stronger conclusions.

---

## Referenced Artifacts

### Result files
- `results/adversarial_channel_router_smoke.json` — Tier 1 deterministic smoke test output
- `results/adversarial_channel_router_agent_harness.json` — Tier 2 agent harness output
- `results/adversarial_channel_router_openai_shim.json` — Tier 3 OpenAI-compatible shim output
- `results/adversarial_channel_router_qwen_calibration.json` — Tier 4 calibration output
- `results/adversarial_channel_router_qwen_small_llm.json` — Tier 4 real LLM benchmark output
- `results/adversarial_channel_router_qwen_gpu_poll.csv` — GPU utilization samples during Tier 4

### Source files
- `src/adversarial_channel_router.py` — Main harness implementing all router variants and CLI
- `src/openai_compatible_shim.py` — Deterministic OpenAI-compatible fallback server
- `src/openai_transformers_server.py` — Transformers-backed OpenAI-compatible server
- `tests/test_adversarial_channel_router.py` — Regression test suite (5 tests)

### Project metadata and decision artifacts
- `run_notes.md` — Detailed execution log across all four tiers
- `.omx/project_decision.json` — Project decision: `finalize_positive`, hypothesis `supported`, confidence `high`, evidence strength `strong`
- `.omx/metrics.json` — Session metrics
- `.omx/project.json` — Project configuration

### Paper artifacts
- `papers/.../claim_ledger.json` — Claim audit with confidence levels and allowed/forbidden wording
- `papers/.../evidence_bundle.json` — Aggregated evidence bundle
- `papers/.../paper_manifest.json` — Written artifact manifest
