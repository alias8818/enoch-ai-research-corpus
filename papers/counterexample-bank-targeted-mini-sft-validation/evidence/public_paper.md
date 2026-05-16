# Counterexample Bank Targeted Mini-SFT Validation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact.

---

## Abstract

We investigate whether a curated counterexample bank—constructed from audited failure clusters of a small language model on synthetic arithmetic tasks—can serve as an effective intervention dataset for targeted prompt-policy correction. A dependency-free intervention harness splits the bank into 400 training pairs (800 examples) and 800 held-out pairs (1,600 examples), induces a restricted prompt-policy overlay from training clusters, and evaluates against both held-out bank examples and a naive synthetic baseline. On held-out bank data, the targeted prompt-policy overlay achieves pair-both-correct accuracy of 1.000, compared to 0.490 for the lexical shortcut baseline (uplift +0.510). Naive synthetic accuracy remains unchanged at 1.000 under both conditions. These results support the viability of the counterexample bank as an intervention dataset source and confirm that an explicit prompt-policy overlay can correct the targeted failure modes without regressing baseline performance on simple inputs. However, the intervention is a symbolic prompt-policy overlay rather than gradient-based fine-tuning, and the evaluation is confined to synthetic, templated distributions. Whether gradient-based mini-SFT on the produced training artifact transfers to less templated or external distributions remains an open question.

## 1. Introduction

Small language models exhibit systematic failure modes on structured reasoning tasks such as multi-step arithmetic. These failures often cluster into recurring patterns—for example, a model may reliably apply a lexical shortcut (copying a surface-level quantity) rather than performing the required computation. A counterexample bank that catalogs these failure clusters offers a potential resource for targeted correction: if the bank captures the failure distribution, a small intervention derived from it might repair the identified weaknesses without degrading performance elsewhere.

This report presents evidence from a controlled experiment within the OMX research automation pipeline. The project, Counterexample Bank Targeted Mini-SFT Validation, tests whether a prompt-policy intervention derived from audited counterexample clusters can improve held-out accuracy on the bank's failure distribution without regressing accuracy on a naive synthetic baseline. A predefined kill condition required a minimum held-out uplift of 0.05 and a maximum naive regression of 0.01.

The experiment produced a positive result under these conditions. However, the intervention tested is an explicit symbolic prompt-policy overlay—not gradient-based supervised fine-tuning—and the evaluation domain is synthetic and templated. The project also produced a mini-SFT-format training artifact (`intervention_train_sft.jsonl`) suitable for future gradient-based experiments, but no such experiment was conducted in this run.

## 2. Method

### 2.1 Data Sources

Two data sources were used:

- **Counterexample bank** (`data/counterexample_bank.jsonl`): An audited collection of model failure cases organized by task type. Each entry records an input, the model's incorrect output, the correct output, and a cluster label identifying the failure mode.
- **Naive synthetic set** (`data/naive_synthetic.jsonl`): A set of straightforward synthetic arithmetic examples where the baseline model already performs at ceiling, used as a regression guard.

### 2.2 Train/Held-out Split

The counterexample bank was split deterministically:

- **Training partition**: 100 pairs per task type, yielding 400 pairs total (800 examples). This partition was used to induce the prompt-policy overlay.
- **Held-out partition**: 800 bank pairs (1,600 examples) withheld from overlay construction and used solely for evaluation.

### 2.3 Intervention: Targeted Prompt-Policy Overlay

The intervention harness (`scripts/targeted_prompt_policy_intervention.py`) is a dependency-free Python script that:

1. Reads the audited counterexample bank and splits it into training and held-out partitions.
2. Induces a restricted prompt-policy overlay from the training clusters. This overlay encodes corrective rules derived from the identified failure patterns (e.g., "do not copy the first number; compute the sum").
3. Writes a mini-SFT-compatible training artifact (`data/intervention_train_sft.jsonl`) in JSONL format, suitable for future gradient-based fine-tuning experiments.
4. Evaluates four conditions on both held-out bank data and naive synthetic data:
   - **Lexical shortcut baseline**: The model's default behavior of copying a surface-level quantity.
   - **Left-to-right arithmetic**: A simple sequential computation strategy.
   - **Targeted prompt-policy overlay**: The induced overlay applied to the model's prompt.
   - **Oracle parser**: An upper bound that parses the correct answer directly.

### 2.4 Kill Condition

The experiment was designed with a predefined kill condition: the branch would be terminated if either:

- The held-out bank pair-both-correct uplift over the lexical shortcut baseline was less than 0.05, or
- The naive synthetic accuracy regressed by more than 0.01.

Both conditions are conservative: the uplift threshold ensures the intervention is meaningfully better than baseline, while the regression threshold guards against catastrophic forgetting on simple inputs.

### 2.5 Evaluation Metric

The primary metric is **pair-both-correct**: the fraction of evaluation pairs for which both elements of the pair are answered correctly. This is stricter than per-example accuracy and penalizes partial corrections within a paired evaluation structure.

## 3. Results

### 3.1 Held-out Bank Performance

| Condition | Pair-both-correct |
|---|---|
| Lexical shortcut baseline | 0.490 |
| Targeted prompt-policy overlay | 1.000 |
| Uplift | +0.510 |

The targeted prompt-policy overlay achieves perfect pair-both-correct accuracy on the held-out bank partition, an uplift of +0.510 over the lexical shortcut baseline. This exceeds the predefined kill condition threshold of +0.05.

### 3.2 Naive Synthetic Regression Check

| Condition | Accuracy |
|---|---|
| Lexical shortcut baseline | 1.000 |
| Targeted prompt-policy overlay | 1.000 |
| Delta | 0.000 |

The prompt-policy overlay produces no regression on the naive synthetic set. The kill condition threshold of 0.01 maximum regression is satisfied.

### 3.3 Kill Condition Verdict

Both kill condition criteria are passed: uplift (+0.510) exceeds the minimum threshold (+0.05), and naive regression (0.000) is below the maximum threshold (0.01). The project decision is `finalize_positive` with hypothesis status `supported`.

### 3.4 Additional Conditions

The harness also evaluated left-to-right arithmetic and oracle parser conditions on both evaluation sets. The full predictions are recorded in `results/targeted_prompt_policy_predictions.csv` and the metrics in `results/targeted_prompt_policy_metrics.json`. The oracle parser serves as an upper-bound reference confirming that the held-out bank examples are solvable when the correct computation is applied.

## 4. Limitations

1. **Symbolic overlay, not gradient fine-tuning.** The intervention tested is an explicit prompt-policy overlay—a set of corrective rules applied symbolically to the model's prompt—rather than gradient-based supervised fine-tuning. The SFT-format training artifact was produced but not used for actual weight updates. Whether gradient-based mini-SFT on this artifact achieves comparable transfer remains untested.

2. **Synthetic, templated distribution.** Both the counterexample bank and the naive synthetic set are generated from templated arithmetic tasks. The prompt-policy overlay's perfect performance on held-out bank data reflects correction of known, structured failure patterns within a narrow distribution. Generalization to less templated, more diverse, or external benchmarks is not established.

3. **No live model evaluation.** The evaluation is conducted within the intervention harness using deterministic parsing and rule application. No live language model inference (e.g., via llama.cpp hooks or API calls) was performed in this run. The results characterize the intervention's logical correctness on the bank's failure patterns, not its effect on model generation under sampling.

4. **Medium confidence, moderate evidence.** The project decision assigns confidence `medium` and evidence strength `moderate`. The positive result is bounded to the tested setting and does not constitute evidence that the method works universally or that gradient-based transfer will succeed.

5. **Single run, no variance estimates.** The experiment was executed once with a deterministic split. No confidence intervals or variance estimates across random seeds are available.

6. **Narrow task scope.** The counterexample bank covers a small number of task types (4, given 100 pairs per type). Broader task coverage may reveal failure modes not represented in the current bank.

## 5. Reproducibility Checklist

- **Code availability**: The intervention harness `scripts/targeted_prompt_policy_intervention.py` is dependency-free Python. Verification confirmed that `python3 scripts/targeted_prompt_policy_intervention.py` completed successfully and `python3 -m py_compile scripts/*.py` passed.
- **Data artifacts**: All input data (`counterexample_bank.jsonl`, `naive_synthetic.jsonl`), split artifacts (`intervention_train_sft.jsonl`, `intervention_holdout_bank.jsonl`, `intervention_naive_eval.jsonl`), and result files (`targeted_prompt_policy_metrics.json`, `targeted_prompt_policy_predictions.csv`, `targeted_prompt_policy_report.md`) are recorded in the project directory.
- **Deterministic split**: The train/held-out split is deterministic within the harness script.
- **Kill condition pre-registered**: The kill condition (uplift ≥ 0.05, regression ≤ 0.01) was defined before evaluation and is recorded in the run notes.
- **Metrics verification**: The metrics JSON was loaded and confirmed to show the kill condition passed.
- **No external dependencies**: The harness requires only the Python standard library.
- **Hardware**: No GPU or specialized hardware was required; the experiment is a symbolic evaluation, not a model training run.

## 6. Conclusion

A targeted prompt-policy overlay derived from audited counterexample clusters improves held-out pair-both-correct accuracy from 0.490 to 1.000 on a synthetic arithmetic counterexample bank, with zero regression on a naive synthetic baseline. This supports the counterexample bank's utility as an intervention dataset source and validates the prompt-policy overlay mechanism within the tested distribution. The produced SFT-format training artifact provides a concrete starting point for future gradient-based mini-SFT experiments.

However, the current evidence is confined to symbolic overlay evaluation on synthetic, templated data. The critical open question is whether gradient-based fine-tuning (e.g., LoRA or QLoRA) on the produced training artifact transfers corrective behavior to less templated or external distributions. The project decision recommends that any follow-on work address this question directly, rather than extending the current synthetic evaluation further.

## Referenced Artifacts

### Run notes and decision
- `run_notes.md`
- `.omx/project_decision.json`
- `.omx/metrics.json`

### Claim audit
- `papers/source-record-redacted/claim_ledger.json`

### Evidence bundle
- `papers/source-record-redacted/evidence_bundle.json`

### Publication manifest
- `papers/source-record-redacted/paper_manifest.json`

### Data files
- `data/counterexample_bank.jsonl`
- `data/naive_synthetic.jsonl`
- `data/intervention_train_sft.jsonl`
- `data/intervention_holdout_bank.jsonl`
- `data/intervention_naive_eval.jsonl`

### Scripts
- `scripts/targeted_prompt_policy_intervention.py`
- `scripts/evaluate_cached_small_llm.py`
- `scripts/counterexample_bank_experiment.py`
- `scripts/audit_classifier_evaluation.py`

### Result files
- `results/targeted_prompt_policy_metrics.json`
- `results/targeted_prompt_policy_predictions.csv`
- `results/targeted_prompt_policy_report.md`
