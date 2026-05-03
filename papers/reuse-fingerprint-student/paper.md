# Reuse-Fingerprint Student: A Compact Fingerprint-Pair Admission Policy for Exact Prefix-Cache Reuse

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, result files, and logs). The operator who released the artifact claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism. No human review is asserted to have occurred.

---

## Abstract

We investigate whether a lightweight logistic-regression classifier operating solely on compact fingerprint-pair features can accurately predict which prior request in a recent-cache window is worth probing for exact prefix-cache reuse. In a synthetic workload modeling repeated student-submission grading traffic with shared rubric prefixes, the student policy recovers 100.0% of oracle-available reusable prefix tokens across calibration (900 requests), stress (1,800 requests), and a 5-seed stress sweep, while admitting zero false-positive cache probes. By contrast, a first-block-hash baseline captures the same reusable tokens but suffers 13.6–18.9% false-positive admission rates, and a whole-prompt MinHash similarity baseline captures only 65.5–71.1% of oracle reuse with 78.7–83.3% false positives. An LRU-previous baseline captures under 2%. These results are positive but narrow: the workload is synthetic, the classification problem is highly separable due to the informativeness of exact prefix block hashes, and no end-to-end serving-engine validation was performed. The student functions as an admission guard for already-existing exact-prefix reuse opportunities, not as a semantic canonicalization router.

## Introduction

Prefix caching in LLM serving engines can reduce redundant computation when consecutive requests share exact token prefixes. Deciding which prior cache slot to probe, however, presents a trade-off: probing too few slots misses reuse opportunities, while probing too many wastes scheduling and comparison work. Simple heuristics—matching on the first block hash, ranking by whole-prompt MinHash similarity, or always probing the LRU-previous slot—each carry distinct failure modes. First-block matching produces false positives when different prompts share an initial block but diverge before reaching a useful reuse threshold. Whole-prompt similarity metrics conflate semantic relatedness with exact prefix overlap, yielding both missed reuse and high false-positive rates. LRU probing captures only the narrow case where the immediately preceding request happens to share a prefix.

We explore an intermediate approach: a compact "reuse-fingerprint student" that takes as input a small set of fingerprint-pair features—prefix block-hash run length, equal-block counts, first-block flags, prefix and whole-prompt SimHash distances, MinHash overlap, and length ratios—and predicts whether a candidate prior request is worth probing for reuse. The student is trained to approximate an oracle that computes the true longest common prefix (LCP) between each incoming request and every slot in a recent-cache window, labeling a pair as reusable when the LCP meets or exceeds a threshold of 64 exact prefix tokens (organized as 16-token blocks × 4).

The central question is whether this compact feature set suffices to recover oracle-level reuse capture while eliminating the false-positive admissions produced by simpler baselines, or whether the problem requires richer and more expensive comparison. A secondary question—whether the learned calibration adds value beyond what a deterministic exact-prefix index or hand-written threshold policy could achieve—remains open and is not resolved by this study.

## Method

### Workload

We generate synthetic traffic modeling a student-submission grading system. Requests are organized into course/assignment/rubric cohorts, producing repeated template prefixes. Each request contains a shared rubric prefix followed by student-specific content. This structure creates exact prefix overlap within cohorts and no meaningful prefix overlap across cohorts. The workload is deliberately favorable to the approach: reuse opportunities are dense and unambiguous.

### Fingerprint Features

For each (incoming request, cached request) pair, the student receives the following fixed-width features:

- **Prefix block-hash run length**: length of the longest consecutive run of matching block hashes starting from position zero.
- **Equal-block count**: total number of block positions where hashes match, regardless of contiguity.
- **First-block flag**: binary indicator of whether the first block hash matches.
- **Prefix SimHash distance**: SimHash computed over the prefix portion only; Hamming distance between pair.
- **Whole-prompt SimHash distance**: SimHash over the full prompt; Hamming distance between pair.
- **MinHash overlap**: Jaccard estimate from MinHash signatures.
- **Length ratios**: ratio of incoming to cached prompt lengths, and ratio of prefix lengths.

All features are computed from compact fingerprint representations, not from raw prompt text. This is the core efficiency claim: the student avoids expensive raw-prompt comparison.

### Student Model

The student is a calibrated logistic-regression classifier. It is trained on pair-level labels derived from the oracle LCP: a pair is positive if the true LCP is ≥ 64 tokens (4 blocks × 16 tokens/block). At inference time, the student scores every (incoming, cached) pair in a sliding window of the 160 most recent requests and ranks candidates by predicted probability. The top-ranked candidate above an admission threshold is selected for probing.

### Baselines

- **First-block**: admit any prior request whose first block hash matches the incoming request's first block hash.
- **Whole-prompt MinHash**: rank by MinHash Jaccard estimate; admit the top candidate above a similarity threshold.
- **LRU previous**: always probe the single most recent prior request.
- **Oracle**: probe the best prior slot as determined by true LCP.

### Evaluation Metrics

- **Oracle-capture fraction**: fraction of oracle-available reusable prefix tokens actually saved by the policy.
- **False-positive admission fraction**: fraction of admitted probes that yield no reusable prefix (LCP < 64 tokens).
- **Precision when selected**: fraction of admitted probes that yield reusable prefix ≥ 64 tokens.
- **Pair classifier quality**: average precision (AP), ROC-AUC, and F1 score for the underlying pair classifier.

### Experimental Modes

- **Smoke**: small-scale correctness check.
- **Calibration**: 900 total requests; 405 held-out stream requests.
- **Stress**: 1,800 total requests; 810 held-out stream requests.
- **5-seed stress sweep**: stress configuration repeated across 5 random seeds to assess variance.

All modes are CPU-only fingerprint simulations. No GPU serving engine, no llama.cpp hooks, and no CUDA copy operations were involved. The experiments measure oracle-reusable prefix tokens in a controlled simulation, not end-to-end serving latency or compute reduction.

### Environment

All experiments ran on a Linux aarch64 host (NVIDIA GB10) with 121 GiB RAM and swap intentionally disabled. The fingerprint simulation is CPU-only; GPU utilization was 0% throughout. Peak RSS was 172,812 kB (mean across the 5-seed sweep), with the single-seed stress run peaking at 172,952 kB. No swap events occurred.

## Results

### Pair Classifier Performance

The pair-level logistic-regression classifier achieved near-perfect discrimination across all configurations:

| Configuration | Average Precision | ROC-AUC | F1    |
|---------------|-------------------|---------|-------|
| Smoke         | 1.000             | —       | 1.000 |
| Calibration   | 1.000             | 1.000   | 1.000 |
| Stress        | 1.000             | 1.000   | 1.000 |

The classifier's separability is high because exact prefix block hashes are highly informative features for the admission-guard task. This is expected and acceptable for the intended function, but it means the student operates closer to a calibrated fingerprint policy than to a learned semantic model. The near-perfect scores should not be interpreted as evidence of generalization to less separable problems.

### Stream Policy: Oracle-Capture and False Positives

| Configuration | Policy         | Oracle-Capture | False-Positive Fraction | Precision When Selected | Tokens Saved |
|---------------|----------------|----------------|-------------------------|-------------------------|--------------|
| Calibration   | Student        | 100.0%         | 0.0%                    | 100.0%                  | 11,632       |
| Calibration   | First-block    | 100.0%         | 13.6%                   | —                       | —            |
| Calibration   | Whole MinHash  | 71.1%          | 78.7%                   | —                       | —            |
| Calibration   | LRU previous   | 1.7%           | —                       | —                       | —            |
| Stress        | Student        | 100.0%         | 0.0%                    | 100.0%                  | 19,776       |
| Stress        | First-block    | —              | 18.9%                   | —                       | —            |
| Stress        | Whole MinHash  | 65.5%          | 83.3%                   | —                       | —            |
| Stress        | LRU previous   | 1.5%           | —                       | —                       | —            |

The student policy captures all oracle-available reuse while admitting zero false positives. The first-block baseline also captures all reuse in the calibration condition (because matching first blocks are necessary for any prefix overlap in this workload), but admits 13.6–18.9% false-positive probes—cases where the first block matches but the prefix diverges before reaching the 64-token threshold. Oracle-capture for the first-block baseline under stress was not separately reported in the result artifacts; given the workload structure, it is expected to be comparable to calibration. The whole-prompt MinHash baseline both misses substantial reuse and produces very high false-positive rates. LRU captures negligible reuse.

The "tokens saved" figures (11,632 and 19,776) represent oracle-measured reusable prefix tokens in the simulation, not measured latency or compute reduction in a serving engine.

### 5-Seed Stress Sweep

| Metric                                      | Mean     | Std   |
|---------------------------------------------|----------|-------|
| Student oracle-capture fraction             | 100.0%   | 0.0%  |
| Student false-positive fraction             | 0.0%     | 0.0%  |
| Student precision when selected             | 100.0%   | 0.0%  |
| First-block false-positive fraction         | 16.8%    | 1.6%  |
| Whole MinHash oracle-capture                | 70.9%    | —     |
| Whole MinHash false-positive fraction       | 81.8%    | —     |

Variance across seeds is negligible for the student policy. The first-block false-positive rate varies modestly (±1.6%), reflecting differences in cohort composition across seeds. Standard deviations for the whole-MinHash metrics were not reported in the summary artifact.

### Resource Usage

Peak RSS across the 5-seed sweep averaged 172,812 kB (approximately 169 MiB), with the single-seed stress run peaking at 172,952 kB. No swap activity was recorded. The simulation is CPU-only; no GPU resources were consumed. These figures characterize the fingerprint simulation only, not an integrated serving path.

## Limitations

1. **Synthetic workload only.** No private or product prompt trace was available. The traffic distribution is deliberately favorable: repeated rubric/template prefixes within cohorts create dense, unambiguous reuse opportunities. Real traffic may exhibit lower reuse density, more partial overlap, and noisier cohort boundaries. The reported metrics should not be assumed to hold for production workloads.

2. **Exact prefix-cache simulation, not end-to-end serving.** The benchmark models exact token-prefix reuse in isolation. It does not exercise a real serving engine (e.g., vLLM, llama.cpp) with actual cache eviction, scheduling, or block-allocation dynamics. The "tokens saved" figures represent oracle-measured reusable prefix tokens, not measured latency or compute reduction.

3. **Highly separable classification problem.** The pair classifier achieves perfect or near-perfect discrimination because exact prefix block hashes are extremely informative for the admission task. This supports the student's viability as a lightweight admission guard but does not demonstrate that the approach generalizes to settings where fingerprint features are less discriminative (e.g., partial-block overlap, multilingual content, or adversarially similar prefixes).

4. **The student is an admission guard, not a semantic router.** It does not create reusable prefixes or canonicalize semantically equivalent prompts. False positives waste probe and comparison work but do not alter prompt semantics. This limits the scope of the claim: the student reduces unnecessary probing, not unnecessary prompt diversity.

5. **No comparison to deterministic exact-prefix index.** A hash-based exact-prefix index (e.g., a trie over block hashes) might achieve the same admission quality without a learned model. The value of the calibrated student over a hand-written threshold policy was not evaluated. This is a significant gap: if a deterministic index suffices, the learned model adds complexity without benefit.

6. **Fixed window size.** The 160-request recent-cache window was not varied. Sensitivity to window size, eviction policy, and cache pressure remains untested.

7. **Single workload domain.** All traffic models one application pattern (student-submission grading with rubric cohorts). Performance under different reuse structures (e.g., conversational multi-turn, retrieval-augmented generation with shared context) is unknown.

## Reproducibility Checklist

- **Source code**: `src/reuse_fingerprint_student.py` (harness), `src/run_seed_sweep.py` (sweep runner).
- **Tests**: `tests/test_reuse_fingerprint_student.py` (unit/regression tests; all passing per `logs/test_final.log`).
- **Result files**: `results/smoke/results.json`, `results/calibration/results.json`, `results/stress/results.json`, `results/seed_sweep/summary.json`, plus per-request CSV files.
- **Logs**: `logs/environment_probe.log`, `logs/py_compile.log`, `logs/test_final.log`, `logs/smoke_final.log`, `logs/calibration.log`, `logs/stress.log`, `logs/seed_sweep.log`, `logs/result_digest.log`.
- **Decision artifact**: `.omx/project_decision.json`.
- **Environment**: Linux aarch64, NVIDIA GB10, 121 GiB RAM, swap disabled, Python 3 with NumPy and scikit-learn (versions recorded in `logs/environment_probe.log`).
- **Random seeds**: 5 seeds in the stress sweep (seed values recorded in `results/seed_sweep/summary.json`).
- **Commands**: Full command sequences recorded in `run_notes.md`.
- **Peak RSS**: Measured via `/usr/bin/time -v`; values reported in run notes and decision JSON.
- **Evidence classification**: All results are from a CPU-only fingerprint simulation (toy/synthetic workload). No llama.cpp hook-prototype results, no CUDA copy calibration, and no production validation data are present.

## Conclusion

On a synthetic repeated-rubric workload, a compact fingerprint-pair logistic-regression student recovers all oracle-available exact-prefix reuse opportunities while producing zero false-positive admission decisions. It substantially outperforms first-block matching (which admits 13.6–18.9% false positives), whole-prompt MinHash similarity (which misses 29–35% of reuse and admits 78.7–83.3% false positives), and LRU-previous probing (which captures under 2% of reuse). The result is stable across five random seeds.

However, the result is narrow. The classification problem is highly separable due to the informativeness of exact block-hash features, the workload is synthetic and favorable, and no end-to-end serving-engine validation was performed. The student functions as a cheap admission guard for exact-prefix cache probing—not as a semantic reuse model—and its primary practical benefit is eliminating the false-positive probe overhead of simpler fingerprint heuristics. The near-perfect classifier performance may reflect the ease of the synthetic task rather than a general property of the approach.

Deployment-level scientific closure requires: (1) replaying real labeled prompt traces through the same harness to measure opportunity density and false-positive rates under production traffic; (2) integration with an actual serving-engine prefix cache to measure end-to-end latency and compute savings; and (3) comparison against deterministic exact-prefix index lookup to determine whether the learned calibration adds value beyond hand-written thresholds. Until these steps are completed, the result supports only a "promising continue" research decision, not a deployment recommendation.

---

## Referenced Artifacts

| Artifact | Path |
|----------|------|
| Run notes | `run_notes.md` |
| Decision JSON | `.omx/project_decision.json` |
| Harness source | `src/reuse_fingerprint_student.py` |
| Sweep runner | `src/run_seed_sweep.py` |
| Test suite | `tests/test_reuse_fingerprint_student.py` |
| Smoke results | `results/smoke/results.json` |
| Calibration results | `results/calibration/results.json` |
| Stress results | `results/stress/results.json` |
| Seed sweep summary | `results/seed_sweep/summary.json` |
| Environment log | `logs/environment_probe.log` |
| Compilation log | `logs/py_compile.log` |
| Test log | `logs/test_final.log` |
| Smoke log | `logs/smoke_final.log` |
| Calibration log | `logs/calibration.log` |
| Stress log | `logs/stress.log` |
| Seed sweep log | `logs/seed_sweep.log` |
| Result digest log | `logs/result_digest.log` |
| Project metadata | `.omx/project.json`, `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260502T154148647090+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T154148647090+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T154148647090+0000/paper_manifest.json` |
