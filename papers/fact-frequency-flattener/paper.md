# Fact Frequency Flattener: A Prompt-Level Controller for Reducing Entity Repetition in Batch Factual Generation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, evidence bundles, claim ledgers, and decision records). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

Repeated open-ended factual generation from language models tends to collapse onto a small set of high-frequency entities, limiting the coverage of batch-generated factual corpora. We investigate a lightweight prompt-level controller—the Fact Frequency Flattener—that maintains a histogram of previously emitted fact subjects and steers subsequent generations toward underrepresented categories. In a prototype experiment using a locally hosted Qwen2.5-7B-Instruct (Q4_K_M) model generating country-fact pairs (N=36 per condition), the flattener increased unique country count from 9 to 34, raised country entropy by 3.30 bits, reduced top-country share from 0.694 to 0.056, and achieved exact uniformity across six continent buckets with 100% target-continent adherence. These results support the viability of prompt/controller-level frequency flattening for improving coverage in batch factual generation. However, important caveats remain: the experiment uses a single model and prompt family, does not verify the semantic truth of generated facts, and is limited to a country-continent ontology. The result is a llama.cpp hook-prototype validation, not a production-scale benchmark. Cross-model replication and retrieval-backed fact verification are necessary before drawing broader conclusions.

## 1. Introduction

When language models are prompted repeatedly for open-ended factual content, the generated outputs tend to concentrate on a small number of high-frequency, salient entities. This phenomenon—which we term *factual collapse*—limits the coverage and diversity of batch-generated factual corpora. The problem is relevant to evaluation dataset construction, synthetic data generation, and knowledge probing, where representative coverage across a factual domain is often more important than raw generation volume.

Existing approaches to increasing output diversity operate primarily at the sampling level (temperature, top-p, top-k) or through fine-tuning. These methods address token-level or distribution-level variance but do not directly target the semantic-level entity repetition that arises from the model's internal frequency prior—the tendency to preferentially generate commonly associated entities regardless of sampling parameters.

We propose and evaluate a complementary approach: a prompt-level controller that tracks which factual subjects have already been emitted and explicitly directs the model toward underrepresented subject categories in subsequent prompts. The controller requires no modification to model weights, logits, or sampling parameters; it operates entirely through prompt construction.

The core hypothesis is that a lightweight external histogram over selected fact-subject facets (e.g., the continent of a generated country) can substantially reduce entity-level repetition and improve distributional coverage. We test this hypothesis in a bounded prototype experiment using a single locally hosted model and a country-fact generation task, measuring both entity-level and category-level distributional properties.

## 2. Method

### 2.1 Model and Runtime

All experiments used a locally hosted Qwen2.5-7B-Instruct model quantized to Q4_K_M format (GGUF), sourced from the `bartowski` repository. The model was served via `llama-server` built from the llama.cpp codebase, launched with full CUDA offload (`-ngl 99`) and a context window of 2048 tokens on a GB10 machine. The server listened on `<loopback-redacted>:8123`.

This configuration constitutes a llama.cpp hook-prototype setup: the controller communicates with the model exclusively through the standard OpenAI-compatible completion API exposed by `llama-server`, with no custom logits hooks, sampler modifications, or model patches.

### 2.2 Task Design

The task was open-ended country-fact generation. Each generation call asked the model to choose one sovereign country and state one concise true fact about it. The base prompt was identical across all calls within a condition; the flattened condition appended steering instructions derived from the controller's histogram state (described below).

### 2.3 Conditions

**Baseline condition.** The same prompt was issued N=36 times with no history or steering. The model received no information about previously generated countries.

**Flattened condition.** A Python controller maintained two data structures across calls: (1) a set of previously generated country names, and (2) a histogram of continent counts. Before each call, the controller identified the continent with the fewest generated countries so far (breaking ties arbitrarily) and appended an instruction to the prompt requesting that the model generate a country from that underrepresented continent and avoid any previously used country names.

### 2.4 Evaluation Metrics

We computed the following metrics per condition:

- **Valid mapped countries**: count of generations where the output could be parsed and mapped to a known country.
- **Unique countries**: number of distinct countries generated.
- **Country entropy**: Shannon entropy in bits over the country frequency distribution.
- **Top-country share**: proportion of generations occupied by the single most frequent country.
- **Continent entropy / max-6**: normalized entropy over the six-continent distribution (maximum 1.0 for uniform).
- **Continent total variation (TV) distance to uniform**: $\frac{1}{2}\sum_{c=1}^{6}|p_c - \frac{1}{6}|$, where 0 indicates perfect uniformity.
- **Target-continent hit rate** (flattened condition only): fraction of generations where the model's output country belonged to the controller's requested continent.

### 2.5 Procedure

A smoke test (N=6 per condition) was run first to verify pipeline correctness. The full evaluation then ran N=36 per condition (72 total generations). The Python driver (`scripts/fact_frequency_flattener_eval.py`) recorded raw generations, timings, and computed metrics. Environment telemetry (GPU utilization, memory, temperature) was captured before and after the run.

No explicit random seed was fixed. The model's sampling behavior is stochastic, so exact numerical results will vary across runs; the directional pattern (baseline collapse, flattener coverage increase) is expected to be robust for this model-prompt combination, but this expectation has not been statistically validated across multiple reruns.

## 3. Results

### 3.1 Entity-Level Diversity

| Metric | Baseline | Flattened | Delta |
|---|---:|---:|---:|
| Valid mapped countries | 36/36 | 36/36 | 0 |
| Unique countries | 9 | 34 | +25 |
| Country entropy (bits) | 1.757 | 5.059 | +3.301 |
| Top-country share | 0.694 | 0.056 | −0.639 |

In the baseline condition, the model collapsed heavily onto a single entity: Japan appeared in 25 of 36 generations (69.4%). Only 9 unique countries were produced across 36 calls. The flattener reduced this concentration substantially, producing 34 unique countries with a top-country share of 5.6% (2 occurrences of the most frequent country).

The magnitude of the baseline collapse is striking but may be model- and prompt-specific. Whether other models exhibit comparable collapse under identical prompts, or whether this particular prompt elicits unusually strong anchoring on Japan, cannot be determined from a single-model experiment.

### 3.2 Category-Level Distribution

| Metric | Baseline | Flattened | Delta |
|---|---:|---:|---:|
| Continent entropy / max-6 | 0.528 | 1.000 | +0.472 |
| Continent TV distance to uniform | 0.556 | 0.000 | −0.556 |
| Target-continent hit rate | n/a | 1.000 | n/a |

The baseline condition's continent distribution was highly skewed. The flattener achieved exact uniformity: 6 countries per continent across all 6 continents, yielding a TV distance of 0.000 to the uniform distribution. Every generation in the flattened condition produced a country from the controller's requested continent (hit rate = 1.000).

The perfect target-continent hit rate of 1.000 is notable but should be interpreted cautiously. At N=36 with 6 continents, the controller requests 6 countries per continent. The model's instruction-following capability for this specific steering task appears strong, but the sample size is small and the task is relatively constrained (selecting from a known set of ~195 sovereign countries mapped to 6 continents). Performance on more open-ended or finer-grained steering tasks remains unknown.

### 3.3 System Performance

The full N=72 generation run completed in 1:09.11 wall time for the Python driver (excluding server load time). The GB10 system reported 95% GPU utilization, 45W power draw, and 56°C GPU temperature during the run. Memory available decreased from 122,581,092 kB to 116,837,788 kB while the server was active, with the server process consuming approximately 4,733 MiB. No out-of-memory events or early memory pressure were observed. Swap was disabled (SwapTotal: 0 kB) as expected.

These system metrics confirm that the prototype ran without resource contention on this hardware, but they do not constitute a production throughput benchmark.

## 4. Limitations

1. **Single model.** All results come from one locally hosted model (Qwen2.5-7B-Instruct Q4_K_M). Whether the flattener achieves comparable coverage gains on other models, sizes, or quantization levels is unknown. Models with weaker instruction-following may exhibit lower target-continent hit rates.

2. **Single prompt family.** The experiment uses one specific country-fact generation prompt. The degree of baseline collapse (Japan at 69.4%) may be prompt- and model-specific. Cross-prompt-family replication is needed before making broad claims about factual collapse as a general phenomenon or the flattener as a general remedy.

3. **Narrow ontology.** The subject facet is limited to country/continent. Whether frequency flattening generalizes to richer or less structured ontologies (chemical elements, historical events, scientific concepts) remains untested. The controller's design assumes a known, discrete facet taxonomy; extending to open-vocabulary or hierarchical facets would require additional mechanism.

4. **No semantic fact verification.** The evaluation verifies JSON parseability, country name validity, and continent-bucket adherence. It does not assess whether the generated factual statements are semantically true. A model that reliably selects underrepresented countries but fabricates facts about them would score well on all reported metrics while being factually unreliable. This is a significant gap: improved coverage without truthfulness is not a sufficient result for most practical applications.

5. **Controller-level, not model-level.** The flattener operates as an external prompt controller. It does not modify logits, sampling parameters, or model weights. Its effectiveness depends on the model's instruction-following capability; less compliant models may ignore steering instructions, yielding lower hit rates without any diagnostic signal.

6. **Small sample size and no repeated runs.** N=36 per condition provides a clear directional signal but limited statistical power for estimating effect sizes precisely. No repeated runs with different random seeds were performed, so we cannot report variance across runs or construct confidence intervals.

7. **No comparison to alternative diversity methods.** The experiment does not compare the flattener against temperature scaling, nucleus sampling adjustments, repetition penalties, or other diversity-promoting techniques. The flattener may be complementary to, redundant with, or inferior to these approaches; the current data do not distinguish among these possibilities.

8. **Prototype status.** This is a llama.cpp hook-prototype validation on a single machine with a single model. It is not a production-scale benchmark, a cross-platform evaluation, or a CUDA copy calibration. Generalization claims are not supported by the current evidence.

## 5. Reproducibility Checklist

- **Model**: Qwen2.5-7B-Instruct Q4_K_M (GGUF), sourced from `bartowski` on Hugging Face.
- **Runtime**: llama.cpp `llama-server`, built locally, launched with `-ngl 99 -c 2048 --port 8123 --host <loopback-redacted>`.
- **Hardware**: GB10 machine with CUDA-capable GPU; swap disabled; ~117 GB RAM available during run.
- **Script**: `scripts/fact_frequency_flattener_eval.py` — accepts `--n` and `--outdir` arguments.
- **Exact command**: `python3 scripts/fact_frequency_flattener_eval.py --n 36 --outdir results/fact_frequency_flattener_full`
- **Randomness**: No explicit random seed was fixed. Exact numerical results will vary across runs.
- **Raw outputs**: Available in `results/fact_frequency_flattener_full/raw_generations.jsonl`.
- **Timings**: Available in `results/fact_frequency_flattener_full/timings.jsonl`.
- **Metrics**: Available in `results/fact_frequency_flattener_full/metrics.json`.
- **Artifact integrity**: SHA-256 hashes recorded in `results/artifact_sha256.txt`.
- **Server logs**: `logs/server_for_full.log`.
- **Environment telemetry**: `logs/environment_20260430T112848.log`, `logs/fff_full_command_20260430T113258.log`.
- **Smoke test**: `logs/fff_smoke.log`, `logs/server_for_smoke.log`.

## 6. Conclusion

The Fact Frequency Flattener—a prompt-level controller that tracks previously generated fact subjects and steers toward underrepresented categories—produced a substantial improvement in entity-level and category-level coverage in a prototype experiment with Qwen2.5-7B-Instruct. Unique countries increased from 9 to 34 out of 36, country entropy rose by 3.30 bits, and continent distribution became exactly uniform with perfect target-continent adherence.

These results support the hypothesis that frequency flattening is viable as a controller technique for reducing repeated high-frequency factual subjects in batch generation, without requiring model modification. The evidence strength is classified as *local LLM smoke and calibrated run*—sufficient to establish a positive directional signal but insufficient for broad generalization claims.

The most important unresolved question is whether improved subject coverage preserves factual truthfulness. The current experiment does not address this: it verifies structural properties of the outputs (valid country names, correct continent mapping) but not the semantic accuracy of the generated facts. A controller that diversifies subjects while the model fabricates details would achieve high coverage metrics but fail at the underlying goal of generating useful factual content.

Recommended next steps are: (1) pairing the flattener with retrieval-backed fact verification to assess whether improved coverage preserves truthfulness; (2) replicating across multiple local models and multiple fact domains (elements, historical events, scientific facts); (3) comparing against alternative diversity-promoting methods to situate the flattener's contribution relative to established techniques; and (4) conducting repeated runs with fixed seeds to estimate run-to-run variance and construct confidence intervals.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Evaluation script | `scripts/fact_frequency_flattener_eval.py` |
| Metrics | `results/fact_frequency_flattener_full/metrics.json` |
| Raw generations | `results/fact_frequency_flattener_full/raw_generations.jsonl` |
| Timings | `results/fact_frequency_flattener_full/timings.jsonl` |
| Artifact hashes | `results/artifact_sha256.txt` |
| Environment telemetry | `logs/environment_20260430T112848.log` |
| Smoke test output | `logs/fff_smoke.log` |
| Smoke server log | `logs/server_for_smoke.log` |
| Full run command log | `logs/fff_full_command_20260430T113258.log` |
| Full run model output | `logs/fff_full.log` |
| Full run server log | `logs/server_for_full.log` |
| Notion fetch head | `logs/notion_fetch_head.html` |
| Project decision JSON | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260430T162818354630+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T162818354630+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T162818354630+0000/paper_manifest.json` |
