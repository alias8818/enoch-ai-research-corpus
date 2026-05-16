# Long-to-Short Compression Training: Feasibility and Generalization Failure on a Synthetic Auditable Benchmark

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts (run notes, decision JSON, benchmark outputs, claim ledger, evidence bundle). The operator claims no personal authorship credit for the writing or results beyond releasing the artifacts. Readers should treat this as an unreviewed AI-generated research artifact. No human review is asserted or implied.

---

## Abstract

We investigate whether a trained compressor can reliably shrink a long context into a short retained subset while preserving the fact needed by a downstream answerer. Using a synthetic, auditable benchmark where each example contains a query and a shuffled context of 64 candidate fact sentences with exactly one gold fact, we train a TF-IDF + logistic regression ranker with pair features (query-token coverage, answer-marker presence, decoy markers) and compare it against random, first, last, lexical overlap, and TF-IDF cosine baselines. On in-distribution and adversarial lexical-decoy conditions, the trained compressor achieves perfect gold-fact retention (1.000 at k=1) while compressing to approximately 2.4% of original token volume, strongly outperforming lexical overlap (0.848 in-distribution; 0.123 adversarial). However, under out-of-distribution paraphrase/template shift, the trained compressor's retention drops to 0.000 at k=1, whereas the untrained TF-IDF cosine baseline retains 0.755. This negative result is replicated across three seeds. We conclude that supervised compression training is viable under matched distributions and robust to lexical decoys, but overfits training templates and fails under semantic shift. Broader claims require semantic augmentation or pretrained encoders.

## 1. Introduction

Long-context language models face a fundamental tension: larger context windows increase the volume of irrelevant information competing for attention, potentially degrading retrieval and reasoning accuracy. A natural response is to compress the long context into a shorter retained subset before passing it to a downstream model. The core question is whether a trained compressor can learn to preserve the specific facts needed for downstream task success.

This question is difficult to study in production settings because real long-context tasks conflate compression quality with downstream model capability, and failures are hard to attribute. We therefore adopt a synthetic, auditable benchmark design that isolates compression quality: each example contains a query, a long shuffled context of candidate fact sentences, and exactly one gold fact sentence required to answer the query. A deterministic downstream answerer succeeds if and only if the gold fact is retained after compression. This design permits unambiguous measurement of compression quality independent of any downstream language model.

We train a lightweight ranker combining TF-IDF features with logistic regression over pair-level features (query-token coverage, answer-marker presence, decoy/no-answer markers) and evaluate across three conditions: in-distribution, adversarial lexical decoys, and out-of-distribution paraphrase/template shift. We report both the positive result—near-perfect compression under matched distributions—and the equally important negative result—complete failure under distribution shift.

## 2. Method

### 2.1 Benchmark Design

Each synthetic example consists of:

- A **query** requiring one specific fact to answer.
- A **long context** of 64 candidate fact sentences in random order.
- Exactly one **gold fact** sentence that, if retained, enables a deterministic answerer to produce the correct answer.

The compressor selects *k* sentences from the context. The downstream answerer is deterministic: it succeeds if and only if the gold fact is among the *k* retained sentences. This eliminates confounds from downstream model variance.

### 2.2 Metrics

Three metrics are reported:

- **Gold-fact retention accuracy**: fraction of examples where the gold fact is among the *k* selected sentences.
- **Mean gold rank**: average rank of the gold fact in the compressor's scoring (lower is better; 1 is optimal).
- **Compression ratio**: ratio of compressed token count to full-context token count (lower means more compression).

### 2.3 Baselines

Five baselines are evaluated:

1. **Random**: select *k* sentences uniformly at random.
2. **First**: select the first *k* sentences in context order.
3. **Last**: select the last *k* sentences in context order.
4. **Lexical overlap**: score each candidate sentence by token overlap with the query; select top-*k*.
5. **TF-IDF cosine**: score each candidate sentence by cosine similarity between its TF-IDF vector and the query's TF-IDF vector; select top-*k*.

### 2.4 Trained Method

The trained compressor uses a two-stage architecture:

1. **Feature extraction**: For each candidate sentence, compute TF-IDF representation and pair-level features including query-token coverage (fraction of query tokens appearing in the candidate), answer-marker presence (binary indicator for tokens associated with answer patterns), and decoy/no-answer markers (binary indicators for sentences containing misleading or non-answer patterns).

2. **Logistic regression ranker**: A logistic regression model trained on the pair features to predict whether a candidate sentence is the gold fact. At inference, all candidate sentences are scored and the top-*k* are retained.

Training uses 2,000 synthetic examples with 64-sentence contexts. Evaluation uses 1,000 examples per condition.

### 2.5 Evaluation Conditions

Three conditions test different aspects of robustness:

- **In-distribution**: Evaluation examples drawn from the same template distribution as training.
- **Adversarial lexical decoys**: Evaluation examples include decoy sentences engineered to have high lexical overlap with the query without containing the gold fact, directly attacking the lexical overlap baseline.
- **Out-of-distribution (OOD) paraphrase/template shift**: Evaluation examples use paraphrased queries and different sentence templates not seen during training, testing generalization beyond surface form.

### 2.6 Replication Protocol

To assess stability, three additional runs are conducted with seeds 11, 13, and 17, using 1,000 training examples and 500 evaluation examples per condition, evaluating at *k*=1 and *k*=4.

### 2.7 Computational Environment

Experiments run on a Linux host (`gx10-efe8`, `aarch64`) with an NVIDIA GB10 GPU visible via `nvidia-smi`. No GPU is used; all computation is CPU-based scikit-learn. Swap is intentionally disabled (`SwapTotal: 0 kB`). Available memory before the full run is approximately 122 GB; peak RSS during the full run is approximately 402 MB; available memory after the full run is approximately 122 GB. Wall-clock time for the full run is approximately 26 seconds. This is a CPU-probe-scale experiment, not a production training run.

## 3. Results

### 3.1 Full Run (64-sentence contexts, 1,000 eval examples per condition)

| Condition | Method | *k* | Gold Retained | Mean Gold Rank | Compression Ratio |
|---|---|---|---|---|---|
| In-distribution | Trained | 1 | 1.000 | 1.00 | 0.025 |
| In-distribution | Lexical overlap | 1 | 0.848 | 2.21 | 0.027 |
| Adversarial lexical decoys | Trained | 1 | 1.000 | 1.00 | 0.024 |
| Adversarial lexical decoys | Lexical overlap | 1 | 0.123 | 4.05 | 0.037 |
| OOD paraphrase/templates | Trained | 1 | 0.000 | 20.57 | 0.026 |
| OOD paraphrase/templates | TF-IDF cosine | 1 | 0.755 | 1.32 | 0.034 |

The trained compressor achieves perfect retention at *k*=1 on both in-distribution and adversarial conditions, compressing to approximately 2.4–2.5% of the original token volume. On the adversarial lexical-decoy condition, the trained method dramatically outperforms lexical overlap (1.000 vs. 0.123), demonstrating that the learned features successfully distinguish gold facts from lexical decoys.

The OOD paraphrase condition reveals a sharp failure: the trained compressor retains 0.000 gold facts at *k*=1, with a mean gold rank of 20.57—worse than random selection for a 64-sentence context (expected rank approximately 32.5). The untrained TF-IDF cosine baseline, by contrast, retains 0.755 at *k*=1 on the same OOD condition.

### 3.2 Replication Across Seeds

Three replicate runs (seeds 11, 13, 17; 500 eval examples per condition) confirm the pattern:

- **In-distribution and adversarial conditions**: Trained method retention is 1.000 at both *k*=1 and *k*=4 across all three seeds.
- **OOD paraphrase condition**: Trained method retention is 0.000 at both *k*=1 and *k*=4 across all three seeds.
- **TF-IDF cosine on OOD paraphrase**: Mean retention at *k*=1 is 0.757; at *k*=4, mean retention is 1.000 across all three seeds.

The replication confirms that the trained compressor's OOD failure is systematic and not an artifact of a single random seed.

### 3.3 Resource Usage

The full run (2,000 training examples, 1,000 eval examples, 4 values of *k*) completed in approximately 26 seconds of wall-clock time with a peak RSS of approximately 402 MB. No GPU memory was consumed. The lightweight computational footprint confirms this is a CPU-probe-scale experiment, not a production training run.

## 4. Limitations

This study has several important limitations that constrain the generality of its conclusions:

1. **Synthetic benchmark only.** All results are obtained on a synthetic, auditable benchmark with templated sentences and a single gold fact per example. Real long-context language data exhibits far greater semantic diversity, multi-hop reasoning requirements, and ambiguous or partial relevance. Performance on this benchmark does not predict performance on real tasks.

2. **Template overfitting.** The trained compressor's complete failure under OOD paraphrase/template shift (0.000 retention) demonstrates severe overfitting to the surface forms present in training. The logistic regression ranker learns template-specific token patterns rather than semantic relevance. This is the central negative result of the study.

3. **Single-sentence gold fact.** The benchmark assumes exactly one sentence is sufficient to answer each query. Real tasks often require synthesizing information across multiple sentences, which this design cannot evaluate.

4. **Shuffled context only.** Sentences are presented in random order, eliminating any positional structure that might exist in real documents. Positional baselines (first, last) are therefore uninformative about real document structure.

5. **No pretrained semantic encoder.** The trained method uses only TF-IDF and hand-crafted pair features. It does not incorporate pretrained embeddings or LLM-based representations, which might improve OOD generalization. This is a deliberate design choice to isolate the effect of supervised training on shallow features, but it limits the method's applicability.

6. **Small scale.** Training on 2,000 synthetic examples with a logistic regression ranker is a proof-of-concept scale. No claim is made about scaling behavior with larger training sets, more complex rankers, or real data.

7. **Deterministic downstream answerer.** The use of a deterministic answerer that succeeds if and only if the gold fact is retained eliminates downstream model variance but also eliminates the possibility that partial information (e.g., a paraphrased version of the gold fact) might enable correct answers. The compression quality measured here is a strict lower bound on what a capable downstream model could achieve.

## 5. Reproducibility Checklist

- **Code**: `scripts/long_to_short_compression_experiment.py` (verified via `py_compile`).
- **Random seeds**: Full run uses seed 7; replication runs use seeds 11, 13, 17. All seeds are specified as command-line arguments.
- **Hardware**: Linux `aarch64` host (`gx10-efe8`), NVIDIA GB10 GPU present but unused. CPU-only execution.
- **Software dependencies**: Python 3, scikit-learn (version as installed on host).
- **Full run command**:
  ```
  /usr/bin/time -v python3 scripts/long_to_short_compression_experiment.py \
    --train 2000 --eval 1000 --sentences 64 --ks 1,2,4,8 --seed 7 \
    --outdir results/full
  ```
- **Replication commands**: See run notes for seed-specific commands.
- **Output artifacts**: `results/full/metrics.csv`, `results/full/run_meta.json`, `results/full/examples.jsonl`, `results/replicate_summary.csv`, per-seed result directories, and corresponding log files.
- **Memory constraints**: Swap disabled; peak RSS approximately 402 MB; approximately 122 GB available before and after full run.
- **Wall-clock time**: Approximately 26 seconds for full run.

## 6. Conclusion

We have shown that a trained long-to-short compressor—a logistic regression ranker over TF-IDF and pair features—can achieve perfect gold-fact retention on a synthetic 64-sentence benchmark under in-distribution and adversarial lexical-decoy conditions, compressing to approximately 2.5% of original token volume. The trained method dramatically outperforms lexical overlap on adversarial decoys (1.000 vs. 0.123 retention at *k*=1), confirming that supervised compression can learn to resist lexical distraction.

However, the trained compressor completely fails under out-of-distribution paraphrase/template shift (0.000 retention at *k*=1, replicated across three seeds), while an untrained TF-IDF cosine baseline generalizes substantially better (0.755 retention). This demonstrates that the learned ranker overfits to training surface forms and does not acquire semantic relevance signals.

These results support a scoped conclusion: learned compression is feasible and robust to lexical adversaries under matched distributions, but supervised training on shallow features alone is insufficient for distributional generalization. The path to broadly useful long-to-short compression likely requires semantic or paraphrase-aware augmentation, pretrained encoders, or LLM-based compressors evaluated on real long-context tasks. The present work establishes a reproducible synthetic benchmark and a clear negative result that any subsequent approach must address.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `scripts/long_to_short_compression_experiment.py` |
| Full run metrics | `results/full/metrics.csv` |
| Full run metadata | `results/full/run_meta.json` |
| Full run examples | `results/full/examples.jsonl` |
| Replicate summary | `results/replicate_summary.csv` |
| Replicate results (seed 11) | `results/rep_seed_11/` |
| Replicate results (seed 13) | `results/rep_seed_13/` |
| Replicate results (seed 17) | `results/rep_seed_17/` |
| Smoke test log | `logs/smoke_v2.log` |
| Full run log | `logs/full.log` |
| Full run time log | `logs/full.time.log` |
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T023148640746+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T023148640746+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T023148640746+0000/paper_manifest.json` |
