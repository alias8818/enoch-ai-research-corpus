# Research Agent Treaty Protocol: A Contract Layer for Multi-Agent Handoff Constraint Enforcement

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, claim ledgers, and decision JSON). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

Multi-agent systems increasingly rely on handoff and delegation protocols, but existing interoperability standards address transport, tool use, and tracing rather than task-level semantic constraints such as scope boundaries, admissible evidence, schema conformance, and termination conditions. We propose the Research Agent Treaty Protocol (RATP), a lightweight contract layer in which agents explicitly commit to task treaties specifying these constraints before execution begins. To evaluate feasibility, we implemented a deterministic, model-free stochastic smoke-test harness and ran 1,000 paired baseline-versus-treaty trials. The treaty condition produced a 73.38% reduction in mean handoff loss (3.339 → 0.889), a 76.56% reduction in scope violations, a 100.00% reduction in evidence violations, and a 74.06% reduction in termination misses, at the cost of a 0.7% acceptance-rate penalty and a 63.8% repair rate. These results constitute a positive smoke-test signal from a synthetic environment only; they do not demonstrate that RATP improves real LLM agent behavior. Live-agent paired trials with blind scoring remain necessary before any scientific closure claim can be supported.

---

## Introduction

Current multi-agent interoperability efforts—including Google's Agent-to-Agent (A2A) protocol, the Model Context Protocol (MCP), and the OpenAI Agents SDK—focus on transport-level connectivity, tool invocation, handoff mechanics, guardrails, and distributed tracing. These layers are necessary but insufficient for ensuring that a delegated sub-task adheres to the semantic constraints intended by the delegating agent: scope boundaries, admissible evidence sources, required output schema fields, and termination conditions.

Without an explicit contract at the task level, handoffs between agents are prone to several failure modes. *Scope creep* occurs when the receiving agent operates beyond its mandate. *Evidence contamination* arises when unsupported or disallowed claims enter the output. *Schema non-conformance* results when required fields are omitted from the handoff output. *Termination misses* happen when the sub-task fails to signal completion under specified conditions. We refer to the aggregate of these failure modes as *handoff loss*.

We propose the Research Agent Treaty Protocol (RATP) as a complementary layer: before a handoff is accepted, both agents commit to a treaty—a structured JSON contract specifying scope, allowed evidence, handoff schema, and termination conditions. Violations trigger repair or rejection rather than silent propagation into downstream agent states.

The central question is whether such a treaty layer can measurably reduce handoff loss without imposing unacceptable overhead or rigidity. This paper reports on a bounded feasibility test: a deterministic, model-free stochastic simulation designed to determine whether the mechanism produces any signal worth investigating in live agent trials. We stress at the outset that this is a smoke test, not a validation study.

---

## Method

### Design

We constructed a paired experimental design comparing a baseline condition (unconstrained handoff) against a treaty condition (RATP-enforced handoff). Each trial simulates a single handoff between a delegating agent and a receiving agent. The simulation is model-free: no LLM is invoked. Instead, stochastic failure modes are injected according to fixed probability distributions, and the treaty mechanism enforces validation, repair, and rejection logic deterministically.

### Harness

The smoke-test harness (`src/treaty_smoke_test.py`) is a standalone Python script that performs the following steps per trial:

1. **Task generation.** Generates a task specification with randomized scope, evidence constraints, required schema fields, and termination conditions.
2. **Failure injection.** Simulates a handoff by sampling failure events (scope violations, evidence violations, missing fields, termination misses) from predefined distributions.
3. **Baseline condition.** The handoff is accepted unconditionally (acceptance rate = 1.0). All violations propagate without intervention.
4. **Treaty condition.** The handoff is validated against the treaty. Violations trigger a repair attempt (with a fixed repair success probability). Unrepairable handoffs are rejected.
5. **Recording.** Per-trial metrics are recorded: handoff loss (composite of all violation types), individual violation counts, acceptance/rejection outcome, and repair events.

### Parameters

| Parameter | Value |
|---|---|
| Trials per condition | 1,000 |
| Random seed | 340367 |
| Baseline acceptance rate | 1.0 (unconditional) |
| Treaty acceptance rate | Empirical (0.993 observed) |

### Metrics

- **Handoff loss**: Composite penalty aggregating scope violations, evidence violations, missing required fields, and termination misses.
- **Scope violations**: Count of handoffs where the receiving agent exceeded its mandated scope.
- **Evidence violations**: Count of handoffs where unsupported or disallowed evidence was introduced.
- **Missing required fields**: Count of schema fields absent from the handoff output.
- **Termination misses**: Count of handoffs where the receiving agent failed to signal completion under the specified termination condition.
- **Repair rate**: Fraction of treaty-condition handoffs that required at least one repair attempt.
- **Accepted rate**: Fraction of handoffs accepted (not rejected) after validation and any repairs.

### Execution

```bash
python3 src/treaty_smoke_test.py --trials 1000 --seed 340367 \
  --out artifacts/treaty_smoke_metrics.json \
  --jsonl logs/treaty_smoke_trials.jsonl
```

---

## Results

### Aggregate Metrics

| Metric | Baseline (n=1000) | Treaty (n=1000) | Delta |
|---|---|---|---|
| Mean handoff loss | 3.339 | 0.889 | −73.38% |
| Mean scope violations | 0.751 | 0.176 | −76.56% |
| Mean evidence violations | 0.103 | 0.000 | −100.00% |
| Mean missing required fields | 2.126 | 0.007 | −99.67% |
| Mean termination misses | 0.640 | 0.166 | −74.06% |
| Repair rate | 0.000 | 0.638 | — |
| Accepted rate | 1.000 | 0.993 | −0.70% |

### Interpretation

The treaty condition produced substantial reductions across all measured violation categories. The largest absolute reduction was in missing required fields (2.126 → 0.007), driven by the treaty's schema validation and repair logic. Evidence violations were eliminated entirely in the treaty condition, though the baseline rate was already low (0.103), making this the least informative comparison.

The treaty mechanism incurred two costs. First, 0.7% of handoffs were rejected rather than accepted (acceptance rate 0.993 vs. 1.000). Second, 63.8% of treaty-condition handoffs required at least one repair attempt, indicating that the raw handoff output frequently violated treaty constraints and that the repair pathway was heavily utilized. The high repair rate raises the question of whether the repair logic in a live system (e.g., re-prompting an LLM) would achieve comparable success at acceptable latency cost.

The 100.00% evidence violation reduction should be interpreted cautiously. The baseline rate was only 0.103, meaning the absolute reduction was small (0.103 → 0.000), and the elimination may reflect the specific repair logic encoded in the harness rather than a general property of the treaty mechanism. A floor effect at a low base rate limits the inferential weight of this particular result.

### Claim Audit Status

The claim ledger for this paper was checked and received a status of `blocked_empty_claims`, indicating that no structured claims were extracted for formal evidence linkage during the automated audit pass. This means the quantitative results reported above have not passed through a structured claim-evidence audit pipeline. Readers should weight the reported metrics accordingly and treat them as raw experimental output rather than audit-approved claims.

---

## Limitations

1. **Synthetic environment.** The smoke-test harness is model-free and stochastic. It simulates failure modes from fixed distributions rather than observing actual LLM agent behavior. The large percentage reductions may not replicate when real language models generate handoff content, because LLM failure modes may differ in distribution, correlation, and repairability from those encoded in the harness.

2. **No live agent validation.** No LLM, Codex, or other production agent was involved in any trial. The results demonstrate that the treaty mechanism *can* reduce violations under the harness's assumptions, not that it *does* reduce violations in practice. This is a feasibility signal, not a validation result.

3. **Repair logic is harness-specific.** The 63.8% repair rate and the resulting violation reductions depend on the repair success probabilities hard-coded in the harness. Real repair attempts (e.g., re-prompting an LLM with constraint feedback) may have different success rates, latencies, and failure modes. The repair dynamics are the least generalizable component of this experiment.

4. **Potential over-rigidity.** A treaty layer that enforces strict scope and schema constraints may harm exploratory or creative tasks where beneficial scope expansion occurs. The harness does not model this trade-off. In live settings, overly rigid treaties could reduce agent utility even as they reduce measured violations.

5. **Confirmation bias risk in follow-up.** The recommended live-agent pilot requires blind scoring to avoid the experimenter's knowledge of condition assignment influencing violation judgments. Without blinding, the treaty's apparent benefit could be inflated by subjective scoring.

6. **Narrow failure model.** The harness models four violation types. Real multi-agent handoffs may exhibit additional failure modes (e.g., adversarial inputs, context window overflow, tool misuse, prompt injection) not captured here.

7. **Unvalidated claim ledger.** The automated claim audit returned `blocked_empty_claims`, meaning no structured claims were extracted and linked to evidence files. The quantitative results in this paper therefore lack the formal claim-evidence traceability that a fully audited artifact would provide.

---

## Reproducibility Checklist

- [x] **Random seed fixed.** Seed 340367 was specified and recorded.
- [x] **Number of trials stated.** 1,000 per condition.
- [x] **Harness source available.** `src/treaty_smoke_test.py`.
- [x] **Per-trial data retained.** `logs/treaty_smoke_trials.jsonl`.
- [x] **Aggregate metrics retained.** `artifacts/treaty_smoke_metrics.json`.
- [x] **Stdout log retained.** `logs/treaty_smoke_stdout.log`.
- [x] **Decision JSON retained.** `.omx/project_decision.json`.
- [x] **Run notes retained.** `run_notes.md`.
- [x] **Research synthesis retained.** `artifacts/research_result.md`.
- [ ] **Live agent replication.** Not performed; required for scientific closure.
- [ ] **Blind scoring.** Not applicable to this synthetic study but required for any live-agent follow-up.
- [ ] **Claim-evidence audit passed.** Claim ledger returned `blocked_empty_claims`; structured claims were not extracted or linked.

---

## Conclusion

The Research Agent Treaty Protocol introduces a task-level contract layer for multi-agent handoffs, addressing scope, evidence, schema, and termination constraints that existing interoperability protocols leave unenforced. A deterministic, model-free smoke test with 1,000 paired trials produced large reductions in simulated handoff loss (73.38%), scope violations (76.56%), evidence violations (100.00%), and termination misses (74.06%), at the cost of a 0.7% acceptance-rate penalty and a 63.8% repair rate.

These results are a positive feasibility signal from a synthetic environment. They do not constitute evidence that RATP improves real LLM agent behavior. The mechanism's value remains undemonstrated outside the harness's assumptions about failure distributions and repair success. The high repair rate (63.8%) in particular raises questions about latency and cost in live deployments that this experiment cannot address.

The appropriate next step is a paired live-agent pilot (12–20 tasks, blind scoring, with a kill condition of less than 20% violation reduction or greater than 25% wall-time increase), as specified in the project decision record. Until such a pilot is completed, the status of RATP remains *positive smoke-test signal, not scientific closure*.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Smoke-test harness | `src/treaty_smoke_test.py` |
| Per-trial log | `logs/treaty_smoke_trials.jsonl` |
| Stdout log | `logs/treaty_smoke_stdout.log` |
| Aggregate metrics | `artifacts/treaty_smoke_metrics.json` |
| Research synthesis | `artifacts/research_result.md` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260430T102048326127+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T102048326127+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T102048326127+0000/paper_manifest.json` |
| Notion source page | `https://www.notion.so/Research-Agent-Treaty-Protocol-source-record-redacted` |

### External Evidence Sources Consulted

- Google A2A protocol announcement: `https://developers.googleblog.com/a2a-a-new-era-of-agent-interoperability/`
- Model Context Protocol specification (2025-06-18): `https://modelcontextprotocol.io/specification/2025-06-18/basic`
- OpenAI Agents SDK — Handoffs: `https://openai.github.io/openai-agents-python/handoffs/`
- OpenAI Agents SDK — Guardrails: `https://openai.github.io/openai-agents-python/guardrails/`
- OpenAI Agents SDK — Tracing: `https://openai.github.io/openai-agents-python/tracing/`
- arXiv:2505.02279
- arXiv:2601.08815
