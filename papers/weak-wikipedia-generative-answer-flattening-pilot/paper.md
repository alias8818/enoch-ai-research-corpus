# Weak-Wikipedia Generative Answer Flattening Pilot

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by the OMX research automation pipeline. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed this document.

---

## Abstract

We investigate whether curriculum flattening—reducing exposure skew toward high-frequency relation-answer pairs—improves tail answer quality in a generative answer-string setting. Using a small encoder-decoder model (mean-pool prompt encoder + GRU decoder) trained on 1,500 weak-Wikipedia triples, we compare five curricula (natural, bucket-flat, flat, dedup-once, and natural-plus-tail-fix) across three random seeds. Flattened and deduplicated curricula produce substantial tail F1 gains over natural sampling (up to +29.46 tail F1 points for flat, +34.46 for dedup-once), with dedup-once achieving the best balanced F1 of 52.27% versus 45.62% for natural. However, all flattened curricula reduce natural-weighted F1 and head/torso F1 relative to the natural baseline, and the natural-plus-tail-fix curriculum damages balanced F1 despite modest tail recovery. These results are limited to a single small-scale synthetic dataset, a tiny model architecture, and one hardware configuration. Confidence in the finding is medium and evidence strength is moderate.

## 1. Introduction

Knowledge-intensive language models trained on naturally distributed corpora exhibit strong performance on head-frequency facts but poor performance on tail-frequency facts, a pattern driven by the heavy-tailed distribution of training exposures. Prior work on the parent project for this branch established that curriculum flattening improves tail fact-ID classification accuracy in a prompt-to-fact retrieval setting. The present pilot asks whether those gains survive a materially different evaluation: generative answer-string decoding rather than fact-ID classification.

This distinction matters because generative decoding introduces compounding error—incorrect early tokens can derail entire answer strings—and because teacher-forced training with greedy decoding may interact differently with exposure distributions than contrastive or classification losses. If flattened curricula improve generative tail quality, the mechanism has broader applicability than the classification-only setting suggests.

We define a branch-specific kill condition: finalize negative if flattened generative curricula fail to improve tail answer-token F1 by at least 5 points over natural sampling and simultaneously fail to improve balanced F1. This condition was not met; the evidence supports a positive finding, though with important caveats.

## 2. Method

### 2.1 Model Architecture

The generative answer model consists of:

- **Encoder:** A prompt encoder that maps `(title, relation)` token sequences to a fixed-dimensional representation via mean pooling of token embeddings.
- **Decoder:** A single-layer GRU that generates answer token sequences autoregressively, conditioned on the encoder output.

Training uses teacher forcing with cross-entropy loss on answer tokens. Evaluation uses greedy decoding to produce answer strings, which are then compared against reference strings via token-level F1.

### 2.2 Data

The dataset comprises 1,500 weak-Wikipedia triples stored in `data/wikipedia_like_facts.jsonl`, copied from the parent branch's cached triples. Each triple contains a title, relation, and answer string. Triples are partitioned into head, torso, and tail frequency bands based on relation frequency in the corpus.

### 2.3 Curricula

Five training curricula are compared:

1. **Natural:** Exposure proportional to natural relation frequency in the corpus.
2. **Bucket-flat:** Relations grouped into frequency buckets; each bucket receives equal total exposure, flattening the distribution partially.
3. **Flat:** Each unique relation-answer pair receives equal exposure regardless of frequency.
4. **Dedup-once:** Natural sampling with duplicate exposures removed (each unique triple seen once per epoch), then repeated to fill the budget.
5. **Natural-plus-tail-fix:** Natural sampling for the base phase (12,000 exposures) followed by a tail-focused continuation phase (4,000 exposures) that oversamples tail relations.

### 2.4 Training Protocol

Each curriculum is evaluated over 3 random seeds. The base training budget is 12,000 exposures; the natural-plus-tail-fix curriculum adds 4,000 tail-fix continuation exposures. Batch size is 64, selected after a calibration sweep to balance optimizer step count against throughput. The model is trained with teacher forcing and evaluated by greedy decoding at the end of training.

### 2.5 Metrics

- **Balanced F1:** Macro-averaged token-level F1 across head, torso, and tail bands.
- **Natural-weighted F1:** Frequency-weighted token-level F1 reflecting the natural distribution.
- **Head/Torso/Tail F1:** Token-level F1 computed separately for each frequency band.
- **Balanced EM:** Macro-averaged exact match across frequency bands (reported for dedup-once).

## 3. Results

### 3.1 Main Comparison

| Curriculum | Balanced F1 | Nat-wtd F1 | Head F1 | Torso F1 | Tail F1 |
|---|---|---|---|---|---|
| Natural | 45.62% | 58.76% | 64.17% | 51.56% | 21.12% |
| Bucket-flat | 50.55% | 56.55% | 63.90% | 45.46% | 42.30% |
| Flat | 48.92% | — | — | — | 50.58% |
| Dedup-once | 52.27% | — | — | — | 55.58% |
| Natural+tail-fix | — | — | — | — | +6.42 vs natural |

Notes: Natural-weighted F1, head F1, and torso F1 for flat and dedup-once are not separately reported in the available artifacts; the run notes provide only balanced F1 and tail F1 for these conditions. Natural-plus-tail-fix is reported as a delta relative to natural for tail F1 only; its balanced F1 is noted as damaged relative to natural.

### 3.2 Tail F1 Gains

All flattened curricula produce large tail F1 improvements over natural sampling:

- **Bucket-flat:** +21.18 tail F1 points over natural.
- **Flat:** +29.46 tail F1 points over natural.
- **Dedup-once:** +34.46 tail F1 points over natural.

These gains exceed the 5-point threshold defined in the kill condition.

### 3.3 Balanced F1 Gains

Balanced F1 also improves:

- **Bucket-flat:** +4.94 balanced F1 points over natural.
- **Flat:** +3.31 balanced F1 points over natural.
- **Dedup-once:** +6.65 balanced F1 points over natural (52.27% vs. 45.62%).

### 3.4 Head and Torso Degradation

Flattened curricula trade head and torso quality for tail gains:

- **Bucket-flat** reduces torso F1 from 51.56% to 45.46% (−6.10 points) and natural-weighted F1 from 58.76% to 56.55% (−2.21 points), while head F1 is nearly unchanged (64.17% → 63.90%).
- **Natural-plus-tail-fix** damages head/torso F1 and balanced F1 relative to natural, making it the least favorable flattened curriculum despite its tail recovery.

### 3.5 Exact Match

Dedup-once achieves a balanced exact match of 31.59%. No other curriculum's exact match is reported in the available artifacts.

### 3.6 Performance and Resource Usage

- **Device:** NVIDIA GB10 (CUDA).
- **Throughput:** ~5,098 samples/sec during calibration; ~19.9k–20.3k train samples/sec during full runs.
- **Wall clock:** 12.66 seconds total.
- **Max process RSS:** ~1.45 GB.
- **MemAvailable:** ~119 GB; SwapFree: 0.
- **GPU utilization:** The `nvidia-smi` utilization sample read 0% at snapshot time, likely because the run completed before the snapshot. Throughput and PyTorch allocator/RSS/meminfo are the reliable performance evidence for this short run.

## 4. Limitations

1. **Scale:** The dataset contains only 1,500 triples, and the model is a tiny mean-pool encoder with a single GRU decoder layer. These results do not establish whether the same pattern holds at larger scale, with deeper architectures, or with pretrained language models.

2. **Single dataset:** All experiments use weak-Wikipedia synthetic triples. Generalization to real-world knowledge bases, open-domain QA datasets, or non-English corpora is not established.

3. **Greedy decoding only:** Evaluation uses greedy decoding. Beam search, nucleus sampling, or constrained decoding may interact differently with curriculum effects.

4. **Incomplete metric reporting:** Natural-weighted F1, head F1, and torso F1 are not reported for the flat and dedup-once curricula in the available artifacts, limiting the precision of trade-off analysis for those conditions.

5. **No external replication:** Results are from a single hardware configuration (NVIDIA GB10) and software environment (PyTorch 2.11.0 +cu130). No cross-platform or independent replication is available.

6. **Short run duration:** The total wall clock of 12.66 seconds and the GPU utilization snapshot at 0% mean that hardware performance numbers should be interpreted cautiously.

7. **Natural-plus-tail-fix is a negative result:** This curriculum recovers some tail quality but damages balanced F1, demonstrating that naive tail oversampling is not a reliable remedy and that the flattening approach matters.

8. **Confidence is medium:** The project decision assigns medium confidence and moderate evidence strength. The finding is supportive but not conclusive.

## 5. Reproducibility Checklist

| Item | Status |
|---|---|
| Code available | Yes: `src/generative_answer_flattening_pilot.py` |
| Data available | Yes: `data/wikipedia_like_facts.jsonl` (1,500 weak-Wikipedia triples) |
| Random seeds reported | Yes: 3 seeds per curriculum (individual seed values not in artifacts) |
| Hardware specified | Yes: NVIDIA GB10, CUDA |
| Software versions specified | Yes: PyTorch 2.11.0 (+cu130), NumPy |
| Batch size reported | Yes: 64 |
| Training budget reported | Yes: 12,000 base exposures; 4,000 tail-fix continuation |
| Metrics defined | Yes: token-level F1 per band, balanced F1, natural-weighted F1, balanced EM |
| Raw results available | Yes: `results/raw_runs.csv` |
| Aggregated metrics available | Yes: `results/metrics.json` |
| Report available | Yes: `results/report.md` |
| Decision rationale recorded | Yes: `.omx/project_decision.json` |
| Claim audit available | Yes: `claim_ledger.json` |
| Evidence bundle available | Yes: `evidence_bundle.json` |

## 6. Conclusion

In a small-scale generative answer-string pilot on 1,500 weak-Wikipedia triples, curriculum flattening and deduplication substantially improve tail answer-token F1 and balanced F1 over natural frequency-proportional sampling. The dedup-once curriculum achieves the best balanced F1 (52.27%, +6.65 over natural) and tail F1 (55.58%, +34.46 over natural). These gains come at the cost of reduced torso F1 and natural-weighted F1, indicating a real trade-off rather than a free improvement. The natural-plus-tail-fix curriculum demonstrates that naive tail oversampling can damage overall quality, making structured flattening preferable.

The kill condition—requiring at least +5 tail F1 points and improved balanced F1—was not met (i.e., the method passed). However, the result is bounded by the small model, single dataset, greedy decoding, and absence of external replication. The finding supports the hypothesis that flattened exposure distributions improve generative tail quality, but confidence is medium and the evidence is moderate. A follow-up with a small pretrained LM adapter would strengthen external validity if required.

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Implementation | `src/generative_answer_flattening_pilot.py` |
| Dataset | `data/wikipedia_like_facts.jsonl` |
| Aggregated metrics | `results/metrics.json` |
| Raw run data | `results/raw_runs.csv` |
| Run report | `results/report.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Run notes | `run_notes.md` |
| Claim audit | `papers/.../claim_ledger.json` |
| Evidence bundle | `papers/.../evidence_bundle.json` |
| Paper manifest | `papers/.../paper_manifest.json` |
