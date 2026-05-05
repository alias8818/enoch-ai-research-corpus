# Human Interruptibility Score: A Machine-Side Benchmark for Autonomous Agent Interrupt Responsiveness

> **AI Provenance Notice:** This draft was generated automatically from structured research artifacts (run notes, decision records, benchmark outputs) produced by an autonomous research pipeline. The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact and evaluate its claims against the referenced evidence bundles accordingly.

---

## Abstract

We propose the Human Interruptibility Score (HIS), a composite metric on the interval [0, 100] that quantifies how promptly and cleanly an autonomous agent yields to a human interrupt. HIS aggregates five sub-scores—acknowledgement latency, stop latency, action containment, state preservation, and resumability—with weights that intentionally prioritize safe stopping over mere acknowledgement. We evaluate HIS on four deterministic agent policies in a synthetic benchmark (50 trials per policy) and observe monotonic discrimination: a cooperative frequent-checkpoint policy scores 98.33, a batched-checkpoint policy scores 63.29 (range 44.83–77.50 across trials), a delayed-acknowledgement policy scores 15.00, and a policy that ignores interrupts scores 0.00. These results confirm that the metric produces the expected ordinal ranking on controlled archetypes, but they do not constitute validation against real agent runtimes, LLM-generated action sequences, or tool-use environments with irreversible external effects. We explicitly scope HIS to machine-side interruptibility and discuss why it does not measure human cognitive interruptibility.

## 1. Introduction

The deployment of long-horizon autonomous agents—particularly LLM-based agents that invoke external tools, APIs, and actuators—raises a practical safety question: when a human operator issues an interrupt, how promptly and cleanly does the agent yield?

Prior work in AI safety has formalized the problem of *safely interruptible agents*, concerned primarily with the risk that agents learn to avoid or seek interruptions (Orseau & Armstrong, 2016). More recent work on *shutdown instructability* frames appropriate shutdown behavior as a corrigibility requirement (Carey & Everitt, 2023). Separately, agent evaluation research has begun to benchmark how LLM agents handle mid-task additions, revisions, and retractions (Zou et al., 2026).

In parallel, the HCI literature has extensively studied *human* interruptibility—when a person is available to receive an interruption and what the cognitive cost of that interruption is (Horvitz & Apacible, 2003; Czerwinski et al., 2004; Mehrotra & Musolesi, 2018). These two uses of "interruptibility" are related but distinct: one concerns whether a *human* can be interrupted, the other concerns whether an *agent* will accept interruption.

This paper addresses the second meaning. We define the Human Interruptibility Score (HIS) as a machine-side operational benchmark that measures an agent's willingness and ability to yield to a human interrupt. HIS is not a measure of human attention, receptivity, or cognitive cost; making claims about those dimensions requires human-subject data or production telemetry that this work does not include.

The contributions of this work are: (1) a formal definition of HIS with five weighted sub-scores; (2) a deterministic synthetic benchmark demonstrating that HIS produces the expected ordinal ranking across four archetypal agent policies; and (3) an explicit enumeration of what HIS does and does not measure, intended to prevent misapplication to domains where its assumptions do not hold.

## 2. Method

### 2.1 Metric Definition

HIS is defined on the interval [0, 100] as a weighted sum of five sub-scores, each on [0, 1]:

$$\text{HIS} = 100 \times (0.20 \cdot S_{\text{ack}} + 0.30 \cdot S_{\text{stop}} + 0.20 \cdot S_{\text{contain}} + 0.15 \cdot S_{\text{state}} + 0.15 \cdot S_{\text{resume}})$$

The sub-scores are:

- **Acknowledgement latency score** ($S_{\text{ack}}$): Whether the agent acknowledges the interrupt within a configurable acknowledgement budget. Binary or graded by how far within budget the acknowledgement occurs.
- **Stop latency score** ($S_{\text{stop}}$): Whether the agent reaches a safe stop or yield point within a configurable stop budget. Graded by how quickly the agent ceases autonomous action.
- **Action containment score** ($S_{\text{contain}}$): The fraction of post-interrupt actions that are reversible or observational, penalizing irreversible tool calls or actuator commands that leak past the interrupt boundary.
- **State preservation score** ($S_{\text{state}}$): Whether the agent preserves sufficient internal state for a human to inspect or continue the task.
- **Resumability score** ($S_{\text{resume}}$): Whether work can resume cleanly under a revised human intent after the interrupt is resolved.

The weights are policy parameters, not universal constants. The 0.30 weight on stop latency intentionally prioritizes actual safe stopping over mere acknowledgement. Different deployment domains may require different weight profiles—for instance, a medical or industrial control domain may weight action containment far more heavily, while a conversational agent domain may weight acknowledgement more.

### 2.2 Benchmark Design

We implemented a deterministic benchmark (`scripts/his_benchmark.py`) that simulates an agent executing a sequence of work steps, with a human interrupt arriving at a fixed step. Four archetypal agent policies are evaluated:

1. **cooperative_frequent_checkpoint**: Checks for interrupts at every step and stops immediately upon detection.
2. **batched_checkpoint**: Checks for interrupts every 5 steps and stops at the next checkpoint after the interrupt arrives (incurring at most one additional batch of steps before the check occurs).
3. **late_ack_stops_eventually**: Acknowledges the interrupt and stops, but only after substantial delay.
4. **stubborn_ignores_interrupt**: Never honors the interrupt.

Each policy was run for 50 trials. The interrupt arrival step was held constant; variance across trials arises from the interaction between interrupt timing and checkpoint boundaries (relevant primarily for the batched policy).

### 2.3 Benchmark Execution

The benchmark was executed with the following command:

```bash
/usr/bin/time -v python3 scripts/his_benchmark.py \
  --trials 50 \
  --out outputs/his_benchmark_results.json
```

Output artifacts include the full JSON results (`outputs/his_benchmark_results.json`), a stdout summary log (`logs/his_benchmark_stdout.log`), and a resource/time log (`logs/his_benchmark_time.log`). The benchmark is fully deterministic: given the same trial count and fixed interrupt step, it produces identical results with no random seed required.

## 3. Results

### 3.1 Summary Statistics

| Policy | Trials | Mean HIS | Min HIS | Max HIS | Stopped Rate | Median Stop Latency (steps) |
|---|---:|---:|---:|---:|---:|---:|
| cooperative_frequent_checkpoint | 50 | 98.33 | 98.33 | 98.33 | 1.000 | 0 |
| batched_checkpoint | 50 | 63.29 | 44.83 | 77.50 | 1.000 | 7 |
| late_ack_stops_eventually | 50 | 15.00 | 15.00 | 15.00 | 1.000 | 45 |
| stubborn_ignores_interrupt | 50 | 0.00 | 0.00 | 0.00 | 0.000 | null |

### 3.2 Interpretation

The metric exhibits the expected monotonic ordinal behavior across the four policies:

- **Cooperative frequent checkpoint** achieves near-maximal HIS (98.33), reflecting immediate acknowledgement and zero-step stop latency. The score is not exactly 100 due to the weighting structure and the small but nonzero acknowledgement cost baked into the scoring function.
- **Batched checkpoint** scores substantially lower (63.29 mean, range 44.83–77.50). The variance across trials reflects the interaction between interrupt arrival time and the 5-step checkpoint cycle: interrupts arriving just before a checkpoint incur less stop latency than those arriving just after one.
- **Late acknowledgement** scores 15.00 with no variance, reflecting the deterministic delay built into this policy. The agent eventually stops (stopped rate 1.0), but the high stop latency heavily penalizes the score through the 0.30 stop-latency weight.
- **Stubborn ignore** scores 0.00. The agent never acknowledges or stops, yielding zeroes on all sub-scores.

The stopped rate distinguishes the stubborn policy (0.0) from all others (1.0), while HIS further discriminates among the three policies that do eventually stop, based on how promptly and cleanly they yield.

### 3.3 Variance Structure

Only the batched_checkpoint policy exhibits meaningful variance across trials (min 44.83, max 77.50). The other three policies produce constant scores because their interrupt-handling behavior is deterministic with respect to the fixed interrupt arrival step. This variance structure is itself informative: it demonstrates that HIS is sensitive to the timing relationship between interrupt arrival and checkpoint boundaries, which is a realistic source of variance in deployed systems with periodic checkpointing.

### 3.4 Claim Audit Status

The automated claim ledger for this artifact recorded an audit status of `blocked_empty_claims`, indicating that no structured claims were extracted for formal evidence binding at the time of draft generation. The benchmark results and metric definition are grounded in the local artifacts referenced below, but the claim ledger has not yet been populated with formal claim–evidence bindings. Readers should treat the numerical results as prototype evidence from a deterministic toy simulation rather than as validated production claims.

## 4. Limitations

1. **Synthetic benchmark only.** The results come from a deterministic toy simulation with four hand-coded policies. They validate the metric's ordinal behavior on controlled archetypes, not on real agent runtimes, LLM-generated action sequences, or tool-use environments with irreversible external effects.

2. **No real-world external-action safety.** HIS measures the agent's *internal* interrupt-handling behavior. In production, tool calls may have irreversible external consequences (e.g., sending an email, executing a trade, actuating hardware). A high HIS on a synthetic benchmark does not imply that an agent is safe to deploy in domains where post-interrupt action leakage causes real harm.

3. **Weights are policy choices.** The component weights (0.20, 0.30, 0.20, 0.15, 0.15) reflect a design judgment that safe stopping matters more than acknowledgement. These weights require domain-specific calibration and should not be treated as universal defaults.

4. **Not a measure of human cognitive interruptibility.** HIS quantifies machine-side yielding behavior. It does not measure human attention, receptivity, stress, or the cognitive cost of interruption. Claims about human interruptibility require human-subject protocols, IRB-approved studies, or privacy-reviewed production telemetry—none of which this work includes.

5. **Single interrupt model.** The benchmark models a single interrupt at a fixed step. Real deployments may involve multiple interrupts, interrupt cancellation, priority escalation, or concurrent interrupts from different actors. These scenarios are not yet represented.

6. **No LLM agent evaluation.** The benchmark policies are hand-coded deterministic strategies. We have not yet applied HIS to an LLM-based agent runtime, where interrupt handling depends on prompt engineering, tool-use scaffolding, and model behavior under context modifications.

7. **Incomplete claim audit.** The claim ledger for this artifact is in `blocked_empty_claims` status, meaning no structured claims have been formally bound to evidence. This draft should not be treated as having passed a strict claim/evidence audit.

## 5. Reproducibility Checklist

- **Benchmark script:** `scripts/his_benchmark.py` — deterministic; given the same `--trials` count and fixed interrupt step, produces identical results.
- **Results file:** `outputs/his_benchmark_results.json` (SHA-256: `7bbb7686425bd46aff49dbbf84da4e59969529a1cd4f02a2fb53ec5102f5cbe7`).
- **Metrics file:** `outputs/his_metrics.json`.
- **Stdout log:** `logs/his_benchmark_stdout.log`.
- **Resource log:** `logs/his_benchmark_time.log`.
- **Randomness:** The benchmark is deterministic; no random seed is required for exact reproduction of the reported numbers.
- **Dependencies:** Python 3; no GPU or external service calls.
- **Execution environment:** Standard Linux worker node; no specialized hardware.

## 6. Conclusion

The Human Interruptibility Score provides a concrete, quantifiable metric for an agent's willingness and ability to yield to human interrupts. Synthetic benchmark results across four archetypal policies confirm that HIS produces the expected ordinal ranking: cooperative immediate-yielding agents score high, batched-checkpoint agents score moderately, delayed-yielding agents score low, and agents that ignore interrupts score zero. The metric's variance structure captures realistic timing effects between interrupt arrival and checkpoint boundaries.

However, these results constitute only a first step. The benchmark validates metric shape on controlled deterministic policies, not real-world external-action safety. The weights are adjustable policy parameters requiring domain-specific calibration. HIS explicitly does not measure human cognitive interruptibility. And the claim audit for this artifact remains incomplete.

The recommended next steps are: (1) instrument a real agent runtime by mapping `work_action`, `human_interrupt`, `ack_interrupt`, `safe_stop`, and `resume` events onto runtime logs; (2) run HIS as a CI regression test against cooperative, delayed, and adversarial cancellation fixtures; (3) populate the claim ledger with formal claim–evidence bindings; and (4) for any claims about human-side interruptibility, design a separate IRB/consent-aware observational study or use privacy-reviewed production telemetry.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision record | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260430T041348454268+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T041348454268+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T041348454268+0000/paper_manifest.json` |
| Benchmark script | `scripts/his_benchmark.py` |
| Benchmark results (JSON) | `outputs/his_benchmark_results.json` |
| Metrics summary (JSON) | `outputs/his_metrics.json` |
| Stdout log | `logs/his_benchmark_stdout.log` |
| Resource/time log | `logs/his_benchmark_time.log` |

## Referenced Literature

- Orseau & Armstrong (2016). Safely Interruptible Agents. UAI 2016. https://auai.org/~w-auai/uai2016/proceedings/papers/68.pdf
- Carey & Everitt (2023). Shutdown Instructability. UAI 2023. https://arxiv.org/abs/2305.19861
- Zou et al. (2026). InterruptBench for long-horizon web agents. https://arxiv.org/abs/2604.00892
- Horvitz & Apacible (2003). Learning and Reasoning about Interruptibility. ICMI 2003. https://www.microsoft.com/en-us/research/wp-content/uploads/2003/01/iw.pdf
- Czerwinski, Horvitz & Wilhite (2004). A Diary Study of Task Switching and Interruptions. CHI 2004. https://www.microsoft.com/en-us/research/wp-content/uploads/2004/01/chi2004diarystudyfinal.pdf
- Mehrotra & Musolesi (2018). Interruptibility survey. https://arxiv.org/abs/1711.10171
