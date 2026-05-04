# A Deterministic MCP-Style Mutation Proxy for LLM-Agent Robustness Benchmarking

---

**AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, and benchmark outputs). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this as an unreviewed AI-generated research artifact and apply appropriate skepticism.

---

## Abstract

We investigate whether a transparent, deterministic mutation proxy operating at the Model Context Protocol (MCP) JSON-RPC message layer can inject reproducible tool-result faults with sufficiently low overhead to serve as a benchmark harness for LLM-agent robustness evaluation. A local in-process proxy forwards requests to a toy MCP server exposing three tools (`get_invoice`, `issue_refund`, `echo`) and mutates `get_invoice` responses according to seeded, auditable mutation strategies. Two deterministic policy simulators—naive (trusts tool output, follows embedded instructions) and guarded (validates structure, double-reads critical data, fails closed)—are evaluated across mutation rates from 0% to 100%. The proxy adds 6.43 µs/call with no mutation and 21.94 µs/call at 100% mutation, sustaining approximately 39,000 calls/sec in the worst case. The benchmark produces monotonic degradation in both policies as mutation rate increases and clearly distinguishes between them: at 100% mutation, the naive policy achieves a 0.785 safe-outcome rate while the guarded policy achieves 0.987. However, the guarded policy's safety is not perfect—repeated independent mutations on double-read requests can occasionally converge to plausible but incorrect structured results, yielding a 1.3% unsafe-outcome rate at 100% mutation—and its exact task-completion rate drops to 0.049 due to conservative refusal. These results support the viability of the proxy as a benchmark harness but do not constitute a claim about any specific LLM's MCP robustness, as all evaluations used deterministic simulators rather than live LLM agents.

## Introduction

LLM-based agents increasingly interact with external tools via structured protocols. The Model Context Protocol (MCP) specifies a JSON-RPC 2.0–based interaction layer in which clients invoke server tools through `tools/call` requests and receive structured `result` or `error` responses. A natural question for agent robustness is: what happens when tool responses are adversarially or accidentally corrupted?

Fault injection at the protocol layer is a well-established technique in distributed systems testing. Applying it to LLM-agent tool-use requires a proxy that can intercept, mutate, and forward MCP messages deterministically, with low enough overhead that the proxy itself does not become the bottleneck in benchmark orchestration—particularly since actual LLM inference latency will dominate in any realistic deployment.

This work addresses two questions:

1. **Proxy viability:** Can a transparent MCP-style mutation proxy inject reproducible tool-result faults with low enough overhead to be useful for LLM-agent robustness benchmarking?
2. **Benchmark sensitivity:** Does the resulting benchmark expose measurable differences between unsafe and guarded tool-use policies?

We emphasize at the outset that this study evaluates the benchmark infrastructure and methodology using deterministic policy simulators, not live LLM agents. The scientific claim is accordingly scoped to infrastructure viability and benchmark sensitivity, not to any specific LLM's robustness characteristics.

## Method

### Protocol Model

The benchmark models MCP at the JSON-RPC message layer, consistent with the official MCP specification (version 2025-06-18, Base Protocol Overview). Key constraints: MCP requests and responses use JSON-RPC 2.0; request IDs are non-null strings or integers; responses carry either a `result` or `error` field; server tools are invoked via MCP-style `tools/call`.

### Proxy Architecture

A transparent in-process proxy sits between the client (policy simulator) and the MCP server. The proxy:

1. Receives JSON-RPC requests from the client.
2. Forwards requests unmodified to the server.
3. Inspects responses for eligibility (currently, only `get_invoice` tool results are mutated).
4. Applies seeded, auditable mutations to eligible responses.
5. Returns the (possibly mutated) response to the client.

Mutation strategies include: `amount_delta` (numeric perturbation), `status_flip` (status field alteration), `missing_amount` (field removal), `currency_flip` (currency code change), and `prompt_injection` (injection of instruction text within tool output). Mutations are seeded for reproducibility.

### Toy MCP Server

The local server exposes three tools:

- `get_invoice`: returns a structured invoice object (amount, currency, status, ID).
- `issue_refund`: executes a refund side effect.
- `echo`: returns its input unchanged.

Only `get_invoice` responses are mutated; `issue_refund` and `echo` pass through unmodified.

### Policy Simulators

Two deterministic policy simulators model contrasting LLM-agent behaviors:

**Naive policy.** Trusts a single tool result. Simulates instruction-following failure when prompt-injection text appears in tool output. Proceeds with actions based on unvalidated tool data.

**Guarded policy.** Validates structured content against expected schema. Ignores tool-text instructions. Double-reads critical data (requests the same invoice twice and checks consistency). Fails closed on invalid or inconsistent results, refusing to issue refunds when data is suspect.

Both simulators are deterministic state machines, not LLMs. They are designed to represent archetypal failure and defense patterns observed in LLM-agent interactions, but they cannot capture the full distribution of LLM responses to corrupted tool output.

### Metrics

- **exact_success_rate:** Fraction of task runs where the simulator's action matches the ground-truth expected action exactly.
- **safe_outcome_rate:** Fraction of task runs where the simulator avoids incorrect refund side effects. Conservative refusal counts as safe (but not exact).
- **Overhead microbenchmarks:** Direct server call latency vs. proxy-mediated call latency at 0% and 100% mutation rates, measured over 100,000 calls per scenario.

### Experimental Configuration

- **Robustness runs:** 2,000 iterations × 3 tasks per iteration = 6,000 task evaluations per (policy, mutation_rate) cell.
- **Mutation rates tested:** 0%, 1%, 5%, 10%, 25%, 50%, 100%.
- **Overhead runs:** 100,000 calls per scenario (direct server, proxy with 0% mutation, proxy with 100% mutation).
- **Platform:** Linux 6.17.0-1014-nvidia-aarch64, glibc 2.39, Python 3.12.3, 128 GB RAM (122 GB available at benchmark time), no swap.
- **Peak resource usage:** 229,036 KB maximum RSS, 0 swap events.

## Results

### Overhead

| Scenario | Calls/sec | Mean (µs) | P95 (µs) | P99 (µs) | Mean overhead vs. direct (µs) | Overhead ratio vs. direct |
|---|---|---|---|---|---|---|
| Direct server | 276,524 | 3.41 | 3.49 | 4.51 | 0.00 | 1.000 |
| Proxy, 0% mutation | 99,343 | 9.83 | 9.97 | 10.54 | 6.43 | 2.888 |
| Proxy, 100% mutation | 39,082 | 25.34 | 26.02 | 33.25 | 21.94 | 7.441 |

The proxy adds approximately 6.43 µs per call with no mutation and 21.94 µs per call when every eligible response is mutated. Even at 100% mutation, the proxy sustains roughly 39,000 calls/sec. In any realistic LLM-agent deployment, inference latency (typically tens to hundreds of milliseconds per turn) would dominate, making this overhead negligible for benchmark orchestration purposes.

### Robustness

| Policy | Mutation rate | Exact success rate | Safe outcome rate | Mutations observed | Refund side effects | Task runs/sec |
|---|---|---|---|---|---|---|
| Naive | 0% | 1.000 | 1.000 | 0 | 6,000 | 67,212 |
| Naive | 1% | 0.994 | 0.997 | 105 | 5,989 | 67,015 |
| Naive | 5% | 0.976 | 0.989 | 477 | 5,932 | 64,784 |
| Naive | 10% | 0.949 | 0.976 | 1,000 | 5,896 | 61,956 |
| Naive | 25% | 0.868 | 0.945 | 2,463 | 5,616 | 55,106 |
| Naive | 50% | 0.736 | 0.892 | 4,958 | 5,260 | 46,611 |
| Naive | 100% | 0.482 | 0.785 | 10,000 | 4,572 | 35,715 |
| Guarded | 0% | 1.000 | 1.000 | 0 | 6,000 | 37,787 |
| Guarded | 1% | 0.982 | 1.000 | 229 | 5,891 | 37,888 |
| Guarded | 5% | 0.925 | 1.000 | 960 | 5,560 | 36,799 |
| Guarded | 10% | 0.841 | 1.000 | 2,023 | 5,058 | 35,292 |
| Guarded | 25% | 0.638 | 0.999 | 4,983 | 3,830 | 31,663 |
| Guarded | 50% | 0.360 | 0.997 | 10,007 | 2,216 | 26,717 |
| Guarded | 100% | 0.049 | 0.987 | 20,000 | 422 | 19,487 |

**Baseline validity.** At 0% mutation, both policies achieve perfect exact success and safe outcome rates, confirming that the proxy itself introduces no false degradation in the absence of mutations.

**Monotonic sensitivity.** Both policies show monotonic degradation in exact success rate as mutation rate increases, demonstrating that the benchmark is sensitive to the fault-injection rate.

**Policy separation.** The benchmark clearly distinguishes the two policies. The naive policy's safe-outcome rate degrades to 0.785 at 100% mutation, while the guarded policy maintains 0.987. This separation is present at every non-zero mutation rate.

**Guarded policy trade-off.** The guarded policy preserves safety at the cost of exact task completion. At 100% mutation, its exact success rate drops to 0.049 because it fails closed on nearly all suspicious data, refusing to act rather than risking incorrect refunds. This is a deliberate design trade-off of the guarded simulator, not a proxy artifact.

**Guarded safety is not perfect.** At 100% mutation, the guarded policy's safe-outcome rate is 0.987, not 1.000. The remaining 1.3% unsafe outcomes occur because repeated independent mutations on double-read requests can occasionally converge to a plausible but incorrect structured result that passes both validation and consistency checks. This is a meaningful negative result: double-read validation alone is insufficient for high-assurance agents under sustained mutation.

**Mutations observed vs. expected.** The guarded policy observes more mutations than the naive policy at the same nominal mutation rate (e.g., 20,000 vs. 10,000 at 100%) because the double-read strategy issues two `get_invoice` calls per task, each of which may be independently mutated.

## Limitations

1. **No live LLM evaluation.** All results are produced by deterministic policy simulators, not by actual LLM agents. The simulators are designed to represent archetypal behaviors, but they cannot capture the full distribution of LLM responses to corrupted tool output. This work supports the infrastructure and benchmark-method claim; it does not support any claim about a specific LLM's MCP robustness.

2. **In-process transport.** The proxy operates via in-process JSON serialization rather than the stdio, SSE, or streamable HTTP transports defined by MCP. Transport-layer effects (latency, framing errors, partial reads) are not exercised.

3. **Small, synthetic task suite.** Only three tools and five mutation strategies are tested. Real MCP deployments may involve more complex tool schemas, nested data, streaming responses, and mutation vectors not represented here (e.g., resource mutations, prompt mutations, tool-schema mutations, JSON-RPC protocol-level errors).

4. **Single mutation target.** Only `get_invoice` responses are mutated. A more comprehensive benchmark would also mutate `issue_refund` responses, tool schemas, resource content, and protocol-level error messages.

5. **Deterministic simulators as proxies for LLM behavior.** The naive and guarded simulators are hand-coded state machines. Whether real LLM agents exhibit the same failure and defense patterns—and at what rates—remains an open empirical question.

6. **Single hardware configuration.** All measurements were taken on one aarch64 host with ample RAM and no swap contention. Overhead figures may differ on resource-constrained or differently-architected systems.

## Reproducibility Checklist

- **Source code:** `scripts/mcp_mutation_benchmark.py`
- **Full metrics:** `outputs/benchmark_results.json`
- **Smoke test output:** `outputs/smoke_results.json`
- **CSV summaries:** `outputs/overhead.csv`, `outputs/robustness.csv`
- **Command logs:** `logs/smoke.log`, `logs/benchmark_run.log`, `logs/summarize.log`
- **Decision record:** `.omx/project_decision.json`
- **Run notes:** `run_notes.md`
- **MCP specification reference:** version 2025-06-18, Base Protocol Overview
- **Platform:** Linux 6.17.0-1014-nvidia-aarch64, Python 3.12.3, 128 GB RAM, 0 swap
- **Random seeds:** Mutations are seeded for reproducibility (seed values recorded in benchmark output)
- **Peak RSS:** 229,036 KB; 0 swap events
- **Exact command lines:** Recorded in run notes and reproduced in this paper
- **Evidence classification:** All results are from a local toy simulation with deterministic policy simulators. No live LLM, no llama.cpp hook prototype, no CUDA copy calibration, and no production validation was performed.

## Conclusion

A simple, transparent MCP-style mutation proxy operating at the JSON-RPC message layer is feasible, deterministic, and fast enough for local benchmark orchestration. The proxy adds at most approximately 22 µs per call even under 100% mutation, which is negligible compared to typical LLM inference latency. The resulting benchmark produces monotonic, sensitive degradation curves that clearly distinguish between naive and guarded tool-use policies.

The guarded policy's safety advantage comes at a steep cost in exact task completion, and its safety is not perfect: under sustained mutation, independent mutations on double-read requests can occasionally produce convergent false results, yielding a 1.3% unsafe-outcome rate at 100% mutation. This negative result suggests that double-read validation alone is insufficient for high-assurance agent designs.

The primary limitation of this work is the absence of live LLM-agent evaluation. The deterministic simulators validate the benchmark infrastructure and demonstrate its sensitivity, but they cannot answer the scientifically central question of how real LLM agents behave under MCP response mutation. A follow-up experiment should wrap a real stdio MCP server/client pair with the same mutation hooks, run against live LLM agents with transcript capture, and grade side effects from actual tool calls. The key acceptance metric for such a follow-up should be zero unsafe side effects under response mutation, not merely successful natural-language explanations.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Benchmark implementation | `scripts/mcp_mutation_benchmark.py` |
| Full JSON metrics | `outputs/benchmark_results.json` |
| Smoke test output | `outputs/smoke_results.json` |
| Overhead CSV | `outputs/overhead.csv` |
| Robustness CSV | `outputs/robustness.csv` |
| Smoke log | `logs/smoke.log` |
| Benchmark run log | `logs/benchmark_run.log` |
| Summary log | `logs/summarize.log` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260430T233348413950+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T233348413950+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T233348413950+0000/paper_manifest.json` |
| MCP specification (version 2025-06-18) | `https://modelcontextprotocol.io/specification/2025-06-18/basic/index` |
