# Outlier Singleton Protection for Compact Evidence Retention Under Tight KV Budgets

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, evidence bundles, decision JSON, benchmark logs). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We investigate a failure mode in online key-value (KV) and prompt-retention policies: when only high-frequency, high-utility, or role-salient evidence is retained under a tight budget, the single record that answers a query can be dropped if it is a statistical outlier. We propose a lightweight outlier singleton protection mechanism that pins statistically extreme singleton spans before normal utility ranking. In a 200-case synthetic retention benchmark with 64 records per case, adding a robust-z-score outlier singleton pin raised exact target-retrieval accuracy from 0.230 (role/utility baseline) to 1.000 at a 4/64 (6.25%) retention budget, matching the oracle upper bound across all tested budgets. In a 12-case compact-prompt generation check using Qwen2.5-7B-Instruct (Q4_K_M) via llama.cpp, the singleton-protected compact prompt achieved 0.750 exact accuracy—matching full-context accuracy—while using approximately 13.4% of full-context prompt tokens and 35.6% of full-context latency. The role-only utility compact prompt achieved only 0.250 exact accuracy, omitting the target outlier from two-thirds of prompts. These results support the mechanism for compact span selection and replay, but do not yet validate a production live-KV compaction implementation. The generation sample is small (12 cases), and the synthetic outlier distribution is intentionally controlled; real tasks may present multiple ambiguous outliers or non-numeric singleton salience.

## 1. Introduction

Long-context inference under memory or compute budgets increasingly relies on selective retention: only a subset of key-value (KV) cache entries or prompt spans are kept active while the rest are evicted or not loaded. Common retention heuristics—recency, frequency, attention-weighted utility, or role-based salience—favor records that appear repeatedly or occupy structurally important positions.

A predictable failure mode arises when the answer depends on a single record that is a statistical outlier: it appears once, carries no frequency signal, and may lack role salience distinct from its neighbors. Standard utility rankings can systematically deprioritize such a record, causing the retained context to miss the one span needed for correct extraction.

We hypothesize that a small outlier singleton protection reserve—pinning spans whose numeric values fall outside a robust median/MAD envelope before normal utility ranking—can eliminate this failure mode without increasing the overall retention budget. This paper reports on a two-stage evaluation: (1) a dependency-light synthetic retention simulator over 200 cases, and (2) a compact-prompt generation check using a local Qwen2.5-7B-Instruct model through llama.cpp on 12 cases.

The two stages serve distinct evidentiary roles. The simulator is a toy/proxy that measures whether the retention policy selects the correct record, independent of any model. The llama.cpp compact-generation check is a hook-prototype that tests whether the retained spans, when formatted as a compact prompt, actually support correct generation. Neither stage constitutes a production validation of live KV cache compaction or in-place cell movement.

## 2. Method

### 2.1 Synthetic Retention Simulator

Each test case contains 64 structured records. One target record has a pressure value drawn far outside the case's robust median/MAD envelope; every record has unique-looking IDs and codes, so singleton-token rarity by itself is intentionally insufficient to identify the target. The query asks for the singleton pressure outlier's `record_id` and `code`.

Six retention policies were tested under identical retained-record budgets:

- **FIFO recent** (`fifo_recent`): recency baseline, evicting oldest records first.
- **Random** (`random`): seeded random baseline.
- **Frequency utility** (`frequency_utility`): score favoring repeated boilerplate/schema tokens.
- **Role utility** (`role_utility`): typed-record role score plus utility.
- **Singleton protected** (`singleton_protected`): role/utility plus a strong pin for robust-z-score outlier singleton spans, with a rare-token boost applied only after the numeric outlier gate.
- **Oracle** (`oracle_target`): upper bound that always retains the target.

The outlier detection uses a robust z-score: the deviation of a record's numeric field from the median, scaled by the median absolute deviation (MAD). Records exceeding a threshold are flagged as outlier singletons and pinned before the utility ranking allocates the remaining budget.

Three experimental runs were executed:

1. **Smoke test**: 4 cases, 32 records, noise tokens 64, budgets 3 and 5, seed 34.
2. **Calibration**: 24 cases, 64 records, noise tokens 128, budgets 4, 6, 8, seed 35.
3. **Main run**: 200 cases, 64 records, noise tokens 192, budgets 4, 6, 8, 12, seed 36.

### 2.2 Local Model Compact-Generation Check

To move beyond the retention proxy and test whether retained spans actually support correct generation, a compact-prompt harness was built using a local Qwen2.5-7B-Instruct model (Q4_K_M quantization) served via llama.cpp with CUDA offload:

```
llama-server -m Qwen2.5-7B-Instruct-Q4_K_M.gguf \
  --host <loopback-redacted> --port 18086 -c 4096 -ngl 99 -fa on --parallel 1 --no-webui
```

Three prompt configurations were compared over 12 cases at a 4/64 retained-record budget:

- **role_utility compact**: 4 records selected by role/utility ranking.
- **singleton_protected compact**: 4 records selected by singleton-protected ranking.
- **full_context**: all 64 records included (no retention budget applied).

The model was asked to generate a JSON answer containing the target outlier's `record_id` and `code`. Exact accuracy required both fields to match the ground truth. This is a hook-prototype check: the compact prompt is constructed from selected spans and replayed through the model, which is not equivalent to in-place KV cache compaction or repositioning.

## 3. Results

### 3.1 Synthetic Retention Benchmark (200 cases × 64 records)

| Retained Budget | FIFO | Random | Frequency | Role | Singleton-Protected | Oracle |
|---:|---:|---:|---:|---:|---:|---:|
| 4 / 64 (6.25%) | 0.035 | 0.085 | 0.230 | 0.230 | 1.000 | 1.000 |
| 6 / 64 (9.38%) | 0.075 | 0.115 | 0.300 | 0.300 | 1.000 | 1.000 |
| 8 / 64 (12.5%) | 0.085 | 0.140 | 0.340 | 0.340 | 1.000 | 1.000 |
| 12 / 64 (18.75%) | 0.120 | 0.210 | 0.425 | 0.425 | 1.000 | 1.000 |

The singleton-protected policy matches oracle accuracy at every budget level. The frequency and role utility policies improve over FIFO and random baselines but plateau well below perfect retrieval even at 12/64 (18.75%) retention, where they reach only 0.425 exact accuracy. This confirms the hypothesized failure mode: utility-based rankings systematically deprioritize the one-off outlier.

Simulator resource usage was minimal: wall time 3.80 s, CPU time 3.80 s, max RSS 18,296 KB. The simulator is CPU-only; the GPU was idle throughout (`nvidia-smi` reported 0% utilization).

### 3.2 Qwen2.5-7B Compact-Generation Check (12 cases)

| Policy | Target in Prompt | Exact Accuracy | Mean Prompt Tokens | Mean Latency |
|---|---:|---:|---:|---:|
| role_utility (4/64) | 0.333 | 0.250 | 379.25 | 0.881 s |
| singleton_protected (4/64) | 1.000 | 0.750 | 379.33 | 0.820 s |
| full_context (64/64) | 1.000 | 0.750 | 2830.50 | 2.306 s |

The singleton-protected compact prompt matched full-context exact accuracy (0.750) while using approximately 13.4% of full-context prompt tokens and 35.6% of full-context latency. The role-only utility compact prompt achieved only 0.250 exact accuracy because it omitted the target outlier from 8 of 12 prompts; when the target was absent, the model could not extract it.

The fact that both singleton-protected compact and full-context achieve 0.750 rather than 1.000 indicates that model generation errors occur even when the target is present. This is an important qualification: outlier singleton protection solves the retention problem, not all generation errors.

### 3.3 Mixed and Negative Observations

- **Full-context accuracy is not perfect.** At 0.750 exact accuracy on 12 cases, full context leaves room for model-level errors (misreading fields, format failures). Singleton protection does not address these.
- **Frequency and role utility are indistinguishable.** Across all budgets, frequency utility and role utility produce identical exact accuracy (0.230, 0.300, 0.340, 0.425). Adding role information on top of frequency provided no benefit for this task structure.
- **FIFO and random baselines remain poor even at higher budgets.** At 12/64 retention, FIFO achieves only 0.120 and random 0.210, indicating that the target outlier has no positional or random-selection advantage.
- **Compact prompt token counts are nearly identical between role_utility and singleton_protected.** Mean prompt tokens were 379.25 and 379.33 respectively, confirming that the singleton pin does not increase prompt size—it swaps a non-outlier record for the outlier record within the same budget.

## 4. Limitations

1. **Synthetic outlier distribution.** The benchmark uses a controlled design where exactly one record per case is a clear numeric outlier. Real tasks may feature multiple ambiguous outliers, non-numeric singleton salience, or outliers that are extreme along dimensions not captured by a univariate robust z-score.

2. **Compact prompt replay, not live KV compaction.** The local-model check constructs a compact prompt from selected spans and replays it through the model. This is not equivalent to in-place KV cache cell movement, compaction, or repositioning. A true cache-manager implementation requires exact token-span metadata and contiguous KV compaction or replay, and sparse hole-punched KV caches are known to be fragile.

3. **Small generation sample.** The Qwen2.5-7B compact-generation check covers only 12 cases. The 0.750 exact accuracy for both singleton-protected and full-context conditions is consistent with parity between the two, but the confidence interval around a 12-case binomial proportion is wide (approximately ±0.22 at 95% coverage). Larger generation validation is needed before production claims.

4. **Single model and quantization.** Results are specific to Qwen2.5-7B-Instruct at Q4_K_M quantization. Other models, sizes, or quantization levels may exhibit different generation error profiles.

5. **No comparison with heavy-hitter KV baselines.** The experiment compares against frequency, role, FIFO, and random baselines but does not include H2O-style or SnapKV-style heavy-hitter eviction policies, which may partially address the same failure mode through different mechanisms.

6. **No accessible Notion page body.** The project's Notion page body was not accessible through the public URL; the experiment was derived from the project title and mission statement rather than a detailed specification.

7. **GPU memory telemetry incomplete.** The `nvidia-smi` memory field was reported as `[N/A]` during the Qwen run, so VRAM usage judgments rely on `/proc/meminfo` and logs rather than direct GPU memory counters.

8. **Swap unavailable.** Swap was intentionally disabled (`SwapFree: 0 kB`), so the memory posture reflects a no-swap configuration that may not generalize to all deployment environments.

9. **Claim ledger audit status is blocked.** The claim ledger for this paper draft contains no structured claims and its audit status is `blocked_empty_claims`. The paper should not be treated as having passed a strict claim/evidence audit.

## 5. Reproducibility Checklist

- **Source code**: `src/outlier_singleton_protection.py` (simulator), `src/outlier_singleton_llama_compact.py` (compact-generation harness).
- **Random seeds**: Smoke (34), calibration (35), main (36). The compact-generation harness does not accept an explicit seed; llama.cpp sampling may introduce non-determinism.
- **Model**: `bartowski/Qwen2.5-7B-Instruct-GGUF/Qwen2.5-7B-Instruct-Q4_K_M.gguf`, served via llama.cpp with `-c 4096 -ngl 99 -fa on --parallel 1`.
- **Hardware**: GB10 host, CPU-only for simulator; llama.cpp with CUDA offload for generation. Simulator max RSS 18 MB; system RAM approximately 117 GB available.
- **Result files**: `results/outlier_singleton_smoke.{json,csv}`, `results/outlier_singleton_calibration.{json,csv}`, `results/outlier_singleton_main.{json,csv}`, `results/outlier_singleton_llama_compact_qwen12.{json,csv}`.
- **Log files**: `logs/outlier_singleton_smoke.log`, `logs/outlier_singleton_calibration.log`, `logs/outlier_singleton_main.log`, `logs/outlier_singleton_llama_compact_qwen12.log`, `logs/services/llama_server_18086.log`.
- **Metrics**: `.omx/research_metrics.json`.
- **Decision record**: `.omx/project_decision.json`.
- **Run notes**: `run_notes.md`.
- **Exact commands**: Listed in Section 2 and in `run_notes.md`; all are reproducible from the source files and specified seeds.
- **Evidence stage classification**: Simulator results are toy/proxy retention measurements. Llama.cpp results are hook-prototype compact-prompt generation checks. No CUDA copy calibration or final production validation was performed.

## 6. Conclusion

Outlier singleton protection—pinning spans whose numeric values exceed a robust z-score threshold before normal utility ranking—eliminates a systematic retention failure in which generic utility rankings drop the one-off outlier record needed to answer a query. In a 200-case synthetic benchmark, the mechanism raised exact target-retrieval accuracy from 0.230 to 1.000 at a 6.25% retention budget, matching the oracle upper bound across all tested budgets. In a 12-case compact-prompt generation check with Qwen2.5-7B-Instruct, the singleton-protected compact prompt matched full-context exact accuracy (0.750) while using approximately 13.4% of the prompt tokens and 35.6% of the latency.

These results support the mechanism as a viable retention feature for compact evidence and KV selection under tight budgets, but with clear caveats. The positive evidence is for selecting and replaying compact spans, not for in-place live KV compaction. The generation sample is small (12 cases), and the parity between singleton-protected compact and full-context accuracy at 0.750 is a point estimate with wide uncertainty. The synthetic outlier distribution is controlled and may not reflect the ambiguity of real-world tasks. The claim ledger for this draft has not passed audit. The recommended next step is an engineering validation that implements the same pinning rule inside a true KV compaction or replay path, with comparisons against role/utility-only policies, H2O/SnapKV-style heavy-hitter baselines, and full context on larger long-context extraction workloads.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Simulator script | `src/outlier_singleton_protection.py` |
| Compact-generation harness | `src/outlier_singleton_llama_compact.py` |
| Smoke results | `results/outlier_singleton_smoke.json`, `results/outlier_singleton_smoke.csv` |
| Calibration results | `results/outlier_singleton_calibration.json`, `results/outlier_singleton_calibration.csv` |
| Main proxy results | `results/outlier_singleton_main.json`, `results/outlier_singleton_main.csv` |
| Qwen generation results | `results/outlier_singleton_llama_compact_qwen12.json`, `results/outlier_singleton_llama_compact_qwen12.csv` |
| Simulator smoke log | `logs/outlier_singleton_smoke.log` |
| Calibration log | `logs/outlier_singleton_calibration.log` |
| Main run log | `logs/outlier_singleton_main.log` |
| Qwen generation log | `logs/outlier_singleton_llama_compact_qwen12.log` |
| Llama server log | `logs/services/llama_server_18086.log` |
| Research metrics | `.omx/research_metrics.json` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Claim ledger | `papers/source-record-redacted-20260430T021348320117+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T021348320117+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T021348320117+0000/paper_manifest.json` |
