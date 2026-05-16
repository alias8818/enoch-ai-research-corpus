# Minimum Curriculum Search: Exact and Greedy Discovery of Shortest Training Sequences for Fixed Learners

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has certified these claims.

---

## Abstract

We investigate *Minimum Curriculum Search* (MCS): the problem of finding the shortest ordered sequence of training examples that drives a fixed learner to a target evaluation score on a given task. We formalize MCS as a combinatorial search over ordered subsets of a finite candidate pool and implement two solution strategies—exhaustive enumeration and greedy forward selection—using a deterministic single-pass perceptron as the fixed learner. On four Boolean concept tasks, exhaustive search discovers exact minimum curricula for all three linearly separable concepts (lengths 3, 3, and 6 for `x1`, `or`, and `and` respectively) and correctly fails to find any curriculum for `xor`, consistent with the known representational impossibility for linear classifiers. On 20 synthetic margin-separated 2D linear classification tasks, greedy forward selection reaches ≥0.99 held-out accuracy in all 20 trials with a mean curriculum length of 2.0, substantially outperforming same-length random baselines (mean accuracy 0.758). These results establish that MCS is a concrete, executable problem formulation with non-trivial solutions on small-scale tasks, but they do not demonstrate applicability to neural network learners or realistic training regimes.

## Introduction

Curriculum learning—ordering training examples so that easier or more informative examples appear earlier—has been studied as a strategy for accelerating convergence and improving generalization. Bengio et al. formalize curricula as sequences of training distributions or embedded training sets and report convergence and generalization effects from meaningful example ordering. Self-paced learning (Kumar, Packer, and Koller, 2010) iteratively selects easy samples while learning parameters, supporting the framing of training as a selective process. Dataset distillation (Wang et al., 2018/2020) compresses a large dataset into very few synthetic examples for a fixed learner, showing that MCS is related to—but distinct from—dataset distillation, which synthesizes new examples rather than selecting from a fixed pool.

A complementary question, less thoroughly explored, is: given a fixed learner, a fixed candidate pool of training examples, and a target evaluation score, what is the *shortest* ordered sequence of examples that achieves the target? We call this the *Minimum Curriculum Search* (MCS) problem.

This paper makes the following contributions:

1. We formalize MCS as a combinatorial optimization problem over ordered subsets of a finite candidate set.
2. We implement and evaluate two search algorithms—exhaustive enumeration and greedy forward selection—on Boolean concept tasks and synthetic linear classification tasks using a deterministic perceptron.
3. We report a clean negative result: MCS correctly identifies representational impossibility when the learner cannot solve the target task regardless of curriculum.
4. We provide an honest assessment of the gap between these toy results and any claim of practical utility for deep network training.

## Method

### Problem Formulation

Let $\mathcal{L}$ be a deterministic learner that, given an ordered sequence of training examples $S = (e_1, e_2, \ldots, e_k)$, produces parameters $\theta = \mathcal{L}(S)$. Let $\mathcal{E}$ be a finite candidate pool of examples, $\mathcal{T}$ a target task with evaluation function $\text{score}(\theta, \mathcal{T}) \in [0, 1]$, and $\tau$ a target score. The Minimum Curriculum Search problem is:

$$\min_{k} \min_{S \in \mathcal{E}^k} k \quad \text{subject to} \quad \text{score}(\mathcal{L}(S), \mathcal{T}) \geq \tau$$

where $\mathcal{E}^k$ denotes the set of all ordered sequences of length $k$ drawn from $\mathcal{E}$ (with repetition allowed).

### Learner

We use a deterministic single-pass perceptron as the fixed learner $\mathcal{L}$. The perceptron initializes weights to zero and processes examples in order, performing a weight update whenever a misclassification occurs. This learner is deterministic given a fixed input sequence, making search results reproducible. It is also limited to linearly separable concepts, which provides a natural test of whether MCS correctly identifies impossibility.

### Search Algorithms

**Exhaustive enumeration.** For Boolean tasks with a candidate pool of four binary inputs, we enumerate all ordered sequences of length $k = 1, 2, 3, \ldots$ up to a bound, evaluate the learner on each, and return the first sequence achieving the target score. The search terminates at the smallest $k$ for which a solution is found, or at the bound if no solution exists.

**Greedy forward selection.** For continuous tasks with larger candidate pools, exhaustive search is infeasible. We use a greedy procedure: starting from an empty curriculum, at each step we evaluate all candidate examples as the next addition, select the one yielding the highest held-out accuracy after retraining from scratch on the extended curriculum, and stop when the target score is reached.

### Tasks

**Boolean concepts.** Four tasks over the binary input space $\{0, 1\}^2$: `x1` (first input bit), `or`, `and`, and `xor`. The candidate pool consists of all four inputs, each labeled according to the target concept. The evaluation score is accuracy on the same four examples (perfect classification required).

**Margin-separated Gaussian classification.** Twenty synthetic 2D binary classification tasks, each generated by drawing 500 points from two isotropic Gaussian distributions separated by a margin. A held-out test set of 500 points is used for evaluation. The target score is $\tau = 0.99$ held-out accuracy.

### Baseline

For the greedy search tasks, we compare against a random baseline: for each trial, we draw a random ordered sequence of the same length as the discovered curriculum and report the held-out accuracy of the learner trained on that sequence. This controls for the possibility that any short sequence of the same length would suffice.

## Results

### Exact Boolean Minimum Curricula

| Task | Status | Minimum length | Sequences checked | Discovered curriculum |
|---|---|---:|---:|---|
| `x1` | Found | 3 | 30 | `[[0,0,−1], [1,0,1], [0,0,−1]]` |
| `or` | Found | 3 | 34 | `[[0,0,−1], [1,1,1], [0,0,−1]]` |
| `and` | Found | 6 | 2,164 | `[[0,0,−1], [1,1,1], [0,0,−1], [0,1,−1], [1,1,1], [1,0,−1]]` |
| `xor` | Not found | — | 87,381 | None |

For the three linearly separable concepts, exhaustive search identified exact minimum curricula. The `x1` and `or` tasks require only three examples; `and` requires six, reflecting the more complex decision boundary. The discovered curricula are not simply subsets of the candidate pool—they contain repeated examples, confirming that example ordering and repetition matter for the single-pass perceptron.

The `xor` result is a clean negative control. After checking 87,381 sequences up to length 8, no curriculum was found. This is expected: XOR is not linearly separable, so no sequence of examples can make a linear perceptron solve it. The impossibility can be verified algebraically: XOR requires simultaneously satisfying $b < 0$, $w_1 + b \geq 0$, $w_2 + b \geq 0$, and $w_1 + w_2 + b < 0$; the middle two inequalities imply $w_1 + w_2 + b \geq -b > 0$, contradicting the fourth. MCS thus correctly identifies a representational impossibility rather than reporting a spurious near-miss.

### Greedy Margin-Gaussian Calibration

Over 20 independent trials (seeds 0–19), greedy forward selection achieved the following:

| Metric | Value |
|---|---|
| Target reached | 20 / 20 |
| Curriculum length (mean) | 2.0 |
| Curriculum length (min, max) | 2, 2 |
| Final held-out accuracy (mean) | 0.9997 |
| Random same-length baseline accuracy (mean) | 0.7585 |

The greedy search consistently found two-example curricula sufficient for near-perfect held-out accuracy. The selected examples typically consist of one high-value example from each side of the linear separator, providing the perceptron with maximal information about the decision boundary.

The random baseline confirms that the discovered curricula are not trivially short: a random two-example sequence achieves only 75.9% held-out accuracy on average, compared to 99.97% for the greedily selected sequences. This gap demonstrates that the content and ordering of the curriculum matters, not merely its length.

### Resource Usage

Peak memory usage was 35,796 KB RSS. No swap was configured or needed. Total compute time was negligible (sub-second per trial) given the small problem scale. These resource figures characterize a toy prototype, not a production workload.

## Limitations

We enumerate the principal limitations honestly:

1. **Learner scope.** The fixed learner is a deterministic single-pass perceptron. Whether MCS produces meaningful curricula for multi-layer neural networks, transformers, or LLM fine-tuning regimes is entirely untested. The perceptron's simplicity makes exhaustive and greedy search tractable; scaling to modern architectures would require fundamentally different search strategies.

2. **Problem scale.** The Boolean tasks involve four candidate examples; the Gaussian tasks involve 500. Real-world training pools contain millions of examples. The combinatorial explosion of ordered sequence search makes exact MCS intractable at scale, and greedy search offers no global optimality guarantee.

3. **Greedy suboptimality.** Greedy forward selection is not guaranteed to find globally minimal curricula beyond the exhaustive tiny cases. On larger candidate sets, greedy curricula may be longer than necessary.

4. **Evaluation protocol.** Boolean tasks evaluate on the training pool itself (no held-out set). Gaussian tasks use a held-out set but the tasks are synthetically easy (large margin, linear boundary). Performance on harder or noisier tasks is unknown.

5. **Determinism assumption.** MCS as formulated assumes a deterministic learner. Stochastic learners (e.g., SGD-trained networks) would require a probabilistic reformulation of the target score, adding substantial complexity.

6. **Curriculum structure.** The discovered curricula contain repeated examples, which is an artifact of the single-pass perceptron update rule. Whether repetition is beneficial or necessary for other learners is an open question.

7. **Source material access.** The original project description (Notion page) was not available as structured content during execution; the problem was operationalized from the project title alone. The implemented MCS may differ from the originally intended formulation.

8. **Claim audit status.** The automated claim ledger for this artifact recorded no structured claims and flagged the audit as blocked. The results reported here are drawn directly from run notes and machine-readable metrics files but have not passed a formal claim-evidence audit pipeline.

## Reproducibility Checklist

- **Algorithm description:** Complete in Method section; source code in `minimum_curriculum_search.py`.
- **Random seeds:** Specified via `--seed` flag; calibration used seeds 0–19.
- **Software versions:** Python 3.12.3, NumPy 2.4.4, Linux 6.17.0-1014-nvidia-aarch64, glibc 2.39.
- **Hardware:** aarch64 platform, 122 GB available memory, no swap, peak RSS 35,796 KB.
- **Complete results:** Boolean summary in `results/calibration/boolean_summary.csv`; greedy trace in `results/calibration/gaussian_trace.csv`; machine-readable metrics in `results/calibration/metrics.json`.
- **Execution logs:** `results_smoke.log`, `results_calibration.log`.
- **Statistical reporting:** All 20 trials reported; means, mins, and maxs provided; no selective reporting.
- **Negative results:** XOR impossibility reported fully with sequence count and algebraic explanation.
- **Baseline comparison:** Random same-length baseline included for greedy experiments.
- **Evidence classification:** All results are toy simulation / prototype calibration on a deterministic perceptron. No CUDA, GPU, llama.cpp, or production validation results are present.

## Conclusion

Minimum Curriculum Search is a well-defined combinatorial problem: find the shortest ordered training sequence that makes a fixed learner achieve a target score. On small-scale tasks with a deterministic perceptron, the problem is solvable—exhaustive search finds exact minima for linearly separable Boolean concepts, greedy search finds effective short curricula for synthetic linear tasks, and the search correctly identifies representational impossibility for non-linearly-separable concepts.

However, these results are confined to toy settings. The gap between a single-pass perceptron on four Boolean inputs and a stochastic gradient-descent-trained neural network on realistic data is large and unbridged. Whether MCS generalizes to produce useful, non-trivial curricula for deep learners—and whether efficient approximate search algorithms exist for that regime—remains an open empirical question.

The primary value of this work is conceptual: it establishes that the minimum curriculum problem can be made concrete, that it has non-trivial solutions and identifiable impossibility cases, and that greedy selection can substantially outperform random baselines. These are necessary but not sufficient conditions for practical utility. Scaling MCS to neural learners is the critical next step, and it should be approached with the expectation that both the search algorithms and the notion of "minimum" may need substantial revision.

---

## Referenced Artifacts

| Artifact | Description |
|---|---|
| `minimum_curriculum_search.py` | Implementation of exhaustive and greedy MCS algorithms |
| `run_notes.md` | Research log including literature grounding, commands, and interpretation |
| `.omx/project_decision.json` | Controller decision record with key metrics and risk assessment |
| `results/calibration/metrics.json` | Machine-readable environment and performance metrics |
| `results/calibration/boolean_summary.csv` | Per-task Boolean search results |
| `results/calibration/gaussian_trace.csv` | Per-trial greedy search trace |
| `results_smoke.log` | Execution log for initial smoke test |
| `results_calibration.log` | Execution log for 20-seed calibration run |
| `papers/.../claim_ledger.json` | Claim audit ledger (status: blocked_empty_claims) |
| `papers/.../evidence_bundle.json` | Evidence bundle (minimal; source/project/run IDs only) |
| `papers/.../paper_manifest.json` | Paper generation manifest |
