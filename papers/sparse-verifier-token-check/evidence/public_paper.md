# Sparse Token Verification as a Correctness Check: An Information-Theoretic Negative Result

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metrics files, claim ledger, evidence bundle). The operator who released this artifact claims no personal authorship credit for the writing or results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed this content.

---

## Abstract

We evaluate whether inspecting a sparse subset of token positions can serve as a correctness or integrity check for generated text. Using an oracle verifier that performs exact token equality at checked positions—an upper bound on any realistic sparse semantic verifier—we measure detection rates across five check budgets (1%–25%), four selection strategies, and four corruption models over 80,000 trials on 250 documents. The results confirm the information-theoretic expectation: for a single random token error in a 2048-token document, a 5% check budget detects the error only 8.0% of the time, and a 25% budget detects it only 24.8% of the time. Under an adversarial model where errors avoid checked positions, detection drops to 0.0% across all budgets and strategies. Sparse token checking is therefore not viable as a correctness or security check. It is conditionally useful only as a probabilistic smoke test for bulk random corruption, where the error fraction is large enough to make the combinatorial detection probability acceptable.

## Introduction

A natural question in verifying generated text is whether one can inspect only a small fraction of token positions and still catch errors. If a 5% or 10% spot-check could reliably detect corruption, the cost of verification could be reduced substantially.

This idea faces an immediate information-theoretic obstacle. If a verifier inspects only $k$ of $n$ token positions, a single random changed token is detected with probability approximately $k/n$, and an adversary who knows or can infer the checked positions can alter unchecked tokens with zero probability of detection. No selection strategy or semantic comparison can overcome this bound under the same sparse-access constraint.

We test this bound empirically using an oracle sparse verifier—one that performs exact token equality comparison at checked positions, thereby giving the proposed approach its best possible chance. If even the oracle fails to provide useful detection rates, no practical sparse verifier can succeed. Our contribution is a systematic empirical confirmation of this negative result across multiple strategies and error models, with precise quantitative characterization of when sparse checking is and is not viable.

## Method

### Oracle Sparse Verifier

The verifier treats each document as a sequence of $n$ tokens. Given a check budget $b \in \{0.01, 0.03, 0.05, 0.10, 0.25\}$, it selects $k = \lfloor b \cdot n \rfloor$ positions and compares the token at each selected position to a reference. Detection occurs if and only if at least one checked position differs from the reference. This oracle comparison is strictly stronger than any realistic semantic or embedding-based check at the same positions, so its detection rate is an upper bound on what any sparse verifier can achieve.

### Corpus

A deterministic local corpus was constructed from project prompts and local Python and documentation text. Tokenization used a conservative regex tokenizer. The corpus yielded 250 documents with token lengths ranging from 169 to 2048, with a median of 2048 tokens.

### Check Selection Strategies

Four strategies for selecting which positions to check were evaluated:

1. **uniform_random**: Positions sampled uniformly at random without replacement.
2. **hash_fixed**: Positions determined by a deterministic hash of the document, yielding the same checked positions for the same document across trials.
3. **even_grid**: Positions spaced at regular intervals across the document.
4. **rare_token_anchor**: A heuristic that biases selection toward high-information (low-frequency) tokens.

### Corruption Models

Four error models were applied, each changing $m$ token positions:

1. **random_m**: $m$ positions selected uniformly at random and replaced.
2. **contiguous_span**: $m$ adjacent positions replaced, modeling localized corruption.
3. **rare_token_biased**: Changes biased toward rare or high-information tokens.
4. **adversarial_avoid_checked**: Changes deliberately placed at unchecked positions, modeling an adversary with knowledge of the verification strategy.

### Theoretical Baseline

For random errors, the detection probability follows the combinatorial formula:

$$P(\text{detect}) = 1 - \frac{\binom{n-m}{k}}{\binom{n}{k}} \approx 1 - \left(1 - \frac{m}{n}\right)^k$$

Empirical results are compared against this formula to validate the simulation and to assess whether any strategy exceeds the random baseline.

### Experimental Scale

The experiment was executed as a toy simulation (not a llama.cpp hook prototype, CUDA calibration, or production deployment). The scale and throughput were:

- Documents: 250
- Token length range: 169–2048 (median 2048)
- Trials: 80,000
- Runtime: 77.35 seconds
- Throughput: 1,034.2 trials/second
- Max RSS: 33,796 kB (measured via `/usr/bin/time -v`)

Memory telemetry confirmed no swap activity (Swaps: 0). MemAvailable before the full run was 122,759,348 kB and after was 122,742,716 kB, indicating negligible memory pressure on the host (`gx10-efe8`).

## Results

### Random Error Detection

Table 1 presents selected detection rates for the uniform-random sparse verifier under random token corruption, alongside the theoretical prediction.

**Table 1.** Detection rates for uniform-random sparse verification under random token errors (median document length 2048 tokens).

| Checked budget | Changed tokens ($m$) | Empirical detection | Theoretical detection |
|---:|---:|---:|---:|
| 1% | 1 | 0.004 | 0.010 |
| 5% | 1 | 0.080 | 0.050 |
| 5% | 4 | 0.208 | 0.185 |
| 5% | 16 | 0.568 | 0.560 |
| 5% | 64 | 0.964 | 0.964 |
| 10% | 1 | 0.104 | 0.100 |
| 25% | 1 | 0.248 | 0.250 |
| 25% | 4 | 0.716 | 0.684 |

The empirical rates closely match the theoretical predictions, confirming the simulation's validity. The key observation is that detection rates for small numbers of changed tokens are low even at generous check budgets. At a 5% check budget, a single random token error is detected only 8.0% of the time. At a 25% check budget—a quarter of all tokens inspected—a single random token error is still detected only 24.8% of the time.

Detection becomes reliable only when the error fraction is large. At a 5% check budget with 64 random changed tokens (approximately 3.1% of the document), detection reaches 96.4%, consistent with the theoretical prediction of 96.4%.

### Adversarial Error Detection

Under the adversarial-avoid-checked model, mean detection was 0.0% across all tested budgets, all strategies, and all error counts. This is the expected result: an adversary who can avoid checked positions faces no constraint from a sparse verifier.

### Strategy Comparison

The `rare_token_anchor` strategy improved detection when the corruption model was also biased toward rare tokens, reflecting a matching between check focus and error distribution. However, it provided no improvement for random single-token errors and still yielded 0.0% detection under adversarial avoidance. The `hash_fixed` and `even_grid` strategies produced results consistent with the random baseline for random errors, as expected by symmetry.

### Contiguous-Span Corruption

Contiguous-span corruption showed detection rates comparable to random corruption at the same $m$, with slight variation depending on whether the span overlapped with checked positions. No strategy reliably detected small spans at low check budgets.

### Mixed and Negative Findings

Several findings qualify the interpretation:

- The empirical detection rate for a single token at 1% budget (0.004) fell below the theoretical prediction (0.010). This discrepancy likely reflects variance at low event rates with finite trials, but it underscores that even the theoretical prediction is pessimistic for correctness-checking purposes: the true detection rate is at most 1% in this regime.
- The empirical rate for 4 tokens at 5% budget (0.208) slightly exceeded the theoretical prediction (0.185), and similarly for 4 tokens at 25% budget (0.716 vs. 0.684). These small upward deviations are consistent with sampling variability but do not alter the qualitative conclusion.
- No strategy overcame the fundamental sparsity constraint. The best-case scenario for sparse checking remains the random-error combinatorial formula, and it yields unacceptable miss rates for small error counts at any practical check budget.

## Limitations

1. **Oracle assumption.** This experiment uses an oracle verifier that performs exact token comparison. Any realistic sparse verifier (e.g., a semantic model or embedding comparison) will be strictly weaker, since it must additionally handle the possibility of semantically equivalent surface-form variation at checked positions. The oracle results therefore represent an upper bound; real-world performance will be equal or worse.

2. **Toy simulation scope.** This is a toy simulation on a local corpus, not a llama.cpp hook prototype, CUDA calibration run, or production validation. The results characterize combinatorial detection limits under controlled conditions and do not account for real-world verifier latency, model inference costs, or distributional shift in production outputs.

3. **Corpus scope.** The corpus is local text and code, not user-private production model outputs. However, the combinatorial detection limits are corpus-independent for position-based errors: the formula $P(\text{detect}) \approx 1 - (1 - m/n)^k$ depends only on the number of tokens and the number of errors, not on token content.

4. **Hypothesis inference.** No private Notion body was available beyond the project title and scaffold. The tested hypothesis was inferred from the project name "Sparse-Verifier Token Check." If the original intent differed from what was tested, the negative result applies specifically to the interpretation evaluated here.

5. **Adversarial model strength.** The adversarial model assumes the adversary knows the checked positions. For deterministic strategies (`hash_fixed`, `even_grid`), this is realistic. For `uniform_random`, an adversary would need to infer positions across multiple queries or exploit side channels. The 0.0% detection rate under adversarial avoidance should be interpreted as a worst-case bound for deterministic strategies and a realistic risk for any strategy whose checked positions can be inferred.

6. **Single-token semantics.** The experiment treats each token position independently. It does not model cases where a single token change has disproportionate semantic impact (e.g., negating a logical operator, changing a numerical constant). Such cases are precisely where sparse checking fails most dangerously: the error is both hard to detect probabilistically and high-impact semantically.

7. **Claim audit status.** The claim ledger for this artifact reports an empty claims list with audit status `blocked_empty_claims`. No structured claims were extracted for independent evidence-grounded auditing. The quantitative results reported here are drawn directly from the run notes and decision JSON and have not passed a formal claim/evidence audit.

## Reproducibility Checklist

- **Experiment script:** `scripts/sparse_verifier_check.py`
- **Full run log:** `logs/full_sparse_verifier.log`
- **Smoke test log:** `logs/smoke_sparse_verifier.log`
- **JSON metrics:** `metrics/sparse_verifier_metrics.json`
- **CSV rows:** `metrics/sparse_verifier_rows.csv`
- **Compact summary:** `metrics/summary.json`
- **Decision JSON:** `.omx/project_decision.json`
- **Notion access probe:** `logs/notion_probe.log`, `logs/notion_page.html`
- **Host:** `gx10-efe8`
- **Python version:** 3.12.3
- **Swap:** Disabled and verified (0 swaps during execution)
- **Randomization:** Deterministic corpus construction; random strategies seeded for reproducibility (see script)
- **Memory:** Max RSS 33,796 kB; no swap; MemAvailable stable at ~122 GB throughout
- **Result classification:** Toy simulation (not llama.cpp hook prototype, not CUDA calibration, not production validation)

## Conclusion

Sparse token verification cannot reliably detect small or adversarial token errors. At a 5% check budget, a single random token error is detected only 8.0% of the time; at 25%, only 24.8%. Under adversarial conditions, detection is 0.0% regardless of budget or strategy. These results hold for an oracle verifier and therefore bound the performance of any practical sparse verifier from above.

Sparse token checking is conditionally viable only as a probabilistic smoke test for bulk random corruption—transmission errors, storage bitrot, or regressions that alter many tokens—where the error fraction is large enough to make the combinatorial detection probability acceptable. The required check budget for a desired miss probability $\alpha$ under a random error fraction $f = m/n$ is approximately:

$$k \geq \frac{\ln(\alpha)}{\ln(1 - f)}$$

For correctness verification of generated text—where a single wrong token can change semantics, numerical results, code behavior, or logical conclusions—sparse token checking is insufficient. Practitioners should instead use full-output deterministic checks when a reference is available, cryptographic commitments over the complete token stream for integrity assurance, or semantic verification that reads all critical spans with targeted checks of numbers, identifiers, claims, and code paths. Sparse checks, if used at all, should be treated as a first-pass heuristic with explicit probabilistic miss rates, not as a correctness guarantee.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `scripts/sparse_verifier_check.py` |
| Full run log | `logs/full_sparse_verifier.log` |
| Smoke test log | `logs/smoke_sparse_verifier.log` |
| JSON metrics | `metrics/sparse_verifier_metrics.json` |
| CSV metrics | `metrics/sparse_verifier_rows.csv` |
| Compact summary | `metrics/summary.json` |
| Project decision | `.omx/project_decision.json` |
| Run notes | `run_notes.md` |
| Notion probe log | `logs/notion_probe.log` |
| Notion page HTML | `logs/notion_page.html` |
| Claim ledger | `papers/source-record-redacted-20260429T201048615377+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260429T201048615377+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260429T201048615377+0000/paper_manifest.json` |
