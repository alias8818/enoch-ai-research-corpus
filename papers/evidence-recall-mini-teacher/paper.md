# Evidence Recall Mini-Teacher: Adaptive Scheduling of Source-Grounded Recall Prompts in a Deterministic Simulation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We investigate whether a minimal evidence-grounded recall teacher — converting source-backed learning claims into adaptively scheduled recall prompts — can outperform equal-budget baselines in a deterministic simulated delayed-recall task. Using a Monte Carlo harness over 1,000 independent seeds with a 14-day training window, a daily 3-prompt budget, and a 30-day delayed test, the adaptive recall teacher achieved a mean delayed recall probability of 0.584 versus 0.546 for the best baseline (random quiz), an absolute lift of +0.038 (relative +6.9%). The paired 95% confidence interval for this difference was [0.034, 0.042], and the adaptive teacher won in 73.9% of seeds — meaning it lost to random quiz in roughly one-quarter of runs. Against massed quiz and reread-only baselines, the adaptive teacher won in 100% of seeds with substantially larger margins. Grounding coverage (fraction of cards with verifiable source references) was 1.0 across all policies. These results support the viability of a small, auditable adaptive scheduling prototype under a synthetic forgetting model, but they do not constitute evidence of human learning gains. The card corpus is limited to five items, the learner model is entirely synthetic, and the modest win rate against random quiz highlights the sensitivity of adaptive scheduling to corpus size and budget constraints.

## Introduction

Retrieval practice and spaced repetition are among the most robustly supported strategies in learning science. Roediger and Karpicke (2006) demonstrated that testing improves later retention more than repeated study, with delayed tests particularly favoring prior retrieval over re-exposure. Agarwal, Nunes, and Blunt (2021) surveyed 50 classroom experiments (n = 5,374) and found that 57% of effects were medium or large, though only 6% of experiments were conducted in non-WEIRD countries, limiting generalizability. Latimier, Peyre, and Ramus (2021) reported that spaced retrieval outperformed massed retrieval (g = 0.74) in their meta-analysis, but found no general advantage for expanding over uniform schedules. Carpenter, Pan, and Butler (2022) emphasized that spacing and retrieval practice remain underused in practice, with metacognitive biases and learner beliefs as key adoption constraints.

Despite this evidence base, the operational question remains: can a minimal, fully auditable system convert evidence-backed claims into adaptively scheduled recall prompts and measurably outperform simple baselines under controlled, reproducible conditions? This paper addresses that question with a deliberately small prototype — five evidence cards, a deterministic forgetting-model simulation, and four competing scheduling policies — to establish computational viability before any attempt to scale to human or LLM-as-learner evaluations.

The question is not whether retrieval practice works — the literature strongly supports that — but whether a minimal adaptive scheduling mechanism can extract measurable gains over naive equal-budget alternatives in a transparent, reproducible simulation. A negative or ambiguous result would suggest that adaptive scheduling requires richer information (larger corpora, learner modeling, or natural-language generation) to differentiate itself from simple random exposure.

## Method

### Evidence Cards

Five source-grounded recall cards were constructed from the external literature. Each card contains four fields: `source` (bibliographic reference and URL), `claim` (a paraphrased finding), `teacher_question` (a recall prompt), and `answer` (the expected response). Grounding coverage is defined as the fraction of cards whose `source` field resolves to a verifiable external reference. The card corpus is stored in `data/evidence_cards.json`.

### Scheduling Policies

Four policies were implemented in `scripts/evidence_recall_eval.py`:

1. **adaptive_recall_teacher** (experimental condition): Retrieves due cards using an interval-growth rule based on the learner's correct-response streak. Correct answers increase the inter-repetition interval; incorrect answers reset it.

2. **random_quiz**: Selects cards at random within the same daily budget, without adaptive due-date scheduling. This controls for exposure quantity while removing spacing adaptation.

3. **massed_quiz**: Clusters all quiz exposures early in the training window, followed by restudy-only for the remaining days. This controls for total quiz count while removing spacing entirely.

4. **reread**: Restudy-only baseline with no quiz component. This represents the repeated-study condition from the retrieval-practice literature.

### Simulation Model

The evaluation uses a deterministic Monte Carlo harness with a synthetic forgetting model. Each simulation run specifies a random seed, a training window (default 14 days), a daily prompt budget (default 3), and a delayed-test day (default 30). The model tracks per-card recall probability as a function of exposure history and spacing. No stochastic noise is added beyond the seed-dependent card selection order. This is a toy simulation: the forgetting model is a parametric convenience, not a validated model of human memory.

### Evaluation Protocol

A smoke test (5 runs) was executed first to verify harness correctness and approximate effect direction. The main evaluation comprised 1,000 independent runs with distinct seeds. The primary outcome is mean delayed recall probability at day 30. Paired differences between the adaptive teacher and each baseline were computed across all 1,000 seeds, with normal-approximation 95% confidence intervals and win rates (fraction of seeds where the adaptive teacher outperformed the comparator).

### Computational Environment

The evaluation was executed on a GB10-class host. Key resource metrics: throughput of 22,279 policy-runs/sec, maximum RSS of 17,180 KiB, and memory availability of approximately 122,442,476 KiB before and 122,440,412 KiB after the main evaluation. Swap was intentionally disabled (SwapTotal: 0 kB). No GPU was used; the workload is CPU-light and did not require GPU acceleration. This was a pure Python simulation — not a llama.cpp hook-prototype, not a CUDA calibration, and not a production deployment.

## Results

### Smoke Test

Over 5 runs, the adaptive recall teacher produced a mean delayed recall probability of 0.620, with 100% grounding coverage and an absolute lift of +0.027 versus the best baseline. This confirmed harness viability and a positive effect direction, but the small sample precludes any inference.

### Main Evaluation

Table 1 summarizes the primary outcomes over 1,000 seeds.

**Table 1.** Mean delayed recall probability at day 30, by policy (n = 1,000 seeds).

| Policy | Mean Delayed Recall Probability |
|---|---|
| adaptive_recall_teacher | 0.5839 |
| random_quiz | 0.5460 |
| massed_quiz | 0.1040 |
| reread | 0.0176 |

Grounding coverage was 1.0 for all cards and all policies.

The massed_quiz and reread baselines performed poorly, consistent with the spacing and retrieval-practice literature: massed exposure without spacing decays rapidly, and restudy without testing produces minimal delayed retention.

### Paired Comparisons

Table 2 reports paired differences (adaptive minus comparator) across 1,000 seeds.

**Table 2.** Paired differences between adaptive recall teacher and baselines (n = 1,000).

| Comparison | Mean Diff | 95% CI | Win Rate |
|---|---|---|---|
| adaptive − random_quiz | +0.0379 | [0.0338, 0.0419] | 73.9% |
| adaptive − massed_quiz | +0.4799 | [0.4769, 0.4828] | 100.0% |
| adaptive − reread | +0.5664 | [0.5633, 0.5695] | 100.0% |

The adaptive teacher's advantage over random quiz is statistically reliable (the 95% CI excludes zero) but modest in absolute terms. Critically, the 73.9% win rate means that random quiz outperformed adaptive scheduling in approximately 26.1% of seeds. This mixed result reflects the stochastic variability in card selection under a small corpus (5 cards) and tight budget (3 prompts/day). With so few cards, random selection occasionally produces favorable spacing by chance, and the adaptive mechanism's advantage is correspondingly compressed.

The advantages over massed quiz and reread are large and consistent, with 100% win rates. These comparisons are essentially tests of spacing and retrieval effects within the simulation, and the results align with the external literature.

### Resource Usage

The evaluation was computationally lightweight: 22,279 policy-runs/sec throughput, 17,180 KiB peak RSS, and negligible memory pressure on the host (approximately 2,064 KiB delta over the full evaluation). No GPU was required or used.

## Limitations

1. **Synthetic learner model.** The forgetting model is a transparent parametric simulation, not a human subject. The positive result validates scheduling and grounding mechanics under the model's assumptions but does not constitute evidence of human learning gains. A learner study or classroom A/B test with delayed post-tests would be required to establish efficacy for real learners.

2. **Tiny card corpus.** The five-card set was chosen deliberately as a viability check. The 73.9% win rate against random quiz — meaning the adaptive teacher loses in roughly one-quarter of seeds — suggests that adaptive scheduling has limited headroom to differentiate itself when the corpus is small. Performance characteristics may change substantially with larger corpora, where the scheduling problem becomes more consequential.

3. **No natural-language generation quality evaluation.** The harness validates scheduling and grounding mechanics but does not assess the pedagogical quality of the `teacher_question` and `answer` fields. No LLM was used for question generation; cards were hand-authored from source material. Question clarity, difficulty calibration, and distractor quality are unmeasured.

4. **Single forgetting model.** All results are conditioned on one parametric forgetting model. Different decay rates, interference assumptions, or model families could yield different policy rankings. The absolute recall probabilities (e.g., 0.584 for adaptive) are artifacts of the model's parametrization and should not be interpreted as predictions of human performance.

5. **No expanding-schedule comparison.** Given Latimier et al.'s (2021) finding that expanding schedules do not generally outperform uniform ones, the adaptive teacher uses a simple streak-based interval growth rule. A direct comparison of expanding versus uniform versus streak-based scheduling was not conducted and remains an open question.

6. **CPU-only, non-GPU workload.** The evaluation did not exercise GPU resources. Generalization to GPU-accelerated or LLM-in-the-loop settings is not addressed. This was a pure Python simulation, not a llama.cpp hook-prototype or CUDA calibration.

7. **No LLM-as-learner evaluation.** The recommended next step — a small human or LLM-as-learner delayed recall pilot — has not been conducted. The current result is strictly a computational proof-of-concept.

## Reproducibility Checklist

- **Random seeds:** 1,000 independent seeds in the main evaluation; 5 seeds in the smoke test. Seeds are deterministically derived from the run index.
- **Code:** `scripts/evidence_recall_eval.py` — deterministic Monte Carlo harness.
- **Data:** `data/evidence_cards.json` — five source-grounded recall cards.
- **Primary results:** `results/main/summary.json`, `results/main/trials.csv`.
- **Smoke results:** `results/smoke/summary.json`.
- **Logs:** `logs/smoke.log`, `logs/main_eval.log`, `logs/stat_analysis.log`, `logs/environment.log`.
- **Decision record:** `.omx/project_decision.json`.
- **Environment:** Python 3, GB10-class host, no GPU required, swap disabled. Full environment telemetry in `logs/environment.log`.
- **Statistical method:** Paired mean differences with normal-approximation 95% confidence intervals and per-seed win rates, computed over 1,000 paired observations.
- **Claim audit status:** The claim ledger (`claim_ledger.json`) contains no formally audit-approved claims. The limitation note states "Model-authored draft; human claim audit required." Readers should treat all claims in this draft as unverified pending independent audit.

## Conclusion

A minimal evidence-grounded recall teacher with adaptive due-card scheduling outperformed three equal-budget baselines in a deterministic simulated delayed-recall evaluation over 1,000 seeds. The advantage over random quiz was modest but statistically reliable (+0.038 absolute, 95% CI [0.034, 0.042], win rate 73.9%). The 26.1% loss rate against random quiz is a genuine limitation: under a small corpus and tight budget, adaptive scheduling does not reliably dominate naive random selection. Advantages over massed quiz and reread-only were large and consistent (100% win rates), consistent with the spacing and retrieval-practice literature. Grounding coverage was maintained at 1.0 across all conditions.

These findings establish the computational viability of a small, auditable adaptive scheduling prototype that preserves source grounding. However, the result is a toy-simulation proof-of-concept under a synthetic forgetting model with a five-card corpus. It does not demonstrate human learning efficacy, and the mixed win rate against random quiz tempers the strength of even the simulation-level claim. The recommended next step is a small human or LLM-as-learner delayed recall pilot with held-out evidence cards, comparing adaptive scheduling against random quiz under identical exposure budgets, to determine whether the modest simulation-level advantage translates to measurable learning gains.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Evidence cards | `data/evidence_cards.json` |
| Evaluation harness | `scripts/evidence_recall_eval.py` |
| Smoke test summary | `results/smoke/summary.json` |
| Main evaluation summary | `results/main/summary.json` |
| Main evaluation trials | `results/main/trials.csv` |
| Smoke test log | `logs/smoke.log` |
| Main evaluation log | `logs/main_eval.log` |
| Statistical analysis log | `logs/stat_analysis.log` |
| Environment telemetry | `logs/environment.log` |
| Project decision record | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Metrics | `.omx/metrics.json` |
| Claim ledger | `papers/.../claim_ledger.json` |
| Evidence bundle | `papers/.../evidence_bundle.json` |
| Paper manifest | `papers/.../paper_manifest.json` |

## External Sources Referenced

- Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning. https://pubmed.ncbi.nlm.nih.gov/16507066/
- Agarwal, P. K., Nunes, L. G. D., & Blunt, J. R. (2021). Retrieval practice classroom systematic review. https://link.springer.com/article/10.1007/s10648-021-09595-9
- Latimier, A., Peyre, H., & Ramus, F. (2021). Spaced retrieval meta-analysis. https://eric.ed.gov/?id=EJ1310148
- Carpenter, S. K., Pan, S. C., & Butler, A. C. (2022). Spacing and retrieval practice review. https://www.nature.com/articles/s44159-022-00089-1
