# A Falsifiable Claim-Verification Ledger for Small Reasoning Agents: Controlled Mechanism Evidence from a Synthetic Tabular Reasoning Harness

## AI Provenance

This draft was AI-generated from automated research artifacts produced by an automated research facility. The evidence basis consists of `run_notes.md`, `.enoch/project_decision.json`, `.omx/project_decision.json`, the local `evidence_bundle.json`, and the local `claim_ledger.json` and `paper_manifest.json` synced to the control plane. The operator claims no personal authorship credit for the writing or for the empirical results beyond releasing the underlying artifacts. Readers should treat this manuscript as an unreviewed AI-generated research artifact; they should verify every numeric value against the referenced artifacts before citing or building on it. The internal project decision recorded in this run is `finalize_negative` with `research_outcome: useful_signal`; the manuscript reflects that scope and does not make claims beyond what the controlled evidence supports.

---

## Abstract

We study whether a lightweight, per-claim falsifiability protocol can reduce the propagation of false intermediate claims in a small reasoning agent. We instantiate the protocol on a deterministic synthetic tabular reasoning harness with noisy agent memory and a perfect verifier over generated tables, and compare three conditions: `baseline` (no ledger), `ledger_facts` (verifies and repairs atomic fact claims), and `ledger_full` (additionally verifies and repairs arithmetic and selection claims). At a memory corruption rate of 0.25 over 10,000 tasks per condition, the baseline reaches 0.6721 accuracy while accepting 12,759 false intermediate claims; both ledger conditions reach 1.0000 accuracy while verifying and rejecting false claims before they affect the answer. The same trend holds at noise rates 0.1 and 0.4; at 0.0 the ledger yields no accuracy gain, consistent with no spurious benefit. These results are bounded mechanism evidence supporting the falsifiable-claim-ledger protocol under controlled corruption. They do not validate real language-model behavior, natural-language retrieval, verifier imperfections, training effects, or deployment latency.

## 1. Introduction

Small reasoning agents that combine recalled or retrieved intermediate facts with arithmetic or selection operations are known to propagate errors silently: an internally false fact, once consumed, biases downstream deductions and may be indistinguishable from a correct chain in the final answer. A natural mitigation is to require each intermediate claim to be falsifiable — to expose a mechanism by which it can be checked — and to reject claims that fail the check before they are used. The unit of verification considered here is a per-claim entry over a structured domain, rather than a whole chain-of-thought trace.

This paper is intentionally narrow. The contributions are presented as a bounded-evidence technical note rather than as a general claim about deployed agents:

1. A portable description of a falsifiable-claim-ledger protocol with three operating modes (off, facts-only, full).
2. A deterministic tabular reasoning harness with a known ground-truth verifier that exercises the protocol.
3. A controlled comparison of accuracy, accepted false intermediate claims, and verifier-call counts at multiple corruption rates.
4. An explicit statement of what this evidence does and does not support, and a concrete proposal for a real-model follow-up.

The remainder of the paper presents the design, the harness, the metrics, the controls, and the limits of the evidence, and ends with a reproducibility checklist.

## 2. Method

### 2.1 Claim Scope

We test the following scoped claim verbatim, as recorded in the project-decision artifact:

> In a reproducible synthetic tabular reasoning harness with noisy agent memory and a perfect verifier, a falsifiable claim ledger eliminates accepted false intermediate claims and improves final-answer accuracy versus a no-ledger baseline.

Claims beyond this scope — including claims about real LLMs, natural-language retrieval, imperfect verifiers, training effects, or deployment latency — are out of scope for this paper and are addressed only as design notes for a follow-up.

### 2.2 Task Family

The harness generates tabular worlds consisting of records with categorical `group` and numeric `attribute` columns. The agent answers four query types:

- `sum_two` — sum of two attribute values for records matching two predicates;
- `difference` — absolute difference between two attribute values;
- `max_group` — maximum attribute value within a group;
- `count_above` — count of records with an attribute above a threshold.

These queries decompose into atomic facts (predicate lookups) and atomic arithmetic/selection operations, which is the structure a claim ledger must exercise.

### 2.3 Agent and Ledger Modes

The agent is a deterministic programmatic solver over the generated tables with a noisy memory layer. Each intermediate fact or operation can be wrapped in a falsifiable claim that names its inputs, its operation, and its expected output. A verifier recomputes the claim from the underlying tables and either accepts or rejects it; rejected claims are repaired by re-evaluating the underlying operation.

We compare three conditions:

- `baseline` — noisy memory, no ledger, no verifier. False facts flow directly into subsequent operations.
- `ledger_facts` — each atomic fact of the form `fact(row, column) → value` is checked against the verifier and repaired if rejected; arithmetic and selection claims are not separately checked.
- `ledger_full` — in addition to fact checks, each arithmetic claim of the form `arithmetic(op, a, b) → c` and each selection claim `select(predicate) → rows` is checked and repaired if rejected.

### 2.4 Noise Model

Each remembered fact is independently corrupted with probability `noise_rate` by a bounded integer perturbation on the stored value. We test `noise_rate ∈ {0.0, 0.1, 0.25, 0.4}`; 0.25 is the main-rate condition; 0.0 is the no-noise control used to detect spurious gains.

### 2.5 Metrics

We report:

- **Final-answer accuracy** — fraction of tasks whose final answer exactly matches the gold answer.
- **Wilson 95% confidence interval** for accuracy.
- **Accepted false intermediate claims** — claims whose stored value mismatches the verifier and which are consumed downstream; lower is better, zero is the target.
- **Checked claims** — total claims submitted to the verifier.
- **Rejected claims** — claims the verifier rejected; these are repaired in the ledger conditions.
- **Mean latency (ms/task)** — Python function-call wall-clock latency. This is reported for completeness only and is not an estimate of LLM inference or tool-call cost.

### 2.6 Compute Envelope

The harness is a single-process, CPU-only Python script. The full main run is scoped below 15 minutes of wall-clock time and is expected to complete in under 10 seconds on the target CPU worker referenced in the run notes, using under 100 MB of memory, with no GPU required. The reproduction recipe is in Section 5.

## 3. Results

### 3.1 Main Run

Table 1 reports the three conditions at `noise_rate = 0.25` over 10,000 tasks per condition (50 seeds × 200 tasks/seed).

| Condition       | Accuracy | 95% Wilson CI         | Accepted false claims | Checked claims | Rejected claims | Mean latency (ms) |
| --------------- | -------: | --------------------- | --------------------: | -------------: | --------------: | ----------------: |
| `baseline`      | 0.6721   | [0.6628, 0.6812]      | 12,759                | 0              | 0               | 0.00936           |
| `ledger_facts`  | 1.0000   | [0.9996, 1.0000]      | 0                     | 40,000         | 9,976           | 0.00889           |
| `ledger_full`   | 1.0000   | [0.9996, 1.0000]      | 0                     | 50,000         | 9,976           | 0.00913           |

*Table 1. Main run, 10,000 tasks per condition, `noise_rate = 0.25`. Values taken from `run_notes.md`.*

The baseline accepts 12,759 false intermediate claims and reaches 0.6721 accuracy; both ledger modes drive accepted false claims to zero and reach 1.0000 accuracy. The two ledger modes produce identical accuracy in this task family: arithmetic and selection claims consume already-repaired facts and are deterministic given those inputs, so `ledger_full` adds no measurable accuracy benefit beyond `ledger_facts` here. The mechanism supported by these numbers is the rejection and repair of false facts before they propagate.

Reported Python-side wall-clock is on the order of 9–10 microseconds per task across all conditions; this is consistent with parser and verifier overhead in a single-threaded harness and should not be read as a model-cost estimate.

### 3.2 Noise-Rate Controls

Table 2 reports accuracy and claim counts for `baseline` and `ledger_full` at four corruption rates.

| Noise rate | Baseline accuracy | Ledger-full accuracy | Baseline accepted false | Ledger rejected |
| ---------: | ----------------: | -------------------: | ----------------------: | --------------: |
| 0.0        | 1.0000            | 1.0000               | 0                       | 0               |
| 0.1        | 0.8560            | 1.0000               | 2,113                   | 1,627           |
| 0.25       | 0.6721            | 1.0000               | 12,759                  | 9,976           |
| 0.4        | 0.5370            | 1.0000               | 7,972                   | 6,406           |

*Table 2. Cross-noise controls, 10,000 tasks per condition at each noise rate. Values taken from `run_notes.md`.*

Three observations:

1. At `noise_rate = 0.0`, the ledger does not produce a spurious gain: both conditions reach 1.0000 accuracy and the verifier issues no rejections. This is the expected behavior when there is nothing for the ledger to catch.
2. At `noise_rate ∈ {0.1, 0.25, 0.4}`, the ledger condition reaches ceiling accuracy while rejecting a non-trivial fraction of checked claims; baseline accuracy decreases monotonically with noise.
3. Accepted false-claim counts in the baseline do not scale linearly with noise rate in this run. Their count depends on how corrupted values interact with downstream operations and on whether a corrupted input ever propagates far enough to be counted; the same caveat applies to ledger-side rejection counts, which depend on the order in which claims are emitted.

### 3.3 Failure-Mode Audit

The only source of error observed in this controlled setting is corrupted memory being consumed before any check; there is no observed failure mode attributable to the ledger machinery itself, since the verifier is a perfect synthetic oracle and introduces no error here. We separately note that `ledger_full` did not add measurable benefit beyond `ledger_facts` in this task family; the additional arithmetic and selection claims were deterministic given already-repaired facts. This is a finding about the harness, not a generalizable result.

### 3.4 Synthesis With Project Decision

The recorded project decision is `finalize_negative` with `research_outcome: useful_signal`, `hypothesis_status: supported`, `confidence: medium`, and `evidence_strength: moderate`. The `claim_scope` and `useful_signal_summary` fields in both `.enoch/project_decision.json` and `.omx/project_decision.json` (which are byte-identical in this run, sha256 `1b21101bdca68d6c7d29830426936c431bd10f17d572d8e7e8f179e5c23b058a`) match Tables 1 and 2 above. The decision records that the evidence is bounded mechanism evidence only, not direct publication-grade evidence for real small reasoning agents, and recommends a bounded deepen follow-up.

## 4. Limitations

The evidence in this paper is bounded. The following are explicit limits on what the numbers above do and do not support:

- **Synthetic generated data.** Tasks are generated tabular worlds, not natural-language QA or real retrieval. The ledger does not interact here with text encoding, retrieval noise, or tool-call ambiguity.
- **Perfect verifier.** The verifier has full access to ground truth and returns a correct accept/reject decision for every claim. Real verifier tools will be imperfect; under imperfect verifiers, repair can introduce new errors and the ledger machinery may incur non-trivial false-rejection and re-check cost.
- **Deterministic agent.** The "small reasoning agent" is a deterministic programmatic solver, not a prompted or fine-tuned LLM. The protocol assumes the agent can emit atomic, parseable claims; a real model's ability to do so is unmeasured here and is the central open question for transfer to real-model settings.
- **Latency interpretation.** Reported latency is Python function-call overhead in a single-process harness and is not an estimate of LLM inference or tool-call cost. The protocol adds per-claim verifier calls; their real cost depends on the verifier's implementation.
- **Task-family specificity.** Arithmetic and selection were deterministic given repaired facts in this task family, which makes `ledger_full` and `ledger_facts` interchangeable in this run. In tasks where arithmetic itself is a source of error, the additional ledger layers could matter; this run does not test that.
- **Non-transferable mechanism evidence.** The result supports the falsifiable-ledger mechanism under controlled corruption. It does not validate real-LLM behavior, realistic retrieval noise, training effects, or deployment latency.
- **Empty structured claim ledger.** The local `claim_ledger.json` for this run has `claims: []` and `ledger_status: "claims_require_review"`, with `unsupported_claim_count: 0`; atomic claim extraction has not yet been performed. Readers should not treat this paper as containing an audited ledger of atomic falsifiable claims; the evidence is at the harness-summary level only.
- **Sync caveat.** During the run, the worker-side project directory was not found and `http_sync.ok = false` (see `evidence_sync.http_sync`). The evidence used to compose this draft was retrieved from control-plane copies listed in the Referenced Artifacts section; per-task CSVs and `summary.json` files were not accessible in the local synced bundle, so the values cited here come from the `run_notes.md` summary rather than from a re-derived analysis of the raw CSV outputs.

Taken together, these limits mean that the numbers above support the mechanism under controlled corruption but do not validate real-LLM agents or production deployment. This is the basis on which the project decision is `finalize_negative` with `research_outcome: useful_signal`.

## 5. Reproducibility Checklist

- **Source script:** `scripts/ledger_experiment.py` (single-file Python harness).
- **Smoke test command:**
  ```
  set -o pipefail; python3 scripts/ledger_experiment.py --seeds 1 --tasks-per-seed 20 --out results/smoke 2>&1 | tee logs/smoke.log
  ```
- **Main run command (50 seeds × 200 tasks/seed = 10,000 tasks/condition at `noise_rate = 0.25`):**
  ```
  set -o pipefail; python3 scripts/ledger_experiment.py --seeds 50 --tasks-per-seed 200 --noise-rate 0.25 --out results/main 2>&1 | tee logs/main.log
  ```
- **Control commands (20 seeds × 200 tasks/seed = 4,000 tasks/condition):**
  ```
  set -o pipefail; python3 scripts/ledger_experiment.py --seeds 20 --tasks-per-seed 200 --noise-rate 0.0  --out results/control_no_noise  2>&1 | tee logs/control_no_noise.log
  set -o pipefail; python3 scripts/ledger_experiment.py --seeds 20 --tasks-per-seed 200 --noise-rate 0.1  --out results/control_low_noise  2>&1 | tee logs/control_low_noise.log
  set -o pipefail; python3 scripts/ledger_experiment.py --seeds 20 --tasks-per-seed 200 --noise-rate 0.4  --out results/control_high_noise 2>&1 | tee logs/control_high_noise.log
  ```
- **Syntax check:**
  ```
  set -o pipefail; python3 -m py_compile scripts/ledger_experiment.py 2>&1 | tee logs/py_compile.log
  ```
- **Per-task counts:** Main run is 50 seeds × 200 tasks/seed = 10,000 tasks/condition; controls are 20 seeds × 200 tasks/seed = 4,000 tasks/condition. Conditions are `baseline`, `ledger_facts`, and `ledger_full`; the noise-rate 0.0 control is intended as a no-effect check.
- **Output artifacts:** `results/main/summary.json`, `results/main/task_results.csv`, `results/main/ledger_claims.csv`; `results/control_no_noise/`, `results/control_low_noise/`, `results/control_high_noise/`; `results/aggregate_summary.csv`.
- **Command logs:** `logs/smoke.log`, `logs/main.log`, `logs/control_no_noise.log`, `logs/control_low_noise.log`, `logs/control_high_noise.log`, `logs/py_compile.log`.
- **Compute envelope:** CPU-only, single process, scoped below 15 minutes wall-clock, under 100 MB memory, no GPU required.
- **Determinism:** The harness uses fixed deterministic seeding; specific seeds are user-supplied CLI integers.
- **Artifact-access caveat:** The original worker-side artifacts listed above were not retrievable during this run because the project directory on the worker was not found (`evidence_sync.http_sync.reason: "worker_read_failed"`); the values in this draft are taken from the control-plane copies of `run_notes.md`, `.enoch/project_decision.json`, and `.omx/project_decision.json` and from the local `evidence_bundle.json`, `claim_ledger.json`, and `paper_manifest.json`.

## 6. Conclusion

A falsifiable-claim ledger, instantiated on a deterministic synthetic tabular reasoning harness with noisy memory and a perfect verifier, eliminates accepted false intermediate claims and lifts final-answer accuracy from 0.6721 to 1.0000 at a corruption rate of 0.25, while a no-noise control shows the protocol produces no spurious accuracy gain. The result supports the underlying mechanism under controlled corruption.

This support is explicitly bounded, and the recorded project decision is `finalize_negative` with `research_outcome: useful_signal` rather than a positive publication record. The natural next step is a bounded deepen follow-up that re-runs the same protocol with a real small open-weight or API model on natural-language tabular QA with noisy retrieval and an imperfect verifier. The follow-up should report, at minimum: (a) accuracy with and without the ledger, (b) unsupported-claim rate, (c) abstention/refusal rate, and (d) a ledger-trace audit confirming that the model emits atomic checkable claims and that verifier calls are well-formed. From the project-decision artifacts: on at least 500 held-out tasks the ledger condition should improve accuracy by at least 5 absolute percentage points, or cut unsupported false claims by at least 50%, without increasing abstention by more than 10 absolute points. Conversely, the follow-up should stop as negative if the model cannot reliably emit auditable atomic claims, if verifier-call failures erase the accuracy gain, or if unsupported false claims are not reduced by at least 25% on a 100-task pilot.

## Referenced Artifacts

The following local artifacts were used as the evidence basis for this paper. Every numeric value in Tables 1 and 2 is taken from `run_notes.md`; the project-decision fields (`claim_scope`, `scale_limits`, `useful_signal_summary`, `followup_*`) are taken from `.enoch/project_decision.json` and `.omx/project_decision.json` (byte-identical in this run); the claim-ledger status and evidence-bundle structure are taken from the local `claim_ledger.json` and `evidence_bundle.json`; the paper-level ledger metadata is taken from `paper_manifest.json`. No external citation database was available to this draft.

- `run_notes.md` (sha256 `cc68895f494d1f6e8a04255a90343bfeb1a05557d848f44c3debd138efce5e9d`) — research question, experiment design, commands, results tables, interpretation, limitations, final decision.
- `.enoch/project_decision.json` and `.omx/project_decision.json` (sha256 `1b21101bdca68d6c7d29830426936c431bd10f17d572d8e7e8f179e5c23b058a`, byte-identical) — project-decision records, including claim scope, scale limits, useful-signal summary, follow-up hypothesis, follow-up thresholds, and stop conditions.
- `scripts/ledger_experiment.py` — the experiment harness.
- `results/main/summary.json`, `results/main/task_results.csv`, `results/main/ledger_claims.csv` — main run outputs (not present in the local synced bundle; referenced by path only).
- `results/control_no_noise/`, `results/control_low_noise/`, `results/control_high_noise/` — control run outputs (not present in the local synced bundle; referenced by path only).
- `results/aggregate_summary.csv` — compact cross-run metric table (not present in the local synced bundle; referenced by path only).
- `logs/smoke.log`, `logs/main.log`, `logs/control_no_noise.log`, `logs/control_low_noise.log`, `logs/control_high_noise.log`, `logs/py_compile.log` — command logs (not present in the local synced bundle; referenced by path only).
- `papers/source-record-redacted-20260530T085753691945+0000/claim_ledger.json` — claim-ledger file for this paper (`schema_version: claim_ledger.v2`). In the synced copy, `claims` is an empty array, `ledger_status: "claims_require_review"`, `unsupported_claim_count: 0`. Atomic claim extraction has not yet been performed and the paper does not present an audited ledger of atomic falsifiable claims.
- `papers/source-record-redacted-20260530T085753691945+0000/evidence_bundle.json` — evidence bundle enumerating three public evidence files (`run_notes.md`, `.enoch/project_decision.json`, `.omx/project_decision.json`), with `metric_summaries` sourced from the two project-decision JSONs. The `evidence_sync.http_sync` record indicates `ok: false` and `reason: "worker_read_failed"`, consistent with the sync caveat in Section 4.
- `papers/source-record-redacted-20260530T085753691945+0000/paper_manifest.json` — paper manifest declaring `claim_count: 0` (consistent with the empty `claims` array in the claim-ledger JSON) and `evidence_file_count: 3`.
- `paper_review_item` — paper review record with `review_status: "finalized"`, `paper_status: "publication_draft"`, `checklist_progress: {passed: 0, failed: 0, pending: 9, accepted_risk: 0, not_applicable: 0, total: 9}`, and `missing_signals: ["readiness_audit"]`. The review record shows nine pending checklist items and a missing readiness-audit signal, consistent with the bounded-evidence status reflected in this draft.
