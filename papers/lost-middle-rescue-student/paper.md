# Lost-Middle Rescue Student: Chunk-Local Extraction for Over-Context Retrieval

> **AI provenance / no-human-credit note:** This draft was AI-generated from automated research artifacts produced by an autonomous research pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether a two-stage "student rescue" protocol—chunk-local extraction by a small model followed by deterministic controller selection—can improve retrieval of facts positioned in the middle of a long context relative to direct single-prompt querying. Using Qwen2.5-7B-Instruct (Q4_K_M GGUF) served locally via llama.cpp with a 32,768-token context window, we construct a synthetic exact key-value needle-in-a-haystack benchmark with 240–1,600 dense audit-style decoy records. On in-window cases (900 records, approximately 19k tokens), direct prompting achieves 3/3 exact hits (mean latency 98.34 s) while rescue achieves 3/3 exact hits (mean latency 105.10 s, 1.07× direct), yielding no demonstrated accuracy advantage. However, at 1,600 records (approximately 51k tokens), the direct prompt exceeds the 32,768-token context window and fails with an HTTP 400 error, whereas the rescue protocol successfully recovers the middle-located value in 171.36 s. The result is narrowly positive: student chunk-gating does not improve in-window lost-middle accuracy on this benchmark, but it does rescue retrieval in over-context scenarios where direct prompting is infeasible.

---

## Introduction

Large language models with extended context windows sometimes exhibit degraded retrieval performance for information positioned in the interior of a long prompt—a phenomenon sometimes described as the "lost in the middle" effect. A natural remediation strategy is to decompose a long context into shorter chunks, extract candidate answers from each chunk independently, and then select among candidates. This "student rescue" approach trades additional inference calls for reduced per-call context length, potentially mitigating both attention dilution and hard context-length limits.

This paper evaluates a concrete instance of that strategy. We define a two-stage protocol: (1) a *student* pass that processes each chunk independently and emits either the target value or NONE, and (2) a *deterministic controller* that collects non-NONE student outputs and returns the rescued value. We compare this protocol against direct single-prompt querying on a synthetic exact key-value retrieval benchmark, varying context length from within-window to over-context.

The central question is whether chunk-local extraction improves retrieval accuracy for middle-positioned facts. Our experiments yield a mixed answer: within the model's context window, direct prompting was already accurate on the tested cases, and the rescue protocol added latency without accuracy gain. Beyond the context window, however, the rescue protocol provided a viable fallback that direct prompting could not.

---

## Method

### Model and Serving

All experiments use Qwen2.5-7B-Instruct quantized to Q4_K_M (GGUF format), served via llama.cpp server with a 32,768-token context window (`-c 32768`), full GPU offload (`-ngl 999`), and no warm-up (`--no-warmup`). The server runs on a host with a CUDA GPU; GB10 telemetry logs confirm approximately 5.5 GiB model/context/compute self-use and greater than 112 GiB free device memory during stress tests. Host `MemAvailable` remained high throughout, and swap was disabled by design (confirmed at 0 B in all telemetry snapshots). No earlyoom-risk posture was observed.

### Benchmark Design

We construct a synthetic needle-in-a-haystack benchmark. Each test case embeds a single target key-value pair (the "needle") among *N* dense decoy audit records of similar format. The needle is placed at one of three positions: **front**, **middle**, or **end**. The task is exact string extraction of the value associated with a specified key.

Decoy records are designed to be superficially similar to the target record (same schema, different values), increasing the difficulty of distractor filtering. The benchmark is synthetic and constrained to exact key-value retrieval; it does not test natural-language question answering, multi-hop reasoning, or open-ended retrieval.

### Protocols

**Direct.** A single prompt contains all *N* records and asks the model to return the value for the target key. The model generates the answer in one call.

**Rescue (student chunk-gating + deterministic controller).** The *N* records are partitioned into chunks of size *C*. For each chunk, a student prompt asks the model to return the target value if present in that chunk, or NONE otherwise. A deterministic controller then scans the student outputs: the first non-NONE value is returned as the answer. This controller is deterministic rather than generative; it does not invoke the model a second time.

### Protocol Evolution

The initial rescue protocol used a fully generative two-stage design (student extraction followed by a teacher model call for final selection). Smoke-test results revealed this generative protocol was brittle—student outputs were inconsistent in format, causing teacher-stage parsing failures. We therefore replaced the generative teacher with a deterministic controller that scans student outputs for the first non-NONE value. All reported rescue results use this final deterministic controller design. This evolution should be noted when interpreting the results: the successful protocol is not a fully generative student–teacher pipeline but rather a student-gating plus rule-based extraction system.

### Experimental Conditions

| Condition | Records (*N*) | Chunk size (*C*) | Positions tested | Seed | Estimated tokens |
|---|---|---|---|---|---|
| Smoke | 240 | 60 | front, middle, end | 100 | ~5k |
| Calibration (900, both) | 900 | 150 | middle | 200 | ~19k |
| Calibration (900, rescue only) | 900 | 150 | middle | 200 | ~19k |
| Replication (900, both) | 900 | 150 | middle | 201 | ~19k |
| Stress direct (1600) | 1600 | 200 | middle | 300 | ~51k |
| Stress rescue (1600) | 1600 | 200 | middle | 300 | ~51k |

The smoke test validated the pipeline and revealed the generative protocol's brittleness. The 900-record conditions test in-window performance (estimated ~19k tokens, well within the 32k context). The 1,600-record conditions test over-context performance (~51k tokens, exceeding the 32k context).

### Metrics

- **Exact hit rate**: fraction of cases where the returned string exactly matches the target value.
- **Latency**: wall-clock time from request submission to final answer (seconds).
- **Speed ratio**: mean rescue latency divided by mean direct latency.

---

## Results

### In-Window Performance (900 Records, Middle Position)

| Protocol | Exact hits | Cases | Mean latency (s) | Speed ratio |
|---|---|---|---|---|
| Direct | 3 | 3 | 98.34 | 1.00× |
| Rescue | 3 | 3 | 105.10 | 1.07× |

Both protocols achieve perfect exact-hit accuracy on the 900-record middle-position cases. The rescue protocol incurs a modest 7% latency overhead. There is no demonstrated accuracy advantage for rescue within the context window on this benchmark.

The calibration run (seed 200) and replication run (seed 201) are consistent: direct and rescue both achieve 3/3 on middle-position needles. The rescue-only controller run (seed 200) also achieves 3/3, confirming the deterministic controller functions as intended.

### Over-Context Performance (1,600 Records, Middle Position)

| Protocol | Result | Latency (s) |
|---|---|---|
| Direct | HTTP 400: 51,586 tokens exceeded 32,768-token context | N/A |
| Rescue | 1/1 exact hit | 171.36 |

The direct prompt cannot be issued: llama.cpp rejects the request because the token count (51,586) exceeds the configured context window (32,768). The rescue protocol, which issues multiple shorter prompts each well within the context limit, successfully retrieves the middle-positioned value.

This result demonstrates that the rescue protocol can handle inputs that exceed the model's context window, but it is a single case (1/1) and should be interpreted accordingly.

### Smoke Test (240 Records)

The 240-record smoke test confirmed that both direct and rescue protocols achieve 3/3 exact hits across front, middle, and end positions. It also revealed the brittleness of the initial generative rescue design, motivating the shift to the deterministic controller. The smoke test serves as a pipeline validation rather than a statistical sample.

---

## Limitations

1. **Synthetic benchmark only.** The task is exact key-value string extraction from structured decoy records. No natural-language QA, document comprehension, or open-ended retrieval task was tested. Performance on more ambiguous or multi-hop retrieval may differ substantially. The structured format of the decoy records may make exact extraction easier than in natural settings.

2. **Single small quantized model.** All results are from Qwen2.5-7B-Instruct Q4_K_M. Larger models, models with longer native context windows, or API-hosted models with different attention implementations may exhibit different lost-middle profiles. The rescue protocol's value depends on the base model's failure mode; if a larger model does not lose the middle within its context window, rescue offers no accuracy benefit in that regime.

3. **Small sample size.** Due to local inference latency (~98–171 s per case), sample sizes are 3 cases per condition for in-window tests and 1 case for the over-context stress test. These are sufficient to establish feasibility and bounded research-action conclusions but do not support publication-grade statistical claims about accuracy differences. The 3/3 result for both protocols at 900 records is consistent with either (a) both protocols being highly accurate or (b) the benchmark being insufficiently challenging to reveal differences.

4. **Deterministic controller, not generative teacher.** The final successful rescue protocol uses a deterministic scan of student outputs rather than a second model call. This design works for exact extraction benchmarks where the answer is a single string, but it may not generalize to tasks requiring synthesis, ranking, or judgment across multiple candidate chunks. The initial generative teacher design was brittle and abandoned; whether a more robust generative teacher could be engineered remains untested.

5. **No comparison to non-LLM baselines.** Simple lexical matching (e.g., grep or BM25) may recover exact key-value needles from structured records without any model inference. The rescue protocol's marginal value over such baselines was not evaluated. For the specific benchmark used here, lexical methods may be sufficient and more efficient.

6. **Latency confound.** Rescue latency scales with the number of chunks and is currently sequential. Parallelization or batched inference could reduce wall time but was not implemented. The 1.07× overhead at 900 records and the 171.36 s latency at 1,600 records reflect sequential execution only.

7. **Evidence classification.** These results are llama.cpp hook-prototype results from a local inference setup, not final production validation. The llama.cpp server configuration, quantization level, and hardware environment all affect results. Generalization to other serving frameworks or deployment configurations is not established.

---

## Reproducibility Checklist

- **Model**: Qwen2.5-7B-Instruct Q4_K_M (GGUF format). Specific GGUF file used in testing.
- **Serving**: llama.cpp server, context window 32,768 tokens, full GPU offload (`-ngl 999`), no warm-up (`--no-warmup`), host 127.0.0.1, port 18080, metrics enabled.
- **Script**: `scripts/lost_middle_rescue_eval.py` (validated via `python3 -m py_compile`).
- **Seeds**: 100 (smoke), 200 (calibration), 201 (replication), 300 (stress).
- **Hardware**: Host with CUDA GPU; GB10 telemetry confirmed ~5.5 GiB model/context/compute self-use and >112 GiB free device memory; swap disabled (0 B confirmed in telemetry).
- **Result files**: `results/smoke_summary.json`, `results/eval_middle_summary.json`, `results/calibration_fixed_summary.json`, `results/rescue_controller_summary.json`, `results/stress_rescue_summary.json`, `results/aggregate_summary.json`, and corresponding JSONL detail files.
- **Log files**: `logs/llama-server-smoke.log`, `logs/llama-server-eval.log`, `logs/smoke_run.log`, `logs/calibration_fixed_run.log`, `logs/rescue_controller_run.log`, `logs/eval_middle_run.log`, `logs/stress_direct_run.log`, `logs/stress_rescue_run.log`, plus telemetry snapshots (`logs/smoke_telemetry_before.txt`, `logs/smoke_telemetry_after.txt`).
- **Decision record**: `.omx/project_decision.json`.
- **Claim ledger**: `papers/source-record-redacted-20260502T100318556077+0000/claim_ledger.json` (contains no claims at time of draft generation; notes model-authored draft requiring human claim audit).

---

## Conclusion

A two-stage student rescue protocol with deterministic controller extraction does not improve in-window retrieval accuracy for middle-positioned facts on a synthetic exact key-value benchmark served by Qwen2.5-7B-Instruct Q4_K_M. Direct prompting already achieves perfect accuracy at 900 records (~19k tokens), and rescue adds 7% latency overhead without accuracy gain. The null result for in-window accuracy improvement is the central negative finding of this study.

The protocol is, however, narrowly viable as an over-context rescue technique. When the input exceeds the model's context window (1,600 records, ~51k tokens vs. 32k limit), direct prompting fails entirely while the rescue protocol successfully recovers the target value. This suggests a practical but circumscribed role for chunk-local student extraction: as a fallback strategy when inputs exceed context capacity, rather than as an accuracy improvement for in-window inputs.

Whether this finding generalizes to natural retrieval tasks, larger models, or scenarios where the base model genuinely exhibits lost-middle degradation remains an open question. The absence of a demonstrated in-window accuracy gap in our experiments may reflect the benchmark's structure, the model's capabilities at this scale, or insufficient sample size to detect small differences. Future work should test on natural multi-document QA with answer-bearing middle passages, compare against lexical retrieval baselines (which may suffice for exact key-value tasks), and evaluate parallelized chunk processing to reduce latency overhead.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Evaluation script | `scripts/lost_middle_rescue_eval.py` |
| Aggregate summary | `results/aggregate_summary.json` |
| Smoke summary | `results/smoke_summary.json` |
| Eval middle summary | `results/eval_middle_summary.json` |
| Calibration fixed summary | `results/calibration_fixed_summary.json` |
| Rescue controller summary | `results/rescue_controller_summary.json` |
| Stress rescue summary | `results/stress_rescue_summary.json` |
| Stress direct run log | `logs/stress_direct_run.log` |
| Stress rescue run log | `logs/stress_rescue_run.log` |
| Llama server smoke log | `logs/llama-server-smoke.log` |
| Llama server eval log | `logs/llama-server-eval.log` |
| Smoke run log | `logs/smoke_run.log` |
| Calibration fixed run log | `logs/calibration_fixed_run.log` |
| Rescue controller run log | `logs/rescue_controller_run.log` |
| Eval middle run log | `logs/eval_middle_run.log` |
| Smoke telemetry (before) | `logs/smoke_telemetry_before.txt` |
| Smoke telemetry (after) | `logs/smoke_telemetry_after.txt` |
| Project decision | `.omx/project_decision.json` |
| Project metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260502T100318556077+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T100318556077+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T100318556077+0000/paper_manifest.json` |
