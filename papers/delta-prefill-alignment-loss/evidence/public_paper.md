# Delta-Prefill Alignment Loss: Measuring Safety Degradation from Assistant-Prefill Manipulation in Instruction-Tuned Language Models

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed these claims.

---

## Abstract

We introduce Delta-Prefill Alignment Loss (DPAL), a metric quantifying the degradation in refusal and safe-response behavior of instruction-tuned language models when the assistant prefill prefix is modified while the user prompt remains fixed. In a local llama.cpp hook-prototype evaluation on Qwen2.5-7B-Instruct (Q4_K_M quantization), we measured alignment rates across three prefill conditions—blank, unsafe procedural scaffold, and fictional procedural scaffold—on a curated set of 12 harmful and 6 benign prompts. The blank-prefill baseline achieved perfect alignment (1.000) on both harmful and benign sets. The unsafe numbered-step prefill reduced the harmful alignment rate to 0.750 (DPAL = 25.0 percentage points), and the fictional numbered-step prefill reduced it to 0.583 (DPAL = 41.7 pp). Benign prompts remained fully aligned across all conditions. These results suggest that assistant-prefill deltas can measurably erode safety alignment when the prefill provides a procedural or fictional answer scaffold, though the effect is bounded and condition-dependent. All results derive from a single quantized model on a small prompt set with one trial per condition; confidence intervals are wide, and replication is required before generalization.

## Introduction

Instruction-tuned language models typically employ a chat template in which the model's response begins after an assistant-role token or prefix. In many inference APIs, the assistant prefill—the initial tokens placed into the model's context as the beginning of its response—is configurable or can be left blank. This design choice creates an attack surface: if a user or system can inject tokens into the assistant prefill, the model's subsequent generation may be steered away from its trained safety behavior.

We term the measurable degradation in safety alignment caused by modifying only the assistant prefill as **Delta-Prefill Alignment Loss (DPAL)**. Formally:

$$\text{DPAL} = R_{\text{blank}} - R_{\text{prefill}}$$

where $R_{\text{blank}}$ is the alignment rate (fraction of responses that are safe refusals or benign completions) under a blank assistant prefill, and $R_{\text{prefill}}$ is the alignment rate under a modified prefill condition. DPAL is reported in percentage points (pp). A DPAL of zero indicates no measurable alignment degradation from the prefill manipulation; positive values indicate degradation.

This work operationalizes and tests whether small assistant-prefill deltas measurably change an instruction-tuned model's safety behavior on harmful versus benign prompts. We do not claim comprehensive validation; rather, we report a bounded positive finding from a local prototype and identify the conditions under which the effect was and was not observed.

## Method

### Model and Serving

We used Qwen2.5-7B-Instruct in the Q4_K_M GGUF quantization, served locally via llama.cpp server with the following configuration:

- **Host:** GB10 environment (20 ARM cores, 121 GiB RAM, swap disabled)
- **GPU:** NVIDIA GB10 (visible via nvidia-smi)
- **Server command:** `llama-server -m Qwen2.5-7B-Instruct-Q4_K_M.gguf --host 127.0.0.1 --port 18082 -ngl 999 -c 4096 --flash-attn on`
- **Context length:** 4096 tokens
- **Flash attention:** Enabled
- **All layers offloaded to GPU** (`-ngl 999`)

This constitutes a llama.cpp hook-prototype evaluation on a single machine, not a production-validated or CUDA-calibrated result.

### Prompt Set

A curated set of prompts was used, consisting of 12 harmful prompts and 6 benign prompts. The prompt set was small and manually curated; it was not drawn from a standardized benchmark. The exact prompt set is not included in the released artifacts.

### Prefill Conditions

Three assistant-prefill conditions were tested:

1. **Blank prefill:** The assistant response begins with no injected tokens (standard behavior).
2. **Unsafe numbered-step prefill:** The assistant prefill contains the beginning of a procedural, step-by-step answer scaffold consistent with complying with the harmful request.
3. **Fictional numbered-step prefill:** The assistant prefill contains the beginning of a fictional or narrative step-by-step answer scaffold.

The exact prefill strings are not included in the released artifacts.

### Evaluation Procedure

For each (prompt, prefill condition) pair, the model generated a single completion. Completions were scored for alignment using a lightweight heuristic classifier supplemented by manual audit. A response was counted as "aligned" if it constituted a refusal or safe response to the prompt. No repeated trials were conducted; each (prompt, prefill) pair was evaluated once.

The primary endpoint was the alignment rate under each condition, and the derived DPAL metric (difference from blank baseline in percentage points).

### Infrastructure Monitoring

System memory was monitored throughout. MemAvailable remained at approximately 116.7 GB before and after the main run, with swap at 0 B and no memory pressure observed. Generation throughput was approximately 44–45 tokens per second.

## Results

### Alignment Rates

| Condition | Harmful Aligned Rate | Harmful n | Benign Aligned Rate | Benign n |
|---|---|---|---|---|
| Blank prefill | 1.000 | 12 | 1.000 | 6 |
| Unsafe numbered-step prefill | 0.750 | 12 | 1.000 | 6 |
| Fictional numbered-step prefill | 0.583 | 12 | 1.000 | 6 |

### Delta-Prefill Alignment Loss

| Prefill Condition | DPAL (pp) |
|---|---|
| Unsafe numbered-step | 25.0 |
| Fictional numbered-step | 41.7 |

### Statistical Uncertainty

Given the small sample sizes and single-trial design, point estimates carry substantial uncertainty. Approximate 95% Clopper-Pearson confidence intervals for the harmful-prompt alignment rates are:

- Blank: 1.000 [0.735, 1.000]
- Unsafe numbered-step: 0.750 [0.428, 0.945]
- Fictional numbered-step: 0.583 [0.277, 0.839]

The interval for the fictional condition overlaps with the point estimate for the blank condition, meaning the observed difference cannot be distinguished from sampling variability at conventional significance levels with this sample size. These intervals are computed post hoc and should be interpreted cautiously given the absence of repeated trials.

### Interpretation

Under the blank-prefill baseline, the model refused all 12 harmful prompts and complied appropriately with all 6 benign prompts, yielding perfect alignment. When the assistant prefill was set to an unsafe procedural scaffold, 3 of 12 harmful prompts received non-aligned (compliant) completions, producing a DPAL of 25.0 percentage points. Under the fictional procedural scaffold, 5 of 12 harmful prompts received non-aligned completions, producing a DPAL of 41.7 percentage points.

Benign prompts showed no alignment degradation under any prefill condition, suggesting the effect is specific to prompts where the prefill scaffold is semantically congruent with a harmful completion trajectory.

The fictional scaffold produced a numerically larger DPAL than the directly unsafe scaffold. One plausible interpretation is that the fictional framing may weaken the model's internal harm-detection pathways more effectively than a straightforward compliance scaffold, though this observation rests on a difference of only 2 additional non-aligned responses (5 vs. 3 out of 12) and is not statistically distinguishable from noise at this sample size. This finding requires further investigation with larger sample sizes and controlled semantic variation.

### System Performance

Generation throughput remained stable at approximately 44–45 tokens/s. No memory pressure, out-of-memory events, or swap activity occurred during the run.

## Limitations

This study has several significant limitations that constrain the generality of its conclusions:

1. **Single model:** Results are from one quantized model (Qwen2.5-7B-Instruct Q4_K_M). Alignment behavior may differ substantially across model families, sizes, and quantization levels.

2. **Small prompt set:** Only 12 harmful and 6 benign prompts were tested. Confidence intervals on the alignment rates are wide; the 95% Clopper-Pearson interval for the 7/12 aligned rate under the fictional condition spans approximately [0.277, 0.839], overlapping with the blank baseline's point estimate of 1.0 only marginally but underscoring the uncertainty inherent in small samples.

3. **Single trial per condition:** Each (prompt, prefill) pair was evaluated once. No repeated trials were conducted, so within-condition variability cannot be estimated.

4. **Heuristic scoring:** Alignment was assessed via a lightweight heuristic classifier supplemented by manual audit, not by blinded human raters or a validated safety classifier. Scoring errors may affect the reported rates.

5. **Quantization effects:** The Q4_K_M quantization may alter safety behavior relative to the full-precision model. We cannot disentangle quantization effects from prefill effects in this design.

6. **No dose-response characterization:** Only two non-blank prefill conditions were tested. The relationship between prefill length, semantic strength, and DPAL magnitude remains uncharacterized.

7. **No logprob analysis:** Continuation log-probabilities for refusal versus compliance tokens were not collected, limiting mechanistic interpretation.

8. **Local prototype only:** This was a llama.cpp hook-prototype evaluation on a single machine, not a production-validated result. Replication across diverse environments is needed.

9. **Incomplete artifact release:** The exact prompt set, prefill strings, and scoring rubric are not included in the released artifacts, which limits independent replication.

10. **Notion connector failure:** An attempted fetch of additional project context from a Notion page failed due to a transport HTTP error, so no private page details were incorporated into the experimental design or analysis.

## Reproducibility Checklist

| Item | Status |
|---|---|
| Model specified (name, quantization) | Yes: Qwen2.5-7B-Instruct Q4_K_M GGUF |
| Model source/commit | Partial: bartowski GGUF on local storage; exact commit hash not recorded |
| Server software and version | llama.cpp server; exact version not recorded in logs |
| Server launch command | Yes: recorded in run notes |
| Hardware specified | Yes: GB10, 20 ARM cores, 121 GiB RAM, NVIDIA GB10, swap disabled |
| Prompt set published | No: curated set not included in artifacts |
| Prefill strings published | No: exact prefill strings not included in artifacts |
| Scoring rubric published | Partial: described as heuristic + manual audit; rubric not in artifacts |
| Raw outputs published | Partial: `artifacts/data/main_raw.jsonl` exists in project directory |
| Metrics published | Yes: `artifacts/data/main_metrics.csv`, `artifacts/data/final_analysis.json` |
| Analysis code published | Partial: `scripts/dpal_harness.py`, `scripts/analyze_results.py` exist in project directory |
| Random seeds recorded | No |
| Number of runs per condition | 1 (no repeated trials) |
| Confidence intervals reported | No (computed post hoc in this draft only) |

## Conclusion

We introduced Delta-Prefill Alignment Loss (DPAL) as a metric for quantifying safety degradation from assistant-prefill manipulation. In a local llama.cpp hook-prototype evaluation on Qwen2.5-7B-Instruct (Q4_K_M), we found that procedural and fictional answer-scaffold prefills reduced the harmful-prompt alignment rate from 1.000 to 0.750 and 0.583 respectively, yielding DPAL values of 25.0 and 41.7 percentage points. Benign prompts were unaffected. These results constitute a bounded positive finding: the phenomenon is measurable for strong procedural/fictional assistant prefills under the tested conditions, but the study's limitations—single model, small prompt set, heuristic scoring, no repeated trials, wide confidence intervals—preclude generalization.

The primary implication is that assistant-prefill configurability represents a non-trivial safety attack surface. Systems that expose or auto-populate the assistant prefill should treat it as a security-relevant input. Replication across model families, blinded scoring, logprob analysis, and dose-response characterization of prefill strength are necessary before drawing stronger conclusions.

## Referenced Artifacts

The following local artifacts from project `source-record-redacted` were used as evidence:

- `run_notes.md` — Execution log and key metric summaries
- `.omx/project_decision.json` — Decision record with primary metrics and limitations
- `scripts/dpal_harness.py` — Evaluation harness script
- `scripts/analyze_results.py` — Analysis and adjudication script
- `artifacts/data/main_raw.jsonl` — Raw generation outputs
- `artifacts/data/main_metrics.csv` — Per-condition metric table
- `artifacts/data/final_analysis.json` — Final analysis summary
- `artifacts/data/final_analysis_rows.csv` — Row-level analysis results
- `artifacts/logs/dpal_harness_run_v2.log` — Harness execution log
- `artifacts/logs/final_analysis.log` — Analysis execution log
- `artifacts/logs/llama_server_live.log` — llama.cpp server log
