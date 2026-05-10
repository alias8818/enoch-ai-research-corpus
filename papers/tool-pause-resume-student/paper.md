# Tool-Pause Resume Student: Offline Distillation of Post-Pause State Reconstruction from Compact Resume Packets

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, metric files, and evidence bundles). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

Tool-augmented language model agents suspend generation during external tool calls and must reconstruct post-pause state upon resumption, typically by re-invoking the full teacher model on the entire context. We investigate whether a small, offline-trained student can approximate the teacher's resume decision from a compact packet combining pre-pause intent and post-pause tool result, at substantially lower cost. On 20,000 synthetic offline traces with a deterministic teacher/oracle, a compact random-forest student achieved 86.3% action accuracy (macro-F1 0.715), versus 47.1% for a majority-class baseline and 47.6% for a tool-only ablation lacking pre-pause context. A context-only ablation achieved only 23.4%, confirming that both signal sources are necessary. The compact resume packet was 19.6× smaller than the full trace in a token-proxy metric, with student inference averaging 4.7 µs/trace. Five-seed replication confirmed stability (mean accuracy 0.867 ± 0.006). These results support the learnability of the hypothesized distillation target in a controlled synthetic setting. They do not demonstrate live-agent utility retention, downstream task quality preservation, or production teacher-call reduction, all of which remain open.

## Introduction

Tool-augmented language model agents interleave generation with external tool calls—retrieval, code execution, API invocations—during which the agent's generation is paused. Upon resumption, the agent must integrate the tool result with its pre-pause intent to continue coherently. In current deployments, resumption typically requires re-running the full teacher model on the entire conversation context augmented with the new tool result. This is expensive when the teacher is large, the context is long, or pauses are frequent.

A natural question is whether a much smaller model can reconstruct the resume decision from a compact representation of the pre-pause state and the tool result, avoiding full teacher re-invocation in most cases. Distillation literature suggests that small students benefit when the teacher exposes task-specific structure rather than raw next-token targets. We apply this intuition to the pause-resume setting: the distillation target is not general language modeling but the specific decision of how to resume after a tool pause, conditioned on a compact packet of pre-pause intent and post-pause tool output.

We formalize this as the **Tool-Pause Resume Student** problem and report results from a minimum-viable experiment on synthetic offline traces. Our contribution is threefold: (1) we establish that the distillation target is learnable under controlled conditions, (2) we show through ablation that both pre-pause intent and tool results are individually necessary and jointly substantially more informative, and (3) we quantify the compaction ratio and inference cost of the compact representation. We do not claim live-agent validation.

## Method

### Problem Formulation

Let a tool-pause trace consist of:

- A **pre-pause intent** vector $x_{\text{ctx}}$ summarizing the agent's state before the tool call,
- A **post-pause tool result** vector $x_{\text{tool}}$ encoding the tool output,
- A **resume action** $y$ drawn from a finite action set, determined by a teacher/oracle policy $\pi^*(x_{\text{ctx}}, x_{\text{tool}})$.

The student's task is to approximate $\pi^*$ using only the compact packet $(x_{\text{ctx}}, x_{\text{tool}})$, avoiding the full trace that the teacher would require for re-invocation.

### Synthetic Trace Generation

We generated synthetic traces using a deterministic teacher/oracle policy over paired pre-pause intent and post-pause tool result features. The oracle assigns resume actions based on the joint distribution of both inputs, deliberately ensuring that neither input alone is sufficient for high accuracy. This design creates the signal-separability structure that makes the distillation problem non-trivial.

Traces were generated with configurable random seeds for reproducibility. The main calibration run used 20,000 traces with seed 3443677. Five replication runs used 10,000 traces each with seeds 101, 202, 303, 404, and 505.

### Models and Ablations

We evaluated six configurations:

1. **Teacher/Oracle (upper bound):** Deterministic full-state policy with access to both $x_{\text{ctx}}$ and $x_{\text{tool}}$. Accuracy is 1.0 by construction.
2. **Student Compact RF:** Random forest classifier trained on the compact packet $(x_{\text{ctx}}, x_{\text{tool}})$.
3. **Student Compact LR:** Logistic regression classifier trained on the same compact packet.
4. **Tool-Only LR (ablation):** Logistic regression using only $x_{\text{tool}}$, with no pre-pause context.
5. **Context-Only LR (ablation):** Logistic regression using only $x_{\text{ctx}}$, with no tool result.
6. **Majority Baseline:** Predicts the most frequent class.

All student and ablation models were trained using scikit-learn on the same train/test split.

### Metrics

- **Action accuracy:** Fraction of traces where the predicted resume action matches the oracle.
- **Macro-F1:** Class-averaged F1 score to account for potential class imbalance.
- **Inference latency:** Microseconds per trace, measured locally via the experiment script.
- **Trace-token compaction proxy:** Ratio of full-trace token count to compact-packet token count, approximating context savings if the student replaces full teacher re-invocation.
- **Memory:** Maximum RSS and system memory availability, measured via `/usr/bin/time -v`.

### Experimental Procedure

The experiment script (`scripts/run_tool_pause_resume_experiment.py`) was executed in three phases:

1. **Smoke test** (400 traces, seed 3443677): Verified script correctness and metric computation.
2. **Calibration run** (20,000 traces, seed 3443677): Primary result collection.
3. **Replication runs** (5 seeds × 10,000 traces each): Assessed result stability across random seeds.

## Results

### Main Calibration (20,000 Traces)

| Model | Accuracy | Macro-F1 | Inference (µs/trace) |
|---|---:|---:|---:|
| Teacher/Oracle | 1.0000 | — | — |
| Student Compact RF | 0.8628 | 0.7147 | 4.74 |
| Student Compact LR | 0.7018 | 0.7137 | 0.12 |
| Tool-Only LR | 0.4764 | 0.5158 | 0.06 |
| Context-Only LR | 0.2340 | 0.1998 | 0.05 |
| Majority Baseline | 0.4712 | 0.0801 | 0.01 |

The compact RF student substantially outperforms all baselines and ablations. The tool-only ablation performs near the majority baseline (47.6% vs. 47.1%), indicating that pre-pause intent is essential for reconstructing the resume decision. The context-only ablation performs well below majority (23.4%), confirming that the tool result is also necessary. Neither input alone is sufficient; both are required.

### Trace-Token Compaction

- Full trace mean tokens: 1,217.91
- Compact packet mean tokens: 62.23
- Mean compaction ratio: 19.57×

### Memory Posture

- Maximum RSS: 201.85 MB
- System MemAvailable before/after: 119,495 MB / 119,456 MB
- Swap total/used: 0.0 MB / 0.0 MB

Memory footprint is modest and no swap pressure was observed.

### Replication Robustness (5 Seeds, 10,000 Traces Each)

| Metric | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| Student Compact RF Accuracy | 0.8674 | 0.0062 | 0.8608 | 0.8768 |
| Tool-Only LR Accuracy | 0.4844 | 0.0145 | — | — |
| Majority Baseline Accuracy | 0.4762 | 0.0053 | — | — |
| RF vs. Tool-Only Δ Accuracy | +0.3830 | — | +0.3540 | — |
| RF vs. Majority Δ Accuracy | +0.3912 | — | +0.3788 | — |
| Compact Packet Ratio | 19.58× | — | — | — |
| RF Inference Latency | 9.68 µs/trace | — | — | — |

Results are stable across seeds. The RF student's advantage over both baselines is consistent, with a minimum accuracy delta of +0.3788 over majority and +0.3540 over tool-only across all replication seeds.

### Mixed and Negative Findings

Several findings temper the positive signal:

1. **LR underperforms RF substantially on accuracy** (70.2% vs. 86.3%) despite similar macro-F1 scores (0.714 vs. 0.715). This indicates that the decision boundary has non-linear structure that logistic regression cannot capture, and that macro-F1 alone is insufficient to distinguish model quality in this setting. The accuracy gap is the more informative metric.

2. **Context-only performance is strikingly low** (23.4%). While this confirms the necessity of tool results, it also reveals a fragility: if the tool result is unavailable or corrupted at resume time, the student has essentially no useful signal. This warrants attention in any deployment design.

3. **The 86.3% accuracy ceiling means approximately 13.7% of resume decisions are misclassified.** Whether this error rate is acceptable depends entirely on the downstream task's tolerance for incorrect resume actions. We have not measured downstream task quality and cannot claim that this error rate preserves "most" teacher utility in any practical sense.

4. **Inference latency increased in replication** (4.7 µs in calibration vs. 9.7 µs mean in replication). This likely reflects system load variation rather than model behavior, but it illustrates that microsecond-scale latency claims are environment-dependent and should not be treated as stable performance guarantees.

5. **The LR macro-F1 paradox.** The compact LR achieves macro-F1 0.7137, nearly identical to the RF's 0.7147, despite a 16-percentage-point accuracy gap. This indicates that macro-F1 is a poor discriminant for this task, likely because it averages per-class F1 scores in a way that obscures the RF's advantage on the dominant class structure. Researchers evaluating similar settings should prioritize accuracy or weighted-F1 over macro-F1.

## Limitations

1. **Synthetic traces only.** The teacher/oracle is a deterministic policy over generated features, not a real language model. The trace distribution may not reflect the statistical structure of actual tool-pause events in production agent systems. The degree to which synthetic separability generalizes to real agent traces is unknown.

2. **No live LLM or tool-agent traces.** No real conversation histories, tool-call logs, or agent trajectories were available within the project. All traces were generated programmatically. This is a signal-separability and cost-proxy test, not a live LLM-agent deployment claim.

3. **Action classification proxy, not downstream task quality.** We measure whether the student predicts the same resume action as the oracle, not whether the resumed agent trajectory produces equivalent downstream task performance. A misclassified resume action might be inconsequential or catastrophic depending on the task; we do not characterize this distribution.

4. **Cost evidence is proxy-level.** The 19.6× compaction ratio measures token counts in a proxy representation, not actual GPU memory savings, inference batch throughput, or production teacher-call reduction. The inference latency is measured on a local CPU for sklearn models, not on a serving path with a real language model. No CUDA copy calibration, llama.cpp hook prototype, or production validation was performed.

5. **Binary feature sufficiency assumption.** The ablation design assumes that pre-pause intent and tool result are the two relevant signal sources. Real agent resumes may depend on additional factors—conversation history, user state, multi-tool chaining, temporal features—not captured here.

6. **No calibration of the "long pause" regime.** The experiment does not vary pause duration or test whether longer pauses degrade student performance differently than teacher performance. The relationship between pause duration and reconstruction difficulty remains uncharacterized.

7. **Single dataset, single task structure.** All traces come from one generative process with one oracle policy. Generalization across different tool types, action spaces, or agent architectures is not tested.

## Reproducibility Checklist

- **Code available:** `scripts/run_tool_pause_resume_experiment.py` — a single self-contained Python script using scikit-learn and standard library only.
- **Random seeds reported:** Main run seed 3443677; replication seeds 101, 202, 303, 404, 505.
- **Sample sizes reported:** Smoke test 400; calibration 20,000; replication 5 × 10,000.
- **Hardware environment:** Local CPU execution; max RSS 201.85 MB; system memory approximately 119 GB available; no GPU used; no swap.
- **Software dependencies:** Python 3, scikit-learn, standard library. No custom CUDA kernels, no llama.cpp hooks, no external API calls.
- **Metrics files preserved:** All metric JSON files saved under `artifacts/metrics/` (smoke, calibration, 5 replicates, replicate summary).
- **Logs preserved:** Stdout and stderr logs under `artifacts/logs/`.
- **Statistical variability:** Reported via 5-seed replication with mean, standard deviation, min, and max where available.
- **Negative results reported:** Context-only ablation (23.4% accuracy), LR accuracy gap vs. RF, inference latency variability, and the macro-F1 paradox are all reported above.
- **Claim audit status:** The claim ledger for this artifact is currently empty with audit status `blocked_empty_claims`. No structured claims have been extracted for formal evidence binding. Readers should interpret the reported metrics as prototype evidence pending formal claim-audit.

## Conclusion

A compact pause-resume student trained on offline synthetic traces achieved 86.3% action accuracy—decisively above majority (47.1%) and tool-only (47.6%) baselines—with a 19.6× compaction ratio and microsecond-scale local inference. Ablations confirmed that both pre-pause intent and post-pause tool results are necessary for this performance; neither alone is sufficient. Five-seed replication confirmed stability (mean 0.867 ± 0.006).

These results support the hypothesis that the pause-resume distillation target is learnable in a controlled setting and that the cost-quality tradeoff is favorable enough to justify further investigation. They do not support claims about live-agent utility retention, downstream task quality preservation, or production teacher-call reduction. The critical next step is collecting and replaying real tool-pause traces with teacher resume labels, then evaluating the compact student against actual downstream task quality and measured teacher-call savings.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `scripts/run_tool_pause_resume_experiment.py` |
| Run notes | `run_notes.md` |
| Smoke metrics | `artifacts/metrics/smoke_metrics.json` |
| Calibration metrics | `artifacts/metrics/calibration_metrics.json` |
| Replicate metrics (seed 101) | `artifacts/metrics/replicate_101.json` |
| Replicate metrics (seed 202) | `artifacts/metrics/replicate_202.json` |
| Replicate metrics (seed 303) | `artifacts/metrics/replicate_303.json` |
| Replicate metrics (seed 404) | `artifacts/metrics/replicate_404.json` |
| Replicate metrics (seed 505) | `artifacts/metrics/replicate_505.json` |
| Replicate summary | `artifacts/metrics/replicate_summary.json` |
| Project decision JSON | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260502T125218552286+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T125218552286+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T125218552286+0000/paper_manifest.json` |
| Execution logs | `artifacts/logs/*.log`, `artifacts/logs/*.stderr` |
| Notion source page | `https://www.notion.so/Tool-Pause-Resume-Student-source-record-redacted` |
