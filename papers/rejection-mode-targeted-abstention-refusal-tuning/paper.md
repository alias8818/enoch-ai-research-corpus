# Rejection-Mode Targeted Abstention Refusal Tuning

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has approved this content.

---

## Abstract

We investigate whether a low-cost, prompt-level intervention can improve a small language model's ability to correctly abstain, refuse, or navigate code on targeted rejection-mode probes without regressing accuracy on random-control inputs. Using Qwen2.5-0.5B-Instruct served through a local OpenAI-compatible shim, we compare a baseline (no system prompt) against a targeted rejection-mode system prompt across 1,000 targeted probes and 1,000 random-control probes. The intervention improved targeted accuracy from 0.338 to 0.568 (+23.0 percentage points) with zero regression on the random-control set (0.389 → 0.389). However, the benign_refusal_trigger subcategory regressed from 1.000 to 0.815 (−18.5 points), indicating the prompt induces over-refusal on inputs that should not trigger rejection. Results are limited to a single 0.5B-parameter model, synthetic probe datasets, and a prompt-only intervention; generalization to larger models, real-world distributions, or fine-tuning-based methods remains untested.

---

## 1. Introduction

Language models deployed in production must sometimes correctly abstain from answering—when context is insufficient, when a requested symbol is absent from code, when a required field is missing from a structured extraction task, or when a request is genuinely unsafe. At the same time, models must not refuse benign requests. Balancing targeted rejection against appropriate responsiveness is a practical alignment challenge.

We test a simple hypothesis: a carefully constructed system prompt can improve a small model's rejection-mode accuracy on targeted probe categories without degrading its behavior on random-control inputs. We define a pre-registered kill condition: abandon the intervention if targeted accuracy improves by fewer than 5 percentage points or if random-control accuracy regresses by more than 1 percentage point.

This report documents the intervention, evaluation protocol, and observed results on Qwen2.5-0.5B-Instruct. The findings are bounded to the tested setting and should not be generalized beyond the artifacts described.

---

## 2. Method

### 2.1 Intervention

The intervention is a prompt-level system message (`prompts/targeted_rejection_mode_system.txt`) designed to instruct the model on when and how to abstain, refuse, or indicate absent information. No model weights are modified; the intervention is purely a system-prompt addition applied at inference time.

### 2.2 Evaluation Infrastructure

The model (Qwen/Qwen2.5-0.5B-Instruct) was served through a local OpenAI-compatible Transformers shim (`scripts/openai_transformers_shim.py`) running from `/tmp/enoch_services` on a CUDA 13 PyTorch environment. The evaluation script (`scripts/evaluate_openai_compatible.py`) was extended with `--system-prompt` and `--system-prompt-file` arguments so that baseline and intervention conditions share the same scoring logic, differing only in the presence or absence of the targeted system prompt.

### 2.3 Datasets

Two synthetic probe datasets were used:

- **Targeted probes** (`data/rejection_mode_synthetic_negatives.jsonl`): 1,000 rows spanning five categories—`abstain_insufficient_context`, `code_navigation_absent_symbol`, `structured_extraction_missing_field`, `unsafe_should_refuse`, and `benign_refusal_trigger`. The first four categories require the model to correctly reject or abstain; the last category contains benign inputs that should *not* trigger refusal.
- **Random-control probes** (`data/random_mix_control.jsonl`): 1,000 rows of mixed general-purpose inputs used to detect regression on non-targeted behavior.

### 2.4 Protocol

1. **Smoke/calibration run**: 50 targeted rows with the intervention prompt, verifying scoring and latency (observed: 0.540 accuracy, ~0.226s mean latency).
2. **Full baseline evaluation**: 1,000 targeted rows and 1,000 control rows without the system prompt, using previously recorded baseline results.
3. **Full intervention evaluation**: 1,000 targeted rows and 1,000 control rows with the targeted rejection-mode system prompt.
4. **Kill-condition check**: The intervention passes if targeted accuracy improves by ≥5 points and random-control accuracy regresses by ≤1 point.

---

## 3. Results

### 3.1 Aggregate Accuracy

| Condition | Targeted Accuracy | Random-Control Accuracy |
|---|---|---|
| Baseline (no system prompt) | 0.338 | 0.389 |
| Intervention (targeted system prompt) | 0.568 | 0.389 |
| **Delta** | **+0.230** | **0.000** |

The intervention improved targeted accuracy by 23.0 percentage points with zero regression on the random-control set. The kill condition (≥5-point targeted uplift without >1-point control regression) was met.

### 3.2 Per-Category Breakdown on Targeted Probes

| Category | Baseline | Intervention | Delta |
|---|---|---|---|
| `abstain_insufficient_context` | 0.000 | 0.375 | +37.5 |
| `code_navigation_absent_symbol` | 0.290 | 0.745 | +45.5 |
| `structured_extraction_missing_field` | 0.215 | 0.485 | +27.0 |
| `unsafe_should_refuse` | 0.185 | 0.420 | +23.5 |
| `benign_refusal_trigger` | 1.000 | 0.815 | **−18.5** |

Four of five targeted subcategories improved substantially. The `benign_refusal_trigger` category regressed by 18.5 points, from perfect accuracy to 0.815. This is the primary negative result: the system prompt induces over-refusal on benign inputs that should be answered normally.

### 3.3 Performance and Resource Utilization

| Metric | Targeted Run | Control Run |
|---|---|---|
| Wall time | 237.66 s | 278.30 s |
| Throughput | 4.21 samples/s | 3.59 samples/s |
| Mean latency | 0.238 s | 0.278 s |
| GPU utilization (avg) | ~80% | ~80% |

The targeted run was slightly faster in wall time and per-sample latency, likely due to shorter average output sequences when the model abstains or refuses. GPU utilization was comparable across conditions. Memory snapshots before and after the intervention runs are recorded in `results/mem_before_promptfix.txt` and `results/mem_after_promptfix.txt`.

---

## 4. Limitations

1. **Single small model.** All results are from Qwen2.5-0.5B-Instruct, a 0.5B-parameter instruction-tuned model. Whether these findings transfer to larger models (7B, 70B, etc.) or other model families is unknown.

2. **Synthetic probe datasets.** Both the targeted and control datasets are synthetic. Real-world distributions may exhibit different failure modes, category frequencies, or interaction effects not captured here.

3. **Prompt-only intervention.** The intervention modifies only the system prompt at inference time. It does not alter model weights. The effect is therefore brittle with respect to prompt phrasing and may not compose well with other system instructions in production deployments.

4. **Benign refusal-trigger regression.** The −18.5-point regression on `benign_refusal_trigger` is a meaningful tradeoff. The prompt causes the model to refuse some benign inputs that it previously handled correctly. Whether this tradeoff is acceptable depends on deployment context and cannot be resolved from these data alone.

5. **No cross-model or cross-dataset replication.** The experiment was conducted once, on one model, on one dataset pair. No statistical significance testing across multiple runs or random seeds was performed.

6. **Baseline provenance.** Baseline results were copied from a parent project branch rather than re-run in the same session. While the scorer and model are identical, subtle environmental differences cannot be fully excluded.

7. **No fine-tuning comparison.** The experiment does not compare against SFT, DPO, or other weight-modifying approaches. Whether prompt-level interventions are competitive with or complementary to fine-tuning remains an open question.

---

## 5. Reproducibility Checklist

- **Model identifier:** `Qwen/Qwen2.5-0.5B-Instruct` (cached locally)
- **Intervention artifact:** `prompts/targeted_rejection_mode_system.txt`
- **Evaluation script:** `scripts/evaluate_openai_compatible.py` (with `--system-prompt` / `--system-prompt-file` flags)
- **Serving shim:** `scripts/openai_transformers_shim.py`
- **Targeted dataset:** `data/rejection_mode_synthetic_negatives.jsonl` (1,000 rows)
- **Control dataset:** `data/random_mix_control.jsonl` (1,000 rows)
- **Baseline result files:** Copied from parent project under `results/baseline/`
- **Intervention result files:** `results/qwen_targeted_promptfix_full.jsonl`, `results/qwen_control_promptfix_full.jsonl`
- **Smoke test file:** `results/qwen_targeted_promptfix_smoke50.jsonl`
- **Summary artifacts:** `results/promptfix_summary.json`, `results/promptfix_report.md`
- **GPU utilization logs:** `results/gpu_util_promptfix_targeted.csv`, `results/gpu_util_promptfix_control.csv`
- **Memory snapshots:** `results/mem_before_promptfix.txt`, `results/mem_after_promptfix.txt`
- **Server process snapshots:** `results/server_ps_before_promptfix.txt`, `results/server_ps_after_targeted_promptfix.txt`, `results/server_ps_after_control_promptfix.txt`
- **Environment:** CUDA 13, PyTorch, Transformers, FastAPI, Uvicorn; project-local `.venv`
- **Kill condition (pre-registered):** Targeted accuracy improvement ≥5 points; random-control regression ≤1 point

---

## 6. Conclusion

A targeted rejection-mode system prompt applied to Qwen2.5-0.5B-Instruct improved targeted abstention/refusal/code-navigation accuracy by 23.0 percentage points (0.338 → 0.568) with no regression on random-control inputs (0.389 → 0.389). The improvement was distributed across four probe categories, with the largest gains on `code_navigation_absent_symbol` (+45.5 points) and `abstain_insufficient_context` (+37.5 points). However, the intervention caused a regression of 18.5 points on `benign_refusal_trigger`, indicating over-refusal on benign inputs.

These results support the hypothesis that prompt-level interventions can meaningfully improve rejection-mode behavior on a small model without degrading general responsiveness, but they also highlight a concrete tradeoff: the same prompt that enables correct abstention also induces some incorrect refusal. Recovering the benign_refusal_trigger loss while preserving the targeted gains—potentially through prompt refinement or lightweight SFT/DPO—is the recommended next step, though success of that follow-up is not guaranteed.

All claims in this report are bounded to the artifacts, model, and datasets described. External replication on additional models, datasets, and hardware is necessary before drawing broader conclusions.

---

## Referenced Artifacts

### Project metadata
- `.omx/project_decision.json` — finalization decision and rationale
- `.omx/metrics.json` — session metrics
- `.omx/project.json` — project configuration
- `run_notes.md` — execution log and interpretation

### Intervention and evaluation code
- `prompts/targeted_rejection_mode_system.txt` — targeted system prompt
- `scripts/evaluate_openai_compatible.py` — evaluation driver (extended with system-prompt support)
- `scripts/openai_transformers_shim.py` — local OpenAI-compatible serving shim
- `scripts/summarize_promptfix.py` — result summarization
- `scripts/spot_check_labels.py` — label verification
- `scripts/summarize_real_model_evals.py` — evaluation summarization

### Datasets
- `data/rejection_mode_synthetic_negatives.jsonl` — targeted probes (1,000 rows)
- `data/random_mix_control.jsonl` — random-control probes (1,000 rows)

### Result files
- `results/qwen_targeted_promptfix_full.jsonl` — full targeted intervention results
- `results/qwen_control_promptfix_full.jsonl` — full control intervention results
- `results/qwen_targeted_promptfix_smoke50.jsonl` — smoke/calibration results
- `results/promptfix_summary.json` — summary statistics
- `results/promptfix_report.md` — human-readable report
- `results/gpu_util_promptfix_targeted.csv` — GPU utilization (targeted run)
- `results/gpu_util_promptfix_control.csv` — GPU utilization (control run)
- `results/mem_before_promptfix.txt` — memory snapshot before intervention
- `results/mem_after_promptfix.txt` — memory snapshot after intervention
- `results/server_ps_before_promptfix.txt` — server process state before
- `results/server_ps_after_targeted_promptfix.txt` — server process state after targeted run
- `results/server_ps_after_control_promptfix.txt` — server process state after control run
- `results/qwen_targeted_promptfix_full.stdout` / `.stderr` — run logs (targeted)
- `results/qwen_control_promptfix_full.stdout` / `.stderr` — run logs (control)
- `results/qwen_targeted_promptfix_smoke50.stdout` / `.stderr` — run logs (smoke test)
- `results/gpu_util_promptfix_targeted.err` — GPU logging stderr (targeted)
- `results/gpu_util_promptfix_control.err` — GPU logging stderr (control)

### Paper and audit artifacts
- `papers/.../evidence_bundle.json` — structured evidence bundle
- `papers/.../claim_ledger.json` — claim audit with confidence levels and wording constraints
- `papers/.../paper_manifest.json` — artifact manifest
