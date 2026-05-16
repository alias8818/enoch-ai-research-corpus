# Context Skeleton Distillation: Deterministic Compression of Instruction-Heavy Agent Contexts

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, benchmark logs, metrics JSON, and decision records). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has validated the claims herein.

---

## Abstract

We investigate Context Skeleton Distillation (CSD), a deterministic, model-free method for compressing long instruction-heavy contexts by retaining structurally actionable lines—headings, constraints, commands, file paths, identifiers, URLs, and normative instructions—while discarding prose filler. In a local prototype benchmark over 15 documents (3 real agent-instruction files and 12 synthetic long-context manuals with planted critical facts), CSD achieves mean critical-fact exact-match recall of 0.741 at a mean compression ratio of 0.141, compared to 0.059 for naive head truncation. However, a simpler ranked structural extractor baseline achieves slightly higher fact recall (0.770) and skeleton-line recall (0.742 vs. 0.694) at a marginally higher compression ratio (0.151). CSD matches the ranked extractor at moderate budgets (15–20%) and surpasses it at the 30% budget (0.936 vs. 0.898 fact recall), but underperforms at low budgets (8–10%). These results establish the feasibility of deterministic skeleton extraction for context compression but do not demonstrate superiority over simpler structural ranking, nor do they measure downstream LLM task accuracy. We report the full budget-sensitive tradeoff and identify necessary next steps for validation.

## 1. Introduction

Long-context language model agents routinely operate with instruction sets, project documentation, and session transcripts that exceed practical token budgets. Naive truncation—retaining the first *N* tokens—discards critical facts that often appear late in structured documents, such as constraint statements in appendices or file paths in configuration sections. Model-dependent prompt compression methods, including coarse-to-fine token pruning and information-theoretic rate-distortion approaches, can reduce context length but introduce inference dependency, non-determinism, and API cost.

We explore whether a purely deterministic, model-free structural extraction pass can preserve critical facts more effectively than head truncation at comparable token budgets. The motivating intuition is that instruction-heavy contexts possess a "skeleton" of actionable lines—headings, normative directives, commands, paths, URLs, and identifiers—that carries disproportionate information for agent task execution. Retaining this skeleton while discarding surrounding prose should yield better fact retention per token spent.

This work is a local prototype feasibility study. We compare three methods—head truncation, ranked structural extraction, and density-aware context skeleton distillation—across five compression budgets on a mixed corpus of real agent instructions and synthetic manuals with oracle-planted facts. We report exact-match recall of critical facts and actionable skeleton lines, compression ratios, and throughput, and we characterize honestly where CSD underperforms the simpler baseline.

## 2. Method

### 2.1 Corpus

The benchmark corpus consists of 15 documents:

- **3 real documents:** Local agent session instructions (`AGENTS.md`), an initial prompt template (`prompts/initial.md`), and a resume prompt template (`prompts/resume.md`).
- **12 synthetic manuals:** Programmatically generated long-context documents containing filler prose with planted critical facts distributed throughout, including after substantial filler sections. This design ensures that head truncation will miss facts placed late in the document.

Critical facts are declared in an oracle list per document, enabling exact-match recall evaluation.

### 2.2 Compression Methods

Three methods are compared:

1. **Head Truncate (`head_truncate`):** Retain the first *N* approximate tokens of the source document, where *N* = budget fraction × original token count. This is the simplest baseline and represents common practice.

2. **Ranked Extract (`ranked_extract`):** Score each line for structural signals—headings (markdown `#` markers), normative words (e.g., "must," "shall," "required"), file paths, URLs, shell commands, and code identifiers. Extract the top-scoring lines up to the token budget, preserving original document order.

3. **Context Skeleton Distillation (`context_skeleton`):** Uses the same structural scoring signals as ranked extract but applies density-aware selection. The objective is to preserve compact, coherent skeleton structures (e.g., a heading plus its immediate normative children) rather than independently top-scoring lines. This aims to produce more readable and contextually coherent compressed output at the cost of potentially skipping some high-scoring isolated lines.

### 2.3 Metrics

- **Fact recall:** Exact-match recall of oracle-declared critical facts in the compressed output. A fact is counted as recalled if its string appears verbatim in the compressed context.
- **Skeleton-line recall:** Exact preservation of lines classified as actionable (normative, path, command, or identifier lines) in the compressed output.
- **Compression ratio:** Approximate token count of compressed output divided by approximate token count of original document.
- **Elapsed time:** Wall-clock milliseconds per compression operation.

### 2.4 Experimental Design

The full benchmark runs each of the 15 documents at 5 budget fractions (8%, 10%, 15%, 20%, 30%) with 5 repeats per configuration, yielding 1,125 total measurement rows. Repeats control for any non-determinism in token counting, which uses an approximate whitespace-based tokenizer. The benchmark script is a single self-contained Python file with no external model or API dependencies.

## 3. Results

### 3.1 Aggregate Performance

Across all budgets and documents (1,125 rows), the three methods yield the following aggregate means:

| Method | Mean Fact Recall | Mean Skeleton-Line Recall | Mean Compression Ratio | Mean Elapsed (ms) |
|---|---:|---:|---:|---:|
| head_truncate | 0.0587 | 0.0000 | 0.1682 | 0.073 |
| ranked_extract | 0.7698 | 0.7424 | 0.1505 | 0.823 |
| context_skeleton | 0.7409 | 0.6940 | 0.1414 | 0.865 |

Both structural methods dramatically outperform head truncation on fact recall (approximately 13× and 12.6× improvement, respectively). Head truncation achieves zero skeleton-line recall because actionable lines are distributed throughout documents and rarely concentrated at the beginning.

CSD achieves a lower mean compression ratio (0.141 vs. 0.151), meaning it uses fewer source tokens per unit of compressed output, but this comes at the cost of slightly lower fact and skeleton-line recall compared to ranked extract. This is a negative result for the hypothesis that density-aware selection would unconditionally improve over independent line ranking.

### 3.2 Budget-Sensitive Tradeoffs

The budget dimension reveals a nuanced picture:

| Budget | Head Fact Recall | Ranked Fact Recall | CSD Fact Recall | CSD Compression Ratio |
|---:|---:|---:|---:|---:|
| 8% | 0.049 | 0.418 | 0.407 | 0.073 |
| 10% | 0.049 | 0.738 | 0.567 | 0.081 |
| 15% | 0.049 | 0.898 | 0.898 | 0.125 |
| 20% | 0.060 | 0.898 | 0.898 | 0.170 |
| 30% | 0.087 | 0.898 | 0.936 | 0.257 |

Key observations:

- **At low budgets (8–10%), ranked extract outperforms CSD** on fact recall (0.418 vs. 0.407 at 8%; 0.738 vs. 0.567 at 10%). The density-aware selection in CSD sacrifices some high-scoring isolated facts in favor of preserving coherent skeleton segments, which is counterproductive when the budget is too tight to accommodate many segments.
- **At moderate budgets (15–20%), the methods converge** on fact recall (both 0.898), though ranked extract retains a skeleton-line recall advantage (0.830 vs. 0.814 at 15%).
- **At the highest tested budget (30%), CSD surpasses ranked extract** on fact recall (0.936 vs. 0.898), suggesting that density-aware selection becomes advantageous when sufficient budget exists to capture most skeleton structures while also including peripheral facts within preserved segments.

Head truncation's fact recall remains near or below 0.087 across all budgets, confirming that critical facts in this corpus are distributed throughout documents rather than concentrated at the beginning.

### 3.3 Throughput and Resource Usage

All methods run in under 1 ms per document on average. The full benchmark processed 1,125 rows at approximately 780 rows per second. Memory telemetry from the full run shows 122 GB available on a 127 GB system with zero swap, indicating no memory pressure. The benchmark is a single-threaded Python script with no GPU, API, or model dependencies.

## 4. Limitations

1. **No downstream LLM task evaluation.** The primary metrics are exact-match fact recall and skeleton-line recall against an oracle. These do not measure whether a compressed context enables an LLM to answer questions or complete tasks as accurately as the full context. A compression method that preserves facts but disrupts their coherence could perform worse in practice.

2. **Synthetic corpus with exact-match oracle.** Twelve of fifteen documents are synthetic manuals with planted facts. Real-world agent contexts may distribute critical information differently, and exact-match recall does not capture paraphrased or implicit fact retention.

3. **CSD underperforms ranked extract at low budgets.** The density-aware selection mechanism in the current CSD variant reduces fact recall relative to the simpler ranked extractor at 8–10% budgets. This is a negative result for CSD's design hypothesis at those operating points.

4. **Approximate tokenization.** Token counting uses a whitespace-based approximation rather than a specific tokenizer (e.g., BPE). Compression ratios may shift under exact tokenization for a given model.

5. **Small real-document sample.** Only 3 of 15 documents are real agent-instruction files. The remaining 12 are synthetic, which may not reflect the distribution of structural signals in production contexts.

6. **No evaluation on multi-file repositories or session transcripts.** The corpus consists of individual documents rather than the concatenated multi-file contexts that agents typically encounter.

7. **Private Notion page content unavailable.** The project's Notion page was not accessible through local artifacts; research relied on prompt and project metadata for framing.

## 5. Reproducibility Checklist

- **Benchmark script:** `scripts/csd_benchmark.py` — self-contained Python 3 script, no external package dependencies beyond the standard library.
- **Syntax validation:** `python3 -m py_compile scripts/csd_benchmark.py` passed cleanly (log at `artifacts/logs/py_compile.log`).
- **Corpus:** 3 local files (`AGENTS.md`, `prompts/initial.md`, `prompts/resume.md`) plus 12 synthetic documents generated deterministically within the script.
- **Randomization:** 5 repeats per configuration; approximate tokenization is deterministic given the same input.
- **Hardware:** Single machine, 127 GB RAM, 0 swap, no GPU required.
- **Metrics artifacts:** Raw JSON and TSV at `artifacts/metrics/metrics_full.json` and `artifacts/metrics/metrics_full.tsv`.
- **Run logs:** `artifacts/logs/full.log` for the primary run; `artifacts/logs/smoke_v3.log` and `artifacts/logs/calibrate.log` for preliminary runs.
- **Decision record:** `.omx/project_decision.json` contains the full evidence bundle including per-budget breakdowns and memory telemetry.

## 6. Conclusion

Context Skeleton Distillation is feasible as a deterministic, model-free context compressor for instruction-heavy agent contexts. It achieves substantially better critical-fact retention than naive head truncation (0.741 vs. 0.059 mean fact recall) at a lower mean compression ratio (0.141 vs. 0.168). However, the current CSD variant does not outperform a simpler ranked structural extractor in aggregate (0.741 vs. 0.770 fact recall; 0.694 vs. 0.742 skeleton-line recall). The density-aware selection in CSD helps at higher budgets (≥15%) and yields a fact-recall advantage at 30% budget (0.936 vs. 0.898), but hurts at low budgets (8–10%) where independent line selection is more effective.

These results establish that deterministic structural extraction is a viable approach to context compression, but they do not establish CSD's superiority over simpler ranked extraction. The critical next step is downstream LLM task evaluation: measuring whether compressed contexts preserve agent task success rates, and whether CSD's coherence advantage (if any) translates into better LLM performance despite slightly lower raw fact recall. If density-aware selection does not confer a downstream advantage, the simpler ranked extractor should be preferred on grounds of parsimony and recall.

---

## Referenced Artifacts

| Artifact | Path | Description |
|---|---|---|
| Benchmark script | `scripts/csd_benchmark.py` | Self-contained Python benchmark; no external dependencies |
| Full run metrics (JSON) | `artifacts/metrics/metrics_full.json` | 1,125-row primary result set |
| Full run metrics (TSV) | `artifacts/metrics/metrics_full.tsv` | Tab-separated version of full metrics |
| Smoke metrics | `artifacts/metrics/metrics_smoke.json` | Preliminary smoke-test metrics |
| Calibration metrics | `artifacts/metrics/metrics_calibrate.json` | Calibration run metrics |
| Full run log | `artifacts/logs/full.log` | Console output from primary benchmark run |
| Smoke run log | `artifacts/logs/smoke_v3.log` | Console output from smoke test |
| Calibration log | `artifacts/logs/calibrate.log` | Console output from calibration run |
| Syntax check log | `artifacts/logs/py_compile.log` | Python syntax validation output |
| Decision record | `.omx/project_decision.json` | Full evidence bundle, per-budget breakdowns, memory telemetry |
| Run notes | `run_notes.md` | Research log with hypothesis, commands, and interpretation |
| Example CSD output (10%) | `artifacts/metrics/*_csd_10pct.md` | Sample distilled contexts at 10% budget |
| Example CSD output (20%) | `artifacts/metrics/*_csd_20pct.md` | Sample distilled contexts at 20% budget |
| Claim ledger | `papers/.../claim_ledger.json` | Claim audit record (empty claims; model-authored limitation noted) |
| Evidence bundle | `papers/.../evidence_bundle.json` | Source and run identifiers |
| Paper manifest | `papers/.../paper_manifest.json` | Generation metadata and writer provider record |
