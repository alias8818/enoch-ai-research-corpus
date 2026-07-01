# Token Rent for Examples: Budget-Aware Evidence Packing with Ambiguity-Aware Backoff

> **AI Provenance Notice.** This draft was generated entirely by AI from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We present Token Rent for Examples, a greedy evidence-packing method that selects retrieved context under a fixed token budget by optimizing a marginal utility density signal penalized by a per-token rent and inter-evidence redundancy. In a deterministic offline synthetic benchmark spanning four task families (1,920 paired comparisons), token-rent packing achieved a +1.16 mean quality-proxy improvement and 20.97% token savings at matched quality versus retrieve-then-read top-k. In live llama.cpp prototype evaluations with Phi-4-mini-instruct (48 pairs) and Qwen2.5-7B-Instruct (72 pairs), a naive adaptive rent variant over-compressed underspecified multi-hop prompts, degrading answer F1. Introducing an ambiguity-aware sparse reserve with top-k backoff for underspecified queries recovered answer quality (mean answer-F1 delta +0.0035, strict citation delta +0.1667) while retaining 15.42% packer-token savings on the final Qwen2.5-7B suite. The result is positive but narrow: robust quality requires detecting when rent should back off rather than applying maximum compression uniformly. All evaluations use synthetic or semi-real benchmarks on local CPU-mode llama.cpp endpoints; external replication on production-grade models and real-world corpora is not yet established.

---

## 1. Introduction

Retrieval-augmented generation (RAG) systems conventionally select context by retrieving the top-k scored evidence chunks and concatenating them until a token budget is exhausted. This retrieve-then-read approach ignores the marginal utility density of each chunk relative to its token cost, leading to bloated prompts that include verbose, redundant, or low-yield evidence.

Token Rent for Examples hypothesizes that treating each token of context as having a rental cost—and selecting evidence by marginal estimated gain minus token rent and redundancy penalties—can produce shorter prompts with equal or better answer quality. The key design question is how to set the rent: too low and the packer behaves like top-k, too high and it over-compresses, evicting evidence required for multi-hop or underspecified queries.

This paper reports the design, iterative calibration, and evaluation of token-rent packing across three tiers of evidence: (1) a deterministic offline synthetic benchmark, (2) a small live inference harness on a 3.8B-parameter model, and (3) a semi-real live benchmark on a 7B-parameter model with progressively harder configurations. The final working mechanism combines adaptive rent estimation with an ambiguity-aware sparse reserve and top-k backoff for underspecified prompts.

---

## 2. Method

### 2.1 Baseline: Retrieve-then-Read Top-k

The baseline packer (`pack_topk`) sorts retrieved evidence chunks by retrieval score and greedily adds them to the prompt until the token budget is exhausted. This is the standard RAG packing strategy.

### 2.2 Token-Rent Packing

The token-rent packer (`pack_token_rent`) selects evidence by maximizing a marginal utility density criterion. For each candidate chunk $i$ with estimated gain $g_i$, token length $t_i$, and redundancy penalty $r_i$ (measured against already-selected evidence), the packer computes:

$$\text{score}_i = \frac{g_i - r_i}{t_i} - \lambda$$

where $\lambda$ is the per-token rent. Candidates with positive net score are added greedily in descending order until the budget is filled. The redundancy penalty ensures that chunks whose evidence is already covered by selected items are deprioritized.

A duplicate-evidence guard was added after an initial live run: candidates whose evidence set is already fully covered by selected items are skipped entirely, preventing the packer from selecting substantively identical chunks.

After selection, evidence is presented in retrieval-relevance order rather than selection order, preserving prompt layout stability for multi-part evidence.

### 2.3 Adaptive Rent Estimation

A fixed $\lambda$ requires manual tuning per task and budget. The adaptive variant (`pack_token_rent_adaptive`) estimates $\lambda$ from the candidate utility-density distribution at packing time:

1. Filter to retrieved, credible candidates (those above a credibility fraction of the best estimated gain).
2. Compute the median estimated utility density across the credible pool.
3. Scale by budget pressure (the ratio of total candidate tokens to the budget).
4. Use the resulting value as the per-token rent.

This removes dependence on a hand-picked rent coefficient. The density scale parameter (default 0.35) controls how aggressively the estimator converts observed density into rent.

### 2.4 Ambiguity-Aware Sparse Reserve with Top-k Backoff

Live evaluation revealed that adaptive rent over-compressed underspecified multi-hop prompts: it kept concise cited clauses but evicted the verbose combined answer-bearing chunks that the model relied on for extraction. The ambiguity-aware extension addresses this by:

1. **Sparse context reserve**: Reserving a small number of high-relevance evidence slots that are filled regardless of rent, ensuring that key citations survive compression.
2. **Underspecified top-k backoff**: Detecting underspecified queries (those with low retrieval score concentration or high ambiguity signals) and falling back to top-k packing for those cases, avoiding aggressive compression when the query is too vague for the rent mechanism to safely discriminate.

This design earns token savings on well-specified queries where rent can safely compress, while preserving full context on queries where compression risks information loss.

---

## 3. Results

Results are organized by evaluation tier, from offline synthetic to live semi-real benchmarks.

### 3.1 Offline Synthetic Benchmark (Deterministic Proxy)

The deterministic synthetic benchmark spans four task families (few-shot prompting, repo-QA, contract extraction, citation-heavy answering) with base, paraphrase, and underspecified query perturbations. Quality is measured by a proxy score derived from evidence coverage and estimated answer utility, not by model generation.

| Metric | Token-Rent vs. Top-k |
|--------|---------------------|
| Mean quality-proxy delta | +1.1571 |
| Token savings (quality within 2%) | 20.97% |
| Mean evidence recall delta | +0.1730 |
| Quality wins / losses / ties (±0.05) | 1582 / 243 / 95 |
| Packer latency (top-k / token-rent) | 0.0025 ms / 0.0256 ms |

Perturbation robustness remained positive across all variants: base (5.207 vs. 4.113), paraphrase (5.131 vs. 3.962), underspecified (5.037 vs. 3.829).

This is a toy simulation result: quality is a proxy, not a model-generated answer metric.

### 3.2 Live Inference Benchmark (Phi-4-mini, Smoke Test)

A small live harness placed both packers ahead of a local llama.cpp OpenAI-compatible endpoint running Phi-4-mini-instruct-Q4_K_M.gguf in CPU mode (`-ngl 0`). GPU offload produced nonsense generations on this build/model combination, so CPU mode was used for correctness.

| Metric | Token-Rent vs. Top-k |
|--------|---------------------|
| Pairs | 48 |
| Mean answer-F1 delta | +0.2107 |
| Mean answer exact delta | +0.5000 |
| Mean citation correctness delta | +0.5000 |
| Contract extraction exact match | 1.0000 vs. 0.5000 |
| Packer-token savings | 59.14% (208.25 vs. 538.31) |
| Server prompt tokens | 516.25 vs. 1236.38 |
| Answer-F1 wins / losses / ties (±0.02) | 24 / 0 / 24 |

This is a llama.cpp hook-prototype result on a small model with only 2 cases per task. The strong positive signal should be interpreted cautiously given the sample size.

### 3.3 Semi-Real Live Benchmark (Phi-4-mini)

The semi-real benchmark uses longer, document-like contexts with multi-hop citation requirements, duplicate/decoy evidence, and the same budget/perturbation controls.

**Default rent (0.0018):** Mixed. Token-rent saved 46.72% packer tokens and had a tiny positive F1 delta (+0.0051), but lost answer exactness (−0.1667) and strict all-citation correctness (−0.0833). Token-rent still admitted verbose combined evidence that confused underspecified multi-hop extraction.

**Higher rent (0.003):** Met live success gates.

| Metric | Token-Rent vs. Top-k |
|--------|---------------------|
| Mean answer-F1 delta | +0.1375 |
| Mean answer exact delta | +0.2083 |
| Mean strict all-citation delta | +0.3333 |
| Packer-token savings | 80.37% (116.75 vs. 613.50) |
| Server prompt tokens | 238.25 vs. 826.00 |
| Extraction exact match | 0.6667 vs. 0.1667 |
| Answer-F1 wins / losses / ties (±0.02) | 10 / 7 / 7 |

**Adaptive rent (default density scale 0.35):** Passed success gates but was more compressive than the manually tuned coefficient.

| Metric | Token-Rent vs. Top-k |
|--------|---------------------|
| Mean answer-F1 delta | +0.0780 |
| Mean answer exact delta | 0.0000 |
| Mean strict all-citation delta | +0.1250 |
| Packer-token savings | 88.12% (69.75 vs. 613.50) |
| Server prompt tokens | 182.25 vs. 826.00 |
| Extraction exact match | 0.6667 vs. 0.1667 |
| Answer-F1 wins / losses / ties (±0.02) | 10 / 10 / 4 |
| Model latency | 3299 ms vs. 4056 ms |

Adaptive rent saved more tokens than fixed rent (88.12% vs. 80.37%) but produced a smaller quality lift (+0.0780 vs. +0.1375 F1; +0.1250 vs. +0.3333 citations), indicating the estimator was slightly over-aggressive.

### 3.4 Semi-Real Live Benchmark (Qwen2.5-7B-Instruct)

The stronger Qwen2.5-7B-Instruct-Q4_K_M.gguf model (4.3 GiB) was acquired via resumable transfer and served through the same llama.cpp endpoint path in CPU mode.

**Adaptive rent (cases_per_task=1):** Did **not** meet the answer-F1 gate. Mean answer-F1 delta was −0.0574, answer-exact delta −0.0833, despite citation-all delta +0.2083 and 88.12% packer-token savings. Inspection revealed that adaptive rent over-compressed multi-hop contract evidence: it kept two concise cited clauses but evicted the verbose combined answer-bearing chunk that Qwen relied on for underspecified contract prompts.

**Fixed rent 0.0018 (cases_per_task=1):** Met gates with mean answer-F1 delta +0.0019, citation-all delta +0.2500, and 46.72% packer-token savings. Model latency improved from 1876 ms to 1573 ms.

**Fixed rent 0.0018 (cases_per_task=3, 72 pairs):** Mixed. Mean answer-F1 delta −0.0117, answer-exact delta −0.0417, citation-all delta +0.2222, packer-token savings 46.69%. Wins/losses/ties at ±0.02: 14/11/47. Most pairs were effectively tied, but the strict mean quality gate was slightly negative.

**Fixed rent 0.0005 (cases_per_task=3):** Did not recover quality (F1 delta −0.0205) and reduced savings to 30.45%, confirming that the default 0.0018 remains the better fixed setting on this suite.

### 3.5 Final Configuration: Ambiguity-Aware Sparse Reserve with Top-k Backoff (Qwen2.5-7B, 72 pairs)

The final evaluated configuration adds sparse context reserve and top-k backoff for underspecified prompts.

| Metric | Token-Rent vs. Top-k |
|--------|---------------------|
| Mean answer-F1 delta | +0.0035 |
| Mean answer exact delta | +0.0139 |
| Mean strict all-citation delta | +0.1667 |
| Packer-token savings | 15.42% |
| Server prompt tokens | 741.29 vs. 862.10 |
| Model latency | 788 ms vs. 1112 ms |
| Answer-F1 wins / losses / ties (±0.02) | 1 / 0 / 71 |

All three success gates (nonnegative answer-F1, nonnegative citation correctness, ≥15% prompt-token savings) were met. Compared to the prior adaptive bridge run (answer-F1 delta −0.0969, citation delta +0.1944, savings 77.78%), the ambiguity-aware mechanism recovered answer quality while retaining meaningful savings and improving citations by 16.7 percentage points.

The margin is narrow: the winning configuration earns savings primarily by compressing well-specified/sparse cases and deliberately backs off to top-k on underspecified prompts. The 71 out of 72 ties by answer-F1 indicate that the quality difference is small in both directions.

---

## 4. Limitations

1. **Small and synthetic benchmarks.** All live evaluations use semi-real benchmarks constructed by the project, not established external datasets. The largest live suite has only 72 paired comparisons across 4 task families with 3 cases per task. Statistical power is limited.

2. **Local CPU-mode inference only.** All live runs used llama.cpp in CPU mode (`-ngl 0`). GPU offload produced nonsense on the Phi-4-mini build. Results may differ on GPU-accelerated or cloud-hosted endpoints with different latency and tokenization characteristics.

3. **Narrow model coverage.** Only two models were tested: Phi-4-mini-instruct (3.8B, Q4_K_M) and Qwen2.5-7B-Instruct (7B, Q4_K_M). Behavior on larger or instruction-tuned models with different context-handling strategies is unknown.

4. **Rent calibration sensitivity.** The method is sensitive to the rent coefficient. Default adaptive rent over-compressed on Qwen2.5-7B and failed the answer-F1 gate. The ambiguity-aware backoff mechanism recovered quality, but the backoff heuristic itself has tuning parameters (sparse reserve size, ambiguity detection threshold) that were not systematically optimized.

5. **Narrow quality margin.** The final 72-pair result shows +0.0035 answer-F1 delta and 15.42% token savings—just above the 15% savings gate. This margin could evaporate on different data distributions or model versions.

6. **No external replication.** No results exist on standard benchmarks (e.g., Natural Questions, HotpotQA, MultiHop-RAG) or on production API endpoints. The claim of positive support is bounded to the project-local artifacts.

7. **Packer latency overhead.** Token-rent packing is approximately 10× slower than top-k in the offline harness (0.0256 ms vs. 0.0025 ms). While negligible in the current setup, this overhead may matter at very high query throughput.

8. **Duplicate-evidence and ordering fixes during evaluation.** The packer was patched mid-experiment (duplicate-evidence guard, relevance-ordered presentation). While regression tests confirm the offline benchmark metrics were preserved, the live results span pre- and post-fix configurations.

---

## 5. Reproducibility Checklist

| Item | Status |
|------|--------|
| Code available in project directory | Yes (`src/token_rent/packer.py`, `scripts/`) |
| Unit tests passing | Yes (10 passed in 0.02s, final check) |
| Deterministic offline benchmark reproducible | Yes (`PYTHONPATH=src python scripts/run_benchmark.py --cases-per-task 40`) |
| Live benchmark scripts available | Yes (`run_live_inference_benchmark.py`, `run_semireal_live_benchmark.py`) |
| Model files specified | Yes (Phi-4-mini-instruct-Q4_K_M.gguf, Qwen2.5-7B-Instruct-Q4_K_M.gguf) |
| llama.cpp build path specified | Yes (`llama-server`) |
| Server launch parameters documented | Yes (`--host <loopback-redacted> --port 18080 -c 4096 -ngl 0`) |
| Result CSV/JSON artifacts saved | Yes (see Referenced Artifacts) |
| Random seeds or determinism guarantee | Synthetic benchmark is deterministic; live inference depends on model sampling |
| Hardware environment documented | Partially (CPU mode, RSS and memory snapshots recorded) |
| External dataset dependencies | None (all benchmarks are project-generated) |

---

## 6. Conclusion

Token Rent for Examples demonstrates that budget-aware evidence packing with marginal utility density, per-token rent, and redundancy penalties can reduce prompt token usage while preserving or slightly improving answer quality and citation correctness. The core finding is qualified by three important caveats revealed through iterative evaluation:

First, naive adaptive rent estimation over-compresses underspecified multi-hop prompts, degrading answer quality on stronger models. Second, the ambiguity-aware sparse reserve with top-k backoff recovers quality but reduces savings to a narrow margin (15.42%). Third, all evidence is confined to synthetic/semi-real benchmarks on local CPU-mode llama.cpp endpoints with small sample sizes.

The current project artifacts support the finding that token-rent packing with ambiguity-aware backoff is a viable strategy in the tested setting. Whether it generalizes to production-scale RAG systems, larger models, and real-world corpora remains an open question requiring external replication.

---

## Referenced Artifacts

### Source code
- `src/token_rent/packer.py` — packer implementations (top-k, fixed-rent, adaptive-rent, ambiguity-aware)
- `src/token_rent/__init__.py` — public API exports
- `scripts/run_benchmark.py` — deterministic offline synthetic benchmark
- `scripts/run_live_inference_benchmark.py` — live inference harness (Phi-4-mini smoke test)
- `scripts/run_semireal_live_benchmark.py` — semi-real live benchmark with adaptive/fixed/ambiguity-aware modes
- `tests/test_packer.py` — unit and regression tests
- `tests/test_semireal_scoring.py` — scoring tests

### Result files
- `results/benchmark_summary.json` — offline synthetic benchmark summary
- `results/benchmark_rows.csv` — offline synthetic benchmark rows (1,920 pairs)
- `results/semireal_live_qwen25_7b_adaptive_sparse_topkbackoff_answerfield_cases3_summary.json` — final ambiguity-aware configuration summary
- `results/semireal_live_qwen25_7b_adaptive_sparse_topkbackoff_answerfield_cases3_rows.csv` — final ambiguity-aware rows (72 pairs)
- `results/semireal_live_qwen25_7b_adaptive_sparse_topkbackoff_answerfield_cases3_stdout.json` — final run stdout
- `results/semireal_live_qwen25_7b_adaptive_sparse_topkbackoff_answerfield_cases3_time.txt` — final run timing
- `results/semireal_live_qwen25_7b_adaptive_sparse_ambiguity_backoff_answerfield_cases3_summary.json` — intermediate ambiguity-aware variant
- `results/semireal_live_qwen25_7b_adaptive_sparse_ambiguity_backoff_answerfield_cases3_rows.csv`
- `results/semireal_live_qwen25_7b_adaptive_sparse_ambiguity_backoff_answerfield_cases3_stdout.json`
- `results/semireal_live_qwen25_7b_adaptive_sparse_ambiguity_backoff_answerfield_cases3_time.txt`
- `results/semireal_live_qwen25_7b_adaptive_ambiguity_backoff_answerfield_cases3_summary.json`
- `results/semireal_live_qwen25_7b_adaptive_ambiguity_backoff_answerfield_cases3_rows.csv`
- `results/semireal_live_qwen25_7b_adaptive_ambiguity_backoff_answerfield_cases3_stdout.json`
- `results/semireal_live_qwen25_7b_adaptive_ambiguity_backoff_answerfield_cases3_time.txt`
- `results/semireal_live_qwen25_7b_adaptive_bridge_answerfield_cases3_summary.json` — adaptive bridge (failed) variant
- `results/semireal_live_qwen25_7b_adaptive_bridge_answerfield_cases3_rows.csv`
- `results/semireal_live_qwen25_7b_adaptive_bridge_answerfield_cases3_stdout.json`
- `results/semireal_live_qwen25_7b_adaptive_bridge_answerfield_cases3_time.txt`
- `results/semireal_live_qwen25_7b_adaptive_bridge_g049_cases3_time.txt`
- `results/semireal_live_qwen25_7b_adaptive_bridge_g049_cases3_stdout.json`

### Project metadata and decision artifacts
- `run_notes.md` — detailed execution log
- `.omx/project_decision.json` — final project decision (finalize_positive, confidence: medium)
- `.omx/metrics.json` — session metrics
- `papers/.../claim_ledger.json` — placeholder/blocked claim ledger; strict claim/evidence audit is blocked because no structured claims were extracted
- `papers/.../evidence_bundle.json` — structured evidence bundle
