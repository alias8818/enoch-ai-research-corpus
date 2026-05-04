# Strong-Draft Weak-Reviewer Transfer: A Pilot Study of Draft-Augmented Code-Review Diagnosis with Asymmetric Local Language Models

> **AI Provenance Notice.** This draft was AI-generated from automated research artifacts (run notes, decision JSON, result files, claim ledger, evidence bundle). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

We investigate whether a weak local language model (0.5B parameters, 4-bit quantized) improves its accuracy on code-review bug diagnosis tasks when provided with a draft analysis from a stronger local model (7B parameters, 4-bit quantized). In a controlled pilot on 8 synthetic multiple-choice code-review items with balanced gold labels, the weak reviewer achieved 5/8 (62.5%) accuracy unassisted and 8/8 (100%) accuracy when augmented with the strong model's draft. Three discordant cases were corrected and zero were harmed, yielding an absolute lift of 37.5 percentage points. However, the sample is too small for statistical closure (exact sign / McNemar-style *p* = 0.25), the strong drafter was itself perfect on this task bank, and transfer behavior under incorrect or noisy drafts remains untested. We present this as a viability pilot, not a publication-grade result, and outline the controls needed for a decisive follow-up experiment.

## Introduction

Deploying large language models for code review often faces a compute budget constraint: a single strong model invocation may be too slow or memory-intensive for interactive use, while a weak model is fast but unreliable. A natural architectural compromise is to have a strong model produce a draft analysis that a weak model then reviews or refines. This "strong-draft weak-reviewer" pattern is intuitively plausible, but its empirical properties—particularly whether the weak model actually benefits, and whether it can be harmed by incorrect drafts—are not well characterized in local inference settings.

This pilot asks a narrow operational question: does a weak local reviewer improve on code-review bug diagnosis tasks when given a stronger local model's draft analysis? We test this with two quantized Qwen2.5 models running locally via `llama.cpp` on a single ARM workstation, using synthetic multiple-choice items with known gold labels. The goal is not to establish a general claim but to determine whether the transfer mechanism is viable enough to justify a larger, better-controlled experiment.

## Method

### Models and Infrastructure

| Role | Model | Format | Size |
|---|---|---|---|
| Strong drafter | `Qwen2.5-7B-Instruct-Q4_K_M` | GGUF, 4-bit quantized | ~4.4 GiB |
| Weak reviewer | `Qwen2.5-0.5B-Instruct-Q4_K_M` | GGUF, 4-bit quantized | ~469 MiB |

Both models were served by a local `llama.cpp` server (`llama-server`) on an NVIDIA GB10 / aarch64 Ubuntu system with approximately 116 GiB available memory and no swap. An earlier attempt using `llama-cli` interactive mode was abandoned due to a 152 MiB log artifact; server mode resolved this.

### Task Design

Eight synthetic multiple-choice code-review diagnosis items were constructed with known gold labels. The label sequence was balanced as A, B, C, A, B, C, A, B to reduce answer-label bias. Task identifiers for the three discordant cases were:

- `py_off_by_one` (gold: B)
- `js_async_foreach` (gold: C)
- `py_late_binding` (gold: C)

### Conditions

Each task was evaluated under two conditions:

1. **Weak baseline:** The 0.5B model answered directly with no draft.
2. **Weak + strong draft (transfer):** The 7B model first produced a draft analysis; this draft was then included in the prompt to the 0.5B model, which produced the final answer.

The strong drafter's standalone accuracy was also recorded.

### Prompt and Parser Controls

An initial exploratory run revealed that the 0.5B model tended to copy the first answer option when the prompt used an `A|B|C` format. The final prompt was revised to require one literal answer letter, and the parser was corrected accordingly. Earlier runs with the flawed prompt/parser were superseded and are not reported.

### Statistical Test

With only 8 items and 3 discordant pairs (all helped, none harmed), we report an exact sign / McNemar-style *p*-value computed as the probability of observing 3 out of 3 discordant cases in the helped direction under a null of 0.5: *p* = (0.5)³ = 0.125, or equivalently the two-sided binomial *p* = 0.25.

## Results

### Accuracy

| Condition | Correct / Total | Accuracy |
|---|---|---:|
| Strong drafter (standalone) | 8 / 8 | 100.0% |
| Weak baseline | 5 / 8 | 62.5% |
| Weak + strong draft | 8 / 8 | 100.0% |
| **Absolute lift** | | **+37.5 pp** |

### Discordant Cases

All three discordant cases were corrected by the transfer condition; no regressions were observed.

| Task ID | Weak baseline | Weak + draft | Gold |
|---|---|---|---|
| `py_off_by_one` | A | B | B |
| `js_async_foreach` | A | C | C |
| `py_late_binding` | A | C | C |

The weak model exhibited a default tendency toward answer A on several items. The strong draft appeared to override this tendency in the three cases where A was incorrect.

### Throughput

| Condition | Mean generation throughput |
|---|---:|
| Strong drafter | ~45.1 tok/s |
| Weak baseline | ~344.5 tok/s |
| Weak + draft | ~364.5 tok/s |

The weak reviewer's throughput was roughly 8× that of the strong drafter, consistent with the parameter count ratio.

### Wall Time

The complete 8-task experiment (both conditions, including server communication overhead) completed in 28.75 seconds.

### Statistical Significance

The exact sign / McNemar-style *p*-value is 0.25. This does not meet conventional significance thresholds, which is expected given *n* = 8 and only 3 discordant pairs. The result is consistent with both a real positive effect and with chance variation.

## Limitations

1. **Small, synthetic task bank.** Eight items constitute a viability pilot, not publication-grade evidence. The tasks are synthetic and may not reflect the distribution of real code-review scenarios.

2. **Perfect strong drafter.** The 7B model achieved 8/8 on this task bank. This is the most favorable possible condition for transfer. The critical question—how the weak reviewer behaves when the strong draft is *wrong*—remains entirely untested. Transfer could harm accuracy if the weak model is led astray by an incorrect draft.

3. **Label bias and default tendencies.** The weak model showed a pronounced A-label default on some balanced-label tasks. Although the balanced label sequence mitigates systematic inflation, the underlying bias means that accuracy numbers may not generalize to unbalanced or differently formatted item banks.

4. **No token-budget control.** The transfer condition gives the weak model additional tokens (the draft) that the baseline condition does not receive. It is possible that some of the lift comes from the weak model having more context or reasoning steps available, rather than from the semantic content of the strong draft specifically. A token-budget-matched weak-only reasoning control was not run.

5. **Single model pair.** Only one strong–weak model pair was tested. The result may not generalize to other model families, quantization levels, or size ratios.

6. **Multiple-choice format.** The diagnosis task was framed as multiple-choice with three options. Real code review is typically open-ended; the constrained format may inflate the apparent benefit of draft transfer.

7. **No held-out test set.** All 8 items were used in the pilot with no held-out set, so there is no estimate of generalization to unseen items from the same distribution.

8. **No preregistered protocol.** This was an exploratory pilot; the analysis was not preregistered, which increases the risk of post-hoc rationalization.

## Reproducibility Checklist

- [x] **Code available.** Harness source: `scripts/strong_draft_weak_reviewer_experiment.py`, `scripts/server_transfer_experiment.py`.
- [x] **Result data available.** `artifacts/results/server_experiment_20260501T204330Z.json`; convenience pointer: `artifacts/results/latest_server_experiment.json`.
- [x] **Command log available.** `artifacts/logs/server_experiment_final_20260501T204301Z.log`.
- [x] **System environment documented.** `artifacts/logs/system_probe_20260501T203329Z.log`. NVIDIA GB10 / aarch64 Ubuntu, ~116 GiB RAM, no swap.
- [x] **Model identifiers specified.** Strong: `Qwen2.5-7B-Instruct-Q4_K_M.gguf` (bartowski GGUF). Weak: `Qwen2.5-0.5B-Instruct-Q4_K_M.gguf` (Hugging Face GGUF).
- [x] **Inference engine specified.** `llama.cpp` server, binary at `/mnt/usb<local-path-redacted>`.
- [x] **Gold labels and task structure documented.** Balanced sequence A, B, C, A, B, C, A, B; per-task logs in `artifacts/logs/server_*_{task_id}_*.prompt.txt` and `.response.json`.
- [x] **Prompt and parser corrections documented.** Initial `A|B|C` format replaced; earlier runs superseded.
- [ ] **Held-out test set.** Not applicable; all 8 items were used in the pilot with no held-out set.
- [ ] **Preregistered protocol.** Not applicable; this was an exploratory pilot.

## Conclusion

On 8 synthetic code-review diagnosis items, providing a weak 0.5B model with a draft from a stronger 7B model improved accuracy from 62.5% to 100%, correcting 3 errors and introducing 0 regressions. This demonstrates the *viability* of the strong-draft weak-reviewer transfer pattern in a narrow, favorable setting.

However, the result is not statistically significant (*p* = 0.25), the task bank is small and synthetic, and the strong drafter was perfect—meaning the hardest and most practically important transfer regime (incorrect or noisy drafts) was never exercised. The weak model's A-label default tendency further complicates interpretation.

We classify this as a **viable positive pilot**. A decisive experiment would require at least 50–100 held-out tasks with balanced labels, explicit controls for draft correctness (including deliberately wrong drafts), a strong-draft ablation, and a token-budget-matched weak-only reasoning condition. Until such an experiment is conducted, the transfer effect should be treated as plausible but unconfirmed.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260501T203253423904+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260501T203253423904+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260501T203253423904+0000/paper_manifest.json` |
| Final result JSON | `artifacts/results/server_experiment_20260501T204330Z.json` |
| Latest result pointer | `artifacts/results/latest_server_experiment.json` |
| Final command log | `artifacts/logs/server_experiment_final_20260501T204301Z.log` |
| System probe log | `artifacts/logs/system_probe_20260501T203329Z.log` |
| Harness script (initial) | `scripts/strong_draft_weak_reviewer_experiment.py` |
| Harness script (final) | `scripts/server_transfer_experiment.py` |
| Per-task prompt logs | `artifacts/logs/server_*_{task_id}_*.prompt.txt` |
| Per-task response logs | `artifacts/logs/server_*_{task_id}_*.response.json` |
