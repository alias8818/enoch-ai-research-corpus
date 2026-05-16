# Safety Interlock Synthesizer: Finite-State Command-Blocking Synthesis with Infeasibility Certification

**Paper ID:** `source-record-redacted`

> **AI Provenance Notice:** This draft was generated entirely by an automated research system from local run notes, evidence bundles, claim ledgers, benchmark results, and decision artifacts. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review or endorsement is implied.

---

## Abstract

We present a finite-state safety interlock synthesizer that, given a plant model with controllable and uncontrollable actions, computes a minimal set of command-blocking edges sufficient to prevent all reachable unsafe states while preserving goal reachability. The synthesizer operates over explicit-state reachability and searches candidate block sets in increasing cardinality. On a three-scenario prototype evaluation, the tool synthesizes a two-edge interlock for a robot-cell-door scenario, with post-synthesis verification confirming safety and goal liveness. For two additional scenarios (two-hand press, lift-gate presence), the synthesizer produces infeasibility certificates identifying specific uncontrollable hazard-entry transitions that prevent any command-blocking interlock from guaranteeing safety. Throughput calibration on these small models yields approximately 16,359 syntheses per wall-clock second with a peak RSS of 13,444 kB on a single core. These results are confined to small finite-state models; the candidate search is exponential in the number of controllable edges, and the framework addresses only reachability safety—not continuous control, probabilistic risk, or full temporal-logic specifications.

---

## 1. Introduction

Safety interlocks selectively block controllable commands to prevent a plant from entering hazardous states. Their design is typically manual, guided by hazard analysis and domain expertise, and verified against applicable safety standards. Automated synthesis of interlocks from plant models could reduce design errors and provide formal guarantees, but the problem is fundamentally constrained by the distinction between controllable actions (which the interlock can block) and uncontrollable actions (which it cannot).

This paper reports on a prototype Safety Interlock Synthesizer that addresses a bounded version of this problem: given a finite-state plant model with designated unsafe and goal states, compute a minimal set of controllable command-blocking edges that (1) eliminate all reachable unsafe states and (2) preserve reachability of at least one goal state. When no such interlock exists—because hazards are reachable via uncontrollable actions—the synthesizer produces an infeasibility certificate enumerating the uncontrollable hazard-entry transitions responsible.

The contribution is deliberately narrow: a working prototype with explicit-state reachability, minimal-block search, and infeasibility certification, evaluated on three small scenarios. We report both positive and negative results with equal specificity. The prototype is not intended as a production safety tool and has not been validated against any safety standard.

---

## 2. Method

### 2.1 Plant Model

A plant is specified as a tuple $(S, A, T, s_0, U, G, A_c)$ where:

- $S$ is a finite set of states, represented as dictionaries of variable–value pairs.
- $A$ is a finite set of actions.
- $T \subseteq S \times A \times S$ is the transition relation.
- $s_0 \in S$ is the initial state.
- $U \subseteq S$ is the set of unsafe (hazard) states.
- $G \subseteq S$ is the set of goal (productive) states.
- $A_c \subseteq A$ is the set of controllable actions (those the interlock may block).

Uncontrollable actions ($A \setminus A_c$) model environment events that the interlock cannot prevent.

### 2.2 Synthesis Algorithm

The algorithm proceeds as follows:

1. **Baseline reachability.** Compute the set of states reachable from $s_0$ under the full transition relation $T$. If no unsafe state is reachable, no interlock is needed.

2. **Candidate enumeration.** Identify all controllable edges $(s, a, s') \in T$ such that $s' \in U$—that is, controllable transitions whose immediate successor is unsafe. These form the candidate blocking set $C$.

3. **Minimal-block search.** Search subsets of $C$ in increasing cardinality $k = 1, 2, \ldots, |C|$. For each candidate block set $B$:
   - Remove all edges in $B$ from $T$ to obtain the restricted transition relation $T_B$.
   - Compute reachability under $T_B$.
   - If no unsafe state is reachable and at least one goal state is reachable, accept $B$ as a valid interlock.

4. **Infeasibility certification.** If no block set (up to and including $C$ itself) yields a safe plant, block every controllable candidate and report the residual unsafe paths. Specifically, enumerate uncontrollable edges $(s, a, s')$ where $s' \in U$ and $s$ is reachable even after all controllable candidates are blocked. These uncontrollable hazard entries form the infeasibility certificate.

The search is complete: if a valid interlock exists within the command-blocking model, the algorithm will find one of minimal cardinality. If none exists, the certificate provides a concrete explanation for why command-blocking alone is insufficient.

### 2.3 Implementation

The synthesizer is implemented in dependency-free Python 3 (`src/interlock_synth.py`). State spaces are represented as frozensets of variable–value pairs; reachability uses standard breadth-first traversal. The implementation includes a benchmark harness (`src/bench_synth.py`) and a regression test suite (`tests/test_interlock_synth.py`) covering three categories: detection of reachable hazards, successful synthesis with post-hoc verification, and infeasibility certification with correct uncontrollable hazard-entry enumeration.

### 2.4 Evaluation Scenarios

Three scenarios were evaluated:

- **robot_cell_door:** A robot cell with a door (open/closed) and a robot (idle/moving). The hazard is the state where the door is open and the robot is moving. Both `open_door` and `start_robot` are controllable.
- **two_hand_press:** A two-hand press with left/right cylinders (up/down) and a press mechanism (downstroke/idle). The hazard is any state where the press is in downstroke and at least one cylinder is up. The actions `left_up` and `right_up` are uncontrollable.
- **lift_gate_presence:** A lift with a gate (latched/unlatched), a lift carriage (moving/stopped), and an operator (clear/inside). The hazard is the state where the lift is moving and the operator is inside. The action `enter` is uncontrollable.

All three scenarios have state spaces on the order of 4–8 states. These are toy models chosen to exercise the synthesizer's positive and negative paths, not industrial-scale case studies.

### 2.5 Benchmark Protocol

Throughput calibration was performed with `SYNTH_BENCH_ITERATIONS=5000`, running each of the three scenarios 5,000 times (15,000 total syntheses). Host telemetry (memory availability, swap status, early OOM daemon) was recorded before and after the benchmark run. The benchmark was executed on a single core with swap intentionally disabled per controller constraint.

---

## 3. Results

### 3.1 Positive Synthesis: robot_cell_door

The synthesizer found a valid interlock with minimal block count 2:

| Blocked Action | State at Block Point |
|---|---|
| `open_door` | `{door: closed, robot: moving}` |
| `start_robot` | `{door: open, robot: idle}` |

Post-synthesis verification confirmed:

- **post_safe:** True (no reachable unsafe state under the restricted transition relation)
- **post_goal_reachable:** True (at least one goal state remains reachable)
- **post_reachable_states:** 3

The interlock enforces a mutual-exclusion invariant: the door cannot be opened while the robot is moving, and the robot cannot be started while the door is open. This is consistent with standard robot-cell safety practice, though we emphasize that this result is a toy-model verification only and carries no industrial safety certification.

### 3.2 Infeasible Synthesis: two_hand_press

After blocking all controllable hazard-entry candidates, residual unsafe states persist. The infeasibility certificate identifies two uncontrollable hazard entries:

| Action | From State | To State |
|---|---|---|
| `left_up` | `{left: down, press: downstroke, right: down}` | `{left: up, press: downstroke, right: down}` |
| `right_up` | `{left: down, press: downstroke, right: down}` | `{left: down, press: downstroke, right: up}` |

Because `left_up` and `right_up` are uncontrollable, no command-blocking interlock can prevent an operator from raising a cylinder during a downstroke. This is a correct negative result: safety in this scenario requires either making these actions controllable (e.g., via solenoid-locked palm buttons) or employing a different interlock mechanism (e.g., a mechanical tie-down or presence-sensing device). The synthesizer does not prescribe such alternatives; it only certifies that command-blocking alone is insufficient.

### 3.3 Infeasible Synthesis: lift_gate_presence

The synthesizer certifies infeasibility with one uncontrollable hazard entry:

| Action | From State | To State |
|---|---|---|
| `enter` | `{gate: latched, lift: moving, operator: clear}` | `{gate: latched, lift: moving, operator: inside}` |

The `enter` action is uncontrollable: the interlock cannot prevent an operator from entering the lift zone while the lift is moving and the gate is latched. Safety would require either controlling the `enter` action (e.g., via a locked gate interlocked to lift motion) or redesigning the plant model. Again, the synthesizer certifies the infeasibility but does not prescribe a remedy.

### 3.4 Throughput and Resource Usage

Benchmark configuration: 5,000 iterations × 3 scenarios = 15,000 total syntheses.

| Metric | Value |
|---|---|
| Wall-clock time | 0.916925 s |
| Throughput | 16,359.03 syntheses/s |
| Max RSS | 13,444 kB |
| MemAvailable (before) | 122,404,248 kB |
| MemAvailable (after) | 122,406,148 kB |
| Swap total | 0 kB (intentionally disabled) |
| CPU utilization | ~1.0 core-equivalent |
| Host | Linux 6.17.0-1014-nvidia-aarch64, glibc 2.39 |
| Early OOM daemon | Active |

Memory usage is negligible relative to available RAM (approximately 116 GB). The slight increase in MemAvailable after the benchmark likely reflects kernel page reclamation during or after the run. No swap activity occurred. These throughput figures apply only to the small models tested; performance on larger state spaces is uncharacterized and should not be extrapolated.

### 3.5 Test Suite

All 4 unit tests passed, covering:

- Detection of reachable hazards in the baseline plant.
- Successful synthesis with post-hoc safety and liveness verification.
- Infeasibility certification with correct uncontrollable hazard-entry enumeration.

Test execution log is archived at `artifacts/logs/unit_final.log`.

---

## 4. Limitations

1. **Finite-state reachability only.** The synthesizer addresses discrete-state reachability safety. It does not handle continuous dynamics, timed automata, probabilistic risk, or full temporal-logic (CTL/LTL) specifications. A plant that is safe under reachability may still be unsafe under finer-grained temporal requirements.

2. **Exponential candidate search.** The minimal-block search enumerates subsets of controllable candidates in increasing cardinality. In the worst case, this is exponential in the number of candidate edges. For larger systems, symbolic methods (BDDs, SAT/SMT encodings) or compositional decomposition would be necessary. The current implementation has no pruning beyond cardinality ordering.

3. **Small model scope.** All three evaluation scenarios have state spaces on the order of 4–8 states. Performance and correctness on industrially relevant models (hundreds to thousands of states, dozens of variables) are unvalidated. The throughput figures reported here should not be extrapolated to larger models.

4. **No continuous-control or sensor validation.** The output is a policy over model states and actions. Production deployment requires validated plant models, sensor trust assumptions, fail-safe hardware semantics, and review against applicable safety standards (e.g., IEC 62443, ISO 13849, IEC 61508). The prototype has undergone no such review.

5. **Infeasibility certificates are sufficient but not minimal.** The certificate lists all uncontrollable hazard entries reachable after maximal controllable blocking. A minimal certificate (the smallest subset of uncontrollable actions whose controllability would enable synthesis) is not computed. Computing minimal certificates may itself be computationally hard.

6. **No compositional or modular synthesis.** The synthesizer operates on monolithic plant models. Compositional methods for interlocking modular subsystems—common in industrial practice—are not addressed.

7. **Artifact scope.** The Notion page body was not available in local project artifacts; the research scope is derived from the controller prompt and project title alone. No external domain literature was consulted during the automated research run.

8. **No comparison to existing methods.** The prototype was not compared against supervisory control theory tools, discrete-event systems synthesizers, or model checkers. Relative performance and completeness claims are therefore absent.

---

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Source code available | `src/interlock_synth.py`, `src/bench_synth.py` |
| Test suite available | `tests/test_interlock_synth.py` (4 tests, all passing) |
| Synthesis output archived | `artifacts/metrics/synthesis_results.json` |
| Benchmark metrics archived | `artifacts/metrics/bench_metrics.json` |
| Host telemetry logged | `artifacts/logs/host_telemetry.log` |
| Compilation/syntax check logged | `artifacts/logs/py_compile.log` |
| Unit test output logged | `artifacts/logs/unit_final.log` |
| Synthesis run output logged | `artifacts/logs/synthesis_final.log` |
| Benchmark run output logged | `artifacts/logs/bench_5000.log` |
| Decision JSON with evidence | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Dependency-free implementation | Yes (Python 3 standard library only) |
| Exact commands for reproduction | Documented in run notes |
| Hardware specification | Linux 6.17.0-1014-nvidia-aarch64, ~116 GB RAM, swap disabled |
| Randomness control | Algorithm is deterministic; no random seeds required |
| Environment variables | `SYNTH_BENCH_ITERATIONS=5000` for benchmark |
| Claim ledger | `papers/.../claim_ledger.json` (empty at time of generation) |
| Evidence bundle | `papers/.../evidence_bundle.json` |

---

## 6. Conclusion

A finite-state command-blocking safety interlock synthesizer was implemented and evaluated on three small scenarios. The prototype demonstrates that minimal interlocks can be synthesized and locally verified for models where all hazard-entry actions are controllable (robot_cell_door: 2-block interlock, post-safe, post-goal-reachable). Equally, the prototype demonstrates that when hazard-entry actions are uncontrollable, the same framework produces concrete infeasibility certificates (two_hand_press, lift_gate_presence), correctly identifying the environmental transitions that prevent any command-blocking interlock from guaranteeing safety.

These results are locally viable but bounded. The synthesizer addresses only discrete reachability safety over small explicit-state models. Scaling to industrial systems would require symbolic representations, compositional methods, and integration with validated hazard analysis and safety standards. The infeasibility certificates, while useful for diagnosing why a command-blocking interlock fails, do not prescribe alternative safety mechanisms; that determination requires engineering judgment beyond the scope of this artifact.

The negative results are as informative as the positive one: they confirm that the synthesizer correctly refuses to claim safety when the plant model admits uncontrollable paths to hazard states, and it provides specific evidence for that refusal. This behavior—producing concrete infeasibility certificates rather than silent failure or false guarantees—is a desirable property for any safety-critical synthesis tool, even at prototype scale.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Synthesizer source | `src/interlock_synth.py` |
| Benchmark harness | `src/bench_synth.py` |
| Test suite | `tests/test_interlock_synth.py` |
| Synthesis results | `artifacts/metrics/synthesis_results.json` |
| Benchmark metrics | `artifacts/metrics/bench_metrics.json` |
| Host telemetry log | `artifacts/logs/host_telemetry.log` |
| Syntax check log | `artifacts/logs/py_compile.log` |
| Unit test log | `artifacts/logs/unit_final.log` |
| Synthesis run log | `artifacts/logs/synthesis_final.log` |
| Benchmark run log | `artifacts/logs/bench_5000.log` |
| Run notes | `run_notes.md` |
| Decision JSON | `.omx/project_decision.json` |
| Project session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260502T164718490851+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T164718490851+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T164718490851+0000/paper_manifest.json` |
