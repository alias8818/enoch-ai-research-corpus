# Confidence-Triggered Reread Training: A Synthetic Study of Learned Reread Policies for Budget-Constrained Retrieval

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is claimed or implied.

---

## Abstract

We investigate whether a small learned confidence-triggered reread policy can improve the accuracy of a constrained-context question-answering system relative to answer-only training on partial context. In a synthetic key/value retrieval task with distractor facts, a first-pass answerer operates on a reduced fact budget where the target fact may be absent. A learned reread trigger, conditioned on confidence features (maximum class probability, margin, entropy, and budget fraction), decides whether to request a full-context reread. Across five random seeds with 8,000 training, 2,000 validation, and 3,000 test examples each, the confidence-triggered reread training (CTRR) policy improved accuracy over the partial-context answer-only baseline by a mean of 8.48 percentage points (worst seed: 6.20 pp; best seed: 11.78 pp) at reread rates of 20–26%. CTRR also outperformed matched-rate random rereading by a mean of 2.29 percentage points, indicating that the trigger learned useful confidence structure rather than merely spending additional context. However, these results are confined to a synthetic retrieval task with a non-neural answerer; generalization to neural language models and real-world RAG benchmarks remains unproven.

## 1. Introduction

Retrieval-augmented generation (RAG) systems frequently operate under context budget constraints, where only a subset of retrieved passages can be presented to the answerer. When the budget excludes a critical fact, answer quality degrades. A natural mitigation is to allow the system to request additional context—but only when the initial answer is likely wrong. This raises a policy question: can a system learn to identify low-confidence situations and selectively request more context, achieving better accuracy per unit of context consumed than naive strategies?

We study this question in a controlled synthetic setting. We define a Confidence-Triggered Reread Training (CTRR) policy that observes confidence features from a first-pass answerer operating on reduced context and decides whether to reread the full context before producing a final answer. We compare CTRR against (1) an answer-only baseline that never rereads, (2) a matched-rate random reread control that rereads at the same rate but without confidence conditioning, and (3) a full-context oracle.

The goal is not to demonstrate production viability but to isolate whether a learned confidence trigger can extract useful signal from first-pass uncertainty and convert it into accuracy gains under controlled conditions. We deliberately use a non-neural answerer (regex matching with learned priors) to separate the trigger mechanism from the complexities of end-to-end language model training.

## 2. Method

### 2.1 Task Design

We construct a synthetic key/value retrieval task. Each example consists of a set of key–value fact pairs, some of which are distractors, and a query targeting one specific key. The answerer must identify the correct value for the queried key. The full context always contains the target fact, making the full-context oracle trivially perfect.

On each trial, the first-pass answerer receives only a *budget* $b$ of facts drawn from the full set. When $b$ is small relative to the total number of facts, the target fact is frequently absent from the first-pass context, inducing predictable accuracy degradation.

### 2.2 Models

**Partial-context answer-only baseline.** A classifier trained and evaluated on the reduced fact budget $b$. This model never requests additional context.

**CTRR policy.** The same first-pass classifier produces an initial answer along with confidence features: maximum class probability, margin (difference between top-two class probabilities), entropy over the class distribution, and budget fraction ($b / b_{\text{full}}$). A learned binary trigger, trained on these features, decides whether to reread. If triggered, the system reads the full context and a separate full-context classifier produces the final answer. If not triggered, the first-pass answer stands.

**Matched-rate random reread control.** Rereads at the same rate as the selected CTRR policy but selects examples uniformly at random rather than based on confidence features. This controls for the effect of simply spending more context.

**Full-context oracle.** Always reads the full context. Serves as an upper bound.

### 2.3 Training

The first-pass classifier and full-context classifier are trained on their respective context distributions. The reread trigger is trained as a binary classifier on the confidence features, with labels derived from whether the first-pass answer was correct (no reread needed) or incorrect (reread beneficial). Threshold selection is performed on the validation set.

### 2.4 Experimental Protocol

We run five seeds (7, 11, 13, 17, 19). Each seed uses 8,000 training examples, 2,000 validation examples, and 3,000 test examples. We sweep first-pass fact budgets $b \in \{2, 3, 4, 6, 8\}$ and reread trigger thresholds $\theta \in \{0.2, 0.4, 0.6, 0.8\}$, selecting the threshold per budget that maximizes validation accuracy subject to a reread-rate ceiling of 35%.

### 2.5 Metrics

Primary metric: test-set accuracy. We report:

- **Partial accuracy**: answer-only baseline accuracy at budget $b$.
- **CTRR accuracy**: accuracy of the confidence-triggered reread policy.
- **Gain**: CTRR accuracy minus partial accuracy, in percentage points (pp).
- **Matched-random accuracy**: accuracy of random reread at the same rate.
- **CTRR vs. random**: CTRR accuracy minus matched-random accuracy, in pp.
- **Reread rate**: fraction of examples for which the trigger requests full context.
- **Average fact reads**: mean number of fact entries consumed per example (first-pass plus reread).

## 3. Results

### 3.1 Aggregate Performance Across Budgets

Table 1 presents the aggregate results across five seeds.

**Table 1.** CTRR performance by first-pass fact budget, aggregated over five seeds.

| Budget | Partial Acc. | CTRR Acc. | Gain (pp) | Random Reread Acc. | CTRR vs. Random (pp) | Reread Rate | Avg Fact Reads |
|-------:|-------------:|----------:|----------:|-------------------:|---------------------:|------------:|---------------:|
| 2      | 0.6612       | 0.7444    | 8.32      | 0.7352             | 0.92                 | 0.2225      | 5.56           |
| 3      | 0.6855       | 0.7626    | 7.71      | 0.7497             | 1.29                 | 0.2054      | 6.29           |
| 4      | 0.7069       | 0.8026    | 9.57      | 0.7812             | 2.14                 | 0.2558      | 8.09           |
| 6      | 0.7581       | 0.8369    | 7.87      | 0.8097             | 2.72                 | 0.2145      | 9.43           |
| 8      | 0.8039       | 0.8931    | 8.92      | 0.8493             | 4.38                 | 0.2321      | 11.71          |

### 3.2 Summary Statistics

Across all budgets and seeds:

- **Mean CTRR gain over partial baseline:** 8.48 pp.
- **Worst single-seed mean gain:** 6.20 pp.
- **Best single-seed mean gain:** 11.78 pp.
- **Mean CTRR advantage over matched-rate random reread:** 2.29 pp.
- **Full-context oracle accuracy:** 1.00 (by construction).

The CTRR policy consistently outperforms both the no-reread baseline and the random reread control across all budgets. The advantage over random reread grows with budget (from 0.92 pp at budget 2 to 4.38 pp at budget 8), suggesting that the trigger becomes more informative as the first-pass answerer's confidence features carry more structure at higher budgets. However, this pattern should be interpreted cautiously: the number of budgets is small (five), and the trend has not been formally tested for significance.

### 3.3 Reread Rate and Resource Usage

Reread rates ranged from 20.5% to 25.6% across budgets, well within the 35% ceiling. Average fact reads per example ranged from 5.56 (budget 2) to 11.71 (budget 8), reflecting the additive cost of full-context rereads.

Internal elapsed time per seed averaged approximately 2.04 seconds. Maximum RSS averaged approximately 194.5 MB. No swap was required. These figures reflect the lightweight nature of the synthetic task and non-neural answerer; they should not be interpreted as indicative of production-scale resource requirements.

### 3.4 Seed Variability

The spread between worst-seed (6.20 pp) and best-seed (11.78 pp) mean gains indicates non-trivial variance. This is expected given the stochastic training and the relatively small dataset sizes. The consistent positive direction across all seeds and budgets supports the viability of the mechanism in this setting, but the magnitude of the effect should be interpreted with appropriate uncertainty. We do not report confidence intervals because the number of seeds (five) is too small for reliable interval estimation.

### 3.5 Negative and Mixed Observations

Several aspects of the results temper the positive findings:

- The gain over random reread, while consistent, is modest in absolute terms (mean 2.29 pp). Whether this margin is practically meaningful depends on application-specific cost-accuracy tradeoffs that are not modeled here.
- The CTRR policy does not approach the full-context oracle (1.00 accuracy). At budget 8, CTRR achieves 0.8931, leaving a gap of 10.69 pp even with rereading 23% of examples.
- The relationship between budget and gain is not monotonic (budget 4 yields the highest gain at 9.57 pp, while budget 3 yields the lowest at 7.71 pp), suggesting that the trigger's effectiveness interacts with budget in ways not fully captured by the current sweep.

## 4. Limitations

1. **Synthetic task only.** The key/value retrieval task is a toy problem. It does not involve natural language understanding, multi-hop reasoning, or the distributional complexities of real RAG benchmarks. The extent to which CTRR gains transfer to realistic settings is unknown.

2. **Non-neural answerer.** The answerer uses regex matching with learned priors, not a neural language model. This design choice deliberately isolates the trigger mechanism but means we have no evidence that a comparable trigger can be trained inside or alongside an end-to-end LM. Confidence features in neural models may be less calibrated or less informative.

3. **Trivial full-context upper bound.** Full-context accuracy is perfect because every synthetic full context contains a directly parseable target fact. In real settings, full context does not guarantee a correct answer, which would compress the achievable gain from rereading.

4. **Cost normalization is incomplete.** Gains partly come from consuming additional context. A fair production comparison requires evaluating accuracy against a token or latency budget frontier, including the cost of the reread. The random reread control partially addresses this, but a full cost-normalized analysis on a real task distribution is needed.

5. **Narrow threshold selection.** The threshold sweep covers only four values (0.2, 0.4, 0.6, 0.8). The selected thresholds may not be optimal, and the sensitivity of results to threshold choice is not fully characterized.

6. **No comparison to alternative adaptive policies.** We compare against random reread but not against other adaptive baselines (e.g., entropy-only triggers, margin-only triggers, or reinforcement-learned policies). The relative advantage of the multi-feature learned trigger over simpler adaptive heuristics remains unquantified.

7. **Small seed count.** Five seeds provide limited statistical power. The reported mean gains are point estimates without confidence intervals, and the true variability of the method may be larger than observed.

8. **No real-model or real-benchmark validation.** This is a toy simulation result, not a llama.cpp hook-prototype result, CUDA copy calibration, or production validation. The experiment runs entirely in a Python harness on synthetic data with no GPU involvement.

## 5. Reproducibility Checklist

- **Code availability:** The experiment harness is contained in `scripts/ctrr_experiment.py`.
- **Seeds reported:** 7, 11, 13, 17, 19.
- **Dataset sizes reported:** 8,000 train / 2,000 validation / 3,000 test per seed.
- **Hyperparameters reported:** Budgets {2, 3, 4, 6, 8}; thresholds {0.2, 0.4, 0.6, 0.8}; reread-rate ceiling 0.35.
- **Confidence features reported:** max_prob, margin, entropy, budget fraction.
- **Per-seed results:** Available in `results/seed_*/summary.json` and `results/seed_*/metrics.csv`.
- **Aggregate results:** Available in `results/aggregate_summary.json` and `results/aggregate_by_budget.csv`.
- **Logs:** Available in `logs/smoke.log`, `logs/full_runs.log`, `logs/aggregate.log`, and `logs/seed_*.log`.
- **Resource measurements:** Internal elapsed time and max RSS logged per seed in `logs/time_seed_*.log`.
- **Environment:** Linux; approximately 122 GB RAM available; no GPU required for this synthetic task.
- **Result classification:** Toy simulation. No llama.cpp hook-prototype, CUDA copy calibration, or production validation was performed.

## 6. Conclusion

In a controlled synthetic key/value retrieval setting, a learned confidence-triggered reread policy improved accuracy over a partial-context answer-only baseline by a mean of 8.48 percentage points across five seeds, while rereading only 20–26% of examples. The policy also outperformed matched-rate random rereading by a mean of 2.29 percentage points, demonstrating that the trigger learned meaningful confidence structure rather than merely spending additional context. These results support the hypothesis that supervising a model to request more context when confidence is low can partially compensate for budget-induced quality loss.

However, the evidence is confined to a narrow synthetic task with a non-neural answerer. The full-context upper bound is trivially perfect, the answerer is not a language model, and cost normalization against real token/latency budgets remains incomplete. The advantage over random reread, while consistent, is modest. We conclude that the mechanism is viable in this toy setting and merits further investigation on real small-model RAG benchmarks with matched resource constraints, but real-world scientific closure is not yet established.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment harness | `scripts/ctrr_experiment.py` |
| Aggregate summary | `results/aggregate_summary.json` |
| Aggregate table by budget | `results/aggregate_by_budget.csv` |
| Seed 7 summary | `results/seed_7/summary.json` |
| Seed 11 summary | `results/seed_11/summary.json` |
| Seed 13 summary | `results/seed_13/summary.json` |
| Seed 17 summary | `results/seed_17/summary.json` |
| Seed 19 summary | `results/seed_19/summary.json` |
| Per-seed threshold sweeps | `results/seed_*/metrics.csv` |
| Smoke test log | `logs/smoke.log` |
| Full runs log | `logs/full_runs.log` |
| Aggregate log | `logs/aggregate.log` |
| Per-seed logs | `logs/seed_*.log` |
| Per-seed resource logs | `logs/time_seed_*.log` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260502T094709031729+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T094709031729+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T094709031729+0000/paper_manifest.json` |
