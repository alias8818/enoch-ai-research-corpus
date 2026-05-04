# Agent Budget Parliament: Adaptive Budget Allocation for Heterogeneous Agent Workflows

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, and metrics). The operator who released this artifact claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this document as an unreviewed AI-generated research artifact and evaluate its claims with appropriate skepticism.

---

## Abstract

We investigate Agent Budget Parliament, a controller mechanism in which agent roles submit budget requests and a parliament allocator assigns scarce inference and tool budget based on estimated marginal utility, uncertainty, role caps, and coordination overhead. In a dependency-free synthetic simulator evaluating 5,000 paired tasks across five task types and five agent roles, the parliament policy achieved a mean quality of 0.969, outperforming uniform allocation (+0.0053, 95% bootstrap CI [0.0052, 0.0055], win rate 88.9%) and single-best allocation (+0.088, win rate 99.9%) under matched total budget. However, parliament remained below a greedy oracle with access to true marginal utilities (−0.0025, 95% CI [−0.0025, −0.0024], win rate 0.0%). A budget sweep at budgets 6, 12, and 24 showed that parliament's advantage over uniform allocation diminishes as budget increases (+0.025 at budget 6, +0.001 at budget 24), consistent with saturation effects. These results support the viability of adaptive budget governance as a controller pattern but do not establish that multi-agent systems outperform a strong single-agent system under matched reasoning-token budgets. All results derive from a synthetic task model with hand-specified quality functions; validation on real LLM-agent traces remains necessary.

## 1. Introduction

Budget allocation across heterogeneous agents in a multi-agent system is a constrained optimization problem: given a fixed total budget of inference tokens or tool calls, how should a controller distribute resources among agent roles with differing skill profiles, diminishing returns, and coordination costs?

Recent work has begun to address this problem from several angles. BAMAS frames LLM allocation as constrained optimization and reports cost reductions up to 86% on evaluated tasks while maintaining comparable performance. However, Tran & Kiela (2026) report that single-agent systems can match or outperform multi-agent systems on multi-hop reasoning when reasoning-token budgets are held constant, raising the question of whether multi-agent budget allocation is beneficial under fair comparisons. CascadeDebate demonstrates that selective deliberation—activating lightweight ensembles only near uncertainty boundaries—outperforms fixed debate policies, suggesting that adaptive rather than always-on coordination is more promising. Budgeted multi-agent synergy theory highlights finite context, lossy communication, and shared failures as constraints that determine when multi-agent systems help or collapse.

We interpret "Agent Budget Parliament" as a controller in which agent roles submit budget requests or bids, and a parliament allocator assigns scarce inference and tool budget based on estimated marginal utility, uncertainty, role caps, and coordination overhead. This paper evaluates the parliament mechanism against three baselines—uniform allocation, single-best allocation, and a greedy oracle—in a synthetic simulation environment, and characterizes the conditions under which adaptive allocation provides the most benefit.

We emphasize at the outset that this study operates entirely within a synthetic task model. The results constitute a positive feasibility signal for adaptive budget governance, not evidence of real-world LLM-agent performance.

## 2. Method

### 2.1 Synthetic Task Model

We constructed a dependency-free synthetic simulator (`src/budget_parliament.py`) modeling five task types (literature, prototype, debug, risk_review, mixed) and five agent roles (researcher, builder, critic, verifier, synthesizer). The model incorporates the following explicit mechanisms:

- **Diminishing returns:** Each agent role exhibits decreasing marginal quality gains as allocated budget increases, with role-specific skill curves per task type.
- **Task complexity and ambiguity:** Tasks are parameterized by complexity and ambiguity, which modulate the baseline quality achievable by each role.
- **Shared-failure correlation:** Agent roles may share correlated failure modes, reducing the effective diversity of multi-agent ensembles.
- **Coordination overhead:** Active agents incur a coordination cost that reduces net quality as the number of participating agents grows.

Quality for a given allocation is computed as a function of per-agent contributions (themselves functions of allocated budget, skill curves, and task parameters), adjusted for shared-failure correlation and coordination overhead. These quality functions are hand-specified; their functional forms and parameter values are design choices of the simulator, not empirically derived from real agent traces.

### 2.2 Allocation Policies

Four policies are compared, all operating under the same total budget constraint:

1. **Uniform:** Equal budget distributed to all agents.
2. **Single-best:** All budget allocated to the agent with the highest prior expected quality for the task type.
3. **Parliament:** Agents submit noisy bids based on estimated marginal utility. The allocator incorporates an uncertainty bonus for under-explored roles, viability grants to ensure minimum participation, per-role caps, and a fragmentation tax penalizing excessive agent activation.
4. **Greedy oracle:** Allocates based on true marginal utility. This is an upper-bound baseline not implementable in production, as it requires knowledge of actual quality functions.

### 2.3 Experimental Protocol

All experiments use paired task instances: the same task is presented to all four policies, ensuring that differences reflect allocation strategy rather than task sampling variance.

**Main run:** 5,000 paired tasks, total budget 12, seed 340367.

**Budget sweep:** 3,000 paired tasks each at total budgets 6, 12, and 24, seed 340367.

**Smoke test:** 20 paired tasks, budget 12, seed 34, to verify pipeline correctness.

All runs were executed via `run_research.py`. Code was verified with `py_compile` and the main run was re-executed to confirm reproducibility of output.

### 2.4 Metrics

The primary metric is mean task quality across all paired instances. We report:

- Mean quality per policy.
- Mean quality delta between parliament and each baseline.
- 95% bootstrap confidence intervals for deltas (computed from paired differences).
- Win rate: the fraction of task instances where parliament achieves strictly higher quality than the comparison policy.

## 3. Results

### 3.1 Main Run

Table 1 reports mean quality and mean number of active agents across 5,000 paired tasks at budget 12.

**Table 1.** Main run results (5,000 tasks, budget 12, seed 340367).

| Policy | Mean quality | Mean active agents |
|---|---:|---:|
| Greedy oracle | 0.9715 | 4.33 |
| Parliament | 0.9691 | 4.96 |
| Uniform | 0.9638 | 5.00 |
| Single-best | 0.8807 | 1.00 |

Parliament outperforms uniform and single-best allocation but remains below the greedy oracle. Parliament activates slightly fewer agents on average than uniform (4.96 vs. 5.00), reflecting its fragmentation tax and viability grant logic. The greedy oracle activates fewer agents still (4.33), suggesting that optimal allocation under this model concentrates budget more than either heuristic policy.

### 3.2 Paired Comparisons

Table 2 reports paired quality deltas between parliament and each baseline.

**Table 2.** Paired quality deltas, parliament vs. baselines (5,000 tasks, budget 12).

| Comparison | Mean delta | 95% bootstrap CI | Win rate |
|---|---:|---|---:|
| Parliament − Uniform | +0.00533 | [0.00517, 0.00550] | 88.92% |
| Parliament − Single-best | +0.08843 | [0.08672, 0.09018] | 99.94% |
| Parliament − Greedy oracle | −0.00247 | [−0.00255, −0.00239] | 0.00% |

Parliament beats uniform allocation on 88.9% of task instances and single-best on 99.9%. However, parliament never beats the greedy oracle on any task instance (win rate 0.0%), and the confidence interval for the oracle gap excludes zero, confirming a consistent and statistically reliable shortfall. The magnitude of this gap is small in absolute terms (−0.0025) but indicates that the parliament's heuristic bidding and allocation adjustments do not fully recover the information available to an oracle.

### 3.3 Budget Sweep

Table 3 reports mean quality across budgets 6, 12, and 24, and the parliament-uniform delta at each budget level.

**Table 3.** Budget sweep results (3,000 tasks per budget, seed 340367).

| Budget | Parliament | Uniform | Single-best | Oracle | Parliament − Uniform |
|---|---:|---:|---:|---:|---:|
| 6 | 0.9026 | 0.8777 | 0.8088 | 0.9102 | +0.0249 |
| 12 | 0.9692 | 0.9638 | 0.8807 | 0.9716 | +0.0053 |
| 24 | 0.9922 | 0.9912 | 0.9259 | 0.9926 | +0.0010 |

Parliament's advantage over uniform allocation is largest at budget 6 (+0.025) and shrinks monotonically as budget increases, reaching +0.001 at budget 24. This is consistent with a saturation effect: when budget is abundant, even uniform allocation can fund all useful roles, and adaptive allocation provides diminishing marginal value. At budget 6, where resources are scarce, the parliament's ability to redirect budget from saturated roles to under-funded ones yields a more substantial improvement.

Single-best allocation performs poorly across all budgets, confirming that concentrating all resources on a single role is suboptimal in heterogeneous task environments modeled by this simulator.

### 3.4 Resource Usage

The smoke test consumed 15,104 kB maximum RSS. The main run consumed 27,728 kB maximum RSS. No swap was configured or needed. Available memory remained approximately 122.6 GB throughout, indicating no memory pressure. These figures confirm that the synthetic simulator is computationally lightweight; they carry no implications for the resource requirements of a production system operating on real LLM-agent workflows.

## 4. Limitations

1. **Synthetic task model.** All results derive from hand-modeled quality functions, skill curves, coordination overhead, and shared-failure correlations. Real LLM-agent tasks may exhibit different functional forms, different diminishing-returns profiles, and different correlation structures. The current results constitute a positive feasibility result under one set of modeling assumptions, not scientific closure on real LLM-agent performance.

2. **No real LLM-agent traces.** The simulator does not invoke any language model. Bids are generated from noisy estimates of modeled marginal utilities, not from actual agent reasoning about real tasks. Validation on real workflow traces—logging per-agent bids, allocated token/tool budget, actual spend, latency, and outcome quality—is necessary before any production or scientific claim.

3. **Idea framing from inference.** The original project specification (Notion page) was not readable from the session. The interpretation of "Agent Budget Parliament" was inferred from the project title and prompt. A different framing might yield different design choices and results.

4. **No claim on multi-agent vs. single-agent.** Consistent with findings in the literature, we do not claim that multi-agent systems outperform single-agent systems under matched reasoning-token budgets. The parliament mechanism governs budget allocation *among* agents; it does not establish that using multiple agents is superior to using a single strong agent with the same total budget.

5. **Oracle gap.** Parliament never beats the greedy oracle, indicating that the bidding mechanism, uncertainty bonus, and heuristic adjustments leave a consistent performance gap relative to perfect information. The magnitude of this gap (−0.0025 at budget 12) is small but statistically reliable, and its practical significance depends on the cost of imperfect allocation in real workflows.

6. **Narrow task and role taxonomy.** Five task types and five agent roles may not capture the diversity of real workflows. Extending the taxonomy could change the relative performance of allocation policies.

7. **Claim ledger audit status.** The structured claim ledger for this artifact was flagged as `blocked_empty_claims` at generation time, meaning no formal claims were extracted and audited against evidence files. This draft should not be treated as having passed a strict claim/evidence audit.

## 5. Reproducibility Checklist

- **Code availability:** `src/budget_parliament.py` (simulator and policies) and `run_research.py` (experiment CLI) are present in the project directory.
- **Dependencies:** None. The implementation is dependency-free (standard Python 3 only).
- **Random seeds:** Main run seed 340367; smoke test seed 34. Budget sweep uses seed 340367.
- **Exact commands:** All commands are recorded in the run notes and reproduced in Section 2.3.
- **Verification:** Code was compiled with `py_compile` and the main run was re-executed to confirm output consistency.
- **Metrics artifacts:** Summary JSON files (`metrics/smoke_summary.json`, `metrics/main_summary.json`, `metrics/budget_6_summary.json`, `metrics/budget_12_summary.json`, `metrics/budget_24_summary.json`) and row-level CSVs are available.
- **Logs:** Command stdout and `/usr/bin/time -v` telemetry (including max RSS) are recorded in `.omx/logs/`.
- **Machine-readable decision:** `.omx/project_decision.json` contains the structured decision, confidence level, primary evidence, and limitations.
- **Result classification:** All reported results are from a synthetic toy simulation. No llama.cpp hook-prototype results, CUDA copy calibration data, or production validation data are present.

## 6. Conclusion

Agent Budget Parliament is viable as an adaptive budget-governance controller for heterogeneous agent workflows under the synthetic model studied. In evaluation across 5,000 paired tasks, it consistently outperformed uniform allocation (mean delta +0.0053, 95% CI [0.0052, 0.0055], win rate 88.9%) and single-best allocation (mean delta +0.088, win rate 99.9%) under matched total budget. The mechanism provides the most value under tight budgets, where adaptive allocation can redirect resources from saturated roles to under-funded ones, and provides diminishing returns as budget increases and saturation reduces the marginal value of adaptation.

However, parliament did not beat a greedy oracle allocator (win rate 0.0%), and these results do not establish that multi-agent systems outperform a strong single-agent system under matched reasoning-token budgets. The synthetic task model, while explicitly incorporating diminishing returns, coordination overhead, and shared-failure correlation, remains a simplification of real LLM-agent workflows. The hand-specified quality functions and parameter values are design choices, not empirical measurements.

The strongest next step is a real-trace pilot on 50–100 tasks, logging per-agent bids, allocated token/tool budget, actual cost and latency, and judged outcome quality, compared against uniform allocation, single-agent-with-tools, and a replay-oracle upper bound where possible. Until such validation is completed, the current result should be treated as a positive feasibility signal for adaptive budget governance under one set of modeling assumptions, not as evidence of real-world performance.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Simulator and policies | `src/budget_parliament.py` |
| Experiment CLI | `run_research.py` |
| Smoke test summary | `metrics/smoke_summary.json` |
| Main run summary | `metrics/main_summary.json` |
| Budget 6 summary | `metrics/budget_6_summary.json` |
| Budget 12 summary | `metrics/budget_12_summary.json` |
| Budget 24 summary | `metrics/budget_24_summary.json` |
| Smoke test stdout | `.omx/logs/smoke_stdout.log` |
| Smoke test time | `.omx/logs/smoke_time.log` |
| Main run stdout | `.omx/logs/main_stdout.log` |
| Main run time | `.omx/logs/main_time.log` |
| Main run env | `.omx/logs/main_env.log` |
| Budget 6 stdout | `.omx/logs/budget_6_stdout.log` |
| Budget 12 stdout | `.omx/logs/budget_12_stdout.log` |
| Budget 24 stdout | `.omx/logs/budget_24_stdout.log` |
| Project decision JSON | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260430T072418342113+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T072418342113+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T072418342113+0000/paper_manifest.json` |

## External Sources Referenced

- BAMAS: `https://chenzhenpeng18.github.io/papers/AAAI2026.pdf`
- Tran & Kiela (2026): `https://arxiv.org/abs/2604.02460`
- CascadeDebate: `https://arxiv.org/abs/2604.12262`
- Budgeted multi-agent synergy theory: `https://arxiv.org/abs/2601.17311`
