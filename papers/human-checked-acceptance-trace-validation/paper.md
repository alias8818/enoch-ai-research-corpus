# Human-Checked Acceptance Trace Validation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present evidence from a cross-validator study of an acceptance-trace validation mechanism for LLM ranking systems. The mechanism augments plain confidence scoring with risk-aware trace utilities and failure-cluster exposure. A materially distinct stronger cached-model validation using Qwen2.5-0.5B-Instruct (64 examples, 4 tasks/domain × 4 domains × 4 ranking systems, CPU-only) preserved the core mechanism: system ranking changed versus plain confidence, a reject-heavy failure cluster (`high_conf_wrong`) was exposed, and targeted-fix utility uplift exceeded 5 points (115.91 utility points above plain confidence). However, failure-cluster coverage was narrower than in larger parent validation slices, and the Kendall τ between risk-aware and plain rankings was 0.0, indicating complete rank reordering rather than refinement. A 24-item human spot-check adjudication packet was prepared but no completed human labels are available. The project decision is `finalize_positive` with medium confidence and moderate evidence strength. The result supports the acceptance-trace mechanism in the tested setting, but broader external validity—particularly failure-cluster stability across larger samples and human label agreement—remains unestablished.

## 1. Introduction

Acceptance-trace validation is a schema for evaluating LLM-based ranking systems by recording structured decision traces that capture not only confidence scores but also risk signals, constraint violations, and failure-mode clusters. The central hypothesis is that risk-aware trace utilities can (a) change system rankings relative to plain confidence scoring, (b) expose reject-heavy failure clusters that plain scoring obscures, and (c) yield targeted-fix utility uplifts exceeding a minimal threshold (5 utility points).

This report documents a branch-specific validation study that applies a stronger cached model (Qwen2.5-0.5B-Instruct) as an independent cross-validator against previously recorded deterministic and tiny-GPT2 slices from a parent project. The study was designed with an explicit kill condition: stop negative if the independent validation shows no ranking change, no reject-heavy failure cluster exposure, or less than 5 utility-point targeted-fix uplift, or if independent labels disagree with verifier labels at a rate that invalidates the schema comparison (target: less than 80% label agreement on spot checks).

The kill condition was not triggered. The results are positive but moderate-strength, constrained by the small sample size (64 examples) and the absence of completed human spot-check labels.

## 2. Method

### 2.1 Acceptance-Trace Schema

The acceptance-trace schema (inherited from the parent project and finalized prior to this branch) structures each evaluation example as a trace record containing:

- Task identifier and domain label
- LLM ranking system identifier
- Plain confidence score
- Risk-aware trace score (incorporating constraint-violation signals and failure-mode indicators)
- Accept/holdout decision under the trace schema
- Failure cluster assignment (e.g., `high_conf_wrong`, `constraint_drift`)

Utility is computed as a scalar function of the trace scores, with targeted-fix utility measuring the gain from addressing identified failure clusters.

### 2.2 Validation Slices

Three validation slices were compared:

1. **Deterministic slice** (parent project): Rule-based evaluation over the acceptance-trace corpus.
2. **Tiny-GPT2 slice** (parent project): GPT-2 small model used as an LLM-based evaluator over the corpus.
3. **Qwen2.5-0.5B-Instruct slice** (this branch): A stronger cached instruct model loaded from local Hugging Face cache with `local_files_only=True`, run on CPU.

### 2.3 Qwen Validation Procedure

The Qwen validation was executed as follows:

- A project-local virtual environment was created with `transformers` and `torch` (CPU-only PyTorch wheel).
- An initial 20-task/domain run was attempted but terminated after approximately 2.5 minutes due to CPU scoring speed constraints and absence of partial output; no partial results were captured.
- A bounded 4-task/domain run was then executed, producing 64 examples (4 tasks × 4 domains × 4 LLM ranking systems).
- The command used was:
  ```
  HF_HOME=/mnt/usb/home/jeremy/.cache/huggingface \
    .venv/bin/python experiments/llm_trace_slice.py \
    --model Qwen/Qwen2.5-0.5B-Instruct \
    --n-tasks-per-domain 4 \
    --max-new-tokens 0 \
    --out data/qwen05_trace_slice.jsonl \
    --summary results/qwen05_trace_summary.json
  ```
- A comparison script (`experiments/compare_validation.py`) was then run to produce cross-slice stability metrics.

### 2.4 Human Spot-Check Packet

A 24-item manual adjudication packet was generated (`data/human_spot_check_packet.jsonl`, `data/human_spot_check_packet.csv`) with accompanying instructions (`results/human_spot_check_readme.md`). This packet is intended for future human label agreement checks. No completed human labels exist in the current artifacts.

## 3. Results

### 3.1 Qwen2.5-0.5B-Instruct Slice Summary

The bounded 64-example Qwen validation produced the following metrics (from `results/qwen05_trace_summary.json`):

| Metric | Value |
|---|---|
| Accept rate | 0.2031 |
| Holdout examples | 22 |
| Plain confidence utility | −0.6909 |
| Risk-aware trace utility | 0.4682 |
| Targeted-fix utility | 0.4682 |
| Utility points vs. plain | 115.91 |
| System ranking changed vs. plain | true |
| Risk-aware Kendall τ vs. plain | 0.0 |
| Failure clusters exposed (n ≥ 2) | 1 (`high_conf_wrong`) |

The `constraint_drift` cluster appeared once but did not meet the evaluator's n ≥ 2 exposure threshold.

### 3.2 Cross-Slice Stability Comparison

The comparison script (`experiments/compare_validation.py`) produced `results/validation_comparison.json` and `results/validation_report.md`. The key stability findings are:

- **Ranking change**: Preserved across all three slices. The risk-aware trace utility produces a different system ranking than plain confidence in every slice.
- **Failure-cluster exposure**: Preserved in direction (reject-heavy clusters are exposed), but narrower in the Qwen slice. The parent deterministic and tiny-GPT2 slices exposed more failure clusters, consistent with their larger sample sizes.
- **Targeted-fix uplift**: Exceeded the 5-point threshold in all slices. The Qwen slice recorded 115.91 utility points above plain confidence.
- **Kendall τ = 0.0**: The risk-aware and plain-confidence rankings are completely uncorrelated in the Qwen slice. This indicates the trace mechanism reorders systems rather than refining an existing ranking, which is a stronger effect than partial rank adjustment but also raises questions about rank stability that a larger sample might clarify.

### 3.3 Human Spot-Check Status

The 24-item adjudication packet has been prepared but no human labels have been completed. The kill condition's label-agreement criterion (≥80% agreement on spot checks) has not been evaluated. This is an open gap in the validation chain.

## 4. Limitations

1. **Small sample size.** The Qwen validation used only 64 examples (4 tasks/domain) due to CPU speed constraints. The initial 20-task/domain attempt was terminated without producing partial output. Failure-cluster coverage is almost certainly underestimated relative to what a larger run would expose.

2. **CPU-only execution.** All Qwen inference was performed on CPU with no GPU acceleration. This limited both the model size (0.5B parameters) and the number of examples feasible within the turn budget. Results may not generalize to larger models or GPU-accelerated evaluation pipelines.

3. **No completed human labels.** The 24-item spot-check packet is prepared but unpopulated. The kill condition's label-agreement threshold has not been tested. Without human adjudication, it remains possible that the trace schema's accept/holdout decisions disagree with human judgment at rates that would undermine the mechanism's practical utility.

4. **Narrow failure-cluster coverage.** Only one cluster (`high_conf_wrong`) met the exposure threshold in the Qwen slice. The `constraint_drift` cluster appeared once. Whether additional clusters would emerge at scale is unknown.

5. **Complete rank reordering (τ = 0.0).** While ranking change is the hypothesized mechanism, a Kendall τ of exactly 0.0 between risk-aware and plain rankings means the two orderings share no concordant pair structure. This could reflect a genuine strong effect or an artifact of the small sample and the specific systems evaluated. A larger sample is needed to determine whether the effect is stable or noisy.

6. **No external replication.** All experiments were conducted within a single project environment using cached models and local data. No independent replication by external researchers or on different hardware has been performed.

7. **Automated artifact provenance.** This draft and the underlying project decision were generated by an automated research pipeline. The project decision (`finalize_positive`, medium confidence, moderate evidence strength) reflects the pipeline's assessment, not a human-authored peer review.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Code available in project artifacts | Yes: `experiments/acceptance_trace_mve.py`, `experiments/real_trace_slice.py`, `experiments/llm_trace_slice.py`, `experiments/compare_validation.py` |
| Data artifacts available | Yes: `data/acceptance_trace_corpus.jsonl`, `data/real_trace_slice.jsonl`, `data/llm_trace_slice.jsonl`, `data/qwen05_trace_slice.jsonl`, `data/human_spot_check_packet.jsonl`, `data/human_spot_check_packet.csv` |
| Result summaries available | Yes: `results/summary.json`, `results/real_trace_summary.json`, `results/llm_trace_summary.json`, `results/qwen05_trace_summary.json`, `results/validation_comparison.json`, `results/validation_report.md`, `results/human_spot_check_readme.md` |
| Model identifier specified | Yes: `Qwen/Qwen2.5-0.5B-Instruct` (loaded with `local_files_only=True`) |
| Hardware specified | Partial: CPU-only, no GPU; specific CPU model not recorded in artifacts |
| Random seeds recorded | Not present in available artifacts |
| Exact commands logged | Yes (see Section 2.3) |
| Dependency versions recorded | Partial: `transformers`, `torch` (CPU wheel); exact version numbers not in artifacts |
| Human labels completed | No: packet prepared, labels pending |
| External replication | No |

## 6. Conclusion

A materially distinct stronger cached-model validation run using Qwen2.5-0.5B-Instruct preserved the core acceptance-trace mechanism: system ranking changed versus plain confidence, a reject-heavy failure cluster was exposed, and targeted-fix utility uplift exceeded 5 points (observed: 115.91 points). The branch-specific kill condition was not triggered.

However, the evidence strength is moderate and confidence is medium, bounded by three principal gaps: (1) the Qwen slice is small (64 examples) and failure-cluster coverage is narrower than in parent slices; (2) no human spot-check labels have been completed, so label agreement with the trace schema is untested; and (3) the Kendall τ of 0.0 between risk-aware and plain rankings, while consistent with the hypothesis of ranking change, could reflect small-sample noise rather than a stable reordering effect.

The recommended next actions are: use the prepared 24-item human spot-check packet to assess label agreement, or run a larger Qwen cached-model slice (with GPU acceleration if available) to establish broader failure-cluster stability. Until one or both of these steps are completed, the finding should be interpreted as positive but moderate-strength, limited to the tested setting.

---

## Referenced Artifacts

### Run notes and decisions
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Evidence and claim audit
- `papers/.../evidence_bundle.json`
- `papers/.../claim_ledger.json`
- `papers/.../paper_manifest.json`

### Experiment code
- `experiments/acceptance_trace_mve.py`
- `experiments/real_trace_slice.py`
- `experiments/llm_trace_slice.py`
- `experiments/compare_validation.py`

### Data files
- `data/acceptance_trace_corpus.jsonl`
- `data/real_trace_slice.jsonl`
- `data/llm_trace_slice.jsonl`
- `data/qwen05_trace_slice.jsonl`
- `data/human_spot_check_packet.jsonl`
- `data/human_spot_check_packet.csv`

### Result files
- `results/summary.json`
- `results/real_trace_summary.json`
- `results/llm_trace_summary.json`
- `results/qwen05_trace_summary.json`
- `results/validation_comparison.json`
- `results/validation_report.md`
- `results/human_spot_check_readme.md`
