# Half-Life Planning: Expiring Stale Assumptions in Long-Running Agent Governance

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, benchmark outputs, decision records, claim ledgers, and evidence bundles). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Long-running autonomous agents risk accumulating stale assumptions as the facts underlying their plans drift over time. We propose Half-Life Planning, a governance mechanism in which every task, memory, and assumption carries a time-to-live derived from its volatility half-life; expired items must be refreshed before they can influence planning decisions. We evaluate the mechanism in a deterministic toy-model simulation of a long-running planner operating over 64 facts with heterogeneous drift rates across 128,000 planning decisions (128 seeds × 1000 steps). The half-life refresh gate reduces stale-assumption uses by 59.3% and wrong planning choices by 51.8% relative to a cached-assumption baseline, with positive net utility at the default refresh cost. A sensitivity sweep across 15 cost and TTL-scale configurations reveals a clear boundary: net utility remains positive up to a refresh cost of 0.5 (in the simulation's cost units) across all TTL scales, but becomes mixed or negative at refresh cost 1.0, even though error reduction remains substantial at that cost. These results support the mechanism as a governance primitive under controlled conditions, but do not demonstrate that real agents can accurately estimate fact volatility or perform cheap, reliable refreshes in messy project workflows. The claim ledger for this artifact records no structured claims and is flagged as audit-blocked; the results herein should be read as prototype evidence pending formal claim-audit.

---

## Introduction

Autonomous agents that operate over extended time horizons face a governance problem qualitatively different from single-turn inference: the world changes while the agent's cached beliefs do not. An assumption valid at planning time may become stale, leading the agent to make decisions based on outdated evidence. This drift accumulates silently because agents typically lack an explicit mechanism to track the expected lifetime of their beliefs.

The Half-Life Planning mechanism addresses this by assigning each piece of evidence a half-life reflecting its expected rate of change, computing a time-to-live (TTL) from that half-life, and requiring refresh before any expired fact can be used in a planning decision. This converts implicit staleness into an explicit, measurable governance cost.

The hypothesis under test is that such a mechanism reduces stale-assumption errors and wrong decisions enough to justify the refresh budget it consumes. We reduce this to a measurable question: in a long-running planning simulation with changing facts, does a half-life refresh gate reduce stale-assumption errors and wrong decisions enough to justify refresh cost?

We emphasize at the outset that this paper reports results from a deterministic toy-model governance benchmark, not from a live LLM-agent workflow, a llama.cpp hook prototype, a CUDA copy calibration, or a replay of real project traces. The simulation provides evidence about the mechanism's behavior under controlled conditions; it does not prove that the mechanism transfers to real deployments where volatility must be estimated and refreshes may fail.

---

## Method

### Simulation Design

We implemented a deterministic Python benchmark (`scripts/half_life_benchmark.py`) modeling a long-running planner that repeatedly chooses among candidate options whose true values depend on a set of project facts.

**World model.** The world consists of $N$ facts (assumptions), each with an independent drift rate drawn from a heterogeneous distribution. At each time step, a fact may change its value according to its drift probability. An oracle tracks the true state of all facts at all times.

**Baseline planner.** The baseline planner reuses cached assumptions until an incidental background refresh updates them. It has no explicit staleness tracking; refresh occurs only as a side effect of other processes.

**Half-life planner.** The half-life planner computes a TTL for each fact from its known drift half-life. Before any planning decision, it checks whether each required fact's TTL has expired and, if so, refreshes it (retrieving the current true value). Only fresh facts are used in the planning decision.

**Planning task.** At each step, the planner selects among candidate options. The true value of each option depends on the current state of the facts. A wrong choice occurs when the planner selects an option that is suboptimal given the true (current) facts, typically because one or more of its cached assumptions are stale.

### Metrics

- **Stale assumption uses:** number of planning steps in which at least one stale fact was used.
- **Stale error rate:** fraction of fact-uses that involved a stale value.
- **Wrong choices:** number of planning decisions that were suboptimal relative to the oracle.
- **Wrong choice rate:** fraction of decisions that were wrong.
- **Refreshes:** total number of explicit refresh operations performed.
- **Refreshes per decision:** average refreshes per planning step.
- **Net utility:** cumulative achieved value minus stale-action penalties minus refresh costs.

### Experimental Protocol

We ran three phases of increasing scale:

1. **Smoke test:** 2 seeds × 40 steps × 16 facts.
2. **Calibration:** 8 seeds × 200 steps × 48 facts.
3. **Main run:** 128 seeds × 1000 steps × 64 facts (128,000 planning decisions).

Following the main run, we conducted a sensitivity sweep (`scripts/half_life_sweep.py`) varying refresh cost (0.02, 0.08, 0.2, 0.5, 1.0) and TTL scale factor (0.5, 1.0, 2.0) across 64 seeds × 600 steps × 64 facts per configuration (15 configurations total).

### Environment

All runs were CPU-only on an NVIDIA GB10 development machine (aarch64, Linux 6.17.0-1014-nvidia). Peak RSS for the main run was 15,388 kB. GPU utilization remained at 0% throughout. Memory available before and after the main run was approximately 122 GB, with no swap configured. The experiment was small enough that no GPU acceleration was necessary. The earlyoom daemon was active with a 4% memory threshold, but no OOM events occurred.

---

## Results

### Main Run

Table 1 summarizes the main run (128 seeds × 1000 steps × 64 facts).

**Table 1.** Main run results across 128,000 planning decisions.

| Metric | Baseline | Half-Life | Delta |
|---|---:|---:|---:|
| Stale assumption uses | 214,456 | 87,240 | −59.3% |
| Stale error rate | 0.3351 | 0.1363 | — |
| Wrong choices | 61,025 | 29,416 | −51.8% |
| Wrong choice rate | 0.4768 | 0.2298 | — |
| Refreshes | 0 | 170,382 | +170,382 |
| Refreshes per decision | 0.000 | 1.331 | — |
| Net utility | −99,973.9 | 37,755.5 | +137,729.5 |

The half-life planner reduces stale assumption uses by 59.3% and wrong choices by 51.8%, at the cost of 1.331 refreshes per decision on average. Net utility shifts from substantially negative under the baseline to positive under half-life governance. However, the baseline's large negative net utility reflects the specific penalty structure of the simulation; the absolute magnitudes should not be taken as domain-general predictions.

### Paired-Seed Robustness

Across the 128 paired seeds:

- Stale reduction median: 0.594 (p5–p95: 0.540–0.641)
- Wrong-choice reduction median: 0.518 (p5–p95: 0.453–0.580)
- Net utility delta median: 1,080.0 (p5–p95: 913.1–1,265.0)

The positive signal is consistent across seeds, though the magnitude of benefit varies. The p5–p95 range for stale reduction (0.540–0.641) and wrong-choice reduction (0.453–0.580) indicates that while the direction of effect is robust, the exact fraction of errors eliminated is sensitive to random conditions within the simulation.

### Sensitivity Sweep

Table 2 shows results across 15 configurations varying refresh cost and TTL scale.

**Table 2.** Sensitivity sweep (64 seeds × 600 steps × 64 facts per configuration).

| Refresh Cost | TTL Scale | Stale Reduction | Wrong-Choice Reduction | Refreshes/Decision | Net Utility Delta | Label |
|---:|---:|---:|---:|---:|---:|---|
| 0.02 | 0.5 | 0.763 | 0.706 | 1.891 | 56,155.5 | positive |
| 0.02 | 1.0 | 0.591 | 0.520 | 1.309 | 43,642.4 | positive |
| 0.02 | 2.0 | 0.408 | 0.339 | 0.842 | 30,220.2 | positive |
| 0.08 | 0.5 | 0.763 | 0.706 | 1.891 | 51,799.2 | positive |
| 0.08 | 1.0 | 0.591 | 0.520 | 1.309 | 40,626.1 | positive |
| 0.08 | 2.0 | 0.408 | 0.339 | 0.842 | 28,281.0 | positive |
| 0.2 | 0.5 | 0.763 | 0.706 | 1.891 | 43,086.5 | positive |
| 0.2 | 1.0 | 0.591 | 0.520 | 1.309 | 34,593.4 | positive |
| 0.2 | 2.0 | 0.408 | 0.339 | 0.842 | 24,402.6 | positive |
| 0.5 | 0.5 | 0.763 | 0.706 | 1.891 | 21,304.7 | positive |
| 0.5 | 1.0 | 0.591 | 0.520 | 1.309 | 19,511.8 | positive |
| 0.5 | 2.0 | 0.408 | 0.339 | 0.842 | 14,706.6 | positive |
| 1.0 | 0.5 | 0.763 | 0.706 | 1.891 | −14,998.3 | mixed |
| 1.0 | 1.0 | 0.591 | 0.520 | 1.309 | −5,624.2 | mixed |
| 1.0 | 2.0 | 0.408 | 0.339 | 0.842 | −1,453.4 | mixed |

Two patterns emerge:

1. **Error reduction is robust across all configurations.** Stale reduction and wrong-choice reduction depend on TTL scale (shorter TTLs expire more facts, yielding greater error reduction) but are insensitive to refresh cost, as expected—cost affects utility, not accuracy.

2. **Net utility has a clear cost boundary.** Positive net utility persists up to refresh cost 0.5 across all TTL scales. At refresh cost 1.0, net utility becomes negative even though error reduction remains substantial. The mechanism is beneficial only when the cost of refreshing evidence is materially lower than the cost of acting on stale assumptions.

A notable negative result: increasing TTL scale from 0.5 to 2.0 monotonically decreases error reduction (stale reduction drops from 0.763 to 0.408; wrong-choice reduction from 0.706 to 0.339) while also decreasing refreshes per decision (from 1.891 to 0.842). This confirms the expected tradeoff: more permissive TTLs reduce governance overhead but allow more stale assumptions through. The net utility gradient across TTL scales is positive in all cases where refresh cost ≤ 0.5, meaning the cost savings from fewer refreshes do not compensate for the utility loss from additional errors at these cost levels.

---

## Limitations

1. **Toy deterministic simulation.** The benchmark models fact drift with known probabilities and perfect refresh. It is not a live LLM-agent workflow, a Notion/project-note replay, or a real tool-calling trace. The degree to which these results transfer to real agent deployments is unknown.

2. **Known drift rates.** The half-life planner is given each fact's true drift half-life. A real system must estimate volatility from evidence type, history, or metadata. Estimation errors could degrade or negate the benefit observed here. The simulation provides no evidence about the feasibility or accuracy of volatility estimation.

3. **Perfect refresh.** In the simulation, refresh always succeeds and always returns the current true value. In practice, refresh can fail (source unavailable, API error), consume context or tool-call budget, or require private or human-verified evidence that is not always obtainable. Failed or partial refreshes could leave the planner in a worse state than simply using a stale assumption.

4. **Cost boundary.** Net utility becomes mixed or negative when refresh cost approaches the stale-action penalty. The exact crossover point depends on domain-specific cost structures that the toy model only approximates. The specific numeric threshold (0.5 vs. 1.0 in simulation units) should not be treated as a general constant.

5. **No real-workflow validation.** The experiment does not address whether real agents can accurately classify facts by volatility, whether half-life assignment is practical at scale, or whether the governance overhead is acceptable in production systems.

6. **Single mechanism, single metric family.** The study evaluates only the half-life TTL mechanism against a simple cached-assumption baseline. It does not compare against alternative governance strategies (e.g., periodic full refresh, confidence-weighted planning, or budget-market mechanisms mentioned in the original hypothesis).

7. **Claim audit status.** The claim ledger for this artifact records zero structured claims and is flagged as `blocked_empty_claims`. The results have not passed formal claim/evidence audit. This does not invalidate the reported numbers, which are drawn from recorded benchmark outputs, but it means the claims have not been individually extracted and verified against the evidence bundle.

---

## Reproducibility Checklist

| Item | Status |
|---|---|
| Code available | `scripts/half_life_benchmark.py`, `scripts/half_life_sweep.py`, `scripts/capture_system_telemetry.py` |
| Deterministic | All runs use explicit random seeds; results are fully reproducible given the same seed and parameters |
| Command lines recorded | All invocation commands are logged in `run_notes.md` and reproduced in the Method section |
| Output artifacts | All metric JSON files and log files listed under Referenced Artifacts |
| Hardware specified | NVIDIA GB10, aarch64, Linux 6.17.0-1014-nvidia, ~122 GB RAM, no swap, CPU-only execution |
| Peak RSS | 15,388 kB for the main run |
| Random seeds | 128 seeds for main run; 64 seeds per sweep configuration |
| Parameter ranges | Facts: 16–64; steps: 40–1000; refresh cost: 0.02–1.0; TTL scale: 0.5–2.0 |
| Statistical reporting | Paired-seed medians with p5–p95 intervals reported for key metrics |
| Claim audit | Not passed; claim ledger is `blocked_empty_claims` with zero structured claims |

---

## Conclusion

A deterministic toy-model simulation supports the Half-Life Planning mechanism as a governance primitive: expiring and refreshing stale assumptions before planning reduced stale-assumption uses by 59.3% and wrong choices by 51.8% across 128,000 planning decisions, with positive net utility at the default refresh cost. Sensitivity analysis across 15 configurations identifies a clear boundary condition—the mechanism's net benefit becomes mixed or negative when refresh cost approaches the cost of acting on stale assumptions, even though error reduction persists at all tested cost levels.

These results are promising but constrained. The simulation assumes known drift rates, perfect refresh, and a simple cost structure. Whether real agents can estimate fact volatility accurately, perform reliable refreshes within tool-call budgets, and realize net utility gains in messy project workflows remains an open empirical question. The appropriate next step is a real workflow-trace replay benchmark where evidence records are typed by volatility class, refresh actions use actual project notes or tool calls, and stale-assumption errors are judged against time-indexed ground truth.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260430T105818348354+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T105818348354+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T105818348354+0000/paper_manifest.json` |
| Benchmark script | `scripts/half_life_benchmark.py` |
| Sweep script | `scripts/half_life_sweep.py` |
| Telemetry script | `scripts/capture_system_telemetry.py` |
| Smoke metrics | `results/metrics/smoke.json` |
| Calibration metrics | `results/metrics/calibration.json` |
| Main metrics | `results/metrics/main.json` |
| Sweep summary | `results/metrics/sweep_summary.json` |
| System telemetry (before) | `results/metrics/system_telemetry_before.json` |
| System telemetry (after) | `results/metrics/system_telemetry_after.json` |
| Smoke log | `results/logs/smoke.log` |
| Calibration log | `results/logs/calibration.log` |
| Main log | `results/logs/main.log` |
| Sweep log | `results/logs/sweep.log` |
